from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
 
from accounts.permissions import IsAdminRole
from .models import Category, Term, Highscore, BASE_POINTS
from .serializers import (
    CategorySerializer, TermSerializer,
    SubmissionWriteSerializer,
    HighscoreSerializer, CurrentRoundDictSerializer, UnknownTermListItemSerializer
)
 
# >>> Cache-basierte Services/Utils importieren
from .services_cache import (
    start_new_round, submit as cache_submit, vote_unknown as cache_vote_unknown,
    finalize_and_score as cache_finalize_and_score
)
from .cache_store import (
    get_active_round, set_active_round, list_all_submissions_for_round, get_votes
)
 
# =========================
# Admin: Kategorien
# =========================
 
class CategoryListCreateView(ListCreateAPIView):
    """
    GET: alle sichtbar (öffentlich)
    POST: nur Admin
    """
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer
 
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdminRole()]
        return [AllowAny()]
 
class CategoryDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
 
    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsAuthenticated(), IsAdminRole()]
        return [AllowAny()]
 
# =========================
# Admin: Terms (komplett Admin-only)
# =========================
 
class TermListCreateView(ListCreateAPIView):
    serializer_class = TermSerializer
    permission_classes = [IsAdminRole]
 
    def get_queryset(self):
        qs = Term.objects.select_related("category").order_by("category__name", "value")
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category_id=category)
        letter = self.request.query_params.get("letter")
        if letter:
            qs = qs.filter(first_letter=letter.upper())
        return qs
 
    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx
 
class TermDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Term.objects.select_related("category")
    serializer_class = TermSerializer
    permission_classes = [IsAdminRole]
 
    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["request"] = self.request
        return ctx
 
# =========================
# Spiel-Endpoints (Cache)
# =========================
 
class JoinView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        rnd = get_active_round()
        if not rnd:
            # neue Runde erstellen mit aktuellem User als erstem Teilnehmer
            participants = [request.user.id]
            cats = list(Category.objects.values_list("id", flat=True))
            rnd = start_new_round(participants, cats)
        else:
            # User zur Teilnehmerliste hinzufügen (und Runde zurück in Cache schreiben)
            if request.user.id not in rnd["participants"]:
                rnd["participants"].append(request.user.id)
                set_active_round(rnd)
        return Response(rnd, status=200)
 
class CurrentRoundView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        active = get_active_round()
        if not active:
            return Response(status=status.HTTP_204_NO_CONTENT)
        ser = CurrentRoundDictSerializer(active, context={"request": request})
        return Response(ser.data, status=200)
 
class SubmitView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        # Erwartet: { "category_id": int, "text": str }
        data = request.data
        if "category_id" not in data or "text" not in data:
            return Response({"detail": "category_id und text sind erforderlich."}, status=400)
        out = cache_submit(request.user.id, int(data["category_id"]), str(data["text"]))
        return Response(out, status=201)
 
class VoteView(APIView):
    permission_classes = [IsAuthenticated]
 
    def post(self, request):
        # Erwartet: { "category_id": int, "normalized": str, "value": bool }
        d = request.data
        for f in ("category_id", "normalized", "value"):
            if f not in d:
                return Response({"detail": f"Feld '{f}' fehlt."}, status=400)
        res = cache_vote_unknown(request.user.id, int(d["category_id"]), str(d["normalized"]), bool(d["value"]))
        return Response(res, status=201)
 
class UnknownTermsListView(APIView):
    permission_classes = [IsAuthenticated]
 
    def get(self, request):
        active = get_active_round()
        if not active:
            return Response({"detail": "Keine aktive Runde."}, status=400)
 
        if request.user.id not in active["participants"]:
            return Response({"detail": "Du bist in dieser Runde kein Teilnehmer."}, status=403)
 
        cat_ids = active.get("categories", [])
        subs = list_all_submissions_for_round(active["number"], active["participants"], cat_ids)
 
        unknown_items = []
        for (user_id, cat_id), s in subs.items():
            if not s.get("is_valid") and not s.get("matched_term_id"):
                normalized = s.get("normalized") or ""
                votes = get_votes(active["number"], cat_id, normalized)
                approvals = sum(1 for v in votes.values() if v is True)
                rejections = sum(1 for v in votes.values() if v is False)
                unknown_items.append({
                    "id": f"{active['number']}:{cat_id}:{normalized}",
                    "normalized_text": normalized,
                    "category": {"id": cat_id},   # Name optional (kannst du später ergänzen)
                    "approvals": approvals,
                    "rejections": rejections,
                    "round": active["number"],
                })
 
        ser = UnknownTermListItemSerializer(unknown_items, many=True)
        return Response(ser.data, status=200)
 
class ScoreboardView(APIView):
    """
    Highscores: aus DB (persistent)
    Live: aus Cache-Submissions (gültige zählen × BASE_POINTS; ohne Unique-Bonus).
    """
    permission_classes = [AllowAny]
 
    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
 
        # Globales Highscore (DB)
        highs = Highscore.objects.select_related("user").order_by("-total_points")[:limit]
        highs_ser = HighscoreSerializer(highs, many=True).data
 
        # Live
        live = []
        active = get_active_round()
        if active:
            cat_ids = active.get("categories", [])
            subs = list_all_submissions_for_round(active["number"], active["participants"], cat_ids)
            # Zähle pro User gültige Submissions
            valid_counts = {}
            for (u, _c), s in subs.items():
                if s.get("is_valid"):
                    valid_counts[u] = valid_counts.get(u, 0) + 1
            for u, cnt in valid_counts.items():
                live.append({
                    "user": {"id": u},  # optional Username nachladen, wenn nötig
                    "valid_count": cnt,
                    "points_estimate": cnt * BASE_POINTS,
                })
            live.sort(key=lambda x: x["points_estimate"], reverse=True)
 
        return Response({"highscores": highs_ser, "live": live}, status=200)
 
class ForceNewRoundView(APIView):
    """
    Finalisiert aktuelle Runde (aus Cache) und kumuliert Punkte in DB.
    """
    permission_classes = [IsAdminRole]
 
    @transaction.atomic
    def post(self, request):
        res = cache_finalize_and_score()
        return Response(res, status=201)
