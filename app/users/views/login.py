from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy


class CustomLoginView(LoginView):
    template_name = 'app/users/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        return reverse_lazy('url_tracker:overview')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        return form
