from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

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
from apps.client_portal.domain.value_objects import ApprovalStatus, ProjectStatus

from .dtos import (
    ActivateProjectCommand,
    ActivityEventDTO,
    AddDeliverableVersionCommand,
    ApprovalDTO,
    ApproveProjectCommand,
    ClientOrganizationDTO,
    CompleteMilestoneCommand,
    CreateMilestoneCommand,
    CreateProjectCommand,
    CreateUserProfileCommand,
    DeliverableVersionDTO,
    FileRecordDTO,
    GrantApprovalCommand,
    InvoiceRecordDTO,
    ListActivityEventsQuery,
    ListFilesForDeliverableQuery,
    ListInvoicesQuery,
    ListMessagesQuery,
    MessageDTO,
    MilestoneDTO,
    ProjectDTO,
    RegisterClientOrganizationCommand,
    RejectApprovalCommand,
    RejectProjectCommand,
    RequestApprovalCommand,
    RequestRevisionCommand,
    SendMessageCommand,
    SubmitProjectForApprovalCommand,
    UploadFileCommand,
    UserProfileDTO,
)
from .ports import FileStoragePort

logger = logging.getLogger(__name__)

_UTC = timezone.utc


def _now() -> datetime:
    return datetime.now(_UTC)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _org_to_dto(org: ClientOrganization) -> ClientOrganizationDTO:
    return ClientOrganizationDTO(
        id=org.id,
        name=org.name,
        slug=org.slug,
        created_at=org.created_at,
    )


def _project_to_dto(project: Project) -> ProjectDTO:
    return ProjectDTO(
        id=project.id,
        name=project.name,
        organization_id=project.organization_id,
        status=project.status.value,
        description=project.description,
        target_date=project.target_date,
        created_at=project.created_at,
    )


def _milestone_to_dto(milestone: Milestone) -> MilestoneDTO:
    return MilestoneDTO(
        id=milestone.id,
        name=milestone.name,
        project_id=milestone.project_id,
        status=milestone.status.value,
        target_date=milestone.target_date,
        created_at=milestone.created_at,
    )


def _approval_to_dto(approval: Approval) -> ApprovalDTO:
    return ApprovalDTO(
        id=approval.id,
        deliverable_version_id=approval.deliverable_version_id,
        reviewer_id=approval.reviewer_id,
        status=approval.status.value,
        comment=approval.comment,
        decided_at=approval.decided_at,
        created_at=approval.created_at,
    )


def _record_activity(
    activity_repo: ActivityEventRepository,
    event_type: str,
    actor_id: object,
    project_id: object = None,
    organization_id: object = None,
    payload: dict | None = None,
) -> None:
    event = ActivityEvent(
        id=uuid.uuid4(),
        event_type=event_type,
        actor_id=actor_id,
        project_id=project_id,
        organization_id=organization_id,
        payload=payload or {},
        occurred_at=_now(),
    )
    activity_repo.save(event)


# ---------------------------------------------------------------------------
# Use cases
# ---------------------------------------------------------------------------


class RegisterClientOrganization:
    def __init__(
        self,
        org_repo: ClientOrganizationRepository,
        activity_repo: ActivityEventRepository,
    ) -> None:
        self._orgs = org_repo
        self._activity = activity_repo

    def execute(self, cmd: RegisterClientOrganizationCommand) -> ClientOrganizationDTO:
        org = ClientOrganization(
            id=uuid.uuid4(),
            name=cmd.name,
            slug=cmd.slug,
            created_at=_now(),
        )
        self._orgs.save(org)
        _record_activity(
            self._activity,
            'ClientOrganizationRegistered',
            actor_id=None,
            organization_id=org.id,
            payload={'name': org.name, 'slug': org.slug},
        )
        return _org_to_dto(org)


class CreateUserProfile:
    def __init__(
        self,
        profile_repo: UserProfileRepository,
        org_repo: ClientOrganizationRepository,
    ) -> None:
        self._profiles = profile_repo
        self._orgs = org_repo

    def execute(self, cmd: CreateUserProfileCommand) -> UserProfileDTO:
        if cmd.is_client and cmd.organization_id is not None:
            org = self._orgs.get_by_id(cmd.organization_id)
            if org is None:
                raise ValueError(f'Organization {cmd.organization_id} not found')
        profile = UserProfile(
            id=uuid.uuid4(),
            user_id=cmd.user_id,
            email=cmd.email,
            is_client=cmd.is_client,
            organization_id=cmd.organization_id,
            created_at=_now(),
        )
        self._profiles.save(profile)
        return UserProfileDTO(
            id=profile.id,
            user_id=profile.user_id,
            email=profile.email,
            is_client=profile.is_client,
            organization_id=profile.organization_id,
            created_at=profile.created_at,
        )


class CreateProject:
    def __init__(
        self,
        project_repo: ProjectRepository,
        org_repo: ClientOrganizationRepository,
        activity_repo: ActivityEventRepository,
    ) -> None:
        self._projects = project_repo
        self._orgs = org_repo
        self._activity = activity_repo

    def execute(self, cmd: CreateProjectCommand) -> ProjectDTO:
        org = self._orgs.get_by_id(cmd.organization_id)
        if org is None:
            raise ValueError(f'Organization {cmd.organization_id} not found')
        project = Project(
            id=uuid.uuid4(),
            name=cmd.name,
            organization_id=cmd.organization_id,
            status=ProjectStatus.ACTIVE,
            description=cmd.description,
            target_date=cmd.target_date,
            created_at=_now(),
        )
        self._projects.save(project)
        _record_activity(
            self._activity,
            'ProjectCreated',
            actor_id=cmd.actor_id,
            project_id=project.id,
            organization_id=cmd.organization_id,
            payload={'name': project.name},
        )
        return _project_to_dto(project)


class ActivateProject:
    def __init__(
        self,
        project_repo: ProjectRepository,
        activity_repo: ActivityEventRepository,
    ) -> None:
        self._projects = project_repo
        self._activity = activity_repo

    def execute(self, cmd: ActivateProjectCommand) -> ProjectDTO:
        project = self._projects.get_by_id(cmd.project_id)
        if project is None:
            raise ValueError(f'Project {cmd.project_id} not found')
        project.status = ProjectStatus.ACTIVE
        self._projects.save(project)
        _record_activity(
            self._activity,
            'ProjectActivated',
            actor_id=cmd.actor_id,
            project_id=project.id,
            organization_id=project.organization_id,
        )
        return _project_to_dto(project)


class SubmitProjectForApproval:
    def __init__(
        self,
        project_repo: ProjectRepository,
        activity_repo: ActivityEventRepository,
    ) -> None:
        self._projects = project_repo
        self._activity = activity_repo

    def execute(self, cmd: SubmitProjectForApprovalCommand) -> ProjectDTO:
        project = self._projects.get_by_id(cmd.project_id)
        if project is None:
            raise ValueError(f'Project {cmd.project_id} not found')
        project.submit_for_approval()
        self._projects.save(project)
        _record_activity(
            self._activity,
            'ProjectSubmittedForApproval',
            actor_id=cmd.actor_id,
            project_id=project.id,
            organization_id=project.organization_id,
        )
        return _project_to_dto(project)


class ApproveProject:
    def __init__(
        self,
        project_repo: ProjectRepository,
        activity_repo: ActivityEventRepository,
    ) -> None:
        self._projects = project_repo
        self._activity = activity_repo

    def execute(self, cmd: ApproveProjectCommand) -> ProjectDTO:
        project = self._projects.get_by_id(cmd.project_id)
        if project is None:
            raise ValueError(f'Project {cmd.project_id} not found')
        project.mark_complete()
        self._projects.save(project)
        _record_activity(
            self._activity,
            'ProjectCompleted',
            actor_id=cmd.actor_id,
            project_id=project.id,
            organization_id=project.organization_id,
        )
        return _project_to_dto(project)


class RejectProject:
    def __init__(
        self,
        project_repo: ProjectRepository,
        activity_repo: ActivityEventRepository,
    ) -> None:
        self._projects = project_repo
        self._activity = activity_repo

    def execute(self, cmd: RejectProjectCommand) -> ProjectDTO:
        project = self._projects.get_by_id(cmd.project_id)
        if project is None:
            raise ValueError(f'Project {cmd.project_id} not found')
        project.return_to_active()
        self._projects.save(project)
        _record_activity(
            self._activity,
            'ProjectReturnedToActive',
            actor_id=cmd.actor_id,
            project_id=project.id,
            organization_id=project.organization_id,
        )
        return _project_to_dto(project)


class CreateMilestone:
    def __init__(
        self,
        milestone_repo: MilestoneRepository,
        project_repo: ProjectRepository,
    ) -> None:
        self._milestones = milestone_repo
        self._projects = project_repo

    def execute(self, cmd: CreateMilestoneCommand) -> MilestoneDTO:
        project = self._projects.get_by_id(cmd.project_id)
        if project is None:
            raise ValueError(f'Project {cmd.project_id} not found')
        from apps.client_portal.domain.value_objects import MilestoneStatus
        milestone = Milestone(
            id=uuid.uuid4(),
            name=cmd.name,
            project_id=cmd.project_id,
            status=MilestoneStatus.PENDING,
            target_date=cmd.target_date,
            created_at=_now(),
        )
        self._milestones.save(milestone)
        return _milestone_to_dto(milestone)


class CompleteMilestone:
    def __init__(
        self,
        milestone_repo: MilestoneRepository,
        activity_repo: ActivityEventRepository,
    ) -> None:
        self._milestones = milestone_repo
        self._activity = activity_repo

    def execute(self, cmd: CompleteMilestoneCommand) -> MilestoneDTO:
        milestone = self._milestones.get_by_id(cmd.milestone_id)
        if milestone is None:
            raise ValueError(f'Milestone {cmd.milestone_id} not found')
        milestone.complete()
        self._milestones.save(milestone)
        _record_activity(
            self._activity,
            'MilestoneCompleted',
            actor_id=cmd.actor_id,
            project_id=milestone.project_id,
            payload={'name': milestone.name},
        )
        return _milestone_to_dto(milestone)


class AddDeliverableVersion:
    def __init__(
        self,
        deliverable_repo: DeliverableRepository,
        version_repo: DeliverableVersionRepository,
        activity_repo: ActivityEventRepository,
    ) -> None:
        self._deliverables = deliverable_repo
        self._versions = version_repo
        self._activity = activity_repo

    def execute(self, cmd: AddDeliverableVersionCommand) -> DeliverableVersionDTO:
        deliverable = self._deliverables.get_by_id(cmd.deliverable_id)
        if deliverable is None:
            raise ValueError(f'Deliverable {cmd.deliverable_id} not found')
        new_version_number = deliverable.current_version_number + 1
        deliverable.current_version_number = new_version_number
        self._deliverables.save(deliverable)
        version = DeliverableVersion(
            id=uuid.uuid4(),
            deliverable_id=cmd.deliverable_id,
            version_number=new_version_number,
            notes=cmd.notes,
            created_at=_now(),
        )
        self._versions.save(version)
        _record_activity(
            self._activity,
            'DeliverableRevisionSubmitted',
            actor_id=cmd.actor_id,
            payload={
                'deliverable_id': str(cmd.deliverable_id),
                'version_number': new_version_number,
            },
        )
        return DeliverableVersionDTO(
            id=version.id,
            deliverable_id=version.deliverable_id,
            version_number=version.version_number,
            notes=version.notes,
            created_at=version.created_at,
        )


class RequestApproval:
    def __init__(
        self,
        version_repo: DeliverableVersionRepository,
        approval_repo: ApprovalRepository,
        activity_repo: ActivityEventRepository,
    ) -> None:
        self._versions = version_repo
        self._approvals = approval_repo
        self._activity = activity_repo

    def execute(self, cmd: RequestApprovalCommand) -> ApprovalDTO:
        version = self._versions.get_by_id(cmd.deliverable_version_id)
        if version is None:
            raise ValueError(f'DeliverableVersion {cmd.deliverable_version_id} not found')
        existing = self._approvals.get_by_deliverable_version(cmd.deliverable_version_id)
        if existing is not None:
            raise ValueError('An approval already exists for this deliverable version')
        approval = Approval(
            id=uuid.uuid4(),
            deliverable_version_id=cmd.deliverable_version_id,
            reviewer_id=cmd.reviewer_id,
            status=ApprovalStatus.PENDING,
            comment=None,
            decided_at=None,
            created_at=_now(),
        )
        self._approvals.save(approval)
        _record_activity(
            self._activity,
            'ApprovalRequested',
            actor_id=cmd.actor_id,
            payload={
                'deliverable_version_id': str(cmd.deliverable_version_id),
                'reviewer_id': str(cmd.reviewer_id),
            },
        )
        return _approval_to_dto(approval)


class GrantApproval:
    def __init__(
        self,
        approval_repo: ApprovalRepository,
        activity_repo: ActivityEventRepository,
    ) -> None:
        self._approvals = approval_repo
        self._activity = activity_repo

    def execute(self, cmd: GrantApprovalCommand) -> ApprovalDTO:
        approval = self._approvals.get_by_id(cmd.approval_id)
        if approval is None:
            raise ValueError(f'Approval {cmd.approval_id} not found')
        if approval.reviewer_id != cmd.reviewer_id:
            raise ValueError('Only the assigned reviewer can grant approval')
        approval.approve(comment=cmd.comment)
        approval.decided_at = _now()
        self._approvals.save(approval)
        _record_activity(
            self._activity,
            'DeliverableApproved',
            actor_id=cmd.reviewer_id,
            payload={
                'approval_id': str(approval.id),
                'comment': cmd.comment,
            },
        )
        return _approval_to_dto(approval)


class RejectApproval:
    def __init__(
        self,
        approval_repo: ApprovalRepository,
        activity_repo: ActivityEventRepository,
    ) -> None:
        self._approvals = approval_repo
        self._activity = activity_repo

    def execute(self, cmd: RejectApprovalCommand) -> ApprovalDTO:
        approval = self._approvals.get_by_id(cmd.approval_id)
        if approval is None:
            raise ValueError(f'Approval {cmd.approval_id} not found')
        if approval.reviewer_id != cmd.reviewer_id:
            raise ValueError('Only the assigned reviewer can reject approval')
        approval.reject(comment=cmd.comment)
        approval.decided_at = _now()
        self._approvals.save(approval)
        _record_activity(
            self._activity,
            'DeliverableRejected',
            actor_id=cmd.reviewer_id,
            payload={
                'approval_id': str(approval.id),
                'comment': cmd.comment,
            },
        )
        return _approval_to_dto(approval)


class RequestRevision:
    def __init__(
        self,
        approval_repo: ApprovalRepository,
        activity_repo: ActivityEventRepository,
    ) -> None:
        self._approvals = approval_repo
        self._activity = activity_repo

    def execute(self, cmd: RequestRevisionCommand) -> ApprovalDTO:
        approval = self._approvals.get_by_id(cmd.approval_id)
        if approval is None:
            raise ValueError(f'Approval {cmd.approval_id} not found')
        if approval.reviewer_id != cmd.reviewer_id:
            raise ValueError('Only the assigned reviewer can request revision')
        approval.request_revision(comment=cmd.comment)
        approval.decided_at = _now()
        self._approvals.save(approval)
        _record_activity(
            self._activity,
            'DeliverableRevisionRequested',
            actor_id=cmd.reviewer_id,
            payload={
                'approval_id': str(approval.id),
                'comment': cmd.comment,
            },
        )
        return _approval_to_dto(approval)


class UploadFile:
    def __init__(
        self,
        file_repo: FileRecordRepository,
        storage: FileStoragePort,
        activity_repo: ActivityEventRepository,
    ) -> None:
        self._files = file_repo
        self._storage = storage
        self._activity = activity_repo

    def execute(self, cmd: UploadFileCommand) -> FileRecordDTO:
        storage_path = self._storage.upload(
            file_data=cmd.file_data,
            filename=cmd.filename,
            content_type=cmd.content_type,
        )
        record = FileRecord(
            id=uuid.uuid4(),
            filename=cmd.filename,
            storage_path=storage_path,
            mime_type=cmd.content_type,
            file_size_bytes=cmd.file_size_bytes,
            deliverable_version_id=cmd.deliverable_version_id,
            message_id=cmd.message_id,
            uploaded_by_id=cmd.uploaded_by_id,
            created_at=_now(),
        )
        self._files.save(record)
        _record_activity(
            self._activity,
            'FileRecordUploaded',
            actor_id=cmd.uploaded_by_id,
            payload={
                'filename': cmd.filename,
                'file_size_bytes': cmd.file_size_bytes,
            },
        )
        download_url = self._storage.get_url(storage_path)
        return FileRecordDTO(
            id=record.id,
            filename=record.filename,
            storage_path=record.storage_path,
            mime_type=record.mime_type,
            file_size_bytes=record.file_size_bytes,
            deliverable_version_id=record.deliverable_version_id,
            message_id=record.message_id,
            uploaded_by_id=record.uploaded_by_id,
            created_at=record.created_at,
            download_url=download_url,
        )


class ListFilesForDeliverable:
    def __init__(self, file_repo: FileRecordRepository) -> None:
        self._files = file_repo

    def execute(self, query: ListFilesForDeliverableQuery) -> list[FileRecordDTO]:
        records = self._files.list_by_deliverable_version(query.deliverable_version_id)
        return [
            FileRecordDTO(
                id=r.id,
                filename=r.filename,
                storage_path=r.storage_path,
                mime_type=r.mime_type,
                file_size_bytes=r.file_size_bytes,
                deliverable_version_id=r.deliverable_version_id,
                message_id=r.message_id,
                uploaded_by_id=r.uploaded_by_id,
                created_at=r.created_at,
            )
            for r in records
        ]


class SendMessage:
    def __init__(
        self,
        message_repo: MessageRepository,
        thread_repo: MessageThreadRepository,
        activity_repo: ActivityEventRepository,
    ) -> None:
        self._messages = message_repo
        self._threads = thread_repo
        self._activity = activity_repo

    def execute(self, cmd: SendMessageCommand) -> MessageDTO:
        thread = self._threads.get_by_id(cmd.thread_id)
        if thread is None:
            raise ValueError(f'MessageThread {cmd.thread_id} not found')
        if not cmd.body:
            raise ValueError('Message body must not be blank')
        message = Message(
            id=uuid.uuid4(),
            thread_id=cmd.thread_id,
            sender_id=cmd.sender_id,
            body=cmd.body,
            created_at=_now(),
        )
        self._messages.save(message)
        _record_activity(
            self._activity,
            'MessagePosted',
            actor_id=cmd.sender_id,
            project_id=thread.project_id,
            payload={'thread_id': str(cmd.thread_id)},
        )
        return MessageDTO(
            id=message.id,
            thread_id=message.thread_id,
            sender_id=message.sender_id,
            body=message.body,
            created_at=message.created_at,
        )


class ListMessages:
    def __init__(
        self,
        message_repo: MessageRepository,
        thread_repo: MessageThreadRepository,
    ) -> None:
        self._messages = message_repo
        self._threads = thread_repo

    def execute(self, query: ListMessagesQuery) -> list[MessageDTO]:
        thread = self._threads.get_by_id(query.thread_id)
        if thread is None:
            raise ValueError(f'MessageThread {query.thread_id} not found')
        messages = self._messages.list_by_thread(query.thread_id)
        return [
            MessageDTO(
                id=m.id,
                thread_id=m.thread_id,
                sender_id=m.sender_id,
                body=m.body,
                created_at=m.created_at,
            )
            for m in messages
        ]


class ListInvoices:
    def __init__(self, invoice_repo: InvoiceRecordRepository) -> None:
        self._invoices = invoice_repo

    def execute(self, query: ListInvoicesQuery) -> list[InvoiceRecordDTO]:
        invoices = self._invoices.list_by_organization(query.organization_id)
        return [
            InvoiceRecordDTO(
                id=inv.id,
                organization_id=inv.organization_id,
                project_id=inv.project_id,
                status=inv.status.value,
                amount=inv.amount,
                due_date=inv.due_date,
                issued_at=inv.issued_at,
                created_at=inv.created_at,
            )
            for inv in invoices
        ]


class ListActivityEvents:
    def __init__(self, activity_repo: ActivityEventRepository) -> None:
        self._activity = activity_repo

    def execute(self, query: ListActivityEventsQuery) -> list[ActivityEventDTO]:
        if query.project_id is not None:
            events = self._activity.list_by_project(query.project_id)
        elif query.organization_id is not None:
            events = self._activity.list_by_organization(query.organization_id)
        else:
            events = []
        return [
            ActivityEventDTO(
                id=e.id,
                event_type=e.event_type,
                actor_id=e.actor_id,
                project_id=e.project_id,
                organization_id=e.organization_id,
                payload=e.payload,
                occurred_at=e.occurred_at,
            )
            for e in events
        ]
