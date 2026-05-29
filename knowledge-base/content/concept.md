# Portfolio Site - Concept Document

## Overview

A professional full stack portfolio site for Joseph Prince, a Full Stack Developer.
The site targets hiring managers and potential consulting clients. It is designed to
demonstrate technical depth through working, self-contained projects and to stand out
visually through a Cyberpunk color scheme.

---

## Goals

- Present Joseph Prince as a credible Full Stack Developer and consultant.
- Demonstrate real-world capability through 3 embedded, self-contained project demos.
- Provide an AI assistant that introduces Joseph's background and answers questions
  about his skills and work - functioning as a live capability demo in itself.
- Give hiring managers and clients a direct contact path through a contact form and
  social media links.

---

## Target Audience

- **Primary:** Hiring managers evaluating candidates for full stack or senior developer
  roles.
- **Secondary:** Prospective consulting clients seeking a developer for contract work.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6, Python |
| Frontend | React (served via Django static files) |
| Database | MySQL (Google Cloud SQL) |
| File Storage | Google Cloud Storage (via django-storages) |
| Hosting | Google App Engine (Python 3.12 runtime) |
| Background Jobs | Django Q2 (Cloud Run worker) |
| AI | OpenAI API |
| Email | SendGrid |
| SMS | Twilio |
| CI/CD | GitHub Actions |

---

## Site Structure

### Home

- Hero section introducing Joseph Prince.
- Profile data pulled from LinkedIn.
- Navigation to all major sections.

### Projects

Three self-contained Django apps under `apps/`, each demonstrating a distinct
technical domain. Specific projects to be determined. Each app is independently
scoped with its own models, views, and URLs.

### AI Assistant

An interactive chat interface powered by the OpenAI API. The assistant:

1. Opens with a brief scripted introduction about Joseph - his background, skills,
   and the type of work he does.
2. Then opens for free-form questions, answering as a knowledgeable representative
   of Joseph's portfolio.

The assistant itself serves as a live demonstration of AI integration skill.

### About

Professional background summary for Joseph Prince, Full Stack Developer.
Data sourced from LinkedIn profile. Covers skills, experience, and consulting
availability.

### Contact

- Contact form (submissions delivered via SendGrid email; optional Twilio SMS
  notification to Joseph).
- Links to social media profiles (LinkedIn and others to be determined).

---

## Differentiators

- **Cyberpunk visual theme** - a deliberate, high-contrast aesthetic that makes the
  site immediately memorable against generic portfolio templates.
- **Working embedded apps** - project demos are live and interactive, not screenshots.
- **AI assistant as a live demo** - the chat feature demonstrates AI integration
  rather than just claiming it as a skill.

---

## Architecture Notes

- Django serves the React frontend as static files; no separate Node server.
- Each app in `apps/` is a self-contained Django application registered in
  `INSTALLED_APPS`.
- Background tasks (email queuing, etc.) run through Django Q2 on a Cloud Run worker.
- All secrets injected at deploy time via GitHub Actions secrets; never committed to
  the repository.

---

## Open Decisions

| # | Question | Notes |
|---|---|---|
| 1 | What are the 3 project apps? | To be decided once site shell is in place. |
| 2 | Which social media platforms are linked? | LinkedIn confirmed; others TBD. |
| 3 | AI assistant persona and knowledge boundary | Define what questions it will and will not answer. |
| 4 | LinkedIn data sync strategy | Static embed vs. live API pull. |
