# Mini-Discovery Artifact

<!-- This artifact is produced by ticket-intake-agent (Stage 0) and enriched by
     codebase-context-agent before the first routed phase orchestrator is invoked.
     Complete every required section. The Codebase Context section is optional and
     is appended by codebase-context-agent if prior archive artifacts exist.
     Validate against: contracts/schemas/mini-discovery.schema.json -->

**Produced by:** `.github/agents/ticket-intake-agent.agent.md` (enriched by `.github/agents/codebase-context-agent.agent.md`)
**Consumed by:** domain-modeling-orchestrator

---

## Ticket Identity

| Field | Value |
|---|---|
| Issue key | FSP-3 |
| Issue type | Epic |
| Project key | FSP |
| Backend | internal |

---

## Summary

Secure Client Portal with Project Approvals and File Management. A full-stack client
portal where companies manage projects, files, deliverables, invoices, messages, and
approvals. Demonstrates secure permissioned multi-user workflows - the kind of software
companies actually pay developers to build. Covers a new `client_portal` bounded context
built on top of the existing Django + DRF + React stack, spanning domain models, a REST
API with object-level permissions, a React UI, DDD layering, unit tests, and portfolio
documentation.

---

## Description

A full-stack client portal where companies manage projects, files, deliverables,
invoices, messages, and approvals. Shows secure permissioned multi-user workflows - the
kind of software companies actually pay developers to build.

Portfolio title: "Secure Client Portal with Project Approvals and File Management"

### Phase 1 - Foundation (Days 1-3)

- Register `apps/client_portal` Django app
- Define models:
  - `ClientOrganization`
  - `ClientUserProfile`
  - `Project`
  - `Milestone`
  - `Deliverable`
  - `DeliverableApproval`
  - `ProjectFile`
  - `ClientMessage`
  - `InvoiceRecord`
  - `ActivityEvent`
- Write and run migrations
- Seed script: 2 demo orgs, 3 projects (active / pending approval / complete), 1 overdue invoice

### Phase 2 - Backend API (Days 4-8)

- DRF viewsets for all models
- Object-level permissions: clients see only their org's data; staff see all
- `services/approvals.py` - approval state machine (pending -> approved/rejected + audit trail)
- `services/files.py` - file upload to GCS via django-storages
- `services/notifications.py` - SendGrid email on approval state change (Q2 background task)
- Test module: approval workflow service unit tests

### Phase 3 - React UI (Days 9-16)

- React routes: `/portal`, `/portal/projects/:id`, `/portal/files`, `/portal/messages`
- Auth flow: login page -> dashboard (allauth token exchange with DRF)
- Project dashboard: status cards, milestone list, deliverable table with approve/reject actions
- File upload component with progress indicator
- Activity timeline component (read-only feed of `ActivityEvent`)
- Invoice status panel (mockup - no real payment processing)

### Phase 4 - Polish + Documentation (Days 17-21)

- Cyberpunk design system applied consistently throughout
- Seed data polished to tell a realistic story
- Projects page writeup:
  - Problem it solves
  - Why object-level permissions (not just `IsAuthenticated`)
  - One tradeoff made during build

### New dependencies

- `djangorestframework`
- `django-allauth`
- `dj-rest-auth`

---

## Acceptance Criteria

<!-- No explicit Given/When/Then clauses found in the ticket body. Acceptance criteria
     below are derived from the phase checklist deliverables as the authoritative
     definition of done for this epic. -->

- The `client_portal` Django app is registered and all ten domain models are defined,
  migrated, and seeded with two demo orgs, three projects spanning all three statuses,
  and one overdue invoice.
- DRF viewsets exist for all models and enforce object-level permissions so that a client
  user can only read and write records belonging to their own `ClientOrganization`.
- The approval state machine in `services/approvals.py` transitions a `DeliverableApproval`
  from pending to approved or rejected and persists a full audit trail of each transition.
- File upload to Google Cloud Storage via `services/files.py` works end-to-end and is
  exercised by at least one integration test.
- `services/notifications.py` queues a SendGrid email via Django-Q2 on every approval
  state change.
- Unit tests cover the approval workflow service with no I/O dependencies.
- The React frontend exposes routes `/portal`, `/portal/projects/:id`, `/portal/files`,
  and `/portal/messages`.
- The auth flow completes the allauth token exchange with DRF and redirects an
  authenticated user to the portal dashboard.
- The project dashboard renders status cards, a milestone list, and a deliverable table
  with working approve/reject actions.
- The file upload component shows a progress indicator during upload.
- The activity timeline renders a read-only feed of `ActivityEvent` records.
- The invoice status panel renders correctly (mockup only - no real payment processing).
- The cyberpunk design system is applied consistently throughout all portal views.
- The portfolio writeup explains the problem, justifies object-level permissions over
  `IsAuthenticated`, and documents one tradeoff made during build.
- `core/asgi.py` is updated to use Django Channels' `ProtocolTypeRouter`, Daphne is
  the ASGI entrypoint, and the `CHANNEL_LAYERS` setting points to the Redis instance
  on the VPS via a `REDIS_URL` environment variable.

---

## Ticket Size

epic

Derived from issue type: Epic. This ticket introduces a new bounded context spanning
domain modeling, a full REST API, a React UI, DDD layering, tests, and documentation
across an estimated four weeks of work. Discovery and architecture phases are already
complete (established by prior bounded contexts in this portfolio). Deployment is handled
separately. Routed phases are therefore domain-modeling through documentation.

---

## Routed Phases

- domain-modeling-orchestrator
- development-orchestrator
- qa-orchestrator
- documentation-orchestrator

---

## Codebase Context

### Existing client_portal State

`apps/client_portal/` is partially implemented. The following already exists and must
NOT be recreated:

**ORM layer (`apps/client_portal/models.py`) - all models present:**
- `ClientOrganization` - UUID PK, name, slug, created_at
- `UserProfile` - UUID PK, OneToOne(User), email, is_client, FK(ClientOrganization nullable), created_at
- `Project` - UUID PK, name, FK(ClientOrganization), status (DRAFT/ACTIVE/PENDING_APPROVAL/COMPLETE/ARCHIVED), description, target_date
- `Milestone` - UUID PK, name, FK(Project), status (PENDING/IN_PROGRESS/COMPLETE), target_date
- `Deliverable` - UUID PK, name, FK(Milestone), description, current_version_number
- `DeliverableVersion` - UUID PK, FK(Deliverable), version_number, notes; unique_together (deliverable, version_number)
- `Approval` - UUID PK, OneToOne(DeliverableVersion), FK(UserProfile as reviewer), status (PENDING/APPROVED/REJECTED/REVISION_REQUESTED), comment, decided_at
- `MessageThread` - UUID PK, subject, FK(Project)
- `Message` - UUID PK, FK(MessageThread), FK(UserProfile as sender), body
- `FileRecord` - UUID PK, filename, storage_path, mime_type, file_size_bytes, FK(DeliverableVersion nullable), FK(Message nullable), FK(UserProfile as uploaded_by)
- `InvoiceRecord` - UUID PK, status (DRAFT/SENT/PAID/OVERDUE/CANCELLED) - partially read; full schema in file

**Naming divergence from ticket:** The artifact uses `ClientUserProfile`, `DeliverableApproval`,
`ProjectFile`, and `ClientMessage` - the actual ORM model names are `UserProfile`,
`Approval`, `FileRecord`, `MessageThread`/`Message`. Use the actual model names throughout.

**Domain layer (`apps/client_portal/domain/`) - fully scaffolded:**
- `model.py` - Plain Python dataclasses with `__post_init__` invariants and state-transition
  methods (`submit_for_approval`, `return_to_active`, `mark_complete`, `archive` on `Project`;
  similar on `Milestone`, `Approval`, `InvoiceRecord`). Zero Django imports. `ActivityEvent`
  dataclass also present.
- `value_objects.py` - Enums: `ProjectStatus`, `MilestoneStatus`, `ApprovalStatus`,
  `InvoiceStatus`, `StakeholderRole`. Frozen dataclasses: `Money`, `FileMetadata`,
  `VersionNumber`.
- `repositories.py` - ABC repository interfaces for all domain entities
  (`ClientOrganizationRepository`, `UserProfileRepository`, `ProjectRepository`, and
  more). Zero Django imports.
- `events.py` - Domain events as frozen dataclasses (`ClientOrganizationRegistered`,
  `UserProfileCreated`, `ProjectActivated`, `ProjectSubmittedForApproval`,
  `ProjectCompleted`, `ProjectArchived`, and others).

**Migrations:** `migrations/0001_initial.py` exists - the initial migration has already
been created. Running `migrate` will apply it; do not recreate it.

**Tests:** `tests.py` has unit tests covering ORM `__str__` methods, domain invariant
enforcement, and state-transition guards. All use `SimpleTestCase` (no database I/O).

**Missing layers (work required):**
- No `application/` layer (no use cases, no DTOs)
- No `infrastructure/` layer (no concrete repository implementations)
- No `urls.py`, no `views.py`, no `services/` directory
- No DRF viewsets or serializers

---

### Reference Implementation

`apps/blog/` is the canonical DDD reference. Follow these patterns exactly:

**Domain layer (`apps/blog/domain/`):**
- `entities.py` - Plain Python classes with `_pending_events` list for domain events;
  state transitions raise named exception types (e.g., `PublishInvariantError`)
- `repositories.py` - ABCs with typed method signatures; one interface per aggregate root
- `value_objects.py` - Frozen dataclasses and `str`-subclassing enums
- `events.py` - Frozen dataclasses with `occurred_at: datetime`
- `exceptions.py` - Named exception subclasses (e.g., `PostNotFoundError`, `SlugConflictError`)

**Application layer (`apps/blog/application/`):**
- `use_cases.py` - One class per use case; constructor receives repository interfaces;
  single `execute()` method; orchestration only - no business logic
- `dtos.py` - `@dataclass` DTOs for all inputs and outputs; no Django or ORM types cross
  the layer boundary

**Infrastructure layer (`apps/blog/infrastructure/`):**
- `repositories.py` - Concrete Django ORM implementations of the domain ABCs;
  private `_model_to_entity()` mapper functions translate ORM -> domain; `save()` uses
  `Model.objects.filter(pk=...).update()` for updates and `Model().save()` for inserts

**Key DI pattern:** Use cases are instantiated in views/viewsets with concrete repository
classes passed to constructors. No service locator; no global registry.

---

### Settings Snapshot

Current `core/settings.py` state relevant to this epic:

- `apps.client_portal` - already in `INSTALLED_APPS`
- `django_q` - already in `INSTALLED_APPS`; `django-q2==1.10.0` installed
- `django-storages==1.14.6` - installed; GCS backend already wired in `STORAGES` setting
  via `GS_BUCKET_NAME` env var (both `default` and `staticfiles` backends use
  `storages.backends.gcloud.GoogleCloudStorage`)
- `sendgrid==6.12.5` - installed; usable for notifications immediately
- `EMAIL_BACKEND` - Gmail SMTP (`smtp.gmail.com:587 TLS`)
- No `rest_framework` in `INSTALLED_APPS` - DRF not yet registered
- No `allauth` or `dj_rest_auth` in `INSTALLED_APPS` - allauth not yet registered
- No `REST_FRAMEWORK` settings block
- No `CHANNEL_LAYERS` settings block
- No `ASGI_APPLICATION` setting (deployment is currently WSGI via `core.wsgi.application`)
- Database: SQLite in dev (`DATABASE_URL` env var), MySQL in production

---

### Missing Dependencies

These packages are required by the epic but are NOT in `requirements.txt`:

| Package | Why needed |
|---|---|
| `djangorestframework` | DRF viewsets and serializers (Phase 2) |
| `django-allauth` | Auth flow and token exchange |
| `dj-rest-auth` | DRF-compatible allauth endpoints |
| `channels` (django-channels) | ASGI WebSocket support (acceptance criterion) |
| `daphne` | ASGI server (acceptance criterion) |
| `channels-redis` | Redis channel layer backend (acceptance criterion) |

Already installed (no action needed): `django-storages`, `django-q2`, `sendgrid`,
`google-cloud-storage`.

---

### ASGI Status

`core/asgi.py` currently uses plain Django ASGI:

```python
from django.core.asgi import get_asgi_application
application = get_asgi_application()
```

No `channels.routing.ProtocolTypeRouter` is configured. No Daphne entrypoint. The
acceptance criterion requires upgrading this to a Channels `ProtocolTypeRouter` and
adding `CHANNEL_LAYERS` pointing to a Redis instance via `REDIS_URL` env var. This is
an explicit deliverable gated on the `channels` and `daphne` packages being installed.

---

### Frontend Patterns

- Router: React Router v6 (`BrowserRouter` + `Routes` + nested `Route`)
- All page components live in `frontend/src/pages/` and are lazy-loaded via `React.lazy`
- A single `Layout` component (`frontend/src/components/layout/Layout`) wraps all routes
- Existing routes: `/` (Home), `/projects`, `/ai`, `/about`, `/contact`
- Portal routes (`/portal`, `/portal/projects/:id`, `/portal/files`, `/portal/messages`)
  do not exist yet; they must be added to `App.tsx`
- Components are organized under `frontend/src/components/`; a `catalyst-ui-kit/`
  subdirectory provides the design system primitives
- No auth-gated route wrapper exists yet; a `ProtectedRoute` component will be needed
- The Django SPA catch-all in `core/urls.py` already handles all non-API paths via
  `re_path(r'^.*$', spa_index)`, so new React routes require no backend URL changes

---

### Relevant ADRs

| ADR | Title | Constraint imposed |
|---|---|---|
| [0001](knowledge-base/content/decisions/0001-django-react-static-architecture.md) | Django + React as Static Files | React must be served as Django static files; no separate Node server; no CORS headers |
| [0002](knowledge-base/content/decisions/0002-cloud-run-worker-for-async-tasks.md) | Cloud Run worker for async tasks | Background tasks (Q2) run in a separate Cloud Run worker container; notifications use django-q2 task queue |
| [0003](knowledge-base/content/decisions/0003-client-portal-ddd-split.md) | client_portal domain-ORM split | **Directly binding:** two parallel representations are mandatory - plain Python dataclasses in `domain/` and Django ORM models in `models.py`; no business logic on ORM models; repository implementations are the only mapping code |
| [0004](knowledge-base/content/decisions/0004-blog-domain-layer-and-supabase-vectorization.md) | Blog domain layer and Supabase vectorization | Establishes `apps/blog/` as the canonical DDD reference implementation; `client_portal` must follow the same layering |

---

### django-storages Status

**Resolves Open Question #4:** `django-storages==1.14.6` is already in `requirements.txt`
and is already fully configured in `core/settings.py`. When `GS_BUCKET_NAME` is set,
the `default` storage backend routes to `storages.backends.gcloud.GoogleCloudStorage`
with `location='media'`. File upload via `services/files.py` can use
`django.core.files.storage.default_storage` directly with no additional setup.

---

## Domain Context

**Bounded context:** `client_portal`

**Key domain concepts:**

- `ClientOrganization` - the tenant unit; all data is scoped to an org
- `ClientUserProfile` - a user who belongs to exactly one `ClientOrganization`
- `Project` - a unit of work tracked within an org; has a status (active / pending
  approval / complete)
- `Milestone` - an ordered checkpoint within a `Project`
- `Deliverable` - a concrete output attached to a `Project` or `Milestone`
- `DeliverableApproval` - the approval record for a `Deliverable`; drives the approval
  state machine
- `ProjectFile` - a file asset stored in GCS and associated with a `Project`
- `ClientMessage` - a threaded message exchanged within a `Project`
- `InvoiceRecord` - a billing record for a `Project`; status can be paid / unpaid /
  overdue
- `ActivityEvent` - an immutable audit log entry recording any significant domain action

**Business rules:**

- A `ClientUserProfile` may only read and write records that belong to their own
  `ClientOrganization`. Staff users bypass this restriction and see all orgs.
- A `DeliverableApproval` follows a strict state machine: pending -> approved or
  pending -> rejected. No transition from approved or rejected back to pending without an
  explicit re-open action (to be defined by domain-modeling-orchestrator).
- Every approval state transition must produce an `ActivityEvent` entry for audit
  purposes.
- File storage uses Google Cloud Storage exclusively; no local filesystem storage is
  permitted in production.
- Invoice payment processing is out of scope for this epic; `InvoiceRecord` is read-only
  display data.

---

## Technical Context

**Stack:**

- Backend: Python 3.14, Django 6.0.5
- ASGI server: Daphne (via `channels[daphne]`) - replaces WSGI for the development server
  and production entrypoint; enables WebSocket support for future bounded contexts
- Channel layer: Redis via `channels-redis`; Redis instance hosted on the same VPS as
  the database
- API layer: Django REST Framework (DRF) - new dependency (`djangorestframework`)
- Auth: django-allauth + dj-rest-auth - new dependencies (`django-allauth`, `dj-rest-auth`)
- Storage: Google Cloud Storage via `django-storages` (already in requirements or to be
  added)
- Background tasks: Django-Q2 (already configured in the project)
- Email: SendGrid (already in project stack)
- Database: MySQL 8.x on Google Cloud SQL
- Frontend: React (Vite + TypeScript), existing `frontend/` app
- SMS/2FA: Twilio (existing)

**Existing patterns to follow:**

- App structure mirrors `apps/blog/`: `domain/`, `application/`, `infrastructure/`,
  `tests/` sub-packages within `apps/client_portal/`
- DRF serializers and viewsets live in `infrastructure/`
- Domain entities and value objects live in `domain/` with zero external imports
- Use cases and service orchestration live in `application/`
- Django ORM models live in `infrastructure/` and map to domain objects; domain layer
  must not import Django models directly
- Object-level permissions implemented via DRF's `BasePermission` subclasses in
  `infrastructure/`
- React components live in `frontend/src/components/` and pages in
  `frontend/src/pages/`

**New dependencies to add:**

- `djangorestframework`
- `django-allauth`
- `dj-rest-auth`
- `channels[daphne]` - ASGI server + WebSocket protocol support
- `channels-redis` - Redis channel layer backend

---

## Out of Scope

- Real invoice payment processing (Stripe or any payment gateway integration)
- Re-opening a previously approved or rejected `DeliverableApproval` (state machine
  extension for a future ticket)
- WebSocket consumers for `ClientMessage` real-time chat (ASGI infrastructure is in
  scope; building chat consumers is deferred to a future ticket)
- Multi-organization admin tooling beyond Django's built-in admin
- Mobile-responsive layout for the React portal (desktop-first for portfolio purposes)
- Deployment pipeline changes (handled by the deployment-orchestrator in a separate
  ticket)
- SendGrid template design (plain-text email is sufficient for this epic)
- Two-factor authentication for portal users (Twilio 2FA already exists for the main
  app; scoping to portal is a future ticket)

---

## Open Questions

1. **Re-open transition:** Should `DeliverableApproval` support a re-open transition
   (approved/rejected -> pending)? The roadmap does not define this. The
   domain-modeling-orchestrator must decide whether to model it now or defer to a future
   ticket.

2. **Auth token strategy for the portal:** The roadmap says "allauth token exchange with
   DRF" but does not specify whether to use DRF's `TokenAuthentication`, JWT (via
   SimpleJWT), or dj-rest-auth's session-based approach. The development-orchestrator
   must resolve this before implementing the auth flow.

3. **`ClientUserProfile` relation to Django's `User`:** Is `ClientUserProfile` a
   one-to-one extension of `auth.User` (like a profile model) or an independent model
   linked by a foreign key? The domain-modeling-orchestrator must decide and document
   the relationship in the aggregate design.

4. **`django-storages` status:** Is `django-storages` already in `requirements.txt` or
   does it need to be added? The development-orchestrator must verify before implementing
   `services/files.py`.

5. **Redis connection string and security hardening:** Redis is hosted on a Hostinger
   VPS (Ubuntu 22.04, CloudPanel) at IP 217.196.48.82. GAE Standard has no fixed egress
   IPs, so IP-based firewall whitelisting is not viable without a VPC Connector + Cloud
   NAT (deployment-phase concern). **Decided:** password-only auth (no IP restriction)
   is acceptable for this portfolio/demo project. Required steps before the development
   phase closes:
   - Redis `redis.conf` must set `requirepass <strong-password>` and `bind 0.0.0.0`.
   - `CHANNEL_LAYERS` in `settings.py` must use
     `redis://:password@217.196.48.82:6379/0` supplied via a `REDIS_URL` environment
     variable. The raw URL (including password) must never appear in source code or any
     committed artifact.
   - The development-orchestrator must document the Redis setup steps in the runbook.
   - IP-based restriction via VPC Connector + Cloud NAT is deferred to the deployment
     ticket as a hardening step.

5. **Seed script location:** Should the seed script live in `apps/client_portal/` as a
   management command, in `knowledge-base/scripts/`, or elsewhere? The
   development-orchestrator must decide and align with the convention established by
   earlier bounded contexts.

6. **Activity event granularity:** Which actions beyond approval state changes should
   produce an `ActivityEvent`? (e.g., file upload, message sent, invoice updated?) The
   domain-modeling-orchestrator must define the full list.


