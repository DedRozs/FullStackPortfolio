# Portfolio Projects Roadmap

**Goal:** Build three embedded Django apps that demonstrate senior full-stack capability,
targeting consulting clients and senior engineering roles.

**Stack decisions locked in:**
- Frontend: DRF API + React (same SPA architecture as the rest of the portfolio)
- Auth: django-allauth (email login)
- Background tasks: Django-Q2 (already configured)
- File storage: Google Cloud Storage (already configured)
- Notifications: SendGrid + Twilio (already configured)

**Build order:** client_portal -> ops_dashboard -> workflow_automation

---

## Pre-Work: Dependency Setup

Before Week 1 starts.

- [x] Install `djangorestframework`, `django-allauth`, `dj-rest-auth`
- [x] Add to `INSTALLED_APPS`: `rest_framework`, `allauth`, `allauth.account`, `dj_rest_auth`
- [x] Configure DRF default authentication classes in settings
- [x] Add protected route wrapper component in React SPA for authenticated pages

---

## Project 1: `client_portal` - Secure Client Project Portal ✓ COMPLETE

**Elevator pitch:** A full-stack client portal where companies manage projects, files,
deliverables, invoices, messages, and approvals. Shows secure permissioned multi-user
workflows - the kind of software companies actually pay developers to build.

**Portfolio title:** "Secure Client Portal with Project Approvals and File Management"

**Shipped:** May 2026

**What was actually built (beyond the original plan):**
- Clean Architecture + DDD throughout: `domain/`, `application/`, `infrastructure/` layers with zero cross-layer leakage
- 12 domain entities, 5 aggregates, 18 domain events, 20 use cases (constructor-injected, no framework deps in domain)
- ASGI migration: Django Channels 4 + Daphne + Redis - WebSocket infrastructure ready for workflow_automation triggers
- Dual authentication: TokenAuthentication (REST) + AuthMiddlewareStack/SessionAuthentication (WebSocket)
- `is_demo` flag on UserProfile - demo accounts are read-only for files; real clients are not affected
- DRF throttling: 10/hour login, 200/hour per user, 20/hour anon
- File upload security: MIME whitelist, 10 MB cap, filename sanitization, demo account block
- Message thread ownership enforcement: cross-org message injection prevented at the viewset
- CSRF cookie always set via `@ensure_csrf_cookie` on SPA entrypoint
- 66 unit tests, all passing
- ADRs: 0005 (dual auth), 0006 (ASGI migration)

### Phase 1 - Foundation

- [x] Register `apps/client_portal` Django app
- [x] Define models (12 ORM models matching domain entities)
- [x] Write and run migrations (0001 initial, 0002 actor nullable, 0003 is_demo)
- [x] Seed script: 2 demo orgs, 3 projects, milestones, deliverables, 1 overdue invoice, message thread

### Phase 2 - Backend API

- [x] DRF viewsets for all models (12 viewsets, all registered in api_urls.py)
- [x] Object-level permissions: `IsClientOfOrganization`, `IsStaffOrClientOfOrganization`, `IsApprover`
- [x] Approval state machine (use case layer: GrantApproval, RejectApproval, RequestRevision)
- [x] File upload to GCS via django-storages + GCSFileStorageAdapter
- [x] SendGrid email on approval state change (Django-Q2 background task in tasks.py)
- [x] 66 unit tests passing

### Phase 3 - React UI

- [x] React routes: `/portal`, `/portal/projects/:id`, `/portal/files`, `/portal/messages`
- [x] Auth flow: demo account quick-fill buttons + login page + token stored in localStorage
- [x] Project dashboard: status cards per project
- [x] File upload component with progress indicator (demo accounts see 403, not crash)
- [x] Message threads with send form
- [x] Invoice status visible in dashboard
- [x] `SidebarLayout` used for portal - consistent with rest of UI kit
- [x] Portal nav link added to main site navbar

### Phase 4 - Polish + Documentation

- [x] Cyberpunk design system applied consistently
- [x] Seed data tells a realistic story (active redesign, pending brand identity, complete phase 0)
- [x] Component reference: `knowledge-base/content/components/client-portal.md`
- [x] Developer runbook: `knowledge-base/content/development/client-portal-runbook.md`
- [ ] Projects page writeup (to do when all three projects are complete)

### New dependencies installed
- `djangorestframework` 3.17.1
- `django-allauth` 65.18.0
- `dj-rest-auth` 7.2.0
- `django-channels` 4.3.2
- `daphne` 4.2.1
- `channels-redis` 4.3.0

---

## Project 2: `ops_dashboard` - Business Operations Dashboard

**Elevator pitch:** A polished internal analytics dashboard that turns raw business data
into KPIs, charts, filters, and automated alerts. Shows you can build executive-facing
software, not just CRUD screens.

**Portfolio title:** "Operational Intelligence Dashboard for Growing Teams"

**Weeks 5-7** - Builds on client_portal auth, permissions, and Q2 patterns.

### Phase 1 - Foundation (Days 1-2)

- [x] Register `apps/ops_dashboard` Django app
- [x] Define models:
  - `CompanyMetric`
  - `RevenueSnapshot`
  - `CustomerGrowthSnapshot`
  - `DashboardAlert`
  - `AlertRule`
  - `AuditLogEntry`
- [x] Seed script: 12 months of synthetic metric snapshots, 3 alert rules (one triggered)

### Phase 2 - Backend (Days 3-7)

- [x] DRF endpoints: metric series (date-range filtered), alert rules, audit log
- [x] `services/metrics.py` - aggregation logic (period-over-period delta, rolling averages)
- [x] `services/alerts.py` - rule evaluator; Q2 scheduled task running every 15 minutes
- [x] `services/imports.py` - CSV import: validates, parses, queues Q2 job for processing
- [x] CSV export endpoint (streaming response)

### Phase 3 - React UI (Days 8-14)

- [x] React routes: `/dashboard`, `/dashboard/metrics`, `/dashboard/alerts`
- [x] KPI cards with delta indicators (up/down vs prior period)
- [x] Line/bar charts via `recharts`
- [x] Sortable/filterable data table (reusable component for all three projects)
- [x] Date range picker for all metric views
- [x] Alert rule builder form

### Phase 4 - Polish + Documentation (Days 15-21)

- [ ] Projects page writeup:
  - The scheduling architecture for alert evaluation
  - Why the alert evaluator is a service, not a model method
  - What you would add next

### New dependencies
- `recharts` (frontend only)

---

## Project 3: `workflow_automation` - Internal Automation Engine

**Elevator pitch:** A lightweight automation system where users define triggers,
conditions, and actions. Think internal Zapier built for business workflows. The
architectural showpiece - demonstrates senior-level thinking about systems, not just pages.

**Portfolio title:** "Workflow Automation Engine for Internal Business Processes"

**Weeks 8-11** - Connects client_portal and ops_dashboard into a coherent ecosystem.

### Phase 1 - Engine Design (Days 1-4)

Design carefully before writing views. This is the part that differentiates the project.

- [x] Register `apps/workflow_automation` Django app
- [x] Define models:
  - `AutomationRule`
  - `AutomationTrigger`
  - `AutomationCondition`
  - `AutomationAction`
  - `AutomationRun`
  - `AutomationRunLog`
- [x] `registry.py` - decorator-based registry for trigger types, condition operators,
      action handlers. Extensible without modifying core engine.
- [x] `engine.py` - executor: loads rule, evaluates conditions, dispatches actions,
      writes run log

### Phase 2 - Triggers, Conditions, Actions (Days 5-9)

- [x] Trigger types:
  - `deliverable.approved` (fires from client_portal)
  - `metric.threshold_crossed` (fires from ops_dashboard)
  - `invoice.overdue`
  - `file.uploaded`
- [x] Condition operators: `gt`, `lt`, `eq`, `contains`, `assigned_to`
- [x] Actions:
  - `send_email` (SendGrid)
  - `create_activity_event`
  - `update_status`
  - `send_sms` (Twilio - already configured)
- [x] All actions execute as Q2 tasks
- [x] Dry-run mode: evaluates rule and logs what would happen without executing

### Phase 3 - React UI (Days 10-16)

- [x] React routes: `/automations`, `/automations/new`, `/automations/:id/runs`
- [x] Rule builder: step-by-step form (trigger -> conditions -> actions)
- [x] Run history table with expandable log entries per run
- [x] Enable/disable toggle per rule
- [x] Dry-run button with results modal

### Phase 4 - Integration + Documentation (Days 17-21)

This is the "ecosystem" moment - one action in the portal visibly changes the dashboard.

- [ ] Wire cross-project trigger: portal deliverable approved -> automation fires ->
      activity event appears in dashboard
- [ ] Projects page writeup:
  - The registry pattern and why it matters for extensibility
  - Why dry-run mode exists and what it prevents in production
  - What you would add next (webhook triggers, conditional branching)

### New dependencies
- None

---

## Dependency Install Checklist

| Package | Layer | Status |
|---------|-------|--------|
| `djangorestframework` | Backend | Installed (3.17.1) |
| `django-allauth` | Backend | Installed (65.18.0) |
| `dj-rest-auth` | Backend | Installed (7.2.0) |
| `django-channels` | Backend | Installed (4.3.2) |
| `daphne` | Backend | Installed (4.2.1) |
| `channels-redis` | Backend | Installed (4.3.0) |
| `recharts` | Frontend | Installed (npm) |
| `django-q2` | Backend | Installed + configured |
| `django-storages` | Backend | Installed + configured |
| `sendgrid` | Backend | Installed + configured |
| `twilio` | Backend | Installed + configured |

---

## Architecture Notes

### Django app structure per project
```
apps/
  client_portal/
    domain/         - entities, value objects (no external imports)
    application/    - use cases, service orchestration
    infrastructure/ - DRF serializers, viewsets, ORM models
    tests/
  ops_dashboard/    - same pattern
  workflow_automation/ - same pattern
```

### React routing pattern
```
/portal/*         - protected, requires client or staff role
/dashboard/*      - protected, requires staff role
/automations/*    - protected, requires staff role
/                 - public (home)
/projects         - public
/about            - public
/contact          - public
/ai               - public
```

### Cross-project event flow
```
client_portal.DeliverableApproval.approved
  -> fires AutomationTrigger(deliverable.approved)
  -> engine evaluates matching AutomationRules
  -> executes AutomationActions (email, activity event, status update)
  -> AutomationRun logged

ops_dashboard.AlertRule.threshold_crossed
  -> fires AutomationTrigger(metric.threshold_crossed)
  -> same engine path
```

---

## Projects Page Plan

Each project gets a card on `/projects` with:
1. Title + one-sentence pitch
2. Live demo link (embedded in the portfolio)
3. Tech tags
4. Expandable writeup: problem / architecture decision / tradeoff / what's next

The three projects should read as a connected product ecosystem, not three separate demos.
