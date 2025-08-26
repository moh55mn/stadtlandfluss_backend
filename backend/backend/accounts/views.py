from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.generics import CreateAPIView, RetrieveAPIView, UpdateAPIView, ListAPIView
from .serializers import RegisterSerializer, UserSerializer, ActivateUserSerializer
from .permissions import IsAdminRole
from .models import User

class RegisterView(CreateAPIView):
    """
    Registriert einen neuen Benutzer (immer inaktiv, Rolle 'user').
    Freischaltung durch Admin notwendig.
    """
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer


class ProfileView(RetrieveAPIView):
    """
    Liefert die Profildaten des eingeloggten Users (Self-Profile).
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


# --- Admin-Endpoints ---

class AdminUserListView(ListAPIView):
    """
    Listet alle User (nur Admins).
    Optional: später Filter/Suche/Pagination ergänzen.
    """
    permission_classes = [IsAdminRole]
    queryset = User.objects.all()
    serializer_class = UserSerializer
class AdminUserActivateView(UpdateAPIView):
    """
    Aktiviert/Deaktiviert einen User (nur Admins).
    PATCH / PUT mit {"is_active": true/false}
    """
    permission_classes = [IsAdminRole]
    queryset = User.objects.all()
    serializer_class = ActivateUserSerializer

