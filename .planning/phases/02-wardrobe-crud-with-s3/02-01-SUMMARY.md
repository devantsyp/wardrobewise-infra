---
phase: 02-wardrobe-crud-with-s3
plan: 01
subsystem: database
tags: [django, s3, django-storages, pillow, imagefield, signals, admin]

# Dependency graph
requires:
  - phase: 01-scaffolding-and-auth
    provides: CustomUser model (AUTH_USER_MODEL), split settings (base/dev/prod), WhiteNoise STORAGES dict

provides:
  - Garment model with 15-category choices and ImageField x2 (garment_photo, care_label_photo)
  - Two-step save pattern documented for upload_to callables requiring pk
  - post_delete signal cleaning up S3/local files on Garment deletion
  - S3Storage backend configured in prod.py (extends, not replaces, WhiteNoise staticfiles entry)
  - Local filesystem media configured in dev.py (MEDIA_URL, MEDIA_ROOT)
  - GarmentForm with JPG/PNG-only and 10 MB file validation
  - Garment registered in Django admin with list_display, filtering, and search
  - 0001_initial migration applied

affects:
  - 02-02-wardrobe-views (builds views/templates on top of Garment model and GarmentForm)
  - 03-ai-pipeline (reads garment_photo and care_label_photo from S3)

# Tech tracking
tech-stack:
  added:
    - django-storages[s3]==1.14.6 (S3 media backend)
    - Pillow==11.3.0 (ImageField support)
    - boto3==1.42.59 (AWS SDK, installed as transitive dep of django-storages[s3])
  patterns:
    - Two-step save for ImageField with upload_to requiring pk: save without files first, then assign and save
    - Extend STORAGES dict with STORAGES["default"] = {...} — never reassign full dict (would wipe WhiteNoise)
    - post_delete signal registered via WardrobeConfig.ready() in apps.py

key-files:
  created:
    - wardrobe/models.py
    - wardrobe/forms.py
    - wardrobe/signals.py
    - wardrobe/admin.py
    - wardrobe/apps.py
    - wardrobe/migrations/0001_initial.py
  modified:
    - requirements.txt
    - laundry_advisor/settings/base.py
    - laundry_advisor/settings/dev.py
    - laundry_advisor/settings/prod.py

key-decisions:
  - "upload_to callables use instance.pk — create view MUST do two-step save (save record first, then assign files)"
  - "STORAGES['default'] extends prod.py STORAGES dict; using STORAGES = {...} would wipe WhiteNoise staticfiles entry"
  - "15 garment categories locked per user decision in CONTEXT.md — not changeable without migration"
  - "File inputs hidden via class=hidden; custom label buttons used for UI (implemented in Plan 02-02)"

patterns-established:
  - "Two-step save: garment = form.save(commit=False); garment.user = request.user; garment.save(); garment.garment_photo = ...; garment.save()"
  - "S3Storage OPTIONS syntax (bucket_name, region_name, access_key, secret_key) for django-storages 1.14"

# Metrics
duration: 5min
completed: 2026-03-03
---

# Phase 2 Plan 01: Wardrobe Data Layer Summary

**Garment model with 15 category choices and S3/local dual-storage, plus GarmentForm with JPG/PNG + 10 MB validation and Django admin**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-03T00:22:48Z
- **Completed:** 2026-03-03T00:27:18Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Garment model migrated with all required fields (name, category, color, fabric, notes, garment_photo, care_label_photo, user FK, timestamps)
- S3 storage configured in prod.py by extending (not replacing) STORAGES dict — WhiteNoise staticfiles entry preserved
- post_delete signal registered via apps.py ready() to clean up S3/local files on Garment deletion
- GarmentForm validates image type (JPG/PNG only) and size (max 10 MB) via shared _validate_image() helper
- Garment registered in Django admin with list_display, list_filter, search_fields, readonly_fields

## Task Commits

Each task was committed atomically:

1. **Task 1: Create wardrobe app with Garment model, S3 storage settings, and file cleanup signals** - `761e212` (feat)
2. **Task 2: Create GarmentForm with file validation and register Garment in Django admin** - `22aff0a` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `wardrobe/models.py` - Garment model with CATEGORY_CHOICES (15), two ImageFields, ForeignKey to AUTH_USER_MODEL
- `wardrobe/forms.py` - GarmentForm with Tailwind widget attrs, _validate_image() helper, JPG/PNG + 10 MB validation
- `wardrobe/signals.py` - post_delete handler deleting S3/local files on Garment deletion
- `wardrobe/admin.py` - GarmentAdmin with list_display, list_filter, search_fields, readonly_fields
- `wardrobe/apps.py` - WardrobeConfig with ready() importing wardrobe.signals
- `wardrobe/migrations/0001_initial.py` - Initial Garment migration (applied)
- `requirements.txt` - Added django-storages[s3]>=1.14,<2.0 and Pillow>=10.0,<12.0
- `laundry_advisor/settings/base.py` - Added 'wardrobe' to INSTALLED_APPS
- `laundry_advisor/settings/dev.py` - Added MEDIA_URL and MEDIA_ROOT for local uploads
- `laundry_advisor/settings/prod.py` - Added STORAGES["default"] = S3Storage (extends, not replaces)

## Decisions Made
- **Two-step save pattern:** upload_to callables require instance.pk. Plan 02-02 create view MUST save the Garment record first (without files), then assign file fields and save again.
- **STORAGES extension pattern:** Used `STORAGES["default"] = {...}` not `STORAGES = {...}` to avoid wiping the WhiteNoise staticfiles entry.
- **15 categories locked:** CATEGORY_CHOICES list was specified as locked in the plan — any change requires a migration.

## Deviations from Plan

None - plan executed exactly as written.

The plan's verify command `python -c "from wardrobe.models import Garment; print(Garment.CATEGORY_CHOICES)"` fails because CATEGORY_CHOICES is a module-level list (not a class attribute) and Django setup is required. Verified correctly with `django.setup()` — all 15 categories confirmed. This is a plan documentation issue only, not a code deviation.

## Issues Encountered
None.

## User Setup Required

**External services require manual configuration before wardrobe photo uploads work in production.** The following AWS S3 environment variables must be added to Render:

- `AWS_STORAGE_BUCKET_NAME` — AWS Console -> S3 -> Create bucket -> copy bucket name
- `AWS_S3_REGION_NAME` — AWS Console -> S3 bucket region (e.g. us-east-1)
- `AWS_ACCESS_KEY_ID` — AWS Console -> IAM -> Users -> Security credentials -> Create access key
- `AWS_SECRET_ACCESS_KEY` — AWS Console -> IAM -> Users -> Security credentials -> Create access key

Dashboard steps:
1. Create S3 bucket with public access enabled (uncheck "Block all public access")
2. Add bucket policy for public read
3. Add all 4 env vars to Render Dashboard -> Environment

Note: The app runs fine locally without these (dev uses local filesystem). They are only required for production photo uploads.

## Next Phase Readiness
- Garment data layer complete — Plan 02-02 can immediately build list, create, detail, edit, delete views
- GarmentForm ready for use in views; two-step save pattern documented for create view
- S3 env vars needed in Render before production photo uploads will work (can configure during or after Plan 02-02)

## Self-Check: PASSED

All 11 files confirmed present. Both task commits (761e212, 22aff0a) confirmed in git log.

---
*Phase: 02-wardrobe-crud-with-s3*
*Completed: 2026-03-03*
