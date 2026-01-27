---
applyTo: "**/*"
---

# Domain-Driven Design Pattern

## Overview

- **Intent:** Align software design with business domain complexity by creating a shared language between developers and domain experts, organizing code around business concepts rather than technical concerns.

- **When to Use:**
  - Complex business logic that requires deep domain understanding
  - Projects where domain experts actively collaborate with developers
  - Systems that model real-world business processes and rules
  - Applications where business logic changes frequently
  - Medium to large projects where tactical patterns benefit long-term maintainability
  - When different parts of the system have distinct domain contexts (bounded contexts)

## Core Principles

1. **Ubiquitous Language**: Shared vocabulary between developers and domain experts used in code, conversations, and documentation
2. **Bounded Contexts**: Explicit boundaries where a particular model is defined and applicable
3. **Domain Model**: Rich object model that encapsulates business logic and behavior
4. **Strategic Design**: High-level organization of contexts, their relationships, and integration patterns
5. **Tactical Design**: Building blocks (entities, value objects, aggregates, services) for implementing the model

## DDD Building Blocks

### Entities
Objects with unique identity that persists over time, even when attributes change.

```python
from dataclasses import dataclass
from uuid import UUID, uuid4
from typing import Optional

@dataclass
class Customer:
    """Entity with identity - two customers with same name are different people."""
    id: UUID
    name: str
    email: str
    credit_limit: float
    
    def __init__(self, name: str, email: str, credit_limit: float = 1000.0):
        self.id = uuid4()
        self.name = name
        self.email = email
        self.credit_limit = credit_limit
    
    def increase_credit_limit(self, amount: float) -> None:
        """Business logic encapsulated in the entity."""
        if amount <= 0:
            raise ValueError("Credit increase must be positive")
        self.credit_limit += amount
    
    def __eq__(self, other) -> bool:
        """Equality based on identity, not attributes."""
        if not isinstance(other, Customer):
            return False
        return self.id == other.id
```

### Value Objects
Immutable objects without identity, defined entirely by their attributes.

```python
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Money:
    """Value object - two Money instances with same amount/currency are identical."""
    amount: float
    currency: str
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be 3-letter code")
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)
    
    def multiply(self, factor: float) -> 'Money':
        return Money(self.amount * factor, self.currency)

@dataclass(frozen=True)
class Address:
    street: str
    city: str
    postal_code: str
    country: str
    
    def __str__(self) -> str:
        return f"{self.street}, {self.city} {self.postal_code}, {self.country}"
```

### Aggregates
Cluster of entities and value objects with a root entity that controls access and maintains invariants.

```python
from dataclasses import dataclass, field
from typing import List
from datetime import datetime
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

@dataclass
class OrderLine:
    """Entity within the Order aggregate."""
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Money
    
    def total(self) -> Money:
        return self.unit_price.multiply(self.quantity)

@dataclass
class Order:
    """Aggregate root - controls all access to OrderLines."""
    id: UUID
    customer_id: UUID
    status: OrderStatus
    lines: List[OrderLine] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    
    def __init__(self, customer_id: UUID):
        self.id = uuid4()
        self.customer_id = customer_id
        self.status = OrderStatus.PENDING
        self.lines = []
        self.created_at = datetime.now()
    
    def add_line(self, product_id: UUID, product_name: str, 
                 quantity: int, unit_price: Money) -> None:
        """Aggregate root enforces business rules."""
        if self.status != OrderStatus.PENDING:
            raise ValueError("Cannot modify confirmed order")
        
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        # Check if product already in order
        for line in self.lines:
            if line.product_id == product_id:
                raise ValueError("Product already in order")
        
        self.lines.append(OrderLine(product_id, product_name, quantity, unit_price))
    
    def confirm(self) -> None:
        """State transition with business rules."""
        if not self.lines:
            raise ValueError("Cannot confirm empty order")
        if self.status != OrderStatus.PENDING:
            raise ValueError("Order already confirmed")
        self.status = OrderStatus.CONFIRMED
    
    def total_amount(self) -> Money:
        if not self.lines:
            return Money(0, "USD")
        return sum((line.total() for line in self.lines[1:]), 
                   start=self.lines[0].total())

### Domain Services
Stateless operations that don't naturally belong to entities or value objects.

```python
from abc import ABC, abstractmethod

class PricingService:
    """Domain service for complex pricing logic spanning multiple aggregates."""
    
    def __init__(self, customer_repo: 'CustomerRepository'):
        self.customer_repo = customer_repo
    
    def calculate_order_total(self, order: Order, customer_id: UUID) -> Money:
        """Business logic that requires customer and order information."""
        base_total = order.total_amount()
        customer = self.customer_repo.find_by_id(customer_id)
        
        if customer is None:
            return base_total
        
        # Apply customer-specific discount
        discount_rate = self._get_customer_discount_rate(customer)
        discounted_amount = base_total.amount * (1 - discount_rate)
        
        return Money(discounted_amount, base_total.currency)
    
    def _get_customer_discount_rate(self, customer: Customer) -> float:
        """Domain logic for determining discount tier."""
        if customer.credit_limit > 10000:
            return 0.15  # Premium customers get 15% off
        elif customer.credit_limit > 5000:
            return 0.10  # Standard customers get 10% off
        return 0.05  # Basic customers get 5% off

class TransferService:
    """Domain service for operations spanning multiple aggregates."""
    
    def transfer_money(self, from_account: 'Account', to_account: 'Account', 
                      amount: Money) -> None:
        """Coordinates transfer between two account aggregates."""
        if from_account.currency != amount.currency:
            raise ValueError("Currency mismatch")
        
        # Both operations must succeed or fail together (transaction boundary)
        from_account.withdraw(amount)
        to_account.deposit(amount)
```

### Repositories
Abstraction for aggregate persistence and retrieval, hiding storage details.

```python
from abc import ABC, abstractmethod
from typing import List, Optional

class CustomerRepository(ABC):
    """Repository interface - part of domain layer."""
    
    @abstractmethod
    def find_by_id(self, customer_id: UUID) -> Optional[Customer]:
        """Retrieve aggregate by identity."""
        pass
    
    @abstractmethod
    def find_by_email(self, email: str) -> Optional[Customer]:
        """Domain-specific query method."""
        pass
    
    @abstractmethod
    def save(self, customer: Customer) -> None:
        """Persist aggregate."""
        pass
    
    @abstractmethod
    def delete(self, customer: Customer) -> None:
        """Remove aggregate."""
        pass

class OrderRepository(ABC):
    """Repository works with aggregate roots only."""
    
    @abstractmethod
    def find_by_id(self, order_id: UUID) -> Optional[Order]:
        pass
    
    @abstractmethod
    def find_by_customer(self, customer_id: UUID) -> List[Order]:
        """Query orders for a customer."""
        pass
    
    @abstractmethod
    def save(self, order: Order) -> None:
        """Saves entire aggregate (order + order lines)."""
        pass

# Infrastructure layer implementation (example)
class InMemoryCustomerRepository(CustomerRepository):
    """Concrete implementation - belongs in infrastructure layer."""
    
    def __init__(self):
        self._customers: dict[UUID, Customer] = {}
    
    def find_by_id(self, customer_id: UUID) -> Optional[Customer]:
        return self._customers.get(customer_id)
    
    def find_by_email(self, email: str) -> Optional[Customer]:
        for customer in self._customers.values():
            if customer.email == email:
                return customer
        return None
    
    def save(self, customer: Customer) -> None:
        self._customers[customer.id] = customer
    
    def delete(self, customer: Customer) -> None:
        self._customers.pop(customer.id, None)

### Domain Events
Represent something significant that happened in the domain.

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List

@dataclass(frozen=True)
class DomainEvent:
    """Base class for domain events."""
    occurred_at: datetime = field(default_factory=datetime.now)

@dataclass(frozen=True)
class OrderConfirmed(DomainEvent):
    """Event indicating an order was confirmed."""
    order_id: UUID
    customer_id: UUID
    total_amount: Money

@dataclass(frozen=True)
class CustomerCreditLimitIncreased(DomainEvent):
    """Event indicating customer credit was increased."""
    customer_id: UUID
    old_limit: float
    new_limit: float

class EventPublisher:
    """Simple event publisher for domain events."""
    
    def __init__(self):
        self._subscribers: List[callable] = []
    
    def subscribe(self, handler: callable) -> None:
        self._subscribers.append(handler)
    
    def publish(self, event: DomainEvent) -> None:
        for handler in self._subscribers:
            handler(event)

# Modified Order aggregate to publish events
class OrderWithEvents(Order):
    """Order that publishes domain events."""
    
    def __init__(self, customer_id: UUID, event_publisher: EventPublisher):
        super().__init__(customer_id)
        self._event_publisher = event_publisher
    
    def confirm(self) -> None:
        """Publish event when order is confirmed."""
        super().confirm()
        
        event = OrderConfirmed(
            order_id=self.id,
            customer_id=self.customer_id,
            total_amount=self.total_amount()
        )
        self._event_publisher.publish(event)
```

## Named Instruction Outline

### Phase 1: Establish Ubiquitous Language and Identify Bounded Contexts

**Objective:** Create shared vocabulary and define context boundaries.

**Steps:**

1. **Conduct Domain Workshops**
   - Meet with domain experts to understand business processes
   - Document key business terms and their meanings
   - Identify core concepts, entities, and relationships
   - Create a glossary of ubiquitous language terms

2. **Identify Bounded Contexts**
   - Look for areas where terms have different meanings
   - Group related concepts that share the same model
   - Define explicit boundaries between contexts
   - Map context relationships (upstream/downstream, shared kernel, etc.)

```python
# Example: E-commerce system with multiple bounded contexts

# Sales Context - focuses on order processing
class SalesOrder:
    """Order in Sales context - emphasizes pricing and customer."""
    order_id: UUID
    customer_id: UUID
    items: List['OrderItem']
    total_price: Money
    discount_applied: float

# Shipping Context - focuses on delivery
class ShipmentOrder:
    """Order in Shipping context - emphasizes address and weight."""
    order_id: UUID
    delivery_address: Address
    items: List['ShippableItem']
    total_weight: float
    shipping_method: str

# Inventory Context - focuses on stock management
class InventoryOrder:
    """Order in Inventory context - emphasizes reservation."""
    order_id: UUID
    items: List['InventoryReservation']
    warehouse_id: UUID
    reservation_status: str
```

3. **Document Context Map**
   - Visualize relationships between bounded contexts
   - Identify integration patterns (anti-corruption layer, published language, etc.)
   - Define translation layers between contexts

### Phase 2: Model the Core Domain with Tactical Patterns

**Objective:** Implement rich domain model using DDD building blocks.

**Steps:**

1. **Identify Entities and Value Objects**
   - **Entities**: Objects with identity (Customer, Order, Product)
   - **Value Objects**: Immutable descriptive objects (Money, Address, DateRange)
   - Rule: If two objects with identical attributes should be considered different, it's an entity
   - Rule: If two objects with identical attributes are interchangeable, it's a value object

2. **Define Aggregates and Roots**
   - Group related entities/value objects into aggregates
   - Choose an aggregate root (the main entity)
   - Enforce invariants within aggregate boundaries
   - Only reference aggregates by their root

```python
# Bad: External code manipulating aggregate internals
order = order_repo.find_by_id(order_id)
order_line = order.lines[0]
order_line.quantity = 10  # Bypassing business rules!

# Good: All access through aggregate root
order = order_repo.find_by_id(order_id)
order.update_line_quantity(order_line_id, 10)  # Enforces rules
```

3. **Implement Domain Services**
   - Extract operations that don't belong to a single entity
   - Keep services stateless
   - Use services for cross-aggregate operations

4. **Define Repository Interfaces**
   - Create repository interfaces in domain layer
   - Design collection-like interfaces for aggregates
   - Include domain-specific query methods

### Phase 3: Implement Layered Architecture

**Objective:** Organize code into clear layers with proper dependencies.

**Steps:**

1. **Structure Project Layers**

```
project/
├── domain/                    # Core business logic
│   ├── model/
│   │   ├── customer.py       # Entities
│   │   ├── order.py          # Aggregates
│   │   ├── money.py          # Value objects
│   │   └── events.py         # Domain events
│   ├── services/
│   │   └── pricing_service.py
│   └── repositories/
│       └── order_repository.py  # Interfaces only
│
├── application/               # Use cases and orchestration
│   ├── commands/
│   │   ├── create_order_command.py
│   │   └── confirm_order_command.py
│   └── queries/
│       └── order_queries.py
│
├── infrastructure/            # Technical implementations
│   ├── persistence/
│   │   ├── sql_order_repository.py
│   │   └── orm_mappings.py
│   ├── messaging/
│   │   └── event_bus.py
│   └── external/
│       └── payment_gateway.py
│
└── presentation/              # UI/API layer
    ├── api/
    │   └── order_controller.py
    └── dto/
        └── order_dto.py
```

2. **Enforce Dependency Rules**
   - Domain layer has no dependencies on other layers
   - Application layer depends only on domain
   - Infrastructure implements domain interfaces
   - Presentation layer uses application services

3. **Application Services as Use Case Coordinators**

```python
class CreateOrderApplicationService:
    """Application service coordinates use case without business logic."""
    
    def __init__(self, 
                 order_repo: OrderRepository,
                 customer_repo: CustomerRepository,
                 event_publisher: EventPublisher):
        self.order_repo = order_repo
        self.customer_repo = customer_repo
        self.event_publisher = event_publisher
    
    def create_order(self, customer_id: UUID, 
                    items: List[dict]) -> UUID:
        """
        Use case: Create new order
        - Validates customer exists
        - Creates order aggregate
        - Persists through repository
        - Returns order ID
        """
        # Verify customer exists
        customer = self.customer_repo.find_by_id(customer_id)
        if customer is None:
            raise ValueError("Customer not found")
        
        # Create domain object (business logic in aggregate)
        order = Order(customer_id)
        
        for item in items:
            price = Money(item['price'], item['currency'])
            order.add_line(
                product_id=item['product_id'],
                product_name=item['name'],
                quantity=item['quantity'],
                unit_price=price
            )
        
        # Persist
        self.order_repo.save(order)
        
        return order.id
```

### Phase 4: Handle Cross-Cutting Concerns

**Objective:** Implement transactions, events, and integration patterns.

**Steps:**

1. **Transaction Boundaries**
   - Transactions should encompass single aggregate modifications
   - Use domain events for eventual consistency across aggregates
   - Avoid distributed transactions when possible

```python
class OrderService:
    """Service demonstrating transaction boundary."""
    
    def confirm_order_and_reserve_inventory(self, order_id: UUID) -> None:
        # Anti-pattern: Modifying multiple aggregates in one transaction
        # Instead: Confirm order, publish event, inventory context reacts
        
        order = self.order_repo.find_by_id(order_id)
        order.confirm()  # Publishes OrderConfirmed event
        self.order_repo.save(order)
        
        # Inventory context subscribes to OrderConfirmed event
        # and handles reservation in its own transaction
```

2. **Implement Domain Events**
   - Aggregates collect events during operations
   - Events published after successful persistence
   - Event handlers in application or infrastructure layer

3. **Anti-Corruption Layer for External Systems**

```python
class PaymentGatewayAdapter:
    """Anti-corruption layer for external payment service."""
    
    def __init__(self, external_gateway: 'ThirdPartyPaymentAPI'):
        self._gateway = external_gateway
    
    def process_payment(self, order: Order, payment_method: str) -> bool:
        """Translate domain model to external API format."""
        # Domain model uses Money value object
        amount = order.total_amount()
        
        # External API uses different structure
        payment_request = {
            'amount_cents': int(amount.amount * 100),
            'currency_code': amount.currency,
            'order_reference': str(order.id),
            'payment_type': self._translate_payment_method(payment_method)
        }
        
        response = self._gateway.charge(payment_request)
        
        # Translate response back to domain concepts
        return response['status'] == 'success'
    
    def _translate_payment_method(self, domain_method: str) -> str:
        """Protect domain from external API changes."""
        mapping = {
            'credit_card': 'CC',
            'debit_card': 'DC',
            'paypal': 'PP'
        }
        return mapping.get(domain_method, 'CC')

## Anti-Patterns

### 1. Anemic Domain Model
**Problem:** Entities with only getters/setters, all business logic in services.

```python
# Anti-pattern: Anemic model
class Order:
    def __init__(self):
        self.id = None
        self.status = None
        self.items = []
    
    def get_status(self): return self.status
    def set_status(self, status): self.status = status
    def get_items(self): return self.items
    def set_items(self, items): self.items = items

class OrderService:
    def confirm_order(self, order: Order):
        if not order.get_items():
            raise ValueError("Cannot confirm empty order")
        if order.get_status() != "PENDING":
            raise ValueError("Order already confirmed")
        order.set_status("CONFIRMED")

# Correct: Rich domain model
class Order:
    def __init__(self, customer_id: UUID):
        self.id = uuid4()
        self.customer_id = customer_id
        self.status = OrderStatus.PENDING
        self._items = []
    
    def confirm(self) -> None:
        """Business logic belongs in the entity."""
        if not self._items:
            raise ValueError("Cannot confirm empty order")
        if self.status != OrderStatus.PENDING:
            raise ValueError("Order already confirmed")
        self.status = OrderStatus.CONFIRMED
```

### 2. Large Aggregates
**Problem:** Aggregates that are too big, causing performance and concurrency issues.

```python
# Anti-pattern: Everything in one aggregate
class Customer:
    id: UUID
    orders: List[Order]  # All orders loaded with customer!
    invoices: List[Invoice]
    support_tickets: List[Ticket]
    preferences: List[Preference]
    # Performance nightmare when loading customer

# Correct: Separate aggregates, reference by ID
class Customer:
    id: UUID
    name: str
    email: str
    credit_limit: float
    # Orders are a separate aggregate, not loaded with customer

class Order:
    id: UUID
    customer_id: UUID  # Reference by ID only
    # Load orders separately when needed
```

### 3. Ignoring Bounded Context Boundaries
**Problem:** Trying to create one unified model for entire system.

```python
# Anti-pattern: Shared "Order" everywhere
class Order:  # Used by sales, shipping, billing, inventory...
    # Becomes bloated with all concerns
    price: float
    shipping_weight: float
    tax_calculation: complex
    warehouse_location: str
    # Tightly couples all contexts

# Correct: Context-specific models
# Sales context
class SalesOrder:
    order_id: UUID
    pricing: Money
    discount: float

# Shipping context  
class Shipment:
    order_id: UUID  # Reference to sales order
    weight: float
    destination: Address
```

### 4. Repository That Returns DTOs or Database Models
**Problem:** Repository returns non-domain objects.

```python
# Anti-pattern
class OrderRepository:
    def find_by_id(self, order_id: UUID) -> dict:
        # Returns database row as dictionary
        return self.db.query("SELECT * FROM orders WHERE id = ?", order_id)

# Correct: Repository returns domain objects
class OrderRepository:
    def find_by_id(self, order_id: UUID) -> Optional[Order]:
        # Returns fully reconstructed aggregate
        row = self.db.query("SELECT * FROM orders WHERE id = ?", order_id)
        if not row:
            return None
        return self._to_domain(row)
```

### 5. Domain Logic in Application Services
**Problem:** Business rules leak into application layer.

```python
# Anti-pattern
class OrderApplicationService:
    def confirm_order(self, order_id: UUID) -> None:
        order = self.order_repo.find_by_id(order_id)
        
        # Business logic in application service!
        if not order.items:
            raise ValueError("Empty order")
        if order.total() > order.customer.credit_limit:
            raise ValueError("Exceeds credit limit")
        
        order.status = "CONFIRMED"
        self.order_repo.save(order)

# Correct: Business logic in domain
class OrderApplicationService:
    def confirm_order(self, order_id: UUID) -> None:
        order = self.order_repo.find_by_id(order_id)
        order.confirm()  # All validation inside
        self.order_repo.save(order)
```

## Decision Aids

### When to Use DDD

✅ **Use DDD When:**
- Domain complexity is high (complex business rules, workflows)
- You have access to domain experts who can collaborate
- Project is medium to large scale (multiple teams, long-term)
- Business logic changes frequently
- Multiple bounded contexts with different models
- Core domain provides competitive advantage

❌ **Don't Use DDD When:**
- Simple CRUD application with minimal business logic
- Data-centric system (reporting, analytics)
- No access to domain experts
- Small project with tight deadlines
- Technical complexity exceeds domain complexity
- Team lacks DDD experience and no time to learn

### Choosing Between Tactical Patterns

**Entity vs Value Object:**
- Use Entity if identity matters over time
- Use Value Object if attributes define the concept completely
- Example: `Customer` is Entity, `Address` is Value Object

**Aggregate vs Separate Entities:**
- Group into aggregate if they must be consistent together
- Keep aggregates small for better performance
- Example: `Order` + `OrderLines` = one aggregate

**Domain Service vs Entity Method:**
- Use Entity method if operation naturally belongs to that entity
- Use Domain Service if operation involves multiple aggregates
- Example: `Order.confirm()` vs `PricingService.calculate_discount(order, customer)`

**Repository vs DAO:**
- Use Repository for aggregates (collection-like interface)
- Repository hides storage details completely
- Repository in domain layer, implementation in infrastructure

## Implementation Checklist

### Domain Layer Setup
- [ ] Ubiquitous language documented and shared with team
- [ ] Bounded contexts identified with clear boundaries
- [ ] Context map showing relationships between contexts
- [ ] Entities defined with clear identity and lifecycle
- [ ] Value objects are immutable and validate invariants
- [ ] Aggregates have well-defined roots
- [ ] Aggregate invariants are enforced
- [ ] Domain services contain only cross-aggregate logic
- [ ] Repository interfaces defined (without implementations)
- [ ] Domain events defined for significant occurrences
- [ ] No dependencies on infrastructure or application layers

### Application Layer Setup
- [ ] Application services coordinate use cases
- [ ] Application services are thin (no business logic)
- [ ] Transaction boundaries defined around aggregates
- [ ] Commands and queries separated (if using CQRS)
- [ ] DTOs defined for external communication
- [ ] Input validation before calling domain layer
- [ ] Event handlers for cross-aggregate coordination

### Infrastructure Layer Setup
- [ ] Repository implementations created
- [ ] ORM mappings configured (if using ORM)
- [ ] Anti-corruption layers for external systems
- [ ] Event publishing mechanism implemented
- [ ] Database migrations for aggregate storage
- [ ] Integration tests for repositories

### Strategic Design
- [ ] Core domain identified (where competitive advantage lies)
- [ ] Supporting subdomains identified
- [ ] Generic subdomains identified (candidates for off-the-shelf)
- [ ] Context integration patterns chosen
- [ ] Shared kernel or separate models decision made
- [ ] Published language for integration defined (if needed)

### Team Practices
- [ ] Regular sessions with domain experts scheduled
- [ ] Ubiquitous language used in all communication
- [ ] Code reviews check for domain logic placement
- [ ] Architecture decision records maintained
- [ ] New team members onboarded with DDD concepts
- [ ] Refactoring sessions when model improves

### Code Quality Checks
- [ ] No anemic domain models (entities have behavior)
- [ ] No business logic in application services
- [ ] Aggregates are appropriately sized
- [ ] Repositories return domain objects (not DTOs/data rows)
- [ ] Domain layer has no external dependencies
- [ ] Value objects properly immutable
- [ ] Domain events named in past tense (OrderConfirmed, not ConfirmOrder)
- [ ] Aggregate roots protect internal consistency

## Example: Complete Order Bounded Context

```python
# domain/model/order.py
from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
from enum import Enum

class OrderStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"

@dataclass(frozen=True)
class Money:
    amount: float
    currency: str
    
    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError("Currency mismatch")
        return Money(self.amount + other.amount, self.currency)
    
    def multiply(self, factor: float) -> 'Money':
        return Money(self.amount * factor, self.currency)

@dataclass
class OrderLine:
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Money
    
    def total(self) -> Money:
        return self.unit_price.multiply(self.quantity)

@dataclass
class Order:
    """Aggregate root for order processing."""
    id: UUID
    customer_id: UUID
    status: OrderStatus
    lines: List[OrderLine] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    _events: List['DomainEvent'] = field(default_factory=list, init=False)
    
    def __init__(self, customer_id: UUID):
        self.id = uuid4()
        self.customer_id = customer_id
        self.status = OrderStatus.DRAFT
        self.lines = []
        self.created_at = datetime.now()
        self._events = []
    
    def add_line(self, product_id: UUID, product_name: str, 
                 quantity: int, unit_price: Money) -> None:
        """Add item to order with business rule validation."""
        if self.status not in [OrderStatus.DRAFT, OrderStatus.PENDING]:
            raise ValueError(f"Cannot modify order in {self.status.value} status")
        
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        for line in self.lines:
            if line.product_id == product_id:
                raise ValueError("Product already in order")
        
        self.lines.append(OrderLine(product_id, product_name, quantity, unit_price))
    
    def confirm(self) -> None:
        """Confirm order for processing."""
        if not self.lines:
            raise ValueError("Cannot confirm empty order")
        
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot confirm order in {self.status.value} status")
        
        self.status = OrderStatus.CONFIRMED
        self._events.append(OrderConfirmed(self.id, self.customer_id, self.total_amount()))
    
    def cancel(self, reason: str) -> None:
        """Cancel order with reason."""
        if self.status in [OrderStatus.SHIPPED, OrderStatus.DELIVERED]:
            raise ValueError(f"Cannot cancel {self.status.value} order")
        
        old_status = self.status
        self.status = OrderStatus.CANCELLED
        self._events.append(OrderCancelled(self.id, old_status, reason))
    
    def total_amount(self) -> Money:
        """Calculate total order amount."""
        if not self.lines:
            return Money(0, "USD")
        return sum((line.total() for line in self.lines[1:]), start=self.lines[0].total())
    
    def collect_events(self) -> List['DomainEvent']:
        """Retrieve and clear collected events."""
        events = self._events.copy()
        self._events.clear()
        return events

# domain/events.py
@dataclass(frozen=True)
class DomainEvent:
    occurred_at: datetime = field(default_factory=datetime.now)

@dataclass(frozen=True)
class OrderConfirmed(DomainEvent):
    order_id: UUID
    customer_id: UUID
    total_amount: Money

@dataclass(frozen=True)
class OrderCancelled(DomainEvent):
    order_id: UUID
    previous_status: OrderStatus
    reason: str

# domain/repositories/order_repository.py
from abc import ABC, abstractmethod

class OrderRepository(ABC):
    """Repository interface in domain layer."""
    
    @abstractmethod
    def find_by_id(self, order_id: UUID) -> Optional[Order]:
        pass
    
    @abstractmethod
    def find_by_customer(self, customer_id: UUID) -> List[Order]:
        pass
    
    @abstractmethod
    def save(self, order: Order) -> None:
        pass

# application/commands/order_commands.py
class CreateOrderCommand:
    """Command for creating new order."""
    
    def __init__(self, order_repo: OrderRepository, event_publisher: 'EventPublisher'):
        self.order_repo = order_repo
        self.event_publisher = event_publisher
    
    def execute(self, customer_id: UUID, items: List[dict]) -> UUID:
        """Execute create order use case."""
        order = Order(customer_id)
        
        for item in items:
            order.add_line(
                product_id=item['product_id'],
                product_name=item['name'],
                quantity=item['quantity'],
                unit_price=Money(item['price'], item['currency'])
            )
        
        order.status = OrderStatus.PENDING
        self.order_repo.save(order)
        
        # Publish any domain events
        for event in order.collect_events():
            self.event_publisher.publish(event)
        
        return order.id

class ConfirmOrderCommand:
    """Command for confirming order."""
    
    def __init__(self, order_repo: OrderRepository, event_publisher: 'EventPublisher'):
        self.order_repo = order_repo
        self.event_publisher = event_publisher
    
    def execute(self, order_id: UUID) -> None:
        """Execute confirm order use case."""
        order = self.order_repo.find_by_id(order_id)
        
        if order is None:
            raise ValueError("Order not found")
        
        order.confirm()  # Domain logic
        self.order_repo.save(order)
        
        # Publish events
        for event in order.collect_events():
            self.event_publisher.publish(event)

# infrastructure/persistence/sql_order_repository.py
class SqlOrderRepository(OrderRepository):
    """SQL implementation of OrderRepository."""
    
    def __init__(self, db_connection):
        self.db = db_connection
    
    def find_by_id(self, order_id: UUID) -> Optional[Order]:
        """Reconstruct aggregate from database."""
        row = self.db.execute(
            "SELECT * FROM orders WHERE id = ?", 
            (str(order_id),)
        ).fetchone()
        
        if not row:
            return None
        
        order = Order(UUID(row['customer_id']))
        order.id = UUID(row['id'])
        order.status = OrderStatus(row['status'])
        order.created_at = datetime.fromisoformat(row['created_at'])
        
        # Load order lines
        lines = self.db.execute(
            "SELECT * FROM order_lines WHERE order_id = ?",
            (str(order_id),)
        ).fetchall()
        
        for line_row in lines:
            order.lines.append(OrderLine(
                product_id=UUID(line_row['product_id']),
                product_name=line_row['product_name'],
                quantity=line_row['quantity'],
                unit_price=Money(line_row['unit_price'], line_row['currency'])
            ))
        
        return order
    
    def save(self, order: Order) -> None:
        """Persist entire aggregate."""
        # Save order
        self.db.execute("""
            INSERT OR REPLACE INTO orders (id, customer_id, status, created_at)
            VALUES (?, ?, ?, ?)
        """, (str(order.id), str(order.customer_id), 
              order.status.value, order.created_at.isoformat()))
        
        # Delete existing lines
        self.db.execute("DELETE FROM order_lines WHERE order_id = ?", (str(order.id),))
        
        # Save lines
        for line in order.lines:
            self.db.execute("""
                INSERT INTO order_lines 
                (order_id, product_id, product_name, quantity, unit_price, currency)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (str(order.id), str(line.product_id), line.product_name,
                  line.quantity, line.unit_price.amount, line.unit_price.currency))
        
        self.db.commit()
```

This complete example demonstrates:
- Rich domain model with business logic in entities
- Aggregate pattern with Order as root
- Value objects (Money) for domain concepts
- Domain events for significant occurrences
- Repository pattern with interface in domain, implementation in infrastructure
- Application services (commands) coordinating use cases
- Clear separation of layers
```
```
```
