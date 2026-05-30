# Component: client_portal

**Location:** `apps/client_portal/`
**Status:** Complete - domain layer, REST API, React frontend, WebSocket infrastructure
**Bounded Context:** Client Project Delivery
**Architecture Pattern:** Domain-Driven Design with split domain/infrastructure layers
**Related ADRs:** [ADR 0003](../decisions/0003-client-portal-ddd-split.md), [ADR 0005](../decisions/0005-dual-authentication-rest-websocket.md), [ADR 0006](../decisions/0006-asgi-migration-channels-infrastructure.md)

---

## Responsibility

The client_portal bounded context manages the full lifecycle of consulting engagements
between Joseph Prince (staff) and client organizations. It owns the data model for
projects, milestones, deliverables, approvals, messaging, file records, invoicing, and
activity tracking.

The context spans a full DDD domain layer, a Django REST Framework API with object-level
permissions, a React frontend at `/portal/*`, Django Channels WebSocket infrastructure
backed by Redis, GCS-based file storage, and a Django Q2 background task for approval
notifications.

---

## Domain Model

### Aggregate Roots

| Aggregate | Primary Identity | Status Field | Key Invariant |
|---|---|---|---|
| `ClientOrganization` | `UUID` | - | name and slug must not be blank |
| `UserProfile` | `UUID` | - | client profiles require organization_id; staff profiles must not have one |
| `Project` | `UUID` | `ProjectStatus` | status transitions enforced: DRAFT->ACTIVE->PENDING_APPROVAL->(COMPLETE|ACTIVE); ARCHIVED only from ACTIVE or COMPLETE |
| `Approval` | `UUID` | `ApprovalStatus` | one-to-one with DeliverableVersion; rejection and revision require non-blank comment |
| `MessageThread` | `UUID` | - | subject must not be blank |
| `InvoiceRecord` | `UUID` | `InvoiceStatus` | amount must be non-negative; tied to one organization |

### Entities (non-root)

| Entity | Belongs To | Key Invariant |
|---|---|---|
| `Milestone` | Project | PENDING -> IN_PROGRESS requires target_date; IN_PROGRESS -> COMPLETE |
| `Deliverable` | Milestone | name must not be blank; tracks current_version_number |
| `DeliverableVersion` | Deliverable | version_number unique per deliverable; version_number >= 1 |
| `Message` | MessageThread | body must not be blank |
| `FileRecord` | DeliverableVersion or Message | exactly one of deliverable_version_id or message_id must be set |
| `ActivityEvent` | Project or Organization | append-only audit log; actor nullable (system-initiated events allowed) |

### Value Objects

| Value Object | Type | Key Invariant |
|---|---|---|
| `ProjectStatus` | `str, Enum` | DRAFT, ACTIVE, PENDING_APPROVAL, COMPLETE, ARCHIVED |
| `MilestoneStatus` | `str, Enum` | PENDING, IN_PROGRESS, COMPLETE |
| `ApprovalStatus` | `str, Enum` | PENDING, APPROVED, REJECTED, REVISION_REQUESTED |
| `InvoiceStatus` | `str, Enum` | DRAFT, SENT, PAID, OVERDUE, CANCELLED |
| `StakeholderRole` | `str, Enum` | CLIENT, STAFF, ADMIN |
| `Money` | frozen dataclass | amount >= 0; currency is a 3-letter ISO 4217 code |
| `FileMetadata` | frozen dataclass | content_type and storage_key not blank; size_bytes > 0 |
| `VersionNumber` | frozen dataclass | value >= 1 |

### Aggregate Boundaries

```
ClientOrganization (root)
  owns --> UserProfile (membership)
  owns --> Project (root)
             owns --> Milestone
                        owns --> Deliverable
                                   owns --> DeliverableVersion
                                              has one --> Approval (root)
                                              has many --> FileRecord
             owns --> MessageThread (root)
                        owns --> Message
                                   has many --> FileRecord
             owns --> ActivityEvent (audit log)
  owns --> InvoiceRecord (root)
```

---

## Key Business Rules

### Organization Isolation

Every API read path (all 12 viewsets) checks `request.user.is_staff`. Staff users see all
records. Client users are filtered to their `organization_id` via `get_queryset` on each
viewset. Object-level permission `IsStaffOrClientOfOrganization.has_object_permission`
traverses the FK chain (e.g. `message -> thread -> project -> organization_id`) to enforce
isolation at write time. Unauthenticated requests are rejected at `has_permission`.

### Approval State Machine

```
PENDING -> APPROVED         (GrantApproval, reviewer only, comment optional)
PENDING -> REJECTED         (RejectApproval, reviewer only, non-blank comment required)
PENDING -> REVISION_REQUESTED (RequestRevision, reviewer only, non-blank comment required)
```

Only the `reviewer_id` set at approval creation may call grant/reject/request-revision.
Attempting to decide as a different user raises `ValueError`.

### Project Status State Machine

```
DRAFT -> ACTIVE              (ActivateProject)
ACTIVE -> PENDING_APPROVAL   (SubmitProjectForApproval)
PENDING_APPROVAL -> ACTIVE   (RejectProject - returns to active)
PENDING_APPROVAL -> COMPLETE (ApproveProject)
ACTIVE | COMPLETE -> ARCHIVED (archive)
```

### Audit Trail

Every state-changing use case calls `_record_activity`, which creates an immutable
`ActivityEvent` with `event_type`, `actor_id` (nullable for system events),
`project_id`, `organization_id`, and a JSON `payload`. The activity endpoint at
`GET /api/portal/activity/` surfaces the append-only feed to the React UI.

---

## Layer Structure

```
apps/client_portal/
    domain/
        __init__.py
        model.py          - Entity and aggregate dataclasses; all business rules
        value_objects.py  - Enums and frozen dataclasses (Money, FileMetadata, VersionNumber)
        events.py         - Domain event definitions
        repositories.py   - Abstract repository interfaces (ABCs); 12 interfaces total
    application/
        __init__.py
        dtos.py           - Command and DTO dataclasses (no Django imports)
        ports.py          - FileStoragePort ABC
        use_cases.py      - 19 use case classes (one class per operation)
    infrastructure/
        __init__.py
        permissions.py    - IsStaffOrClientOfOrganization, IsClientOfOrganization, IsApprover
        repositories.py   - DjangoXxxRepository implementations (12 concrete classes)
        serializers.py    - DRF ModelSerializer classes (12)
        storage.py        - GCSFileStorageAdapter implementing FileStoragePort
        viewsets.py       - 12 DRF ModelViewSet classes with custom actions
    models.py             - Django ORM models (12 models mirroring the domain layer)
    api_urls.py           - DRF DefaultRouter; 12 registered endpoints
    tasks.py              - Django Q2 background task: approval notification email
    apps.py
    migrations/           - Django migration history
```

---

## Application Layer Use Cases

| Use Case Class | Command/Query | Activity Event Emitted |
|---|---|---|
| `RegisterClientOrganization` | `RegisterClientOrganizationCommand` | `ClientOrganizationRegistered` |
| `CreateUserProfile` | `CreateUserProfileCommand` | - |
| `CreateProject` | `CreateProjectCommand` | `ProjectCreated` |
| `ActivateProject` | `ActivateProjectCommand` | `ProjectActivated` |
| `SubmitProjectForApproval` | `SubmitProjectForApprovalCommand` | `ProjectSubmittedForApproval` |
| `ApproveProject` | `ApproveProjectCommand` | `ProjectCompleted` |
| `RejectProject` | `RejectProjectCommand` | `ProjectReturnedToActive` |
| `CreateMilestone` | `CreateMilestoneCommand` | - |
| `CompleteMilestone` | `CompleteMilestoneCommand` | `MilestoneCompleted` |
| `AddDeliverableVersion` | `AddDeliverableVersionCommand` | `DeliverableRevisionSubmitted` |
| `RequestApproval` | `RequestApprovalCommand` | `ApprovalRequested` |
| `GrantApproval` | `GrantApprovalCommand` | `DeliverableApproved` |
| `RejectApproval` | `RejectApprovalCommand` | `DeliverableRejected` |
| `RequestRevision` | `RequestRevisionCommand` | `DeliverableRevisionRequested` |
| `UploadFile` | `UploadFileCommand` | `FileRecordUploaded` |
| `ListFilesForDeliverable` | `ListFilesForDeliverableQuery` | - |
| `SendMessage` | `SendMessageCommand` | `MessageSent` |
| `ListMessages` | `ListMessagesQuery` | - |
| `ListInvoices` | `ListInvoicesQuery` | - |
| `ListActivityEvents` | `ListActivityEventsQuery` | - |

---

## API Endpoints

**Base URL:** `/api/portal/`
**Authentication:** `Authorization: Token <token>` (DRF TokenAuthentication)
**Permissions:** `IsStaffOrClientOfOrganization` on all viewsets

| Resource | Standard CRUD | Custom Actions |
|---|---|---|
| `organizations/` | list, create, retrieve, update, destroy | - |
| `profiles/` | list, create, retrieve, update, destroy | - |
| `projects/` | list, create, retrieve, update, destroy | `POST .../submit-for-approval/` |
| `milestones/` | list, create, retrieve, update, destroy | - |
| `deliverables/` | list, create, retrieve, update, destroy | - |
| `deliverable-versions/` | list, create, retrieve, update, destroy | - |
| `approvals/` | list, create, retrieve, update, destroy | `POST .../grant/`, `POST .../reject/`, `POST .../request-revision/` |
| `threads/` | list, create, retrieve, update, destroy | - |
| `messages/` | list, create, retrieve, update, destroy | `POST messages/send/` |
| `files/` | list, create, retrieve, update, destroy | - |
| `invoices/` | list, create, retrieve, update, destroy | - |
| `activity/` | list, retrieve | - |

All endpoints return DRF browsable API pages when accessed with `Accept: text/html`.

---

## Authentication Strategy

The portal uses two authentication mechanisms on two transports. See
[ADR 0005](../decisions/0005-dual-authentication-rest-websocket.md).

**REST API (HTTP):** DRF `TokenAuthentication`.
1. Client posts credentials to `POST /api/auth/login/` (django-allauth token endpoint).
2. Server returns a DRF token in the response body.
3. Client stores the token in `localStorage` under the key `auth_token`.
4. All subsequent REST requests include the header `Authorization: Token <token>`.

**WebSocket:** Django Channels `AuthMiddlewareStack` + `SessionAuthentication`.
- WebSocket handshakes carry the session cookie, which is validated by
  `AuthMiddlewareStack` before the connection is accepted.
- `AllowedHostsOriginValidator` wraps the WebSocket router to block cross-origin
  connection attempts.

**Known limitation:** Token in `localStorage` is accessible to JavaScript (XSS surface).
CSP headers at the GAE layer are the primary mitigation. HttpOnly cookie upgrade is
tracked as a future hardening task.

---

## File Storage

**Port:** `apps/client_portal/application/ports.py::FileStoragePort` (ABC)
**Adapter:** `apps/client_portal/infrastructure/storage.py::GCSFileStorageAdapter`

The `UploadFile` use case calls `FileStoragePort.upload(file_data, filename, content_type)`
and receives a `storage_path` string. The storage key is prefixed with `uuid4().hex` to
prevent path traversal and collisions. The adapter delegates to `django.core.files.storage`
configured with `django-storages` Google Cloud Storage backend.

Required settings: `GS_BUCKET_NAME`, `GOOGLE_APPLICATION_CREDENTIALS`.

---

## WebSocket Infrastructure

See [ADR 0006](../decisions/0006-asgi-migration-channels-infrastructure.md).

- **Entry point:** `core/asgi.py` exposes a `ProtocolTypeRouter` routing HTTP to the
  standard Django ASGI app and WebSocket connections to `AuthMiddlewareStack(URLRouter(...))`.
- **Channel layer:** `channels_redis.core.RedisChannelLayer` configured via `REDIS_URL`
  env var. Falls back to `InMemoryChannelLayer` when `REDIS_URL` is absent.
- **WebSocket consumers:** `websocket_urlpatterns` is currently empty (infrastructure
  is live; specific consumer implementations are deferred to the workflow_automation epic).
- **Development server:** Run with Daphne - `daphne -b 0.0.0.0 -p 8000 core.asgi:application`.
  Do not use `manage.py runserver` for WebSocket testing.

---

## Background Tasks

**Runner:** Django Q2 (`django-q2`) broker: MySQL (same database as application)
**Worker entry point:** `Dockerfile.worker` runs `manage.py qcluster`

| Task | Module | Trigger |
|---|---|---|
| Approval notification email | `apps/client_portal/tasks.py` | Queued by `GrantApproval`, `RejectApproval`, `RequestRevision` use cases on state change |

The email is sent via SendGrid using the `SENDGRID_API_KEY` environment variable (or
Django `EMAIL_*` settings as fallback). The task is a Q2 async task dispatched with
`django_q.tasks.async_task()`.

---

## Repository Interfaces

Twelve abstract repository classes are defined in `domain/repositories.py`:

| Interface | Key Query Methods |
|---|---|
| `ClientOrganizationRepository` | `get_by_id`, `get_by_slug`, `save`, `list_all` |
| `UserProfileRepository` | `get_by_id`, `get_by_user_id`, `save`, `list_stakeholders_for_organization` |
| `ProjectRepository` | `get_by_id`, `save`, `list_by_organization`, `list_by_status` |
| `MilestoneRepository` | `get_by_id`, `save`, `list_by_project` |
| `DeliverableRepository` | `get_by_id`, `save`, `list_by_milestone` |
| `DeliverableVersionRepository` | `get_by_id`, `save`, `list_by_deliverable` |
| `ApprovalRepository` | `get_by_id`, `get_by_deliverable_version`, `save` |
| `FileRecordRepository` | `get_by_id`, `save`, `list_by_deliverable_version`, `list_by_message` |
| `MessageThreadRepository` | `get_by_id`, `save`, `list_by_project` |
| `MessageRepository` | `get_by_id`, `save` |
| `InvoiceRecordRepository` | `get_by_id`, `save`, `list_by_organization` |
| `ActivityEventRepository` | `save`, `list_by_project`, `list_by_organization` |

---

## Key Design Decisions

1. **Domain-ORM split:** Domain dataclasses are pure Python; ORM models are a separate
   persistence representation. See [ADR 0003](../decisions/0003-client-portal-ddd-split.md).

2. **UUIDs as primary keys:** All entities use `uuid.UUID` in the domain layer and
   `UUIDField(primary_key=True)` in ORM models. Identity generation is decoupled from
   the database.

3. **Status as str Enum:** All status enums inherit from `(str, Enum)`, making them
   directly serializable to JSON and compatible with Django `CharField(choices=...)`.

4. **FileRecord exclusivity invariant:** A `FileRecord` must be attached to exactly one
   of `DeliverableVersion` or `Message`. Enforced in `__post_init__` in the domain layer.

5. **Approval is one-to-one with DeliverableVersion:** One approval workflow per version.
   Concurrent approvals on the same version are prevented via `OneToOneField`.

6. **ActivityEvent.actor is nullable:** System-initiated events (e.g.
   `ClientOrganizationRegistered` triggered from a seed script) have no human actor.
   Made nullable in migration `0002_make_activityevent_actor_nullable`.

---

## Test Coverage

- **66 unit tests** across domain invariants, use case logic, viewset permissions, and
  ORM round-trip verification
- All domain invariants, status transition guards, FK exclusivity, and money validation
  are covered
- All 5 OWASP Top 10 findings resolved (see QA sign-off artifact)
- Test suite wall-clock duration: < 1 s

---

## Seed Script

A seed script populates the database with representative data for development and demo:

```
.venv\Scripts\python.exe knowledge-base/scripts/seed_client_portal.py
```

Creates: 2 demo organizations, 3 projects (active, pending approval, complete),
milestones and deliverables, 1 overdue invoice, sample activity events.

See [scripts/README.md](../../scripts/README.md) for full usage details and the
[developer runbook](../development/client-portal-runbook.md) for local setup steps.

