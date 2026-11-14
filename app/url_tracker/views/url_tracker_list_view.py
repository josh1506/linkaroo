from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from app.url_tracker.models import models_url_tracker


class UrlTrackerListView(LoginRequiredMixin, ListView):
    model = models_url_tracker.URLTracker
    template_name = 'app/url_tracker/tracker_list/index.html'
    context_object_name = 'tracker_list'
    paginate_by = 10

    def get_queryset(self):
        # Authorize on the link's current owner; the denormalized url_owner goes stale if a link is reassigned (F7).
        return super().get_queryset().filter(url__owner=self.request.user).select_related('url')
