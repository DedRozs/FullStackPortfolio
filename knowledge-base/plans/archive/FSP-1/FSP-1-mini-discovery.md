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
