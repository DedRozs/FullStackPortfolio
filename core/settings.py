"""
Django settings for core project.
Environment variables are loaded from .env via django-environ.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)
environ.Env.read_env(BASE_DIR / '.env')

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env('ALLOWED_HOSTS')

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'channels',
    'django_q',
    'markdownx',
    'rest_framework',
    'rest_framework.authtoken',
    'allauth',
    'allauth.account',
    'allauth.headless',
    'dj_rest_auth',
    'django.contrib.sites',
    # Portfolio apps
    'apps.home',
    'apps.about',
    'apps.contact',
    'apps.ai_assistant',
    'apps.react_app',
    'apps.client_portal',
    'apps.blog',
    'apps.ops_dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'
ASGI_APPLICATION = 'core.asgi.application'

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASES = {
    'default': {
        **env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR}/db.sqlite3'),
        # Keep the Cloud SQL connection alive across requests instead of
        # paying the 2-4 s TCP/TLS setup cost on every API call.
        'CONN_MAX_AGE': 600,
    },
}

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

# Default PBKDF2 at 870 000 iterations takes 3-8 s on a constrained GAE
# instance. ScryptPasswordHasher is faster on modern hardware; SHA1 is kept
# as the fallback for tokens created before this change.
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.ScryptPasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []

# ---------------------------------------------------------------------------
# Default primary key
# ---------------------------------------------------------------------------

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# File upload limits
# ---------------------------------------------------------------------------

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB

# ---------------------------------------------------------------------------
# Google Cloud Storage (django-storages)
# ---------------------------------------------------------------------------

GS_BUCKET_NAME = env('GS_BUCKET_NAME', default='')

if GS_BUCKET_NAME:
    # In DEBUG mode serve static files locally so new builds are picked up
    # immediately without a collectstatic upload.  Media files (user uploads)
    # always use GCS even in DEBUG so upload/retrieval round-trips work.
    if DEBUG:
        STORAGES = {
            'default': {
                'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage',
                'OPTIONS': {'location': 'media'},
            },
            'staticfiles': {
                'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
            },
        }
    else:
        STORAGES = {
            'default': {
                'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage',
                'OPTIONS': {'location': 'media'},
            },
            'staticfiles': {
                'BACKEND': 'storages.backends.gcloud.GoogleCloudStorage',
                # querystring_auth=False generates plain public URLs instead of
                # signed URLs, so no credentials are needed at request time.
                # Static assets in this bucket are intentionally public-read.
                'OPTIONS': {'location': 'static', 'querystring_auth': False},
            },
        }
        STATIC_URL = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/static/'

# ---------------------------------------------------------------------------
# Django Channels / Redis channel layer
# ---------------------------------------------------------------------------

REDIS_URL = env('REDIS_URL', default='')

if REDIS_URL:
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                'hosts': [REDIS_URL],
            },
        },
    }
else:
    # Falls back to in-memory layer for local development without Redis.
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels.layers.InMemoryChannelLayer',
        },
    }

# ---------------------------------------------------------------------------
# AI providers
# ---------------------------------------------------------------------------

OPENAI_API_KEY = env('OPENAI_API_KEY', default='')
ANTHROPIC_API_KEY = env('ANTHROPIC_API_KEY', default='')

# ---------------------------------------------------------------------------
# Supabase (pgvector - blog post embeddings)
# ---------------------------------------------------------------------------

# Full PostgreSQL connection URL, e.g.:
# postgresql://postgres:PASSWORD@db.<ref>.supabase.co:5432/postgres
SUPABASE_DB_URL = env('SUPABASE_DB_URL', default='')

# ---------------------------------------------------------------------------
# Email (Gmail SMTP)
# ---------------------------------------------------------------------------

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = env('EMAIL_HOST_USER', default='')
CONTACT_RECIPIENT_EMAIL = env('CONTACT_RECIPIENT_EMAIL', default='')

# ---------------------------------------------------------------------------
# Twilio
# ---------------------------------------------------------------------------

TWILIO_ACCOUNT_SID = env('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = env('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = env('TWILIO_PHONE_NUMBER', default='')
SMS_NOTIFICATION_NUMBER = env('SMS_NOTIFICATION_NUMBER', default='')

# ---------------------------------------------------------------------------
# Django Q2 (background jobs)
# ---------------------------------------------------------------------------

Q_CLUSTER = {
    'name': 'portfolio',
    'workers': 2,
    'timeout': 90,
    'retry': 120,
    'queue_limit': 50,
    'bulk': 10,
    'redis': REDIS_URL or 'redis://127.0.0.1:6379/1',
}

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/hour',
        'user': '200/hour',
        'login': '10/hour',
    },
}

# ---------------------------------------------------------------------------
# django-allauth
# ---------------------------------------------------------------------------

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_LOGIN_METHODS = {'email'}
SITE_ID = 1
