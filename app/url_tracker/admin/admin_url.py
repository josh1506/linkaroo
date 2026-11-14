from django.contrib import admin
from django.db import models

from app.url_tracker.models.models_url import URL


@admin.register(URL)
class URLAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'title',
        'description',
        'created_at',
        'updated_at'
    ]
    search_fields = ['title', 'description']
    list_filter = ['created_at', 'updated_at']
    exclude = ['created_at', 'updated_at', 'status', 'activate_date', 'deactivate_date']
    # Same scheme-less default as the site form (Django 6.0 default; avoids RemovedInDjango60Warning).
    formfield_overrides = {models.URLField: {'assume_scheme': 'https'}}
