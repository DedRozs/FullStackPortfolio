---
name: workflow-artifact-validation
description: "Use when: implementing a validation checkpoint that must confirm all required input fields are present before a phase or step advances."
mode: agent
---

## Artifact Validation Pattern

Before advancing past any validation checkpoint, confirm that the incoming artifact
meets all completeness requirements.

### Validation Steps

1. Check that the artifact exists and is non-empty.
2. For each field listed in the Input Contract as required:
   a. Confirm the field is present in the artifact.
   b. Confirm the field value is non-empty (not `null`, `""`, `[]`, or `{}`).
   c. Confirm the field value does not contain an unfilled `{{PLACEHOLDER_NAME}}`.
3. For array fields that must be non-empty, confirm at least one element is present.
4. For boolean sign-off fields (e.g., `readinessConfirmed`, `signOffGranted`), confirm
   the value is explicitly `true`. A missing field does not count as `true`.
5. If all checks pass, proceed to the next step.
6. If any check fails, compile a gap list with: field name, the reason it failed, and
   the agent responsible for producing that field. Report the gap list to the parent
   orchestrator. Do not proceed until all gaps are resolved.

### Never

- Never infer or default a missing required field; absence is always a failure.
- Never treat a partial value (e.g., a non-empty string that is clearly a placeholder)
  as a valid populated field.
- Never skip validation to meet a deadline or because the gap seems minor.
