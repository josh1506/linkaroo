"""UX regression tests (docs/UX_AUDIT.md): empty/error states, semantics and navigation markers."""
import re

from django.contrib.auth import get_user_model
from django.template.loader import render_to_string
from django.test import TestCase

from app.url_tracker.models import URL

User = get_user_model()


class UxBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.empty = User.objects.create_user("empty", password="Empty-pass-123", first_name="Erin")
        cls.full = User.objects.create_user("full", password="Full-pass-123", first_name="Fay")
        cls.link = URL.objects.create(owner=cls.full, link="https://example.com/a", title="A", custom_url="a-link")

    def page(self, user, path):
        if user:
            self.client.force_login(user)
        r = self.client.get(path)
        return r, r.content.decode()


class EmptyStateTests(UxBase):
    def test_empty_dashboard_shows_messages_not_charts(self):
        r, html = self.page(self.empty, "/urls/")
        self.assertEqual(r.status_code, 200)
        self.assertNotIn('class="chart"', html)  # charts can't draw without data columns (raw Google error before)
        self.assertIn("No links yet.", html)
        self.assertIn("No clicks yet.", html)

    def test_populated_dashboard_draws_labelled_charts(self):
        _, html = self.page(self.full, "/urls/")
        charts = re.findall(r'<div id="[^"]+" class="chart" role="img" aria-label="[^"]+">', html)
        self.assertEqual(len(charts), 4)

    def test_empty_link_list_offers_next_step_and_no_pagination(self):
        _, html = self.page(self.empty, "/urls/list/")
        self.assertIn("No links yet.", html)
        self.assertIn('href="/urls/create/"', html)
        self.assertNotIn('class="pagination"', html)

    def test_empty_click_log(self):
        _, html = self.page(self.empty, "/urls/tracker/list/")
        self.assertIn("No clicks recorded yet.", html)

    def test_pagination_marks_only_current_page(self):
        for i in range(12):
            URL.objects.create(owner=self.full, link=f"https://example.com/{i}", title=f"T{i}")
        _, html = self.page(self.full, "/urls/list/?page=2")
        self.assertIn('class="pagination"', html)
        self.assertEqual(html.count('aria-current="page"'), 2)  # sidebar section + current page number


class ErrorPageTests(UxBase):
    def test_unknown_short_link_gets_branded_404(self):
        r, html = self.page(None, "/no-such-alias/")
        self.assertEqual(r.status_code, 404)
        self.assertIn("Link not found", html)
        self.assertIn('href="/"', html)

    def test_500_page_renders_without_context(self):
        html = render_to_string("500.html")
        self.assertIn("Something went wrong", html)
        self.assertNotIn("{%", html)


class SemanticsTests(UxBase):
    PAGES = [(None, "/"), (None, "/auth/login/"), (None, "/auth/signup/"), ("full", "/urls/"), ("full", "/urls/list/"),
             ("full", "/urls/create/"), ("full", "/urls/tracker/list/")]

    def test_every_page_has_skip_link_and_exactly_one_h1(self):
        for who, path in self.PAGES:
            self.client.logout()
            _, html = self.page(getattr(self, who) if who else None, path)
            self.assertIn('href="#main-content"', html, path)
            self.assertIn('id="main-content"', html, path)
            self.assertEqual(len(re.findall(r"<h1\b", html)), 1, path)

    def test_sidebar_marks_current_section(self):
        cases = {"/urls/": "Overview", "/urls/list/": "Manage URL", "/urls/create/": "Manage URL",
                 f"/urls/detail/{self.link.pk}/": "Manage URL", "/urls/tracker/list/": "URL Tracker"}
        for path, label in cases.items():
            _, html = self.page(self.full, path)
            current = re.findall(r'aria-current="page">([^<]+)</a>', html)
            self.assertEqual(current, [label], path)

    def test_decorative_images_have_empty_alt(self):
        _, html = self.page(None, "/")
        imgs = re.findall(r"<img\b[^>]*>", html)
        self.assertTrue(imgs)
        for tag in imgs:
            self.assertRegex(tag, r'\salt="', tag)
            self.assertNotRegex(tag, r'alt="(logo|background)"', tag)
            self.assertNotIn('src=""', tag)
