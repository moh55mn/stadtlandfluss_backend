from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
 
 
class CustomUserManager(DjangoUserManager):
    """Custom manager so normal users start inactive, superusers get staff/admin rights."""
 
    def create_user(self, username, password=None, **extra_fields):
        # we drop 'email' completely, since our User model has no email field
        extra_fields.setdefault("is_active", False)
        extra_fields.setdefault("is_staff", False)
 
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
 
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        # superuser must be active and staff
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
 
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
 
        return super().create_superuser(username, email, password, **extra_fields)
 
 
class User(AbstractUser):
    """
    Custom user:
    - Remove first_name, last_name, email
    - Use is_staff instead of custom role
    """
 
    first_name = None
    last_name = None
    email = None
 
    objects = CustomUserManager()
 
    def __str__(self):
        return f"{self.username} ({'Admin' if self.is_staff else 'User'})"
