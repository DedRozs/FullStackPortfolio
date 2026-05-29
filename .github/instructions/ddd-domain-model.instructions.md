---
applyTo: "**/domain/**/*.{py,ts,cs,java,kt}"
description: "Use when writing or reviewing code in domain/ - entities, value objects, aggregates, domain events, or domain services. Covers identity, invariants, state transitions, immutability, and the zero-external-dependency rule for the domain layer."
---
<!-- v1.0 | Created: 2026-05-01 | Pattern: DDD - Domain Model Layer -->

# DDD Domain Model Instructions

Rules for code inside `domain/`. This layer has zero dependencies on any other layer.

---

## Entities

**Rules:**
- Have a stable identity (`UUID` or equivalent). Equality is by identity, not attributes.
- Encapsulate invariants as methods. An entity that is a plain data bag with public setters is an anemic model - a violation.
- State transitions happen through named methods that enforce guards. Never mutate state fields directly from outside the class.
- `__init__` assigns identity and sets initial valid state. It does not accept an `id` parameter from callers - the entity owns its own identity.

```python
# domain/model/customer.py
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID, uuid4


@dataclass
class Customer:
    id: UUID
    name: str
    email: str
    credit_limit: Decimal

    def __init__(self, name: str, email: str, credit_limit: Decimal = Decimal('1000.00')):
        self.id = uuid4()
        self.name = name
        self.email = email
        self.credit_limit = credit_limit

    def increase_credit_limit(self, amount: Decimal) -> None:
        """Business rule: increases must be positive."""
        if amount <= 0:
            raise ValueError("Credit increase must be positive")
        self.credit_limit += amount

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Customer):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)
```

**What to reject:**

```python
# WRONG - anemic model, state mutated externally
customer.credit_limit = customer.credit_limit + amount

# WRONG - public setter bypasses invariants
def set_credit_limit(self, value): self.credit_limit = value
```

---

## Value Objects

**Rules:**
- Immutable: `@dataclass(frozen=True)` in Python, or equivalent in other languages.
- Validated at construction in `__post_init__`. Invalid state must be unconstructable.
- Equality is by value, not identity. Two `Money(Decimal('10.00'), 'USD')` instances are equal.
- Define `__add__` when the type will be used with `sum()` or accumulation. `sum()` uses `+`; without `__add__` it raises `TypeError`.
- Use `Decimal`, not `float`, for all monetary and financial values. `float` cannot represent most decimal fractions exactly.
- Value objects are side-effect free. Methods return new instances; they never mutate.

```python
# domain/model/money.py
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative")
        if not self.currency or len(self.currency) != 3:
            raise ValueError("Currency must be a 3-letter ISO code")

    def add(self, other: 'Money') -> 'Money':
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __add__(self, other: 'Money') -> 'Money':
        return self.add(other)

    def multiply(self, factor: Decimal) -> 'Money':
        return Money(self.amount * factor, self.currency)

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"
```

```python
# domain/model/address.py
from dataclasses import dataclass


@dataclass(frozen=True)
class Address:
    street: str
    city: str
    postal_code: str
    country: str

    def __post_init__(self) -> None:
        if not self.street or not self.city:
            raise ValueError("Street and city are required")
        if not self.country or len(self.country) != 2:
            raise ValueError("Country must be a 2-letter ISO code")
```

**What to reject:**

```python
# WRONG - float for money
amount: float = 10.50

# WRONG - no validation, invalid state constructable
@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str
```

---

## Aggregates

**Rules:**
- One aggregate root per cluster. All external access goes through the root - never through internal entities.
- Never reach into an aggregate's internal collections directly (`order.lines.append(...)`). Always call a root method.
- All state transitions are guarded inside root methods. The root is the only code that may change its own state or the state of its internal entities.
- Keep aggregates small. If loading an aggregate requires joining more than 2-3 tables, it is probably too large.
- Cross-aggregate references use IDs only - never hold object references to other aggregates.
- One aggregate = one transaction boundary. Coordinating multiple aggregates in one transaction is a design smell.
- For infrastructure rehydration, provide a `reconstitute()` class method clearly marked as infrastructure-only. Never reuse domain creation methods (e.g., `add_line()`) for rehydration - they enforce creation invariants that do not apply when restoring persisted state.

```python
# domain/model/order.py
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List
from uuid import UUID, uuid4

from domain.model.money import Money


class OrderStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass
class OrderLine:
    product_id: UUID
    product_name: str
    quantity: int
    unit_price: Money

    def total(self) -> Money:
        return self.unit_price.multiply(Decimal(self.quantity))


@dataclass
class Order:
    """Aggregate root. All mutation goes through public methods - never directly."""
    id: UUID
    customer_id: UUID
    status: OrderStatus
    lines: List[OrderLine]
    created_at: datetime
    _events: List

    def __init__(self, customer_id: UUID) -> None:
        self.id = uuid4()
        self.customer_id = customer_id
        self.status = OrderStatus.DRAFT
        self.lines = []
        self.created_at = datetime.now()
        self._events = []

    # --- Commands (state-changing methods) ---

    def add_line(self, product_id: UUID, product_name: str,
                 quantity: int, unit_price: Money) -> None:
        if self.status not in (OrderStatus.DRAFT, OrderStatus.PENDING):
            raise ValueError(f"Cannot modify order in {self.status.value} status")
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if any(line.product_id == product_id for line in self.lines):
            raise ValueError("Product already in order")
        self.lines.append(OrderLine(product_id, product_name, quantity, unit_price))

    def submit(self) -> None:
        """Transition DRAFT -> PENDING."""
        if self.status != OrderStatus.DRAFT:
            raise ValueError(f"Cannot submit order in {self.status.value} status")
        if not self.lines:
            raise ValueError("Cannot submit an empty order")
        self.status = OrderStatus.PENDING

    def confirm(self) -> None:
        """Transition PENDING -> CONFIRMED. Collects OrderConfirmed event."""
        if self.status != OrderStatus.PENDING:
            raise ValueError(f"Cannot confirm order in {self.status.value} status")
        self.status = OrderStatus.CONFIRMED
        self._events.append(OrderConfirmed(
            order_id=self.id,
            customer_id=self.customer_id,
            total_amount=self.total_amount(),
        ))

    def cancel(self, reason: str) -> None:
        if self.status in (OrderStatus.SHIPPED, OrderStatus.DELIVERED):
            raise ValueError(f"Cannot cancel {self.status.value} order")
        old_status = self.status
        self.status = OrderStatus.CANCELLED
        self._events.append(OrderCancelled(
            order_id=self.id,
            previous_status=old_status,
            reason=reason,
        ))

    # --- Queries (read-only methods) ---

    def total_amount(self) -> Money:
        if not self.lines:
            return Money(Decimal('0'), 'USD')
        return sum((line.total() for line in self.lines[1:]),
                   start=self.lines[0].total())

    # --- Event collection ---

    def collect_events(self) -> List:
        events = self._events.copy()
        self._events.clear()
        return events

    # --- Infrastructure rehydration (infrastructure layer use only) ---

    @classmethod
    def reconstitute(cls, id: UUID, customer_id: UUID, status: OrderStatus,
                     lines: List[OrderLine], created_at: datetime) -> 'Order':
        """Rehydrate an Order from persistence. Do NOT use in domain or application code."""
        instance = object.__new__(cls)
        instance.id = id
        instance.customer_id = customer_id
        instance.status = status
        instance.lines = lines
        instance.created_at = created_at
        instance._events = []
        return instance
```

**What to reject:**

```python
# WRONG - direct collection mutation bypasses invariants
order.lines.append(OrderLine(...))

# WRONG - direct state mutation bypasses guards
order.status = OrderStatus.CONFIRMED

# WRONG - cross-aggregate object reference
order.customer = customer_object  # use order.customer_id: UUID instead
```

---

## Domain Events

**Rules:**
- Named in past tense, describing what happened: `OrderConfirmed`, `PaymentReceived`, `CustomerCreditLimitIncreased`.
- Immutable: `@dataclass(frozen=True)` in Python.
- Carry sufficient payload for consumers to act without re-querying. Include key identifiers and relevant values.
- Aggregates collect events during operations. Events are published by the application layer after successful persistence - never inside the aggregate, never before the save.
- Prefer the collect-and-publish pattern over injecting a publisher into the aggregate constructor.
- Place event definitions in `domain/events/`. They are part of the domain contract.

```python
# domain/events/order_events.py
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from domain.model.money import Money
from domain.model.order import OrderStatus


@dataclass(frozen=True)
class DomainEvent:
    occurred_at: datetime = field(default_factory=datetime.now)


@dataclass(frozen=True)
class OrderConfirmed(DomainEvent):
    order_id: UUID
    customer_id: UUID
    total_amount: Money  # carry the value, not just the ID


@dataclass(frozen=True)
class OrderCancelled(DomainEvent):
    order_id: UUID
    previous_status: OrderStatus
    reason: str


@dataclass(frozen=True)
class CustomerCreditLimitIncreased(DomainEvent):
    customer_id: UUID
    old_limit: Decimal
    new_limit: Decimal
```

**What to reject:**

```python
# WRONG - imperative name
class ConfirmOrder: ...

# WRONG - carries only an ID, forces consumers to re-query
@dataclass(frozen=True)
class OrderConfirmed(DomainEvent):
    order_id: UUID  # consumer must query to find out what happened

# WRONG - publisher injected into aggregate
class Order:
    def __init__(self, customer_id: UUID, publisher: EventPublisher): ...
```

---

## Domain Services

**Rules:**
- Stateless. No mutable instance fields beyond injected repository or service interfaces.
- Used only for operations that naturally span multiple aggregates and belong to neither root.
- Import only from `domain/`. Never import from `infrastructure/`, `application/`, or any framework.
- If an operation belongs to a single aggregate, it is a method on that aggregate - not a domain service.

```python
# domain/services/pricing_service.py
from decimal import Decimal
from uuid import UUID

from domain.model.money import Money
from domain.model.order import Order
from domain.repositories.customer_repository import CustomerRepository


class PricingService:
    """Calculates order totals with customer-tier discounts.

    Uses both Order and Customer aggregates, so it belongs in a domain service
    rather than on either aggregate root.
    """

    def __init__(self, customer_repo: CustomerRepository) -> None:
        self._customer_repo = customer_repo

    def calculate_discounted_total(self, order: Order, customer_id: UUID) -> Money:
        base = order.total_amount()
        customer = self._customer_repo.find_by_id(customer_id)
        if customer is None:
            return base
        rate = self._discount_rate(customer.credit_limit)
        return base.multiply(Decimal('1') - rate)

    def _discount_rate(self, credit_limit: Decimal) -> Decimal:
        if credit_limit > Decimal('10000'):
            return Decimal('0.15')
        if credit_limit > Decimal('5000'):
            return Decimal('0.10')
        return Decimal('0.05')
```
