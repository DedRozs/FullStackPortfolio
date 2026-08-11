from __future__ import annotations

import logging
from uuid import UUID

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.client_portal import models as orm
from apps.client_portal.application.dtos import (
    GrantApprovalCommand,
    ListActivityEventsQuery,
    ListInvoicesQuery,
    ListMessagesQuery,
    RejectApprovalCommand,
    RequestRevisionCommand,
    SendMessageCommand,
    SubmitProjectForApprovalCommand,
    UploadFileCommand,
)
from apps.client_portal.application.use_cases import (
    GrantApproval,
    ListActivityEvents,
    ListInvoices,
    ListMessages,
    RejectApproval,
    RequestRevision,
    SendMessage,
    SubmitProjectForApproval,
    UploadFile,
)
from apps.client_portal.infrastructure.permissions import IsStaffOrClientOfOrganization
from core.demo_guard import DemoReadOnlyMixin
from apps.client_portal.infrastructure.repositories import (
    DjangoActivityEventRepository,
    DjangoApprovalRepository,
    DjangoInvoiceRecordRepository,
    DjangoMessageRepository,
    DjangoMessageThreadRepository,
    DjangoProjectRepository,
)
from apps.client_portal.infrastructure.serializers import (
    ActivityEventSerializer,
    ApprovalSerializer,
    ClientOrganizationSerializer,
    DeliverableSerializer,
    DeliverableVersionSerializer,
    FileRecordSerializer,
    InvoiceRecordSerializer,
    MessageSerializer,
    MessageThreadSerializer,
    MilestoneSerializer,
    ProjectSerializer,
    UserProfileSerializer,
)
from apps.client_portal.infrastructure.storage import GCSFileStorageAdapter

_ALLOWED_MIME_TYPES: frozenset[str] = frozenset({
    # Documents
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    'text/plain',
    'text/csv',
    # Images
    'image/jpeg',
    'image/png',
    'image/gif',
    'image/webp',
    # Archives
    'application/zip',
    'application/x-zip-compressed',
})

_MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024  # 10 MB
_MAX_MESSAGE_BODY_LENGTH: int = 4000

logger = logging.getLogger(__name__)


def _profile_for(request: Request) -> orm.UserProfile | None:
    cached = getattr(request, '_portal_profile_cache', _CACHE_MISS)
    if cached is not _CACHE_MISS:
        return cached
    try:
        profile = orm.UserProfile.objects.get(user=request.user)
    except orm.UserProfile.DoesNotExist:
        profile = None
    request._portal_profile_cache = profile  # type: ignore[attr-defined]
    return profile


_CACHE_MISS = object()


class ClientOrganizationViewSet(DemoReadOnlyMixin, ModelViewSet):
    serializer_class = ClientOrganizationSerializer
    permission_classes = [IsStaffOrClientOfOrganization]

    def get_queryset(self):
        if self.request.user.is_staff:
            return orm.ClientOrganization.objects.all()
        profile = _profile_for(self.request)
        if profile and profile.organization_id:
            return orm.ClientOrganization.objects.filter(pk=profile.organization_id)
        return orm.ClientOrganization.objects.none()


class UserProfileViewSet(DemoReadOnlyMixin, ModelViewSet):
    serializer_class = UserProfileSerializer
    permission_classes = [IsStaffOrClientOfOrganization]

    def get_queryset(self):
        if self.request.user.is_staff:
            return orm.UserProfile.objects.all()
        profile = _profile_for(self.request)
        if profile and profile.organization_id:
            return orm.UserProfile.objects.filter(organization_id=profile.organization_id)
        return orm.UserProfile.objects.none()


class ProjectViewSet(DemoReadOnlyMixin, ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [IsStaffOrClientOfOrganization]

    def get_queryset(self):
        if self.request.user.is_staff:
            return orm.Project.objects.all()
        profile = _profile_for(self.request)
        if profile and profile.organization_id:
            return orm.Project.objects.filter(organization_id=profile.organization_id)
        return orm.Project.objects.none()

    @action(detail=True, methods=['post'], url_path='submit-for-approval')
    def submit_for_approval(self, request: Request, pk: str = None) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        profile = _profile_for(request)
        if profile is None:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_403_FORBIDDEN)
        use_case = SubmitProjectForApproval(
            project_repo=DjangoProjectRepository(),
            activity_repo=DjangoActivityEventRepository(),
        )
        try:
            dto = use_case.execute(
                SubmitProjectForApprovalCommand(
                    project_id=UUID(str(pk)),
                    actor_id=profile.id,
                )
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': dto.status})


class MilestoneViewSet(DemoReadOnlyMixin, ModelViewSet):
    serializer_class = MilestoneSerializer
    permission_classes = [IsStaffOrClientOfOrganization]

    def get_queryset(self):
        if self.request.user.is_staff:
            return orm.Milestone.objects.all()
        profile = _profile_for(self.request)
        if profile and profile.organization_id:
            return orm.Milestone.objects.filter(
                project__organization_id=profile.organization_id
            )
        return orm.Milestone.objects.none()


class DeliverableViewSet(DemoReadOnlyMixin, ModelViewSet):
    serializer_class = DeliverableSerializer
    permission_classes = [IsStaffOrClientOfOrganization]

    def get_queryset(self):
        if self.request.user.is_staff:
            return orm.Deliverable.objects.all()
        profile = _profile_for(self.request)
        if profile and profile.organization_id:
            return orm.Deliverable.objects.filter(
                milestone__project__organization_id=profile.organization_id
            )
        return orm.Deliverable.objects.none()


class DeliverableVersionViewSet(DemoReadOnlyMixin, ModelViewSet):
    serializer_class = DeliverableVersionSerializer
    permission_classes = [IsStaffOrClientOfOrganization]

    def get_queryset(self):
        if self.request.user.is_staff:
            return orm.DeliverableVersion.objects.all()
        profile = _profile_for(self.request)
        if profile and profile.organization_id:
            return orm.DeliverableVersion.objects.filter(
                deliverable__milestone__project__organization_id=profile.organization_id
            )
        return orm.DeliverableVersion.objects.none()


class ApprovalViewSet(DemoReadOnlyMixin, ModelViewSet):
    serializer_class = ApprovalSerializer
    permission_classes = [IsStaffOrClientOfOrganization]

    def get_queryset(self):
        if self.request.user.is_staff:
            return orm.Approval.objects.all()
        profile = _profile_for(self.request)
        if profile and profile.organization_id:
            return orm.Approval.objects.filter(
                deliverable_version__deliverable__milestone__project__organization_id=profile.organization_id
            )
        return orm.Approval.objects.none()

    @action(detail=True, methods=['post'], url_path='grant')
    def grant(self, request: Request, pk: str = None) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        profile = _profile_for(request)
        if profile is None:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_403_FORBIDDEN)
        use_case = GrantApproval(
            approval_repo=DjangoApprovalRepository(),
            activity_repo=DjangoActivityEventRepository(),
        )
        try:
            dto = use_case.execute(
                GrantApprovalCommand(
                    approval_id=UUID(str(pk)),
                    reviewer_id=profile.id,
                    comment=request.data.get('comment'),
                )
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        # Fire automation trigger
        try:
            from apps.workflow_automation.engine import fire_trigger
            fire_trigger(
                'deliverable.approved',
                {
                    'trigger_type': 'deliverable.approved',
                    'source_id': str(pk),
                    'source_type': 'Approval',
                    'payload': {
                        'reviewer_id': str(profile.id) if profile else None,
                    },
                },
            )
        except Exception:
            import logging as _logging
            _logging.getLogger(__name__).exception('fire_trigger failed for deliverable.approved')
        return Response({'status': dto.status, 'decided_at': dto.decided_at})

    @action(detail=True, methods=['post'], url_path='reject')
    def reject(self, request: Request, pk: str = None) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        profile = _profile_for(request)
        if profile is None:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_403_FORBIDDEN)
        use_case = RejectApproval(
            approval_repo=DjangoApprovalRepository(),
            activity_repo=DjangoActivityEventRepository(),
        )
        try:
            dto = use_case.execute(
                RejectApprovalCommand(
                    approval_id=UUID(str(pk)),
                    reviewer_id=profile.id,
                    comment=request.data.get('comment', ''),
                )
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': dto.status, 'decided_at': dto.decided_at})

    @action(detail=True, methods=['post'], url_path='request-revision')
    def request_revision(self, request: Request, pk: str = None) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        profile = _profile_for(request)
        if profile is None:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_403_FORBIDDEN)
        use_case = RequestRevision(
            approval_repo=DjangoApprovalRepository(),
            activity_repo=DjangoActivityEventRepository(),
        )
        try:
            dto = use_case.execute(
                RequestRevisionCommand(
                    approval_id=UUID(str(pk)),
                    reviewer_id=profile.id,
                    comment=request.data.get('comment', ''),
                )
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'status': dto.status, 'decided_at': dto.decided_at})


class MessageThreadViewSet(DemoReadOnlyMixin, ModelViewSet):
    serializer_class = MessageThreadSerializer
    permission_classes = [IsStaffOrClientOfOrganization]

    def get_queryset(self):
        if self.request.user.is_staff:
            return orm.MessageThread.objects.all()
        profile = _profile_for(self.request)
        if profile and profile.organization_id:
            return orm.MessageThread.objects.filter(
                project__organization_id=profile.organization_id
            )
        return orm.MessageThread.objects.none()


class MessageViewSet(DemoReadOnlyMixin, ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [IsStaffOrClientOfOrganization]

    def get_queryset(self):
        if self.request.user.is_staff:
            return orm.Message.objects.select_related('sender').all()
        profile = _profile_for(self.request)
        if profile and profile.organization_id:
            return orm.Message.objects.select_related('sender').filter(
                thread__project__organization_id=profile.organization_id
            )
        return orm.Message.objects.none()

    @action(detail=False, methods=['post'], url_path='send')
    def send(self, request: Request) -> Response:
        if (block := self._demo_block()) is not None:
            return block
        profile = _profile_for(request)
        if profile is None:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_403_FORBIDDEN)
        body_text = request.data.get('body', '')
        if not body_text or not body_text.strip():
            return Response({'detail': 'Message body is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if len(body_text) > _MAX_MESSAGE_BODY_LENGTH:
            return Response(
                {'detail': f'Message body exceeds the {_MAX_MESSAGE_BODY_LENGTH}-character limit.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            thread_id = UUID(request.data['thread_id'])
        except (KeyError, ValueError):
            return Response({'detail': 'Invalid or missing thread_id.'}, status=status.HTTP_400_BAD_REQUEST)
        # Verify the thread belongs to the user's organization.
        if not request.user.is_staff:
            owns_thread = orm.MessageThread.objects.filter(
                pk=thread_id,
                project__organization_id=profile.organization_id,
            ).exists()
            if not owns_thread:
                return Response({'detail': 'Thread not found.'}, status=status.HTTP_404_NOT_FOUND)
        use_case = SendMessage(
            message_repo=DjangoMessageRepository(),
            thread_repo=DjangoMessageThreadRepository(),
            activity_repo=DjangoActivityEventRepository(),
        )
        try:
            dto = use_case.execute(
                SendMessageCommand(
                    thread_id=thread_id,
                    sender_id=profile.id,
                    body=body_text,
                )
            )
        except (ValueError, KeyError) as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'id': str(dto.id),
            'body': dto.body,
            'created_at': dto.created_at,
            'sender_email': profile.email,
        })


class FileRecordViewSet(DemoReadOnlyMixin, ModelViewSet):
    serializer_class = FileRecordSerializer
    permission_classes = [IsStaffOrClientOfOrganization]

    def get_queryset(self):
        if self.request.user.is_staff:
            return orm.FileRecord.objects.all()
        profile = _profile_for(self.request)
        if profile and profile.organization_id:
            return orm.FileRecord.objects.filter(
                uploaded_by__organization_id=profile.organization_id
            )
        return orm.FileRecord.objects.none()

    def _reject_if_demo(self, request: Request) -> Response | None:
        profile = _profile_for(request)
        if profile and profile.is_demo:
            return Response(
                {'detail': 'Demo accounts cannot upload or delete files.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        return None

    def destroy(self, request: Request, *args, **kwargs) -> Response:
        rejection = self._reject_if_demo(request)
        if rejection is not None:
            return rejection
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='upload')
    def upload(self, request: Request) -> Response:
        profile = _profile_for(request)
        if profile is None:
            return Response({'detail': 'Profile not found.'}, status=status.HTTP_403_FORBIDDEN)
        if profile.is_demo:
            return Response(
                {'detail': 'Demo accounts cannot upload files.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        uploaded = request.FILES.get('file')
        if uploaded is None:
            return Response({'detail': 'No file provided.'}, status=status.HTTP_400_BAD_REQUEST)
        if uploaded.size > _MAX_UPLOAD_BYTES:
            return Response(
                {'detail': f'File exceeds the 10 MB limit ({uploaded.size} bytes).'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        declared_mime = (uploaded.content_type or '').split(';')[0].strip().lower()
        if declared_mime not in _ALLOWED_MIME_TYPES:
            return Response(
                {'detail': f'File type "{declared_mime}" is not permitted.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        dv_id_raw = request.data.get('deliverable_version_id')
        msg_id_raw = request.data.get('message_id')
        use_case = UploadFile(
            file_repo=__import__(
                'apps.client_portal.infrastructure.repositories',
                fromlist=['DjangoFileRecordRepository'],
            ).DjangoFileRecordRepository(),
            storage=GCSFileStorageAdapter(),
            activity_repo=DjangoActivityEventRepository(),
        )
        try:
            dto = use_case.execute(
                UploadFileCommand(
                    filename=uploaded.name,
                    content_type=uploaded.content_type or 'application/octet-stream',
                    file_size_bytes=uploaded.size,
                    file_data=uploaded.read(),
                    deliverable_version_id=UUID(dv_id_raw) if dv_id_raw else None,
                    message_id=UUID(msg_id_raw) if msg_id_raw else None,
                    uploaded_by_id=profile.id,
                )
            )
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(
            {
                'id': str(dto.id),
                'filename': dto.filename,
                'download_url': dto.download_url,
                'file_size_bytes': dto.file_size_bytes,
            },
            status=status.HTTP_201_CREATED,
        )


class InvoiceRecordViewSet(DemoReadOnlyMixin, ModelViewSet):
    serializer_class = InvoiceRecordSerializer
    permission_classes = [IsStaffOrClientOfOrganization]

    def get_queryset(self):
        if self.request.user.is_staff:
            return orm.InvoiceRecord.objects.all()
        profile = _profile_for(self.request)
        if profile and profile.organization_id:
            return orm.InvoiceRecord.objects.filter(organization_id=profile.organization_id)
        return orm.InvoiceRecord.objects.none()

    @action(detail=False, methods=['get'], url_path='my-invoices')
    def my_invoices(self, request: Request) -> Response:
        profile = _profile_for(request)
        if profile is None or not profile.organization_id:
            return Response([], status=status.HTTP_200_OK)
        use_case = ListInvoices(
            invoice_repo=DjangoInvoiceRecordRepository(),
        )
        dtos = use_case.execute(ListInvoicesQuery(organization_id=profile.organization_id))
        return Response(
            [
                {
                    'id': str(d.id),
                    'status': d.status,
                    'amount': str(d.amount),
                    'due_date': str(d.due_date) if d.due_date else None,
                    'issued_at': d.issued_at.isoformat() if d.issued_at else None,
                }
                for d in dtos
            ]
        )


class ActivityEventViewSet(ModelViewSet):
    serializer_class = ActivityEventSerializer
    permission_classes = [IsStaffOrClientOfOrganization]
    http_method_names = ['get', 'head', 'options']

    def get_queryset(self):
        if self.request.user.is_staff:
            return orm.ActivityEvent.objects.all()
        profile = _profile_for(self.request)
        if profile and profile.organization_id:
            return orm.ActivityEvent.objects.filter(
                organization_id=profile.organization_id
            )
        return orm.ActivityEvent.objects.none()
