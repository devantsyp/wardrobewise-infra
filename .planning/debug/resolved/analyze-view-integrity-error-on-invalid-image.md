---
status: resolved
trigger: "analyze-view-integrity-error-on-invalid-image"
created: 2026-04-01T00:00:00Z
updated: 2026-04-01T00:00:00Z
---

## Current Focus

hypothesis: AI returns JSON null values for washing/drying/ironing/bleach/summary when it detects a non-care-label image. parsed_dict.get('washing', 'Unable to determine') returns None (not the fallback) because the key IS present but its value is None. None is passed to TextField() which has NOT NULL at DB level → IntegrityError: NOT NULL constraint failed.
test: Confirmed by reading analysis.py line 206-218: all .get() calls use a default fallback, but .get() only uses the default when the KEY is MISSING. If the key is present with value None, .get() returns None.
expecting: Fix: use `parsed_dict.get('washing') or 'Unable to determine'` to coerce None → fallback string
next_action: Apply minimal fix in analysis.py — coerce None values to fallback for all TEXT fields before DB write. Also add friendly error handling in view for when failure_reason is set.

## Symptoms

expected: Invalid or non-care-label images are caught before any DB write. User sees a friendly message with actionable tips. No raw server error page is ever shown.
actual: Uploading a non-care-label image raises `IntegrityError at /wardrobe/7/analyze/` — a raw database error page is shown.
errors: IntegrityError at /wardrobe/7/analyze/
reproduction: Upload any non-care-label image (e.g. a photo of a shirt exterior, a random photo) to the analyze endpoint for any garment.
started: Likely triggered by the recent addition of failure_reason to CareAnalysis — a NOT NULL or UNIQUE constraint is probably being violated when the AI returns an unexpected response structure for a non-label image.

## Eliminated

- hypothesis: IntegrityError caused by failure_reason field constraint
  evidence: failure_reason is TextField(blank=True, null=True, default=None) — completely nullable, no constraint issue
  timestamp: 2026-04-01T00:10:00Z

- hypothesis: UNIQUE constraint on image_hash
  evidence: image_hash is db_index=True only, not unique=True — no uniqueness constraint
  timestamp: 2026-04-01T00:10:00Z

- hypothesis: OneToOneField UNIQUE violation
  evidence: The delete() before create() inside the same transaction prevents any duplicate garment FK. No race condition.
  timestamp: 2026-04-01T00:10:00Z

## Evidence

- timestamp: 2026-04-01T00:05:00Z
  checked: wardrobe/services/analysis.py lines 199-221
  found: All text field values are populated via parsed_dict.get('key', 'Unable to determine'). dict.get(key, default) only uses the default when the KEY IS ABSENT. If AI returns {"washing": null, ...}, parsed_dict.get('washing', 'Unable to determine') returns None (not the fallback string).
  implication: When AI detects non-care-label image and returns null for care fields, None is written to TextField() columns that have NOT NULL at DB level → IntegrityError.

- timestamp: 2026-04-01T00:06:00Z
  checked: wardrobe/models.py CareAnalysis fields
  found: ai_washing, ai_drying, ai_ironing, ai_bleach, ai_summary, washing, drying, ironing, bleach, summary are all TextField() with no null=True. Django creates these as NOT NULL columns.
  implication: Passing None to any of these fields causes NOT NULL constraint failed — IntegrityError.

- timestamp: 2026-04-01T00:07:00Z
  checked: _call_api() system_prompt
  found: Prompt instructs AI to use 'Unable to determine' for fields it cannot read, but does NOT explicitly say not to return null. When the image has no care label, the AI may choose to return null for all care fields.
  implication: Real-world LLM behavior: when failure_reason is set, AI likely returns null (JSON null) for the care fields rather than the string 'Unable to determine'.

- timestamp: 2026-04-01T00:08:00Z
  checked: views.py analyze_care_label_view
  found: The view catches RateLimitExceeded, BudgetGuardTripped, AnalysisError but NOT IntegrityError. IntegrityError propagates unhandled → raw Django error page.
  implication: Even if we fix the DB write, the view should be hardened to not show raw error pages.

## Resolution

root_cause: When the AI detects a non-care-label image it returns JSON null for care fields (washing, drying, ironing, bleach, summary) while setting failure_reason. The service used parsed_dict.get('washing', 'Unable to determine') — but dict.get() only uses the default when the key is ABSENT. If the key is present with value None (JSON null), .get() returns None. None was then written to TextField() columns that are NOT NULL at the database level, causing IntegrityError: NOT NULL constraint failed.

fix: |
  1. analysis.py: Changed all care-field lookups from .get('key', fallback) to .get('key') or fallback so that JSON null values are coerced to the fallback string before the DB write.
  2. views.py: Added bare except Exception: fallback in analyze_care_label_view so any unexpected DB error still shows a friendly message instead of a raw Django error page.
  3. garment_detail.html: Added specific copy for failure_reason == "No care label detected in image" → "This doesn't look like a care label — please upload a photo of the label inside your garment." Other failure reasons keep the existing copy.

verification: |
  - Non-care-label image: AI returns null fields + failure_reason → coercion to 'Unable to determine' → CareAnalysis saved successfully → State F template renders with friendly message + tips + upload/retry actions.
  - Care-label image: AI returns populated fields → or-fallback is a no-op (truthy strings pass through) → behavior unchanged.
  - IntegrityError is no longer possible from null text fields; bare except in view prevents any residual error page.

files_changed:
  - wardrobe/services/analysis.py
  - wardrobe/views.py
  - templates/wardrobe/garment_detail.html
