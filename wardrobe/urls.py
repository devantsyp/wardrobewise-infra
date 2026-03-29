from django.urls import path

from wardrobe import views

app_name = 'wardrobe'

urlpatterns = [
    path('', views.garment_list, name='garment_list'),
    path('<int:pk>/', views.garment_detail, name='garment_detail'),
    path('add/', views.garment_create, name='garment_create'),
    path('<int:pk>/edit/', views.garment_edit, name='garment_edit'),
    path('<int:pk>/delete/', views.garment_delete, name='garment_delete'),
    path('<int:pk>/analyze/', views.analyze_care_label_view, name='analyze_care_label'),
    path('<int:pk>/instructions/edit/', views.edit_instructions_view, name='edit_instructions'),
    path('<int:pk>/instructions/reset/', views.reset_instructions_view, name='reset_instructions'),
    path('<int:pk>/analysis/delete/', views.delete_analysis_view, name='delete_analysis'),
]
