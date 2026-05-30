from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response

_DEMO_DETAIL = (
    'Demo accounts are read-only. This action is disabled for demo purposes.'
)


def is_demo_user(request) -> bool:
    """Return True when the authenticated user has is_demo=True on their UserProfile."""
    try:
        from apps.client_portal.models import UserProfile
        return UserProfile.objects.filter(user=request.user, is_demo=True).exists()
    except Exception:
        return False


class DemoReadOnlyMixin:
    """
    Mixin that blocks create / update / partial_update / destroy for accounts
    where UserProfile.is_demo is True.

    Apply to any ModelViewSet (or compatible viewset) to protect standard CRUD
    operations automatically.  For custom @action methods that mutate state, call
    self._demo_block() explicitly at the top of the handler and return early if
    it is not None.
    """

    def _demo_block(self) -> Response | None:
        if is_demo_user(self.request):
            return Response({'detail': _DEMO_DETAIL}, status=status.HTTP_403_FORBIDDEN)
        return None

    def create(self, request, *args, **kwargs):
        block = self._demo_block()
        if block is not None:
            return block
        parent = super()
        if not hasattr(parent, 'create'):
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return parent.create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        block = self._demo_block()
        if block is not None:
            return block
        parent = super()
        if not hasattr(parent, 'update'):
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return parent.update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        block = self._demo_block()
        if block is not None:
            return block
        parent = super()
        if not hasattr(parent, 'partial_update'):
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return parent.partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        block = self._demo_block()
        if block is not None:
            return block
        parent = super()
        if not hasattr(parent, 'destroy'):
            return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)
        return parent.destroy(request, *args, **kwargs)
