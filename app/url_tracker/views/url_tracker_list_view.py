from django.views.generic import ListView

from app.url_tracker.models import models_url_tracker


class UrlTrackerListView(ListView):
    model = models_url_tracker.URLTracker
    template_name = 'app/url_tracker/tracker_list/index.html'
    context_object_name = 'tracker_list'
    paginate_by = 10

    def get_queryset(self):
        return super().get_queryset().filter(url_owner=self.request.user.pk)
