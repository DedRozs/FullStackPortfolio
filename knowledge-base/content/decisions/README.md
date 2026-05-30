# Architecture Decision Records

This directory contains all Architecture Decision Records (ADRs) for FullStackPortfolio.

An ADR documents a significant architectural or design decision: what was decided, why,
what alternatives were considered, and what the consequences are.

---

## Index

| Number | Title | Status | Date |
|---|---|---|---|
| [0001](0001-django-react-static-architecture.md) | Django + React-as-static-files architecture | Accepted | 2026-05-29 |
| [0002](0002-cloud-run-worker-for-async-tasks.md) | Cloud Run worker for async task processing | Accepted | 2026-05-29 |
| [0003](0003-client-portal-ddd-split.md) | client_portal domain-ORM split | Accepted | 2026-05-29 |
| [0004](0004-blog-domain-layer-and-supabase-vectorization.md) | Blog domain layer and Supabase vectorization | Accepted | 2026-05-29 |

---

## Creating a New ADR

1. Determine the next ADR number from the index above.
2. Copy the template from `contracts/templates/` or use the standard ADR format.
3. Name the file: `NNNN-kebab-case-title.md`
4. Add a row to the index above.
5. Set status to `Proposed` until the decision is finalized.

## ADR Statuses

- **Proposed** - Under discussion; decision not yet final
- **Accepted** - Decision finalized and in effect
- **Deprecated** - Was accepted but no longer applies
- **Superseded by [ADR-NNNN]** - Replaced by a newer decision
