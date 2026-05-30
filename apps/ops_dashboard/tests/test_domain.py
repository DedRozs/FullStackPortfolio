"""
Unit tests for apps.ops_dashboard domain layer.

Tests cover:
- Value object invariants (DateRange, PeriodDelta, enums)
- Entity invariants (CompanyMetric, RevenueSnapshot, CustomerGrowthSnapshot)
- AlertRule state transitions (pause / activate)
- DashboardAlert state transitions (acknowledge / resolve)
- AuditLogEntry immutability (no state methods)
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from apps.ops_dashboard.domain.model import (
    AlertRule,
    AuditLogEntry,
    CompanyMetric,
    CustomerGrowthSnapshot,
    DashboardAlert,
    RevenueSnapshot,
)
from apps.ops_dashboard.domain.value_objects import (
    AlertRuleStatus,
    AlertSeverity,
    AlertStatus,
    AuditAction,
    DateRange,
    MetricType,
    PeriodDelta,
    ThresholdOperator,
)

_UTC = timezone.utc
_NOW = datetime(2025, 6, 1, 12, 0, 0, tzinfo=_UTC)


def _uid() -> uuid.UUID:
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# Helper factories
# ---------------------------------------------------------------------------


def _metric(name: str = 'Monthly Revenue', metric_type: MetricType = MetricType.REVENUE) -> CompanyMetric:
    return CompanyMetric(
        id=_uid(),
        name=name,
        metric_type=metric_type,
        description=None,
        created_at=_NOW,
    )


def _revenue_snapshot(**kwargs) -> RevenueSnapshot:
    defaults = dict(
        id=_uid(),
        metric_id=_uid(),
        amount=Decimal('10000.00'),
        currency='USD',
        period_start=date(2025, 1, 1),
        period_end=date(2025, 1, 31),
        recorded_at=_NOW,
    )
    defaults.update(kwargs)
    return RevenueSnapshot(**defaults)


def _growth_snapshot(**kwargs) -> CustomerGrowthSnapshot:
    defaults = dict(
        id=_uid(),
        metric_id=_uid(),
        new_customers=10,
        churned_customers=2,
        net_customers=8,
        period_start=date(2025, 1, 1),
        period_end=date(2025, 1, 31),
        recorded_at=_NOW,
    )
    defaults.update(kwargs)
    return CustomerGrowthSnapshot(**defaults)


def _alert_rule(status: AlertRuleStatus = AlertRuleStatus.ACTIVE) -> AlertRule:
    return AlertRule(
        id=_uid(),
        name='Revenue Drop',
        metric_id=_uid(),
        threshold_value=Decimal('50000.00'),
        operator=ThresholdOperator.LT,
        severity=AlertSeverity.CRITICAL,
        status=status,
        last_evaluated_at=None,
        created_at=_NOW,
    )


def _dashboard_alert(status: AlertStatus = AlertStatus.ACTIVE) -> DashboardAlert:
    return DashboardAlert(
        id=_uid(),
        rule_id=_uid(),
        metric_id=_uid(),
        triggered_value=Decimal('45000.00'),
        threshold_value=Decimal('50000.00'),
        operator=ThresholdOperator.LT,
        severity=AlertSeverity.CRITICAL,
        status=status,
        acknowledged_at=None,
        acknowledged_by=None,
        resolved_at=None,
        resolved_by=None,
        created_at=_NOW,
    )


# ---------------------------------------------------------------------------
# DateRange
# ---------------------------------------------------------------------------


class TestDateRange:
    def test_valid_range_created(self) -> None:
        dr = DateRange(start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        assert dr.start_date == date(2025, 1, 1)
        assert dr.end_date == date(2025, 1, 31)

    def test_same_day_range_is_valid(self) -> None:
        dr = DateRange(start_date=date(2025, 6, 1), end_date=date(2025, 6, 1))
        assert dr.start_date == dr.end_date

    def test_end_before_start_raises(self) -> None:
        with pytest.raises(ValueError, match='end_date'):
            DateRange(start_date=date(2025, 1, 31), end_date=date(2025, 1, 1))

    def test_contains_inside(self) -> None:
        dr = DateRange(start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        assert dr.contains(date(2025, 1, 15)) is True

    def test_contains_boundary_start(self) -> None:
        dr = DateRange(start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        assert dr.contains(date(2025, 1, 1)) is True

    def test_contains_boundary_end(self) -> None:
        dr = DateRange(start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        assert dr.contains(date(2025, 1, 31)) is True

    def test_contains_outside(self) -> None:
        dr = DateRange(start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        assert dr.contains(date(2025, 2, 1)) is False


# ---------------------------------------------------------------------------
# PeriodDelta
# ---------------------------------------------------------------------------


class TestPeriodDelta:
    def test_delta_positive(self) -> None:
        pd = PeriodDelta(current_value=Decimal('120000'), prior_value=Decimal('100000'))
        assert pd.delta == Decimal('20000')

    def test_delta_negative(self) -> None:
        pd = PeriodDelta(current_value=Decimal('80000'), prior_value=Decimal('100000'))
        assert pd.delta == Decimal('-20000')

    def test_percentage_change_positive(self) -> None:
        pd = PeriodDelta(current_value=Decimal('110000'), prior_value=Decimal('100000'))
        assert pd.percentage_change == pytest.approx(10.0)

    def test_percentage_change_zero_prior_returns_none(self) -> None:
        pd = PeriodDelta(current_value=Decimal('10000'), prior_value=Decimal('0'))
        assert pd.percentage_change is None


# ---------------------------------------------------------------------------
# ThresholdOperator enum
# ---------------------------------------------------------------------------


class TestThresholdOperatorEnum:
    def test_all_values_are_string_subclass(self) -> None:
        for op in ThresholdOperator:
            assert isinstance(op, str)

    def test_gt_value(self) -> None:
        assert ThresholdOperator.GT == 'gt'

    def test_lt_value(self) -> None:
        assert ThresholdOperator.LT == 'lt'


# ---------------------------------------------------------------------------
# CompanyMetric
# ---------------------------------------------------------------------------


class TestCompanyMetric:
    def test_valid_metric_created(self) -> None:
        m = _metric()
        assert m.name == 'Monthly Revenue'

    def test_blank_name_raises(self) -> None:
        with pytest.raises(ValueError, match='name'):
            CompanyMetric(
                id=_uid(), name='', metric_type=MetricType.REVENUE,
                description=None, created_at=_NOW,
            )

    def test_whitespace_name_raises(self) -> None:
        with pytest.raises(ValueError, match='name'):
            CompanyMetric(
                id=_uid(), name='   ', metric_type=MetricType.REVENUE,
                description=None, created_at=_NOW,
            )


# ---------------------------------------------------------------------------
# RevenueSnapshot
# ---------------------------------------------------------------------------


class TestRevenueSnapshot:
    def test_valid_snapshot_created(self) -> None:
        s = _revenue_snapshot()
        assert s.amount == Decimal('10000.00')

    def test_negative_amount_raises(self) -> None:
        with pytest.raises(ValueError, match='amount'):
            _revenue_snapshot(amount=Decimal('-1'))

    def test_zero_amount_is_valid(self) -> None:
        s = _revenue_snapshot(amount=Decimal('0'))
        assert s.amount == Decimal('0')

    def test_period_end_before_start_raises(self) -> None:
        with pytest.raises(ValueError, match='period_end'):
            _revenue_snapshot(
                period_start=date(2025, 1, 31),
                period_end=date(2025, 1, 1),
            )

    def test_invalid_currency_length_raises(self) -> None:
        with pytest.raises(ValueError, match='currency'):
            _revenue_snapshot(currency='US')

    def test_currency_with_digits_raises(self) -> None:
        with pytest.raises(ValueError, match='currency'):
            _revenue_snapshot(currency='U1D')


# ---------------------------------------------------------------------------
# CustomerGrowthSnapshot
# ---------------------------------------------------------------------------


class TestCustomerGrowthSnapshot:
    def test_valid_snapshot_created(self) -> None:
        s = _growth_snapshot()
        assert s.net_customers == 8

    def test_negative_new_customers_raises(self) -> None:
        with pytest.raises(ValueError, match='new_customers'):
            _growth_snapshot(new_customers=-1, churned_customers=2, net_customers=-3)

    def test_negative_churned_customers_raises(self) -> None:
        with pytest.raises(ValueError, match='churned_customers'):
            _growth_snapshot(new_customers=5, churned_customers=-1, net_customers=6)

    def test_wrong_net_raises(self) -> None:
        with pytest.raises(ValueError, match='net_customers'):
            _growth_snapshot(new_customers=10, churned_customers=2, net_customers=99)


# ---------------------------------------------------------------------------
# AlertRule state transitions
# ---------------------------------------------------------------------------


class TestAlertRuleTransitions:
    def test_pause_active_rule_succeeds(self) -> None:
        rule = _alert_rule(AlertRuleStatus.ACTIVE)
        event = rule.pause(paused_by=_uid())
        assert rule.status == AlertRuleStatus.PAUSED
        assert event.rule_id == rule.id

    def test_pause_already_paused_raises(self) -> None:
        rule = _alert_rule(AlertRuleStatus.PAUSED)
        with pytest.raises(ValueError, match='ACTIVE'):
            rule.pause(paused_by=_uid())

    def test_activate_paused_rule_succeeds(self) -> None:
        rule = _alert_rule(AlertRuleStatus.PAUSED)
        event = rule.activate(activated_by=_uid())
        assert rule.status == AlertRuleStatus.ACTIVE
        assert event.rule_id == rule.id

    def test_activate_active_rule_raises(self) -> None:
        rule = _alert_rule(AlertRuleStatus.ACTIVE)
        with pytest.raises(ValueError, match='PAUSED'):
            rule.activate(activated_by=_uid())

    def test_blank_name_raises(self) -> None:
        with pytest.raises(ValueError, match='name'):
            AlertRule(
                id=_uid(), name='', metric_id=_uid(),
                threshold_value=Decimal('100'), operator=ThresholdOperator.GT,
                severity=AlertSeverity.INFO, status=AlertRuleStatus.ACTIVE,
                last_evaluated_at=None, created_at=_NOW,
            )


# ---------------------------------------------------------------------------
# DashboardAlert state transitions
# ---------------------------------------------------------------------------


class TestDashboardAlertTransitions:
    def test_acknowledge_active_alert_succeeds(self) -> None:
        alert = _dashboard_alert(AlertStatus.ACTIVE)
        actor = _uid()
        event = alert.acknowledge(acknowledged_by=actor)
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_by == actor
        assert alert.acknowledged_at is not None
        assert event.alert_id == alert.id

    def test_acknowledge_resolved_alert_raises(self) -> None:
        alert = _dashboard_alert(AlertStatus.RESOLVED)
        with pytest.raises(ValueError, match='ACTIVE'):
            alert.acknowledge(acknowledged_by=_uid())

    def test_resolve_active_alert_succeeds(self) -> None:
        alert = _dashboard_alert(AlertStatus.ACTIVE)
        actor = _uid()
        event = alert.resolve(resolved_by=actor)
        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_by == actor
        assert alert.resolved_at is not None

    def test_resolve_acknowledged_alert_succeeds(self) -> None:
        alert = _dashboard_alert(AlertStatus.ACKNOWLEDGED)
        actor = _uid()
        alert.resolve(resolved_by=actor)
        assert alert.status == AlertStatus.RESOLVED

    def test_resolve_already_resolved_raises(self) -> None:
        alert = _dashboard_alert(AlertStatus.RESOLVED)
        with pytest.raises(ValueError, match='ACTIVE or ACKNOWLEDGED'):
            alert.resolve(resolved_by=_uid())


# ---------------------------------------------------------------------------
# AuditLogEntry immutability
# ---------------------------------------------------------------------------


class TestAuditLogEntry:
    def test_audit_entry_created(self) -> None:
        entry = AuditLogEntry(
            id=_uid(),
            action=AuditAction.RULE_CREATED,
            actor_id=_uid(),
            resource_id=_uid(),
            resource_type='AlertRule',
            detail=None,
            created_at=_NOW,
        )
        assert entry.action == AuditAction.RULE_CREATED

    def test_audit_entry_has_no_state_transition_methods(self) -> None:
        entry = AuditLogEntry(
            id=_uid(),
            action=AuditAction.ALERT_ACKNOWLEDGED,
            actor_id=_uid(),
            resource_id=_uid(),
            resource_type='DashboardAlert',
            detail='test',
            created_at=_NOW,
        )
        assert not hasattr(entry, 'acknowledge')
        assert not hasattr(entry, 'resolve')
        assert not hasattr(entry, 'pause')
        assert not hasattr(entry, 'activate')
