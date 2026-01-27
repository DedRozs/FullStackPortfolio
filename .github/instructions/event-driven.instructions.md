---
applyTo: "**/*"
---

# Event-Driven Architecture Pattern

## Overview

- **Intent:** Design systems where components communicate through the production, detection, and consumption of events, enabling loose coupling, scalability, and real-time responsiveness.

- **When to Use:**
  - Systems need to react to state changes in real-time
  - Multiple services need to respond to the same occurrence without tight coupling
  - You need asynchronous processing and decoupled workflows
  - Building microservices that must remain independent
  - Implementing audit trails, analytics, or activity streams
  - Handling high-throughput data streams (IoT, financial transactions, logs)
  - Need for temporal decoupling (producers and consumers operate independently)

## Core Principles

1. **Event as First-Class Citizen**: Events represent facts about things that happened in the past (immutable)
2. **Publisher-Subscriber Decoupling**: Event producers don't know about consumers
3. **Asynchronous Communication**: Non-blocking message passing between components
4. **Event Immutability**: Once published, events cannot be changed
5. **Event Schema**: Well-defined structure for event data
6. **Eventual Consistency**: Accept that data may not be immediately consistent across all services

## Named Instruction Outline

### Phase 1: Define Event Schema and Types

**Objective:** Establish a consistent event structure and taxonomy.

**Steps:**

1. **Create Base Event Class:**
```python
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any
import uuid

@dataclass
class Event:
    """Base class for all domain events."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = ""
    version: str = "1.0"
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'event_id': self.event_id,
            'event_type': self.event_type,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source,
            'version': self.version,
            'data': self.data,
            'metadata': self.metadata
        }
```

2. **Define Domain-Specific Events:**
```python
@dataclass
class OrderPlacedEvent(Event):
    """Event emitted when a customer places an order."""
    
    def __init__(self, order_id: str, customer_id: str, total: float, items: list):
        super().__init__(
            event_type="order.placed",
            source="order-service",
            data={
                'order_id': order_id,
                'customer_id': customer_id,
                'total': total,
                'items': items
            }
        )

@dataclass
class PaymentProcessedEvent(Event):
    """Event emitted when payment is successfully processed."""
    
    def __init__(self, payment_id: str, order_id: str, amount: float):
        super().__init__(
            event_type="payment.processed",
            source="payment-service",
            data={
                'payment_id': payment_id,
                'order_id': order_id,
                'amount': amount,
                'status': 'completed'
            }
        )
```

3. **Use Past Tense Naming**: Events represent facts that already occurred (`OrderPlaced`, not `PlaceOrder`)

### Phase 2: Implement Event Bus/Broker

**Objective:** Create the infrastructure for publishing and subscribing to events.

**Steps:**

1. **Create Event Bus Interface:**
```python
from abc import ABC, abstractmethod
from typing import Callable, List
from collections import defaultdict

class EventBus(ABC):
    """Abstract base class for event bus implementations."""
    
    @abstractmethod
    def publish(self, event: Event) -> None:
        """Publish an event to the bus."""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe a handler to an event type."""
        pass
```

2. **Implement In-Memory Event Bus (for development/testing):**
```python
class InMemoryEventBus(EventBus):
    """Simple in-memory event bus for local development."""
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
    
    def publish(self, event: Event) -> None:
        """Publish event to all registered handlers."""
        event_type = event.event_type
        
        # Notify exact match subscribers
        for handler in self._subscribers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                print(f"Error in handler for {event_type}: {e}")
        
        # Notify wildcard subscribers (e.g., "order.*")
        base_type = event_type.split('.')[0]
        wildcard = f"{base_type}.*"
        for handler in self._subscribers.get(wildcard, []):
            try:
                handler(event)
            except Exception as e:
                print(f"Error in handler for {wildcard}: {e}")
    
    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Register a handler for an event type."""
        self._subscribers[event_type].append(handler)
```

3. **Implement Production Event Bus (using message broker):**
```python
import json
from typing import Optional

class RabbitMQEventBus(EventBus):
    """Production event bus using RabbitMQ."""
    
    def __init__(self, connection_url: str):
        # In real implementation: import pika and establish connection
        self.connection_url = connection_url
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        # self.connection = pika.BlockingConnection(...)
        # self.channel = self.connection.channel()
    
    def publish(self, event: Event) -> None:
        """Publish event to RabbitMQ exchange."""
        exchange = 'events'
        routing_key = event.event_type
        message = json.dumps(event.to_dict())
        
        # self.channel.basic_publish(
        #     exchange=exchange,
        #     routing_key=routing_key,
        #     body=message
        # )
        print(f"Published {event.event_type} to {exchange}")
    
    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe to events from RabbitMQ queue."""
        self._subscribers[event_type].append(handler)
        
        # In real implementation:
        # queue_name = f"{event_type}_queue"
        # self.channel.queue_declare(queue=queue_name)
        # self.channel.queue_bind(exchange='events', queue=queue_name, routing_key=event_type)
        # self.channel.basic_consume(queue=queue_name, on_message_callback=self._on_message)

### Phase 3: Implement Event Publishers

**Objective:** Enable services to emit events when state changes occur.

**Steps:**

1. **Create Event Publisher Mixin:**
```python
class EventPublisher:
    """Mixin to add event publishing capability to any class."""
    
    def __init__(self, event_bus: EventBus):
        self._event_bus = event_bus
    
    def publish_event(self, event: Event) -> None:
        """Publish an event to the bus."""
        self._event_bus.publish(event)
```

2. **Integrate with Domain Services:**
```python
class OrderService(EventPublisher):
    """Service for managing orders."""
    
    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
        self.orders = {}
    
    def place_order(self, customer_id: str, items: list) -> str:
        """Place a new order and emit event."""
        order_id = str(uuid.uuid4())
        total = sum(item['price'] * item['quantity'] for item in items)
        
        # Update state
        self.orders[order_id] = {
            'order_id': order_id,
            'customer_id': customer_id,
            'items': items,
            'total': total,
            'status': 'pending'
        }
        
        # Emit event
        event = OrderPlacedEvent(
            order_id=order_id,
            customer_id=customer_id,
            total=total,
            items=items
        )
        self.publish_event(event)
        
        return order_id

class PaymentService(EventPublisher):
    """Service for processing payments."""
    
    def __init__(self, event_bus: EventBus):
        super().__init__(event_bus)
    
    def process_payment(self, order_id: str, amount: float) -> str:
        """Process payment and emit event."""
        payment_id = str(uuid.uuid4())
        
        # Process payment logic here
        # ...
        
        # Emit event
        event = PaymentProcessedEvent(
            payment_id=payment_id,
            order_id=order_id,
            amount=amount
        )
        self.publish_event(event)
        
        return payment_id
```

3. **Ensure Events Are Published After State Changes:** Publish events only after successfully persisting state changes to prevent inconsistencies.

### Phase 4: Implement Event Handlers/Consumers

**Objective:** Create components that react to events.

**Steps:**

1. **Define Event Handler Interface:**
```python
class EventHandler(ABC):
    """Base class for event handlers."""
    
    @abstractmethod
    def handle(self, event: Event) -> None:
        """Process the event."""
        pass
    
    @abstractmethod
    def can_handle(self, event_type: str) -> bool:
        """Check if this handler can process the event type."""
        pass
```

2. **Implement Specific Event Handlers:**
```python
class InventoryEventHandler(EventHandler):
    """Handler that updates inventory when orders are placed."""
    
    def __init__(self):
        self.inventory = {}
    
    def can_handle(self, event_type: str) -> bool:
        return event_type == "order.placed"
    
    def handle(self, event: Event) -> None:
        """Reduce inventory for ordered items."""
        if not self.can_handle(event.event_type):
            return
        
        items = event.data.get('items', [])
        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']
            
            if product_id in self.inventory:
                self.inventory[product_id] -= quantity
                print(f"Reduced inventory for {product_id} by {quantity}")

class NotificationEventHandler(EventHandler):
    """Handler that sends notifications based on events."""
    
    def can_handle(self, event_type: str) -> bool:
        return event_type in ["order.placed", "payment.processed"]
    
    def handle(self, event: Event) -> None:
        """Send appropriate notification."""
        if event.event_type == "order.placed":
            customer_id = event.data.get('customer_id')
            order_id = event.data.get('order_id')
            print(f"Sending order confirmation to customer {customer_id} for order {order_id}")
        
        elif event.event_type == "payment.processed":
            order_id = event.data.get('order_id')
            amount = event.data.get('amount')
            print(f"Sending payment receipt for order {order_id}, amount ${amount}")

class OrderFulfillmentHandler(EventHandler):
    """Handler that triggers order fulfillment after payment."""
    
    def can_handle(self, event_type: str) -> bool:
        return event_type == "payment.processed"
    
    def handle(self, event: Event) -> None:
        """Start fulfillment process."""
        order_id = event.data.get('order_id')
        print(f"Starting fulfillment for order {order_id}")
        # Trigger warehouse systems, shipping, etc.
```

3. **Register Handlers with Event Bus:**
```python
def setup_event_handlers(event_bus: EventBus):
    """Register all event handlers with the event bus."""
    
    # Create handler instances
    inventory_handler = InventoryEventHandler()
    notification_handler = NotificationEventHandler()
    fulfillment_handler = OrderFulfillmentHandler()
    
    # Register handlers
    event_bus.subscribe("order.placed", inventory_handler.handle)
    event_bus.subscribe("order.placed", notification_handler.handle)
    event_bus.subscribe("payment.processed", notification_handler.handle)
    event_bus.subscribe("payment.processed", fulfillment_handler.handle)

### Phase 5: Implement Error Handling and Resilience

**Objective:** Ensure the system handles failures gracefully.

**Steps:**

1. **Add Dead Letter Queue for Failed Events:**
```python
class ResilientEventBus(EventBus):
    """Event bus with error handling and retry logic."""
    
    def __init__(self, base_bus: EventBus, max_retries: int = 3):
        self._base_bus = base_bus
        self._max_retries = max_retries
        self._dead_letter_queue: List[Dict[str, Any]] = []
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
    
    def publish(self, event: Event) -> None:
        """Publish event with retry logic."""
        self._base_bus.publish(event)
    
    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe with automatic retry wrapper."""
        wrapped_handler = self._create_retry_handler(handler)
        self._subscribers[event_type].append(wrapped_handler)
        self._base_bus.subscribe(event_type, wrapped_handler)
    
    def _create_retry_handler(self, handler: Callable[[Event], None]) -> Callable[[Event], None]:
        """Wrap handler with retry logic."""
        def retry_wrapper(event: Event) -> None:
            attempts = 0
            last_error = None
            
            while attempts < self._max_retries:
                try:
                    handler(event)
                    return  # Success
                except Exception as e:
                    attempts += 1
                    last_error = e
                    print(f"Handler failed (attempt {attempts}/{self._max_retries}): {e}")
            
            # All retries exhausted
            self._dead_letter_queue.append({
                'event': event.to_dict(),
                'error': str(last_error),
                'failed_at': datetime.utcnow().isoformat()
            })
            print(f"Event {event.event_id} moved to dead letter queue")
        
        return retry_wrapper
    
    def get_dead_letters(self) -> List[Dict[str, Any]]:
        """Retrieve failed events for manual inspection."""
        return self._dead_letter_queue.copy()
```

2. **Implement Idempotent Handlers:**
```python
class IdempotentEventHandler(EventHandler):
    """Handler that tracks processed events to avoid duplicate processing."""
    
    def __init__(self):
        self._processed_events: set = set()
    
    def handle(self, event: Event) -> None:
        """Process event only once."""
        if event.event_id in self._processed_events:
            print(f"Event {event.event_id} already processed, skipping")
            return
        
        try:
            self._process_event(event)
            self._processed_events.add(event.event_id)
        except Exception as e:
            print(f"Failed to process event {event.event_id}: {e}")
            raise
    
    @abstractmethod
    def _process_event(self, event: Event) -> None:
        """Actual event processing logic."""
        pass
```

3. **Add Event Versioning Support:**
```python
class VersionedEventHandler(EventHandler):
    """Handler that supports multiple event schema versions."""
    
    def __init__(self):
        self._version_handlers = {}
    
    def register_version(self, version: str, handler: Callable[[Event], None]) -> None:
        """Register handler for specific event version."""
        self._version_handlers[version] = handler
    
    def handle(self, event: Event) -> None:
        """Route to appropriate version handler."""
        version = event.version
        
        if version not in self._version_handlers:
            # Try to upgrade event to latest version
            event = self._upgrade_event(event)
            version = event.version
        
        handler = self._version_handlers.get(version)
        if handler:
            handler(event)
        else:
            raise ValueError(f"No handler for event version {version}")
    
    def _upgrade_event(self, event: Event) -> Event:
        """Upgrade event to latest schema version."""
        # Implement schema migration logic
        return event
```

### Complete Usage Example

```python
# Initialize the system
event_bus = InMemoryEventBus()
resilient_bus = ResilientEventBus(event_bus)

# Set up services
order_service = OrderService(resilient_bus)
payment_service = PaymentService(resilient_bus)

# Set up event handlers
setup_event_handlers(resilient_bus)

# Simulate a complete order flow
def process_customer_order():
    """Demonstrates end-to-end event-driven flow."""
    
    # Customer places an order
    items = [
        {'product_id': 'PROD-001', 'name': 'Widget', 'price': 29.99, 'quantity': 2},
        {'product_id': 'PROD-002', 'name': 'Gadget', 'price': 49.99, 'quantity': 1}
    ]
    
    print("=== Placing Order ===")
    order_id = order_service.place_order(
        customer_id="CUST-123",
        items=items
    )
    print(f"Order placed: {order_id}\n")
    
    # Events propagate:
    # 1. InventoryEventHandler reduces stock
    # 2. NotificationEventHandler sends confirmation
    
    # Process payment
    print("=== Processing Payment ===")
    total = sum(item['price'] * item['quantity'] for item in items)
    payment_id = payment_service.process_payment(order_id, total)
    print(f"Payment processed: {payment_id}\n")
    
    # Events propagate:
    # 1. NotificationEventHandler sends receipt
    # 2. OrderFulfillmentHandler starts shipping

# Run the example
if __name__ == "__main__":
    process_customer_order()
    
    # Check for any failed events
    dead_letters = resilient_bus.get_dead_letters()
    if dead_letters:
        print(f"\n=== Dead Letter Queue ({len(dead_letters)} events) ===")
        for dl in dead_letters:
            print(f"Failed: {dl['event']['event_type']} - {dl['error']}")

## Anti-Patterns

### 1. Event Dependency Chains
**Problem:** Creating long chains where Event A triggers Event B triggers Event C, making the flow hard to debug and reason about.

**Solution:** Keep event chains shallow. If you need complex orchestration, consider using a saga pattern or workflow engine.

```python
# ❌ BAD: Deep event chain
class OrderHandler:
    def handle(self, event):
        # ... process order ...
        self.publish(OrderValidatedEvent(...))  # Triggers another handler
        
class OrderValidatedHandler:
    def handle(self, event):
        # ... validate ...
        self.publish(InventoryReservedEvent(...))  # Triggers another handler
        
class InventoryReservedHandler:
    def handle(self, event):
        # ... reserve inventory ...
        self.publish(PaymentInitiatedEvent(...))  # And so on...

# ✅ GOOD: Direct coordination when needed
class OrderCoordinator:
    def process_order(self, order_id):
        # Explicit orchestration
        self.validate_order(order_id)
        self.reserve_inventory(order_id)
        self.initiate_payment(order_id)
        
        # Publish single event for interested parties
        self.publish(OrderProcessedEvent(order_id))
```

### 2. Synchronous Event Handling
**Problem:** Blocking the publisher until all handlers complete defeats the purpose of asynchronous architecture.

**Solution:** Always handle events asynchronously, return immediately from publish operations.

```python
# ❌ BAD: Synchronous processing blocks publisher
class EventBus:
    def publish(self, event):
        for handler in self._subscribers[event.event_type]:
            handler(event)  # Blocks until handler completes
        return  # Publisher waits for all handlers

# ✅ GOOD: Asynchronous processing
import asyncio
from concurrent.futures import ThreadPoolExecutor

class AsyncEventBus:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=10)
    
    def publish(self, event):
        """Non-blocking publish."""
        for handler in self._subscribers[event.event_type]:
            self._executor.submit(handler, event)  # Fire and forget
        return  # Publisher continues immediately
```

### 3. Events With Business Logic
**Problem:** Putting behavior/logic inside event objects turns them into active objects rather than passive data containers.

**Solution:** Events should be pure data structures. Put logic in handlers, not events.

```python
# ❌ BAD: Event contains logic
class OrderPlacedEvent(Event):
    def notify_customer(self):
        send_email(...)  # Logic doesn't belong here
    
    def update_inventory(self):
        inventory_service.reduce(...)  # Logic doesn't belong here

# ✅ GOOD: Event is pure data
@dataclass
class OrderPlacedEvent(Event):
    order_id: str
    customer_id: str
    items: List[Dict]
    # Just data, no methods

# Logic lives in handlers
class CustomerNotificationHandler:
    def handle(self, event: OrderPlacedEvent):
        send_email(event.customer_id, event.order_id)
```

### 4. Missing Event Schema Versioning
**Problem:** Changing event structure breaks existing consumers, causing production failures.

**Solution:** Always include version field in events, maintain backward compatibility.

```python
# ❌ BAD: No versioning, breaking change
# Version 1
class OrderEvent(Event):
    order_id: str
    total: float

# Version 2 - breaks consumers expecting 'total'
class OrderEvent(Event):
    order_id: str
    subtotal: float  # Renamed field!
    tax: float

# ✅ GOOD: Versioned events with compatibility
class OrderEventV1(Event):
    version = "1.0"
    order_id: str
    total: float

class OrderEventV2(Event):
    version = "2.0"
    order_id: str
    subtotal: float
    tax: float
    
    @property
    def total(self):
        """Backward compatibility for v1 consumers."""
        return self.subtotal + self.tax
```

### 5. Lack of Idempotency
**Problem:** Processing the same event multiple times (due to retries/network issues) causes duplicate actions (double charges, double inventory deduction).

**Solution:** Make all handlers idempotent using event IDs or database constraints.

```python
# ❌ BAD: Non-idempotent handler
class PaymentHandler:
    def handle(self, event):
        # If this runs twice, customer is charged twice!
        charge_credit_card(event.amount)

# ✅ GOOD: Idempotent handler
class PaymentHandler:
    def __init__(self):
        self.processed_events = set()  # In production: use database
    
    def handle(self, event):
        if event.event_id in self.processed_events:
            return  # Already processed, skip
        
        charge_credit_card(event.amount)
        self.processed_events.add(event.event_id)
```

### 6. Event Storm
**Problem:** Too many fine-grained events create excessive network traffic and complexity.

**Solution:** Find the right granularity - not too coarse, not too fine.

```python
# ❌ BAD: Too many events
class OrderService:
    def place_order(self, order):
        self.publish(OrderCreatedEvent(...))
        self.publish(OrderItemAddedEvent(...))
        self.publish(OrderItemAddedEvent(...))
        self.publish(OrderTotalCalculatedEvent(...))
        self.publish(OrderValidatedEvent(...))
        # 5+ events for one operation!

# ✅ GOOD: Right-sized events
class OrderService:
    def place_order(self, order):
        # Single event with all necessary data
        self.publish(OrderPlacedEvent(
            order_id=order.id,
            items=order.items,
            total=order.total,
            customer_id=order.customer_id
        ))

## Decision Aids

### When Event-Driven Architecture is a Good Fit

✅ **Use Event-Driven Architecture when:**

1. **Multiple Systems Need to React to Same Occurrence**
   - Example: When an order is placed, inventory, shipping, notification, and analytics systems all need to know
   - Traditional approach would require the order service to call 4+ services directly
   - With events: Order service publishes once, all interested parties subscribe

2. **You Need Temporal Decoupling**
   - Producers and consumers don't need to be online simultaneously
   - Events can be persisted and consumed later
   - Example: Processing financial transactions that must be audited even if audit system is down

3. **Real-Time Responsiveness Required**
   - Users expect immediate feedback but backend processing can be async
   - Example: Social media "like" - update UI immediately, propagate to followers asynchronously

4. **Building Audit Trails/Event Logs**
   - Every state change must be recorded
   - Need to replay history or debug "how did we get here?"
   - Example: Financial systems, medical records, compliance-heavy industries

5. **Implementing Complex Business Processes**
   - Workflows span multiple services
   - Different teams own different steps
   - Example: E-commerce checkout (inventory → payment → shipping → notification)

### When to Avoid Event-Driven Architecture

❌ **Avoid Event-Driven Architecture when:**

1. **Simple CRUD Applications**
   - If you just need to read/write data without complex reactions
   - Example: Basic content management system - direct API calls are simpler

2. **Strong Consistency Required**
   - If you can't tolerate eventual consistency
   - Example: Real-time inventory that must be exact (though this can be solved with patterns like CQRS)

3. **Tight Transaction Boundaries**
   - When multiple operations must succeed/fail as atomic unit
   - Example: Banking transfer (debit + credit) - use distributed transactions instead

4. **Small Team/Simple Domain**
   - Overhead of event infrastructure not justified
   - Example: Internal tool used by 5 people - keep it simple

5. **Debugging/Observability is Critical Constraint**
   - Event-driven systems are harder to debug than request/response
   - If your team lacks tooling/expertise for distributed tracing

### Hybrid Approach: When to Mix Patterns

Often the best solution combines event-driven with request/response:

```python
class OrderService:
    """Hybrid: Synchronous for critical path, async for side effects."""
    
    def place_order(self, order_data):
        # Synchronous operations for immediate feedback
        order = self._validate_order(order_data)
        payment_result = self._payment_service.authorize(order.total)  # Sync call
        
        if not payment_result.success:
            return {'error': 'Payment failed'}
        
        # Save order (critical path)
        self._repository.save(order)
        
        # Asynchronous events for non-critical notifications
        self._event_bus.publish(OrderPlacedEvent(order))  # Fire and forget
        
        return {'order_id': order.id, 'status': 'confirmed'}
```

**Decision Matrix:**

| Requirement | Request/Response | Event-Driven | Hybrid |
|------------|------------------|--------------|--------|
| Need immediate response | ✅ | ❌ | ✅ |
| Multiple consumers | ❌ | ✅ | ✅ |
| Loose coupling | ❌ | ✅ | ⚠️ |
| Debugging simplicity | ✅ | ❌ | ⚠️ |
| Audit trail | ❌ | ✅ | ✅ |
| Transaction guarantees | ✅ | ❌ | ⚠️ |

## Implementation Checklist

### Phase 1: Event Schema ✓
- [ ] Base `Event` class created with: event_id, event_type, timestamp, source, version, data, metadata
- [ ] Domain events defined using past tense naming (e.g., `OrderPlaced`, not `PlaceOrder`)
- [ ] Events are immutable (use `@dataclass(frozen=True)` or similar)
- [ ] Event types use namespaced naming (e.g., "order.placed", "payment.processed")
- [ ] Events include version field for future schema evolution

### Phase 2: Event Bus ✓
- [ ] `EventBus` interface defined with `publish()` and `subscribe()` methods
- [ ] In-memory implementation exists for local development/testing
- [ ] Production implementation chosen (RabbitMQ, Kafka, AWS SNS/SQS, Azure Service Bus, etc.)
- [ ] Event bus supports wildcard subscriptions (e.g., "order.*")
- [ ] Connection management and error handling implemented

### Phase 3: Event Publishers ✓
- [ ] `EventPublisher` mixin or base class created
- [ ] Domain services emit events after state changes (not before)
- [ ] Events published only after successful persistence (no phantom events)
- [ ] Published events include all necessary context (avoid requiring lookups)
- [ ] Publisher doesn't know about subscribers (true decoupling)

### Phase 4: Event Handlers ✓
- [ ] `EventHandler` interface defined with `handle()` and `can_handle()` methods
- [ ] Handlers implemented for each domain reaction
- [ ] Handlers registered with event bus using clear subscription rules
- [ ] Handlers are focused (single responsibility - don't do too much)
- [ ] Handler errors don't crash other handlers

### Phase 5: Error Handling & Resilience ✓
- [ ] Dead letter queue implemented for failed events
- [ ] Retry logic with exponential backoff
- [ ] Handlers are idempotent (can safely process same event multiple times)
- [ ] Event deduplication strategy in place (using event_id)
- [ ] Poison message detection (events that always fail)
- [ ] Monitoring and alerting for event processing failures
- [ ] Circuit breaker pattern for downstream service failures

### Operational Readiness ✓
- [ ] Event schema documented (what events exist, what data they carry)
- [ ] Event flow diagrams created (which events trigger which handlers)
- [ ] Distributed tracing implemented (correlation IDs across event chains)
- [ ] Metrics tracked: events published, events consumed, handler latency, failures
- [ ] Log aggregation captures event processing across all services
- [ ] Tools available to replay events (for testing/recovery)
- [ ] Dead letter queue inspection/reprocessing procedures documented

### Testing Strategy ✓
- [ ] Unit tests for event handlers (isolated from event bus)
- [ ] Integration tests for event flow (end-to-end scenarios)
- [ ] Contract tests for event schemas (prevent breaking changes)
- [ ] Chaos testing for failure scenarios (lost messages, duplicate delivery)
- [ ] Performance tests for event throughput and latency

### Common Gotchas Addressed ✓
- [ ] ⚠️ Event chains don't exceed 2-3 levels deep (or saga pattern used)
- [ ] ⚠️ Events don't contain behavior (pure data only)
- [ ] ⚠️ No circular event dependencies (A triggers B which triggers A)
- [ ] ⚠️ Event granularity is right-sized (not too fine, not too coarse)
- [ ] ⚠️ Handlers don't call back to event publishers (breaks decoupling)
- [ ] ⚠️ Schema versioning strategy prevents breaking changes
- [ ] ⚠️ Team understands eventual consistency tradeoffs

## Related Patterns

- **CQRS (Command Query Responsibility Segregation)**: Often used with event-driven architecture to separate read and write models
- **Event Sourcing**: Store all state changes as sequence of events (more extreme than event-driven)
- **Saga Pattern**: Coordinate distributed transactions using events
- **Circuit Breaker**: Protect event handlers from cascading failures
- **Message Queue Pattern**: Infrastructure for reliable event delivery
- **Outbox Pattern**: Ensure events are published reliably with database transactions

## Further Reading

- Martin Fowler's "Event-Driven" article: https://martinfowler.com/articles/201701-event-driven.html
- "Building Event-Driven Microservices" by Adam Bellemare (O'Reilly)
- AWS Well-Architected Framework: Event-Driven Architecture
- Microsoft Azure Architecture Center: Event-Driven Architecture style
```
```
```
```
