---
name: audit-document
description: "Comprehensive quality gate review of any knowledge-base document (feature plan, ADR, component doc, architecture overview) against enterprise SDLC standards for This Project. Runs two audit passes; blocks pipeline continuation until both passes are clean. Usage: /audit-document <path>"
mode: agent
argument-hint: "Path to the document to audit (e.g. knowledge-base/plans/active/my-feature.md)"
---

Perform a comprehensive enterprise-quality audit of: **$args**

**Input guard:** If `$args` is empty or was not provided, halt immediately and respond:
"No document path supplied. Usage: /audit-document <path>  
Example: /audit-document knowledge-base/plans/active/my-feature.md"
Do not proceed past this line until a non-empty path is confirmed.

You are acting as a combined panel of senior specialists - solution architect, domain modeler,
security engineer, QA lead, and technical writer - conducting a pre-implementation quality gate
review for `This Project`. Superficial audits are worse than no audit: they create false
confidence. Be thorough, direct, and specific.

This audit runs in two passes. Both passes must return a clean gate decision before the pipeline
may continue.

---

## Pass 1 - Initial Audit

### Phase 1 - Locate and Identify the Document

1. If the argument looks like a partial name, search these locations in order until you find
   a match:
   - `knowledge-base/plans/active/`
   - `knowledge-base/drafts/features/`
   - `knowledge-base/content/features/`
   - `knowledge-base/content/decisions/`
   - `knowledge-base/content/components/`
   - `knowledge-base/content/architecture/`
   List each directory before opening files. Do not guess paths.

2. If the argument is a full file path, open it directly.

3. Read the **entire** document. Do not truncate. Extract and record:
   - Document type: feature plan, ADR, component doc, architecture overview, or other
   - Plan or ADR ID if present
   - All referenced source files (by path and layer)
   - All referenced ADR numbers
   - All listed upstream and downstream dependencies
   - All acceptance criteria (verbatim)
   - All API contracts, interface contracts, or integration event schemas defined
   - All domain events defined
   - All performance targets or constraints stated

4. Set the audit scope based on document type. Use the table below to determine which
   dimensions are active. Skip inactive dimensions entirely.

   | Document Type | Active Dimensions |
   |---|---|
   | Feature plan | All 15 |
   | ADR | 1, 2, 3, 4*, 9, 13, 14, 15 (apply Dim 4 only if the ADR governs interface contracts) |
   | Component doc | 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 14, 15 |
   | Architecture overview | 1, 2, 3, 9, 14, 15 |
   | Other (prompts, conventions, onboarding) | 1, 15 |

   State the active dimension set on a single line at the top of Phase 3.
   Format: `Active dimensions: 1, 2, 3, ...`

---

### Phase 2 - Codebase Exploration (mandatory before scoring)

Skipping this phase produces a superficial audit. Complete every applicable step before
scoring any dimension.

**2a. Resolve every file reference.**

For each source file named in the document, search the workspace using `file_search` or
`grep_search`. If it exists, read the relevant section to verify method signatures, layer
placement, and dependency direction. If it does not exist, note it as "not yet created".

**2b. Find unleveraged infrastructure.**

Search the project's shared modules, utilities, and framework wrappers for anything the
document's feature domain should reuse but does not mention. List every item found with
the file path, what it provides, and where in the document it should be referenced.

**2c. Read every referenced ADR.**

List `knowledge-base/content/decisions/`. Open every ADR cited in the document and any ADR
whose title or domain governs the subject matter. For each ADR, identify: decisions that
constrain this work, decisions that enable it, and whether the document reflects them
correctly.

**2d. Check the phase artifact schemas (feature plans only).**

Read the schema in `contracts/schemas/` that corresponds to the phase this work belongs to.
Verify the document's acceptance criteria and output definitions are consistent with the
schema's required fields. Skip for other document types.

**2e. Check related component documents.**

List `knowledge-base/content/components/`. Open every component document whose subject
corresponds to source files named in the target document. Skip if no new components are
introduced.

**2f. Check the parent plan (feature plans only).**

List `knowledge-base/plans/active/`. Open any plan that owns or contains this document.
Verify the document is in scope and does not implement anything explicitly deferred.

**2g. Check existing API contracts (skip if no new endpoints or interface contracts).**

Search `knowledge-base/content/api/` for the endpoint or contract registry. For every
endpoint or contract the document introduces, verify the path or identifier does not
conflict with existing registrations and follows the established naming convention.

**2h. Trace cross-layer contracts (skip if no new interface contracts).**

For every new interface contract the document introduces (API endpoint, integration event,
or inter-module message), verify that the consuming side of that contract is either already
implemented or listed as a required companion change. A contract with no documented consumer
is a Major finding under Dimension 14.

---

### Phase 3 - Audit Dimensions

For every finding, record:

- **Severity**: Critical (blocks correct implementation, introduces a security vulnerability,
  or violates a hard architectural rule) | Major (causes rework or significantly reduces
  quality) | Minor (polish, completeness, or clarity gap)
- **Dimension**: number and name
- **Location**: section name and a quoted snippet of the problematic text
- **Finding**: what is wrong and why it matters
- **Fix**: exact change required, precise enough to apply without further design decisions
- **Reference**: file path, class name, or ADR that supports the fix

---

#### Dimension 1 - Document Completeness

- Every section has substantive content or is explicitly deferred with a dated rationale.
  "TBD" without rationale is Major.
- No unreplaced `{{PLACEHOLDER}}` tokens in any section intended for delivery. Intentional
  runtime placeholders in prompt body text are exempt.
- All cross-references are resolvable: ADR numbers, file paths, schema names. A reference
  to a file that does not exist and is not noted as "not yet created" is Critical.
- The document's stated scope is consistent with the parent plan's in-scope and deferred
  lists. Any work the document implements that the parent plan marks as deferred is Critical.

---

#### Dimension 2 - Clean Architecture Compliance

- **Dependency direction**: dependencies point inward only. Domain-layer code must not import
  from infrastructure, adapters, or framework packages. Any violation is Critical.
- **Layer placement**: business logic (domain rules, calculations, invariants) lives in the
  domain or use-case layer. Logic found in a controller, presenter, or infrastructure class
  is Critical.
- **Repository interfaces** are defined in the domain layer; concrete implementations are in
  the infrastructure layer. A domain class that directly calls an ORM or data store is
  Critical.
- **Module structure**: each layer has a distinct package or directory. All logic in a flat
  file set with no layer separation is Major.
- One public type per module; file name matches the primary type. A file named `utils.py`
  or equivalent containing multiple unrelated helpers is Minor.

---

#### Dimension 3 - DDD Tactical Pattern Compliance

- **Entities** have identity and encapsulate business invariants. A pure data container with
  no behavior is an anemic domain model - Major.
- **Value objects** are immutable and validated at construction. A value object with a public
  setter is Critical.
- **Aggregates** enforce invariants at the root. Code that bypasses the aggregate root to
  modify a child directly is Critical.
- **Domain events** are named in past tense (`OrderConfirmed`, not `ConfirmOrder`).
  Command-named events are Minor.
- **Domain events** carry all data consumers need; consumers must not re-query to handle the
  event. An event carrying only an ID with no context is Major.
- **Repository interfaces** return domain objects, never ORM models or raw collections. A
  repository returning a framework query result is Critical.
- **Domain services** are stateless and operate only on domain types. A domain service
  importing framework configuration is Major.

---

#### Dimension 4 - Interface Contract Quality

- Every interface contract (API endpoint, integration event schema, inter-module message, or
  phase artifact) the document defines is listed with complete field definitions: all fields,
  types, and constraints. A contract described in prose without a schema is Major.
- Contract identifiers (paths, event names, message type strings) follow the naming
  conventions defined in the project conventions document. Deviations are Minor.
- Any change to an existing contract is explicitly called out with a migration or versioning
  strategy. An undocumented breaking change is Critical.
- The document states whether new contracts are additive (safe) or modify existing contracts
  (requires coordination). Silence on this is Major.

---

#### Dimension 5 - Authority Boundaries

- The authoritative source of truth for each piece of mutable state is named explicitly.
  State mutation without a designated authority is Major.
- No presentation-layer or client-side code determines final outcomes for business operations.
  Final outcome determination in a client is Critical.
- State transitions that affect domain invariants are authorized by the domain layer or the
  authoritative server component. A client-initiated state transition without domain
  authorization is Critical.
- Client-side prediction or optimistic update patterns are labeled as such and include a
  documented reconciliation strategy. Undocumented prediction is Major.
- The document states what happens when an operation is rejected by the authority. Absence
  of a rejection-handling strategy for any mutation is Major.

---

#### Dimension 6 - API Design Quality

- Endpoints follow resource-oriented conventions: plural noun paths, HTTP verbs match
  semantics. A POST endpoint whose only effect is returning data with no state change is
  Major. POST is correct for custom actions with side effects that do not fit standard verb
  semantics.
- Every endpoint specifies its authentication and authorization requirements explicitly. An
  endpoint without stated permission requirements is Critical.
- Every endpoint that traverses relations specifies its query strategy to prevent N+1 queries.
  Missing query strategy on a relation-traversing endpoint is Major.
- List endpoints that can return unbounded results apply pagination. An unpaginated unbounded
  list endpoint is Major.
- Every endpoint's response schema is documented. An endpoint with no documented response
  shape is Major.

---

#### Dimension 7 - Security (OWASP Top 10)

Security defects are Critical by default.

- **Authentication (A01, A07)**: all endpoints and handlers require authentication unless
  explicitly public with documented justification. Anonymous access to system state is
  Critical.
- **Authorization (A01)**: users can only read and modify data they own or have permission
  for. Any operation that does not scope results to the authenticated principal is Critical.
- **Input validation (A03)**: all external input is validated before reaching the domain
  layer. Unvalidated input in the domain is Critical.
- **Injection (A03)**: no raw queries constructed from user input. Use parameterized queries
  or the ORM. A raw query incorporating user-controlled data is Critical.
- **Object-level authorization (A01)**: every lookup by ID checks ownership or permission.
  A lookup by user-supplied ID without an ownership check is Critical.
- **Mass assignment (A04)**: input models use explicit field allow-lists. An input model
  accepting all fields on a sensitive type is Major.
- **Rate limiting**: authentication and high-risk mutation endpoints must be rate-limited.
  Absence of rate limiting on authentication endpoints is Major.
- **Credential handling**: credentials must not be logged or included in error responses.
  A log statement that could emit token or password values is Major.

---

#### Dimension 8 - Performance and Scalability

- **Query budget**: every endpoint and handler documents its expected query count. An
  operation that executes queries inside a loop (N+1) is Critical.
- **Async correctness**: async handlers that access I/O use the appropriate async wrappers.
  A synchronous blocking I/O call inside an async handler is Critical.
- **High-frequency operations**: operations that execute per-request, per-tick, or per-event
  document their expected rate and any throttling strategy. Undocumented high-frequency
  operations are Major.
- **Background tasks**: operations involving external I/O or unbounded computation should use
  an async task queue. A synchronous handler doing heavy computation without documented
  justification is Major.
- **In-system time**: any time-based mechanic must derive from the canonical in-system time
  source, not wall-clock time from the operating system, unless explicitly justified. Using
  OS wall-clock time for system-internal logic without justification is Major.

---

#### Dimension 9 - Acceptance Criteria Quality

- Each criterion is a binary, verifiable statement. "Works correctly" or "handles errors
  gracefully" without a specific measurement is Major.
- Each criterion maps to at least one test entry. A criterion with no test is Major.
- Criteria collectively cover the full scope stated in the goal. A scenario in the goal with
  no corresponding criterion is Critical.
- Criteria cover both the happy path and the most important failure modes. Absence of any
  failure-mode criteria for a feature that has failure modes is Major.

---

#### Dimension 10 - Test Coverage

- Every acceptance criterion has a test entry with: description, test type (unit / integration
  / e2e / manual), file path, and what it covers.
- Unit tests cover all domain and use-case logic with no I/O or database dependency. Domain
  logic tested only at the integration level is Major.
- Integration tests cover repository implementations and adapter layers against real
  infrastructure.
- Manual tests are listed only when automation is genuinely impractical. An unexplained
  manual test for something automatable is Major.
- At least one test covers the rejection or error path for every mutation operation. Absence
  of negative-path tests is Major.

---

#### Dimension 11 - Dependency Completeness

- Every upstream dependency (must exist before this work starts) is listed.
- Every downstream consumer (depends on this work's output) is listed.
- No circular dependencies between features or between domain aggregates.
- Cross-module dependencies are identified and integration boundaries are explicit.
- The dependency list is consistent with the parent plan's ordering. Any discrepancy is Major.

---

#### Dimension 12 - Definition of Done

- Every DoD item is binary: Done or Not Done with zero ambiguity.
- The DoD covers all applicable categories: implementation complete, all criteria pass, all
  tests pass, no architecture violations, all contracts documented, ADRs created for new
  decisions, knowledge-base docs updated, security self-assessed.
- A document introducing new persistence models that does not include "migration created and
  reviewed" in the DoD is Major.
- A document introducing new interface contracts that does not include "contract documented
  and backward-compatible" in the DoD is Major.

---

#### Dimension 13 - Scope Precision

- The scope is neither too broad (multiple independent features bundled) nor too narrow
  (trivial work dressed up as a plan entry).
- No scope creep: the implementation section does not contain work the parent plan marks as
  deferred and does not reach into other features' bounded contexts.
- Deferred sections are appropriate: deferred because the information genuinely does not
  exist yet, not because the section was skipped.

---

#### Dimension 14 - Cross-System Impact

- All systems outside this feature's bounded context that are affected are identified.
- Interface contract changes: any change to a contract another module consumes must list
  the consuming module as a required companion change.
- Persistence schema changes: if this work adds or modifies persistence models, migration
  dependencies and data migration risks are addressed.
- Integration event changes: if this work changes an event schema or adds a new event type,
  all consumers of that event are listed as downstream dependents.

---

#### Dimension 15 - Execution Hierarchy

A document optimized for execution presents information in the order a developer needs it,
not the order it was written.

- Can a developer read this document once and implement the work without consulting other
  documents for basic facts? List any specific missing facts.
- Are any sections ordered in a way that forces forward references? Identify the better order.
- Is there duplicated information that should be consolidated into one place?
- Is any architectural decision embedded in the document that belongs in an ADR instead?
- Is any ADR content duplicated in the document (should be a reference, not a copy)?

---

### Phase 4 - Pass 1 Output

#### 4a. Executive Summary

State concisely:
- Document type and stated purpose
- Pass 1 verdict: **Not Ready / Needs Work / Ready with Minor Fixes / Ready**
- Total findings: Critical: X, Major: X, Minor: X
- The single highest-priority gap that most threatens implementation quality or safety

#### 4b. Findings Table

Present all findings in a single table. Sort by severity (Critical first), then by dimension
number. The severity sort is non-negotiable.

| # | Severity | Dimension | Location | Finding | Fix | Reference |
|---|---|---|---|---|---|---|

#### 4c. Unleveraged Infrastructure Report

List every existing infrastructure item found in Phase 2b that the document should reference
but does not. For each item:
- Name and file path
- What it provides
- Where in the document it should appear
- One-sentence recommended change

If none found: "No unleveraged infrastructure identified."

#### 4d. Security Summary

Summarize the security posture:
- Authentication and authorization coverage
- Input validation coverage
- OWASP Top 10 categories that apply and how they are addressed (or not)
- Overall security verdict: **Secure / Needs Review / Insecure**

#### 4e. Companion Changes Required

List every change required in a different layer or system from the document's primary scope.
These are the most common cause of breakage when context-switching.

For each companion change:
- **What must change**: specific file, endpoint, schema, or artifact
- **Why**: the dependency that creates the requirement
- **When**: must ship in the same commit / can follow in the next commit / can follow later

If none: "No companion changes required."

#### 4f. Pass 1 Gate Decision

State one of:

- **PROCEED TO PASS 2**: No Critical or Major findings. Pass 2 will verify Minor findings
  and confirm readiness.
- **HALT - FIXES REQUIRED**: Every Critical and Major finding that must be resolved before
  Pass 2 begins is listed below. Do not proceed to Pass 2 until all items in this list have
  been addressed and re-audit has been explicitly requested.

---

## Pass 2 - Verification Audit

Run Pass 2 only after the author confirms all Critical and Major findings from Pass 1 have
been addressed. If Pass 1 returned "PROCEED TO PASS 2" with no fixes required, begin Pass 2
immediately by re-reading the document in its current state.

### Phase 5 - Re-read and Re-verify

1. Re-read the document at its current path in full. Do not rely on Pass 1 notes for the
   document's current content - the document may have changed.
2. Re-execute Phase 2 steps 2a, 2b, and 2c for any files added or modified since Pass 1.
3. For every Critical and Major finding from Pass 1, re-inspect the relevant section and
   record: **Resolved** / **Partially Resolved** / **Unresolved**, with the remaining issue
   stated precisely for any non-Resolved status.
4. Scan all active dimensions for new issues introduced by edits made between passes.

### Phase 6 - Pass 2 Output

#### 6a. Resolution Confirmation

For each Critical and Major finding from Pass 1:

| Pass 1 # | Finding Summary | Status | Remaining Issue (if not Resolved) |
|---|---|---|---|

#### 6b. New Findings (if any)

Any issues introduced by edits between Pass 1 and Pass 2, in the same format as the Pass 1
findings table.

If none: "No new findings introduced between passes."

#### 6c. Pass 2 Gate Decision

State one of:

- **PIPELINE MAY CONTINUE**: All Critical and Major findings from Pass 1 are Resolved. No
  new Critical or Major findings were introduced. Minor findings (if any) are noted for
  awareness but do not block continuation.
- **HALT - ESCALATE TO ORCHESTRATOR**: One or more Critical or Major findings remain
  Unresolved or Partially Resolved after two passes. The producing agent must escalate to
  its parent orchestrator. Each unresolved finding is listed with its status and what
  remains to be fixed.

Do not produce an updated version of the document unless the author explicitly requests it.
The purpose of this audit is to surface gaps, not to overwrite the author's work.
