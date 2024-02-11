from django.urls import path
from django.contrib.auth import views as auth_views

from .views import CustomLoginView


app_name = 'users'

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/user/', auth_views.LogoutView.as_view(next_page='users:login'), name='logout')
]
