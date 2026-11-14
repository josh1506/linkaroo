"""Security regression tests (threat model: docs/THREAT_MODEL.md).

Tests marked @expectedFailure document CONFIRMED, not-yet-fixed gaps. When a fix lands the test
"unexpectedly succeeds" and the marker must be removed in the same change.
"""
import inspect
from unittest import expectedFailure

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from app.url_tracker.models import URL, URLTracker

User = get_user_model()


class SecurityBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.staff = User.objects.create_superuser("staffer", password="Staff-pass-123")
        cls.alice = User.objects.create_user("alice", password="Alice-pass-123")
        cls.bob = User.objects.create_user("bob", password="Bob-pass-123")
        cls.b_url = URL.objects.create(owner=cls.bob, link="https://example.com/b", title="Bob link", custom_url="bob-link")

    def setUp(self):
        cache.clear()

    def tearDown(self):
        cache.clear()


class ObjectAuthorizationTests(SecurityBase):
    """ASVS 8.2.1 / 8.2.2 — anonymous, wrong-owner and non-staff access (fixed; must stay fixed)."""

    def test_anonymous_redirected_to_login_for_every_owner_endpoint(self):
        for path in ["/urls/", "/urls/list/", "/urls/create/", "/urls/tracker/list/",
                     f"/urls/detail/{self.b_url.pk}/", f"/urls/update/{self.b_url.pk}/"]:
            self.assertTrue(self.client.get(path)["Location"].startswith("/auth/login/"), path)
        r = self.client.post(f"/urls/delete/{self.b_url.pk}/")
        self.assertTrue(r["Location"].startswith("/auth/login/"))
        self.assertTrue(URL.objects.filter(pk=self.b_url.pk).exists())

    def test_wrong_owner_gets_404_on_read_write_delete(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get(f"/urls/detail/{self.b_url.pk}/").status_code, 404)
        self.assertEqual(self.client.post(f"/urls/update/{self.b_url.pk}/", {
            "link": "https://evil.example/", "title": "x", "custom_url": "bob-link", "description": ""}).status_code, 404)
        self.assertEqual(self.client.post(f"/urls/delete/{self.b_url.pk}/").status_code, 404)
        self.b_url.refresh_from_db()
        self.assertEqual(self.b_url.link, "https://example.com/b")

    def test_wrong_owner_sees_no_analytics(self):
        self.client.get("/bob-link/")
        self.client.force_login(self.alice)
        self.assertEqual(list(self.client.get("/urls/tracker/list/").context["tracker_list"]), [])
        self.assertEqual(self.client.get("/urls/").context["top_links"], [])

    def test_owner_field_not_mass_assignable(self):
        self.client.force_login(self.alice)
        self.client.post("/urls/create/", {"link": "https://example.com/m", "title": "M", "custom_url": "",
                                           "description": "", "owner": self.bob.pk})
        self.assertEqual(URL.objects.get(title="M").owner, self.alice)

    def test_non_staff_cannot_reach_admin(self):
        self.client.force_login(self.alice)
        self.assertEqual(self.client.get("/admin/url_tracker/url/").status_code, 302)

    def test_signup_cannot_grant_staff(self):
        self.client.post("/auth/signup/", {"username": "mallory", "first_name": "M", "last_name": "M",
                                           "email": "m@example.com", "password1": "Mallory-pass-987",
                                           "password2": "Mallory-pass-987", "is_staff": "on", "is_superuser": "on"})
        u = User.objects.get(username="mallory")
        self.assertFalse(u.is_staff or u.is_superuser)

    def test_previous_owner_loses_click_history_after_reassignment(self):
        link = URL.objects.create(owner=self.alice, link="https://example.com/m", title="Moved", custom_url="moved")
        self.client.get("/moved/")
        link.owner = self.bob
        link.save()
        self.client.force_login(self.alice)
        self.assertEqual(list(self.client.get("/urls/tracker/list/").context["tracker_list"]), [])


class CsrfAndMethodTests(SecurityBase):
    """ASVS 3.3.2 — state-changing requests need a CSRF token; redirect endpoint is GET-only."""

    def test_state_changing_posts_rejected_without_csrf_token(self):
        c = self.client_class(enforce_csrf_checks=True)
        c.force_login(self.bob)
        self.assertEqual(c.post(f"/urls/delete/{self.b_url.pk}/").status_code, 403)
        self.assertEqual(c.post("/urls/create/", {"link": "https://example.com", "title": "x"}).status_code, 403)
        self.assertEqual(c.post(reverse("users:logout")).status_code, 403)
        self.assertTrue(URL.objects.filter(pk=self.b_url.pk).exists())

    def test_redirect_endpoint_rejects_non_get(self):
        for method in ("post", "put", "delete"):
            self.assertEqual(getattr(self.client, method)("/bob-link/").status_code, 405, method)
        self.assertFalse(URLTracker.objects.exists())


class AuthenticationAbuseTests(SecurityBase):
    """ASVS 6.1.1 / 6.3.1 / 2.4.1 — brute force, spraying, lockout abuse, sign-up automation."""

    def _fail(self, client, path, username, n):
        for _ in range(n):
            client.post(path, {"username": username, "password": "wrong-password"})

    def test_site_login_locks_after_5_failures(self):
        self._fail(self.client, "/auth/login/", "alice", 5)
        r = self.client.post("/auth/login/", {"username": "alice", "password": "Alice-pass-123"})
        self.assertEqual(r.status_code, 429)

    def test_admin_login_locks_after_5_failures(self):
        self._fail(self.client, "/admin/login/", "staffer", 5)
        self.client.post("/admin/login/?next=/admin/", {"username": "staffer", "password": "Staff-pass-123"})
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_password_spraying_capped_per_client(self):
        c = self.client_class(REMOTE_ADDR="203.0.113.9")
        codes = [c.post("/auth/login/", {"username": f"user{i}", "password": "Summer2026!"}).status_code for i in range(60)]
        self.assertIn(429, codes)

    def test_lockout_of_one_client_does_not_lock_other_clients_behind_proxy(self):
        with self.settings(TRUSTED_PROXY_COUNT=1):
            attacker = self.client_class(REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="198.51.100.66")
            self._fail(attacker, "/auth/login/", "alice", 5)
            victim = self.client_class(REMOTE_ADDR="10.0.0.1", HTTP_X_FORWARDED_FOR="192.0.2.10")
            r = victim.post("/auth/login/", {"username": "alice", "password": "Alice-pass-123"})
            self.assertEqual(r.status_code, 302)

    def test_signup_rate_limited_per_client(self):
        c = self.client_class(REMOTE_ADDR="203.0.113.10")
        codes = [c.post("/auth/signup/", {"username": f"bot{i}", "first_name": "B", "last_name": "B",
                                          "email": f"b{i}@example.com", "password1": "Bot-pass-98765",
                                          "password2": "Bot-pass-98765"}).status_code for i in range(20)]
        self.assertIn(429, codes)

    def test_spoofed_forwarded_for_ignored_without_trusted_proxy(self):
        # Default TRUSTED_PROXY_COUNT=0: rotating X-Forwarded-For must not reset the per-client lockout.
        for i in range(5):
            self.client_class(REMOTE_ADDR="198.51.100.7", HTTP_X_FORWARDED_FOR=f"192.0.2.{i}").post(
                "/auth/login/", {"username": "alice", "password": "wrong"})
        r = self.client_class(REMOTE_ADDR="198.51.100.7", HTTP_X_FORWARDED_FOR="192.0.2.99").post(
            "/auth/login/", {"username": "alice", "password": "Alice-pass-123"})
        self.assertEqual(r.status_code, 429)

    def test_admin_login_still_works_for_staff(self):
        r = self.client.post("/admin/login/?next=/admin/", {"username": "staffer", "password": "Staff-pass-123"})
        self.assertEqual(r.status_code, 302)
        self.assertIn("_auth_user_id", self.client.session)

    def test_failed_login_message_does_not_reveal_whether_user_exists(self):  # ASVS 6.3.8
        a = self.client.post("/auth/login/", {"username": "alice", "password": "wrong"}).content
        cache.clear()
        b = self.client.post("/auth/login/", {"username": "no-such-user", "password": "wrong"}).content
        strip = lambda html: html.decode().split("csrfmiddlewaretoken")[0].replace("no-such-user", "alice")
        self.assertEqual(strip(a), strip(b))


class ClickRecordingAbuseTests(SecurityBase):
    """ASVS 2.4.1 / 2.3.2 — F5: anonymous click inflation. Redirects are never blocked; recording is capped."""

    def test_clicks_recorded_up_to_limit_per_client_but_every_visit_redirects(self):
        c = self.client_class(REMOTE_ADDR="203.0.113.11")
        with self.settings(CLICK_RECORD_LIMIT_PER_MINUTE=10):
            codes = [c.get("/bob-link/").status_code for _ in range(25)]
        self.assertEqual(codes, [302] * 25)
        self.assertEqual(URLTracker.objects.filter(url=self.b_url).count(), 10)

    def test_other_clients_still_counted(self):
        with self.settings(CLICK_RECORD_LIMIT_PER_MINUTE=2):
            for ip in ["203.0.113.1", "203.0.113.2", "203.0.113.3"]:
                for _ in range(3):
                    self.client_class(REMOTE_ADDR=ip).get("/bob-link/")
        self.assertEqual(URLTracker.objects.filter(url=self.b_url).count(), 6)

    def test_limit_zero_records_every_click(self):
        with self.settings(CLICK_RECORD_LIMIT_PER_MINUTE=0):
            for _ in range(40):
                self.client.get("/bob-link/")
        self.assertEqual(URLTracker.objects.filter(url=self.b_url).count(), 40)


class DestinationValidationTests(SecurityBase):
    """ASVS 2.2.1 / 3.7.2 (documented exception: a shortener redirects to external hosts by design)."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.alice)

    def create(self, link, alias="", host="lnk.example.com"):
        return self.client.post("/urls/create/", {"link": link, "title": "T", "custom_url": alias, "description": ""},
                                HTTP_HOST=host)

    def test_script_and_data_schemes_rejected(self):
        for link in ["javascript:alert(1)", "data:text/html,<script>alert(1)</script>", "vbscript:msgbox(1)",
                     "file:///etc/passwd"]:
            self.create(link)
        self.assertFalse(URL.objects.filter(title="T").exists())

    def test_scheme_relative_input_is_stored_as_plain_http(self):
        self.create("//evil.example/", "rel")
        self.assertEqual(URL.objects.get(custom_url="rel").link, "http://evil.example/")

    @expectedFailure  # F8: ftps:// passes form validation but Django refuses to redirect to it (link is dead, 400)
    def test_only_http_https_destinations_accepted(self):
        self.create("ftps://example.com/f", "f1")
        self.create("ftp://example.com/f", "f2")
        self.assertFalse(URL.objects.filter(custom_url__in=["f1", "f2"]).exists())

    @expectedFailure  # F6: links pointing back at the shortener itself allow redirect loops / click amplification
    def test_destination_on_own_domain_rejected(self):
        with self.settings(ALLOWED_HOSTS=["lnk.example.com"]):
            self.create("https://lnk.example.com/other-alias/", "self-ref")
        self.assertFalse(URL.objects.filter(custom_url="self-ref").exists())

    def test_existing_links_keep_redirecting_regardless_of_new_rules(self):
        legacy = URL.objects.create(owner=self.bob, link="ftp://example.com/old", title="old", custom_url="legacy-ftp")
        self.assertEqual(self.client.get(f"/{legacy.custom_url}/")["Location"], "ftp://example.com/old")


class TokenGenerationTests(TestCase):
    @expectedFailure  # F9: generated aliases come from random (Mersenne Twister), not a CSPRNG (ASVS 11.5.1)
    def test_generated_alias_uses_csprng(self):
        from app.url_tracker.models import models_url
        src = inspect.getsource(models_url.generate_unique_link)
        self.assertIn("secrets", src)
        self.assertNotIn("random.choice", src)
