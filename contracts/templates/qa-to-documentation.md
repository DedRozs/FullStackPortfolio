# QA to Documentation Artifact

<!-- This template is produced by the QA Orchestrator and consumed by the
     Documentation Orchestrator. The Documentation Orchestrator must not begin
     until securitySignOff.signOffGranted is true and all test results pass.
     Validate against:
     contracts/schemas/qa-to-documentation.schema.json -->

**Schema version:** 1.0
**Project name:** This Project
**Produced by:** `.github/agents/qa-orchestrator.agent.md`
**Consumed by:** `.github/agents/documentation-orchestrator.agent.md`

---

## Schema Version

Record the schema version used: `1.0`

---

## Project Name

State the full project name as configured in `This Project`.

---

## Verified Codebase Reference

<!-- Produced by: qa-orchestrator (recorded after final re-verification pass) -->

| Field | Value |
|---|---|
| Commit hash | [full Git commit hash] |
| Branch | [branch name] |
| Verified at | [ISO 8601 UTC timestamp - e.g., 2026-05-01T14:30:00Z] |

---

## Test Results

<!-- Produced by: unit-test-engineer, integration-test-engineer, e2e-test-engineer -->

| Test Type | Passed |
|---|---|
| Unit tests | [true / false] |
| Integration tests | [true / false] |
| End-to-end tests | [true / false] |

| Metric | Count |
|---|---|
| Total defects found | [n] |
| Total defects resolved | [n] |

> Both defect counts must be equal for the Documentation phase gate to pass.

---

## Known Limitations Log

<!-- Produced by: defect-repair-coordinator (documented accepted limitations) -->

Limitations that were reviewed, accepted, and will be noted in documentation.
Document them here so the documentation-orchestrator can include them in user-facing
materials. Leave table empty if none.

| Limitation | Impact | Workaround |
|---|---|---|
| [description] | [who is affected and under what conditions] | [workaround, or "none"] |

---

## Security Sign-Off

<!-- Produced by: security-reviewer -->

| Field | Value |
|---|---|
| Reviewed by | security-reviewer |
| OWASP findings status | [all-mitigated / open-low-only / open-medium / open-high / open-critical] |
| Sign-off granted | [true / false] |

> Sign-off granted must be `true` (no critical or high findings open) for the
> Documentation phase to begin.

### Open Findings

List any OWASP findings that remain open after QA. Empty if sign-off is granted.

| OWASP Item | Description | Severity |
|---|---|---|
| [item] | [finding description] | [critical / high / medium / low] |

---

## Performance Summary

<!-- Produced by: performance-analyst -->

### Metrics Recorded

| Metric | Value | Unit |
|---|---|---|
| [metric name - e.g., p99 response time] | [value] | [ms / rps / ...] |

### Bottlenecks Identified

- [bottleneck description, or "none"]

### Non-Functional Requirements Met

**All performance NFRs satisfied:** [true / false]

> If false, list which NFRs are not met and the gap before submitting this artifact.
