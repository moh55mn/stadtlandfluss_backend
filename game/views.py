from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.utils import timezone
 
from accounts.permissions import IsAdminRole
from .models import Category, Term, Highscore, BASE_POINTS
from .serializers import (
    CategorySerializer, TermSerializer,
    SubmissionWriteSerializer,
    HighscoreSerializer, CurrentRoundDictSerializer, UnknownTermListItemSerializer
)
 
# Services
from .services_cache import (
    start_new_round, submit as cache_submit, vote_unknown as cache_vote_unknown,
    ensure_round_progress
)
from .cache_store import (
    get_active_round, set_active_round, list_all_submissions_for_round, get_votes,
    add_waiting_user, get_waiting_users, get_last_result_for_user
)
 
# --------- Join: bei aktiver Runde warten ----------
class JoinView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        user_id = request.user.id
 
        # Fortschritt/Phase aktualisieren (kann neue Runde starten, falls alte zu Ende etc.)
        rnd = ensure_round_progress()
 
        if not rnd:
            # keine aktive Runde -> sofort starten mit diesem Spieler
            cats = list(Category.objects.values_list("id", flat=True))
            new_rnd = start_new_round([user_id], cats)
            return Response(new_rnd, status=200)
 
        # aktive Runde (playing oder voting) -> NICHT hinzufügen, sondern in Warteschlange
        add_waiting_user(user_id)
        return Response({
            "detail": "Du bist in der Warteschlange und spielst in der nächsten Runde mit.",
            "current_round": {
                "number": rnd["number"],
                "letter": rnd["letter"],
                "phase": rnd["phase"],
                "phase_end": rnd["phase_end"],
            },
            "waiting_count": len(get_waiting_users())
        }, status=202)
 
# --------- Current: liefert Phase + Restzeit, triggert State Machine ----------
class CurrentRoundView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        rnd = ensure_round_progress()
        if not rnd:
            return Response(status=status.HTTP_204_NO_CONTENT)
 
        # remaining_seconds aus phase_end berechnen
        from datetime import datetime, timezone as py_tz
        try:
            end_dt = datetime.fromisoformat(rnd["phase_end"])
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=py_tz.utc)
            remaining = int((end_dt - timezone.now()).total_seconds())
            remaining = max(0, remaining)
        except Exception:
            remaining = None
 
        data = {
            **rnd,
            "remaining_seconds": remaining,
            "i_am_participant": request.user.id in rnd.get("participants", []),
        }
        return Response(data, status=200)
 
# --------- Submit bleibt, aber nur in 'playing' erlaubt (Services prüft das) ----------
class SubmitView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        data = request.data
        if "category_id" not in data or "text" not in data:
            return Response({"detail":"category_id und text sind erforderlich."}, status=400)
        out = cache_submit(request.user.id, int(data["category_id"]), str(data["text"]))
        return Response(out, status=201)
 
# --------- Unknowns nur in Voting-Phase (einmal laden zu Beginn) ----------
class UnknownTermsListView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        rnd = ensure_round_progress()
        if not rnd:
            return Response({"detail": "Keine aktive Runde."}, status=400)
        if rnd["phase"] != "voting":
            return Response({"detail": "Abstimmungen sind nur in der Voting-Phase möglich."}, status=400)
        if request.user.id not in rnd.get("participants", []):
            return Response({"detail": "Nur Teilnehmer der letzten Runde dürfen abstimmen."}, status=403)
 
        cat_ids = rnd.get("categories", [])
        subs = list_all_submissions_for_round(rnd["number"], rnd["participants"], cat_ids)
 
        unknown_items = []
        for (user_id, cat_id), s in subs.items():
            if not s.get("is_valid") and not s.get("matched_term_id"):
                normalized = s.get("normalized") or ""
                votes = get_votes(rnd["number"], cat_id, normalized)
                approvals = sum(1 for v in votes.values() if v is True)
                rejections = sum(1 for v in votes.values() if v is False)
                unknown_items.append({
                    "id": f"{rnd['number']}:{cat_id}:{normalized}",
                    "normalized_text": normalized,
                    "category": {"id": cat_id},
                    "approvals": approvals,
                    "rejections": rejections,
                    "round": rnd["number"],
                })
 
        ser = UnknownTermListItemSerializer(unknown_items, many=True)
        return Response(ser.data, status=200)
 
# --------- Vote nur in Voting-Phase ----------
class VoteView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        rnd = get_active_round()
        if not rnd or rnd["phase"] != "voting":
            return Response({"detail": "Derzeit keine Voting-Phase."}, status=400)
        d = request.data
        for f in ("category_id", "normalized", "value"):
            if f not in d:
                return Response({"detail": f"Feld '{f}' fehlt."}, status=400)
        res = cache_vote_unknown(request.user.id, int(d["category_id"]), str(d["normalized"]), bool(d["value"]))
        return Response(res, status=201)
 
# --------- Highscore (wie gehabt) ----------
class ScoreboardView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        highs = Highscore.objects.select_related("user").order_by("-total_points")[:limit]
        highs_ser = HighscoreSerializer(highs, many=True).data
 
        live = []
        active = get_active_round()
        if active and active["phase"] == "playing":
            cat_ids = active.get("categories", [])
            subs = list_all_submissions_for_round(active["number"], active["participants"], cat_ids)
            valid_counts = {}
            for (u, _c), s in subs.items():
                if s.get("is_valid"):
                    valid_counts[u] = valid_counts.get(u, 0) + 1
            for u, cnt in valid_counts.items():
                live.append({
                    "user": {"id": u},
                    "valid_count": cnt,
                    "points_estimate": cnt * BASE_POINTS,
                })
            live.sort(key=lambda x: x["points_estimate"], reverse=True)
 
        return Response({"highscores": highs_ser}, status=200)
 
# --------- Letztes Ergebnis je Spieler ----------
class MyTotalScoreView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        total = Highscore.objects.filter(user=request.user).values_list("total_points", flat=True).first() or 0
        return Response({"user": {"id": request.user.id, "username": request.user.username}, "total_points": total}, status=200)
 
class MyLastResultView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data = get_last_result_for_user(request.user.id)
        if not data:
            return Response({"detail": "Kein Rundenergebnis vorhanden."}, status=status.HTTP_204_NO_CONTENT)
        return Response(data, status=200)
