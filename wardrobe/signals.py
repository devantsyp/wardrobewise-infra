from django.db.models.signals import post_delete
from django.dispatch import receiver

from wardrobe.models import Garment


@receiver(post_delete, sender=Garment)
def delete_garment_files(sender, instance, **kwargs):
    """
    Clean up S3/local files when a Garment instance is deleted.
    Uses delete(save=False) to remove the file without triggering another model save.
    """
    if instance.garment_photo:
        instance.garment_photo.delete(save=False)
    if instance.care_label_photo:
        instance.care_label_photo.delete(save=False)
