# Developer Runbook: client_portal

**Bounded context:** Client Project Delivery (`apps/client_portal/`)
**Status:** Complete
**Last updated:** 2026-05-29

---

## Prerequisites

- Python 3.14 virtual environment at `.venv/`
- Node.js 18+ (for frontend build)
- A running MySQL 8 instance (or SQLite for local development)
- Redis instance accessible via `REDIS_URL` (optional locally - falls back to
  in-memory channel layer)
- A `.env` file at the project root with the required environment variables listed
  in the section below

---

## Required Environment Variables

| Variable | Purpose | Required for |
|---|---|---|
| `REDIS_URL` | Redis connection string for Django Channels channel layer | WebSocket support |
| `GS_BUCKET_NAME` | Google Cloud Storage bucket for file uploads | File upload feature |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP service account JSON key file | GCS file storage |
| `SENDGRID_API_KEY` | SendGrid API key for approval notification emails | Q2 email tasks |
| `SECRET_KEY` | Django secret key | All environments |
| `DEBUG` | Set to `True` for local development | Local dev only |
| `DATABASE_URL` | Database connection string (MySQL or SQLite) | All environments |

Set these in a `.env` file at the project root. `django-environ` loads them
automatically via `env()` calls in `core/settings.py`.

For local development without GCS, you can omit `GS_BUCKET_NAME` and
`GOOGLE_APPLICATION_CREDENTIALS` - the app will use the default Django file storage
backend (local filesystem). File upload use cases will still work but files will be
stored on disk rather than in GCS.

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

This applies all migrations including the client_portal schema:
- `0001_initial` - creates all 12 ORM models
- `0002_make_activityevent_actor_nullable` - makes `ActivityEvent.actor` nullable to
  allow system-initiated audit events

### 4. Create a superuser (first time only)

```
.venv\Scripts\python.exe manage.py createsuperuser
```

### 5. Run the seed script

```
.venv\Scripts\python.exe knowledge-base/scripts/seed_client_portal.py
```

This creates:
- 2 demo client organizations (`Acme Corp`, `Beta Industries`)
- 3 projects in different lifecycle states (ACTIVE, PENDING_APPROVAL, COMPLETE)
- Milestones and deliverables for each project
- 1 overdue invoice for Acme Corp
- Sample activity events in the audit trail

See `knowledge-base/scripts/README.md` for full seed script documentation.

---

## Running the Development Server

### Standard HTTP (no WebSocket)

```
.venv\Scripts\python.exe manage.py runserver
```

This starts the Gunicorn-compatible WSGI server on `http://localhost:8000`. REST API
endpoints work normally. WebSocket connections are not served.

### ASGI with WebSocket support (Daphne)

```
daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

Or via the virtual environment explicitly:

```
.venv\Scripts\python.exe -m daphne -b 0.0.0.0 -p 8000 core.asgi:application
```

Daphne serves both HTTP and WebSocket connections. Use this whenever testing the
Channels infrastructure, WebSocket handshake behavior, or the channel layer
connectivity against Redis.

If `REDIS_URL` is not set, the channel layer falls back to `InMemoryChannelLayer`
which is single-process only - suitable for local development but not for production
or multi-worker setups.

---

## Redis Setup on a VPS

The following steps configure Redis for use as the Django Channels channel layer
on a VPS (e.g. an existing Ubuntu instance).

### 1. Install Redis

```
sudo apt update
sudo apt install redis-server
```

### 2. Configure Redis

Edit `/etc/redis/redis.conf`:

- Set a password:
  ```
  requirepass <your-redis-password>
  ```
- Allow external connections (replace the default `bind 127.0.0.1`):
  ```
  bind 0.0.0.0
  ```
- Optionally restrict to specific IPs using a firewall rule rather than binding to
  all interfaces in production.

### 3. Restart Redis

```
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### 4. Verify connectivity

```
redis-cli -h <vps-ip> -a <your-redis-password> ping
```

Expected output: `PONG`

### 5. Set the REDIS_URL environment variable

In the project `.env` file:

```
REDIS_URL=redis://:<your-redis-password>@<vps-ip>:6379/0
```

Django Channels will detect this variable and configure `RedisChannelLayer`
automatically (see `core/settings.py` - the `if REDIS_URL:` block).

---

## Running Tests

Run all client_portal tests:

```
.venv\Scripts\python.exe -m pytest apps/client_portal/ -v
```

Run only domain unit tests (no database required):

```
.venv\Scripts\python.exe -m pytest apps/client_portal/domain/ -v
```

Run with coverage:

```
.venv\Scripts\python.exe -m pytest apps/client_portal/ --cov=apps/client_portal --cov-report=term-missing
```

Test counts as of FSP-3 completion:
- 66 tests total, all passing
- Domain invariant tests: < 1 s wall-clock (no I/O)

---

## Portal Routes (React Frontend)

| Route | Description |
|---|---|
| `/portal` | Dashboard - project status cards, recent activity |
| `/portal/projects/:id` | Project detail - milestones, deliverables, approval actions |
| `/portal/files` | File browser - upload and download deliverable files |
| `/portal/messages` | Messaging - message thread list and conversation view |
| `/portal/login` | Login page (redirected to by ProtectedRoute when unauthenticated) |

The React SPA is served by Django's staticfiles at `/portal/*`. The Django catch-all
view in `apps/react_app/views.py` renders the React shell for all `/portal/*` paths.

---

## API Base URL

All portal REST endpoints are mounted under `/api/portal/`. The full list of registered
routes is in `apps/client_portal/api_urls.py`. The DRF DefaultRouter generates standard
CRUD URLs for each resource.

Examples:
- `GET /api/portal/projects/` - list all projects visible to the caller
- `POST /api/portal/projects/` - create a project
- `GET /api/portal/projects/{id}/` - retrieve a single project
- `POST /api/portal/projects/{id}/submit-for-approval/` - trigger approval state machine
- `POST /api/portal/approvals/{id}/grant/` - grant an approval decision
- `POST /api/portal/messages/send/` - send a message via use case

---

## Authentication Flow

1. **Login:** POST credentials to `POST /api/auth/login/` (django-allauth token endpoint)

   ```json
   {
     "username": "client@example.com",
     "password": "secret"
   }
   ```

2. **Receive token:** The response body contains a `key` field holding the DRF auth token.

3. **Store token:** The React frontend stores the token in `localStorage` under
   `auth_token`.

4. **Authenticated requests:** All subsequent REST API requests include the header:

   ```
   Authorization: Token <token>
   ```

5. **Logout:** DELETE or POST to the allauth token logout endpoint to invalidate the
   token server-side. The React frontend clears `auth_token` from `localStorage`.

**WebSocket authentication** uses the session cookie set during login. `AuthMiddlewareStack`
in `core/asgi.py` validates the session before accepting the WebSocket connection.
`AllowedHostsOriginValidator` blocks connections from origins not listed in
`ALLOWED_HOSTS`.

---

## Background Task Worker

Approval notification emails are dispatched as Django Q2 async tasks. The worker
must be running to process them.

Start the Q2 worker locally:

```
.venv\Scripts\python.exe manage.py qcluster
```

The worker polls the Django Q2 broker (MySQL task queue by default). In production,
the worker runs as a Cloud Run container defined in `Dockerfile.worker`.

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

ORM models are importable from `apps.client_portal.models`. Domain objects from
`apps.client_portal.domain.model`.

### List all registered API routes

```
.venv\Scripts\python.exe manage.py show_urls
```

(Requires `django-extensions` installed.)

---

## Related Documentation

- [Component reference](../components/client-portal.md)
- [ADR 0003 - Domain-ORM Split](../decisions/0003-client-portal-ddd-split.md)
- [ADR 0005 - Dual Authentication](../decisions/0005-dual-authentication-rest-websocket.md)
- [ADR 0006 - ASGI Migration and Channels](../decisions/0006-asgi-migration-channels-infrastructure.md)
