---
name: constraint-read-only-analysis
description: "Use when: creating a review or audit agent that must analyze artifacts without modifying any source file."
mode: agent
---

## Read-Only Analysis Constraint

This agent performs analysis only. It must not create, modify, or delete any source
file, artifact, or working document.

Rules:

- Never call `create_file`, `replace_string_in_file`, `edit`, or any equivalent
  write tool on source files or artifacts under review.
- Never apply suggested fixes directly; record every finding as an observation in the
  output report and let the appropriate specialist agent perform any remediation.
- Never reformat, reorder, or rewrite content in reviewed files, even if the change
  would be purely cosmetic.
- If a critical defect is discovered, escalate by adding it to the `defectFindings`
  section of the output report. Do not attempt to repair it inline.

Output from this agent is always a structured report delivered to the parent
orchestrator. The report must describe findings precisely enough that a downstream
repair agent can act on each finding without ambiguity.
