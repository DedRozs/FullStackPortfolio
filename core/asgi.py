"""
ASGI config for core project.

HTTP requests are handled by Django's standard ASGI application.
WebSocket connections are routed through Django Channels.
Add WebSocket URL patterns to the `websocket_urlpatterns` list.
"""

import os

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Must be called before any other Django imports that trigger app loading.
django_asgi_app = get_asgi_application()

# Register WebSocket URL patterns here as features are built.
websocket_urlpatterns: list = []

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
