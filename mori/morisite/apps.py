from django.apps import AppConfig


class MorisiteConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "morisite"

    def ready(self):
        import morisite.signals