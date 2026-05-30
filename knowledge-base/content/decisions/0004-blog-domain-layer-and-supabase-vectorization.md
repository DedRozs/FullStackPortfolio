# ADR 0004: Blog Domain Layer and Supabase Vectorization

**Status:** Accepted
**Date:** 2026-05-29
**Deciders:** Joseph Prince
**Technical Story:** FSP-2 - Blog feature with Supabase pgvector

---

## Context

The blog bounded context requires:

1. A domain model for `Post` and `Tag` entities with invariants (slug format, excerpt
   length, title length, publish guard on empty body) that must be unit-testable without
   a database.
2. A semantic search capability backed by OpenAI `text-embedding-3-small` and Supabase
   pgvector so that related posts can be surfaced and future AI assistant queries can
   find relevant content.
3. Asynchronous embedding generation so that Django admin saves are never blocked by
   OpenAI or Supabase network calls.
4. Access control: draft posts must not be visible to unauthenticated users or to
   authenticated non-staff users, preventing information disclosure from the public URL.

The client_portal bounded context established the domain-ORM split pattern in ADR-0003.
The blog feature is a natural candidate for the same pattern: the `Post` aggregate has
meaningful invariants and a publish/unpublish lifecycle that benefits from unit testing
in isolation.

---

## Decision 1: Full domain layer following the client_portal precedent

Implement the blog bounded context with a full domain layer identical in structure to
client_portal:

- `domain/value_objects.py` - `Slug`, `Excerpt`, `ReadingTime`, `FeaturedImagePath`,
  `PostStatus`, `EmbeddingVector` as frozen dataclasses and enums.
- `domain/entities.py` - `Post` and `Tag` as plain Python classes with invariants and
  state-transition methods (`publish`, `unpublish`, `add_tag`, `remove_tag`).
- `domain/events.py` - `PostPublished`, `PostUnpublished`, `PostUpdated`,
  `PostVectorized`, `PostVectorizationFailed` as frozen dataclasses.
- `domain/repositories.py` - `IPostRepository` and `ITagRepository` abstract base
  classes with no Django imports.
- `domain/services.py` - `ReadingTimeCalculator` and `RelatedPostFinder` as pure
  domain services.
- `models.py` - Django ORM models that mirror the domain but carry no business logic.
- `infrastructure/repositories.py` - `DjangoPostRepository` and `DjangoTagRepository`
  implementing the domain interfaces.

---

## Decision 2: Supabase pgvector as an external write-only boundary

Supabase is an external infrastructure concern. The domain layer raises
`PostVectorized` and `PostVectorizationFailed` events but contains no Supabase imports
or SDK calls. The `PostEmbeddingService` in `services/embedding_service.py` is the
sole translation point between the domain and the Supabase Postgres connection.

The domain treats Supabase as a write-only projection store:

- Post content (source of truth) lives in MySQL via the `Post` ORM model.
- Embeddings (derived projection) live in Supabase `post_embeddings` table.
- The projection is rebuilt on every publish/update and deleted on unpublish.
- The domain never reads from Supabase to make a business decision.

This boundary means that Supabase credentials, connection pooling, and pgvector schema
are entirely contained in `services/embedding_service.py` and never leak into the
application or domain layers.

---

## Decision 3: Django Q2 for all vectorization tasks

Per ADR-0002, Django Q2 with a Cloud Run worker is the established async task mechanism.
Vectorization tasks are enqueued in the `post_save` signal handler in `signals.py` and
executed by `vectorization_task.py`. The signal is the only integration point between
the ORM save lifecycle and the async worker.

OpenAI embedding calls (approximately 300 ms to 1 s per call) and Supabase write
operations must not block the Django admin HTTP response. Enqueuing a task returns
immediately; the worker processes it asynchronously. Failures are logged with
`logger.exception` and do not surface to the admin user.

---

## Decision 4: Draft post access restricted to staff users

The `GetPostBySlug` use case gates draft post visibility on `request_user_is_staff`.
Authenticated non-staff users (such as client portal users) receive a 404 identical to
the unauthenticated response. This was hardened during QA after defect SEC-001 found
that the initial implementation allowed any authenticated user to view drafts.

The check is enforced in two places for defense in depth:
1. `application/use_cases.py` - `GetPostBySlug.execute` raises `PostNotFoundError` if
   `post.status != PUBLISHED and not request_user_is_staff`.
2. `views.py` - passes `request.user.is_staff` to the use case.

---

## Options Considered

### Blog domain layer

**Option A: Business logic on Django ORM models only**
Rejected for the same reasons as ADR-0003: couples domain rules to ORM; unit tests
require a database; violates the dependency rule.

**Option B: Full domain layer (chosen)**
Consistent with client_portal; 82 domain unit tests run without a database; dependency
rule respected; domain is reasoned about independently of persistence.

### Supabase integration boundary

**Option A: Inject `PostEmbeddingService` into domain entities**
Rejected: domain entities would depend on an external service; violates the dependency
rule; makes domain unit tests require network mocking.

**Option B: Domain raises events; infrastructure handles them (chosen)**
Domain raises `PostVectorized`/`PostVectorizationFailed` events. The signal and task
layer handles Supabase writes independently. Domain is kept pure.

**Option C: Supabase writes in the Django admin `save_model` override**
Rejected: blocks the admin response; no retry; harder to test.

### Async task mechanism

**Option A: Synchronous Supabase call in the signal handler**
Rejected: blocks the HTTP request; no retry; degrades admin UX.

**Option B: Django Q2 (chosen)**
Consistent with ADR-0002; Cloud Run worker reuses existing infrastructure; retry on
failure; zero additional broker infrastructure.

---

## Consequences

### Positive

- 82 domain unit tests run in under 1 second with no database or network access.
- Vectorization failures do not degrade the admin save experience.
- Supabase schema changes are isolated to `PostEmbeddingService`; no domain files need
  to change.
- SEC-001 fix means draft posts are inaccessible to all non-staff users regardless of
  authentication state.

### Negative

- Two class hierarchies to maintain (domain entities and ORM models) as in client_portal.
- Vectorization is eventually consistent: there is a short window after a post is
  published where the embedding has not yet been created.
- If the Q2 worker is not running, embeddings fall out of sync silently until the worker
  is restarted.

### Neutral

- `EmbeddingVector` value object is defined in the domain but is not currently used in
  the `Post` entity. It is reserved for a future `PostVectorized` enrichment pattern
  and is validated by unit tests.
