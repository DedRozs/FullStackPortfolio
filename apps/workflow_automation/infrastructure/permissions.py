from __future__ import annotations

from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsStaffUser(BasePermission):
    """Only authenticated staff users may access workflow automation."""

    message = 'Only staff users can access workflow automation.'

    def has_permission(self, request: Request, view: APIView) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)
