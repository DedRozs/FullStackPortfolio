# Data Models

This document covers all Django data models, database configuration, and schema design
for FullStackPortfolio.

---

## Database Configuration

**Engine:** MySQL 8.x
**Host:** Google Cloud SQL (IP: configured via `DB_HOST` environment variable)
**Database name:** `Portfolio`
**ORM:** Django ORM

Development uses the credentials in `.env`. Production credentials must be rotated
before any public deployment (current `.env` credentials are exposed - see security note).

---

## Current Schema Status

No custom models have been created yet. The database schema consists only of Django's
built-in tables installed via `python manage.py migrate`:

| Table | Source | Purpose |
|---|---|---|
| `django_migrations` | Django core | Migration history |
| `django_content_type` | contenttypes | Generic relations |
| `auth_user` | django.contrib.auth | User accounts |
| `auth_group` | django.contrib.auth | Permission groups |
| `auth_permission` | django.contrib.auth | Individual permissions |
| `auth_user_groups` | django.contrib.auth | User-group membership |
| `auth_user_user_permissions` | django.contrib.auth | User-permission assignment |
| `django_admin_log` | django.contrib.admin | Admin action audit log |
| `django_session` | django.contrib.sessions | Session storage |
| `django_q_task` | django-q2 | Queued task definitions |
| `django_q_schedule` | django-q2 | Scheduled task config |
| `django_q_success` | django-q2 | Completed task log |
| `django_q_failure` | django-q2 | Failed task log |

---

## Planned Models

The following models will be added as Django apps are developed. Create an ADR before
finalizing any schema that involves relationships or non-trivial fields.

### ContactSubmission (apps/contact/)

Persists contact form submissions for audit and replay.

| Field | Type | Required | Description |
|---|---|---|---|
| id | AutoField | yes | Primary key |
| name | CharField(100) | yes | Sender's full name |
| email | EmailField | yes | Sender's email address |
| message | TextField | yes | Message body |
| submitted_at | DateTimeField(auto_now_add) | yes | Submission timestamp (UTC) |
| email_sent | BooleanField | yes | Whether SendGrid call succeeded |
| sms_sent | BooleanField | yes | Whether Twilio call succeeded |

---

## Migration Workflow

```bash
# Create migrations after adding/changing models
python manage.py makemigrations <app_name>

# Apply all pending migrations
python manage.py migrate

# Inspect current schema
python manage.py dbshell
```

Always review auto-generated migration files before applying. Never hand-edit migration
files; roll back and regenerate if a migration is wrong.

---

## File/Media Storage

**Backend:** Google Cloud Storage via `django-storages`
**Bucket:** `ai-fullstack-portfolio.appspot.com`
**Config variable:** `GS_BUCKET_NAME` in `.env`

Django's `DEFAULT_FILE_STORAGE` will be set to the GCS backend in `settings.py` when
media upload features are implemented. No media models exist yet.
