# Domain Modeling to Development Artifact

<!-- This template is produced by the Domain Modeling Orchestrator and consumed by the
     Development Orchestrator. Complete every section before handoff. This document is
     the implementation specification: development agents must not begin coding until
     this artifact is approved. Validate against:
     contracts/schemas/domain-modeling-to-development.schema.json -->

**Schema version:** 1.0
**Project name:** FullStackPortfolio
**Ticket:** FSP-1
**Produced by:** `.github/agents/domain-modeling-orchestrator.agent.md`
**Consumed by:** `.github/agents/development-orchestrator.agent.md`

---

## Schema Version

`1.0`

---

## Project Name

FullStackPortfolio

---

## Ubiquitous Language

Finalized domain vocabulary. All development agents use these terms verbatim as code identifiers. No synonyms, abbreviations, or technical substitutes are permitted.

| Term | Definition | Bounded Context | Usage Examples |
|---|---|---|---|
| `ClientOrganization` | The named client company or individual entity that commissions Projects. Root of the portal organizational hierarchy; all Projects, InvoiceRecords, and Stakeholder memberships belong to a ClientOrganization. | client_portal | `class ClientOrganization`, `ClientOrganization.objects.get(slug=slug)`, `class ClientOrganizationRepository(ABC)` |
| `UserProfile` | A portal participant - either a staff member or a client Stakeholder - identified by email address. Wraps Django's built-in User to carry portal-specific attributes such as `is_client` and `organization`. | client_portal | `class UserProfile`, `UserProfile.user_id`, `def get_profile(user_id: int) -> UserProfile` |
| `Stakeholder` | A UserProfile whose `is_client` attribute is `True`, representing a member of the client team who reviews Deliverables and authorizes Approvals. Semantically distinct from a staff UserProfile. Not a separate model - a role classification on UserProfile. | client_portal | `stakeholder: UserProfile`, `def notify_stakeholders(project: Project) -> None`, `if user_profile.is_client` |
| `Project` | A scoped, time-bounded body of work commissioned by a ClientOrganization. Progresses through states defined by `ProjectStatus`. Contains Milestones, Messages, and InvoiceRecords. | client_portal | `class Project`, `project.status`, `class ProjectRepository(ABC)`, `Project.objects.filter(status=ProjectStatus.ACTIVE)` |
| `ProjectStatus` | Enumeration of valid Project lifecycle states. Values: `ACTIVE` (work in progress), `PENDING_APPROVAL` (awaiting Stakeholder sign-off), `COMPLETE` (all Deliverables approved and closed). | client_portal | `class ProjectStatus(str, Enum)`, `project.status == ProjectStatus.COMPLETE`, `ProjectStatus.PENDING_APPROVAL` |
| `Milestone` | A named checkpoint within a Project with a target completion date. Groups related Deliverables into reviewable phases. Progresses through states defined by `MilestoneStatus`. | client_portal | `class Milestone`, `milestone.target_date`, `milestone.project_id`, `Milestone.objects.filter(project=project)` |
| `MilestoneStatus` | Enumeration of valid Milestone completion states. Values: `PENDING` (not yet started), `IN_PROGRESS` (work underway), `COMPLETE` (all Deliverables in the Milestone approved). | client_portal | `class MilestoneStatus(str, Enum)`, `milestone.status == MilestoneStatus.COMPLETE`, `MilestoneStatus.IN_PROGRESS` |
| `Deliverable` | A concrete work product produced within a Milestone, submitted for Stakeholder review and formal Approval. Versioned through `DeliverableVersion` records each time a revision is submitted. | client_portal | `class Deliverable`, `deliverable.milestone_id`, `class DeliverableService`, `Deliverable.objects.filter(milestone=milestone)` |
| `DeliverableVersion` | An immutable, versioned snapshot of a Deliverable's content created each time a new revision is submitted for review. Preserves the full review history of a Deliverable. `version_number` is a monotonically increasing integer per Deliverable. | client_portal | `class DeliverableVersion`, `DeliverableVersion.version_number`, `class DeliverableVersionRepository(ABC)`, `DeliverableVersion.objects.filter(deliverable=deliverable)` |
| `Approval` | A formal, immutable decision record created when a Stakeholder accepts or rejects a specific DeliverableVersion. Carries `ApprovalStatus` and an optional reviewer comment. | client_portal | `class Approval`, `Approval.status`, `approval.reviewer_id`, `class ApprovalStatus(str, Enum)` |
| `ApprovalStatus` | Enumeration of valid Approval decision states. Values: `PENDING` (awaiting Stakeholder action), `APPROVED` (Stakeholder accepted the Deliverable), `REJECTED` (Stakeholder rejected; revision required), `REVISION_REQUESTED` (Stakeholder requests specific changes before re-review). | client_portal | `class ApprovalStatus(str, Enum)`, `approval.status == ApprovalStatus.APPROVED`, `ApprovalStatus.REVISION_REQUESTED` |
| `FileRecord` | Metadata describing a file asset attached to a Deliverable or Message. Stores filename, storage path, MIME type, and file size. Does not contain binary data; binary data resides in object storage. | client_portal | `class FileRecord`, `FileRecord.storage_path`, `FileRecord.mime_type`, `class FileRecordModel` |
| `MessageThread` | A named, ordered channel within a Project that groups related Messages by topic or Milestone. Provides context for asynchronous communication between portal participants. | client_portal | `class MessageThread`, `MessageThread.project_id`, `MessageThread.subject`, `class MessageThreadModel` |
| `Message` | A single communication from a portal participant addressed to a MessageThread within a Project. Contains the message body, sender reference, and creation timestamp. Messages are append-only; no editing or deletion. | client_portal | `class Message`, `Message.thread_id`, `Message.sender_id`, `class MessageRepository(ABC)` |
| `InvoiceRecord` | A billing document issued to a ClientOrganization itemizing charges for Project work. Tracks payment lifecycle via `InvoiceStatus`. Carries `due_date`, `amount`, and line items. | client_portal | `class InvoiceRecord`, `InvoiceRecord.due_date`, `InvoiceRecord.amount`, `class InvoiceStatus(str, Enum)` |
| `InvoiceStatus` | Enumeration of valid InvoiceRecord payment states. Values: `DRAFT` (not yet sent), `SENT` (delivered to client), `PAID` (payment confirmed), `OVERDUE` (past due date without payment). | client_portal | `class InvoiceStatus(str, Enum)`, `invoice.status == InvoiceStatus.OVERDUE`, `InvoiceStatus.PAID` |
| `ActivityEvent` | An immutable, append-only log entry capturing a significant domain action within the portal (for example: project status change, approval decision, file upload, invoice issued). Event type is expressed in past tense per DDD convention. Never updated or deleted after creation. | client_portal | `class ActivityEvent`, `ActivityEvent.event_type`, `class ActivityEventRepository(ABC)`, `ActivityEvent.objects.filter(project=project).order_by('occurred_at')` |
| `Portal` | The bounded context itself - the secure, role-gated web application through which ClientOrganization Stakeholders collaborate with the service provider on Projects. Used as the Django app label and Python package name. | client_portal | `apps.client_portal` (Django app label), `from apps.client_portal.domain.model import Project` |

---

## Entities

### ClientOrganization

- **Bounded Context:** client_portal
- **Identity:** UUID
- **Invariants:**
  - `name` must not be blank.
  - `slug` must be non-empty, URL-safe (alphanumeric and hyphens only), and unique across all ClientOrganization records.
  - A ClientOrganization may not be the target of an InvoiceRecord unless it has at least one Stakeholder (UserProfile with `is_client=True`).
  - `created_at` is set once at construction and is immutable.
- **State Transitions:** none

- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identity, assigned at construction via `uuid4()`. |
  | `name` | `str` | Human-readable display name of the client company or individual. |
  | `slug` | `str` | URL-safe identifier used in portal routes; unique per portal instance. |
  | `created_at` | `datetime` | UTC timestamp set at construction; immutable thereafter. |

---

### UserProfile

- **Bounded Context:** client_portal
- **Identity:** UUID
- **Invariants:**
  - `email` must be a non-empty, syntactically valid email address.
  - `user_id` must uniquely reference a Django User; no two UserProfiles may share the same `user_id`.
  - If `is_client` is `True`, `organization_id` must not be null - a Stakeholder must belong to a ClientOrganization.
  - A staff UserProfile (`is_client=False`) must have `organization_id` set to null - staff are not members of a ClientOrganization.
- **State Transitions:** none

- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identity, assigned at construction via `uuid4()`. |
  | `user_id` | `int` | Foreign key to Django's built-in User; one-to-one. |
  | `email` | `str` | Contact email address; mirrors `User.email`. |
  | `is_client` | `bool` | `True` if this UserProfile is a Stakeholder; `False` for staff. |
  | `organization_id` | `UUID \| None` | References the ClientOrganization this Stakeholder belongs to; null for staff. |
  | `created_at` | `datetime` | UTC timestamp set at construction; immutable thereafter. |

---

### Project

- **Bounded Context:** client_portal
- **Identity:** UUID
- **Invariants:**
  - `name` must not be blank.
  - `organization_id` must reference an existing ClientOrganization and is immutable after creation.
  - `status` must follow valid ProjectStatus transitions; direct field mutation from outside the entity is prohibited.
  - `target_date`, when set, must be a date in the future relative to `created_at`.
- **State Transitions:**

  | From | To | Trigger | Guard |
  |---|---|---|---|
  | `ACTIVE` | `PENDING_APPROVAL` | `submit_for_approval()` | Project has at least one Milestone with at least one Deliverable. |
  | `PENDING_APPROVAL` | `ACTIVE` | `return_to_active()` | At least one Approval on the current review cycle is `REJECTED` or `REVISION_REQUESTED`. |
  | `PENDING_APPROVAL` | `COMPLETE` | `mark_complete()` | All Deliverables across all Milestones have an `APPROVED` Approval on their current DeliverableVersion. |

- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identity, assigned at construction via `uuid4()`. |
  | `name` | `str` | Human-readable Project name. |
  | `organization_id` | `UUID` | References the ClientOrganization that commissioned this Project; immutable. |
  | `status` | `ProjectStatus` | Current lifecycle state; defaults to `ACTIVE` at construction. |
  | `description` | `str \| None` | Optional narrative description of the Project scope. |
  | `target_date` | `date \| None` | Expected completion date; null if not yet scheduled. |
  | `created_at` | `datetime` | UTC timestamp set at construction; immutable thereafter. |

---

### Milestone

- **Bounded Context:** client_portal
- **Identity:** UUID
- **Invariants:**
  - `name` must not be blank.
  - `project_id` must reference an existing Project and is immutable after creation.
  - `target_date` must be set before the Milestone can transition to `IN_PROGRESS`.
  - `status` must follow valid MilestoneStatus transitions; direct field mutation from outside the entity is prohibited.
- **State Transitions:**

  | From | To | Trigger | Guard |
  |---|---|---|---|
  | `PENDING` | `IN_PROGRESS` | `begin()` | Parent Project `status` is `ACTIVE`; `target_date` is not null. |
  | `IN_PROGRESS` | `COMPLETE` | `complete()` | All Deliverables within this Milestone have an `APPROVED` Approval on their current DeliverableVersion. |

- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identity, assigned at construction via `uuid4()`. |
  | `name` | `str` | Human-readable checkpoint name. |
  | `project_id` | `UUID` | References the parent Project; immutable. |
  | `status` | `MilestoneStatus` | Current completion state; defaults to `PENDING` at construction. |
  | `target_date` | `date \| None` | Expected completion date for this checkpoint. |
  | `created_at` | `datetime` | UTC timestamp set at construction; immutable thereafter. |

---

### Deliverable

- **Bounded Context:** client_portal
- **Identity:** UUID
- **Invariants:**
  - `name` must not be blank.
  - `milestone_id` must reference an existing Milestone and is immutable after creation.
  - `current_version_number` must be a positive integer; it increments monotonically with each call to `submit_revision()` and never decrements.
  - A new revision must not be submitted while the current DeliverableVersion has a `PENDING` Approval - the reviewer must first reach a decision.
- **State Transitions:** none (lifecycle state is expressed through the `ApprovalStatus` of the Approval on the current DeliverableVersion; no separate status field on Deliverable)

- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identity, assigned at construction via `uuid4()`. |
  | `name` | `str` | Human-readable name of the work product. |
  | `milestone_id` | `UUID` | References the parent Milestone; immutable. |
  | `description` | `str \| None` | Optional narrative description of the deliverable content. |
  | `current_version_number` | `int` | Monotonically increasing version counter; starts at `1` on first submission. Initialized to `0` before the first `submit_revision()` call. |
  | `created_at` | `datetime` | UTC timestamp set at construction; immutable thereafter. |

---

### Approval

- **Bounded Context:** client_portal
- **Identity:** UUID
- **Invariants:**
  - `deliverable_version_id` must be set at construction and is immutable; an Approval is permanently bound to one DeliverableVersion.
  - `reviewer_id` must reference a UserProfile with `is_client=True` (a Stakeholder); staff members may not create Approvals.
  - At most one Approval may exist per DeliverableVersion; a second Approval for the same version is a domain violation.
  - `status` is immutable once it reaches `APPROVED`, `REJECTED`, or `REVISION_REQUESTED`; no further transitions are permitted.
- **State Transitions:**

  | From | To | Trigger | Guard |
  |---|---|---|---|
  | `PENDING` | `APPROVED` | `approve(comment: str \| None)` | Caller is a Stakeholder (`reviewer_id` references a UserProfile with `is_client=True`). |
  | `PENDING` | `REJECTED` | `reject(comment: str)` | `comment` must not be blank; caller is a Stakeholder. |
  | `PENDING` | `REVISION_REQUESTED` | `request_revision(comment: str)` | `comment` must not be blank; caller is a Stakeholder. |

- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identity, assigned at construction via `uuid4()`. |
  | `deliverable_version_id` | `UUID` | References the specific DeliverableVersion under review; immutable. |
  | `reviewer_id` | `UUID` | References the Stakeholder UserProfile who owns this Approval. |
  | `status` | `ApprovalStatus` | Current decision state; defaults to `PENDING` at construction. |
  | `comment` | `str \| None` | Reviewer's rationale; required when status is `REJECTED` or `REVISION_REQUESTED`. |
  | `decided_at` | `datetime \| None` | UTC timestamp when a terminal decision was recorded; null while `PENDING`. |
  | `created_at` | `datetime` | UTC timestamp set at construction; immutable thereafter. |

---

### FileRecord

- **Bounded Context:** client_portal
- **Identity:** UUID
- **Invariants:**
  - `filename` must not be blank.
  - `storage_path` must not be blank; it is set at construction and is immutable (the record is invalidated rather than mutated when a file is replaced).
  - `file_size_bytes` must be a positive integer.
  - `mime_type` must not be blank.
  - Exactly one of `deliverable_version_id` or `message_id` must be set; a FileRecord cannot be simultaneously attached to both, nor detached from both.
- **State Transitions:** none

- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identity, assigned at construction via `uuid4()`. |
  | `filename` | `str` | Original filename as provided by the uploader. |
  | `storage_path` | `str` | Absolute path or object-storage key where the binary resides; immutable. |
  | `mime_type` | `str` | MIME type of the file (e.g., `application/pdf`, `image/png`). |
  | `file_size_bytes` | `int` | Size of the stored binary in bytes; must be positive. |
  | `deliverable_version_id` | `UUID \| None` | References the DeliverableVersion this file is attached to; mutually exclusive with `message_id`. |
  | `message_id` | `UUID \| None` | References the Message this file is attached to; mutually exclusive with `deliverable_version_id`. |
  | `uploaded_by_id` | `UUID` | References the UserProfile who uploaded this file. |
  | `created_at` | `datetime` | UTC timestamp set at construction; immutable thereafter. |

---

### Message

- **Bounded Context:** client_portal
- **Identity:** UUID
- **Invariants:**
  - `body` must not be blank.
  - `thread_id` must reference an existing MessageThread and is immutable after creation.
  - `sender_id` must reference an existing UserProfile and is immutable after creation.
  - A Message is append-only and immutable after creation; no editing or deletion is permitted.
- **State Transitions:** none (Messages are append-only; no lifecycle states)

- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identity, assigned at construction via `uuid4()`. |
  | `thread_id` | `UUID` | References the MessageThread this Message belongs to; immutable. |
  | `sender_id` | `UUID` | References the UserProfile who authored this Message; immutable. |
  | `body` | `str` | Full text content of the Message; must not be blank. |
  | `created_at` | `datetime` | UTC timestamp set at construction; immutable thereafter. |

---

### InvoiceRecord

- **Bounded Context:** client_portal
- **Identity:** UUID
- **Invariants:**
  - `amount` must be a positive `Decimal` value; zero and negative amounts are prohibited.
  - `organization_id` must reference an existing ClientOrganization and is immutable after creation.
  - `due_date` must be set before the InvoiceRecord can transition out of `DRAFT`.
  - `status` may not transition from `PAID` or `OVERDUE` to any other state; both are terminal.
- **State Transitions:**

  | From | To | Trigger | Guard |
  |---|---|---|---|
  | `DRAFT` | `SENT` | `send()` | `amount` is positive; `due_date` is not null. |
  | `SENT` | `PAID` | `mark_paid()` | None beyond valid current status. |
  | `SENT` | `OVERDUE` | `mark_overdue()` | Current date is strictly after `due_date`. |

- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identity, assigned at construction via `uuid4()`. |
  | `organization_id` | `UUID` | References the ClientOrganization being billed; immutable. |
  | `project_id` | `UUID \| None` | References the Project this invoice relates to; optional. |
  | `status` | `InvoiceStatus` | Current payment lifecycle state; defaults to `DRAFT` at construction. |
  | `amount` | `Decimal` | Total billed amount; must be positive. Use `Decimal`, not `float`. |
  | `due_date` | `date \| None` | Date by which payment is expected; null in `DRAFT` state until explicitly set. |
  | `issued_at` | `datetime \| None` | UTC timestamp when the invoice was sent; null while in `DRAFT`. |
  | `created_at` | `datetime` | UTC timestamp set at construction; immutable thereafter. |

---

### ActivityEvent

- **Bounded Context:** client_portal
- **Identity:** UUID
- **Invariants:**
  - `event_type` must not be blank and must be expressed in past tense per DDD naming convention (e.g., `ProjectStatusChanged`, `ApprovalDecisionRecorded`, `InvoiceIssued`).
  - `occurred_at` is set at construction to the current UTC time and is immutable thereafter.
  - `actor_id` must reference an existing UserProfile.
  - An ActivityEvent is immutable after creation; it is never updated or deleted.
- **State Transitions:** none (ActivityEvent is an immutable, append-only log entry)

- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identity, assigned at construction via `uuid4()`. |
  | `event_type` | `str` | Past-tense name of the domain action recorded (e.g., `ProjectStatusChanged`). |
  | `actor_id` | `UUID` | References the UserProfile whose action triggered this event. |
  | `project_id` | `UUID \| None` | References the Project this event relates to; null for organization-level events. |
  | `organization_id` | `UUID \| None` | References the ClientOrganization this event relates to; null for project-scoped events. |
  | `payload` | `dict` | Structured key-value data capturing the event details (e.g., previous and new status values). |
  | `occurred_at` | `datetime` | UTC timestamp set at construction; immutable thereafter. |

---

## Value Objects

### Money

- **Bounded Context:** client_portal
- **Properties:**

  | Name | Type |
  |---|---|
  | `amount` | `Decimal` |
  | `currency` | `str` |

- **Validation Rules:**
  - `amount` must be >= 0
  - `currency` must be a 3-letter alphabetic ISO 4217 code (e.g., `USD`, `EUR`, `GBP`)

- **Equality Basis:** All properties (`amount` and `currency`)

---

### ProjectStatus

- **Bounded Context:** client_portal
- **Type:** `str` enum (`class ProjectStatus(str, Enum)`)
- **Members:**

  | Member | Meaning |
  |---|---|
  | `DRAFT` | Project created but not yet activated |
  | `ACTIVE` | Work is in progress |
  | `PENDING_APPROVAL` | Awaiting Stakeholder sign-off on all Deliverables |
  | `COMPLETE` | All Deliverables approved and Project closed |
  | `ARCHIVED` | Project preserved for historical reference; no further action |

- **Validation Rules:**
  - Value must be one of the defined members; enforced by Python enum assignment

- **Equality Basis:** By value (enum member identity)

---

### MilestoneStatus

- **Bounded Context:** client_portal
- **Type:** `str` enum (`class MilestoneStatus(str, Enum)`)
- **Members:**

  | Member | Meaning |
  |---|---|
  | `PENDING` | Milestone not yet started |
  | `IN_PROGRESS` | Work on this checkpoint is underway |
  | `COMPLETE` | All Deliverables in this Milestone are approved |

- **Validation Rules:**
  - Value must be one of the defined members; enforced by Python enum assignment

- **Equality Basis:** By value (enum member identity)

---

### ApprovalStatus

- **Bounded Context:** client_portal
- **Type:** `str` enum (`class ApprovalStatus(str, Enum)`)
- **Members:**

  | Member | Meaning |
  |---|---|
  | `PENDING` | Awaiting Stakeholder action |
  | `APPROVED` | Stakeholder accepted the Deliverable |
  | `REJECTED` | Stakeholder rejected; revision required |
  | `REVISION_REQUESTED` | Stakeholder requests specific changes before re-review |

- **Validation Rules:**
  - Value must be one of the defined members; enforced by Python enum assignment

- **Equality Basis:** By value (enum member identity)

---

### InvoiceStatus

- **Bounded Context:** client_portal
- **Type:** `str` enum (`class InvoiceStatus(str, Enum)`)
- **Members:**

  | Member | Meaning |
  |---|---|
  | `DRAFT` | Invoice created but not yet sent to the client |
  | `SENT` | Invoice delivered to the ClientOrganization |
  | `PAID` | Payment confirmed |
  | `OVERDUE` | Past due date without payment |
  | `CANCELLED` | Invoice voided; no payment expected |

- **Validation Rules:**
  - Value must be one of the defined members; enforced by Python enum assignment

- **Equality Basis:** By value (enum member identity)

---

### StakeholderRole

- **Bounded Context:** client_portal
- **Type:** `str` enum (`class StakeholderRole(str, Enum)`)
- **Members:**

  | Member | Meaning |
  |---|---|
  | `CLIENT` | A Stakeholder representing the client organization |
  | `STAFF` | A portal participant representing the service provider |
  | `ADMIN` | A portal participant with administrative privileges |

- **Validation Rules:**
  - Value must be one of the defined members; enforced by Python enum assignment

- **Equality Basis:** By value (enum member identity)

---

### FileMetadata

- **Bounded Context:** client_portal
- **Properties:**

  | Name | Type |
  |---|---|
  | `content_type` | `str` |
  | `size_bytes` | `int` |
  | `storage_key` | `str` |

- **Validation Rules:**
  - `content_type` must not be blank
  - `size_bytes` must be a positive integer (> 0)
  - `storage_key` must not be blank

- **Equality Basis:** All properties (`content_type`, `size_bytes`, and `storage_key`)

- **Note:** Shared value object - embeddable in `FileRecord` and any entity that references a stored binary asset within this bounded context.

---

### VersionNumber

- **Bounded Context:** client_portal
- **Properties:**

  | Name | Type |
  |---|---|
  | `value` | `int` |

- **Validation Rules:**
  - `value` must be a positive integer (>= 1); zero and negative values are prohibited

- **Equality Basis:** All properties (`value`)

- **Note:** Shared value object - used by `Deliverable.current_version_number` and `DeliverableVersion.version_number` within the same bounded context.

---

## Aggregates

### ClientOrganizationAggregate

- **Root:** ClientOrganization
- **Members:** [ClientOrganization]
- **Invariants:**
  - `name` must not be blank.
  - `slug` must be non-empty, URL-safe (alphanumeric and hyphens only), and unique across all ClientOrganization records.
  - `created_at` is set once at construction and is immutable.
- **Cross-Aggregate References:**

  | Target Aggregate | Field | Nullable |
  |---|---|---|
  | (none) | - | - |

---

### UserProfileAggregate

- **Root:** UserProfile
- **Members:** [UserProfile]
- **Invariants:**
  - `email` must be a non-empty, syntactically valid email address.
  - `user_id` must uniquely reference a Django User; no two UserProfiles may share the same `user_id`.
  - If `is_client` is `True`, `organization_id` must not be null - a Stakeholder must belong to a ClientOrganization.
  - If `is_client` is `False`, `organization_id` must be null - staff are not members of a ClientOrganization.
- **Cross-Aggregate References:**

  | Target Aggregate | Field | Nullable |
  |---|---|---|
  | ClientOrganizationAggregate | `organization_id` | Yes |

---

### ProjectAggregate

- **Root:** Project
- **Members:** [Project, Milestone]
- **Rationale:** A Milestone cannot exist independently of its parent Project - `project_id` is immutable and Milestone status transitions are guarded by the parent Project's status. They share a single transaction boundary.
- **Invariants:**
  - `Project.name` must not be blank.
  - `Project.organization_id` is immutable after creation.
  - Project status must follow the defined `ProjectStatus` transition rules; direct field mutation from outside the root is prohibited.
  - `Milestone.project_id` is immutable and must equal the aggregate root's `id`.
  - `Milestone.target_date` must be set before a Milestone can transition to `IN_PROGRESS`.
  - Milestone status must follow the defined `MilestoneStatus` transition rules.
  - All Milestones within the aggregate belong to the same Project root.
- **Cross-Aggregate References:**

  | Target Aggregate | Field | Nullable |
  |---|---|---|
  | ClientOrganizationAggregate | `Project.organization_id` | No |

---

### DeliverableAggregate

- **Root:** Deliverable
- **Members:** [Deliverable, DeliverableVersion, Approval]
- **Rationale:** DeliverableVersion is an immutable revision record that is inseparable from its Deliverable; Approval is permanently bound to a single DeliverableVersion. The invariant "a new revision must not be submitted while the current DeliverableVersion has a PENDING Approval" spans all three members and can only be enforced within one transaction boundary.
- **Invariants:**
  - `Deliverable.name` must not be blank.
  - `Deliverable.milestone_id` is immutable after creation.
  - `Deliverable.current_version_number` increments monotonically with each `submit_revision()` call and never decrements.
  - A new revision must not be submitted while the current `DeliverableVersion` has a `PENDING` Approval.
  - At most one Approval may exist per DeliverableVersion; a second Approval for the same version is a domain violation.
  - `Approval.deliverable_version_id` is immutable and must reference a DeliverableVersion that is a member of this aggregate.
  - `Approval.status` is immutable once it reaches `APPROVED`, `REJECTED`, or `REVISION_REQUESTED`.
- **Cross-Aggregate References:**

  | Target Aggregate | Field | Nullable |
  |---|---|---|
  | ProjectAggregate | `Deliverable.milestone_id` | No |
  | UserProfileAggregate | `Approval.reviewer_id` | No |

---

### FileRecordAggregate

- **Root:** FileRecord
- **Members:** [FileRecord]
- **Invariants:**
  - `filename`, `storage_path`, and `mime_type` must not be blank.
  - `storage_path` is immutable after construction.
  - `file_size_bytes` must be a positive integer.
  - Exactly one of `deliverable_version_id` or `message_id` must be set; a FileRecord cannot be simultaneously attached to both, nor detached from both.
- **Cross-Aggregate References:**

  | Target Aggregate | Field | Nullable |
  |---|---|---|
  | DeliverableAggregate | `deliverable_version_id` | Yes |
  | MessageThreadAggregate | `message_id` | Yes |
  | UserProfileAggregate | `uploaded_by_id` | No |

---

### MessageThreadAggregate

- **Root:** MessageThread
- **Members:** [MessageThread, Message]
- **Rationale:** A Message cannot exist independently of its parent MessageThread - `thread_id` is immutable. MessageThread is the natural aggregate root because all external access to Messages flows through it. Both are append-only within the same transaction boundary.
- **Invariants:**
  - `MessageThread.subject` must not be blank.
  - `MessageThread.project_id` is immutable after creation.
  - `Message.thread_id` is immutable and must equal the aggregate root's `id`.
  - `Message.body` must not be blank.
  - Messages are append-only; no editing or deletion is permitted after creation.
- **Cross-Aggregate References:**

  | Target Aggregate | Field | Nullable |
  |---|---|---|
  | ProjectAggregate | `MessageThread.project_id` | No |
  | UserProfileAggregate | `Message.sender_id` | No |

---

### InvoiceRecordAggregate

- **Root:** InvoiceRecord
- **Members:** [InvoiceRecord]
- **Invariants:**
  - `amount` must be a positive `Decimal` value; zero and negative amounts are prohibited.
  - `organization_id` is immutable after creation.
  - `due_date` must be set before the InvoiceRecord can transition out of `DRAFT`.
  - `PAID` and `OVERDUE` are terminal states; no further status transitions are permitted.
- **Cross-Aggregate References:**

  | Target Aggregate | Field | Nullable |
  |---|---|---|
  | ClientOrganizationAggregate | `organization_id` | No |
  | ProjectAggregate | `project_id` | Yes |

---

### ActivityEventAggregate

- **Root:** ActivityEvent
- **Members:** [ActivityEvent]
- **Invariants:**
  - `event_type` must not be blank and must be expressed in past tense (e.g., `ProjectStatusChanged`, `ApprovalDecisionRecorded`).
  - `occurred_at` is set at construction to the current UTC time and is immutable thereafter.
  - An ActivityEvent is immutable after creation; it is never updated or deleted.
- **Cross-Aggregate References:**

  | Target Aggregate | Field | Nullable |
  |---|---|---|
  | UserProfileAggregate | `actor_id` | No |
  | ProjectAggregate | `project_id` | Yes |
  | ClientOrganizationAggregate | `organization_id` | Yes |

---

## Domain Events

> **Collection pattern:** All domain events are raised by collecting them on the aggregate
> root via `collect_events()`. Application services drain this collection after persistence.
> Publishers are never injected into aggregates. Event chains must not exceed 2 levels deep.
> Raw PII is excluded from all payloads; consumers that require PII look it up via the
> owning aggregate's repository using the identity fields carried in the event.

---

### ClientOrganizationRegistered

- **CloudEvents type:** `personal-portfolio.client_organization.registered`
- **Trigger:** `ClientOrganization.__init__()` - new ClientOrganization constructed and persisted
- **Producers:** [ClientOrganizationAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `organization_id` | UUID | Identity of the newly registered ClientOrganization |
  | `name` | str | Display name of the ClientOrganization |
  | `slug` | str | URL-safe identifier |
  | `occurred_at` | datetime | When the event occurred |

---

### UserProfileCreated

- **CloudEvents type:** `personal-portfolio.user_profile.created`
- **Trigger:** `UserProfile.__init__()` - new UserProfile constructed and persisted
- **Producers:** [UserProfileAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `user_profile_id` | UUID | Identity of the new UserProfile |
  | `is_client` | bool | True if this is a Stakeholder profile |
  | `organization_id` | UUID or None | ClientOrganization the Stakeholder belongs to; None for staff |
  | `occurred_at` | datetime | When the event occurred |

  > Note: Email is excluded from the payload (PII). The NotificationService resolves
  > contact details by querying UserProfileRepository with `user_profile_id`.

---

### ProjectActivated

- **CloudEvents type:** `personal-portfolio.project.activated`
- **Trigger:** `Project.activate()` - state transition DRAFT -> ACTIVE
- **Producers:** [ProjectAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `project_id` | UUID | Identity of the activated Project |
  | `organization_id` | UUID | Owning ClientOrganization |
  | `name` | str | Project name at activation time |
  | `occurred_at` | datetime | When the event occurred |

---

### ProjectSubmittedForApproval

- **CloudEvents type:** `personal-portfolio.project.submitted_for_approval`
- **Trigger:** `Project.submit_for_approval()` - state transition ACTIVE -> PENDING_APPROVAL
- **Producers:** [ProjectAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `project_id` | UUID | Identity of the Project submitted for approval |
  | `organization_id` | UUID | Owning ClientOrganization |
  | `occurred_at` | datetime | When the event occurred |

---

### ProjectReturnedToActive

- **CloudEvents type:** `personal-portfolio.project.returned_to_active`
- **Trigger:** `Project.return_to_active()` - state transition PENDING_APPROVAL -> ACTIVE
- **Producers:** [ProjectAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `project_id` | UUID | Identity of the Project returned to active work |
  | `organization_id` | UUID | Owning ClientOrganization |
  | `occurred_at` | datetime | When the event occurred |

---

### ProjectCompleted

- **CloudEvents type:** `personal-portfolio.project.completed`
- **Trigger:** `Project.mark_complete()` - state transition PENDING_APPROVAL -> COMPLETE
- **Producers:** [ProjectAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `project_id` | UUID | Identity of the completed Project |
  | `organization_id` | UUID | Owning ClientOrganization |
  | `occurred_at` | datetime | When the event occurred |

---

### ProjectArchived

- **CloudEvents type:** `personal-portfolio.project.archived`
- **Trigger:** `Project.archive()` - state transition ACTIVE -> ARCHIVED
- **Producers:** [ProjectAggregate]
- **Consumers:** [ActivityEventLogger]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `project_id` | UUID | Identity of the archived Project |
  | `organization_id` | UUID | Owning ClientOrganization |
  | `occurred_at` | datetime | When the event occurred |

---

### MilestoneStarted

- **CloudEvents type:** `personal-portfolio.milestone.started`
- **Trigger:** `Milestone.begin()` - state transition PENDING -> IN_PROGRESS
- **Producers:** [ProjectAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `milestone_id` | UUID | Identity of the started Milestone |
  | `project_id` | UUID | Parent Project |
  | `organization_id` | UUID | Owning ClientOrganization (denormalized for consumer convenience) |
  | `name` | str | Milestone name |
  | `target_date` | date | Expected completion date |
  | `occurred_at` | datetime | When the event occurred |

---

### MilestoneCompleted

- **CloudEvents type:** `personal-portfolio.milestone.completed`
- **Trigger:** `Milestone.complete()` - state transition IN_PROGRESS -> COMPLETE
- **Producers:** [ProjectAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `milestone_id` | UUID | Identity of the completed Milestone |
  | `project_id` | UUID | Parent Project |
  | `organization_id` | UUID | Owning ClientOrganization (denormalized for consumer convenience) |
  | `name` | str | Milestone name |
  | `occurred_at` | datetime | When the event occurred |

---

### DeliverableRevisionSubmitted

- **CloudEvents type:** `personal-portfolio.deliverable.revision_submitted`
- **Trigger:** `Deliverable.submit_revision()` - new DeliverableVersion created; `current_version_number` incremented
- **Producers:** [DeliverableAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `deliverable_id` | UUID | Identity of the Deliverable |
  | `deliverable_version_id` | UUID | Identity of the newly created DeliverableVersion |
  | `version_number` | int | New monotonically increasing version counter value |
  | `milestone_id` | UUID | Parent Milestone |
  | `project_id` | UUID | Parent Project (denormalized for consumer convenience) |
  | `occurred_at` | datetime | When the event occurred |

---

### DeliverableApproved

- **CloudEvents type:** `personal-portfolio.deliverable.approved`
- **Trigger:** `Approval.approve()` on DeliverableAggregate - Approval state transition PENDING -> APPROVED
- **Producers:** [DeliverableAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `deliverable_id` | UUID | Identity of the approved Deliverable |
  | `deliverable_version_id` | UUID | The specific DeliverableVersion that was approved |
  | `approval_id` | UUID | Identity of the Approval record |
  | `reviewer_id` | UUID | Stakeholder UserProfile who approved |
  | `comment` | str or None | Optional reviewer comment |
  | `milestone_id` | UUID | Parent Milestone |
  | `project_id` | UUID | Parent Project (denormalized for consumer convenience) |
  | `occurred_at` | datetime | When the event occurred |

---

### DeliverableRejected

- **CloudEvents type:** `personal-portfolio.deliverable.rejected`
- **Trigger:** `Approval.reject()` on DeliverableAggregate - Approval state transition PENDING -> REJECTED
- **Producers:** [DeliverableAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `deliverable_id` | UUID | Identity of the rejected Deliverable |
  | `deliverable_version_id` | UUID | The specific DeliverableVersion that was rejected |
  | `approval_id` | UUID | Identity of the Approval record |
  | `reviewer_id` | UUID | Stakeholder UserProfile who rejected |
  | `comment` | str | Mandatory rejection reason |
  | `milestone_id` | UUID | Parent Milestone |
  | `project_id` | UUID | Parent Project (denormalized for consumer convenience) |
  | `occurred_at` | datetime | When the event occurred |

---

### DeliverableRevisionRequested

- **CloudEvents type:** `personal-portfolio.deliverable.revision_requested`
- **Trigger:** `Approval.request_revision()` on DeliverableAggregate - Approval state transition PENDING -> REVISION_REQUESTED
- **Producers:** [DeliverableAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `deliverable_id` | UUID | Identity of the Deliverable requiring revision |
  | `deliverable_version_id` | UUID | The specific DeliverableVersion under review |
  | `approval_id` | UUID | Identity of the Approval record |
  | `reviewer_id` | UUID | Stakeholder UserProfile who requested the revision |
  | `comment` | str | Mandatory revision instructions |
  | `milestone_id` | UUID | Parent Milestone |
  | `project_id` | UUID | Parent Project (denormalized for consumer convenience) |
  | `occurred_at` | datetime | When the event occurred |

---

### FileRecordUploaded

- **CloudEvents type:** `personal-portfolio.file_record.uploaded`
- **Trigger:** `FileRecord.__init__()` - binary asset stored in object storage and FileRecord metadata persisted
- **Producers:** [FileRecordAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `file_record_id` | UUID | Identity of the uploaded FileRecord |
  | `filename` | str | Original filename |
  | `mime_type` | str | MIME type of the uploaded file |
  | `file_size_bytes` | int | File size in bytes |
  | `uploaded_by_id` | UUID | UserProfile who performed the upload |
  | `deliverable_version_id` | UUID or None | DeliverableVersion this file is attached to; None if a message attachment |
  | `message_id` | UUID or None | Message this file is attached to; None if a deliverable attachment |
  | `occurred_at` | datetime | When the event occurred |

---

### MessagePosted

- **CloudEvents type:** `personal-portfolio.message_thread.message_posted`
- **Trigger:** `MessageThread.append_message()` - a new Message appended to a MessageThread
- **Producers:** [MessageThreadAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `message_id` | UUID | Identity of the new Message |
  | `thread_id` | UUID | Parent MessageThread |
  | `project_id` | UUID | Project this thread belongs to |
  | `sender_id` | UUID | UserProfile who posted the message |
  | `occurred_at` | datetime | When the event occurred |

  > Note: Message body is excluded from the payload (potentially large; consumers that
  > display message content query MessageRepository with `message_id`).

---

### InvoiceSent

- **CloudEvents type:** `personal-portfolio.invoice_record.sent`
- **Trigger:** `InvoiceRecord.send()` - state transition DRAFT -> SENT
- **Producers:** [InvoiceRecordAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `invoice_id` | UUID | Identity of the InvoiceRecord |
  | `organization_id` | UUID | Billed ClientOrganization |
  | `project_id` | UUID or None | Related Project; None if not project-linked |
  | `amount` | Decimal | Total billed amount |
  | `due_date` | date | Payment due date |
  | `occurred_at` | datetime | When the event occurred |

---

### InvoicePaid

- **CloudEvents type:** `personal-portfolio.invoice_record.paid`
- **Trigger:** `InvoiceRecord.mark_paid()` - state transition SENT -> PAID
- **Producers:** [InvoiceRecordAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `invoice_id` | UUID | Identity of the InvoiceRecord |
  | `organization_id` | UUID | Billed ClientOrganization |
  | `project_id` | UUID or None | Related Project; None if not project-linked |
  | `amount` | Decimal | Amount paid |
  | `occurred_at` | datetime | When the event occurred |

---

### InvoiceMarkedOverdue

- **CloudEvents type:** `personal-portfolio.invoice_record.marked_overdue`
- **Trigger:** `InvoiceRecord.mark_overdue()` - state transition SENT -> OVERDUE
- **Producers:** [InvoiceRecordAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `invoice_id` | UUID | Identity of the InvoiceRecord |
  | `organization_id` | UUID | Billed ClientOrganization |
  | `project_id` | UUID or None | Related Project; None if not project-linked |
  | `amount` | Decimal | Overdue amount |
  | `due_date` | date | Payment due date that was missed |
  | `occurred_at` | datetime | When the event occurred |

---

### InvoiceCancelled

- **CloudEvents type:** `personal-portfolio.invoice_record.cancelled`
- **Trigger:** `InvoiceRecord.cancel()` - transition from DRAFT or SENT to CANCELLED
- **Producers:** [InvoiceRecordAggregate]
- **Consumers:** [ActivityEventLogger, NotificationService]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `invoice_id` | UUID | Identity of the InvoiceRecord |
  | `organization_id` | UUID | Billed ClientOrganization |
  | `project_id` | UUID or None | Related Project; None if not project-linked |
  | `amount` | Decimal | Amount on the cancelled invoice |
  | `previous_status` | str | Status before cancellation (`DRAFT` or `SENT`) |
  | `occurred_at` | datetime | When the event occurred |

---

## Repository Interfaces

> Repository interfaces define the collection contract in domain language. Interfaces live
> in `apps/client_portal/domain/repositories/`. All parameters and return types are domain
> objects; ORM models, raw dicts, and DB rows are prohibited.
>
> Concrete implementations live in `apps/client_portal/infrastructure/persistence/` and
> must use `reconstitute()` (not creation methods) when rehydrating aggregates from
> persistence.

---

### ClientOrganizationRepository

- **Aggregate Root:** ClientOrganization
- **Module path:** `apps/client_portal/domain/repositories/client_organization_repository.py`
- **Methods:**

  | Method | Parameters | Return Type | Description |
  |---|---|---|---|
  | `save` | `organization: ClientOrganization` | `None` | Persist a new or updated ClientOrganization aggregate. |
  | `find_by_id` | `organization_id: UUID` | `Optional[ClientOrganization]` | Retrieve a ClientOrganization by its domain identity. |
  | `find_by_slug` | `slug: str` | `Optional[ClientOrganization]` | Retrieve by unique URL-safe slug; used in portal route resolution. |

---

### UserProfileRepository

- **Aggregate Root:** UserProfile
- **Module path:** `apps/client_portal/domain/repositories/user_profile_repository.py`
- **Methods:**

  | Method | Parameters | Return Type | Description |
  |---|---|---|---|
  | `save` | `profile: UserProfile` | `None` | Persist a new or updated UserProfile aggregate. |
  | `find_by_id` | `profile_id: UUID` | `Optional[UserProfile]` | Retrieve a UserProfile by its domain identity. |
  | `find_by_user_id` | `user_id: int` | `Optional[UserProfile]` | Retrieve by Django User FK; used during authentication to resolve the domain profile from the framework user. |
  | `find_by_email` | `email: str` | `Optional[UserProfile]` | Retrieve by email address; used for login and invitation lookups. |
  | `find_stakeholders_by_organization` | `organization_id: UUID` | `List[UserProfile]` | Return all Stakeholders (`is_client=True`) belonging to a ClientOrganization; used by NotificationService to dispatch approval requests. |

---

### ProjectRepository

- **Aggregate Root:** Project (includes Milestone members)
- **Module path:** `apps/client_portal/domain/repositories/project_repository.py`
- **Methods:**

  | Method | Parameters | Return Type | Description |
  |---|---|---|---|
  | `save` | `project: Project` | `None` | Persist a new or updated ProjectAggregate (Project and its Milestones within one transaction boundary). |
  | `find_by_id` | `project_id: UUID` | `Optional[Project]` | Retrieve a Project with its Milestones by identity. |
  | `find_by_organization` | `organization_id: UUID` | `List[Project]` | Return all Projects commissioned by a ClientOrganization, ordered by creation date descending. |
  | `find_active_by_organization` | `organization_id: UUID` | `List[Project]` | Return Projects in ACTIVE status for a ClientOrganization; used in portal dashboard views. |
  | `find_pending_approval_by_organization` | `organization_id: UUID` | `List[Project]` | Return Projects in PENDING_APPROVAL status; used by NotificationService after ProjectSubmittedForApproval. |
  | `find_by_status` | `status: ProjectStatus` | `List[Project]` | Return all Projects matching a given ProjectStatus across all organizations; used by administrative views. |

---

### DeliverableRepository

- **Aggregate Root:** Deliverable (includes DeliverableVersion and Approval members)
- **Module path:** `apps/client_portal/domain/repositories/deliverable_repository.py`
- **Methods:**

  | Method | Parameters | Return Type | Description |
  |---|---|---|---|
  | `save` | `deliverable: Deliverable` | `None` | Persist a new or updated DeliverableAggregate (Deliverable, DeliverableVersions, and Approvals within one transaction boundary). |
  | `find_by_id` | `deliverable_id: UUID` | `Optional[Deliverable]` | Retrieve a Deliverable with its full version and approval history by identity. |
  | `find_by_milestone` | `milestone_id: UUID` | `List[Deliverable]` | Return all Deliverables belonging to a Milestone, ordered by creation date. |
  | `find_by_project` | `project_id: UUID` | `List[Deliverable]` | Return all Deliverables across all Milestones for a Project; used when evaluating project completion readiness. |
  | `find_pending_approval_by_milestone` | `milestone_id: UUID` | `List[Deliverable]` | Return Deliverables whose current DeliverableVersion has a PENDING Approval; used to guard the MilestoneCompleted transition. |

---

### FileRecordRepository

- **Aggregate Root:** FileRecord
- **Module path:** `apps/client_portal/domain/repositories/file_record_repository.py`
- **Methods:**

  | Method | Parameters | Return Type | Description |
  |---|---|---|---|
  | `save` | `file_record: FileRecord` | `None` | Persist a new FileRecord aggregate. Storage path is immutable; records are never updated after creation. |
  | `find_by_id` | `file_record_id: UUID` | `Optional[FileRecord]` | Retrieve a FileRecord by its identity. |
  | `find_by_deliverable_version` | `deliverable_version_id: UUID` | `List[FileRecord]` | Return all FileRecords attached to a DeliverableVersion; used by FileRecordUploaded event consumers. |
  | `find_by_message` | `message_id: UUID` | `List[FileRecord]` | Return all FileRecords attached to a Message; used when rendering message content with its attachments. |

---

### MessageThreadRepository

- **Aggregate Root:** MessageThread (includes Message members)
- **Module path:** `apps/client_portal/domain/repositories/message_thread_repository.py`
- **Methods:**

  | Method | Parameters | Return Type | Description |
  |---|---|---|---|
  | `save` | `thread: MessageThread` | `None` | Persist a new or updated MessageThreadAggregate (MessageThread and appended Messages within one transaction boundary). |
  | `find_by_id` | `thread_id: UUID` | `Optional[MessageThread]` | Retrieve a MessageThread with its Messages by identity. |
  | `find_by_project` | `project_id: UUID` | `List[MessageThread]` | Return all MessageThreads belonging to a Project, ordered by most recent message activity descending. |

---

### InvoiceRecordRepository

- **Aggregate Root:** InvoiceRecord
- **Module path:** `apps/client_portal/domain/repositories/invoice_record_repository.py`
- **Methods:**

  | Method | Parameters | Return Type | Description |
  |---|---|---|---|
  | `save` | `invoice: InvoiceRecord` | `None` | Persist a new or updated InvoiceRecord aggregate. |
  | `find_by_id` | `invoice_id: UUID` | `Optional[InvoiceRecord]` | Retrieve an InvoiceRecord by its identity. |
  | `find_by_organization` | `organization_id: UUID` | `List[InvoiceRecord]` | Return all InvoiceRecords issued to a ClientOrganization, ordered by creation date descending. |
  | `find_by_project` | `project_id: UUID` | `List[InvoiceRecord]` | Return all InvoiceRecords associated with a specific Project. |
  | `find_overdue_invoices` | *(none)* | `List[InvoiceRecord]` | Return all InvoiceRecords with OVERDUE status; used by scheduled overdue-detection tasks and seed data validation. |
  | `find_unpaid_by_organization` | `organization_id: UUID` | `List[InvoiceRecord]` | Return InvoiceRecords in SENT status for a ClientOrganization; used to display outstanding balance to Stakeholders. |

---

### ActivityEventRepository

- **Aggregate Root:** ActivityEvent
- **Module path:** `apps/client_portal/domain/repositories/activity_event_repository.py`
- **Note:** ActivityEvent is immutable and append-only. `save` appends a new record only; no update or delete methods exist on this repository.
- **Methods:**

  | Method | Parameters | Return Type | Description |
  |---|---|---|---|
  | `save` | `event: ActivityEvent` | `None` | Append a new immutable ActivityEvent to the log. Never updates or deletes an existing record. |
  | `find_by_id` | `event_id: UUID` | `Optional[ActivityEvent]` | Retrieve an ActivityEvent by its identity. |
  | `find_by_project` | `project_id: UUID, page: int, page_size: int` | `List[ActivityEvent]` | Return paginated ActivityEvents for a Project ordered by occurred_at descending; used for the project activity feed. |
  | `find_by_organization` | `organization_id: UUID, page: int, page_size: int` | `List[ActivityEvent]` | Return paginated organization-level ActivityEvents ordered by occurred_at descending. |
  | `find_by_actor` | `actor_id: UUID, page: int, page_size: int` | `List[ActivityEvent]` | Return paginated ActivityEvents triggered by a specific UserProfile; used for per-user audit trail views. |

---

## Domain Services

> **Candidate evaluation:**
>
> - **InvoiceOverdueClassifier** - Rejected. The `SENT -> OVERDUE` transition is already
>   encapsulated in `InvoiceRecord.mark_overdue()`. Identifying which invoices are past due
>   is a query concern - a future `find_sent_past_due_date` repository method returns the
>   candidates, and the application service calls `mark_overdue()` on each. No
>   cross-aggregate logic is involved.
>
> - **ProjectCompletionEligibilityChecker** - Rejected. Milestone is a member of
>   `ProjectAggregate`. The completion eligibility check belongs in `Project.mark_complete()`
>   as its guard condition ("All Deliverables across all Milestones have an APPROVED
>   Approval on their current DeliverableVersion"). No aggregate boundary is crossed.
>
> - **ActivityEventFactory** - Rejected. ActivityEvent construction is straightforward and
>   requires no cross-aggregate coordination. Consistent `event_type` strings are enforced
>   by constants or an enum in the domain model. A static factory method on `ActivityEvent`
>   is sufficient if construction complexity warrants it.

---

### DeliverableApprovalCoordinator

- **Responsibility:** When a Deliverable is approved, checks whether all Deliverables within the parent Milestone are now approved and, if so, triggers Milestone completion on the ProjectAggregate.
- **Operates On:** [DeliverableAggregate, ProjectAggregate]
- **Location:** `apps/client_portal/domain/services/deliverable_approval_coordinator.py`
- **Methods:**

  | Method | Description |
  |---|---|
  | `coordinate_post_approval(deliverable: Deliverable, milestone_deliverables: List[Deliverable], project: Project) -> None` | Inspects the current approval state of every Deliverable in `milestone_deliverables`; calls `project.complete_milestone(deliverable.milestone_id)` when every member has an `APPROVED` Approval on its current `DeliverableVersion`. |

- **Design Notes:**
  - `milestone_deliverables` is the complete list of Deliverables for the parent Milestone,
    loaded by the application service via `DeliverableRepository.find_by_milestone` before
    invoking this service. The domain service receives hydrated domain objects only - no IDs,
    ORM instances, or infrastructure types.
  - The service raises `MilestoneCompletionNotAllowed` (a domain exception) if
    `milestone_deliverables` is empty, guarding against a degenerate Milestone with no
    Deliverables.
  - After `project.complete_milestone()` succeeds, the calling application service is
    responsible for persisting the updated ProjectAggregate and draining its domain events.
