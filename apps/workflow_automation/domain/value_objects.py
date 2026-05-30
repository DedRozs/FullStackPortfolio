from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class TriggerType(str, Enum):
    DELIVERABLE_APPROVED = "deliverable.approved"
    METRIC_THRESHOLD_CROSSED = "metric.threshold_crossed"
    INVOICE_OVERDUE = "invoice.overdue"
    FILE_UPLOADED = "file.uploaded"


class ConditionOperator(str, Enum):
    GT = "gt"
    LT = "lt"
    EQ = "eq"
    CONTAINS = "contains"
    ASSIGNED_TO = "assigned_to"


class ActionType(str, Enum):
    SEND_EMAIL = "send_email"
    CREATE_ACTIVITY_EVENT = "create_activity_event"
    UPDATE_STATUS = "update_status"
    SEND_SMS = "send_sms"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILURE = "failure"
    DRY_RUN = "dry_run"


@dataclass(frozen=True)
class TriggerContext:
    trigger_type: TriggerType
    source_id: str
    source_type: str
    payload: dict = field(default_factory=dict)
