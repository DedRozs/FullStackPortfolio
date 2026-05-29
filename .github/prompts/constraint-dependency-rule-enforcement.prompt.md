---
name: constraint-dependency-rule-enforcement
description: "Use when: reviewing or implementing domain layer code to enforce the Clean Architecture dependency rule."
mode: agent
---

## Dependency Rule Enforcement

The Clean Architecture dependency rule is absolute: source code dependencies must point
only inward. Inner layers have no knowledge of outer layers.

### Layer order (outermost to innermost)

```
Frameworks & Drivers  ->  Interface Adapters  ->  Application  ->  Domain
```

### Rules by layer

**Domain layer** (`domain/`)
- May import only from within `domain/`.
- Must never import from `application/`, `adapters/`, `infrastructure/`, `presentation/`,
  or any framework package.
- Framework types, ORM annotations, HTTP types, and message broker types are all
  prohibited in the domain layer.

**Application layer** (`application/`)
- May import from `domain/` and `application/`.
- Must never import concrete infrastructure or adapter implementations.
- Must depend on interfaces (ports) defined in `application/ports/`; implementations
  are injected from outside.

**Adapters layer** (`adapters/`)
- May import from `application/` (input/output port interfaces) and `domain/` (entity
  and event types only).
- Must never import directly from `infrastructure/` or bypass a port interface.

**Infrastructure layer** (`infrastructure/`)
- May import from any inner layer but must not be imported by those layers.
- All domain and application access to infrastructure must go through interfaces.

### Violation severity

- Domain importing from application or outer layers: **critical**
- Application importing concrete infrastructure implementations: **high**
- Adapter importing from infrastructure directly: **high**
- Any circular dependency between layers: **critical**
