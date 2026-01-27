"""Contact message entity - the aggregate root for this context."""
from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID, uuid4

from apps.shared.domain.value_objects import Email, PersonName


@dataclass
class ContactMessage:
    """Aggregate root for contact messages.
    
    Represents a message submitted through the contact form.
    All business rules are enforced here.
    """
    id: UUID
    name: PersonName
    email: Email
    message: str
    created_at: datetime
    is_read: bool = False
    
    def __init__(
        self,
        name: PersonName,
        email: Email,
        message: str,
        id: UUID | None = None,
        created_at: datetime | None = None,
        is_read: bool = False,
    ) -> None:
        self.id = id or uuid4()
        self.name = name
        self.email = email
        self.message = self._validate_message(message)
        self.created_at = created_at or datetime.utcnow()
        self.is_read = is_read
    
    @staticmethod
    def _validate_message(message: str) -> str:
        """Validate message content."""
        message = message.strip()
        if len(message) < 10:
            raise ValueError("Message must be at least 10 characters")
        if len(message) > 5000:
            raise ValueError("Message must not exceed 5000 characters")
        return message
    
    def mark_as_read(self) -> None:
        """Mark this message as read."""
        self.is_read = True
    
    def mark_as_unread(self) -> None:
        """Mark this message as unread."""
        self.is_read = False
