from django.apps import AppConfig


class FactAdminConfig(AppConfig):
    """
    Configuration class for the FACT Admin application.
    
    This class configures the Django application for the FACT Admin module,
    which provides administrative functionality for managing the FACT event
    including:
    - Delegate management
    - Workshop scheduling
    - Location management
    - Registration flags
    - System notifications
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'fact_admin'
