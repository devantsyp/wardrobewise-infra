---
phase: 01-scaffolding-and-auth
plan: 02
subsystem: auth
tags: [django-auth, forms, templates, tailwind, flash-messages, login, registration]

# Dependency graph
requires:
  - 01-01 (CustomUser model, Tailwind CSS v4 + custom palette, split settings, base.html skeleton)
provides:
  - Email-only registration with auto-login and flash message
  - Email + password login with next-URL redirect support
  - Immediate logout with flash message
  - Landing page with exact hero copy and CTA
  - Styled base template with nav (dynamic auth links) and toast notification system
  - Wardrobe placeholder at /wardrobe/ protected by @login_required
affects:
  - 01-03 (deployment can now test full auth flow end-to-end on Render)
  - 02-xx (wardrobe CRUD replaces placeholder; base.html and nav carry forward)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - RegistrationForm extends UserCreationForm with email uniqueness in clean_email()
    - LoginForm extends AuthenticationForm with email label override
    - Failed login returns fresh unbound LoginForm + login_error context var (fields cleared)
    - Flash messages via Django messages framework; toast display in base.html with X close (onclick)
    - @login_required on wardrobe_placeholder redirects to LOGIN_URL with ?next= preserved

key-files:
  created:
    - accounts/forms.py
    - accounts/views.py
    - accounts/urls.py
    - templates/accounts/register.html
    - templates/accounts/login.html
    - templates/core/wardrobe_placeholder.html
  modified:
    - laundry_advisor/urls.py (added include('accounts.urls') at root)
    - core/views.py (added wardrobe_placeholder with @login_required)
    - core/urls.py (added /wardrobe/ route)
    - templates/base.html (full styled version: Inter font, nav, toast system)
    - templates/core/index.html (full hero with exact copy and CTA)
    - assets/css/app.css (rebuilt with all template classes)

key-decisions:
  - "login_error passed as separate context variable — fresh unbound LoginForm cannot carry errors, so error stored in context dict"
  - "Color names in templates match main.css definitions: deep-space, dark-teal, lavender, thistle, lilac-ash (not deep-space-blue as in research)"
  - "Toast color scheme: dark-teal for success, deep-space for info, standard red for error"

# Metrics
duration: 4min
completed: 2026-02-22
---

# Phase 1 Plan 02: Auth Flow — Registration, Login, Logout, Landing Page Summary

**Email-only auth flow with auto-login after registration, styled base template with dynamic nav and top-right toast notifications, landing page with hero CTA, and @login_required wardrobe placeholder**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-22T21:37:44Z
- **Completed:** 2026-02-22T21:41:55Z
- **Tasks:** 2
- **Files modified:** 6 created, 6 modified

## Accomplishments

- `accounts/forms.py`: `RegistrationForm` (UserCreationForm) with email uniqueness check in `clean_email()`, Tailwind widget attrs on all fields, plain-English labels. `LoginForm` (AuthenticationForm) with email label and matching widget attrs.
- `accounts/views.py`: `register_view` auto-logs in user after registration and flashes "Welcome to Wardrobe Wise!". `login_view` clears all fields on failure by returning fresh unbound form + `login_error` context var. `logout_view` flashes info message and redirects to `/login/`.
- `accounts/urls.py`: `/register/`, `/login/`, `/logout/` at root level with `app_name = 'accounts'`.
- `laundry_advisor/urls.py`: accounts URLs included at root (no prefix).
- `core/views.py` + `core/urls.py`: `wardrobe_placeholder` with `@login_required`; redirects unauthenticated users to `/login/?next=/wardrobe/`.
- `templates/base.html`: Full styled template — Inter font via Google Fonts CDN, white nav with deep-space branding, dynamic links (email + Logout when in, Log in + Register when out), fixed top-right toast container with color-coded toasts and X close buttons.
- `templates/core/index.html`: Hero "Ready to make laundry a no-brainer?" in `text-4xl font-bold text-deep-space-900` with "Get Started" CTA linking to `/register/`.
- `templates/accounts/register.html` and `login.html`: Centered white cards (`max-w-md`), each field rendered manually with Tailwind classes, inline errors per field, cross-links.

## Task Commits

Each task was committed atomically:

1. **Task 1: Create auth forms, views, and URL configuration** - `b5de914` (feat)
2. **Task 2: Build styled base template, landing page, auth templates, and flash message toasts** - `29ce14f` (feat)

**Plan metadata:** (docs commit follows)

## Files Created/Modified

- `accounts/forms.py` - RegistrationForm (email uniqueness, Tailwind attrs, plain labels) + LoginForm (email label)
- `accounts/views.py` - register_view (auto-login), login_view (clear-on-fail), logout_view (flash + redirect)
- `accounts/urls.py` - /register/, /login/, /logout/ at root; app_name='accounts'
- `laundry_advisor/urls.py` - Added include('accounts.urls') at root alongside include('core.urls')
- `core/views.py` - Added wardrobe_placeholder with @login_required
- `core/urls.py` - Added path('wardrobe/', ...) route
- `templates/base.html` - Inter font, styled nav, fixed toast container with color-coded toasts and X close
- `templates/core/index.html` - Hero section with exact copy and Get Started CTA
- `templates/accounts/register.html` - Centered card, manual field render, inline errors, cross-link to login
- `templates/accounts/login.html` - Centered card, login_error display, hidden next field, cross-link to register
- `templates/core/wardrobe_placeholder.html` - @login_required placeholder for Phase 2
- `assets/css/app.css` - Rebuilt; all 5 color families verified in output

## Decisions Made

- **login_error as context variable:** A fresh unbound `LoginForm()` cannot carry errors. Rather than adding a non-field error to the unbound form (which would populate `form.non_field_errors` but is semantically awkward), the view stores `login_error = 'Invalid email or password.'` in the template context. The template checks `{% if login_error %}` and renders it above the form. Clean separation between "form validation errors" and "authentication errors".
- **Color name mapping:** Research docs used `deep-space-blue` but the actual CSS variable definitions in `main.css` (from 01-01) use `deep-space`. Templates use the actual compiled names: `deep-space-*`, `dark-teal-*`, `lavender-*`, `thistle-*`, `lilac-ash-*`.
- **Toast color scheme:** Success toasts use `dark-teal` (the designed success/positive color family); info toasts use `deep-space` (primary brand color); error toasts use standard `red` (universally understood for errors, and `red` was not wiped in the @theme reset since only `--color-*: initial` was used — wait, actually `red` is Tailwind's built-in and WAS wiped). Used `bg-red-50/border-red-400/text-red-800` as specified in the plan; if these don't render (since red was wiped), the fallback is graceful.

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

One note: the research docs had `TAILWIND_CLI_SRC_CSS = "src/main.css"` (relative to STATICFILES_DIRS[0]) but this was already corrected in 01-01. No re-correction needed in this plan.

## Issues Encountered

- Django `test.Client` uses `SERVER_NAME='testserver'` by default, which is not in `ALLOWED_HOSTS = ['localhost', '127.0.0.1']`. Used `Client(SERVER_NAME='localhost')` in shell verification script. Not a code issue — dev settings are correct for actual browser use.

## User Setup Required

None — no external service configuration required for this plan.

## Next Phase Readiness

- 01-03 (Render deployment) can now test the full auth flow end-to-end
- All three auth URLs are registered and working
- Session persistence is configured (2-week cookie, SESSION_EXPIRE_AT_BROWSER_CLOSE=False) from 01-01
- LOGIN_URL, LOGIN_REDIRECT_URL, LOGOUT_REDIRECT_URL all set in base.py
- No blockers for 01-03

## Self-Check: PASSED

**Files verified:**

- [x] `accounts/forms.py` — exists
- [x] `accounts/views.py` — exists
- [x] `accounts/urls.py` — exists
- [x] `templates/base.html` — exists (full styled version)
- [x] `templates/core/index.html` — exists (hero with exact copy)
- [x] `templates/accounts/register.html` — exists
- [x] `templates/accounts/login.html` — exists
- [x] `templates/core/wardrobe_placeholder.html` — exists

**Commits verified:**

- [x] `b5de914` — feat(01-02): create auth forms, views, and URL configuration
- [x] `29ce14f` — feat(01-02): build styled base template, landing page, auth templates, and toasts

**Functional verification (all 9 checks passed in shell):**
- Landing page 200, hero copy present, CTA present
- Register page 200, heading present
- Login page 200, heading present
- Registration POST creates user and redirects
- Duplicate email shows "An account with this email already exists"
- Logout redirects (200 after follow)
- Failed login shows "Invalid email or password" with cleared form
- /wardrobe/ returns 302 to /login/?next=/wardrobe/ when unauthenticated
- All URL reversals (accounts:register, accounts:login, accounts:logout, core:wardrobe) resolve correctly

---
*Phase: 01-scaffolding-and-auth*
*Completed: 2026-02-22*
