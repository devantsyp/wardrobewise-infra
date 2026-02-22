# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-19)

**Core value:** Decode a confusing care label and tell the user exactly how to wash a specific garment — so they never ruin a piece of clothing again.
**Current focus:** Phase 1 - Scaffolding and Auth

## Current Position

Phase: 1 of 5 (Scaffolding and Auth)
Plan: 1 of 3 in current phase
Status: In progress
Last activity: 2026-02-22 - Completed 01-01-PLAN.md (Django scaffold + Tailwind CSS v4)

Progress: [█░░░░░░░░░] 7% (1/15 plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 1
- Average duration: 8 min
- Total execution time: 8 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-scaffolding-and-auth | 1/3 | 8 min | 8 min |

**Recent Trend:**
- Last 5 plans: 01-01 (8 min)
- Trend: baseline

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- All phases: Synchronous OpenAI calls (no Celery) — reduces infrastructure complexity
- Phase 1: Split settings (base/dev/prod) from day one — prevents DEBUG=True in production
- Phase 2: S3 configured before AI pipeline — Render ephemeral filesystem cannot hold media
- Phase 3: DB-backed rate limit (UsageLog model) — in-memory counters reset on Render restart
- Phase 3: Budget guard halts at $9.00 cumulative spend — protects $10 API budget

**From 01-01 execution:**
- TAILWIND_CLI_SRC_CSS is relative to BASE_DIR (not STATICFILES_DIRS[0]) in django-tailwind-cli 4.5.1 — use `'assets/src/main.css'` not `'src/main.css'`
- CustomUser must be created before first migration — done; cannot be changed without DB reset
- Tailwind CLI binary downloads to `.django_tailwind_cli/` — excluded from git, re-downloaded on fresh clone

### Pending Todos

None.

### Blockers/Concerns

- Phase 3: Verify current GPT-4o model identifier on platform.openai.com before writing service layer (naming conventions change; may be versioned)
- Phase 3: Confirm `response_format={"type": "json_object"}` still supported for Vision inputs (OpenAI iterates on this surface)
- Phase 2: Verify `STORAGES` dict configuration syntax against current django-storages docs (changed in Django 4.2)
- All phases: Verify Django version — 5.2 LTS confirmed as of 2026-02-22

## Session Continuity

Last session: 2026-02-22
Stopped at: 01-01 complete — Django scaffold with Tailwind CSS v4 and CustomUser model
Resume file: .planning/phases/01-scaffolding-and-auth/01-02-PLAN.md
