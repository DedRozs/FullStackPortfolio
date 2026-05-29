import json
from unittest.mock import patch

from django.core.cache import cache
from django.test import Client, TestCase

from .models import ContactMessage
from .views import RATE_LIMIT_SUBMISSIONS

SUBMIT_URL = '/api/contact/submit/'

VALID_PAYLOAD = {
    'name': 'Jane Doe',
    'email': 'jane@example.com',
    'subject': 'Hello',
    'message': 'This is a test message.',
}


def _post(client: Client, payload: dict, ip: str = '10.0.0.1') -> object:
    return client.post(
        SUBMIT_URL,
        data=json.dumps(payload),
        content_type='application/json',
        REMOTE_ADDR=ip,
    )


class ContactSubmitHappyPathTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch('apps.contact.views._send_sms_notification')
    @patch('apps.contact.views._send_email_notification')
    def test_valid_submission_returns_201(self, mock_email, mock_sms):
        response = _post(self.client, VALID_PAYLOAD)

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data['status'], 'ok')
        self.assertIn('id', data)

    @patch('apps.contact.views._send_sms_notification')
    @patch('apps.contact.views._send_email_notification')
    def test_valid_submission_persists_to_db(self, mock_email, mock_sms):
        _post(self.client, VALID_PAYLOAD)

        self.assertEqual(ContactMessage.objects.count(), 1)
        msg = ContactMessage.objects.first()
        self.assertEqual(msg.name, 'Jane Doe')
        self.assertEqual(msg.email, 'jane@example.com')
        self.assertEqual(msg.subject, 'Hello')
        self.assertEqual(msg.message, 'This is a test message.')

    @patch('apps.contact.views._send_sms_notification')
    @patch('apps.contact.views._send_email_notification')
    def test_subject_is_optional(self, mock_email, mock_sms):
        payload = {**VALID_PAYLOAD, 'subject': ''}
        response = _post(self.client, payload)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(ContactMessage.objects.first().subject, '')

    @patch('apps.contact.views._send_sms_notification')
    @patch('apps.contact.views._send_email_notification')
    def test_whitespace_is_stripped_from_fields(self, mock_email, mock_sms):
        payload = {
            'name': '  Jane Doe  ',
            'email': '  jane@example.com  ',
            'subject': '  Hello  ',
            'message': '  Test.  ',
        }
        _post(self.client, payload)

        msg = ContactMessage.objects.first()
        self.assertEqual(msg.name, 'Jane Doe')
        self.assertEqual(msg.email, 'jane@example.com')
        self.assertEqual(msg.subject, 'Hello')
        self.assertEqual(msg.message, 'Test.')

    @patch('apps.contact.views._send_sms_notification')
    @patch('apps.contact.views._send_email_notification')
    def test_notifications_are_called(self, mock_email, mock_sms):
        _post(self.client, VALID_PAYLOAD)

        mock_email.assert_called_once()
        mock_sms.assert_called_once()


class ContactSubmitValidationTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_missing_name_returns_400(self):
        payload = {**VALID_PAYLOAD, 'name': ''}
        response = _post(self.client, payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn('name', response.json()['error'])

    def test_missing_email_returns_400(self):
        payload = {**VALID_PAYLOAD, 'email': ''}
        response = _post(self.client, payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.json()['error'])

    def test_missing_message_returns_400(self):
        payload = {**VALID_PAYLOAD, 'message': ''}
        response = _post(self.client, payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn('message', response.json()['error'])

    def test_invalid_email_format_returns_400(self):
        payload = {**VALID_PAYLOAD, 'email': 'not-an-email'}
        response = _post(self.client, payload)

        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid email', response.json()['error'])

    def test_invalid_json_returns_400(self):
        response = self.client.post(
            SUBMIT_URL,
            data='not json{{{',
            content_type='application/json',
            REMOTE_ADDR='10.0.0.1',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid JSON', response.json()['error'])

    def test_get_request_returns_405(self):
        response = self.client.get(SUBMIT_URL)
        self.assertEqual(response.status_code, 405)

    def test_no_db_record_on_validation_failure(self):
        _post(self.client, {**VALID_PAYLOAD, 'email': 'bad'})
        self.assertEqual(ContactMessage.objects.count(), 0)


class ContactSubmitRateLimitTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch('apps.contact.views._send_sms_notification')
    @patch('apps.contact.views._send_email_notification')
    def test_rate_limit_blocks_after_max_submissions(self, mock_email, mock_sms):
        ip = '10.0.0.42'
        for _ in range(RATE_LIMIT_SUBMISSIONS):
            resp = _post(self.client, VALID_PAYLOAD, ip=ip)
            self.assertEqual(resp.status_code, 201)

        blocked = _post(self.client, VALID_PAYLOAD, ip=ip)
        self.assertEqual(blocked.status_code, 429)
        self.assertIn('Too many submissions', blocked.json()['error'])

    @patch('apps.contact.views._send_sms_notification')
    @patch('apps.contact.views._send_email_notification')
    def test_rate_limit_is_per_ip(self, mock_email, mock_sms):
        for _ in range(RATE_LIMIT_SUBMISSIONS):
            _post(self.client, VALID_PAYLOAD, ip='10.0.0.1')

        response = _post(self.client, VALID_PAYLOAD, ip='10.0.0.2')
        self.assertEqual(response.status_code, 201)

    @patch('apps.contact.views._send_sms_notification')
    @patch('apps.contact.views._send_email_notification')
    def test_no_extra_db_records_when_rate_limited(self, mock_email, mock_sms):
        ip = '10.0.0.99'
        for _ in range(RATE_LIMIT_SUBMISSIONS):
            _post(self.client, VALID_PAYLOAD, ip=ip)

        _post(self.client, VALID_PAYLOAD, ip=ip)
        self.assertEqual(ContactMessage.objects.count(), RATE_LIMIT_SUBMISSIONS)


class ContactSubmitIpExtractionTests(TestCase):
    def setUp(self):
        cache.clear()

    @patch('apps.contact.views._send_sms_notification')
    @patch('apps.contact.views._send_email_notification')
    def test_x_forwarded_for_is_used_when_present(self, mock_email, mock_sms):
        for _ in range(RATE_LIMIT_SUBMISSIONS):
            self.client.post(
                SUBMIT_URL,
                data=json.dumps(VALID_PAYLOAD),
                content_type='application/json',
                HTTP_X_FORWARDED_FOR='1.2.3.4, 5.6.7.8',
                REMOTE_ADDR='10.0.0.1',
            )

        # 10.0.0.1 should NOT be rate-limited - the limit should be on 1.2.3.4
        response = self.client.post(
            SUBMIT_URL,
            data=json.dumps(VALID_PAYLOAD),
            content_type='application/json',
            REMOTE_ADDR='10.0.0.1',
        )
        self.assertEqual(response.status_code, 201)
