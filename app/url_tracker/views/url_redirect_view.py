from django.http import HttpResponseRedirect, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404
from app.url_tracker.models import URL, URLTracker


def redirect_view(request, custom_url):
    allowed_methods = ["GET"]

    if request.method not in allowed_methods:
        return HttpResponseNotAllowed(allowed_methods)

    url_model = get_object_or_404(URL, custom_url=custom_url)
    URLTracker.objects.create(url=url_model)

    return HttpResponseRedirect(url_model.link)
