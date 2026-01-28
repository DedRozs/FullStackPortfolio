"""Django app configuration for the Trading bounded context."""
from django.apps import AppConfig


class TradingConfig(AppConfig):
    """Configuration for the Trading app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.trading'
    label = 'trading'
    verbose_name = 'Trading Blog'
    
    def ready(self) -> None:
        """Import models when the app is ready.
        
        This ensures Django discovers models in the infrastructure layer.
        """
        # Import models so Django can discover them for migrations
        from apps.trading.infrastructure import models  # noqa: F401
