from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from app.url_tracker.models import models_url


class UrlDetailView(LoginRequiredMixin, generic.DetailView):
    model = models_url.URL
    template_name = 'app/url_tracker/detail_url/index.html'
    lookup_url_kwarg = 'pk'

    def get_object(self, queryset=None):
        return self.model.objects.get(pk=self.kwargs['pk'])
