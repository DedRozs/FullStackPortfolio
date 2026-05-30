from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class MetricSnapshotRecorded:
    event_id: UUID
    metric_id: UUID
    snapshot_id: UUID
    snapshot_type: str
    occurred_at: datetime


@dataclass(frozen=True)
class AlertTriggered:
    event_id: UUID
    alert_id: UUID
    rule_id: UUID
    metric_id: UUID
    triggered_value: object
    threshold_value: object
    severity: str
    occurred_at: datetime


@dataclass(frozen=True)
class AlertAcknowledged:
    event_id: UUID
    alert_id: UUID
    acknowledged_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class AlertResolved:
    event_id: UUID
    alert_id: UUID
    resolved_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class AlertRulePaused:
    event_id: UUID
    rule_id: UUID
    paused_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class AlertRuleActivated:
    event_id: UUID
    rule_id: UUID
    activated_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class MetricImportCompleted:
    event_id: UUID
    import_id: str
    metric_id: UUID
    rows_imported: int
    occurred_at: datetime


@dataclass(frozen=True)
class MetricImportFailed:
    event_id: UUID
    import_id: str
    reason: str
    occurred_at: datetime
