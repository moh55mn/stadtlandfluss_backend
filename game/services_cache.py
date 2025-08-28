from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from .models import Highscore, Category, Term, BASE_POINTS, UNIQUE_BONUS
from .utils import normalize_text, similarity, first_letter_upper
 
from .cache_store import (
    set_active_round, get_active_round, clear_active_round,
    set_submission, get_votes, add_vote, list_all_submissions_for_round,
    get_waiting_users, clear_waiting_users, set_last_result_for_user
)
 
ROUND_SECONDS = 60
SIMILARITY_THRESHOLD = 0.80
# BASE_POINTS / UNIQUE_BONUS kommen aus models.py
 
VOTE_WINDOW_SECONDS = 20  # Abstimmungsphase
 
# ---------- Runde starten ----------
 
def _random_letter():
    import random, string
    return random.choice(string.ascii_uppercase)
 
def start_new_round(participants: list[int], cat_ids: list[int]) -> dict:
    now = timezone.now()
    play_end = now + timedelta(seconds=ROUND_SECONDS)
    rnd = {
        "number": int(timezone.now().timestamp()),  # deine bestehende ID-Logik
        "letter": _random_letter(),
        "start": now.isoformat(),
        "phase": "playing",
        "phase_end": play_end.isoformat(),
        "participants": list(set(participants)),
        "categories": cat_ids,
    }
    set_active_round(rnd)
    clear_waiting_users()
    return rnd
 
# ---------- Auto-Matching & Submit (wie gehabt, nur set_submission mit phase_end) ----------
 
def auto_match(letter: str, cat: Category, text: str) -> tuple[bool, dict]:
    norm = normalize_text(text)
    if not norm:
        return False, {"normalized": norm, "similarity": 0.0, "matched_term_id": None}
    if first_letter_upper(text) != letter:
        return False, {"normalized": norm, "similarity": 0.0, "matched_term_id": None}
    candidates = Term.objects.filter(category=cat, value__istartswith=letter).only("id", "value")[:500]
    best_id, best_sim = None, 0.0
    for t in candidates:
        t_norm = normalize_text(t.value)
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
    if rnd["phase"] != "playing":
        raise ValueError("Submissions sind nur in der Spielphase erlaubt.")
    if user_id not in rnd["participants"]:
        raise PermissionError("Nicht Teilnehmer dieser Runde")
 
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
    set_submission(rnd["number"], user_id, category_id, payload, rnd["phase_end"])
    return payload
 
def vote_unknown(user_id: int, category_id: int, normalized: str, value: bool):
    rnd = get_active_round()
    if not rnd:
        raise ValueError("Keine aktive Runde")
    if rnd["phase"] != "voting":
        raise ValueError("Voting ist nur in der Abstimmungsphase erlaubt.")
    if user_id not in rnd["participants"]:
        raise PermissionError("Nur Teilnehmer dürfen abstimmen.")
    add_vote(rnd["number"], category_id, normalized, user_id, value, rnd["phase_end"])
    return {"ok": True}
 
# ---------- Finalisierung & Scoring ----------
 
@transaction.atomic
def _finalize_and_score_current_round(rnd: dict) -> dict:
    """
    Wird sowohl nach 'playing' (falls keine Unknowns) als auch nach 'voting' aufgerufen.
    Bewertet unknowns per Mehrheitsvotum, setzt Unique, vergibt Punkte, aktualisiert Highscore
    und speichert pro User das 'letzte Ergebnis' im Cache.
    """
    participants = rnd["participants"]
    cat_ids = rnd["categories"]
    subs = list_all_submissions_for_round(rnd["number"], participants, cat_ids)
 
    # 1) Unknowns per Votes bewerten
    for (u, c), s in subs.items():
        if not s["is_valid"] and not s.get("matched_term_id"):
            votes = get_votes(rnd["number"], c, s["normalized"])
            if votes:
                yes = sum(1 for v in votes.values() if v is True)
                no  = sum(1 for v in votes.values() if v is False)
                s["is_valid"] = yes > no
 
    # 2) Unique-Bonus
    groups = {}
    for (u, c), s in subs.items():
        if s.get("is_valid"):
            groups.setdefault((c, s["normalized"]), []).append((u, c))
    uniques = {pairs[0] for pairs in groups.values() if len(pairs) == 1}
    for key, s in subs.items():
        s["is_unique"] = key in uniques
 
    # 3) Punkte berechnen & Highscore kumulieren
    from django.db.models import F
    per_user_points = {}
    per_user_breakdown = {u: [] for u in participants}
 
    for (u, c), s in subs.items():
        if s.get("is_valid"):
            pts = BASE_POINTS + (UNIQUE_BONUS if s.get("is_unique") else 0)
            per_user_points[u] = per_user_points.get(u, 0) + pts
            per_user_breakdown[u].append({
                "category_id": c,
                "text": s.get("original"),
                "normalized": s.get("normalized"),
                "is_unique": s.get("is_unique", False),
                "points": pts
            })
 
    for user_id, pts in per_user_points.items():
        hs, _ = Highscore.objects.get_or_create(user_id=user_id, defaults={"total_points": 0})
        hs.total_points = F("total_points") + pts
        hs.save(update_fields=["total_points"])
 
    # 4) Last result pro User speichern
    for u in participants:
        set_last_result_for_user(u, {
            "round": rnd["number"],
            "gained_points": per_user_points.get(u, 0),
            "valid_count": sum(1 for (uu, _c), s in subs.items() if uu == u and s.get("is_valid")),
            "breakdown": per_user_breakdown.get(u, []),
        })
 
    return {"awarded": per_user_points, "round": rnd["number"]}
 
# ---------- Phasen-Logik ----------
 
def _phase_over(rnd: dict) -> bool:
    from datetime import datetime, timezone as py_tz
    end = datetime.fromisoformat(rnd["phase_end"])
    if end.tzinfo is None:
        end = end.replace(tzinfo=py_tz.utc)
    return timezone.now() >= end
 
def _unknowns_exist_for_round(rnd: dict) -> bool:
    # Unknowns = Submissions ohne matched_term_id und is_valid=False
    subs = list_all_submissions_for_round(rnd["number"], rnd["participants"], rnd["categories"])
    for s in subs.values():
        if not s.get("is_valid") and not s.get("matched_term_id"):
            return True
    return False
 
def ensure_round_progress():
    """
    State:
      playing & abgelaufen:
         - wenn Unknowns existieren -> phase=voting (phase_end jetzt + VOTE_WINDOW_SECONDS)
         - sonst finalisieren & evtl. neue Runde
      voting & abgelaufen:
         - finalisieren & evtl. neue Runde
      keine Runde:
         - falls Wartende: neue Runde
    """
    from .cache_store import get_waiting_users
    rnd = get_active_round()
    if not rnd:
        waiting = get_waiting_users()
        if waiting:
            cats = list(Category.objects.values_list("id", flat=True))
            return start_new_round(waiting, cats)
        return None
 
    if not _phase_over(rnd):
        return rnd
 
    # Phase beendet
    if rnd["phase"] == "playing":
        if _unknowns_exist_for_round(rnd):
            # in Voting wechseln
            vote_end = timezone.now() + timedelta(seconds=VOTE_WINDOW_SECONDS)
            rnd["phase"] = "voting"
            rnd["phase_end"] = vote_end.isoformat()
            set_active_round(rnd)
            return rnd
        else:
            # direkt finalisieren & ggf. neue Runde
            _finalize_and_score_current_round(rnd)
            return _start_next_round_after(rnd)
 
    if rnd["phase"] == "voting":
        _finalize_and_score_current_round(rnd)
        return _start_next_round_after(rnd)
 
    return rnd
 
def _start_next_round_after(prev_rnd: dict):
    from .cache_store import get_waiting_users
    participants_next = list(set(prev_rnd.get("participants", []) + get_waiting_users()))
    cats = list(Category.objects.values_list("id", flat=True))
    clear_active_round()
    if participants_next:
        return start_new_round(participants_next, cats)
    return None
