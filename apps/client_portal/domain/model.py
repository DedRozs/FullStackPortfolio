from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from apps.client_portal.domain.value_objects import (
    ApprovalStatus,
    InvoiceStatus,
    MilestoneStatus,
    ProjectStatus,
)


@dataclass
class ClientOrganization:
    id: UUID
    name: str
    slug: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ClientOrganization.name must not be blank")
        if not self.slug:
            raise ValueError("ClientOrganization.slug must not be blank")


@dataclass
class UserProfile:
    id: UUID
    user_id: int
    email: str
    is_client: bool
    organization_id: UUID | None
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.email:
            raise ValueError("UserProfile.email must not be blank")
        if self.is_client and self.organization_id is None:
            raise ValueError("Stakeholder UserProfile must have an organization_id")
        if not self.is_client and self.organization_id is not None:
            raise ValueError("Staff UserProfile must not have an organization_id")


@dataclass
class Project:
    id: UUID
    name: str
    organization_id: UUID
    status: ProjectStatus
    description: str | None
    target_date: date | None
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Project.name must not be blank")

    def submit_for_approval(self) -> None:
        if self.status != ProjectStatus.ACTIVE:
            raise ValueError("Only ACTIVE projects can be submitted for approval")
        self.status = ProjectStatus.PENDING_APPROVAL

    def return_to_active(self) -> None:
        if self.status != ProjectStatus.PENDING_APPROVAL:
            raise ValueError("Only PENDING_APPROVAL projects can return to active")
        self.status = ProjectStatus.ACTIVE

    def mark_complete(self) -> None:
        if self.status != ProjectStatus.PENDING_APPROVAL:
            raise ValueError("Only PENDING_APPROVAL projects can be marked complete")
        self.status = ProjectStatus.COMPLETE

    def archive(self) -> None:
        if self.status not in (ProjectStatus.ACTIVE, ProjectStatus.COMPLETE):
            raise ValueError("Only ACTIVE or COMPLETE projects can be archived")
        self.status = ProjectStatus.ARCHIVED


@dataclass
class Milestone:
    id: UUID
    name: str
    project_id: UUID
    status: MilestoneStatus
    target_date: date | None
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Milestone.name must not be blank")

    def begin(self) -> None:
        if self.status != MilestoneStatus.PENDING:
            raise ValueError("Only PENDING milestones can be started")
        if self.target_date is None:
            raise ValueError("target_date must be set before starting a Milestone")
        self.status = MilestoneStatus.IN_PROGRESS

    def complete(self) -> None:
        if self.status != MilestoneStatus.IN_PROGRESS:
            raise ValueError("Only IN_PROGRESS milestones can be completed")
        self.status = MilestoneStatus.COMPLETE


@dataclass
class Deliverable:
    id: UUID
    name: str
    milestone_id: UUID
    description: str | None
    current_version_number: int
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Deliverable.name must not be blank")


@dataclass
class DeliverableVersion:
    id: UUID
    deliverable_id: UUID
    version_number: int
    notes: str | None
    created_at: datetime


@dataclass
class Approval:
    id: UUID
    deliverable_version_id: UUID
    reviewer_id: UUID
    status: ApprovalStatus
    comment: str | None
    decided_at: datetime | None
    created_at: datetime

    def approve(self, comment: str | None = None) -> None:
        if self.status != ApprovalStatus.PENDING:
            raise ValueError("Only PENDING approvals can be approved")
        self.status = ApprovalStatus.APPROVED
        self.comment = comment

    def reject(self, comment: str) -> None:
        if not comment:
            raise ValueError("A rejection comment is required")
        if self.status != ApprovalStatus.PENDING:
            raise ValueError("Only PENDING approvals can be rejected")
        self.status = ApprovalStatus.REJECTED
        self.comment = comment

    def request_revision(self, comment: str) -> None:
        if not comment:
            raise ValueError("A revision request comment is required")
        if self.status != ApprovalStatus.PENDING:
            raise ValueError("Only PENDING approvals can have revisions requested")
        self.status = ApprovalStatus.REVISION_REQUESTED
        self.comment = comment


@dataclass
class FileRecord:
    id: UUID
    filename: str
    storage_path: str
    mime_type: str
    file_size_bytes: int
    deliverable_version_id: UUID | None
    message_id: UUID | None
    uploaded_by_id: UUID
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.filename:
            raise ValueError("FileRecord.filename must not be blank")
        if not self.storage_path:
            raise ValueError("FileRecord.storage_path must not be blank")
        if not self.mime_type:
            raise ValueError("FileRecord.mime_type must not be blank")
        if self.file_size_bytes <= 0:
            raise ValueError("FileRecord.file_size_bytes must be positive")
        has_dv = self.deliverable_version_id is not None
        has_msg = self.message_id is not None
        if has_dv == has_msg:
            raise ValueError(
                "Exactly one of deliverable_version_id or message_id must be set"
            )


@dataclass
class MessageThread:
    id: UUID
    subject: str
    project_id: UUID
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.subject:
            raise ValueError("MessageThread.subject must not be blank")


@dataclass
class Message:
    id: UUID
    thread_id: UUID
    sender_id: UUID
    body: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.body:
            raise ValueError("Message.body must not be blank")


@dataclass
class InvoiceRecord:
    id: UUID
    organization_id: UUID
    project_id: UUID | None
    status: InvoiceStatus
    amount: Decimal
    due_date: date | None
    issued_at: datetime | None
    created_at: datetime

    def __post_init__(self) -> None:
        if self.amount <= Decimal("0"):
            raise ValueError("InvoiceRecord.amount must be positive")

    def send(self) -> None:
        if self.status != InvoiceStatus.DRAFT:
            raise ValueError("Only DRAFT invoices can be sent")
        if self.due_date is None:
            raise ValueError("due_date must be set before sending")
        self.status = InvoiceStatus.SENT

    def mark_paid(self) -> None:
        if self.status != InvoiceStatus.SENT:
            raise ValueError("Only SENT invoices can be marked paid")
        self.status = InvoiceStatus.PAID

    def mark_overdue(self) -> None:
        if self.status != InvoiceStatus.SENT:
            raise ValueError("Only SENT invoices can be marked overdue")
        self.status = InvoiceStatus.OVERDUE


@dataclass
class ActivityEvent:
    id: UUID
    event_type: str
    actor_id: UUID
    project_id: UUID | None
    organization_id: UUID | None
    payload: dict
    occurred_at: datetime

    def __post_init__(self) -> None:
        if not self.event_type:
            raise ValueError("ActivityEvent.event_type must not be blank")
