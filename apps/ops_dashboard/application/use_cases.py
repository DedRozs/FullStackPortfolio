from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from apps.ops_dashboard.application.dtos import (
    AuditLogEntryDTO,
    AlertRuleDTO,
    CreateCompanyMetricCommand,
    DashboardAlertDTO,
    GrowthSnapshotDTO,
    MetricDTO,
    MetricSeriesDTO,
    RevenueSnapshotDTO,
    AcknowledgeAlertCommand,
    ActivateAlertRuleCommand,
    CreateAlertRuleCommand,
    DeleteAlertRuleCommand,
    GetMetricSeriesQuery,
    ListActiveAlertsQuery,
    ListAlertRulesQuery,
    ListAuditLogQuery,
    ListMetricsQuery,
    PauseAlertRuleCommand,
    RecordGrowthSnapshotCommand,
    RecordRevenueSnapshotCommand,
    ResolveAlertCommand,
    UpdateAlertRuleCommand,
    UpdateCompanyMetricCommand,
)
from apps.ops_dashboard.domain.model import (
    AlertRule,
    AuditLogEntry,
    CompanyMetric,
    CustomerGrowthSnapshot,
    RevenueSnapshot,
)
from apps.ops_dashboard.domain.repositories import (
    AlertRuleRepository,
    AuditLogRepository,
    DashboardAlertRepository,
    MetricRepository,
)
from apps.ops_dashboard.domain.services import MetricAggregationService
from apps.ops_dashboard.domain.value_objects import (
    AlertRuleStatus,
    AlertSeverity,
    AuditAction,
    DateRange,
    ThresholdOperator,
)

logger = logging.getLogger(__name__)

_UTC = timezone.utc


def _now() -> datetime:
    return datetime.now(_UTC)


# ---------------------------------------------------------------------------
# Private mappers
# ---------------------------------------------------------------------------


def _metric_to_dto(m) -> MetricDTO:
    return MetricDTO(
        id=m.id,
        name=m.name,
        metric_type=m.metric_type.value,
        description=m.description,
        created_at=m.created_at,
    )


def _revenue_snapshot_to_dto(s: RevenueSnapshot) -> RevenueSnapshotDTO:
    return RevenueSnapshotDTO(
        id=s.id,
        metric_id=s.metric_id,
        amount=s.amount,
        currency=s.currency,
        period_start=s.period_start,
        period_end=s.period_end,
        recorded_at=s.recorded_at,
    )


def _growth_snapshot_to_dto(s: CustomerGrowthSnapshot) -> GrowthSnapshotDTO:
    return GrowthSnapshotDTO(
        id=s.id,
        metric_id=s.metric_id,
        new_customers=s.new_customers,
        churned_customers=s.churned_customers,
        net_customers=s.net_customers,
        period_start=s.period_start,
        period_end=s.period_end,
        recorded_at=s.recorded_at,
    )


def _rule_to_dto(r: AlertRule) -> AlertRuleDTO:
    return AlertRuleDTO(
        id=r.id,
        name=r.name,
        metric_id=r.metric_id,
        threshold_value=r.threshold_value,
        operator=r.operator.value,
        severity=r.severity.value,
        status=r.status.value,
        last_evaluated_at=r.last_evaluated_at,
        created_at=r.created_at,
    )


def _alert_to_dto(a) -> DashboardAlertDTO:
    return DashboardAlertDTO(
        id=a.id,
        rule_id=a.rule_id,
        metric_id=a.metric_id,
        triggered_value=a.triggered_value,
        threshold_value=a.threshold_value,
        operator=a.operator.value,
        severity=a.severity.value,
        status=a.status.value,
        acknowledged_at=a.acknowledged_at,
        acknowledged_by=a.acknowledged_by,
        resolved_at=a.resolved_at,
        resolved_by=a.resolved_by,
        created_at=a.created_at,
    )


def _audit_to_dto(e: AuditLogEntry) -> AuditLogEntryDTO:
    return AuditLogEntryDTO(
        id=e.id,
        action=e.action.value,
        actor_id=e.actor_id,
        resource_id=e.resource_id,
        resource_type=e.resource_type,
        detail=e.detail,
        created_at=e.created_at,
    )


def _log(
    audit_repo: AuditLogRepository,
    action: AuditAction,
    actor_id,
    resource_id,
    resource_type: str,
    detail: str | None = None,
) -> None:
    entry = AuditLogEntry(
        id=uuid.uuid4(),
        action=action,
        actor_id=actor_id,
        resource_id=resource_id,
        resource_type=resource_type,
        detail=detail,
        created_at=_now(),
    )
    audit_repo.append(entry)


# ---------------------------------------------------------------------------
# Use cases
# ---------------------------------------------------------------------------


class CreateCompanyMetric:
    def __init__(
        self,
        metric_repo: MetricRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self._metric_repo = metric_repo
        self._audit_repo = audit_repo

    def execute(self, cmd: CreateCompanyMetricCommand) -> MetricDTO:
        from apps.ops_dashboard.domain.value_objects import MetricType as _MetricType

        metric = CompanyMetric(
            id=uuid.uuid4(),
            name=cmd.name,
            metric_type=_MetricType(cmd.metric_type),
            description=cmd.description,
            created_at=_now(),
        )
        self._metric_repo.save(metric)
        _log(
            self._audit_repo,
            AuditAction.METRIC_CREATED,
            cmd.created_by_id,
            metric.id,
            "CompanyMetric",
        )
        return _metric_to_dto(metric)


class UpdateCompanyMetric:
    def __init__(
        self,
        metric_repo: MetricRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self._metric_repo = metric_repo
        self._audit_repo = audit_repo

    def execute(self, cmd: UpdateCompanyMetricCommand) -> MetricDTO:
        metric = self._metric_repo.get_by_id(cmd.metric_id)
        if metric is None:
            raise ValueError(f"Metric {cmd.metric_id} not found")
        metric.name = cmd.name
        metric.description = cmd.description
        self._metric_repo.save(metric)
        _log(
            self._audit_repo,
            AuditAction.METRIC_UPDATED,
            cmd.updated_by_id,
            metric.id,
            "CompanyMetric",
        )
        return _metric_to_dto(metric)


class RecordRevenueSnapshot:
    def __init__(
        self,
        metric_repo: MetricRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self._metric_repo = metric_repo
        self._audit_repo = audit_repo

    def execute(self, cmd: RecordRevenueSnapshotCommand) -> RevenueSnapshotDTO:
        from apps.ops_dashboard.domain.value_objects import MetricType

        metric = self._metric_repo.get_by_id(cmd.metric_id)
        if metric is None:
            raise ValueError(f"Metric {cmd.metric_id} not found")
        if metric.metric_type != MetricType.REVENUE:
            raise ValueError("Metric is not of type REVENUE")

        snapshot = RevenueSnapshot(
            id=uuid.uuid4(),
            metric_id=cmd.metric_id,
            amount=cmd.amount,
            currency=cmd.currency,
            period_start=cmd.period_start,
            period_end=cmd.period_end,
            recorded_at=_now(),
        )
        self._metric_repo.save_revenue_snapshot(snapshot)
        _log(
            self._audit_repo,
            AuditAction.METRIC_CREATED,
            cmd.recorded_by_id,
            snapshot.id,
            "RevenueSnapshot",
        )
        return _revenue_snapshot_to_dto(snapshot)


class RecordGrowthSnapshot:
    def __init__(
        self,
        metric_repo: MetricRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self._metric_repo = metric_repo
        self._audit_repo = audit_repo

    def execute(self, cmd: RecordGrowthSnapshotCommand) -> GrowthSnapshotDTO:
        from apps.ops_dashboard.domain.value_objects import MetricType

        metric = self._metric_repo.get_by_id(cmd.metric_id)
        if metric is None:
            raise ValueError(f"Metric {cmd.metric_id} not found")
        if metric.metric_type != MetricType.CUSTOMER_GROWTH:
            raise ValueError("Metric is not of type CUSTOMER_GROWTH")

        snapshot = CustomerGrowthSnapshot(
            id=uuid.uuid4(),
            metric_id=cmd.metric_id,
            new_customers=cmd.new_customers,
            churned_customers=cmd.churned_customers,
            net_customers=cmd.new_customers - cmd.churned_customers,
            period_start=cmd.period_start,
            period_end=cmd.period_end,
            recorded_at=_now(),
        )
        self._metric_repo.save_growth_snapshot(snapshot)
        _log(
            self._audit_repo,
            AuditAction.METRIC_CREATED,
            cmd.recorded_by_id,
            snapshot.id,
            "CustomerGrowthSnapshot",
        )
        return _growth_snapshot_to_dto(snapshot)


class CreateAlertRule:
    def __init__(
        self,
        rule_repo: AlertRuleRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self._rule_repo = rule_repo
        self._audit_repo = audit_repo

    def execute(self, cmd: CreateAlertRuleCommand) -> AlertRuleDTO:
        existing = self._rule_repo.list_all()
        for r in existing:
            if r.name == cmd.name and r.metric_id == cmd.metric_id:
                raise ValueError(
                    f"Alert rule named '{cmd.name}' already exists for this metric"
                )

        rule = AlertRule(
            id=uuid.uuid4(),
            name=cmd.name,
            metric_id=cmd.metric_id,
            threshold_value=cmd.threshold_value,
            operator=ThresholdOperator(cmd.operator),
            severity=AlertSeverity(cmd.severity),
            status=AlertRuleStatus.ACTIVE,
            last_evaluated_at=None,
            created_at=_now(),
        )
        self._rule_repo.save(rule)
        _log(
            self._audit_repo,
            AuditAction.RULE_CREATED,
            cmd.created_by_id,
            rule.id,
            "AlertRule",
        )
        return _rule_to_dto(rule)


class UpdateAlertRule:
    def __init__(
        self,
        rule_repo: AlertRuleRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self._rule_repo = rule_repo
        self._audit_repo = audit_repo

    def execute(self, cmd: UpdateAlertRuleCommand) -> AlertRuleDTO:
        rule = self._rule_repo.get_by_id(cmd.rule_id)
        if rule is None:
            raise ValueError(f"AlertRule {cmd.rule_id} not found")
        rule.name = cmd.name
        rule.threshold_value = cmd.threshold_value
        rule.operator = ThresholdOperator(cmd.operator)
        rule.severity = AlertSeverity(cmd.severity)
        self._rule_repo.save(rule)
        _log(
            self._audit_repo,
            AuditAction.METRIC_UPDATED,
            cmd.updated_by_id,
            rule.id,
            "AlertRule",
        )
        return _rule_to_dto(rule)


class PauseAlertRule:
    def __init__(
        self,
        rule_repo: AlertRuleRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self._rule_repo = rule_repo
        self._audit_repo = audit_repo

    def execute(self, cmd: PauseAlertRuleCommand) -> AlertRuleDTO:
        rule = self._rule_repo.get_by_id(cmd.rule_id)
        if rule is None:
            raise ValueError(f"AlertRule {cmd.rule_id} not found")
        rule.pause(cmd.paused_by_id)
        self._rule_repo.save(rule)
        _log(
            self._audit_repo,
            AuditAction.RULE_PAUSED,
            cmd.paused_by_id,
            rule.id,
            "AlertRule",
        )
        return _rule_to_dto(rule)


class ActivateAlertRule:
    def __init__(
        self,
        rule_repo: AlertRuleRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self._rule_repo = rule_repo
        self._audit_repo = audit_repo

    def execute(self, cmd: ActivateAlertRuleCommand) -> AlertRuleDTO:
        rule = self._rule_repo.get_by_id(cmd.rule_id)
        if rule is None:
            raise ValueError(f"AlertRule {cmd.rule_id} not found")
        rule.activate(cmd.activated_by_id)
        self._rule_repo.save(rule)
        _log(
            self._audit_repo,
            AuditAction.RULE_ACTIVATED,
            cmd.activated_by_id,
            rule.id,
            "AlertRule",
        )
        return _rule_to_dto(rule)


class DeleteAlertRule:
    def __init__(
        self,
        rule_repo: AlertRuleRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self._rule_repo = rule_repo
        self._audit_repo = audit_repo

    def execute(self, cmd: DeleteAlertRuleCommand) -> None:
        rule = self._rule_repo.get_by_id(cmd.rule_id)
        if rule is None:
            raise ValueError(f"AlertRule {cmd.rule_id} not found")
        self._rule_repo.delete(cmd.rule_id)
        _log(
            self._audit_repo,
            AuditAction.METRIC_UPDATED,
            cmd.deleted_by_id,
            cmd.rule_id,
            "AlertRule",
            "rule deleted",
        )


class AcknowledgeAlert:
    def __init__(
        self,
        alert_repo: DashboardAlertRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self._alert_repo = alert_repo
        self._audit_repo = audit_repo

    def execute(self, cmd: AcknowledgeAlertCommand) -> DashboardAlertDTO:
        alert = self._alert_repo.get_by_id(cmd.alert_id)
        if alert is None:
            raise ValueError(f"DashboardAlert {cmd.alert_id} not found")
        alert.acknowledge(cmd.acknowledged_by_id)
        self._alert_repo.save(alert)
        _log(
            self._audit_repo,
            AuditAction.ALERT_ACKNOWLEDGED,
            cmd.acknowledged_by_id,
            alert.id,
            "DashboardAlert",
        )
        return _alert_to_dto(alert)


class ResolveAlert:
    def __init__(
        self,
        alert_repo: DashboardAlertRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self._alert_repo = alert_repo
        self._audit_repo = audit_repo

    def execute(self, cmd: ResolveAlertCommand) -> DashboardAlertDTO:
        alert = self._alert_repo.get_by_id(cmd.alert_id)
        if alert is None:
            raise ValueError(f"DashboardAlert {cmd.alert_id} not found")
        alert.resolve(cmd.resolved_by_id)
        self._alert_repo.save(alert)
        _log(
            self._audit_repo,
            AuditAction.ALERT_RESOLVED,
            cmd.resolved_by_id,
            alert.id,
            "DashboardAlert",
        )
        return _alert_to_dto(alert)


class GetMetricSeries:
    def __init__(
        self,
        metric_repo: MetricRepository,
        aggregation_service: MetricAggregationService,
    ) -> None:
        self._metric_repo = metric_repo
        self._aggregation_service = aggregation_service

    def execute(self, query: GetMetricSeriesQuery) -> MetricSeriesDTO:
        metric = self._metric_repo.get_by_id(query.metric_id)
        if metric is None:
            raise ValueError(f"Metric {query.metric_id} not found")

        date_range = DateRange(start_date=query.start_date, end_date=query.end_date)
        revenue_snapshots = self._metric_repo.get_revenue_snapshots(
            query.metric_id, date_range
        )
        growth_snapshots = self._metric_repo.get_growth_snapshots(
            query.metric_id, date_range
        )
        return MetricSeriesDTO(
            metric=_metric_to_dto(metric),
            revenue_snapshots=[_revenue_snapshot_to_dto(s) for s in revenue_snapshots],
            growth_snapshots=[_growth_snapshot_to_dto(s) for s in growth_snapshots],
            delta=None,
        )


class ListMetrics:
    def __init__(self, metric_repo: MetricRepository) -> None:
        self._metric_repo = metric_repo

    def execute(self, query: ListMetricsQuery) -> list[MetricDTO]:
        return [_metric_to_dto(m) for m in self._metric_repo.list_all()]


class ListActiveAlerts:
    def __init__(self, alert_repo: DashboardAlertRepository) -> None:
        self._alert_repo = alert_repo

    def execute(self, query: ListActiveAlertsQuery) -> list[DashboardAlertDTO]:
        return [_alert_to_dto(a) for a in self._alert_repo.list_active()]


class ListAlertRules:
    def __init__(self, rule_repo: AlertRuleRepository) -> None:
        self._rule_repo = rule_repo

    def execute(self, query: ListAlertRulesQuery) -> list[AlertRuleDTO]:
        return [_rule_to_dto(r) for r in self._rule_repo.list_all()]


class ListAuditLog:
    def __init__(self, audit_repo: AuditLogRepository) -> None:
        self._audit_repo = audit_repo

    def execute(self, query: ListAuditLogQuery) -> list[AuditLogEntryDTO]:
        return [_audit_to_dto(e) for e in self._audit_repo.list_recent(query.limit)]
