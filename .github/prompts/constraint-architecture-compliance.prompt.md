---
name: constraint-architecture-compliance
description: "Use when: a specialist agent must declare compliance with Clean Architecture and DDD instruction files for code generation or validation work."
mode: agent
---

## Architecture Compliance Requirements

All code generation, review, and validation work in this agent must comply with the
following instruction files. Read each complete file before producing any output.

- Must follow rules in clean-architecture.instructions.md
  (path: `.github/instructions/clean-architecture.instructions.md`)
- Must follow rules in domain-driven-design.instructions.md
  (path: `.github/instructions/domain-driven-design.instructions.md`)
- Must follow rules in ddd-domain-model.instructions.md
  (path: `.github/instructions/ddd-domain-model.instructions.md`)
- Must follow rules in ddd-application.instructions.md
  (path: `.github/instructions/ddd-application.instructions.md`)
- Must follow rules in ddd-infrastructure.instructions.md
  (path: `.github/instructions/ddd-infrastructure.instructions.md`)
- Must follow rules in event-driven.instructions.md
  (path: `.github/instructions/event-driven.instructions.md`)

Include only the subset of files that applies to the layer or domain of this agent's
responsibility. Domain-layer agents require `clean-architecture`, `domain-driven-design`,
and `ddd-domain-model`. Application-layer agents add `ddd-application`. Infrastructure
and adapter agents add `ddd-infrastructure`. Event-driven work adds `event-driven`.
