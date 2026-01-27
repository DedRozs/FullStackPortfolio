"""Application services for the Contact bounded context.

Application services orchestrate use cases by:
1. Receiving commands/queries
2. Coordinating domain objects
3. Using repositories for persistence
4. Publishing domain events
"""
from dataclasses import dataclass
from uuid import UUID

from apps.contact.domain.entities import ContactMessage
from apps.contact.domain.events import ContactMessageCreated, ContactMessageRead
from apps.contact.domain.repositories import ContactMessageRepository
from apps.contact.application.commands import (
    CreateContactMessageCommand,
    MarkMessageAsReadCommand,
    DeleteMessageCommand,
)
from apps.contact.application.queries import GetMessageByIdQuery, GetAllMessagesQuery
from apps.shared.domain.value_objects import Email, PersonName
from apps.shared.infrastructure.event_bus import EventBus


class ContactApplicationService:
    """Application service for Contact use cases.
    
    This is the entry point for the application layer.
    It coordinates between the domain and infrastructure.
    """
    
    def __init__(
        self,
        repository: ContactMessageRepository,
        event_bus: EventBus,
    ) -> None:
        self._repository = repository
        self._event_bus = event_bus
    
    def create_message(self, command: CreateContactMessageCommand) -> UUID:
        """Handle CreateContactMessageCommand.
        
        Creates a new contact message and publishes an event.
        Returns the message ID.
        """
        # Create value objects (validation happens here)
        name = PersonName(command.name)
        email = Email(command.email)
        
        # Create the aggregate
        message = ContactMessage(
            name=name,
            email=email,
            message=command.message,
        )
        
        # Persist through repository
        self._repository.save(message)
        
        # Publish domain event
        event = ContactMessageCreated(
            message_id=message.id,
            sender_name=str(message.name),
            sender_email=str(message.email),
        )
        self._event_bus.publish(event)
        
        return message.id
    
    def mark_as_read(self, command: MarkMessageAsReadCommand) -> None:
        """Handle MarkMessageAsReadCommand."""
        message = self._repository.find_by_id(command.message_id)
        if message is None:
            raise ValueError(f"Message not found: {command.message_id}")
        
        message.mark_as_read()
        self._repository.save(message)
        
        event = ContactMessageRead(message_id=message.id)
        self._event_bus.publish(event)
    
    def delete_message(self, command: DeleteMessageCommand) -> None:
        """Handle DeleteMessageCommand."""
        message = self._repository.find_by_id(command.message_id)
        if message is None:
            raise ValueError(f"Message not found: {command.message_id}")
        
        self._repository.delete(message)
    
    def get_message(self, query: GetMessageByIdQuery) -> ContactMessage | None:
        """Handle GetMessageByIdQuery."""
        return self._repository.find_by_id(query.message_id)
    
    def get_all_messages(self, query: GetAllMessagesQuery) -> list[ContactMessage]:
        """Handle GetAllMessagesQuery."""
        return self._repository.find_all(include_read=query.include_read)


@dataclass
class ContactMessageDTO:
    """Data Transfer Object for ContactMessage.
    
    Used to transfer data to the presentation layer
    without exposing domain internals.
    """
    id: str
    name: str
    email: str
    message: str
    created_at: str
    is_read: bool
    
    @classmethod
    def from_entity(cls, entity: ContactMessage) -> 'ContactMessageDTO':
        """Create DTO from domain entity."""
        return cls(
            id=str(entity.id),
            name=str(entity.name),
            email=str(entity.email),
            message=entity.message,
            created_at=entity.created_at.isoformat(),
            is_read=entity.is_read,
        )
