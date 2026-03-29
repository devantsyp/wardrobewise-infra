---
phase: 03-care-label-analysis-pipeline
plan: 02
subsystem: web
tags: [django, templates, views, rate-limiting, ui, analysis]

# Dependency graph
requires:
  - phase: 03-care-label-analysis-pipeline/03-01
    provides: analyze_care_label() service, RateLimitExceeded, BudgetGuardTripped, AnalysisError, daily_usage_counter context processor

provides:
  - analyze_care_label_view POST endpoint at /wardrobe/<pk>/analyze/
  - 5-state care instructions section on garment detail page
  - Nav counter showing daily usage on wardrobe pages
  - Analysis badge on wardrobe grid cards

affects:
  - 03-03 (edit_instructions URL will replace href="#" placeholder in garment_detail.html)
  - templates/wardrobe/garment_detail.html (wired to service layer, full care instructions UI)
  - templates/base.html (nav counter active for all authenticated wardrobe pages)
  - templates/wardrobe/wardrobe_list.html (analysis badge using has_analysis annotation)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Sentinel message strings ("daily_limit_reached", "budget_guard_tripped", "analysis_failed") passed via Django messages framework — templates check for specific strings to render appropriate UI
    - Explicit analysis context from try/except CareAnalysis.DoesNotExist — avoids ambiguous reverse OneToOne access in templates
    - Exists() subquery annotation for has_analysis on garment list — single query, no N+1
    - Vanilla JS countdown timer for midnight reset (no dependencies)
    - Loading state via form submit event listener — disables button, shows spinner SVG + "Analyzing..."

key-files:
  created: []
  modified:
    - wardrobe/views.py (analyze_care_label_view, updated garment_detail + garment_list views)
    - wardrobe/urls.py (added analyze_care_label URL route)
    - templates/wardrobe/garment_detail.html (full care instructions section replacing placeholder)
    - templates/base.html (daily usage counter in nav)
    - templates/wardrobe/wardrobe_list.html (analysis badge on garment cards)

key-decisions:
  - "Sentinel message strings: error message values are sentinel keys (e.g. 'analysis_failed') that templates check — actual user-facing text lives in templates, not views"
  - "Explicit analysis context: garment_detail view does try/except CareAnalysis.DoesNotExist and passes analysis=None — avoids unreliable reverse OneToOne truthiness in templates"
  - "href='#' placeholder for Edit Instructions: Plan 03-03 will wire this to wardrobe:edit_instructions — avoids fake URL stub"
  - "has_analysis via Exists() annotation: single optimized query with subquery instead of prefetch_related which does not prevent DoesNotExist on reverse OneToOne access"
  - "&#10003; checkmark entity for analysis badge: avoids emoji, renders as standard HTML entity"
  - "&#9888; warning entity for delicates badge: functional UI indicator without emoji dependency"

# Metrics
duration: 3min
completed: 2026-03-29
---

# Phase 3 Plan 02: Analysis View and UI Summary

**Synchronous analyze endpoint with 5-state garment detail UI, midnight countdown, nav usage counter, and grid analysis badge — fully wired to the service layer from 03-01**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-29T23:29:43Z
- **Completed:** 2026-03-29T23:32:52Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- analyze_care_label_view POST handler calls service layer, catches all 3 exceptions, redirects with sentinel message strings
- Garment detail page handles 5 full states: no photo (disabled button + tooltip), pre-analysis (enabled Analyze button with loading spinner), rate-limit-reached (inline countdown timer), budget-guard-tripped (temporary unavailable), and results (summary sentence + bullet list + delicates badge + thumbnail + timestamp + re-analyze)
- Daily usage counter added to nav bar with color coding: normal (0-6), amber warning (7-9), red (10) — only visible on wardrobe pages via context processor gating
- Wardrobe grid cards show teal checkmark badge for analyzed garments using Exists() annotation (no N+1)

## Task Commits

Each task was committed atomically:

1. **Task 1: Analyze view + URL route + garment detail view update** - `70a6c4e` (feat)
2. **Task 2: Garment detail template — care instructions display, analyze button, rate limit UI** - `9c99bb8` (feat)

## Files Created/Modified

- `wardrobe/views.py` - analyze_care_label_view added; garment_detail passes explicit analysis context; garment_list annotates has_analysis
- `wardrobe/urls.py` - Added path `<int:pk>/analyze/` as wardrobe:analyze_care_label
- `templates/wardrobe/garment_detail.html` - Full care instructions section replacing placeholder; all 5 states; loading state JS; countdown timer JS
- `templates/base.html` - Daily usage counter inserted in nav between "My Wardrobe" link and email
- `templates/wardrobe/wardrobe_list.html` - Analysis badge on image container (relative positioning added)

## Decisions Made

- **Sentinel message strings:** Django messages values "daily_limit_reached", "budget_guard_tripped", "analysis_failed" are sentinel keys checked by templates. User-facing text is in templates, not views — clean separation of concerns.
- **Explicit analysis context:** `garment_detail` view does `try: analysis = garment.care_analysis except CareAnalysis.DoesNotExist: analysis = None`. Accessing a reverse OneToOne in templates via `{% if garment.care_analysis %}` can raise DoesNotExist rather than being falsy — explicit context is the safe pattern.
- **href="#" for Edit Instructions:** Plan 03-03 creates the edit_instructions URL and view. Using a placeholder avoids creating a fake stub URL route that would be confusing.

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None beyond dependencies (openai and Pillow) not installed in the worktree's venv — installed via pip during verification. Both are already in requirements.txt from prior phases.

## Next Phase Readiness

- Plan 03-03 must replace `href="#"` on "Edit Instructions" button with `{% url 'wardrobe:edit_instructions' garment.pk %}`
- Plan 03-03 must create the edit_instructions URL pattern and view
- The full analysis flow is now end-to-end testable with OPENAI_API_KEY configured

---
*Phase: 03-care-label-analysis-pipeline*
*Completed: 2026-03-29*
