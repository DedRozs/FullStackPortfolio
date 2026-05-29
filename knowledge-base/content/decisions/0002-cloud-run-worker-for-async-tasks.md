# ADR 0002: Cloud Run Worker for Async Task Processing

**Status:** Accepted
**Date:** 2026-05-29
**Deciders:** Joseph Prince
**Technical Story:** Background job architecture for email, SMS, and AI API calls

---

## Context

The contact form, AI assistant, and notification features require calling external APIs
(SendGrid, Twilio, OpenAI). These calls can be slow or fail transiently and must not
block the HTTP request/response cycle. The portfolio is hosted on Google App Engine
standard environment, which does not support persistent background threads.

---

## Decision

Use Django Q2 as the task queue with MySQL as the broker. A separate Google Cloud Run
container runs `manage.py qcluster` to process tasks. Tasks are enqueued by Django views
and executed asynchronously by the worker.

---

## Options Considered

### Option 1: Synchronous API calls in Django views
**Pros:** No additional infrastructure.
**Cons:** HTTP requests timeout if external APIs are slow; poor user experience; no retry
on failure.

### Option 2: Django Q2 + Cloud Run worker (chosen)
**Pros:** Decouples API calls from request lifecycle; automatic retry on failure; Cloud
Run scales to zero (no cost when idle).
**Cons:** Additional deployment artifact (Dockerfile.worker); slight delay between form
submission and email delivery.

### Option 3: Google Cloud Tasks / Pub/Sub
**Pros:** Managed queue service; no worker to maintain.
**Cons:** More complex integration; requires rewriting task functions as HTTP endpoints
or Cloud Functions; overkill for a portfolio.

---

## Rationale

Django Q2 with a Cloud Run worker reuses the existing MySQL database as a broker
(no additional infrastructure like Redis or RabbitMQ). Cloud Run's scale-to-zero
model means zero cost when the queue is idle. The Dockerfile is already in place.

---

## Consequences

### Positive
- Contact form returns immediately; email/SMS sent asynchronously.
- Automatic retry logic via Django Q2 for transient API failures.
- Worker scales to zero when not in use.

### Negative
- Email delivery is not instantaneous (seconds to minutes delay).
- Worker must be redeployed alongside the main app when task definitions change.
- MySQL becomes a critical dependency for both the app and the queue broker.

---

## Follow-up Actions

- [ ] Configure `Q_CLUSTER` settings in `settings.py` (orm broker, retry counts, timeout)
- [ ] Deploy worker to Cloud Run with the same environment variables as the main app
- [ ] Add health check endpoint or Cloud Run monitoring for the worker
