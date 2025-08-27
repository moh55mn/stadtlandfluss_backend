# accounts/permissions.py
from rest_framework.permissions import BasePermission

class IsAdminRole(BasePermission):
    
    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and user.is_staff
        )

