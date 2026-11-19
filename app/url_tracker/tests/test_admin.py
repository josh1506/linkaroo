from django.contrib.auth import get_user_model
from django.test import TestCase

from app.url_tracker.models import URL, URLTracker


class AdminSmokeTests(TestCase):
    """Jazzmin-themed admin pages render (guards framework/theme upgrades)."""

    def test_admin_pages_render(self):
        admin = get_user_model().objects.create_superuser("root", password="root-pass-123")
        url = URL.objects.create(owner=admin, link="https://example.com", title="T", custom_url="t1")
        URLTracker.objects.create(url=url)
        self.client.force_login(admin)
        for path in ["/admin/", "/admin/url_tracker/url/", f"/admin/url_tracker/url/{url.pk}/change/",
                     "/admin/url_tracker/urltracker/", "/admin/auth/user/"]:
            self.assertEqual(self.client.get(path).status_code, 200, path)

    def test_admin_requires_staff(self):
        get_user_model().objects.create_user("plain", password="plain-pass-123")
        self.client.login(username="plain", password="plain-pass-123")
        self.assertEqual(self.client.get("/admin/").status_code, 302)
