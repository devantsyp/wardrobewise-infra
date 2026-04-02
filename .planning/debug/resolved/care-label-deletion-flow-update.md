---
status: resolved
trigger: "Update the deletion flow so that removing a care label analysis also deletes the uploaded care label image, immediately prompts the user to upload a replacement image, and shows a warning that deleting the analysis will also delete the care label image."
created: 2026-04-01T00:00:00Z
updated: 2026-04-01T00:20:00Z
symptoms_prefilled: true
---

## Current Focus

hypothesis: CONFIRMED. All three requirements implemented and verified.
test: Django system check passed (0 issues). End-to-end wiring verified via grep.
expecting: n/a
next_action: DONE

## Symptoms

expected:
1. Deleting a care label analysis also deletes the associated care label image from storage.
2. After deletion, the user is immediately prompted to upload a replacement care label image.
3. A warning is shown before deletion: "Deleting the analysis will also delete the care label image."

actual: Deletion removes the CareAnalysis record only. No image deletion, no replacement prompt, no warning.

errors: None — feature/flow enhancement.

reproduction: On the wardrobe page, trigger deletion of a care label analysis on a garment card.

started: New feature request — never existed.

## Eliminated

(none yet)

## Evidence

- timestamp: 2026-04-01T00:05:00Z
  checked: wardrobe/views.py delete_analysis_view (lines 165-173)
  found: Only calls analysis.delete() then redirects to garment_detail. No image deletion, no post-delete upload prompt.
  implication: Root cause confirmed — three things are missing.

- timestamp: 2026-04-01T00:05:00Z
  checked: wardrobe/signals.py
  found: post_delete signal on Garment deletes both garment_photo and care_label_photo from storage. No equivalent signal for CareAnalysis deletion.
  implication: The pattern for file deletion on delete is already established via signals. We need the same for care_label_photo when analysis is deleted.

- timestamp: 2026-04-01T00:05:00Z
  checked: wardrobe/models.py Garment model
  found: care_label_photo lives on the Garment model (not CareAnalysis). So deleting CareAnalysis does NOT cascade to delete the image file.
  implication: delete_analysis_view must explicitly clear garment.care_label_photo and delete the file in addition to deleting the CareAnalysis record.

- timestamp: 2026-04-01T00:05:00Z
  checked: templates/wardrobe/garment_detail.html (lines 330-339)
  found: Delete Analysis button has confirm() dialog but warning text only says "Delete this analysis? This will remove all care instructions." No mention of care label image being deleted.
  implication: Warning text must be updated to mention image deletion.

- timestamp: 2026-04-01T00:05:00Z
  checked: templates/wardrobe/garment_detail.html (lines 342-381)
  found: After deletion, redirect goes to garment_detail which shows State A (no photo, no analysis) — just a disabled "Analyze Care Label" button and a note. No automatic upload prompt is shown.
  implication: After deletion, we need to show an upload section. The garment_edit page already has a care_label_photo file input but redirecting there changes context. Best approach: show an inline upload form in garment_detail when there is no care_label_photo and no analysis (State A), or pass a flag from delete_analysis_view via a message to open/highlight the upload panel.

- timestamp: 2026-04-01T00:05:00Z
  checked: wardrobe/views.py garment_edit (line 63-78) and forms.py
  found: GarmentForm handles care_label_photo upload. We can add a dedicated upload-only endpoint or reuse garment_edit. A cleaner approach: add an upload_care_label_view that only updates care_label_photo, then show that inline form in garment_detail State A.
  implication: We need a new lightweight view for uploading just the care label photo, and expose it in the detail template.

## Resolution

root_cause: delete_analysis_view only deletes the CareAnalysis DB record. It does not: (1) delete care_label_photo from storage or clear it from the Garment, (2) warn the user that the image will be deleted, (3) prompt for a replacement upload after deletion.
fix: |
  1. delete_analysis_view now clears garment.care_label_photo (file deleted from storage via .delete(save=False), field set to None, saved).
  2. confirm() dialog text updated: "This will also delete the uploaded care label image."
  3. New CareLabelUploadForm (forms.py) — validates type/size, mirrors GarmentForm validation.
  4. New upload_care_label_view (views.py) — POST-only, validates via form, deletes old file before saving new.
  5. New URL: <int:pk>/care-label/upload/ -> upload_care_label_view (name='upload_care_label').
  6. State A in garment_detail.html now shows inline "Upload Care Label" button (file input triggers auto-submit) so user is immediately prompted after deletion.
verification: Django check passed (0 issues). All references verified end-to-end via grep.
files_changed:
  - wardrobe/views.py
  - wardrobe/forms.py
  - wardrobe/urls.py
  - templates/wardrobe/garment_detail.html
