# Component: blog

**Location:** `apps/blog/`
**Status:** Complete - all layers implemented and verified (FSP-2)
**Bounded Context:** Blog Publishing
**Architecture Pattern:** Domain-Driven Design with split domain/infrastructure layers
**Related ADRs:** ADR-0002, ADR-0003, ADR-0004

---

## Responsibility

The blog bounded context manages the lifecycle of public blog posts authored by Joseph
Prince. It owns:

- Creating, publishing, and unpublishing blog posts via Django admin.
- Serving the public-facing blog list, post detail, and RSS feed.
- Computing reading time automatically on every save.
- Generating and storing OpenAI text embeddings in Supabase pgvector for semantic search.
- Enforcing draft post access control (staff-only).

---

## Domain Model

### Aggregate Roots

| Aggregate | Primary Identity | Status Field | Key Invariant |
|---|---|---|---|
| `Post` | `int` (auto) | `PostStatus` | title <= 300 chars; body required to publish; slug must match `^[a-z0-9]+(-[a-z0-9]+)*$` |
| `Tag` | `int` (auto) | - | name <= 100 chars, non-empty; equality by id if both set, otherwise by slug |

### Value Objects

| Value Object | Type | Key Invariant |
|---|---|---|
| `Slug` | frozen dataclass | Non-empty; <= 255 chars; lowercase alphanumeric with single hyphens |
| `Excerpt` | frozen dataclass | HTML stripped; non-empty; <= 500 chars |
| `ReadingTime` | frozen dataclass | Integer >= 1 minute |
| `FeaturedImagePath` | frozen dataclass | No leading slash; no `..` traversal; non-empty |
| `PostStatus` | Enum | `DRAFT`, `PUBLISHED` |
| `EmbeddingVector` | frozen dataclass | Exactly 1536 finite float dimensions |

### Domain Events

| Event | Raised By | Purpose |
|---|---|---|
| `PostPublished` | `Post.publish()` | Signals that a post has been made public |
| `PostUnpublished` | `Post.unpublish()` | Signals that a post has been removed from public view |
| `PostUpdated` | `Post.publish()` (re-publish) | Signals that published post content changed |
| `PostVectorized` | Reserved | Confirms successful embedding creation (future enrichment) |
| `PostVectorizationFailed` | Reserved | Records a failed embedding attempt (future enrichment) |

### Domain Services

| Service | Responsibility |
|---|---|
| `ReadingTimeCalculator` | Estimates reading time from word count using 200 wpm; minimum 1 minute |
| `RelatedPostFinder` | Delegates to `IPostRepository.find_published_by_tag_ids` to find posts sharing tags |

### Repository Interfaces

| Interface | Key Methods |
|---|---|
| `IPostRepository` | `save`, `find_by_id`, `find_by_slug`, `find_published`, `find_by_tag`, `find_published_by_tag_ids`, `find_all_published`, `delete`, `count_published` |
| `ITagRepository` | `save`, `find_by_id`, `find_by_slug`, `find_by_name`, `find_by_ids`, `find_all` |

---

## Layer Structure

```
apps/blog/
    domain/
        value_objects.py    - Slug, Excerpt, ReadingTime, FeaturedImagePath,
                              PostStatus, EmbeddingVector
        entities.py         - Post aggregate, Tag entity; all business rules
        events.py           - Domain event frozen dataclasses
        exceptions.py       - PostNotFoundError, PublishInvariantError,
                              SlugConflictError, TagNameConflictError
        repositories.py     - IPostRepository and ITagRepository ABCs
        services.py         - ReadingTimeCalculator, RelatedPostFinder
    application/
        dtos.py             - PostListItemDTO, PostDetailDTO, PostFeedItemDTO, TagDTO
        use_cases.py        - ListPublishedPosts, GetPostBySlug, GetFeedPosts,
                              CountPublishedPosts
        vectorization_task.py - vectorize_post and delete_post_vector (Django Q2 tasks)
    infrastructure/
        repositories.py     - DjangoPostRepository, DjangoTagRepository
    services/
        embedding_service.py - PostEmbeddingService (OpenAI + Supabase psycopg2)
    models.py               - Django ORM models (Post, Tag, PostTag)
    admin.py                - Django admin registration
    signals.py              - compute_reading_time (pre_save), schedule_vectorization
                              (post_save)
    views.py                - blog_list, post_detail, blog_feed HTTP views
    urls.py                 - URL patterns: /blog/, /blog/<slug>/, /blog/feed/
    templates/blog/         - post_list.html, post_detail.html
    tests/
        test_domain_value_objects.py         - 82 unit tests (no DB, no network)
        test_domain_entities_and_services.py
        test_views_integration.py            - 18 integration tests (Django TestClient)
    migrations/             - Django migration history
```

---

## Vectorization Pipeline

The pipeline runs entirely outside the HTTP request cycle.

```
Django admin saves Post
        |
        v
pre_save signal: compute_reading_time
        |
        v
ORM write to MySQL (Post.save())
        |
        v
post_save signal: schedule_vectorization
        |
        +-- status == PUBLISHED --> async_task(vectorize_post, post_id)
        |
        +-- status != PUBLISHED --> async_task(delete_post_vector, post_id)
        |
        v
Django Q2 task queue (MySQL broker)
        |
        v
Cloud Run worker (qcluster)
        |
        v
vectorize_post(post_id):
    1. Load Post from MySQL
    2. Concatenate title + excerpt + body
    3. PostEmbeddingService._embed() --> OpenAI embeddings.create()
    4. PostEmbeddingService.upsert() --> psycopg2 INSERT...ON CONFLICT to Supabase
        |
        v
post_embeddings table in Supabase (pgvector)
```

**Failure handling:** Any exception in `vectorize_post` or `delete_post_vector` is
caught and logged with `logger.exception`. The task is not automatically retried in
the current version. The post save succeeds regardless of embedding outcome.

---

## HTTP Endpoints

| URL | View | Description |
|---|---|---|
| `/blog/` | `blog_list` | Paginated list of published posts |
| `/blog/<slug>/` | `post_detail` | Single post detail; drafts return 404 for non-staff |
| `/blog/feed/` | `blog_feed` | RSS 2.0 feed of all published posts |

**Draft access control:** `GetPostBySlug.execute` checks `request_user_is_staff`.
Unauthenticated users and authenticated non-staff users both receive HTTP 404 on drafts.

---

## Environment Variables Required

| Variable | Purpose | Required |
|---|---|---|
| `SUPABASE_DB_URL` | psycopg2 connection string to Supabase Postgres | Yes (for vectorization) |
| `OPENAI_API_KEY` | OpenAI API key for `text-embedding-3-small` | Yes (for vectorization) |
| `DATABASE_URL` | MySQL connection string (primary database) | Yes |
| `SECRET_KEY` | Django secret key | Yes |
| `GS_BUCKET_NAME` | GCS bucket for featured image uploads | Yes (for image uploads) |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account key path for GCS | Yes (for image uploads) |

All variables are loaded from environment via `django-environ` in `core/settings.py`.
No variable is hardcoded in source files.

---

## Key Design Decisions

- **Domain-ORM split** (ADR-0004): Plain Python domain entities with no Django imports.
  82 unit tests run without a database connection.
- **Supabase as write-only boundary** (ADR-0004): The domain layer never reads from
  Supabase. Embeddings are a derived projection of the primary MySQL data.
- **Django Q2 for vectorization** (ADR-0002, ADR-0004): Embedding calls are async to
  avoid blocking admin saves.
- **Draft access restricted to `is_staff`** (ADR-0004, SEC-001): Non-staff authenticated
  users cannot view drafts via the public URL. Defect SEC-001 hardened this during QA.
- **Reading time computed on every save**: The `pre_save` signal calls
  `ReadingTimeCalculator` so `reading_time_minutes` is always consistent with the
  current body without requiring the author to set it manually.

---

## Known Limitations

- **N+1 author resolution**: `ListPublishedPosts` calls `User.objects.get()` once per
  post. For a personal blog with O(10) posts per page this is negligible. Future fix:
  use `select_related('author')` in the repository query.
- **Vectorization is eventually consistent**: A short window exists after publish where
  the embedding does not yet exist in Supabase.
- **No automatic retry**: Failed vectorization tasks are logged but not retried.
- **`|safe` filter in post_detail.html**: Body HTML is rendered without escaping. This
  is intentional (admin-authored content) and accepted per the security sign-off.
