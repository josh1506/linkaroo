from django.db import models
from django.contrib.auth import get_user_model

from .models_url import URL
from app.utils.model import Model


User = get_user_model()


class URLTracker(Model):
    class Meta:
        verbose_name = "URL Tracker"
        verbose_name_plural = "URL Tracker"
        ordering = ["-created_at"]

    url = models.ForeignKey(URL, on_delete=models.CASCADE, related_name="tracker", verbose_name="URL")
    url_owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="owned_url_tracker",
        verbose_name="URL Owner",
        blank=True,
        null=True
    )

    def __str__(self):
        return self.url.title

    def save(self, *args, **kwargs):
        self.url_owner = self.url.owner
        super().save(*args, **kwargs)
