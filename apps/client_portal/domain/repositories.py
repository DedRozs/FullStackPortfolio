from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence
from uuid import UUID

from apps.client_portal.domain.model import (
    ActivityEvent,
    Approval,
    ClientOrganization,
    Deliverable,
    DeliverableVersion,
    FileRecord,
    InvoiceRecord,
    Message,
    MessageThread,
    Milestone,
    Project,
    UserProfile,
)
from apps.client_portal.domain.value_objects import InvoiceStatus, ProjectStatus


class ClientOrganizationRepository(ABC):
    @abstractmethod
    def get_by_id(self, organization_id: UUID) -> ClientOrganization | None: ...

    @abstractmethod
    def get_by_slug(self, slug: str) -> ClientOrganization | None: ...

    @abstractmethod
    def save(self, organization: ClientOrganization) -> None: ...

    @abstractmethod
    def list_all(self) -> Sequence[ClientOrganization]: ...


class UserProfileRepository(ABC):
    @abstractmethod
    def get_by_id(self, profile_id: UUID) -> UserProfile | None: ...

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> UserProfile | None: ...

    @abstractmethod
    def save(self, profile: UserProfile) -> None: ...

    @abstractmethod
    def list_stakeholders_for_organization(
        self, organization_id: UUID
    ) -> Sequence[UserProfile]: ...


class ProjectRepository(ABC):
    @abstractmethod
    def get_by_id(self, project_id: UUID) -> Project | None: ...

    @abstractmethod
    def save(self, project: Project) -> None: ...

    @abstractmethod
    def list_by_organization(
        self, organization_id: UUID
    ) -> Sequence[Project]: ...

    @abstractmethod
    def list_by_status(self, status: ProjectStatus) -> Sequence[Project]: ...


class MilestoneRepository(ABC):
    @abstractmethod
    def get_by_id(self, milestone_id: UUID) -> Milestone | None: ...

    @abstractmethod
    def save(self, milestone: Milestone) -> None: ...

    @abstractmethod
    def list_by_project(self, project_id: UUID) -> Sequence[Milestone]: ...


class DeliverableRepository(ABC):
    @abstractmethod
    def get_by_id(self, deliverable_id: UUID) -> Deliverable | None: ...

    @abstractmethod
    def save(self, deliverable: Deliverable) -> None: ...

    @abstractmethod
    def list_by_milestone(self, milestone_id: UUID) -> Sequence[Deliverable]: ...


class DeliverableVersionRepository(ABC):
    @abstractmethod
    def get_by_id(self, version_id: UUID) -> DeliverableVersion | None: ...

    @abstractmethod
    def save(self, version: DeliverableVersion) -> None: ...

    @abstractmethod
    def list_by_deliverable(
        self, deliverable_id: UUID
    ) -> Sequence[DeliverableVersion]: ...


class ApprovalRepository(ABC):
    @abstractmethod
    def get_by_id(self, approval_id: UUID) -> Approval | None: ...

    @abstractmethod
    def get_by_deliverable_version(
        self, deliverable_version_id: UUID
    ) -> Approval | None: ...

    @abstractmethod
    def save(self, approval: Approval) -> None: ...


class FileRecordRepository(ABC):
    @abstractmethod
    def get_by_id(self, file_record_id: UUID) -> FileRecord | None: ...

    @abstractmethod
    def save(self, file_record: FileRecord) -> None: ...

    @abstractmethod
    def list_by_deliverable_version(
        self, deliverable_version_id: UUID
    ) -> Sequence[FileRecord]: ...

    @abstractmethod
    def list_by_message(self, message_id: UUID) -> Sequence[FileRecord]: ...


class MessageThreadRepository(ABC):
    @abstractmethod
    def get_by_id(self, thread_id: UUID) -> MessageThread | None: ...

    @abstractmethod
    def save(self, thread: MessageThread) -> None: ...

    @abstractmethod
    def list_by_project(self, project_id: UUID) -> Sequence[MessageThread]: ...


class MessageRepository(ABC):
    @abstractmethod
    def get_by_id(self, message_id: UUID) -> Message | None: ...

    @abstractmethod
    def save(self, message: Message) -> None: ...

    @abstractmethod
    def list_by_thread(self, thread_id: UUID) -> Sequence[Message]: ...


class InvoiceRecordRepository(ABC):
    @abstractmethod
    def get_by_id(self, invoice_id: UUID) -> InvoiceRecord | None: ...

    @abstractmethod
    def save(self, invoice: InvoiceRecord) -> None: ...

    @abstractmethod
    def list_by_organization(
        self, organization_id: UUID
    ) -> Sequence[InvoiceRecord]: ...

    @abstractmethod
    def list_by_status(self, status: InvoiceStatus) -> Sequence[InvoiceRecord]: ...


class ActivityEventRepository(ABC):
    @abstractmethod
    def save(self, event: ActivityEvent) -> None: ...

    @abstractmethod
    def list_by_project(self, project_id: UUID) -> Sequence[ActivityEvent]: ...

    @abstractmethod
    def list_by_organization(
        self, organization_id: UUID
    ) -> Sequence[ActivityEvent]: ...
