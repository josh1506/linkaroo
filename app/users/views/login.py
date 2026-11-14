from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.urls import reverse_lazy

# ponytail: Django's default per-process LocMemCache, so the limit is per worker; configure a shared CACHES (e.g. Redis/DB) for multi-worker deploys.
MAX_FAILURES = 5
LOCK_SECONDS = 15 * 60


def _failure_key(request):
    # Keyed on IP + username: a bad actor can't lock a victim out from everywhere, and IP rotation alone doesn't reset one account.
    username = request.POST.get('username', '').strip().lower()
    return f"login-failures:{request.META.get('REMOTE_ADDR', '')}:{username}"


class ThrottledAuthenticationForm(AuthenticationForm):
    def clean(self):
        # Check before super().clean(), which calls authenticate(); a locked attempt never tests the password.
        if cache.get(_failure_key(self.request), 0) >= MAX_FAILURES:
            raise ValidationError("Too many failed login attempts. Please try again in 15 minutes.", code="throttled")
        return super().clean()


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

    def form_valid(self, form):
        cache.delete(_failure_key(self.request))
        return super().form_valid(form)

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if form.has_error(NON_FIELD_ERRORS, 'throttled'):
            response.status_code = 429
        else:
            key = _failure_key(self.request)
            cache.add(key, 0, LOCK_SECONDS)
            cache.incr(key)
        return response
