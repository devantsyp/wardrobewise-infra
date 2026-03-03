from django.urls import path

from wardrobe import views

app_name = 'wardrobe'

urlpatterns = [
    path('', views.garment_list, name='garment_list'),
    path('<int:pk>/', views.garment_detail, name='garment_detail'),
    path('add/', views.garment_create, name='garment_create'),
    path('<int:pk>/edit/', views.garment_edit, name='garment_edit'),
    path('<int:pk>/delete/', views.garment_delete, name='garment_delete'),
]
