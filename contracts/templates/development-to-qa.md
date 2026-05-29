# Development to QA Artifact

<!-- This template is produced by the Development Orchestrator and consumed by the
     QA Orchestrator. All test counts and coverage metrics must be populated before
     handoff. The QA Orchestrator will not accept this artifact if any test has
     failCount > 0. Validate against:
     contracts/schemas/development-to-qa.schema.json -->

**Schema version:** 1.0
**Project name:** This Project
**Produced by:** `.github/agents/development-orchestrator.agent.md`
**Consumed by:** `.github/agents/qa-orchestrator.agent.md`

---

## Schema Version

Record the schema version used: `1.0`

---

## Project Name

State the full project name as configured in `This Project`.

---

## Source Code Manifest

<!-- Produced by: development-orchestrator (assembled from all four mid-level teams) -->

List every source file created during development. Include the Clean Architecture layer
and a brief description of its role.

| File Path | Layer | Description |
|---|---|---|
| `[relative/path/to/file]` | [domain / application / adapters / infrastructure / presentation] | [what this file contains] |

---

## Test Coverage Summary

<!-- Produced by: domain-implementation-orchestrator, use-case-orchestrator (unit tests);
     adapter-orchestrator, infrastructure-orchestrator (integration tests) -->

### Unit Tests

| Metric | Value |
|---|---|
| Test file count | [n] |
| Passing | [n] |
| Failing | [n] |
| Coverage % (domain + application layers) | [n]% |

### Integration Tests

| Metric | Value |
|---|---|
| Test file count | [n] |
| Passing | [n] |
| Failing | [n] |

### End-to-End Tests

| Metric | Value |
|---|---|
| Test file count | [n] |
| Passing | [n] |
| Failing | [n] |

### Overall Coverage

**Aggregate statement coverage across all test types:** [n]%

---

## Dependency List

<!-- Produced by: di-container-configurator -->

List all runtime dependencies. Include pinned version and SPDX license identifier.

| Package | Version | License | Purpose |
|---|---|---|---|
| [package name] | [pinned version] | [SPDX identifier] | [why this dependency is needed] |

---

## Layer Compliance Summary

<!-- Produced by: development-orchestrator (verified during code assembly) -->

For each layer, confirm compliance with Clean Architecture dependency rules. Any
violation must be listed. The QA code-reviewer will re-verify this section.

### Domain Layer

- **Compliant:** [true / false]
- **Violations:** [list violations, or "none"]

### Application Layer

- **Compliant:** [true / false]
- **Violations:** [list violations, or "none"]

### Adapters Layer

- **Compliant:** [true / false]
- **Violations:** [list violations, or "none"]

### Infrastructure Layer

- **Compliant:** [true / false]
- **Violations:** [list violations, or "none"]

---

## Known Issues

<!-- Produced by: development-orchestrator -->

List any known limitations, deferred items, or accepted technical debt. Include why
each item was not resolved during Development. Leave empty if none.

| Description | Severity | Deferral Reason |
|---|---|---|
| [issue description] | [critical / high / medium / low] | [why it was deferred] |
