from django.apps import AppConfig


class WardrobeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'wardrobe'

    def ready(self):
        import wardrobe.signals  # noqa: F401 — registers post_delete handler
