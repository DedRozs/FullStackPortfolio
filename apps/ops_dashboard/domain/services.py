from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from apps.ops_dashboard.domain.model import (
    AlertRule,
    CustomerGrowthSnapshot,
    DashboardAlert,
    RevenueSnapshot,
)
from apps.ops_dashboard.domain.repositories import (
    AlertRuleRepository,
    DashboardAlertRepository,
    MetricRepository,
)
from apps.ops_dashboard.domain.value_objects import (
    AlertSeverity,
    AlertStatus,
    DateRange,
    PeriodDelta,
    ThresholdOperator,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


_OPERATOR_MAP = {
    ThresholdOperator.GT: lambda v, t: v > t,
    ThresholdOperator.LT: lambda v, t: v < t,
    ThresholdOperator.GTE: lambda v, t: v >= t,
    ThresholdOperator.LTE: lambda v, t: v <= t,
    ThresholdOperator.EQ: lambda v, t: v == t,
}


class AlertEvaluationService:
    def __init__(
        self,
        metric_repo: MetricRepository,
        rule_repo: AlertRuleRepository,
        alert_repo: DashboardAlertRepository,
    ) -> None:
        self._metric_repo = metric_repo
        self._rule_repo = rule_repo
        self._alert_repo = alert_repo

    def evaluate_rule(self, rule: AlertRule) -> Optional[DashboardAlert]:
        """Evaluate a single rule against the most recent snapshot.

        Returns a new DashboardAlert if the threshold is crossed and no ACTIVE
        alert already exists for this rule, otherwise returns None.
        """
        from apps.ops_dashboard.domain.value_objects import MetricType

        metric = self._metric_repo.get_by_id(rule.metric_id)
        if metric is None:
            return None

        current_value: Optional[Decimal] = None
        if metric.metric_type == MetricType.REVENUE:
            wide_range = DateRange(
                start_date=datetime(2000, 1, 1).date(),
                end_date=_now().date(),
            )
            snapshots = self._metric_repo.get_revenue_snapshots(rule.metric_id, wide_range)
            if snapshots:
                latest = max(snapshots, key=lambda s: s.recorded_at)
                current_value = latest.amount
        elif metric.metric_type == MetricType.CUSTOMER_GROWTH:
            wide_range = DateRange(
                start_date=datetime(2000, 1, 1).date(),
                end_date=_now().date(),
            )
            growth_snapshots = self._metric_repo.get_growth_snapshots(
                rule.metric_id, wide_range
            )
            if growth_snapshots:
                latest = max(growth_snapshots, key=lambda s: s.recorded_at)
                current_value = Decimal(str(latest.net_customers))

        if current_value is None:
            return None

        compare = _OPERATOR_MAP.get(rule.operator)
        if compare is None or not compare(current_value, rule.threshold_value):
            return None

        existing = self._alert_repo.list_by_rule(rule.id)
        if any(a.status == AlertStatus.ACTIVE for a in existing):
            return None

        alert = DashboardAlert(
            id=uuid.uuid4(),
            rule_id=rule.id,
            metric_id=rule.metric_id,
            triggered_value=current_value,
            threshold_value=rule.threshold_value,
            operator=rule.operator,
            severity=rule.severity,
            status=AlertStatus.ACTIVE,
            acknowledged_at=None,
            acknowledged_by=None,
            resolved_at=None,
            resolved_by=None,
            created_at=_now(),
        )
        self._alert_repo.save(alert)
        return alert

    def evaluate_all_rules(self) -> list[DashboardAlert]:
        triggered: list[DashboardAlert] = []
        for rule in self._rule_repo.list_active():
            alert = self.evaluate_rule(rule)
            if alert is not None:
                triggered.append(alert)
        return triggered


class MetricAggregationService:
    def __init__(self, metric_repo: MetricRepository) -> None:
        self._metric_repo = metric_repo

    def compute_period_delta(
        self,
        metric_id: UUID,
        current_range: DateRange,
        prior_range: DateRange,
    ) -> Optional[PeriodDelta]:
        from apps.ops_dashboard.domain.value_objects import MetricType

        metric = self._metric_repo.get_by_id(metric_id)
        if metric is None:
            return None

        if metric.metric_type == MetricType.REVENUE:
            current_snapshots = self._metric_repo.get_revenue_snapshots(
                metric_id, current_range
            )
            prior_snapshots = self._metric_repo.get_revenue_snapshots(
                metric_id, prior_range
            )
            current_total = sum((s.amount for s in current_snapshots), Decimal("0"))
            prior_total = sum((s.amount for s in prior_snapshots), Decimal("0"))
        elif metric.metric_type == MetricType.CUSTOMER_GROWTH:
            current_snapshots = self._metric_repo.get_growth_snapshots(
                metric_id, current_range
            )
            prior_snapshots = self._metric_repo.get_growth_snapshots(
                metric_id, prior_range
            )
            current_total = Decimal(
                str(sum(s.net_customers for s in current_snapshots))
            )
            prior_total = Decimal(
                str(sum(s.net_customers for s in prior_snapshots))
            )
        else:
            return None

        return PeriodDelta(current_value=current_total, prior_value=prior_total)

    def compute_rolling_average(
        self, metric_id: UUID, date_range: DateRange
    ) -> Optional[Decimal]:
        from apps.ops_dashboard.domain.value_objects import MetricType

        metric = self._metric_repo.get_by_id(metric_id)
        if metric is None:
            return None

        if metric.metric_type == MetricType.REVENUE:
            snapshots = self._metric_repo.get_revenue_snapshots(metric_id, date_range)
            if not snapshots:
                return None
            total = sum((s.amount for s in snapshots), Decimal("0"))
            return total / Decimal(str(len(snapshots)))

        if metric.metric_type == MetricType.CUSTOMER_GROWTH:
            snapshots = self._metric_repo.get_growth_snapshots(metric_id, date_range)
            if not snapshots:
                return None
            total = Decimal(str(sum(s.net_customers for s in snapshots)))
            return total / Decimal(str(len(snapshots)))

        return None
