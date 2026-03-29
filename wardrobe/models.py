from decimal import Decimal

from django.conf import settings
from django.db import models


CATEGORY_CHOICES = [
    ("T-Shirts & Tops", "T-Shirts & Tops"),
    ("Shirts", "Shirts"),
    ("Jeans", "Jeans"),
    ("Pants", "Pants"),
    ("Dresses", "Dresses"),
    ("Skirts", "Skirts"),
    ("Jackets & Blazers", "Jackets & Blazers"),
    ("Coats & Outerwear", "Coats & Outerwear"),
    ("Shorts", "Shorts"),
    ("Sweaters & Knitwear", "Sweaters & Knitwear"),
    ("Hoodies & Sweatshirts", "Hoodies & Sweatshirts"),
    ("Underwear & Loungewear", "Underwear & Loungewear"),
    ("Socks", "Socks"),
    ("Activewear", "Activewear"),
    ("Sleepwear & Robes", "Sleepwear & Robes"),
    ("Other", "Other"),
]


def garment_photo_path(instance, filename):
    """
    Upload path for garment photos.
    IMPORTANT: Requires instance.pk to be set — use two-step save in create view:
    1. save the Garment record (without files)
    2. assign file fields and save again
    """
    return f"user_{instance.user.id}/garment_{instance.pk}/garment.jpg"


def care_label_path(instance, filename):
    """
    Upload path for care label photos.
    IMPORTANT: Requires instance.pk to be set — use two-step save in create view.
    """
    return f"user_{instance.user.id}/garment_{instance.pk}/care_label.jpg"


class Garment(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='garments',
    )
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    color = models.CharField(max_length=100, blank=True)
    fabric = models.CharField(max_length=100, blank=True)
    notes = models.TextField(max_length=500, blank=True)
    garment_photo = models.ImageField(
        upload_to=garment_photo_path,
        blank=True,
        null=True,
    )
    care_label_photo = models.ImageField(
        upload_to=care_label_path,
        blank=True,
        null=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class CareAnalysis(models.Model):
    garment = models.OneToOneField(
        'Garment',
        on_delete=models.CASCADE,
        related_name='care_analysis',
    )
    image_hash = models.CharField(max_length=64, db_index=True)

    # Immutable AI output fields — never updated after creation
    raw_ai_json = models.JSONField()
    ai_washing = models.TextField()
    ai_drying = models.TextField()
    ai_ironing = models.TextField()
    ai_bleach = models.TextField()
    ai_is_delicate = models.BooleanField(default=False)
    ai_summary = models.TextField()

    # User-editable copy fields — start as copy of ai_* fields
    washing = models.TextField()
    drying = models.TextField()
    ironing = models.TextField()
    bleach = models.TextField()
    is_delicate = models.BooleanField(default=False)
    summary = models.TextField()
    personal_notes = models.TextField(blank=True)
    is_user_edited = models.BooleanField(default=False)

    # Timestamps
    analyzed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    from_cache = models.BooleanField(default=False)

    def __str__(self):
        return f"Analysis for {self.garment.name}"


class UsageLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='usage_logs',
    )
    garment = models.ForeignKey(
        'Garment',
        on_delete=models.SET_NULL,
        null=True,
        related_name='usage_logs',
    )
    prompt_tokens = models.IntegerField()
    completion_tokens = models.IntegerField()
    cost_usd = models.DecimalField(max_digits=10, decimal_places=8)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Usage {self.user} - {self.created_at:%Y-%m-%d}"
