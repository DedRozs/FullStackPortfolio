# Component Map

This document maps every component in the FullStackPortfolio codebase, its responsibility,
current status, and links to detailed documentation.

---

## Django Core Configuration

**Location:** `core/`
**Status:** Configured (minimal), ready for app development

| File | Purpose |
|---|---|
| `core/settings.py` | All Django settings (database, installed apps, middleware, static files) |
| `core/urls.py` | Root URL dispatcher - currently only routes `/admin/` |
| `core/wsgi.py` | WSGI entry point for Gunicorn (production) |
| `core/asgi.py` | ASGI entry point (for potential async support) |
| `core/__init__.py` | Marks core as a Python package |

**Known gaps:**
- `INSTALLED_APPS` does not yet include any of the `apps/` modules
- `TEMPLATES['DIRS']` is empty - template directory not configured
- `DEBUG = True` is hardcoded; should read from environment

---

## Django Applications

### home

**Location:** `apps/home/`
**Status:** Not started - empty directory
**Responsibility:** Home page hero section and LinkedIn profile integration

Planned files (not yet created):
- `views.py` - Hero and profile view
- `urls.py` - Route definitions
- `templates/home/` - HTML templates
- `tests.py` - Unit tests

---

### about

**Location:** `apps/about/`
**Status:** Not started - empty directory
**Responsibility:** Professional background, skills, resume

Planned files (not yet created):
- `views.py` - About page view
- `urls.py` - Route definitions
- `templates/about/` - HTML templates
- `tests.py` - Unit tests

---

### contact

**Location:** `apps/contact/`
**Status:** Not started - empty directory
**Responsibility:** Contact form with SendGrid email delivery and optional Twilio SMS notification

Planned files (not yet created):
- `views.py` - Form handling view (POST only)
- `urls.py` - Route definitions
- `forms.py` - Django form with validation
- `tasks.py` - Django Q2 async tasks for email/SMS dispatch
- `templates/contact/` - HTML templates
- `tests.py` - Unit tests

**External integrations:** SendGrid API, Twilio API, Django Q2

---

### react_app

**Location:** `apps/react_app/`
**Status:** Not started - empty directory
**Responsibility:** React SPA source code and static file serving configuration

Planned structure:
- `src/` - React source (components, pages, hooks)
- `public/` - Static assets
- `package.json` - Node dependencies
- `build/` or `dist/` - Compiled output (served by Django staticfiles)

**Note:** React is not a separate server. The compiled artifacts are served via
`django.contrib.staticfiles` - no Node.js process runs in production.

---

## Portfolio Demo Applications

Three portfolio demo applications have not yet been specified. They will be added as
Django apps under `apps/` and documented here once defined. See
[concept.md](../concept.md) for the project brief.

---

## Background Worker

**Location:** `Dockerfile.worker`
**Status:** Ready - not deployed yet
**Responsibility:** Runs `manage.py qcluster` to process Django Q2 async task queue

Worker handles:
- SendGrid email delivery tasks
- Twilio SMS notification tasks
- OpenAI API calls (AI assistant responses)

**Infrastructure:** Google Cloud Run (stateless container, scales to zero)

---

## AI SDLC Pipeline

**Location:** `.github/agents/`, `.github/prompts/`, `.github/instructions/`
**Status:** Fully defined
**Responsibility:** Hierarchical multi-agent pipeline for SDLC workflow in VS Code Copilot

77 specialist agents covering 7 SDLC phases. See [AGENT-HIERARCHY.md](../../../AGENT-HIERARCHY.md)
for the full hierarchy.

---

## Phase Artifact Contracts

**Location:** `contracts/`
**Status:** Fully defined

| Directory | Contents |
|---|---|
| `contracts/schemas/` | 9 JSON schemas for phase-to-phase artifact validation |
| `contracts/templates/` | 9 Markdown templates for filling out phase artifacts |

---

## Relationships

```
Browser
  |
  +-- React SPA (apps/react_app/ -> compiled static files)
  |
  +-- Django Views
       |-- apps/home/views.py    -> renders home page
       |-- apps/about/views.py   -> renders about page
       |-- apps/contact/views.py -> handles contact form POST
       |
       +-- Django Q2 Task Queue (MySQL broker)
            |
            +-- Cloud Run Worker (Dockerfile.worker)
                 |-- apps/contact/tasks.py (SendGrid, Twilio)
                 |-- AI assistant tasks (OpenAI)
```
