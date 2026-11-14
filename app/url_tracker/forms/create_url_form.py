from django import forms
from django.core.validators import validate_slug
from app.url_tracker.models import URL

# First path segments owned by other routes in config/urls.py; an alias here could never be reached.
RESERVED_ALIASES = {'admin', 'auth', 'urls', 'static', 'media', '__debug__', '400', '403', '404', '500'}
ALIAS_MAX_LENGTH = 64


class CreateURLForm(forms.ModelForm):
    link = forms.URLField(required=True, widget=forms.TextInput(attrs={'placeholder': 'URL/Link', 'class': 'form-control', 'autofocus': 'autofocus'}))
    title = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Link Title', 'class': 'form-control'}))
    custom_url = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Insert custom URL (optional)', 'class': 'form-control'}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'placeholder': 'Insert link description (optional)', 'class': 'form-control'}))

    class Meta:
        model = URL
        fields = ['link', 'title', 'custom_url', 'description']

    def clean_custom_url(self):
        alias = self.cleaned_data['custom_url'].strip()
        current = self.instance.custom_url if self.instance.pk else None

        # Editing: blank or unchanged keeps the existing alias, so links already shared keep working.
        if current and alias in ('', current):
            return current
        if not alias:
            return alias  # new URL: model generates a random alias

        validate_slug(alias)
        if len(alias) > ALIAS_MAX_LENGTH:
            raise forms.ValidationError(f"Use at most {ALIAS_MAX_LENGTH} characters.")
        if alias.lower() in RESERVED_ALIASES:
            raise forms.ValidationError("This alias is reserved. Please choose another.")
        return alias
