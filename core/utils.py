from pysendpulse.pysendpulse import PySendPulse
import os
from dotenv import load_dotenv

load_dotenv()


REST_API_ID = os.getenv("REST_API_ID")
REST_API_SECRET = os.getenv("REST_API_SECRET")
TOKEN_STORAGE = 'memcached' # or "file"

sp_api = PySendPulse(REST_API_ID, REST_API_SECRET, TOKEN_STORAGE)

def send_contact_form(message, sender_email, sender_name):
    output_message = f"Name: {sender_name}\nEmail: {sender_email}\n\nMessage:\n{message}",

    email_data = {
        'subject': 'New Contact Form Submission from {}'.format(sender_name),
        'text': output_message,
        'from': {
            'name': "Joseph Prince",
            'email': 'JPrince@TheJosephPrince.com'
        },
        'to': [
            {
                'name': "Joseph Prince",
                'email': 'jprincemarketing@gmail.com'
            }
        ]
    }

    try:
        result = sp_api.smtp_send_mail(email_data)
        print(result)
    except Exception as e:
        print(f"Error sending email: {e}")