---
name: workflow-defect-feedback-loop
description: "Use when: implementing QA orchestration that must manage defect discovery, routing to development, repair, and re-verification cycles."
mode: agent
---

## Defect Feedback Loop Workflow

Follow this process pattern whenever QA findings must be routed for repair and
re-verified before a phase can complete.

### Standard Process

1. Collect `defectFindings` from all review and test specialist agents. Each finding
   must include: `defectId`, `filePath`, `description`, `severity`, and
   `reportingAgent`.
2. Assign a unique `defectId` to any finding that lacks one, using the format
   `DEF-{{sequence number}}`.
3. Group defects by owning layer (domain, application, adapters, infrastructure).
4. Route each defect group to the appropriate development orchestrator with:
   - The full defect entry list for that layer
   - The original source file paths
   - The repair acceptance criteria (what must be true for the defect to be closed)
5. Wait for the development orchestrator to confirm repair completion and deliver
   updated file paths.
6. Re-invoke the specialist agent that originally reported each defect with the updated
   files. Confirm the defect is no longer present in the re-verification output.
7. Mark each defect `resolved` once the reporting specialist confirms the fix.
8. If a re-verification reveals the defect is still present, return to step 4 with a
   note that this is a second repair attempt.
9. After all defects are resolved, compile the defect summary:
   `totalDefectsFound`, `totalDefectsResolved`, and `unresolvedDefects` (must be empty
   before the phase can close).

### Never

- Never close a defect without re-verification from the original reporting specialist.
- Never route a defect to a layer that did not produce the violation.
- Never allow the phase to complete while `unresolvedDefects` is non-empty.
