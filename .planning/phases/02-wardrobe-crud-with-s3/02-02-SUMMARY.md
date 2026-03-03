---
phase: 02-wardrobe-crud-with-s3
plan: 02
subsystem: ui
tags: [django, tailwind, function-based-views, s3, imagefield, forms, crud]

# Dependency graph
requires:
  - phase: 02-01
    provides: Garment model with ImageFields, GarmentForm with file validation, two-step save pattern, S3/local dual storage

provides:
  - 5 FBVs: garment_list, garment_detail, garment_create (two-step save), garment_edit (old file deletion), garment_delete (@require_POST)
  - URL namespace 'wardrobe' at /wardrobe/ prefix with 5 patterns
  - 3 Tailwind-styled templates: responsive photo grid (wardrobe_list), full detail page (garment_detail), shared create/edit form (garment_form)
  - User isolation via get_object_or_404(Garment, pk=pk, user=request.user) — 404 (not 403) for other users' garments
  - Empty wardrobe state with hanger icon placeholder and Add Clothing button
  - File upload UI: hidden file inputs, styled upload buttons, JS preview on file select, existing photo thumbnails in edit mode
  - Delete via JS confirm dialog (POST form with CSRF token)
  - "My Wardrobe" nav link for authenticated users in base.html
  - Dev media serving via static() in DEBUG mode
  - Core wardrobe placeholder removed

affects:
  - 02-03 (deploy/prod verification)
  - 03-ai-pipeline (reads garment and care_label photos by URL from detail page context)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Two-step save in garment_create: form.save(commit=False) -> garment.user -> garment.save() -> assign FILES -> garment.save()
    - File replacement in garment_edit: garment.garment_photo.delete(save=False) before form.save() to avoid orphan files
    - User isolation: get_object_or_404(Garment, pk=pk, user=request.user) returns 404 for cross-user access (not 403)
    - Floating label pattern: peer + placeholder=" " + peer-focus/peer-[:not(:placeholder-shown)] translate/scale

key-files:
  created:
    - wardrobe/views.py
    - wardrobe/urls.py
    - templates/wardrobe/wardrobe_list.html
    - templates/wardrobe/garment_detail.html
    - templates/wardrobe/garment_form.html
  modified:
    - laundry_advisor/urls.py
    - core/urls.py
    - core/views.py
    - templates/base.html
    - assets/css/app.css
  deleted:
    - templates/core/wardrobe_placeholder.html

key-decisions:
  - "User isolation returns 404 (not 403) for other users' garments — per user decision in CONTEXT.md"
  - "Delete confirmation uses JS confirm() dialog — no separate confirmation page needed"
  - "Care label photo section hidden entirely on detail page if no photo exists"
  - "My Wardrobe nav link added to base.html for authenticated users"

patterns-established:
  - "Two-step save: save record without files first (get pk), then assign FILES and save again"
  - "File replacement in edit: call .delete(save=False) on existing file before form.save() assigns new one"
  - "Floating label inputs: peer class + placeholder=' ' enables CSS-only label animation without JavaScript"

# Metrics
duration: 5min
completed: 2026-03-03
---

# Phase 2 Plan 02: Wardrobe CRUD Views and Templates Summary

**5 FBVs with user isolation, two-step S3 save, and 3 Tailwind-styled templates — responsive photo grid, detail page with care placeholder, shared create/edit form with floating labels and file upload preview**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-03-03T00:38:22Z
- **Completed:** 2026-03-03T00:43:04Z
- **Tasks:** 2
- **Files modified:** 10 (created 5, modified 4, deleted 1)

## Accomplishments
- All 5 wardrobe CRUD views implemented with @login_required, get_object_or_404 user isolation, two-step save for create, old-file deletion on edit, and POST-only delete
- 3 Tailwind-styled templates: wardrobe_list (2-5 col responsive grid with hanger placeholder), garment_detail (photos, field display, JS confirm delete), garment_form (floating labels, hidden file inputs, JS preview, double-submit prevention)
- Core wardrobe placeholder removed; wardrobe app now owns /wardrobe/ prefix with proper URL namespace
- Dev media serving configured; base.html nav link updated to wardrobe:garment_list
- Tailwind CSS rebuilt to include all new grid/card/form utility classes

## Task Commits

Each task was committed atomically:

1. **Task 1: Create all 5 wardrobe views with user isolation and two-step save** - `594d46f` (feat)
2. **Task 2: Create all wardrobe templates with Tailwind styling and rebuild CSS** - `4fe0920` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified
- `wardrobe/views.py` - 5 FBVs: garment_list, garment_detail, garment_create (two-step save), garment_edit (old file deletion), garment_delete (@require_POST)
- `wardrobe/urls.py` - app_name='wardrobe', 5 URL patterns covering list/detail/add/edit/delete
- `laundry_advisor/urls.py` - Added path('wardrobe/', include('wardrobe.urls')) and DEBUG media serving via static()
- `core/urls.py` - Removed wardrobe placeholder route
- `core/views.py` - Removed wardrobe_placeholder view function
- `templates/core/wardrobe_placeholder.html` - Deleted (wardrobe app owns /wardrobe/)
- `templates/wardrobe/wardrobe_list.html` - Responsive photo grid (2-5 cols), empty state with hanger SVG, card with image/placeholder and name
- `templates/wardrobe/garment_detail.html` - Back link, garment photo, optional care label, field DL (empty fields omitted), care placeholder, Edit + Delete buttons
- `templates/wardrobe/garment_form.html` - Shared create/edit form: enctype=multipart/form-data, floating labels, category select, hidden file inputs with styled buttons and JS preview
- `templates/base.html` - Added My Wardrobe nav link for authenticated users
- `assets/css/app.css` - Rebuilt with all new Tailwind utility classes (grid, aspect-square, object-cover, etc.)

## Decisions Made
- **User isolation returns 404:** get_object_or_404(Garment, pk=pk, user=request.user) — per CONTEXT.md user decision; prevents information leakage vs 403
- **JS confirm for delete:** `onsubmit="return confirm('Delete this garment? This cannot be undone.')"` — no separate confirmation page per user decision
- **Care label section omitted if no photo:** Don't show empty "Care Label" section on detail page if no photo exists
- **My Wardrobe nav link added:** base.html needed to link to wardrobe:garment_list for authenticated users (was missing from Plan 01 — added as part of this plan's base.html update step)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- Task 1 work (views.py, urls.py, laundry_advisor/urls.py changes) had been created before plan execution started but was uncommitted. Committed atomically as Task 1.

## User Setup Required

None - no external service configuration required for this plan. S3 env vars from Plan 02-01 still needed in Render before production photo uploads work.

## Next Phase Readiness
- Full wardrobe CRUD works in the browser at /wardrobe/
- Photos stored locally in dev (media/ directory), S3 in production when env vars are configured
- Plan 02-03 (deploy/verification) can proceed immediately
- Phase 3 AI pipeline can read garment_photo and care_label_photo URLs from Garment model

## Self-Check: PASSED

All 5 created files confirmed present. Both task commits (594d46f, 4fe0920) confirmed in git log.

---
*Phase: 02-wardrobe-crud-with-s3*
*Completed: 2026-03-03*
