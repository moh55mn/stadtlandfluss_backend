# game/apps.py
from django.apps import AppConfig

class GameConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "game"

    def ready(self):
        # Registriert post_migrate-Signal, um Default-Kategorien zu erstellen
        from . import signals  # noqa

