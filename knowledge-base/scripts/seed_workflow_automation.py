"""
Seed script for workflow_automation - creates realistic demo rules and run history.

Usage:
    .venv\\Scripts\\python.exe knowledge-base\\scripts\\seed_workflow_automation.py

Requires Django settings to be configured (set DJANGO_SETTINGS_MODULE).
"""
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

import django

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from apps.workflow_automation import models as orm

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ago(days=0, hours=0, minutes=0):
    return datetime.now(tz=timezone.utc) - timedelta(days=days, hours=hours, minutes=minutes)


def make_run(rule, trigger_type, context_payload, status, started_offset_days, duration_minutes=1, is_dry_run=False):
    started = ago(days=started_offset_days)
    completed = started + timedelta(minutes=duration_minutes)
    return orm.AutomationRun.objects.create(
        id=uuid.uuid4(),
        rule=rule,
        trigger_type=trigger_type,
        context_payload=context_payload,
        status=status,
        is_dry_run=is_dry_run,
        started_at=started,
        completed_at=completed,
    )


def make_logs(run, entries):
    """entries: list of (level, message, offset_seconds)"""
    base = run.started_at
    for level, message, offset_seconds in entries:
        orm.AutomationRunLog.objects.create(
            id=uuid.uuid4(),
            run=run,
            level=level,
            message=message,
            logged_at=base + timedelta(seconds=offset_seconds),
        )


# ---------------------------------------------------------------------------
# Rules
# ---------------------------------------------------------------------------

def seed():
    print('Seeding workflow_automation demo data...')

    # ------------------------------------------------------------------
    # Rule 1: Notify team on deliverable approval (ENABLED)
    # Trigger: deliverable.approved
    # Conditions: status eq approved
    # Actions: send_email + create_activity_event
    # ------------------------------------------------------------------
    rule1, created = orm.AutomationRule.objects.get_or_create(
        name='Notify Team on Deliverable Approval',
        defaults={
            'trigger_type': 'deliverable.approved',
            'description': (
                'When a client approves a deliverable, email the project manager '
                'and log an activity event in the ops dashboard.'
            ),
            'is_enabled': True,
        },
    )
    if created:
        orm.AutomationCondition.objects.create(
            rule=rule1, field_name='status', operator='eq',
            expected_value='approved', position=0,
        )
        orm.AutomationAction.objects.create(
            rule=rule1, action_type='send_email',
            parameters={
                'to_email': 'pm@example.com',
                'subject': 'Deliverable approved - {{deliverable_name}}',
                'body': (
                    'Good news - the client has approved the deliverable. '
                    'Project: {{project_name}}. Approved by: {{approved_by}}.'
                ),
            },
            position=0,
        )
        orm.AutomationAction.objects.create(
            rule=rule1, action_type='create_activity_event',
            parameters={
                'event_type': 'deliverable_approved',
                'description': 'Deliverable approved by client - {{deliverable_name}}',
            },
            position=1,
        )
        print(f'  Created rule: {rule1.name}')

        # Run history: 4 successes, 1 dry run
        for d, org in [(2, 'Acme Corp'), (6, 'Nova Ventures'), (10, 'Acme Corp'), (15, 'Nova Ventures')]:
            r = make_run(
                rule1, 'deliverable.approved',
                {'deliverable_name': 'Brand Identity V2', 'project_name': f'{org} Rebrand', 'approved_by': 'Alice'},
                'success', started_offset_days=d,
            )
            make_logs(r, [
                ('info',  'Rule triggered: deliverable.approved', 0),
                ('info',  'Evaluating 1 condition(s)', 1),
                ('info',  'Condition passed: status eq approved', 2),
                ('info',  'Executing action 1/2: send_email', 3),
                ('info',  f'Email dispatched to pm@example.com (deliverable: Brand Identity V2, org: {org})', 5),
                ('info',  'Executing action 2/2: create_activity_event', 6),
                ('info',  'Activity event created: deliverable_approved', 8),
                ('info',  'Run completed successfully', 9),
            ])
        # Dry run
        r = make_run(
            rule1, 'deliverable.approved',
            {'deliverable_name': 'Phase 0 Kickoff Deck', 'project_name': 'Acme Corp Rebrand', 'approved_by': 'Bob'},
            'dry_run', started_offset_days=1, is_dry_run=True,
        )
        make_logs(r, [
            ('info',  'DRY RUN - no actions will be executed', 0),
            ('info',  'Evaluating 1 condition(s)', 1),
            ('info',  'Condition passed: status eq approved', 2),
            ('info',  '[DRY RUN] Would execute: send_email to pm@example.com', 3),
            ('info',  '[DRY RUN] Would execute: create_activity_event (deliverable_approved)', 4),
            ('info',  'Dry run complete - 2 action(s) would have executed', 5),
        ])
    else:
        print(f'  Rule already exists: {rule1.name}')

    # ------------------------------------------------------------------
    # Rule 2: Alert on high churn metric (ENABLED)
    # Trigger: metric.threshold_crossed
    # Conditions: metric_type eq customer_growth, value lt -5
    # Actions: send_email + send_sms
    # ------------------------------------------------------------------
    rule2, created = orm.AutomationRule.objects.get_or_create(
        name='Alert on High Customer Churn',
        defaults={
            'trigger_type': 'metric.threshold_crossed',
            'description': (
                'When the customer growth metric drops below -5 (net churn), '
                'email the CEO and send an SMS to the operations lead.'
            ),
            'is_enabled': True,
        },
    )
    if created:
        orm.AutomationCondition.objects.create(
            rule=rule2, field_name='metric_type', operator='eq',
            expected_value='customer_growth', position=0,
        )
        orm.AutomationCondition.objects.create(
            rule=rule2, field_name='value', operator='lt',
            expected_value='-5', position=1,
        )
        orm.AutomationAction.objects.create(
            rule=rule2, action_type='send_email',
            parameters={
                'to_email': 'ceo@example.com',
                'subject': 'ALERT: Customer churn threshold crossed',
                'body': 'Net customer growth has dropped to {{value}}. Immediate review recommended.',
            },
            position=0,
        )
        orm.AutomationAction.objects.create(
            rule=rule2, action_type='send_sms',
            parameters={
                'to_number': '+12025550101',
                'body': 'OPS ALERT: Churn threshold crossed. Net growth: {{value}}. Check dashboard.',
            },
            position=1,
        )
        print(f'  Created rule: {rule2.name}')

        # 2 successes, 1 failure (SMS provider error)
        r = make_run(
            rule2, 'metric.threshold_crossed',
            {'metric_type': 'customer_growth', 'value': -8, 'period': 'March 2026'},
            'success', started_offset_days=7,
        )
        make_logs(r, [
            ('info',  'Rule triggered: metric.threshold_crossed', 0),
            ('info',  'Evaluating 2 condition(s)', 1),
            ('info',  'Condition passed: metric_type eq customer_growth', 2),
            ('info',  'Condition passed: value lt -5 (actual: -8)', 3),
            ('info',  'Executing action 1/2: send_email', 4),
            ('info',  'Email dispatched to ceo@example.com', 6),
            ('info',  'Executing action 2/2: send_sms', 7),
            ('info',  'SMS dispatched to +12025550101', 9),
            ('info',  'Run completed successfully', 10),
        ])
        r = make_run(
            rule2, 'metric.threshold_crossed',
            {'metric_type': 'customer_growth', 'value': -12, 'period': 'April 2026'},
            'failure', started_offset_days=5,
        )
        make_logs(r, [
            ('info',  'Rule triggered: metric.threshold_crossed', 0),
            ('info',  'Evaluating 2 condition(s)', 1),
            ('info',  'Condition passed: metric_type eq customer_growth', 2),
            ('info',  'Condition passed: value lt -5 (actual: -12)', 3),
            ('info',  'Executing action 1/2: send_email', 4),
            ('info',  'Email dispatched to ceo@example.com', 6),
            ('info',  'Executing action 2/2: send_sms', 7),
            ('error', 'SMS provider error: invalid destination number format', 8),
            ('error', 'Action send_sms failed - run marked as failure', 9),
        ])
        r = make_run(
            rule2, 'metric.threshold_crossed',
            {'metric_type': 'customer_growth', 'value': -6, 'period': 'May 2026'},
            'success', started_offset_days=1,
        )
        make_logs(r, [
            ('info',  'Rule triggered: metric.threshold_crossed', 0),
            ('info',  'Evaluating 2 condition(s)', 1),
            ('info',  'Condition passed: metric_type eq customer_growth', 2),
            ('info',  'Condition passed: value lt -5 (actual: -6)', 3),
            ('info',  'Executing action 1/2: send_email', 4),
            ('info',  'Email dispatched to ceo@example.com', 6),
            ('info',  'Executing action 2/2: send_sms', 7),
            ('info',  'SMS dispatched to +12025550101', 9),
            ('info',  'Run completed successfully', 10),
        ])
    else:
        print(f'  Rule already exists: {rule2.name}')

    # ------------------------------------------------------------------
    # Rule 3: Escalate overdue invoice (ENABLED)
    # Trigger: invoice.overdue
    # Conditions: amount gt 5000
    # Actions: send_email + update_status
    # ------------------------------------------------------------------
    rule3, created = orm.AutomationRule.objects.get_or_create(
        name='Escalate High-Value Overdue Invoice',
        defaults={
            'trigger_type': 'invoice.overdue',
            'description': (
                'For invoices over $5,000 that are overdue, email the accounts team '
                'and update the invoice status to escalated.'
            ),
            'is_enabled': True,
        },
    )
    if created:
        orm.AutomationCondition.objects.create(
            rule=rule3, field_name='amount', operator='gt',
            expected_value='5000', position=0,
        )
        orm.AutomationAction.objects.create(
            rule=rule3, action_type='send_email',
            parameters={
                'to_email': 'accounts@example.com',
                'subject': 'Overdue invoice escalation - {{client_name}}',
                'body': (
                    'Invoice #{{invoice_id}} for {{client_name}} is {{days_overdue}} days overdue. '
                    'Amount: ${{amount}}. Please follow up immediately.'
                ),
            },
            position=0,
        )
        orm.AutomationAction.objects.create(
            rule=rule3, action_type='update_status',
            parameters={
                'entity_type': 'invoice',
                'entity_id': '{{invoice_id}}',
                'new_status': 'escalated',
            },
            position=1,
        )
        print(f'  Created rule: {rule3.name}')

        # 3 successes over past weeks
        for d, client, amount, days in [
            (3, 'Acme Corp', 12500, 14),
            (11, 'Nova Ventures', 8750, 21),
            (18, 'Acme Corp', 6200, 7),
        ]:
            r = make_run(
                rule3, 'invoice.overdue',
                {'invoice_id': f'INV-{1000 + d}', 'client_name': client, 'amount': amount, 'days_overdue': days},
                'success', started_offset_days=d,
            )
            make_logs(r, [
                ('info',  'Rule triggered: invoice.overdue', 0),
                ('info',  'Evaluating 1 condition(s)', 1),
                ('info',  f'Condition passed: amount gt 5000 (actual: {amount})', 2),
                ('info',  'Executing action 1/2: send_email', 3),
                ('info',  f'Email dispatched to accounts@example.com (invoice: INV-{1000 + d}, client: {client})', 5),
                ('info',  'Executing action 2/2: update_status', 6),
                ('info',  f'Invoice INV-{1000 + d} status updated to escalated', 8),
                ('info',  'Run completed successfully', 9),
            ])
    else:
        print(f'  Rule already exists: {rule3.name}')

    # ------------------------------------------------------------------
    # Rule 4: Log activity on file upload (ENABLED)
    # Trigger: file.uploaded
    # Conditions: file_type contains pdf
    # Actions: create_activity_event
    # ------------------------------------------------------------------
    rule4, created = orm.AutomationRule.objects.get_or_create(
        name='Log PDF Upload to Activity Feed',
        defaults={
            'trigger_type': 'file.uploaded',
            'description': 'When a PDF is uploaded to the portal, create an activity event for the ops team.',
            'is_enabled': True,
        },
    )
    if created:
        orm.AutomationCondition.objects.create(
            rule=rule4, field_name='file_type', operator='contains',
            expected_value='pdf', position=0,
        )
        orm.AutomationAction.objects.create(
            rule=rule4, action_type='create_activity_event',
            parameters={
                'event_type': 'file_uploaded',
                'description': 'PDF uploaded: {{file_name}} by {{uploaded_by}}',
            },
            position=0,
        )
        print(f'  Created rule: {rule4.name}')

        # 5 successes - frequent, lightweight runs
        files = [
            (1, 'Brand_Brief_Final.pdf', 'alice@acme-corp.example.com'),
            (2, 'Contract_Signed.pdf', 'bob@nova-ventures.example.com'),
            (4, 'Proposal_Q2.pdf', 'alice@acme-corp.example.com'),
            (8, 'Invoice_April.pdf', 'bob@nova-ventures.example.com'),
            (13, 'Scope_of_Work_v3.pdf', 'alice@acme-corp.example.com'),
        ]
        for d, fname, uploader in files:
            r = make_run(
                rule4, 'file.uploaded',
                {'file_name': fname, 'file_type': 'application/pdf', 'uploaded_by': uploader},
                'success', started_offset_days=d, duration_minutes=0,
            )
            make_logs(r, [
                ('info', 'Rule triggered: file.uploaded', 0),
                ('info', 'Evaluating 1 condition(s)', 0),
                ('info', 'Condition passed: file_type contains pdf', 1),
                ('info', 'Executing action 1/1: create_activity_event', 1),
                ('info', f'Activity event created: file_uploaded ({fname})', 2),
                ('info', 'Run completed successfully', 2),
            ])
    else:
        print(f'  Rule already exists: {rule4.name}')

    # ------------------------------------------------------------------
    # Rule 5: Auto-close resolved metric alerts (DISABLED)
    # Trigger: metric.threshold_crossed
    # Conditions: assigned_to eq ops-team
    # Actions: update_status
    # ------------------------------------------------------------------
    rule5, created = orm.AutomationRule.objects.get_or_create(
        name='Auto-Close Resolved Metric Alerts',
        defaults={
            'trigger_type': 'metric.threshold_crossed',
            'description': (
                'Automatically mark metric alerts as resolved when assigned to the ops team. '
                'Disabled pending review of alert resolution criteria.'
            ),
            'is_enabled': False,
        },
    )
    if created:
        orm.AutomationCondition.objects.create(
            rule=rule5, field_name='assigned_to', operator='assigned_to',
            expected_value='ops-team', position=0,
        )
        orm.AutomationAction.objects.create(
            rule=rule5, action_type='update_status',
            parameters={
                'entity_type': 'alert',
                'entity_id': '{{alert_id}}',
                'new_status': 'resolved',
            },
            position=0,
        )
        print(f'  Created rule: {rule5.name} (disabled)')

        # 1 dry run from when the rule was being tested before it was disabled
        r = make_run(
            rule5, 'metric.threshold_crossed',
            {'alert_id': 'ALR-042', 'assigned_to': 'ops-team', 'metric': 'churn_rate'},
            'dry_run', started_offset_days=9, is_dry_run=True,
        )
        make_logs(r, [
            ('info',  'DRY RUN - no actions will be executed', 0),
            ('info',  'Evaluating 1 condition(s)', 1),
            ('info',  'Condition passed: assigned_to ops-team', 2),
            ('info',  '[DRY RUN] Would execute: update_status -> resolved for alert ALR-042', 3),
            ('warn',  'Note: entity ALR-042 does not currently exist in the system', 4),
            ('info',  'Dry run complete - 1 action(s) would have executed', 5),
        ])
    else:
        print(f'  Rule already exists: {rule5.name}')

    print('Seeding complete.')


if __name__ == '__main__':
    seed()
