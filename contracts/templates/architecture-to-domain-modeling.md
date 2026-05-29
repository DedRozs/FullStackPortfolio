# Architecture to Domain Modeling Artifact

<!-- This template is produced by the Architecture Orchestrator and consumed by the
     Domain Modeling Orchestrator. Complete every section. Validate against:
     contracts/schemas/architecture-to-domain-modeling.schema.json -->

**Schema version:** 1.0
**Project name:** This Project
**Produced by:** `.github/agents/architecture-orchestrator.agent.md`
**Consumed by:** `.github/agents/domain-modeling-orchestrator.agent.md`

---

## Schema Version

Record the schema version used: `1.0`

---

## Project Name

State the full project name as configured in `This Project`.

---

## Architecture Decisions

<!-- Produced by: adr-writer -->

Record every ADR produced during the Architecture phase. Each ADR must have a unique ID,
a status, and all five required fields. Use additional ADR files in `knowledge-base/decisions/`
for full detail; include summaries here.

### ADR-001: [title]

- **Status:** [proposed / accepted / deprecated / superseded]
- **Context:** [forces and constraints that made this decision necessary]
- **Decision:** [the specific choice made and the rationale]
- **Consequences:** [positive and negative consequences]

### ADR-002: [title]

- **Status:**
- **Context:**
- **Decision:**
- **Consequences:**

---

## Bounded Context Map

<!-- Produced by: solution-architect -->

### Contexts

| Context Name | Responsibility | Owner |
|---|---|---|
| [context name] | [single business capability this context owns] | [team or role] |

### Integration Patterns

| Upstream | Downstream | Pattern |
|---|---|---|
| [context] | [context] | [shared-kernel / anti-corruption-layer / open-host-service / conformist] |

---

## Interface Contracts

<!-- Produced by: api-contract-designer -->

| Contract ID | Name | Type | Description | Key Endpoints |
|---|---|---|---|---|
| API-001 | [name] | [REST / gRPC / message-queue / event-stream] | [what it exposes and who consumes it] | [list key operations] |

---

## Data Model

<!-- Produced by: data-architect -->

### Entities

| Entity | Description | Key Attributes |
|---|---|---|
| [name] | [what it represents in the domain] | [attr1, attr2, attr3] |

### Relationships

| From | To | Cardinality | Description |
|---|---|---|---|
| [entity] | [entity] | [one-to-many / many-to-many / ...] | [nature of the relationship] |

### Data Ownership

| Entity | Owner Context |
|---|---|
| [entity] | [bounded context name] |

---

## Security Controls

<!-- Produced by: security-architect -->

### Threat Summary

| Threat | Risk Rating | Mitigation |
|---|---|---|
| [threat description] | [critical / high / medium / low] | [planned control] |

### OWASP Top 10 Mitigations

All ten OWASP Top 10 items must be addressed. For each, state the specific control planned.

| OWASP Item | Mitigation |
|---|---|
| A01:2021 Broken Access Control | [specific control] |
| A02:2021 Cryptographic Failures | [specific control] |
| A03:2021 Injection | [specific control] |
| A04:2021 Insecure Design | [specific control] |
| A05:2021 Security Misconfiguration | [specific control] |
| A06:2021 Vulnerable and Outdated Components | [specific control] |
| A07:2021 Identification and Authentication Failures | [specific control] |
| A08:2021 Software and Data Integrity Failures | [specific control] |
| A09:2021 Security Logging and Monitoring Failures | [specific control] |
| A10:2021 Server-Side Request Forgery | [specific control] |

### Authentication Strategy

[Describe the selected authentication approach - e.g., "OAuth 2.0 + PKCE for user-facing APIs; mTLS for service-to-service communication"]

### Authorization Strategy

[Describe the selected authorization model - e.g., "Role-Based Access Control (RBAC) with three roles: admin, operator, viewer"]

---

## Technology Stack

<!-- Produced by: solution-architect -->

| Component | Selection |
|---|---|
| Language | {{TARGET_LANGUAGE}} |
| Framework | {{FRAMEWORK_NAME}} |
| Database | {{DATABASE_ENGINE}} |
| Messaging Platform | [platform name, or "none"] |
| Deployment Target | {{DEPLOYMENT_TARGET}} |
