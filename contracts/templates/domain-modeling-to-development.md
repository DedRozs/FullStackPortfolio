# Domain Modeling to Development Artifact

<!-- This template is produced by the Domain Modeling Orchestrator and consumed by the
     Development Orchestrator. Complete every section before handoff. This document is
     the implementation specification: development agents must not begin coding until
     this artifact is approved. Validate against:
     contracts/schemas/domain-modeling-to-development.schema.json -->

**Schema version:** 1.0
**Project name:** This Project
**Produced by:** `.github/agents/domain-modeling-orchestrator.agent.md`
**Consumed by:** `.github/agents/development-orchestrator.agent.md`

---

## Schema Version

Record the schema version used: `1.0`

---

## Project Name

State the full project name as configured in `This Project`.

---

## Ubiquitous Language

<!-- Produced by: ubiquitous-language-curator -->

Finalized domain vocabulary. All development agents use these terms verbatim as code
identifiers. No synonyms, abbreviations, or technical substitutes are permitted.

| Term | Definition | Bounded Context | Usage Examples |
|---|---|---|---|
| [Term] | [Precise definition] | [Context] | [`ClassName`, method name example] |

---

## Entities

<!-- Produced by: entity-modeler -->

For each entity, document identity type, invariants, state transitions, and key attributes.

### [EntityName]

- **Bounded Context:** [context name]
- **Identity:** [UUID / composite key / ...]
- **Invariants:**
  - [invariant 1 - business rule that must always hold]
  - [invariant 2]
- **State Transitions:**

  | From | To | Trigger | Guard |
  |---|---|---|---|
  | [state] | [state] | [method name] | [condition that must be true] |

- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | [name] | [type] | [what this attribute represents] |

---

## Value Objects

<!-- Produced by: value-object-modeler -->

For each value object, document its immutable properties, validation rules, and equality basis.

### [ValueObjectName]

- **Bounded Context:** [context name]
- **Properties:**

  | Name | Type |
  |---|---|
  | [name] | [type] |

- **Validation Rules:**
  - [rule enforced at construction time]
- **Equality Basis:** [e.g., "All properties must be equal"]

---

## Aggregates

<!-- Produced by: aggregate-designer -->

For each aggregate, identify the root, members, cross-boundary invariants, and external references.

### [AggregateName]

- **Root:** [entity name that is the aggregate root]
- **Members:** [list of entities and value objects inside this boundary]
- **Aggregate-Level Invariants:**
  - [invariant spanning multiple members]
- **Cross-Aggregate References (by identity only):**

  | Target Aggregate | Reference Type |
  |---|---|
  | [aggregate name] | by-id |

---

## Domain Events

<!-- Produced by: domain-event-designer -->

All event names must be past tense. Payloads must contain sufficient data for consumers
to act without a secondary lookup. Follow the CloudEvents standard (see
`.github/instructions/event-driven.instructions.md`).

### [EventName]

- **Trigger:** [action or state transition that raises this event]
- **Producers:** [aggregate or service that publishes this event]
- **Consumers:** [who subscribes to this event]
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | [field] | [type] | [what it represents] |

---

## Repository Interfaces

<!-- Produced by: repository-interface-designer -->

Interfaces are defined in domain language. They live in `domain/repositories/` and have
no infrastructure types. Only aggregate roots have repositories.

### [RepositoryName]

- **Aggregate Root:** [entity name]
- **Methods:**

  | Method Name | Parameters | Return Type | Description |
  |---|---|---|---|
  | [name] | [(param: type)] | [type] | [what it does in domain terms] |

---

## Domain Services

<!-- Produced by: domain-service-designer -->

Document only services for logic that genuinely spans multiple aggregates. Single-aggregate
logic belongs in the entity itself.

### [DomainServiceName]

- **Responsibility:** [cross-aggregate business logic this service encapsulates]
- **Operates On:** [aggregate1, aggregate2, ...]
- **Methods:**

  | Method Name | Description |
  |---|---|
  | [name] | [what this operation does] |
