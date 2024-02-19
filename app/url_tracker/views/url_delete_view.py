from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.urls import reverse_lazy

from app.url_tracker.models import models_url


class UrlDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = models_url.URL
    success_url = reverse_lazy("url_tracker:list")
