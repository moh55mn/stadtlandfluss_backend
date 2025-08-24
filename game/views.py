from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db import transaction

from .models import (
    Category, Term, Round, Submission, UnknownTerm, Vote, WaitingPlayer, RoundParticipant, BASE_POINTS
)
from .serializers import (
    CategorySerializer, TermSerializer, CurrentRoundSerializer,
    SubmissionWriteSerializer, SubmissionReadSerializer,
    VoteWriteSerializer, UnknownTermSerializer, HighscoreSerializer
)
from .services import ensure_active_round, get_active_round
from .permissions import IsAdminRole


# ---- Admin: Kategorien ----

class CategoryListCreateView(ListCreateAPIView):
    """
    GET: alle sichtbar (für alle)
    POST: nur Admin
    """
    queryset = Category.objects.all().order_by("name")
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdminRoleOrStaff()]
        return [AllowAny()]


class CategoryDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method in ("PUT", "PATCH", "DELETE"):
            return [IsAuthenticated(), IsAdminRoleOrStaff()]
        return [AllowAny()]


# ---- Admin: Terms ----

# game/views.py
from accounts.permissions import IsAdminRole

class TermListCreateView(ListCreateAPIView):
    """
    Komplett Admin-only (inkl. GET), um die Begriffe nicht öffentlich zu leaken.
    Nur Admins dürfen neue Begriffe anlegen.
    """
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



# ---- Spiel-Endpoints ----

class JoinView(APIView):
    """
    Setzt den User auf die Warteliste. Wenn keine aktive Runde läuft,
    startet sofort eine neue Runde und liefert sie zurück.
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user

        # Ist der User bereits Teilnehmer der aktiven Runde?
        active = get_active_round()
        if active and RoundParticipant.objects.filter(round=active, user=user).exists():
            # Bereits drin → gib aktuelle Runde zurück
            data = CurrentRoundSerializer(active, context={"request": request}).data
            return Response(data, status=status.HTTP_200_OK)

        # Warteliste setzen (OneToOne → get_or_create)
        WaitingPlayer.objects.get_or_create(user=user)

        # Sicherstellen, dass (falls keine Runde aktiv) eine gestartet wird
        active = ensure_active_round(start_if_waiting=True)

        if not active:
            # sollte praktisch nicht eintreten, aber zur Sicherheit
            return Response({"detail": "Du wurdest in die Warteschlange aufgenommen."}, status=202)

        data = CurrentRoundSerializer(active, context={"request": request}).data
        return Response(data, status=status.HTTP_200_OK)


class CurrentRoundView(APIView):
    """
    Liefert die aktuelle Runde; finalisiert im Hintergrund abgelaufene Runden
    und startet ggf. eine neue, wenn Spieler warten.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active = ensure_active_round(start_if_waiting=True)
        if not active:
            return Response(status=status.HTTP_204_NO_CONTENT)
        ser = CurrentRoundSerializer(active, context={"request": request})
        return Response(ser.data)


class SubmitView(APIView):
    """
    Nimmt eine Eingabe je Kategorie an. Upsert-Logik:
    - existiert Submission -> überschreiben (solange Runde aktiv)
    - sonst neu erstellen (Auto-Matching)
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        active = get_active_round()
        if not active:
            return Response({"detail": "Keine aktive Runde."}, status=status.HTTP_400_BAD_REQUEST)
        if not RoundParticipant.objects.filter(round=active, user=user).exists():
            return Response({"detail": "Du bist in dieser Runde kein Teilnehmer (ab nächster Runde dabei)."}, status=403)

        serializer = SubmissionWriteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category_id = serializer.validated_data["category_id"]
        text = serializer.validated_data["text"]

        # Kategorie muss Teil der Runde sein
        category = get_object_or_404(active.categories, id=category_id)

        # Upsert: unique (round, user, category)
        sub, created = Submission.objects.get_or_create(
            round=active, user=user, category=category,
            defaults={"original_text": text}
        )
        if not created:
            # Aktualisieren → Auto-Matching erneut anwenden
            sub.original_text = text
            # save() triggert apply_auto_match() nur bei creating; deshalb:
            sub.normalized_text = ""
            sub.matched_term = None
            sub.unknown_term = None
            sub.is_valid = False
            sub.is_unique = False
            sub.similarity = 0.0
            sub.save()  # führt nicht automatisch apply_auto_match aus
            # darum manuell:
            sub.apply_auto_match()
            sub.save(update_fields=[
                "normalized_text", "matched_term", "unknown_term",
                "is_valid", "is_unique", "similarity", "original_text"
            ])
        else:
            # bei create hat save() auto-match ausgeführt
            sub.save()

        read = SubmissionReadSerializer(sub)
        return Response(read.data, status=201 if created else 200)



class VoteView(APIView):
    """
    Abstimmung zu einem UnknownTerm (nur Teilnehmer der Runde).
    Unique: pro (unknown_term, user) genau eine Stimme (updatebar).
    """
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user
        data = VoteWriteSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        ut = get_object_or_404(UnknownTerm, id=data.validated_data["unknown_term_id"])
        rnd = ut.round

        if rnd.is_finalized:
            return Response({"detail": "Diese Runde ist bereits finalisiert. Keine Votes mehr möglich."}, status=400)

        if not RoundParticipant.objects.filter(round=rnd, user=user).exists():
            return Response({"detail": "Du bist kein Teilnehmer dieser Runde."}, status=403)

        vote, created = Vote.objects.update_or_create(
            unknown_term=ut, user=user, defaults={"value": data.validated_data["value"]}
        )
        ser = UnknownTermSerializer(ut)
        return Response(ser.data, status=201 if created else 200)



class ScoreboardView(APIView):
    """
    Liefert:
    - Globales Highscore (Top N; default 10)
    - Live-Snapshot der aktuellen Runde: pro Teilnehmer Anzahl gültiger Submissions und temporäre Punkte
      (ohne Unique-Bonus, der erst bei Finalisierung feststeht).
    """
    permission_classes = [AllowAny]

    def get(self, request):
        limit = int(request.query_params.get("limit", 10))

        # Globales Highscore
        highs = Highscore.objects.select_related("user").order_by("-total_points")[:limit]
        highs_ser = HighscoreSerializer(highs, many=True).data

        # Live der aktuellen Runde (wenn vorhanden)
        live = []
        active = get_active_round()
        if active:
            # Für alle Teilnehmer gültige Submissions zählen
            participants = active.round_participants.select_related("user").all()
            for rp in participants:
                valid_count = Submission.objects.filter(round=active, user=rp.user, is_valid=True).count()
                live.append({
                    "user": {"id": rp.user.id, "username": rp.user.username},
                    "valid_count": valid_count,
                    "points_estimate": valid_count * BASE_POINTS,  # ohne Unique-Bonus
                })

            # Sortieren nach points_estimate absteigend
            live.sort(key=lambda x: x["points_estimate"], reverse=True)

        return Response({
            "highscores": highs_ser,
            "live": live,
        })


# ---- Admin/Test: neue Runde erzwingen ----

class ForceNewRoundView(APIView):
    """
    Nur Admin: finalisiert ggf. aktive Runde und startet sofort eine neue.
    Nützlich für Tests/Demos.
    """
    permission_classes = [IsAuthenticated, IsAdminRole]

    @transaction.atomic
    def post(self, request):
        # Finalisierung über ensure_active_round (finalize) erzwingen,
        # danach direkt neue Runde start_new()
        latest = Round.objects.order_by("-number").first()
        if latest and not latest.is_finalized:
            latest.finalize()
        rnd = Round.start_new()
        ser = CurrentRoundSerializer(rnd, context={"request": request})
        return Response(ser.data, status=201)




class UnknownTermsListView(APIView):
    """
    Listet UnknownTerms der aktiven Runde, nur für Runde-Teilnehmer.
    Damit kann das Frontend eine Abstimmungsansicht bauen.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        active = get_active_round()
        if not active:
            return Response({"detail": "Keine aktive Runde."}, status=400)

        if not RoundParticipant.objects.filter(round=active, user=request.user).exists():
            return Response({"detail": "Du bist in dieser Runde kein Teilnehmer."}, status=403)

        uts = active.unknown_terms.select_related("category").all().order_by("category__name", "normalized_text")
        ser = UnknownTermSerializer(uts, many=True)
        return Response(ser.data)
