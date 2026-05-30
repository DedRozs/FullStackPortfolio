from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID


# ---------------------------------------------------------------------------
# Command DTOs (inputs to use cases)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RegisterClientOrganizationCommand:
    name: str
    slug: str


@dataclass(frozen=True)
class CreateUserProfileCommand:
    user_id: int
    email: str
    is_client: bool
    organization_id: Optional[UUID]


@dataclass(frozen=True)
class CreateProjectCommand:
    name: str
    organization_id: UUID
    description: Optional[str]
    target_date: Optional[date]
    actor_id: UUID


@dataclass(frozen=True)
class ActivateProjectCommand:
    project_id: UUID
    actor_id: UUID


@dataclass(frozen=True)
class SubmitProjectForApprovalCommand:
    project_id: UUID
    actor_id: UUID


@dataclass(frozen=True)
class ApproveProjectCommand:
    project_id: UUID
    actor_id: UUID


@dataclass(frozen=True)
class RejectProjectCommand:
    project_id: UUID
    actor_id: UUID


@dataclass(frozen=True)
class CreateMilestoneCommand:
    name: str
    project_id: UUID
    target_date: Optional[date]


@dataclass(frozen=True)
class CompleteMilestoneCommand:
    milestone_id: UUID
    actor_id: UUID


@dataclass(frozen=True)
class AddDeliverableVersionCommand:
    deliverable_id: UUID
    notes: Optional[str]
    actor_id: UUID


@dataclass(frozen=True)
class RequestApprovalCommand:
    deliverable_version_id: UUID
    reviewer_id: UUID
    actor_id: UUID


@dataclass(frozen=True)
class GrantApprovalCommand:
    approval_id: UUID
    reviewer_id: UUID
    comment: Optional[str]


@dataclass(frozen=True)
class RejectApprovalCommand:
    approval_id: UUID
    reviewer_id: UUID
    comment: str


@dataclass(frozen=True)
class RequestRevisionCommand:
    approval_id: UUID
    reviewer_id: UUID
    comment: str


@dataclass(frozen=True)
class UploadFileCommand:
    filename: str
    content_type: str
    file_size_bytes: int
    file_data: bytes
    deliverable_version_id: Optional[UUID]
    message_id: Optional[UUID]
    uploaded_by_id: UUID


@dataclass(frozen=True)
class SendMessageCommand:
    thread_id: UUID
    sender_id: UUID
    body: str


@dataclass(frozen=True)
class ListFilesForDeliverableQuery:
    deliverable_version_id: UUID


@dataclass(frozen=True)
class ListMessagesQuery:
    thread_id: UUID


@dataclass(frozen=True)
class ListInvoicesQuery:
    organization_id: UUID


@dataclass(frozen=True)
class ListActivityEventsQuery:
    project_id: Optional[UUID]
    organization_id: Optional[UUID]


# ---------------------------------------------------------------------------
# Result DTOs (outputs from use cases)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ClientOrganizationDTO:
    id: UUID
    name: str
    slug: str
    created_at: datetime


@dataclass(frozen=True)
class UserProfileDTO:
    id: UUID
    user_id: int
    email: str
    is_client: bool
    organization_id: Optional[UUID]
    created_at: datetime


@dataclass(frozen=True)
class ProjectDTO:
    id: UUID
    name: str
    organization_id: UUID
    status: str
    description: Optional[str]
    target_date: Optional[date]
    created_at: datetime


@dataclass(frozen=True)
class MilestoneDTO:
    id: UUID
    name: str
    project_id: UUID
    status: str
    target_date: Optional[date]
    created_at: datetime


@dataclass(frozen=True)
class DeliverableDTO:
    id: UUID
    name: str
    milestone_id: UUID
    description: Optional[str]
    current_version_number: int
    created_at: datetime


@dataclass(frozen=True)
class DeliverableVersionDTO:
    id: UUID
    deliverable_id: UUID
    version_number: int
    notes: Optional[str]
    created_at: datetime


@dataclass(frozen=True)
class ApprovalDTO:
    id: UUID
    deliverable_version_id: UUID
    reviewer_id: UUID
    status: str
    comment: Optional[str]
    decided_at: Optional[datetime]
    created_at: datetime


@dataclass(frozen=True)
class FileRecordDTO:
    id: UUID
    filename: str
    storage_path: str
    mime_type: str
    file_size_bytes: int
    deliverable_version_id: Optional[UUID]
    message_id: Optional[UUID]
    uploaded_by_id: UUID
    created_at: datetime
    download_url: str = field(default='')


@dataclass(frozen=True)
class MessageThreadDTO:
    id: UUID
    subject: str
    project_id: UUID
    created_at: datetime


@dataclass(frozen=True)
class MessageDTO:
    id: UUID
    thread_id: UUID
    sender_id: UUID
    body: str
    created_at: datetime


@dataclass(frozen=True)
class InvoiceRecordDTO:
    id: UUID
    organization_id: UUID
    project_id: Optional[UUID]
    status: str
    amount: Decimal
    due_date: Optional[date]
    issued_at: Optional[datetime]
    created_at: datetime


@dataclass(frozen=True)
class ActivityEventDTO:
    id: UUID
    event_type: str
    actor_id: UUID
    project_id: Optional[UUID]
    organization_id: Optional[UUID]
    payload: dict
    occurred_at: datetime
