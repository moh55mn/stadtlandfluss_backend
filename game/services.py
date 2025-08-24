from django.utils import timezone
from .models import Round, WaitingPlayer

def finalize_if_expired(latest_round: Round | None) -> Round | None:
    if latest_round and not latest_round.is_finalized and timezone.now() >= latest_round.end_time:
        latest_round.finalize()
    return latest_round

def get_active_round() -> Round | None:
    latest = Round.objects.order_by("-number").first()
    finalize_if_expired(latest)
    if latest and latest.is_active:
        return latest
    return None

def ensure_active_round(start_if_waiting: bool = True) -> Round | None:
    """
    Finalisiert abgelaufene Runde. Falls keine aktive Runde existiert:
    - Wenn Spieler warten und start_if_waiting=True → starte neue Runde.
    - Andernfalls: gib None zurück.
    """
    latest = Round.objects.order_by("-number").first()
    finalize_if_expired(latest)

    # Gibt es nach Finalisierung eine aktive Runde?
    active = get_active_round()
    if active:
        return active

    if start_if_waiting and WaitingPlayer.objects.exists():
        # Startet neue Runde (importiert waiting players)
        return Round.start_new()

    # Optional: erste Runde starten, selbst wenn (noch) niemand wartet?
    # -> Wir warten, bis mindestens ein Spieler beitreten möchte.
    return None
