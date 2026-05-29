---
name: pattern-layer-separation
description: "Use when: implementing adapters, controllers, presenters, or infrastructure configuration where business logic must not appear."
mode: agent
---

## Layer Separation - No Business Logic in Outer Layers

The domain layer owns all business rules, domain calculations, and invariant enforcement.
Outer layers (adapters, controllers, presenters, infrastructure, framework configuration)
must contain no business logic.

### What belongs in the domain layer only

- Validation rules that enforce domain invariants
- Calculations that produce domain values (prices, totals, durations, statuses)
- State transition guards and conditions
- Domain-specific string formatting or parsing tied to domain meaning

### What outer layers must do instead

- **Controllers / Input Adapters:** deserialize HTTP input into request models, invoke
  the use case through its input port interface, and return the output model or error
  code. No if-branches that implement domain decisions.
- **Presenters / Output Adapters:** transform use case output models into view models
  or response payloads. No business calculations; reshape only.
- **Repository Implementations:** translate between domain entities and persistence
  models. Use a mapper; no business logic in the mapper.
- **Framework Configuration / DI Container:** wire dependencies. No conditional logic
  based on business state.
- **Infrastructure / External Service Clients:** call external APIs and translate
  responses. Error mapping to domain exceptions is permitted; business decisions are not.

### Prohibited patterns

- `if (order.total > 100)` in a controller
- Tax or discount calculation in a presenter
- Status derivation in a repository mapper
- Feature flags that encode business rules in framework configuration
