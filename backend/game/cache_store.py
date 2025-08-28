from django.core.cache import cache
from datetime import datetime, timedelta, timezone
 
ROUND_SECONDS = 60
VOTE_WINDOW_SECONDS = 20  # Dauer der Voting-Phase (Sekunden)
 
# Keys
ACTIVE_ROUND_KEY = "round:active"
WAITING_USERS_KEY = "round:waiting_users"
LAST_RESULT_USER_KEY = "round:last_result:{uid}"
 
def now_utc():
    return datetime.now(timezone.utc)
 
def _timeout_until(dt: datetime) -> int:
    # seconds until dt + Puffer (min 60s)
    remaining = int((dt - now_utc()).total_seconds())
    return max(60, remaining + 300)
 
# ---------- Active Round ----------
 
def set_active_round(data: dict):
    """
    data enthält jetzt:
      - number, letter
      - start (iso)
      - phase: "playing" | "voting"
      - phase_end (iso)
      - participants: [user_ids]
      - categories: [cat_ids]
    """
    phase_end = datetime.fromisoformat(data["phase_end"])
    cache.set(ACTIVE_ROUND_KEY, data, timeout=_timeout_until(phase_end))
 
def get_active_round() -> dict | None:
    return cache.get(ACTIVE_ROUND_KEY)
 
def clear_active_round():
    cache.delete(ACTIVE_ROUND_KEY)
 
# ---------- Waiting Queue ----------
 
def get_waiting_users() -> list[int]:
    return cache.get(WAITING_USERS_KEY) or []
 
def add_waiting_user(user_id: int) -> None:
    users = get_waiting_users()
    if user_id not in users:
        users.append(user_id)
        cache.set(WAITING_USERS_KEY, users, None)
 
def clear_waiting_users():
    cache.delete(WAITING_USERS_KEY)
 
# ---------- Submissions / Votes (unverändert) ----------
 
def sub_key(round_no: int, user_id: int, cat_id: int) -> str:
    return f"round:{round_no}:sub:{user_id}:{cat_id}"
 
def set_submission(round_no: int, user_id: int, cat_id: int, payload: dict, phase_end_iso: str):
    end_dt = datetime.fromisoformat(phase_end_iso)
    cache.set(sub_key(round_no, user_id, cat_id), payload, timeout=_timeout_until(end_dt))
 
def get_submission(round_no: int, user_id: int, cat_id: int) -> dict | None:
    return cache.get(sub_key(round_no, user_id, cat_id))
 
def vote_key(round_no: int, cat_id: int, normalized: str) -> str:
    return f"round:{round_no}:votes:{cat_id}:{normalized}"
 
def add_vote(round_no: int, cat_id: int, normalized: str, user_id: int, value: bool, phase_end_iso: str):
    end_dt = datetime.fromisoformat(phase_end_iso)
    key = vote_key(round_no, cat_id, normalized)
    votes = cache.get(key) or {}
    votes[str(user_id)] = bool(value)
    cache.set(key, votes, timeout=_timeout_until(end_dt))
 
def get_votes(round_no: int, cat_id: int, normalized: str) -> dict:
    return cache.get(vote_key(round_no, cat_id, normalized)) or {}
 
def list_all_submissions_for_round(round_no: int, participants: list[int], cat_ids: list[int]) -> dict[tuple[int,int], dict]:
    result = {}
    for u in participants:
        for c in cat_ids:
            s = get_submission(round_no, u, c)
            if s:
                result[(u, c)] = s
    return result
 
# ---------- Last Result per User ----------
 
def set_last_result_for_user(user_id: int, payload: dict) -> None:
    cache.set(LAST_RESULT_USER_KEY.format(uid=user_id), payload, None)
 
def get_last_result_for_user(user_id: int) -> dict | None:
    return cache.get(LAST_RESULT_USER_KEY.format(uid=user_id))
