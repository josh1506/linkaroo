from django.conf import settings
from django.urls import reverse_lazy
from django.views.generic import CreateView

from app.users.forms import RegistrationForm
from app.utils.throttle import client_ip, hit, hits

WINDOW_SECONDS = 60 * 60


def _signup_key(request):
    return f"signups:{client_ip(request)}"


class SignUpTemplateView(CreateView):
    template_name = 'app/users/signup.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('users:login')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        return form

    def post(self, request, *args, **kwargs):
        # Accounts created per client per hour (threat model F4: account farming for phishing links).
        if hits(_signup_key(request)) >= settings.SIGNUPS_PER_CLIENT_PER_HOUR:
            self.object = None
            form = self.get_form()
            form.add_error(None, "Too many accounts were created from your network. Please try again later.")
            return self.render_to_response(self.get_context_data(form=form), status=429)
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        hit(_signup_key(self.request), WINDOW_SECONDS)
        return super().form_valid(form)
