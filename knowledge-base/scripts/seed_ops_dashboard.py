"""
Seed script for ops_dashboard app.

Generates:
- 2 CompanyMetric records (Monthly Revenue, Active Customers)
- 12 RevenueSnapshot records (Jan-Dec 2025, trending $40k-$120k)
- 12 CustomerGrowthSnapshot records (realistic growth data)
- 3 AlertRule records (revenue drop, revenue spike, customer churn)
- 1 triggered DashboardAlert (ACTIVE, revenue drop)
- 5 AuditLogEntry records

Usage:
    .venv\\Scripts\\python.exe knowledge-base/scripts/seed_ops_dashboard.py
"""
import os
import sys
import datetime
import decimal
import uuid

# ---------------------------------------------------------------------------
# Bootstrap Django before importing any app models.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

# ---------------------------------------------------------------------------
# Imports - safe after django.setup()
# ---------------------------------------------------------------------------
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.ops_dashboard.models import (
    AlertRule,
    AuditLogEntry,
    CompanyMetric,
    CustomerGrowthSnapshot,
    DashboardAlert,
    RevenueSnapshot,
)

User = get_user_model()


MONTHLY_REVENUE = [
    decimal.Decimal('42000.00'),
    decimal.Decimal('47000.00'),
    decimal.Decimal('51000.00'),
    decimal.Decimal('55000.00'),
    decimal.Decimal('61000.00'),
    decimal.Decimal('68000.00'),
    decimal.Decimal('72000.00'),
    decimal.Decimal('79000.00'),
    decimal.Decimal('85000.00'),
    decimal.Decimal('94000.00'),
    decimal.Decimal('108000.00'),
    decimal.Decimal('121000.00'),
]

GROWTH_DATA = [
    (8, 2), (10, 3), (12, 2), (14, 3), (11, 2), (15, 4),
    (13, 3), (16, 2), (18, 3), (14, 4), (20, 3), (22, 5),
]


def get_or_create_staff_user():
    user, _ = User.objects.get_or_create(
        username='ops_admin',
        defaults={'email': 'ops_admin@example.com'},
    )
    user.is_staff = True
    user.set_password('OpsDashboard2025!')
    user.save()
    return user


def run() -> None:
    print('Seeding ops_dashboard data...')

    staff = get_or_create_staff_user()
    print(f'  Staff user: {staff.username}')

    # ------------------------------------------------------------------
    # CompanyMetric records
    # ------------------------------------------------------------------
    revenue_metric, created = CompanyMetric.objects.get_or_create(
        name='Monthly Revenue',
        defaults={'metric_type': 'revenue', 'description': 'Total monthly recurring revenue in USD.'},
    )
    print(f'  CompanyMetric: {revenue_metric.name} ({"created" if created else "exists"})')

    growth_metric, created = CompanyMetric.objects.get_or_create(
        name='Active Customers',
        defaults={'metric_type': 'customer_growth', 'description': 'Monthly active customer net growth.'},
    )
    print(f'  CompanyMetric: {growth_metric.name} ({"created" if created else "exists"})')

    # ------------------------------------------------------------------
    # RevenueSnapshot records - Jan-Dec 2025
    # ------------------------------------------------------------------
    existing_revenue = set(
        RevenueSnapshot.objects.filter(metric=revenue_metric).values_list('period_start', flat=True)
    )
    for month_idx, amount in enumerate(MONTHLY_REVENUE, start=1):
        period_start = datetime.date(2025, month_idx, 1)
        if period_start in existing_revenue:
            continue
        last_day = (
            datetime.date(2025, month_idx + 1, 1) - datetime.timedelta(days=1)
            if month_idx < 12
            else datetime.date(2025, 12, 31)
        )
        RevenueSnapshot.objects.create(
            metric=revenue_metric,
            amount=amount,
            currency='USD',
            period_start=period_start,
            period_end=last_day,
            recorded_at=timezone.make_aware(datetime.datetime(2025, month_idx, last_day.day, 18, 0, 0)),
        )
    print(f'  RevenueSnapshot: {RevenueSnapshot.objects.filter(metric=revenue_metric).count()} records')

    # ------------------------------------------------------------------
    # CustomerGrowthSnapshot records - Jan-Dec 2025
    # ------------------------------------------------------------------
    existing_growth = set(
        CustomerGrowthSnapshot.objects.filter(metric=growth_metric).values_list('period_start', flat=True)
    )
    for month_idx, (new_c, churned_c) in enumerate(GROWTH_DATA, start=1):
        period_start = datetime.date(2025, month_idx, 1)
        if period_start in existing_growth:
            continue
        last_day = (
            datetime.date(2025, month_idx + 1, 1) - datetime.timedelta(days=1)
            if month_idx < 12
            else datetime.date(2025, 12, 31)
        )
        CustomerGrowthSnapshot.objects.create(
            metric=growth_metric,
            new_customers=new_c,
            churned_customers=churned_c,
            net_customers=new_c - churned_c,
            period_start=period_start,
            period_end=last_day,
            recorded_at=timezone.make_aware(datetime.datetime(2025, month_idx, last_day.day, 18, 0, 0)),
        )
    print(f'  CustomerGrowthSnapshot: {CustomerGrowthSnapshot.objects.filter(metric=growth_metric).count()} records')

    # ------------------------------------------------------------------
    # AlertRule records
    # ------------------------------------------------------------------
    revenue_drop_rule, created = AlertRule.objects.get_or_create(
        name='Revenue Drop Alert',
        defaults={
            'metric': revenue_metric,
            'threshold_value': decimal.Decimal('40000.00'),
            'operator': 'lt',
            'severity': 'critical',
            'status': 'active',
        },
    )
    print(f'  AlertRule: {revenue_drop_rule.name} ({"created" if created else "exists"})')

    revenue_spike_rule, created = AlertRule.objects.get_or_create(
        name='Revenue Spike Alert',
        defaults={
            'metric': revenue_metric,
            'threshold_value': decimal.Decimal('150000.00'),
            'operator': 'gt',
            'severity': 'info',
            'status': 'active',
        },
    )
    print(f'  AlertRule: {revenue_spike_rule.name} ({"created" if created else "exists"})')

    churn_rule, created = AlertRule.objects.get_or_create(
        name='High Customer Churn Alert',
        defaults={
            'metric': growth_metric,
            'threshold_value': decimal.Decimal('10'),
            'operator': 'gt',
            'severity': 'warning',
            'status': 'active',
        },
    )
    print(f'  AlertRule: {churn_rule.name} ({"created" if created else "exists"})')

    # ------------------------------------------------------------------
    # DashboardAlert record (ACTIVE - revenue drop triggered)
    # ------------------------------------------------------------------
    if not DashboardAlert.objects.filter(rule=revenue_drop_rule, status='active').exists():
        DashboardAlert.objects.create(
            rule=revenue_drop_rule,
            metric=revenue_metric,
            triggered_value=decimal.Decimal('38500.00'),
            threshold_value=decimal.Decimal('40000.00'),
            operator='lt',
            severity='critical',
            status='active',
        )
        print('  DashboardAlert: created ACTIVE revenue drop alert')
    else:
        print('  DashboardAlert: already exists')

    # ------------------------------------------------------------------
    # AuditLogEntry records
    # ------------------------------------------------------------------
    if AuditLogEntry.objects.filter(actor=staff).count() < 5:
        actions = [
            ('rule_created', revenue_metric.id, 'CompanyMetric', 'Monthly Revenue metric created'),
            ('rule_created', growth_metric.id, 'CompanyMetric', 'Active Customers metric created'),
            ('rule_created', revenue_drop_rule.id, 'AlertRule', 'Revenue Drop Alert rule created'),
            ('rule_created', revenue_spike_rule.id, 'AlertRule', 'Revenue Spike Alert rule created'),
            ('rule_created', churn_rule.id, 'AlertRule', 'High Customer Churn Alert rule created'),
        ]
        for action, resource_id, resource_type, detail in actions:
            AuditLogEntry.objects.get_or_create(
                action=action,
                actor=staff,
                resource_id=resource_id,
                resource_type=resource_type,
                defaults={'detail': detail},
            )
        print(f'  AuditLogEntry: {AuditLogEntry.objects.filter(actor=staff).count()} records')

    print('Done.')


if __name__ == '__main__':
    run()
