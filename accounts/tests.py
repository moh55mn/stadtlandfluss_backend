from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
 
User = get_user_model()
 
class AuthFlowTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alice", password="pw", is_active=True)
 
    def test_login_and_me(self):
        r = self.client.post("/api/accounts/auth/login/", {"username": "alice", "password": "pw"}, format="json")
        self.assertEqual(r.status_code, 200)
        tokens = r.json()
        self.assertIn("access", tokens)
 
        access = tokens["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        me = self.client.get("/api/accounts/me/")
        self.assertEqual(me.status_code, 200)
        data = me.json()
        self.assertEqual(data["username"], "alice")
