"""
Seed script for client_portal app - Phase 1 Foundation.

Generates:
- 2 ClientOrganization records
- 3 Project records (ACTIVE, PENDING_APPROVAL, COMPLETE)
- 1 InvoiceRecord with OVERDUE status

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
from django.utils import timezone
from apps.client_portal.models import (
    ClientOrganization,
    InvoiceRecord,
    Project,
)


def run() -> None:
    print("Seeding client_portal data...")

    # ------------------------------------------------------------------
    # ClientOrganization records
    # ------------------------------------------------------------------
    acme, acme_created = ClientOrganization.objects.get_or_create(
        slug='acme-corp',
        defaults={'name': 'Acme Corporation'},
    )
    print(f"  ClientOrganization: {acme.name} ({'created' if acme_created else 'already exists'})")

    nova, nova_created = ClientOrganization.objects.get_or_create(
        slug='nova-ventures',
        defaults={'name': 'Nova Ventures LLC'},
    )
    print(f"  ClientOrganization: {nova.name} ({'created' if nova_created else 'already exists'})")

    # ------------------------------------------------------------------
    # Project records
    # ------------------------------------------------------------------
    active_project, p1_created = Project.objects.get_or_create(
        name='Acme Website Redesign',
        organization=acme,
        defaults={
            'status': Project.STATUS_ACTIVE,
            'description': 'Full redesign of the Acme public-facing website.',
            'target_date': (datetime.date.today() + datetime.timedelta(days=90)),
        },
    )
    print(
        f"  Project: {active_project.name} [{active_project.status}]"
        f" ({'created' if p1_created else 'already exists'})"
    )

    pending_project, p2_created = Project.objects.get_or_create(
        name='Nova Brand Identity',
        organization=nova,
        defaults={
            'status': Project.STATUS_PENDING_APPROVAL,
            'description': 'Brand identity package including logo, colour system, and style guide.',
            'target_date': (datetime.date.today() + datetime.timedelta(days=30)),
        },
    )
    print(
        f"  Project: {pending_project.name} [{pending_project.status}]"
        f" ({'created' if p2_created else 'already exists'})"
    )

    complete_project, p3_created = Project.objects.get_or_create(
        name='Acme Mobile App - Phase 0',
        organization=acme,
        defaults={
            'status': Project.STATUS_COMPLETE,
            'description': 'Discovery and scoping phase for the Acme mobile application.',
            'target_date': (datetime.date.today() - datetime.timedelta(days=30)),
        },
    )
    print(
        f"  Project: {complete_project.name} [{complete_project.status}]"
        f" ({'created' if p3_created else 'already exists'})"
    )

    # ------------------------------------------------------------------
    # InvoiceRecord - OVERDUE
    # ------------------------------------------------------------------
    overdue_invoice, inv_created = InvoiceRecord.objects.get_or_create(
        organization=acme,
        project=complete_project,
        status=InvoiceRecord.STATUS_OVERDUE,
        defaults={
            'amount': decimal.Decimal('4500.00'),
            'due_date': datetime.date.today() - datetime.timedelta(days=15),
            'issued_at': timezone.now() - datetime.timedelta(days=45),
        },
    )
    print(
        f"  InvoiceRecord: ${overdue_invoice.amount} for {acme.name} [{overdue_invoice.status}]"
        f" ({'created' if inv_created else 'already exists'})"
    )

    print("Seed complete.")


if __name__ == '__main__':
    run()
