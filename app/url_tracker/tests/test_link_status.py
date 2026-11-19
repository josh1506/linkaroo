"""UPG-002 phases 1-2: disable/enable links, copy short link, dashboard activity charts."""
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from app.url_tracker.models import URL, URLTracker
from app.url_tracker.utils import get_click_activity

User = get_user_model()


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user("alice", password="pw-Alice-123!")
        cls.bob = User.objects.create_user("bob", password="pw-Bob-123!")
        cls.url = URL.objects.create(owner=cls.alice, link="https://example.com/a", title="A", custom_url="alice-link")

    def toggle(self, url=None):
        return self.client.post(reverse("url_tracker:toggle-status", kwargs={"pk": (url or self.url).pk}))


class DisableLinkTests(Base):
    def setUp(self):
        self.client.force_login(self.alice)

    def test_new_links_are_enabled(self):
        self.assertEqual(self.url.status, URL.ACTIVE_STATUS)

    def test_disabled_link_404s_without_recording_click_and_reenable_restores_it(self):
        r = self.toggle()
        self.assertRedirects(r, reverse("url_tracker:details", kwargs={"pk": self.url.pk}))
        self.client.logout()
        r = self.client.get("/alice-link/")
        self.assertEqual(r.status_code, 404)
        self.assertContains(r, "Link not found", status_code=404)
        self.assertFalse(URLTracker.objects.exists())

        self.client.force_login(self.alice)
        self.toggle()
        self.assertEqual(self.client.get("/alice-link/")["Location"], "https://example.com/a")
        self.assertEqual(URLTracker.objects.count(), 1)

    def test_disabling_keeps_click_history_and_alias(self):
        self.client.get("/alice-link/")
        self.toggle()
        self.url.refresh_from_db()
        self.assertEqual((self.url.custom_url, self.url.tracker.count()), ("alice-link", 1))

    def test_only_owner_can_toggle(self):
        self.client.force_login(self.bob)
        self.assertEqual(self.toggle().status_code, 404)
        self.url.refresh_from_db()
        self.assertEqual(self.url.status, URL.ACTIVE_STATUS)

    def test_toggle_requires_login_and_post(self):
        path = reverse("url_tracker:toggle-status", kwargs={"pk": self.url.pk})
        self.assertEqual(self.client.get(path).status_code, 405)
        self.client.logout()
        self.assertTrue(self.client.post(path)["Location"].startswith("/auth/login/"))

    def test_details_and_list_show_status_and_toggle(self):
        html = self.client.get(reverse("url_tracker:details", kwargs={"pk": self.url.pk})).content.decode()
        self.assertIn("Enabled", html)
        self.assertIn(">Disable</button>", html)
        self.toggle()
        html = self.client.get(reverse("url_tracker:list")).content.decode()
        self.assertIn("Disabled", html)


class CopyLinkTests(Base):
    def test_details_and_list_offer_full_short_url_copy_button(self):
        self.client.force_login(self.alice)
        for path in (reverse("url_tracker:details", kwargs={"pk": self.url.pk}), reverse("url_tracker:list")):
            r = self.client.get(path)
            self.assertContains(r, 'data-copy="http://testserver/alice-link/"')
            self.assertContains(r, 'aria-label="Copy short link for A"')
            self.assertContains(r, 'aria-live="polite"')


class ActivityChartTests(Base):
    def click(self, when, url=None):
        with mock.patch("django.utils.timezone.now", return_value=when):
            URLTracker.objects.create(url=url or self.url)

    def test_buckets_by_day_weekday_and_hour_for_owner_only(self):
        now = timezone.now()
        local_now = timezone.localtime(now)
        self.click(now)
        self.click(now)
        self.click(now - timedelta(days=60))  # outside 30-day trend, inside 90-day pattern
        self.click(now - timedelta(days=200))  # outside both windows
        self.click(now, url=URL.objects.create(owner=self.bob, link="https://example.com/b", title="B"))

        a = get_click_activity(URLTracker.objects.filter(url__owner=self.alice), 30, 90)

        self.assertEqual(a["per_day"][0], ["Day", "Clicks"])
        self.assertEqual(len(a["per_day"]), 32)  # header + 31 days, today included
        self.assertEqual(a["per_day"][-1], [local_now.strftime("%b %d"), 2])
        self.assertEqual(sum(n for _, n in a["per_day"][1:]), 2)
        self.assertEqual(sum(n for _, n in a["per_weekday"][1:]), 3)
        self.assertEqual(sum(n for _, n in a["per_hour"][1:]), 3)
        self.assertGreaterEqual(a["per_weekday"][local_now.isoweekday()][1], 2)  # row 0 is the header
        label, n = a["per_hour"][1 + local_now.hour]
        self.assertEqual(label, f"{local_now.hour:02d}:00")
        self.assertGreaterEqual(n, 2)

    def test_dashboard_context_has_enabled_disabled_counts(self):
        URL.objects.create(owner=self.alice, link="https://example.com/off", title="Off", status=URL.INACTIVE_STATUS)
        self.client.force_login(self.alice)
        ctx = self.client.get(reverse("url_tracker:overview")).context
        self.assertEqual(ctx["enabled_disabled"], [["Status", "Links"], ["Enabled", 1], ["Disabled", 1]])
