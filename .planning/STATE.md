# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-02-19)

**Core value:** Decode a confusing care label and tell the user exactly how to wash a specific garment — so they never ruin a piece of clothing again.
**Current focus:** Phase 2 - Wardrobe CRUD with S3

## Current Position

Phase: 2 of 5 (Wardrobe CRUD with S3)
Plan: 1 of 3 in current phase
Status: Plan 02-01 complete — wardrobe data layer, Garment model, S3 storage, GarmentForm ready
Last activity: 2026-03-03 - Plan 02-01 complete; Garment model migrated, S3 storage configured

Progress: [████░░░░░░] 27% (4/15 plans complete)

## Performance Metrics

**Velocity:**
- Total plans completed: 4
- Average duration: ~8 min
- Total execution time: ~47 min

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01-scaffolding-and-auth | 3/3 | ~42 min | ~14 min |
| 02-wardrobe-crud-with-s3 | 1/3 | ~5 min | ~5 min |

**Recent Trend:**
- Last 5 plans: 01-01 (8 min), 01-02 (4 min), 01-03 (~30 min incl. deploy debug), 02-01 (5 min)
- Trend: variable (deploy plans include human verification time)

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

**From 01-02 execution:**
- Color names in templates must match main.css: `deep-space-*` not `deep-space-blue-*` (research docs had wrong name)
- Failed login: return fresh unbound LoginForm() + `login_error` context var — clean separation of auth error from form validation errors
- Django test.Client uses SERVER_NAME='testserver' — not in ALLOWED_HOSTS; use Client(SERVER_NAME='localhost') for shell verification

**From 01-03 execution:**
- prod.py uses STORAGES dict (not deprecated STATICFILES_STORAGE) for WhiteNoise
- TAILWIND_CLI_AUTOMATIC_DOWNLOAD = False in prod — binary installed via build.sh's `tailwind download_cli`
- render.yaml uses `generateValue: true` for SECRET_KEY — Render generates it on first deploy
- build.sh order: pip install -> tailwind download_cli -> tailwind build -> rm -rf assets/src/ -> collectstatic -> migrate
- CRITICAL: assets/src/main.css (Tailwind v4 source, contains `@import "tailwindcss"`) must be deleted before collectstatic — WhiteNoise's CompressedManifestStaticFilesStorage tries to resolve the import as a static file and fails with MissingFileError

**From 02-01 execution:**
- upload_to callables (garment_photo_path, care_label_path) require instance.pk — create view MUST do two-step save: save Garment record first (without files), then assign file fields and save again
- prod.py extends STORAGES dict via `STORAGES["default"] = {...}` — reassigning `STORAGES = {...}` would wipe the WhiteNoise staticfiles entry
- CATEGORY_CHOICES is a module-level list (not class attribute) — plan verify command needs django.setup() to import Garment

### Pending Todos

None.

### Blockers/Concerns

- Phase 3: Verify current GPT-4o model identifier on platform.openai.com before writing service layer (naming conventions change; may be versioned)
- Phase 3: Confirm `response_format={"type": "json_object"}` still supported for Vision inputs (OpenAI iterates on this surface)
- Phase 2: STORAGES dict configuration verified working against django-storages 1.14.6 (concern resolved)
- All phases: Verify Django version — 5.2 LTS confirmed as of 2026-02-22
- Phase 2: AWS S3 env vars (AWS_STORAGE_BUCKET_NAME, AWS_S3_REGION_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) must be configured in Render before production photo uploads work

## Session Continuity

Last session: 2026-03-03
Stopped at: Completed 02-wardrobe-crud-with-s3/02-01-PLAN.md
Resume file: none — ready for Plan 02-02 (wardrobe views)
