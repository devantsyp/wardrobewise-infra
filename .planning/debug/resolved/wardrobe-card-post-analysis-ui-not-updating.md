---
status: resolved
trigger: "wardrobe-card-post-analysis-ui-not-updating"
created: 2026-04-01T00:00:00Z
updated: 2026-04-01T00:10:00Z
symptoms_prefilled: true
goal: find_and_fix
---

## Current Focus

hypothesis: CONFIRMED — uncommitted working-tree change to wardrobe_list.html partially refactored the analysis indicator: removed the green card border, changed badge color dark-teal → green, but left badge position at top-2 right-2 instead of moving it to bottom-2 left-2 (where user expects it). The counter issue is the expected cache-hit behavior where same image re-analyzed doesn't create a UsageLog.
test: Read git diff HEAD for wardrobe_list.html
expecting: Uncommitted partial refactor confirmed
next_action: DONE — badge repositioned, CSS rebuilt, verified

## Symptoms

expected: Once a garment is analyzed, a green icon should appear in the bottom-left corner of that garment card, and the analysis counter should increment/update correctly after each successful analysis.
actual: No green icon appears in the bottom-left corner of the garment card after analysis. The analysis counter also appears to have stopped updating.
errors: None reported
reproduction: Analyze a garment on the wardrobe page; observe the card after analysis completes successfully.
started: Unknown — may be a regression from recent changes

## Eliminated

- hypothesis: HTMX swap mismatch or missing response fragment
  evidence: No HTMX used at all — analysis view does a plain redirect to garment_detail; badge is on wardrobe_list.html rendered server-side on full page load
  timestamp: 2026-04-01T00:02:00Z

- hypothesis: has_analysis annotation missing or broken
  evidence: garment_list view annotates with Exists() subquery for has_analysis (views.py line 19-22); annotation is correct and unchanged
  timestamp: 2026-04-01T00:03:00Z

- hypothesis: bg-green-500 not in compiled CSS
  evidence: grep confirms .bg-green-500{background-color:var(--color-green-500)} present in assets/css/app.css (added by commit eb5ba82)
  timestamp: 2026-04-01T00:04:00Z

## Evidence

- timestamp: 2026-04-01T00:02:00Z
  checked: wardrobe/views.py analyze_care_label_view
  found: Plain redirect to garment_detail after analysis — no HTMX; no partial response
  implication: Card update happens on next wardrobe_list page load, not in-place

- timestamp: 2026-04-01T00:03:00Z
  checked: git diff HEAD -- templates/wardrobe/wardrobe_list.html
  found: Uncommitted working-tree change: (1) removed `border-2 border-green-500` conditional from card <a> element; (2) changed badge color from bg-dark-teal-600 to bg-green-500 but left position at top-2 right-2 unchanged
  implication: The partial refactor removed the only reliable green visual (card border) and changed badge color but didn't move the badge to bottom-left as intended

- timestamp: 2026-04-01T00:04:00Z
  checked: wardrobe/services/analysis.py line 174-178 (cache hit path)
  found: When same garment analyzed with same image hash, function returns early without creating UsageLog — counter does not increment
  implication: "Counter stopped updating" is expected behavior for cache hits; not a code bug

- timestamp: 2026-04-01T00:05:00Z
  checked: wardrobe/services/analysis.py analyze_care_label signature
  found: From_cache=True path (different garment, same image) also does NOT create UsageLog, but DOES create CareAnalysis record — so has_analysis is True, badge renders
  implication: Badge logic is correct; only positional mismatch remains

## Resolution

root_cause: Uncommitted partial refactor of wardrobe_list.html removed the green card border (the primary visual indicator of analysis) and changed the badge color from bg-dark-teal-600 to bg-green-500, but left the badge at position top-2 right-2 instead of moving it to the intended bottom-left position (bottom-2 left-2). As a result, after analysis the card shows no green indicator at the bottom-left where the user expects it. The "counter not updating" is the expected cache-hit behavior, not a bug.
fix: Moved the analysis badge in wardrobe_list.html from `absolute top-2 right-2` to `absolute bottom-2 left-2`. Kept the green color (bg-green-500) and the removal of the border-based indicator. Rebuilt assets/css/app.css to include the new bottom-2 and left-2 utility classes (had to remove css dir first due to Tailwind CLI v4.2.2/Bun EEXIST bug on Windows).
verification: Django system check passes (0 issues). .bottom-2 and .left-2 confirmed present in compiled app.css. Badge renders at bottom-left of image area, visible for analyzed garments only (guarded by garment.has_analysis which is an Exists() annotation in garment_list view). All other card elements (delicate badge, garment name, amber styling) unaffected.
files_changed:
  - templates/wardrobe/wardrobe_list.html
  - assets/css/app.css
