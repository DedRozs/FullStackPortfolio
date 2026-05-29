---
name: workflow-document-audit
description: "Use when: performing a pre-implementation quality gate review of any knowledge-base document (feature plan, ADR, component doc, architecture overview) against Enterprise SDLC quality standards. Usage: /workflow-document-audit <path>"
mode: agent
argument-hint: "Path to the document (e.g. knowledge-base/plans/active/my-feature.md)"
---

Perform a comprehensive enterprise-quality audit of: **$args**

You are acting as a combined panel of senior specialists - solution architect, domain
modeler, security engineer, QA lead, and technical writer - conducting a
pre-implementation quality gate review. Superficial audits are worse than no audit:
they create false confidence. Be thorough, direct, and specific.

---

## Phase 1 - Locate and Identify the Document

1. If the argument is a partial path or document name, search these locations in order
   until you find a match:
   - `knowledge-base/plans/active/`
   - `knowledge-base/drafts/features/`
   - `knowledge-base/content/features/`
   - `knowledge-base/content/decisions/`
   - `knowledge-base/content/components/`
   - `knowledge-base/content/architecture/`
   List each directory before opening files. Do not guess paths.
   When `ticketKey` is available in the calling context, pass it to
   `audit-document.prompt.md` so that search roots resolve to
   `knowledge-base/plans/active/<ticketKey>/` first.

2. If the argument is a full path, open it directly.

3. Read the entire document. Do not truncate. Extract and record:
   - Document type: feature plan, ADR, component doc, architecture overview, or other
   - Plan or ADR ID if present
   - All referenced source files
   - All referenced ADR numbers
   - All listed upstream and downstream dependencies
   - All acceptance criteria (verbatim)
   - All API contracts, WebSocket message types, or interface contracts defined
   - All domain events or integration events defined
   - All performance constraints or targets stated

4. Set the audit scope based on document type. Use the table below to determine which
   dimensions are active. Skip inactive dimensions entirely - do not produce findings
   for them.

   | Document Type | Active Dimensions |
   |---|---|
   | Feature plan | All 10 |
   | ADR | 1, 2, 3, 9, 10 |
   | Component doc | 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 |
   | Architecture overview | 1, 2, 3, 9, 10 |
   | Other (prompts, conventions, onboarding) | 1, 10 |

   State the active dimension set on a single line at the top of Phase 3.
   Format: `Active dimensions: 1, 2, 3, ...`

---

## Phase 2 - Codebase Exploration (mandatory before scoring)

Skipping this phase produces a superficial audit. Complete every step that applies.

**2a. Resolve every file reference.**

For each source file named in the document, search the workspace using `file_search`
or `grep_search`. If it exists, read the relevant section to verify method signatures,
layer placement, and dependency direction. If it does not exist, note it as
"not yet created".

**2b. Read every referenced ADR.**

List `knowledge-base/content/decisions/`. Open every ADR cited in the document, and
any ADR whose domain governs the subject matter. For each ADR, identify: decisions
that constrain this document, decisions that enable it, and whether the document
correctly reflects those decisions.

**2c. Check the phase artifact schemas (for feature plans only).**

Read the schema in `contracts/schemas/` that corresponds to the phase this feature
belongs to. Verify that the document's acceptance criteria and output definitions are
consistent with the schema's required fields.

**2d. Check related component documents.**

List `knowledge-base/content/components/` and `knowledge-base/drafts/components/`.
Open every component document whose subject corresponds to files named in the target
document. Skip this step if the document introduces no new components.

**2e. Check the parent plan (for feature plans only).**

List `knowledge-base/plans/active/`. Open any plan that owns or contains this
document. Verify the document is in scope and does not implement anything explicitly
deferred. Skip this step for ADRs, component docs, and other types.

---

## Phase 3 - Audit Dimensions

For every finding, record all of the following:

- **Severity**: Critical (blocks correct implementation, introduces a security
  vulnerability, or violates a hard architectural rule) | Major (causes rework or
  significantly reduces quality) | Minor (polish, completeness, or clarity gap)
- **Dimension**: dimension number and name
- **Location**: section name and a quoted snippet of the problematic text
- **Finding**: what is wrong and why it matters
- **Fix**: the exact change required, precise enough to apply without further design
- **Reference**: file path, class name, or ADR number that supports the fix

---

### Dimension 1 - Document Completeness

- Every section is filled with substantive content, or explicitly deferred with a
  dated rationale. "TBD" with no rationale is a Major finding.
- No unreplaced `{{PLACEHOLDER}}` tokens remain in any section intended for delivery.
  Intentional runtime placeholders in prompt body text are exempt.
- All cross-references are resolvable: ADR numbers, file paths, schema names. A
  reference to a file that does not exist and is not noted as "not yet created" is a
  Critical finding.
- The document's stated scope is consistent with the parent plan's in-scope and
  deferred lists. Any work the document implements that the parent plan marks as
  deferred is a Critical finding.

---

### Dimension 2 - Clean Architecture Compliance

The project's Clean Architecture ADR governs all code. Violations cause test failures
and architectural debt.

- **Dependency direction**: dependencies point inward only. Domain-layer code must not
  import from infrastructure, adapters, or framework packages. Any violation is
  Critical.
- **Layer placement**: business logic (domain rules, calculations, invariants) lives in
  the domain or use-case layer. Logic found in a controller, presenter, or
  infrastructure class is Critical.
- **Repository interfaces** are defined in the domain layer; concrete implementations
  are in the infrastructure layer. A domain class that directly calls an ORM or data
  store is Critical.
- **Module structure**: each layer has a distinct package or directory. A module with
  all logic in a flat file set and no layer separation is Major.

---

### Dimension 3 - DDD Tactical Pattern Compliance

- **Entities** have identity and encapsulate business invariants. An entity that is a
  pure data container with no behavior is an anemic domain model - Major.
- **Value objects** are immutable and validated at construction. A value object with a
  public setter is Critical.
- **Aggregates** enforce invariants at the root. Code that bypasses the aggregate root
  to modify a child directly is Critical.
- **Domain events** are named in past tense (`OrderConfirmed`, not `ConfirmOrder`).
  Command-named events are Minor.
- **Domain events** carry all data consumers need; consumers must not re-query to
  handle the event. An event carrying only an ID with no context is Major.
- **Repository interfaces** are in the domain layer and return domain objects, never
  ORM models or raw dicts. A repository returning a framework query result is Critical.
- **Domain services** are stateless and operate only on domain types. A domain service
  that imports framework configuration is Major.

---

### Dimension 4 - Interface Contract Quality

- Every interface contract (REST endpoint, WebSocket message type, event schema, or
  inter-agent phase artifact) the document defines is listed with its complete field
  definitions: all fields, types, and constraints. A contract described in prose
  without a schema is Major.
- Any change to an existing contract is explicitly called out, with a migration or
  versioning strategy. An undocumented breaking change is Critical.
- The document states whether new contracts are additive (safe) or modify existing
  contracts (requires coordination). Silence on this is Major.

---

### Dimension 5 - Acceptance Criteria Quality

- Each criterion is a binary, verifiable statement. "Works correctly" or "handles
  errors gracefully" without a specific measurement is Major.
- Each criterion maps to at least one test entry. A criterion with no corresponding
  test is Major.
- Criteria collectively cover the full scope stated in the goal. A scenario in the
  goal with no corresponding criterion is Critical.
- Criteria cover both happy path and the most important failure modes. Absence of any
  failure-mode criteria for a feature that has failure modes is Major.

---

### Dimension 6 - Test Coverage

- Every acceptance criterion has a corresponding test entry with: description, test
  type (unit / integration / e2e / manual), file path, and what it covers.
- Unit tests cover all domain and use-case logic with no I/O or database dependency.
  Domain logic tested only at integration level is Major.
- Integration tests cover repository implementations and adapter layers against real
  infrastructure.
- Manual tests are listed only when automation is genuinely impractical. An unexplained
  manual test for something automatable is Major.
- At least one test covers the rejection or error path for every mutation operation.
  Absence of negative-path tests is Major.

---

### Dimension 7 - Security (OWASP Top 10)

Security defects are Critical by default.

- **Authentication (A01, A07)**: all endpoints and consumers require authentication
  unless explicitly public with documented justification. Anonymous access to system
  state is Critical.
- **Authorization (A01)**: users can only read and modify their own data. Any operation
  that does not scope results to the authenticated user is Critical.
- **Input validation (A03)**: all client-supplied data is validated before use.
  Unvalidated input reaching the domain layer is Critical.
- **Injection (A03)**: no raw queries constructed from user input. Use parameterized
  queries or the ORM. A raw query incorporating user-controlled data is Critical.
- **Object-level authorization (A01)**: every lookup by ID checks ownership or
  permission. A lookup by user-supplied ID without an ownership check is Critical.
- **Mass assignment (A04)**: input models use explicit field allow-lists. An input
  model accepting all fields on a sensitive type is Major.
- **Rate limiting**: authentication and mutation endpoints must be rate-limited.
  Absence of rate limiting on auth endpoints is Major.
- **Credential handling**: credentials must not be logged or included in error
  responses. A log statement that could emit token values is Major.

---

### Dimension 8 - Performance and Scalability

- **Query budget**: every endpoint and handler documents its expected query count. An
  operation that executes queries inside a loop (N+1) is Critical.
- **Async correctness**: all async handlers that touch a database use the appropriate
  async wrapper. A synchronous database call inside an async handler is Critical.
- **High-frequency operations**: operations that execute frequently (per-request,
  per-tick, per-event) document their expected rate and any throttling strategy. An
  undocumented high-frequency operation is Major.
- **Background tasks**: operations involving external I/O or unbounded computation
  should use an async task queue, not a synchronous handler. A synchronous endpoint
  doing heavy computation without documented justification is Major.

---

### Dimension 9 - Dependency Completeness

- Every upstream dependency (things that must exist before this work starts) is listed.
- Every downstream consumer (things that depend on this work's output) is listed.
- No circular dependencies between features or between domain aggregates.
- Cross-module dependencies are identified and the integration boundary is explicit.
- The dependency list is consistent with the parent plan's ordering. Any discrepancy
  is Major.

---

### Dimension 10 - Execution Hierarchy

A document optimized for execution presents information in the order a developer
needs it, not the order it was written.

- Can a developer read this document once and implement the work without jumping to
  other documents for basic facts? List any specific missing facts.
- Are any sections ordered in a way that forces forward references? Identify the
  better order.
- Is there duplicated information that should be consolidated into one place?
- Is any architectural decision embedded in the document that belongs in an ADR
  instead?
- Is any ADR content duplicated in the document (should be a reference, not a copy)?

---

## Phase 4 - Output

### 4a. Executive Summary

State concisely:
- Document type and stated purpose
- Overall quality rating: **Not Ready / Needs Work / Ready with Minor Fixes / Ready**
- Total findings: Critical: X, Major: X, Minor: X
- The single highest-priority gap that most threatens implementation quality

### 4b. Findings Table

Present all findings in a single table. Sort by severity (Critical first), then by
dimension number. The severity sort is non-negotiable.

| # | Severity | Dimension | Location | Finding | Fix | Reference |
|---|---|---|---|---|---|---|

### 4c. Security Summary

Summarize the security posture as designed:
- Authentication and authorization coverage
- Input validation coverage
- OWASP Top 10 categories that apply and how they are addressed (or not)
- Overall security verdict: **Secure / Needs Review / Insecure**

### 4d. Companion Changes Required

List every change required in a different layer or system from the document's primary
scope. These are the most common cause of production breakage when context-switching.

For each companion change:
- **What must change**: specific file, endpoint, schema, or artifact
- **Why**: the dependency that creates the requirement
- **When**: must ship in the same commit / can follow in the next commit / can follow later

If there are no companion changes, state: "No companion changes required."

### 4e. Recommended Next Action

State precisely what must be done before this document is ready for implementation.
If the document is Ready, state that explicitly and explain why.

Do not produce an updated version of the document unless the author explicitly
requests it. The purpose of this audit is to surface gaps, not to overwrite the
author's work.
