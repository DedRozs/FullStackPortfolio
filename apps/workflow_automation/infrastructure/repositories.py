from __future__ import annotations

import logging
from typing import Sequence
from uuid import UUID

from apps.workflow_automation import models as orm
from apps.workflow_automation.domain.model import (
    AutomationAction,
    AutomationCondition,
    AutomationRule,
    AutomationRun,
    AutomationRunLog,
)
from apps.workflow_automation.domain.repositories import (
    AutomationActionRepository,
    AutomationConditionRepository,
    AutomationRuleRepository,
    AutomationRunLogRepository,
    AutomationRunRepository,
)
from apps.workflow_automation.domain.value_objects import (
    ActionType,
    ConditionOperator,
    RunStatus,
    TriggerType,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Private mappers
# ---------------------------------------------------------------------------


def _rule_orm_to_entity(obj: orm.AutomationRule) -> AutomationRule:
    return AutomationRule(
        id=obj.id,
        name=obj.name,
        description=obj.description,
        trigger_type=TriggerType(obj.trigger_type),
        is_enabled=obj.is_enabled,
        created_at=obj.created_at,
    )


def _condition_orm_to_entity(obj: orm.AutomationCondition) -> AutomationCondition:
    return AutomationCondition(
        id=obj.id,
        rule_id=obj.rule_id,
        field_name=obj.field_name,
        operator=ConditionOperator(obj.operator),
        expected_value=obj.expected_value,
        position=obj.position,
    )


def _action_orm_to_entity(obj: orm.AutomationAction) -> AutomationAction:
    return AutomationAction(
        id=obj.id,
        rule_id=obj.rule_id,
        action_type=ActionType(obj.action_type),
        parameters=dict(obj.parameters),
        position=obj.position,
    )


def _run_orm_to_entity(obj: orm.AutomationRun) -> AutomationRun:
    return AutomationRun(
        id=obj.id,
        rule_id=obj.rule_id,
        trigger_type=obj.trigger_type,
        context_payload=dict(obj.context_payload),
        status=RunStatus(obj.status),
        is_dry_run=obj.is_dry_run,
        started_at=obj.started_at,
        completed_at=obj.completed_at,
        created_at=obj.created_at,
    )


def _log_orm_to_entity(obj: orm.AutomationRunLog) -> AutomationRunLog:
    return AutomationRunLog(
        id=obj.id,
        run_id=obj.run_id,
        level=obj.level,
        message=obj.message,
        logged_at=obj.logged_at,
    )


# ---------------------------------------------------------------------------
# Repository implementations
# ---------------------------------------------------------------------------


class DjangoAutomationRuleRepository(AutomationRuleRepository):
    def get_by_id(self, rule_id: UUID) -> AutomationRule | None:
        try:
            return _rule_orm_to_entity(orm.AutomationRule.objects.get(pk=rule_id))
        except orm.AutomationRule.DoesNotExist:
            return None

    def find_by_trigger_type(self, trigger_type: TriggerType) -> Sequence[AutomationRule]:
        return [
            _rule_orm_to_entity(obj)
            for obj in orm.AutomationRule.objects.filter(trigger_type=trigger_type.value)
        ]

    def find_all_enabled(self) -> Sequence[AutomationRule]:
        return [
            _rule_orm_to_entity(obj)
            for obj in orm.AutomationRule.objects.filter(is_enabled=True)
        ]

    def list_all(self) -> Sequence[AutomationRule]:
        return [_rule_orm_to_entity(obj) for obj in orm.AutomationRule.objects.all()]

    def save(self, rule: AutomationRule) -> None:
        orm.AutomationRule.objects.update_or_create(
            pk=rule.id,
            defaults={
                'name': rule.name,
                'description': rule.description,
                'trigger_type': rule.trigger_type.value,
                'is_enabled': rule.is_enabled,
            },
        )

    def delete(self, rule_id: UUID) -> None:
        orm.AutomationRule.objects.filter(pk=rule_id).delete()


class DjangoAutomationConditionRepository(AutomationConditionRepository):
    def find_by_rule_id(self, rule_id: UUID) -> Sequence[AutomationCondition]:
        return [
            _condition_orm_to_entity(obj)
            for obj in orm.AutomationCondition.objects.filter(rule_id=rule_id)
        ]

    def save(self, condition: AutomationCondition) -> None:
        orm.AutomationCondition.objects.update_or_create(
            pk=condition.id,
            defaults={
                'rule_id': condition.rule_id,
                'field_name': condition.field_name,
                'operator': condition.operator.value,
                'expected_value': condition.expected_value,
                'position': condition.position,
            },
        )

    def delete_by_rule_id(self, rule_id: UUID) -> None:
        orm.AutomationCondition.objects.filter(rule_id=rule_id).delete()


class DjangoAutomationActionRepository(AutomationActionRepository):
    def find_by_rule_id(self, rule_id: UUID) -> Sequence[AutomationAction]:
        return [
            _action_orm_to_entity(obj)
            for obj in orm.AutomationAction.objects.filter(rule_id=rule_id)
        ]

    def save(self, action: AutomationAction) -> None:
        orm.AutomationAction.objects.update_or_create(
            pk=action.id,
            defaults={
                'rule_id': action.rule_id,
                'action_type': action.action_type.value,
                'parameters': action.parameters,
                'position': action.position,
            },
        )

    def delete_by_rule_id(self, rule_id: UUID) -> None:
        orm.AutomationAction.objects.filter(rule_id=rule_id).delete()


class DjangoAutomationRunRepository(AutomationRunRepository):
    def get_by_id(self, run_id: UUID) -> AutomationRun | None:
        try:
            return _run_orm_to_entity(orm.AutomationRun.objects.get(pk=run_id))
        except orm.AutomationRun.DoesNotExist:
            return None

    def find_by_rule_id(self, rule_id: UUID) -> Sequence[AutomationRun]:
        return [
            _run_orm_to_entity(obj)
            for obj in orm.AutomationRun.objects.filter(rule_id=rule_id)
        ]

    def save(self, run: AutomationRun) -> None:
        orm.AutomationRun.objects.update_or_create(
            pk=run.id,
            defaults={
                'rule_id': run.rule_id,
                'trigger_type': run.trigger_type,
                'context_payload': run.context_payload,
                'status': run.status.value,
                'is_dry_run': run.is_dry_run,
                'started_at': run.started_at,
                'completed_at': run.completed_at,
            },
        )


class DjangoAutomationRunLogRepository(AutomationRunLogRepository):
    def find_by_run_id(self, run_id: UUID) -> Sequence[AutomationRunLog]:
        return [
            _log_orm_to_entity(obj)
            for obj in orm.AutomationRunLog.objects.filter(run_id=run_id)
        ]

    def save(self, log: AutomationRunLog) -> None:
        orm.AutomationRunLog.objects.update_or_create(
            pk=log.id,
            defaults={
                'run_id': log.run_id,
                'level': log.level,
                'message': log.message,
                'logged_at': log.logged_at,
            },
        )
