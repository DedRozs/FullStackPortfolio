"""
Integration tests for apps.ops_dashboard infrastructure layer.

Tests cover:
- Authentication and authorization (401/403/200) on major endpoints
- Read-only enforcement on DashboardAlert and AuditLog endpoints
- Alert rule create and pause via API
- Alert acknowledge via API
- Revenue snapshot ORM round-trip
- Customer growth snapshot net_customers computation
"""
from __future__ import annotations

import uuid
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

import apps.ops_dashboard.models as orm

User = get_user_model()
BASE = '/api/dashboard/'


def _make_staff() -> User:
    return User.objects.create_user(
        username=f'staff_{uuid.uuid4().hex[:8]}',
        email=f'staff_{uuid.uuid4().hex[:8]}@test.com',
        password='pass',
        is_staff=True,
    )


def _make_user() -> User:
    return User.objects.create_user(
        username=f'user_{uuid.uuid4().hex[:8]}',
        email=f'user_{uuid.uuid4().hex[:8]}@test.com',
        password='pass',
        is_staff=False,
    )


def _revenue_metric(name: str = 'Monthly Revenue') -> orm.CompanyMetric:
    return orm.CompanyMetric.objects.create(name=name, metric_type='revenue')


def _growth_metric(name: str = 'Customer Growth') -> orm.CompanyMetric:
    return orm.CompanyMetric.objects.create(name=name, metric_type='customer_growth')


def _alert_rule(metric: orm.CompanyMetric, name: str = 'Revenue Alert') -> orm.AlertRule:
    return orm.AlertRule.objects.create(
        name=name,
        metric=metric,
        threshold_value=Decimal('10000.00'),
        operator='gt',
        severity='warning',
        status='active',
    )


def _active_alert(
    rule: orm.AlertRule, metric: orm.CompanyMetric
) -> orm.DashboardAlert:
    return orm.DashboardAlert.objects.create(
        rule=rule,
        metric=metric,
        triggered_value=Decimal('15000.00'),
        threshold_value=Decimal('10000.00'),
        operator='gt',
        severity='warning',
        status='active',
    )


# ---------------------------------------------------------------------------
# Authentication / authorization
# ---------------------------------------------------------------------------


class DashboardAuthTest(TestCase):
    def setUp(self) -> None:
        self.staff_user = _make_staff()
        self.regular_user = _make_user()
        self.anon = APIClient()
        self.staff = APIClient()
        self.staff.force_authenticate(user=self.staff_user)
        self.regular = APIClient()
        self.regular.force_authenticate(user=self.regular_user)

    def test_unauthenticated_metrics_list_returns_401(self) -> None:
        response = self.anon.get(f'{BASE}metrics/')
        self.assertEqual(response.status_code, 401)

    def test_non_staff_metrics_list_returns_403(self) -> None:
        response = self.regular.get(f'{BASE}metrics/')
        self.assertEqual(response.status_code, 403)

    def test_staff_user_metrics_list_returns_200(self) -> None:
        response = self.staff.get(f'{BASE}metrics/')
        self.assertEqual(response.status_code, 200)


# ---------------------------------------------------------------------------
# Alert rule endpoints
# ---------------------------------------------------------------------------


class AlertRuleApiTest(TestCase):
    def setUp(self) -> None:
        self.staff_user = _make_staff()
        self.staff = APIClient()
        self.staff.force_authenticate(user=self.staff_user)
        self.metric = _revenue_metric()
        self.rule = _alert_rule(self.metric)

    def test_staff_can_create_alert_rule(self) -> None:
        response = self.staff.post(
            f'{BASE}alert-rules/',
            {
                'name': 'New Revenue Alert',
                'metric': str(self.metric.id),
                'threshold_value': '5000.00',
                'operator': 'gt',
                'severity': 'info',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.data)

    def test_staff_can_pause_alert_rule(self) -> None:
        response = self.staff.post(
            f'{BASE}alert-rules/{self.rule.id}/pause/',
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'paused')


# ---------------------------------------------------------------------------
# Alert endpoints
# ---------------------------------------------------------------------------


class AlertApiTest(TestCase):
    def setUp(self) -> None:
        self.staff_user = _make_staff()
        self.staff = APIClient()
        self.staff.force_authenticate(user=self.staff_user)
        self.metric = _revenue_metric()
        self.rule = _alert_rule(self.metric)
        self.alert = _active_alert(self.rule, self.metric)

    def test_staff_can_acknowledge_alert(self) -> None:
        response = self.staff.post(
            f'{BASE}alerts/{self.alert.id}/acknowledge/',
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'acknowledged')

    def test_alerts_list_read_only(self) -> None:
        response = self.staff.post(
            f'{BASE}alerts/',
            {'rule': str(self.rule.id)},
            format='json',
        )
        self.assertEqual(response.status_code, 405)


# ---------------------------------------------------------------------------
# Audit log endpoint
# ---------------------------------------------------------------------------


class AuditLogApiTest(TestCase):
    def setUp(self) -> None:
        self.staff_user = _make_staff()
        self.staff = APIClient()
        self.staff.force_authenticate(user=self.staff_user)

    def test_audit_log_read_only(self) -> None:
        response = self.staff.post(
            f'{BASE}audit-log/',
            {'action': 'metric_created'},
            format='json',
        )
        self.assertEqual(response.status_code, 405)


# ---------------------------------------------------------------------------
# Revenue snapshot - ORM round-trip
# ---------------------------------------------------------------------------


class RevenueSnapshotApiTest(TestCase):
    def setUp(self) -> None:
        self.staff_user = _make_staff()
        self.staff = APIClient()
        self.staff.force_authenticate(user=self.staff_user)
        self.metric = _revenue_metric()

    def test_revenue_snapshot_create_stores_record(self) -> None:
        response = self.staff.post(
            f'{BASE}revenue-snapshots/',
            {
                'metric': str(self.metric.id),
                'amount': 10000.00,
                'currency': 'USD',
                'period_start': '2025-01-01',
                'period_end': '2025-01-31',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn('id', response.data)
        self.assertTrue(
            orm.RevenueSnapshot.objects.filter(id=response.data['id']).exists()
        )


# ---------------------------------------------------------------------------
# Customer growth snapshot - net_customers computation
# ---------------------------------------------------------------------------


class CustomerGrowthSnapshotApiTest(TestCase):
    def setUp(self) -> None:
        self.staff_user = _make_staff()
        self.staff = APIClient()
        self.staff.force_authenticate(user=self.staff_user)
        self.metric = _growth_metric()

    def test_growth_snapshot_net_customers_computed(self) -> None:
        response = self.staff.post(
            f'{BASE}growth-snapshots/',
            {
                'metric': str(self.metric.id),
                'new_customers': 10,
                'churned_customers': 3,
                'period_start': '2025-01-01',
                'period_end': '2025-01-31',
            },
            format='json',
        )
        self.assertEqual(response.status_code, 201)
        snap = orm.CustomerGrowthSnapshot.objects.get(id=response.data['id'])
        self.assertEqual(snap.net_customers, 10 - 3)
