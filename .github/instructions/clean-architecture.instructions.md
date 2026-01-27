---
applyTo: "**/*"
---

# Clean Architecture Pattern

## Overview

- **Intent:** Organize software into concentric layers with dependencies pointing inward, keeping business logic independent of frameworks, UI, databases, and external agencies. The goal is to create systems that are testable, maintainable, and adaptable to change by enforcing separation of concerns through explicit dependency rules.

- **When to Use:** 
  - Building applications with complex business logic that must remain stable as external dependencies evolve
  - Projects requiring high testability and the ability to defer infrastructure decisions
  - Systems that need to support multiple interfaces (web, mobile, CLI, API) sharing the same business rules
  - Long-lived applications where maintainability and adaptability are critical
  - Teams wanting clear boundaries between business logic and technical implementation details
  - Applications that may need to swap out databases, frameworks, or external services without affecting core logic

## Core Principles

1. **Dependency Rule**: Source code dependencies must point only inward toward higher-level policies. Inner layers know nothing about outer layers.

2. **Entities Layer**: Contains enterprise-wide business rules and domain models. These are the most stable and least likely to change.

3. **Use Cases Layer**: Contains application-specific business rules. Orchestrates data flow between entities and defines application behavior.

4. **Interface Adapters Layer**: Converts data between the format most convenient for use cases/entities and the format most convenient for external agencies (web, database, etc.).

5. **Frameworks & Drivers Layer**: The outermost layer containing frameworks, tools, and glue code. This is where details live.

6. **Independence**: Business logic is independent of UI, database, frameworks, and external services. These are plugins to the business rules.

## Named Instruction Outline

### Phase 1: Domain Modeling (Entities Layer)

**Role**: Domain Expert + Developer

1. **Identify Core Entities**
   - Extract business objects that represent core concepts
   - Define entity properties and invariants
   - Implement business rules that apply across all use cases
   - Keep entities free from infrastructure concerns

2. **Define Domain Interfaces**
   - Create repository interfaces for data access
   - Define service interfaces for domain operations
   - Establish value objects for domain concepts
   - Document domain rules and constraints

**Checkpoint**: Entities should have no dependencies on outer layers and encapsulate pure business logic.

### Phase 2: Use Case Implementation

**Role**: Application Developer

1. **Create Use Case Classes**
   - Define one class per use case (e.g., CreateOrderUseCase, GetUserProfileUseCase)
   - Implement input/output ports (interfaces for data transfer)
   - Orchestrate entity interactions to fulfill business requirements
   - Handle application-specific validation and workflows

2. **Define Boundaries**
   - Create request/response models (DTOs) for use case inputs and outputs
   - Establish presenter interfaces for output formatting
   - Define gateway interfaces for external system access
   - Keep use cases framework-agnostic

**Checkpoint**: Use cases should depend only on entities and abstractions, not on implementation details.

### Phase 3: Interface Adapters Layer

**Role**: Integration Developer

1. **Implement Controllers**
   - Create controllers/handlers that receive external requests
   - Convert HTTP/CLI/message queue inputs to use case request models
   - Invoke appropriate use cases
   - Handle routing and input validation at the boundary

2. **Implement Presenters**
   - Transform use case outputs into formats for external consumers (JSON, HTML, XML)
   - Apply view-specific formatting logic
   - Keep presentation logic separate from business logic

3. **Implement Gateways/Repositories**
   - Create concrete implementations of repository interfaces
   - Handle data persistence and retrieval
   - Map between domain entities and database models
   - Implement external service clients

**Checkpoint**: Adapters should translate between external formats and internal use case models without containing business logic.

### Phase 4: Frameworks & Drivers Layer

**Role**: Infrastructure Developer

1. **Configure Framework**
   - Set up web framework (Express, Spring, ASP.NET, etc.)
   - Configure dependency injection container
   - Wire up adapters to use cases
   - Establish routing and middleware

2. **Configure Database**
   - Set up database connections and ORM
   - Implement database migrations
   - Configure connection pooling and optimization
   - Handle database-specific concerns

3. **Integrate External Services**
   - Configure third-party API clients
   - Set up message queues, caching, logging
   - Implement cross-cutting concerns (authentication, monitoring)
   - Handle environment-specific configuration

**Checkpoint**: Framework and infrastructure code should be isolated in this outer layer, easily replaceable without affecting business logic.

### Phase 5: Testing Strategy

**Role**: QA Engineer + Developer

1. **Entity Tests**
   - Unit test business rules in isolation
   - Test entity invariants and validation
   - No mocking required - pure logic testing

2. **Use Case Tests**
   - Test use case orchestration with mocked repositories/gateways
   - Verify business workflows and edge cases
   - Test with fake implementations of interfaces

3. **Integration Tests**
   - Test adapters with real external dependencies
   - Verify data mapping and transformations
   - Test database repositories with test databases

4. **End-to-End Tests**
   - Test complete flows through all layers
   - Verify system behavior from external perspective
   - Focus on critical user journeys

**Checkpoint**: High test coverage should be achievable because business logic is decoupled from infrastructure.

## Layer Structure & Dependencies

```
┌─────────────────────────────────────────┐
│   Frameworks & Drivers (Outermost)      │
│   - Web Framework, Database, UI, APIs   │
│   - External Services, Devices          │
└─────────────────┬───────────────────────┘
                  │ depends on
┌─────────────────▼───────────────────────┐
│      Interface Adapters                 │
│   - Controllers, Presenters             │
│   - Gateways, Repositories              │
└─────────────────┬───────────────────────┘
                  │ depends on
┌─────────────────▼───────────────────────┐
│      Use Cases (Application Logic)      │
│   - Use Case Interactors                │
│   - Input/Output Ports (Interfaces)     │
└─────────────────┬───────────────────────┘
                  │ depends on
┌─────────────────▼───────────────────────┐
│      Entities (Enterprise Logic)        │
│   - Business Objects, Domain Models     │
│   - Business Rules, Validations         │
└─────────────────────────────────────────┘
          (Innermost - Most Stable)
```

**Dependency Flow**: Outer → Inner (never Inner → Outer)

## Anti-Patterns to Avoid

### 1. **Dependency Rule Violation**
- **Problem**: Inner layers importing outer layer classes (e.g., entities importing ORM annotations)
- **Solution**: Use dependency inversion - define interfaces in inner layers, implement in outer layers

### 2. **Anemic Domain Model**
- **Problem**: Entities are just data containers with no behavior, all logic in use cases
- **Solution**: Push business rules into entities where they belong; use cases should orchestrate, not implement rules

### 3. **Fat Use Cases**
- **Problem**: Use cases contain business logic that should be in entities or infrastructure logic that should be in adapters
- **Solution**: Extract domain logic to entities, delegate infrastructure concerns to gateways/repositories

### 4. **Leaky Abstractions**
- **Problem**: Use case interfaces expose database models, HTTP request objects, or framework types
- **Solution**: Create clean DTOs and domain models at boundaries; adapters handle all conversions

### 5. **Over-Engineering Small Applications**
- **Problem**: Applying full Clean Architecture to simple CRUD apps with minimal business logic
- **Solution**: Use simpler patterns for simple problems; Clean Architecture shines with complex domains

### 6. **Bypassing Use Cases**
- **Problem**: Controllers directly manipulating entities or calling repositories
- **Solution**: All business operations should flow through use cases to maintain consistency

## Example: E-Commerce Order Processing

### Entities Layer
```python
# entities/order.py
from enum import Enum
from typing import List

class OrderStatus(Enum):
    DRAFT = "draft"
    CONFIRMED = "confirmed"

class OrderItem:
    def __init__(self, product_id: str, quantity: int, price: float):
        self.product_id = product_id
        self.quantity = quantity
        self.price = price

class Order:
    def __init__(self, id: str, items: List[OrderItem], status: OrderStatus):
        self._id = id
        self._items = items
        self._status = status

    @property
    def id(self) -> str:
        return self._id

    @property
    def status(self) -> OrderStatus:
        return self._status

    def add_item(self, item: OrderItem) -> None:
        if self._status != OrderStatus.DRAFT:
            raise ValueError("Cannot modify confirmed order")
        self._items.append(item)

    def calculate_total(self) -> float:
        return sum(item.price * item.quantity for item in self._items)

    def confirm(self) -> None:
        if len(self._items) == 0:
            raise ValueError("Cannot confirm empty order")
        self._status = OrderStatus.CONFIRMED
```

### Use Cases Layer
```python
# usecases/create_order.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
from uuid import uuid4

from entities.order import Order, OrderItem, OrderStatus

@dataclass
class OrderItemRequest:
    product_id: str
    quantity: int
    price: float

@dataclass
class CreateOrderRequest:
    items: List[OrderItemRequest]

@dataclass
class CreateOrderResponse:
    order_id: str
    total: float
    status: OrderStatus

class OrderRepository(ABC):
    @abstractmethod
    async def save(self, order: Order) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, order_id: str) -> Optional[Order]:
        pass

class CreateOrderUseCase:
    def __init__(self, order_repo: OrderRepository):
        self._order_repo = order_repo

    async def execute(self, request: CreateOrderRequest) -> CreateOrderResponse:
        order = Order(
            id=str(uuid4()),
            items=[OrderItem(i.product_id, i.quantity, i.price) for i in request.items],
            status=OrderStatus.DRAFT
        )

        order.confirm()
        await self._order_repo.save(order)

        return CreateOrderResponse(
            order_id=order.id,
            total=order.calculate_total(),
            status=order.status
        )
```

### Interface Adapters Layer
```python
# adapters/controllers/order_controller.py
from typing import Dict, Any

from usecases.create_order import CreateOrderUseCase, CreateOrderRequest, OrderItemRequest

class OrderController:
    def __init__(self, create_order_use_case: CreateOrderUseCase):
        self._create_order_use_case = create_order_use_case

    async def handle_create_order(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        # Convert from HTTP to use case format
        request = CreateOrderRequest(
            items=[OrderItemRequest(**item) for item in request_data["items"]]
        )

        response = await self._create_order_use_case.execute(request)

        return {
            "status": 201,
            "body": {
                "order_id": response.order_id,
                "total": response.total
            }
        }

# adapters/repositories/postgres_order_repository.py
from typing import Optional
import asyncpg

from entities.order import Order
from usecases.create_order import OrderRepository

class PostgresOrderRepository(OrderRepository):
    def __init__(self, db_pool: asyncpg.Pool):
        self._db_pool = db_pool

    async def save(self, order: Order) -> None:
        # Convert domain Order to database model and save
        async with self._db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO orders (id, status, total) VALUES ($1, $2, $3)",
                order.id, order.status.value, order.calculate_total()
            )

    async def find_by_id(self, order_id: str) -> Optional[Order]:
        # Mapping logic here
        pass
```

### Frameworks & Drivers Layer
```python
# infrastructure/fastapi/server.py
from fastapi import FastAPI, Request
import asyncpg

from adapters.controllers.order_controller import OrderController
from adapters.repositories.postgres_order_repository import PostgresOrderRepository
from usecases.create_order import CreateOrderUseCase

app = FastAPI()

# Initialize dependencies
db_pool = asyncpg.create_pool(
    host="localhost",
    database="orders_db",
    user="user",
    password="password"
)

order_repo = PostgresOrderRepository(db_pool)
create_order_use_case = CreateOrderUseCase(order_repo)
order_controller = OrderController(create_order_use_case)

@app.post("/orders")
async def create_order(request: Request):
    request_data = await request.json()
    response = await order_controller.handle_create_order(request_data)
    return response["body"]
```

## Decision Aids

### When to Choose Clean Architecture

**Choose Clean Architecture when:**
- ✅ Complex business logic that must remain stable
- ✅ Multiple delivery mechanisms (web, mobile, API, CLI)
- ✅ Need to defer infrastructure decisions
- ✅ Long-term project with evolving requirements
- ✅ High testability requirements
- ✅ Team size supports maintaining multiple layers

**Consider alternatives when:**
- ❌ Simple CRUD application with minimal business logic
- ❌ Proof of concept or short-lived project
- ❌ Small team that might struggle with architectural overhead
- ❌ Tight deadlines where speed trumps long-term maintainability
- ❌ Domain logic is inherently simple and unlikely to change

### Where Does Logic Belong?

| Type of Logic | Layer | Example |
|--------------|-------|---------|
| Business rules that apply universally | Entities | Order cannot be modified after confirmation |
| Application-specific workflows | Use Cases | Process order, send confirmation email, update inventory |
| Data format conversion | Interface Adapters | Convert JSON to domain objects, map entities to database models |
| Framework configuration | Frameworks & Drivers | Express route setup, database connection pooling |
| Input validation at boundary | Interface Adapters | Validate HTTP request format, check required fields |
| Domain validation | Entities | Ensure order total is positive, email format is valid |

## Implementation Checklist

### Initial Setup
- [ ] Define folder structure reflecting layers (entities, usecases, adapters, infrastructure)
- [ ] Establish module boundaries and import rules
- [ ] Configure dependency injection framework
- [ ] Set up testing infrastructure for each layer

### For Each Feature
- [ ] **Entities**: Define domain models with business rules
- [ ] **Entities**: Create repository/gateway interfaces
- [ ] **Use Cases**: Implement use case class with input/output DTOs
- [ ] **Use Cases**: Write unit tests with mocked dependencies
- [ ] **Adapters**: Implement controllers to handle external requests
- [ ] **Adapters**: Implement repositories/gateways connecting to external systems
- [ ] **Adapters**: Create presenters to format responses
- [ ] **Infrastructure**: Wire dependencies in DI container
- [ ] **Infrastructure**: Configure routes and middleware
- [ ] **Testing**: Write integration tests for adapters
- [ ] **Testing**: Write end-to-end tests for critical paths

### Ongoing Maintenance
- [ ] Review dependencies regularly - ensure they point inward
- [ ] Refactor business logic from use cases to entities when patterns emerge
- [ ] Keep DTOs at boundaries separate from domain models
- [ ] Monitor for framework leakage into inner layers
- [ ] Update tests when changing layer contracts

## Common Challenges & Solutions

### Challenge 1: Too Many Layers of Indirection
**Problem**: Every simple operation requires touching 4+ files  
**Solution**: Start with fewer layers for simple features; add abstraction when you need it, not before

### Challenge 2: Data Mapping Overhead
**Problem**: Converting between entity, DTO, database model, and API response feels repetitive  
**Solution**: Use mapping libraries (AutoMapper, MapStruct) or accept some duplication as the cost of decoupling

### Challenge 3: Transaction Management Across Use Cases
**Problem**: Maintaining database transactions when use cases call other use cases  
**Solution**: Implement Unit of Work pattern or use transaction decorators at the adapter layer

### Challenge 4: Circular Dependencies Between Use Cases
**Problem**: Use case A needs use case B, and B needs A  
**Solution**: Extract shared logic to a separate use case or entity method; consider domain event pattern

### Challenge 5: Performance Concerns
**Problem**: Multiple layers add overhead  
**Solution**: Profile first; optimize hot paths by allowing some controlled coupling where justified

### Challenge 6: Onboarding Difficulty
**Problem**: New developers struggle with architecture complexity  
**Solution**: Provide clear documentation, coding examples, and architectural decision records (ADRs)

## Related Patterns

- **Hexagonal Architecture (Ports & Adapters)**: Similar philosophy; Clean Architecture is more prescriptive about layers
- **Onion Architecture**: Nearly identical; Clean Architecture adds explicit use case layer
- **Domain-Driven Design**: Provides tactical patterns for the domain layer
- **CQRS**: Can be combined with Clean Architecture to separate read and write models
- **Dependency Injection**: Essential technique for implementing dependency inversion

## Further Reading

- "Clean Architecture" by Robert C. Martin (Uncle Bob)
- "Implementing Domain-Driven Design" by Vaughn Vernon
- "Architecture Patterns with Python" by Harry Percival & Bob Gregory
- Blog series: Clean Architecture on the Martin Fowler website
