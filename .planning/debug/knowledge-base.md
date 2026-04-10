# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## temperature-non-numeric — basket planner shows "Coolest wash" string instead of numeric temperature; garments with descriptive wash phrases grouped separately from explicit 30°C garments
- **Date:** 2026-04-09
- **Error patterns:** temperature, coolest wash, temp_label, grouping, numeric, string, non-numeric, descriptive phrase, washing instructions
- **Root cause:** grouping.py set temp_label to the string 'Coolest wash' when washing instructions had no parseable numeric temperature, and included temp_label in the grouping key tuple — causing both a non-numeric display label and incorrect load splitting for garments that share the same temp_bucket.
- **Fix:** Always derive temp_label as f"{temp_bucket}°C"; remove temp_label from the grouping key so only (color_group, temp_bucket) drives load grouping.
- **Files changed:** laundry/services/grouping.py, laundry/tests/test_grouping.py
---

## laundry-page-muted-purple-color — laundry page muted-purple text color overridden to #aa7ec2
- **Date:** 2026-04-07
- **Error patterns:** muted purple, accent-500, accent-400, text color, laundry page, #9C92A3, readability
- **Root cause:** The laundry page uses Tailwind utility classes text-accent-500 (#9C92A3) and text-accent-400 (#a89db0) for muted purple text, shared with the nav bar via the global design system. A targeted override was needed scoped to <main> content only.
- **Fix:** Added a <style> block inside {% block content %} of templates/laundry/basket.html overriding main .text-accent-500 and main .text-accent-400 with color #aa7ec2. Nav bar is unaffected; all 14 accent-text usages on the laundry page (including JS-injected content) are covered.
- **Files changed:** templates/laundry/basket.html
---

## garment-edit-flow-no-care-label — garments without care labels cannot access the edit laundry instructions form
- **Date:** 2026-04-09
- **Error patterns:** edit instructions, no care label, no analysis, CareAnalysis, edit form, no analysis to edit, is_user_edited, manual entry, garment detail
- **Root cause:** edit_instructions_view returned a redirect with "No analysis to edit" when no CareAnalysis existed for the garment — no code path created a new record for manual entry. The template also lacked an "Enter instructions manually" link in the no-analysis state and showed "Reset to AI" unconditionally during editing.
- **Fix:** (1) edit_instructions_view now creates a blank CareAnalysis with empty ai_* fields on GET/POST when none exists, allowing manual entry with is_user_edited=True. (2) "Reset to AI" button guarded with {% if analysis and analysis.ai_washing %} so it only appears when AI instructions exist. (3) "Enter instructions manually" link added to the State A (no photo, no analysis) block in garment_detail.html.
- **Files changed:** wardrobe/views.py, templates/wardrobe/garment_detail.html
---

