from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable
from uuid import UUID

from apps.workflow_automation.domain.value_objects import (
    ActionType,
    ConditionOperator,
    RunStatus,
    TriggerContext,
    TriggerType,
)

_now = lambda: datetime.now(timezone.utc)


@dataclass
class AutomationRule:
    id: UUID
    name: str
    trigger_type: TriggerType
    is_enabled: bool
    created_at: datetime
    description: str | None = None

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("AutomationRule name must not be blank.")

    def enable(self) -> None:
        self.is_enabled = True

    def disable(self) -> None:
        self.is_enabled = False


@dataclass
class AutomationCondition:
    id: UUID
    rule_id: UUID
    field_name: str
    operator: ConditionOperator
    expected_value: str
    position: int

    def __post_init__(self) -> None:
        if not self.field_name or not self.field_name.strip():
            raise ValueError("AutomationCondition field_name must not be blank.")


@dataclass
class AutomationAction:
    id: UUID
    rule_id: UUID
    action_type: ActionType
    position: int
    parameters: dict = field(default_factory=dict)


@dataclass
class AutomationRun:
    id: UUID
    rule_id: UUID
    trigger_type: str
    status: RunStatus
    is_dry_run: bool
    created_at: datetime
    context_payload: dict = field(default_factory=dict)
    started_at: datetime | None = None
    completed_at: datetime | None = None

    def start(self) -> None:
        self.status = RunStatus.RUNNING
        self.started_at = _now()

    def complete(self) -> None:
        self.status = RunStatus.SUCCESS
        self.completed_at = _now()

    def fail(self) -> None:
        self.status = RunStatus.FAILURE
        self.completed_at = _now()

    def mark_dry_run_complete(self) -> None:
        self.status = RunStatus.DRY_RUN
        self.completed_at = _now()


@dataclass
class AutomationRunLog:
    id: UUID
    run_id: UUID
    level: str
    message: str
    logged_at: datetime


class RuleEvaluationService:
    def evaluate(
        self,
        rule: AutomationRule,
        conditions: list[AutomationCondition],
        context: TriggerContext,
        condition_evaluators: dict,
    ) -> bool:
        for condition in conditions:
            evaluator = condition_evaluators.get(condition.operator.value)
            if evaluator is None:
                return False
            field_value = context.payload.get(condition.field_name)
            if not evaluator(field_value, condition.expected_value):
                return False
        return True


class AutomationEngineService:
    def execute(
        self,
        rule: AutomationRule,
        conditions: list[AutomationCondition],
        actions: list[AutomationAction],
        context: TriggerContext,
        condition_evaluators: dict,
        action_handlers: dict,
        run: AutomationRun,
        run_log_factory: Callable,
    ) -> AutomationRun:
        evaluation_service = RuleEvaluationService()
        run.start()

        conditions_met = evaluation_service.evaluate(rule, conditions, context, condition_evaluators)
        if not conditions_met:
            run_log_factory(run_id=run.id, level="info", message="conditions not met")
            run.fail()
            return run

        if run.is_dry_run:
            run.mark_dry_run_complete()
            return run

        for action in sorted(actions, key=lambda a: a.position):
            handler = action_handlers.get(action.action_type.value)
            if handler is None:
                run_log_factory(
                    run_id=run.id,
                    level="error",
                    message=f"No handler registered for action type: {action.action_type.value}",
                )
                run.fail()
                return run
            try:
                handler(action.parameters, context)
            except Exception as exc:
                run_log_factory(run_id=run.id, level="error", message=str(exc))
                run.fail()
                return run

        run.complete()
        return run
