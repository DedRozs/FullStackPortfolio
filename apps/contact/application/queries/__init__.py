"""Queries for the Contact bounded context.

Queries represent read-only data retrieval.
"""
from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class GetMessageByIdQuery:
    """Query to get a specific message."""
    message_id: UUID


@dataclass(frozen=True)
class GetAllMessagesQuery:
    """Query to get all messages."""
    include_read: bool = True
