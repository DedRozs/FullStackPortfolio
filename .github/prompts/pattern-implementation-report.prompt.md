---
name: pattern-implementation-report
description: "Use when: coordinating code-generation agents that must compile a file-list manifest of all created artifacts for orchestrator consolidation."
mode: agent
---

## Implementation Report Pattern

Every code-generation specialist must produce an Implementation Report as part of its
output. Orchestrators consolidate these reports into the `sourceCodeManifest` field of
the phase-transition artifact.

### Required Report Format

The Implementation Report is a Markdown list. Each item represents one created file:

```
- filePath: `{{layer}}/{{subdirectory}}/{{FileName}}.{{extension}}`
  layer: {{domain | application | adapters | infrastructure | presentation}}
  description: One sentence describing the class or module and its responsibility.
```

### Rules

- Every file created by this agent must appear in the report. Do not omit files.
- `filePath` must be the path relative to the project root, using forward slashes.
- `layer` must be one of the five Clean Architecture layers listed above. Use the layer
  that reflects where the file is placed, not what it depends on.
- `description` must be one sentence naming the class and its single responsibility.
  Do not describe what the file imports or what framework it uses.
- If a file already existed and was modified rather than created, include it with a note
  `(modified)` appended to the description.

### How orchestrators use this report

The parent orchestrator appends each specialist's report to the working document and,
at phase close, flattens all reports into `sourceCodeManifest` for the downstream
phase. Incomplete or incorrectly formatted reports cause gaps in QA coverage because
the code reviewer identifies test targets from this manifest.
