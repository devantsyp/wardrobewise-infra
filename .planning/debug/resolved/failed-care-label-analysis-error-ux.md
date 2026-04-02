---
status: resolved
trigger: "failed-care-label-analysis-error-ux"
created: 2026-04-01T00:00:00Z
updated: 2026-04-01T00:05:00Z
---

## Current Focus

hypothesis: CONFIRMED. The root cause is a two-layer gap: (1) the AI prompt instructs the model to never give image-quality caveats, preventing structured failure reasons from coming back; (2) the view catches AnalysisError with a single generic string and the template echoes it verbatim with no tips. There is no failure_reason field or image-quality guidance in the system.
test: N/A — root cause confirmed by code reading.
expecting: N/A
next_action: Implement fix — update AI prompt to return a failure_reason on bad images, surface it in the view context, update the template to show the reason + tips.

## Symptoms

expected: When analysis fails, the user sees a specific reason why it failed (e.g. "Care label text was not readable", "No care label detected in image", "Image too blurry"). Actionable image-quality tips are shown so the user knows how to retake the photo and succeed on retry.
actual: A generic failure message is shown with no specific reason or guidance.
errors: None — this is a UX enhancement, not a crash.
reproduction: Upload a poor-quality care label image and trigger analysis; observe the failure state shown to the user.
started: New enhancement — specific error messaging has never existed.

## Eliminated

(none yet)

## Evidence

- timestamp: 2026-04-01T00:01:00Z
  checked: wardrobe/services/analysis.py _call_api()
  found: The system prompt explicitly says "no caveats about image quality" and instructs the model to always fill every field with "Unable to determine" when it cannot read the label. There is no failure_reason or success/failure concept in the AI response schema.
  implication: The AI will never communicate WHY it couldn't read a label; it just quietly fills all fields with "Unable to determine".

- timestamp: 2026-04-01T00:01:30Z
  checked: wardrobe/views.py analyze_care_label_view()
  found: AnalysisError is caught and messages.error() is called with the hardcoded string "Analysis failed. Please try again." — no reason, no tips.
  implication: Even if the AI returned a reason, the view discards the AnalysisError's message and uses a hardcoded fallback.

- timestamp: 2026-04-01T00:02:00Z
  checked: templates/wardrobe/garment_detail.html lines 216-229
  found: The template checks for the analysis_failed extra_tag and renders: "Analysis failed. Please try again." with a Retry button. No failure reason, no image-quality tips.
  implication: This is the generic failure UI the user sees.

- timestamp: 2026-04-01T00:02:30Z
  checked: wardrobe/models.py CareAnalysis
  found: No failure_reason field exists on CareAnalysis. No separate AnalysisFailure model exists.
  implication: There is nowhere to persist a failure reason — it must be passed through the Django messages framework or a new model field.

- timestamp: 2026-04-01T00:03:00Z
  checked: wardrobe/services/analysis.py analyze_care_label() return path
  found: The service only raises exceptions (BudgetGuardTripped, RateLimitExceeded, AnalysisError) or returns a CareAnalysis. There is no "soft failure" concept where analysis succeeds but the label was unreadable.
  implication: The cleanest fix is: (1) update the AI prompt to include an optional failure_reason field; (2) when the AI response indicates a failure_reason (or all fields are "Unable to determine"), surface it in the view; (3) update the template failure block with specific reason + tips.

## Resolution

root_cause: >
  Three-layer gap: (1) The AI prompt actively suppressed failure feedback ("no caveats about image quality")
  and had no structured failure_reason field in its schema, so the model could never communicate why a label
  was unreadable. (2) The CareAnalysis model had no field to persist a failure reason across the
  POST->redirect->GET cycle. (3) The template had a single hard-failure block ("Analysis failed. Please try again.")
  with no reason or tips, and the soft-failure state (analysis record exists but unreadable) fell through to
  the success display showing all "Unable to determine" fields.
fix: >
  (1) Updated _call_api() system prompt to include a failure_reason field in the JSON schema with four
  enumerated values, and set it to null on success. (2) Added failure_reason nullable TextField to
  CareAnalysis model with migration 0004. (3) Service layer extracts failure_reason from parsed_dict and
  stores it on the new CareAnalysis record. (4) View suppresses generic success toast when failure_reason
  is set. (5) Template adds State F block ({% elif analysis and analysis.failure_reason %}) with specific
  failure reason text, five actionable image-quality tips, and Upload New Photo + Retry with Current Photo
  buttons. Hard failure block (AnalysisError) updated with a service-error explanation separate from the
  image-quality message.
verification: >
  - django check passes (0 issues)
  - Migration 0004 applied cleanly
  - Template parses without errors (manage.py shell confirm)
  - Code review: all failure states map correctly — State F only triggers when analysis.failure_reason is
    truthy; State E (success) only triggers when analysis exists with no failure_reason.
files_changed:
  - wardrobe/models.py: added failure_reason nullable TextField to CareAnalysis
  - wardrobe/migrations/0004_add_failure_reason.py: migration for new field
  - wardrobe/services/analysis.py: updated AI prompt schema + extracted/stored failure_reason
  - wardrobe/views.py: suppress success toast when analysis has failure_reason
  - templates/wardrobe/garment_detail.html: new State F soft-failure block with reason + tips + action buttons; improved hard-failure text
