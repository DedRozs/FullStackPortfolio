"""
Workflow automation engine entry point.

Usage:
    from apps.workflow_automation.engine import fire_trigger
    fire_trigger(
        'deliverable.approved',
        {'source_id': str(deliverable_id), 'source_type': 'Deliverable', 'payload': {...}}
    )
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def fire_trigger(trigger_type: str, context_payload: dict) -> None:
    """Enqueue Q2 tasks for every enabled AutomationRule matching trigger_type."""
    from apps.workflow_automation import models as orm
    from apps.workflow_automation.domain.value_objects import TriggerType
    from django_q.tasks import async_task

    try:
        trigger_enum = TriggerType(trigger_type)
    except ValueError:
        logger.warning('fire_trigger: unknown trigger type %r', trigger_type)
        return

    matching_ids = list(
        orm.AutomationRule.objects.filter(
            trigger_type=trigger_enum.value,
            is_enabled=True,
        ).values_list('id', flat=True)
    )

    for rule_id in matching_ids:
        async_task(
            'apps.workflow_automation.tasks.execute_automation_rule',
            str(rule_id),
            context_payload,
        )
        logger.info('fire_trigger: queued rule %s for trigger %r', rule_id, trigger_type)
