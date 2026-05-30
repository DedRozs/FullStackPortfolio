# Component: workflow_automation

**Location:** `apps/workflow_automation/`
**Status:** Complete - domain layer, REST API, React frontend, cross-app integrations
**Bounded Context:** Internal Workflow Automation
**Architecture Pattern:** Domain-Driven Design with Clean Architecture layers
**Related ADRs:** [ADR 0008](../decisions/0008-workflow-automation-registry-pattern.md)

---

## Responsibility

The workflow_automation bounded context provides a lightweight automation engine where
users define rules that bind a trigger type to a set of conditions and an ordered list of
actions. It is the architectural showpiece of the portfolio: a decorator-based registry
allows new triggers, conditions, and actions to be added without ever modifying the core
engine. All action side-effects execute as Django-Q2 background tasks so the trigger
call-site is non-blocking.

The context wires client_portal and ops_dashboard into a coherent ecosystem. When a
deliverable is approved in client_portal, or when a metric threshold is crossed in
ops_dashboard, `fire_trigger()` is called with the relevant payload. The engine loads all
matching enabled rules, evaluates their conditions, and dispatches their actions
asynchronously.

---

## Architecture Diagram

```
workflow_automation bounded context
============================================================

  Presentation (React SPA)
  +---------------------------------------------------------+
  | AutomationLayout (layout/AutomationLayout.tsx)          |
  | AutomationListPage  /automations                        |
  | AutomationNewPage   /automations/new                    |
  | AutomationRunsPage  /automations/:id/runs               |
  +---------------------------------------------------------+
              |  fetch() + DRF token auth
  Infrastructure (Django / DRF)
  +---------------------------------------------------------+
  | AutomationRuleViewSet (rules, enable, disable, dry_run) |
  | AutomationConditionViewSet                              |
  | AutomationActionViewSet                                 |
  | AutomationRunViewSet                                    |
  | AutomationRunLogViewSet                                 |
  | DjangoAutomationRule/Condition/Action/Run/LogRepository |
  | registry.py  - action handlers + condition evaluators   |
  | engine.py    - fire_trigger() entry point               |
  | tasks.py     - execute_automation_rule Q2 task          |
  | migrations/  - 0001_initial, 0002_add_rule_indexes      |
  +---------------------------------------------------------+
              |  domain interfaces only
  Application
  +---------------------------------------------------------+
  | EnableRule, DisableRule, DryRunRule use cases           |
  | AutomationEngineService (evaluate + dispatch)           |
  | RuleEvaluationService                                   |
  | DTOs: EnableRuleCommand, DisableRuleCommand,            |
  |        DryRunRuleCommand, DryRunRuleResult              |
  +---------------------------------------------------------+
              |  pure Python only
  Domain
  +---------------------------------------------------------+
  | Entities: AutomationRule, AutomationCondition,          |
  |           AutomationAction, AutomationRun, AutomationRunLog |
  | Value Objects: TriggerType, ConditionOperator,          |
  |                ActionType, RunStatus, TriggerContext     |
  | Repositories (interfaces): IAutomationRuleRepository,   |
  |   IAutomationConditionRepository, IAutomationActionRepository, |
  |   IAutomationRunRepository, IAutomationRunLogRepository |
  | Events: RuleFired, RuleEvaluationFailed                 |
  +---------------------------------------------------------+

  External triggers (cross-app)
  client_portal DeliverableApproved  ->  fire_trigger('deliverable.approved', ...)
  ops_dashboard check_metric_alerts  ->  fire_trigger('metric.threshold_crossed', ...)
```

---

## Domain Model

### Entities

| Entity | Identity | Key Invariants |
|---|---|---|
| `AutomationRule` | UUID | `name` must not be blank; `trigger_type` must be a valid `TriggerType`; an enabled rule must have at least one `AutomationAction` |
| `AutomationCondition` | UUID | `field_name` and `expected_value` must not be blank; `operator` must be a valid `ConditionOperator`; `rule_id` must reference an existing rule |
| `AutomationAction` | UUID | `action_type` must be a valid `ActionType`; `parameters` must not be None (empty dict is valid); `order >= 0`; `rule_id` must reference an existing rule |
| `AutomationRun` | UUID | `rule_id` must reference an existing rule; `triggered_at` must not be in the future; `completed_at >= triggered_at` when set; `error_message` must be set when `status` is `FAILURE` |
| `AutomationRunLog` | UUID | append-only; `run_id` must reference an existing run; `message` must not be blank |

### Value Objects

| Value Object | Type | Values / Invariants |
|---|---|---|
| `TriggerType` | `str, Enum` | `deliverable.approved`, `metric.threshold_crossed`, `invoice.overdue`, `file.uploaded` |
| `ConditionOperator` | `str, Enum` | `gt`, `lt`, `eq`, `contains`, `assigned_to` |
| `ActionType` | `str, Enum` | `send_email`, `create_activity_event`, `update_status`, `send_sms` |
| `RunStatus` | `str, Enum` | `pending`, `running`, `success`, `failure`, `dry_run` |
| `TriggerContext` | frozen dataclass | `trigger_type`, `source_id`, `source_type`, `payload: dict`; immutable; passed to condition evaluators and action handlers |

### AutomationRun State Machine

```
PENDING  -->  RUNNING   (start(); guard: is_dry_run is False)
RUNNING  -->  SUCCESS   (complete())
RUNNING  -->  FAILURE   (fail(error_message); guard: error_message not blank)
PENDING  -->  DRY_RUN   (mark_dry_run_complete(); guard: is_dry_run is True)
```

---

## Registry Pattern

### How it works

`registry.py` maintains two module-level dictionaries:

```python
_action_handlers: dict[str, Callable] = {}
_condition_evaluators: dict[str, Callable] = {}
```

Two decorator factories allow any function to register itself at import time:

```python
@register_action_handler(ActionType.SEND_EMAIL)
def _handle_send_email(action_params: dict, context: dict) -> str:
    ...

@register_condition_evaluator(ConditionOperator.GT)
def _eval_gt(field_value: object, expected: object) -> bool:
    ...
```

When `registry.py` is first imported, every decorated function is stored under its
`ActionType.value` or `ConditionOperator.value` string key. Handlers are retrieved by
`get_action_handler(action_type: str)` and `get_condition_evaluator(operator: str)`.

### Why it is extensible

Adding a new action type requires two steps and zero changes to `engine.py`:

1. Add the new value to the `ActionType` enum in `domain/value_objects.py`.
2. Write a function in `registry.py` (or any module that is imported before the engine
   runs) and decorate it with `@register_action_handler(ActionType.YOUR_TYPE)`.

The engine only calls `get_action_handler(action_type)` - it has no knowledge of which
handlers exist. If no handler is registered for a given type, the engine logs a warning
and skips that action; it does not raise.

The same pattern applies to condition evaluators via `@register_condition_evaluator`.

---

## Engine Entry Point: `fire_trigger()`

```python
# apps/workflow_automation/engine.py
fire_trigger(trigger_type: str, context_payload: dict) -> None
```

`fire_trigger()` is the single public entry point for every trigger source. It:

1. Validates `trigger_type` against the `TriggerType` enum. Logs a warning and returns
   early if the value is unknown.
2. Queries the ORM for all `AutomationRule` rows where `trigger_type` matches and
   `is_enabled=True`. Both columns are indexed (`db_index=True`) for fast lookup.
3. For each matching rule ID, enqueues a `execute_automation_rule` Django-Q2 task. The
   call-site is non-blocking; the actual evaluation and action dispatch happen in the
   Q2 worker process.
4. Logs each enqueued rule ID at `INFO` level for observability.

`fire_trigger()` uses deferred ORM imports (inside the function body) to avoid circular
import issues when it is called from other apps at startup.

---

## Cross-App Integration

### client_portal - `deliverable.approved`

`apps/client_portal/infrastructure/viewsets.py` calls `fire_trigger` inside
`ApprovalViewSet` after a deliverable version is approved:

```python
from apps.workflow_automation.engine import fire_trigger
fire_trigger('deliverable.approved', {
    'source_id': str(deliverable_version.id),
    'source_type': 'DeliverableVersion',
    'payload': {
        'project_id': str(project.id),
        'organization_id': str(organization.id),
        'deliverable_id': str(deliverable.id),
    }
})
```

Any enabled rule with `trigger_type = deliverable.approved` is evaluated. A common
configuration is: condition `organization_id eq <uuid>` + action `create_activity_event`
to append an entry to the ops_dashboard audit trail automatically.

### ops_dashboard - `metric.threshold_crossed`

`apps/ops_dashboard/tasks.py` calls `fire_trigger` after the periodic alert-rule
evaluator detects a threshold breach:

```python
from apps.workflow_automation.engine import fire_trigger
fire_trigger('metric.threshold_crossed', {
    'source_id': str(alert_rule.id),
    'source_type': 'AlertRule',
    'payload': {
        'metric_name': alert_rule.metric_name,
        'current_value': str(current_value),
        'threshold': str(alert_rule.threshold),
    }
})
```

Rules configured for this trigger can dispatch `send_email` or `send_sms` notifications
to operations staff.

---

## Dry-Run Mode

Dry-run mode allows a rule to be fully evaluated (all conditions are checked against a
provided context payload) without dispatching any Q2 tasks. The `AutomationRun` record is
created with `is_dry_run=True` and transitions to `RunStatus.DRY_RUN` on completion.
`AutomationRunLog` entries are written describing each condition result and what action
*would* have been dispatched.

**Why it exists:** In a production system, actions have irreversible side-effects (emails
sent, SMS messages delivered, records mutated). Dry-run lets a developer or operator
validate a rule's logic against realistic payloads without any risk. It is also used
during automated testing to verify rule evaluation logic without hitting external APIs.

**How to invoke it via the API:**

```
POST /api/workflow_automation/rules/{id}/dry_run/
Content-Type: application/json

{"context": {"trigger_type": "deliverable.approved", "source_id": "...", "source_type": "DeliverableVersion", "payload": {"organization_id": "..."}}}
```

The React UI exposes a "Dry Run" button on the rule detail page that opens a results
modal showing each log entry from the dry-run execution.

---

## React UI

### Layout Component

`AutomationLayout` (`frontend/src/components/layout/AutomationLayout.tsx`) wraps all
automation pages. It uses the same `SidebarLayout` and cyberpunk design system as the
client_portal and ops_dashboard UIs for visual consistency.

### Routes and Pages

| Route | Component | Description |
|---|---|---|
| `/automations` | `AutomationListPage` | Lists all defined rules with their enabled/disabled state and an enable/disable toggle per row |
| `/automations/new` | `AutomationNewPage` | Step-by-step rule builder: select trigger type, add conditions, add actions. Submits via POST to `/api/workflow_automation/rules/` then POSTs conditions and actions |
| `/automations/:id/runs` | `AutomationRunsPage` | Paginated run history table for a specific rule with expandable log entries per run and a Dry Run button |

---

## API Endpoints

All endpoints are prefixed at `/api/workflow_automation/` and require staff authentication
(`IsStaffUser` permission class).

| Method | Path | Description |
|---|---|---|
| `GET` | `rules/` | List all automation rules |
| `POST` | `rules/` | Create a new automation rule |
| `GET` | `rules/{id}/` | Retrieve a single rule |
| `PUT/PATCH` | `rules/{id}/` | Update a rule |
| `DELETE` | `rules/{id}/` | Delete a rule |
| `POST` | `rules/{id}/enable/` | Enable a rule (calls `EnableRule` use case) |
| `POST` | `rules/{id}/disable/` | Disable a rule (calls `DisableRule` use case) |
| `POST` | `rules/{id}/dry_run/` | Execute a dry run with a provided context payload |
| `GET` | `conditions/` | List all conditions (filter by `rule_id` query param) |
| `POST` | `conditions/` | Create a condition for a rule |
| `GET/PUT/PATCH/DELETE` | `conditions/{id}/` | Manage a single condition |
| `GET` | `actions/` | List all actions (filter by `rule_id` query param) |
| `POST` | `actions/` | Create an action for a rule |
| `GET/PUT/PATCH/DELETE` | `actions/{id}/` | Manage a single action |
| `GET` | `runs/` | List all run records (filter by `rule_id` query param) |
| `GET` | `runs/{id}/` | Retrieve a single run record |
| `GET` | `logs/` | List all run log entries (filter by `run_id` query param) |
| `GET` | `logs/{id}/` | Retrieve a single log entry |
