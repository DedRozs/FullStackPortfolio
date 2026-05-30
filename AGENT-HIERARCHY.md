# Agent Hierarchy

Complete reference tree for all agents in This Project.
Organized by level and phase. All cross-reference paths are relative to the workspace root.

All agents are implemented. No files are marked _(planned)_.

---

## Level 1: Top-Level Orchestrator

- [top-level-orchestrator.agent.md](.github/agents/top-level-orchestrator.agent.md) - Root interface; coordinates all seven SDLC phases in serial order and gates each phase transition on structured artifact review and user approval

---

## Commands Layer

Alternative VS Code Copilot slash-command entry points that route into the agent
hierarchy. Each command file is a thin launcher: it declares required input fields and
a phase invocation order, then delegates all execution to the appropriate phase
orchestrators via `workflow-gate.prompt.md`. Commands do not replace the top-level
orchestrator; they are additive entry points for scoped workflows.

- [start-sdlc-session.prompt.md](.github/prompts/start-sdlc-session.prompt.md) - Starts a full seven-phase SDLC session for a net-new project, from Discovery through Deployment, or resumes a paused session at any phase (`/start-sdlc-session`)
- [feature-kickoff.prompt.md](.github/prompts/feature-kickoff.prompt.md) - Runs a feature-scoped pipeline: Discovery (feature-scoped), Domain Modeling, Development, and QA (`/feature-kickoff`)
- [architecture-review.prompt.md](.github/prompts/architecture-review.prompt.md) - Runs the Architecture phase only against an existing codebase (`/architecture-review`)
- [bug-fix.prompt.md](.github/prompts/bug-fix.prompt.md) - Runs a targeted bug-fix pipeline: QA investigation, Development repair, and QA re-verification (`/bug-fix`)
- [create-epic.prompt.md](.github/prompts/create-epic.prompt.md) - Creates a Jira Epic with prioritized child User Stories from a feature idea, running feature-scoped Discovery and backlog prioritization (`/create-epic`)
- [implement-ticket.prompt.md](.github/prompts/implement-ticket.prompt.md) - Runs the full ticket implementation pipeline routed by ticket size, then posts implementation notes back to Jira (`/implement-ticket`)

Shared gate prompt used by all commands at phase boundaries:

- [workflow-gate.prompt.md](.github/prompts/workflow-gate.prompt.md) - Centralized phase-boundary gate; delegates artifact validation to workflow-artifact-validation.prompt.md and opens an explicit user approval gate before each phase advances

---

## Level 2: Senior Phase Orchestrators

- [discovery-orchestrator.agent.md](.github/agents/discovery-orchestrator.agent.md) - Coordinates the Discovery phase; collects vision, stakeholders, domain knowledge, and requirements; produces the discovery-to-architecture artifact
- [architecture-orchestrator.agent.md](.github/agents/architecture-orchestrator.agent.md) - Coordinates the Architecture phase; designs system structure, data model, security posture, and API contracts; produces the architecture-to-domain-modeling artifact
- [domain-modeling-orchestrator.agent.md](.github/agents/domain-modeling-orchestrator.agent.md) - Coordinates the Domain Modeling phase; translates architecture into a complete domain model specification; produces the domain-modeling-to-development artifact
- [development-orchestrator.agent.md](.github/agents/development-orchestrator.agent.md) - Senior orchestrator for the Development phase; coordinates four mid-level orchestrators in Clean Architecture layer order; produces the development-to-qa artifact
- [qa-orchestrator.agent.md](.github/agents/qa-orchestrator.agent.md) - Coordinates the QA phase; manages verification, defect routing, and re-verification; produces the qa-to-documentation artifact
- [documentation-orchestrator.agent.md](.github/agents/documentation-orchestrator.agent.md) - Coordinates the Documentation phase; produces architecture docs, API reference, runbooks, and ADR index; produces the documentation-to-deployment artifact
- [deployment-orchestrator.agent.md](.github/agents/deployment-orchestrator.agent.md) - Coordinates the Deployment phase; configures CI/CD, environments, monitoring, and rollback; reports completion to the top-level orchestrator

---

## Utility Agents

Utility agents operate outside the 7-phase pipeline. They are invoked on demand for
maintenance, housekeeping, and standalone workflows.

- [archive-manager.agent.md](.github/agents/archive-manager.agent.md) - On-demand utility that archives `knowledge-base/plans/active/` contents into a TICKET_KEY-scoped or bulk subfolder of `knowledge-base/plans/archive/` before or after a pipeline run
- [audit-document.agent.md](.github/agents/audit-document.agent.md) - Single-file specialist invoked once per document by `audit-all-documents.prompt.md`; performs a single-pass quality audit of one markdown file and returns a structured findings report with a gate verdict; not part of the ticket pipeline
- [document-auditor.agent.md](.github/agents/document-auditor.agent.md) - On-demand utility that performs a two-pass quality audit of any deliverable document; issues a gate decision that either permits pipeline continuation or halts for remediation; invoked automatically by every specialist and phase orchestrator after producing a deliverable
- [jira-epic-writer.agent.md](.github/agents/jira-epic-writer.agent.md) - Creates a Jira Epic and child User Stories from the backlog-prioritizer output, setting Given/When/Then acceptance criteria and capped Fibonacci story point estimates on each story; invoked by the `create-epic` command only

---

## Stage 0 - Intake Agents

Intake agents run at the start of every ticket-pipeline run (Stage 0 of
`implement-ticket.prompt.md`). They create the tracking ticket, read the source Jira
ticket, and snapshot codebase context before the first SDLC phase begins.

- [project-ticket-creator.agent.md](.github/agents/project-ticket-creator.agent.md) - Cross-cutting utility that creates a Jira issue at pipeline start, validates the returned TICKET_KEY, and returns the TICKET_KEY and initial SessionPath to the invoking command; invoked as step zero by all project-driven commands
- [ticket-intake-agent.agent.md](.github/agents/ticket-intake-agent.agent.md) - Reads a Jira ticket via mcp_com_atlassian_getJiraIssue, maps its fields to the mini-Discovery artifact format, determines ticket size from issue type, and writes the MiniDiscoveryArtifact to knowledge-base/plans/active/
- [codebase-context-agent.agent.md](.github/agents/codebase-context-agent.agent.md) - Reads the most recent archived pipeline artifacts and knowledge-base content to produce a bounded-context snapshot appended to the MiniDiscoveryArtifact for use by downstream phase orchestrators

## Close-out Agents

Close-out agents run after Gate 7 is approved. They create the pull request, merge the
feature branch to `{{GITHUB_BASE_BRANCH}}`, and update the source Jira ticket.

- [git-workflow-manager.agent.md](.github/agents/git-workflow-manager.agent.md) - Cross-cutting utility that manages the full Git lifecycle of a pipeline run: feature branch creation (startMode) and PR creation, auto-merge to {{GITHUB_BASE_BRANCH}}, Jira status transition to Done, and archive trigger (completionMode)
- [jira-ticket-updater.agent.md](.github/agents/jira-ticket-updater.agent.md) - Posts implementation notes as a Jira comment and transitions the source ticket to Done or the nearest equivalent using a best-match fallback sequence against available Jira workflow transitions

---

## Level 3: Mid-Level Orchestrators (Development Phase Only)

- [domain-implementation-orchestrator.agent.md](.github/agents/domain-implementation-orchestrator.agent.md) - Coordinates domain layer implementation; manages entity-implementer, value-object-implementer, and domain-event-implementer in serial order
- [use-case-orchestrator.agent.md](.github/agents/use-case-orchestrator.agent.md) - Coordinates use case layer implementation; manages use-case-implementer, input-port-designer, output-port-designer, and dto-designer in serial order
- [adapter-orchestrator.agent.md](.github/agents/adapter-orchestrator.agent.md) - Coordinates adapter layer implementation; manages typescript-type-generator, controller-implementer, presenter-implementer, repository-implementer, and event-handler-implementer in serial order
- [infrastructure-orchestrator.agent.md](.github/agents/infrastructure-orchestrator.agent.md) - Coordinates infrastructure layer implementation; manages framework-configurator, asset-pipeline-configurator, database-migration-writer, external-service-integrator, and di-container-configurator in serial order

---

## Level 4: Specialist Agents

### Discovery Phase (6 agents)

- [vision-analyst.agent.md](.github/agents/vision-analyst.agent.md) - Captures and documents the initial product vision and core problem statement from the user
- [stakeholder-analyst.agent.md](.github/agents/stakeholder-analyst.agent.md) - Identifies all affected parties, their roles, and their interests in the system
- [domain-vocabulary-elicitor.agent.md](.github/agents/domain-vocabulary-elicitor.agent.md) - Elicits domain vocabulary from the user and builds the preliminary domain glossary
- [business-analyst.agent.md](.github/agents/business-analyst.agent.md) - Translates domain knowledge and stakeholder needs into structured functional and non-functional requirements
- [backlog-prioritizer.agent.md](.github/agents/backlog-prioritizer.agent.md) - Prioritizes the requirements into a ranked product backlog with acceptance criteria
- [discovery-artifact-validator.agent.md](.github/agents/discovery-artifact-validator.agent.md) - Validates the discovery process, identifies gaps, and confirms readiness to advance to the Architecture phase

### Architecture Phase (7 agents)

- [architecture-constraints-definer.agent.md](.github/agents/architecture-constraints-definer.agent.md) - Establishes cross-system constraints, integration patterns, and compliance boundaries
- [solution-architect.agent.md](.github/agents/solution-architect.agent.md) - Designs the overall system structure, bounded contexts, and technology stack selection
- [frontend-architect.agent.md](.github/agents/frontend-architect.agent.md) - Decides rendering strategy, component layer model, state management pattern, frontend framework token, and build toolchain for the user-facing interface
- [data-architect.agent.md](.github/agents/data-architect.agent.md) - Defines the canonical data model, entity relationships, and data ownership boundaries
- [security-architect.agent.md](.github/agents/security-architect.agent.md) - Performs threat modeling, defines security controls, and identifies OWASP Top 10 mitigations
- [api-contract-designer.agent.md](.github/agents/api-contract-designer.agent.md) - Specifies all external and internal API contracts including request and response schemas
- [adr-writer.agent.md](.github/agents/adr-writer.agent.md) - Documents all architectural decisions as ADRs with context, decision, and consequences

### Domain Modeling Phase (7 agents)

- [ubiquitous-language-curator.agent.md](.github/agents/ubiquitous-language-curator.agent.md) - Establishes and documents the domain vocabulary; all subsequent domain modeling agents consume this vocabulary
- [entity-modeler.agent.md](.github/agents/entity-modeler.agent.md) - Identifies domain entities, their identities, invariants, and state transitions
- [value-object-modeler.agent.md](.github/agents/value-object-modeler.agent.md) - Identifies value objects, their validation rules, and equality semantics
- [aggregate-designer.agent.md](.github/agents/aggregate-designer.agent.md) - Defines aggregate boundaries, aggregate roots, and cross-aggregate reference rules
- [domain-event-designer.agent.md](.github/agents/domain-event-designer.agent.md) - Identifies domain events, their triggers, payloads, and consumer relationships
- [repository-interface-designer.agent.md](.github/agents/repository-interface-designer.agent.md) - Defines repository interfaces in domain language for each aggregate root
- [domain-service-designer.agent.md](.github/agents/domain-service-designer.agent.md) - Identifies domain services for business logic that spans multiple aggregates

### Development Phase - Domain Implementation (3 agents)

- [entity-implementer.agent.md](.github/agents/entity-implementer.agent.md) - Implements all domain entities in code per the domain model specification
- [value-object-implementer.agent.md](.github/agents/value-object-implementer.agent.md) - Implements all value objects in code per the domain model specification
- [domain-event-implementer.agent.md](.github/agents/domain-event-implementer.agent.md) - Implements all domain events in code following the CloudEvents standard

### Development Phase - Use Cases (4 agents)

- [use-case-implementer.agent.md](.github/agents/use-case-implementer.agent.md) - Implements application service classes for each use case
- [input-port-designer.agent.md](.github/agents/input-port-designer.agent.md) - Defines input port interfaces and command or query request models for each use case
- [output-port-designer.agent.md](.github/agents/output-port-designer.agent.md) - Defines output port interfaces and presenter contracts for each use case
- [dto-designer.agent.md](.github/agents/dto-designer.agent.md) - Designs data transfer objects for all use case inputs and outputs

### Development Phase - Adapters (5 agents)

- [typescript-type-generator.agent.md](.github/agents/typescript-type-generator.agent.md) - Translates DTO shapes and API contracts into TypeScript type artifacts for the adapter layer, including type aliases, discriminated unions, branded primitives, and runtime type-guard functions
- [controller-implementer.agent.md](.github/agents/controller-implementer.agent.md) - Implements controllers that receive external requests, validate input, and invoke use cases
- [presenter-implementer.agent.md](.github/agents/presenter-implementer.agent.md) - Implements presenters that transform use case output into external response formats
- [repository-implementer.agent.md](.github/agents/repository-implementer.agent.md) - Implements concrete repository classes against the domain repository interfaces
- [event-handler-implementer.agent.md](.github/agents/event-handler-implementer.agent.md) - Implements event handlers that subscribe to domain events and trigger downstream actions

### Development Phase - Infrastructure (5 agents)

- [framework-configurator.agent.md](.github/agents/framework-configurator.agent.md) - Configures the web or application framework, routing, and middleware
- [asset-pipeline-configurator.agent.md](.github/agents/asset-pipeline-configurator.agent.md) - Configures the frontend asset pipeline, bundler, CSS toolchain, environment-mode build scripts, and CI/CD integration hooks
- [database-migration-writer.agent.md](.github/agents/database-migration-writer.agent.md) - Creates database migration scripts aligned with the data model specification
- [external-service-integrator.agent.md](.github/agents/external-service-integrator.agent.md) - Implements anti-corruption layer adapters for all third-party services
- [di-container-configurator.agent.md](.github/agents/di-container-configurator.agent.md) - Wires all layer dependencies in the dependency injection container

### QA Phase (7 agents)

- [code-reviewer.agent.md](.github/agents/code-reviewer.agent.md) - Performs structural code review for Clean Architecture compliance and coding standards
- [unit-test-engineer.agent.md](.github/agents/unit-test-engineer.agent.md) - Writes and runs unit tests for all domain and use case logic without infrastructure dependencies
- [integration-test-engineer.agent.md](.github/agents/integration-test-engineer.agent.md) - Writes and runs integration tests for adapters and infrastructure components
- [e2e-test-engineer.agent.md](.github/agents/e2e-test-engineer.agent.md) - Writes and runs end-to-end tests covering critical user journeys
- [security-reviewer.agent.md](.github/agents/security-reviewer.agent.md) - Performs OWASP Top 10 assessment and identifies security vulnerabilities
- [performance-analyst.agent.md](.github/agents/performance-analyst.agent.md) - Evaluates performance characteristics and identifies bottlenecks
- [defect-repair-coordinator.agent.md](.github/agents/defect-repair-coordinator.agent.md) - Formats defect reports and routes them to the appropriate Development sub-team orchestrator for repair

### Documentation Phase (7 agents)

- [architecture-doc-writer.agent.md](.github/agents/architecture-doc-writer.agent.md) - Produces the architecture overview document including diagrams and design rationale
- [api-doc-writer.agent.md](.github/agents/api-doc-writer.agent.md) - Documents all API contracts with endpoint descriptions, schemas, and usage examples
- [readme-writer.agent.md](.github/agents/readme-writer.agent.md) - Generates the project README with setup instructions, entry points, and development workflow
- [onboarding-guide-writer.agent.md](.github/agents/onboarding-guide-writer.agent.md) - Creates the developer onboarding guide covering local setup and contribution workflow
- [runbook-writer.agent.md](.github/agents/runbook-writer.agent.md) - Creates operational runbooks for deployment, incident response, and routine maintenance
- [adr-indexer.agent.md](.github/agents/adr-indexer.agent.md) - Organizes and indexes all ADRs produced during Architecture and Development phases
- [decision-log-writer.agent.md](.github/agents/decision-log-writer.agent.md) - Compiles the full decision history across all phases into a searchable decision log

### Deployment Phase (6 agents)

- [ci-cd-engineer.agent.md](.github/agents/ci-cd-engineer.agent.md) - Configures the build and deployment pipeline for the target CI/CD platform
- [environment-configurator.agent.md](.github/agents/environment-configurator.agent.md) - Sets up and documents target environment configurations covering dev, staging, and production
- [release-coordinator.agent.md](.github/agents/release-coordinator.agent.md) - Manages the release process including versioning, changelogs, and deployment sequencing
- [monitoring-configurator.agent.md](.github/agents/monitoring-configurator.agent.md) - Establishes observability configuration including log aggregation, metrics collection, and alerting thresholds
- [health-check-validator.agent.md](.github/agents/health-check-validator.agent.md) - Verifies the deployed system against the monitoring baseline and reports health status
- [rollback-planner.agent.md](.github/agents/rollback-planner.agent.md) - Documents the rollback procedure for each deployment scenario
