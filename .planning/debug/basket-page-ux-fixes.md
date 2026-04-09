---
status: resolved
trigger: "Multiple UI/UX issues on the Laundry Basket page plus one analysis-related bug (dedup notification)."
created: 2026-04-07T00:00:00Z
updated: 2026-04-07T00:00:00Z
---

## Current Focus

hypothesis: Root causes pre-diagnosed. Reading files to locate exact code locations before applying fixes.
test: Read basket template, views, base template for each issue location
expecting: Find exact lines for all 7 fixes
next_action: Read basket template and relevant views

## Symptoms

expected: |
  1. Plan auto-generates when user selects garments — no manual buttons needed
  2. "Manage Baskets" link appears below the active basket controls
  3. Rename workflow: second modal with Confirm/Cancel, no inline input
  4. Rename and Delete buttons visually aligned
  5. Logo link redirects authenticated users to /wardrobe/
  6. Stale plan message reads "Adjust your selection to refresh"
  7. from_cache=True shows distinct success message

actual: |
  1. Both "Create Laundry Plan" and "Save Plan" buttons exist
  2. "Manage Baskets" link sits inline with basket dropdown and New Basket button
  3. Manage Baskets modal has inline <input> for rename
  4. Rename button sits slightly higher than Delete button
  5. Logo click goes to "/" for all users
  6. Message says "Re-generate for latest results."
  7. from_cache=True shows same generic success message

errors: No errors — UX/UI issues and missing behavior

reproduction: |
  1. Go to basket page, notice both Create Laundry Plan and Save Plan buttons
  2. Click Manage Baskets, observe inline rename input
  3. Inspect Rename/Delete button alignment in Manage Baskets modal
  4. Click logo from any authenticated page
  5. Trigger a stale plan warning
  6. Analyze a garment that was previously analyzed (same image hash)

started: Identified during Phase 4 UAT

## Eliminated

(none yet)

## Evidence

- timestamp: 2026-04-07T00:00:00Z
  checked: basket.html lines 104, 134-140 (Save Plan button, Create Laundry Plan button in sticky bar)
  found: savePlanBtn at line 104 in plan section header; createPlanBtn at line 134 in sticky bar; toggleGarment calls triggerDebouncedPlanUpdate only when planGenerated=true (line 302); planGenerated set to true only via createPlanBtn click (line 391)
  implication: Fix 1 — remove both buttons, drop planGenerated guard, auto-trigger plan on selection change

- timestamp: 2026-04-07T00:00:00Z
  checked: basket.html lines 12-22 (basket controls row)
  found: manage-baskets-trigger anchor is inside same flex div as basket-selector and new-basket-trigger
  implication: Fix 2 — move Manage Baskets link outside this div, add new row below

- timestamp: 2026-04-07T00:00:00Z
  checked: basket.html lines 172-176 (Manage Baskets modal rename)
  found: inline <form> with <input type="text"> for rename inside Manage Baskets modal; no second modal
  implication: Fix 3 — remove inline input, add rename button that opens a separate Rename Basket modal

- timestamp: 2026-04-07T00:00:00Z
  checked: basket.html line 172 — rename form uses class="inline-flex items-center gap-1"
  found: inline-flex on rename form causes taller layout vs the delete form which uses class="inline"
  implication: Fix 4 — convert rename to a plain button (no form/input), aligned via same flex row

- timestamp: 2026-04-07T00:00:00Z
  checked: base.html line 21
  found: <a href="/"> hardcoded for logo; no auth check
  implication: Fix 5 — use {% if user.is_authenticated %}...{% url 'wardrobe:garment_list' %}...{% endif %}

- timestamp: 2026-04-07T00:00:00Z
  checked: basket.html line 110
  found: stale plan notice text ends with "Re-generate for latest results."
  implication: Fix 6 — replace with "Adjust your selection to refresh."

- timestamp: 2026-04-07T00:00:00Z
  checked: wardrobe/views.py line 100-101 (analyze_care_label_view)
  found: success message is always "Care instructions analyzed successfully." — from_cache flag on returned analysis not consulted
  implication: Fix 7 — check analysis.from_cache and show distinct message

## Resolution

root_cause: |
  Pre-diagnosed:
  1. toggleGarment calls triggerDebouncedPlanUpdate already; planGenerated guard + manual buttons are redundant
  2. Manage Baskets link placed inline in basket controls row
  3. Inline <input> in Manage Baskets modal instead of second modal
  4. inline-flex on rename form wrapper causes vertical offset
  5. Logo anchor hardcoded to "/"
  6. Stale plan message string contains "Re-generate for latest results."
  7. basket/analysis view uses same success message regardless of from_cache

fix: |
  1. basket.html — removed createPlanBtn (sticky bar) and savePlanBtn (plan header); dropped planGenerated guard; fetchAndRenderPlan now auto-shows plan section and calls autoSavePlan silently after each render; plan hides when selection < 2
  2. basket.html — moved Manage Baskets link to its own row below the basket selector / New Basket row (flex-col wrapper)
  3. basket.html — replaced inline rename <form>+<input> in Manage Baskets modal with a plain <button data-rename-*>; added separate Rename Basket modal (z-[60]) with name input, Confirm submit, Cancel returns to Manage Baskets
  4. basket.html — Rename is now a plain <button> with no wrapping form; both Rename and Delete sit in the same flex items-center gap-2 container, so vertical alignment is consistent
  5. base.html — logo href changed to {% if user.is_authenticated %}{% url 'wardrobe:garment_list' %}{% else %}/{% endif %}
  6. basket.html — stale plan message text changed from "Re-generate for latest results." to "Adjust your selection to refresh."
  7. wardrobe/views.py — analyze_care_label_view now shows "Using previous analysis — image was already processed." when analysis.from_cache is True

verification: Self-verified by reading all changed files after edits. All 7 issues addressed. No regressions to unrelated code.
files_changed:
  - templates/laundry/basket.html
  - templates/base.html
  - wardrobe/views.py
