---
applyTo: "**/application/**/*.{py,ts,cs,java,kt}"
description: "Use when writing or reviewing code in application/ - application services, use cases, command handlers, or query handlers. Covers orchestration rules, DTO boundaries, prohibited business logic, and dependency injection patterns for the application layer."
---
<!-- v1.0 | Created: 2026-05-01 | Pattern: DDD - Application Layer -->

# DDD Application Layer Instructions

Rules for code inside `application/`. This layer orchestrates use cases. It contains
no business logic - all domain rules live in `domain/`.

---

## Application Services

**Rules:**
- One public method per use case. Name it after the use case: `create_order`, `confirm_order`.
- The only logic permitted: validate input exists, load aggregate(s), call domain method(s), save, publish collected events, return a DTO or scalar.
- No `if/else` on domain state. No calculations. No business rules of any kind. If any appear, move them into the aggregate or a domain service.
- Inject all dependencies (repositories, domain services, event publisher) via constructor.
- Return DTOs or primitive types to the presentation layer. Never return domain objects directly.
- Events are published here, after a successful save. Never before the save, never inside the domain object.

```python
# application/commands/order_commands.py
from decimal import Decimal
from typing import List
from uuid import UUID

from domain.model.money import Money
from domain.model.order import Order
from domain.repositories.customer_repository import CustomerRepository
from domain.repositories.order_repository import OrderRepository


class CreateOrderCommand:

    def __init__(self, order_repo: OrderRepository,
                 customer_repo: CustomerRepository,
                 event_publisher) -> None:
        self._order_repo = order_repo
        self._customer_repo = customer_repo
        self._publisher = event_publisher

    def execute(self, customer_id: UUID, items: List[dict]) -> UUID:
        # 1. Validate input exists
        if self._customer_repo.find_by_id(customer_id) is None:
            raise ValueError("Customer not found")

        # 2. Create and mutate aggregate via domain methods
        order = Order(customer_id)
        for item in items:
            order.add_line(
                product_id=item['product_id'],
                product_name=item['name'],
                quantity=item['quantity'],
                unit_price=Money(Decimal(str(item['price'])), item['currency']),
            )
        order.submit()

        # 3. Persist
        self._order_repo.save(order)

        # 4. Publish events collected during domain operations
        for event in order.collect_events():
            self._publisher.publish(event)

        # 5. Return scalar, not domain object
        return order.id


class ConfirmOrderCommand:

    def __init__(self, order_repo: OrderRepository, event_publisher) -> None:
        self._order_repo = order_repo
        self._publisher = event_publisher

    def execute(self, order_id: UUID) -> None:
        order = self._order_repo.find_by_id(order_id)
        if order is None:
            raise ValueError("Order not found")

        order.confirm()  # all business logic is inside the aggregate

        self._order_repo.save(order)
        for event in order.collect_events():
            self._publisher.publish(event)
```

**What to reject:**

```python
# WRONG - business logic in application service
def execute(self, order_id: UUID) -> None:
    order = self._order_repo.find_by_id(order_id)
    if not order.lines:                           # domain rule - belongs in order.confirm()
        raise ValueError("Empty order")
    if order.total_amount().amount > limit:       # domain rule - belongs in aggregate
        raise ValueError("Exceeds limit")
    order.status = OrderStatus.CONFIRMED          # direct mutation - violates aggregate root
    self._order_repo.save(order)

# WRONG - domain object returned to presentation layer
def execute(self, order_id: UUID) -> Order:       # should return a DTO
    return self._order_repo.find_by_id(order_id)

# WRONG - events published before save
order.confirm()
for event in order.collect_events():
    self._publisher.publish(event)    # fires before save - if save fails, event already sent
self._order_repo.save(order)
```

---

## Query Handlers

**Rules:**
- Query handlers (read side) live in `application/queries/`. They do not modify state.
- Queries may bypass the domain model and read directly from a read model or view when performance requires it. This is acceptable on the read side only.
- Never use a query handler to load an aggregate just to read its state for a response. Use a dedicated read model or DTO projection.

```python
# application/queries/order_queries.py
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from uuid import UUID


@dataclass
class OrderSummaryDto:
    order_id: UUID
    customer_id: UUID
    status: str
    total_amount: Decimal
    currency: str
    line_count: int


class GetOrderSummaryQuery:

    def __init__(self, db) -> None:
        self._db = db

    def execute(self, order_id: UUID) -> Optional[OrderSummaryDto]:
        row = self._db.execute("""
            SELECT o.id, o.customer_id, o.status,
                   SUM(ol.quantity * ol.unit_price) AS total,
                   MAX(ol.currency) AS currency,
                   COUNT(ol.id) AS line_count
            FROM orders o
            LEFT JOIN order_lines ol ON ol.order_id = o.id
            WHERE o.id = ?
            GROUP BY o.id
        """, (str(order_id),)).fetchone()

        if not row:
            return None

        return OrderSummaryDto(
            order_id=UUID(row['id']),
            customer_id=UUID(row['customer_id']),
            status=row['status'],
            total_amount=Decimal(str(row['total'] or 0)),
            currency=row['currency'] or 'USD',
            line_count=row['line_count'],
        )
```
