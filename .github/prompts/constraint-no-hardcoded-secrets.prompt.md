---
name: constraint-no-hardcoded-secrets
description: "Use when: implementing infrastructure, persistence, or framework configuration that requires external service credentials or database connections."
mode: agent
---

## Secrets and Credentials Handling

Never hardcode credentials, connection strings, API keys, tokens, passwords, or any
other secret value in source code, configuration files, migration scripts, or
documentation artifacts.

Required patterns:

- All secrets must be read from environment variables at runtime using the platform's
  standard mechanism (e.g., `os.environ`, `process.env`, `Environment.GetEnvironmentVariable`).
- Where a secrets manager is available, use `{{SECRETS_MANAGER}}` to retrieve secrets
  by name rather than reading raw environment variables.
- Connection string templates must use placeholders:
  `{{DB_HOST}}`, `{{DB_PORT}}`, `{{DB_NAME}}`, `{{DB_USER}}`, `{{DB_PASSWORD}}`
- CI/CD pipeline definitions must reference secret store variables, never inline values.
- Runbooks and onboarding guides must instruct readers to populate their local `.env`
  file from a secure source; never provide example values that are real credentials.

Prohibited patterns:

- Inline string literals that look like passwords, tokens, or keys
- `.env` files committed to source control with real values
- Base64-encoded secrets embedded in YAML or JSON configuration
- Hardcoded IP addresses or hostnames for production systems
