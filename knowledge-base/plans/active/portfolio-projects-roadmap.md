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

- [ ] Install `djangorestframework`, `django-allauth`, `dj-rest-auth`
- [ ] Add to `INSTALLED_APPS`: `rest_framework`, `allauth`, `allauth.account`, `dj_rest_auth`
- [ ] Configure DRF default authentication classes in settings
- [ ] Add protected route wrapper component in React SPA for authenticated pages

---

## Project 1: `client_portal` - Secure Client Project Portal

**Elevator pitch:** A full-stack client portal where companies manage projects, files,
deliverables, invoices, messages, and approvals. Shows secure permissioned multi-user
workflows - the kind of software companies actually pay developers to build.

**Portfolio title:** "Secure Client Portal with Project Approvals and File Management"

**Weeks 1-4**

### Phase 1 - Foundation (Days 1-3)

- [ ] Register `apps/client_portal` Django app
- [ ] Define models:
  - `ClientOrganization`
  - `ClientUserProfile`
  - `Project`
  - `Milestone`
  - `Deliverable`
  - `DeliverableApproval`
  - `ProjectFile`
  - `ClientMessage`
  - `InvoiceRecord`
  - `ActivityEvent`
- [ ] Write and run migrations
- [ ] Seed script: 2 demo orgs, 3 projects (active / pending approval / complete), 1 overdue invoice

### Phase 2 - Backend API (Days 4-8)

- [ ] DRF viewsets for all models
- [ ] Object-level permissions: clients see only their org's data; staff see all
- [ ] `services/approvals.py` - approval state machine (pending -> approved/rejected + audit trail)
- [ ] `services/files.py` - file upload to GCS via django-storages
- [ ] `services/notifications.py` - SendGrid email on approval state change (Q2 background task)
- [ ] Test module: approval workflow service unit tests

### Phase 3 - React UI (Days 9-16)

- [ ] React routes: `/portal`, `/portal/projects/:id`, `/portal/files`, `/portal/messages`
- [ ] Auth flow: login page -> dashboard (allauth token exchange with DRF)
- [ ] Project dashboard: status cards, milestone list, deliverable table with approve/reject actions
- [ ] File upload component with progress indicator
- [ ] Activity timeline component (read-only feed of `ActivityEvent`)
- [ ] Invoice status panel (mockup - no real payment processing)

### Phase 4 - Polish + Documentation (Days 17-21)

- [ ] Cyberpunk design system applied consistently throughout
- [ ] Seed data polished to tell a realistic story
- [ ] Projects page writeup:
  - Problem it solves
  - Why object-level permissions (not just `IsAuthenticated`)
  - One tradeoff made during build

### New dependencies
- `djangorestframework`
- `django-allauth`
- `dj-rest-auth`

---

## Project 2: `ops_dashboard` - Business Operations Dashboard

**Elevator pitch:** A polished internal analytics dashboard that turns raw business data
into KPIs, charts, filters, and automated alerts. Shows you can build executive-facing
software, not just CRUD screens.

**Portfolio title:** "Operational Intelligence Dashboard for Growing Teams"

**Weeks 5-7** - Builds on client_portal auth, permissions, and Q2 patterns.

### Phase 1 - Foundation (Days 1-2)

- [ ] Register `apps/ops_dashboard` Django app
- [ ] Define models:
  - `CompanyMetric`
  - `RevenueSnapshot`
  - `CustomerGrowthSnapshot`
  - `DashboardAlert`
  - `AlertRule`
  - `AuditLogEntry`
- [ ] Seed script: 12 months of synthetic metric snapshots, 3 alert rules (one triggered)

### Phase 2 - Backend (Days 3-7)

- [ ] DRF endpoints: metric series (date-range filtered), alert rules, audit log
- [ ] `services/metrics.py` - aggregation logic (period-over-period delta, rolling averages)
- [ ] `services/alerts.py` - rule evaluator; Q2 scheduled task running every 15 minutes
- [ ] `services/imports.py` - CSV import: validates, parses, queues Q2 job for processing
- [ ] CSV export endpoint (streaming response)

### Phase 3 - React UI (Days 8-14)

- [ ] React routes: `/dashboard`, `/dashboard/metrics`, `/dashboard/alerts`
- [ ] KPI cards with delta indicators (up/down vs prior period)
- [ ] Line/bar charts via `recharts`
- [ ] Sortable/filterable data table (reusable component for all three projects)
- [ ] Date range picker for all metric views
- [ ] Alert rule builder form

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

- [ ] Register `apps/workflow_automation` Django app
- [ ] Define models:
  - `AutomationRule`
  - `AutomationTrigger`
  - `AutomationCondition`
  - `AutomationAction`
  - `AutomationRun`
  - `AutomationRunLog`
- [ ] `registry.py` - decorator-based registry for trigger types, condition operators,
      action handlers. Extensible without modifying core engine.
- [ ] `engine.py` - executor: loads rule, evaluates conditions, dispatches actions,
      writes run log

### Phase 2 - Triggers, Conditions, Actions (Days 5-9)

- [ ] Trigger types:
  - `deliverable.approved` (fires from client_portal)
  - `metric.threshold_crossed` (fires from ops_dashboard)
  - `invoice.overdue`
  - `file.uploaded`
- [ ] Condition operators: `gt`, `lt`, `eq`, `contains`, `assigned_to`
- [ ] Actions:
  - `send_email` (SendGrid)
  - `create_activity_event`
  - `update_status`
  - `send_sms` (Twilio - already configured)
- [ ] All actions execute as Q2 tasks
- [ ] Dry-run mode: evaluates rule and logs what would happen without executing

### Phase 3 - React UI (Days 10-16)

- [ ] React routes: `/automations`, `/automations/new`, `/automations/:id/runs`
- [ ] Rule builder: step-by-step form (trigger -> conditions -> actions)
- [ ] Run history table with expandable log entries per run
- [ ] Enable/disable toggle per rule
- [ ] Dry-run button with results modal

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
| `djangorestframework` | Backend | Not installed |
| `django-allauth` | Backend | Not installed |
| `dj-rest-auth` | Backend | Not installed |
| `recharts` | Frontend | Not installed |
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
