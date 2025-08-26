from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from .models import Highscore, Category, Term
from .utils import normalize_text, similarity, first_letter_upper
from .cache_store import set_active_round, get_active_round, clear_active_round, set_submission, get_votes, add_vote, list_all_submissions_for_round
 
ROUND_SECONDS = 60
SIMILARITY_THRESHOLD = 0.80
BASE_POINTS = 10
UNIQUE_BONUS = 5
 
def start_new_round(participants: list[int], cat_ids: list[int]) -> dict:
    # Buchstabe ziehen
    import random, string
    letter = random.choice(string.ascii_uppercase)
    now = timezone.now()
    end = now + timedelta(seconds=ROUND_SECONDS)
    rnd = {
        "number": int(timezone.now().timestamp()),  # einfache laufende ID; oder DB-Counter
        "letter": letter,
        "start": now.isoformat(),
        "end": end.isoformat(),
        "participants": participants,
        "categories": cat_ids,
    }
    set_active_round(rnd)
    return rnd
 
def auto_match(letter: str, cat: Category, text: str) -> tuple[bool, dict]:
    norm = normalize_text(text)
    if not norm:
        return False, {"normalized": norm, "similarity": 0.0, "matched_term_id": None}
 
    # Buchstaben der Runde strikt prüfen (Regel des Spiels)
    if first_letter_upper(text) != letter:
        return False, {"normalized": norm, "similarity": 0.0, "matched_term_id": None}
 
    # Kandidaten: alle Terms der Kategorie, die mit dem Buchstaben anfangen (per DB)
    candidates = Term.objects.filter(category=cat, value__istartswith=letter).only("id", "value")[:500]
 
    best_id, best_sim = None, 0.0
    for t in candidates:
        t_norm = normalize_text(t.value)              # on-the-fly statt normalized_value-Feld
        sim = similarity(norm, t_norm)
        if sim > best_sim:
            best_sim, best_id = sim, t.id
 
    if best_id and best_sim >= SIMILARITY_THRESHOLD:
        return True, {"normalized": norm, "similarity": best_sim, "matched_term_id": best_id}
 
    return False, {"normalized": norm, "similarity": best_sim, "matched_term_id": None}
 
def submit(user_id: int, category_id: int, text: str):
    rnd = get_active_round()
    if not rnd:
        raise ValueError("Keine aktive Runde")
    if user_id not in rnd["participants"]:
        raise PermissionError("Nicht Teilnehmer dieser Runde")
 
    from .models import Category
    cat = Category.objects.get(id=category_id)
 
    ok, info = auto_match(rnd["letter"], cat, text)
    payload = {
        "original": text,
        "normalized": info["normalized"],
        "normalized_text": info["normalized"],
        "matched_term_id": info["matched_term_id"],
        "similarity": info["similarity"],
        "is_valid": bool(ok),
        "is_unique": False,  # wird bei Finalisierung gesetzt
    }
    set_submission(rnd["number"], user_id, category_id, payload, rnd["end"])
    return payload
 
def vote_unknown(user_id: int, category_id: int, normalized: str, value: bool):
    rnd = get_active_round()
    if not rnd:
        raise ValueError("Keine aktive Runde")
    if user_id not in rnd["participants"]:
        raise PermissionError("Nicht Teilnehmer")
    add_vote(rnd["number"], category_id, normalized, user_id, value, rnd["end"])
    return {"ok": True}
 
@transaction.atomic
def finalize_and_score():
    rnd = get_active_round()
    if not rnd:
        return {"detail": "keine aktive Runde"}
 
    # Zeit abgelaufen?
    from datetime import datetime
    if timezone.now() < datetime.fromisoformat(rnd["end"]):
        # Optional: frühzeitiges Finalisieren erlauben
        pass
 
    participants = rnd["participants"]
    cat_ids = rnd["categories"]
    subs = list_all_submissions_for_round(rnd["number"], participants, cat_ids)
 
    # 1) unbekannte Begriffe als gültig/ungültig markieren (per Mehrheitsvotum)
    #    Hier: simple Regel – wenn es kein matched_term_id gibt, prüfe Votes
    approvals = {}
    for (u, c), s in subs.items():
        if not s["is_valid"]:  # d. h. unknown
            votes = get_votes(rnd["number"], c, s["normalized"])
            if votes:
                yes = sum(1 for v in votes.values() if v is True)
                no  = sum(1 for v in votes.values() if v is False)
                s["is_valid"] = yes > no
 
    # 2) uniqueness pro (category_id, normalized)
    groups = {}
    for (u, c), s in subs.items():
        if s["is_valid"]:
            groups.setdefault((c, s["normalized"]), []).append((u, c))
    uniques = {pairs[0] for pairs in groups.values() if len(pairs) == 1}
    for key, s in subs.items():
        s["is_unique"] = key in uniques
 
    # 3) Punkte vergeben & in DB (Highscore) kumulieren
    points = {}
    for (u, _c), s in subs.items():
        if s["is_valid"]:
            pts = BASE_POINTS + (UNIQUE_BONUS if s["is_unique"] else 0)
            points[u] = points.get(u, 0) + pts
 
    for user_id, pts in points.items():
        hs, _ = Highscore.objects.get_or_create(user_id=user_id, defaults={"total_points": 0})
        # F()-Update für Race-Safety
        from django.db.models import F
        hs.total_points = F("total_points") + pts
        hs.save(update_fields=["total_points"])
 
    # 4) Runde aufräumen
    clear_active_round()
    return {"awarded": points, "round": rnd["number"]}
