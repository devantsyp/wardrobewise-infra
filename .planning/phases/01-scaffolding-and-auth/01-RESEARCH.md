# Phase 1: Scaffolding and Auth - Research

**Researched:** 2026-02-21
**Domain:** Django 5.2 scaffolding, email-only auth, Tailwind CSS v4, Render deployment
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Auth flow:**
- Registration: email + password only (no username)
- Confirm password field on registration form
- Login identifier: email only
- Separate pages for /register and /login with cross-links ("Don't have an account? Register" / "Already have an account? Log in")
- Auto-login after successful registration, redirect to wardrobe page (placeholder until Phase 2)
- Post-login redirect: wardrobe page
- Post-logout redirect: login page
- Immediate logout on click (no confirmation page)
- Always stay logged in — no "Remember me" checkbox, session persists until explicit logout
- Unauthenticated users accessing protected pages: redirect to login with return-to-original-page after login
- Unique emails enforced; explicit error: "An account with this email already exists"
- Django default password validators (length, common passwords, numeric-only, similarity)
- No forgot password flow — not needed for v1
- Dynamic nav links: Login/Register when logged out, user email + Logout when logged in
- Success flash messages after login, registration, and logout (Django messages framework)

**Login error handling:**
- Generic "Invalid email or password" on failed login (no enumeration of which field is wrong)
- Form clears all fields (including email) on failed submit
- No password show/hide toggle
- No button loading/disabled state on submit

**CSS framework & visual style:**
- Tailwind CSS v4 (latest)
- Bold & modern visual vibe — strong colors, sharp contrasts, confident feel
- Custom color palette with 5 families:
  - Dark Teal: #e9fafb → #051d1f (50–950)
  - Deep Space Blue: #e9f6fb → #05161f (50–950) — PRIMARY brand color
  - Lilac Ash: #f2f1f3 → #121013 (50–950)
  - Thistle: #f3f0f4 → #130f15 (50–950)
  - Lavender: #edecf8 → #0b091b (50–950)
- Color roles: Deep Space Blue = primary (buttons, links, nav accents); Lavender = hover/focus states; Dark Teal = success/positive; Thistle & Lilac Ash = muted/secondary text

**Base template & nav:**
- Top horizontal nav bar with light/white background and colored text/accents
- App name "Wardrobe Wise" as styled text (no icon/logo)
- Desktop-first layout (mobile responsiveness deferred)
- Page background: very light tint (one of the 50-shade palette colors)

**Landing page:**
- Hero section with CTA for logged-out users
- Hero copy: "Ready to make laundry a no-brainer?"
- No sub-heading — just hero copy then CTA button
- CTA button text: "Get Started" (links to register page)

**Error & validation UX:**
- Form validation on submit only (server-side, no JS validation)
- Inline errors below each field (red text, standard red color)
- Flash messages as top-right toast notifications with manual close (X button)
- User-friendly error message rewrites (plain English, not Django's raw defaults)
- Errors only — no green/success state on valid fields
- Default Django 404 and 500 error pages (custom pages deferred)
- No button loading states — standard form submission

### Claude's Discretion

- Exact Tailwind v4 setup method for Django (CDN vs build tool)
- Which palette 50-shade to use for page background tint
- Typography choices (font family, sizes, weights)
- Spacing and layout proportions
- Flash message toast animation/styling details
- Health check endpoint implementation
- Split settings structure (base/dev/prod)
- Render deployment configuration details

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope
</user_constraints>

---

## Summary

Phase 1 delivers a working Django 5.2 application with email-only authentication, deployed to Render.com, styled with Tailwind CSS v4. The core technical challenge is that Django's built-in User model uses a username field — the project requires a custom user model with `username = None` and `email` as `USERNAME_FIELD` before any migrations are run. This must happen first; retrofitting a custom user model after initial migrations is extremely painful and requires resetting the database.

Tailwind CSS v4 is a significant departure from v3: configuration is now CSS-first using `@theme` directives instead of `tailwind.config.js`, and custom color palettes are defined as CSS variables (`--color-*`). The recommended integration method for Django is `django-tailwind-cli` (v4.5.1), which downloads the standalone Tailwind CLI binary with no Node.js dependency. The source CSS file containing `@import "tailwindcss"` and `@theme` blocks must not be in any `STATICFILES_DIRS` directory — it lives in a separate source location and the compiled output goes into the static directory.

Render deployment is well-documented and straightforward for Django: `gunicorn` serves the app, `whitenoise` (middleware + Django 4.2+ `STORAGES` dict) serves static files, `dj-database-url` parses the `DATABASE_URL` env var for PostgreSQL, and a `build.sh` script runs `python manage.py tailwind build && python manage.py collectstatic --no-input && python manage.py migrate` in the correct order. The `RENDER` environment variable is auto-set by Render and used to toggle `DEBUG = False` in production settings.

**Primary recommendation:** Create the custom user model in an `accounts` app before running any migrations; use `django-tailwind-cli` for zero-Node.js Tailwind v4 integration; deploy with `render.yaml` Blueprint for reproducible infrastructure.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 5.2 (LTS) | Web framework | Latest LTS, active security support through April 2028, Python 3.10–3.14 support |
| gunicorn | latest stable | WSGI production server | Render's documented standard; simple, battle-tested |
| whitenoise | 6.11.0 | Static file serving in production | Eliminates need for separate CDN/nginx for static files; Render's documented approach |
| dj-database-url | latest stable | DATABASE_URL env var → Django DATABASES dict | Render passes connection as DATABASE_URL; this library parses it |
| django-tailwind-cli | 4.5.1 | Tailwind CSS v4 integration, no Node.js | Zero Node.js; downloads standalone Tailwind binary; v4.5.1 released 2025-12-29 |
| psycopg2-binary | latest stable | PostgreSQL driver | Required for Render PostgreSQL; binary wheel avoids compilation |
| python-dotenv or django-environ | latest stable | .env file loading in development | Industry standard; keeps secrets out of settings.py |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| django-environ | latest stable | .env parsing with type coercion | Preferred over plain python-dotenv; handles booleans, lists, URLs natively |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| django-tailwind-cli | Node.js + npm + Tailwind CLI | Node.js adds toolchain complexity; zero value for this project |
| django-tailwind-cli | Tailwind CDN (Play CDN) | CDN doesn't support custom @theme colors or production optimization; not suitable |
| AbstractUser (username=None) | AbstractBaseUser | AbstractBaseUser requires reimplementing all auth methods manually; AbstractUser with `username=None` keeps Django's permission system, admin integration, and password validators working out of the box |
| django-environ | python-dotenv | python-dotenv only handles strings; django-environ parses booleans, integers, and DATABASE_URL format natively |
| whitenoise CompressedManifestStaticFilesStorage | S3 for static files | S3 for static files is Phase 2+; whitenoise is sufficient for Phase 1 |

**Installation:**
```bash
pip install django==5.2 gunicorn whitenoise[brotli] dj-database-url psycopg2-binary django-environ django-tailwind-cli
pip freeze > requirements.txt
```

---

## Architecture Patterns

### Recommended Project Structure

```
laundry_advisor/          # Django project config package (settings, root urls, wsgi)
├── settings/
│   ├── __init__.py       # Empty or imports base
│   ├── base.py           # Shared settings (INSTALLED_APPS, AUTH_USER_MODEL, etc.)
│   ├── dev.py            # DEBUG=True, sqlite or local postgres, dev-only apps
│   └── prod.py           # DEBUG=False, whitenoise storage, secure cookies
├── urls.py               # Root URL config
└── wsgi.py               # WSGI entry point

accounts/                 # Custom user model + auth views
├── migrations/
├── models.py             # CustomUser (AbstractUser, username=None, email=USERNAME_FIELD)
├── managers.py           # CustomUserManager
├── forms.py              # RegistrationForm, LoginForm
├── views.py              # register_view, login_view, logout_view
├── urls.py               # /register, /login, /logout
└── admin.py              # CustomUserAdmin

core/                     # Landing page, health check
├── views.py              # index_view, healthz_view
└── urls.py               # /, /healthz/

templates/                # Project-wide templates
├── base.html             # Nav, flash messages, {% tailwind_css %}
├── core/
│   └── index.html        # Landing page hero
└── accounts/
    ├── register.html
    └── login.html

assets/                   # STATICFILES_DIRS entry for django-tailwind-cli
└── src/
    └── main.css          # @import "tailwindcss"; @theme { ... }
```

**Settings selection:** Use `DJANGO_SETTINGS_MODULE` env var. In `.env`: `DJANGO_SETTINGS_MODULE=laundry_advisor.settings.dev`. In Render env vars: `DJANGO_SETTINGS_MODULE=laundry_advisor.settings.prod`.

### Pattern 1: Custom User Model (Do This Before First Migration)

**What:** Subclass `AbstractUser`, set `username = None`, set `USERNAME_FIELD = 'email'`, use a custom manager that drops the username parameter.

**When to use:** Always — for any new Django project. This cannot be changed after the first migration without a database reset.

**Example:**
```python
# accounts/managers.py
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import UserManager as AuthUserManager

class CustomUserManager(AuthUserManager):
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self._create_user(email, password, **extra_fields)
```

```python
# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager

class CustomUser(AbstractUser):
    username = None
    email = models.EmailField(_("email address"), unique=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return self.email
```

```python
# settings/base.py
AUTH_USER_MODEL = "accounts.CustomUser"
```

### Pattern 2: Email Authentication with Custom Forms

**What:** Django's built-in `AuthenticationForm` references `username`; override it to present an `email` field. Because `USERNAME_FIELD = 'email'`, Django's `authenticate()` already looks up by email — the custom form just renames the label.

**Example:**
```python
# accounts/forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("email", "password1", "password2")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={"autofocus": True})
    )
```

**Registration view (auto-login after success):**
```python
# accounts/views.py
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.shortcuts import render, redirect
from .forms import RegistrationForm, LoginForm

def register_view(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Welcome to Wardrobe Wise!")
            return redirect("wardrobe:index")  # placeholder in Phase 1
        # Form is returned with errors; fields cleared via empty POST re-render
    else:
        form = RegistrationForm()
    return render(request, "accounts/register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, "Logged in successfully.")
            next_url = request.GET.get("next") or request.POST.get("next")
            return redirect(next_url or "wardrobe:index")
        # On failure, LoginForm automatically produces generic error
        # Do NOT re-populate email field — return empty form for security
        form = LoginForm()  # Clear all fields on failed login
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form, "next": request.GET.get("next", "")})

def logout_view(request):
    logout(request)
    messages.success(request, "You've been logged out.")
    return redirect("accounts:login")
```

**Note on form clearing:** The user decision is that all fields clear on failed login. Returning a fresh `LoginForm()` after a failed POST achieves this. The generic error ("Invalid email or password") must be added manually since the cleared form won't carry the AuthenticationForm's `__all__` error.

### Pattern 3: Tailwind CSS v4 with django-tailwind-cli

**What:** Install `django-tailwind-cli`, add to `INSTALLED_APPS`, set `STATICFILES_DIRS`, create a source CSS file with `@import "tailwindcss"` and `@theme` blocks, use `{% tailwind_css %}` template tag.

**Source CSS file** (`assets/src/main.css`):
```css
@import "tailwindcss";

@theme {
  /* Wipe defaults, use only custom palette */
  --color-*: initial;

  /* Deep Space Blue (PRIMARY brand color) */
  --color-deep-space-blue-50: #e9f6fb;
  --color-deep-space-blue-100: #c8e8f5;
  --color-deep-space-blue-200: #a0d4ec;
  --color-deep-space-blue-300: #72bce0;
  --color-deep-space-blue-400: #4aa1d1;
  --color-deep-space-blue-500: #2b83bc;
  --color-deep-space-blue-600: #1f6696;
  --color-deep-space-blue-700: #174d74;
  --color-deep-space-blue-800: #0f3450;
  --color-deep-space-blue-900: #081e30;
  --color-deep-space-blue-950: #05161f;

  /* Dark Teal (success/positive) */
  --color-dark-teal-50: #e9fafb;
  --color-dark-teal-100: #c4f1f4;
  --color-dark-teal-200: #96e4e9;
  --color-dark-teal-300: #5dd1da;
  --color-dark-teal-400: #2db8c5;
  --color-dark-teal-500: #1c9aa8;
  --color-dark-teal-600: #147a86;
  --color-dark-teal-700: #0f5d66;
  --color-dark-teal-800: #093f46;
  --color-dark-teal-900: #052829;
  --color-dark-teal-950: #051d1f;

  /* Lavender (hover/focus states) */
  --color-lavender-50: #edecf8;
  --color-lavender-100: #d6d4f0;
  --color-lavender-200: #b8b5e4;
  --color-lavender-300: #9490d5;
  --color-lavender-400: #736ec3;
  --color-lavender-500: #5752ae;
  --color-lavender-600: #433f8a;
  --color-lavender-700: #322f68;
  --color-lavender-800: #221f46;
  --color-lavender-900: #141228;
  --color-lavender-950: #0b091b;

  /* Thistle (muted/secondary text) */
  --color-thistle-50: #f3f0f4;
  --color-thistle-100: #e3dde5;
  --color-thistle-200: #c9c1cc;
  --color-thistle-300: #ab9fb0;
  --color-thistle-400: #8e7e93;
  --color-thistle-500: #736176;
  --color-thistle-600: #594a5b;
  --color-thistle-700: #413541;
  --color-thistle-800: #2a222b;
  --color-thistle-900: #1c151d;
  --color-thistle-950: #130f15;

  /* Lilac Ash (muted/secondary text) */
  --color-lilac-ash-50: #f2f1f3;
  --color-lilac-ash-100: #e0dde2;
  --color-lilac-ash-200: #c4c0c8;
  --color-lilac-ash-300: #a49fa9;
  --color-lilac-ash-400: #857f8a;
  --color-lilac-ash-500: #68626d;
  --color-lilac-ash-600: #504b54;
  --color-lilac-ash-700: #3a363d;
  --color-lilac-ash-800: #252228;
  --color-lilac-ash-900: #181619;
  --color-lilac-ash-950: #121013;

  /* Keep white and black available */
  --color-white: #ffffff;
  --color-black: #000000;
}
```

**Settings:**
```python
# settings/base.py
INSTALLED_APPS = [
    # ...
    "django_tailwind_cli",
]

STATICFILES_DIRS = [BASE_DIR / "assets"]

# Pin version to avoid unexpected upgrades
TAILWIND_CLI_VERSION = "4.1.3"
# Source CSS is in assets/src/main.css (under STATICFILES_DIRS root)
TAILWIND_CLI_SRC_CSS = "src/main.css"
# Output is compiled to assets/css/app.css
TAILWIND_CLI_DIST_CSS = "css/app.css"
```

**Base template:**
```html
{% load tailwind_cli %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wardrobe Wise</title>
    {% tailwind_css %}
</head>
```

**Development command:**
```bash
python manage.py tailwind runserver  # watch + runserver in one command
```

**Production build command (in build.sh):**
```bash
python manage.py tailwind build
python manage.py collectstatic --no-input
python manage.py migrate
```

### Pattern 4: Session Persistence (Always Stay Logged In)

**What:** The default Django session behavior is what we want. `SESSION_EXPIRE_AT_BROWSER_CLOSE` defaults to `False`, meaning sessions persist for `SESSION_COOKIE_AGE` (default: 2 weeks = 1209600 seconds). No additional configuration needed.

**Settings (explicit for clarity):**
```python
# settings/base.py
SESSION_EXPIRE_AT_BROWSER_CLOSE = False   # default; session persists across browser close
SESSION_COOKIE_AGE = 1209600              # 2 weeks in seconds (default)
```

### Pattern 5: Login-Required Redirect with next Parameter

**What:** `@login_required` automatically appends `?next=/original/path/` to the login URL. The login template must include `<input type="hidden" name="next" value="{{ next }}">` and the login view must read `next` and redirect there after successful login.

**Settings:**
```python
# settings/base.py
LOGIN_URL = "/login/"
LOGIN_REDIRECT_URL = "/wardrobe/"   # Phase 1 placeholder; updated to real wardrobe URL in Phase 2
LOGOUT_REDIRECT_URL = "/login/"
```

### Pattern 6: Render Deployment

**render.yaml:**
```yaml
services:
  - type: web
    name: wardrobe-wise
    runtime: python
    buildCommand: "./build.sh"
    startCommand: "gunicorn laundry_advisor.wsgi:application"
    healthCheckPath: /healthz/
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: laundry_advisor.settings.prod
      - key: SECRET_KEY
        generateValue: true
      - key: DATABASE_URL
        fromDatabase:
          name: wardrobe-wise-db
          property: connectionString
      - key: WEB_CONCURRENCY
        value: 4
      - key: PYTHON_VERSION
        value: 3.13.5

databases:
  - name: wardrobe-wise-db
    plan: free
    databaseName: wardrobe-wise
```

**build.sh:**
```bash
#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt
python manage.py tailwind build
python manage.py collectstatic --no-input
python manage.py migrate
```

**Python version:** Set via `PYTHON_VERSION` env var in render.yaml or via `.python-version` file in repo root. Render auto-sets `RENDER=True` on all services — use this to toggle `DEBUG`.

**prod.py settings key settings:**
```python
# settings/prod.py
from .base import *
import os

DEBUG = False
SECRET_KEY = os.environ["SECRET_KEY"]
ALLOWED_HOSTS = [os.environ.get("RENDER_EXTERNAL_HOSTNAME", "")]

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ["DATABASE_URL"],
        conn_max_age=600
    )
}

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

STATIC_ROOT = BASE_DIR / "staticfiles"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # ... rest of middleware
]

# Disable Tailwind CLI auto-download on Render (binary not in PATH)
TAILWIND_CLI_AUTOMATIC_DOWNLOAD = False
```

### Pattern 7: Flash Message Toasts (Pure CSS, No JS Library)

**What:** Django messages framework + pure CSS toast positioned top-right. Manual close via HTML checkbox hack or minimal inline JS. No external library required.

**Base template snippet:**
```html
{% if messages %}
<div id="toast-container" class="fixed top-4 right-4 z-50 flex flex-col gap-2">
  {% for message in messages %}
  <div class="toast-item flex items-center gap-3 px-4 py-3 rounded shadow-lg
              {% if message.tags == 'success' %}bg-dark-teal-500 text-white
              {% elif message.tags == 'error' %}bg-red-600 text-white
              {% else %}bg-deep-space-blue-700 text-white{% endif %}">
    <span>{{ message }}</span>
    <button onclick="this.parentElement.remove()"
            class="ml-auto text-white/70 hover:text-white text-xl leading-none">&times;</button>
  </div>
  {% endfor %}
</div>
{% endif %}
```

### Anti-Patterns to Avoid

- **Running `migrate` before defining `AUTH_USER_MODEL`:** Creates Django's default User table; changing it later requires database reset and data migration.
- **Storing the Tailwind source CSS in STATICFILES_DIRS:** WhiteNoise processes all files in `STATICFILES_DIRS` and will stumble on `@import "tailwindcss"` directives. The source CSS must live outside static directories (the compiled output goes in, not the source).
- **Using `AbstractBaseUser` instead of `AbstractUser` with `username=None`:** AbstractBaseUser requires reimplementing `has_perm`, `has_module_perms`, `is_staff`, `is_active`, password validation integration, and Django admin compatibility. AbstractUser with `username=None` keeps all of this working.
- **Hardcoding `SECRET_KEY` in production settings:** Must come from environment variable; Render can auto-generate with `generateValue: true`.
- **Using `STATICFILES_STORAGE` string instead of `STORAGES` dict:** Django 4.2+ uses the `STORAGES` dict; the old `STATICFILES_STORAGE` string is deprecated.
- **Running collectstatic before tailwind build:** WhiteNoise's manifest will include an outdated or missing `app.css`; `tailwind build` must run first.
- **Forgetting `{% csrf_token %}` in login/register forms:** POST views will return 403 Forbidden.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Password hashing | Custom hash function | Django's built-in `set_password()` / `check_password()` | PBKDF2-SHA256 with salt; timing-attack resistant |
| Password strength validation | Custom regex validators | Django's `AUTH_PASSWORD_VALIDATORS` (default set) | Handles length, common passwords, numeric-only, similarity checks |
| Session management | Custom session tokens | Django sessions framework (`django.contrib.sessions`) | Handles cookie security, CSRF, session rotation |
| Login rate limiting | Custom attempt counter | Not needed in Phase 1; flag for v2 | Adds complexity; generic error message already prevents enumeration |
| Static file serving in production | Nginx/CDN setup | WhiteNoise | Eliminates separate server; Render-compatible; handles compression and content hashing |
| Database URL parsing | Custom DSN parser | `dj-database-url` | Parses all PostgreSQL URL variants; Render's standard |
| Email normalization | Lowercase email on save | `BaseUserManager.normalize_email()` (called in manager) | Normalizes domain portion; handles Unicode edge cases |

**Key insight:** Django's auth system has been hardened against security vulnerabilities for 15+ years. Every custom reimplementation introduces risk. Use the built-in primitives and only override where necessary.

---

## Common Pitfalls

### Pitfall 1: Custom User Model After Initial Migration

**What goes wrong:** Developer runs `python manage.py migrate` before creating the custom user model. Django creates the default `auth_user` table. Later, setting `AUTH_USER_MODEL` after the fact requires complex data migrations or a full database wipe.

**Why it happens:** Scaffolding tutorial installs Django and runs `migrate` immediately as a "sanity check" before writing any code.

**How to avoid:** The order of operations in `01-01` plan must be: (1) create `accounts` app, (2) define `CustomUser` model, (3) set `AUTH_USER_MODEL = 'accounts.CustomUser'` in settings, (4) run `python manage.py makemigrations accounts`, (5) run `python manage.py migrate`. Never run `migrate` before step 3.

**Warning signs:** `django.db.models.signals.pre_migrate` runs and creates `auth_user` table.

### Pitfall 2: Tailwind Source CSS in STATICFILES_DIRS

**What goes wrong:** Placing `main.css` (with `@import "tailwindcss"`) inside a `STATICFILES_DIRS` directory. WhiteNoise's `CompressedManifestStaticFilesStorage` processes all files during `collectstatic` and hits the `@import "tailwindcss"` directive it cannot resolve. Deployment fails.

**Why it happens:** Intuition says CSS belongs in the static directory. But the source CSS is a build input, not a static asset.

**How to avoid:** Keep source CSS in a directory that is inside `STATICFILES_DIRS` but not the source itself — or better, keep source at `assets/src/main.css` and configure `TAILWIND_CLI_SRC_CSS = "src/main.css"` with `TAILWIND_CLI_DIST_CSS = "css/app.css"`. The compiled output (`assets/css/app.css`) is what WhiteNoise serves; the source is never served directly.

**Alternative:** Set `WHITENOISE_MANIFEST_STRICT = False` to suppress the error (hides the problem rather than fixing it).

### Pitfall 3: Form Clears All Fields on Failed Login (Requires Deliberate Code)

**What goes wrong:** Standard form pattern re-renders the bound form on failure, which repopulates the email field. The user decision is that ALL fields clear on failed login.

**Why it happens:** The default Django pattern returns `form` with errors, which includes the submitted email value.

**How to avoid:** After a failed login POST, instantiate a fresh `LoginForm()` (unbound) and add a manual error message. Do not return the bound form.

```python
def login_view(request):
    if request.method == "POST":
        bound_form = LoginForm(request, data=request.POST)
        if bound_form.is_valid():
            login(request, bound_form.get_user())
            messages.success(request, "Logged in successfully.")
            return redirect(request.POST.get("next") or "wardrobe:index")
        # Clear all fields — return fresh empty form
        form = LoginForm()
        form.add_error(None, "Invalid email or password.")
    else:
        form = LoginForm()
    return render(request, "accounts/login.html", {"form": form, "next": request.GET.get("next", "")})
```

### Pitfall 4: TAILWIND_CLI_AUTOMATIC_DOWNLOAD on Render

**What goes wrong:** By default, `django-tailwind-cli` downloads the Tailwind binary at runtime if not found. On Render, the binary from `build.sh` may not persist to the runtime container, or the download attempt may fail without `TAILWIND_CLI_PATH` set.

**Why it happens:** The Render build environment and runtime environment may be different containers.

**How to avoid:** In `prod.py`, set `TAILWIND_CLI_AUTOMATIC_DOWNLOAD = False`. The `build.sh` script runs `python manage.py tailwind build` which downloads and runs the CLI during the build phase — the compiled `app.css` is what matters at runtime, not the CLI binary itself.

### Pitfall 5: `ALLOWED_HOSTS` Empty in Production

**What goes wrong:** Django returns 400 Bad Request for all requests in production if `ALLOWED_HOSTS` doesn't include the Render external hostname.

**Why it happens:** Forgetting to configure `ALLOWED_HOSTS` in prod settings, or misconfiguring it.

**How to avoid:** Render auto-sets `RENDER_EXTERNAL_HOSTNAME` env var. Read it in `prod.py`:
```python
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
ALLOWED_HOSTS = [RENDER_EXTERNAL_HOSTNAME] if RENDER_EXTERNAL_HOSTNAME else []
```

### Pitfall 6: WhiteNoise `STORAGES` vs `STATICFILES_STORAGE`

**What goes wrong:** Using the old `STATICFILES_STORAGE = "whitenoise.storage...."` string format. Django 4.2+ uses the `STORAGES` dict. Both may work in Django 5.2 (backwards-compat), but the dict form is the correct approach and avoids deprecation warnings.

**How to avoid:**
```python
# Correct for Django 4.2+
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}
```

### Pitfall 7: Password Validator Error Messages Are Ugly

**What goes wrong:** Django's default password validators produce messages like "This password is too short. It must contain at least 8 characters." — acceptable but slightly technical. The user wants "plain English" rewrites.

**Why it happens:** Django's built-in error strings are functional but not brand-friendly.

**How to avoid:** Subclass each validator and override the `get_help_text()` and error messages, or wrap form errors in the template with friendlier copy. The simplest approach for Phase 1 is to override form error display in the template rather than subclassing all four validators.

---

## Code Examples

Verified patterns from official sources:

### Health Check Endpoint (Claude's Discretion: Simple View)

```python
# core/views.py
from django.http import HttpResponse

def healthz(request):
    return HttpResponse("OK", content_type="text/plain", status=200)
```

```python
# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("healthz/", views.healthz, name="healthz"),
]
```

No `@login_required` — the health check must be publicly accessible.

### Unique Email Validation in RegistrationForm

```python
# accounts/forms.py
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django import forms

User = get_user_model()

class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("email", "password1", "password2")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email
```

### django-environ Settings Loading

```python
# settings/base.py
import environ

env = environ.Env(
    DEBUG=(bool, False)
)

# Read .env file in development (doesn't fail if file missing)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
```

### Admin Registration for CustomUser

```python
# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as AuthUserAdmin
from django.utils.translation import gettext_lazy as _
from .forms import RegistrationForm
from .models import CustomUser

class CustomUserAdmin(AuthUserAdmin):
    add_form = RegistrationForm
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),
    )
    list_display = ("email", "is_staff", "is_active")
    search_fields = ("email",)
    ordering = ("email",)

admin.site.register(CustomUser, CustomUserAdmin)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `tailwind.config.js` for custom colors | `@theme` directive in CSS | Tailwind v4 (2025) | No JS config file; all theme in CSS |
| `STATICFILES_STORAGE` string | `STORAGES` dict | Django 4.2 (2023) | Old form deprecated |
| `AbstractBaseUser` for custom auth | `AbstractUser` with `username=None` | Community shift ~2022 | Less boilerplate; keeps Django perms intact |
| `django-tailwind` (timonweb) | `django-tailwind-cli` (django-commons) | 2024 | Official django-commons org; better maintained |
| `runtime.txt` for Python version on Render | `.python-version` file or `PYTHON_VERSION` env var | Render docs update 2025 | `runtime.txt` not mentioned in current Render docs |

**Deprecated/outdated:**
- `django-tailwind` (timonweb/django-tailwind): Still works but `django-tailwind-cli` (django-commons) is the community-preferred alternative for standalone CLI use.
- Tailwind CDN "Play CDN": Only for prototyping; does not support `@theme` custom colors, cannot be used in production.
- `STATICFILES_STORAGE = "whitenoise.storage...."`: Deprecated in favor of `STORAGES` dict in Django 4.2+.

---

## Open Questions

1. **Tailwind CLI binary on Render build vs. runtime container**
   - What we know: `django-tailwind-cli` downloads the binary on first run; `tailwind build` in `build.sh` should generate `app.css` during build.
   - What's unclear: Whether the Render build container persists the downloaded binary or if each build re-downloads. Also unclear if `python manage.py tailwind runserver` (which downloads binary) works in the Render build environment at all, or only `tailwind build` is safe.
   - Recommendation: Set `TAILWIND_CLI_AUTOMATIC_DOWNLOAD = False` in prod settings; rely on `python manage.py tailwind build` in `build.sh` to produce the compiled CSS; the binary is only needed at build time, not runtime.

2. **django-tailwind-cli source CSS location relative to STATICFILES_DIRS**
   - What we know: `TAILWIND_CLI_SRC_CSS` is relative to the first `STATICFILES_DIRS` entry. `TAILWIND_CLI_DIST_CSS` is also relative to the first `STATICFILES_DIRS` entry.
   - What's unclear: The exact relationship — whether the source CSS at `assets/src/main.css` causes whitenoise to try to serve the raw source file during collectstatic.
   - Recommendation: Verify by running `python manage.py collectstatic` locally after `tailwind build`. If the manifest errors on the source CSS, either exclude `src/` from collectstatic or switch to `CompressedStaticFilesStorage` (without Manifest) to be lenient.

3. **`createsuperuser` on Render after first deployment**
   - What we know: `createsuperuser` requires a username by default; our model has no username.
   - What's unclear: How Render Shell / one-off commands work for superuser creation.
   - Recommendation: `createsuperuser` with `AbstractUser(username=None)` + `REQUIRED_FIELDS = []` should prompt only for email + password. Verify locally first. Document in project README.

---

## Sources

### Primary (HIGH confidence)

- Django 5.2 official docs — `https://docs.djangoproject.com/en/5.2/topics/auth/customizing/` — AbstractUser, AbstractBaseUser, USERNAME_FIELD, AUTH_USER_MODEL
- Django 5.2 official docs — `https://docs.djangoproject.com/en/5.2/topics/auth/default/` — login_required, login(), logout(), next parameter, SESSION_EXPIRE_AT_BROWSER_CLOSE
- Tailwind CSS v4 official docs — `https://tailwindcss.com/docs/theme` — @theme directive, --color-* namespace, CSS-first configuration
- Tailwind CSS v4 official docs — `https://tailwindcss.com/docs/colors` — color shade naming, hex vs oklch, --color-*: initial
- WhiteNoise 6.11.0 official docs — `https://whitenoise.readthedocs.io/en/stable/django.html` — middleware position, STORAGES config, STATIC_ROOT
- django-tailwind-cli official docs — `https://django-tailwind-cli.readthedocs.io/latest/` — version 4.5.1, settings, development commands
- django-tailwind-cli PyPI — `https://pypi.org/project/django-tailwind-cli/` — version 4.5.1 confirmed, Tailwind v4 support confirmed
- Render official docs — `https://render.com/docs/deploy-django` — build.sh, render.yaml, environment variables, DATABASE_URL, RENDER_EXTERNAL_HOSTNAME
- Render official docs — `https://render.com/docs/health-checks` — healthCheckPath, 2xx/3xx required, 60s restart threshold
- Render official docs — `https://render.com/docs/python-version` — PYTHON_VERSION env var, .python-version file, default 3.13.4+ for new services

### Secondary (MEDIUM confidence)

- joshkaramuth.com — "How to Remove Username from Django's Default User model" — AbstractUser + username=None pattern; complete manager/forms/admin code verified against official Django docs
- learndjango.com — "Django Custom User Model" — community-standard tutorial; AbstractUser approach confirmed as recommended
- djangocentral.com — "Authentication using an Email Address" — EmailBackend pattern; note that if `USERNAME_FIELD = 'email'`, the default ModelBackend already looks up by email — custom backend only needed for additional flexibility

### Tertiary (LOW confidence)

- loopwerk.io — "Production-ready cache-busting for Django and Tailwind CSS" (2025) — build order (tailwind build before collectstatic); not independently verified against official docs but aligns with WhiteNoise docs
- Medium — various posts on django-tailwind-cli with Render — general patterns; superseded by official docs above

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified via PyPI and official docs
- Architecture: HIGH — patterns from official Django docs and django-tailwind-cli docs
- Pitfalls: HIGH for Django pitfalls (official docs); MEDIUM for Tailwind+Whitenoise interaction (community sources, aligns with whitenoise docs)
- Render deployment: HIGH — official Render docs accessed directly

**Research date:** 2026-02-21
**Valid until:** 2026-03-21 (30 days; stable technologies with no upcoming breaking changes expected)
