from __future__ import annotations

from abc import ABC, abstractmethod


class FileStoragePort(ABC):
    @abstractmethod
    def upload(self, file_data: bytes, filename: str, content_type: str) -> str:
        """Upload file_data and return the storage path (key)."""

    @abstractmethod
    def get_url(self, storage_path: str) -> str:
        """Return a publicly accessible URL for the given storage path."""
