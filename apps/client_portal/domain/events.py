from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID


@dataclass(frozen=True)
class ClientOrganizationRegistered:
    organization_id: UUID
    name: str
    slug: str
    occurred_at: datetime


@dataclass(frozen=True)
class UserProfileCreated:
    user_profile_id: UUID
    is_client: bool
    organization_id: UUID | None
    occurred_at: datetime


@dataclass(frozen=True)
class ProjectActivated:
    project_id: UUID
    organization_id: UUID
    name: str
    occurred_at: datetime


@dataclass(frozen=True)
class ProjectSubmittedForApproval:
    project_id: UUID
    organization_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class ProjectReturnedToActive:
    project_id: UUID
    organization_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class ProjectCompleted:
    project_id: UUID
    organization_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class ProjectArchived:
    project_id: UUID
    organization_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class MilestoneStarted:
    milestone_id: UUID
    project_id: UUID
    organization_id: UUID
    name: str
    target_date: date
    occurred_at: datetime


@dataclass(frozen=True)
class MilestoneCompleted:
    milestone_id: UUID
    project_id: UUID
    organization_id: UUID
    name: str
    occurred_at: datetime


@dataclass(frozen=True)
class DeliverableRevisionSubmitted:
    deliverable_id: UUID
    deliverable_version_id: UUID
    version_number: int
    milestone_id: UUID
    project_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class DeliverableApproved:
    deliverable_id: UUID
    deliverable_version_id: UUID
    approval_id: UUID
    reviewer_id: UUID
    comment: str | None
    milestone_id: UUID
    project_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class DeliverableRejected:
    deliverable_id: UUID
    deliverable_version_id: UUID
    approval_id: UUID
    reviewer_id: UUID
    comment: str
    milestone_id: UUID
    project_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class DeliverableRevisionRequested:
    deliverable_id: UUID
    deliverable_version_id: UUID
    approval_id: UUID
    reviewer_id: UUID
    comment: str
    milestone_id: UUID
    project_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class FileRecordUploaded:
    file_record_id: UUID
    filename: str
    mime_type: str
    file_size_bytes: int
    uploaded_by_id: UUID
    deliverable_version_id: UUID | None
    message_id: UUID | None
    occurred_at: datetime


@dataclass(frozen=True)
class MessagePosted:
    message_id: UUID
    thread_id: UUID
    project_id: UUID
    sender_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class InvoiceSent:
    invoice_record_id: UUID
    organization_id: UUID
    amount_cents: int
    due_date: date
    occurred_at: datetime


@dataclass(frozen=True)
class InvoicePaid:
    invoice_record_id: UUID
    organization_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class InvoiceMarkedOverdue:
    invoice_record_id: UUID
    organization_id: UUID
    occurred_at: datetime
