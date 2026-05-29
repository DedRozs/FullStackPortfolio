# Knowledge Base - FullStackPortfolio

All documentation and planning artifacts for the FullStackPortfolio project live here.

## Structure

```
knowledge-base/
|-- content/           Curated, reviewed documentation
|   |-- architecture/  System architecture and design
|   |-- components/    Per-component documentation
|   |-- api/           API endpoints and contracts
|   |-- data/          Data models and database design
|   |-- development/   Dev setup, testing, conventions
|   |-- deployment/    Infrastructure and deployment guides
|   |-- decisions/     Architecture Decision Records (ADRs)
|   |-- features/      Feature documentation
|   |-- troubleshooting/ Common issues and solutions
|   |-- onboarding/    New developer guides
|-- plans/             Development planning workflow
|   |-- active/        Current in-flight development plans
|   |-- archive/       Completed plans
|-- drafts/            Draft documentation awaiting review
|-- temp/              Temporary files and working notes
|-- uploads/           Uploaded files and external docs
|-- scripts/           AI-generated utility scripts only
```

## Quick Links

- [Architecture Overview](content/architecture/overview.md)
- [Component Map](content/components/overview.md)
- [Development Setup](content/development/setup.md)
- [Coding Conventions](content/development/conventions.md)
- [Deployment & Infrastructure](content/deployment/infrastructure.md)
- [ADR Index](content/decisions/README.md)
- [Quick Start (Onboarding)](content/onboarding/quick-start.md)

## Workflow

**Before starting work:**
1. Check `plans/active/` for existing plans
2. Create a new plan if none exists for the work

**During development:**
1. Draft documentation updates in `drafts/` (mirrors `content/` structure)
2. Update plans as decisions are made

**Before committing:**
1. Move approved drafts from `drafts/` to `content/`
2. Create an ADR in `content/decisions/` for any architectural decision
3. Update this README if the structure changes

## Scripts

All AI-generated utility scripts live in `scripts/`. See [scripts/README.md](scripts/README.md)
for a full index and usage instructions.
