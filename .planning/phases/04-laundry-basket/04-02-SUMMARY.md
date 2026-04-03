---
phase: 04-laundry-basket
plan: 02
subsystem: views+templates
tags: [django, python, views, templates, javascript, basket, integration-tests]

# Dependency graph
requires:
  - phase: 04-laundry-basket
    plan: 01
    provides: group_into_loads() grouping service and Basket model
  - phase: 03-care-label-analysis-pipeline
    provides: CareAnalysis model with washing/drying/bleach/is_delicate fields
provides:
  - Full basket page at /basket/ with garment selection grid, plan generation, and basket management
  - REST-style plan API at /basket/api/plan/ returning JSON
  - Basket CRUD endpoints: create, rename, delete, update-selection, save-plan
  - Plan Laundry nav link in base.html
  - 15 integration tests covering basket CRUD, plan API, auth, and user isolation
affects: [user-facing-basket-ui, production-deploy]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Exists() + OuterRef() annotation to filter analyzed-only garments without N+1
    - json_script template tag for XSS-safe JSON injection into inline JS
    - Fire-and-forget selection persistence via fetch() to update-selection endpoint
    - Debounced plan refetch (300ms) when selection changes after first plan generation
    - Max('updated_at') aggregate for stale plan detection comparing to plan_saved_at
    - Stale plan detection: aggregate Max(updated_at) over basket's garment PKs, compare to plan_saved_at

key-files:
  created:
    - laundry/urls.py
    - laundry/views.py
    - laundry/tests/test_views.py
    - templates/laundry/basket.html
  modified:
    - laundry_advisor/urls.py
    - templates/base.html
    - assets/css/app.css
    - .gitignore

# Key decisions
decisions:
  - "basket_view uses Exists() subquery annotation to filter analyzed-only garments — same pattern as wardrobe garment_list (from 03-02)"
  - "json_script Django template tag used for XSS-safe basket.saved_plan and basket.garment_pks injection — avoids |safe filter on user-controlled JSON"
  - ".django_tailwind_cli/ added to .gitignore — binary re-downloaded on fresh clone (from 01-03 decision)"
  - "basket_create and basket_rename redirect via f-string URL with ?basket_id param rather than redirect() with args — simpler than adding named URL parameter"

metrics:
  duration: "6 min"
  completed_date: "2026-04-03"
  tasks_completed: 2
  files_created: 4
  files_modified: 4
---

# Phase 04 Plan 02: Basket Page Views, URLs, Template, and Tests Summary

**One-liner:** Django basket page with 7 URL endpoints, 6 view functions, 15 integration tests, and full interactive template using inline JS for selection persistence, debounced plan fetch, basket CRUD, and modal management.

## What Was Built

### Task 1: URLs, Views, Nav Link, and Integration Tests

- **`laundry/urls.py`** — 7 endpoints with `app_name = 'laundry'`: basket (GET /basket/), plan_api (POST /basket/api/plan/), basket_create (POST /basket/create/), basket_rename (POST /basket/<pk>/rename/), basket_delete (POST /basket/<pk>/delete/), save_plan (POST /basket/save-plan/), update_selection (POST /basket/update-selection/)
- **`laundry/views.py`** — 6 view functions (7 including update_selection): all `@login_required`, plan_api also `@require_POST`, basket_view with Exists() annotation for analyzed-only filtering, stale plan detection via Max('updated_at') aggregate, basket CRUD with user isolation via get_object_or_404(Basket, pk=pk, user=request.user)
- **`laundry_advisor/urls.py`** — Added `path('basket/', include('laundry.urls'))`
- **`templates/base.html`** — Added "Plan Laundry" nav link immediately after "My Wardrobe"
- **`laundry/tests/test_views.py`** — `BasketSelectionTest` (9 tests) and `PlanDisplayTest` (6 tests): 15 total

### Task 2: Basket Page Template

- **`templates/laundry/basket.html`** — 350+ lines extending base.html with:
  - Empty state (no analyzed garments) and first-visit state (no baskets)
  - Basket selector dropdown with switch-on-change
  - Responsive garment selection grid (2/3/4/5 cols) with checkboxes and card click handling
  - Category filter dropdown (client-side hide/show)
  - Select All / Clear All buttons
  - Max-20 inline notice
  - Sticky bottom CTA bar (fixed bottom-0 inset-x-0 z-40) with disabled/enabled state
  - Plan results section with machine-wash load cards (bg-deep-space-700 header) and special care card (bg-amber-500 header)
  - Loading skeleton with animate-pulse during fetch
  - Stale plan notice (server-rendered)
  - New basket modal and Manage Baskets modal (with rename/delete forms)
  - Inline JS: selection state management, debounced plan refetch, save plan with toast, modal handlers, basket selector redirect

## Test Results

- All 40 laundry app tests pass (25 grouping + 15 views)
- `python manage.py tailwind build --force` exits 0

## Commits

| Task | Hash | Message |
|------|------|---------|
| Task 1 | 43c4c13 | feat(04-02): basket URLs, views, nav link, and integration tests |
| Task 2 | 571093e | feat(04-02): basket page template with selection grid, plan results, modals, and inline JS |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing] Added .django_tailwind_cli/ to .gitignore**
- **Found during:** Task 2 (tailwind build downloaded binary to untracked directory)
- **Issue:** `.django_tailwind_cli/` directory appeared as untracked after `tailwind build --force`; STATE.md note from 01-03 confirms "Tailwind CLI binary downloads to `.django_tailwind_cli/` — excluded from git, re-downloaded on fresh clone" but the pattern wasn't in .gitignore
- **Fix:** Added `.django_tailwind_cli/` to .gitignore
- **Files modified:** `.gitignore`
- **Commit:** 571093e

## Known Stubs

None — all views wire real data from the database; plan results are generated live from group_into_loads(); no hardcoded empty values flow to the UI.

## Self-Check: PASSED
