import json
from io import StringIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from app.url_tracker.models import URL, URLTracker


class DataFingerprintTests(TestCase):
    def fingerprint(self):
        out = StringIO()
        call_command("data_fingerprint", "--json", stdout=out)
        return json.loads(out.getvalue())

    def setUp(self):
        owner = get_user_model().objects.create_user("owner", password="Owner-pass-123")
        self.url = URL.objects.create(owner=owner, link="https://example.com", title="T", custom_url="t")
        self.click = URLTracker.objects.create(url=self.url)

    def test_stable_and_read_only(self):
        first, second = self.fingerprint(), self.fingerprint()
        self.assertEqual(first, second)
        self.assertEqual((URL.objects.count(), URLTracker.objects.count()), (1, 1))
        self.assertEqual(first["tables"]["url_tracker_urltracker"]["rows"], 1)
        self.assertEqual(first["integrity"]["click_owner_drift"], 0)

    def test_detects_content_change_with_equal_row_counts(self):
        before = self.fingerprint()
        URL.objects.filter(pk=self.url.pk).update(title="changed")
        after = self.fingerprint()
        self.assertEqual(before["tables"]["url_tracker_url"]["rows"], after["tables"]["url_tracker_url"]["rows"])
        self.assertNotEqual(before["tables"]["url_tracker_url"]["sha256"], after["tables"]["url_tracker_url"]["sha256"])

    def test_reports_denormalized_owner_drift(self):
        URLTracker.objects.bulk_create([URLTracker(url=self.url)])  # bulk_create skips save(): url_owner stays NULL
        self.assertEqual(self.fingerprint()["integrity"]["click_owner_drift"], 1)
