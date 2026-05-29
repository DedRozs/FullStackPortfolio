---
name: workflow-code-generation-from-spec
description: "Use when: creating an implementation agent that translates domain design specifications or architecture contracts into source code files."
mode: agent
---

## Code Generation from Specification Workflow

Follow this process pattern for implementation agents that translate specifications
into source code.

### Standard Process

1. Read the `ubiquitousLanguage` array and build a reference lookup. Every class name,
   method name, and key variable in generated code must match an approved term.
2. Read the relevant specification section (entities, value objects, events, use cases,
   adapters, etc.) from the upstream artifact.
3. For each specification item:
   a. Determine the correct file path based on the Clean Architecture layer and the
      bounded context: `domain/`, `application/`, `infrastructure/`, or `adapters/`.
   b. Generate the source file using the `{{TARGET_LANGUAGE}}` conventions.
   c. Use the ubiquitous language term as the class name; match method names to
      specified behaviors exactly.
   d. Verify the file imports only from layers that are inward or at the same level.
      Flag and fix any outward dependency before proceeding to the next file.
4. After all files are generated, verify no file retains a framework type, ORM
   annotation, or infrastructure dependency in a layer that must not have one.
5. Compile the Implementation Report: a Markdown list of all created files, each entry
   containing `filePath`, `layer`, and a one-line `description`.
6. Deliver the Implementation Report alongside the original upstream artifact to the
   downstream agent and report completion to the parent orchestrator.

### Never

- Never generate code that violates the dependency rule; inner layers never import
  from outer layers.
- Never use names not present in `ubiquitousLanguage`; domain language is the source
  of truth for all identifiers.
- Never create files outside the designated layer directory for the concept being
  implemented.
