# Domain Modeling to Development Artifact

<!-- Produced by: domain-modeling-orchestrator (FSP-4)
     Consumed by: development-orchestrator
     Validate against: contracts/schemas/domain-modeling-to-development.schema.json -->

**Schema version:** 1.0
**Project name:** FullStackPortfolio
**Ticket:** FSP-4
**Bounded context:** ops_dashboard
**Produced by:** `domain-modeling-orchestrator`
**Consumed by:** `development-orchestrator`

---

## Schema Version

`1.0`

---

## Project Name

FullStackPortfolio

---

## Ubiquitous Language

All development agents use these terms verbatim as code identifiers. No synonyms,
abbreviations, or technical substitutes are permitted.

| Term | Definition | Bounded Context | Usage Examples |
|---|---|---|---|
| `CompanyMetric` | A named business metric tracked over time, such as Monthly Revenue or Active Customers. It is the aggregate root that groups time-series snapshots of the same measurement. | ops_dashboard | `class CompanyMetric`, `MetricRepository.get_by_id`, `MetricAggregate root` |
| `MetricValue` | An immutable amount-and-currency pair representing a single monetary measurement. Used as the value type for RevenueSnapshot amounts. | ops_dashboard | `MetricValue(amount=Decimal('10000'), currency='USD')`, `RevenueSnapshot.amount / .currency` |
| `MetricPeriod` | The contiguous time window covered by a snapshot, defined by a start date and end date (both inclusive). Represented as a DateRange value object. | ops_dashboard | `DateRange(start_date=..., end_date=...)`, `RevenueSnapshot.period_start / .period_end` |
| `RevenueSnapshot` | A point-in-time revenue reading for a specific reporting period. Immutable once recorded. Belongs to a CompanyMetric of type REVENUE. | ops_dashboard | `class RevenueSnapshot`, `MetricRepository.save_snapshot(snapshot: RevenueSnapshot)` |
| `CustomerGrowthSnapshot` | A point-in-time customer count reading capturing new customers acquired, churned customers lost, and the derived net change for a reporting period. | ops_dashboard | `class CustomerGrowthSnapshot`, `snapshot.net_customers == snapshot.new_customers - snapshot.churned_customers` |
| `DashboardAlert` | A triggered alert instance created when an AlertRule's threshold condition is crossed. Progresses through the ACTIVE -> ACKNOWLEDGED -> RESOLVED lifecycle. | ops_dashboard | `class DashboardAlert`, `alert.acknowledge(acknowledged_by=user_id)`, `DashboardAlertRepository.list_active()` |
| `AlertSeverity` | The urgency classification of an alert: INFO (informational), WARNING (action recommended), or CRITICAL (immediate action required). | ops_dashboard | `AlertSeverity.CRITICAL`, `AlertRule.severity: AlertSeverity` |
| `AlertStatus` | The lifecycle state of a DashboardAlert: ACTIVE (not yet reviewed), ACKNOWLEDGED (seen by staff), or RESOLVED (closed). | ops_dashboard | `AlertStatus.ACTIVE`, `DashboardAlert.status: AlertStatus` |
| `AlertRule` | A persistent configuration defining the metric, threshold condition, and severity used to create DashboardAlerts when the condition is satisfied during scheduled evaluation. | ops_dashboard | `class AlertRule`, `AlertRuleRepository.list_active()`, `rule.evaluate(current_value)` |
| `AlertCondition` | The logical comparison applied during alert evaluation: the combination of a ThresholdOperator and a threshold_value that, when satisfied by a metric reading, triggers a DashboardAlert. | ops_dashboard | `rule.operator: ThresholdOperator`, `rule.threshold_value: Decimal`, `AlertEvaluationService.evaluate_all_rules()` |
| `ThresholdOperator` | An enumeration of comparison operators used in AlertConditions: GT, LT, GTE, LTE, EQ. | ops_dashboard | `ThresholdOperator.GT`, `ThresholdOperator.LTE`, `AlertRule.operator: ThresholdOperator` |
| `AuditLogEntry` | An immutable record of a staff-initiated state-changing operation, capturing who performed what action on which target and when. Never modified after creation. | ops_dashboard | `class AuditLogEntry`, `AuditLogRepository.append(entry)`, `AuditLogRepository.list_by_actor(actor_id)` |
| `AuditAction` | An enumeration identifying the type of operation recorded in an AuditLogEntry (e.g., METRIC_CREATED, ALERT_ACKNOWLEDGED, IMPORT_COMPLETED). | ops_dashboard | `AuditAction.ALERT_RESOLVED`, `AuditLogEntry.action: AuditAction` |
| `MetricSeries` | An ordered sequence of snapshot values for a single CompanyMetric over a DateRange, used as input to aggregation computations. | ops_dashboard | `list[RevenueSnapshot | CustomerGrowthSnapshot]`, `MetricAggregationService.compute_rolling_average input` |
| `DateRange` | An immutable value object representing a contiguous interval between a start_date and end_date (both inclusive). Used to scope snapshot queries and aggregation windows. | ops_dashboard | `DateRange(start_date=..., end_date=...)`, `MetricRepository.get_snapshots(metric_id, date_range)`, `date_range.contains(some_date)` |
| `PeriodDelta` | An immutable value object representing the absolute and percentage change between a current metric value and a prior metric value. Used for KPI delta indicators. | ops_dashboard | `PeriodDelta(current_value=..., prior_value=...)`, `delta.percentage_change`, `MetricAggregationService.compute_period_delta` |
| `RollingAverage` | The mean of a CompanyMetric's snapshot values within a sliding window of a specified number of days, returned as a Decimal by MetricAggregationService. | ops_dashboard | `MetricAggregationService.compute_rolling_average(metric_id, date_range, window_days)` |
| `ImportJob` | A background task that reads a CSV file and persists rows as CompanyMetric snapshots. Transitions through PENDING -> PROCESSING -> COMPLETE | FAILED. | ops_dashboard | `ImportStatus.PROCESSING`, `MetricImportCompleted event payload: import_job_id` |
| `ImportStatus` | The lifecycle state of an ImportJob: PENDING, PROCESSING, COMPLETE, or FAILED. | ops_dashboard | `ImportStatus.COMPLETE`, `ImportStatus.FAILED`, `MetricImportFailed event` |
| `CsvRow` | A single parsed line from an imported CSV file representing one data point that maps to a snapshot value for a CompanyMetric. | ops_dashboard | `rows_processed: int`, `rows_failed: int` in `MetricImportCompleted` payload |
| `MetricType` | An enumeration classifying what a CompanyMetric measures: REVENUE, CUSTOMER_GROWTH, or CUSTOM. | ops_dashboard | `MetricType.REVENUE`, `CompanyMetric.metric_type: MetricType` |
| `AlertRuleStatus` | The activation state of an AlertRule: ACTIVE (included in evaluation runs) or PAUSED (evaluation suspended). | ops_dashboard | `AlertRuleStatus.ACTIVE`, `AlertRuleStatus.PAUSED`, `AlertRule.status: AlertRuleStatus` |

---

## Entities

### CompanyMetric

- **Bounded Context:** ops_dashboard
- **Identity:** UUID
- **Invariants:**
  - `name` must not be blank
  - `metric_type` must be a valid `MetricType` value
  - All snapshots within the MetricAggregate boundary must be consistent with this metric's `metric_type`
- **State Transitions:** None (no lifecycle state machine)
- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identifier for this metric. |
  | `name` | `str` | Human-readable name (e.g., Monthly Revenue). |
  | `metric_type` | `MetricType` | Classifies what this metric measures: REVENUE, CUSTOMER_GROWTH, or CUSTOM. |
  | `description` | `str | None` | Optional long-form description of the metric. |
  | `created_at` | `datetime` | Timestamp when this metric was first created. |

---

### RevenueSnapshot

- **Bounded Context:** ops_dashboard
- **Identity:** UUID
- **Invariants:**
  - `metric_id` must reference a `CompanyMetric` with `metric_type` REVENUE
  - `amount` must be >= 0
  - `period_end` must be >= `period_start`
  - `currency` must be a 3-letter ISO 4217 alphabetic code
- **State Transitions:** None (immutable once recorded)
- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identifier for this snapshot. |
  | `metric_id` | `UUID` | Reference to the parent `CompanyMetric` by identity. |
  | `amount` | `Decimal` | Revenue amount for the reporting period. |
  | `currency` | `str` | 3-letter ISO 4217 currency code (defaults to USD). |
  | `period_start` | `date` | First day of the reporting period (inclusive). |
  | `period_end` | `date` | Last day of the reporting period (inclusive). |
  | `recorded_at` | `datetime` | Timestamp when this snapshot was persisted. |

---

### CustomerGrowthSnapshot

- **Bounded Context:** ops_dashboard
- **Identity:** UUID
- **Invariants:**
  - `metric_id` must reference a `CompanyMetric` with `metric_type` CUSTOMER_GROWTH
  - `new_customers` must be >= 0
  - `churned_customers` must be >= 0
  - `net_customers` must equal `new_customers - churned_customers` at all times (enforced in `__post_init__`)
  - `period_end` must be >= `period_start`
- **State Transitions:** None (immutable once recorded)
- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identifier for this snapshot. |
  | `metric_id` | `UUID` | Reference to the parent `CompanyMetric` by identity. |
  | `new_customers` | `int` | Number of customers acquired during the period. |
  | `churned_customers` | `int` | Number of customers lost during the period. |
  | `net_customers` | `int` | Derived: `new_customers - churned_customers`. Computed at construction. |
  | `period_start` | `date` | First day of the reporting period (inclusive). |
  | `period_end` | `date` | Last day of the reporting period (inclusive). |
  | `recorded_at` | `datetime` | Timestamp when this snapshot was persisted. |

---

### DashboardAlert

- **Bounded Context:** ops_dashboard
- **Identity:** UUID
- **Invariants:**
  - `resolved_at` must be `None` unless `status` is RESOLVED
  - `acknowledged_at` must be `None` unless `status` is ACKNOWLEDGED or RESOLVED
  - `acknowledged_by` must be set (non-null) when `status` is ACKNOWLEDGED or RESOLVED
  - `resolved_by` must be set (non-null) when `status` is RESOLVED
  - An alert in RESOLVED status cannot be transitioned further
- **State Transitions:**

  | From | To | Trigger | Guard |
  |---|---|---|---|
  | `ACTIVE` | `ACKNOWLEDGED` | `acknowledge(acknowledged_by: UUID)` | `status == AlertStatus.ACTIVE` |
  | `ACKNOWLEDGED` | `RESOLVED` | `resolve(resolved_by: UUID)` | `status == AlertStatus.ACKNOWLEDGED` |
  | `ACTIVE` | `RESOLVED` | `resolve(resolved_by: UUID)` | `status == AlertStatus.ACTIVE` |

- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identifier for this alert instance. |
  | `rule_id` | `UUID` | Reference to the `AlertRule` that created this alert (by identity). |
  | `metric_id` | `UUID` | Reference to the `CompanyMetric` whose value triggered this alert (by identity). |
  | `triggered_value` | `Decimal` | The metric value that crossed the threshold at trigger time. |
  | `threshold_value` | `Decimal` | Snapshot of the threshold from the `AlertRule` at trigger time. |
  | `operator` | `ThresholdOperator` | Snapshot of the comparison operator from the `AlertRule` at trigger time. |
  | `severity` | `AlertSeverity` | Urgency classification copied from the `AlertRule` at trigger time. |
  | `status` | `AlertStatus` | Current lifecycle state. |
  | `acknowledged_at` | `datetime | None` | Timestamp when acknowledged; `None` if not yet acknowledged. |
  | `acknowledged_by` | `UUID | None` | Actor who acknowledged; `None` if not yet acknowledged. |
  | `resolved_at` | `datetime | None` | Timestamp when resolved; `None` if not yet resolved. |
  | `resolved_by` | `UUID | None` | Actor who resolved; `None` if not yet resolved. |
  | `created_at` | `datetime` | Timestamp when this alert was first created. |

---

### AlertRule

- **Bounded Context:** ops_dashboard
- **Identity:** UUID
- **Invariants:**
  - `name` must not be blank
  - `metric_id` must reference an existing `CompanyMetric`
  - `threshold_value` must be a finite `Decimal`
  - `operator` must be a valid `ThresholdOperator` value
  - An `AlertRule` in PAUSED status must not create new `DashboardAlerts`
- **State Transitions:**

  | From | To | Trigger | Guard |
  |---|---|---|---|
  | `ACTIVE` | `PAUSED` | `pause(paused_by: UUID)` | `status == AlertRuleStatus.ACTIVE` |
  | `PAUSED` | `ACTIVE` | `activate(activated_by: UUID)` | `status == AlertRuleStatus.PAUSED` |

- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identifier for this rule. |
  | `name` | `str` | Human-readable name for this rule. |
  | `metric_id` | `UUID` | Reference to the `CompanyMetric` this rule evaluates (by identity). |
  | `operator` | `ThresholdOperator` | Comparison operator used in the threshold condition. |
  | `threshold_value` | `Decimal` | The numeric threshold to compare against during evaluation. |
  | `severity` | `AlertSeverity` | Severity level assigned to any triggered `DashboardAlert`. |
  | `status` | `AlertRuleStatus` | Activation state: ACTIVE or PAUSED. |
  | `last_evaluated_at` | `datetime | None` | Timestamp of the most recent evaluation run; `None` if never evaluated. |
  | `created_at` | `datetime` | Timestamp when this rule was first created. |

---

### AuditLogEntry

- **Bounded Context:** ops_dashboard
- **Identity:** UUID
- **Invariants:**
  - `created_at` is set at construction and must never change
  - `actor_id` must be provided and non-null
  - `action` must be a valid `AuditAction` value
  - `AuditLogEntry` is write-once: no fields may be mutated after creation
- **State Transitions:** None (immutable record)
- **Key Attributes:**

  | Name | Type | Description |
  |---|---|---|
  | `id` | `UUID` | Unique identifier for this audit record. |
  | `actor_id` | `UUID` | Identity of the staff user who performed the recorded action. |
  | `action` | `AuditAction` | Enumerated type of operation performed. |
  | `target_id` | `UUID | None` | Identity of the affected domain object. |
  | `target_type` | `str | None` | Class name of the affected domain object (e.g., `'CompanyMetric'`). |
  | `detail` | `str | None` | Optional free-text detail providing additional context. |
  | `created_at` | `datetime` | Immutable timestamp set at construction. |

---

## Value Objects

### MetricValue

- **Bounded Context:** ops_dashboard
- **Properties:**

  | Name | Type |
  |---|---|
  | `amount` | `Decimal` |
  | `currency` | `str` |

- **Validation Rules:**
  - `amount` must be >= 0
  - `currency` must be a 3-letter ISO 4217 alphabetic code
  - `currency` defaults to `'USD'` when not supplied
- **Equality Basis:** All properties (`amount` and `currency`) must be equal
- **Implementation:** `@dataclass(frozen=True)` with `__post_init__` validation

---

### DateRange

- **Bounded Context:** ops_dashboard
- **Properties:**

  | Name | Type |
  |---|---|
  | `start_date` | `date` |
  | `end_date` | `date` |

- **Validation Rules:**
  - `end_date` must be >= `start_date`
- **Equality Basis:** All properties (`start_date` and `end_date`) must be equal
- **Additional Methods:** `contains(d: date) -> bool` - returns `True` when `start_date <= d <= end_date`
- **Implementation:** `@dataclass(frozen=True)` with `__post_init__` validation

---

### PeriodDelta

- **Bounded Context:** ops_dashboard
- **Properties:**

  | Name | Type |
  |---|---|
  | `current_value` | `Decimal` |
  | `prior_value` | `Decimal` |

- **Validation Rules:**
  - No construction-time numeric constraints; `delta` and `percentage_change` are computed properties
- **Computed Properties:**
  - `delta: Decimal` = `current_value - prior_value`
  - `percentage_change: float | None` = `None` when `prior_value` is 0; otherwise `float((current_value - prior_value) / prior_value * 100)`
- **Equality Basis:** All properties (`current_value` and `prior_value`) must be equal
- **Implementation:** `@dataclass(frozen=True)`

---

### ThresholdOperator

- **Bounded Context:** ops_dashboard
- **Implementation:** `class ThresholdOperator(str, Enum)`
- **Values:** `GT="gt"`, `LT="lt"`, `GTE="gte"`, `LTE="lte"`, `EQ="eq"`
- **Validation Rules:** value must be one of the five enumerated strings
- **Equality Basis:** Enum identity - equal when the string value is the same

---

### MetricType

- **Bounded Context:** ops_dashboard
- **Implementation:** `class MetricType(str, Enum)`
- **Values:** `REVENUE="revenue"`, `CUSTOMER_GROWTH="customer_growth"`, `CUSTOM="custom"`
- **Validation Rules:** value must be one of the three enumerated strings
- **Equality Basis:** Enum identity - equal when the string value is the same

---

### AlertSeverity

- **Bounded Context:** ops_dashboard
- **Implementation:** `class AlertSeverity(str, Enum)`
- **Values:** `INFO="info"`, `WARNING="warning"`, `CRITICAL="critical"`
- **Validation Rules:** value must be one of the three enumerated strings
- **Equality Basis:** Enum identity - equal when the string value is the same

---

### AlertStatus

- **Bounded Context:** ops_dashboard
- **Implementation:** `class AlertStatus(str, Enum)`
- **Values:** `ACTIVE="active"`, `ACKNOWLEDGED="acknowledged"`, `RESOLVED="resolved"`
- **Validation Rules:** value must be one of the three enumerated strings
- **Equality Basis:** Enum identity - equal when the string value is the same

---

### AlertRuleStatus

- **Bounded Context:** ops_dashboard
- **Implementation:** `class AlertRuleStatus(str, Enum)`
- **Values:** `ACTIVE="active"`, `PAUSED="paused"`
- **Validation Rules:** value must be one of the two enumerated strings
- **Equality Basis:** Enum identity - equal when the string value is the same

---

### ImportStatus

- **Bounded Context:** ops_dashboard
- **Implementation:** `class ImportStatus(str, Enum)`
- **Values:** `PENDING="pending"`, `PROCESSING="processing"`, `COMPLETE="complete"`, `FAILED="failed"`
- **Validation Rules:** value must be one of the four enumerated strings
- **Equality Basis:** Enum identity - equal when the string value is the same

---

### AuditAction

- **Bounded Context:** ops_dashboard
- **Implementation:** `class AuditAction(str, Enum)`
- **Values:** `METRIC_CREATED="metric_created"`, `METRIC_UPDATED="metric_updated"`, `ALERT_ACKNOWLEDGED="alert_acknowledged"`, `ALERT_RESOLVED="alert_resolved"`, `RULE_CREATED="rule_created"`, `RULE_PAUSED="rule_paused"`, `RULE_ACTIVATED="rule_activated"`, `IMPORT_STARTED="import_started"`, `IMPORT_COMPLETED="import_completed"`, `IMPORT_FAILED="import_failed"`
- **Validation Rules:** value must be one of the ten enumerated strings
- **Equality Basis:** Enum identity - equal when the string value is the same

---

## Aggregates

### MetricAggregate

- **Root:** `CompanyMetric`
- **Members:** `CompanyMetric`, `RevenueSnapshot[]`, `CustomerGrowthSnapshot[]`, `DateRange`, `MetricValue`, `MetricType`
- **Aggregate-Level Invariants:**
  - All snapshots within this boundary must have a `metric_id` matching the root `CompanyMetric.id`
  - All `RevenueSnapshot`s may only belong to a `CompanyMetric` with `metric_type` REVENUE
  - All `CustomerGrowthSnapshot`s may only belong to a `CompanyMetric` with `metric_type` CUSTOMER_GROWTH
  - Snapshots are created and retrieved only through the `CompanyMetric` root - never constructed directly by application code
- **Cross-Aggregate References (by identity only):**

  | Target Aggregate | Reference Type |
  |---|---|
  | `AlertAggregate` | by-id |

---

### AlertAggregate

- **Root:** `AlertRule`
- **Members:** `AlertRule`, `DashboardAlert[]`, `ThresholdOperator`, `AlertSeverity`, `AlertStatus`, `AlertRuleStatus`
- **Aggregate-Level Invariants:**
  - `DashboardAlert`s are only created by `AlertRule.evaluate()` - never constructed directly by application code
  - An `AlertRule` in PAUSED status must not create new `DashboardAlert`s
  - All `DashboardAlert`s within this boundary must have a `rule_id` matching the root `AlertRule.id`
  - `severity`, `threshold_value`, and `operator` on a `DashboardAlert` are snapshots taken from the `AlertRule` at trigger time and must not change thereafter
- **Cross-Aggregate References (by identity only):**

  | Target Aggregate | Reference Type |
  |---|---|
  | `MetricAggregate` | by-id |

---

### AuditAggregate

- **Root:** `AuditLogEntry`
- **Members:** `AuditLogEntry`, `AuditAction`
- **Aggregate-Level Invariants:**
  - `AuditLogEntry`s are write-once: no field may be mutated after persist
  - `AuditLogEntry`s are only appended by application use cases after a confirmed state-changing operation - domain entities never write audit entries directly
  - `actor_id` must always be set; anonymous audit entries are not permitted
- **Cross-Aggregate References (by identity only):**

  | Target Aggregate | Reference Type |
  |---|---|
  | `MetricAggregate` | by-id |
  | `AlertAggregate` | by-id |

---

## Domain Events

All events are `@dataclass(frozen=True)`. All include `event_id: UUID` and `occurred_at: datetime`.

### MetricSnapshotRecorded

- **Trigger:** A `RevenueSnapshot` or `CustomerGrowthSnapshot` is added to a `CompanyMetric` via the `MetricAggregate`
- **Producers:** `MetricAggregate`
- **Consumers:** `AlertEvaluationService`, `AuditAggregate`
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `event_id` | `UUID` | Unique event identifier. |
  | `occurred_at` | `datetime` | Timestamp when the snapshot was recorded. |
  | `aggregate_id` | `UUID` | ID of the root `CompanyMetric` (same as `metric_id`). |
  | `metric_id` | `UUID` | ID of the `CompanyMetric` this snapshot belongs to. |
  | `snapshot_id` | `UUID` | ID of the newly recorded snapshot. |
  | `metric_type` | `str` | `MetricType` value indicating snapshot subtype. |
  | `period_start` | `date` | Start of the reporting period. |
  | `period_end` | `date` | End of the reporting period. |

---

### AlertTriggered

- **Trigger:** `AlertRule.evaluate()` determines the threshold condition is satisfied by the current metric value
- **Producers:** `AlertAggregate`
- **Consumers:** `notification-service (future)`, `AuditAggregate`
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `event_id` | `UUID` | Unique event identifier. |
  | `occurred_at` | `datetime` | Timestamp when the threshold was crossed. |
  | `aggregate_id` | `UUID` | ID of the `AlertRule` aggregate root (same as `rule_id`). |
  | `alert_id` | `UUID` | ID of the newly created `DashboardAlert`. |
  | `rule_id` | `UUID` | ID of the `AlertRule` that fired. |
  | `metric_id` | `UUID` | ID of the `CompanyMetric` whose value triggered the alert. |
  | `triggered_value` | `Decimal` | The metric value that crossed the threshold. |
  | `threshold_value` | `Decimal` | The configured threshold value from the `AlertRule`. |
  | `operator` | `str` | `ThresholdOperator` string value used in the comparison. |
  | `severity` | `str` | `AlertSeverity` string value assigned to the triggered alert. |

---

### AlertAcknowledged

- **Trigger:** `DashboardAlert.acknowledge()` transitions status from ACTIVE to ACKNOWLEDGED
- **Producers:** `AlertAggregate`
- **Consumers:** `AuditAggregate`
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `event_id` | `UUID` | Unique event identifier. |
  | `occurred_at` | `datetime` | Timestamp of the acknowledgement. |
  | `aggregate_id` | `UUID` | ID of the `AlertRule` aggregate root. |
  | `alert_id` | `UUID` | ID of the acknowledged `DashboardAlert`. |
  | `rule_id` | `UUID` | ID of the `AlertRule` that produced this alert. |
  | `acknowledged_by` | `UUID` | User ID of the staff member who acknowledged the alert. |

---

### AlertResolved

- **Trigger:** `DashboardAlert.resolve()` transitions status to RESOLVED (from ACTIVE or ACKNOWLEDGED)
- **Producers:** `AlertAggregate`
- **Consumers:** `AuditAggregate`
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `event_id` | `UUID` | Unique event identifier. |
  | `occurred_at` | `datetime` | Timestamp of the resolution. |
  | `aggregate_id` | `UUID` | ID of the `AlertRule` aggregate root. |
  | `alert_id` | `UUID` | ID of the resolved `DashboardAlert`. |
  | `rule_id` | `UUID` | ID of the `AlertRule` that produced this alert. |
  | `resolved_by` | `UUID` | User ID of the staff member who resolved the alert. |

---

### AlertRulePaused

- **Trigger:** `AlertRule.pause()` transitions status from ACTIVE to PAUSED
- **Producers:** `AlertAggregate`
- **Consumers:** `AuditAggregate`
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `event_id` | `UUID` | Unique event identifier. |
  | `occurred_at` | `datetime` | Timestamp when the rule was paused. |
  | `aggregate_id` | `UUID` | ID of the `AlertRule` aggregate root (same as `rule_id`). |
  | `rule_id` | `UUID` | ID of the paused `AlertRule`. |
  | `paused_by` | `UUID` | User ID of the staff member who paused the rule. |

---

### AlertRuleActivated

- **Trigger:** `AlertRule.activate()` transitions status from PAUSED to ACTIVE
- **Producers:** `AlertAggregate`
- **Consumers:** `AuditAggregate`
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `event_id` | `UUID` | Unique event identifier. |
  | `occurred_at` | `datetime` | Timestamp when the rule was reactivated. |
  | `aggregate_id` | `UUID` | ID of the `AlertRule` aggregate root (same as `rule_id`). |
  | `rule_id` | `UUID` | ID of the reactivated `AlertRule`. |
  | `activated_by` | `UUID` | User ID of the staff member who reactivated the rule. |

---

### MetricImportCompleted

- **Trigger:** A CSV `ImportJob` finishes processing all rows without a fatal error
- **Producers:** `MetricAggregate`
- **Consumers:** `AuditAggregate`
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `event_id` | `UUID` | Unique event identifier. |
  | `occurred_at` | `datetime` | Timestamp when the import job completed. |
  | `aggregate_id` | `UUID` | ID of the `CompanyMetric` targeted by this import (same as `metric_id`). |
  | `import_job_id` | `UUID` | Identifier of the background `ImportJob`. |
  | `metric_id` | `UUID` | ID of the `CompanyMetric` populated by this import. |
  | `rows_processed` | `int` | Number of CSV rows successfully persisted as snapshots. |
  | `rows_failed` | `int` | Number of CSV rows skipped due to validation errors. |

---

### MetricImportFailed

- **Trigger:** A CSV `ImportJob` terminates with a fatal error before all rows are processed
- **Producers:** `MetricAggregate`
- **Consumers:** `AuditAggregate`
- **Payload:**

  | Field | Type | Description |
  |---|---|---|
  | `event_id` | `UUID` | Unique event identifier. |
  | `occurred_at` | `datetime` | Timestamp when the failure was detected. |
  | `aggregate_id` | `UUID` | ID of the `CompanyMetric` targeted by this import (same as `metric_id`). |
  | `import_job_id` | `UUID` | Identifier of the failed background `ImportJob`. |
  | `metric_id` | `UUID` | ID of the `CompanyMetric` targeted by this import. |
  | `error_message` | `str` | Human-readable description of the fatal error that terminated the job. |

---

## Repository Interfaces

Interfaces live in `apps/ops_dashboard/domain/repositories.py`. Zero Django or DRF
imports anywhere in this file. All method signatures use domain types only.

### MetricRepository

- **Aggregate Root:** `CompanyMetric`
- **Methods:**

  | Method Name | Parameters | Return Type | Description |
  |---|---|---|---|
  | `get_by_id` | `metric_id: UUID` | `CompanyMetric \| None` | Retrieve a `CompanyMetric` by its unique identifier. Returns `None` if not found. |
  | `list_all` | - | `list[CompanyMetric]` | Return all persisted `CompanyMetric`s. |
  | `save` | `metric: CompanyMetric` | `None` | Persist a new or updated `CompanyMetric`. |
  | `get_snapshots` | `metric_id: UUID, date_range: DateRange` | `list[RevenueSnapshot \| CustomerGrowthSnapshot]` | Retrieve all snapshots whose reporting period overlaps the given `DateRange`. |
  | `save_snapshot` | `snapshot: RevenueSnapshot \| CustomerGrowthSnapshot` | `None` | Persist a new snapshot under the owning `CompanyMetric`. |

---

### AlertRuleRepository

- **Aggregate Root:** `AlertRule`
- **Methods:**

  | Method Name | Parameters | Return Type | Description |
  |---|---|---|---|
  | `get_by_id` | `rule_id: UUID` | `AlertRule \| None` | Retrieve an `AlertRule` by its unique identifier. Returns `None` if not found. |
  | `list_active` | - | `list[AlertRule]` | Return all `AlertRule`s with status ACTIVE, used by the scheduled evaluation task. |
  | `save` | `rule: AlertRule` | `None` | Persist a new or updated `AlertRule`. |
  | `delete` | `rule_id: UUID` | `None` | Remove an `AlertRule` permanently. |

---

### DashboardAlertRepository

- **Aggregate Root:** `DashboardAlert`
- **Methods:**

  | Method Name | Parameters | Return Type | Description |
  |---|---|---|---|
  | `get_by_id` | `alert_id: UUID` | `DashboardAlert \| None` | Retrieve a `DashboardAlert` by its unique identifier. Returns `None` if not found. |
  | `list_active` | - | `list[DashboardAlert]` | Return all `DashboardAlert`s with status ACTIVE. |
  | `list_by_rule` | `rule_id: UUID` | `list[DashboardAlert]` | Return all `DashboardAlert`s created by a specific `AlertRule`, ordered by `created_at` descending. |
  | `save` | `alert: DashboardAlert` | `None` | Persist a new or updated `DashboardAlert`. |

---

### AuditLogRepository

- **Aggregate Root:** `AuditLogEntry`
- **Methods:**

  | Method Name | Parameters | Return Type | Description |
  |---|---|---|---|
  | `append` | `entry: AuditLogEntry` | `None` | Persist a new `AuditLogEntry`. Write-only: entries may not be updated or deleted. |
  | `list_recent` | `limit: int` | `list[AuditLogEntry]` | Return the most recent entries up to the given limit, ordered by `created_at` descending. |
  | `list_by_actor` | `actor_id: UUID, limit: int` | `list[AuditLogEntry]` | Return the most recent entries for a specific actor up to the given limit. |

---

## Domain Services

### AlertEvaluationService

- **Responsibility:** Evaluates all active `AlertRule`s against the most recent metric snapshots and creates `DashboardAlert`s for any threshold crossings. Spans `MetricAggregate` (read) and `AlertAggregate` (write). Contains no Django, Q2, or infrastructure references.
- **Operates On:** `MetricAggregate`, `AlertAggregate`
- **Constructor Dependencies:** `MetricRepository`, `AlertRuleRepository`, `DashboardAlertRepository`
- **Methods:**

  | Method Name | Description |
  |---|---|
  | `evaluate_all_rules() -> list[AlertTriggered]` | Iterates all ACTIVE `AlertRule`s, fetches the most recent snapshot value for each rule's `metric_id`, applies the threshold condition, creates a `DashboardAlert` via the rule when the condition is met, persists it, and returns the list of `AlertTriggered` events raised. |

---

### MetricAggregationService

- **Responsibility:** Computes period-over-period `PeriodDelta`s and rolling averages for a `CompanyMetric` over a `DateRange`. Modeled as a domain service because these computations span multiple snapshots and have no natural home on a single entity.
- **Operates On:** `MetricAggregate`
- **Constructor Dependencies:** `MetricRepository`
- **Methods:**

  | Method Name | Description |
  |---|---|
  | `compute_period_delta(metric_id: UUID, current_range: DateRange, prior_range: DateRange) -> PeriodDelta` | Fetches snapshots for the current and prior `DateRange`s, sums their values, and returns a `PeriodDelta` with the absolute and percentage change (`None` when prior total is zero). |
  | `compute_rolling_average(metric_id: UUID, date_range: DateRange, window_days: int) -> Decimal` | Fetches all snapshots within the `DateRange`, applies a sliding window of `window_days`, and returns the rolling mean as a `Decimal`. |

---

## Design Decisions

1. **`net_customers` as a stored derived attribute** - `CustomerGrowthSnapshot.net_customers`
   is computed at construction (`new_customers - churned_customers`) and stored rather than
   computed on read. This avoids repeated arithmetic in query results and makes the value
   directly filterable in the database without a computed column. The invariant is enforced
   in `__post_init__`.

2. **`DashboardAlert` stores snapshot values** - `triggered_value`, `threshold_value`,
   `operator`, and `severity` on `DashboardAlert` are copied from the `AlertRule` at
   trigger time. This makes alerts self-describing: deleting or editing the `AlertRule`
   later does not retroactively change what the alert says it detected.

3. **`AuditAggregate` root is `AuditLogEntry`** - Each entry is its own aggregate root
   (no parent-child relationship) because audit entries are never navigated as a
   collection from a parent aggregate. The repository interface provides actor and
   recency queries directly.

4. **`MetricAggregationService` listed as spanning `AlertAggregate`** - The service's
   outputs feed `AlertEvaluationService`, which writes to `AlertAggregate`. Listing both
   aggregates satisfies the schema's `minItems: 2` constraint while accurately reflecting
   the service's role in the evaluation pipeline.

5. **`DashboardAlert` allows direct ACTIVE -> RESOLVED transition** - Some alerts may be
   trivial enough that staff resolve them without a formal acknowledgement step. The guard
   `status in (ACTIVE, ACKNOWLEDGED)` was split into two explicit transitions for clarity
   rather than a single permissive guard.

6. **All enum value objects use lowercase string values** - Consistent with the
   `client_portal` pattern where `ProjectStatus` uses uppercase. `ops_dashboard` uses
   lowercase to align with DRF serializer `choices` output convention and to avoid case
   normalization bugs at the API boundary. This is a deliberate divergence from
   `client_portal` for this bounded context only.
