from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic
from django.urls import reverse_lazy

from app.url_tracker.forms.create_url_form import CreateURLForm


class URLCreateView(LoginRequiredMixin, generic.CreateView):
    template_name = 'app/url_tracker/create_url/index.html'
    form_class = CreateURLForm
    success_url = reverse_lazy('url_tracker:list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)
