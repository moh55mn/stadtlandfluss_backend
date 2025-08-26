from django.core.cache import cache
from datetime import datetime, timedelta, timezone
 
ROUND_SECONDS = 60
 
def now_utc():
    return datetime.now(timezone.utc)
 
def _round_timeout(end_dt):
    # Seconds remaining + Puffer, min. 60s
    remaining = int((end_dt - now_utc()).total_seconds())
    return max(60, remaining + 300)
 
def set_active_round(data: dict):
    # data = {"number": 42, "letter": "B", "start": iso, "end": iso, "participants": [1,2]}
    end_dt = datetime.fromisoformat(data["end"])
    cache.set("round:active", data, timeout=_round_timeout(end_dt))
 
def get_active_round() -> dict | None:
    return cache.get("round:active")
 
def clear_active_round():
    cache.delete("round:active")
 
def sub_key(round_no: int, user_id: int, cat_id: int) -> str:
    return f"round:{round_no}:sub:{user_id}:{cat_id}"
 
def set_submission(round_no: int, user_id: int, cat_id: int, payload: dict, end_iso: str):
    end_dt = datetime.fromisoformat(end_iso)
    cache.set(sub_key(round_no, user_id, cat_id), payload, timeout=_round_timeout(end_dt))
 
def get_submission(round_no: int, user_id: int, cat_id: int) -> dict | None:
    return cache.get(sub_key(round_no, user_id, cat_id))
 
def vote_key(round_no: int, cat_id: int, normalized: str) -> str:
    return f"round:{round_no}:votes:{cat_id}:{normalized}"
 
def add_vote(round_no: int, cat_id: int, normalized: str, user_id: int, value: bool, end_iso: str):
    end_dt = datetime.fromisoformat(end_iso)
    key = vote_key(round_no, cat_id, normalized)
    votes = cache.get(key) or {}
    votes[str(user_id)] = bool(value)
    cache.set(key, votes, timeout=_round_timeout(end_dt))
 
def get_votes(round_no: int, cat_id: int, normalized: str) -> dict:
    return cache.get(vote_key(round_no, cat_id, normalized)) or {}
 
def list_all_submissions_for_round(round_no: int, participants: list[int], cat_ids: list[int]) -> dict[tuple,int|int, dict]:
    # einfaches Scan-Pattern (schlank, da 5–6 Spieler)
    result = {}
    for u in participants:
        for c in cat_ids:
            s = get_submission(round_no, u, c)
            if s:
                result[(u, c)] = s
    return result
