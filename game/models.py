from django.conf import settings
from django.db import models
from django.utils.text import slugify
 
from .utils import normalize_text, first_letter_upper
 
# Konstanten (du kannst sie später in game/constants.py auslagern)
ROUND_DURATION_SECONDS = 60
SIMILARITY_THRESHOLD = 0.80
BASE_POINTS = 10
UNIQUE_BONUS = 5
 
 
class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
 
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
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_terms",
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
 
 
class Highscore(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="highscore")
    total_points = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
 
    def __str__(self):
        return f"{self.user}: {self.total_points} pts"
