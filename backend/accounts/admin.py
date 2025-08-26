from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Roles

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
    list_display = ("username", "email", "role", "is_active", "date_joined")
    list_display_links = ("username",)  # Link bleibt auf dem Username
    list_editable = ("role", "is_active")  # Direkt in der Liste änderbar
    list_filter = ("role", "is_active")
    search_fields = ("username", "email")
    ordering = ("-date_joined",)
    actions = [activate_users, deactivate_users]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (_("Persönliche Info"), {"fields": ("first_name", "last_name", "email")}),
        (_("Rollen & Status"), {"fields": ("role", "is_active")}),
        (_("Berechtigungen"), {"fields": ("groups", "user_permissions")}),
        (_("Wichtige Daten"), {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("username", "password1", "password2", "role", "is_active"),
        }),
    )


