# Mini-Discovery Artifact

<!-- Produced by: ticket-intake-agent (Stage 0)
     Consumed by: domain-modeling-orchestrator
     Validate against: contracts/schemas/mini-discovery.schema.json -->

**Produced by:** `.github/agents/ticket-intake-agent.agent.md`
**Consumed by:** domain-modeling-orchestrator

---

## Ticket Identity

| Field       | Value                                   |
|-------------|-----------------------------------------|
| Issue key   | FSP-2                                   |
| Issue type  | Story                                   |
| Project key | FSP                                     |
| Title       | Full Blog Feature with Supabase Vectorization |
| Priority    | (not specified)                         |
| Labels      | (none)                                  |
| Epic link   | (none)                                  |

---

## Summary

Implement the complete blog section of the FullStackPortfolio site. This covers a
public-facing blog with list and detail views, a full data model for posts (title,
slug, rich-text body, excerpt, featured image, tags, author, published date,
draft/published status), a Django admin interface for content management, an RSS feed,
a related-posts sidebar, and estimated reading-time display. In addition, every
published or updated post must be automatically vectorized using an embedding model
and stored in a Supabase pgvector store so that AI agents can perform semantic search
over all blog content.

---

## Description

Implement the entire blog portion of the portfolio. This includes:
- A public-facing blog with list and detail views
- Blog posts with title, slug, body (rich text), excerpt, featured image, tags, author, published date, and draft/published status
- Admin interface for creating and managing posts
- RSS feed
- Related posts sidebar
- Estimated reading time
- Ensure that all posts are automatically vectorized for agent consumption in Supabase (pgvector). When a post is published or updated, its content should be vectorized using an embedding model and stored in a Supabase vector store so that AI agents can perform semantic search over blog content.

---

## Acceptance Criteria

Given a visitor navigates to the blog list page,
When the page loads,
Then a paginated list of published posts is displayed, each showing title, excerpt, featured image, author, published date, estimated reading time, and tags.

Given a visitor clicks on a blog post in the list,
When the detail page loads,
Then the full post body (rich text rendered as HTML), featured image, author, published date, estimated reading time, tags, and a related-posts sidebar are displayed.

Given an authenticated admin user creates or updates a blog post and sets its status to "published",
When the save action is committed,
Then the post becomes visible on the public blog list and detail views.

Given a draft post exists,
When an unauthenticated visitor attempts to view it by URL,
Then a 404 response is returned.

Given the RSS feed endpoint is requested,
When the feed is returned,
Then it contains all published posts in valid RSS 2.0 format with title, link, description, and publication date.

Given a blog post is published or updated,
When the post-save signal fires,
Then the post body is sent to an embedding model, the resulting vector is upserted into the Supabase pgvector store keyed by the post's slug or ID, and no error is raised if the vectorization service is temporarily unavailable (the failure is logged and retried or queued).

Given an AI agent performs a semantic search query against the Supabase vector store,
When the query is executed,
Then the most semantically similar blog posts are returned in ranked order.

---

## Ticket Size

story

Derived from issue type: Story -> story.

---

## Routed Phases

- domain-modeling-orchestrator
- development-orchestrator
- qa-orchestrator
- documentation-orchestrator

---

## Out of Scope

- User-facing comments or comment moderation on blog posts.
- Social sharing buttons or Open Graph metadata beyond basic SEO tags.
- Newsletter or email subscription functionality.
- Multi-author role and permissions management beyond the default Django admin.
- Analytics or view-count tracking for individual posts.
- Search within the blog (full-text or otherwise) beyond the Supabase vector store integration already specified.
- Internationalization or multi-language support.
- Deployment configuration changes to App Engine or Cloud Run (covered by deployment-orchestrator in a separate ticket if needed).
- The AI agent interface that consumes the vector store - only the vectorization pipeline is in scope.

---

## Assumptions

- The existing `apps/blog/` Django app is the correct location for all new domain models,
  views, signals, and services; no new Django app will be created.
- The project's primary database (MySQL on Google Cloud SQL) stores all relational blog
  data; Supabase stores only the vector embeddings and associated metadata.
- Supabase project credentials (URL and anon/service key) will be supplied as environment
  variables; they are not committed to source control.
- The embedding model to use is not specified in the ticket; the implementation will
  default to OpenAI `text-embedding-3-small` unless overridden by an environment variable,
  so the integration remains model-agnostic.
- Rich text is implemented using a third-party Django package (e.g., django-ckeditor or
  django-tinymce); the specific package selection is deferred to the development phase.
- Vectorization is triggered asynchronously via Django signals on the post-save event to
  avoid blocking the admin save response; a synchronous fallback is acceptable for the
  first implementation if a task queue is not yet configured.
- "Related posts" are determined by shared tags; semantic similarity via the vector store
  is a future enhancement and is not in scope for this ticket.
- Estimated reading time is calculated on the server using a standard words-per-minute
  formula (approximately 200 wpm) and stored or computed at render time.
- The RSS feed is served at a predictable URL such as `/blog/feed/` and requires no
  authentication.
- Slug uniqueness is enforced at the database level; auto-generation from the title is
  provided in the admin but editable before first publish.

---

## Codebase Context

<!-- Appended by codebase-context-agent on 2026-05-29. -->

### Bounded Contexts

- **blog** - `apps/blog/`. Already partially implemented. Contains a `Post` model
  (title, slug, summary, body, published flag, published_at, created_at, updated_at),
  a `PostAdmin` registration, a `sync_embedding` post-save signal, and a
  `PostEmbeddingService` in `apps/blog/services/embedding_service.py`. No views, urls,
  tags, featured image, author FK, estimated reading time, or RSS feed exist yet.
- **client_portal** - `apps/client_portal/`. Bounded context with a full domain-ORM
  split (ADR 0003). Domain layer in `apps/client_portal/domain/`; ORM models in
  `apps/client_portal/models.py`. This is the only context applying the plain-Python
  domain layer pattern; other apps use Django ORM models directly.
- **contact** - `apps/contact/`. Contact form with SendGrid email delivery via Django Q2.
- **ai_assistant** - `apps/ai_assistant/`. OpenAI-backed chatbot.
- **home**, **about**, **react_app** - Stub apps, not yet implemented.
- **Vector Store (Supabase / pgvector)** - External context. `PostEmbeddingService`
  connects via `psycopg2` directly to the Supabase PostgreSQL database
  (`settings.SUPABASE_DB_URL`). Embeddings are stored in a `post_embeddings` table with
  columns `post_id`, `embedding` (vector), `updated_at`. Uses OpenAI
  `text-embedding-3-small` (1536 dimensions). This context is already wired to the blog
  signal.

---

### Key ADR Decisions

- **ADR 0001 - Django + React-as-static-files architecture (Accepted, 2026-05-29):**
  React SPA compiled to static files and served by Django. No separate frontend server.
  All server-side routing, admin, and API endpoints handled by Django. Single GAE
  deployment unit.
- **ADR 0002 - Cloud Run worker for async task processing (Accepted, 2026-05-29):**
  Django Q2 with MySQL as broker. A Cloud Run container runs `manage.py qcluster`.
  All slow or failure-prone external API calls (SendGrid, Twilio, OpenAI) are enqueued
  as tasks rather than called synchronously in views. This is the established pattern
  for the vectorization signal as well.
- **ADR 0003 - client_portal domain-ORM split (Accepted, 2026-05-29):**
  Plain Python dataclasses for domain logic (zero Django imports); separate ORM models
  for persistence. Applied only to `client_portal` due to its state-machine complexity.
  The `blog` context does not require this level of separation.

---

### Established Patterns

- **Signal-driven side effects:** `apps/blog/signals.py` uses a Django `post_save`
  receiver registered in `BlogConfig.ready()`. The signal catches all exceptions and
  logs them rather than propagating, preventing admin save failures on service
  unavailability. This is the existing pattern for the embedding sync and should be
  followed for any additional post-save side effects.
- **Service layer in `services/` subdirectory:** External integrations are encapsulated
  in a `services/` package inside the app (e.g., `apps/blog/services/embedding_service.py`).
  Services are plain Python classes instantiated by callers; they receive settings values
  via `django.conf.settings` imports, not constructor injection.
- **`AppConfig.ready()` for signal registration:** All signal modules are imported inside
  `AppConfig.ready()` to avoid circular imports and ensure signals register only once.
- **Django Q2 for async tasks:** Long-running or failure-prone work is offloaded to
  `django_q.tasks.async_task()` (contact app pattern). The blog vectorization currently
  runs synchronously in the signal handler; ADR 0002 establishes that async offloading
  via Django Q2 is the approved pattern for blocking external calls.
- **`django-environ` for configuration:** All secrets and environment-specific values are
  read via `environ.Env` from a `.env` file. New settings (e.g., `SUPABASE_DB_URL`,
  `OPENAI_API_KEY`) follow the same `env('VAR_NAME')` pattern in `core/settings.py`.
- **Django ORM models with auto-slug in `save()`:** `Post.save()` auto-generates the
  slug from the title when blank. New fields should follow the same pattern of computed
  defaults inside `save()`.
- **Google Cloud Storage for media files:** `django-storages` 1.14.6 with GCS backend
  is installed. Featured image fields should use a `FileField` or `ImageField` backed by
  the GCS storage backend, not local filesystem storage.
- **`prepopulated_fields` and `readonly_fields` in ModelAdmin:** Established in
  `PostAdmin`; new admin classes should follow the same conventions.

---

### Technology Stack

- **Python:** 3.14 (production runtime target: 3.12 on GAE standard)
- **Django:** 6.0.5
- **Database (primary):** MySQL 8.x on Google Cloud SQL via `mysqlclient` 2.2.8
- **Database (vector store):** Supabase PostgreSQL with pgvector, accessed directly via
  `psycopg2-binary` 2.9.12 (no ORM; raw SQL)
- **Task queue:** Django Q2 1.10.0 with MySQL broker
- **Async worker:** Google Cloud Run (`Dockerfile.worker`, `manage.py qcluster`)
- **File storage:** Google Cloud Storage via `django-storages` 1.14.6
- **Embedding model:** OpenAI `text-embedding-3-small` (1536 dimensions) via
  `openai` 2.38.0
- **Configuration:** `django-environ` 0.13.0; secrets from `.env`
- **Email:** SendGrid via `sendgrid` 6.12.5
- **SMS:** Twilio via `twilio` 9.10.9
- **HTTP/async helpers:** `httpx` 0.28.1, `aiohttp` 3.13.5 (present but not yet used
  in blog context)
- **Rich text editor:** Not yet installed; ticket assumption is `django-ckeditor` or
  `django-tinymce` - package selection deferred to development phase
- **RSS feed:** Django's built-in `django.contrib.syndication` framework (no extra
  package needed)
- **Notable absent packages:** No DRF, no Celery, no Redis; `django-q2` is the sole
  task queue mechanism
