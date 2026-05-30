import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class CompanyMetric(models.Model):
    METRIC_TYPE_REVENUE = 'revenue'
    METRIC_TYPE_CUSTOMER_GROWTH = 'customer_growth'
    METRIC_TYPE_CUSTOM = 'custom'
    METRIC_TYPE_CHOICES = [
        (METRIC_TYPE_REVENUE, 'Revenue'),
        (METRIC_TYPE_CUSTOMER_GROWTH, 'Customer Growth'),
        (METRIC_TYPE_CUSTOM, 'Custom'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    metric_type = models.CharField(max_length=20, choices=METRIC_TYPE_CHOICES)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return f'{self.name} ({self.metric_type})'


class RevenueSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric = models.ForeignKey(
        CompanyMetric,
        on_delete=models.CASCADE,
        related_name='revenue_snapshots',
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    period_start = models.DateField()
    period_end = models.DateField()
    recorded_at = models.DateTimeField()

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self) -> str:
        return f'{self.metric.name} {self.period_start} - {self.period_end}: {self.amount} {self.currency}'


class CustomerGrowthSnapshot(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    metric = models.ForeignKey(
        CompanyMetric,
        on_delete=models.CASCADE,
        related_name='growth_snapshots',
    )
    new_customers = models.IntegerField()
    churned_customers = models.IntegerField()
    net_customers = models.IntegerField()
    period_start = models.DateField()
    period_end = models.DateField()
    recorded_at = models.DateTimeField()

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self) -> str:
        return f'{self.metric.name} {self.period_start} - {self.period_end}: net {self.net_customers}'


class AlertRule(models.Model):
    OPERATOR_GT = 'gt'
    OPERATOR_LT = 'lt'
    OPERATOR_GTE = 'gte'
    OPERATOR_LTE = 'lte'
    OPERATOR_EQ = 'eq'
    OPERATOR_CHOICES = [
        (OPERATOR_GT, 'Greater Than'),
        (OPERATOR_LT, 'Less Than'),
        (OPERATOR_GTE, 'Greater Than or Equal'),
        (OPERATOR_LTE, 'Less Than or Equal'),
        (OPERATOR_EQ, 'Equal'),
    ]

    SEVERITY_INFO = 'info'
    SEVERITY_WARNING = 'warning'
    SEVERITY_CRITICAL = 'critical'
    SEVERITY_CHOICES = [
        (SEVERITY_INFO, 'Info'),
        (SEVERITY_WARNING, 'Warning'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]

    STATUS_ACTIVE = 'active'
    STATUS_PAUSED = 'paused'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_PAUSED, 'Paused'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    metric = models.ForeignKey(
        CompanyMetric,
        on_delete=models.CASCADE,
        related_name='alert_rules',
    )
    threshold_value = models.DecimalField(max_digits=12, decimal_places=2)
    operator = models.CharField(max_length=10, choices=OPERATOR_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    last_evaluated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.name} ({self.severity})'


class DashboardAlert(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_ACKNOWLEDGED = 'acknowledged'
    STATUS_RESOLVED = 'resolved'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_ACKNOWLEDGED, 'Acknowledged'),
        (STATUS_RESOLVED, 'Resolved'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(
        AlertRule,
        on_delete=models.CASCADE,
        related_name='alerts',
    )
    metric = models.ForeignKey(
        CompanyMetric,
        on_delete=models.CASCADE,
        related_name='alerts',
    )
    triggered_value = models.DecimalField(max_digits=12, decimal_places=2)
    threshold_value = models.DecimalField(max_digits=12, decimal_places=2)
    operator = models.CharField(max_length=10, choices=AlertRule.OPERATOR_CHOICES)
    severity = models.CharField(max_length=20, choices=AlertRule.SEVERITY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='acknowledged_alerts',
    )
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='resolved_alerts',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Alert {self.id} [{self.severity}] {self.status}'


class AuditLogEntry(models.Model):
    ACTION_CHOICES = [
        ('metric_created', 'Metric Created'),
        ('metric_updated', 'Metric Updated'),
        ('alert_acknowledged', 'Alert Acknowledged'),
        ('alert_resolved', 'Alert Resolved'),
        ('rule_created', 'Rule Created'),
        ('rule_paused', 'Rule Paused'),
        ('rule_activated', 'Rule Activated'),
        ('import_started', 'Import Started'),
        ('import_completed', 'Import Completed'),
        ('import_failed', 'Import Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=40, choices=ACTION_CHOICES)
    actor = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='ops_audit_entries',
    )
    resource_id = models.UUIDField(db_index=True)
    resource_type = models.CharField(max_length=50)
    detail = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.action} by {self.actor_id} on {self.resource_type} {self.resource_id}'
