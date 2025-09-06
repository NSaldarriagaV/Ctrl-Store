from django.apps import AppConfig


class AuthxConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ctrlstore.apps.authx"
    label = "authx"

    def ready(self):
        """Importa los signals cuando la app está lista."""
        import ctrlstore.apps.authx.signals
