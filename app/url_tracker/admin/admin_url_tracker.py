from django.contrib import admin

from app.url_tracker.models.models_url_tracker import URLTracker


@admin.register(URLTracker)
class URLTrackerAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'url',
        'created_at'
    ]
    list_filter = ['created_at', 'updated_at']
