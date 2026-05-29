---
name: constraint-schema-validation-gate
description: "Use when: implementing a phase-boundary handoff that must validate an assembled artifact against a contract schema before delivery."
mode: agent
---

## Schema Validation Gate

Before delivering any phase-transition artifact to the downstream orchestrator, validate
it against the corresponding contract schema.

Steps:

1. Locate the applicable schema at
   `contracts/schemas/{{phase-transition-name}}.schema.json`.
2. Verify every required field listed in the schema is present in the artifact and
   contains a non-empty, non-placeholder value.
3. Verify array fields contain at least one element where the schema requires it.
4. Verify all nested objects contain their required child fields.
5. If any required field is missing, empty, or still contains an unfilled
   `{{PLACEHOLDER_NAME}}`, do not deliver the artifact. Record the specific gaps and
   return to the step that should have produced the missing data.

Never pass an artifact that fails schema validation to the next phase. An incomplete
artifact propagates gaps through all downstream phases and produces unrecoverable
inconsistencies in the final system.
