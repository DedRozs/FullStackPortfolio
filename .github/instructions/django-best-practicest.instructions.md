---
applyTo: "*"
---


# Enterprise-Grade Monolith Architecture Guide

> Assumption: We are building an **enterprise-grade modular monolith**.

## 1. Architecture Overview

For an enterprise monolith, the key is **strong internal modularity**:

- One deployable unit (monolith).
- Internally split into **bounded contexts / modules** (e.g., `identity`, `billing`, `catalog`).
- Each module encapsulates:
  - API / interface layer
  - Application / use case layer
  - Domain layer
  - Infrastructure layer
- Modules interact mainly via:
  - Direct service calls (within the same process), or
  - Domain events / application events for decoupled communication.

This keeps all the benefits of a monolith (simple deployment, easier debugging) while avoiding the chaos of a "big ball of mud".

---

## 2. Layers and Responsibilities

We use a **hexagonal / clean architecture** style inside the monolith. All dependencies point **inwards** toward the domain.

### 2.1 Presentation / Interface Layer

**Purpose**

- Handle external protocols and I/O:
  - HTTP/REST/GraphQL controllers
  - gRPC endpoints
  - Web UI adapters, CLI handlers, etc.
- Map transport data into **application commands/queries**.

**Responsibilities**

- Request/response mapping (DTOs ⇄ JSON, protobuf, etc.).
- Input validation (basic syntactic checks).
- Authentication (extract identity from tokens/headers).
- Calling appropriate application services.

**Non-responsibilities**

- Business rules and decisions.
- Persistence or transaction management.

---

### 2.2 Application Layer

**Purpose**

- Orchestrate **use cases**.
- Coordinate domain objects, transactions, and infrastructure.

**Typical contents**

- Application services (e.g., `RegisterUserService`, `PlaceOrderService`).
- Command/Query DTOs (`RegisterUserCommand`, `GetOrderQuery`).
- Application-level interfaces:
  - `UserRepository`
  - `OrderRepository`
  - `EmailSender`
  - `PaymentGateway`

**Characteristics**

- Thin but explicit use case orchestration.
- Uses domain model to enforce invariants.
- Does not contain technical details of persistence or HTTP.

---

### 2.3 Domain Layer

**Purpose**

- Represent the **core business logic** and rules.
- Stay independent from frameworks and infrastructure.

**Typical contents**

- Entities (with identity and lifecycle), e.g. `User`, `Order`.
- Value Objects (immutable, defined by value), e.g. `Email`, `Money`, `Address`.
- Aggregates and aggregate roots, e.g. `Order` aggregate with `OrderLine` items.
- Domain services, for logic that doesn’t naturally belong to a single entity.
- Domain events, e.g. `UserRegistered`, `OrderPlaced`.

**Characteristics**

- No direct database or network code.
- Pure domain language and invariants.
- High testability (simple unit tests without DB).

---

### 2.4 Infrastructure Layer

**Purpose**

- Implement technical details required by the domain and application layers.

**Typical contents**

- ORM models and repository implementations.
- Message bus / queue adapters.
- HTTP clients for external services.
- Email/SMS gateways.
- File storage adapters.

**Characteristics**

- Depends on frameworks (ORM, HTTP clients, etc.).
- Implements interfaces defined in the application layer.
- Can be swapped or modified without changing domain logic.

---

## 3. Domain-Driven Design (DDD) in the Monolith

### 3.1 Bounded Contexts

Split the monolith into **bounded contexts** aligned to business capabilities:

- `Identity` – users, authentication, roles.
- `Billing` – invoices, payments, subscriptions.
- `Catalog` – products, categories, pricing.

Each context has its own model, language, and internal structure. Cross-context interaction happens via:

- Application services interfaces, or
- Published domain/application events.

### 3.2 Entities and Value Objects

- **Entities**
  - Have a stable identity (`UserId`, `OrderId`).
  - Change over time.
- **Value Objects**
  - Identified by their values.
  - Immutable (`Money(currency, amount)`, `Email(address)`).

Use Value Objects to:

- Encapsulate validation and formatting.
- Keep invariants local (e.g., `Money` never negative, `Email` always valid).

---

### 3.3 Aggregates and Invariants

Define **aggregates** to enforce business rules consistently:

- An aggregate is a cluster of entities and value objects with a single **aggregate root**.
- All external modifications go through the root.

Example: `Order` aggregate

- Root: `Order`.
- Children: `OrderLine` items.
- Invariants enforced by `Order`:
  - Total must be sum of lines.
  - Cannot add lines to a shipped order.
  - Cannot pay for a cancelled order.

Aggregates:

- Limit the scope of transactions.
- Simplify consistency guarantees.

---

### 3.4 Domain Services

Use domain services when:

- Logic involves multiple aggregates.
- Logic does not belong to a single entity.

Example: `PricingService`

- Computes prices based on:
  - Current promotions.
  - Customer tier.
  - Product attributes.

Domain services should:

- Operate on domain types.
- Be stateless (usually).

---

### 3.5 Domain Events

Domain events capture things that happened in the business:

- `UserRegistered`.
- `OrderPlaced`.
- `PaymentFailed`.

Use them to:

- Trigger reactions in other parts of the system.
- Decouple modules inside the monolith.

Pattern inside a monolith:

1. Aggregate method is called (e.g., `Order.place()`).
2. Aggregate raises a domain event.
3. Application layer or a domain event handler reacts (e.g., sends an email, updates read model).

---

## 4. Persistence and Integration Patterns (Inside the Monolith)

### 4.1 Repository Pattern

Repositories abstract persistence for aggregates:

- Domain/Application define interfaces:

  - `OrderRepository` with operations like `save(order)`, `byId(orderId)`, `byCustomer(customerId)`.

- Infrastructure implements with:

  - ORM, SQL, NoSQL, or external API.

Benefits:

- Domain logic is independent from persistence technology.
- Easier testing (in-memory implementations, fakes).

---

### 4.2 Unit of Work

A Unit of Work:

- Tracks changes to aggregates during a use case.
- Commits them in a single transaction at the end.

In a monolith:

- Often tied to a database transaction.
- Typically scoped to a single application service call.

Guideline:

- "One **use case** = one **Unit of Work** = one **transaction**".

---

### 4.3 Data Mapping

Choose a mapping style:

- **Data Mapper** (recommended for rich domain)
  - Separate domain classes from persistence models.
  - Explicit mapping layer.
- **Active Record**
  - Simpler for CRUD-heavy modules.
  - Entities know how to persist themselves.

For enterprise domains with many rules, prefer **Data Mapper + Repositories**.

---

### 4.4 Integration with External Systems

Even in a monolith, you will integrate with:

- Payment gateways.
- Third-party APIs.
- Legacy systems.

Best practices:

- Use **gateway interfaces** in the application layer (`PaymentGateway`, `CRMClient`).
- Implement them in the infrastructure layer.
- Optionally use an **anti-corruption layer** to:
  - Translate external models into your domain model.
  - Hide protocol quirks and legacy semantics.

---

## 5. Cross-Cutting Concerns

### 5.1 Security

- Centralize authentication & authorization.
- Use middleware or filters in the presentation layer to:
  - Validate tokens / sessions.
  - Load user identity and roles.
- Express business authorization in the domain/application layer:
  - Permissions/roles checks aligned with business rules.

---

### 5.2 Configuration

- Store configuration in environment variables or a configuration service.
- Avoid hard-coding environment-specific values.
- Support multiple environments (dev, staging, production) with the same codebase.

Patterns:

- Configuration objects injected into services.
- Typed configuration wrappers for critical values.

---

### 5.3 Observability

- **Logging**
  - Structured logs (JSON) with correlation IDs.
  - Centralized log aggregation.
- **Metrics**
  - Technical (latency, throughput, error rates).
  - Business (orders per minute, failed logins, payment failures).
- **Tracing**
  - Trace a request through layers and modules.

Keep cross-cutting concerns in shared libraries and middleware, not in domain classes.

---

### 5.4 Resilience and Performance

- Timeouts for external calls.
- Retries with backoff where safe.
- Circuit breakers for unstable dependencies.
- Caching where appropriate:
  - HTTP/API response caching.
  - Application-level caching for expensive reads.
  - Database query caching.

---

## 6. Testing Strategy

Design the monolith to be **testable by design**.

### 6.1 Unit Tests

- Focus on domain layer and application services.
- No database or network calls.
- Use in-memory implementations for repositories and gateways.

### 6.2 Integration Tests

- Test repository implementations against a real database.
- Test HTTP clients against test instances or mocks.
- Validate mapping layers and configurations.

### 6.3 End-to-End Tests

- Cover critical flows only:
  - User registration and login.
  - Placing an order.
  - Payment and refund flows.

- Run less frequently than unit tests (e.g., nightly or on main branch).

---

## 9. Practical Checklist for a New Enterprise Monolith

1. Identify **bounded contexts** and modules.
2. For each module:
   - Define domain model (entities, value objects, aggregates).
   - Define key use cases and application services.
   - Define repository and gateway interfaces.
3. Implement **presentation layer** endpoints that translate requests into commands/queries.
4. Implement **domain logic** with rich models and domain events.
5. Implement **infrastructure** adapters (DB, external APIs) behind interfaces.
6. Introduce **cross-cutting** modules for:
   - Security
   - Configuration
   - Logging, metrics, tracing
7. Set up **testing pyramid** (unit, integration, e2e).
8. Add **CI pipeline** to run tests and checks on each change.
9. Evolve toward more explicit events and clearer boundaries as the domain grows.

The result is an enterprise-grade, modular monolith that is:

- Easy to reason about.
- Ready to scale horizontally.
- Prepared for future extraction of individual modules into services, if needed.

### Boy Scout Rule (Always)

**Leave code cleaner than you found it** - Small improvements during every edit:
- Rename unclear variables (`x` → `trade_r_multiple`)
- Extract magic numbers to constants (`0.75` → `GBDT_A_MIN_CONFIDENCE`)
- Add missing docstrings and type hints
- Remove unused imports

### Evolutionary DDD (Architecture)

**Start simple, refine incrementally**:
- Phase 1: Simple Django apps with services/selectors
- Phase 2: Introduce domain layer with entities/value objects
- Phase 3: Bounded contexts with repository pattern
