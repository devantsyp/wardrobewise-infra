---
phase: 03-care-label-analysis-pipeline
plan: 01
subsystem: api
tags: [openai, gpt-4o, vision, django, models, migrations, rate-limiting, budget-guard, deduplication]

# Dependency graph
requires:
  - phase: 02-wardrobe-crud-with-s3
    provides: Garment model with care_label_photo ImageField stored in S3

provides:
  - CareAnalysis model with immutable AI fields + user-editable copy fields + image_hash dedup
  - UsageLog model with Decimal cost tracking and compound DB indexes
  - analyze_care_label() service function with full pipeline: budget guard -> rate limit -> image read -> SHA-256 hash -> dedup -> GPT-4o Vision API -> save
  - Three custom exceptions: RateLimitExceeded, BudgetGuardTripped, AnalysisError
  - daily_usage_counter context processor injecting daily count + budget status into wardrobe pages

affects:
  - 03-02 (analysis view will call analyze_care_label and handle all three exceptions)
  - 03-03 (templates will use daily_usage_count, daily_usage_limit, budget_guard_tripped from context processor)
  - all future wardrobe views (context processor active on all wardrobe namespace pages)

# Tech tracking
tech-stack:
  added:
    - openai>=2.30,<3.0 (GPT-4o Vision API client)
  patterns:
    - Lazy OpenAI client instantiation (_get_client()) so module can be imported without OPENAI_API_KEY set
    - Two-table design: CareAnalysis (one-to-one with Garment) + UsageLog (append-only audit trail)
    - SHA-256 image hash for deduplication across garments (same label image reuses AI output)
    - Decimal-only cost arithmetic (never float) for financial precision
    - Context processor gated on resolver_match.app_name to avoid unnecessary DB queries

key-files:
  created:
    - wardrobe/models.py (CareAnalysis + UsageLog models appended)
    - wardrobe/migrations/0003_careanalysis_usagelog.py
    - wardrobe/services/__init__.py
    - wardrobe/services/analysis.py
    - wardrobe/context_processors.py
  modified:
    - requirements.txt (added openai>=2.30,<3.0)
    - laundry_advisor/settings/base.py (registered daily_usage_counter in TEMPLATES context_processors)

key-decisions:
  - "Lazy OpenAI client: _get_client() instead of module-level OpenAI() — allows import without OPENAI_API_KEY (discovered during Task 2 verify)"
  - "DB-backed rate limit via UsageLog count query — in-memory counters reset on Render restart"
  - "Budget guard halts at $9.00 cumulative spend across all users — protects $10 API budget"
  - "image_hash deduplication: same label image across different garments reuses AI output without new API call"
  - "CareAnalysis from_cache flag: distinguishes cached results from fresh API calls for views"

patterns-established:
  - "Service layer in wardrobe/services/ directory — views import from here, not from models directly"
  - "analyze_care_label() returns CareAnalysis instance — caller does not interact with UsageLog"
  - "All three guard checks (budget, rate limit) happen before any I/O (image read, API call)"

# Metrics
duration: 18min
completed: 2026-03-29
---

# Phase 3 Plan 01: Care Label Analysis Backend Summary

**GPT-4o Vision service with SHA-256 dedup, per-user rate limiting (10/day), $9 budget guard, and Decimal cost tracking via CareAnalysis + UsageLog models**

## Performance

- **Duration:** 18 min
- **Started:** 2026-03-29T23:11:54Z
- **Completed:** 2026-03-29T23:30:00Z
- **Tasks:** 3
- **Files modified:** 7

## Accomplishments

- CareAnalysis model (20 fields: immutable AI outputs, user-editable copies, image_hash, from_cache) and UsageLog model (Decimal cost, compound indexes) added to DB via migration 0003
- analyze_care_label() implements full pipeline: budget guard -> rate limit -> image read (FieldFile stream-safe) -> SHA-256 hash -> dedup (same-garment early return + cross-garment copy) -> GPT-4o Vision API -> atomic transaction save
- Context processor daily_usage_counter injects daily_usage_count, daily_usage_limit, budget_guard_tripped into all wardrobe namespace template contexts

## Task Commits

Each task was committed atomically:

1. **Task 1: CareAnalysis and UsageLog models + migration + requirements** - `67091e6` (feat)
2. **Task 2: Analysis service layer (services/analysis.py)** - `7f67ea7` (feat)
3. **Task 3: Context processor + settings registration** - `ca54e24` (feat)

## Files Created/Modified

- `wardrobe/models.py` - Added CareAnalysis (20 fields) and UsageLog (7 fields) below Garment model
- `wardrobe/migrations/0003_careanalysis_usagelog.py` - Migration creating both tables with indexes
- `wardrobe/services/__init__.py` - Empty package marker
- `wardrobe/services/analysis.py` - Full analysis service: constants, 3 exceptions, 8 functions including analyze_care_label()
- `wardrobe/context_processors.py` - daily_usage_counter processor gated on wardrobe app_name
- `requirements.txt` - Added openai>=2.30,<3.0
- `laundry_advisor/settings/base.py` - Registered daily_usage_counter in TEMPLATES context_processors list

## Decisions Made

- **Lazy OpenAI client:** Used `_get_client()` instead of module-level `client = OpenAI()`. Module-level instantiation raises `OpenAIError` at import time when `OPENAI_API_KEY` is not set — blocks Django system checks, test runs, and any import without the env var. Lazy pattern defers the check to first actual API call.
- **DB-backed rate limit:** UsageLog count query per user per day. Chosen over in-memory counter because Render restarts workers, resetting any in-memory state.
- **Decimal cost arithmetic:** All cost fields use `Decimal` throughout — model field `DecimalField`, constants `Decimal('0.0000025')`, arithmetic `Decimal(token_count) * rate`. Never float.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Lazy OpenAI client instantiation**
- **Found during:** Task 2 (Analysis service layer) — verification step
- **Issue:** Plan specified `client = OpenAI()` at module level. When `OPENAI_API_KEY` is not set in the environment, `OpenAI()` raises `openai.OpenAIError` at import time, preventing the module from loading and blocking Django's system check
- **Fix:** Added `_client = None` module variable and `_get_client()` function that initializes the client on first call; replaced direct `client.` usage with `_get_client().`
- **Files modified:** `wardrobe/services/analysis.py`
- **Verification:** `DJANGO_SETTINGS_MODULE=laundry_advisor.settings.dev python -c "... from wardrobe.services.analysis import analyze_care_label ..."` succeeds without OPENAI_API_KEY
- **Committed in:** `7f67ea7` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug)
**Impact on plan:** Essential fix — without it Django's system check (`manage.py check`) would fail in any environment without OPENAI_API_KEY, including CI and production during startup.

## Issues Encountered

None beyond the auto-fixed lazy client issue above.

## User Setup Required

**External services require manual configuration.** The OpenAI API key must be set before analysis features are usable:

1. Get API key from platform.openai.com -> API keys -> Create new secret key
2. Add `OPENAI_API_KEY=sk-...` to local `.env` file for development
3. Add `OPENAI_API_KEY` environment variable in Render Dashboard -> Environment -> Add Environment Variable

Without this key, `analyze_care_label()` will raise `OpenAIError` on first call. All other app functionality (wardrobe CRUD, auth) continues to work without it.

## Next Phase Readiness

- analyze_care_label() is ready to wire to a view — Plan 03-02 creates the analysis view and URL
- Context processor already active; templates in 03-03 can use daily_usage_count, daily_usage_limit, budget_guard_tripped
- Blocker: OPENAI_API_KEY must be configured in Render before end-to-end testing in production

---
*Phase: 03-care-label-analysis-pipeline*
*Completed: 2026-03-29*

## Self-Check: PASSED

All 7 files verified present. All 3 task commits verified in git history.
