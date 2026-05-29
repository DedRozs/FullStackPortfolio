# Documentation to Deployment Artifact

<!-- This template is produced by the Documentation Orchestrator and consumed by the
     Deployment Orchestrator. Every file path listed must exist on disk before this
     artifact is delivered. Validate against:
     contracts/schemas/documentation-to-deployment.schema.json -->

**Schema version:** 1.0
**Project name:** This Project
**Produced by:** `.github/agents/documentation-orchestrator.agent.md`
**Consumed by:** `.github/agents/deployment-orchestrator.agent.md`

---

## Schema Version

Record the schema version used: `1.0`

---

## Project Name

State the full project name as configured in `This Project`.

---

## Knowledge Base Manifest

<!-- Produced by: documentation-orchestrator (assembled from all documentation specialists) -->

List every documentation file produced during the Documentation phase. All paths are
relative to the project repository root.

| File Path | Type | Description |
|---|---|---|
| `[relative/path]` | [architecture / api / readme / onboarding / runbook / adr / decision-log] | [what this document covers] |

---

## README Path

<!-- Produced by: readme-writer -->

**Project README location:** `[relative path - e.g., README.md]`

> The Deployment Orchestrator uses this path to confirm the README is present and
> current before triggering CI/CD configuration.

---

## Runbooks

<!-- Produced by: runbook-writer -->

List all operational runbooks. At minimum, a deployment runbook must be present.

| File Path | Scope | Audience |
|---|---|---|
| `[relative/path]` | [Deployment / Incident Response / Database Backup / ...] | [Operations team / On-call engineer / ...] |

---

## ADR Index

<!-- Produced by: adr-indexer -->

| Field | Value |
|---|---|
| Total ADR count | [n] |
| Index file path | `[relative/path/to/adr-index.md]` |

### ADR Entries

| ADR ID | Title | Status | File Path |
|---|---|---|---|
| ADR-001 | [title] | [proposed / accepted / deprecated / superseded] | `[path]` |

---

## Decision Log

<!-- Produced by: decision-log-writer -->

| Field | Value |
|---|---|
| File path | `[relative/path/to/decision-log.md]` |
| Total decisions | [n] |
| Phases covered | [discovery, architecture, domain-modeling, development, qa, documentation] |
