I am implementing a trading blog feature for my Django + React portfolio application. The project follows Clean Architecture with Domain-Driven Design patterns.

## Project Context

- **Workspace**: FullStackPortfolio
- **Architecture**: Django 6.0 backend, React 19 + Vite frontend
- **Pattern**: Clean Architecture with DDD (entities, value objects, repositories, domain events)
- **Existing blog**: `apps/blog/` - use this as a reference for patterns and conventions

## Implementation Plan

The full plan is documented in `TRADING_BLOG_PLAN.md` in the project root. Read this file first to understand the complete scope.

## Your Task

Implement **Phase [4]** of the trading blog.

Phase reference:
| Phase | Name | Key Deliverables |
|-------|------|------------------|
| 1 | Domain Layer | Entities, value objects, repository interfaces, events |
| 2 | Infrastructure Layer | Django models, yfinance client, repository implementations |
| 3 | Application Layer | Commands, queries, application service |
| 4 | Content Generation | AI prompts for each post type, generator service |
| 5 | Presentation Layer | Views, URLs, admin, feeds, sitemaps |
| 6 | Frontend (React) | List page, detail page, instrument filters, routing |
| 7 | Scheduling | Management commands, cron configuration |
| 8 | Testing | Unit tests, integration tests, e2e tests |

## Architecture Requirements

Follow the existing patterns in `apps/blog/`:

1. **Domain Layer** (`domain/`):
   - Entities are pure Python dataclasses with business logic
   - Value objects are frozen dataclasses with validation in `__post_init__`
   - Repository interfaces are abstract base classes
   - Domain events inherit from shared `DomainEvent` base class

2. **Infrastructure Layer** (`infrastructure/`):
   - Django ORM models are separate from domain entities
   - Repositories implement domain interfaces and map ORM ↔ entities
   - External service clients (like yfinance) go here

3. **Application Layer** (`application/`):
   - Commands are frozen dataclasses representing write operations
   - Queries are frozen dataclasses for read operations
   - Services orchestrate use cases, no business logic here

4. **Presentation Layer** (`presentation/`):
   - Views are thin controllers that delegate to application services
   - URLs follow RESTful patterns

## Key Files to Reference

Before implementing, read these files for conventions:
- `apps/blog/domain/entities/__init__.py` - Entity patterns
- `apps/blog/domain/value_objects/__init__.py` - Value object patterns
- `apps/blog/infrastructure/repositories.py` - Repository implementation
- `apps/blog/application/services.py` - Service patterns
- `apps/shared/domain/events/__init__.py` - Event base class
- `apps/shared/domain/value_objects/__init__.py` - Shared value objects

## Trading Blog Specifics

- **Bounded context**: `apps/trading/`
- **Instruments**: NQ, ES, RTY, YM (futures contracts)
- **Post types**: PRE_MARKET, POST_MARKET, WEEKLY_RECAP
- **Data source**: yfinance (free delayed futures data)
- **URL prefix**: `/trading-blog/`

## Instructions

1. Read `TRADING_BLOG_PLAN.md` first
2. Review the reference files listed above for patterns
3. Implement only the specified phase
4. Follow existing code conventions exactly
5. Create all necessary `__init__.py` files
6. Add appropriate type hints throughout
7. Do not implement phases beyond what is specified

Begin implementation.