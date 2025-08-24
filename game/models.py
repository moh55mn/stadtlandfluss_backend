# game/models.py
from django.conf import settings
from django.db import models
from django.utils import timezone
import random
import string

from .utils import normalize_text, first_letter_upper, similarity

User = settings.AUTH_USER_MODEL

ROUND_DURATION_SECONDS = 60
SIMILARITY_THRESHOLD = 0.80
BASE_POINTS = 10
UNIQUE_BONUS = 5

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Term(models.Model):
    """
    Bekannte, gültige Begriffe, gepflegt durch Admins.
    normalized_value dient schnellem Matching (fuzzy).
    first_letter enthält den Großbuchstaben (A–Z) des Begriffs.
    """
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="terms")
    value = models.CharField(max_length=120)
    normalized_value = models.CharField(max_length=140, db_index=True)
    first_letter = models.CharField(max_length=1, db_index=True)  # 'A'–'Z'
    is_approved = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_terms"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("category", "normalized_value"),)

    def save(self, *args, **kwargs):
        self.normalized_value = normalize_text(self.value)
        self.first_letter = first_letter_upper(self.value)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.value} [{self.category.name}]"


class WaitingPlayer(models.Model):
    """
    Spielt-als-nächstes Warteliste. Wer hier drin ist, wird bei Start der
    nächsten Runde automatisch Teilnehmer.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="waiting_flag")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Waiting: {self.user}"


class Round(models.Model):
    """
    Eine 60s-Runde mit einem zufälligen Buchstaben.
    Teilnehmer werden beim Start aus WaitingPlayer importiert.
    """
    number = models.PositiveIntegerField(db_index=True)  # fortlaufende Nummer
    letter = models.CharField(max_length=1, db_index=True)  # 'A'–'Z'
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_finalized = models.BooleanField(default=False)

    categories = models.ManyToManyField(Category, related_name="rounds")
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="RoundParticipant", related_name="rounds"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-number",)

    @property
    def is_active(self) -> bool:
        now = timezone.now()
        return self.start_time <= now < self.end_time and not self.is_finalized

    @classmethod
    def random_letter(cls) -> str:
        # Exklusive Umlaute, nur A–Z
        return random.choice(string.ascii_uppercase)

    @classmethod
    def start_new(cls, categories_qs=None) -> "Round":
        """
        Startet eine neue Runde:
        - runden-nummer = (letzte nummer + 1)
        - letter = random
        - start = jetzt, ende = +60s
        - participants = alle WaitingPlayer
        """
        last = cls.objects.order_by("-number").first()
        next_number = (last.number + 1) if last else 1
        letter = cls.random_letter()
        now = timezone.now()
        rnd = cls.objects.create(
            number=next_number,
            letter=letter,
            start_time=now,
            end_time=now + timezone.timedelta(seconds=ROUND_DURATION_SECONDS),
        )
        # Kategorien – falls nicht übergeben, alle (mindestens Stadt/Land/Fluss/Tier)
        if categories_qs is None:
            from .models import Category
            categories_qs = Category.objects.all()
        rnd.categories.set(categories_qs)

        # Waiting → Participants
        waiting = list(WaitingPlayer.objects.select_related("user").all())
        RoundParticipant.objects.bulk_create(
            [RoundParticipant(round=rnd, user=w.user) for w in waiting]
        )
        # Waiting leeren
        WaitingPlayer.objects.all().delete()
        return rnd

    def finalize(self):
        """
        Finalisiert Runde:
        - Votings auswerten (UnknownTerms -> valid wenn approvals > rejections)
        - Submissions valid markieren
        - Unique-Bonus je Kategorie für unique gültige Einträge
        - Punkte je Teilnehmer berechnen und in Highscore kumulieren
        """
        if self.is_finalized:
            return
        # 1) Abstimmungen auswerten
        for ut in self.unknown_terms.all():
            if ut.approvals > ut.rejections:
                # Alle Submissions mit dieser UnknownTerm als valid werten
                Submission.objects.filter(unknown_term=ut).update(is_valid=True)

        # 2) Unique-Bonus ermitteln (je Kategorie)
        for cat in self.categories.all():
            subs = Submission.objects.filter(round=self, category=cat, is_valid=True)
            # gruppieren nach normalized_text
            groups = {}
            for s in subs:
                groups.setdefault(s.normalized_text, []).append(s.id)
            # unique = genau eine Submission mit diesem normalized_text
            unique_ids = {ids[0] for ids in groups.values() if len(ids) == 1}
            Submission.objects.filter(id__in=unique_ids).update(is_unique=True)

        # 3) Punkte berechnen
        # Basispunkte für gültige Submission, Bonus falls unique
        participant_points = {}
        valid_subs = Submission.objects.filter(round=self, is_valid=True).values(
            "user_id", "is_unique"
        )
        for item in valid_subs:
            pts = BASE_POINTS + (UNIQUE_BONUS if item["is_unique"] else 0)
            participant_points[item["user_id"]] = participant_points.get(item["user_id"], 0) + pts

        # 4) Rundenscore speichern
        for rp in RoundParticipant.objects.filter(round=self):
            rp.score_this_round = participant_points.get(rp.user_id, 0)
            rp.save(update_fields=["score_this_round"])

        # 5) Highscore kumulieren
        for user_id, pts in participant_points.items():
            hs, _ = Highscore.objects.get_or_create(user_id=user_id, defaults={"total_points": 0})
            hs.total_points = models.F("total_points") + pts
            hs.save(update_fields=["total_points"])

        self.is_finalized = True
        self.save(update_fields=["is_finalized"])


class RoundParticipant(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="round_participants")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="round_participations")
    joined_at = models.DateTimeField(auto_now_add=True)
    score_this_round = models.IntegerField(default=0)

    class Meta:
        unique_together = (("round", "user"),)

    def __str__(self):
        return f"Round {self.round.number} - {self.user}"


class UnknownTerm(models.Model):
    """
    Repräsentiert einen unbekannten Begriff pro (Runde, Kategorie, normalized_text),
    über den abgestimmt wird.
    """
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="unknown_terms")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="unknown_terms")
    normalized_text = models.CharField(max_length=140)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("round", "category", "normalized_text"),)

    @property
    def approvals(self) -> int:
        return self.votes.filter(value=True).count()

    @property
    def rejections(self) -> int:
        return self.votes.filter(value=False).count()

    def __str__(self):
        return f"Unknown '{self.normalized_text}' ({self.category.name}) r{self.round.number}"


class Vote(models.Model):
    unknown_term = models.ForeignKey(UnknownTerm, on_delete=models.CASCADE, related_name="votes")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="votes")
    value = models.BooleanField()  # True = gültig, False = ungültig
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("unknown_term", "user"),)

    def __str__(self):
        return f"Vote {self.user} -> {self.unknown_term}: {self.value}"


class Submission(models.Model):
    """
    Nutzer-Eingabe je (Runde, Kategorie).
    Validation-Strategie beim Anlegen:
    - Falls Term mit first_letter == round.letter existiert und similarity >= threshold:
        -> matched_term, is_valid=True
    - Sonst UnknownTerm anlegen/finden -> is_valid=False (pending vote)
    """
    round = models.ForeignKey(Round, on_delete=models.CASCADE, related_name="submissions")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="submissions")
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="submissions")

    original_text = models.CharField(max_length=200)
    normalized_text = models.CharField(max_length=200, db_index=True)

    matched_term = models.ForeignKey(Term, on_delete=models.SET_NULL, null=True, blank=True, related_name="matched_submissions")
    unknown_term = models.ForeignKey(UnknownTerm, on_delete=models.SET_NULL, null=True, blank=True, related_name="submissions")

    similarity = models.FloatField(default=0.0)
    is_valid = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("round", "user", "category"),)

    def save(self, *args, **kwargs):
        creating = self._state.adding
        self.normalized_text = normalize_text(self.original_text)
        if creating:
            # Nur bei Neu-Anlage: auto-Matching
            self.apply_auto_match()
        super().save(*args, **kwargs)

    def apply_auto_match(self):
        # Nur erlaubte Startbuchstaben
        start_letter = self.round.letter
        # Kandidaten: gleiche Kategorie + gleicher first_letter
        candidates = Term.objects.filter(
            category=self.category,
            first_letter=start_letter,
            is_approved=True,
        )
        best = None
        best_score = 0.0
        for term in candidates:
            score = similarity(self.normalized_text, term.normalized_value)
            if score > best_score:
                best_score = score
                best = term

        self.similarity = best_score
        if best and best_score >= SIMILARITY_THRESHOLD:
            self.matched_term = best
            self.is_valid = True
            self.unknown_term = None
        else:
            # UnknownTerm (pro Runde/Kategorie/normalized_text)
            ut, _ = UnknownTerm.objects.get_or_create(
                round=self.round,
                category=self.category,
                normalized_text=self.normalized_text,
            )
            self.unknown_term = ut
            self.matched_term = None
            self.is_valid = False


class Highscore(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="highscore")
    total_points = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user}: {self.total_points} pts"
