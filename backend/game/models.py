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

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="terms")
    value = models.CharField(max_length=120)
 
    class Meta:
        unique_together = (("category", "value"),)
 
 
    def __str__(self):
        return f"{self.value} [{self.category.name}]"
 
 
class Highscore(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="highscore")
    total_points = models.IntegerField(default=0)
 
    def __str__(self):
        return f"{self.user}: {self.total_points} pts"
