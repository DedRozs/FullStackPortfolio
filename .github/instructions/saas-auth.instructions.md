---
applyTo: "**/adapters/**/*.{py,ts,cs,java,kt}, **/infrastructure/**/*.{py,ts,cs,java,kt}"
---
# SaaS Authentication and Authorization Rules

OAuth 2.0 with OIDC is the required authentication protocol. Authorization Code Flow
with PKCE is required for user-facing clients. Client Credentials Flow is permitted
only for machine-to-machine service accounts. Any other authentication mechanism
(custom session tokens, HTTP Basic Auth, API key-only authentication for user-facing
flows) must not be used unless explicitly justified in an ADR.

Token validation (JWT signature verification, expiry check, issuer check, audience
check) must be performed at the adapter boundary - specifically inside the controller
or a dedicated authentication middleware. Token validation logic is prohibited in use
cases, domain services, and domain entities. Placing token validation anywhere other
than the adapter boundary violates the Clean Architecture dependency rule by introducing
framework-level security infrastructure into the domain.

The authenticated user's identity must be passed into use cases as a typed value object
(e.g., `AuthenticatedUser` or `UserIdentity`), never as a raw string or decoded JWT
map. Passing raw JWT claims or untyped dictionaries into use cases leaks the token
format into the application layer and prevents compile-time type checking of identity
properties.

Authorization (permission checks, role enforcement) must be performed in the use-case
layer using domain-language roles, never by inspecting raw JWT claims inside a domain
entity. Domain entities must not contain authorization logic; authorization is an
application-layer concern that belongs in use-case command and query handlers.

Refresh token rotation must be implemented. Refresh tokens must be stored as hashed
values; plaintext refresh tokens must never be persisted. Storing plaintext refresh
tokens creates a credential exposure risk if the token store is compromised.

All authentication endpoints must be rate-limited. Brute-force protection (account
lockout or exponential backoff) is required for credential-based flows. Authentication
endpoints without rate limiting are a critical security vulnerability that violates
OWASP Top 10 A07 (Identification and Authentication Failures).
