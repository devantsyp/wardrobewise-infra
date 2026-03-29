---
phase: 03-care-label-analysis-pipeline
plan: 03
subsystem: web
tags: [django, forms, views, admin, edit, crud]

# Dependency graph
requires:
  - phase: 03-care-label-analysis-pipeline/03-02
    provides: analyze_care_label_view, garment_detail with 5-state UI, href="#" Edit Instructions placeholder

provides:
  - CareInstructionsForm for editing care instructions (washing/drying/ironing/bleach/is_delicate/personal_notes)
  - edit_instructions_view at /wardrobe/<pk>/instructions/edit/
  - reset_instructions_view at /wardrobe/<pk>/instructions/reset/
  - delete_analysis_view at /wardrobe/<pk>/analysis/delete/
  - CareAnalysisAdmin with pretty-printed raw JSON and readonly AI fields
  - UsageLogAdmin fully read-only audit log with date hierarchy

affects:
  - wardrobe/forms.py (CareInstructionsForm added)
  - wardrobe/views.py (3 new views)
  - wardrobe/urls.py (3 new URL routes)
  - wardrobe/admin.py (2 new admin registrations)
  - templates/wardrobe/garment_detail.html (edit mode section, Delete Analysis, wired Edit link)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Edit form replaces read-only instructions section via {% if editing %} conditional — no separate template needed
    - Reset to AI version as separate <form> below edit form — avoids nested forms (invalid HTML)
    - Delete Analysis with browser confirm() dialog — lightweight confirmation without JS modal
    - CareAnalysisAdmin.raw_ai_json_pretty: format_html with <pre> tag for human-readable JSON diff
    - UsageLogAdmin has_add/change/delete_permission all return False — fully immutable audit log

key-files:
  created: []
  modified:
    - wardrobe/forms.py (added CareInstructionsForm, added CareAnalysis import)
    - wardrobe/views.py (added edit_instructions_view, reset_instructions_view, delete_analysis_view)
    - wardrobe/urls.py (added edit_instructions, reset_instructions, delete_analysis URL routes)
    - wardrobe/admin.py (replaced single GarmentAdmin with GarmentAdmin + CareAnalysisAdmin + UsageLogAdmin)
    - templates/wardrobe/garment_detail.html (edit mode section, Delete Analysis button, wired Edit Instructions link)

key-decisions:
  - "CareInstructionsForm uses TextInput (not Textarea) for washing/drying/ironing/bleach — single-line instructions; Textarea only for personal_notes"
  - "Reset to AI version as separate form element (not nested inside edit form) — nested forms are invalid HTML and cause unpredictable browser behavior"
  - "Delete Analysis uses browser confirm() dialog — sufficient for destructive action confirmation without adding JS modal infrastructure"
  - "CareAnalysisAdmin ai_* fields in readonly_fields — immutable AI output must never be accidentally edited via admin"
  - "UsageLogAdmin has_add/change/delete_permission return False — append-only audit log (ANLZ-04/ANLZ-11)"
  - "edit_instructions_view lazy-imports CareInstructionsForm inside method body — avoids potential circular import between views and forms"

# Metrics
duration: 10min
completed: 2026-03-29
---

# Phase 3 Plan 03: Edit Instructions, Delete Analysis, and Admin Integration Summary

**Edit/reset/delete care instructions flow with Django admin for CareAnalysis (pretty JSON) and read-only UsageLog audit — completes Phase 3 feature set**

## Performance

- Tasks completed: 3/3
- Duration: ~10 min
- Files modified: 5

## What Was Built

### Task 1: Edit instructions form, views, and URL routes

Added `CareInstructionsForm` to `wardrobe/forms.py` — a `ModelForm` bound to `CareAnalysis` with six fields: `washing`, `drying`, `ironing`, `bleach`, `is_delicate`, and `personal_notes`. Text fields use `TextInput` with matching Tailwind classes from `GarmentForm`; `is_delicate` uses `CheckboxInput`; `personal_notes` uses `Textarea`.

Added three views to `wardrobe/views.py`:
- `edit_instructions_view`: GET shows edit form in garment detail template with `editing=True`; POST validates, saves, sets `is_user_edited=True`, flashes "Instructions updated."
- `reset_instructions_view` (`@require_POST`): Copies all `ai_*` fields back to user-editable fields, clears `personal_notes`, resets `is_user_edited=False`, flashes "Instructions reset to AI version."
- `delete_analysis_view` (`@require_POST`): Deletes `CareAnalysis` record, flashes "Analysis deleted."

All three views use `get_object_or_404(Garment, pk=pk, user=request.user)` for user isolation.

Registered three URL routes in `wardrobe/urls.py`:
- `<int:pk>/instructions/edit/` → `edit_instructions`
- `<int:pk>/instructions/reset/` → `reset_instructions`
- `<int:pk>/analysis/delete/` → `delete_analysis`

### Task 2: Garment detail template edit mode

Updated `templates/wardrobe/garment_detail.html`:
- Wired `href="#"` placeholder to `{% url 'wardrobe:edit_instructions' garment.pk %}`
- Added `{% if editing %}` conditional wrapping the entire instructions section
- Edit mode shows: care label thumbnail for reference, per-field form inputs (loops `edit_form` fields), Save and Cancel buttons
- Reset to AI version is a separate `<form>` (not nested) to avoid invalid HTML
- Added Delete Analysis `<form>` with `onsubmit confirm()` dialog in the action buttons area

### Task 3: Django admin for CareAnalysis and UsageLog

Replaced single `GarmentAdmin` in `wardrobe/admin.py` with three registrations:

**CareAnalysisAdmin:**
- `list_display`: garment, user email, analyzed_at, from_cache, is_user_edited, is_delicate
- `list_filter`: from_cache, is_user_edited, is_delicate, analyzed_at
- `readonly_fields`: all `ai_*` fields, `image_hash`, `raw_ai_json_pretty`, timestamps, `from_cache`
- Custom `raw_ai_json_pretty` method renders `json.dumps(..., indent=2)` inside `<pre>` via `format_html`

**UsageLogAdmin:**
- `list_display`: user, garment, prompt_tokens, completion_tokens, cost_usd, created_at
- `date_hierarchy`: created_at
- All fields readonly; `has_add_permission`, `has_change_permission`, `has_delete_permission` all return `False`

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

## Self-Check

### Files Verified

- wardrobe/forms.py — CareInstructionsForm present with correct fields
- wardrobe/views.py — edit_instructions_view, reset_instructions_view, delete_analysis_view present
- wardrobe/urls.py — 3 new URL routes registered
- wardrobe/admin.py — CareAnalysisAdmin and UsageLogAdmin registered
- templates/wardrobe/garment_detail.html — edit mode conditional, Delete Analysis, wired Edit link

### Commits Verified

- 6d65a97: feat(03-03): add CareInstructionsForm, edit/reset/delete views, and URL routes
- 8c16ede: feat(03-03): add edit mode, delete action, and wire Edit Instructions link in garment detail
- bc2e74b: feat(03-03): register CareAnalysis and UsageLog in Django admin

## Self-Check: PASSED
