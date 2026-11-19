from django.contrib import admin

from app.users.views.login import ThrottledAdminAuthenticationForm

# /admin/login/ previously bypassed the site login lockout (threat model F1).
admin.site.login_form = ThrottledAdminAuthenticationForm
