from app.url_tracker.views.url_delete_view import UrlDeleteView
from app.url_tracker.views.url_detail_view import UrlDetailView
from app.url_tracker.views.url_list_view import UrlListView
from app.url_tracker.views.url_update_view import UrlUpdateView
from app.url_tracker.views.url_create_view import URLCreateView
from app.url_tracker.views.url_overview_view import UrlOverviewTemplateView
from app.url_tracker.views.url_tracker_list_view import UrlTrackerListView
from app.url_tracker.views.url_redirect_view import redirect_view


__all__ = [
    URLCreateView,
    UrlOverviewTemplateView,
    UrlDetailView,
    UrlListView,
    UrlUpdateView,
    UrlTrackerListView,
    redirect_view
]
