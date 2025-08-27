# accounts/permissions.py
from rest_framework.permissions import BasePermission

class IsAdminRole(BasePermission):
    """
    Erlaubt Zugriff nur für Nutzer mit role='admin' ODER is_superuser=True.
    Kein Fallback auf is_staff, damit "nur Admins" wirklich enforced ist.
    """
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_staff
        )

