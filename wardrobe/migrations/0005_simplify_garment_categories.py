from django.db import migrations, models


# Maps old DB values (display strings stored before this migration) to new slug values.
CATEGORY_MAP = {
    "T-Shirts & Tops": "shirts",
    "Shirts": "shirts",
    "Jeans": "bottoms",
    "Pants": "bottoms",
    "Dresses": "dresses_skirts",
    "Skirts": "dresses_skirts",
    "Jackets & Blazers": "outerwear",
    "Coats & Outerwear": "outerwear",
    "Shorts": "bottoms",
    "Sweaters & Knitwear": "sweaters_knitwear",
    "Hoodies & Sweatshirts": "hoodies_sweatshirts",
    "Underwear & Loungewear": "undergarments",
    "Socks": "undergarments",
    "Activewear": "other",
    "Sleepwear & Robes": "other",
    "Other": "other",
}


def migrate_categories_forward(apps, schema_editor):
    Garment = apps.get_model("wardrobe", "Garment")
    for old_value, new_value in CATEGORY_MAP.items():
        Garment.objects.filter(category=old_value).update(category=new_value)


def migrate_categories_backward(apps, schema_editor):
    """Reverse migration: map new slugs back to the first matching old display string."""
    REVERSE_MAP = {
        "shirts": "Shirts",
        "bottoms": "Pants",
        "outerwear": "Coats & Outerwear",
        "dresses_skirts": "Dresses",
        "undergarments": "Underwear & Loungewear",
        "sweaters_knitwear": "Sweaters & Knitwear",
        "hoodies_sweatshirts": "Hoodies & Sweatshirts",
        "other": "Other",
    }
    Garment = apps.get_model("wardrobe", "Garment")
    for new_value, old_value in REVERSE_MAP.items():
        Garment.objects.filter(category=new_value).update(category=old_value)


class Migration(migrations.Migration):

    dependencies = [
        ("wardrobe", "0004_add_failure_reason"),
    ]

    operations = [
        # Step 1: migrate data while the column still accepts the old values (max_length=50 fits both)
        migrations.RunPython(migrate_categories_forward, migrate_categories_backward),
        # Step 2: update the field definition to reflect the new choices
        migrations.AlterField(
            model_name="garment",
            name="category",
            field=models.CharField(
                choices=[
                    ("shirts", "Shirts"),
                    ("bottoms", "Bottoms (pants, shorts)"),
                    ("outerwear", "Outerwear (jackets, coats)"),
                    ("dresses_skirts", "Dresses & Skirts"),
                    ("undergarments", "Undergarments (underwear, socks)"),
                    ("sweaters_knitwear", "Sweaters & Knitwear"),
                    ("hoodies_sweatshirts", "Hoodies & Sweatshirts"),
                    ("other", "Other"),
                ],
                max_length=50,
            ),
        ),
    ]
