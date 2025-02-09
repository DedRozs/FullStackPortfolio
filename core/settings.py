import os
from pathlib import Path
import pymysql
from dotenv import load_dotenv
from google.oauth2 import service_account
from google.auth import compute_engine, impersonated_credentials
from google.oauth2 import service_account

# Install MySQL Client
pymysql.install_as_MySQLdb()

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Security & Debug
SECRET_KEY = os.getenv("SECRET_KEY", "your-default-secret-key")



# ✅ Detect if running in Google App Engine
ON_GAE = "GOOGLE_CLOUD_PROJECT" in os.environ

# Debug mode - Only True in local development
DEBUG = not ON_GAE  # Automatically set to False when deployed on GAE

# Allowed Hosts
ALLOWED_HOSTS = [
    "ai-fullstack-portfolio.uc.r.appspot.com",
    "localhost",
    "thejosephprince.com",
    "www.thejosephprince.com",
    "portfolio.thejosephprince.com",
    "127.0.0.1",
]

# Installed Apps
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "storages",
    'apps.analytics',
    'rest_framework',
    'drf_yasg'
]


# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# Root URL Configuration
ROOT_URLCONF = "core.urls"

# Templates Configuration
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# WSGI Application
WSGI_APPLICATION = "core.wsgi.application"

# Database Configuration (Google Cloud SQL - MySQL)
DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT", "3306"),
        }
}

# Static & Media Files (Google Cloud Storage)
# Google Cloud Storage settings
GS_BUCKET_NAME = os.getenv("GS_BUCKET_NAME")


if ON_GAE:
    base_credentials = compute_engine.Credentials()
    GS_CREDENTIALS = impersonated_credentials.Credentials(
        source_credentials=base_credentials,
        target_principal=os.getenv("GAE_SERVICE_ACCOUNT", "ai-fullstack-portfolio@appspot.gserviceaccount.com"),
        target_scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
else:
    # Use service account credentials for local development
    GS_CREDENTIALS = service_account.Credentials.from_service_account_file(
        os.path.join(BASE_DIR,  "creds.json")
    )


STATICFILES_DIRS = [
    BASE_DIR / "static",
]


STORAGES = {
    "default": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": GS_BUCKET_NAME,
            "credentials": GS_CREDENTIALS,
            "location":"media/"
        }
    },
    "staticfiles": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": GS_BUCKET_NAME,
            "credentials": GS_CREDENTIALS,
            "location":"static/"
        }
    }
}

# Static files settings
STATIC_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/static/"
STATIC_ROOT = "staticfiles/"

# Media files settings
MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/"


EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp-pulse.com"  # Use Google's SMTP relay
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "your.email@example.com")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER



# Authentication
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# # Security (Production Settings)
# if ON_GAE:
#     SECURE_SSL_REDIRECT = True
#     SESSION_COOKIE_SECURE = True
#     CSRF_COOKIE_SECURE = True
#     SECURE_BROWSER_XSS_FILTER = True
#     SECURE_CONTENT_TYPE_NOSNIFF = True

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Denver"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Default Primary Key Field Type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
