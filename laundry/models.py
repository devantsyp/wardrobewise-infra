from django.conf import settings
from django.db import models


class Basket(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='baskets',
    )
    name = models.CharField(max_length=100)
    garment_pks = models.JSONField(default=list)
    saved_plan = models.JSONField(null=True, blank=True)
    plan_saved_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_used_at']

    def __str__(self):
        return f"{self.name} ({self.user})"
