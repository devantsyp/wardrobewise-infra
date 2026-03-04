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
