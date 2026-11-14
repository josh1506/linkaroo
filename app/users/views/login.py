from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.urls import reverse_lazy

from app.utils.throttle import client_ip, hit, hits

LOCK_SECONDS = 15 * 60
MAX_ACCOUNT_FAILURES = 5   # per client + username: stops guessing one account
MAX_CLIENT_FAILURES = 30   # per client, any username: stops password spraying


def _keys(request):
    ip = client_ip(request)
    username = request.POST.get('username', '').strip().lower()
    return f"login-failures:{ip}:{username}", f"login-failures:{ip}"


class ThrottledLoginMixin:
    """Lockout enforced inside the form, so every login entrypoint using it (site and admin) is covered."""

    def clean(self):
        account_key, client_key = _keys(self.request)
        # Checked before super().clean(), which calls authenticate(): a locked attempt never tests the password.
        if hits(account_key) >= MAX_ACCOUNT_FAILURES or hits(client_key) >= MAX_CLIENT_FAILURES:
            raise ValidationError("Too many failed login attempts. Please try again in 15 minutes.", code="throttled")
        try:
            cleaned = super().clean()
        except ValidationError:
            hit(account_key, LOCK_SECONDS)
            hit(client_key, LOCK_SECONDS)
            raise
        cache.delete(account_key)
        return cleaned


class ThrottledAuthenticationForm(ThrottledLoginMixin, AuthenticationForm):
    pass


class ThrottledAdminAuthenticationForm(ThrottledLoginMixin, AdminAuthenticationForm):
    pass


class CustomLoginView(LoginView):
    template_name = 'app/users/login.html'
    redirect_authenticated_user = True
    authentication_form = ThrottledAuthenticationForm

    def get_success_url(self):
        return reverse_lazy('url_tracker:overview')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        return form

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if form.has_error(NON_FIELD_ERRORS, 'throttled'):
            response.status_code = 429
        return response
