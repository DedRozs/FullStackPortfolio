"""Domain events for the Contact bounded context."""
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from apps.shared.domain.events import DomainEvent


@dataclass(frozen=True)
class ContactMessageCreated(DomainEvent):
    """Event raised when a new contact message is submitted."""
    message_id: UUID = field(default_factory=lambda: None)  # type: ignore
    sender_name: str = ""
    sender_email: str = ""
    
    def _get_event_data(self) -> dict[str, Any]:
        return {
            'message_id': str(self.message_id),
            'sender_name': self.sender_name,
            'sender_email': self.sender_email,
        }


@dataclass(frozen=True)
class ContactMessageRead(DomainEvent):
    """Event raised when a contact message is marked as read."""
    message_id: UUID = field(default_factory=lambda: None)  # type: ignore
    
    def _get_event_data(self) -> dict[str, Any]:
        return {
            'message_id': str(self.message_id),
        }
