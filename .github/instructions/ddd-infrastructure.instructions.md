---
applyTo: "**/infrastructure/**/*.{py,ts,cs,java,kt}"
description: "Use when writing or reviewing code in infrastructure/ - repository implementations, ORM mapping, persistence adapters, external service clients, or anti-corruption layers. Covers interface implementation rules, domain-to-persistence mapping, and bounded context translation."
---
<!-- v1.0 | Created: 2026-05-01 | Pattern: DDD - Infrastructure Layer -->

# DDD Infrastructure Instructions

Rules for code inside `infrastructure/`. This layer implements domain interfaces and
translates between the domain model and external systems (databases, APIs, message brokers).

---

## Repositories

**Rules:**
- Repository interfaces live in `domain/repositories/` and are ABCs. They define the collection contract in domain language.
- Concrete implementations live in `infrastructure/persistence/` and may use any ORM or raw SQL.
- Interfaces accept and return domain objects (aggregate roots). They never accept or return ORM models, raw dicts, or DB rows.
- Method names use domain language: `find_by_email`, `find_confirmed_orders`. Not `select`, `query`, `fetch`, or `get_all`.
- Only work with aggregate roots. Never expose a repository for an internal entity (e.g., `OrderLineRepository` is wrong - access order lines through `OrderRepository`).
- Rehydration in the concrete implementation must use `reconstitute()` or equivalent. Never call domain creation methods (e.g., `add_line()`) during reconstruction from DB - those enforce creation invariants that must not run at rehydration time.

```python
# domain/repositories/order_repository.py  (interface - lives in domain, not infrastructure)
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from domain.model.order import Order


class OrderRepository(ABC):

    @abstractmethod
    def find_by_id(self, order_id: UUID) -> Optional[Order]:
        ...

    @abstractmethod
    def find_by_customer(self, customer_id: UUID) -> List[Order]:
        ...

    @abstractmethod
    def save(self, order: Order) -> None:
        ...
```

```python
# infrastructure/persistence/sql_order_repository.py
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from domain.model.money import Money
from domain.model.order import Order, OrderLine, OrderStatus
from domain.repositories.order_repository import OrderRepository


class SqlOrderRepository(OrderRepository):

    def __init__(self, db) -> None:
        self._db = db

    def find_by_id(self, order_id: UUID) -> Optional[Order]:
        row = self._db.execute(
            "SELECT * FROM orders WHERE id = ?", (str(order_id),)
        ).fetchone()
        if not row:
            return None

        line_rows = self._db.execute(
            "SELECT * FROM order_lines WHERE order_id = ?", (str(order_id),)
        ).fetchall()

        lines = [
            OrderLine(
                product_id=UUID(r['product_id']),
                product_name=r['product_name'],
                quantity=r['quantity'],
                unit_price=Money(Decimal(r['unit_price']), r['currency']),
            )
            for r in line_rows
        ]

        # reconstitute() is the correct entry point for rehydration.
        # Never call Order() or add_line() here.
        return Order.reconstitute(
            id=UUID(row['id']),
            customer_id=UUID(row['customer_id']),
            status=OrderStatus(row['status']),
            lines=lines,
            created_at=row['created_at'],
        )

    def find_by_customer(self, customer_id: UUID) -> List[Order]:
        rows = self._db.execute(
            "SELECT id FROM orders WHERE customer_id = ?", (str(customer_id),)
        ).fetchall()
        return [self.find_by_id(UUID(r['id'])) for r in rows]

    def save(self, order: Order) -> None:
        self._db.execute(
            "INSERT OR REPLACE INTO orders (id, customer_id, status, created_at) "
            "VALUES (?, ?, ?, ?)",
            (str(order.id), str(order.customer_id),
             order.status.value, order.created_at.isoformat()),
        )
        self._db.execute(
            "DELETE FROM order_lines WHERE order_id = ?", (str(order.id),)
        )
        for line in order.lines:
            self._db.execute(
                "INSERT INTO order_lines "
                "(order_id, product_id, product_name, quantity, unit_price, currency) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (str(order.id), str(line.product_id), line.product_name,
                 line.quantity, str(line.unit_price.amount), line.unit_price.currency),
            )
        self._db.commit()
```

---

## Bounded Contexts

**Rules:**
- Each bounded context owns its own model. The same real-world concept (an "order") is modeled differently in different contexts - do not share the class.
- Cross-context references use IDs only. Never pass a domain object from one context into another context's code.
- Integration between contexts happens via published domain events or an anti-corruption layer (ACL) - never by sharing a repository or domain class.
- If the same term means different things in two parts of the system, that is a context boundary signal. Model them separately.

```python
# Sales context - cares about pricing and customer relationship
# domain/model/sales_order.py
@dataclass
class SalesOrder:
    order_id: UUID
    customer_id: UUID
    line_items: List['SalesLineItem']
    applied_discount: Decimal

# Shipping context - cares about delivery logistics
# domain/model/shipment.py
@dataclass
class Shipment:
    order_id: UUID          # reference by ID only - not a SalesOrder object
    destination: Address
    total_weight_kg: float
    carrier: str
    tracking_number: Optional[str]

# Inventory context - cares about stock reservation
# domain/model/inventory_reservation.py
@dataclass
class InventoryReservation:
    order_id: UUID          # same order_id, entirely different model
    warehouse_id: UUID
    reserved_lines: List['ReservationLine']
    expires_at: datetime
```

**What to reject:**

```python
# WRONG - one Order class imported across all contexts
from sales.domain.model.order import Order  # used in shipping code
```

---

## Anti-Corruption Layer

When integrating with an external system (payment gateway, third-party API, legacy service),
wrap it in an ACL class inside `infrastructure/external/`. The ACL translates between the
external system's model and the domain model. The domain layer never imports external types directly.

```python
# infrastructure/external/payment_gateway_adapter.py
from domain.model.money import Money
from domain.model.order import Order


class PaymentGatewayAdapter:
    """ACL: translates between domain model and ThirdPartyPaymentAPI.

    The domain never knows this external service exists. All translation
    happens here, protecting the domain from third-party API changes.
    """

    def __init__(self, gateway) -> None:
        self._gateway = gateway

    def charge(self, order: Order, payment_method: str) -> bool:
        amount = order.total_amount()
        response = self._gateway.charge({
            'amount_cents': int(amount.amount * 100),
            'currency_code': amount.currency,
            'order_ref': str(order.id),
            'method': self._map_method(payment_method),
        })
        return response['status'] == 'success'

    def _map_method(self, domain_method: str) -> str:
        """Translate domain payment method names to external API codes."""
        return {'credit_card': 'CC', 'debit_card': 'DC', 'paypal': 'PP'}.get(
            domain_method, 'CC'
        )
```

**What to reject:**

```python
# WRONG - domain model imports from external library directly
from stripe import PaymentIntent  # external type leaking into domain

# WRONG - no translation layer, external response used directly in domain logic
external_response = gateway.charge(...)
if external_response['status'] == 'success':  # domain logic coupled to external schema
    order.confirm()
```
