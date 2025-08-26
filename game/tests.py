from django.test import override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
 
from game.models import Category, Term, Highscore, BASE_POINTS, UNIQUE_BONUS
from game.cache_store import get_active_round, clear_active_round
from uuid import uuid4
User = get_user_model()
 
# Für Tests: schneller Memory-Cache statt DB-Cache
TEST_CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "slf-tests",
        "TIMEOUT": 300,
    }
}
 
@override_settings(CACHES=TEST_CACHES)
class GameCacheFlowTests(APITestCase):
    from uuid import uuid4
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
 
from game.models import Category, Term
from game.cache_store import clear_active_round
 
User = get_user_model()
 
class GameCacheFlowTests(APITestCase):
    def setUp(self):
        # Users
        self.u1 = User.objects.create_user(username="alice", password="pw", is_active=True)
        self.u2 = User.objects.create_user(username="bob", password="pw", is_active=True)
 
        # Kategorien (kollisionsfrei – entweder feste Namen via get_or_create ODER eindeutige Namen)
        # Variante A: feste Namen, aber robust gegen vorhandene Defaults
        self.cat_city, _ = Category.objects.get_or_create(name="Stadt")
        self.cat_country, _ = Category.objects.get_or_create(name="Land")
 
        # Variante B (Alternative): garantiert eindeutig
        # self.cat_city    = Category.objects.create(name=f"Stadt-{uuid4().hex[:6]}")
        # self.cat_country = Category.objects.create(name=f"Land-{uuid4().hex[:6]}")
 
        # Term „Berlin“ in Kategorie „Stadt“ (robust: category_id + defaults)
        Term.objects.get_or_create(
            category_id=self.cat_city.id,
            value="Berlin",
            defaults={"is_approved": True},
        )
 
        # Clients authentifizieren
        self.client_u1 = APIClient()
        self.client_u1.force_authenticate(user=self.u1)
 
        self.client_u2 = APIClient()
        self.client_u2.force_authenticate(user=self.u2)
 
        # Aktive Runde im Cache wegräumen (falls von anderem Test übrig)
        clear_active_round()
 
    # ... deine Tests folgen ...
 
 
    def test_join_and_current_round(self):
        r = self.client_u1.post("/api/game/join/")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertIn(self.u1.id, data["participants"])
 
        r2 = self.client_u1.get("/api/game/current/")
        self.assertIn(r2.status_code, (200, 204))
        if r2.status_code == 200:
            cur = r2.json()
            self.assertIn("letter", cur)
            self.assertGreaterEqual(cur.get("remaining_seconds", 0), 0)
 
    def test_submit_vote_and_highscore(self):
        self.client_u1.post("/api/game/join/")
        self.client_u2.post("/api/game/join/")
        active = get_active_round()
        cat_id = active["categories"][0]
 
        payload = {"category_id": cat_id, "text": "Xyzunbekannt"}
        r = self.client_u1.post("/api/game/submit/", payload, format="json")
        self.assertEqual(r.status_code, 201)
        sub = r.json()
        self.assertFalse(sub["is_valid"])
 
        r_unk = self.client_u1.get("/api/game/unknown/")
        self.assertEqual(r_unk.status_code, 200)
        unknowns = r_unk.json()
        self.assertTrue(any(u["normalized_text"] == sub.get("normalized_text", "").lower() for u in unknowns))
 
        # Bob stimmt zu
        vote_payload = {"category_id": cat_id, "normalized": sub["normalized_text"], "value": True}
        rv = self.client_u2.post("/api/game/vote/", vote_payload, format="json")
        self.assertEqual(rv.status_code, 201)
 
        # Admin erstellt → Finalisierung
        admin = User.objects.create_superuser(username="admin", password="pw")
        admin_client = APIClient()
        admin_client.force_authenticate(user=admin)
        r_fin = admin_client.post("/api/game/force-new-round/")
        self.assertEqual(r_fin.status_code, 201)
 
        # Highscore prüfen
        hs = Highscore.objects.filter(user=self.u1).first()
        self.assertIsNotNone(hs)
        self.assertGreaterEqual(hs.total_points, BASE_POINTS)


