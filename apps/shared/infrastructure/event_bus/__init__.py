"""Event bus for publishing and subscribing to domain events."""
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Callable

from apps.shared.domain.events import DomainEvent


class EventBus(ABC):
    """Abstract event bus interface.
    
    Defined in infrastructure but interface could live in domain.
    """
    
    @abstractmethod
    def publish(self, event: DomainEvent) -> None:
        """Publish an event to all subscribers."""
        pass
    
    @abstractmethod
    def subscribe(self, event_type: type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        """Subscribe a handler to an event type."""
        pass


class InMemoryEventBus(EventBus):
    """Simple in-memory event bus for development.
    
    In production, replace with RabbitMQ, Redis, or similar.
    """
    
    def __init__(self) -> None:
        self._subscribers: dict[type[DomainEvent], list[Callable]] = defaultdict(list)
    
    def publish(self, event: DomainEvent) -> None:
        """Publish event to all registered handlers."""
        event_type = type(event)
        for handler in self._subscribers.get(event_type, []):
            try:
                handler(event)
            except Exception as e:
                # In production: log error, potentially retry or dead-letter
                print(f"Error in event handler for {event_type.__name__}: {e}")
    
    def subscribe(self, event_type: type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        """Register a handler for an event type."""
        self._subscribers[event_type].append(handler)


# Singleton instance for dependency injection
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """Get the event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = InMemoryEventBus()
    return _event_bus
