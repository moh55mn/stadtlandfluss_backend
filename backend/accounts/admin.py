from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.action(description="Ausgewählte Nutzer aktivieren")
def activate_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=True)
    modeladmin.message_user(request, f"{updated} Nutzer aktiviert.")

@admin.action(description="Ausgewählte Nutzer deaktivieren")
def deactivate_users(modeladmin, request, queryset):
    updated = queryset.update(is_active=False)
    modeladmin.message_user(request, f"{updated} Nutzer deaktiviert.")

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    model = User
    ordering = ("id",)
    list_display = ("id", "username", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "is_superuser")
    search_fields = ("username",)
 
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "user_permissions")}),
    )
 
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username", "password1", "password2",
                "is_active", "is_staff", "is_superuser",
                "groups", "user_permissions",
            ),
        }),
    )


