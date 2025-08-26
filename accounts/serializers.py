from rest_framework import serializers
from .models import User

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("username", "password")

    def create(self, validated_data):
        
        return User.objects.create_user(**validated_data)


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
