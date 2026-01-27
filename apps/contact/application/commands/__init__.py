"""Commands for the Contact bounded context.

Commands represent intentions to change state.
They are handled by the application service.
"""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class CreateContactMessageCommand:
    """Command to create a new contact message."""
    name: str
    email: str
    message: str


@dataclass(frozen=True)
class MarkMessageAsReadCommand:
    """Command to mark a message as read."""
    message_id: UUID


@dataclass(frozen=True)
class DeleteMessageCommand:
    """Command to delete a message."""
    message_id: UUID
