---
name: workflow-documentation-synthesis
description: "Use when: creating a documentation specialist that aggregates information from multiple prior artifacts into a single cohesive reference document."
mode: agent
---

## Documentation Synthesis Workflow

Follow this process pattern for documentation agents that aggregate content from
multiple source artifacts.

### Standard Process

1. Receive the list of source artifacts and file paths from the parent orchestrator.
   Verify all listed sources exist and are readable before proceeding.
2. Read each source artifact in full. Do not skip sections; the synthesis step in step 3
   requires the full content of every source.
3. Identify the content required for each section of the target document. Extract
   relevant content verbatim where precision matters (e.g., API contracts, ADR
   decisions). Summarize for narrative sections (e.g., overview, rationale).
4. Verify all required sections defined in the Output Contract are covered by at least
   one source artifact. If a required section has no source content, flag it as a gap
   and report to the parent orchestrator before writing.
5. Write the document to the designated path in `knowledge-base/` or the path specified
   by the parent orchestrator.
6. Verify the written document contains all required sections and is internally
   consistent (no contradictory statements, no references to artifacts that do not exist,
   no unfilled `{{PLACEHOLDER_NAME}}` values).
7. Deliver the document file path to the parent orchestrator and report completion.

### Never

- Never fabricate content that is not present in the source artifacts.
- Never omit a required section because the source artifact is incomplete; flag the gap
  and wait for resolution.
- Never write documents outside the `knowledge-base/` directory unless explicitly
  directed by the parent orchestrator.
