---
name: constraint-event-idempotency
description: "Use when: implementing an event handler or event-driven workflow that must tolerate duplicate message delivery from a broker."
mode: agent
---

## Event Handler Idempotency

Every event handler must be idempotent. Processing the same event more than once must
produce exactly the same observable outcome as processing it once.

Required implementation pattern:

1. Extract the event `id` field from the CloudEvents envelope on every invocation.
2. Check a deduplication store (database table, cache, or equivalent) for the event id
   before processing.
3. If the id is already present in the deduplication store, skip all processing and
   return a success response without side effects.
4. If the id is not present, execute the handler logic and record the id in the
   deduplication store within the same transaction as the side-effect commit.

Additional rules:

- Never assume a message broker guarantees exactly-once delivery; always implement
  idempotency in the handler regardless of broker claims.
- Deduplication store lookups must be within the same atomic transaction as the
  state-changing operation where possible.
- Event chains must not exceed two levels deep. If a handler reaction would trigger a
  further chain beyond depth two, use a saga or process manager instead.
- Subscribe by event type, never by publisher class or module name; this decouples
  handler from publisher.
