---
status: resolved
trigger: "temperature field from care label analysis can return words instead of a number"
created: 2026-04-09T00:00:00Z
updated: 2026-04-09T00:00:02Z
---

## Current Focus

hypothesis: CONFIRMED AND FIXED
next_action: complete

## Symptoms
<!-- Written during gathering, then IMMUTABLE -->

expected: temperature field is always a number (e.g., 30, 40, 60)
actual: sometimes returns a string like "coolest wash" instead of a numeric value
errors: no crash — silent data quality issue; wrong type stored/displayed
reproduction: analyze a garment whose care label specifies temperature as a descriptive phrase rather than a number (e.g., "wash at coolest wash", "cold wash")
started: identified during Phase 4 UAT

## Eliminated

- hypothesis: AI prompt returns non-numeric temperature — no temperature field in AI JSON schema; temperature is only derived inside grouping.py
  evidence: analysis.py system prompt has no "temperature" key; CareAnalysis model has no temperature field
  timestamp: 2026-04-09

- hypothesis: temperature key in load dict is a string — _build_load always receives temp_bucket (int from _normalise_bucket) and stores it as 'temperature'
  evidence: _normalise_bucket always returns int (30, 40, or 60); _build_load parameter typed as int
  timestamp: 2026-04-09

## Evidence

- timestamp: 2026-04-09
  checked: wardrobe/services/analysis.py system_prompt and CareAnalysis model
  found: no temperature field exists in the AI JSON schema or the Django model; temperature is derived only inside grouping.py from the free-text 'washing' field
  implication: the bug is purely in grouping.py, not in AI analysis

- timestamp: 2026-04-09
  checked: grouping.py _extract_temperature (lines 82-103) and _normalise_bucket (lines 106-114)
  found: _extract_temperature returns (None, False) when input is unparseable (e.g. "coolest wash"); _normalise_bucket(None) returns 30
  implication: temp_bucket is always an int; the string "Coolest wash" only appears in temp_label

- timestamp: 2026-04-09
  checked: grouping.py line 191
  found: temp_label = f"{temp_bucket}°C" if raw_temp is not None else 'Coolest wash'
  implication: when washing text has no parseable temperature, temp_label is the string 'Coolest wash' rather than '30°C'

- timestamp: 2026-04-09
  checked: grouping.py line 206 (grouping key)
  found: color_temp_groups[(color_group, temp_bucket, temp_label)].append(g['pk'])
  implication: temp_label is part of the grouping key — a garment with "coolest wash" and a garment with explicit "30°C" both have temp_bucket=30 but different temp_labels, so they land in separate loads when they should be in the same load

- timestamp: 2026-04-09
  checked: basket.html line 461 (JS renderPlan)
  found: const tempLabel = load.temp_label || `${load.temperature}°C`; — the UI uses temp_label for display; when temp_label is 'Coolest wash' it is shown as-is
  implication: the UAT tester saw "Coolest wash" displayed where a numeric temperature (e.g. "30°C") was expected

- timestamp: 2026-04-09
  checked: all 26 grouping tests after fix applied
  found: all pass, including new test_temperature_descriptive_phrase_grouped_with_explicit_30
  implication: fix is correct and complete

## Resolution

root_cause: In grouping.py, when washing instructions contain descriptive temperature phrases (e.g. "coolest wash") rather than a numeric value, temp_label was set to the string 'Coolest wash' instead of a numeric label like '30°C'. This caused two bugs: (1) users saw "Coolest wash" displayed where a consistent numeric temperature was expected, and (2) the grouping key included temp_label, so garments with "coolest wash" language were grouped separately from garments with explicit 30°C despite both resolving to the same temp_bucket=30, producing unnecessary extra loads.

fix: 1. Changed temp_label to always use f"{temp_bucket}°C" (removed the 'Coolest wash' special case). The normalised bucket integer is the authoritative wash temperature; it should always display as a number.
    2. Removed temp_label from the grouping key tuple so only (color_group, temp_bucket) drives grouping — garments with descriptive and numeric 30°C instructions now correctly merge into one load.
    3. Updated existing tests that asserted temp_label == 'Coolest wash' to assert '30°C'.
    4. Added new regression test: test_temperature_descriptive_phrase_grouped_with_explicit_30.

verification: All 26 unit tests pass (Ran 26 tests in 0.002s — OK).
files_changed: [laundry/services/grouping.py, laundry/tests/test_grouping.py]
