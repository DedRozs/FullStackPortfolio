import json
import logging

from django.conf import settings
from django.core.cache import cache
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import ContactMessage

logger = logging.getLogger(__name__)

REQUIRED_FIELDS = ('name', 'email', 'message')
RATE_LIMIT_SUBMISSIONS = 5
RATE_LIMIT_WINDOW_SECONDS = 3600


@csrf_exempt
@require_POST
def submit(request):
    """Receive a contact form submission, persist it, and fire notifications."""
    ip = _get_client_ip(request)
    cache_key = f'contact_submit_{ip}'
    submission_count = cache.get(cache_key, 0)
    if submission_count >= RATE_LIMIT_SUBMISSIONS:
        return JsonResponse(
            {'error': 'Too many submissions. Please try again later.'},
            status=429,
        )

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON payload.'}, status=400)

    missing = [f for f in REQUIRED_FIELDS if not body.get(f, '').strip()]
    if missing:
        return JsonResponse(
            {'error': f'Missing required fields: {", ".join(missing)}.'},
            status=400,
        )

    try:
        validate_email(body['email'].strip())
    except ValidationError:
        return JsonResponse({'error': 'Invalid email address.'}, status=400)

    message = ContactMessage.objects.create(
        name=body['name'].strip(),
        email=body['email'].strip(),
        subject=body.get('subject', '').strip(),
        message=body['message'].strip(),
    )

    cache.set(cache_key, submission_count + 1, RATE_LIMIT_WINDOW_SECONDS)

    _send_email_notification(message)
    _send_sms_notification(message)

    return JsonResponse({'status': 'ok', 'id': message.pk}, status=201)


def _get_client_ip(request) -> str:
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


def _send_email_notification(message: ContactMessage) -> None:
    """Send a notification email via Gmail SMTP. Logs errors without raising."""
    recipient = settings.CONTACT_RECIPIENT_EMAIL
    host_user = settings.EMAIL_HOST_USER
    if not recipient or not host_user:
        return

    try:
        from django.core.mail import send_mail

        send_mail(
            subject=f'Portfolio contact from {message.name}: {message.subject or "(no subject)"}',
            message=(
                f'Name: {message.name}\n'
                f'Email: {message.email}\n\n'
                f'{message.message}'
            ),
            from_email=host_user,
            recipient_list=[recipient],
            fail_silently=False,
        )
        message.email_sent = True
        message.save(update_fields=['email_sent'])
    except Exception:
        logger.exception('Email notification failed for ContactMessage pk=%s', message.pk)


def _send_sms_notification(message: ContactMessage) -> None:
    """Send an SMS alert via Twilio. Logs errors without raising."""
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_number = settings.TWILIO_PHONE_NUMBER
    to_number = settings.SMS_NOTIFICATION_NUMBER
    if not all([account_sid, auth_token, from_number, to_number]):
        return

    try:
        from twilio.rest import Client

        client = Client(account_sid, auth_token)
        client.messages.create(
            body=f'New portfolio contact from {message.name} ({message.email}).',
            from_=from_number,
            to=to_number,
        )
        message.sms_sent = True
        message.save(update_fields=['sms_sent'])
    except Exception:
        logger.exception('Twilio notification failed for ContactMessage pk=%s', message.pk)
