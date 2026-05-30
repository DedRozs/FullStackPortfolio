# Developer Runbook: workflow_automation

**Bounded context:** Internal Workflow Automation (`apps/workflow_automation/`)
**Status:** Complete
**Last updated:** 2026-05-30

---

## Prerequisites

- Python 3.14 virtual environment at `.venv/`
- Node.js 18+ (for frontend build)
- A running MySQL 8 instance (or SQLite for local development)
- Redis instance accessible via `REDIS_URL` (optional locally)
- A `.env` file at the project root with the required environment variables listed below

---

## Required Environment Variables

| Variable | Purpose | Required for |
|---|---|---|
| `SECRET_KEY` | Django secret key | All environments |
| `DEBUG` | Set to `True` for local development | Local dev only |
| `DATABASE_URL` | Database connection string (MySQL or SQLite) | All environments |
| `REDIS_URL` | Redis connection string for Django Q2 broker and Channels layer | Q2 task execution, WebSocket |
| `SENDGRID_API_KEY` | SendGrid API key | `send_email` action handler |
| `TWILIO_ACCOUNT_SID` | Twilio account SID | `send_sms` action handler |
| `TWILIO_AUTH_TOKEN` | Twilio auth token | `send_sms` action handler |
| `TWILIO_FROM_NUMBER` | Twilio source phone number in E.164 format (e.g. `+15551234567`) | `send_sms` action handler |

Action handlers that call external APIs (`send_email`, `send_sms`) import their clients
lazily inside the handler function, so the server starts without error even if these
variables are absent. The handler will raise `AttributeError` at task execution time if
the variable is missing.

---

## Local Setup

### 1. Verify the virtual environment

```
python -m venv .venv
```

If `.venv/` already exists, skip this step.

### 2. Install dependencies

```
.venv\Scripts\pip install -r requirements.txt
```

### 3. Run migrations

```
.venv\Scripts\python.exe manage.py migrate
```

This applies both workflow_automation migrations:

- `0001_initial` - creates all six ORM models: `AutomationRule`, `AutomationCondition`,
  `AutomationAction`, `AutomationRun`, `AutomationRunLog`, and the `AutomationTrigger`
  placeholder
- `0002_add_rule_indexes` - adds `db_index=True` to `AutomationRule.trigger_type` and
  `AutomationRule.is_enabled`; these two columns are used in every `fire_trigger()` query

### 4. Run the development server

```
.venv\Scripts\python.exe manage.py runserver
```

The workflow_automation API is available at `http://localhost:8000/api/workflow_automation/`.

### 5. Start the Q2 worker (required for action execution)

In a separate terminal:

```
.venv\Scripts\python.exe manage.py qcluster
```

Without the Q2 worker running, `fire_trigger()` enqueues tasks but they will not execute
until the worker is started.

### 6. Run the seed script

```
.venv\Scripts\python.exe knowledge-base/scripts/seed_workflow_automation.py
```

This creates sample automation rules demonstrating the three main trigger types, sample
conditions using multiple operators, and sample action configurations for email, SMS, and
activity event creation. See `knowledge-base/scripts/README.md` for full documentation.

---

## Running Tests

```
.venv\Scripts\python.exe -m pytest apps/workflow_automation/tests/ -v
```

55 unit tests covering:

- All domain entity invariants and state transitions
- All five `ConditionOperator` evaluators
- `RuleEvaluationService` logic (pass/fail conditions, short-circuit behavior)
- `AutomationEngineService` live execution and dry-run execution paths
- `AutomationRun` lifecycle transitions (`start`, `complete`, `fail`, `mark_dry_run_complete`)

All tests are pure Python: no database, no network, no Django ORM. Infrastructure
repository implementations follow the same mapper patterns as `client_portal` (which has
integration test coverage); repository integration tests are deferred to a future sprint
(KI-4).

---

## Running Migrations

```
.venv\Scripts\python.exe manage.py migrate workflow_automation
```

To create a new migration after model changes:

```
.venv\Scripts\python.exe manage.py makemigrations workflow_automation
```

---

## Adding a New Trigger Type

1. Add the new value to `TriggerType` in
   `apps/workflow_automation/domain/value_objects.py`:

   ```python
   class TriggerType(str, Enum):
       DELIVERABLE_APPROVED = "deliverable.approved"
       # ... existing values ...
       PAYMENT_RECEIVED = "payment.received"   # new
   ```

2. Add the ORM `CharField` choice constant to `apps/workflow_automation/models.py`
   inside `AutomationRule.TriggerTypeChoices` (or the equivalent `TextChoices` block).

3. Create and run a migration:

   ```
   .venv\Scripts\python.exe manage.py makemigrations workflow_automation
   .venv\Scripts\python.exe manage.py migrate workflow_automation
   ```

4. In the source app that owns the event, call `fire_trigger` after the event fires:

   ```python
   from apps.workflow_automation.engine import fire_trigger
   fire_trigger('payment.received', {
       'source_id': str(payment.id),
       'source_type': 'Payment',
       'payload': {'amount': str(payment.amount), 'organization_id': str(org.id)},
   })
   ```

No changes to `engine.py` are required.

---

## Adding a New Action Handler

1. Add the new value to `ActionType` in
   `apps/workflow_automation/domain/value_objects.py`:

   ```python
   class ActionType(str, Enum):
       # ... existing values ...
       SEND_WEBHOOK = "send_webhook"   # new
   ```

2. Implement the handler function in `apps/workflow_automation/registry.py` and
   decorate it:

   ```python
   @register_action_handler(ActionType.SEND_WEBHOOK)
   def _handle_send_webhook(action_params: dict, context: dict) -> str:
       import requests
       url = action_params.get('url', '')
       response = requests.post(url, json=context, timeout=10)
       return f'Webhook delivered, status={response.status_code}'
   ```

3. The handler signature must be `(action_params: dict, context: dict) -> str`. The
   return value is written to `AutomationRunLog.message`.

4. No changes to `engine.py` are required. The engine calls
   `get_action_handler(action_type)` at task execution time; if the handler is
   registered, it is invoked.

---

## Adding a New Condition Operator

1. Add the new value to `ConditionOperator` in
   `apps/workflow_automation/domain/value_objects.py`:

   ```python
   class ConditionOperator(str, Enum):
       # ... existing values ...
       STARTS_WITH = "starts_with"   # new
   ```

2. Implement the evaluator in `apps/workflow_automation/registry.py` and decorate it:

   ```python
   @register_condition_evaluator(ConditionOperator.STARTS_WITH)
   def _eval_starts_with(field_value: object, expected: object) -> bool:
       return str(field_value).startswith(str(expected))
   ```

3. The evaluator signature must be `(field_value: object, expected: object) -> bool`.

4. No changes to `engine.py` or `RuleEvaluationService` are required.

---

## Q2 Task Monitoring

### Check the task queue

In Django admin at `http://localhost:8000/admin/`, navigate to **Django Q > Queued Tasks**
to see pending `execute_automation_rule` tasks.

### View task success and failure

Navigate to **Django Q > Successful Tasks** and **Django Q > Failed Tasks** in Django
admin. Each failed task record includes the traceback. Common failure causes:

- `KeyError` in an action handler - missing required key in `action_params`
- External API errors (`SendGridException`, `TwilioRestException`) - check environment
  variables and service status
- `DoesNotExist` - the `AutomationRule` was deleted after the task was enqueued

### View run logs

Each Q2 task execution writes `AutomationRunLog` entries. Query them:

```python
from apps.workflow_automation.models import AutomationRunLog
AutomationRunLog.objects.filter(run__rule_id='<uuid>').order_by('logged_at')
```

Or use the API:

```
GET /api/workflow_automation/logs/?run_id=<run_uuid>
```

---

## Troubleshooting

### Rule not firing

1. Confirm the rule is enabled: `AutomationRule.objects.get(pk=...).is_enabled` must
   be `True`.
2. Confirm `trigger_type` on the rule matches the string passed to `fire_trigger()`
   exactly (e.g. `deliverable.approved` not `DELIVERABLE_APPROVED`).
3. Confirm `fire_trigger()` is actually being called. Add a temporary log line or check
   the Q2 queued tasks in admin immediately after the triggering action.
4. Confirm the Q2 worker is running (`manage.py qcluster`). Tasks are enqueued but not
   executed without a running worker.

### Action not executing

1. Check **Django Q > Failed Tasks** in admin for the task traceback.
2. Verify that the action handler is registered: in a Django shell, run:
   ```python
   from apps.workflow_automation.registry import get_action_handler
   print(get_action_handler('send_email'))   # must not be None
   ```
3. Verify environment variables are set for the action type being used (see table above).

### Dry-run shows unexpected results

1. Confirm the context payload passed to `dry_run` matches the structure that the
   condition's `field_name` refers to. Conditions use dot-path lookup into
   `TriggerContext.payload`.
2. Check the `AutomationRunLog` entries for the dry-run execution - each condition
   evaluation step is logged with the extracted field value and expected value.

### Dry-run actions appearing in live production

This cannot happen by design. The `DryRunRule` use case sets `is_dry_run=True` on the
`AutomationRun` and calls `mark_dry_run_complete()` without dispatching any Q2 tasks.
The `execute_automation_rule` Q2 task is never enqueued during a dry-run execution.
