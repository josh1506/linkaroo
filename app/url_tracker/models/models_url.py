import random
import string
from turtle import onkey

from django.contrib.auth import get_user_model
from django.db import models
from django_extensions.db.models import ActivatorModel

from app.utils.model import Model


User = get_user_model()

def generate_unique_link():
    # Define characters to be used in short link
    characters = string.ascii_letters + string.digits

    # Generate random character with length of 12
    custom_url = "".join(random.choice(characters) for _ in range(12))

    # Ensure the short link is unique
    while URL.objects.filter(custom_url=custom_url).exists():
        custom_url = "".join(random.choice(characters) for _ in range(12))

    return custom_url


class URL(ActivatorModel, Model):
    class Meta:
        verbose_name = "URL"
        verbose_name_plural = "URLs"
        ordering = ["-created_at"]

    link = models.URLField(verbose_name="Link")
    title = models.CharField(max_length=255, verbose_name="Title")
    custom_url = models.CharField(max_length=255, verbose_name="Shortened", blank=True, null=True, unique=True)
    owner = models.ForeignKey(
        User, verbose_name="Owner", on_delete=models.CASCADE, related_name="url", blank=True, null=True
    )
    description = models.TextField(verbose_name="Description", blank=True, null=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.custom_url:
            self.custom_url = generate_unique_link()
        super().save(*args, **kwargs)
