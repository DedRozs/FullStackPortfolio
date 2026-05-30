from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from apps.workflow_automation.domain.model import (
    AutomationAction,
    AutomationCondition,
    AutomationEngineService,
    AutomationRule,
    AutomationRun,
    AutomationRunLog,
    RuleEvaluationService,
)
from apps.workflow_automation.domain.repositories import (
    AutomationActionRepository,
    AutomationConditionRepository,
    AutomationRuleRepository,
    AutomationRunLogRepository,
    AutomationRunRepository,
)
from apps.workflow_automation.domain.value_objects import (
    RunStatus,
    TriggerContext,
    TriggerType,
)
from apps.workflow_automation.application.dtos import (
    ActionDTO,
    AddActionCommand,
    AddConditionCommand,
    AutomationRuleDTO,
    AutomationRunDTO,
    ConditionDTO,
    CreateRuleCommand,
    DeleteRuleCommand,
    DisableRuleCommand,
    DryRunResultDTO,
    DryRunRuleCommand,
    EnableRuleCommand,
    ExecuteRuleCommand,
    GetRuleRunsQuery,
    ListRulesQuery,
    RunLogDTO,
    UpdateRuleCommand,
)

logger = logging.getLogger(__name__)

_now = lambda: datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Mapper helpers
# ---------------------------------------------------------------------------


def _rule_to_dto(rule: AutomationRule) -> AutomationRuleDTO:
    return AutomationRuleDTO(
        id=rule.id,
        name=rule.name,
        description=rule.description,
        trigger_type=rule.trigger_type.value,
        is_enabled=rule.is_enabled,
        created_at=rule.created_at,
    )


def _run_to_dto(run: AutomationRun) -> AutomationRunDTO:
    return AutomationRunDTO(
        id=run.id,
        rule_id=run.rule_id,
        trigger_type=run.trigger_type,
        status=run.status.value,
        is_dry_run=run.is_dry_run,
        started_at=run.started_at,
        completed_at=run.completed_at,
        created_at=run.created_at,
    )


def _condition_to_dto(condition: AutomationCondition) -> ConditionDTO:
    return ConditionDTO(
        id=condition.id,
        rule_id=condition.rule_id,
        field_name=condition.field_name,
        operator=condition.operator.value,
        expected_value=condition.expected_value,
        position=condition.position,
    )


def _action_to_dto(action: AutomationAction) -> ActionDTO:
    return ActionDTO(
        id=action.id,
        rule_id=action.rule_id,
        action_type=action.action_type.value,
        parameters=action.parameters,
        position=action.position,
    )


def _log_to_dto(log: AutomationRunLog) -> RunLogDTO:
    return RunLogDTO(
        id=log.id,
        run_id=log.run_id,
        level=log.level,
        message=log.message,
        logged_at=log.logged_at,
    )


# ---------------------------------------------------------------------------
# Use cases
# ---------------------------------------------------------------------------


class CreateRule:
    def __init__(self, rule_repo: AutomationRuleRepository) -> None:
        self._rule_repo = rule_repo

    def execute(self, cmd: CreateRuleCommand) -> AutomationRuleDTO:
        rule = AutomationRule(
            id=uuid.uuid4(),
            name=cmd.name,
            trigger_type=cmd.trigger_type,
            is_enabled=True,
            created_at=_now(),
            description=cmd.description,
        )
        self._rule_repo.save(rule)
        logger.info("AutomationRule created: %s", rule.id)
        return _rule_to_dto(rule)


class UpdateRule:
    def __init__(self, rule_repo: AutomationRuleRepository) -> None:
        self._rule_repo = rule_repo

    def execute(self, cmd: UpdateRuleCommand) -> AutomationRuleDTO:
        rule = self._rule_repo.get_by_id(cmd.rule_id)
        if rule is None:
            raise ValueError(f"AutomationRule {cmd.rule_id} not found.")
        if cmd.name is not None:
            rule.name = cmd.name
        if cmd.description is not None:
            rule.description = cmd.description
        self._rule_repo.save(rule)
        return _rule_to_dto(rule)


class DeleteRule:
    def __init__(
        self,
        rule_repo: AutomationRuleRepository,
        condition_repo: AutomationConditionRepository,
        action_repo: AutomationActionRepository,
    ) -> None:
        self._rule_repo = rule_repo
        self._condition_repo = condition_repo
        self._action_repo = action_repo

    def execute(self, cmd: DeleteRuleCommand) -> None:
        rule = self._rule_repo.get_by_id(cmd.rule_id)
        if rule is None:
            raise ValueError(f"AutomationRule {cmd.rule_id} not found.")
        self._condition_repo.delete_by_rule_id(cmd.rule_id)
        self._action_repo.delete_by_rule_id(cmd.rule_id)
        self._rule_repo.delete(cmd.rule_id)
        logger.info("AutomationRule deleted: %s", cmd.rule_id)


class EnableRule:
    def __init__(self, rule_repo: AutomationRuleRepository) -> None:
        self._rule_repo = rule_repo

    def execute(self, cmd: EnableRuleCommand) -> AutomationRuleDTO:
        rule = self._rule_repo.get_by_id(cmd.rule_id)
        if rule is None:
            raise ValueError(f"AutomationRule {cmd.rule_id} not found.")
        rule.enable()
        self._rule_repo.save(rule)
        return _rule_to_dto(rule)


class DisableRule:
    def __init__(self, rule_repo: AutomationRuleRepository) -> None:
        self._rule_repo = rule_repo

    def execute(self, cmd: DisableRuleCommand) -> AutomationRuleDTO:
        rule = self._rule_repo.get_by_id(cmd.rule_id)
        if rule is None:
            raise ValueError(f"AutomationRule {cmd.rule_id} not found.")
        rule.disable()
        self._rule_repo.save(rule)
        return _rule_to_dto(rule)


class AddCondition:
    def __init__(
        self,
        rule_repo: AutomationRuleRepository,
        condition_repo: AutomationConditionRepository,
    ) -> None:
        self._rule_repo = rule_repo
        self._condition_repo = condition_repo

    def execute(self, cmd: AddConditionCommand) -> ConditionDTO:
        if self._rule_repo.get_by_id(cmd.rule_id) is None:
            raise ValueError(f"AutomationRule {cmd.rule_id} not found.")
        condition = AutomationCondition(
            id=uuid.uuid4(),
            rule_id=cmd.rule_id,
            field_name=cmd.field_name,
            operator=cmd.operator,
            expected_value=cmd.expected_value,
            position=cmd.position,
        )
        self._condition_repo.save(condition)
        return _condition_to_dto(condition)


class AddAction:
    def __init__(
        self,
        rule_repo: AutomationRuleRepository,
        action_repo: AutomationActionRepository,
    ) -> None:
        self._rule_repo = rule_repo
        self._action_repo = action_repo

    def execute(self, cmd: AddActionCommand) -> ActionDTO:
        if self._rule_repo.get_by_id(cmd.rule_id) is None:
            raise ValueError(f"AutomationRule {cmd.rule_id} not found.")
        action = AutomationAction(
            id=uuid.uuid4(),
            rule_id=cmd.rule_id,
            action_type=cmd.action_type,
            parameters=dict(cmd.parameters),
            position=cmd.position,
        )
        self._action_repo.save(action)
        return _action_to_dto(action)


class ListRules:
    def __init__(self, rule_repo: AutomationRuleRepository) -> None:
        self._rule_repo = rule_repo

    def execute(self, query: ListRulesQuery) -> list[AutomationRuleDTO]:
        if query.trigger_type is not None:
            rules = self._rule_repo.find_by_trigger_type(query.trigger_type)
        elif query.enabled_only:
            rules = self._rule_repo.find_all_enabled()
        else:
            rules = self._rule_repo.list_all()
        return [_rule_to_dto(rule) for rule in rules]


class GetRuleRuns:
    def __init__(
        self,
        run_repo: AutomationRunRepository,
        log_repo: AutomationRunLogRepository,
    ) -> None:
        self._run_repo = run_repo
        self._log_repo = log_repo

    def execute(self, query: GetRuleRunsQuery) -> list[AutomationRunDTO]:
        runs = self._run_repo.find_by_rule_id(query.rule_id)
        return [_run_to_dto(run) for run in runs]


class ExecuteRule:
    def __init__(
        self,
        rule_repo: AutomationRuleRepository,
        condition_repo: AutomationConditionRepository,
        action_repo: AutomationActionRepository,
        run_repo: AutomationRunRepository,
        run_log_repo: AutomationRunLogRepository,
    ) -> None:
        self._rule_repo = rule_repo
        self._condition_repo = condition_repo
        self._action_repo = action_repo
        self._run_repo = run_repo
        self._run_log_repo = run_log_repo
        self._condition_evaluators: dict = {}
        self._action_handlers: dict = {}

    def set_condition_evaluators(self, evaluators: dict) -> None:
        self._condition_evaluators = evaluators

    def set_action_handlers(self, handlers: dict) -> None:
        self._action_handlers = handlers

    def execute(self, cmd: ExecuteRuleCommand) -> AutomationRunDTO:
        rule = self._rule_repo.get_by_id(cmd.rule_id)
        if rule is None:
            raise ValueError(f"AutomationRule {cmd.rule_id} not found.")

        conditions = list(self._condition_repo.find_by_rule_id(cmd.rule_id))
        actions = list(self._action_repo.find_by_rule_id(cmd.rule_id))

        context = TriggerContext(
            trigger_type=TriggerType(cmd.trigger_type),
            source_id=cmd.context_payload.get("source_id", ""),
            source_type=cmd.context_payload.get("source_type", ""),
            payload=cmd.context_payload,
        )

        run = AutomationRun(
            id=uuid.uuid4(),
            rule_id=cmd.rule_id,
            trigger_type=cmd.trigger_type,
            status=RunStatus.PENDING,
            is_dry_run=False,
            created_at=_now(),
            context_payload=cmd.context_payload,
        )
        self._run_repo.save(run)

        run_log_repo = self._run_log_repo

        def _factory(*, run_id: uuid.UUID, level: str, message: str) -> None:
            log_entry = AutomationRunLog(
                id=uuid.uuid4(),
                run_id=run_id,
                level=level,
                message=message,
                logged_at=_now(),
            )
            run_log_repo.save(log_entry)

        AutomationEngineService().execute(
            rule,
            conditions,
            actions,
            context,
            self._condition_evaluators,
            self._action_handlers,
            run,
            _factory,
        )
        self._run_repo.save(run)
        logger.info(
            "AutomationRule %s executed; run %s status=%s",
            rule.id,
            run.id,
            run.status,
        )
        return _run_to_dto(run)


class DryRunRule:
    def __init__(
        self,
        rule_repo: AutomationRuleRepository,
        condition_repo: AutomationConditionRepository,
        action_repo: AutomationActionRepository,
        run_repo: AutomationRunRepository,
        run_log_repo: AutomationRunLogRepository,
    ) -> None:
        self._rule_repo = rule_repo
        self._condition_repo = condition_repo
        self._action_repo = action_repo
        self._run_repo = run_repo
        self._run_log_repo = run_log_repo
        self._condition_evaluators: dict = {}
        self._action_handlers: dict = {}

    def set_condition_evaluators(self, evaluators: dict) -> None:
        self._condition_evaluators = evaluators

    def set_action_handlers(self, handlers: dict) -> None:
        self._action_handlers = handlers

    def execute(self, cmd: DryRunRuleCommand) -> DryRunResultDTO:
        rule = self._rule_repo.get_by_id(cmd.rule_id)
        if rule is None:
            raise ValueError(f"AutomationRule {cmd.rule_id} not found.")

        conditions = list(self._condition_repo.find_by_rule_id(cmd.rule_id))
        actions = list(self._action_repo.find_by_rule_id(cmd.rule_id))

        context = TriggerContext(
            trigger_type=rule.trigger_type,
            source_id=cmd.context_payload.get("source_id", ""),
            source_type=cmd.context_payload.get("source_type", ""),
            payload=cmd.context_payload,
        )

        run = AutomationRun(
            id=uuid.uuid4(),
            rule_id=cmd.rule_id,
            trigger_type=rule.trigger_type.value,
            status=RunStatus.PENDING,
            is_dry_run=True,
            created_at=_now(),
            context_payload=cmd.context_payload,
        )
        self._run_repo.save(run)

        run_log_repo = self._run_log_repo
        collected_logs: list[str] = []

        def _factory(*, run_id: uuid.UUID, level: str, message: str) -> None:
            log_entry = AutomationRunLog(
                id=uuid.uuid4(),
                run_id=run_id,
                level=level,
                message=message,
                logged_at=_now(),
            )
            run_log_repo.save(log_entry)
            collected_logs.append(message)

        AutomationEngineService().execute(
            rule,
            conditions,
            actions,
            context,
            self._condition_evaluators,
            self._action_handlers,
            run,
            _factory,
        )
        self._run_repo.save(run)

        conditions_passed = run.status == RunStatus.DRY_RUN
        would_execute_actions = (
            [a.action_type.value for a in sorted(actions, key=lambda a: a.position)]
            if conditions_passed
            else []
        )

        return DryRunResultDTO(
            rule_id=cmd.rule_id,
            conditions_passed=conditions_passed,
            log_messages=collected_logs,
            would_execute_actions=would_execute_actions,
        )
