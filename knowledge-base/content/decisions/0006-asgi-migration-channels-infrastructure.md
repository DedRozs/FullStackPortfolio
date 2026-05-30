# ADR 0006: ASGI Migration and Django Channels Infrastructure

**Status:** Accepted
**Date:** 2026-05-29
**Deciders:** Joseph Prince
**Technical Story:** FSP-3 - Secure Client Portal with Project Approvals and File Management

---

## Context

The portfolio project originally used Django's WSGI interface (`core/wsgi.py`) served
by Gunicorn. WSGI is a synchronous, request/response protocol. It cannot serve
WebSocket connections, which require a persistent, bidirectional, long-lived connection.

FSP-3 introduces an acceptance criterion: the server must be capable of serving
WebSocket connections. A planned future epic (`workflow_automation`) will require
real-time push notifications to portal clients when approval states change, when
milestones are marked complete, or when project status transitions occur. The
infrastructure must be in place before that epic begins.

The Django ecosystem's standard answer for WebSocket support is Django Channels
with an ASGI-compatible server (Daphne or Uvicorn). The channel layer (the message
broker between Channels workers) requires an external broker for multi-process
deployments. Redis is the standard choice.

---

## Decision

Migrate the server entry point from WSGI to ASGI using Django Channels:

1. **Entry point:** `core/asgi.py` is updated to expose a `ProtocolTypeRouter` that:
   - Routes HTTP connections to the standard Django ASGI application.
   - Routes WebSocket connections to `AllowedHostsOriginValidator(AuthMiddlewareStack(URLRouter(websocket_urlpatterns)))`.

2. **Development and production server:** Daphne replaces Gunicorn as the primary
   ASGI server. Command: `daphne -b 0.0.0.0 -p 8000 core.asgi:application`.

3. **Channel layer:** `channels_redis.core.RedisChannelLayer` configured via a
   `REDIS_URL` environment variable pointing to a Redis instance on a VPS.
   Falls back to `InMemoryChannelLayer` when `REDIS_URL` is absent (local development
   without Redis).

4. **WebSocket consumers:** `websocket_urlpatterns` is an empty list at FSP-3
   completion. The infrastructure is operational; specific consumer implementations
   are deferred to the `workflow_automation` epic.

5. **HTTP compatibility maintained:** The `ProtocolTypeRouter` routes all HTTP traffic
   to the standard Django ASGI application, so all existing views, REST API endpoints,
   static file serving, and admin continue to work without modification.

---

## Options Considered

### Option 1: Upstash Redis (managed Redis-as-a-service)
Use Upstash as a serverless Redis provider instead of a self-hosted VPS Redis instance.

**Rejected.** The project already has a running VPS. Upstash introduces a paid dependency
for a feature that already has infrastructure. Upstash also has connection count limits
on free tiers that could cause intermittent failures in demo scenarios.

### Option 2: VPC Connector + Cloud NAT for GAE-to-VPS Redis connectivity
Configure a Google Cloud VPC Connector so that Google App Engine instances can connect
to the VPS Redis instance over a private network.

**Deferred to deployment.** This is a production hardening step, not a local development
requirement. For the portfolio demo, the VPS Redis instance is accessible over the
public internet with password authentication (`requirepass` in `redis.conf`). VPC
Connector configuration is deferred to the deployment epic.

### Option 3: Remain on WSGI, use polling for real-time features
Keep the WSGI server and use client-side polling (e.g. every 2-5 seconds) instead of
WebSocket push.

**Rejected.** Polling does not demonstrate WebSocket capability, which is an explicit
FSP-3 acceptance criterion. Polling also increases server load compared to a single
persistent WebSocket connection per portal user.

### Option 4: Django Channels + Daphne + Redis channel layer (chosen)
Migrate to ASGI, use Daphne, configure Redis channel layer via `REDIS_URL`.

**Accepted.** This is the standard Django Channels deployment pattern, well-documented
and widely used. Daphne is maintained by the Django Channels team. The `ProtocolTypeRouter`
provides clean HTTP/WebSocket separation.

---

## Rationale

Django Channels is the idiomatic WebSocket solution for Django projects. Migrating to
ASGI at this point (FSP-3) rather than later means all subsequent Django apps in the
portfolio start from an ASGI-capable base. The cost of the migration is low because
HTTP handling is fully delegated to the standard Django ASGI app - no existing views
or middleware require changes.

The Redis channel layer on the VPS is the simplest multi-process-capable channel layer
available. The `InMemoryChannelLayer` fallback ensures local development does not require
Redis to be running.

---

## Consequences

### Positive
- WebSocket connections are now supportable without further infrastructure changes.
- `workflow_automation` epic can implement real-time push without a second migration.
- `InMemoryChannelLayer` fallback means no Redis dependency for local development.
- `AllowedHostsOriginValidator` prevents cross-origin WebSocket connections at no cost.

### Negative
- Daphne must replace Gunicorn in the production `app.yaml` deployment configuration
  (deferred to deployment epic).
- The CI/CD pipeline health check must be validated against Daphne's behavior
  (deferred to deployment epic).
- Redis on the VPS is currently publicly accessible with password authentication only.
  VPC Connector for private connectivity is deferred.

### Neutral
- `manage.py runserver` continues to work for development but does not serve WebSocket
  connections. Developers who need WebSocket testing must use Daphne.
- The `websocket_urlpatterns` list in `core/asgi.py` is the registration point for all
  future WebSocket consumers.

---

## Follow-up Actions

- [ ] Update `app.yaml` to use Daphne as the entrypoint instead of Gunicorn
- [ ] Validate CI/CD health check against Daphne startup behavior
- [ ] Configure VPC Connector for GAE-to-VPS Redis private networking (production hardening)
- [ ] Register first WebSocket consumer in `websocket_urlpatterns` when workflow_automation
      epic begins
