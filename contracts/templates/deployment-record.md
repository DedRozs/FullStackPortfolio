# Deployment Record

<!-- This artifact is produced by the Deployment Orchestrator at the close of Stage 7.
     It records the paths of all deployment deliverables and the Gate-7 readiness status.
     Gate 7 passes only when deploymentStatus is 'ready-for-deployment'.
     Validate against: contracts/schemas/deployment-record.schema.json -->

**Schema version:** 1.0
**Project name:** This Project
**Produced by:** `.github/agents/deployment-orchestrator.agent.md`
**Consumed by:** `git-workflow-manager` (completionMode) and `archive-manager`

---

## Schema Version

Record the schema version used: `1.0`

---

## Project Name

State the full project name as configured in `This Project`.

---

## Deployment Date

Record the ISO 8601 date on which this deployment record was produced (e.g., `2026-05-11`).

---

## CI/CD Pipeline Configuration

<!-- Produced by: ci-cd-engineer -->

| Field | Value |
|---|---|
| Pipeline config path | [relative path to CI/CD pipeline configuration document] |

---

## Environment Configuration

<!-- Produced by: environment-configurator -->

| Field | Value |
|---|---|
| Environments config path | [relative path to environment configuration document] |

---

## Release Plan

<!-- Produced by: release-coordinator -->

| Field | Value |
|---|---|
| Release plan path | [relative path to release plan document] |

---

## Monitoring Configuration

<!-- Produced by: monitoring-configurator -->

| Field | Value |
|---|---|
| Monitoring config path | [relative path to monitoring configuration document] |

---

## Health Check Validation

<!-- Produced by: health-check-validator -->

| Field | Value |
|---|---|
| Health check path | [relative path to health check validation document] |

---

## Rollback Plan

<!-- Produced by: rollback-planner -->

| Field | Value |
|---|---|
| Rollback plan path | [relative path to rollback procedures document] |

---

## Deployment Status

<!-- Gate-7 sign-off. Must be 'ready-for-deployment' for Gate 7 to pass. -->

**Status:** [ready-for-deployment | blocked]

**Blocking reason:** [Required if status is 'blocked'. Describe what is blocking deployment and which specialist must resolve it. Omit this line if status is 'ready-for-deployment'.]

---

## Ticket Key

<!-- Optional. Present only in namespaced-run mode (implement-ticket pipeline). -->

**Ticket key:** [e.g., TT-42, or omit this section if not applicable]
