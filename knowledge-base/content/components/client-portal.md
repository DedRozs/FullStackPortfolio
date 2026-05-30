# Component: client_portal

**Location:** `apps/client_portal/`
**Status:** Phase 1 complete - domain layer and ORM models verified
**Bounded Context:** Client Project Delivery
**Architecture Pattern:** Domain-Driven Design with split domain/infrastructure layers

---

## Responsibility

The client_portal bounded context manages the full lifecycle of consulting engagements
between Joseph Prince (staff) and client organizations. It owns the data model for
projects, milestones, deliverables, approvals, messaging, file records, invoicing, and
activity tracking.

Phase 1 delivers the domain layer (pure Python dataclasses with business rules) and the
Django ORM persistence layer (12 models with migrations). No HTTP interface exists in
Phase 1; views, URL routing, and admin registration are deferred to Phase 2.

---

## Domain Model

### Aggregate Roots

| Aggregate | Primary Identity | Status Field | Key Invariant |
|---|---|---|---|
| `ClientOrganization` | `UUID` | - | name and slug must not be blank |
| `UserProfile` | `UUID` | - | client profiles require organization_id; staff profiles must not have one |
| `Project` | `UUID` | `ProjectStatus` | status transitions enforced: DRAFT->ACTIVE->PENDING_APPROVAL->(COMPLETE|ACTIVE); ARCHIVED only from ACTIVE or COMPLETE |
| `InvoiceRecord` | `UUID` | `InvoiceStatus` | amount must be non-negative; tied to one organization |

### Entities

| Entity | Belongs To | Key Invariant |
|---|---|---|
| `Milestone` | Project aggregate | PENDING -> IN_PROGRESS requires target_date; IN_PROGRESS -> COMPLETE |
| `Deliverable` | Milestone aggregate | name must not be blank; tracks current_version_number |
| `DeliverableVersion` | Deliverable aggregate | version_number unique per deliverable |
| `Approval` | DeliverableVersion | one-to-one with DeliverableVersion; PENDING -> (APPROVED, REJECTED, REVISION_REQUESTED); rejection requires comment |
| `MessageThread` | Project aggregate | subject must not be blank |
| `Message` | MessageThread aggregate | body must not be blank |
| `FileRecord` | DeliverableVersion or Message | exactly one of deliverable_version_id or message_id must be set |
| `ActivityEvent` | Project or Organization | append-only audit log entry |

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
    models.py             - Django ORM models (12 models mirroring the domain layer)
    migrations/           - Django migration history
    apps.py
    tests.py              - 54 unit tests covering domain invariants and ORM round-trip
```

### Design Principle: Domain-ORM Split

Domain entities live in `domain/model.py` as plain Python dataclasses with no Django
dependency. Django ORM models in `models.py` mirror the domain structure but use
`models.Model` as their base class. Repository implementations (deferred to Phase 2)
are responsible for translating between the two representations.

See [ADR 0003](../decisions/0003-client-portal-ddd-split.md) for the rationale.

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
| `InvoiceRecordRepository` | (defined in repositories.py) |
| `ActivityEventRepository` | (defined in repositories.py) |

Repository implementations using the Django ORM are deferred to Phase 2.

---

## Key Design Decisions

1. **Domain-ORM split:** Domain dataclasses are pure Python; ORM models are a separate
   persistence representation. This preserves domain testability without a running
   database. See [ADR 0003](../decisions/0003-client-portal-ddd-split.md).

2. **UUIDs as primary keys:** All entities use `uuid.UUID` as the identity type in the
   domain layer and `UUIDField(primary_key=True)` in ORM models. This decouples identity
   generation from the database and allows entities to be created offline.

3. **Status as str Enum:** All status enums inherit from `(str, Enum)`, making them
   directly serializable to JSON and compatible with Django's `CharField(choices=...)`.
   Status transitions are enforced as methods on the domain entity, not in the ORM.

4. **FileRecord exclusivity invariant:** A `FileRecord` must be attached to exactly one
   of `DeliverableVersion` or `Message`. This is enforced in `__post_init__` in the
   domain layer. The ORM model uses nullable FKs; the domain layer is the enforcement
   point.

5. **Approval is one-to-one with DeliverableVersion:** One approval workflow per version.
   Concurrent approvals on the same version are prevented at the ORM level via
   `OneToOneField`.

---

## Deferred Items (Phase 2)

| Item | Impact | Reference |
|---|---|---|
| Django admin registration for all 12 models | Staff cannot manage records via /admin/ until resolved | KI-1 |
| HTTP views and URL routing | No HTTP interface in Phase 1; all interaction via shell/seed script | KI-2 |
| Django ORM repository implementations | ABCs defined; concrete implementations not yet written | Phase 2 |
| `db_index=True` on `Project.status` and `InvoiceRecord.status` | Full table scan on list_by_status queries at scale | Performance |
| `select_related()` on all list querysets in admin and views | N+1 risk on Milestone, DeliverableVersion, Approval, MessageThread, Message, InvoiceRecord `__str__` | Performance |
| Path traversal validation on `FileRecord.storage_path` | No attack surface in Phase 1 (no HTTP interface); must be enforced at application service boundary before Phase 2 write paths go live | Security (OWASP A03) |

---

## Test Coverage

- **54 unit tests** in `apps/client_portal/tests.py`
- All domain invariants (blank field checks, status transition guards, FK exclusivity,
  money validation) are covered
- ORM round-trip tests verify model creation and field persistence
- Zero issues from Django system check (`python manage.py check`)
- Test suite wall-clock duration: 0.008 s

---

## Seed Script

A seed script is available to populate the database with representative client_portal
data for development and demo purposes:

```
.venv\Scripts\python.exe knowledge-base/scripts/seed_client_portal.py
```

See [scripts/README.md](../../scripts/README.md) for full usage details.
