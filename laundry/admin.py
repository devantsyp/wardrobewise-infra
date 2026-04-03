from django.contrib import admin

from laundry.models import Basket


@admin.register(Basket)
class BasketAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'last_used_at', 'created_at')
    list_filter = ('user',)
    readonly_fields = ('created_at', 'last_used_at')
