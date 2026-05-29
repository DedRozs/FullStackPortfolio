# Quick Start Guide

Get the FullStackPortfolio development environment running in under 30 minutes.

---

## What You Are Setting Up

A personal developer portfolio built with Django 6.0.5 and React, deployed on Google App
Engine with a Cloud Run background worker. The project is currently a well-configured
skeleton - Django is initialized, credentials and infrastructure are wired up, but no
app views, models, or React code have been built yet.

---

## Step 1: Prerequisites (5 minutes)

Install if not already present:
- Python 3.12 or 3.14: https://python.org
- MySQL client libraries (for `mysqlclient`):
  - Windows: MySQL Connector/C from https://dev.mysql.com/downloads/connector/c/
  - macOS: `brew install mysql-client`
  - Ubuntu: `sudo apt-get install libmysqlclient-dev`
- Git

---

## Step 2: Clone and Install (10 minutes)

```bash
git clone <repo-url>
cd FullStackPortfolio

# Create virtual environment
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

## Step 3: Configure Environment (5 minutes)

Create a `.env` file in the repo root. Ask the project owner for credentials, or
configure your own (you need a MySQL database and the various API keys).

Minimum required variables for local development:
```
SECRET_KEY="<generate with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'>"
DJANGO_SETTINGS_MODULE=core.settings
DEBUG=True
DB_HOST=<mysql host>
DB_NAME=Portfolio
DB_USER=<db user>
DB_PASSWORD=<db password>
DB_PORT=3306
```

---

## Step 4: Apply Migrations and Verify (5 minutes)

```bash
python manage.py migrate
python manage.py check
```

Expected: `System check identified no issues (0 silenced).`

---

## Step 5: Run the Development Server

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/admin/` - the Django admin login page should appear.

---

## What to Read Next

Now that your environment is running, orient yourself with these documents:

1. [Architecture Overview](../architecture/overview.md) - What the system does and how the pieces connect
2. [Component Map](../components/overview.md) - What exists, what needs to be built
3. [Coding Conventions](../development/conventions.md) - How code should be written
4. [ADR Index](../decisions/README.md) - Why key architectural decisions were made

---

## Common Issues

**`pip install` fails on `mysqlclient`**
You are missing the MySQL client libraries. See prerequisites above.

**`python manage.py migrate` fails with "Unknown database"**
The MySQL database must exist before running migrations:
```sql
CREATE DATABASE Portfolio;
```

**`python manage.py check` shows "No module named X"**
The virtual environment is not activated. Run `.\.venv\Scripts\Activate.ps1` first.
