from django.urls import path
from laundry import views

app_name = 'laundry'

urlpatterns = [
    path('', views.basket_view, name='basket'),
    path('api/plan/', views.plan_api, name='plan_api'),
    path('create/', views.basket_create, name='basket_create'),
    path('<int:pk>/rename/', views.basket_rename, name='basket_rename'),
    path('<int:pk>/delete/', views.basket_delete, name='basket_delete'),
    path('save-plan/', views.save_plan, name='save_plan'),
    path('update-selection/', views.update_selection, name='update_selection'),
]
