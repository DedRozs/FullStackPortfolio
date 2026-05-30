"""
Background notification tasks for the client_portal app.

These tasks are executed asynchronously by Django-Q2.

Usage (from Django code):
    from django_q.tasks import async_task
    async_task('apps.client_portal.tasks.send_approval_notification', str(approval_id))
"""
from __future__ import annotations

import logging

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_approval_notification(approval_id: str) -> None:
    """Read the approval record and email the project owner about the decision.

    Args:
        approval_id: String representation of the Approval UUID primary key.
    """
    from apps.client_portal import models as orm

    try:
        approval = orm.Approval.objects.select_related(
            'deliverable_version__deliverable__milestone__project__organization',
            'reviewer',
        ).get(pk=approval_id)
    except orm.Approval.DoesNotExist:
        logger.error('send_approval_notification: Approval %s not found', approval_id)
        return

    project = approval.deliverable_version.deliverable.milestone.project
    org = project.organization

    stakeholder_emails = list(
        orm.UserProfile.objects.filter(
            organization=org, is_client=True
        ).values_list('email', flat=True)
    )

    if not stakeholder_emails:
        logger.info(
            'send_approval_notification: no stakeholder emails found for org %s', org.id
        )
        return

    subject = f'[Client Portal] Approval {approval.status} - {project.name}'
    reviewer_email = approval.reviewer.email
    body = (
        f'Project: {project.name}\n'
        f'Deliverable: {approval.deliverable_version.deliverable.name}\n'
        f'Version: {approval.deliverable_version.version_number}\n'
        f'Status: {approval.status}\n'
        f'Reviewer: {reviewer_email}\n'
    )
    if approval.comment:
        body += f'Comment: {approval.comment}\n'

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')

    try:
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=stakeholder_emails,
            fail_silently=False,
        )
        logger.info(
            'send_approval_notification: sent to %d recipients for approval %s',
            len(stakeholder_emails),
            approval_id,
        )
    except Exception:
        logger.exception(
            'send_approval_notification: failed to send email for approval %s', approval_id
        )
