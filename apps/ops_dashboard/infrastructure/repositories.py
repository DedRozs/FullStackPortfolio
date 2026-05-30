from __future__ import annotations

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Sequence
from uuid import UUID

from apps.ops_dashboard.domain.model import (
    AlertRule,
    AuditLogEntry,
    CompanyMetric,
    CustomerGrowthSnapshot,
    DashboardAlert,
    RevenueSnapshot,
)
from apps.ops_dashboard.domain.repositories import (
    AlertRuleRepository,
    AuditLogRepository,
    DashboardAlertRepository,
    MetricRepository,
)
from apps.ops_dashboard.domain.value_objects import (
    AlertRuleStatus,
    AlertSeverity,
    AlertStatus,
    AuditAction,
    DateRange,
    MetricType,
    ThresholdOperator,
)
from apps.ops_dashboard import models as orm

logger = logging.getLogger(__name__)

_UTC = timezone.utc


def _ensure_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=_UTC)
    return dt


# ---------------------------------------------------------------------------
# Private mappers
# ---------------------------------------------------------------------------


def _metric_orm_to_entity(obj: orm.CompanyMetric) -> CompanyMetric:
    return CompanyMetric(
        id=obj.id,
        name=obj.name,
        metric_type=MetricType(obj.metric_type),
        description=obj.description,
        created_at=_ensure_aware(obj.created_at),
    )


def _revenue_orm_to_entity(obj: orm.RevenueSnapshot) -> RevenueSnapshot:
    return RevenueSnapshot(
        id=obj.id,
        metric_id=obj.metric_id,
        amount=obj.amount,
        currency=obj.currency,
        period_start=obj.period_start,
        period_end=obj.period_end,
        recorded_at=_ensure_aware(obj.recorded_at),
    )


def _growth_orm_to_entity(obj: orm.CustomerGrowthSnapshot) -> CustomerGrowthSnapshot:
    return CustomerGrowthSnapshot(
        id=obj.id,
        metric_id=obj.metric_id,
        new_customers=obj.new_customers,
        churned_customers=obj.churned_customers,
        net_customers=obj.net_customers,
        period_start=obj.period_start,
        period_end=obj.period_end,
        recorded_at=_ensure_aware(obj.recorded_at),
    )


def _rule_orm_to_entity(obj: orm.AlertRule) -> AlertRule:
    return AlertRule(
        id=obj.id,
        name=obj.name,
        metric_id=obj.metric_id,
        threshold_value=obj.threshold_value,
        operator=ThresholdOperator(obj.operator),
        severity=AlertSeverity(obj.severity),
        status=AlertRuleStatus(obj.status),
        last_evaluated_at=_ensure_aware(obj.last_evaluated_at) if obj.last_evaluated_at else None,
        created_at=_ensure_aware(obj.created_at),
    )


def _alert_orm_to_entity(obj: orm.DashboardAlert) -> DashboardAlert:
    return DashboardAlert(
        id=obj.id,
        rule_id=obj.rule_id,
        metric_id=obj.metric_id,
        triggered_value=obj.triggered_value,
        threshold_value=obj.threshold_value,
        operator=ThresholdOperator(obj.operator),
        severity=AlertSeverity(obj.severity),
        status=AlertStatus(obj.status),
        acknowledged_at=_ensure_aware(obj.acknowledged_at) if obj.acknowledged_at else None,
        acknowledged_by=obj.acknowledged_by_id,
        resolved_at=_ensure_aware(obj.resolved_at) if obj.resolved_at else None,
        resolved_by=obj.resolved_by_id,
        created_at=_ensure_aware(obj.created_at),
    )


def _audit_orm_to_entity(obj: orm.AuditLogEntry) -> AuditLogEntry:
    return AuditLogEntry(
        id=obj.id,
        action=AuditAction(obj.action),
        actor_id=obj.actor_id,
        resource_id=obj.resource_id,
        resource_type=obj.resource_type,
        detail=obj.detail,
        created_at=_ensure_aware(obj.created_at),
    )


# ---------------------------------------------------------------------------
# Repository implementations
# ---------------------------------------------------------------------------


class DjangoMetricRepository(MetricRepository):
    def get_by_id(self, metric_id: UUID) -> CompanyMetric | None:
        try:
            return _metric_orm_to_entity(orm.CompanyMetric.objects.get(pk=metric_id))
        except orm.CompanyMetric.DoesNotExist:
            return None

    def list_all(self) -> Sequence[CompanyMetric]:
        return [_metric_orm_to_entity(obj) for obj in orm.CompanyMetric.objects.all()]

    def save(self, metric: CompanyMetric) -> None:
        orm.CompanyMetric.objects.update_or_create(
            pk=metric.id,
            defaults={
                'name': metric.name,
                'metric_type': metric.metric_type.value,
                'description': metric.description,
            },
        )

    def get_revenue_snapshots(
        self, metric_id: UUID, date_range: DateRange
    ) -> list[RevenueSnapshot]:
        qs = orm.RevenueSnapshot.objects.filter(
            metric_id=metric_id,
            period_start__lte=date_range.end_date,
            period_end__gte=date_range.start_date,
        )
        return [_revenue_orm_to_entity(obj) for obj in qs]

    def get_growth_snapshots(
        self, metric_id: UUID, date_range: DateRange
    ) -> list[CustomerGrowthSnapshot]:
        qs = orm.CustomerGrowthSnapshot.objects.filter(
            metric_id=metric_id,
            period_start__lte=date_range.end_date,
            period_end__gte=date_range.start_date,
        )
        return [_growth_orm_to_entity(obj) for obj in qs]

    def save_revenue_snapshot(self, snapshot: RevenueSnapshot) -> None:
        orm.RevenueSnapshot.objects.update_or_create(
            pk=snapshot.id,
            defaults={
                'metric_id': snapshot.metric_id,
                'amount': snapshot.amount,
                'currency': snapshot.currency,
                'period_start': snapshot.period_start,
                'period_end': snapshot.period_end,
                'recorded_at': snapshot.recorded_at,
            },
        )

    def save_growth_snapshot(self, snapshot: CustomerGrowthSnapshot) -> None:
        orm.CustomerGrowthSnapshot.objects.update_or_create(
            pk=snapshot.id,
            defaults={
                'metric_id': snapshot.metric_id,
                'new_customers': snapshot.new_customers,
                'churned_customers': snapshot.churned_customers,
                'net_customers': snapshot.net_customers,
                'period_start': snapshot.period_start,
                'period_end': snapshot.period_end,
                'recorded_at': snapshot.recorded_at,
            },
        )


class DjangoAlertRuleRepository(AlertRuleRepository):
    def get_by_id(self, rule_id: UUID) -> AlertRule | None:
        try:
            return _rule_orm_to_entity(orm.AlertRule.objects.get(pk=rule_id))
        except orm.AlertRule.DoesNotExist:
            return None

    def list_active(self) -> Sequence[AlertRule]:
        return [
            _rule_orm_to_entity(obj)
            for obj in orm.AlertRule.objects.filter(status=orm.AlertRule.STATUS_ACTIVE)
        ]

    def list_all(self) -> Sequence[AlertRule]:
        return [_rule_orm_to_entity(obj) for obj in orm.AlertRule.objects.all()]

    def save(self, rule: AlertRule) -> None:
        orm.AlertRule.objects.update_or_create(
            pk=rule.id,
            defaults={
                'name': rule.name,
                'metric_id': rule.metric_id,
                'threshold_value': rule.threshold_value,
                'operator': rule.operator.value,
                'severity': rule.severity.value,
                'status': rule.status.value,
                'last_evaluated_at': rule.last_evaluated_at,
            },
        )

    def delete(self, rule_id: UUID) -> None:
        orm.AlertRule.objects.filter(pk=rule_id).delete()


class DjangoDashboardAlertRepository(DashboardAlertRepository):
    def get_by_id(self, alert_id: UUID) -> DashboardAlert | None:
        try:
            return _alert_orm_to_entity(orm.DashboardAlert.objects.get(pk=alert_id))
        except orm.DashboardAlert.DoesNotExist:
            return None

    def list_active(self) -> Sequence[DashboardAlert]:
        return [
            _alert_orm_to_entity(obj)
            for obj in orm.DashboardAlert.objects.filter(status=orm.DashboardAlert.STATUS_ACTIVE)
        ]

    def list_by_rule(self, rule_id: UUID) -> Sequence[DashboardAlert]:
        return [
            _alert_orm_to_entity(obj)
            for obj in orm.DashboardAlert.objects.filter(rule_id=rule_id)
        ]

    def save(self, alert: DashboardAlert) -> None:
        orm.DashboardAlert.objects.update_or_create(
            pk=alert.id,
            defaults={
                'rule_id': alert.rule_id,
                'metric_id': alert.metric_id,
                'triggered_value': alert.triggered_value,
                'threshold_value': alert.threshold_value,
                'operator': alert.operator.value,
                'severity': alert.severity.value,
                'status': alert.status.value,
                'acknowledged_at': alert.acknowledged_at,
                'acknowledged_by_id': alert.acknowledged_by,
                'resolved_at': alert.resolved_at,
                'resolved_by_id': alert.resolved_by,
            },
        )


class DjangoAuditLogRepository(AuditLogRepository):
    def append(self, entry: AuditLogEntry) -> None:
        orm.AuditLogEntry.objects.create(
            id=entry.id,
            action=entry.action.value,
            actor_id=entry.actor_id,
            resource_id=entry.resource_id,
            resource_type=entry.resource_type,
            detail=entry.detail,
        )

    def list_recent(self, limit: int) -> Sequence[AuditLogEntry]:
        return [
            _audit_orm_to_entity(obj)
            for obj in orm.AuditLogEntry.objects.all()[:limit]
        ]

    def list_by_resource(self, resource_id: UUID, limit: int) -> Sequence[AuditLogEntry]:
        return [
            _audit_orm_to_entity(obj)
            for obj in orm.AuditLogEntry.objects.filter(resource_id=resource_id)[:limit]
        ]
