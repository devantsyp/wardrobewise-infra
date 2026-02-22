---
phase: 01-scaffolding-and-auth
plan: 01
subsystem: infra
tags: [django, tailwind, custom-user-model, sqlite, django-environ, django-tailwind-cli]

# Dependency graph
requires: []
provides:
  - Django 5.2 project with split settings (base/dev/prod)
  - CustomUser model using email as USERNAME_FIELD, no username field
  - Tailwind CSS v4 with 5-family custom color palette compiled and serving
  - Health check endpoint at /healthz/ returning {"status":"ok"}
  - Migrations applied — CustomUser is the active auth model
  - .gitignore, .env.example, requirements.txt with pinned deps
affects:
  - 01-02 (landing page, auth templates use base.html and custom color palette)
  - 01-03 (prod deployment depends on split settings and wsgi/asgi entry points)
  - all-phases (AUTH_USER_MODEL established; cannot change without DB reset)

# Tech tracking
tech-stack:
  added:
    - Django==5.2
    - django-tailwind-cli==4.5.1 (Tailwind CSS v4, no Node.js)
    - django-environ==0.13.0
    - dj-database-url==2.3.0
    - whitenoise==6.11.0
    - gunicorn==22.0.0
    - psycopg2-binary==2.9.11
  patterns:
    - Split settings package (base/dev/prod) — manage.py defaults to dev, wsgi/asgi default to prod
    - AbstractUser with username=None + email as USERNAME_FIELD
    - CustomUserManager extending AuthUserManager using make_password directly
    - TAILWIND_CLI_SRC_CSS relative to BASE_DIR; TAILWIND_CLI_DIST_CSS relative to STATICFILES_DIRS[0]

key-files:
  created:
    - laundry_advisor/settings/base.py
    - laundry_advisor/settings/dev.py
    - laundry_advisor/settings/prod.py
    - accounts/models.py
    - accounts/managers.py
    - accounts/admin.py
    - accounts/migrations/0001_initial.py
    - core/views.py
    - core/urls.py
    - templates/base.html
    - assets/src/main.css
    - assets/css/app.css
    - .gitignore
    - .env.example
    - requirements.txt
  modified:
    - manage.py (settings module changed to .dev)
    - laundry_advisor/wsgi.py (settings module changed to .prod)
    - laundry_advisor/asgi.py (settings module changed to .prod)
    - laundry_advisor/urls.py (added include('core.urls'))

key-decisions:
  - "TAILWIND_CLI_SRC_CSS must be BASE_DIR-relative (not STATICFILES_DIRS-relative) — corrected from plan docs"
  - "CustomUserManager uses make_password from django.contrib.auth.hashers rather than set_password on model instance"
  - "Assets at assets/src/main.css; compiled to assets/css/app.css — source never served directly by WhiteNoise"
  - "django-tailwind-cli auto-downloads binary to .django_tailwind_cli/ — excluded from git via Tailwind CLI binary pattern in .gitignore"

patterns-established:
  - "Pattern: All env reads via django-environ env() with sensible defaults in base.py"
  - "Pattern: AUTH_USER_MODEL set before any migrations — CustomUser is foundational"
  - "Pattern: Custom colors defined as CSS variables in @theme block with --color-*: initial to wipe Tailwind defaults"

# Metrics
duration: 8min
completed: 2026-02-22
---

# Phase 1 Plan 01: Scaffold Django project with Tailwind CSS v4 and email-only custom user model Summary

**Django 5.2 with split settings, AbstractUser email auth (no username), and Tailwind CSS v4 with 5 custom color families compiled from @theme directive**

## Performance

- **Duration:** 8 min
- **Started:** 2026-02-22T21:10:36Z
- **Completed:** 2026-02-22T21:19:13Z
- **Tasks:** 2
- **Files modified:** 22 created, 4 modified

## Accomplishments
- Django 5.2 project scaffolded with split settings package (base/dev/prod) — manage.py uses dev, wsgi/asgi use prod
- CustomUser model with `username = None` and `email` as `USERNAME_FIELD` defined and migrated BEFORE the standard auth tables
- Tailwind CSS v4 integrated via django-tailwind-cli (no Node.js); all 5 custom color families (deep-space, dark-teal, lavender, thistle, lilac-ash) verified in compiled CSS
- Health check at `/healthz/` returns `{"status": "ok"}` HTTP 200; index at `/` returns HTTP 200
- `python manage.py check` passes with zero issues after all setup

## Task Commits

Each task was committed atomically:

1. **Task 1: Initialize Django project with split settings, core app, accounts app, and foundational files** - `ae8831d` (feat)
2. **Task 2: Set up Tailwind CSS v4 with custom color palette, run migrations, and verify the dev server** - `923686d` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified
- `laundry_advisor/settings/base.py` - Shared settings with AUTH_USER_MODEL, Tailwind config, session/login settings
- `laundry_advisor/settings/dev.py` - Development: DEBUG=True, SQLite database
- `laundry_advisor/settings/prod.py` - Production stub: DEBUG=False (completed in 01-03)
- `accounts/models.py` - CustomUser: email as USERNAME_FIELD, username=None
- `accounts/managers.py` - CustomUserManager using make_password for correct password hashing
- `accounts/admin.py` - CustomUserAdmin with email-based fieldsets
- `accounts/migrations/0001_initial.py` - First and only migration — CustomUser created before auth tables
- `core/views.py` - healthz() returns JsonResponse({'status':'ok'}); index() renders core/index.html
- `core/urls.py` - app_name='core'; routes / to index, /healthz/ to healthz
- `templates/base.html` - Skeleton with {% tailwind_css %} and bg-deep-space-50 body class
- `assets/src/main.css` - @import "tailwindcss" + @theme block with all 5 color families (55 color variables + white/black)
- `assets/css/app.css` - Compiled Tailwind output (verified contains all custom color names)
- `.gitignore` - Excludes .env, venv/, .venv/, __pycache__, db.sqlite3, staticfiles/, etc.
- `.env.example` - Template with SECRET_KEY, DJANGO_SETTINGS_MODULE, DEBUG, DATABASE_URL, RENDER_EXTERNAL_HOSTNAME
- `requirements.txt` - Pinned: Django==5.2, gunicorn, whitenoise, dj-database-url, django-tailwind-cli, psycopg2-binary, django-environ

## Decisions Made
- **TAILWIND_CLI_SRC_CSS path:** Plan documentation said this was relative to STATICFILES_DIRS[0], but the library source code (config.py line 510) resolves it relative to BASE_DIR. Corrected setting from `'src/main.css'` to `'assets/src/main.css'`. First build created a spurious `src/main.css` at project root using a minimal auto-generated CSS; removed and rebuilt correctly.
- **CustomUserManager implementation:** Used `make_password()` from `django.contrib.auth.hashers` directly (as in the research Pattern 1) rather than `self.set_password()` on the model. Both are correct, but the research recommended approach was used.
- **Tailwind CLI binary location:** django-tailwind-cli downloads to `.django_tailwind_cli/` at project root; this directory excluded from git (binary is re-downloaded on fresh clone via `tailwind download_cli`).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Corrected TAILWIND_CLI_SRC_CSS path from 'src/main.css' to 'assets/src/main.css'**
- **Found during:** Task 2 (Tailwind build step)
- **Issue:** The plan specified `TAILWIND_CLI_SRC_CSS = "src/main.css"` based on research docs saying the path is relative to STATICFILES_DIRS[0]. The actual django-tailwind-cli 4.5.1 source code (config.py, _resolve_css_paths()) resolves SRC_CSS relative to BASE_DIR, not STATICFILES_DIRS[0]. The first build created a default `src/main.css` at project root with only `@import "tailwindcss"` (missing the custom @theme block), compiled from that instead of our custom CSS.
- **Fix:** Changed setting to `'assets/src/main.css'`; removed spurious `src/` directory at project root; forced rebuild confirmed correct CSS compiled (all 5 color families present in output).
- **Files modified:** `laundry_advisor/settings/base.py`
- **Verification:** `grep -o "deep-space|dark-teal|lavender|thistle|lilac-ash" assets/css/app.css | sort | uniq` showed all 5 families.
- **Committed in:** `923686d` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 - bug in plan's path specification)
**Impact on plan:** Essential fix — without it, the compiled CSS would have been missing all custom colors. No scope creep.

## Issues Encountered
- Apps listed in INSTALLED_APPS before the app directories existed caused `manage.py startapp` to fail. Resolved by creating app directories manually (writing all files directly) rather than using the `startapp` command.

## User Setup Required
None - no external service configuration required for this plan.

## Next Phase Readiness
- Plan 01-02 can use all custom color classes (bg-deep-space-*, text-lavender-*, etc.) in templates
- CustomUser model is immutably established — all future auth work builds on email-based auth
- base.html is minimal (no nav, no flash messages) — Plan 01-02 will add full nav and flash message toasts
- db.sqlite3 exists locally with all migrations applied; prod DB setup deferred to Plan 01-03
- No blockers for Plan 01-02

## Self-Check: PASSED

All key files found on disk. Both task commits (ae8831d, 923686d) verified in git log.

---
*Phase: 01-scaffolding-and-auth*
*Completed: 2026-02-22*
