from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from app.url_tracker.models import models_url


class UrlListView(LoginRequiredMixin, generic.ListView):
    model = models_url.URL
    template_name = 'app/url_tracker/list_url/index.html'
    context_object_name = 'url_list'
    paginate_by = 10

    def get_queryset(self):
        return self.model.objects.filter(owner=self.request.user.pk)
