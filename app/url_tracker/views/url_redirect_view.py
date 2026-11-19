from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from app.url_tracker.models import URL, URLTracker
from app.utils.throttle import client_ip, hit


def redirect_view(request, custom_url):
    allowed_methods = ["GET"]

    if request.method not in allowed_methods:
        return HttpResponseNotAllowed(allowed_methods)

<<<<<<< HEAD
    # Disabled links get the same branded 404 as unknown ones and record no click.
    url_model = get_object_or_404(URL, custom_url=custom_url, status=URL.ACTIVE_STATUS)
=======
    url_model = get_object_or_404(URL, custom_url=custom_url)
>>>>>>> origin/master

    # Always redirect; record at most N clicks per client per link per minute (F5: click inflation / write amplification).
    limit = settings.CLICK_RECORD_LIMIT_PER_MINUTE
    if not limit or hit(f"clicks:{client_ip(request)}:{url_model.pk}", 60) <= limit:
        URLTracker.objects.create(url=url_model)

    return HttpResponseRedirect(url_model.link)
