# FullStackPortfolio - AI Assistant Guidelines

## Codebase Identity

**Repository:** FullStackPortfolio
**Domain:** personal-portfolio
**Language:** Python 3.14
**Framework:** Django 6.0.5
**Database:** MySQL 8.x (Google Cloud SQL)
**Deployment:** Google App Engine + Cloud Run
**Primary Agent Language:** Markdown (agent definitions, contracts, prompts)
**Agent Runtime:** VS Code Copilot Agent Mode

## Architecture Overview

This Project uses a hierarchical multi-agent SDLC pipeline coordinated through a strict
chain of command. A single top-level orchestrator serves as the user's primary interface
and gates every phase transition on explicit user approval.

Seven SDLC phases run in strict serial order: Discovery, Architecture, Domain Modeling,
Development, QA, Documentation, and Deployment. Each phase is managed by a senior
orchestrator that coordinates specialist agents. The Development phase adds a mid-level
tier of four orchestrators corresponding to Clean Architecture layers.

Key patterns:
- **Hierarchical delegation**: Every task flows downward through the tree; no agent acts
  outside its defined scope.
- **Structured artifact handoffs**: Each phase produces a validated JSON artifact consumed
  by the next phase. Schemas live in `contracts/schemas/`; templates in
  `contracts/templates/`.
- **Instruction file enforcement**: Clean Architecture and DDD rules are injected via
  `.github/instructions/*.instructions.md` files referenced in every relevant agent.

## Critical Context for AI

### Code Organization

- Agent definitions: `.github/agents/`
- Prompt files: `.github/prompts/`
- Instruction files: `.github/instructions/`
- Phase artifact schemas: `contracts/schemas/`
- Phase artifact templates: `contracts/templates/`
- Documentation: `knowledge-base/content/`
- Development plans: `knowledge-base/plans/`
- Draft documentation: `knowledge-base/drafts/`
- AI-generated scripts: `knowledge-base/scripts/`

### Naming Conventions

- Agent files: `kebab-case-role.agent.md` (e.g., `vision-analyst.agent.md`)
- Prompt files: `kebab-case-purpose.prompt.md`
- Instruction files: `kebab-case-topic.instructions.md`
- Schema files: `phase-to-phase.schema.json`
- ADRs: `NNNN-kebab-case-title.md`

### Template Placeholder Tokens

Ten core tokens must be configured before the first pipeline run:

| Token | Description | Example |
|---|---|---|
| `This Project` | Human-readable project name | `MyApp` |
| `personal-portfolio` | Primary business domain | `e-commerce` |
| `Python` | Implementation language | `Python` |
| `Django` | Application framework | `FastAPI` |
| `MySQL` | Persistence technology | `PostgreSQL` |
| `Google App Engine` | Hosting platform | `AWS ECS` |
| `FSP` | Jira project key for ticket creation | `PROJ` |
| `93a7d59f-0d17-4391-a277-a7218e22a692` | Jira Cloud ID (from Atlassian admin) | `93a7d59f-...` |
| `https://ai-minion.atlassian.net` | Jira site base URL | `https://your-site.atlassian.net` |
| `DedRozs/FullStackPortfolio` | GitHub repository in owner/repo format | `DedRozs/FullStackPortfolio` |
| `main` | Base branch for feature branches | `main` |

Run `Select-String -Path ".github\agents\*.agent.md" -Pattern "\{\{" -Recurse` (Windows) or
`grep -r "{{" . --include="*.agent.md"` (macOS/Linux) to find unresolved tokens.

### Key Abstractions

- **Phase artifact**: A structured JSON document that is the sole output of a phase and
  the sole input of the next phase. Validate against the schema before passing.
- **Agent file**: A Markdown file with YAML frontmatter plus role,
  input/output contracts, process steps, and constraints sections.
- **Constraint injection**: Rules from `*.instructions.md` files are enforced by
  including them in an agent's `## Constraints` section by path reference.
- **Coordinator constraint**: The top-level orchestrator must never perform work directly.
  All content production is delegated to subagents. The only inline output allowed is
  delegation instructions, verbatim summaries, and approval gate requests.

### Common Patterns

```markdown
<!-- Agent file structure -->
---
decription: [One-sentence description of the agent's role]
name: "[Role Name]"
---
# Role Name

## Role
[Single sentence describing this agent's purpose]

## Input Contract
**Receives from:** [Parent agent]
**Format:** [Structure of input]
**Required fields:** [List]

## Output Contract
**Produces for:** [Consumer agent]
**Format:** [Structure of output]
**Required fields:** [List]

## Process
[Numbered steps in strict serial order]

## Constraints
[Hard rules; include instruction file references for CA/DDD compliance]
```

### Anti-Patterns to Avoid

- Inline content production by the top-level orchestrator - delegate to the correct
  subagent instead.
- Skipping schema validation at a phase gate - always validate before advancing.
- Parallel phase execution - phases are strictly serial; never run two simultaneously.
- Business logic in agent frontmatter - process steps belong in the `## Process` section.
- Placeholder tokens left in delivered artifacts - all `{{VARIABLE}}` tokens must be
  resolved before the artifact is used.

### Testing Philosophy

- No test framework (agents are prose); quality is enforced by schema validation and the
  review/approval gates built into the top-level orchestrator process.
- Schema validation runs at every phase transition using contracts in `contracts/schemas/`.
- Instruction file compliance is verified by the QA code-reviewer agent.

### Development Workflow

1. **Before editing an agent:**
   - Read the agent file and its role in `AGENT-HIERARCHY.md`.
   - Identify which phase it belongs to and which constraints apply.
   - Check whether changes affect the input or output contract.

2. **During editing:**
   - Keep frontmatter minimal - only `description`, `name`, and `agents:` (orchestrators only).
   - Follow the standard section order: Role, Authority, Input Contract, Output Contract,
     Team (if orchestrator), Process, Constraints.
   - Reference instruction files by path in Constraints, do not inline their content.

3. **Before committing:**
   - Confirm all `{{PLACEHOLDER}}` tokens are resolved in the modified file.
   - Update `knowledge-base/content/` docs if the change affects architecture or process.
   - Create an ADR in `knowledge-base/content/decisions/` for structural changes.

### File Modification Rules

**When editing agent files, always:**
- Do not add `tools:` or `model:` to frontmatter - these keys must not exist in any file.
- Maintain the standard section order.
- Keep process steps numbered and strictly serial.
- Update `AGENT-HIERARCHY.md` if the agent's role description changes.

**Never:**
- Add `tools:` or `model:` keys to any agent file.
- Merge two agents into one (one responsibility per agent).
- Remove the Constraints section from any agent.
- Produce artifact content inline in the top-level orchestrator.

### Script Creation Rules

**AI-generated scripts MUST go in `knowledge-base/scripts/` only.**

Each script must have:
- Clear purpose documented at the top of the file.
- Usage examples in comments.
- An entry in `knowledge-base/scripts/README.md`.

**Never create scripts in:**
- Repository root.
- `.github/` directories.
- `contracts/` directories.

### Key Documentation

- [Architecture Overview](knowledge-base/content/architecture/overview.md)
- [Component Map](knowledge-base/content/components/overview.md)
- [Development Conventions](knowledge-base/content/development/conventions.md)
- [Decision Records](knowledge-base/content/decisions/README.md)
- [Agent Hierarchy](AGENT-HIERARCHY.md)

### Decision Authority

**AI Can Decide:**
- Prose improvements and formatting within existing agent files.
- Documentation updates that do not change agent responsibilities.
- Script logic within `knowledge-base/scripts/`.

**AI Should Ask:**
- Adding or removing agents from the hierarchy.
- Changing phase artifact schemas.
- Altering tool permissions in agent frontmatter.
- Changes to the coordinator constraint.

**AI Must Never:**
- Delete agent files without explicit instruction.
- Change a phase artifact schema without updating all agents that consume it.
- Modify `.github/instructions/` content without an ADR.

### Response Style

- **Be concise** - Direct answers; skip preamble.
- **Show examples** - Concrete examples over abstract explanations.
- **Reference docs** - Link to `knowledge-base/` when relevant.
- **Explain trade-offs** - When proposing changes, name the cost.

## Knowledge Base Maintenance

### When to Update Docs

**Automatically consider updating:**
- `knowledge-base/content/architecture/` when adding or removing agents or phases.
- `knowledge-base/content/components/` when agent responsibilities change.
- ADRs when structural decisions are made about the hierarchy or contracts.

**How to update:**
1. Generate draft in `knowledge-base/drafts/`.
2. Review for accuracy.
3. Move to `knowledge-base/content/` after approval.
4. Delete the source draft from `knowledge-base/drafts/` after confirming the content file is correct.

### Documentation Quality

Good documentation:
- Explains WHY the design is structured this way, not just WHAT the structure is.
- Includes concrete examples from the actual agent files.
- Links to related agents and instruction files.
- Notes known constraints and trade-offs.

---

## Auto-Commit Configuration

AUTO_COMMIT_ENABLED: false
AUTO_COMMIT_DOCS_ENABLED: true
LAST_DOCUMENTATION_UPDATE: null

### Auto-Commit Rules

**Auto-commit documentation when:**
- Agent file committed - Documentation updated in same commit.
- New agent added - Component docs auto-generated.
- Phase artifact schema changed - Contract documentation updated.
- Instruction file changed - Architecture docs updated.

**Never auto-commit:**
- Agent `.agent.md` files (always requires explicit commit).
- Schema or contract files (always requires explicit commit).
- Instruction files (requires review).

**Commit Message Format:**
```
docs: update [component/area] documentation

- Updated for [change description]
- Regenerated [specific docs]
- Added documentation for [new agent/phase]

[Automated commit - reviewed by developer]
```

## Boy Scout Rule

**Always leave code cleaner than you found it.**

When touching any file during implementation or review, make small improvements in passing:

- Rename unclear variables and functions to match the ubiquitous language of the domain
- Extract magic numbers and repeated literals to named constants
- Remove unused imports and dead code
- Fix obvious style violations (naming, formatting) in lines you already touch
- Add missing type hints or docstrings only on code you are changing

Do not treat cleanup as a separate phase — apply it incrementally on every edit. Do not refactor code that is not related to the current task.
