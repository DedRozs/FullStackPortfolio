from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class ProjectStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    COMPLETE = "COMPLETE"
    ARCHIVED = "ARCHIVED"


class MilestoneStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"


class ApprovalStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVISION_REQUESTED = "REVISION_REQUESTED"


class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"


class StakeholderRole(str, Enum):
    CLIENT = "CLIENT"
    STAFF = "STAFF"
    ADMIN = "ADMIN"


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        if self.amount < Decimal("0"):
            raise ValueError("Money.amount must be >= 0")
        if len(self.currency) != 3 or not self.currency.isalpha():
            raise ValueError("Money.currency must be a 3-letter ISO 4217 code")


@dataclass(frozen=True)
class FileMetadata:
    content_type: str
    size_bytes: int
    storage_key: str

    def __post_init__(self) -> None:
        if not self.content_type:
            raise ValueError("FileMetadata.content_type must not be blank")
        if self.size_bytes <= 0:
            raise ValueError("FileMetadata.size_bytes must be a positive integer")
        if not self.storage_key:
            raise ValueError("FileMetadata.storage_key must not be blank")


@dataclass(frozen=True)
class VersionNumber:
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise ValueError("VersionNumber.value must be >= 1")
