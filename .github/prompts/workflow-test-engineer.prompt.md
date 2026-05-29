---
name: workflow-test-engineer
description: "Use when: creating a test automation agent targeting a specific level of the test pyramid within the QA phase."
mode: agent
---

## Test Engineer Workflow

Follow this process pattern for all test automation agents. The specific isolation level
(unit, integration, or e2e) is defined in the agent's Role section.

### Standard Process

1. Receive the `sourceCodeManifest` from the parent orchestrator. Confirm it is non-empty
   and contains entries for the layer(s) this agent targets.
2. Identify the test targets for this isolation level:
   - **Unit tests** - domain entities, value objects, domain events, and domain services.
     No I/O, no infrastructure. Test each class in isolation with no mocks of domain types.
   - **Integration tests** - repository implementations, external service adapters, and
     event handlers. Use real infrastructure (test containers or equivalent); mock nothing
     that has a real implementation.
   - **E2E tests** - critical user-facing paths through the deployed system. One test per
     acceptance criterion in the prioritized backlog.
3. For each test target, write one or more test cases using the naming convention:
   `Given_[context]_When_[action]_Then_[expected outcome]`
4. Place test files in the directory that mirrors the source structure:
   `tests/unit/`, `tests/integration/`, or `tests/e2e/`.
5. Execute all tests and collect results.
6. For any failing test or any source file with no corresponding test, create a defect
   entry with: file path, missing or failing test description, and severity.
7. Compile the test results report with: total tests written, total passed, total failed,
   coverage percentage (unit level only), and the defect entry list.
8. Deliver the report to the parent orchestrator.

### Never

- Never mock a type that has a real implementation in the scope being tested.
- Never write tests that depend on execution order or shared mutable state.
- Never skip writing tests for domain logic on the grounds that it "looks correct."
