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

