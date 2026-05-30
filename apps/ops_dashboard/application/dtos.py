from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID


# ---------------------------------------------------------------------------
# Command DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RecordRevenueSnapshotCommand:
    metric_id: UUID
    amount: Decimal
    currency: str
    period_start: date
    period_end: date
    recorded_by_id: UUID


@dataclass(frozen=True)
class RecordGrowthSnapshotCommand:
    metric_id: UUID
    new_customers: int
    churned_customers: int
    period_start: date
    period_end: date
    recorded_by_id: UUID


@dataclass(frozen=True)
class CreateCompanyMetricCommand:
    name: str
    metric_type: str
    description: Optional[str]
    created_by_id: UUID


@dataclass(frozen=True)
class UpdateCompanyMetricCommand:
    metric_id: UUID
    name: str
    description: Optional[str]
    updated_by_id: UUID


@dataclass(frozen=True)
class CreateAlertRuleCommand:
    name: str
    metric_id: UUID
    threshold_value: Decimal
    operator: str
    severity: str
    created_by_id: UUID


@dataclass(frozen=True)
class UpdateAlertRuleCommand:
    rule_id: UUID
    name: str
    threshold_value: Decimal
    operator: str
    severity: str
    updated_by_id: UUID


@dataclass(frozen=True)
class PauseAlertRuleCommand:
    rule_id: UUID
    paused_by_id: UUID


@dataclass(frozen=True)
class ActivateAlertRuleCommand:
    rule_id: UUID
    activated_by_id: UUID


@dataclass(frozen=True)
class DeleteAlertRuleCommand:
    rule_id: UUID
    deleted_by_id: UUID


@dataclass(frozen=True)
class AcknowledgeAlertCommand:
    alert_id: UUID
    acknowledged_by_id: UUID


@dataclass(frozen=True)
class ResolveAlertCommand:
    alert_id: UUID
    resolved_by_id: UUID


# ---------------------------------------------------------------------------
# Query DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GetMetricSeriesQuery:
    metric_id: UUID
    start_date: date
    end_date: date


@dataclass(frozen=True)
class GetPeriodDeltaQuery:
    metric_id: UUID
    current_start: date
    current_end: date
    prior_start: date
    prior_end: date


@dataclass(frozen=True)
class ListMetricsQuery:
    pass


@dataclass(frozen=True)
class ListActiveAlertsQuery:
    pass


@dataclass(frozen=True)
class ListAlertRulesQuery:
    pass


@dataclass(frozen=True)
class ListAuditLogQuery:
    limit: int = 50


# ---------------------------------------------------------------------------
# Output DTOs
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MetricDTO:
    id: UUID
    name: str
    metric_type: str
    description: Optional[str]
    created_at: datetime


@dataclass(frozen=True)
class RevenueSnapshotDTO:
    id: UUID
    metric_id: UUID
    amount: Decimal
    currency: str
    period_start: date
    period_end: date
    recorded_at: datetime


@dataclass(frozen=True)
class GrowthSnapshotDTO:
    id: UUID
    metric_id: UUID
    new_customers: int
    churned_customers: int
    net_customers: int
    period_start: date
    period_end: date
    recorded_at: datetime


@dataclass(frozen=True)
class AlertRuleDTO:
    id: UUID
    name: str
    metric_id: UUID
    threshold_value: Decimal
    operator: str
    severity: str
    status: str
    last_evaluated_at: Optional[datetime]
    created_at: datetime


@dataclass(frozen=True)
class DashboardAlertDTO:
    id: UUID
    rule_id: UUID
    metric_id: UUID
    triggered_value: Decimal
    threshold_value: Decimal
    operator: str
    severity: str
    status: str
    acknowledged_at: Optional[datetime]
    acknowledged_by: Optional[UUID]
    resolved_at: Optional[datetime]
    resolved_by: Optional[UUID]
    created_at: datetime


@dataclass(frozen=True)
class AuditLogEntryDTO:
    id: UUID
    action: str
    actor_id: UUID
    resource_id: UUID
    resource_type: str
    detail: Optional[str]
    created_at: datetime


@dataclass(frozen=True)
class MetricSeriesDTO:
    metric: MetricDTO
    revenue_snapshots: list[RevenueSnapshotDTO]
    growth_snapshots: list[GrowthSnapshotDTO]
    delta: Optional[object]
