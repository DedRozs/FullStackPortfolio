from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import View


class IsStaffUser(BasePermission):
    """Allow access only to authenticated staff users."""

    def has_permission(self, request: Request, view: View) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
