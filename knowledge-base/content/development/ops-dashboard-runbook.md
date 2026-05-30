# Developer Runbook: ops_dashboard

**Bounded context:** Business Operations Intelligence (`apps/ops_dashboard/`)
**Status:** Complete
**Last updated:** 2026-05-29

---

## Prerequisites

- Python 3.14 virtual environment at `.venv/`
- Node.js 18+ (for frontend build)
- A running MySQL 8 instance (or SQLite for local development)
- `ops_dashboard` registered in `INSTALLED_APPS` (see setup below)
- A `.env` file at the project root with the required environment variables

---

## Required Environment Variables

| Variable | Purpose | Required for |
|---|---|---|
| `SECRET_KEY` | Django secret key | All environments |
| `DEBUG` | Set to `True` for local development | Local dev only |
| `DATABASE_URL` | Database connection string (MySQL or SQLite) | All environments |

No additional environment variables are required for ops_dashboard beyond the base
project variables. The Q2 worker uses the same MySQL broker as the rest of the project.

---

## Local Setup

### 1. Verify the virtual environment

```
python -m venv .venv
```

If `.venv/` already exists, skip this step.

### 2. Install Python dependencies

```
.venv\Scripts\pip install -r requirements.txt
```

### 3. Add ops_dashboard to INSTALLED_APPS

In `core/settings.py`, confirm `'apps.ops_dashboard'` is in the `INSTALLED_APPS` list.
It should already be present if you are working on the main branch.

### 4. Run migrations

```
.venv\Scripts\python.exe manage.py migrate
```

This applies all ops_dashboard migrations:
- `0001_initial` - creates all 6 ORM models (`CompanyMetric`, `RevenueSnapshot`,
  `CustomerGrowthSnapshot`, `AlertRule`, `DashboardAlert`, `AuditLogEntry`)

### 5. Create a staff user

The ops_dashboard API and React frontend require a staff user. If you already have a
superuser from the `client_portal` setup, it qualifies. Otherwise:

```
.venv\Scripts\python.exe manage.py createsuperuser
```

Enter a username, email, and password. Django superusers have `is_staff=True`
automatically.

To promote an existing non-staff user to staff via the Django shell:

```
.venv\Scripts\python.exe manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(username='your-username')
u.is_staff = True
u.save()
```

### 6. Run the seed script

```
.venv\Scripts\python.exe knowledge-base/scripts/seed_ops_dashboard.py
```

This creates:
- 3 `CompanyMetric` instances (Monthly Revenue, New Customers, Net Revenue Retention)
- 12 months of `RevenueSnapshot` and `CustomerGrowthSnapshot` records
- 3 `AlertRule` instances with varying severity levels; one rule is pre-triggered

See `knowledge-base/scripts/README.md` for full seed script documentation.

---

## Running the Development Server

```
.venv\Scripts\python.exe manage.py runserver
```

The dashboard API is available at `http://localhost:8000/api/dashboard/`. The React
frontend is served at `http://localhost:8000/dashboard/` (requires a frontend build -
see below).

---

## Running the Q2 Worker (Alert Evaluation)

The `evaluate_alert_rules` task runs every 15 minutes via the Q2 scheduler. To process
alert evaluations and metric imports locally, start the Q2 cluster worker in a separate
terminal:

```
.venv\Scripts\python.exe manage.py qcluster
```

Without the worker running, queued tasks accumulate in the database but are not executed.

To verify the Q2 scheduler is configured:

```
.venv\Scripts\python.exe manage.py shell
```

```python
from django_q.models import Schedule
for s in Schedule.objects.all():
    print(s.name, s.func, s.schedule_type, s.minutes)
```

If no `evaluate_alert_rules` schedule exists, create it:

```python
from django_q.models import Schedule
Schedule.objects.get_or_create(
    func='apps.ops_dashboard.tasks.evaluate_alert_rules',
    defaults={
        'name': 'Evaluate Alert Rules',
        'schedule_type': Schedule.MINUTES,
        'minutes': 15,
    }
)
```

---

## Testing Alert Evaluation Manually

Call `evaluate_alert_rules` directly in the Django shell to trigger an evaluation cycle
without waiting for the Q2 scheduler:

```
.venv\Scripts\python.exe manage.py shell
```

```python
from apps.ops_dashboard.tasks import evaluate_alert_rules
evaluate_alert_rules()
```

To call the domain service directly with explicit dependencies (useful for debugging
a specific rule):

```python
from apps.ops_dashboard.domain.services import AlertEvaluationService
from apps.ops_dashboard.infrastructure.repositories import (
    DjangoMetricRepository,
    DjangoAlertRuleRepository,
    DjangoDashboardAlertRepository,
)

service = AlertEvaluationService(
    metric_repo=DjangoMetricRepository(),
    rule_repo=DjangoAlertRuleRepository(),
    alert_repo=DjangoDashboardAlertRepository(),
)
triggered = service.evaluate_all_rules()
print(f'Triggered {len(triggered)} new alert(s)')
for alert in triggered:
    print(alert.rule_id, alert.triggered_value, alert.severity)
```

---

## Frontend Build

Install frontend dependencies (first time only):

```
cd frontend
npm install
```

Build the React app:

```
npm run build
```

Django's static file serving picks up the build output automatically. The dashboard is
served at `/dashboard/` by the catch-all view in `apps/react_app/views.py`.

For live frontend development with hot reload:

```
npm run dev
```

The Vite dev server proxies API requests to Django at `http://localhost:8000`.

---

## Running Tests

Run all ops_dashboard tests:

```
.venv\Scripts\python.exe -m pytest apps/ops_dashboard/tests/ -v
```

Run only domain unit tests (no database required):

```
.venv\Scripts\python.exe -m pytest apps/ops_dashboard/tests/test_domain.py -v
```

Run only integration tests:

```
.venv\Scripts\python.exe -m pytest apps/ops_dashboard/tests/test_api.py -v
```

Run with coverage:

```
.venv\Scripts\python.exe -m pytest apps/ops_dashboard/tests/ --cov=apps/ops_dashboard --cov-report=term-missing
```

Test counts as of FSP-4 completion: 49 tests (39 domain unit + 10 integration), all passing.
- Domain test suite wall-clock time: ~0.22 s (no I/O)
- Integration test suite wall-clock time: ~47 s (Django TestCase + SQLite setup)

---

## API Testing Examples

Obtain a token first:

```
curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}' | python -m json.tool
```

The response includes a `key` field. Use it as the Bearer token in subsequent requests.

List all company metrics:

```
curl -s http://localhost:8000/api/dashboard/metrics/ \
  -H "Authorization: Token <your-token>" | python -m json.tool
```

Retrieve the time-series for a metric:

```
curl -s "http://localhost:8000/api/dashboard/metrics/<metric-id>/series/?start_date=2025-01-01&end_date=2025-12-31" \
  -H "Authorization: Token <your-token>" | python -m json.tool
```

Export metric snapshots as CSV:

```
curl -s "http://localhost:8000/api/dashboard/metrics/<metric-id>/export/?start_date=2025-01-01&end_date=2025-12-31" \
  -H "Authorization: Token <your-token>" -o metrics-export.csv
```

List active alerts:

```
curl -s http://localhost:8000/api/dashboard/alerts/ \
  -H "Authorization: Token <your-token>" | python -m json.tool
```

Acknowledge an alert:

```
curl -s -X POST http://localhost:8000/api/dashboard/alerts/<alert-id>/acknowledge/ \
  -H "Authorization: Token <your-token>" | python -m json.tool
```

List all alert rules:

```
curl -s http://localhost:8000/api/dashboard/alert-rules/ \
  -H "Authorization: Token <your-token>" | python -m json.tool
```

View the audit log:

```
curl -s http://localhost:8000/api/dashboard/audit-log/ \
  -H "Authorization: Token <your-token>" | python -m json.tool
```

---

## How to Add a New Metric Type

Metric types are defined as a `MetricType` enum in the domain value objects. Adding a
new type requires changes in four places:

### Step 1: Add the enum value

In `apps/ops_dashboard/domain/value_objects.py`, add the new value to `MetricType`:

```python
class MetricType(str, Enum):
    REVENUE = "revenue"
    CUSTOMER_GROWTH = "customer_growth"
    CUSTOM = "custom"
    YOUR_NEW_TYPE = "your_new_type"  # add this
```

### Step 2: Create a migration

Django CharField choices are not automatically migrated when an enum changes. If the
ORM model's `metric_type` field uses `choices` from this enum, run:

```
.venv\Scripts\python.exe manage.py makemigrations ops_dashboard
.venv\Scripts\python.exe manage.py migrate
```

If the field uses a plain `CharField` without explicit choices (check `models.py`),
no migration is needed.

### Step 3: Handle the new type in AlertEvaluationService

In `apps/ops_dashboard/domain/services.py`, the `evaluate_rule` method branches on
`metric.metric_type`. Add a branch for the new type to define how the "current value"
is extracted from the relevant snapshot model:

```python
elif metric.metric_type == MetricType.YOUR_NEW_TYPE:
    # fetch and derive current_value from the appropriate snapshot
    pass
```

### Step 4: Update the frontend constant

In the React frontend, metric type labels are typically mapped in a constants file or
inline in the page components. Search for references to `"revenue"` or `"customer_growth"`
in `frontend/src/pages/dashboard/` to find all places that need the new label added.

---

## Common Operations

### Check Django system configuration

```
.venv\Scripts\python.exe manage.py check
```

Zero warnings expected after migrations and environment configuration.

### Open a Django shell

```
.venv\Scripts\python.exe manage.py shell
```

ORM models are importable from `apps.ops_dashboard.models`. Domain objects from
`apps.ops_dashboard.domain.model`.

### List all registered API routes

```
.venv\Scripts\python.exe manage.py show_urls
```

(Requires `django-extensions` installed.)

---

## Troubleshooting

### "table ops_dashboard_companymetric does not exist"

Migrations have not been applied. Run:

```
.venv\Scripts\python.exe manage.py migrate
```

If the error persists, check that `'apps.ops_dashboard'` is in `INSTALLED_APPS` in
`core/settings.py`.

### "recharts is not found" / chart components fail to render

The `recharts` npm package is not installed. Run from the `frontend/` directory:

```
npm install recharts
```

Then rebuild:

```
npm run build
```

### HTTP 403 Forbidden on API requests

The user account does not have `is_staff=True`. Promote the user in the Django shell
(see the "Create a staff user" section above) or use the superuser credentials.

### Q2 worker exits immediately or tasks are not being processed

Common causes:

1. **Missing Q2 schedule:** The `evaluate_alert_rules` schedule may not exist in the
   database. Create it using the shell commands in the "Running the Q2 Worker" section.

2. **Worker not started:** The `qcluster` management command must be running in a
   separate process. The development server does not start the worker automatically.

3. **MySQL broker misconfigured:** Confirm `django_q` is in `INSTALLED_APPS` and
   `Q_CLUSTER` settings in `core/settings.py` point to the correct database.

### Alert rules are not triggering

1. Confirm at least one `AlertRule` has `status = "active"` and has a `metric_id`
   referencing an existing `CompanyMetric` with snapshots.
2. Call `evaluate_alert_rules()` directly in the shell to bypass the Q2 scheduler and
   see immediate output.
3. Check that no ACTIVE `DashboardAlert` already exists for the rule - duplicate alerts
   are intentionally suppressed.

---

## Related Documentation

- [Component reference](../components/ops-dashboard.md)
- [ADR 0007 - ops_dashboard Alert Evaluation Architecture](../decisions/0007-ops-dashboard-alert-evaluation-architecture.md)
- [client_portal runbook](client-portal-runbook.md) - Q2 worker and auth patterns shared with ops_dashboard
