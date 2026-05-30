from __future__ import annotations

import re
import uuid

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from apps.client_portal.application.ports import FileStoragePort

_SAFE_FILENAME_RE = re.compile(r'[^\w\s\-.]')


def _sanitize_filename(name: str) -> str:
    """Strip path components and remove characters outside word chars, spaces, hyphens, dots."""
    basename = name.replace('\\', '/').split('/')[-1]
    sanitized = _SAFE_FILENAME_RE.sub('_', basename)
    return sanitized[:200] or 'upload'


class GCSFileStorageAdapter(FileStoragePort):
    """Implements FileStoragePort using Django's default_storage backend.

    In production this resolves to GoogleCloudStorage (via django-storages).
    In development/tests it resolves to the local filesystem storage.
    """

    def upload(self, file_data: bytes, filename: str, content_type: str) -> str:
        safe_name = _sanitize_filename(filename)
        unique_key = f'client_portal/{uuid.uuid4().hex}/{safe_name}'
        content = ContentFile(file_data, name=unique_key)
        saved_path = default_storage.save(unique_key, content)
        return saved_path

    def get_url(self, storage_path: str) -> str:
        return default_storage.url(storage_path)
