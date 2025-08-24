from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, ProfileView, AdminUserListView, AdminUserActivateView

urlpatterns = [
    # Auth
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("auth/login/", TokenObtainPairView.as_view(), name="auth-login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth-refresh"),
    path("me/", ProfileView.as_view(), name="me"),

    # Admin
    path("admin/users/", AdminUserListView.as_view(), name="admin-user-list"),
    path("admin/users/<int:pk>/activate/", AdminUserActivateView.as_view(), name="admin-user-activate"),
]
