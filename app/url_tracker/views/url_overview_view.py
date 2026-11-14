from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
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
        user_url = list(self.request.user.url.annotate(click_count=Count('tracker')))
        clicks_7_days = get_url_clicks_day_range(user_url, 7)

        # Plain data; the template serializes it with |json_script (no inline JS, CSP-compatible).
        kwargs['top_links'] = get_top_5_links(user_url)
        kwargs['total_active_url'] = get_total_active_urls(user_url)
        kwargs['latest_total_clicks'] = clicks_7_days  # both charts used identical data; computed once
        kwargs['total_links_data'] = get_links_created_day_range(user_url, 7)
        kwargs['total_clicks_data'] = clicks_7_days
        # Charts can't be drawn without at least one link (no data columns); templates show an empty state instead.
        kwargs['has_links'] = bool(user_url)

        return kwargs
