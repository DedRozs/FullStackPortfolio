"""
Seed script for workflow_automation - creates sample rules for local dev.

Usage:
    .venv\\Scripts\\python.exe knowledge-base\\scripts\\seed_workflow_automation.py

Requires Django settings to be configured (set DJANGO_SETTINGS_MODULE).
"""
import os
import sys
import django

# Append project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.workflow_automation import models as orm


def seed():
    # Rule 1: Email on deliverable approval
    rule1, created = orm.AutomationRule.objects.get_or_create(
        name='Notify on Deliverable Approval',
        defaults={
            'trigger_type': 'deliverable.approved',
            'description': 'Send email when a deliverable is approved',
            'is_enabled': True,
        },
    )
    if created:
        orm.AutomationAction.objects.create(
            rule=rule1,
            action_type='send_email',
            parameters={
                'to_email': 'admin@example.com',
                'subject': 'Deliverable Approved',
                'body': 'A deliverable has been approved.',
            },
            position=0,
        )
        print(f'Created rule: {rule1.name}')
    else:
        print(f'Rule already exists: {rule1.name}')

    # Rule 2: SMS on invoice overdue
    rule2, created = orm.AutomationRule.objects.get_or_create(
        name='SMS on Invoice Overdue',
        defaults={
            'trigger_type': 'invoice.overdue',
            'description': 'Send SMS when an invoice becomes overdue',
            'is_enabled': True,
        },
    )
    if created:
        orm.AutomationAction.objects.create(
            rule=rule2,
            action_type='send_sms',
            parameters={
                'to_number': '+10000000000',
                'body': 'Invoice is overdue.',
            },
            position=0,
        )
        print(f'Created rule: {rule2.name}')
    else:
        print(f'Rule already exists: {rule2.name}')

    print('Seeding complete.')


if __name__ == '__main__':
    seed()
