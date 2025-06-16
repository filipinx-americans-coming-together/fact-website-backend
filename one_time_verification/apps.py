from django.apps import AppConfig


class OneTimeVerificationConfig(AppConfig):
    """
    Email verification system using one-time codes.
    Handles code generation, email delivery, and verification.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'one_time_verification'
