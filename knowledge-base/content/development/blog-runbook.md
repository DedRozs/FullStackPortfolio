# Blog Feature Runbook

**Bounded Context:** Blog Publishing
**App:** `apps/blog/`
**Status:** Production-ready (FSP-2 complete)
**Related ADRs:** ADR-0002, ADR-0003, ADR-0004

---

## Table of Contents

1. [Add a new blog post via admin](#1-add-a-new-blog-post-via-admin)
2. [Apply migrations for this feature](#2-apply-migrations-for-this-feature)
3. [Run unit and integration tests](#3-run-unit-and-integration-tests)
4. [Test the vectorization pipeline locally](#4-test-the-vectorization-pipeline-locally)
5. [Troubleshooting](#5-troubleshooting)

---

## 1. Add a new blog post via admin

### Prerequisites

- Django dev server running (`manage.py runserver`).
- A superuser account (create one with `manage.py createsuperuser` if needed).

### Steps

1. Navigate to `http://localhost:8000/admin/blog/post/add/`.
2. Fill in the required fields:
   - **Title** - plain text, max 300 characters.
   - **Slug** - lowercase alphanumeric with hyphens (e.g., `my-first-post`). Django
     admin pre-fills this from the title.
   - **Excerpt** - plain text summary, max 500 characters. HTML tags are stripped
     automatically by the domain layer.
   - **Body** - Markdown content via django-markdownx.
   - **Author** - select the staff user who authored the post.
   - **Status** - leave as `DRAFT` until ready to publish.
3. Add tags (optional): use the inline tag selector or create tags at
   `/admin/blog/tag/add/`.
4. Upload a featured image (optional): use the file upload field. Images are stored in
   Google Cloud Storage under the configured `GS_BUCKET_NAME` bucket.
5. Click **Save**. Reading time is computed automatically by the `pre_save` signal.
6. To publish: change **Status** to `PUBLISHED` and click **Save**. The `post_save`
   signal enqueues a `vectorize_post` Django Q2 task immediately.

### What happens after save

- `pre_save` signal recomputes `reading_time_minutes` from the body word count.
- `post_save` signal enqueues `vectorize_post` (if PUBLISHED) or `delete_post_vector`
  (if DRAFT) as a Django Q2 async task.
- The Q cluster worker processes the task and calls OpenAI + Supabase. If the worker is
  not running locally, the task stays queued in the `django_q_task` MySQL table.

---

## 2. Apply migrations for this feature

The blog app has Django migrations in `apps/blog/migrations/`. Apply them with:

```
# Windows (virtual environment)
.venv\Scripts\python.exe manage.py migrate blog

# macOS / Linux
.venv/bin/python manage.py migrate blog
```

To apply all pending migrations:

```
.venv\Scripts\python.exe manage.py migrate
```

### Supabase schema

The `post_embeddings` table must exist in Supabase before vectorization runs. The table
is NOT created by Django migrations (Supabase is an external boundary). Create it once
by running the following SQL in the Supabase SQL editor or via psql:

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS post_embeddings (
    id          BIGSERIAL PRIMARY KEY,
    post_id     INTEGER NOT NULL UNIQUE,
    embedding   vector(1536),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS post_embeddings_embedding_idx
    ON post_embeddings
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

---

## 3. Run unit and integration tests

All tests live in `apps/blog/tests/`. Use the virtual environment:

```
# Windows
.venv\Scripts\python.exe -m pytest apps/blog/tests/ -v

# macOS / Linux
.venv/bin/python -m pytest apps/blog/tests/ -v
```

### Run only domain unit tests (no DB required)

```
.venv\Scripts\python.exe -m pytest apps/blog/tests/test_domain_value_objects.py apps/blog/tests/test_domain_entities_and_services.py -v
```

Expected: 82 tests, all pass, no database connection needed.

### Run only integration tests (Django TestClient, SQLite in-memory)

```
.venv\Scripts\python.exe -m pytest apps/blog/tests/test_views_integration.py -v
```

Expected: 18 tests, all pass.

### Run with coverage

```
.venv\Scripts\python.exe -m pytest apps/blog/tests/ --cov=apps/blog --cov-report=term-missing
```

### pytest.ini

The project `pytest.ini` configures `DJANGO_SETTINGS_MODULE`. No additional environment
variables are required to run the test suite. Tests that would touch Supabase or OpenAI
are not present in the test suite; those integrations are tested manually (see section 4).

---

## 4. Test the vectorization pipeline locally

The vectorization pipeline calls OpenAI and Supabase. These calls are not mocked in the
automated test suite. Use the following approaches.

### Option A: Mock Supabase, use a real OpenAI key

This verifies the embedding generation without needing a live Supabase connection.

1. Set environment variables:

   ```
   OPENAI_API_KEY=sk-...your-key...
   SUPABASE_DB_URL=postgresql://user:pass@host:5432/postgres
   ```

   You can use a throwaway local Postgres instance for `SUPABASE_DB_URL`. Install the
   `vector` extension and create the `post_embeddings` table (see section 2 for DDL).

2. Start a local Q cluster in a separate terminal:

   ```
   .venv\Scripts\python.exe manage.py qcluster
   ```

3. In a third terminal, open the Django shell and trigger vectorization manually:

   ```
   .venv\Scripts\python.exe manage.py shell
   ```

   ```python
   from apps.blog.application.vectorization_task import vectorize_post
   vectorize_post(post_id=1)  # replace with a real post ID
   ```

4. Check the output for `INFO vectorize_post: upserted embedding for post 1.`

### Option B: End-to-end with live Supabase

1. Set `SUPABASE_DB_URL` to the real Supabase connection string from the project
   credentials.
2. Ensure the `post_embeddings` table and `vector` extension exist (see section 2).
3. Start the Q cluster: `.venv\Scripts\python.exe manage.py qcluster`
4. Publish a post via Django admin.
5. Observe Q cluster output for task pickup and completion.
6. Verify the embedding was written:

   ```
   .venv\Scripts\python.exe manage.py shell
   ```

   ```python
   from apps.blog.services.embedding_service import PostEmbeddingService
   svc = PostEmbeddingService()
   ids = svc.find_similar_post_ids("your test query", top_k=3)
   print(ids)
   ```

### Confirming the task was enqueued

Check the Django Q task table directly:

```
.venv\Scripts\python.exe manage.py shell
```

```python
from django_q.models import OrmQ
print(list(OrmQ.objects.values('id', 'name', 'func', 'started')))
```

---

## 5. Troubleshooting

### Q2 worker not running

**Symptom:** Posts are saved successfully but no embedding appears in Supabase. The
`django_q_task` table accumulates rows.

**Diagnosis:**
```
.venv\Scripts\python.exe manage.py shell
```
```python
from django_q.models import OrmQ, Success, Failure
print(f"Queued: {OrmQ.objects.count()}")
print(f"Success: {Success.objects.count()}")
print(f"Failure: {Failure.objects.count()}")
```

**Fix:**
- Locally: start the Q cluster with `.venv\Scripts\python.exe manage.py qcluster`.
- Production: ensure the Cloud Run worker service is deployed and healthy. Check Cloud
  Run logs for the `worker` service.

---

### Supabase connection failed

**Symptom:** `vectorize_post` log line: `ERROR vectorize_post: failed to upsert
embedding for post N.` with a `psycopg2.OperationalError`.

**Diagnosis steps:**
1. Verify `SUPABASE_DB_URL` is set correctly in the environment.
2. Test the connection directly:
   ```python
   import psycopg2, os
   conn = psycopg2.connect(os.environ['SUPABASE_DB_URL'], sslmode='require')
   print("Connected")
   conn.close()
   ```
3. Check that the Supabase project is active (free-tier projects pause after inactivity).
4. Check that `post_embeddings` table exists (see section 2 for DDL).
5. Check that the `vector` extension is enabled in Supabase.

---

### OpenAI API call failed

**Symptom:** `vectorize_post` log line contains `openai.AuthenticationError` or
`openai.RateLimitError`.

**Diagnosis:**
1. `AuthenticationError` - `OPENAI_API_KEY` is missing or invalid. Verify the key is
   set in the environment and has not been rotated.
2. `RateLimitError` - API rate limit hit. For a personal portfolio this should not occur
   under normal load. If it does, wait and the next admin save will re-trigger the task.

---

### Image upload to GCS failing

**Symptom:** Featured image upload in Django admin fails with a `SuspiciousFileOperation`
or a 500 error.

**Diagnosis steps:**
1. Verify `GS_BUCKET_NAME` is set to the correct bucket name.
2. Verify `GOOGLE_APPLICATION_CREDENTIALS` points to a valid service account JSON key
   that has Storage Object Admin permission on the bucket.
3. Test GCS access from the shell:
   ```python
   from google.cloud import storage
   client = storage.Client()
   bucket = client.bucket("your-bucket-name")
   print(bucket.exists())
   ```
4. Check `FeaturedImagePath` value object validation: paths must not start with `/` and
   must not contain `..`. If the upload adapter is generating invalid paths, inspect the
   model field storage configuration.

---

### Draft post visible to non-staff user

**Symptom:** A logged-in non-staff user can access `/blog/<slug>/` for a draft post.

**Diagnosis:** This was defect SEC-001, fixed during FSP-2 QA. Confirm the fix is in
place by checking `apps/blog/application/use_cases.py`:

```python
if post.status != PostStatus.PUBLISHED and not request_user_is_staff:
    raise PostNotFoundError(...)
```

and `apps/blog/views.py`:

```python
request_user_is_staff=request.user.is_staff
```

If either check is missing, re-apply the fix and run the integration tests.

---

### Migration conflicts or missing tables

**Symptom:** `django.db.utils.ProgrammingError: relation "blog_post" does not exist`.

**Fix:** Run pending migrations:
```
.venv\Scripts\python.exe manage.py migrate
```

If a migration conflict exists, run `manage.py showmigrations blog` to identify the
discrepancy and resolve it before applying.
