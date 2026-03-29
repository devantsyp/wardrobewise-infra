import json

from django.contrib import admin
from django.utils.html import format_html

from wardrobe.models import CareAnalysis, Garment, UsageLog


@admin.register(Garment)
class GarmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'user', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'color', 'fabric', 'notes')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(CareAnalysis)
class CareAnalysisAdmin(admin.ModelAdmin):
    list_display = ('garment', 'get_user', 'analyzed_at', 'from_cache', 'is_user_edited', 'is_delicate')
    list_filter = ('from_cache', 'is_user_edited', 'is_delicate', 'analyzed_at')
    readonly_fields = (
        'garment', 'image_hash', 'raw_ai_json_pretty',
        'ai_washing', 'ai_drying', 'ai_ironing', 'ai_bleach', 'ai_is_delicate', 'ai_summary',
        'analyzed_at', 'updated_at', 'from_cache',
    )
    search_fields = ('garment__name', 'garment__user__email')

    @admin.display(description='User')
    def get_user(self, obj):
        return obj.garment.user.email

    @admin.display(description='Raw AI JSON')
    def raw_ai_json_pretty(self, obj):
        formatted = json.dumps(obj.raw_ai_json, indent=2)
        return format_html('<pre style="white-space:pre-wrap; max-width:600px;">{}</pre>', formatted)


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'garment', 'prompt_tokens', 'completion_tokens', 'cost_usd', 'created_at')
    list_filter = ('created_at', 'user')
    readonly_fields = ('user', 'garment', 'prompt_tokens', 'completion_tokens', 'cost_usd', 'created_at')
    search_fields = ('user__email',)
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
