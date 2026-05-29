---
name: workflow-domain-specification
description: "Use when: creating a domain modeling specialist that produces design specifications from ubiquitous language without generating source code."
mode: agent
---

## Domain Specification Workflow

Follow this process pattern for domain modeling specialists whose output is a design
specification document, not source code.

### Standard Process

1. Read the `ubiquitousLanguage` array from the upstream artifact and build a reference
   lookup of all approved domain terms. Every name used in specifications (classes,
   methods, fields, events) must match an approved term.
2. Read the bounded context map and identify which context owns the concepts this
   agent is specifying. Never define concepts that belong to a different bounded context.
3. For each item in the relevant input array (entities, value objects, events, services,
   or repository interfaces depending on this agent's scope):
   a. Confirm the concept name exists in `ubiquitousLanguage`.
   b. Draft the specification section: identity (if applicable), invariants, state
      transitions or behavior, relationships to other domain concepts, and the bounded
      context owner.
   c. Present the draft to the user for review before finalizing.
4. After all specifications are drafted and reviewed, assemble them into a single
   Markdown section in the working domain model document.
5. Verify no specification contains an implementation detail (import statement, ORM
   annotation, framework type, or language-specific syntax). Specifications describe
   behavior and structure in domain language only.
6. Deliver the completed specification section to the downstream agent and report
   completion to the parent orchestrator.

### Never

- Never generate source code; output is always a design specification in Markdown.
- Never introduce domain terms not present in the approved `ubiquitousLanguage` array
  without first adding them to the glossary.
- Never define a concept whose bounded context ownership is ambiguous; resolve
  ownership with the parent orchestrator before specifying it.
