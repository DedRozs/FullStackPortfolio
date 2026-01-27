"""Repository interfaces for the Contact bounded context.

These are abstract interfaces defined in the domain layer.
Concrete implementations live in the infrastructure layer.
"""
from abc import ABC, abstractmethod
from uuid import UUID

from apps.contact.domain.entities import ContactMessage


class ContactMessageRepository(ABC):
    """Abstract repository for ContactMessage aggregate.
    
    Repositories provide collection-like interfaces for aggregates.
    They abstract away persistence details from the domain.
    """
    
    @abstractmethod
    def save(self, message: ContactMessage) -> None:
        """Persist a contact message."""
        pass
    
    @abstractmethod
    def find_by_id(self, message_id: UUID) -> ContactMessage | None:
        """Find a message by its ID."""
        pass
    
    @abstractmethod
    def find_all(self, include_read: bool = True) -> list[ContactMessage]:
        """Find all messages, optionally filtering by read status."""
        pass
    
    @abstractmethod
    def delete(self, message: ContactMessage) -> None:
        """Delete a contact message."""
        pass
