from django.db import models

from .models_url import URL
from app.utils.model import Model


class URLTracker(Model):
    class Meta:
        verbose_name = "URL Tracker"
        verbose_name_plural = "URL Tracker"
        ordering = ["-created_at"]

    url = models.ForeignKey(URL, on_delete=models.CASCADE, related_name="tracker", verbose_name="URL")

    def __str__(self):
        return self.url.title
