from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("username", "password")

    def create(self, validated_data):
        # Normale Nutzer: Rolle "user", is_active=False (Freischaltung durch Admin)
        user = User(
            username=validated_data["username"],
            # email=validated_data.get("email", ""),
            role=Roles.USER,
        )
        user.set_password(validated_data["password"])
        # is_active bleibt default False (siehe Model)
        user.save()
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "role", "is_active")


class ActivateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("is_active",)
        extra_kwargs = {
            "is_active": {"required": True}
        }
