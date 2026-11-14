from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class AuthFlowTests(TestCase):
    def test_landing_renders(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_signup_then_login_then_logout(self):
        r = self.client.post(reverse("users:signup"), {
            "username": "carol", "first_name": "Carol", "last_name": "C", "email": "carol@example.com",
            "password1": "S3cure-pass-xyz", "password2": "S3cure-pass-xyz"})
        self.assertRedirects(r, reverse("users:login"))
        self.assertTrue(User.objects.get(username="carol").check_password("S3cure-pass-xyz"))

        r = self.client.post(reverse("users:login"), {"username": "carol", "password": "S3cure-pass-xyz"})
        self.assertRedirects(r, reverse("url_tracker:overview"))

        r = self.client.post(reverse("users:logout"))
        self.assertRedirects(r, reverse("users:login"))
        self.assertEqual(self.client.get(reverse("url_tracker:overview")).status_code, 302)

    def test_bad_password_rejected(self):
        User.objects.create_user("dave", password="right-pass-123")
        r = self.client.post(reverse("users:login"), {"username": "dave", "password": "wrong"})
        self.assertEqual(r.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_existing_password_hashes_still_work(self):
        # Auth compatibility: users created before the upgrade must still log in.
        User.objects.create_user("erin", password="legacy-pass-123")
        self.assertTrue(self.client.login(username="erin", password="legacy-pass-123"))
