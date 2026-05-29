# ADR 0001: Django + React-as-Static-Files Architecture

**Status:** Accepted
**Date:** 2026-05-29
**Deciders:** Joseph Prince
**Technical Story:** Initial portfolio architecture design

---

## Context

A professional developer portfolio needs a modern, visually rich frontend and a reliable
backend for server-side features (contact form, AI assistant, project demos). The options
are a traditional Django-rendered site, a fully decoupled SPA with a separate API, or a
hybrid. The constraint is deployment simplicity: a single Google App Engine service is
preferred over managing separate frontend and backend deployments.

---

## Decision

Build the frontend as a React SPA that is compiled to static files and served by Django's
`staticfiles` system. Django handles all server-side routing, the admin interface, form
processing, and API endpoints. No separate Node.js server runs in production.

---

## Options Considered

### Option 1: Pure Django (server-side rendered HTML + Jinja2 templates)
**Pros:** Simplest deployment; full Django ORM and template access.
**Cons:** Limited interactivity; dated developer experience for front-end work.

### Option 2: React served as Django static files (chosen)
**Pros:** Modern React tooling; single deployment unit; no CORS complexity; Django
handles all API calls server-side.
**Cons:** React build step required before deploying; static file caching must be managed.

### Option 3: Decoupled React frontend (Vercel/Netlify) + Django API (GAE)
**Pros:** Independent deployments; true SPA experience.
**Cons:** CORS configuration required; two deployment pipelines; more operational
overhead for a single-developer portfolio.

---

## Rationale

Option 2 gives a modern frontend experience while keeping deployment simple. A portfolio
site does not require real-time data or the scalability benefits of a decoupled
architecture. Serving React artifacts through Django's staticfiles is a well-understood
pattern with no operational surprises.

---

## Consequences

### Positive
- Single deployment to Google App Engine covers the entire stack.
- No CORS headers required; Django handles all API calls.
- Django admin is available without a separate backend deployment.

### Negative
- React must be compiled before each deployment; the build step is added to the CI/CD
  pipeline.
- Static file cache busting requires `ManifestStaticFilesStorage` or an equivalent.

### Neutral
- `apps/react_app/` holds the React source. The compiled `build/` directory is committed
  to the repository or generated during CI/CD.

---

## Follow-up Actions

- [ ] Configure `STATICFILES_STORAGE` in `settings.py` for cache busting
- [ ] Add React build step to GitHub Actions workflow
- [ ] Decide whether compiled React artifacts are committed to the repo or generated in CI
