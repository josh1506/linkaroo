import json

from django.views import generic

from app.url_tracker.utils import get_latest_7_days_total_clicks, get_total_active_urls, get_top_5_links, get_links_created_day_range


class UrlOverviewTemplateView(generic.TemplateView):
    template_name = 'app/url_tracker/overview/index.html'

    def get_context_data(self, **kwargs):
        user_url = self.request.user.url.all()

        kwargs['top_links'] = get_top_5_links(user_url)
        kwargs['total_active_url'] = json.dumps(get_total_active_urls(user_url))
        kwargs['latest_total_clicks'] = json.dumps(get_latest_7_days_total_clicks(user_url))
        kwargs['total_links_data'] = json.dumps(get_links_created_day_range(user_url, 7))

        kwargs['total_clicks_data'] = json.dumps({
            'clicks_count': 0,
            'recent_7_days_created': [
                ['2013', 1000, 400, 200],
                ['2014', 1170, 460, 400],
                ['2015', 660, 1120, 300],
                ['2016', 1030, 540, 700]
            ]
        })

        return kwargs
