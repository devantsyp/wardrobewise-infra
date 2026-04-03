---
phase: 04-laundry-basket
plan: 01
subsystem: api
tags: [django, python, grouping-algorithm, unit-tests, jsonfield, basket]

# Dependency graph
requires:
  - phase: 03-care-label-analysis-pipeline
    provides: CareAnalysis model with washing/drying/bleach/is_delicate fields consumed by grouping algorithm
provides:
  - Pure-Python group_into_loads() grouping service in laundry/services/grouping.py
  - Basket model with JSONField garment_pks and saved_plan storage
  - 25 unit tests covering all grouping edge cases
  - laundry app registered in INSTALLED_APPS with 0001_initial migration applied
affects: [04-laundry-basket-02, plan-api-endpoint, basket-views]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Pure-Python service layer with no ORM calls (testable with plain dicts, no DB setup)
    - Two-stage temperature parse: explicit Celsius regex then keyword fallback to 30/40/60
    - Color classification via ordered keyword list (darks first to catch substrings like 'dark navy')
    - Delicates splitting only when mixed within same (color_group, temp_bucket) — avoids over-splitting all-delicate loads

key-files:
  created:
    - laundry/__init__.py
    - laundry/apps.py
    - laundry/models.py
    - laundry/admin.py
    - laundry/migrations/__init__.py
    - laundry/migrations/0001_initial.py
    - laundry/services/__init__.py
    - laundry/services/grouping.py
    - laundry/tests/__init__.py
    - laundry/tests/test_grouping.py
  modified:
    - laundry_advisor/settings/base.py

key-decisions:
  - "group_into_loads() is pure Python with no ORM calls — view layer assembles garment dicts, service layer handles only algorithm"
  - "Temperature null/unparseable defaults to bucket 30 with display label Coolest wash (not None) to ensure groupability"
  - "Darks keywords checked before generic 'dark' prefix to avoid order-sensitivity issues; longest-specific first"
  - "Delicates separation only when mixed in same (color_group, temp_bucket) — all-delicate groups stay as single load with cycle=delicate"

patterns-established:
  - "Pure service pattern: service functions accept plain dicts, return plain dicts — no ORM, no Django imports inside service module"
  - "Two-stage parse pattern: explicit regex first, keyword fallback second, sentinel default third"

requirements-completed: [BSKT-02, BSKT-03]

# Metrics
duration: 12min
completed: 2026-04-03
---

# Phase 4 Plan 01: Laundry App Scaffold and Grouping Service Summary

**Django laundry app with Basket model (JSONField storage) and group_into_loads() pure-Python algorithm fully covered by 25 passing unit tests**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-04-03T11:30:54Z
- **Completed:** 2026-04-03T11:43:00Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 11

## Accomplishments

- Created laundry Django app with all scaffold files (apps.py, models.py, admin.py, migrations)
- Implemented group_into_loads() with 7-step algorithm: special care routing, color classification, temperature extraction with bucket normalization, delicates splitting, warning extraction, load construction, and sort by garment count descending
- Wrote 25 unit tests (plain dict inputs, no DB required) covering all edge cases specified in plan
- Applied 0001_initial migration; Basket model live in dev database

## Task Commits

Each task was committed atomically:

1. **Task 1: Create laundry app scaffold, Basket model, and group_into_loads() with unit tests** - `ed28615` (feat)

**Plan metadata:** (docs commit follows this SUMMARY)

_Note: TDD task executed as RED (tests written first, import error confirmed) then GREEN (implementation written, all 25 pass)_

## Files Created/Modified

- `laundry/__init__.py` - App package marker
- `laundry/apps.py` - LaundryConfig with name='laundry'
- `laundry/models.py` - Basket model with garment_pks JSONField, saved_plan JSONField, plan_saved_at, last_used_at, created_at
- `laundry/admin.py` - BasketAdmin registered with list_display and readonly_fields
- `laundry/migrations/__init__.py` - Migrations package marker
- `laundry/migrations/0001_initial.py` - Initial migration for Basket model
- `laundry/services/__init__.py` - Services package marker
- `laundry/services/grouping.py` - group_into_loads() algorithm (pure Python, ~200 lines)
- `laundry/tests/__init__.py` - Tests package marker
- `laundry/tests/test_grouping.py` - 25 unit tests in GroupingLogicTest (SimpleTestCase, no DB)
- `laundry_advisor/settings/base.py` - Added 'laundry' to INSTALLED_APPS

## Decisions Made

- Used `SimpleTestCase` (not `TestCase`) for all grouping tests — no database needed since group_into_loads() takes plain dicts
- Temperature bucket rounding thresholds: <=35 -> 30, 36-50 -> 40, >50 -> 60 (matches plan specification exactly)
- Warning scan over combined washing+drying+bleach fields in lowercase — catches warnings regardless of which field they appear in
- Darks keyword list checks multi-word keywords ('dark blue', 'dark grey', etc.) before single-word 'dark' to avoid substring false positives

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

- `openai` package not installed in local virtualenv; Django system check failed on import. Installed via `pip install openai` before tests could run. Not a code deviation — environment setup gap.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- group_into_loads() is fully tested and ready for consumption by plan_api JSON endpoint (Plan 04-02)
- Basket model is migrated and available for view layer CRUD operations
- All 25 unit tests green; zero regressions in wardrobe/accounts apps
- Plan 04-02 can proceed immediately: basket views, templates, URL wiring, and vanilla JS plan renderer

---
*Phase: 04-laundry-basket*
*Completed: 2026-04-03*
