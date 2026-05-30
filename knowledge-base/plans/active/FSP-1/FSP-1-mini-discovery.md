# Mini Discovery Artifact

**Ticket:** FSP-1
**Generated:** 2026-05-29
**Backend:** internal

---

## ticketIdentity

- **issueKey:** FSP-1
- **issueType:** Story
- **title:** client_portal Phase 1 - Foundation: App Registration, Models, Migrations, and Seed Data
- **status:** In Progress

---

## summary

Register the `apps/client_portal` Django app and implement the foundational data layer: 10 Django ORM models covering client organizations, user profiles, projects, milestones, deliverables, approvals, file records, messages, invoices, and activity events. Write and run migrations. Produce a seed script generating 2 demo organizations, 3 projects (active / pending approval / complete), and 1 overdue invoice.

**Bounded Context:** `client_portal` - the secure client project portal bounded context.

**Out of Scope:** DRF viewsets, React UI, authentication flows, background tasks - those belong to subsequent phases.

---

## ticketSize

story

---

## routedPhases

1. domain-modeling-orchestrator
2. development-orchestrator
3. qa-orchestrator
4. documentation-orchestrator

---

## acceptanceCriteria

- `apps/client_portal` registered in INSTALLED_APPS and loads without error
- All 10 models defined with appropriate fields, relationships, and `__str__` methods
- Django migrations written and apply cleanly (`migrate --run-syncdb`)
- Seed script produces: 2 ClientOrganization records, 3 Project records (one per status), 1 InvoiceRecord with overdue status
- All model fields follow the ubiquitous language of the client portal domain

---

## constraints

- Python 3.14, Django 6.0.5
- Clean Architecture: models belong in the infrastructure layer (ORM); domain entities may be separate if DDD guidelines require it
- Follow `.github/instructions/ddd-domain-model.instructions.md` and `.github/instructions/ddd-infrastructure.instructions.md`
- No business logic in model methods (state machines belong in `application/services/`)
- All files must use UTF-8 encoding; no emojis or non-ASCII characters

---

## Codebase Context

### Bounded Contexts Found

- `contact` - ContactMessage model + migrations implemented; canonical reference app for new bounded contexts. Source: [apps/contact/](apps/contact/)
- `ai_assistant` - Registered in INSTALLED_APPS; stub only (no models). Source: [apps/ai_assistant/](apps/ai_assistant/)
- `home` - Registered in INSTALLED_APPS; stub only. Source: [apps/home/](apps/home/)
- `about` - Registered in INSTALLED_APPS; stub only. Source: [apps/about/](apps/about/)
- `react_app` - React SPA entry point and static file serving; no models. Source: [apps/react_app/](apps/react_app/)
- `client_portal` - NEW; does not yet exist. This is the bounded context FSP-1 introduces.

### Key ADRs

2 ADRs on record:

- ADR 0001: Django + React-as-Static-Files Architecture - React compiled to static files, served by Django; no separate Node server in production. Source: [knowledge-base/content/decisions/0001-django-react-static-architecture.md](knowledge-base/content/decisions/0001-django-react-static-architecture.md)
- ADR 0002: Cloud Run Worker for Async Task Processing - Django Q2 task queue with MySQL broker; async worker on Cloud Run for email/SMS/AI calls. Source: [knowledge-base/content/decisions/0002-cloud-run-worker-for-async-tasks.md](knowledge-base/content/decisions/0002-cloud-run-worker-for-async-tasks.md)

### Established Patterns

- **AppConfig registration pattern** - Every app defines an `AppConfig` subclass with `name = 'apps.<label>'`, `label = '<label>'`, and `default_auto_field = 'django.db.models.BigAutoField'`. Registered in `INSTALLED_APPS` as the dotted string `'apps.<label>'`. Reference: [apps/contact/apps.py](apps/contact/apps.py)
- **Django ORM model pattern** - Models are plain Django ORM classes. Each model has a `__str__` method returning a human-readable string, a `Meta` class with `ordering`, and `auto_now_add` on timestamp fields. No business logic in model methods. Reference: [apps/contact/models.py](apps/contact/models.py)
- **Migration pattern** - Auto-generated Django migrations; first migration per app is `0001_initial.py`; all PKs use `BigAutoField`. Reference: [apps/contact/migrations/0001_initial.py](apps/contact/migrations/0001_initial.py)
- **DDD domain-infrastructure split** - Domain entities are pure Python dataclasses in `domain/` with no external dependencies. ORM models are infrastructure artifacts in `infrastructure/persistence/` that map to domain entities via `reconstitute()`. Repository interfaces are ABCs in `domain/repositories/`. Reference: [.github/instructions/ddd-domain-model.instructions.md](.github/instructions/ddd-domain-model.instructions.md), [.github/instructions/ddd-infrastructure.instructions.md](.github/instructions/ddd-infrastructure.instructions.md)
- **Clean Architecture layer separation** - No business logic in Django ORM models or views. State machines and orchestration belong in `application/services/`. Dependencies point inward (domain <- application <- infrastructure). Reference: [.github/instructions/clean-architecture.instructions.md](.github/instructions/clean-architecture.instructions.md)

### Implementation Notes

- Register the new app as `'apps.client_portal'` in `INSTALLED_APPS` in [core/settings.py](core/settings.py) after the existing portfolio apps block, consistent with `'apps.contact'` and `'apps.ai_assistant'`.
- `AppConfig` for the new app must set `default_auto_field = 'django.db.models.BigAutoField'` to match all existing apps.
- The 10 Django ORM models are infrastructure-layer artifacts. If the DDD guidelines require it, place domain entities (pure dataclasses) under `apps/client_portal/domain/` and ORM models under `apps/client_portal/infrastructure/`. The `contact` app uses a flat layout (models directly in the app); `client_portal` complexity warrants the layered layout.
- The first migration file must be `0001_initial.py` and must be auto-generated via `makemigrations apps.client_portal`.
- No `__str__` method may contain business logic - it must return a simple descriptive string using field values only.
- The architecture overview notes "The three portfolio demo projects are not yet defined" - `client_portal` is the first concrete bounded context beyond the initial portfolio skeleton.
- The seed script is not a management command in the existing codebase; the `contact` app has no equivalent. Implement it as a standalone management command under `apps/client_portal/management/commands/seed_client_portal.py` following Django's management command convention.
