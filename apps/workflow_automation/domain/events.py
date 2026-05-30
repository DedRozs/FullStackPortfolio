from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AutomationRuleCreated:
    rule_id: UUID
    name: str
    trigger_type: str
    occurred_at: datetime


@dataclass(frozen=True)
class AutomationRuleUpdated:
    rule_id: UUID
    name: str
    occurred_at: datetime


@dataclass(frozen=True)
class AutomationRuleDeleted:
    rule_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class AutomationRuleEnabled:
    rule_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class AutomationRuleDisabled:
    rule_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class AutomationRunCompleted:
    run_id: UUID
    rule_id: UUID
    status: str
    is_dry_run: bool
    occurred_at: datetime
