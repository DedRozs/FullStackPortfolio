# ADR 0007: ops_dashboard Alert Evaluation Architecture

**Status:** Accepted
**Date:** 2026-05-29
**Deciders:** Joseph Prince
**Technical Story:** FSP-4 - ops_dashboard Business Operations Dashboard

---

## Context

The ops_dashboard needs to evaluate `AlertRule` objects against the most recent metric
snapshots and create `DashboardAlert` records whenever a threshold is crossed. Three
implementation options were considered:

1. **Model method on `AlertRule`:** Add an `evaluate(snapshot)` method directly to the
   `AlertRule` entity. The entity would receive a snapshot value, compare it against its
   own threshold, and return a boolean.

2. **Django signal on snapshot save:** Hook a `post_save` signal on `RevenueSnapshot`
   (and `CustomerGrowthSnapshot`) to trigger evaluation every time a new snapshot is
   saved.

3. **Domain service + Q2 scheduled polling:** Implement `AlertEvaluationService` as a
   domain service that evaluates all active rules on demand, and invoke it from a Django
   Q2 task scheduled to run every 15 minutes.

---

## Decision

Implement alert evaluation as a domain service (`AlertEvaluationService`) invoked by a
Django Q2 scheduled task (`evaluate_alert_rules`) that runs every 15 minutes.

`AlertEvaluationService` is constructor-injected with `MetricRepository`,
`AlertRuleRepository`, and `DashboardAlertRepository`. It has zero Django imports.
The Q2 task instantiates the service with concrete Django repository implementations
and calls `evaluate_all_rules()`.

---

## Options Considered

### Option 1: Model method on AlertRule

Add `AlertRule.evaluate(current_value: Decimal) -> bool` and let the caller decide
whether to create an alert.

**Rejected.** The entity method only tests whether a threshold is crossed. The caller
still needs to fetch the latest snapshot, check whether an ACTIVE alert already exists
for the rule, and create the `DashboardAlert` if not. This logic spans two entity
boundaries (AlertRule and the snapshot / existing alert state). It cannot live on a
single entity without giving that entity access to repository interfaces, which would
violate the domain model's zero-dependency rule.

### Option 2: Django signal on snapshot save

Connect a `post_save` receiver to `RevenueSnapshot` and `CustomerGrowthSnapshot` that
triggers evaluation for every rule associated with the saved metric.

**Rejected.** Signal handlers run synchronously in the save transaction. A slow
evaluation (many rules, slow repository queries) would delay every snapshot write.
A failing evaluation (exception in the signal handler) would potentially roll back the
snapshot save. Fan-out to many rules per metric compounds both risks. Signals also make
the write path non-obvious and harder to test in isolation.

### Option 3: Domain service + Q2 scheduled polling (chosen)

Encapsulate all cross-entity evaluation logic in `AlertEvaluationService`. Schedule it
via Q2 every 15 minutes. The write path (saving a snapshot) is completely decoupled
from the evaluation path.

**Chosen.** The domain service pattern is the correct DDD construct for operations that
cross aggregate boundaries. Q2 is already configured for the project. The 15-minute
evaluation window is acceptable for an internal staff tool.

---

## Rationale

1. **Crosses entity boundaries.** Evaluation must read a `RevenueSnapshot` (or
   `CustomerGrowthSnapshot`) and check an existing `DashboardAlert`, then potentially
   create a new `DashboardAlert`. No single entity owns all three of these. A domain
   service with repository interfaces is the correct construct.

2. **Q2 polling decouples evaluation from the write path.** Snapshot saves are fast and
   transactionally simple. Evaluation is deliberately asynchronous. Failures in the
   evaluation task (a bad rule configuration, a transient DB error) do not affect the
   ability to record new snapshots.

3. **Q2 is already configured.** The `client_portal` app already registers Django Q2
   tasks and runs a worker via `Dockerfile.worker`. Adding a new scheduled task requires
   one `Schedule` record and one Python function.

4. **WebSocket push can be layered on later.** If a future iteration requires sub-minute
   alert delivery, the `AlertEvaluationService` can remain unchanged. The Q2 task can be
   modified to publish to a Django Channels group after calling `evaluate_all_rules()`.
   The domain service does not need to know about the delivery mechanism.

---

## Consequences

### Positive

- `AlertEvaluationService` is fully unit-testable with mock repositories; no Django
  test database required.
- The snapshot save path has no evaluation overhead.
- Future migrations to event-driven delivery (Channels push, webhook) do not require
  changes to the domain service.
- Alert deduplication (no ACTIVE alert created if one already exists for the rule) is
  enforced at the domain service level, independent of the scheduling mechanism.

### Negative / Trade-offs

- **15-minute evaluation lag.** Alerts triggered between evaluation windows are not
  raised until the next run. For an internal staff dashboard this is acceptable. For
  sub-minute SLAs a different architecture would be required.
- **Minor polling DB load.** Every 15 minutes the Q2 task queries all active rules and
  their associated snapshots. At portfolio data volumes (a few dozen rules and hundreds
  of snapshots) this is negligible. At large scale, incremental evaluation (only rules
  whose metric has new snapshots since the last run) would reduce load.
- **Schedule must be created manually or via a migration.** The Q2 `Schedule` record
  is not created by a Django migration; it must be seeded. The seed script and runbook
  document how to create it.
