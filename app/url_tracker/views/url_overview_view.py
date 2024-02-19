import json

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

from app.url_tracker.utils import (
    get_links_created_day_range,
    get_total_active_urls,
    get_top_5_links,
    get_url_clicks_day_range
)


class UrlOverviewTemplateView(LoginRequiredMixin, generic.TemplateView):
    template_name = 'app/url_tracker/overview/index.html'

    def get_context_data(self, **kwargs):
        user_url = self.request.user.url.all()

        kwargs['top_links'] = get_top_5_links(user_url)
        kwargs['total_active_url'] = json.dumps(get_total_active_urls(user_url))
        kwargs['latest_total_clicks'] = json.dumps(get_url_clicks_day_range(user_url, 7))
        kwargs['total_links_data'] = json.dumps(get_links_created_day_range(user_url, 7))
        kwargs['total_clicks_data'] = json.dumps(get_url_clicks_day_range(user_url, 7))

        return kwargs
