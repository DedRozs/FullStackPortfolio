"""Repository implementations for the Contact bounded context.

These are concrete implementations of the repository interfaces
defined in the domain layer. They use Django ORM.
"""
from uuid import UUID

from apps.contact.domain.entities import ContactMessage
from apps.contact.domain.repositories import ContactMessageRepository
from apps.contact.infrastructure.models import ContactMessageModel
from apps.shared.domain.value_objects import Email, PersonName


class DjangoContactMessageRepository(ContactMessageRepository):
    """Django ORM implementation of ContactMessageRepository.
    
    Handles mapping between domain entities and ORM models.
    """
    
    def save(self, message: ContactMessage) -> None:
        """Persist a contact message."""
        ContactMessageModel.objects.update_or_create(
            id=message.id,
            defaults={
                'name': str(message.name),
                'email': str(message.email),
                'message': message.message,
                'is_read': message.is_read,
            }
        )
    
    def find_by_id(self, message_id: UUID) -> ContactMessage | None:
        """Find a message by its ID."""
        try:
            model = ContactMessageModel.objects.get(id=message_id)
            return self._to_entity(model)
        except ContactMessageModel.DoesNotExist:
            return None
    
    def find_all(self, include_read: bool = True) -> list[ContactMessage]:
        """Find all messages."""
        queryset = ContactMessageModel.objects.all()
        if not include_read:
            queryset = queryset.filter(is_read=False)
        return [self._to_entity(model) for model in queryset]
    
    def delete(self, message: ContactMessage) -> None:
        """Delete a contact message."""
        ContactMessageModel.objects.filter(id=message.id).delete()
    
    @staticmethod
    def _to_entity(model: ContactMessageModel) -> ContactMessage:
        """Map ORM model to domain entity."""
        return ContactMessage(
            id=model.id,
            name=PersonName(model.name),
            email=Email(model.email),
            message=model.message,
            created_at=model.created_at,
            is_read=model.is_read,
        )
