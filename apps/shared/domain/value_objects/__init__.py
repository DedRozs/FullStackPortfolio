"""Shared value objects used across bounded contexts."""
from dataclasses import dataclass
import re


@dataclass(frozen=True)
class Email:
    """Email address value object with validation.
    
    Value objects are immutable and defined by their attributes.
    Two Email objects with the same address are considered equal.
    """
    address: str
    
    def __post_init__(self) -> None:
        if not self._is_valid_email(self.address):
            raise ValueError(f"Invalid email address: {self.address}")
    
    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Basic email validation."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    def __str__(self) -> str:
        return self.address


@dataclass(frozen=True)
class PersonName:
    """Person name value object.
    
    Encapsulates name validation and formatting.
    """
    value: str
    
    def __post_init__(self) -> None:
        if not self.value or len(self.value.strip()) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(self.value) > 100:
            raise ValueError("Name must not exceed 100 characters")
    
    def __str__(self) -> str:
        return self.value.strip()
