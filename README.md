# Full Stack Portfolio

A modern portfolio website built with Django and React, following Clean Architecture and Domain-Driven Design principles.

## Blog

The blog bounded context (`apps/blog/`) provides a full publishing workflow for personal
technical posts. Key capabilities:

- **Public endpoints:** `/blog/` (paginated list), `/blog/<slug>/` (post detail),
  `/blog/feed/` (RSS 2.0 feed).
- **Content authoring:** Posts are created and published via Django admin using
  Markdown (django-markdownx). Reading time is computed automatically.
- **Semantic search:** On every publish, an OpenAI `text-embedding-3-small` embedding
  is generated asynchronously (Django Q2 worker) and stored in Supabase pgvector.
  Related posts are surfaced by tag overlap in the current version; vector similarity
  search is available for future AI assistant integration.
- **Access control:** Draft posts return HTTP 404 for all non-staff visitors, including
  authenticated client portal users.
- **Architecture:** Full DDD domain layer (value objects, entities, domain events,
  repository interfaces) following the same pattern as the client_portal bounded context.
  Domain logic is testable without a database (82 unit tests).

Required environment variables: `SUPABASE_DB_URL`, `OPENAI_API_KEY`. See
[knowledge-base/content/components/blog.md](knowledge-base/content/components/blog.md)
for the full component reference and
[knowledge-base/content/development/blog-runbook.md](knowledge-base/content/development/blog-runbook.md)
for the developer runbook.

## Client Portal

The client_portal bounded context (`apps/client_portal/`) delivers a full-stack secure
portal where client organizations manage projects, deliverables, approvals, files,
messages, and invoices.

Key capabilities:

- **Multi-tenant isolation:** All API read and write paths are scoped to the caller's
  `ClientOrganization`. Staff users have cross-org access; client users see only their
  own data. Object-level DRF permissions enforce isolation at every viewset.
- **Approval state machine:** Deliverable versions go through a formal
  PENDING -> APPROVED | REJECTED | REVISION_REQUESTED workflow. Only the assigned
  reviewer may decide. All decisions emit an immutable `ActivityEvent` audit entry.
- **File storage:** Files are uploaded to Google Cloud Storage via `GCSFileStorageAdapter`
  implementing the `FileStoragePort` abstraction. Storage keys are UUID-prefixed to
  prevent path traversal.
- **Real-time infrastructure:** Django Channels + Daphne (ASGI) with a Redis channel
  layer on a VPS. WebSocket consumers are registered in `core/asgi.py` and will be
  implemented in the `workflow_automation` epic.
- **Background tasks:** Approval notification emails are dispatched via Django Q2 async
  tasks processed by the Cloud Run worker.

Required environment variables: `REDIS_URL`, `GS_BUCKET_NAME`,
`GOOGLE_APPLICATION_CREDENTIALS`, `SENDGRID_API_KEY`. See
[knowledge-base/content/components/client-portal.md](knowledge-base/content/components/client-portal.md)
for the full component reference and
[knowledge-base/content/development/client-portal-runbook.md](knowledge-base/content/development/client-portal-runbook.md)
for the developer runbook.

## Author

**Joseph Prince**
- LinkedIn: [thejprince](https://www.linkedin.com/in/thejprince/)
- GitHub: [DedRozs](https://github.com/DedRozs)

## License

This project is licensed under the MIT License.
