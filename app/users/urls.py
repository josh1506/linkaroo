from django.urls import path
from django.contrib.auth import views as auth_views

from . import views


app_name = 'users'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('signup/', views.SignUpTemplateView.as_view(), name='signup'),
    path('logout/user/', auth_views.LogoutView.as_view(next_page='users:login'), name='logout')
]
