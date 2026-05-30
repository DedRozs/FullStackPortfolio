from __future__ import annotations

import logging
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
from apps.client_portal.domain.repositories import (
    ActivityEventRepository,
    ApprovalRepository,
    ClientOrganizationRepository,
    DeliverableRepository,
    DeliverableVersionRepository,
    FileRecordRepository,
    InvoiceRecordRepository,
    MessageRepository,
    MessageThreadRepository,
    MilestoneRepository,
    ProjectRepository,
    UserProfileRepository,
)
from apps.client_portal.domain.value_objects import (
    ApprovalStatus,
    InvoiceStatus,
    MilestoneStatus,
    ProjectStatus,
)
from apps.client_portal import models as orm

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Private mappers
# ---------------------------------------------------------------------------


def _org_model_to_entity(obj: orm.ClientOrganization) -> ClientOrganization:
    return ClientOrganization(
        id=obj.id,
        name=obj.name,
        slug=obj.slug,
        created_at=obj.created_at,
    )


def _profile_model_to_entity(obj: orm.UserProfile) -> UserProfile:
    return UserProfile(
        id=obj.id,
        user_id=obj.user_id,
        email=obj.email,
        is_client=obj.is_client,
        organization_id=obj.organization_id,
        created_at=obj.created_at,
    )


def _project_model_to_entity(obj: orm.Project) -> Project:
    return Project(
        id=obj.id,
        name=obj.name,
        organization_id=obj.organization_id,
        status=ProjectStatus(obj.status),
        description=obj.description,
        target_date=obj.target_date,
        created_at=obj.created_at,
    )


def _milestone_model_to_entity(obj: orm.Milestone) -> Milestone:
    return Milestone(
        id=obj.id,
        name=obj.name,
        project_id=obj.project_id,
        status=MilestoneStatus(obj.status),
        target_date=obj.target_date,
        created_at=obj.created_at,
    )


def _deliverable_model_to_entity(obj: orm.Deliverable) -> Deliverable:
    return Deliverable(
        id=obj.id,
        name=obj.name,
        milestone_id=obj.milestone_id,
        description=obj.description,
        current_version_number=obj.current_version_number,
        created_at=obj.created_at,
    )


def _deliverable_version_model_to_entity(obj: orm.DeliverableVersion) -> DeliverableVersion:
    return DeliverableVersion(
        id=obj.id,
        deliverable_id=obj.deliverable_id,
        version_number=obj.version_number,
        notes=obj.notes,
        created_at=obj.created_at,
    )


def _approval_model_to_entity(obj: orm.Approval) -> Approval:
    return Approval(
        id=obj.id,
        deliverable_version_id=obj.deliverable_version_id,
        reviewer_id=obj.reviewer_id,
        status=ApprovalStatus(obj.status),
        comment=obj.comment,
        decided_at=obj.decided_at,
        created_at=obj.created_at,
    )


def _file_record_model_to_entity(obj: orm.FileRecord) -> FileRecord:
    return FileRecord(
        id=obj.id,
        filename=obj.filename,
        storage_path=obj.storage_path,
        mime_type=obj.mime_type,
        file_size_bytes=obj.file_size_bytes,
        deliverable_version_id=obj.deliverable_version_id,
        message_id=obj.message_id,
        uploaded_by_id=obj.uploaded_by_id,
        created_at=obj.created_at,
    )


def _thread_model_to_entity(obj: orm.MessageThread) -> MessageThread:
    return MessageThread(
        id=obj.id,
        subject=obj.subject,
        project_id=obj.project_id,
        created_at=obj.created_at,
    )


def _message_model_to_entity(obj: orm.Message) -> Message:
    return Message(
        id=obj.id,
        thread_id=obj.thread_id,
        sender_id=obj.sender_id,
        body=obj.body,
        created_at=obj.created_at,
    )


def _invoice_model_to_entity(obj: orm.InvoiceRecord) -> InvoiceRecord:
    return InvoiceRecord(
        id=obj.id,
        organization_id=obj.organization_id,
        project_id=obj.project_id,
        status=InvoiceStatus(obj.status),
        amount=obj.amount,
        due_date=obj.due_date,
        issued_at=obj.issued_at,
        created_at=obj.created_at,
    )


def _activity_model_to_entity(obj: orm.ActivityEvent) -> ActivityEvent:
    return ActivityEvent(
        id=obj.id,
        event_type=obj.event_type,
        actor_id=obj.actor_id,
        project_id=obj.project_id,
        organization_id=obj.organization_id,
        payload=obj.payload,
        occurred_at=obj.occurred_at,
    )


# ---------------------------------------------------------------------------
# Repository implementations
# ---------------------------------------------------------------------------


class DjangoClientOrganizationRepository(ClientOrganizationRepository):
    def get_by_id(self, organization_id: UUID) -> ClientOrganization | None:
        try:
            return _org_model_to_entity(orm.ClientOrganization.objects.get(pk=organization_id))
        except orm.ClientOrganization.DoesNotExist:
            return None

    def get_by_slug(self, slug: str) -> ClientOrganization | None:
        try:
            return _org_model_to_entity(orm.ClientOrganization.objects.get(slug=slug))
        except orm.ClientOrganization.DoesNotExist:
            return None

    def save(self, organization: ClientOrganization) -> None:
        orm.ClientOrganization.objects.update_or_create(
            pk=organization.id,
            defaults={'name': organization.name, 'slug': organization.slug},
        )

    def list_all(self) -> Sequence[ClientOrganization]:
        return [_org_model_to_entity(o) for o in orm.ClientOrganization.objects.all()]


class DjangoUserProfileRepository(UserProfileRepository):
    def get_by_id(self, profile_id: UUID) -> UserProfile | None:
        try:
            return _profile_model_to_entity(orm.UserProfile.objects.get(pk=profile_id))
        except orm.UserProfile.DoesNotExist:
            return None

    def get_by_user_id(self, user_id: int) -> UserProfile | None:
        try:
            return _profile_model_to_entity(orm.UserProfile.objects.get(user_id=user_id))
        except orm.UserProfile.DoesNotExist:
            return None

    def save(self, profile: UserProfile) -> None:
        orm.UserProfile.objects.update_or_create(
            pk=profile.id,
            defaults={
                'user_id': profile.user_id,
                'email': profile.email,
                'is_client': profile.is_client,
                'organization_id': profile.organization_id,
            },
        )

    def list_stakeholders_for_organization(
        self, organization_id: UUID
    ) -> Sequence[UserProfile]:
        qs = orm.UserProfile.objects.filter(organization_id=organization_id, is_client=True)
        return [_profile_model_to_entity(p) for p in qs]


class DjangoProjectRepository(ProjectRepository):
    def get_by_id(self, project_id: UUID) -> Project | None:
        try:
            return _project_model_to_entity(orm.Project.objects.get(pk=project_id))
        except orm.Project.DoesNotExist:
            return None

    def save(self, project: Project) -> None:
        orm.Project.objects.update_or_create(
            pk=project.id,
            defaults={
                'name': project.name,
                'organization_id': project.organization_id,
                'status': project.status.value,
                'description': project.description,
                'target_date': project.target_date,
            },
        )

    def list_by_organization(self, organization_id: UUID) -> Sequence[Project]:
        qs = orm.Project.objects.filter(organization_id=organization_id)
        return [_project_model_to_entity(p) for p in qs]

    def list_by_status(self, status: ProjectStatus) -> Sequence[Project]:
        qs = orm.Project.objects.filter(status=status.value)
        return [_project_model_to_entity(p) for p in qs]


class DjangoMilestoneRepository(MilestoneRepository):
    def get_by_id(self, milestone_id: UUID) -> Milestone | None:
        try:
            return _milestone_model_to_entity(orm.Milestone.objects.get(pk=milestone_id))
        except orm.Milestone.DoesNotExist:
            return None

    def save(self, milestone: Milestone) -> None:
        orm.Milestone.objects.update_or_create(
            pk=milestone.id,
            defaults={
                'name': milestone.name,
                'project_id': milestone.project_id,
                'status': milestone.status.value,
                'target_date': milestone.target_date,
            },
        )

    def list_by_project(self, project_id: UUID) -> Sequence[Milestone]:
        qs = orm.Milestone.objects.filter(project_id=project_id)
        return [_milestone_model_to_entity(m) for m in qs]


class DjangoDeliverableRepository(DeliverableRepository):
    def get_by_id(self, deliverable_id: UUID) -> Deliverable | None:
        try:
            return _deliverable_model_to_entity(orm.Deliverable.objects.get(pk=deliverable_id))
        except orm.Deliverable.DoesNotExist:
            return None

    def save(self, deliverable: Deliverable) -> None:
        orm.Deliverable.objects.update_or_create(
            pk=deliverable.id,
            defaults={
                'name': deliverable.name,
                'milestone_id': deliverable.milestone_id,
                'description': deliverable.description,
                'current_version_number': deliverable.current_version_number,
            },
        )

    def list_by_milestone(self, milestone_id: UUID) -> Sequence[Deliverable]:
        qs = orm.Deliverable.objects.filter(milestone_id=milestone_id)
        return [_deliverable_model_to_entity(d) for d in qs]


class DjangoDeliverableVersionRepository(DeliverableVersionRepository):
    def get_by_id(self, version_id: UUID) -> DeliverableVersion | None:
        try:
            return _deliverable_version_model_to_entity(
                orm.DeliverableVersion.objects.get(pk=version_id)
            )
        except orm.DeliverableVersion.DoesNotExist:
            return None

    def save(self, version: DeliverableVersion) -> None:
        orm.DeliverableVersion.objects.update_or_create(
            pk=version.id,
            defaults={
                'deliverable_id': version.deliverable_id,
                'version_number': version.version_number,
                'notes': version.notes,
            },
        )

    def list_by_deliverable(self, deliverable_id: UUID) -> Sequence[DeliverableVersion]:
        qs = orm.DeliverableVersion.objects.filter(deliverable_id=deliverable_id)
        return [_deliverable_version_model_to_entity(v) for v in qs]


class DjangoApprovalRepository(ApprovalRepository):
    def get_by_id(self, approval_id: UUID) -> Approval | None:
        try:
            return _approval_model_to_entity(orm.Approval.objects.get(pk=approval_id))
        except orm.Approval.DoesNotExist:
            return None

    def get_by_deliverable_version(
        self, deliverable_version_id: UUID
    ) -> Approval | None:
        try:
            return _approval_model_to_entity(
                orm.Approval.objects.get(deliverable_version_id=deliverable_version_id)
            )
        except orm.Approval.DoesNotExist:
            return None

    def save(self, approval: Approval) -> None:
        orm.Approval.objects.update_or_create(
            pk=approval.id,
            defaults={
                'deliverable_version_id': approval.deliverable_version_id,
                'reviewer_id': approval.reviewer_id,
                'status': approval.status.value,
                'comment': approval.comment,
                'decided_at': approval.decided_at,
            },
        )


class DjangoFileRecordRepository(FileRecordRepository):
    def get_by_id(self, file_record_id: UUID) -> FileRecord | None:
        try:
            return _file_record_model_to_entity(orm.FileRecord.objects.get(pk=file_record_id))
        except orm.FileRecord.DoesNotExist:
            return None

    def save(self, file_record: FileRecord) -> None:
        orm.FileRecord.objects.update_or_create(
            pk=file_record.id,
            defaults={
                'filename': file_record.filename,
                'storage_path': file_record.storage_path,
                'mime_type': file_record.mime_type,
                'file_size_bytes': file_record.file_size_bytes,
                'deliverable_version_id': file_record.deliverable_version_id,
                'message_id': file_record.message_id,
                'uploaded_by_id': file_record.uploaded_by_id,
            },
        )

    def list_by_deliverable_version(
        self, deliverable_version_id: UUID
    ) -> Sequence[FileRecord]:
        qs = orm.FileRecord.objects.filter(deliverable_version_id=deliverable_version_id)
        return [_file_record_model_to_entity(f) for f in qs]

    def list_by_message(self, message_id: UUID) -> Sequence[FileRecord]:
        qs = orm.FileRecord.objects.filter(message_id=message_id)
        return [_file_record_model_to_entity(f) for f in qs]


class DjangoMessageThreadRepository(MessageThreadRepository):
    def get_by_id(self, thread_id: UUID) -> MessageThread | None:
        try:
            return _thread_model_to_entity(orm.MessageThread.objects.get(pk=thread_id))
        except orm.MessageThread.DoesNotExist:
            return None

    def save(self, thread: MessageThread) -> None:
        orm.MessageThread.objects.update_or_create(
            pk=thread.id,
            defaults={
                'subject': thread.subject,
                'project_id': thread.project_id,
            },
        )

    def list_by_project(self, project_id: UUID) -> Sequence[MessageThread]:
        qs = orm.MessageThread.objects.filter(project_id=project_id)
        return [_thread_model_to_entity(t) for t in qs]


class DjangoMessageRepository(MessageRepository):
    def get_by_id(self, message_id: UUID) -> Message | None:
        try:
            return _message_model_to_entity(orm.Message.objects.get(pk=message_id))
        except orm.Message.DoesNotExist:
            return None

    def save(self, message: Message) -> None:
        orm.Message.objects.update_or_create(
            pk=message.id,
            defaults={
                'thread_id': message.thread_id,
                'sender_id': message.sender_id,
                'body': message.body,
            },
        )

    def list_by_thread(self, thread_id: UUID) -> Sequence[Message]:
        qs = orm.Message.objects.filter(thread_id=thread_id)
        return [_message_model_to_entity(m) for m in qs]


class DjangoInvoiceRecordRepository(InvoiceRecordRepository):
    def get_by_id(self, invoice_id: UUID) -> InvoiceRecord | None:
        try:
            return _invoice_model_to_entity(orm.InvoiceRecord.objects.get(pk=invoice_id))
        except orm.InvoiceRecord.DoesNotExist:
            return None

    def save(self, invoice: InvoiceRecord) -> None:
        orm.InvoiceRecord.objects.update_or_create(
            pk=invoice.id,
            defaults={
                'organization_id': invoice.organization_id,
                'project_id': invoice.project_id,
                'status': invoice.status.value,
                'amount': invoice.amount,
                'due_date': invoice.due_date,
                'issued_at': invoice.issued_at,
            },
        )

    def list_by_organization(self, organization_id: UUID) -> Sequence[InvoiceRecord]:
        qs = orm.InvoiceRecord.objects.filter(organization_id=organization_id)
        return [_invoice_model_to_entity(inv) for inv in qs]

    def list_by_status(self, status: InvoiceStatus) -> Sequence[InvoiceRecord]:
        qs = orm.InvoiceRecord.objects.filter(status=status.value)
        return [_invoice_model_to_entity(inv) for inv in qs]


class DjangoActivityEventRepository(ActivityEventRepository):
    def save(self, event: ActivityEvent) -> None:
        orm.ActivityEvent.objects.update_or_create(
            pk=event.id,
            defaults={
                'event_type': event.event_type,
                'actor_id': event.actor_id,
                'project_id': event.project_id,
                'organization_id': event.organization_id,
                'payload': event.payload,
            },
        )

    def list_by_project(self, project_id: UUID) -> Sequence[ActivityEvent]:
        qs = orm.ActivityEvent.objects.filter(project_id=project_id)
        return [_activity_model_to_entity(e) for e in qs]

    def list_by_organization(self, organization_id: UUID) -> Sequence[ActivityEvent]:
        qs = orm.ActivityEvent.objects.filter(organization_id=organization_id)
        return [_activity_model_to_entity(e) for e in qs]
