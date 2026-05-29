---
name: architecture-review
description: Runs the Architecture phase only against an existing codebase, producing an architecture-to-domain-modeling artifact capturing the current structural state and any identified concerns.
mode: agent
---

Run the Architecture phase against an existing codebase to assess its structural state and document identified concerns.

## Required Input Fields

- This Project: Human-readable name of the project under review
- {{EXISTING_CODEBASE_PATH}}: Workspace-relative path to the root of the existing codebase
- {{ARCHITECTURE_CONCERNS}}: Comma-separated list of specific architectural concerns to investigate (e.g., "dependency direction violations, missing abstraction layers, tight coupling")

## Phase Invocation Order

0. project-ticket-creator (step zero - project-driven command; create Jira issue under
   {{JIRA_PROJECT_KEY}}, receive TICKET_KEY and sessionPath before any artifact is written;
   skip this step and run in offlineRun mode if Jira integration is unavailable)
1. architecture-orchestrator

Collect all Required Input Fields from the user, then invoke `workflow-gate.prompt.md` after the architecture phase completes, passing the produced artifact path and required output fields. Pass all Required Input Fields to `architecture-orchestrator` to begin execution.
