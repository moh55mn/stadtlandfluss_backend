from django.test import override_settings
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from unittest.mock import patch
from django.utils import timezone
from django.urls import reverse, NoReverseMatch
from datetime import timedelta
from uuid import uuid4
 
from game.models import Category, Term
from game.cache_store import get_active_round, set_active_round
 
User = get_user_model()
 
 
def reverse_any(candidates, **kwargs):
    """
    Versucht eine Liste von URL-Namen (mit/ohne Namespace) nacheinander.
    Gibt beim ersten Treffer die URL zurück, sonst wirft NoReverseMatch.
    """
    last_exc = None
    for name in candidates:
        try:
            return reverse(name, kwargs=kwargs)
        except NoReverseMatch as e:
            last_exc = e
            continue
    raise last_exc or NoReverseMatch(f"No URL name matched out of: {candidates}")
 
 
@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class GameSinglePlayerFlowTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Eindeutige Kategorienamen, um UNIQUE(name) nicht zu verletzen
        suffix = uuid4().hex[:6]
        cls.cat_city = Category.objects.create(name=f"Stadt-{suffix}")
        cls.cat_country = Category.objects.create(name=f"Land-{suffix}")
        Term.objects.create(category=cls.cat_city, value="Berlin")
 
        # Ein aktiver User
        cls.user = User.objects.create_user(username="alice", password="secret", is_active=True)
 
        # Merke IDs für spätere Nutzung in Tests
        cls.city_id = cls.cat_city.id
        cls.country_id = cls.cat_country.id
 
    def setUp(self):
        # API Client + Bearer Token
        self.c = APIClient()
        access = self._login_get_access("alice", "secret")
        self.c.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
 
        # URLs (probiert mehrere Namen – passe ggf. die Listen an deine Projekte an)
        self.url_login         = reverse_any(["accounts:auth-login", "auth-login"])
        self.url_join          = reverse_any(["game:join", "join"])
        self.url_current       = reverse_any(["game:current", "current-round"])
        self.url_submit        = reverse_any(["game:submit", "submit"])
        self.url_unknown       = reverse_any(["game:unknown", "unknown-terms"])
        self.url_vote          = reverse_any(["game:vote", "vote"])
        self.url_scoreboard    = reverse_any(["game:scoreboard", "scoreboard"])
        self.url_my_score      = reverse_any(["game:my-score", "my-total-score"])
        # my-last-result ist evtl. optional, falls du ihn (noch) nicht hast:
        try:
            self.url_my_last = reverse_any(["game:my-last-result", "my-last-result"])
        except NoReverseMatch:
            self.url_my_last = None  # Test überspringt dann freundlich
 
    def _login_get_access(self, username, password):
        url_login = reverse_any(["accounts:auth-login", "auth-login"])
        r = self.client.post(url_login, {"username": username, "password": password}, format="json")
        self.assertEqual(r.status_code, 200, r.content)
        self.assertIn("access", r.json())
        return r.json()["access"]
 
    def _force_phase_end_now(self):
        """phase_end in die Vergangenheit setzen, damit /game/current/ in die nächste Phase springt."""
        rnd = get_active_round()
        self.assertIsNotNone(rnd, "Keine aktive Runde im Cache.")
        rnd["phase_end"] = (timezone.now() - timedelta(seconds=1)).isoformat()
        set_active_round(rnd)
 
    # WICHTIG: Stelle sicher, dass in game/services_cache.py die Funktion _random_letter benutzt wird.
    # Falls du direkt random.choice verwendest, lege in services_cache eine kleine Wrapper-Funktion an:
    # def _random_letter(): import string, random; return random.choice(string.ascii_uppercase)
    @patch("game.services_cache._random_letter", return_value="B")
    def test_single_player_full_flow(self, _patched_letter):
        # 1) Join -> startet eine neue Runde
        r = self.c.post(self.url_join)
        self.assertEqual(r.status_code, 200, r.content)
        rnd = r.json()
        self.assertEqual(rnd["letter"], "B")
        self.assertIn(self.__class__.user.id, rnd["participants"])
 
        # 2) Submit: bekannter Begriff (valid)
        r = self.c.post(self.url_submit, {"category_id": self.city_id, "text": "Berlin"}, format="json")        
        self.assertEqual(r.status_code, 201, r.content)
        body_known = r.json()
        self.assertTrue(body_known["is_valid"])
        self.assertEqual(body_known.get("normalized_text"), "berlin")
 
        # 3) Submit: unbekannt (erzwingt Voting)
        r = self.c.post(self.url_submit, {"category_id": self.country_id, "text": "Beligien"}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
        body_unknown = r.json()
        self.assertFalse(body_unknown["is_valid"])
        self.assertEqual(body_unknown.get("normalized_text"), "beligien")
 
        # 4) Spielphase beenden -> sollte in 'voting' wechseln
        self._force_phase_end_now()
        r = self.c.get(self.url_current)
        self.assertEqual(r.status_code, 200, r.content)
        cur = r.json()
        self.assertEqual(cur["phase"], "voting")
 
        # 5) Unknowns einmal laden (nur in Voting)
        r = self.c.get(self.url_unknown)
        self.assertEqual(r.status_code, 200, r.content)
        unknowns = r.json()
        self.assertTrue(any(
            u["normalized_text"] == "beligien" and u["category"]["id"] == self.country_id
            for u in unknowns
        ))
 
        # 6) Abstimmen
        r = self.c.post(self.url_vote, {"category_id": self.country_id, "normalized": "beligien", "value": True}, format="json")
        self.assertEqual(r.status_code, 201, r.content)
 
        # 7) Voting-Phase beenden -> Finalisierung & ggf. neue Runde
        self._force_phase_end_now()
        r = self.c.get(self.url_current)
        self.assertIn(r.status_code, (200, 204))  # neue Runde gestartet oder im Leerlauf
 
        # 8) Scoreboard & eigener Score / letztes Ergebnis
        r = self.client.get(self.url_scoreboard)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertIn("highscores", r.json())
 
        r = self.c.get(self.url_my_score)
        self.assertEqual(r.status_code, 200, r.content)
        self.assertIn("total_points", r.json())
 
        if self.url_my_last:
            r = self.c.get(self.url_my_last)
            self.assertIn(r.status_code, (200, 204))
