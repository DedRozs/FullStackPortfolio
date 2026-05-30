from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from apps.ops_dashboard.domain.value_objects import (
    AlertRuleStatus,
    AlertSeverity,
    AlertStatus,
    AuditAction,
    MetricType,
    ThresholdOperator,
)


@dataclass
class CompanyMetric:
    id: UUID
    name: str
    metric_type: MetricType
    description: str | None
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("CompanyMetric.name must not be blank")


@dataclass
class RevenueSnapshot:
    id: UUID
    metric_id: UUID
    amount: Decimal
    currency: str
    period_start: date
    period_end: date
    recorded_at: datetime

    def __post_init__(self) -> None:
        if self.amount < Decimal("0"):
            raise ValueError("RevenueSnapshot.amount must be >= 0")
        if self.period_end < self.period_start:
            raise ValueError("RevenueSnapshot.period_end must be >= period_start")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("RevenueSnapshot.currency must be a 3-letter ISO 4217 code")


@dataclass
class CustomerGrowthSnapshot:
    id: UUID
    metric_id: UUID
    new_customers: int
    churned_customers: int
    net_customers: int
    period_start: date
    period_end: date
    recorded_at: datetime

    def __post_init__(self) -> None:
        if self.new_customers < 0:
            raise ValueError("CustomerGrowthSnapshot.new_customers must be >= 0")
        if self.churned_customers < 0:
            raise ValueError("CustomerGrowthSnapshot.churned_customers must be >= 0")
        if self.net_customers != self.new_customers - self.churned_customers:
            raise ValueError(
                "CustomerGrowthSnapshot.net_customers must equal new_customers - churned_customers"
            )


@dataclass
class AlertRule:
    id: UUID
    name: str
    metric_id: UUID
    threshold_value: Decimal
    operator: ThresholdOperator
    severity: AlertSeverity
    status: AlertRuleStatus
    last_evaluated_at: datetime | None
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise ValueError("AlertRule.name must not be blank")

    def pause(self, paused_by: UUID) -> "AlertRulePaused":
        from apps.ops_dashboard.domain.events import AlertRulePaused

        if self.status != AlertRuleStatus.ACTIVE:
            raise ValueError("Only ACTIVE alert rules can be paused")
        self.status = AlertRuleStatus.PAUSED
        return AlertRulePaused(
            event_id=_new_uuid(),
            rule_id=self.id,
            paused_by=paused_by,
            occurred_at=_now(),
        )

    def activate(self, activated_by: UUID) -> "AlertRuleActivated":
        from apps.ops_dashboard.domain.events import AlertRuleActivated

        if self.status != AlertRuleStatus.PAUSED:
            raise ValueError("Only PAUSED alert rules can be activated")
        self.status = AlertRuleStatus.ACTIVE
        return AlertRuleActivated(
            event_id=_new_uuid(),
            rule_id=self.id,
            activated_by=activated_by,
            occurred_at=_now(),
        )


@dataclass
class DashboardAlert:
    id: UUID
    rule_id: UUID
    metric_id: UUID
    triggered_value: Decimal
    threshold_value: Decimal
    operator: ThresholdOperator
    severity: AlertSeverity
    status: AlertStatus
    acknowledged_at: datetime | None
    acknowledged_by: UUID | None
    resolved_at: datetime | None
    resolved_by: UUID | None
    created_at: datetime

    def acknowledge(self, acknowledged_by: UUID) -> "AlertAcknowledged":
        from apps.ops_dashboard.domain.events import AlertAcknowledged

        if self.status != AlertStatus.ACTIVE:
            raise ValueError("Only ACTIVE alerts can be acknowledged")
        now = _now()
        self.status = AlertStatus.ACKNOWLEDGED
        self.acknowledged_at = now
        self.acknowledged_by = acknowledged_by
        return AlertAcknowledged(
            event_id=_new_uuid(),
            alert_id=self.id,
            acknowledged_by=acknowledged_by,
            occurred_at=now,
        )

    def resolve(self, resolved_by: UUID) -> "AlertResolved":
        from apps.ops_dashboard.domain.events import AlertResolved

        if self.status not in (AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED):
            raise ValueError("Only ACTIVE or ACKNOWLEDGED alerts can be resolved")
        now = _now()
        self.status = AlertStatus.RESOLVED
        self.resolved_at = now
        self.resolved_by = resolved_by
        return AlertResolved(
            event_id=_new_uuid(),
            alert_id=self.id,
            resolved_by=resolved_by,
            occurred_at=now,
        )


@dataclass
class AuditLogEntry:
    id: UUID
    action: AuditAction
    actor_id: UUID
    resource_id: UUID
    resource_type: str
    detail: str | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Private helpers (no Django dependency)
# ---------------------------------------------------------------------------


def _now() -> datetime:
    from datetime import timezone
    return datetime.now(timezone.utc)


def _new_uuid() -> UUID:
    import uuid
    return uuid.uuid4()
