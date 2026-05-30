# ADR 0003: client_portal Domain-ORM Split

**Status:** Accepted
**Date:** 2026-05-29
**Deciders:** Joseph Prince
**Technical Story:** FSP-1 - client_portal Phase 1 Foundation

---

## Context

The client_portal bounded context has significant domain complexity: four status state
machines (Project, Milestone, Approval, Invoice), cross-entity invariants (FileRecord
must attach to exactly one of DeliverableVersion or Message), and role-based constraints
(client UserProfiles must belong to an organization; staff must not). This logic must be
unit-testable without a running database.

Django encourages placing business logic on `models.Model` subclasses, but doing so
couples domain rules to the ORM and makes testing require a database. The alternative -
duplicating validation in both a plain Python layer and ORM model - creates divergence
risk.

---

## Decision

Implement two parallel representations of every domain entity:

1. **Domain layer** (`apps/client_portal/domain/model.py`): Plain Python dataclasses
   with `__post_init__` invariants and state-transition methods. Zero Django imports.
   Enums and frozen dataclasses for value objects in `domain/value_objects.py`. Abstract
   repository interfaces (ABCs) in `domain/repositories.py`.

2. **Persistence layer** (`apps/client_portal/models.py`): Django ORM models that mirror
   the domain structure. Responsible for schema definition and migration management only.
   No business logic. Status values use `CharField(choices=...)` with string constants
   matching the domain enums.

Repository implementations (deferred to Phase 2) are the only code that translates
between the two representations.

---

## Options Considered

### Option 1: Business logic on Django ORM models only
**Pros:** Single representation; less code duplication; Django tooling (admin, shell)
works directly on the objects that carry the rules.
**Cons:** Domain logic coupled to ORM; unit tests require a database or complex mocking;
violates the dependency rule (domain depends on infrastructure).

### Option 2: Plain Python domain layer + separate ORM layer (chosen)
**Pros:** Domain is testable without a database (54 tests run in 0.008 s); dependency
rule respected; domain can be reasoned about independently of persistence concerns.
**Cons:** Two class hierarchies to maintain; mapping code required in repository
implementations; Django admin works on ORM models, not domain objects.

### Option 3: Single Django model with service functions for business rules
**Pros:** Fewer files; admin and ORM tools work directly.
**Cons:** Service functions are easy to bypass; no structural enforcement that business
rules run before persistence; no clear home for invariants.

---

## Rationale

The client_portal domain has enough state machine complexity that unit-testable domain
objects are worth the cost of maintaining two layers. With 12 entities, 4 status enums,
and cross-entity invariants, the risk of introducing a silent regression is high without
fast, database-free tests. The mapping cost in repository implementations is a one-time
investment per aggregate, bounded and predictable.

The 54 domain unit tests run in 8 ms - fast enough to run on every save. This speed is
only possible because the domain layer has zero infrastructure dependencies.

---

## Consequences

### Positive
- Domain invariants and state transitions are unit-testable without a database.
- The domain layer can be understood and evolved independently of Django migration history.
- Clear enforcement boundary: business rules in `domain/`, persistence concerns in
  `models.py`.

### Negative (trade-offs)
- Two representations of every entity must be kept structurally consistent.
- Django admin operates on ORM models, not domain objects; domain rules are not enforced
  through the admin interface unless explicitly re-applied in admin validation.
- Repository implementations in Phase 2 require field-by-field mapping between ORM rows
  and domain dataclasses.
- `FileRecord.storage_path` has no model-level path traversal validation in the ORM
  layer; this must be enforced at the application service boundary before any Phase 2
  write paths are introduced.
