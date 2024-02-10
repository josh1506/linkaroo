from django.urls import path

from . import views

app_name = 'url_tracker'

urlpatterns = [
    path('', views.UrlOverviewTemplateView.as_view(), name='overview'),
    path('create/', views.URLCreateView.as_view(), name='create'),
    path('list/', views.UrlListView.as_view(), name='list'),
    path('detail/<uuid:pk>/', views.UrlDetailView.as_view(), name='details'),
    path('update/<uuid:pk>/', views.UrlUpdateView.as_view(), name='update'),
    path('delete/<uuid:pk>/', views.UrlDeleteView.as_view(), name='delete'),
]
