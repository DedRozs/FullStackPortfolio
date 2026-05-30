# ADR 0005: Dual Authentication for REST and WebSocket Transports

**Status:** Accepted
**Date:** 2026-05-29
**Deciders:** Joseph Prince
**Technical Story:** FSP-3 - Secure Client Portal with Project Approvals and File Management

---

## Context

The client portal exposes two types of connections:

1. **REST API** (`/api/portal/*`) - standard HTTP request/response used for all CRUD
   operations, approval decisions, file uploads, and list queries.
2. **WebSocket** (via Django Channels) - long-lived bidirectional connections used for
   real-time push notifications (approval state changes, new messages).

DRF `TokenAuthentication` is the standard authentication mechanism for the REST API.
Clients send `Authorization: Token <token>` in the HTTP request header. This mechanism
cannot be reused directly for WebSocket connections because the browser's native
WebSocket API does not support setting custom HTTP headers during the initial handshake.

---

## Decision

Use two different authentication mechanisms - one per transport:

**REST API:** DRF `TokenAuthentication`
- Client stores the token returned by `POST /api/auth/login/` in `localStorage`.
- All REST requests include the header `Authorization: Token <token>`.
- DRF validates the token against the `authtoken_token` table on every request.

**WebSocket:** Django Channels `AuthMiddlewareStack` + `SessionAuthentication`
- The browser login flow (django-allauth) sets a server-side session cookie.
- The WebSocket handshake carries the session cookie automatically (same-origin).
- `AuthMiddlewareStack` in `core/asgi.py` validates the session before the
  WebSocket connection is accepted.
- `AllowedHostsOriginValidator` wraps the WebSocket URLRouter to block connections
  from origins not listed in `ALLOWED_HOSTS`, preventing cross-origin WebSocket abuse.

---

## Options Considered

### Option 1: Token in query string for WebSocket
Append the DRF token to the WebSocket URL: `ws://host/ws/?token=<token>`.

**Rejected.** Tokens in query strings are logged in web server access logs, browser
history, and Referer headers. This is a credential leakage risk classified under
OWASP A02 (Cryptographic Failures). No advantages over the session approach.

### Option 2: JWT for both transports
Issue a JWT on login; validate it on both REST and WebSocket (custom Channels middleware).

**Rejected.** JWT introduces token revocation complexity (tokens remain valid until
expiry even after logout), requires a refresh mechanism, and adds implementation surface
for a portfolio project where the main goal is demonstrating secure permissioned
workflows - not JWT lifecycle management. DRF tokens are simpler, immediately revocable
(DELETE the token row), and sufficient for portfolio scope.

### Option 3: Dual authentication (chosen)
Use DRF token for REST, session cookie for WebSocket.

**Accepted.** Each mechanism is the idiomatic fit for its transport. No credential
leakage. Token revocation works normally on REST. WebSocket authentication is handled
by the standard Channels middleware stack without custom code.

---

## Rationale

The session cookie is sent automatically by the browser on WebSocket handshake to the
same origin. This is the standard approach documented by Django Channels. Token
authentication over REST is the standard DRF approach for SPA/mobile clients.
Combining both is the minimal-complexity solution that avoids the query-string leakage
problem while keeping each transport's authentication idiomatic.

---

## Consequences

### Positive
- No credential leakage via query strings or logs.
- Token revocation (logout) works correctly on REST.
- WebSocket authentication requires no custom middleware.
- `AllowedHostsOriginValidator` provides CSRF-equivalent protection for WebSockets.

### Negative
- Two authentication mechanisms to maintain and understand.
- REST token is stored in `localStorage`, which is accessible to JavaScript. An XSS
  vulnerability would expose the token. This is a known limitation accepted for this
  architecture phase; CSP headers at the GAE layer are the primary mitigation.
  HttpOnly cookie upgrade is a future hardening task.

### Neutral
- WebSocket consumers must check `scope["user"].is_authenticated` explicitly, since
  unauthenticated WebSocket connections would otherwise be accepted before rejection
  in the consumer.

---

## Follow-up Actions

- [ ] Configure Content-Security-Policy headers at Google App Engine ingress to
      reduce XSS risk from the `localStorage` token
- [ ] Evaluate HttpOnly cookie upgrade for the DRF token when authentication
      hardening is prioritized
