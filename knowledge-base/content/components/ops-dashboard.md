# Component: ops_dashboard

**Location:** `apps/ops_dashboard/`
**Status:** Complete - domain layer, REST API, background tasks, React frontend
**Bounded Context:** Business Operations Intelligence
**Architecture Pattern:** Clean Architecture with domain-ORM split; domain services for cross-entity operations
**Related ADRs:** [ADR 0007](../decisions/0007-ops-dashboard-alert-evaluation-architecture.md)

---

## Responsibility

The ops_dashboard bounded context is an internal staff-only analytics tool that turns
raw business data into actionable KPIs, time-series charts, and automated threshold
alerts. It owns the data model for company metrics, revenue and growth snapshots, alert
rules, triggered alerts, and an append-only audit log.

The context spans a full Clean Architecture domain layer, a Django REST Framework API
restricted to staff users, a React frontend at `/dashboard/*`, and two Django Q2
background tasks for scheduled alert evaluation and CSV metric import processing.

---

## Domain Model

### Entities

| Entity | Primary Identity | Key Invariant |
|---|---|---|
| `CompanyMetric` | `UUID` | name must not be blank |
| `RevenueSnapshot` | `UUID` | amount >= 0; currency is 3-letter ISO 4217; period_end >= period_start |
| `CustomerGrowthSnapshot` | `UUID` | new_customers >= 0; churned_customers >= 0; net_customers == new_customers - churned_customers |
| `AlertRule` | `UUID` | name must not be blank; transitions: ACTIVE <-> PAUSED |
| `DashboardAlert` | `UUID` | transitions: ACTIVE -> ACKNOWLEDGED -> RESOLVED; ACTIVE -> RESOLVED |
| `AuditLogEntry` | `UUID` | append-only; no update or delete methods |

### Value Objects

| Value Object | Type | Values |
|---|---|---|
| `MetricType` | `str, Enum` | `revenue`, `customer_growth`, `custom` |
| `ThresholdOperator` | `str, Enum` | `gt`, `lt`, `gte`, `lte`, `eq` |
| `AlertSeverity` | `str, Enum` | `info`, `warning`, `critical` |
| `AlertStatus` | `str, Enum` | `active`, `acknowledged`, `resolved` |
| `AlertRuleStatus` | `str, Enum` | `active`, `paused` |
| `AuditAction` | `str, Enum` | `metric_created`, `metric_updated`, `alert_acknowledged`, `alert_resolved`, `rule_created`, `rule_paused`, `rule_activated`, `import_started`, `import_completed`, `import_failed` |
| `ImportStatus` | `str, Enum` | `pending`, `processing`, `complete`, `failed` |
| `DateRange` | frozen dataclass | end_date >= start_date |
| `PeriodDelta` | frozen dataclass | current_value, prior_value; computed delta and pct_change |

### Alert State Machine

```
ACTIVE -> ACKNOWLEDGED    (acknowledge, requires actor UUID)
ACTIVE -> RESOLVED        (resolve, requires actor UUID)
ACKNOWLEDGED -> RESOLVED  (resolve, requires actor UUID)
```

### AlertRule State Machine

```
ACTIVE -> PAUSED          (pause, requires actor UUID)
PAUSED -> ACTIVE          (activate, requires actor UUID)
```

### Domain Events

| Event | Emitted By | Key Fields |
|---|---|---|
| `MetricSnapshotRecorded` | `RecordRevenueSnapshot`, `RecordGrowthSnapshot` use cases | metric_id, snapshot_id, snapshot_type |
| `AlertTriggered` | `AlertEvaluationService.evaluate_rule` | alert_id, rule_id, triggered_value, threshold_value, severity |
| `AlertAcknowledged` | `DashboardAlert.acknowledge` | alert_id, acknowledged_by |
| `AlertResolved` | `DashboardAlert.resolve` | alert_id, resolved_by |
| `AlertRulePaused` | `AlertRule.pause` | rule_id, paused_by |
| `AlertRuleActivated` | `AlertRule.activate` | rule_id, activated_by |

---

## Domain Services

### `AlertEvaluationService`

Evaluates all active `AlertRule` objects against the most recent metric snapshot for
each rule's associated `CompanyMetric`. Returns a new `DashboardAlert` for each rule
whose threshold is crossed and for which no ACTIVE alert already exists. Receives
`MetricRepository`, `AlertRuleRepository`, and `DashboardAlertRepository` via
constructor injection. Has zero Django dependencies.

This is a domain service rather than a method on `AlertRule` because evaluation crosses
two entity boundaries: it must read the latest snapshot for a metric and check existing
alert state. Neither entity alone has enough information to perform the check.

### `MetricAggregationService`

Computes period-over-period deltas and rolling statistics across revenue and growth
snapshot series. Used by the `GetMetricSeries` use case to annotate the time-series
response with `PeriodDelta` objects. Receives `MetricRepository` via constructor
injection. Has zero Django dependencies.

---

## Application Layer Use Cases

| Use Case Class | Command / Query | Audit Action Emitted |
|---|---|---|
| `CreateCompanyMetric` | `CreateCompanyMetricCommand` | `METRIC_CREATED` |
| `UpdateCompanyMetric` | `UpdateCompanyMetricCommand` | `METRIC_UPDATED` |
| `ListMetrics` | `ListMetricsQuery` | - |
| `RecordRevenueSnapshot` | `RecordRevenueSnapshotCommand` | - |
| `RecordGrowthSnapshot` | `RecordGrowthSnapshotCommand` | - |
| `GetMetricSeries` | `GetMetricSeriesQuery` | - |
| `CreateAlertRule` | `CreateAlertRuleCommand` | `RULE_CREATED` |
| `UpdateAlertRule` | `UpdateAlertRuleCommand` | - |
| `DeleteAlertRule` | `DeleteAlertRuleCommand` | - |
| `PauseAlertRule` | `PauseAlertRuleCommand` | `RULE_PAUSED` |
| `ActivateAlertRule` | `ActivateAlertRuleCommand` | `RULE_ACTIVATED` |
| `ListAlertRules` | `ListAlertRulesQuery` | - |
| `ListActiveAlerts` | `ListActiveAlertsQuery` | - |
| `AcknowledgeAlert` | `AcknowledgeAlertCommand` | `ALERT_ACKNOWLEDGED` |
| `ResolveAlert` | `ResolveAlertCommand` | `ALERT_RESOLVED` |
| `ListAuditLog` | `ListAuditLogQuery` | - |

All state-changing use cases write an `AuditLogEntry` via a `_log()` helper to maintain
an immutable audit trail.

---

## API Endpoints

**Base URL:** `/api/dashboard/`
**Authentication:** `Authorization: Token <token>` (DRF TokenAuthentication)
**Permissions:** `IsStaffUser` on all viewsets - no client-tier access

| Method | Path | Description |
|---|---|---|
| `GET, POST` | `/api/dashboard/metrics/` | List all company metrics; create a new metric |
| `GET, PUT, PATCH, DELETE` | `/api/dashboard/metrics/<id>/` | Retrieve, update, or delete a metric |
| `GET` | `/api/dashboard/metrics/<id>/series/` | Time-series snapshots for a metric; requires `start_date` and `end_date` query params (YYYY-MM-DD) |
| `GET` | `/api/dashboard/metrics/<id>/export/` | Stream metric snapshots as CSV; optional `start_date` / `end_date` filter |
| `GET, POST` | `/api/dashboard/revenue-snapshots/` | List or create revenue snapshots |
| `GET, PUT, PATCH, DELETE` | `/api/dashboard/revenue-snapshots/<id>/` | Retrieve, update, or delete a revenue snapshot |
| `GET, POST` | `/api/dashboard/growth-snapshots/` | List or create customer growth snapshots |
| `GET, PUT, PATCH, DELETE` | `/api/dashboard/growth-snapshots/<id>/` | Retrieve, update, or delete a growth snapshot |
| `GET, POST` | `/api/dashboard/alert-rules/` | List alert rules; create a new rule |
| `GET, PUT, PATCH, DELETE` | `/api/dashboard/alert-rules/<id>/` | Retrieve, update, or delete a rule |
| `POST` | `/api/dashboard/alert-rules/<id>/pause/` | Pause an ACTIVE alert rule |
| `POST` | `/api/dashboard/alert-rules/<id>/activate/` | Activate a PAUSED alert rule |
| `GET` | `/api/dashboard/alerts/` | List active (non-resolved) alerts |
| `GET` | `/api/dashboard/alerts/<id>/` | Retrieve a specific alert |
| `POST` | `/api/dashboard/alerts/<id>/acknowledge/` | Acknowledge an ACTIVE alert |
| `POST` | `/api/dashboard/alerts/<id>/resolve/` | Resolve an ACTIVE or ACKNOWLEDGED alert |
| `GET` | `/api/dashboard/audit-log/` | List audit log entries (read-only) |
| `GET` | `/api/dashboard/audit-log/<id>/` | Retrieve a specific audit log entry (read-only) |

**Notes on special endpoints:**

- The `series` action returns a nested object with `metric`, `revenue_snapshots`, and
  `growth_snapshots` arrays. All dates are ISO 8601 strings. Amounts are stringified
  decimals. Both `start_date` and `end_date` are required; omitting either returns HTTP 400.
- The `export` action returns a `StreamingHttpResponse` with `Content-Type: text/csv`.
  A `Content-Disposition` header names the file `metrics-<id>.csv`. `start_date` and
  `end_date` are optional; they default to the full available history.
- `DashboardAlertViewSet` is deliberately read-only on the list/retrieve actions.
  Acknowledge and resolve are custom `POST` actions only - there is no `POST /alerts/`
  create route.
- `AuditLogEntryViewSet` uses `ReadOnlyModelViewSet` - no write endpoints are exposed.
- PATCH on `metrics/<id>/` requires the `name` field even for partial updates (full PUT
  semantics are enforced on both PUT and PATCH). See known limitations.

---

## Layer Structure

```
apps/ops_dashboard/
    domain/
        __init__.py
        model.py          - Entity dataclasses; invariants and state transitions
        value_objects.py  - Enums and frozen dataclasses (DateRange, PeriodDelta)
        events.py         - Domain event definitions (6 events)
        repositories.py   - Abstract repository interfaces (ABCs)
        services.py       - AlertEvaluationService, MetricAggregationService
    application/
        __init__.py
        dtos.py           - Command, query, and DTO dataclasses (no Django imports)
        use_cases.py      - 16 use case classes (one class per operation)
    infrastructure/
        __init__.py
        permissions.py    - IsStaffUser (DRF BasePermission)
        repositories.py   - DjangoXxxRepository implementations (4 concrete classes)
        serializers.py    - DRF ModelSerializer classes (6)
        viewsets.py       - 6 DRF viewsets; 2 custom actions (series, export) on CompanyMetricViewSet
    models.py             - Django ORM models (6 models mirroring the domain layer)
    api_urls.py           - DRF DefaultRouter; 6 registered endpoints
    tasks.py              - Django Q2 tasks: evaluate_alert_rules, process_metric_import
    apps.py
    migrations/           - Django migration history
```

---

## Key Design Decisions

### 1. AlertEvaluationService is a domain service, not a model method

Alert evaluation requires reading the most recent snapshot for a `CompanyMetric` and
checking whether an ACTIVE alert already exists for the rule. This information spans
two entity boundaries (`AlertRule` and the snapshot entities). Neither entity alone
can perform the check without knowing about the other. A domain service is the correct
DDD pattern for logic that crosses aggregate boundaries. See
[ADR 0007](../decisions/0007-ops-dashboard-alert-evaluation-architecture.md).

### 2. Q2 polling (every 15 minutes) instead of signal-driven evaluation

Hooking alert evaluation onto the `post_save` signal of `RevenueSnapshot` would couple
the write path to the evaluation path. A slow or failing evaluation would cascade into
a slow or failing save. Django Q2 is already configured for the project (see
`client_portal` background tasks). Using a scheduled Q2 task decouples evaluation from
the write path entirely. For an internal staff tool, 15-minute alert lag is acceptable.
WebSocket push can be layered on later without changing the domain service.

### 3. IsStaffUser on all endpoints

The ops_dashboard is an internal tool with no client-facing surface. Applying
`IsStaffUser` on every viewset eliminates any possibility of a client user reaching
metrics, alert rules, or audit log data. There is no tiered permission model because
there is only one tier: staff.

### 4. AuditLogEntry is append-only

The `AuditLogEntry` entity has no update or delete methods. The
`AuditLogEntryViewSet` uses `ReadOnlyModelViewSet` - there are no PUT, PATCH, or
DELETE endpoints. This preserves audit trail integrity: a log entry, once written,
cannot be modified or erased through the API.

### 5. CSV import deferred to background task

The `process_metric_import` Q2 task receives an `import_id` and retrieves the CSV
data from Django's cache layer. This prevents HTTP timeout on large CSV files by
returning immediately with an `ImportStatus.PENDING` response and doing the
parsing, validation, and database writes in the background worker.

---

## Background Tasks

**Runner:** Django Q2 (`django-q2`); broker: MySQL (same database as application)
**Worker entry point:** `Dockerfile.worker` runs `manage.py qcluster`

| Task | Module | Trigger |
|---|---|---|
| `evaluate_alert_rules` | `apps/ops_dashboard/tasks.py` | Scheduled by Q2 every 15 minutes |
| `process_metric_import` | `apps/ops_dashboard/tasks.py` | Queued on demand when a CSV import is initiated |

---

## React Frontend

**Base route:** `/dashboard/*` (staff-only, behind `ProtectedRoute`)

### Page Components

| Component | Route | Description |
|---|---|---|
| `DashboardOverviewPage` | `/dashboard` | KPI summary cards showing current period revenue, customer growth, and net customers with period-over-period delta indicators |
| `DashboardMetricsPage` | `/dashboard/metrics` | Full metric list with date-range picker; line/bar charts rendered via `recharts`; CSV export button per metric |
| `DashboardAlertsPage` | `/dashboard/alerts` | Active and acknowledged alert list; acknowledge and resolve actions inline |

### Layout

`DashboardLayout` is the shared shell for all three dashboard pages. It renders the
top navigation bar (using `StackedLayout` from Catalyst UI Kit) and wraps page content
in a consistent padding and max-width container.

### New Catalyst UI Kit Components

Four new components were added to `frontend/src/components/catalyst-ui-kit/typescript/`
as part of this ticket. They follow the existing Catalyst Kit patterns (Tailwind-based,
typed props, no business logic):

| Component | File | Props | Purpose |
|---|---|---|---|
| `KpiCard` | `kpi-card.tsx` | `label`, `value`, `delta?`, `trend?` (`'up' \| 'down' \| 'neutral'`), `className?` | Single KPI display with optional delta indicator colored by trend direction |
| `KpiGrid` | `kpi-grid.tsx` | `children`, `className?` | Responsive 1/2/3-column grid for laying out multiple `KpiCard` instances |
| `PageSection` | `page-section.tsx` | `heading?`, `children`, `className?` | Semantic `<section>` wrapper with an optional bold heading; used to group related content within a page |
| `ChartContainer` | `chart-container.tsx` | `children`, `height?` (default 300), `className?` | Styled container for `recharts` chart components; enforces consistent border, background, and padding |

---

## Repository Interfaces

| Interface | Key Methods |
|---|---|
| `MetricRepository` | `get_by_id`, `save`, `list_all`, `get_revenue_snapshots`, `get_growth_snapshots`, `save_revenue_snapshot`, `save_growth_snapshot` |
| `AlertRuleRepository` | `get_by_id`, `save`, `delete`, `list_active` |
| `DashboardAlertRepository` | `get_by_id`, `save`, `list_active`, `get_active_for_rule` |
| `AuditLogRepository` | `save`, `list_all` |

---

## Known Limitations and Future Work

- **PATCH requires `name`:** Full PUT semantics are enforced on both PUT and PATCH for
  `CompanyMetricViewSet`. API consumers must include `name` even on partial updates.
  This is a backlog item to add proper partial-update support.
- **`actor_id` type mismatch:** `AuditLogEntry.actor_id` is typed as `UUID` in the
  domain model but receives a Django integer pk at runtime. The repository layer casts
  to int before writing to the ORM. A future cleanup task would standardize actor
  identification across all bounded contexts.
- **`GetMetricSeries` loads all snapshots into memory:** The use case fetches all
  `RevenueSnapshot` and `CustomerGrowthSnapshot` records for the requested date range
  into memory. For large datasets, pagination or streaming would be needed. Acceptable
  at current portfolio data volumes.
- **WebSocket push alerts not yet implemented:** The alert evaluation result currently
  only writes to the database; there is no push notification to the React frontend.
  Django Channels infrastructure is already in place (from `client_portal`). Wiring
  `AlertEvaluationService` output to a Channels group send is the natural next step.
- **`AlertNotificationPort` is not yet implemented:** The domain has a placeholder for
  an outbound notification port (email, Slack, webhook) triggered when an alert fires.
  The Q2 task logs triggered alerts but does not send any external notification.
- **`GetMetricSeries` lacks pagination:** For metrics with many years of snapshot
  history, the series endpoint returns all records in a single response. Adding
  `limit` / `offset` or cursor-based pagination is the recommended next step.
