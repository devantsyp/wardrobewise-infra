from django.contrib import admin

from wardrobe.models import Garment


@admin.register(Garment)
class GarmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'user', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'color', 'fabric', 'notes')
    readonly_fields = ('created_at', 'updated_at')
