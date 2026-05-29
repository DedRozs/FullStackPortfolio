# Infrastructure and Deployment

---

## Hosting Platform

**Primary:** Google App Engine (Standard Environment, Python 3.12 runtime)
**Background Worker:** Google Cloud Run (Docker container)

---

## Environments

| Environment | Platform | Notes |
|---|---|---|
| Local development | `python manage.py runserver` | SQLite or MySQL via .env |
| Staging | Not yet configured | |
| Production | Google App Engine | MySQL on Cloud SQL |

---

## Google App Engine

The main Django application runs on GAE standard environment. Configuration requires an
`app.yaml` file in the repo root (not yet created).

Minimal `app.yaml` structure:

```yaml
runtime: python312
entrypoint: gunicorn -b :$PORT core.wsgi:application

env_variables:
  DJANGO_SETTINGS_MODULE: core.settings
  # All other secrets should come from Google Secret Manager, not app.yaml

handlers:
  - url: /static
    static_dir: static/
  - url: /.*
    script: auto
```

**Important:** Do not embed secrets in `app.yaml`. Use Google Secret Manager and
inject via environment variables at runtime.

---

## Cloud Run Worker

**Dockerfile:** `Dockerfile.worker`
**Command:** `python manage.py qcluster`
**Purpose:** Processes Django Q2 async task queue (email, SMS, AI calls)

```dockerfile
FROM python:3.14
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "manage.py", "qcluster"]
```

The worker scales to zero when the queue is empty. It needs the same environment
variables as the main app (database, API keys).

Build and deploy:
```bash
# Build image
docker build -f Dockerfile.worker -t portfolio-worker .

# Deploy to Cloud Run (requires gcloud CLI)
gcloud run deploy portfolio-worker \
  --image gcr.io/<project-id>/portfolio-worker \
  --platform managed \
  --region us-central1 \
  --set-env-vars DJANGO_SETTINGS_MODULE=core.settings
```

---

## Database: Google Cloud SQL (MySQL 8.x)

- Instance connection via direct IP (current setup) or Cloud SQL Auth Proxy
- Database: `Portfolio`
- Access controlled via `DB_USER` / `DB_PASSWORD` environment variables

**Production security checklist before launch:**
- Rotate all database credentials (the `.env` credentials were committed to the repo)
- Restrict Cloud SQL instance access to GAE service account only
- Enable SSL for database connections
- Use Cloud SQL Auth Proxy instead of direct IP in production

---

## File Storage: Google Cloud Storage

**Bucket:** `ai-fullstack-portfolio.appspot.com`
**SDK:** `django-storages` + `google-cloud-storage`
**Credentials:** `creds.json` (Google Cloud service account key, gitignored)

When media file support is added, `settings.py` will configure:
```python
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = os.environ['GS_BUCKET_NAME']
```

---

## CI/CD

GitHub Actions workflows are defined in `.github/workflows/`. Specific workflow files
not yet implemented.

---

## Monitoring

Not yet configured. Planned:
- Google Cloud Logging (automatic on GAE/Cloud Run)
- Google Cloud Error Reporting
- Uptime checks via Google Cloud Monitoring

---

## Secret Management

Current state: all secrets in `.env` (gitignored). For production, migrate to
Google Secret Manager and update `settings.py` to fetch secrets at startup.

**Credentials to rotate before production launch:**
- `SECRET_KEY` - generate a new one
- `DB_PASSWORD` - rotate MySQL user password
- `SENDGRID_API_KEY` - revoke and regenerate
- `TWILIO_AUTH_TOKEN` - revoke and regenerate
- `OPENAI_API_KEY` - revoke and regenerate
- Google Cloud service account key (`creds.json`) - rotate
