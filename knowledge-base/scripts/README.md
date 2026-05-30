# Scripts

AI-generated utility scripts for This Project.

**Rule:** All AI-generated scripts must be created in this directory only. Never create
AI-generated scripts in the repository root, `.github/`, or `contracts/`.

## Available Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `archive-plans.ps1` | Moves all files from `knowledge-base/plans/active/` into a new timestamped, project-named subfolder under `knowledge-base/plans/archive/`. Preserves historical pipeline artifacts across multiple runs. | `.\knowledge-base\scripts\archive-plans.ps1 -ProjectName "my-project"` (run from repo root) |
| `resolve-tokens.ps1` | Replaces all static configuration `{{TOKEN}}` placeholders across `.github/` agent and prompt files with their resolved project values (language, framework, database, deployment target, Jira credentials, GitHub repo). Runtime input tokens (`{{BUG_DESCRIPTION}}`, `{{EntityName}}`, etc.) are intentionally left untouched. Run with `-DryRun` to preview before applying. | `.\knowledge-base\scripts\resolve-tokens.ps1 [-DryRun]` (run from repo root) |
| `validate-schemas.sh` | Validates all JSON files in `contracts/schemas/` are well-formed. Exits non-zero on any failure. | `bash knowledge-base/scripts/validate-schemas.sh` (run from repo root) |
| `validate-template.yml` | GitHub Actions workflow that runs four integrity checks on every push and PR: JSON schema validation, placeholder token audit, agent section completeness, and instruction file reference integrity. Copy to `.github/workflows/` to activate in CI. | Copy to `.github/workflows/validate-template.yml` |
| `qa-prompt-conformance.py` | Conformance checks for all `.prompt.md` files in `.github/prompts/`. Checks: frontmatter field order, name/filename match, model value, mode value, tool validity, absence of unresolved config placeholders, read-only tool restriction on constraint/pattern files. Requires pyyaml. | `.venv\Scripts\python.exe knowledge-base/scripts/qa-prompt-conformance.py` (run from repo root) |
| `qa-integration-tests.py` | Cross-file consistency checks for the prompt library: unique name values, resolvable instruction file paths, and valid agent file references in start-sdlc-session. Requires pyyaml. | `.venv\Scripts\python.exe knowledge-base/scripts/qa-integration-tests.py` (run from repo root) |
| `qa-e2e-test.py` | First-time user simulation E2E test for `implement-ticket.prompt.md`. Verifies all 7 phase orchestrators are named, required input fields (TICKET_ID, TARGET_LANGUAGE, FRAMEWORK_NAME) are present, TICKET_ID validation regex is present, coordinator constraint is stated, and workflow-gate.prompt.md delegation is present. | `.venv\Scripts\python.exe knowledge-base/scripts/qa-e2e-test.py` (run from repo root) |
| `health-check-prompts.py` | Deployment health check for the prompt library. Parses YAML frontmatter of all `.prompt.md` files and reports parse errors or unresolved configuration placeholders. Exits 0 if healthy, 1 if not. Run after cloning and after any prompt file edit. | `.venv\Scripts\python.exe knowledge-base/scripts/health-check-prompts.py` (run from repo root) |
| `ticket-cli.py` | Internal Ticketing System CLI. Full implementation of 18 subcommands (init-project, create, get, update, transition, add-comment, list-comments, add-worklog, list-worklogs, create-link, list-links, search, list-issues, set-epic-link, list-epic-children, add-label, remove-label, list-labels). Routes to local JSON store when TICKET_BACKEND=internal; exits 0 directing to mcp_com_atlassian_* tools when TICKET_BACKEND=jira (default). Python stdlib only. Single writer only. | `TICKET_BACKEND=internal .venv\Scripts\python.exe knowledge-base/scripts/ticket-cli.py <subcommand> [args]` (run from repo root) |
| `qa-field-parity-check.py` | QA script for the FieldParity manifest. Loads `knowledge-base/plans/tickets/field-parity.json`, validates structure, and prints a tabular summary of every IssueField parity status against the Jira REST API. Exits 0 if manifest is well-formed (missing-parity entries are acceptable when documented); exits 1 if manifest is malformed or unreadable. Python stdlib only. | `.venv\Scripts\python.exe knowledge-base/scripts/qa-field-parity-check.py` (run from repo root) |
| `gcs-cors.json` | CORS policy for the `ai-fullstack-portfolio.appspot.com` GCS bucket. Allows GET requests from the production domains so fonts and scripts can be loaded cross-origin. Reapply with: `gcloud storage buckets update gs://ai-fullstack-portfolio.appspot.com --cors-file=knowledge-base\scripts\gcs-cors.json` | `gcloud storage buckets update gs://ai-fullstack-portfolio.appspot.com --cors-file=knowledge-base\scripts\gcs-cors.json` |
| `seed_client_portal.py` | Populates the database with representative client_portal data for development and demo purposes. Creates a ClientOrganization, UserProfiles (client and staff), a Project, Milestones, Deliverables, DeliverableVersions, Approvals, MessageThreads, Messages, FileRecords, and InvoiceRecords. Safe to run multiple times (uses get_or_create). | `.venv\Scripts\python.exe knowledge-base/scripts/seed_client_portal.py` (run from repo root) |

## Tests

The `tests/` subdirectory contains the automated test suite for `ticket-cli.py`:

| Test file | Type | Count | Purpose |
|---|---|---|---|
| `tests/test_ticket_unit.py` | Unit | 38 | IssueKey generation, JQL parser, atomic write semantics - no filesystem I/O |
| `tests/test_ticket_integration.py` | Integration | 34 | Full CLI invocation contract (stdout-JSON / stderr-text) against a temporary ticket store |
| `tests/test_ticket_e2e.py` | End-to-end | 8 | First-user workflows: init-project, create, search, link, label, and epic flows |

Run all tests from the repo root:

```powershell
.venv\Scripts\python.exe -m pytest knowledge-base/scripts/tests/ -v
```

All 80 tests pass. No external dependencies beyond the Python stdlib and `pytest`.

## Adding a Script

Every script in this directory must:

1. Have a clear purpose documented in a comment block at the top of the file
2. Include at least one usage example in comments
3. Be listed in the table above

When asking the AI assistant to create a script, say:
"Create a script in knowledge-base/scripts/ that [purpose]."

## Script Categories

- **Archive** - Archive active plan artifacts into timestamped project-named folders for historical record-keeping.
- **Analysis** - Scan agent files, count placeholders, report structure
- **Validation** - Verify schema compliance, check artifact contracts
- **Documentation** - Auto-generate or sync documentation from agent files
- **Maintenance** - Bulk placeholder replacement, file reorganization helpers
