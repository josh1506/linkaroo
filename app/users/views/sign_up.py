from django.views.generic import CreateView
from django.contrib.auth import login
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model

from app.users.forms import RegistrationForm


User = get_user_model()


class SignUpTemplateView(CreateView):
    template_name = 'app/users/signup.html'
    form_class = RegistrationForm
    success_url = reverse_lazy('url_tracker:overview')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)

        for field in form.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

        return form
