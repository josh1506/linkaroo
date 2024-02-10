from django.contrib import admin

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
