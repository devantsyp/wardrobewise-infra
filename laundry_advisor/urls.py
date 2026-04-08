"""
URL configuration for wardrobe_wise project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('wardrobe/', include('wardrobe.urls')),
    path('basket/', include('laundry.urls')),
    path('', include('core.urls')),
    path('', include('accounts.urls')),
]

# Serve uploaded media files in development
from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
