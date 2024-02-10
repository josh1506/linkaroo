from django import forms
from app.url_tracker.models import URL


class CreateURLForm(forms.ModelForm):
    link = forms.URLField(required=True, widget=forms.TextInput(attrs={'placeholder': 'URL/Link', 'class': 'form-control', 'autofocus': 'autofocus'}))
    title = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Link Title', 'class': 'form-control'}))
    custom_url = forms.CharField(required=False, widget=forms.TextInput(attrs={'placeholder': 'Insert custom URL (optional)', 'class': 'form-control'}))
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'placeholder': 'Insert link description (optional)', 'class': 'form-control'}))

    class Meta:
        model = URL
        fields = ['link', 'title', 'custom_url', 'description']
