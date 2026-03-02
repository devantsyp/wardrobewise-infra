# Phase 02: Wardrobe CRUD with S3 - Research

**Researched:** 2026-03-02
**Domain:** Django CRUD views, AWS S3 file storage, django-storages, Tailwind CSS responsive grid
**Confidence:** HIGH (core stack), MEDIUM (S3 bucket config steps), HIGH (Django patterns)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Wardrobe Grid Layout**
- Fixed-size cards, tight/dense grid
- Each card shows: garment photo (square 1:1 crop) with garment name below
- Grid columns: responsive CSS grid (auto-fill based on screen width, no fixed column count)
- Ordered: newest first (creation date descending)
- Clicking a card: navigate to the garment detail page
- No-photo fallback: styled placeholder (clothing hanger icon or pattern) — not a plain grey box
- Page header: "My Wardrobe" heading above the grid
- "Add Clothing" button: top-right corner, styled with app's color palette, prominent/noticeable

**Empty State**
- Simple message + prominent Add button
- No illustration required

**Garment Form Fields**
- Form layout: single page (all fields + photo uploads on one page)
- Label style: floating labels (placeholder floats up when field is focused/filled)
- Required fields: name + category only
- Name field: free text, max 100 characters
- Category field: predefined dropdown — fixed list:
  T-Shirts & Tops, Shirts, Jeans, Pants, Dresses, Skirts, Jackets & Blazers,
  Coats & Outerwear, Shorts, Sweaters & Knitwear, Hoodies & Sweatshirts,
  Underwear & Loungewear, Socks, Activewear, Sleepwear & Robes
- Color field: free text ("navy blue", "off-white", etc.)
- Fabric/material field: free text
- Notes field: optional, max 500 characters
- Post-create redirect: garment detail page (not back to the grid)

**Photo Handling**
- Both garment photo and care label photo are optional
- Accepted formats: images only (JPG/PNG), max 10 MB each
- Hint text shown below each upload field: "JPG or PNG, max 10 MB"
- Thumbnail preview shown immediately after a file is selected (before form submit)
- Upload progress: no progress bar; submit button is disabled during upload
- S3 path structure: `user_<id>/garment_<id>/garment.jpg` and `user_<id>/garment_<id>/care_label.jpg`
- Image serving: direct S3 URLs (public bucket)
- On edit with existing photo: show current photo as thumbnail with a "Replace" button below
- Photo replacement: delete the old S3 file when a new one is uploaded
- Removing without replacing: not supported

**Garment Detail Page**
- Page title: garment name as H1 at the top
- "← Back to Wardrobe" link at top of page
- All fields displayed: name, category, color, fabric, notes, date added ("Added: Feb 25, 2026")
- Photos: stacked vertically — garment photo full-width (edge to edge) at top, care label photo smaller below
- Photos have clearly labeled headings: "Garment Photo" and "Care Label"
- Photos are display-only (no tap-to-expand)
- Care instruction placeholder: simple text "Care instructions coming soon"
- Edit and Delete buttons both on the detail page only (not accessible from grid cards)
- Delete button: red/danger styling; Edit button: neutral styling

**Edit Behavior**
- Edit form: separate page using the same form as create, pre-populated with current values
- Cancel button on edit form: returns user to the garment detail page
- Post-edit redirect: garment detail page
- Save errors: error banner at top of the form page

**Delete Behavior**
- Delete requires a confirmation dialog: "Delete this garment? This cannot be undone."
- On confirm: delete S3 files immediately, then delete garment record (and cascade-delete any linked AnalysisResult)
- Post-delete redirect: wardrobe grid
- No success toast after delete

**Security and Data Isolation**
- All wardrobe pages require login (redirect to login if unauthenticated)
- Strict user isolation: all queries filter by `request.user`
- Accessing another user's garment URL returns 404 (not 403) — does not reveal existence

### Claude's Discretion
- Exact loading skeleton or spinner design during form submit
- Spacing, typography, and specific Tailwind classes
- Mobile-specific layout adjustments within the responsive grid
- Exact S3 bucket policy configuration (public read vs. signed URLs — user chose direct URLs, Claude handles bucket permissions)

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

## Summary

This phase builds the full garment CRUD system: a `wardrobe` Django app with a `Garment` model, five views (list, detail, create, edit, delete), and AWS S3 photo storage via django-storages. The project already has authentication (Phase 1), a custom user model, split settings (base/dev/prod), and a WhiteNoise static files pipeline. The wardrobe app is a greenfield addition.

The most important technical challenge is the S3 path structure `user_<id>/garment_<id>/garment.jpg`. Django's `upload_to` callable receives the model `instance` before it has a primary key on first save. The solution is a **two-step save**: save the garment record first (without the file), then upload the file to S3 using the newly assigned `garment.pk` in the path. This is a well-known Django pattern, not a hack.

For public image serving, the bucket must have Block Public Access disabled and a bucket policy granting anonymous `s3:GetObject`. The django-storages setting `querystring_auth = False` then generates plain `https://<bucket>.s3.amazonaws.com/...` URLs with no expiring signature. `file_overwrite = True` (the default) allows photo replacement by uploading to the same fixed path.

**Primary recommendation:** Create a new `wardrobe` Django app, use function-based views (matching Phase 1 style), and keep S3 interaction entirely within `django-storages` — no direct boto3 calls needed except for explicit file deletion.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| django-storages | 1.14.6 (latest) | S3 media file storage backend for Django | The de-facto standard; integrates with Django's `FileField`/`ImageField` transparently |
| boto3 | latest (>=1.4.4) | AWS SDK used by django-storages internally | Required dependency of django-storages S3 backend |
| Pillow | latest stable | Required for Django `ImageField` validation | Django refuses to run `ImageField` migrations without it |

### Supporting
| Library | Purpose | When to Use |
|---------|---------|-------------|
| (none new) | — | All other libraries (Django 5.2, dj-database-url, WhiteNoise, django-tailwind-cli) already installed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| django-storages | Direct boto3 | More boilerplate, no Django storage API integration — don't do this |
| ImageField | FileField | FileField skips image validation; user wants images only — use ImageField |
| Public bucket URL | Presigned URLs | Presigned URLs expire (default 3600s), require AWS credentials on every page render, add complexity — user chose direct URLs, correct for this use case |

**Installation additions to requirements.txt:**
```
django-storages[s3]>=1.14,<2.0
Pillow>=10.0,<12.0
```

`django-storages[s3]` installs boto3 automatically via the extras bracket.

---

## Architecture Patterns

### Recommended Project Structure

```
wardrobe/
├── __init__.py
├── apps.py
├── models.py          # Garment model with ImageField + upload_to callables
├── forms.py           # GarmentForm with file size validation
├── views.py           # 5 FBVs: list, detail, create, edit, delete
├── urls.py            # wardrobe app URL namespace
├── signals.py         # post_delete signal to clean up S3 files
└── apps.py            # register signals in ready()

templates/
└── wardrobe/
    ├── wardrobe_list.html      # photo grid
    ├── garment_detail.html     # detail page
    ├── garment_form.html       # shared create/edit form
    └── garment_confirm_delete.html  # delete confirmation (or modal on detail page)
```

### Pattern 1: Garment Model with Fixed S3 Paths

The path structure `user_<id>/garment_<id>/garment.jpg` requires the garment's `pk` before upload. `instance.pk` is `None` during the first `upload_to` call. The canonical solution: use `user.id` (available via FK) in the callable, and for the garment portion of the path use the garment's `pk` by doing a **two-step save** in the view — save the model without a file first, then assign and save the file.

```python
# wardrobe/models.py

def garment_photo_path(instance, filename):
    # instance.pk IS available here because the view saves first, then attaches file
    return f"user_{instance.user.id}/garment_{instance.pk}/garment.jpg"

def care_label_path(instance, filename):
    return f"user_{instance.user.id}/garment_{instance.pk}/care_label.jpg"

class Garment(models.Model):
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
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="garments",
    )
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    color = models.CharField(max_length=100, blank=True)
    fabric = models.CharField(max_length=100, blank=True)
    notes = models.TextField(max_length=500, blank=True)
    garment_photo = models.ImageField(
        upload_to=garment_photo_path, blank=True, null=True
    )
    care_label_photo = models.ImageField(
        upload_to=care_label_path, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]  # newest first

    def __str__(self):
        return self.name
```

### Pattern 2: Two-Step Save in Create View

```python
# wardrobe/views.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .forms import GarmentForm
from .models import Garment

@login_required
def garment_create(request):
    if request.method == "POST":
        form = GarmentForm(request.POST, request.FILES)
        if form.is_valid():
            # Step 1: save without committing to get a pk
            garment = form.save(commit=False)
            garment.user = request.user
            garment.save()  # garment.pk now set

            # Step 2: if files were uploaded, assign them and save again
            # Files from form.cleaned_data are already validated
            if form.cleaned_data.get("garment_photo"):
                garment.garment_photo = form.cleaned_data["garment_photo"]
            if form.cleaned_data.get("care_label_photo"):
                garment.care_label_photo = form.cleaned_data["care_label_photo"]
            garment.save()  # S3 upload happens here; pk is in path

            return redirect("wardrobe:garment_detail", pk=garment.pk)
    else:
        form = GarmentForm()
    return render(request, "wardrobe/garment_form.html", {"form": form, "action": "create"})
```

**Why two saves?** Django calls `upload_to` at the moment the file is saved to storage. If we call `form.save()` with files in one step, `upload_to` fires before the pk exists. Saving the record first (without files) gives us a pk, then assigning files triggers `upload_to` when pk is already populated.

### Pattern 3: User Isolation — get_object_or_404 with user filter

```python
# Returns 404 for other users' garments (does not reveal existence)
garment = get_object_or_404(Garment, pk=pk, user=request.user)
```

This single pattern satisfies the security requirement: `get_object_or_404(Model, pk=pk, user=request.user)` returns 404 if the garment exists but belongs to someone else, or if it simply does not exist.

### Pattern 4: S3 File Deletion on Model Delete

Django does NOT automatically delete S3 files when a model instance is deleted. Use a `post_delete` signal:

```python
# wardrobe/signals.py
from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import Garment

@receiver(post_delete, sender=Garment)
def delete_garment_files(sender, instance, **kwargs):
    if instance.garment_photo:
        instance.garment_photo.delete(save=False)
    if instance.care_label_photo:
        instance.care_label_photo.delete(save=False)
```

```python
# wardrobe/apps.py
class WardrobeConfig(AppConfig):
    name = "wardrobe"

    def ready(self):
        import wardrobe.signals  # noqa: F401
```

`FieldFile.delete(save=False)` calls `storage.delete(name)` on the S3 backend — this issues an S3 `DeleteObject` API call. The `save=False` prevents an extra DB write when the model is already being deleted.

### Pattern 5: Photo Replacement on Edit

Because `file_overwrite = True` is the default in django-storages, uploading a new file to the same S3 key (same `upload_to` path) simply replaces the existing object. The view logic:

```python
@login_required
def garment_edit(request, pk):
    garment = get_object_or_404(Garment, pk=pk, user=request.user)
    if request.method == "POST":
        form = GarmentForm(request.POST, request.FILES, instance=garment)
        if form.is_valid():
            # Delete old S3 file before saving new one (ensures clean replacement)
            if "garment_photo" in request.FILES and garment.garment_photo:
                garment.garment_photo.delete(save=False)
            if "care_label_photo" in request.FILES and garment.care_label_photo:
                garment.care_label_photo.delete(save=False)
            form.save()
            return redirect("wardrobe:garment_detail", pk=garment.pk)
    else:
        form = GarmentForm(instance=garment)
    return render(request, "wardrobe/garment_form.html", {"form": form, "garment": garment, "action": "edit"})
```

Note: explicit deletion before replacement is belt-and-suspenders; with `file_overwrite=True`, the upload itself would overwrite. Explicit deletion is included to satisfy the requirement ("delete the old S3 file when a new one is uploaded").

### Pattern 6: Delete Confirmation via POST + JavaScript confirm()

The confirmation dialog requirement can be satisfied with a simple JavaScript `window.confirm()` on the detail page — no extra library, no separate confirmation page:

```html
<!-- On garment_detail.html -->
<form method="POST" action="{% url 'wardrobe:garment_delete' garment.pk %}"
      onsubmit="return confirm('Delete this garment? This cannot be undone.');">
    {% csrf_token %}
    <button type="submit"
            class="bg-red-600 hover:bg-red-700 text-white font-semibold px-4 py-2 rounded-lg transition-colors">
        Delete
    </button>
</form>
```

The delete view itself handles only POST (checking `request.method == "POST"`). On GET it redirects back.

### Pattern 7: Responsive Photo Grid with Tailwind v4

Tailwind v4 supports arbitrary values with underscores for spaces. For the auto-fill grid:

```html
<div class="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-3">
  <!-- garment cards -->
</div>
```

For square 1:1 image cropping on each card:

```html
<div class="aspect-square w-full overflow-hidden bg-deep-space-100 rounded-t-lg">
  {% if garment.garment_photo %}
    <img src="{{ garment.garment_photo.url }}" alt="{{ garment.name }}"
         class="w-full h-full object-cover">
  {% else %}
    <!-- Fallback placeholder -->
    <div class="w-full h-full flex items-center justify-center">
      <svg ...><!-- hanger icon --></svg>
    </div>
  {% endif %}
</div>
```

### Pattern 8: Floating Labels with Tailwind v4

Floating labels require the label to come AFTER the input (CSS peer selector is a "previous sibling" rule). The input gets `peer` and uses a transparent placeholder:

```html
<div class="relative mb-6">
  <input type="text" id="id_name" name="name"
         placeholder=" "
         class="peer w-full px-3 pt-5 pb-2 border border-lilac-ash-200 rounded-lg
                focus:outline-none focus:ring-2 focus:ring-lavender-400 focus:border-lavender-400">
  <label for="id_name"
         class="absolute left-3 top-4 text-thistle-500 text-sm transition-all
                peer-focus:top-1.5 peer-focus:text-xs peer-focus:text-lavender-600
                peer-placeholder-shown:top-4 peer-placeholder-shown:text-sm
                peer-not-placeholder-shown:top-1.5 peer-not-placeholder-shown:text-xs">
    Name
  </label>
</div>
```

Key: `placeholder=" "` (a single space) is required — `peer-placeholder-shown` triggers when placeholder is visible, i.e., when the field is empty. With a space placeholder, the label floats up immediately on focus or when the field has content.

### Pattern 9: Image Preview Before Upload (Vanilla JS)

```html
<input type="file" id="id_garment_photo" name="garment_photo" accept="image/jpeg,image/png"
       onchange="previewImage(this, 'preview_garment')">
<img id="preview_garment" src="" class="hidden mt-2 w-24 h-24 object-cover rounded">

<script>
function previewImage(input, previewId) {
  const preview = document.getElementById(previewId);
  if (input.files && input.files[0]) {
    preview.src = URL.createObjectURL(input.files[0]);
    preview.classList.remove('hidden');
  }
}
</script>
```

`URL.createObjectURL()` is preferred over `FileReader.readAsDataURL()` — it is synchronous, more memory-efficient, and works for large files without base64 encoding overhead.

### Pattern 10: Form File Validation (10 MB limit, images only)

```python
# wardrobe/forms.py
from django import forms
from .models import Garment

MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB in bytes
ALLOWED_TYPES = ["image/jpeg", "image/png"]

class GarmentForm(forms.ModelForm):
    class Meta:
        model = Garment
        fields = ["name", "category", "color", "fabric", "notes",
                  "garment_photo", "care_label_photo"]

    def _validate_image(self, field_name):
        f = self.cleaned_data.get(field_name)
        if f:
            if f.size > MAX_UPLOAD_SIZE:
                raise forms.ValidationError("File size must be 10 MB or less.")
            if hasattr(f, "content_type") and f.content_type not in ALLOWED_TYPES:
                raise forms.ValidationError("Only JPG and PNG files are accepted.")
        return f

    def clean_garment_photo(self):
        return self._validate_image("garment_photo")

    def clean_care_label_photo(self):
        return self._validate_image("care_label_photo")
```

Note: `ImageField` also runs Pillow validation (checks that the file is a real image), providing a second layer of defense beyond MIME type checks.

### Anti-Patterns to Avoid

- **Using `instance.pk` in `upload_to` without two-step save:** `instance.pk` is `None` on first save — the path becomes `user_5/garment_None/garment.jpg`. Always save without files first.
- **`form.save()` with files in one step on create:** Triggers `upload_to` before pk is set. Use `commit=False`, save, then assign files.
- **Storing files with `file_overwrite=False` at fixed paths:** Appends random characters, breaking the deterministic path scheme. Keep the default `file_overwrite=True`.
- **Using `DEFAULT_FILE_STORAGE` instead of `STORAGES` dict:** Deprecated in Django 4.2. The project already uses the `STORAGES` dict for WhiteNoise. Add the `"default"` key to that same dict.
- **Adding `storages` to INSTALLED_APPS:** Not required for django-storages 1.14. The `STORAGES` setting is sufficient.
- **Relying on WhiteNoise for media files:** WhiteNoise serves only static files. Media (user uploads) must go to S3 — there is no MEDIA_ROOT on Render's ephemeral filesystem.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| S3 file storage | Custom boto3 upload code | `django-storages` S3 backend | Storage API integrates transparently with `ImageField.url`, `ImageField.delete()`, `form.save()` |
| Image validation | Manual MIME sniffing | Django `ImageField` + Pillow | Pillow verifies actual image bytes, not just extension |
| File size validation | Middleware request size limits | `clean_<field>()` in form | Field-level errors display inline; middleware returns generic errors |
| User isolation | Manual permission checks | `get_object_or_404(Model, pk=pk, user=request.user)` | One-liner that returns 404, not 403 |
| Login protection | Session checks in views | `@login_required` decorator | Handles redirect to login with `next` parameter automatically |
| S3 file cleanup on delete | Scheduled cleanup jobs | `post_delete` signal + `FieldFile.delete(save=False)` | Synchronous, transactionally correct, no orphan files |

---

## Common Pitfalls

### Pitfall 1: `upload_to` Callable Receives `instance.pk = None`

**What goes wrong:** The S3 path becomes `user_5/garment_None/garment.jpg`. The file uploads to the wrong location. On edit, the path doesn't match the intended scheme.

**Why it happens:** Django calls `upload_to` at the moment the file is saved. On model creation, the pk hasn't been assigned yet (Django assigns it only after `INSERT INTO` completes).

**How to avoid:** Two-step save in the create view — `form.save(commit=False)`, set `user`, call `.save()` to get pk, then assign file fields and call `.save()` again.

**Warning signs:** S3 paths contain "None" in the path.

### Pitfall 2: Block Public Access Enabled on New S3 Bucket

**What goes wrong:** Images return 403 Forbidden. The app appears to work (files upload) but images can't be displayed.

**Why it happens:** Since April 2023, all new AWS S3 buckets have Block Public Access enabled AND ACLs disabled by default. Setting `default_acl = "public-read"` in django-storages has no effect when ACLs are disabled — AWS silently ignores it.

**How to avoid:** Configure the bucket correctly before writing a single line of Django code:
1. In S3 bucket settings, under "Permissions" → "Block Public Access": turn OFF all four options.
2. Under "Object Ownership": keep "Bucket owner enforced" (ACLs off — this is correct; use bucket policy instead).
3. Add a bucket policy granting `s3:GetObject` to `Principal: "*"`.
4. In django-storages settings, set `querystring_auth = False` and do NOT set `default_acl` (it's irrelevant when ACLs are disabled).

**Warning signs:** Uploaded files appear in S3 console but return 403 when accessed directly via URL.

**Required bucket policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::YOUR_BUCKET_NAME/*"
    }
  ]
}
```

### Pitfall 3: WhiteNoise's `STORAGES` Dict Collision

**What goes wrong:** Adding a `"default"` key to `STORAGES` in `prod.py` accidentally removes the `"staticfiles"` WhiteNoise key.

**Why it happens:** Python dict assignment `STORAGES = {"default": ...}` replaces the entire dict.

**How to avoid:** Always use `STORAGES` dict update syntax to add the default storage:
```python
# In prod.py — DON'T reassign, UPDATE
STORAGES["default"] = {
    "BACKEND": "storages.backends.s3.S3Storage",
    "OPTIONS": { ... },
}
```
Or define the full `STORAGES` dict including both keys.

### Pitfall 4: `querystring_auth = True` (Default) on a Public Bucket

**What goes wrong:** Image URLs include `?AWSAccessKeyId=...&Signature=...&Expires=...` parameters that expire after 3600 seconds. Cached pages show broken images after an hour.

**Why it happens:** django-storages defaults to signed URL generation even when the bucket is public.

**How to avoid:** Set `querystring_auth = False` in the S3 storage OPTIONS. Generated URLs become plain `https://bucket.s3.region.amazonaws.com/user_1/garment_3/garment.jpg`.

### Pitfall 5: `enctype="multipart/form-data"` Missing from Form Tag

**What goes wrong:** File inputs appear in the form but `request.FILES` is always empty. Photos never upload.

**Why it happens:** Without `enctype="multipart/form-data"`, browsers submit forms as `application/x-www-form-urlencoded`, which strips file data.

**How to avoid:** Every form that handles file uploads must have:
```html
<form method="POST" enctype="multipart/form-data">
```

### Pitfall 6: Django Admin Conflict with Custom Wardrobe URLs

**What goes wrong:** Navigating to `/wardrobe/` hits the Django admin pattern prefix if urls.py ordering is wrong.

**Why it happens:** URL resolution is first-match; if admin.site.urls is included with a broad prefix, it can shadow app URLs.

**How to avoid:** Keep the existing project `urls.py` structure — `path('', include('wardrobe.urls'))` under the root, same as accounts and core are already included.

### Pitfall 7: Missing MEDIA_URL/MEDIA_ROOT Does Not Break S3 (But Confuses Dev)

**What goes wrong:** In development (SQLite, no S3), `ImageField.url` raises `ValueError: The 'garment_photo' attribute has no file associated with it.` or returns an unusable path.

**Why it happens:** In dev, there is no S3 backend and no MEDIA_ROOT configured. The project's `dev.py` has no media file settings.

**How to avoid:** Add to `dev.py`:
```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
```
And add to `dev` URL conf:
```python
from django.conf import settings
from django.conf.urls.static import static
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```
In production (Render), the S3 backend handles all media; `MEDIA_ROOT` is irrelevant.

Alternatively, you can configure dev to use S3 as well (simpler for consistency), but a local media folder is standard for dev environments.

---

## Code Examples

Verified patterns from official sources and project codebase:

### S3 Storage Settings (prod.py addition)

```python
# Source: django-storages 1.14.6 docs + Django 5.2 STORAGES dict pattern

# In prod.py — extend existing STORAGES dict, don't replace it
STORAGES["default"] = {
    "BACKEND": "storages.backends.s3.S3Storage",
    "OPTIONS": {
        "bucket_name": env("AWS_STORAGE_BUCKET_NAME"),
        "region_name": env("AWS_S3_REGION_NAME", default="us-east-1"),
        "access_key": env("AWS_ACCESS_KEY_ID"),
        "secret_key": env("AWS_SECRET_ACCESS_KEY"),
        "querystring_auth": False,     # plain URLs, no expiring signatures
        "file_overwrite": True,        # replace files at same path (default, explicit for clarity)
        "default_acl": None,           # ACLs disabled on bucket; bucket policy handles public read
    },
}
```

Required environment variables (Render dashboard):
- `AWS_STORAGE_BUCKET_NAME`
- `AWS_S3_REGION_NAME`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### Wardrobe App URL namespace

```python
# wardrobe/urls.py
from django.urls import path
from . import views

app_name = "wardrobe"

urlpatterns = [
    path("wardrobe/", views.wardrobe_list, name="wardrobe_list"),
    path("wardrobe/add/", views.garment_create, name="garment_create"),
    path("wardrobe/<int:pk>/", views.garment_detail, name="garment_detail"),
    path("wardrobe/<int:pk>/edit/", views.garment_edit, name="garment_edit"),
    path("wardrobe/<int:pk>/delete/", views.garment_delete, name="garment_delete"),
]
```

Replace `core.urls` wardrobe placeholder with this app's URL include in `laundry_advisor/urls.py`.

### Login-Protected View Pattern (matching Phase 1 style)

```python
# Source: existing accounts/views.py + django.contrib.auth.decorators
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from .models import Garment

@login_required
def wardrobe_list(request):
    garments = Garment.objects.filter(user=request.user)
    return render(request, "wardrobe/wardrobe_list.html", {"garments": garments})

@login_required
def garment_detail(request, pk):
    garment = get_object_or_404(Garment, pk=pk, user=request.user)
    return render(request, "wardrobe/garment_detail.html", {"garment": garment})
```

### Wardrobe Grid Template Skeleton

```html
{# templates/wardrobe/wardrobe_list.html #}
{% extends "base.html" %}
{% block content %}
<div class="max-w-7xl mx-auto px-6 py-8">
  <div class="flex items-center justify-between mb-6">
    <h1 class="text-2xl font-bold text-deep-space-900">My Wardrobe</h1>
    <a href="{% url 'wardrobe:garment_create' %}"
       class="bg-deep-space-600 hover:bg-lavender-500 text-white font-semibold px-4 py-2 rounded-lg transition-colors">
      + Add Clothing
    </a>
  </div>

  {% if garments %}
  <div class="grid grid-cols-[repeat(auto-fill,minmax(160px,1fr))] gap-3">
    {% for garment in garments %}
    <a href="{% url 'wardrobe:garment_detail' garment.pk %}"
       class="bg-white rounded-lg shadow-sm overflow-hidden hover:shadow-md transition-shadow">
      <div class="aspect-square w-full overflow-hidden bg-deep-space-50">
        {% if garment.garment_photo %}
          <img src="{{ garment.garment_photo.url }}" alt="{{ garment.name }}"
               class="w-full h-full object-cover">
        {% else %}
          <div class="w-full h-full flex items-center justify-center text-thistle-300">
            {# SVG hanger icon placeholder #}
          </div>
        {% endif %}
      </div>
      <div class="p-2">
        <p class="text-deep-space-900 text-sm font-medium truncate">{{ garment.name }}</p>
      </div>
    </a>
    {% endfor %}
  </div>
  {% else %}
  <div class="text-center py-24">
    <p class="text-thistle-500 text-lg mb-4">Your wardrobe is empty.</p>
    <a href="{% url 'wardrobe:garment_create' %}"
       class="bg-deep-space-600 hover:bg-lavender-500 text-white font-semibold px-6 py-3 rounded-lg transition-colors">
      Add your first garment
    </a>
  </div>
  {% endif %}
</div>
{% endblock %}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'` | `STORAGES = {"default": {"BACKEND": "storages.backends.s3.S3Storage", ...}}` | Django 4.2 / django-storages 1.13 | Old approach deprecated; new approach allows per-field storage and cleaner config |
| `AWS_S3_FILE_OVERWRITE`, `AWS_QUERYSTRING_AUTH` global settings | `OPTIONS` dict within `STORAGES["default"]` | django-storages 1.13+ | Old global settings still work but OPTIONS is preferred for Django 4.2+ |
| Object ACL `public-read` | Bucket policy `s3:GetObject` to `Principal: "*"` | AWS default change April 2023 | New buckets have ACLs disabled; must use bucket policy for public access |
| `s3boto3.S3Boto3Storage` backend path | `s3.S3Storage` backend path | django-storages ~1.13 | Old path still works as alias but new path is canonical |

**Deprecated/outdated:**
- `DEFAULT_FILE_STORAGE = '...'`: Replaced by `STORAGES["default"]` in Django 4.2
- Setting `default_acl = "public-read"` on new AWS buckets: ACLs are disabled by default since April 2023; bucket policy is the correct mechanism
- `STATICFILES_STORAGE = '...'`: Already correctly replaced by `STORAGES["staticfiles"]` in this project's `prod.py`

---

## Open Questions

1. **Dev environment S3 vs local storage**
   - What we know: `dev.py` has no media file settings; Render's ephemeral FS cannot be used in prod
   - What's unclear: Should dev use a real S3 bucket or local file storage? Both work; this is Claude's discretion
   - Recommendation: Use local file storage in dev (`MEDIA_ROOT = BASE_DIR / "media"`) — simpler, no AWS cost, no credential management in dev. Add `MEDIA_URL` and `MEDIA_ROOT` to `dev.py` and serve via `django.conf.urls.static` in dev urls.

2. **IAM Policy for the S3 IAM user**
   - What we know: IAM user needs `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on the bucket
   - What's unclear: Whether to use `AmazonS3FullAccess` (broader) or a scoped policy
   - Recommendation: Use a scoped custom policy allowing only `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on `arn:aws:s3:::BUCKET_NAME/*` — principle of least privilege

3. **Replacing the `core` wardrobe placeholder**
   - What we know: `core/views.py` has `wardrobe_placeholder` view; `core/urls.py` routes `/wardrobe/` to it
   - What's unclear: Whether to delete `wardrobe_placeholder` from core, or just shadow the route
   - Recommendation: Remove the placeholder view and URL from `core` when the `wardrobe` app URL is added to project `urls.py`. The `wardrobe` include should come before `core` in `urlpatterns` to ensure `/wardrobe/` routes correctly, or remove from `core` entirely.

---

## Sources

### Primary (HIGH confidence)
- Django 5.2 official docs — `FileField.upload_to` callable, `instance.pk` None warning, `FieldFile.delete()`, `get_object_or_404`, `@login_required`
- django-storages 1.14.6 official docs — S3 backend, `querystring_auth`, `file_overwrite`, `default_acl`, `bucket_name`, `OPTIONS` dict pattern for Django 4.2+
- AWS official docs — Block Public Access default behavior (April 2023 change), bucket policy `s3:GetObject` to anonymous principal

### Secondary (MEDIUM confidence)
- TestDriven.io "Storing Django Static and Media Files on Amazon S3" — IAM user setup, `AmazonS3FullAccess` vs scoped policy, production gotchas (verified against official docs)
- AWS re:Post — S3 public access with ACLs disabled, bucket policy requirement (consistent with AWS official documentation)

### Tertiary (LOW confidence)
- Multiple blog posts on two-step save pattern for `upload_to` with pk — consensus approach, not in official Django docs as a named pattern but documented in Django ticket #12009 as a known limitation
- Floating label Tailwind pattern from Flowbite/DEV Community — CSS `peer` approach is well-established Tailwind pattern, verified works with Tailwind v4 `peer-*` utilities

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — django-storages 1.14.6 is the current stable release; boto3 requirement verified in official docs; Pillow requirement verified in Django 5.2 docs
- Architecture: HIGH — Django patterns (two-step save, `post_delete` signal, `get_object_or_404` filtering) verified in official Django docs
- S3 bucket configuration: MEDIUM — AWS console steps verified conceptually against AWS docs, but exact console UI steps can change; the bucket policy JSON is from official AWS examples
- Pitfalls: HIGH — Block Public Access default change is documented by AWS (April 2023); `upload_to pk=None` issue documented in Django ticket tracker

**Research date:** 2026-03-02
**Valid until:** 2026-06-01 (django-storages is stable; AWS S3 policy mechanics are stable; re-verify if django-storages releases 2.0)
