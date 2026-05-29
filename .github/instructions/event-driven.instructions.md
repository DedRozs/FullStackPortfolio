---
applyTo: "**/*.{py,ts,cs,java,kt}"
description: "Use when implementing event-driven systems, publishing or consuming domain events, designing message-based or async communication, or applying the Transactional Outbox Pattern. Covers event naming, idempotency, publisher-consumer decoupling, and event chain depth limits."
---
<!-- v2.0 | Updated: 2026-05-01 | Pattern: Event-Driven Architecture -->

# Event-Driven Architecture Instructions

Apply these rules to all event-driven systems in this project.

---

## Core Rules

1. Events represent **facts that already occurred** - they are immutable, past-tense, and cannot change after publication.
2. Publishers are **fully decoupled** from consumers. A publisher never imports, calls, or references a consumer.
3. All handlers **must be idempotent** - processing the same event twice produces the same result.
4. Publish events **only after** successful state persistence, or use the Transactional Outbox Pattern.
5. Event chains must not exceed **2 levels deep**. Use a saga for deeper workflows.
6. Events carry **sufficient data** for consumers to act without re-querying the originating service.

---

## Event Envelope - CloudEvents Standard

All events must follow the [CloudEvents v1.0](https://cloudevents.io) envelope specification.

### Required Fields

| Field | Type | Rule |
|-------|------|------|
| `id` | UUID | Unique per event; used for deduplication |
| `type` | string | Namespaced event type - e.g., `order.placed` |
| `source` | URI | Originating service - e.g., `/order-service` |
| `specversion` | string | Always `"1.0"` |
| `time` | ISO 8601 | UTC timestamp of when the fact occurred |
| `datacontenttype` | string | Always `"application/json"` |
| `data` | object | Domain payload; schema registered in schema registry |

### Recommended Extensions

| Field | Rule |
|-------|------|
| `correlationid` | UUID tracing a business transaction across services; propagate from trigger |
| `causationid` | `id` of the event or command that caused this event |
| `dataschema` | Schema registry URI for the `data` payload |
| `subject` | Entity subject - e.g., `order-123` |
| `version` | Semver schema version of `data` - e.g., `"2.0"` |

### Data Payload Rules

- Include all fields a consumer needs to act without a secondary lookup to the source service.
- Exclude credentials, raw PII (tokenize or encrypt instead), and internal identifiers irrelevant to consumers.
- For large payloads (> 64 KB), use the **Claim Check Pattern**: store payload in object storage, include the URI in the event.

### Canonical Envelope Example

```python
# domain/events/order_placed.py
from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID, uuid4

@dataclass(frozen=True)
class OrderPlaced:
    id: UUID = field(default_factory=uuid4)
    type: str = "order.placed"
    source: str = "/order-service"
    specversion: str = "1.0"
    time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    datacontenttype: str = "application/json"
    correlationid: UUID = None
    causationid: UUID = None
    data: dict = field(default_factory=dict)  # order_id, customer_id, items, total
```

---

## Naming Conventions

### Event Types

- Format: `{domain}.{entity}.{past-tense-verb}` - e.g., `order.placed`, `payment.failed`
- Multi-word segments use kebab-case: `inventory.item.stock-depleted`
- CloudEvents reverse-DNS prefix: `com.company.order.placed`
- **Never** use imperative names: `order.place` is wrong; `order.placed` is correct.

### Topics, Exchanges, and Queues

- Topic name mirrors event type: `{domain}.{entity}.{past-tense-verb}`
- Dead letter queue: append `.dlq` - e.g., `order.placed.dlq`
- Consumer group: `{consuming-service}.{event-type}` - e.g., `inventory-service.order.placed`
- Namespace per environment: `{env}.{topic-name}` - e.g., `prod.order.placed`

### Handler and Publisher Classes

- Handler format: `{Action}{Entity}On{Event}Handler` - e.g., `ReserveInventoryOnOrderPlacedHandler`
- One handler class per event type - no multi-event handler classes.
- Publisher format: `{Entity}EventPublisher` - e.g., `OrderEventPublisher`

---

## Delivery Semantics

Select one guarantee per consumer use case and design the handler accordingly.

| Guarantee | Broker Support | Handler Requirement | Use When |
|-----------|---------------|---------------------|----------|
| At-most-once | Fire and forget | No dedup needed | Metrics, telemetry |
| At-least-once | Ack-based | Handler MUST be idempotent | Business events (default) |
| Exactly-once | Transactional (Kafka EOS, etc.) | Idempotent + distributed tx | Financial, inventory |

**Default for all business events: at-least-once with idempotent handlers.**

---

## Reliable Publishing - Transactional Outbox

Never publish to the broker in the same code path as a database transaction without a durability guarantee. Use the **Transactional Outbox Pattern**:

1. In the same DB transaction as the state change, insert the event into an `outbox` table.
2. A relay process reads unpublished outbox rows and publishes to the broker.
3. Mark rows published only after broker acknowledgement.
4. Guarantees zero event loss if the service crashes between write and publish.

```python
# Inside a database transaction - no phantom events on rollback
with db.transaction():
    order = Order.create(order_data)
    db.outbox.insert(event=OrderPlaced(order).to_envelope())
# Relay publishes asynchronously; publisher does not wait
```

The **Transactional Inbox Pattern** is the consumer-side complement: persist the event to an inbox table before processing to prevent duplicate side effects on broker redelivery.

---

## DDD Integration - Domain Events vs Integration Events

- **Domain event**: raised inside the domain model; lives in `domain/events/`. Consumed only within the same bounded context.
- **Integration event**: published to the broker for cross-service consumption; lives in `infrastructure/messaging/`. Translated from domain events at the application layer.
- Never publish domain events directly to an external broker. Translate to integration events at the application layer boundary.
- The translation step is the anti-corruption layer - it shields the domain model from broker envelope concerns.
- Domain events are not frozen to the CloudEvents envelope format; integration events always are.

---

## Publisher Rules

- Fire and forget: publishers do not await handler results or acknowledgements.
- Always set `correlationid` and `causationid` on every published event.
- Log `event.id`, `event.type`, and `correlationid` at INFO level on every publish.
- Publish only after state is committed, or via the Transactional Outbox Pattern.
- Never embed consumer-specific routing logic in a publisher.

---

## Handler / Consumer Rules

- Each handler class handles **exactly one** event type. One class, one responsibility.
- Check `event.id` against a processed-events store before executing (idempotency gate).
- Acknowledge the message **only after** successful processing.
- Handler errors must not propagate to or cancel sibling handlers.
- Never call back to the publisher service synchronously from a handler.
- Log `correlationid`, `causationid`, and `event.id` at INFO at handler entry and exit.

### Canonical Idempotent Handler

```python
# infrastructure/messaging/handlers/reserve_inventory_on_order_placed.py
class ReserveInventoryOnOrderPlacedHandler:
    def handle(self, event: OrderPlaced) -> None:
        if self._store.already_processed(event.id):
            return  # Idempotency gate - safe to skip
        self._reserve_items(event.data["items"])
        self._store.mark_processed(event.id)  # Commit atomically with work
```

---

## Error Handling and Resilience

### Retry Policy

- Retry transient failures with exponential backoff: 1 s, 2 s, 4 s, 8 s, ...
- Maximum 3-5 attempts (configure per handler based on SLA sensitivity).
- Validation failures and schema mismatches: route directly to DLQ, do not retry.

### Dead Letter Queue

- Every subscription **must** have a configured DLQ. Absence is a production incident.
- DLQ message must include: original payload, failure reason, handler name, timestamp, attempt count.
- DLQ depth > 0 triggers an alert. Treat stale DLQ items as a P2 incident.
- Provide an operational runbook for DLQ inspection and selective reprocessing.

### Circuit Breaker

- Wrap all downstream service calls inside handlers with a circuit breaker.
- Open circuit after 5 consecutive failures; half-open probe after 30 s.
- Log all circuit state transitions at WARN with the downstream target name.

### Poison Message Detection

- After N DLQ re-enqueue attempts, quarantine the message and page on-call.
- A single poison message must never halt queue processing for other messages.
- Quarantined messages must be inspectable and replayable after the root cause is fixed.

---

## Schema Evolution and Versioning

### Backward-Compatible Changes (safe to deploy independently)

- Adding optional fields with safe defaults.
- Adding new event types or new optional envelope extensions.

### Breaking Changes (require coordinated deployment)

- Removing or renaming fields.
- Changing field types or semantics.
- Changing event type strings or topic names.

### Breaking Change Process

1. Register the new schema version in the schema registry before any deployment.
2. Deploy producers publishing both old and new schema versions in parallel.
3. Migrate all consumers to the new schema during the parallel run (minimum one sprint).
4. Publish a sunset date for the old schema; remove only after all consumers are migrated and confirmed.

### Schema Compatibility Matrix

| Change Type | Safe to Deploy | Registry Policy Required |
|-------------|---------------|--------------------------|
| Add optional field | Yes | BACKWARD compatible |
| Remove field | No | Follow breaking change process |
| Rename field | No | Follow breaking change process |
| Add new event type | Yes | New subject entry |
| Change field type | No | Follow breaking change process |

### Schema Registry

- **All event schemas must be registered** in a schema registry (Confluent Schema Registry, AWS Glue, Apicurio, etc.).
- Producers validate events against the registry before publishing.
- Consumers validate incoming events against the registry before processing.
- Default compatibility policy: **BACKWARD** (additive-only unless the breaking change process is followed).

---

## Security Rules

- All broker connections use **TLS**. Plaintext broker connections are prohibited.
- Producers and consumers authenticate with **per-service credentials**. Shared keys are prohibited.
- Apply **least-privilege topic-level authorization**: producers write-only, consumers read-only on their topics.
- Events must **never contain** secrets, passwords, API keys, or session tokens.
- PII fields must be tokenized or field-level encrypted before inclusion in any event payload.
- Authentication context (acting user ID) belongs in `metadata`, never raw in `data`.
- Rate-limit event ingestion endpoints to prevent broker flooding (DoS mitigation).
- Validate event schema at the consumer boundary before processing - reject malformed envelopes.
- Audit log all schema registry access (schema registration, deletion, compatibility overrides).

---

## Observability Standards

Every event-driven feature must implement all four observability signals.

| Signal | Required Items |
|--------|----------------|
| **Logs** | INFO on publish: `event.id`, `event.type`, `correlationid`. INFO on handler start/complete. ERROR on failure with full stack trace and `event.id`. |
| **Metrics** | Published count (counter, per type), consumed count (counter, per type), handler processing time (histogram, p50/p95/p99), DLQ depth (gauge), handler error rate (counter), consumer lag (gauge). |
| **Traces** | Propagate W3C Trace Context in event `metadata`. Create a child span per handler execution tagged with `event.type` and `event.id`. |
| **Alerts** | DLQ depth > 0, handler error rate > threshold, consumer lag > SLA window, circuit breaker open. |

Alert thresholds must be defined before a feature ships to production. "TBD" thresholds are not acceptable for production launch.

---

## Performance and Scalability

- **N+1 prohibition**: handlers must not issue one query per event in a batch. Load referenced entities in bulk before processing the batch.
- **Fanout scope**: target events at the narrowest applicable consumer group. Unbounded broadcast requires explicit justification.
- **High-frequency events** (> 100/s): document expected rate, acceptable consumer lag, and throttling strategy before implementation.
- **Backpressure**: consumers falling behind must reduce prefetch count / maxConcurrency, not drop messages.
- **No blocking I/O in async handlers**: async handlers use async I/O exclusively. Blocking calls starve the event loop.
- **Consumer lag monitoring**: alert when lag exceeds the processing window defined for the event type.
- **Batching**: prefer batched delivery over single-message polling for high-throughput consumers where the broker supports it.

---

## Event Ordering

- By default, assume **no ordering guarantee**. Design handlers to be order-independent.
- When strict ordering is required (e.g., state machine progression): use a single partition key per entity and process that partition serially.
- Never assume global ordering across partitions or queue instances.
- Document ordering requirements explicitly per event type in the schema registry or ADR.

---

## Consumer Groups and Competing Consumers

- Each logical consumer registers its own **consumer group** so it receives all events independently.
- Within a consumer group, multiple instances **compete** for messages to scale throughput horizontally.
- Competing consumers require idempotent handlers - the same message may reach different instances on retry.
- Do not share a consumer group between services with different business purposes.
- Scale consumer instances by monitoring consumer lag, not CPU or memory alone.

---

## Saga Pattern

Use sagas for workflows spanning multiple services where a distributed transaction is needed.

### Choreography (use for simple workflows, <= 3 steps)

- Each service reacts to domain events and publishes its own outcome events.
- No central coordinator - flow is implicit in the chain of events.
- Pros: simple, no single point of failure. Cons: flow is hard to visualize beyond 3 steps.

### Orchestration (use for complex workflows, > 3 steps)

- A **Saga Orchestrator** sends commands to services and awaits their reply events.
- The orchestrator state machine is a first-class domain object with its own persistence.
- Pros: explicit flow, observable, easy to add steps. Cons: orchestrator is a coordination point.

### Compensation Rules

- Every saga step that can fail must have a defined compensating transaction documented alongside it.
- Compensating transactions are appended to the event log as new events - never mutate past events.
- Compensation is **not rollback** - it is a forward-correcting action that undoes the business effect.
- The saga must handle partial compensation failures; document the manual recovery path.

---

## CQRS Integration

When EDA is combined with CQRS:

- The write model publishes domain events; read model projections consume them via the broker.
- Projections are rebuilt from the event log on demand - never via direct DB queries to the write model.
- Projections never call back to the write model - data flows one way only.
- Read model staleness is expected and acceptable; communicate staleness to the UI via cache-control headers or explicit "as-of" timestamps in responses.

---

## Event Sourcing vs Event-Driven Architecture

These are distinct patterns often confused:

| Concern | Event-Driven Architecture | Event Sourcing |
|---------|--------------------------|----------------|
| Primary goal | Decoupled service communication | State derivation from an immutable log |
| State storage | Current state in DB; events are notifications | Events ARE the state; DB is a materialized view |
| Event log | Optional; broker retention policy applies | Required; the log is permanent and authoritative |
| Replayability | Optional | Mandatory |
| Complexity | Low-medium | High |

EDA does not require event sourcing. Event sourcing implies EDA. Adopt event sourcing only when audit completeness and full temporal query capability justify the complexity.

---

## Event Replay and Recovery

- The event log (Kafka topic, EventStore stream, etc.) is the system of record for all published events.
- Consumers must be able to **replay events from a known offset** without side effects. Design and test for replay safety.
- Test replay explicitly: process the same batch twice and assert idempotent results.
- Document the retention period for every topic. Default: retain long enough to rebuild any downstream projection from scratch.
- Provide an operational procedure for selective replay (reprocess a specific time window or entity partition).

---

## Broker Selection Reference

| Broker | Best For | Ordering | Replay | Exactly-Once |
|--------|----------|----------|--------|--------------|
| **Kafka** | High-throughput, durable log, event sourcing | Per partition | Yes (log retention) | Yes (EOS transactions) |
| **RabbitMQ** | Low-latency, complex routing, work queues | Per queue | No (after ack) | No |
| **AWS SNS/SQS** | Managed, multi-subscriber fanout, serverless | SQS FIFO only | No | No |
| **Azure Service Bus** | Managed, enterprise messaging, sessions | Sessions only | No | No |
| **Google Pub/Sub** | Managed, global scale, at-least-once | No | Via snapshots | No |

---

## Testing Standards

| Test Type | What to Cover | Required |
|-----------|-------------|----------|
| Unit | Handler logic in isolation. Mock event bus. Inject pre-built event objects. | Yes |
| Contract | Schema compliance against schema registry or committed schema snapshots. | Yes |
| Integration | Handler + real broker (containerized). Verify full publish-consume cycle. | Yes |
| Idempotency | Submit same event twice; assert side effect occurs exactly once. | Yes |
| Failure | DLQ routing, retry exhaustion, circuit breaker open behavior. | Yes |
| Schema migration | Old-schema events consumed correctly by new-schema handler. | On schema change |
| Load | Consumer processes events within SLA under expected peak event rate. | High-frequency events |

Test naming pattern: `test_{handler}_given_{context}_when_{event}_then_{outcome}`.

---

## Anti-Patterns

| Anti-Pattern | Why It Is Wrong | Correct Approach |
|---|---|---|
| Event as command | Couples producer to consumer intent | Events are facts; use commands for intent |
| Logic inside event class | Turns data into an active object | Events are pure data; logic lives in handlers |
| Synchronous publish-wait | Blocks publisher until all handlers finish | Publish is fire-and-forget |
| Deep event chains (> 2 levels) | Unpredictable cascades, impossible to debug | Use saga orchestration for complex flows |
| Circular event dependencies | A triggers B which triggers A | Redesign with an explicit saga coordinator |
| Missing DLQ | Failed events silently lost | Every subscription requires a configured DLQ |
| Non-idempotent handler | Double-charge, double-deduction on retry | Check `event.id` before processing |
| Micro-event storm | Excessive traffic, exposes implementation internals | Right-size events to business facts |
| PII in event payload | Data governance and compliance risk | Tokenize or field-encrypt before publishing |
| Shared mutable consumer state | Race conditions across parallel consumer instances | Handlers are stateless; state lives in persistence |
| Version-less events | Breaking schema changes crash consumers | Include `version` in every event envelope |
| No schema registry | Schema drift across teams and deployments | Register and validate all schemas centrally |
| Publishing before commit | Phantom events on transaction rollback | Use Transactional Outbox Pattern |
| Domain event on broker | Couples domain model to broker envelope format | Translate to integration event at app layer boundary |

---

## When to Use Event-Driven Architecture

### Use EDA When

- Multiple services react to the same business fact without knowing about each other.
- Temporal decoupling is acceptable - producers and consumers need not be online simultaneously.
- Audit trail, event replay, or historical query capability is required.
- Services are owned by different teams and must be independently deployable.
- The workflow naturally spans multiple bounded contexts.

### Avoid EDA When

- Strong consistency is non-negotiable and eventual consistency is unacceptable.
- The entire operation must succeed or fail atomically with no saga compensation path.
- The team lacks distributed tracing tooling to debug async flows in production.
- The domain is simple CRUD with a single consumer - direct API calls are simpler and more observable.

### Hybrid Approach

For most systems, combine EDA with synchronous request/response: use synchronous calls for the critical path that requires immediate feedback, and publish events for side effects that can be processed asynchronously. This avoids eventual-consistency complexity on the happy path while still decoupling non-critical consumers.

---

## Implementation Checklist

### Event Schema

- [ ] All required CloudEvents envelope fields present (`id`, `type`, `source`, `specversion`, `time`, `datacontenttype`, `data`)
- [ ] `correlationid` and `causationid` extensions included on every event
- [ ] Event type follows `{domain}.{entity}.{past-tense-verb}` naming convention
- [ ] Schema registered in schema registry with version before first deployment
- [ ] Events are immutable (frozen dataclass, record type, or equivalent)
- [ ] Events carry sufficient data; no secondary lookup required to act on the event
- [ ] PII tokenized or field-encrypted before inclusion

### Reliability

- [ ] Transactional Outbox Pattern or equivalent durability guarantee in place
- [ ] Every subscription has a configured DLQ with alerting
- [ ] Retry policy with exponential backoff configured per handler
- [ ] Circuit breaker wraps all downstream calls inside handlers
- [ ] All handlers are idempotent and check `event.id` before processing
- [ ] Poison message quarantine policy and operational runbook defined

### Schema Evolution

- [ ] Schema version field present in every event envelope
- [ ] Breaking change process followed for any non-additive schema change
- [ ] Old and new schema versions run in parallel during migration sprint

### Observability

- [ ] Structured logs on publish and consume include `correlationid` and `event.id`
- [ ] Metrics instrumented: published count, consumed count, handler latency, DLQ depth, error rate, consumer lag
- [ ] W3C Trace Context propagated through event `metadata`; child span created per handler
- [ ] Alerts defined and thresholds set before production launch: DLQ depth, error rate, consumer lag, circuit breaker

### Security

- [ ] Broker connections use TLS
- [ ] Per-service credentials for broker authentication (no shared keys)
- [ ] Topic-level least-privilege authorization applied
- [ ] No secrets or raw PII in event payloads
- [ ] Schema registry access is audited

### Testing

- [ ] Unit tests for all handler logic
- [ ] Contract tests for all event schemas
- [ ] Integration test covers full publish-consume round-trip
- [ ] Idempotency tested with duplicate event submission
- [ ] Failure paths tested: DLQ routing, retry exhaustion, circuit breaker
- [ ] Replay safety tested: same event batch processed twice, idempotent result asserted

