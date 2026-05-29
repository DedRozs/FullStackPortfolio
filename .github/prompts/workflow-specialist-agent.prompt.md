---
name: workflow-specialist-agent
description: "Use when: creating a single-responsibility specialist agent that receives structured input, produces a deliverable, and reports results to an orchestrator."
mode: agent
---

## Specialist Agent Workflow

Follow this process pattern for every single-responsibility specialist agent. Substitute
the agent's specific domain actions in steps 3 through N.

### Standard Process

1. Receive the input artifact or extracted fields delivered by the upstream agent or
   orchestrator.
2. Validate that all fields listed in the Input Contract are present and non-empty.
   If any required field is missing, halt and report the gap to the parent orchestrator
   before proceeding.
3. Perform the first domain-specific action for this agent's responsibility.
4. Perform subsequent domain-specific actions, one atomic step at a time.
   Complete each step fully before advancing to the next.
5. Assemble the output in the format specified by the Output Contract.
6. Verify the assembled output contains every required field. If any field is missing
   or contains an unfilled placeholder, correct it before delivery.
7. Deliver the output to the downstream agent specified in the Output Contract and
   report completion to the parent orchestrator.

### Two-Pass Audit Loop

After step 7, every specialist must run a two-pass document audit before the pipeline
may continue.

**Pass 1:**

8. Invoke the `document-auditor` agent with the `documentPath` of the deliverable
   produced in steps 3-5.
9. Receive the Pass 1 output. If the gate decision is `PROCEED TO PASS 2`, advance
   immediately to step 10.
   If the gate decision is `HALT - FIXES REQUIRED`, address every blocking finding
   listed in the gate decision, then re-invoke `document-auditor` with the updated
   `documentPath`. Repeat until `PROCEED TO PASS 2` is returned.

**Pass 2:**

10. Re-invoke `document-auditor` with `documentPath` and the `pass1Findings` array
    populated with the IDs of all findings addressed since Pass 1.
11. Receive the Pass 2 output.
    - If the gate decision is `PIPELINE MAY CONTINUE`, report completion to the parent
      orchestrator and advance.
    - If the gate decision is `HALT - ESCALATE TO ORCHESTRATOR`, halt and escalate to
      the parent orchestrator with the full Pass 2 output. Do not advance in the pipeline.

### Scope Rules

- Never perform actions outside the single responsibility stated in the Role section.
- Never modify artifacts or files owned by a different phase or agent.
- Never advance to the next step if the current step produced an error or incomplete
  result. Stop and report the failure.
- Never pass natural language summaries to agents expecting structured artifacts;
  all inter-agent outputs must conform to the defined contract format.
