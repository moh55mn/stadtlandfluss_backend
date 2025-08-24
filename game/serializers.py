from rest_framework import serializers
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models import (
    Category, Term, Round, Submission, UnknownTerm, Vote, Highscore, ROUND_DURATION_SECONDS,
    BASE_POINTS
)
from .utils import normalize_text

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name", "slug")


class TermSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    created_by = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Term
        fields = ("id", "category", "value", "first_letter", "is_approved", "created_by", "created_at")
        read_only_fields = ("first_letter", "created_by", "created_at")

    def get_created_by(self, obj):
        return obj.created_by.username if obj.created_by else None

    def create(self, validated_data):
        user = self.context["request"].user
        validated_data["created_by"] = user if user.is_authenticated else None
        return super().create(validated_data)


class UnknownTermSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    approvals = serializers.IntegerField(read_only=True)
    rejections = serializers.IntegerField(read_only=True)

    class Meta:
        model = UnknownTerm
        fields = ("id", "normalized_text", "category", "approvals", "rejections", "round")


class SubmissionReadSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    matched_term = TermSerializer(read_only=True)
    unknown_term = UnknownTermSerializer(read_only=True)

    class Meta:
        model = Submission
        fields = (
            "id", "round", "category", "original_text", "normalized_text", "matched_term",
            "unknown_term", "similarity", "is_valid", "is_unique", "created_at"
        )


class SubmissionWriteSerializer(serializers.Serializer):
    category_id = serializers.IntegerField()
    text = serializers.CharField(max_length=200)

    def validate(self, attrs):
        text = attrs.get("text", "").strip()
        if not text:
            raise serializers.ValidationError("Text darf nicht leer sein.")
        attrs["normalized_text"] = normalize_text(text)
        return attrs


class CurrentRoundSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    is_active = serializers.SerializerMethodField()
    ends_in_seconds = serializers.SerializerMethodField()
    my_submissions = serializers.SerializerMethodField()
    participants_count = serializers.SerializerMethodField()

    class Meta:
        model = Round
        fields = (
            "number", "letter", "start_time", "end_time", "is_active",
            "ends_in_seconds", "categories", "participants_count", "is_finalized",
            "id", "created_at", "my_submissions"
        )

    def get_is_active(self, obj):
        return obj.is_active

    def get_ends_in_seconds(self, obj):
        now = timezone.now()
        if now >= obj.end_time:
            return 0
        return int((obj.end_time - now).total_seconds())

    def get_participants_count(self, obj):
        return obj.round_participants.count()

    def get_my_submissions(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return {}
        subs = (
            Submission.objects
            .filter(round=obj, user=user)
            .select_related("category", "matched_term")
        )
        result = {}
        for s in subs:
            result[s.category.id] = {
                "category": s.category.name,
                "original_text": s.original_text,
                "is_valid": s.is_valid,
                "similarity": round(s.similarity, 3),
                "unknown_term_id": s.unknown_term_id,
                "matched_term": s.matched_term.value if s.matched_term_id else None,
            }
        return result


class VoteWriteSerializer(serializers.Serializer):
    unknown_term_id = serializers.IntegerField()
    value = serializers.BooleanField()


class HighscoreSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Highscore
        fields = ("user", "total_points", "last_updated")

    def get_user(self, obj):
        u = obj.user
        return {"id": u.id, "username": u.username}
