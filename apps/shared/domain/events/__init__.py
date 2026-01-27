"""Base domain event classes."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True)
class DomainEvent:
    """Base class for all domain events.
    
    Events are immutable facts about things that happened in the domain.
    They are named in past tense (e.g., ContactMessageCreated).
    """
    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> dict[str, Any]:
        """Serialize event for publishing."""
        return {
            'event_id': str(self.event_id),
            'event_type': self.__class__.__name__,
            'occurred_at': self.occurred_at.isoformat(),
            'data': self._get_event_data(),
        }
    
    def _get_event_data(self) -> dict[str, Any]:
        """Override in subclasses to provide event-specific data."""
        return {}
