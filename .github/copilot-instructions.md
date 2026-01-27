# Copilot Instructions for FullStackPortfolio

## Architecture Overview

This is a **Django + React SPA** portfolio application using **Clean Architecture** with **Domain-Driven Design** patterns. Django 6.0 serves as the backend API, React 19 with Vite as the frontend SPA.

### Bounded Contexts (apps/)
Each app is a self-contained bounded context with strict layer separation:
```
apps/{context}/
├── domain/           # Entities, Value Objects, Repository interfaces, Events
├── application/      # Services, Commands, Queries (use case orchestration)
├── infrastructure/   # Django ORM models, Repository implementations
└── presentation/     # Views (API controllers), URLs, Admin
```

**Dependency Rule**: Dependencies point inward only (presentation → application → domain ← infrastructure).

## Key Patterns

### Entities vs ORM Models
- **Domain entities** ([apps/blog/domain/entities/__init__.py](apps/blog/domain/entities/__init__.py)): Pure Python dataclasses with business logic
- **ORM models** ([apps/blog/infrastructure/models.py](apps/blog/infrastructure/models.py)): Django models for persistence only
- Repositories map between them (see `_to_entity()` in [apps/blog/infrastructure/repositories.py](apps/blog/infrastructure/repositories.py))

### Value Objects
Immutable, validated domain concepts using `@dataclass(frozen=True)`:
- Shared: `Email`, `PersonName` in [apps/shared/domain/value_objects/__init__.py](apps/shared/domain/value_objects/__init__.py)
- Context-specific: `Slug`, `Tag`, `PostContent` in [apps/blog/domain/value_objects/__init__.py](apps/blog/domain/value_objects/__init__.py)

### Commands & Queries (CQRS-lite)
- **Commands**: Frozen dataclasses representing write operations (e.g., `CreateBlogPostCommand`)
- **Queries**: Frozen dataclasses for read operations (e.g., `GetPublishedPostsQuery`)
- Located in `apps/{context}/application/commands/` and `queries/`

### Event-Driven Communication
- Domain events inherit from `DomainEvent` ([apps/shared/domain/events/__init__.py](apps/shared/domain/events/__init__.py))
- Published via `EventBus` after state changes in application services
- Events use past tense naming: `BlogPostCreated`, `BlogPostPublished`

### Dependency Injection Pattern
Factory functions provide dependencies in views:
```python
def get_blog_service() -> BlogApplicationService:
    return BlogApplicationService(
        repository=DjangoBlogPostRepository(),
        event_bus=get_event_bus(),
    )
```

## Developer Workflows

### Virtual Environment (Critical)
**Always activate before running any Python/Django commands:**
```bash
# Windows
.\.venv\Scripts\Activate.ps1

# After activation, prompt shows (.venv)
```
Install dependencies: `pip install -r requirements.txt`

### Backend (Django)
```bash
# Requires activated venv
python manage.py runserver         # Dev server at localhost:8000
python manage.py makemigrations    # After model changes
python manage.py migrate
```

### Frontend (React + Vite)
```bash
cd frontend
npm run dev      # Dev server with HMR
npm run build    # Build to staticfiles/frontend/
npm run lint     # ESLint
```

### Full Stack Development
1. Run `npm run build` in frontend/ to update staticfiles
2. Django serves React SPA via catch-all route (`re_path(r'^.*$', ...)`)
3. API routes are under `/api/{context}/`

## Code Conventions

### Adding a New Feature
1. Define entity/value objects in `domain/entities/` or `domain/value_objects/`
2. Create repository interface in `domain/repositories.py`
3. Add commands/queries in `application/commands/` and `application/queries/`
4. Implement use case in `application/services.py`
5. Create Django model in `infrastructure/models.py`
6. Implement repository in `infrastructure/repositories.py`
7. Add API views in `presentation/views.py`

### Naming Conventions
- Events: Past tense (`BlogPostCreated`, not `CreateBlogPost`)
- Commands: Imperative (`CreateBlogPostCommand`)
- Repositories: `{Entity}Repository` interface, `Django{Entity}Repository` implementation
- Value objects validate in `__post_init__`

### Business Logic Placement
- **Entities**: Invariants, state transitions (e.g., `BlogPost.publish()`)
- **Application Services**: Use case orchestration, cross-aggregate coordination
- **Never** in ORM models, views, or infrastructure

## API Structure
- `/api/blog/` - Blog posts, tags
- `/api/contact/` - Contact form submissions
- All other routes serve the React SPA

## Tech Stack
- Python 3.12+, Django 6.0, SQLite (dev)
- React 19, TypeScript 5.9, Vite 7, Tailwind CSS 4
- react-router-dom for client-side routing
