from django.contrib.auth.models import AbstractUser, UserManager as DjangoUserManager
from django.db import models
 
 
class CustomUserManager(DjangoUserManager):
    """Custom manager so normal users start inactive, superusers get staff/admin rights."""
 
    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault("is_active", False)
        extra_fields.setdefault("is_staff", False)
 
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
 
    def create_superuser(self, username, password=None, **extra_fields):
        # required flags for superuser
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
 
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
 
        user = self.model(username=username, **extra_fields) 
        if password:
            user.set_password(password)
        else:
            raise ValueError("Superuser must have a password.")
        user.save(using=self._db)
        return user

        
 
        return super().create_superuser(username, password, **extra_fields)
 
 
class User(AbstractUser):
    """
    Custom user:
    - Remove first_name, last_name, email
    - Use is_staff instead of custom role
    """
 
    first_name = None
    last_name = None
    email = None
    last_login= None
    date_joined = None
 
    objects = CustomUserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []
 
    def __str__(self):
        return f"{self.username} ({'Admin' if self.is_staff else 'User'})"
