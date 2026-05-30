"""
Decorator-based registry for condition operators and action handlers.

Usage:
    from apps.workflow_automation.registry import register_action_handler, get_action_handler
    from apps.workflow_automation.domain.value_objects import ActionType

    @register_action_handler(ActionType.SEND_EMAIL)
    def handle_send_email(action_params: dict, context: dict) -> str:
        ...
"""
from __future__ import annotations

import logging
from typing import Callable

from apps.workflow_automation.domain.value_objects import ActionType, ConditionOperator

logger = logging.getLogger(__name__)

_action_handlers: dict[str, Callable] = {}
_condition_evaluators: dict[str, Callable] = {}


def register_action_handler(action_type: ActionType) -> Callable:
    def decorator(fn: Callable) -> Callable:
        _action_handlers[action_type.value] = fn
        return fn
    return decorator


def register_condition_evaluator(operator: ConditionOperator) -> Callable:
    def decorator(fn: Callable) -> Callable:
        _condition_evaluators[operator.value] = fn
        return fn
    return decorator


def get_action_handler(action_type: str) -> Callable | None:
    return _action_handlers.get(action_type)


def get_condition_evaluator(operator: str) -> Callable | None:
    return _condition_evaluators.get(operator)


# ---------------------------------------------------------------------------
# Default condition evaluators
# ---------------------------------------------------------------------------

@register_condition_evaluator(ConditionOperator.GT)
def _eval_gt(field_value: object, expected: object) -> bool:
    try:
        return float(str(field_value)) > float(str(expected))
    except (TypeError, ValueError):
        return False


@register_condition_evaluator(ConditionOperator.LT)
def _eval_lt(field_value: object, expected: object) -> bool:
    try:
        return float(str(field_value)) < float(str(expected))
    except (TypeError, ValueError):
        return False


@register_condition_evaluator(ConditionOperator.EQ)
def _eval_eq(field_value: object, expected: object) -> bool:
    return str(field_value) == str(expected)


@register_condition_evaluator(ConditionOperator.CONTAINS)
def _eval_contains(field_value: object, expected: object) -> bool:
    return str(expected) in str(field_value)


@register_condition_evaluator(ConditionOperator.ASSIGNED_TO)
def _eval_assigned_to(field_value: object, expected: object) -> bool:
    return str(field_value) == str(expected)


# ---------------------------------------------------------------------------
# Default action handlers (registered at import time)
# ---------------------------------------------------------------------------

@register_action_handler(ActionType.SEND_EMAIL)
def _handle_send_email(action_params: dict, context: dict) -> str:
    from django.conf import settings
    try:
        import sendgrid
        from sendgrid.helpers.mail import Mail
        sg = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        message = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=action_params.get('to_email', ''),
            subject=action_params.get('subject', 'Automation Notification'),
            plain_text_content=action_params.get('body', ''),
        )
        response = sg.send(message)
        return f'Email sent, status={response.status_code}'
    except Exception as exc:
        logger.exception('_handle_send_email failed: %s', exc)
        raise


@register_action_handler(ActionType.SEND_SMS)
def _handle_send_sms(action_params: dict, context: dict) -> str:
    from django.conf import settings
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body=action_params.get('body', 'Automation triggered'),
            from_=settings.TWILIO_FROM_NUMBER,
            to=action_params.get('to_number', ''),
        )
        return f'SMS sent, sid={message.sid}'
    except Exception as exc:
        logger.exception('_handle_send_sms failed: %s', exc)
        raise


@register_action_handler(ActionType.CREATE_ACTIVITY_EVENT)
def _handle_create_activity_event(action_params: dict, context: dict) -> str:
    import uuid
    from apps.client_portal import models as portal_orm
    portal_orm.ActivityEvent.objects.create(
        id=uuid.uuid4(),
        event_type=action_params.get('event_type', 'automation.triggered'),
        actor_id=None,
        project_id=action_params.get('project_id'),
        organization_id=action_params.get('organization_id'),
        payload={'automation_context': context},
    )
    return 'ActivityEvent created'


@register_action_handler(ActionType.UPDATE_STATUS)
def _handle_update_status(action_params: dict, context: dict) -> str:
    # Generic status update - logs the intent; callers extend with specific ORM calls
    model_type = action_params.get('model_type', 'unknown')
    object_id = action_params.get('object_id', context.get('source_id', ''))
    new_status = action_params.get('new_status', '')
    logger.info('update_status: %s id=%s -> %s', model_type, object_id, new_status)
    return f'Status update logged: {model_type} {object_id} -> {new_status}'
