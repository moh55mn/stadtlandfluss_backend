from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models

class Roles(models.TextChoices):
    ADMIN = "admin", "Admin"
    USER = "user", "User"

class CustomUserManager(DjangoUserManager):
    """Sorgt dafür, dass Superuser aktiv & Admin-Rolle erhält."""
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)   # Superuser sofort aktiv
        extra_fields.setdefault("role", Roles.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)

class User(AbstractUser):
    # Standardfelder wie username, email, first_name, last_name kommen von AbstractUser
    role = models.CharField(max_length=10, choices=Roles.choices, default=Roles.USER)
    # Normale User müssen durch Admin freigeschaltet werden:
    is_active = models.BooleanField(default=False)

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.username} ({self.role})"
