---
name: workflow-gate
description: "Use when: advancing between two consecutive SDLC phases; delegates artifact completeness validation to workflow-artifact-validation.prompt.md and opens an explicit user approval gate before the next phase begins."
mode: agent
---

Centralized phase-boundary gate that validates a completed phase artifact and requests
explicit user approval before the next phase begins.

## Gate Procedure

Execute all steps in strict serial order. Do not skip any step.

1. **Receive context.** Confirm the invoking Command has supplied:
   - `phaseName` - the name of the phase that just completed (e.g., `discovery`).
   - `artifactPath` - the workspace-relative path to the completed phase artifact JSON
     file (e.g., `knowledge-base/plans/active/discovery-to-architecture.json`).
   - `requiredFields` - the list of field names that must be present and non-empty in
     the artifact per the phase output contract.

   If any of these three inputs are absent, halt immediately and report to the invoking
   Command: "WorkflowGate invocation is missing required context: [list missing items].
   Cannot proceed."

2. **Delegate validation.** Invoke `workflow-artifact-validation.prompt.md` with the
   artifact at `artifactPath` and the `requiredFields` list. Do not perform any
   field-level validation inline; all completeness and placeholder checks are performed
   exclusively by that prompt.

3. **Evaluate validation result.**
   - If validation reports one or more gaps: proceed to step 4 (Gap Report).
   - If validation reports all fields present and no unfilled placeholder tokens: proceed
     to step 5 (Approval Gate).

4. **Gap Report (validation failed).** Present the following structured report to the
   user and halt:

   ```
   Phase Validation Failed: {{phaseName}}
   Artifact: {{artifactPath}}

   The following gaps must be resolved before this phase can be approved:
   [gap list from workflow-artifact-validation.prompt.md]

   Resolution: The responsible agent(s) listed above must address each gap.
   Re-invoke this WorkflowGate after gaps are corrected.
   ```

   Do not proceed past this step. Return control to the invoking Command with a HALT
   signal.

5. **Approval Gate (validation passed).** Present the following summary to the user:

   ```
   Phase Complete: {{phaseName}}
   Artifact: {{artifactPath}}
   Validation: All required fields present. No unfilled placeholder tokens detected.

   Review the completed phase artifact before approving advancement to the next phase.

   Type APPROVE to continue or REJECT to halt.
   ```

6. **Evaluate user response.**
   - On `APPROVE`: respond with "Phase {{phaseName}} approved. Advancing to the next
     phase." Return an APPROVED signal to the invoking Command.
   - On `REJECT`: respond with "Phase {{phaseName}} halted at user request. Identify
     what must be corrected and re-invoke the WorkflowGate when ready." Return a HALT
     signal to the invoking Command.
   - On any other input: re-present the approval prompt from step 5 exactly once. If the
     user's second response is also unrecognized, treat it as REJECT.

## Never

- Never auto-approve; always present the ApprovalGate to the user and await an explicit
  response.
- Never inline any field-level validation logic; all such checks belong exclusively in
  `workflow-artifact-validation.prompt.md`.
- Never suppress a validation failure or gap; every gap must be named and reported.
- Never advance to the next phase after a REJECT or HALT signal.
