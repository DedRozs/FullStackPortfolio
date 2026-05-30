"""
Background tasks for workflow_automation.

Usage:
    from django_q.tasks import async_task
    async_task(
        'apps.workflow_automation.tasks.execute_automation_rule',
        str(rule_id),
        context_dict,
    )
    async_task('apps.workflow_automation.tasks.check_invoice_overdue_rules')
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def execute_automation_rule(rule_id: str, context_payload: dict) -> None:
    """Execute a single AutomationRule for a given trigger context."""
    import uuid
    from apps.workflow_automation.application.dtos import ExecuteRuleCommand
    from apps.workflow_automation.application.use_cases import ExecuteRule
    from apps.workflow_automation.infrastructure.repositories import (
        DjangoAutomationActionRepository,
        DjangoAutomationConditionRepository,
        DjangoAutomationRuleRepository,
        DjangoAutomationRunLogRepository,
        DjangoAutomationRunRepository,
    )
    from apps.workflow_automation.registry import get_action_handler, get_condition_evaluator
    from apps.workflow_automation.domain.value_objects import ConditionOperator, ActionType

    rule_repo = DjangoAutomationRuleRepository()
    condition_repo = DjangoAutomationConditionRepository()
    action_repo = DjangoAutomationActionRepository()
    run_repo = DjangoAutomationRunRepository()
    run_log_repo = DjangoAutomationRunLogRepository()

    condition_evaluators = {
        op.value: get_condition_evaluator(op.value)
        for op in ConditionOperator
        if get_condition_evaluator(op.value)
    }
    action_handlers = {
        at.value: get_action_handler(at.value)
        for at in ActionType
        if get_action_handler(at.value)
    }

    use_case = ExecuteRule(
        rule_repo=rule_repo,
        condition_repo=condition_repo,
        action_repo=action_repo,
        run_repo=run_repo,
        run_log_repo=run_log_repo,
    )
    use_case.set_condition_evaluators(condition_evaluators)
    use_case.set_action_handlers(action_handlers)

    trigger_type = context_payload.get('trigger_type', '')
    cmd = ExecuteRuleCommand(
        rule_id=uuid.UUID(rule_id),
        trigger_type=trigger_type,
        context_payload=context_payload,
    )
    try:
        dto = use_case.execute(cmd)
        logger.info(
            'execute_automation_rule: rule=%s status=%s', rule_id, dto.status
        )
    except Exception:
        logger.exception('execute_automation_rule: failed for rule=%s', rule_id)
        raise


def check_invoice_overdue_rules() -> None:
    """Fire the invoice.overdue trigger for all OVERDUE invoices.

    Called by the Q2 scheduler (e.g. daily).
    """
    from apps.client_portal import models as portal_orm
    from apps.workflow_automation.engine import fire_trigger

    overdue_invoices = portal_orm.InvoiceRecord.objects.filter(status='OVERDUE')
    for invoice in overdue_invoices:
        fire_trigger(
            'invoice.overdue',
            {
                'trigger_type': 'invoice.overdue',
                'source_id': str(invoice.id),
                'source_type': 'InvoiceRecord',
                'payload': {
                    'project_id': str(invoice.project_id) if invoice.project_id else None,
                },
            },
        )
        logger.info('check_invoice_overdue_rules: fired for invoice %s', invoice.id)
