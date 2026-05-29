# External Dependencies

All direct dependencies from `requirements.txt` grouped by function.

---

## Django Framework

| Package | Version | Purpose |
|---|---|---|
| Django | 6.0.5 | Core web framework |
| asgiref | 3.11.1 | ASGI compatibility layer |
| sqlparse | 0.5.5 | SQL formatter (Django dev tooling) |
| gunicorn | 26.0.0 | Production WSGI server |

## Database

| Package | Version | Purpose |
|---|---|---|
| mysqlclient | 2.2.8 | MySQL adapter for Django ORM |

## File Storage

| Package | Version | Purpose |
|---|---|---|
| django-storages | 1.14.6 | Custom storage backends (GCS) |
| google-cloud-storage | 3.10.1 | Google Cloud Storage SDK |
| google-cloud-core | 2.6.0 | GCS core client |
| google-resumable-media | 2.9.0 | Resumable upload support |
| google-crc32c | 1.8.0 | Checksum library for GCS |

## Google Auth / APIs

| Package | Version | Purpose |
|---|---|---|
| google-auth | 2.53.0 | Google authentication |
| google-api-core | 2.30.3 | Google API base client |
| googleapis-common-protos | 1.75.0 | Shared proto types |
| proto-plus | 1.28.0 | Proto wrapper for Python |
| protobuf | 7.35.0 | Protocol Buffers runtime |
| pyasn1 | 0.6.3 | ASN.1 parsing (auth) |
| pyasn1_modules | 0.4.2 | ASN.1 modules |
| cryptography | 48.0.0 | Cryptographic primitives |
| cffi | 2.0.0 | C Foreign Function Interface (crypto) |
| pycparser | 3.0 | C parser for cffi |

## Task Queue

| Package | Version | Purpose |
|---|---|---|
| django-q2 | 1.10.0 | Async task queue (background jobs) |
| django-picklefield | 3.4.0 | Pickled field for Django Q2 |

## AI / OpenAI

| Package | Version | Purpose |
|---|---|---|
| openai | 2.38.0 | OpenAI API client (AI assistant) |
| httpx | 0.28.1 | HTTP client (used by openai SDK) |
| httpcore | 1.0.9 | Low-level HTTP transport |
| h11 | 0.16.0 | HTTP/1.1 state machine |
| jiter | 0.15.0 | Fast JSON iterator (openai dependency) |
| anyio | 4.13.0 | Async I/O library |
| sniffio | 1.3.1 | Async library sniffer |
| distro | 1.9.0 | OS detection (openai SDK) |
| tqdm | 4.67.3 | Progress bars |

## Email (SendGrid)

| Package | Version | Purpose |
|---|---|---|
| sendgrid | 6.12.5 | SendGrid email delivery |
| python-http-client | 3.3.7 | HTTP client for SendGrid |

## SMS (Twilio)

| Package | Version | Purpose |
|---|---|---|
| twilio | 9.10.9 | Twilio SMS/voice SDK |
| PyJWT | 2.13.0 | JWT tokens (Twilio auth) |
| Werkzeug | 3.1.8 | WSGI utilities (Twilio dependency) |

## Async HTTP

| Package | Version | Purpose |
|---|---|---|
| aiohttp | 3.13.5 | Async HTTP client |
| aiohttp-retry | 2.9.1 | Retry logic for aiohttp |
| aiohappyeyeballs | 2.6.2 | Happy Eyeballs for aiohttp |
| aiosignal | 1.4.0 | Signal handling for aiohttp |
| frozenlist | 1.8.0 | Immutable list type |
| multidict | 6.7.1 | Multi-value dict for HTTP headers |
| yarl | 1.24.2 | URL parsing/manipulation |
| propcache | 0.5.2 | Property cache (yarl) |

## Data Validation

| Package | Version | Purpose |
|---|---|---|
| pydantic | 2.13.4 | Data validation and serialization |
| pydantic_core | 2.46.4 | Rust core for pydantic |
| annotated-types | 0.7.0 | Type annotation utilities |
| typing-inspection | 0.4.2 | Runtime type inspection |
| typing_extensions | 4.15.0 | Backport typing features |

## HTTP Utilities

| Package | Version | Purpose |
|---|---|---|
| requests | 2.34.2 | Synchronous HTTP client |
| urllib3 | 2.7.0 | Low-level HTTP (requests dependency) |
| certifi | 2026.5.20 | SSL certificate bundle |
| charset-normalizer | 3.4.7 | Charset detection |
| idna | 3.17 | Internationalized domain names |

## Miscellaneous

| Package | Version | Purpose |
|---|---|---|
| MarkupSafe | 3.0.3 | Safe string escaping (Jinja2/Werkzeug) |
| packaging | 26.2 | Version parsing utilities |
| colorama | 0.4.6 | Cross-platform terminal colors |
| tzdata | 2026.2 | IANA timezone database |
| attrs | 26.1.0 | Declarative classes (aiohttp) |

---

## Adding New Dependencies

1. Install in the active virtualenv: `pip install <package>==<version>`
2. Update `requirements.txt`: `pip freeze > requirements.txt`
3. Document the package in this file under the appropriate group
4. If the dependency is significant (new capability), create an ADR
