---
name: constraint-serial-orchestration
description: "Use when: designing an orchestrator agent that must invoke child specialists in strict sequence and never in parallel."
mode: agent
---

## Serial Orchestration Requirement

All child specialist agents must be invoked in strict serial order. Never invoke two or
more specialists simultaneously or in parallel.

Rules:

- Do not invoke the next specialist until the current specialist has delivered its
  complete output and that output has been recorded in the working document.
- If a specialist reports an error or delivers incomplete output, halt and report the
  failure to the parent orchestrator before proceeding. Do not attempt to continue with
  downstream specialists.
- If a specialist times out or becomes unresponsive, report the failure immediately
  rather than skipping the specialist or substituting its output.
- The serial order listed in the Team section is mandatory. Do not reorder specialists
  based on perceived efficiency or availability.

Rationale: each specialist's output feeds into subsequent specialists as input. Parallel
invocation would cause data races on the working document and produce incomplete or
contradictory phase-transition artifacts.
