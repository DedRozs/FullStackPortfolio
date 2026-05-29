---
name: workflow-phase-orchestrator
description: "Use when: creating a senior phase orchestrator that must invoke multiple specialists serially and assemble a phase-transition artifact."
mode: agent
---

## Phase Orchestrator Workflow

Follow this process pattern for every phase orchestrator. Substitute phase-specific
artifact names, specialist names, and schema paths as required.

### Standard Process

1. Receive the upstream phase-transition artifact from the parent orchestrator.
   Verify that the artifact's `processValidation.readinessConfirmed` field is `true`
   (or the equivalent sign-off field for this phase). Halt and report to the parent
   if it is not.
2. Validate that all required input fields defined in the Input Contract are present
   and non-empty. Report any gaps before proceeding.
3. Create a working document at `knowledge-base/plans/active/This Project-{{phase-name}}.md` by copying
   the relevant template from `contracts/templates/` and populating `schemaVersion`
   and `projectName`.
4. For each specialist in the Team section (in strict serial order):
   a. Invoke the specialist with the required inputs.
   b. Wait for the specialist to confirm completion and deliver its output.
   c. Record the specialist output in the corresponding section of the working document
      before invoking the next specialist.
5. Assemble the phase-transition artifact from the completed working document, ensuring
   all required fields defined in the Output Contract are populated.
6. Validate the assembled artifact against the schema at
   `contracts/schemas/{{phase-transition-artifact-name}}.schema.json`.
   Correct any schema violations before proceeding.
7. Run a two-pass document audit on the assembled phase-transition artifact:

   **Pass 1:** Invoke `document-auditor` with the artifact path.
   - If `PROCEED TO PASS 2` is returned, advance immediately to Pass 2.
   - If `HALT - FIXES REQUIRED` is returned, resolve every blocking finding, then
     re-run schema validation (step 6), then re-invoke `document-auditor`. Repeat until
     `PROCEED TO PASS 2` is returned.

   **Pass 2:** Re-invoke `document-auditor` with the artifact path and the
   `pass1Findings` array populated.
   - If `PIPELINE MAY CONTINUE` is returned, advance to step 8.
   - If `HALT - ESCALATE TO ORCHESTRATOR` is returned, halt and report to the parent
     orchestrator with the full Pass 2 output. Do not advance.

8. Present the validated artifact to the user with a plain-language summary of key
   decisions made during the phase. Request explicit approval to proceed.
9. On user approval, deliver the artifact to the downstream orchestrator and report
   phase completion.

### Failure Handling

- If a specialist reports an error or delivers incomplete output, halt at that step.
  Record the failure and report it to the parent orchestrator.
- Never substitute a specialist's output or estimate missing fields to satisfy the
  schema. Return to the failing specialist with corrected inputs.
- If the user rejects the artifact, identify the specific objection, return to the
  specialist whose output contains the issue, and re-run from that point.
