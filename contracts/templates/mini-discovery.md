# Mini-Discovery Artifact

<!-- This artifact is produced by ticket-intake-agent (Stage 0) and enriched by
     codebase-context-agent before the first routed phase orchestrator is invoked.
     Complete every required section. The Codebase Context section is optional and
     is appended by codebase-context-agent if prior archive artifacts exist.
     Validate against: contracts/schemas/mini-discovery.schema.json -->

**Produced by:** `.github/agents/ticket-intake-agent.agent.md` (enriched by `.github/agents/codebase-context-agent.agent.md`)
**Consumed by:** First agent listed in the Routed Phases section

---

## Ticket Identity

| Field | Value |
|---|---|
| Issue key | [e.g., TT-42] |
| Issue type | [e.g., Bug, Story, Epic, Chore, Spike] |
| Project key | [e.g., TT] |

---

## Summary

[Ticket summary field verbatim from the ticketing backend]

---

## Description

[Ticket description field verbatim from the ticketing backend. Write "(none)" if the ticket has no description.]

---

## Acceptance Criteria

<!-- Extracted by ticket-intake-agent: lines/sentences starting with Given, When, or Then -->

[List each Given/When/Then clause on a separate line, or write "(none found in ticket body)" if none were extracted.]

---

## Ticket Size

[One of: spike | chore | story | epic]

Derived from issue type.

---

## Routed Phases

[Ordered list of phase orchestrator names to invoke. One per line. Determined by Ticket Size.]

Example for story:
- domain-modeling-orchestrator
- development-orchestrator
- qa-orchestrator
- documentation-orchestrator

---

## Codebase Context

<!-- Appended by codebase-context-agent. If no prior archive exists, all sub-sections
     record "No prior pipeline artifact found." -->

### Bounded Contexts

[Deduplicated bounded context names from the most recent pipeline archive and architecture overview. One per line, or "No prior pipeline artifact found."]

### Key ADR Decisions

[Bullet list of the five most recently added ADR titles from decision-log.md, or "No prior pipeline artifact found."]

### Established Patterns

[Recurring architectural pattern names from the most recent archive artifacts. One per line, or "No prior pipeline artifact found."]

### Technology Stack

[Technology choices from the most recent architecture-to-domain-modeling artifact. One per line, or "No prior pipeline artifact found."]
