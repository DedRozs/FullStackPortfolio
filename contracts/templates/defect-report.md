# Defect Report

<!-- This template is produced by the defect-repair-coordinator in the QA phase.
     One report per defect. Route the completed report to the Development sub-team
     orchestrator identified in routingTarget. After repair, re-run all steps listed
     in verificationStepsRequired before closing this report. Validate against:
     contracts/schemas/defect-report.schema.json -->

**Schema version:** 1.0
**Project name:** This Project
**Produced by:** `.github/agents/defect-repair-coordinator.agent.md`
**Routed to:** [see Routing Target below]

---

## Schema Version

Record the schema version used: `1.0`

---

## Defect ID

Unique identifier assigned by the defect-repair-coordinator: `DEF-[nnn]`

---

## Defect Description

<!-- Be specific: state the observed behavior, the expected behavior, and the difference. -->

**Observed behavior:**
[What the system actually does]

**Expected behavior:**
[What the system should do according to the requirements or domain model specification]

**Difference:**
[The specific gap between observed and expected]

---

## Reproduction Steps

Ordered steps that reliably reproduce this defect. Include any setup required.

1. [step 1]
2. [step 2]
3. [step 3 - add more as needed]

---

## Severity

**Severity:** [critical / high / medium / low]

- **critical** - System is unusable; data loss or security breach risk
- **high** - Core functionality broken; no acceptable workaround
- **medium** - Functionality degraded; workaround exists
- **low** - Minor issue; cosmetic or edge-case impact

---

## Affected Component

**Component:** [specific file, class, module, or subsystem where the defect originates]

---

## Affected Layer

**Layer:** [domain / application / adapters / infrastructure / presentation]

---

## Originating Phase

**Discovered during:** [code-review / unit-testing / integration-testing / e2e-testing / security-review / performance-analysis]

---

## Routing Target

The Development sub-team orchestrator responsible for repairing this defect.

**Route to:**
`[.github/agents/domain-implementation-orchestrator.agent.md |
  .github/agents/use-case-orchestrator.agent.md |
  .github/agents/adapter-orchestrator.agent.md |
  .github/agents/infrastructure-orchestrator.agent.md]`

**Routing rationale:** [explain why this sub-team owns the repair]

---

## Reported By

**Reporting agent:** [code-reviewer / unit-test-engineer / integration-test-engineer / e2e-test-engineer / security-reviewer / performance-analyst]

---

## Verification Steps Required

After repair, the following QA steps must be re-run before this defect is closed:

- [verification step 1 - e.g., "Re-run unit tests for OrderAggregate"]
- [verification step 2]

> The QA Orchestrator will not mark the defect as resolved until all listed
> verification steps pass.
