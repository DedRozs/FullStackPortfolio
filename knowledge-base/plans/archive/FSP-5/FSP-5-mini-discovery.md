# Mini-Discovery Artifact

<!-- This artifact is produced by ticket-intake-agent (Stage 0) and enriched by
     codebase-context-agent before the first routed phase orchestrator is invoked.
     Validate against: contracts/schemas/mini-discovery.schema.json -->

**Produced by:** `.github/agents/ticket-intake-agent.agent.md`
**Consumed by:** domain-modeling-orchestrator

---

## Ticket Identity

| Field | Value |
|---|---|
| Issue key | FSP-5 |
| Issue type | Story |
| Project key | FSP |

---

## Summary

workflow_automation - Internal Automation Engine

---

## Description

Build the `workflow_automation` Django app - a lightweight automation engine where users
define triggers, conditions, and actions. Think internal Zapier built for business
workflows. This is the architectural showpiece connecting client_portal and ops_dashboard
into a coherent ecosystem.

**Phase 1 - Engine Design:**
Register `apps/workflow_automation` Django app. Define models: AutomationRule,
AutomationTrigger, AutomationCondition, AutomationAction, AutomationRun, AutomationRunLog.
Implement `registry.py` - decorator-based registry for trigger types, condition operators,
and action handlers that is extensible without modifying the core engine. Implement
`engine.py` - executor that loads a rule, evaluates conditions, dispatches actions, and
writes run logs.

**Phase 2 - Triggers, Conditions, Actions:**
Trigger types: `deliverable.approved` (fires from client_portal),
`metric.threshold_crossed` (fires from ops_dashboard), `invoice.overdue`, `file.uploaded`.
Condition operators: `gt`, `lt`, `eq`, `contains`, `assigned_to`.
Actions: `send_email` (SendGrid), `create_activity_event`, `update_status`,
`send_sms` (Twilio - already configured). All actions execute as Django-Q2 tasks.
Dry-run mode: evaluates a rule and logs what would happen without executing any action.

**Phase 3 - React UI:**
React routes: `/automations`, `/automations/new`, `/automations/:id/runs`.
Rule builder: step-by-step form (trigger -> conditions -> actions).
Run history table with expandable log entries per run.
Enable/disable toggle per rule.
Dry-run button with results modal.
MUST use the same UI kit components as client_portal (SidebarLayout, same cyberpunk
design system - no raw custom Tailwind).

**Phase 4 - Integration + Documentation:**
Wire cross-project trigger: portal deliverable approved -> automation fires -> activity
event appears in dashboard.
Projects page writeup: the registry pattern and extensibility rationale, dry-run mode
purpose, and future extension ideas (webhook triggers, conditional branching).

**Existing infrastructure (no new dependencies required):**
Django-Q2 background tasks, SendGrid email, Twilio SMS, Django Channels + ASGI + Redis,
client_portal domain events (DeliverableApprovalGranted), ops_dashboard alert rules.

---

## Acceptance Criteria

<!-- No explicit Given/When/Then clauses found in ticket body. Derived from stated
     requirements as acceptance statements. -->

- Given a user defines an AutomationRule with a trigger, conditions, and one or more
  actions, when the rule is saved and enabled, then the rule is persisted and the engine
  can load it for evaluation.
- Given a `deliverable.approved` domain event fires in client_portal, when the engine
  evaluates matching rules, then all condition operators are evaluated and passing rules
  dispatch their configured actions as Django-Q2 tasks.
- Given an automation rule fires with `send_email` action configured, when the Q2 task
  executes, then an email is sent via SendGrid and the result is written to
  AutomationRunLog.
- Given an automation rule fires with `send_sms` action configured, when the Q2 task
  executes, then an SMS is sent via Twilio and the result is written to AutomationRunLog.
- Given dry-run mode is requested for a rule, when the engine evaluates the rule, then
  it logs what would happen without executing any action and returns the dry-run result.
- Given a user navigates to `/automations`, when the page loads, then all defined rules
  are listed with their enabled/disabled state using SidebarLayout and the established
  cyberpunk UI kit.
- Given a user navigates to `/automations/new`, when the form is completed step by step
  (trigger -> conditions -> actions), then a new AutomationRule is created via the API.
- Given a user navigates to `/automations/:id/runs`, when the page loads, then the run
  history table is displayed with expandable log entries per run.
- Given a portal deliverable is approved end-to-end, when the full integration path
  executes, then an activity event appears in the ops_dashboard, demonstrating the
  cross-app ecosystem connection.
- Given the React UI for workflow_automation is implemented, when inspected, then it uses
  only the established UI kit components (SidebarLayout, shared design system) with no
  raw custom Tailwind outside the kit.

---

## Ticket Size

story

Derived from issue type: this is a full implementation story (new Django app, domain
model, DDD layers, React UI, cross-app integration) where the architecture is already
established by existing codebase patterns. Discovery and high-level architecture
decisions are pre-resolved by the roadmap and the existing bounded-context structures
of client_portal and ops_dashboard. No architectural unknowns require a separate
discovery or architecture phase.

---

## Routed Phases

- domain-modeling-orchestrator
- development-orchestrator
- qa-orchestrator
- documentation-orchestrator

---

## Codebase Context

<!-- Enriched by codebase-context-agent from live codebase inspection.
     Sources: apps/client_portal/, apps/ops_dashboard/, frontend/src/,
     knowledge-base/content/, knowledge-base/plans/archive/FSP-4/ -->

### Bounded Contexts

- blog (`apps/blog/`) - domain layer, Supabase vectorization, Q2 tasks
- client_portal (`apps/client_portal/`) - full DDD domain/application/infrastructure, REST API, React `/portal/*`, WebSocket
- ops_dashboard (`apps/ops_dashboard/`) - full DDD domain/application/infrastructure, REST API, React `/dashboard/*`, Q2 scheduled tasks
- workflow_automation (`apps/workflow_automation/`) - new; introduced by this ticket
- contact (`apps/contact/`) - simple form, Q2 email/SMS tasks
- ai_assistant (`apps/ai_assistant/`) - OpenAI integration

### Key ADR Decisions

- ADR 0007: ops_dashboard alert evaluation architecture - domain service + Q2 polling; no Django signals; constructor injection only
- ADR 0006: ASGI migration and Django Channels infrastructure - Daphne + Redis channel layer; JWT middleware for WebSocket auth
- ADR 0005: Dual authentication REST and WebSocket - DRF token for REST; custom JWT middleware for WebSocket
- ADR 0003: client_portal domain-ORM split - two parallel representations; domain dataclasses have zero Django imports; ORM models carry no business logic; repository ABCs bridge the two
- ADR 0002: Cloud Run worker for async tasks - Django Q2 + MySQL broker; separate Cloud Run container runs `qcluster`; `async_task()` is the only dispatch mechanism

### Established Patterns

- **Clean Architecture layers per app:** `domain/` (model.py, events.py, value_objects.py, repositories.py, services.py) | `application/` (use_cases.py, dtos.py, ports.py) | `infrastructure/` (repositories.py, serializers.py, viewsets.py, permissions.py)
- **Domain entities:** Plain Python `@dataclass` with `__post_init__` invariants and state-transition methods; zero Django imports; status enums are `str, Enum` subclasses
- **Domain events:** Frozen `@dataclass(frozen=True)` in `domain/events.py`; event name matches past-tense domain language; fields include `occurred_at: datetime`
- **Repository ABCs:** Defined in `domain/repositories.py`; implemented in `infrastructure/repositories.py`; injected via constructor only
- **Use cases:** One class per operation in `application/use_cases.py`; receive all dependencies via `__init__`; return frozen DTO dataclasses; no framework types
- **Django-Q2 task dispatch:** `async_task('apps.<context>.tasks.<function>', *args)` called inside viewset action methods or scheduled; task functions live in `apps/<context>/tasks.py`; all ORM imports are deferred inside the function body to avoid circular imports
- **DRF viewsets:** Extend `ModelViewSet` or `ReadOnlyModelViewSet`; `get_queryset()` enforces org-isolation or staff-only; custom actions via `@action(detail=True, methods=['post'], url_path='...')`; repos and use cases instantiated inline inside action methods
- **DRF router:** `DefaultRouter()` in `api_urls.py`; registered in `core/urls.py` under `/api/<context>/`
- **React layout pattern:** One layout file per section (e.g. `DashboardLayout.tsx`, `PortalLayout.tsx`) that composes `<SidebarLayout navbar=... sidebar=...><Outlet /></SidebarLayout>`; routes wrapped in `<ProtectedRoute>` in `App.tsx`
- **React pages pattern:** Pages import only catalyst-ui-kit components; use `useEffect` + `fetch` for API calls; data types defined as local interfaces at top of file

### Technology Stack

- Python 3.14 / Django 6.0.5
- MySQL 8.x on Google Cloud SQL
- React (Vite) + TypeScript compiled to Django static files
- Django Q2 1.10.0 (task queue, MySQL broker)
- Django Channels + Daphne (ASGI) + Redis (WebSocket channel layer)
- SendGrid (transactional email via `django.core.mail`)
- Twilio (SMS - already configured in settings)
- Google App Engine (web server) + Cloud Run (qcluster worker, `Dockerfile.worker`)
- Google Cloud Storage (file uploads via `GCSFileStorageAdapter`)
- `django-allauth` + `dj-rest-auth` (authentication)

### client_portal Domain Layer - Key Files for workflow_automation

**Trigger source:** `DeliverableApproved` frozen event in `apps/client_portal/domain/events.py`

```python
@dataclass(frozen=True)
class DeliverableApproved:
    deliverable_id: UUID
    deliverable_version_id: UUID
    approval_id: UUID
    reviewer_id: UUID
    comment: str | None
    milestone_id: UUID
    project_id: UUID
    occurred_at: datetime
```

**How the approval event is currently dispatched (no event bus exists):**
- `GrantApproval` use case (`apps/client_portal/application/use_cases.py`) calls `_record_activity()` which writes an `ActivityEvent` row with `event_type='DeliverableApproved'` to the database
- After the use case, the viewset calls `async_task('apps.client_portal.tasks.send_approval_notification', str(approval_id))` to email stakeholders
- **There is no in-process event bus, no Django signal, and no pub/sub.** The `DeliverableApproved` frozen dataclass in `events.py` is defined but not currently instantiated at runtime.
- **Required integration point:** The `ApprovalViewSet.grant_approval` action in `apps/client_portal/infrastructure/viewsets.py` must also call `async_task('apps.workflow_automation.tasks.check_triggers', 'deliverable.approved', {...payload...})` after the use case succeeds. The payload must include at minimum: `deliverable_id`, `project_id`, `organization_id`, `reviewer_id`.

**Other available trigger events from ops_dashboard (`apps/ops_dashboard/domain/events.py`):**
- `AlertTriggered` - fields: `alert_id`, `rule_id`, `metric_id`, `triggered_value`, `threshold_value`, `severity` - maps to `metric.threshold_crossed` trigger type
- `MetricSnapshotRecorded` - fields: `metric_id`, `snapshot_id`, `snapshot_type`

**ActivityEvent append-only audit log** (`apps/client_portal/domain/model.py`):
- `event_type: str` (e.g. `'DeliverableApproved'`, `'ProjectCompleted'`)
- `actor_id: UUID | None`, `project_id: UUID | None`, `organization_id: UUID | None`
- `payload: dict` (JSON; contents vary by event type)
- The `create_activity_event` action in workflow_automation must call `ActivityEventRepository.save()` via the existing use case pattern

### ops_dashboard Q2 Task Pattern to Replicate

`apps/ops_dashboard/tasks.py` - canonical reference:

```python
def evaluate_alert_rules() -> None:
    # All imports deferred inside function body
    from apps.ops_dashboard import models as orm
    from apps.ops_dashboard.domain.services import AlertEvaluationService
    from apps.ops_dashboard.infrastructure.repositories import (
        DjangoAlertRuleRepository,
        DjangoDashboardAlertRepository,
        DjangoMetricRepository,
    )
    service = AlertEvaluationService(
        metric_repo=DjangoMetricRepository(),
        rule_repo=DjangoAlertRuleRepository(),
        alert_repo=DjangoDashboardAlertRepository(),
    )
    triggered = service.evaluate_all_rules()
```

Dispatch pattern used in docstring and by Q2 scheduler:
```python
from django_q.tasks import async_task
async_task('apps.workflow_automation.tasks.execute_automation_rule', str(rule_id), context_payload)
```

All workflow_automation action tasks (send_email, send_sms, create_activity_event, update_status) must follow this same pattern.

### DRF Viewset Pattern to Replicate

Reference: `apps/ops_dashboard/infrastructure/viewsets.py` (staff-only, same permission needed for workflow_automation)

```python
from apps.ops_dashboard.infrastructure.permissions import IsStaffUser

class AlertRuleViewSet(ModelViewSet):
    permission_classes = [IsStaffUser]

    def get_queryset(self):
        return orm.AlertRule.objects.all()

    @action(detail=True, methods=['post'], url_path='pause')
    def pause(self, request: Request, pk: str = None) -> Response:
        use_case = PauseAlertRule(rule_repo=DjangoAlertRuleRepository())
        try:
            dto = use_case.execute(PauseAlertRuleCommand(...))
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(...)
```

workflow_automation viewsets must use `IsStaffUser` (internal tool, no client access).
Router registration goes in `apps/workflow_automation/api_urls.py` using `DefaultRouter`.

### React UI Kit Inventory

**Location:** `frontend/src/components/catalyst-ui-kit/typescript/`

| Component | File | Use in workflow_automation |
|---|---|---|
| `SidebarLayout` | `sidebar-layout.tsx` | AutomationLayout wrapper - required |
| `Sidebar`, `SidebarBody`, `SidebarFooter`, `SidebarHeader`, `SidebarItem`, `SidebarSection` | `sidebar.tsx` | AutomationLayout nav |
| `Navbar`, `NavbarItem`, `NavbarLabel` | `navbar.tsx` | AutomationLayout mobile nav |
| `Heading` | `heading.tsx` | Page headings |
| `Text` | `text.tsx` | Body copy, descriptions |
| `Badge` | `badge.tsx` | Rule status (enabled/disabled), run status (success/failed) |
| `Button` | `button.tsx` | Save rule, dry-run, enable/disable actions |
| `Table`, `TableBody`, `TableCell`, `TableHead`, `TableHeader`, `TableRow` | `table.tsx` | Run history table, rules list |
| `Dialog` | `dialog.tsx` | Dry-run results modal |
| `Switch` | `switch.tsx` | Enable/disable toggle per rule |
| `Input` | `input.tsx` | Rule name, condition value fields |
| `Select` | `select.tsx` | Trigger type selector, condition operator selector, action type selector |
| `Fieldset` | `fieldset.tsx` | Step-by-step form grouping |
| `PageSection` | `page-section.tsx` | Section layout within pages |
| `Card` | `card.tsx` | Rule cards if needed |
| `Pagination` | `pagination.tsx` | Run history table pagination |

**Cyberpunk design system classes (use only these - no raw custom Tailwind):**
- `bg-cyber-dark` - main page background
- `bg-cyber-surface` - card/panel background
- `ring-cyber-border` - border color
- `text-neon-magenta` - brand accent text
- `drop-shadow-[0_0_6px_rgba(0,255,255,0.6)]` - neon glow effect on logos
- `font-display tracking-wider uppercase` - display font style for nav labels

**Layout file pattern to replicate** (`frontend/src/components/layout/AutomationLayout.tsx`):
- Import `SidebarLayout` from catalyst-ui-kit
- Define `AUTOMATION_NAV = [{ href: '/automations', label: 'Rules', end: true }, { href: '/automations/runs', label: 'Run History' }]`
- Compose `<Sidebar>` + `<Navbar>` + `<Outlet />`
- Register in `App.tsx` under `path="automations"` wrapped in `<ProtectedRoute>`

**Existing layout files to use as copy-paste template:**
- `frontend/src/components/layout/DashboardLayout.tsx` (identical structure needed)
- `frontend/src/components/layout/PortalLayout.tsx` (identical structure)

**MUST NOT:**
- Write raw Tailwind utility classes (e.g. `bg-gray-900`, `text-white`, `flex`, `rounded-lg`) outside of what the catalyst-ui-kit components already use internally
- Create new CSS files or inline styles
- Use `className` with arbitrary Tailwind values not in the cyberpunk design system

### How Domain Events Flow Between Bounded Contexts

**Current state (no event bus):**

```
client_portal viewset
  -> use case executes (saves domain state + ActivityEvent to DB)
  -> viewset calls async_task() directly (tight coupling)
```

**Required pattern for workflow_automation integration:**

```
client_portal viewset (ApprovalViewSet.grant_approval)
  -> GrantApproval use case executes
  -> viewset calls async_task('apps.workflow_automation.tasks.check_triggers',
                              'deliverable.approved',
                              {'deliverable_id': ..., 'project_id': ..., ...})

workflow_automation.tasks.check_triggers(trigger_type, context)
  -> loads all enabled AutomationRules with matching trigger_type
  -> for each rule: evaluates conditions against context
  -> for passing rules: calls async_task('apps.workflow_automation.tasks.execute_action', ...)
```

**ops_dashboard trigger (`metric.threshold_crossed`):**
- `AlertEvaluationService.evaluate_rule()` in `apps/ops_dashboard/domain/services.py` creates `DashboardAlert`
- The Q2 task `evaluate_alert_rules` must also call `async_task('apps.workflow_automation.tasks.check_triggers', 'metric.threshold_crossed', {...})` after triggering alerts

### Gaps and Risks Identified

1. **No event bus exists.** Domain events are plain frozen dataclasses that are instantiated in tests but never dispatched at runtime. workflow_automation cannot subscribe to a bus - it must be called explicitly from viewset actions and existing Q2 tasks. This is a coupling point that requires small, targeted additions to `client_portal` and `ops_dashboard` viewsets/tasks.

2. **`apps.workflow_automation` is not yet in `INSTALLED_APPS`** in `core/settings.py`. This must be the first step in implementation.

3. **No `core/urls.py` route for `/api/workflow_automation/`** exists yet. Must add `path('api/workflow-automation/', include('apps.workflow_automation.api_urls'))` to `core/urls.py`.

4. **React `App.tsx` has no `/automations` route.** Must add an `AutomationLayout` route block alongside the existing `dashboard` and `portal` blocks.

5. **`invoice.overdue` trigger type** has no existing dispatch point in the codebase. `InvoiceRecord` status is managed via the `InvoiceRecordViewSet` in client_portal but there is no scheduled task that scans for overdue invoices. This trigger will require a new Q2 scheduled task in client_portal.

6. **`file.uploaded` trigger type** can be hooked into the `UploadFile` use case or the `FileRecordViewSet` action in client_portal - straightforward.

7. **Dry-run mode** requires the engine to short-circuit before dispatching any `async_task()` call. The engine must return a structured result listing which conditions passed and which actions would have been dispatched.

8. **The `context_payload` schema for each trigger type** must be defined explicitly so condition evaluators can reliably reference field names. This is the core design risk - the payload schema is an implicit contract between the source context and the engine.
