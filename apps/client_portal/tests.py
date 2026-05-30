"""
Unit tests for the client_portal app.

Coverage:
- ORM model __str__ methods (all 12 models, no database I/O)
- AppConfig label and name
- Domain value object invariants (value_objects.py, no I/O)
- Domain entity invariants and state transitions (model.py, no I/O)
- Repository ABC instantiation guard
- Permission class: IsClientOfOrganization org isolation
- Permission class: IsStaffOrClientOfOrganization staff bypass
- GrantApproval use case: PENDING -> APPROVED produces ActivityEvent
- RejectApproval use case: PENDING -> REJECTED produces ActivityEvent
- GCSFileStorageAdapter.upload() stores to correct path
- ProjectViewSet queryset scoping: client cannot see other org's projects
"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.apps import apps
from django.test import RequestFactory, SimpleTestCase, TestCase

import apps.client_portal.models as orm
from apps.client_portal.domain import model as domain
from apps.client_portal.domain.repositories import (
    ClientOrganizationRepository,
    ProjectRepository,
)
from apps.client_portal.domain.value_objects import (
    ApprovalStatus,
    FileMetadata,
    InvoiceStatus,
    MilestoneStatus,
    Money,
    ProjectStatus,
    VersionNumber,
)


def _now() -> datetime:
    return datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


# ---------------------------------------------------------------------------
# ORM model __str__ tests - all 12 models, no DB required
# ---------------------------------------------------------------------------

class ClientOrganizationStrTest(SimpleTestCase):
    def test_str_returns_name(self):
        org = orm.ClientOrganization(name='Acme Corp')
        self.assertEqual(str(org), 'Acme Corp')


class UserProfileStrTest(SimpleTestCase):
    def test_str_client_role(self):
        up = orm.UserProfile(email='alice@example.com', is_client=True)
        self.assertEqual(str(up), 'alice@example.com (client)')

    def test_str_staff_role(self):
        up = orm.UserProfile(email='bob@example.com', is_client=False)
        self.assertEqual(str(up), 'bob@example.com (staff)')


class ProjectStrTest(SimpleTestCase):
    def test_str_includes_name_and_status(self):
        org = orm.ClientOrganization(id=_uuid(), name='Acme Corp', slug='acme')
        project = orm.Project(
            id=_uuid(), name='Portal V2',
            status=orm.Project.STATUS_ACTIVE, organization=org,
        )
        self.assertEqual(str(project), 'Portal V2 (ACTIVE)')


class MilestoneStrTest(SimpleTestCase):
    def test_str_includes_name_project_and_status(self):
        org = orm.ClientOrganization(id=_uuid(), name='Acme Corp', slug='acme')
        project = orm.Project(
            id=_uuid(), name='Portal V2',
            status=orm.Project.STATUS_ACTIVE, organization=org,
        )
        milestone = orm.Milestone(
            id=_uuid(), name='Sprint 1',
            status=orm.Milestone.STATUS_PENDING, project=project,
        )
        self.assertEqual(str(milestone), 'Sprint 1 - Portal V2 (PENDING)')


class DeliverableStrTest(SimpleTestCase):
    def test_str_includes_name_and_version(self):
        deliverable = orm.Deliverable(
            id=_uuid(), name='Design Mockup', current_version_number=3,
        )
        self.assertEqual(str(deliverable), 'Design Mockup (v3)')


class DeliverableVersionStrTest(SimpleTestCase):
    def test_str_includes_deliverable_name_and_version(self):
        deliverable = orm.Deliverable(
            id=_uuid(), name='Design Mockup', current_version_number=1,
        )
        dv = orm.DeliverableVersion(
            id=_uuid(), deliverable=deliverable, version_number=2,
        )
        self.assertEqual(str(dv), 'Design Mockup v2')


class ApprovalStrTest(SimpleTestCase):
    def test_str_includes_deliverable_version_and_status(self):
        deliverable = orm.Deliverable(
            id=_uuid(), name='Design Mockup', current_version_number=1,
        )
        dv = orm.DeliverableVersion(
            id=_uuid(), deliverable=deliverable, version_number=1,
        )
        reviewer = orm.UserProfile(email='reviewer@example.com', is_client=False)
        approval = orm.Approval(
            id=_uuid(),
            deliverable_version=dv,
            reviewer=reviewer,
            status=orm.Approval.STATUS_PENDING,
        )
        self.assertIn('Design Mockup v1', str(approval))
        self.assertIn('PENDING', str(approval))


class MessageThreadStrTest(SimpleTestCase):
    def test_str_includes_subject_and_project_name(self):
        org = orm.ClientOrganization(id=_uuid(), name='Acme Corp', slug='acme')
        project = orm.Project(
            id=_uuid(), name='Portal V2',
            status=orm.Project.STATUS_ACTIVE, organization=org,
        )
        thread = orm.MessageThread(
            id=_uuid(), subject='Bug Report', project=project,
        )
        self.assertEqual(str(thread), 'Bug Report (Portal V2)')


class MessageStrTest(SimpleTestCase):
    def test_str_includes_sender_email_and_thread_subject(self):
        org = orm.ClientOrganization(id=_uuid(), name='Acme Corp', slug='acme')
        project = orm.Project(
            id=_uuid(), name='Portal V2',
            status=orm.Project.STATUS_ACTIVE, organization=org,
        )
        thread = orm.MessageThread(
            id=_uuid(), subject='Feature Request', project=project,
        )
        sender = orm.UserProfile(email='alice@example.com', is_client=True)
        msg = orm.Message(
            id=_uuid(), thread=thread, sender=sender, body='Can we add X?',
        )
        self.assertEqual(str(msg), 'Message by alice@example.com in "Feature Request"')


class FileRecordStrTest(SimpleTestCase):
    def test_str_includes_filename_and_mime_type(self):
        fr = orm.FileRecord(
            id=_uuid(), filename='spec.pdf', mime_type='application/pdf',
            file_size_bytes=1024, storage_path='files/spec.pdf',
        )
        self.assertEqual(str(fr), 'spec.pdf (application/pdf)')


class InvoiceRecordStrTest(SimpleTestCase):
    def test_str_includes_id_org_status_and_amount(self):
        invoice_id = _uuid()
        org = orm.ClientOrganization(id=_uuid(), name='Acme Corp', slug='acme')
        inv = orm.InvoiceRecord(
            id=invoice_id,
            organization=org,
            status=orm.InvoiceRecord.STATUS_SENT,
            amount=Decimal('1500.00'),
        )
        self.assertEqual(str(inv), f'Invoice {invoice_id} - Acme Corp (SENT) $1500.00')


class ActivityEventStrTest(SimpleTestCase):
    def test_str_includes_event_type_and_occurred_at(self):
        actor = orm.UserProfile(email='staff@example.com', is_client=False)
        ae = orm.ActivityEvent(
            id=_uuid(), event_type='ProjectActivated', actor=actor,
        )
        ae.occurred_at = _now()
        self.assertIn('ProjectActivated', str(ae))
        self.assertIn('2024-06-01', str(ae))


# ---------------------------------------------------------------------------
# AppConfig tests
# ---------------------------------------------------------------------------

class AppConfigTest(SimpleTestCase):
    def test_label_is_client_portal(self):
        config = apps.get_app_config('client_portal')
        self.assertEqual(config.label, 'client_portal')

    def test_name_is_apps_client_portal(self):
        config = apps.get_app_config('client_portal')
        self.assertEqual(config.name, 'apps.client_portal')


# ---------------------------------------------------------------------------
# Domain value object tests
# ---------------------------------------------------------------------------

class MoneyValueObjectTest(SimpleTestCase):
    def test_valid_construction(self):
        m = Money(amount=Decimal('100.00'), currency='USD')
        self.assertEqual(m.amount, Decimal('100.00'))
        self.assertEqual(m.currency, 'USD')

    def test_negative_amount_raises(self):
        with self.assertRaises(ValueError):
            Money(amount=Decimal('-1.00'), currency='USD')

    def test_zero_amount_is_valid(self):
        m = Money(amount=Decimal('0'), currency='GBP')
        self.assertEqual(m.amount, Decimal('0'))

    def test_two_letter_currency_raises(self):
        with self.assertRaises(ValueError):
            Money(amount=Decimal('10.00'), currency='US')

    def test_numeric_char_in_currency_raises(self):
        with self.assertRaises(ValueError):
            Money(amount=Decimal('10.00'), currency='U1D')


class FileMetadataValueObjectTest(SimpleTestCase):
    def test_valid_construction(self):
        fm = FileMetadata(
            content_type='application/pdf', size_bytes=2048,
            storage_key='files/doc.pdf',
        )
        self.assertEqual(fm.content_type, 'application/pdf')

    def test_blank_content_type_raises(self):
        with self.assertRaises(ValueError):
            FileMetadata(content_type='', size_bytes=1024, storage_key='key')

    def test_non_positive_size_raises(self):
        with self.assertRaises(ValueError):
            FileMetadata(content_type='text/plain', size_bytes=0, storage_key='key')

    def test_blank_storage_key_raises(self):
        with self.assertRaises(ValueError):
            FileMetadata(content_type='text/plain', size_bytes=1, storage_key='')


class VersionNumberValueObjectTest(SimpleTestCase):
    def test_valid_construction(self):
        vn = VersionNumber(value=1)
        self.assertEqual(vn.value, 1)

    def test_zero_raises(self):
        with self.assertRaises(ValueError):
            VersionNumber(value=0)

    def test_negative_raises(self):
        with self.assertRaises(ValueError):
            VersionNumber(value=-3)


# ---------------------------------------------------------------------------
# Domain entity tests
# ---------------------------------------------------------------------------

class DomainClientOrganizationTest(SimpleTestCase):
    def test_valid_construction(self):
        org = domain.ClientOrganization(
            id=_uuid(), name='Acme Corp', slug='acme', created_at=_now(),
        )
        self.assertEqual(org.name, 'Acme Corp')

    def test_blank_name_raises(self):
        with self.assertRaises(ValueError):
            domain.ClientOrganization(
                id=_uuid(), name='', slug='acme', created_at=_now(),
            )

    def test_blank_slug_raises(self):
        with self.assertRaises(ValueError):
            domain.ClientOrganization(
                id=_uuid(), name='Acme', slug='', created_at=_now(),
            )


class DomainUserProfileInvariantTest(SimpleTestCase):
    def test_client_without_organization_raises(self):
        with self.assertRaises(ValueError):
            domain.UserProfile(
                id=_uuid(), user_id=1, email='alice@example.com',
                is_client=True, organization_id=None, created_at=_now(),
            )

    def test_staff_with_organization_raises(self):
        with self.assertRaises(ValueError):
            domain.UserProfile(
                id=_uuid(), user_id=1, email='bob@example.com',
                is_client=False, organization_id=_uuid(), created_at=_now(),
            )

    def test_client_with_organization_is_valid(self):
        up = domain.UserProfile(
            id=_uuid(), user_id=1, email='alice@example.com',
            is_client=True, organization_id=_uuid(), created_at=_now(),
        )
        self.assertEqual(up.email, 'alice@example.com')

    def test_staff_without_organization_is_valid(self):
        up = domain.UserProfile(
            id=_uuid(), user_id=2, email='bob@example.com',
            is_client=False, organization_id=None, created_at=_now(),
        )
        self.assertEqual(up.email, 'bob@example.com')


class DomainProjectStateTransitionTest(SimpleTestCase):
    def _make_project(self, status: ProjectStatus) -> domain.Project:
        return domain.Project(
            id=_uuid(),
            name='Test Project',
            organization_id=_uuid(),
            status=status,
            description=None,
            target_date=None,
            created_at=_now(),
        )

    def test_submit_for_approval_from_active(self):
        p = self._make_project(ProjectStatus.ACTIVE)
        p.submit_for_approval()
        self.assertEqual(p.status, ProjectStatus.PENDING_APPROVAL)

    def test_submit_for_approval_from_non_active_raises(self):
        p = self._make_project(ProjectStatus.DRAFT)
        with self.assertRaises(ValueError):
            p.submit_for_approval()

    def test_return_to_active_from_pending_approval(self):
        p = self._make_project(ProjectStatus.PENDING_APPROVAL)
        p.return_to_active()
        self.assertEqual(p.status, ProjectStatus.ACTIVE)

    def test_return_to_active_from_wrong_state_raises(self):
        p = self._make_project(ProjectStatus.COMPLETE)
        with self.assertRaises(ValueError):
            p.return_to_active()

    def test_mark_complete_from_pending_approval(self):
        p = self._make_project(ProjectStatus.PENDING_APPROVAL)
        p.mark_complete()
        self.assertEqual(p.status, ProjectStatus.COMPLETE)

    def test_archive_from_active(self):
        p = self._make_project(ProjectStatus.ACTIVE)
        p.archive()
        self.assertEqual(p.status, ProjectStatus.ARCHIVED)

    def test_archive_from_complete(self):
        p = self._make_project(ProjectStatus.COMPLETE)
        p.archive()
        self.assertEqual(p.status, ProjectStatus.ARCHIVED)

    def test_archive_from_draft_raises(self):
        p = self._make_project(ProjectStatus.DRAFT)
        with self.assertRaises(ValueError):
            p.archive()


class DomainMilestoneStateTransitionTest(SimpleTestCase):
    def _make_milestone(
        self, status: MilestoneStatus, target_date: date | None = None,
    ) -> domain.Milestone:
        return domain.Milestone(
            id=_uuid(),
            name='Sprint 1',
            project_id=_uuid(),
            status=status,
            target_date=target_date,
            created_at=_now(),
        )

    def test_begin_with_target_date(self):
        m = self._make_milestone(MilestoneStatus.PENDING, target_date=date(2024, 7, 1))
        m.begin()
        self.assertEqual(m.status, MilestoneStatus.IN_PROGRESS)

    def test_begin_without_target_date_raises(self):
        m = self._make_milestone(MilestoneStatus.PENDING)
        with self.assertRaises(ValueError):
            m.begin()

    def test_complete_from_in_progress(self):
        m = self._make_milestone(
            MilestoneStatus.IN_PROGRESS, target_date=date(2024, 7, 1),
        )
        m.complete()
        self.assertEqual(m.status, MilestoneStatus.COMPLETE)

    def test_complete_from_pending_raises(self):
        m = self._make_milestone(MilestoneStatus.PENDING)
        with self.assertRaises(ValueError):
            m.complete()


class DomainInvoiceRecordTest(SimpleTestCase):
    def _make_invoice(
        self, status: InvoiceStatus, due_date: date | None = None,
    ) -> domain.InvoiceRecord:
        return domain.InvoiceRecord(
            id=_uuid(),
            organization_id=_uuid(),
            project_id=None,
            status=status,
            amount=Decimal('500.00'),
            due_date=due_date,
            issued_at=None,
            created_at=_now(),
        )

    def test_zero_amount_raises(self):
        with self.assertRaises(ValueError):
            domain.InvoiceRecord(
                id=_uuid(), organization_id=_uuid(), project_id=None,
                status=InvoiceStatus.DRAFT, amount=Decimal('0'),
                due_date=None, issued_at=None, created_at=_now(),
            )

    def test_send_from_draft_with_due_date(self):
        inv = self._make_invoice(InvoiceStatus.DRAFT, due_date=date(2024, 7, 31))
        inv.send()
        self.assertEqual(inv.status, InvoiceStatus.SENT)

    def test_send_without_due_date_raises(self):
        inv = self._make_invoice(InvoiceStatus.DRAFT)
        with self.assertRaises(ValueError):
            inv.send()

    def test_mark_paid_from_sent(self):
        inv = self._make_invoice(InvoiceStatus.SENT)
        inv.mark_paid()
        self.assertEqual(inv.status, InvoiceStatus.PAID)

    def test_mark_paid_from_draft_raises(self):
        inv = self._make_invoice(InvoiceStatus.DRAFT)
        with self.assertRaises(ValueError):
            inv.mark_paid()

    def test_mark_overdue_from_sent(self):
        inv = self._make_invoice(InvoiceStatus.SENT)
        inv.mark_overdue()
        self.assertEqual(inv.status, InvoiceStatus.OVERDUE)


# ---------------------------------------------------------------------------
# Repository ABC tests
# ---------------------------------------------------------------------------

class RepositoryAbcTest(SimpleTestCase):
    def test_client_organization_repository_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            ClientOrganizationRepository()

    def test_project_repository_cannot_be_instantiated(self):
        with self.assertRaises(TypeError):
            ProjectRepository()


# ---------------------------------------------------------------------------
# Permission tests
# ---------------------------------------------------------------------------

from apps.client_portal.infrastructure.permissions import (  # noqa: E402
    IsClientOfOrganization,
    IsStaffOrClientOfOrganization,
)


class IsClientOfOrganizationPermissionTest(SimpleTestCase):
    """IsClientOfOrganization enforces org isolation at object level."""

    def _make_profile(self, organization_id, is_client=True):
        profile = MagicMock(spec=orm.UserProfile)
        profile.is_client = is_client
        profile.organization_id = organization_id
        return profile

    def test_denies_cross_org_access(self):
        org_a = uuid.uuid4()
        org_b = uuid.uuid4()
        profile = self._make_profile(org_a)
        obj = MagicMock()
        obj.organization_id = org_b
        perm = IsClientOfOrganization()
        request = MagicMock()
        request.user.is_authenticated = True
        with patch(
            'apps.client_portal.infrastructure.permissions._get_user_profile',
            return_value=profile,
        ):
            self.assertFalse(perm.has_object_permission(request, MagicMock(), obj))

    def test_allows_own_org_access(self):
        org_a = uuid.uuid4()
        profile = self._make_profile(org_a)
        obj = MagicMock()
        obj.organization_id = org_a
        perm = IsClientOfOrganization()
        request = MagicMock()
        request.user.is_authenticated = True
        with patch(
            'apps.client_portal.infrastructure.permissions._get_user_profile',
            return_value=profile,
        ):
            self.assertTrue(perm.has_object_permission(request, MagicMock(), obj))

    def test_denies_unauthenticated_user(self):
        perm = IsClientOfOrganization()
        request = MagicMock()
        request.user = None
        with patch(
            'apps.client_portal.infrastructure.permissions._get_user_profile',
            return_value=None,
        ):
            self.assertFalse(perm.has_object_permission(request, MagicMock(), MagicMock()))


class IsStaffOrClientOfOrganizationPermissionTest(SimpleTestCase):
    """IsStaffOrClientOfOrganization: staff users bypass org restrictions."""

    def test_staff_bypass_returns_true(self):
        request = MagicMock()
        request.user.is_authenticated = True
        request.user.is_staff = True
        obj = MagicMock()
        obj.organization_id = uuid.uuid4()
        perm = IsStaffOrClientOfOrganization()
        self.assertTrue(perm.has_object_permission(request, MagicMock(), obj))

    def test_client_with_matching_org_allowed(self):
        org_id = uuid.uuid4()
        profile = MagicMock(spec=orm.UserProfile)
        profile.is_client = True
        profile.organization_id = org_id
        request = MagicMock()
        request.user.is_authenticated = True
        request.user.is_staff = False
        obj = MagicMock()
        obj.organization_id = org_id
        perm = IsStaffOrClientOfOrganization()
        with patch(
            'apps.client_portal.infrastructure.permissions._get_user_profile',
            return_value=profile,
        ):
            self.assertTrue(perm.has_object_permission(request, MagicMock(), obj))


# ---------------------------------------------------------------------------
# Use case tests - GrantApproval and RejectApproval
# ---------------------------------------------------------------------------

from apps.client_portal.application.dtos import (  # noqa: E402
    GrantApprovalCommand,
    RejectApprovalCommand,
)
from apps.client_portal.application.use_cases import (  # noqa: E402
    GrantApproval,
    RejectApproval,
)


def _make_pending_approval() -> domain.Approval:
    return domain.Approval(
        id=uuid.uuid4(),
        deliverable_version_id=uuid.uuid4(),
        reviewer_id=uuid.uuid4(),
        status=ApprovalStatus.PENDING,
        comment=None,
        decided_at=None,
        created_at=_now(),
    )


class GrantApprovalUseCaseTest(SimpleTestCase):
    """GrantApproval: PENDING->APPROVED transition records a DeliverableApproved ActivityEvent."""

    def test_pending_to_approved_produces_activity_event(self):
        approval = _make_pending_approval()
        approval_repo = MagicMock()
        approval_repo.get_by_id.return_value = approval
        activity_repo = MagicMock()

        use_case = GrantApproval(approval_repo=approval_repo, activity_repo=activity_repo)
        dto = use_case.execute(
            GrantApprovalCommand(
                approval_id=approval.id,
                reviewer_id=approval.reviewer_id,
                comment='LGTM',
            )
        )

        self.assertEqual(dto.status, ApprovalStatus.APPROVED.value)
        activity_repo.save.assert_called_once()
        saved_event = activity_repo.save.call_args[0][0]
        self.assertEqual(saved_event.event_type, 'DeliverableApproved')
        self.assertEqual(saved_event.actor_id, approval.reviewer_id)

    def test_wrong_reviewer_raises_value_error(self):
        approval = _make_pending_approval()
        approval_repo = MagicMock()
        approval_repo.get_by_id.return_value = approval
        activity_repo = MagicMock()

        use_case = GrantApproval(approval_repo=approval_repo, activity_repo=activity_repo)
        with self.assertRaises(ValueError):
            use_case.execute(
                GrantApprovalCommand(
                    approval_id=approval.id,
                    reviewer_id=uuid.uuid4(),  # different reviewer
                    comment=None,
                )
            )


class RejectApprovalUseCaseTest(SimpleTestCase):
    """RejectApproval: PENDING->REJECTED transition records a DeliverableRejected ActivityEvent."""

    def test_pending_to_rejected_produces_activity_event(self):
        approval = _make_pending_approval()
        approval_repo = MagicMock()
        approval_repo.get_by_id.return_value = approval
        activity_repo = MagicMock()

        use_case = RejectApproval(approval_repo=approval_repo, activity_repo=activity_repo)
        dto = use_case.execute(
            RejectApprovalCommand(
                approval_id=approval.id,
                reviewer_id=approval.reviewer_id,
                comment='Does not meet requirements.',
            )
        )

        self.assertEqual(dto.status, ApprovalStatus.REJECTED.value)
        activity_repo.save.assert_called_once()
        saved_event = activity_repo.save.call_args[0][0]
        self.assertEqual(saved_event.event_type, 'DeliverableRejected')
        self.assertEqual(saved_event.actor_id, approval.reviewer_id)

    def test_wrong_reviewer_raises_value_error(self):
        approval = _make_pending_approval()
        approval_repo = MagicMock()
        approval_repo.get_by_id.return_value = approval
        activity_repo = MagicMock()

        use_case = RejectApproval(approval_repo=approval_repo, activity_repo=activity_repo)
        with self.assertRaises(ValueError):
            use_case.execute(
                RejectApprovalCommand(
                    approval_id=approval.id,
                    reviewer_id=uuid.uuid4(),  # different reviewer
                    comment='Reject.',
                )
            )


# ---------------------------------------------------------------------------
# Storage adapter tests
# ---------------------------------------------------------------------------

from apps.client_portal.infrastructure.storage import GCSFileStorageAdapter  # noqa: E402


class GCSFileStorageAdapterTest(SimpleTestCase):
    """GCSFileStorageAdapter.upload() delegates to default_storage with a prefixed key."""

    def test_upload_returns_saved_path(self):
        expected_path = 'client_portal/abc123hex/design.pdf'
        with patch('apps.client_portal.infrastructure.storage.default_storage') as mock_storage:
            mock_storage.save.return_value = expected_path
            result = GCSFileStorageAdapter().upload(b'pdfdata', 'design.pdf', 'application/pdf')
        self.assertEqual(result, expected_path)

    def test_upload_key_has_client_portal_prefix_and_filename(self):
        with patch('apps.client_portal.infrastructure.storage.default_storage') as mock_storage:
            mock_storage.save.return_value = 'client_portal/x/design.pdf'
            GCSFileStorageAdapter().upload(b'data', 'design.pdf', 'application/pdf')
        call_key = mock_storage.save.call_args[0][0]
        self.assertTrue(
            call_key.startswith('client_portal/'),
            f'Expected key to start with "client_portal/", got: {call_key}',
        )
        self.assertIn('design.pdf', call_key)


# ---------------------------------------------------------------------------
# Viewset queryset scoping tests (require database)
# ---------------------------------------------------------------------------

from apps.client_portal.infrastructure.viewsets import ProjectViewSet  # noqa: E402


class ProjectViewSetQueryScopingTest(TestCase):
    """ProjectViewSet.get_queryset() scopes results to the authenticated client's organization."""

    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()

        self.org1 = orm.ClientOrganization.objects.create(
            id=uuid.uuid4(), name='Org Alpha', slug='org-alpha',
        )
        self.org2 = orm.ClientOrganization.objects.create(
            id=uuid.uuid4(), name='Org Beta', slug='org-beta',
        )
        self.user1 = User.objects.create_user(
            username='alice_scoping', password='pw', email='alice_scoping@example.com',
        )
        orm.UserProfile.objects.create(
            id=uuid.uuid4(),
            user=self.user1,
            email='alice_scoping@example.com',
            is_client=True,
            organization=self.org1,
        )
        self.project_org1 = orm.Project.objects.create(
            id=uuid.uuid4(), name='Alpha Project',
            organization=self.org1, status=orm.Project.STATUS_ACTIVE,
        )
        self.project_org2 = orm.Project.objects.create(
            id=uuid.uuid4(), name='Beta Project',
            organization=self.org2, status=orm.Project.STATUS_ACTIVE,
        )

    def test_client_cannot_see_other_orgs_projects(self):
        factory = RequestFactory()
        request = factory.get('/api/client-portal/projects/')
        request.user = self.user1

        view = ProjectViewSet()
        view.request = request
        view.kwargs = {}
        view.action = 'list'
        view.format_kwarg = None

        qs = view.get_queryset()
        ids = list(qs.values_list('id', flat=True))
        self.assertIn(self.project_org1.id, ids)
        self.assertNotIn(self.project_org2.id, ids)

