---
applyTo: "**/infrastructure/**/*.{py,ts,cs,java,kt}, **/adapters/**/*.{py,ts,cs,java,kt}"
---
# SaaS Multi-Tenancy Rules

Every repository implementation MUST filter all queries by a `tenantId` resolved from
a `TenantContext` value object passed through the use-case input port. Cross-tenant data
access is prohibited at every layer. Any query that does not include a tenant filter is
a critical invariant violation.

The `TenantContext` value object must be propagated from the adapter boundary
(controller) through the use-case input port into the repository interface. It must
never be read directly from an HTTP header inside the domain or application layer.
Pulling the tenant identity from an HTTP context inside the domain or use case layer
couples those layers to the web framework and violates the Clean Architecture dependency
rule.

Row-level security enforcement must be implemented at the persistence adapter boundary.
The domain layer must remain entirely unaware of multi-tenancy mechanics. Embedding
tenant filtering logic inside domain entities or domain services creates an illegal
dependency on infrastructure concerns.

All repository integration tests must include at least one test asserting that a query
for tenant A cannot return data belonging to tenant B. This cross-tenant isolation test
is mandatory for every repository implementation and must be executed as part of the
integration test suite before any release.

Tenant identifiers must be non-guessable (UUID v4 or equivalent). Sequential integer
tenant IDs are prohibited because they enable enumeration attacks that allow one tenant
to access or probe the resources of adjacent tenants.

Database schema design must use one of: (a) separate schema per tenant, (b) shared
schema with `tenant_id` column on every table, or (c) separate database per tenant.
The chosen strategy must be documented in an ADR before implementation begins. Mixing
strategies across tables in the same application is prohibited.

All database queries that filter by `tenantId` must use parameterized queries or a
typed ORM query builder. String interpolation or concatenation of tenant identifiers
directly into SQL or query strings is prohibited. This applies to all persistence
adapters regardless of the underlying database engine or ORM framework.
