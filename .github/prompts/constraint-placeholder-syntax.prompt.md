---
name: constraint-placeholder-syntax
description: "Use when: authoring any template agent that must remain reusable across multiple projects and configurations."
mode: agent
---

## Placeholder Syntax Requirement

Never hardcode project-specific configuration values in the body text of any template
agent or prompt file that must remain reusable across projects. All configuration slots
in body text must use `{{PLACEHOLDER_NAME}}` syntax.

**Frontmatter exception:** Frontmatter fields (`name`, `description`, `mode`, `model`,
`tools`) in delivered prompt and agent files must always contain resolved concrete
values - never placeholder tokens. Placeholder tokens in frontmatter fields cause
VS Code Copilot to fail silently when loading the prompt.

Configuration values that must use placeholder syntax in body text:

- Project name - use `This Project`
- Target language - use `{{TARGET_LANGUAGE}}`
- Framework name - use `{{FRAMEWORK_NAME}}`
- Database engine - use `{{DATABASE_ENGINE}}`
- Domain terms and bounded context names - use `{{DOMAIN_NAME}}` and equivalent
- Environment names (dev, staging, prod) - use `{{ENVIRONMENT_NAME}}`
- Message broker - use `{{MESSAGE_BROKER}}`
- Cloud provider or deployment target - use `{{DEPLOYMENT_TARGET}}`
- Secrets manager - use `{{SECRETS_MANAGER}}`

If a value is project-specific and no placeholder exists in this list, introduce a new
`{{DESCRIPTIVE_NAME}}` placeholder and document it in `README.md` under the placeholder
configuration table.
