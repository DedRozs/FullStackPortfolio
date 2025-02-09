import os
from pathlib import Path
import pymysql
from dotenv import load_dotenv
from google.auth.credentials import AnonymousCredentials
from google.oauth2 import service_account

# Install MySQL Client
pymysql.install_as_MySQLdb()

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Security & Debug
SECRET_KEY = os.getenv("SECRET_KEY", "your-default-secret-key")

# Detect if running in Google App Engine
ON_GAE = os.getenv("GAE_ENV", "")

# Debug mode - Only True in local development
DEBUG = not ON_GAE  # Automatically set to False when deployed on GAE
DEBUG = True
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
    "storages"
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
    # ✅ Fix: Use anonymous credentials for static files to prevent signing error
    GS_CREDENTIALS = AnonymousCredentials()
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
        }
    },
    "staticfiles": {
        "BACKEND": "storages.backends.gcloud.GoogleCloudStorage",
        "OPTIONS": {
            "bucket_name": GS_BUCKET_NAME,
            "credentials": GS_CREDENTIALS,
        }
    }
}

# Static files settings
STATIC_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/static/"
STATIC_ROOT = "staticfiles/"

# Media files settings
MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/"





# Authentication
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Security (Production Settings)
if ON_GAE:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/Denver"
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Default Primary Key Field Type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
