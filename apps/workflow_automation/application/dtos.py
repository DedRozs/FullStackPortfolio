from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from apps.workflow_automation.domain.value_objects import (
    ActionType,
    ConditionOperator,
    RunStatus,
    TriggerType,
)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CreateRuleCommand:
    name: str
    trigger_type: TriggerType
    description: str | None = None


@dataclass(frozen=True)
class UpdateRuleCommand:
    rule_id: UUID
    name: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class DeleteRuleCommand:
    rule_id: UUID


@dataclass(frozen=True)
class EnableRuleCommand:
    rule_id: UUID


@dataclass(frozen=True)
class DisableRuleCommand:
    rule_id: UUID


@dataclass(frozen=True)
class AddConditionCommand:
    rule_id: UUID
    field_name: str
    operator: ConditionOperator
    expected_value: str
    position: int = 0


@dataclass(frozen=True)
class AddActionCommand:
    rule_id: UUID
    action_type: ActionType
    parameters: dict = field(default_factory=dict)
    position: int = 0


@dataclass(frozen=True)
class ExecuteRuleCommand:
    rule_id: UUID
    trigger_type: str
    context_payload: dict = field(default_factory=dict)


@dataclass(frozen=True)
class DryRunRuleCommand:
    rule_id: UUID
    context_payload: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Queries
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ListRulesQuery:
    trigger_type: TriggerType | None = None
    enabled_only: bool = False


@dataclass(frozen=True)
class GetRuleRunsQuery:
    rule_id: UUID


# ---------------------------------------------------------------------------
# Read DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ConditionDTO:
    id: UUID
    rule_id: UUID
    field_name: str
    operator: str
    expected_value: str
    position: int


@dataclass(frozen=True)
class ActionDTO:
    id: UUID
    rule_id: UUID
    action_type: str
    parameters: dict
    position: int


@dataclass(frozen=True)
class AutomationRuleDTO:
    id: UUID
    name: str
    description: str | None
    trigger_type: str
    is_enabled: bool
    created_at: datetime


@dataclass(frozen=True)
class AutomationRunDTO:
    id: UUID
    rule_id: UUID
    trigger_type: str
    status: str
    is_dry_run: bool
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime


@dataclass(frozen=True)
class RunLogDTO:
    id: UUID
    run_id: UUID
    level: str
    message: str
    logged_at: datetime


@dataclass(frozen=True)
class DryRunResultDTO:
    rule_id: UUID
    conditions_passed: bool
    log_messages: list
    would_execute_actions: list
