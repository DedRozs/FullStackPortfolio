# Discovery to Architecture Artifact

<!-- This template is produced by the Discovery Orchestrator and consumed by the
     Architecture Orchestrator. Complete every section. Do not leave placeholder
     text in the final artifact. Validate against:
     contracts/schemas/discovery-to-architecture.schema.json -->

**Schema version:** 1.0
**Project name:** This Project
**Produced by:** `.github/agents/discovery-orchestrator.agent.md`
**Consumed by:** `.github/agents/architecture-orchestrator.agent.md`

---

## Schema Version

Record the schema version used: `1.0`

---

## Project Name

State the full project name as configured in `This Project`.

---

## Product Vision

<!-- Produced by: vision-analyst -->

### Problem Statement

State the core problem this system solves in one to three sentences. Be specific about
the pain, the affected parties, and why existing solutions fall short.

> [vision-analyst: insert problem statement here]

### Target Users

List each primary user group on a separate line:

- [user group 1]
- [user group 2]

### Success Metrics

List measurable outcomes that define success. Each metric must be specific and verifiable:

- [metric 1 - e.g., "Reduce order processing time from 4 hours to under 15 minutes"]
- [metric 2]

---

## Stakeholders

<!-- Produced by: stakeholder-analyst -->

For each stakeholder, provide name/role, category, and their interest in the system.

| Name / Role | Category | Interest |
|---|---|---|
| [stakeholder 1] | [end-user / sponsor / regulator / integrator] | [what they need and why] |
| [stakeholder 2] | | |

---

## Domain Glossary

<!-- Produced by: domain-vocabulary-elicitor -->

These terms are the preliminary ubiquitous language for `This Project`. All
subsequent phases use these terms verbatim in code, documents, and discussions.

| Term | Definition | Bounded Context |
|---|---|---|
| [Term] | [Precise domain definition] | [Context name] |
| [Term] | | |

---

## Requirements

<!-- Produced by: business-analyst -->

### Functional Requirements

| ID | Title | Description |
|---|---|---|
| FR-001 | [title] | [full description of required behavior] |
| FR-002 | | |

### Non-Functional Requirements

| ID | Category | Description |
|---|---|---|
| NFR-001 | [performance / security / availability / scalability / ...] | [specific, measurable statement] |
| NFR-002 | | |

### Constraints

List fixed limitations the system must operate within:

- [constraint 1 - e.g., "Must comply with GDPR"]
- [constraint 2]

---

## Prioritized Backlog

<!-- Produced by: backlog-prioritizer -->

Requirements ranked from highest (1) to lowest priority. Each entry must reference a
functional requirement ID and include at least one Given/When/Then acceptance criterion.

| Rank | Req ID | Title | Acceptance Criteria |
|---|---|---|---|
| 1 | FR-001 | [title] | Given [context], when [action], then [outcome] |
| 2 | FR-002 | | |

---

## Process Validation

<!-- Produced by: discovery-artifact-validator -->

**Validated by:** discovery-artifact-validator

**Identified gaps or open questions carried forward to Architecture:**

- [gap 1, or "none"]

**Readiness confirmed:** [true / false]

> The readiness field must be `true` for the Architecture Orchestrator to accept this
> artifact and begin the Architecture phase.
