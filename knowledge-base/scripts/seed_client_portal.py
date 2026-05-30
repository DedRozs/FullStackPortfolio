"""
Seed script for client_portal app.

Generates:
- 2 ClientOrganization records
- 3 Project records (ACTIVE, PENDING_APPROVAL, COMPLETE)
- Milestones, Deliverables, DeliverableVersions
- At least one APPROVED DeliverableVersion
- 1 OVERDUE InvoiceRecord
- MessageThread + Message records
- UserProfile records for test users

Usage:
    .venv\\Scripts\\python.exe knowledge-base/scripts/seed_client_portal.py
"""
import os
import sys
import datetime
import decimal

# ---------------------------------------------------------------------------
# Bootstrap Django before importing any app models.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

# ---------------------------------------------------------------------------
# Imports - safe after django.setup()
# ---------------------------------------------------------------------------
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.client_portal.models import (
    Approval,
    ClientOrganization,
    Deliverable,
    DeliverableVersion,
    InvoiceRecord,
    Message,
    MessageThread,
    Milestone,
    Project,
    UserProfile,
)

User = get_user_model()
TODAY = datetime.date.today()


def get_or_create_user(username, email, is_staff=False):
    user, _ = User.objects.get_or_create(username=username, defaults={'email': email})
    user.is_staff = is_staff
    user.set_password('PortalDemo2025!')
    user.save()
    return user


def run() -> None:
    print("Seeding client_portal data...")

    # ------------------------------------------------------------------
    # Users
    # ------------------------------------------------------------------
    staff_user = get_or_create_user('staff_admin', 'staff@example.com', is_staff=True)
    acme_user = get_or_create_user('acme_alice', 'alice@acme-corp.example.com')
    nova_user = get_or_create_user('nova_bob', 'bob@nova-ventures.example.com')

    # ------------------------------------------------------------------
    # ClientOrganization records
    # ------------------------------------------------------------------
    acme, acme_created = ClientOrganization.objects.get_or_create(
        slug='acme-corp',
        defaults={'name': 'Acme Corporation'},
    )
    print(f"  ClientOrganization: {acme.name} ({'created' if acme_created else 'exists'})")

    nova, nova_created = ClientOrganization.objects.get_or_create(
        slug='nova-ventures',
        defaults={'name': 'Nova Ventures LLC'},
    )
    print(f"  ClientOrganization: {nova.name} ({'created' if nova_created else 'exists'})")

    # ------------------------------------------------------------------
    # UserProfile records
    # ------------------------------------------------------------------
    staff_profile, _ = UserProfile.objects.get_or_create(
        user=staff_user,
        defaults={'email': staff_user.email, 'is_client': False, 'organization': None},
    )
    acme_profile, _ = UserProfile.objects.get_or_create(
        user=acme_user,
        defaults={'email': acme_user.email, 'is_client': True, 'organization': acme},
    )
    nova_profile, _ = UserProfile.objects.get_or_create(
        user=nova_user,
        defaults={'email': nova_user.email, 'is_client': True, 'organization': nova},
    )
    print(f"  Profiles: {acme_profile.email}, {nova_profile.email}, {staff_profile.email}")

    # ------------------------------------------------------------------
    # Project records
    # ------------------------------------------------------------------
    active_project, p1_created = Project.objects.get_or_create(
        name='Acme Website Redesign',
        organization=acme,
        defaults={
            'status': Project.STATUS_ACTIVE,
            'description': 'Full redesign of the Acme public-facing website.',
            'target_date': TODAY + datetime.timedelta(days=90),
        },
    )
    print(f"  Project: {active_project.name} [{active_project.status}] ({'created' if p1_created else 'exists'})")

    pending_project, p2_created = Project.objects.get_or_create(
        name='Nova Brand Identity',
        organization=nova,
        defaults={
            'status': Project.STATUS_PENDING_APPROVAL,
            'description': 'Brand identity package including logo, colour system, and style guide.',
            'target_date': TODAY + datetime.timedelta(days=30),
        },
    )
    print(f"  Project: {pending_project.name} [{pending_project.status}] ({'created' if p2_created else 'exists'})")

    complete_project, p3_created = Project.objects.get_or_create(
        name='Acme Mobile App - Phase 0',
        organization=acme,
        defaults={
            'status': Project.STATUS_COMPLETE,
            'description': 'Discovery and scoping phase for the Acme mobile application.',
            'target_date': TODAY - datetime.timedelta(days=30),
        },
    )
    print(f"  Project: {complete_project.name} [{complete_project.status}] ({'created' if p3_created else 'exists'})")

    # ------------------------------------------------------------------
    # Milestones
    # ------------------------------------------------------------------
    ms_discovery = Milestone.objects.create(
        name='Discovery & Wireframes',
        project=active_project,
        status='COMPLETE',
        target_date=TODAY - datetime.timedelta(days=14),
    )
    ms_design = Milestone.objects.create(
        name='Visual Design',
        project=active_project,
        status='IN_PROGRESS',
        target_date=TODAY + datetime.timedelta(days=14),
    )
    ms_mobile = Milestone.objects.create(
        name='Core Feature Set',
        project=pending_project,
        status='COMPLETE',
        target_date=TODAY - datetime.timedelta(days=5),
    )
    print(f"  Milestones: {ms_discovery.name}, {ms_design.name}, {ms_mobile.name}")

    # ------------------------------------------------------------------
    # Deliverables, Versions, Approvals
    # ------------------------------------------------------------------
    deliv_logo = Deliverable.objects.create(
        name='Logo Concepts',
        milestone=ms_design,
        description='Three logo concept directions for client review.',
        current_version_number=2,
    )
    dv1 = DeliverableVersion.objects.create(
        deliverable=deliv_logo,
        version_number=1,
        notes='Initial three concepts.',
    )
    Approval.objects.create(
        deliverable_version=dv1,
        reviewer=acme_profile,
        status='REVISION_REQUESTED',
        comment='Please revise Concept B - the font feels dated.',
    )
    dv2 = DeliverableVersion.objects.create(
        deliverable=deliv_logo,
        version_number=2,
        notes='Revised Concept B with modern typeface.',
    )
    Approval.objects.create(
        deliverable_version=dv2,
        reviewer=acme_profile,
        status='APPROVED',
        comment='Love the new direction. Approved!',
    )
    print(f"  Deliverable '{deliv_logo.name}': v1 REVISION_REQUESTED, v2 APPROVED")

    # ------------------------------------------------------------------
    # InvoiceRecord - OVERDUE
    # ------------------------------------------------------------------
    overdue_invoice, inv_created = InvoiceRecord.objects.get_or_create(
        organization=acme,
        project=complete_project,
        status=InvoiceRecord.STATUS_OVERDUE,
        defaults={
            'amount': decimal.Decimal('4500.00'),
            'due_date': TODAY - datetime.timedelta(days=15),
            'issued_at': timezone.now() - datetime.timedelta(days=45),
        },
    )
    print(
        f"  InvoiceRecord: ${overdue_invoice.amount} for {acme.name} [{overdue_invoice.status}]"
        f" ({'created' if inv_created else 'exists'})"
    )

    # ------------------------------------------------------------------
    # MessageThread + Messages
    # ------------------------------------------------------------------
    thread = MessageThread.objects.create(
        subject='Brand guidelines feedback',
        project=active_project,
    )
    Message.objects.create(
        thread=thread,
        sender=acme_profile,
        body='Hi team, the initial mockups look great. Can we add more negative space?',
    )
    Message.objects.create(
        thread=thread,
        sender=staff_profile,
        body='Absolutely - we will update the layouts and share revised files shortly.',
    )
    print(f"  MessageThread '{thread.subject}' with 2 messages created")

    print("\nSeed complete.")


if __name__ == '__main__':
    run()
