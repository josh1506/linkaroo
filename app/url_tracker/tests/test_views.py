import json
from datetime import datetime, timezone as dt_timezone
from unittest import mock

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from app.url_tracker.models import URL, URLTracker

User = get_user_model()


class Base(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user("alice", password="pw-Alice-123!", first_name="Alice")
        cls.bob = User.objects.create_user("bob", password="pw-Bob-123!")
        cls.a_url = URL.objects.create(owner=cls.alice, link="https://example.com/a", title="A", custom_url="alice-link")
        cls.b_url = URL.objects.create(owner=cls.bob, link="https://example.com/b", title="B", custom_url="bob-link")


class RedirectContractTests(Base):
    """Public redirect contract: GET /<alias>/ -> 302 to stored link, one click recorded."""

    def test_get_redirects_302_and_records_click(self):
        r = self.client.get("/alice-link/")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "https://example.com/a")
        t = URLTracker.objects.get()
        self.assertEqual((t.url, t.url_owner), (self.a_url, self.alice))

    def test_unknown_alias_404_no_click(self):
        self.assertEqual(self.client.get("/nope/").status_code, 404)
        self.assertFalse(URLTracker.objects.exists())

    def test_post_not_allowed(self):
        self.assertEqual(self.client.post("/alice-link/").status_code, 405)
        self.assertFalse(URLTracker.objects.exists())

    def test_generated_alias_is_12_chars_and_redirects(self):
        u = URL.objects.create(owner=self.alice, link="https://example.com/gen", title="G")
        self.assertEqual(len(u.custom_url), 12)
        self.assertEqual(self.client.get(f"/{u.custom_url}/")["Location"], "https://example.com/gen")


class OwnerFlowTests(Base):
    def setUp(self):
        self.client.login(username="alice", password="pw-Alice-123!")

    def test_login_required(self):
        self.client.logout()
        for name, kw in [("overview", {}), ("create", {}), ("list", {}), ("tracker-list", {}),
                         ("details", {"pk": self.a_url.pk}), ("update", {"pk": self.a_url.pk}),
                         ("delete", {"pk": self.a_url.pk})]:
            r = self.client.get(reverse(f"url_tracker:{name}", kwargs=kw))
            self.assertEqual(r.status_code, 302, name)
            self.assertTrue(r["Location"].startswith("/auth/login/"), name)

    def test_create_sets_owner(self):
        r = self.client.post(reverse("url_tracker:create"),
                             {"link": "https://example.com/new", "title": "New", "custom_url": "", "description": ""})
        self.assertRedirects(r, reverse("url_tracker:list"))
        u = URL.objects.get(title="New")
        self.assertEqual(u.owner, self.alice)
        self.assertEqual(len(u.custom_url), 12)

    def test_create_rejects_unsafe_scheme(self):
        r = self.client.post(reverse("url_tracker:create"),
                             {"link": "javascript:alert(1)", "title": "X", "custom_url": "", "description": ""})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(URL.objects.filter(title="X").exists())

    def test_create_duplicate_alias_rejected(self):
        r = self.client.post(reverse("url_tracker:create"),
                             {"link": "https://example.com/x", "title": "X", "custom_url": "bob-link", "description": ""})
        self.assertEqual(r.status_code, 200)
        self.assertFalse(URL.objects.filter(title="X").exists())

    def test_list_and_tracker_list_show_only_own(self):
        self.client.get("/bob-link/")
        self.client.get("/alice-link/")
        urls = list(self.client.get(reverse("url_tracker:list")).context["url_list"])
        self.assertEqual(urls, [self.a_url])
        trackers = list(self.client.get(reverse("url_tracker:tracker-list")).context["tracker_list"])
        self.assertEqual([t.url for t in trackers], [self.a_url])

    def test_own_detail_update_delete(self):
        self.assertEqual(self.client.get(reverse("url_tracker:details", kwargs={"pk": self.a_url.pk})).status_code, 200)
        r = self.client.post(reverse("url_tracker:update", kwargs={"pk": self.a_url.pk}),
                             {"link": "https://example.com/a2", "title": "A2", "custom_url": "alice-link", "description": ""})
        self.assertEqual(r.status_code, 302)
        self.a_url.refresh_from_db()
        self.assertEqual((self.a_url.link, self.a_url.custom_url), ("https://example.com/a2", "alice-link"))
        r = self.client.post(reverse("url_tracker:delete", kwargs={"pk": self.a_url.pk}))
        self.assertRedirects(r, reverse("url_tracker:list"))
        self.assertFalse(URL.objects.filter(pk=self.a_url.pk).exists())

    def test_overview_renders_counts(self):
        self.client.get("/alice-link/")
        self.client.get("/alice-link/")
        self.client.get("/bob-link/")
        r = self.client.get(reverse("url_tracker:overview"))
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["top_links"], [
            {"id": str(self.a_url.id), "link": self.a_url.link, "title": "A", "total_clicks": 2}])


class AnalyticsDayBucketTests(Base):
    """Charts must label days in settings.TIME_ZONE (Asia/Manila), the same zone clicks are bucketed in."""

    def test_click_after_local_midnight_counts_on_local_today(self):
        # 01:00 Manila on Mar 10 == 17:00 UTC on Mar 09 (date far from fixture creation).
        early_morning = datetime(2030, 3, 9, 17, 0, tzinfo=dt_timezone.utc)
        with mock.patch("django.utils.timezone.now", return_value=early_morning):
            fresh = URL.objects.create(owner=self.alice, link="https://example.com/t", title="T")
            self.client.get(f"/{fresh.custom_url}/")
            self.client.login(username="alice", password="pw-Alice-123!")
            ctx = self.client.get(reverse("url_tracker:overview")).context

        clicks = json.loads(ctx["total_clicks_data"])
        header, today = clicks[0], clicks[-1]
        self.assertEqual(today[0], "Mar 10")
        self.assertEqual(today[header.index("T")], 1)
        self.assertEqual(sum(row[header.index("T")] for row in clicks[1:]), 1)

        links = json.loads(ctx["total_links_data"])
        self.assertEqual(links[-1][:2], ["Mar 10", 1])

    def test_chart_totals_match_raw_rows(self):
        for _ in range(3):
            self.client.get("/alice-link/")
        self.client.login(username="alice", password="pw-Alice-123!")
        ctx = self.client.get(reverse("url_tracker:overview")).context
        clicks = json.loads(ctx["total_clicks_data"])
        col = clicks[0].index("A")
        self.assertEqual(sum(r[col] for r in clicks[1:]), URLTracker.objects.filter(url=self.a_url).count())
        self.assertEqual(ctx["latest_total_clicks"], ctx["total_clicks_data"])
        self.assertEqual(json.loads(ctx["total_active_url"]), [["Active", "Inactive"], ["Active", 1], ["Inactive", 0]])


class QueryBudgetTests(Base):
    """Dashboard/redirect query counts must not grow with the number of links."""

    def test_overview_query_count_constant(self):
        self.client.login(username="alice", password="pw-Alice-123!")
        self.client.get(reverse("url_tracker:overview"))  # warm session
        with self.assertNumQueries(4):  # session, user, urls+counts, grouped clicks
            self.client.get(reverse("url_tracker:overview"))
        for i in range(10):
            u = URL.objects.create(owner=self.alice, link=f"https://example.com/{i}", title=f"T{i}")
            self.client.get(f"/{u.custom_url}/")
        with self.assertNumQueries(4):
            self.client.get(reverse("url_tracker:overview"))

    def test_redirect_two_queries(self):
        with self.assertNumQueries(2):  # lookup + insert
            self.client.get("/alice-link/")


class AliasValidationTests(Base):
    def setUp(self):
        self.client.login(username="alice", password="pw-Alice-123!")

    def post_create(self, alias):
        return self.client.post(reverse("url_tracker:create"),
                                {"link": "https://example.com/x", "title": "X", "custom_url": alias, "description": ""})

    def post_update(self, url, alias):
        return self.client.post(reverse("url_tracker:update", kwargs={"pk": url.pk}),
                                {"link": url.link, "title": url.title, "custom_url": alias, "description": ""})

    def test_rejects_reserved_slash_space_and_too_long(self):
        for alias in ["admin", "Auth", "urls", "a/b", "has space", "x" * 65]:
            self.assertEqual(self.post_create(alias).status_code, 200, alias)
        self.assertFalse(URL.objects.filter(title="X").exists())

    def test_accepts_slug_alias_and_redirects(self):
        self.assertEqual(self.post_create("My_link-2024").status_code, 302)
        self.assertEqual(self.client.get("/My_link-2024/")["Location"], "https://example.com/x")

    def test_blank_alias_on_edit_keeps_existing_link(self):
        self.post_update(self.a_url, "")
        self.a_url.refresh_from_db()
        self.assertEqual(self.a_url.custom_url, "alice-link")

    def test_legacy_alias_outside_new_rules_still_editable_and_redirects(self):
        legacy = URL.objects.create(owner=self.alice, link="https://example.com/l", title="L", custom_url="old alias!")
        self.assertEqual(self.post_update(legacy, "old alias!").status_code, 302)
        legacy.refresh_from_db()
        self.assertEqual(legacy.custom_url, "old alias!")
        self.assertEqual(self.client.get("/old alias!/").status_code, 302)


class CrossUserAccessTests(Base):
    """Security AC1: users cannot read, modify or delete another user's URL."""

    def setUp(self):
        self.client.login(username="alice", password="pw-Alice-123!")

    def test_cannot_view_other_users_url(self):
        r = self.client.get(reverse("url_tracker:details", kwargs={"pk": self.b_url.pk}))
        self.assertEqual(r.status_code, 404)

    def test_cannot_update_other_users_url(self):
        r = self.client.post(reverse("url_tracker:update", kwargs={"pk": self.b_url.pk}),
                             {"link": "https://evil.example/", "title": "pwn", "custom_url": "bob-link", "description": ""})
        self.assertEqual(r.status_code, 404)
        self.b_url.refresh_from_db()
        self.assertEqual(self.b_url.link, "https://example.com/b")

    def test_cannot_delete_other_users_url(self):
        r = self.client.post(reverse("url_tracker:delete", kwargs={"pk": self.b_url.pk}))
        self.assertEqual(r.status_code, 404)
        self.assertTrue(URL.objects.filter(pk=self.b_url.pk).exists())

    def test_unknown_pk_is_404_not_500(self):
        r = self.client.get(reverse("url_tracker:details", kwargs={"pk": "00000000-0000-0000-0000-000000000000"}))
        self.assertEqual(r.status_code, 404)
