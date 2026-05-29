# Development Setup

## Prerequisites

- Python 3.12 or 3.14
- MySQL 8.x client libraries (for `mysqlclient` compilation)
- Git
- Node.js 20+ (for React development, when that work begins)

---

## Installation

### 1. Clone the repository

```bash
git clone <repo-url>
cd FullStackPortfolio
```

### 2. Create and activate the virtual environment

```bash
# Create
python -m venv .venv

# Activate (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Activate (macOS/Linux)
source .venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

`mysqlclient` requires the MySQL client libraries. On Windows, install
[MySQL Connector/C](https://dev.mysql.com/downloads/connector/c/). On macOS:
`brew install mysql-client`. On Ubuntu: `sudo apt-get install libmysqlclient-dev`.

### 4. Configure environment variables

The project reads configuration from a `.env` file in the repo root. This file is
gitignored. Create your own from the list of required variables:

```bash
# Required
SECRET_KEY="<generate a new key - do not reuse the insecure dev key>"
DJANGO_SETTINGS_MODULE="core.settings"
DEBUG=True

# Database (MySQL)
DB_HOST="<mysql host>"
DB_NAME="Portfolio"
DB_USER="<db user>"
DB_PASSWORD="<db password>"
DB_PORT="3306"

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS="creds.json"
GS_BUCKET_NAME="<gcs bucket name>"

# SendGrid
SENDGRID_API_KEY="<key>"

# Twilio
TWILIO_ACCOUNT_SID="<sid>"
TWILIO_AUTH_TOKEN="<token>"
TWILIO_PHONE_NUMBER="<e164 number>"
SMS_NOTIFICATION_NUMBER="<destination number>"

# OpenAI
OPENAI_API_KEY="<key>"
```

**Important:** Never commit real credentials. The production credentials in the
original `.env` must be rotated before the project goes live (they were committed).

### 5. Generate a new SECRET_KEY

```python
# Run once in a Python shell
from django.core.management.utils import get_random_secret_key
print(get_random_secret_key())
```

Copy the output into `SECRET_KEY` in your `.env`.

### 6. Apply database migrations

```bash
python manage.py migrate
```

### 7. Create a superuser (optional)

```bash
python manage.py createsuperuser
```

### 8. Run the development server

```bash
python manage.py runserver
```

The server starts at `http://127.0.0.1:8000/`. The admin panel is at
`http://127.0.0.1:8000/admin/`.

### 9. Run the background worker (optional)

In a second terminal (with venv active):

```bash
python manage.py qcluster
```

Required if you are testing contact form email/SMS delivery locally.

---

## Verification

```bash
python manage.py check
```

Expected output: `System check identified no issues (0 silenced).`

---

## Common Setup Issues

### mysqlclient fails to compile
Install MySQL development libraries first (see Step 3 above). On Windows, the
precompiled wheel may not be available for Python 3.14; use Python 3.12 in that case.

### "No module named 'core'" on manage.py commands
Ensure the virtual environment is activated before running any `python` command.

### Migrations fail with "Unknown database"
The database named in `DB_NAME` must exist on the MySQL server before running
`migrate`. Create it manually: `CREATE DATABASE Portfolio;`

---

## Next Steps

After setup:
- [Architecture Overview](../architecture/overview.md) - understand the system design
- [Component Map](../components/overview.md) - understand what exists and what to build
- [Coding Conventions](conventions.md) - follow the project's standards
