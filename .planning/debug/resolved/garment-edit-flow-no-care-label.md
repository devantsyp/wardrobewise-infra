---
status: resolved
trigger: "Garments without care labels or AI-analyzed instructions cannot currently use the Edit button to enter laundry instructions manually."
created: 2026-04-09T00:00:00Z
updated: 2026-04-09T12:00:00Z
---

## Current Focus

hypothesis: CONFIRMED AND FIXED
test: N/A
expecting: N/A
next_action: Awaiting human verification

## Symptoms

expected: A garment with no care label can open the Edit form, enter laundry instructions manually, save them, and have them display correctly. "Reset to AI" should not appear for garments that were never analyzed.
actual: Garments without care labels / analyzed instructions cannot currently use the edit flow.
errors: Unknown — investigate from code
reproduction: Add a garment with no care label, navigate to garment details page, attempt to edit laundry instructions
started: Existing bug/missing feature

## Eliminated

## Evidence

- timestamp: 2026-04-09
  checked: wardrobe/views.py edit_instructions_view (lines 136-162)
  found: |
    When CareAnalysis does not exist, the view immediately redirects with
    "No analysis to edit." message. It never creates a new CareAnalysis
    record for garments that have no prior AI analysis.
  implication: The edit form is completely inaccessible for garments without analysis

- timestamp: 2026-04-09
  checked: templates/wardrobe/garment_detail.html edit form block (lines 161-211)
  found: |
    "Reset to AI" button (line 204-210) renders unconditionally whenever
    `editing` is True — no check for whether AI instructions actually exist.
  implication: Reset to AI would show even for manually-entered instructions with no AI origin

- timestamp: 2026-04-09
  checked: templates/wardrobe/garment_detail.html State A/B block (lines 404-458)
  found: |
    The "No analysis yet" states show only Upload/Analyze buttons. There is
    no "Enter instructions manually" or "Edit Instructions" link in those states.
  implication: User has no UI path to reach the edit form for a garment without analysis

- timestamp: 2026-04-09
  checked: wardrobe/models.py CareAnalysis (lines 68-107)
  found: |
    ai_washing, ai_drying, ai_ironing, ai_bleach, ai_is_delicate, ai_summary
    are all non-nullable TextFields with no blank=True. A manually-created
    CareAnalysis with no AI data must be given empty string values for those
    fields to satisfy the model constraint.
  implication: Can create CareAnalysis with empty ai_* fields and blank failure_reason; is_user_edited=True marks it as manual entry

## Resolution

root_cause: |
  edit_instructions_view (views.py:136-162) returns a redirect with error "No analysis to edit"
  when garment.care_analysis does not exist. There is no code path to create a new
  CareAnalysis record with blank AI fields and manual user values. Additionally, the
  template shows no "Edit Instructions" button in the no-analysis states, so the user
  has no way to navigate to the edit URL at all.

fix: |
  1. In edit_instructions_view: when CareAnalysis does not exist, create one with
     empty ai_* fields (not a failure), render the edit form, and on POST save the
     manually entered values with is_user_edited=True.
  2. In garment_detail.html edit form: add {% if analysis and not analysis.failure_reason and analysis.ai_washing %}
     guard around "Reset to AI" button so it only shows when AI instructions exist.
  3. In garment_detail.html State A/B: add an "Enter instructions manually" link to
     edit_instructions URL so users without a care label photo can access the form.

verification: |
  Self-verified by code inspection:
  - edit_instructions_view now handles analysis=None on GET (renders blank form)
    and on POST (creates CareAnalysis with empty ai_* fields before binding form)
  - CareInstructionsForm binds to the new analysis instance; saved values appear
    in the same display block (State E) as AI-analyzed instructions
  - "Reset to AI" guard `{% if analysis and analysis.ai_washing %}` prevents the
    button appearing when ai_washing is empty (manually-entered garments)
  - "enter instructions manually" link added to State A (no photo, no analysis)
  Awaiting human confirmation that the flow works end-to-end.
files_changed:
  - wardrobe/views.py
  - templates/wardrobe/garment_detail.html
