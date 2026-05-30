"""
Seed script for ops_dashboard app.

Generates:
- 2 CompanyMetric records (Monthly Revenue, Active Customers)
- RevenueSnapshot records (Jan 2025 - May 2026, trending $40k-$145k)
- CustomerGrowthSnapshot records (realistic growth data for same range)
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


# Jan 2025 - May 2026 (17 months)
MONTHLY_REVENUE = [
    decimal.Decimal('42000.00'),   # 2025-01
    decimal.Decimal('47000.00'),   # 2025-02
    decimal.Decimal('51000.00'),   # 2025-03
    decimal.Decimal('55000.00'),   # 2025-04
    decimal.Decimal('61000.00'),   # 2025-05
    decimal.Decimal('68000.00'),   # 2025-06
    decimal.Decimal('72000.00'),   # 2025-07
    decimal.Decimal('79000.00'),   # 2025-08
    decimal.Decimal('85000.00'),   # 2025-09
    decimal.Decimal('94000.00'),   # 2025-10
    decimal.Decimal('108000.00'),  # 2025-11
    decimal.Decimal('121000.00'),  # 2025-12
    decimal.Decimal('127000.00'),  # 2026-01
    decimal.Decimal('132000.00'),  # 2026-02
    decimal.Decimal('138000.00'),  # 2026-03
    decimal.Decimal('141000.00'),  # 2026-04
    decimal.Decimal('145000.00'),  # 2026-05
]

GROWTH_DATA = [
    (8, 2), (10, 3), (12, 2), (14, 3), (11, 2), (15, 4),
    (13, 3), (16, 2), (18, 3), (14, 4), (20, 3), (22, 5),
    (19, 4), (21, 5), (24, 4), (22, 6), (25, 5),
]

# Months corresponding to the data above, in order
SEED_MONTHS = [
    datetime.date(2025, m, 1) for m in range(1, 13)
] + [
    datetime.date(2026, m, 1) for m in range(1, 6)
]


def month_last_day(d: datetime.date) -> datetime.date:
    import calendar
    return d.replace(day=calendar.monthrange(d.year, d.month)[1])


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
    # RevenueSnapshot records - Jan 2025 to May 2026
    # ------------------------------------------------------------------
    existing_revenue = set(
        RevenueSnapshot.objects.filter(metric=revenue_metric).values_list('period_start', flat=True)
    )
    for period_start, amount in zip(SEED_MONTHS, MONTHLY_REVENUE):
        if period_start in existing_revenue:
            continue
        last_day = month_last_day(period_start)
        RevenueSnapshot.objects.create(
            metric=revenue_metric,
            amount=amount,
            currency='USD',
            period_start=period_start,
            period_end=last_day,
            recorded_at=timezone.make_aware(
                datetime.datetime(period_start.year, period_start.month, last_day.day, 18, 0, 0)
            ),
        )
    print(f'  RevenueSnapshot: {RevenueSnapshot.objects.filter(metric=revenue_metric).count()} records')

    # ------------------------------------------------------------------
    # CustomerGrowthSnapshot records - Jan 2025 to May 2026
    # ------------------------------------------------------------------
    existing_growth = set(
        CustomerGrowthSnapshot.objects.filter(metric=growth_metric).values_list('period_start', flat=True)
    )
    for period_start, (new_c, churned_c) in zip(SEED_MONTHS, GROWTH_DATA):
        if period_start in existing_growth:
            continue
        last_day = month_last_day(period_start)
        CustomerGrowthSnapshot.objects.create(
            metric=growth_metric,
            new_customers=new_c,
            churned_customers=churned_c,
            net_customers=new_c - churned_c,
            period_start=period_start,
            period_end=last_day,
            recorded_at=timezone.make_aware(
                datetime.datetime(period_start.year, period_start.month, last_day.day, 18, 0, 0)
            ),
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
