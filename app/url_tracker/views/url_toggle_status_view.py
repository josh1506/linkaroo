from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.views import View

from app.url_tracker.models import URL


class UrlToggleStatusView(LoginRequiredMixin, View):
    """POST only: disable an enabled link or re-enable a disabled one. Owner-scoped (others get 404)."""
    http_method_names = ['post']

    def post(self, request, pk):
        url = get_object_or_404(URL, pk=pk, owner=request.user)
        url.status = URL.INACTIVE_STATUS if url.status == URL.ACTIVE_STATUS else URL.ACTIVE_STATUS
        url.save(update_fields=['status', 'updated_at'])
        return redirect('url_tracker:details', pk=url.pk)
