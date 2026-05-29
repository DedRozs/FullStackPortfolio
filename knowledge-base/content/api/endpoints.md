# API Endpoints

No custom API endpoints have been implemented yet.

This document will be updated as Django views and URL patterns are added to the
`apps/` modules. See [Component Map](../components/overview.md) for the planned
app structure.

---

## Existing Endpoints

| Path | Method | Purpose | Status |
|---|---|---|---|
| `/admin/` | GET | Django admin panel | Built-in, active |

---

## Planned Endpoints

| Path | Method | App | Purpose |
|---|---|---|---|
| `/` | GET | home | Home/hero page |
| `/about/` | GET | about | About page |
| `/contact/` | GET | contact | Contact form page |
| `/contact/submit/` | POST | contact | Contact form submission |

Additional endpoints will be added for the three portfolio demo applications once
those apps are defined.
