from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('healthz/', views.healthz, name='healthz'),
    path('favicon.ico', views.FaviconRedirect.as_view(), name='favicon'),
]
