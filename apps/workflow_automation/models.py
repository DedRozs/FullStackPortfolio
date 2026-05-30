import uuid

from django.db import models


class AutomationRule(models.Model):
    TRIGGER_TYPE_CHOICES = [
        ('deliverable.approved', 'Deliverable Approved'),
        ('metric.threshold_crossed', 'Metric Threshold Crossed'),
        ('invoice.overdue', 'Invoice Overdue'),
        ('file.uploaded', 'File Uploaded'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    trigger_type = models.CharField(max_length=40, choices=TRIGGER_TYPE_CHOICES, db_index=True)
    is_enabled = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.name} ({self.trigger_type})'


class AutomationCondition(models.Model):
    OPERATOR_CHOICES = [
        ('gt', 'Greater Than'),
        ('lt', 'Less Than'),
        ('eq', 'Equals'),
        ('contains', 'Contains'),
        ('assigned_to', 'Assigned To'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(
        AutomationRule, on_delete=models.CASCADE, related_name='conditions'
    )
    field_name = models.CharField(max_length=255)
    operator = models.CharField(max_length=20, choices=OPERATOR_CHOICES)
    expected_value = models.CharField(max_length=255)
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ['position']

    def __str__(self) -> str:
        return f'{self.field_name} {self.operator} {self.expected_value}'


class AutomationAction(models.Model):
    ACTION_TYPE_CHOICES = [
        ('send_email', 'Send Email'),
        ('create_activity_event', 'Create Activity Event'),
        ('update_status', 'Update Status'),
        ('send_sms', 'Send SMS'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(
        AutomationRule, on_delete=models.CASCADE, related_name='actions'
    )
    action_type = models.CharField(max_length=40, choices=ACTION_TYPE_CHOICES)
    parameters = models.JSONField(default=dict)
    position = models.IntegerField(default=0)

    class Meta:
        ordering = ['position']

    def __str__(self) -> str:
        return f'{self.action_type} ({self.rule.name})'


class AutomationRun(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('success', 'Success'),
        ('failure', 'Failure'),
        ('dry_run', 'Dry Run'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rule = models.ForeignKey(
        AutomationRule, on_delete=models.CASCADE, related_name='runs'
    )
    trigger_type = models.CharField(max_length=40)
    context_payload = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_dry_run = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Run {self.id} ({self.status})'


class AutomationRunLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(
        AutomationRun, on_delete=models.CASCADE, related_name='logs'
    )
    level = models.CharField(max_length=20)
    message = models.TextField()
    logged_at = models.DateTimeField()

    class Meta:
        ordering = ['logged_at']

    def __str__(self) -> str:
        return f'[{self.level}] {self.message[:50]}'
