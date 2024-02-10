from django.views import generic
from django.urls import reverse_lazy

from app.url_tracker.forms.create_url_form import CreateURLForm


class URLCreateView(generic.CreateView):
    template_name = 'app/url_tracker/create_url/index.html'
    form_class = CreateURLForm
    success_url = reverse_lazy('url_tracker:list')
