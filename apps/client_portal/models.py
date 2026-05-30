import uuid

from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class ClientOrganization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class UserProfile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='client_portal_profile'
    )
    email = models.EmailField(unique=True)
    is_client = models.BooleanField(default=False)
    is_demo = models.BooleanField(default=False)
    organization = models.ForeignKey(
        ClientOrganization,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='stakeholders',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['email']

    def __str__(self) -> str:
        role = 'client' if self.is_client else 'staff'
        return f'{self.email} ({role})'


class Project(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_PENDING_APPROVAL = 'PENDING_APPROVAL'
    STATUS_COMPLETE = 'COMPLETE'
    STATUS_ARCHIVED = 'ARCHIVED'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_PENDING_APPROVAL, 'Pending Approval'),
        (STATUS_COMPLETE, 'Complete'),
        (STATUS_ARCHIVED, 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(
        ClientOrganization, on_delete=models.CASCADE, related_name='projects'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )
    description = models.TextField(blank=True, null=True)
    target_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.name} ({self.status})'


class Milestone(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETE = 'COMPLETE'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETE, 'Complete'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='milestones'
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    target_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['target_date', 'name']

    def __str__(self) -> str:
        return f'{self.name} - {self.project.name} ({self.status})'


class Deliverable(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    milestone = models.ForeignKey(
        Milestone, on_delete=models.CASCADE, related_name='deliverables'
    )
    description = models.TextField(blank=True, null=True)
    current_version_number = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return f'{self.name} (v{self.current_version_number})'


class DeliverableVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deliverable = models.ForeignKey(
        Deliverable, on_delete=models.CASCADE, related_name='versions'
    )
    version_number = models.PositiveIntegerField()
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['deliverable', 'version_number']
        unique_together = [('deliverable', 'version_number')]

    def __str__(self) -> str:
        return f'{self.deliverable.name} v{self.version_number}'


class Approval(models.Model):
    STATUS_PENDING = 'PENDING'
    STATUS_APPROVED = 'APPROVED'
    STATUS_REJECTED = 'REJECTED'
    STATUS_REVISION_REQUESTED = 'REVISION_REQUESTED'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_REVISION_REQUESTED, 'Revision Requested'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deliverable_version = models.OneToOneField(
        DeliverableVersion, on_delete=models.CASCADE, related_name='approval'
    )
    reviewer = models.ForeignKey(
        UserProfile, on_delete=models.PROTECT, related_name='approvals_given'
    )
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    comment = models.TextField(blank=True, null=True)
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Approval for {self.deliverable_version} ({self.status})'


class MessageThread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.CharField(max_length=500)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name='message_threads'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.subject} ({self.project.name})'


class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    thread = models.ForeignKey(
        MessageThread, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey(
        UserProfile, on_delete=models.PROTECT, related_name='messages_sent'
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self) -> str:
        return f'Message by {self.sender.email} in "{self.thread.subject}"'


class FileRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(max_length=500)
    storage_path = models.CharField(max_length=1000)
    mime_type = models.CharField(max_length=200)
    file_size_bytes = models.PositiveBigIntegerField()
    deliverable_version = models.ForeignKey(
        DeliverableVersion,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='file_records',
    )
    message = models.ForeignKey(
        Message,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='file_records',
    )
    uploaded_by = models.ForeignKey(
        UserProfile, on_delete=models.PROTECT, related_name='uploaded_files'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.filename} ({self.mime_type})'


class InvoiceRecord(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_SENT = 'SENT'
    STATUS_PAID = 'PAID'
    STATUS_OVERDUE = 'OVERDUE'
    STATUS_CANCELLED = 'CANCELLED'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_SENT, 'Sent'),
        (STATUS_PAID, 'Paid'),
        (STATUS_OVERDUE, 'Overdue'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        ClientOrganization, on_delete=models.PROTECT, related_name='invoices'
    )
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='invoices',
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'Invoice {self.id} - {self.organization.name} ({self.status}) ${self.amount}'


class ActivityEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event_type = models.CharField(max_length=200)
    actor = models.ForeignKey(
        UserProfile,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='activity_events',
    )
    project = models.ForeignKey(
        Project,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='activity_events',
    )
    organization = models.ForeignKey(
        ClientOrganization,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='activity_events',
    )
    payload = models.JSONField(default=dict)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-occurred_at']

    def __str__(self) -> str:
        return f'{self.event_type} at {self.occurred_at}'
