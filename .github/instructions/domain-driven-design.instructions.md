---
applyTo: "**/*.{py,ts,cs,java,kt}"
description: "Use when applying Domain-Driven Design (DDD) - ubiquitous language, bounded contexts, aggregates, entities, value objects, domain events, or repositories. Core cross-layer DDD rules; layer-specific rules are in the ddd-domain-model, ddd-application, and ddd-infrastructure instruction files."
---
<!-- v1.2 | Created: 2026-05-01 | Pattern: Domain-Driven Design -->

# Domain-Driven Design Instructions

Core DDD rules that apply across all layers. Layer-specific rules and code examples are in:
- `ddd-domain-model.instructions.md` - Entities, Value Objects, Aggregates, Domain Events, Domain Services
- `ddd-application.instructions.md` - Application Services, Query Handlers
- `ddd-infrastructure.instructions.md` - Repositories, Bounded Contexts, Anti-Corruption Layer

---

## Ubiquitous Language

- Use domain terms from the project glossary in all code: class names, method names, variable names, events.
- Never substitute technical synonyms when a domain term exists (e.g., use `Order`, not `Record` or `Entity`).
- Event names are past tense: `OrderConfirmed`, `PaymentReceived`. Never imperative: `ConfirmOrder` is wrong.
- If a term has different meanings in different parts of the system, that is a bounded context boundary - model them separately.

---

## Layer Rules

Project layers in dependency order (dependencies point inward only):

```
domain/ -> application/ -> infrastructure/ -> presentation/
```

- `domain/` has zero imports from any other layer. No ORM types, no framework types, no HTTP types.
- `application/` imports only from `domain/`. Application services are thin coordinators: load aggregate, call domain method, save, publish events.
- `infrastructure/` implements domain interfaces. ORM mappings and DB queries live here.
- `presentation/` calls application services. No business logic. No domain types in responses - use DTOs.

Any business rule (calculation, validation, state guard) found outside `domain/` is a violation.

### Canonical Folder Structure

```
project/
├── domain/
│   ├── model/          # Entities, value objects, aggregates
│   ├── events/         # Domain events
│   ├── services/       # Domain services (cross-aggregate logic only)
│   └── repositories/   # Repository interfaces (ABC only, no implementations)
├── application/
│   ├── commands/       # Use case handlers (write side)
│   └── queries/        # Query handlers (read side)
├── infrastructure/
│   ├── persistence/    # Repository implementations, ORM mappings
│   ├── messaging/      # Event bus, message broker adapters
│   └── external/       # Anti-corruption layers for third-party services
└── presentation/
    ├── api/            # Controllers, route handlers
    └── dto/            # Request/response shapes
```

---

## Anti-Patterns Reference

| Anti-Pattern | Symptom | Correct Approach |
|---|---|---|
| Anemic Domain Model | Entity has only getters/setters; all logic lives in services | Move business rules into entity methods |
| God Aggregate | Aggregate loads unrelated collections (Customer has orders, invoices, tickets) | Separate aggregates; reference by ID |
| Shared Cross-Context Model | One `Order` class used by Sales, Shipping, and Inventory | Each context defines its own model |
| Repository Returns Non-Domain Types | Repository returns ORM model, dict, or DB row to domain layer | Repository returns fully reconstituted aggregate |
| Business Logic in Application Service | Application service contains guards, calculations, or state decisions | Move all business logic into the aggregate or domain service |
| Direct State Mutation | `order.status = OrderStatus.CONFIRMED` called from outside | Use `order.confirm()` - aggregate enforces its own transitions |
| Publisher Injected into Aggregate | `Order.__init__` accepts an `EventPublisher` | Use `collect_events()` pattern; application layer publishes |
| Creation Methods Used for Rehydration | `add_line()` called during DB reconstruction | Use `reconstitute()` factory method |
