from rest_framework import serializers
from django.contrib.auth import get_user_model
from datetime import datetime, timezone as dt_timezone  # <-- kein Shadowing von django.utils.timezone
from .models import Category, Term, Highscore
from .utils import normalize_text
 
User = get_user_model()
 
# --- Stammdaten / Admin ---
 
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name")
 
class TermSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
 
    class Meta:
        model = Term
        fields = ("id", "category", "value")
 
 
# --- Write-Serializer für Submits (Cache-Variante weiter nutzbar) ---
 
class SubmissionWriteSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    text = serializers.CharField(max_length=200)
 
    def validate(self, attrs):
        text = attrs.get("text", "").strip()
        if not text:
            raise serializers.ValidationError("Text darf nicht leer sein.")
        attrs["normalized_text"] = normalize_text(text)
        return attrs
 
# --- Highscores (DB) ---
 
class HighscoreSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
 
    class Meta:
        model = Highscore
        fields = ("user", "total_points")
 
    def get_user(self, obj):
        u = obj.user
        return {"id": u.id, "username": u.username}
 
# --- Cache-Variante: Dict-basierte Runde & Unknowns ---
 
class CategoryRefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField(required=False, allow_blank=True)
 
class CurrentRoundDictSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    letter = serializers.CharField()
    start = serializers.CharField()  # ISO-String aus dem Cache
    end = serializers.CharField()    # ISO-String aus dem Cache
    participants = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)
    categories = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)
    remaining_seconds = serializers.SerializerMethodField()
 
    def get_remaining_seconds(self, obj):
        try:
            end_dt = datetime.fromisoformat(obj["end"])
            if end_dt.tzinfo is None:
                end_dt = end_dt.replace(tzinfo=dt_timezone.utc)
            now = datetime.now(dt_timezone.utc)
            remaining = int((end_dt - now).total_seconds())
            return max(0, remaining)
        except Exception:
            return None
 
class UnknownTermListItemSerializer(serializers.Serializer):
    id = serializers.CharField()  # z. B. "42:7:berlin"
    normalized_text = serializers.CharField()
    category = CategoryRefSerializer()
    approvals = serializers.IntegerField()
    rejections = serializers.IntegerField()
    round = serializers.IntegerField()
