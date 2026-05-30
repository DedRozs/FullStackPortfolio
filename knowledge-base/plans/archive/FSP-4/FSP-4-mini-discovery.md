# Mini-Discovery Artifact

<!-- This artifact is produced by ticket-intake-agent (Stage 0) and enriched by
     codebase-context-agent before the first routed phase orchestrator is invoked.
     Complete every required section. The Codebase Context section is optional and
     is appended by codebase-context-agent if prior archive artifacts exist.
     Validate against: contracts/schemas/mini-discovery.schema.json -->

**Produced by:** `.github/agents/ticket-intake-agent.agent.md` (enriched by `.github/agents/codebase-context-agent.agent.md`)
**Consumed by:** `domain-modeling-orchestrator`

---

## Ticket Identity

| Field | Value |
|---|---|
| Issue key | FSP-4 |
| Issue type | Story |
| Project key | FSP |

---

## Summary

ops_dashboard - Business Operations Dashboard

---

## Description

The ops_dashboard is a polished internal analytics dashboard that turns raw business data into KPIs, charts, filters, and automated alerts. It demonstrates executive-facing software capability beyond basic CRUD screens. It builds on client_portal auth, permissions, and Q2 patterns. Stack: Python/Django backend, DRF API, React SPA frontend integrating with the existing portfolio React app using the same component library (SidebarLayout, cyberpunk design system). Models: CompanyMetric, RevenueSnapshot, CustomerGrowthSnapshot, DashboardAlert, AlertRule, AuditLogEntry. Services: metrics.py (aggregation, period-over-period delta, rolling averages), alerts.py (rule evaluator, Q2 task every 15 min), imports.py (CSV import + Q2 job). React routes: /dashboard, /dashboard/metrics, /dashboard/alerts. Features: KPI cards with delta indicators, line/bar charts via recharts, sortable/filterable data table, date range picker, alert rule builder form, CSV export endpoint.

The ops_dashboard must integrate with the existing React SPA exactly as the client_portal does.

**UI kit constraint (non-negotiable):** All UI - visual, interactive, AND structural layout - must be built using the Catalyst UI Kit components at `frontend/src/components/catalyst-ui-kit/typescript/`. Zero raw Tailwind utility classes anywhere in page or layout components. If a layout primitive (e.g. a KPI card grid, a stat row, a section wrapper) does not already exist in the kit, it must be added as a new named kit component first, then consumed from there. No raw `<div className="grid ...">` or `<div className="flex ...">` in page files under any circumstances. The existing portal pages are also being refactored to this same standard. The available kit components are:

| Category | Components |
|---|---|
| Layout | `SidebarLayout`, `Sidebar`, `SidebarHeader`, `SidebarBody`, `SidebarFooter`, `SidebarItem`, `SidebarSection`, `StackedLayout` |
| Navigation | `Navbar`, `NavbarItem`, `NavbarLabel` |
| Content | `Heading`, `Subheading`, `Text`, `TextLink`, `Strong`, `Code`, `Divider` |
| Data display | `Card` (variant: surface/elevated; accent: cyan/magenta/none), `Badge`, `BadgeButton`, `Avatar`, `DescriptionList`, `Table`, `TableHead`, `TableBody`, `TableRow`, `TableHeader`, `TableCell` |
| Forms | `Button`, `Input`, `Textarea`, `Select`, `Listbox`, `Combobox`, `Checkbox`, `Radio`, `Switch`, `Fieldset` |
| Overlays | `Dialog`, `Dropdown`, `Alert` |
| Pagination | `Pagination` |

**Design tokens to use:** `neon-cyan`, `neon-magenta`, `bg-cyber-surface`, `bg-cyber-elevated`, `border-cyber-border`, `text-text-primary`, `text-text-muted`, `hover:border-glow-cyan`, `hover:border-glow-magenta`.

**SPA integration requirements:**
- Create `DashboardLayout.tsx` mirroring `PortalLayout.tsx` - uses `SidebarLayout` with branded sidebar nav
- Add `/dashboard/*` routes to `frontend/src/App.tsx` inside `ProtectedRoute` (staff-only)
- Add a "Dashboard" `NavbarItem` to the main site `Layout.tsx` navbar
- Token-based auth: same `localStorage.getItem('auth_token')` pattern as client_portal
- `ProtectedRoute` wrapper already exists - reuse it unchanged

---

## Acceptance Criteria

- Given a staff user visits /dashboard, When the page loads, Then they see KPI cards for revenue, customer growth, and active alerts with period-over-period delta indicators.
- Given a staff user is on /dashboard/metrics, When they apply a date range filter, Then the charts update to show only data within the selected period.
- Given an AlertRule threshold is crossed, When the Q2 scheduler runs, Then a DashboardAlert is created and the staff user sees it flagged in the UI.
- Given a staff user uploads a CSV file, When the import job processes it, Then the metrics are persisted and visible in the dashboard.
- Given a staff user visits /dashboard/alerts, When they view the alert rule builder, Then they can create, edit, and delete AlertRules with threshold conditions.
- Given any dashboard page or layout component is rendered, When inspecting the source, Then every element - visual, interactive, and structural - is a Catalyst UI Kit component; zero raw Tailwind utility classes appear in any file under `frontend/src/pages/` or `frontend/src/components/layout/`; if a needed layout primitive (e.g. KPI card grid) does not exist in the kit, it was added to the kit at `frontend/src/components/catalyst-ui-kit/typescript/` before being used.
- Given a new DashboardLayout is created, When it renders, Then it uses SidebarLayout + Sidebar* components from the kit, matches the visual structure of PortalLayout.tsx exactly, and includes a branded sidebar with nav items for Dashboard, Metrics, and Alerts.

---

## Ticket Size

story

Derived from issue type: Story maps to story.

---

## Routed Phases

- domain-modeling-orchestrator
- development-orchestrator
- qa-orchestrator
- documentation-orchestrator

---

## Codebase Context

<!-- Appended by codebase-context-agent. Source: FSP-3 archive +
     knowledge-base/content/decisions/ + live codebase inspection. -->

### Bounded Contexts

Derived from `apps/` directory structure and FSP-3 `domain-modeling-to-development.json`:

- **client_portal** - Project delivery and approval workflow for client organizations.
  Entities: ClientOrganization, UserProfile, Project, Milestone, Deliverable,
  DeliverableVersion, Approval, FileRecord, MessageThread, Message, InvoiceRecord,
  ActivityEvent. Status state machines: Project (DRAFT -> ACTIVE -> PENDING_APPROVAL ->
  COMPLETE | ARCHIVED), Milestone (PENDING -> IN_PROGRESS -> COMPLETE), Approval
  (PENDING -> APPROVED | REJECTED | REVISION_REQUESTED), InvoiceRecord (DRAFT -> SENT
  -> PAID | OVERDUE | CANCELLED). File storage via GCS.
- **blog** - Blog post publishing with semantic search. Domain entities: Post, Tag.
  Async embedding via OpenAI text-embedding-3-small written to Supabase pgvector.
  Background vectorization via Django-Q2.
- **ops_dashboard** - Business operations analytics dashboard (new - FSP-4). Entities:
  CompanyMetric, RevenueSnapshot, CustomerGrowthSnapshot, DashboardAlert, AlertRule,
  AuditLogEntry. Services: metrics aggregation, alert rule evaluation, CSV import.
- **Portfolio presentation** (`home`, `about`, `contact`, `ai_assistant`, `react_app`) -
  Framework/presentation layer; no domain model. Not a DDD bounded context.

### Key ADR Decisions

Five most recent ADRs (by document order from `knowledge-base/content/decisions/`):

- **ADR-0002** - Cloud Run Worker for Async Task Processing (Accepted) - Background jobs
  (email, SMS, AI API calls) must not block the HTTP cycle; Django-Q2 worker runs on
  Cloud Run; `async_task(...)` is the only approved dispatch mechanism.
- **ADR-0003** - client_portal Domain-ORM Split (Accepted) - Plain Python domain layer
  (zero Django imports) with abstract repository ABCs; separate `models.py` for ORM
  schema only. All bounded contexts follow this split.
- **ADR-0004** - Blog Domain Layer and Supabase Vectorization (Accepted) - Blog follows
  the same domain-ORM split as client_portal; Supabase is a write-only projection store
  reached only through an infrastructure service; domain raises events, does not call
  external services.
- **ADR-0005** - Dual Authentication for REST and WebSocket Transports (Accepted) - REST
  API uses DRF TokenAuthentication (`Authorization: Token <token>`); WebSocket uses
  Django Channels AuthMiddlewareStack + session cookie. Token-in-query-string is
  explicitly rejected (OWASP A02 risk).
- **ADR-0006** - ASGI Migration and Django Channels Infrastructure (Accepted) - Entry
  point is `core/asgi.py` with ProtocolTypeRouter; Daphne replaces Gunicorn;
  RedisChannelLayer via `REDIS_URL` env var with InMemoryChannelLayer fallback for local
  dev; WebSocket consumer implementations deferred to workflow_automation epic.

### Established Patterns

All patterns sourced from the live `apps/client_portal/` implementation. The
`ops_dashboard` bounded context must follow every pattern listed here.

**Clean Architecture layer structure**
Every bounded context is structured as three directories inside its Django app:
- `domain/` - `model.py` (entities as plain Python classes), `value_objects.py`
  (frozen dataclasses + enums), `repositories.py` (abstract ABCs, zero Django imports),
  `events.py` (frozen dataclasses for domain events)
- `application/` - `use_cases.py` (orchestration only; no business rules), `dtos.py`
  (command/query objects), `ports.py` (output port interfaces)
- `infrastructure/` - `viewsets.py` (DRF ModelViewSet subclasses), `repositories.py`
  (implements domain ABCs against Django ORM), `serializers.py`, `permissions.py`,
  `storage.py`
The `models.py` at app root is ORM schema + migration management only; no business logic.

**DDD tactical patterns**
- Entities: plain Python classes with `__post_init__`-style invariant checks and
  state-transition methods that raise `ValueError` on invalid transitions.
- Value objects: `@dataclass(frozen=True)` with validation in `__post_init__`.
- Domain events: `@dataclass(frozen=True)`; raised by state transitions; dispatched by
  application use cases, not by the domain itself.
- Repository interfaces: abstract base classes in `domain/repositories.py`; no concrete
  implementations in the domain layer.
- Status enums: Python `str, Enum` mixing; string values match ORM `CharField(choices=)`
  constants.

**DRF viewset and permissions patterns**
- ViewSet base: `ModelViewSet`; custom `@action` decorators for non-CRUD operations.
- Permission classes: project-specific `BasePermission` subclasses in
  `infrastructure/permissions.py` (e.g., `IsStaffOrClientOfOrganization`); composed per
  viewset via `permission_classes`.
- Authentication: `TokenAuthentication` + `SessionAuthentication` (global DRF default);
  token stored client-side in `localStorage` as `auth_token`.
- Throttling: `AnonRateThrottle` (20/hour) and `UserRateThrottle` (200/hour) applied
  globally; `login` rate at 10/hour.
- Default permission: `IsAuthenticated` globally; override per viewset as needed.

**React SPA patterns**
- All authenticated routes nested inside `<ProtectedRoute>` which reads
  `localStorage.getItem('auth_token')` and redirects to the login page when absent.
- Each portal feature area has a dedicated layout component (`PortalLayout.tsx`,
  `DashboardLayout.tsx`) that renders `<Outlet />` for child routes.
- Layout components use `SidebarLayout` + `Sidebar*` family from the Catalyst UI Kit.
- Navigation state uses `useLocation()` + `isActive()` helper; active item passed via
  `current` prop on `SidebarItem`.
- All `fetch` calls include `Authorization: Token ${localStorage.getItem('auth_token')}`.
- Routes registered in `frontend/src/App.tsx` inside `<Routes>`; pages loaded via
  `lazy()` + `<Suspense>`.

**Catalyst UI Kit constraint (non-negotiable)**
- Kit location: `frontend/src/components/catalyst-ui-kit/typescript/`
- Zero raw Tailwind utility classes in any file under `frontend/src/pages/` or
  `frontend/src/components/layout/`.
- If a layout primitive (KPI card grid, stat row, section wrapper, etc.) does not exist
  in the kit, it must be added to the kit as a named component FIRST, then consumed.
- No inline `<div className="grid ...">` or `<div className="flex ...">` in page files.
- Available layout kit components: `SidebarLayout`, `Sidebar`, `SidebarHeader`,
  `SidebarBody`, `SidebarFooter`, `SidebarItem`, `SidebarSection`, `StackedLayout`.
- Available data display components: `Card` (variant: surface/elevated; accent:
  cyan/magenta/none), `Badge`, `BadgeButton`, `Table`, `TableHead`, `TableBody`,
  `TableRow`, `TableHeader`, `TableCell`, `DescriptionList`, `Avatar`.
- Design tokens: `neon-cyan`, `neon-magenta`, `bg-cyber-surface`, `bg-cyber-elevated`,
  `border-cyber-border`, `text-text-primary`, `text-text-muted`, `hover:border-glow-cyan`,
  `hover:border-glow-magenta`.

**Django-Q2 background task pattern**
- Task functions live in `apps/<context>/tasks.py`; each function is a plain Python
  callable importable by dotted path.
- Dispatch: `async_task('apps.<context>.tasks.<function_name>', arg1, arg2)` from any
  Django code (viewset action, signal, scheduled hook).
- Q_CLUSTER config: name=`portfolio`, workers=2, timeout=90s, retry=120s,
  queue_limit=50, Redis backend via `REDIS_URL` env var.
- Scheduled tasks registered via `Q_CLUSTER` `schedule` key or Django admin
  `Schedule` model; recurring tasks (e.g., alert rule evaluator) use cron expression.

**Testing patterns**
- Framework: pytest + pytest-django (`pytest.ini` at workspace root).
- Domain unit tests: no I/O, no database, no mocks for pure domain logic.
- Integration tests: use Django test database via `@pytest.mark.django_db`.
- Test naming: `Given_<context>_When_<action>_Then_<outcome>` or descriptive function
  names following the same intent.
- Coverage target: domain and use-case layers must have full unit test coverage.

### Technology Stack

Sourced from `requirements.txt`, `frontend/package.json`, and `core/settings.py`.

**Backend**
- Python 3.14
- Django 6.0.5
- djangorestframework 3.17.1
- django-q2 1.10.0 (background jobs; Q_CLUSTER workers=2, timeout=90s, Redis backend)
- channels 4.3.2 (ASGI / WebSocket support)
- daphne 4.2.1 (ASGI production server; replaces Gunicorn)
- django-allauth 65.18.0 (session-based auth for WebSocket handshake)
- mysqlclient 2.2.8 (Google Cloud SQL / MySQL 8.x database)
- pytest 9.0.3 + pytest-django 4.12.0 (test framework)
- INSTALLED_APPS includes: `daphne`, `channels`, `django_q`, `rest_framework`,
  `rest_framework.authtoken`, `allauth`, `allauth.account`, `allauth.headless`,
  `dj_rest_auth`, `apps.client_portal`, `apps.blog`
- `apps.ops_dashboard` must be added to INSTALLED_APPS as part of FSP-4.

**Frontend**
- React 19.2.6
- TypeScript 6.0.2
- Vite 8.0.12 (build tool; `tsc -b && vite build`)
- react-router-dom 7.16.0
- @headlessui/react 2.2.10 (used by Catalyst UI Kit internals)
- tailwindcss 4.3.0 (design system tokens; NOT used directly in page components)
- Catalyst UI Kit: `frontend/src/components/catalyst-ui-kit/typescript/`
- recharts: NOT currently in `frontend/package.json`; must be added
  (`npm install recharts`) before implementing chart components in ops_dashboard.
