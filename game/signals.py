# game/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver

DEFAULT_CATEGORIES = ["Stadt", "Land", "Fluss", "Tier"]

@receiver(post_migrate)
def ensure_default_categories(sender, **kwargs):
    """
    Stellt sicher, dass die Pflicht-Kategorien in der DB vorhanden sind.
    Läuft nach jeder Migration in jedem App-Context – daher defensiv implementieren.
    """
    from .models import Category  # Import hier, damit Apps geladen sind
    try:
        for name in DEFAULT_CATEGORIES:
            Category.objects.get_or_create(name=name)
    except Exception:
        # still & safe: bei Migrationen/Tests nicht hart fehlschlagen
        pass
