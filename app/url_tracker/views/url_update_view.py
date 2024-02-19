from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.urls import reverse_lazy

from app.url_tracker.models import models_url
from app.url_tracker.forms import CreateURLForm


class UrlUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = models_url.URL
    form_class = CreateURLForm
    template_name = 'app/url_tracker/update_url/index.html'

    def get_success_url(self):
        return reverse_lazy('url_tracker:details', kwargs={'pk': self.object.id})
