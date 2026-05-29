# Coding Conventions

Conventions for all code written in FullStackPortfolio. Follow these in every file
you touch (Boy Scout Rule: leave the code cleaner than you found it).

---

## General Principles

- Clean Architecture: dependencies point inward only. No framework types in domain logic.
- DDD tactical patterns apply to any non-trivial domain objects.
- SOLID at all times; prefer composition over inheritance.
- Inject all dependencies; never hard-wire.
- No magic numbers or strings - use named constants or enums.
- No dead code; delete rather than comment out.
- Methods: short, single level of abstraction, single responsibility.

---

## Python / Django

### Naming

| Construct | Convention | Example |
|---|---|---|
| Module / file | `snake_case` | `contact_service.py` |
| Class | `PascalCase` | `ContactSubmission` |
| Function / method | `snake_case` | `send_confirmation_email` |
| Variable | `snake_case` | `submission_id` |
| Constant | `UPPER_SNAKE_CASE` | `MAX_MESSAGE_LENGTH` |
| Django model | `PascalCase` singular | `ContactSubmission` (not `ContactSubmissions`) |
| URL pattern name | `kebab-case` | `contact-submit` |
| App label | `snake_case` | `contact` |

No abbreviations unless universally known (`id`, `url`, `dto`). Use domain language
from the concept document for all names.

### File Layout

Each Django app follows this structure:

```
apps/<app_name>/
    __init__.py
    admin.py          Model registrations for Django admin
    apps.py           AppConfig
    forms.py          Django Form classes (if applicable)
    models.py         ORM models
    tasks.py          Django Q2 async task functions (if applicable)
    urls.py           URL patterns (included from core/urls.py)
    views.py          View classes/functions
    tests/
        __init__.py
        test_views.py
        test_models.py
        test_forms.py
    templates/
        <app_name>/
            base.html     (if app has its own base)
            index.html
```

### Views

- Prefer class-based views for CRUD; function-based views are fine for simple actions.
- No business logic in views. Views validate input and call service/task functions.
- Always return explicit HTTP status codes (do not rely on Django defaults for errors).

### Models

- Every model has a `__str__` method returning a human-readable identifier.
- Use `verbose_name` and `verbose_name_plural` on the `Meta` class.
- Never put business logic in model methods beyond simple computed properties.
- Field ordering: primary key implied, then foreign keys, then core fields, then
  timestamps (`created_at`, `updated_at`) last.

### Settings

- No hardcoded secrets in `settings.py`. All sensitive values read from `os.environ`.
- `DEBUG` must default to `False` if the environment variable is absent.
- Use `django.core.management.utils.get_random_secret_key()` to generate `SECRET_KEY`.

### URL Configuration

- Each app defines its own `urls.py` with an `app_name` for namespacing.
- `core/urls.py` includes app URL files with a path prefix.
- URL pattern names use `kebab-case`.

### Async Tasks (Django Q2)

- All external API calls (SendGrid, Twilio, OpenAI) run in `tasks.py` as async tasks.
- Tasks are idempotent where possible (safe to retry on failure).
- Tasks accept only serializable arguments (no Django model instances - pass PKs).

---

## JavaScript / React

- Naming: PascalCase for components, camelCase for variables/functions, UPPER_SNAKE_CASE
  for constants.
- One component per file; file name matches component name.
- No business logic in components. Components render state; they call service functions.
- All API calls go through a centralized service layer, not inline in components.

---

## Commit Messages

Format: `<type>: <short description>`

Types:
- `feat` - new feature
- `fix` - bug fix
- `refactor` - code restructuring without behavior change
- `test` - adding or updating tests
- `docs` - documentation only
- `chore` - build scripts, dependency updates, configuration

Examples:
```
feat: add contact form POST handler
fix: handle SendGrid API timeout in email task
docs: update development setup for mysqlclient on Windows
```

Documentation commits that accompany code changes may be combined:
```
feat: implement contact form

- Add ContactSubmission model
- Add contact view and URL routing
- Add async email/SMS tasks
- Update data model docs and component map
```

---

## Testing

- Test pyramid: unit tests (no I/O) > integration tests (real DB) > e2e.
- All business logic and service functions must be unit-testable without infrastructure.
- Test names: `test_<context>_<action>_<expected_outcome>`.
  Example: `test_contact_form_with_empty_email_returns_400`
- Test files mirror source files: `views.py` -> `tests/test_views.py`.
- Do not use production credentials in tests. Use environment-mocked or test doubles.

---

## Security

- Never log credentials, tokens, or PII.
- Validate all user input at the boundary (Django forms or DRF serializers).
- CSRF protection must remain enabled for all form endpoints.
- Do not disable Django's security middleware.
- See OWASP Top 10 for the full checklist.
