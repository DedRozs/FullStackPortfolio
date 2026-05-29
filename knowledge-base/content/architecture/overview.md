# Architecture Overview

**System Type:** Full-Stack Web Application (Portfolio)
**Purpose:** Professional portfolio for Joseph Prince, Full Stack Developer - demonstrates
technical depth to hiring managers and consulting clients.
**Primary Language:** Python 3.14
**Framework:** Django 6.0.5
**Architecture Pattern:** Django monolith with React served as static files; background
worker on Cloud Run; Clean Architecture applied at the Django app level.

---

## High-Level Structure

The portfolio is a Django application deployed on Google App Engine. The React frontend
is compiled to static files and served directly by Django via `django.contrib.staticfiles`.
Long-running tasks (email delivery, SMS notifications, AI calls) are offloaded to a
Django Q2 task queue processed by a separate Cloud Run worker.

```
Browser
  |
  v
Google App Engine (Django 6.0.5 / Gunicorn)
  |-- /static/           --> React SPA (built artifacts)
  |-- /api/              --> Django REST views
  |-- /admin/            --> Django admin
  |-- /contact/          --> Contact form handlers
  |
  v
Django Q2 Task Queue (broker: MySQL)
  |
  v
Cloud Run Worker (Dockerfile.worker -> manage.py qcluster)
  |-- SendGrid (email)
  |-- Twilio (SMS)
  |-- OpenAI API (AI assistant)
  |
  v
Google Cloud SQL (MySQL 8.x)     Google Cloud Storage (files/media)
```

---

## Technology Stack

### Backend
- Language: Python 3.14 (Cloud Run), Python 3.12 (GAE runtime target)
- Framework: Django 6.0.5
- WSGI Server: Gunicorn 26.0.0
- Task Queue: Django Q2 1.10.0

### Frontend
- Framework: React (to be scaffolded)
- Integration: Compiled static files served by Django
- Location: `apps/react_app/` (source); `static/` (compiled output)

### Data Layer
- Database: MySQL 8.x on Google Cloud SQL
- ORM: Django ORM (built into Django)
- Caching: Not yet configured
- File Storage: Google Cloud Storage (`django-storages` 1.14.6)

### External Services
- Email: SendGrid 6.12.5 (transactional email)
- SMS: Twilio 9.10.9 (notifications)
- AI: OpenAI API 2.38.0 (AI assistant chatbot)
- Secrets/Config: Environment variables via `.env`

### Infrastructure
- Hosting: Google App Engine (Python 3.12 standard runtime)
- Background Worker: Google Cloud Run (`Dockerfile.worker`)
- File Storage: Google Cloud Storage bucket `ai-fullstack-portfolio.appspot.com`
- CI/CD: GitHub Actions (`.github/workflows/`)
- Credentials: `creds.json` (Google Cloud service account, gitignored)

---

## Django Applications

| App | Directory | Status | Responsibility |
|---|---|---|---|
| home | `apps/home/` | Not started | Hero section, LinkedIn integration |
| about | `apps/about/` | Not started | Professional background, skills |
| contact | `apps/contact/` | Not started | Contact form, SendGrid email |
| react_app | `apps/react_app/` | Not started | React SPA entry + static file serving |

The three portfolio demo projects are not yet defined. They will live as additional Django
apps under `apps/` once specified.

---

## Entry Points

- **Development server:** `python manage.py runserver` (from repo root, venv active)
- **Production WSGI:** `gunicorn core.wsgi:application`
- **Background worker:** `python manage.py qcluster` (Cloud Run container)
- **Django admin:** `/admin/`

---

## Key Design Decisions

- [ADR 0001](../decisions/0001-django-react-static-architecture.md) - Django + React-as-static-files architecture
- [ADR 0002](../decisions/0002-cloud-run-worker-for-async-tasks.md) - Cloud Run for Django Q2 worker

---

## Current Status

This project is a well-configured skeleton. All infrastructure credentials, third-party
integrations, and deployment targets are in place. No Django apps have been implemented
yet. See [components/overview.md](../components/overview.md) for the full component map.
