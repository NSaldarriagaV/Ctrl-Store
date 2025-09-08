from django.apps import AppConfig

class AnalyticsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ctrlstore.apps.analytics"

    def ready(self):
        # Registra signals
        from . import receivers  # noqa: F401
