---
status: resolved
trigger: "daily-analysis-reset-bug"
created: 2026-04-01T00:00:00Z
updated: 2026-04-01T00:05:00Z
---

## Current Focus

hypothesis: CONFIRMED — Frontend countdown targets local browser midnight; backend resets at UTC midnight. For users west of UTC, local midnight arrives before UTC midnight, so the countdown expires but the backend still considers it the same day.
test: Read full countdown JS, backend _daily_count query, and Django settings.
expecting: Fix the JS to compute ms until UTC midnight instead of local midnight; add auto-reload when countdown hits zero.
next_action: Fix getMsUntilMidnight() in garment_detail.html to target UTC midnight and add window.location.reload() when countdown reaches 0.

## Symptoms

expected: At midnight UTC, the daily analysis usage resets. Counter shows 0/10 used for the new day. A new 24h countdown begins after reset is applied.
actual: Countdown timer resets at midnight and starts counting down for the new day, but the analysis usage counter still shows 10/10 used. User cannot run new analyses even though it's a new day.
errors: No error messages — the UI appears to update (new countdown appears) but the backend rate limit is not refreshed.
reproduction: Use all 10 daily analyses. Wait for midnight. Observe that the countdown resets but the usage counter does not. Attempting to run analysis still fails with rate limit error.
started: Likely never worked correctly since rate limit logic was implemented in Phase 03.

## Eliminated

- hypothesis: Backend _daily_count uses wrong date (naive datetime or wrong timezone)
  evidence: _daily_count uses `created_at__date=timezone.now().date()` with USE_TZ=True and TIME_ZONE='UTC'. Django generates `django_datetime_cast_date(created_at, UTC, UTC)` SQL — correct UTC date comparison.
  timestamp: 2026-04-01T00:04:00Z

- hypothesis: Django __date lookup silently uses server-local time instead of UTC
  evidence: Inspected generated SQL — `django_datetime_cast_date("wardrobe_usagelog"."created_at", UTC, UTC)` confirms it casts to UTC correctly.
  timestamp: 2026-04-01T00:04:00Z

## Evidence

- timestamp: 2026-04-01T00:02:00Z
  checked: wardrobe/services/analysis.py _daily_count()
  found: Uses `created_at__date=timezone.now().date()` — correct UTC date. USE_TZ=True and TIME_ZONE='UTC'.
  implication: Backend rate limit check is timezone-correct.

- timestamp: 2026-04-01T00:03:00Z
  checked: templates/wardrobe/garment_detail.html — JS countdown (lines 247-268)
  found: getMsUntilMidnight() uses `new Date()` + `setHours(24, 0, 0, 0)` = local browser midnight, not UTC midnight.
  implication: For users in timezones west of UTC (e.g. UTC-5), local midnight arrives 5 hours before UTC midnight. Countdown hits 0, user reloads page, backend still treats it as same UTC day — rate limit still blocked.

- timestamp: 2026-04-01T00:03:30Z
  checked: garment_detail.html countdown — does it trigger a page reload at 0?
  found: No — it calls setTimeout(tick, 1000) indefinitely. At 0 it just keeps showing "0h 0m 0s". No page reload.
  implication: Even if the timezones matched, the user would have to manually reload the page. Without auto-reload, the "new countdown" the symptoms describe is just the timer ticking again after local midnight.

- timestamp: 2026-04-01T00:04:00Z
  checked: Django settings — USE_TZ, TIME_ZONE
  found: USE_TZ=True, TIME_ZONE='UTC'
  implication: Server is fully UTC. Backend reset happens at UTC midnight. Frontend must target UTC midnight too.

## Resolution

root_cause: Frontend countdown JS computes time until local browser midnight (setHours(24,0,0,0)) rather than UTC midnight. Since the backend resets at UTC midnight, users in timezones west of UTC see the countdown expire before the backend has actually reset. Additionally, no auto-reload is triggered when the countdown reaches zero, so even if the user is in UTC, they must manually reload to see the refreshed counter.
fix: Replace getMsUntilMidnight() to compute milliseconds until the next UTC midnight using UTC date arithmetic. Add auto-reload via window.location.reload() when the countdown reaches 0.
verification: Simulated getMsUntilUtcMidnight() across UTC, UTC-5 (EST), UTC+5 scenarios in Node.js. UTC midnight is correctly computed using Date.UTC with getUTCFullYear/Month/Date+1. Auto-reload triggers on ms <= 0 so page refreshes at the exact moment the backend date rolls over. Confirmed the old bug: UTC+5 user at local midnight (19:00 UTC) would have gotten 0ms with old code but backend still needed 5 more hours.
files_changed:
  - templates/wardrobe/garment_detail.html
