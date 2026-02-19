# Phase 1: Scaffolding and Auth - Research

**Researched:** 2026-02-19
**Domain:** Django project setup, split settings, custom auth, Render deployment baseline
**Confidence:** HIGH — all major findings verified against PyPI, official Django docs, and Render docs as of 2026-02-19

---

## Summary

Phase 1 establishes the foundation that every subsequent phase depends on: a working Django project, a custom user model with email-based auth, split settings that prevent DEBUG=True from reaching Render, and a verified deployment baseline on Render with PostgreSQL.

The primary version decision resolves the blocker from prior research: **Django 5.2 LTS** released April 2, 2025 and is the correct choice for this project. Django 6.0.2 (released Feb 3, 2026) exists but is not LTS. Django 5.2 LTS receives security support through April 2028. All library versions have been verified against PyPI on 2026-02-19.

The single most important architectural decision for Phase 1 is creating the custom user model with email-as-username **before running any migrations**. This cannot be retrofitted without destroying and recreating the database. Everything else in this phase is recoverable; this is not.

**Primary recommendation:** Start with `django-admin startproject`, immediately create the `accounts` app with a custom `AbstractBaseUser` model (email as `USERNAME_FIELD`, no `username` field), set `AUTH_USER_MODEL = "accounts.CustomUser"` in settings, and only then run the first migration. Split settings into `base.py`, `development.py`, and `production.py` from the first commit.

---

## Standard Stack

### Core (Phase 1 scope)

| Library | Verified Version | Purpose | Why Standard |
|---------|-----------------|---------|--------------|
| Django | 5.2.11 LTS | Web framework, ORM, admin, auth | Current LTS — security support to April 2028. Django 6.0 exists but is not LTS. |
| Python | 3.12.x | Runtime | LTS-grade stability; Django 5.2 supports 3.10–3.14; 3.12 is the safest choice for team reproducibility |
| gunicorn | 25.1.0 | WSGI production server | Required for Render; latest stable (released Feb 13, 2026). Use WSGI (not ASGI/uvicorn) — no async views in this project. |
| psycopg2-binary | 2.9.11 | PostgreSQL adapter | Latest stable (Oct 2025). Still supported in Django 5.2. psycopg3 is the future but adds migration friction; psycopg2-binary is safer for team projects now. |
| dj-database-url | 3.1.2 | Parse `DATABASE_URL` env var | Latest stable (released Feb 19, 2026). Compatible with Django 4.2, 5.2, and 6. Use `conn_max_age=600, conn_health_checks=True`. |
| python-dotenv | 1.2.1 | Load `.env` locally | Latest stable. No-op on Render (env vars injected by dashboard). Call `load_dotenv()` at top of `manage.py` and `wsgi.py`. |
| whitenoise | 6.11.0 | Serve static files on Render | Current stable version. Use `STORAGES` dict (not deprecated `STATICFILES_STORAGE`). |

### Supporting

| Library | Verified Version | Purpose | When to Use |
|---------|-----------------|---------|-------------|
| django-crispy-forms | 2.3.x | Bootstrap-styled form rendering | Use for login/register forms if Bootstrap 5 is in the template stack. Only add if team wants Bootstrap; plain Django form rendering works. |
| crispy-bootstrap5 | 2024.x | Bootstrap 5 template pack | Required companion to django-crispy-forms when using Bootstrap 5. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Django 5.2 LTS | Django 6.0.2 | 6.0 is not LTS; security support ends April 2027 only. 5.2 LTS supported to April 2028. Use 5.2. |
| psycopg2-binary | psycopg (v3) | psycopg3 is the modern choice but requires more team onboarding; psycopg2-binary is battle-tested on Render. |
| gunicorn (WSGI) | uvicorn/gunicorn+UvicornWorker (ASGI) | Render's own Django docs show ASGI config with uvicorn workers. However, this project uses no async views or Django Channels — pure WSGI gunicorn is simpler and sufficient. |
| python-dotenv | django-environ | django-environ combines env loading and type casting but adds a dependency. python-dotenv + dj-database-url covers all Phase 1 needs without overlap. |
| Custom user model (AbstractBaseUser) | Django's built-in `User` | Built-in User has `username` field which is redundant when email is the identifier. Switching later requires data migration. AbstractBaseUser is the right choice from day one. |

**Installation (Phase 1 only):**
```bash
pip install Django==5.2.11 gunicorn==25.1.0 psycopg2-binary==2.9.11 \
    dj-database-url==3.1.2 python-dotenv==1.2.1 "whitenoise[brotli]==6.11.0"
pip freeze > requirements.txt
```

---

## Architecture Patterns

### Recommended Project Structure

The prior architecture research established this layout. Phase 1 creates the skeleton:

```
laundry_advisor/              <- Django project package (manage.py lives alongside this)
├── settings/
│   ├── __init__.py           <- empty
│   ├── base.py               <- shared settings for all environments
│   ├── development.py        <- from .base import *; DEBUG=True; local DB
│   └── production.py         <- from .base import *; DEBUG=False; Render settings
├── urls.py
└── wsgi.py

apps/
└── accounts/                 <- Phase 1: custom user model + auth views
    ├── migrations/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── forms.py              <- SignUpForm using CustomUser
    ├── models.py             <- CustomUser (AbstractBaseUser, email login)
    ├── urls.py
    └── views.py              <- SignUpView, uses Django built-in LoginView/LogoutView

templates/
├── base.html                 <- mobile-responsive base (Bootstrap 5 via CDN)
├── home.html
└── registration/
    ├── login.html
    ├── logout.html           <- not needed: Django handles redirect
    └── signup.html

static/                       <- CSS, JS (collected by collectstatic)
staticfiles/                  <- collectstatic output (gitignored)
manage.py
requirements.txt
.env                          <- NEVER committed
.env.example                  <- ALWAYS committed, no values
.gitignore
render.yaml
build.sh                      <- Render build script (executable)
```

### Pattern 1: Custom User Model — Email as Username (AbstractBaseUser)

**What:** Create a custom user model that uses email as the primary identifier, removing the `username` field entirely.

**When to use:** Always, from day one, before any migration is run. Cannot be changed afterward without database recreation.

**Critical timing:** Create `accounts` app and `CustomUser` model, add `AUTH_USER_MODEL = "accounts.CustomUser"` to settings, then run `python manage.py migrate` for the first time. Never run migrations with the default `User` model if you plan to switch.

**Model:**
```python
# apps/accounts/models.py
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be provided")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = CustomUserManager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # email and password are always required; nothing else prompted

    def __str__(self):
        return self.email
```

**Settings:**
```python
# settings/base.py
AUTH_USER_MODEL = "accounts.CustomUser"
```

**Admin (required or createsuperuser will break):**
```python
# apps/accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ["email", "is_staff", "is_active"]
    ordering = ["email"]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "password1", "password2", "is_staff", "is_active"),
        }),
    )
    search_fields = ("email",)

admin.site.register(CustomUser, CustomUserAdmin)
```

### Pattern 2: Split Settings (base / development / production)

**What:** Three settings files; environment selects which to use via `DJANGO_SETTINGS_MODULE`.

**When to use:** From the first commit. The decision was locked in prior planning.

```python
# settings/base.py
import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

load_dotenv()  # no-op on Render; loads .env locally

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # adjust based on actual layout

SECRET_KEY = os.environ["SECRET_KEY"]  # fail loudly if missing — never have a default
AUTH_USER_MODEL = "accounts.CustomUser"
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.accounts",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # immediately after SecurityMiddleware
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

```python
# settings/development.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", "postgresql://localhost/laundry_advisor_dev"),
        conn_max_age=600,
        conn_health_checks=True,
    )
}
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
```

```python
# settings/production.py
from .base import *

DEBUG = False

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split()
RENDER_EXTERNAL_HOSTNAME = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

DATABASES = {
    "default": dj_database_url.config(
        default=os.environ["DATABASE_URL"],  # fail loudly if missing
        conn_max_age=600,
        conn_health_checks=True,
    )
}
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
```

### Pattern 3: Auth Views — Login, Logout, Register

Django provides `LoginView` and `LogoutView` out of the box; only register (signup) needs a custom view. Django 5.x requires logout via POST (not GET).

```python
# apps/accounts/forms.py
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ("email",)
```

```python
# apps/accounts/views.py
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views.generic import CreateView
from .forms import CustomUserCreationForm

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"
```

```python
# apps/accounts/urls.py
from django.urls import path
from .views import SignUpView

urlpatterns = [
    path("signup/", SignUpView.as_view(), name="signup"),
]
```

```python
# laundry_advisor/urls.py
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("apps.accounts.urls")),    # signup first
    path("accounts/", include("django.contrib.auth.urls")),  # login, logout after
    path("", TemplateView.as_view(template_name="home.html"), name="home"),
    path("healthz/", include("apps.accounts.health_urls")),  # or inline view
]
```

**Logout requires POST in Django 5.x:**
```html
<!-- In base.html nav -->
{% if user.is_authenticated %}
  <form action="{% url 'logout' %}" method="post">
    {% csrf_token %}
    <button type="submit">Log Out</button>
  </form>
{% endif %}
```

### Pattern 4: Health Check Endpoint

Simple inline view — no third-party package needed for Phase 1:

```python
# In laundry_advisor/urls.py (or a dedicated health.py view)
from django.http import HttpResponse

def health_check(request):
    return HttpResponse("OK", content_type="text/plain", status=200)

urlpatterns = [
    ...
    path("healthz/", health_check, name="health-check"),
]
```

### Pattern 5: Session Persistence (AUTH-04)

Django's default session configuration already satisfies AUTH-04 with no extra settings:

- `SessionMiddleware` is in `MIDDLEWARE` by default
- `SESSION_COOKIE_AGE` defaults to 1,209,600 seconds (2 weeks)
- `SESSION_EXPIRE_AT_BROWSER_CLOSE` defaults to `False` (cookies persist across browser close/refresh)
- Sessions are stored in the database by default (`django.contrib.sessions` must be in `INSTALLED_APPS` and `migrate` must have been run)

No extra configuration is needed. `migrate` creates the `django_session` table automatically.

### Pattern 6: Render Deployment Configuration

**render.yaml:**
```yaml
databases:
  - name: laundryadvisor-db
    databaseName: laundryadvisor
    user: laundryadvisor
    plan: free          # expires 30 days after creation — upgrade before demo

services:
  - type: web
    name: laundryadvisor
    runtime: python
    plan: free          # spins down after 15 min inactivity
    buildCommand: "./build.sh"
    startCommand: "gunicorn laundry_advisor.wsgi:application --workers 2 --timeout 60 --bind 0.0.0.0:$PORT"
    envVars:
      - key: PYTHON_VERSION
        value: 3.12.0
      - key: DJANGO_SETTINGS_MODULE
        value: laundry_advisor.settings.production
      - key: DATABASE_URL
        fromDatabase:
          name: laundryadvisor-db
          property: connectionString
      - key: SECRET_KEY
        generateValue: true
      - key: RENDER_EXTERNAL_HOSTNAME
        fromService:
          type: web
          name: laundryadvisor
          property: host
```

**build.sh** (must be `chmod +x build.sh` before committing):
```bash
#!/usr/bin/env bash
set -o errexit  # exit on error

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

**ALLOWED_HOSTS on Render:** Render automatically injects `RENDER_EXTERNAL_HOSTNAME` environment variable — use it in `production.py` as shown in Pattern 2.

### Pattern 7: .gitignore and .env.example

**.gitignore minimum for Phase 1:**
```
# Environment
.env
.env.local
.env.production

# Virtual environment
venv/
.venv/
env/

# Python
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.egg-info/
dist/
build/

# Django
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
staticfiles/
media/

# IDE
.vscode/
.idea/
*.swp
```

**.env.example (Phase 1 keys only — more added in later phases):**
```
SECRET_KEY=your-secret-key-here
DEBUG=True
DATABASE_URL=postgresql://localhost/laundry_advisor_dev
ALLOWED_HOSTS=localhost,127.0.0.1

# Phase 2 (S3) — leave blank until Phase 2
USE_S3=False
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=

# Phase 3 (OpenAI) — leave blank until Phase 3
OPENAI_API_KEY=
```

### Anti-Patterns to Avoid

- **Creating migrations before `AUTH_USER_MODEL` is set:** Running `python manage.py migrate` before setting `AUTH_USER_MODEL = "accounts.CustomUser"` creates a `auth_user` table tied to the default `User` model. The migration to switch later is extremely painful. Set it before any migration runs.
- **Using `AbstractUser` if you want email-only login:** `AbstractUser` keeps the `username` field and makes email-as-username awkward. Use `AbstractBaseUser` to remove `username` entirely.
- **Using `STATICFILES_STORAGE` in Django 5.2:** This setting was deprecated in Django 4.2 and raises a warning in 5.2. Use `STORAGES["staticfiles"]` dict instead.
- **Putting secrets in `settings/base.py` with defaults:** `SECRET_KEY = os.getenv("SECRET_KEY", "some-default")` silently uses a weak key if the env var is missing. Use `os.environ["SECRET_KEY"]` (no default) to fail loudly.
- **Using `gunicorn project.wsgi` start command without `--bind 0.0.0.0:$PORT`:** Render assigns a dynamic port via `$PORT` env var. Gunicorn must bind to it explicitly or Render's router cannot reach the service.
- **Using SQLite locally while PostgreSQL is on Render:** Schema differences cause migration surprises. Connect to PostgreSQL from Day 1 locally via `DATABASE_URL`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Parsing `DATABASE_URL` env var | Custom parser | `dj-database-url 3.1.2` | Handles all PostgreSQL URL formats, connection pooling, health checks |
| Serving static files on Render | Custom Nginx | `whitenoise 6.11.0` | Zero-config, compresses+hashes files, works on Render with no additional services |
| Session management | Custom session middleware | Django built-in sessions | Already handles database-backed sessions, CSRF, cookie security |
| Password hashing | Custom hasher | Django built-in | Django uses PBKDF2 by default; Argon2 available. Never implement your own. |
| Email normalization | Custom logic | `BaseUserManager.normalize_email()` | Handles case normalization, domain lowercasing |
| WSGI server | `manage.py runserver` in production | `gunicorn 25.1.0` | `runserver` is single-threaded, not production-grade, disabled in DEBUG=False mode |

**Key insight:** The Django auth system, session framework, and whitenoise together handle all auth and static file complexity. The only custom code needed is the user model and signup form.

---

## Common Pitfalls

### Pitfall 1: Custom User Model Created After First Migration

**What goes wrong:** `python manage.py migrate` is run to test that the database connects. Django creates `auth_user` table. Then `AUTH_USER_MODEL = "accounts.CustomUser"` is set. Django raises `ValueError: Dependency on app with no migrations: accounts` or a migration conflict. There is no clean fix except dropping the database and starting over.

**Why it happens:** Developers want to verify the DB connection before building the user model. Reasonable instinct, terrible consequence.

**How to avoid:** The only correct sequence is:
1. Create `apps/accounts/` directory
2. Write `CustomUser` model in `models.py`
3. Add `accounts` to `INSTALLED_APPS`
4. Set `AUTH_USER_MODEL = "accounts.CustomUser"` in settings
5. Run `python manage.py makemigrations accounts`
6. Run `python manage.py migrate`

Never run step 6 before step 4.

**Warning signs:** Git log shows a migration run before `accounts` app was created.

### Pitfall 2: Logout via GET (Django 5.x Breaking Change)

**What goes wrong:** Templates use `<a href="{% url 'logout' %}">Log Out</a>`. In Django 5.x, GET requests to `/accounts/logout/` no longer log the user out — they redirect to the login page (or return an error). Users click "Log Out" and nothing happens.

**Why it happens:** Every Django tutorial before 2024 used GET-based logout. Developers copy the old pattern.

**How to avoid:** All logout links must be forms with POST method and `{% csrf_token %}`. See Pattern 3 above.

**Warning signs:** Clicking "Log Out" in the UI does not change the nav bar state.

### Pitfall 3: `collectstatic` Fails on First Render Deploy

**What goes wrong:** The Render build step runs `python manage.py collectstatic --no-input`. It fails because `STATIC_ROOT` is not set, or `whitenoise` is not in `INSTALLED_APPS` with `runserver_nostatic`, or the `STORAGES` dict is misconfigured.

**Why it happens:** Static files work in local dev with `DEBUG=True` (Django serves them automatically). The production configuration is never tested locally before the first deploy.

**How to avoid:**
- Test locally with `DEBUG=False` and run `collectstatic` before the first commit that includes deployment config
- Use the exact `STORAGES` dict configuration shown in Pattern 2
- Verify `STATIC_ROOT = BASE_DIR / "staticfiles"` is set in base settings
- Ensure `whitenoise.middleware.WhiteNoiseMiddleware` is in MIDDLEWARE immediately after `SecurityMiddleware`

**Warning signs:** Render build logs show `CommandError: You're using the staticfiles app...` or `SuspiciousFileOperation`.

### Pitfall 4: Secrets Committed to Git History

**What goes wrong:** `.env` file or hardcoded `SECRET_KEY` / `DATABASE_URL` gets committed before `.gitignore` is set up. Even after removing the file, the secret is in git history and must be rotated.

**Why it happens:** Developers create settings before creating `.gitignore`. Easy ordering mistake on the first day.

**How to avoid:** The very first commit must include `.gitignore` and `.env.example`. No exceptions.

**Warning signs:** `git log --all -- .env` shows any commits. `git grep "SECRET_KEY"` finds actual keys (not `os.environ["SECRET_KEY"]` references).

### Pitfall 5: Free Render PostgreSQL Expires After 30 Days

**What goes wrong:** The free Render PostgreSQL database is created during Phase 1 deployment. 30 days later, it expires and the app stops working. By the time Phase 3 or 4 is in progress, all accumulated test data is gone.

**Why it happens:** The "free" tier sounds permanent. The 30-day limit is easy to miss.

**How to avoid:** Note the database creation date and upgrade to a paid Render PostgreSQL ($7/month starter) before the 30-day mark — or factor the data loss into the project timeline. For a group project lasting multiple weeks, plan to upgrade.

**Warning signs:** App returns 500 errors after day 30. Render dashboard shows database as "Expired".

### Pitfall 6: `RENDER_EXTERNAL_HOSTNAME` Not Added to `ALLOWED_HOSTS`

**What goes wrong:** `DEBUG=False` is set in production. A request comes from the Render URL. Django raises `DisallowedHost` and returns a 400 error. The app appears to be broken on Render even though the code is correct.

**Why it happens:** `ALLOWED_HOSTS` is set to a hardcoded list that doesn't include the Render-assigned hostname.

**How to avoid:** Use the pattern in `production.py` above: read `RENDER_EXTERNAL_HOSTNAME` env var (auto-injected by Render) and append it to `ALLOWED_HOSTS` dynamically.

**Warning signs:** Render logs show `Invalid HTTP_HOST header`. Browser shows "Bad Request (400)".

---

## Code Examples

Verified patterns from official sources:

### Complete build.sh

```bash
#!/usr/bin/env bash
# build.sh - Render build script
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
python manage.py migrate
```

Make executable before first commit: `git add build.sh && git update-index --chmod=+x build.sh`

### manage.py with dotenv

```python
#!/usr/bin/env python
# manage.py
import os
import sys

def main():
    # Load .env file for local development
    # python-dotenv is a no-op if the file doesn't exist (Render sets vars via dashboard)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not installed — ok in CI or minimal environments

    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "laundry_advisor.settings.development"
    )
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError("Django not found. Activate your venv.") from exc
    execute_from_command_line(sys.argv)

if __name__ == "__main__":
    main()
```

### Session persistence verification

The default Django session setup satisfies AUTH-04 with zero configuration beyond what `startproject` generates. The only verification needed:

```python
# Confirm these exist in base.py INSTALLED_APPS and MIDDLEWARE:
INSTALLED_APPS = [
    ...
    "django.contrib.sessions",     # required
    ...
]
MIDDLEWARE = [
    ...
    "django.contrib.sessions.middleware.SessionMiddleware",  # required
    ...
]
# Session cookie defaults (do not override unless needed):
# SESSION_COOKIE_AGE = 1209600  (2 weeks)
# SESSION_EXPIRE_AT_BROWSER_CLOSE = False  (sessions persist)
# SESSION_ENGINE = "django.contrib.sessions.backends.db"  (database-backed)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `STATICFILES_STORAGE = "whitenoise..."` | `STORAGES = {"staticfiles": {...}}` dict | Django 4.2 (deprecated), fully removed in 5.1+ | Use `STORAGES` dict; old string setting raises `RemovedInDjango51Warning` |
| `DEFAULT_FILE_STORAGE = "..."` | `STORAGES = {"default": {...}}` dict | Django 4.2 | Same — use `STORAGES` dict for both static and media |
| GET-based logout `<a href="/logout">` | POST-based logout `<form method="post">` | Django 5.0 | Logout via GET no longer works |
| `django.contrib.auth.User` (username-based) | `AbstractBaseUser` with `email` as `USERNAME_FIELD` | Best practice, not a Django change | Must be set before first migration |
| `gunicorn project.wsgi` without port | `gunicorn ... --bind 0.0.0.0:$PORT` | Render requirement | Required for Render to route traffic |
| `pip install Django` (latest) | `pip install Django==5.2.11` (pinned LTS) | Team project best practice | Prevents version drift across teammates |

**Deprecated/outdated:**
- `STATICFILES_STORAGE`: deprecated Django 4.2, raises warning in 5.2. Use `STORAGES` dict.
- `DEFAULT_FILE_STORAGE`: same deprecation path.
- GET-based logout: removed in Django 5.0. All logout must be POST.
- `response_format="json_object"` as a string (Phase 3, not Phase 1): use `{"type": "json_object"}` dict.

---

## Open Questions

1. **Project package name: `laundry_advisor` or `config`?**
   - What we know: Django is flexible — the project package created by `startproject` can be named anything. Common conventions are the project name (`laundry_advisor`) or a generic name (`config`).
   - What's unclear: The prior ARCHITECTURE.md uses `config/` as the settings directory but also references `laundry_advisor/` as the project root. These naming choices affect every import path and the gunicorn start command.
   - Recommendation: Use `laundry_advisor` as the Django project package name (the inner directory created by `startproject`). This makes imports and the gunicorn command (`laundry_advisor.wsgi`) unambiguous and self-documenting.

2. **Local PostgreSQL vs. SQLite for development?**
   - What we know: The PITFALLS.md explicitly warns against using SQLite locally while PostgreSQL is used in production — schema differences cause migration surprises.
   - What's unclear: Requiring all team members to install PostgreSQL locally adds setup friction. Using Render's free dev PostgreSQL remotely adds network latency.
   - Recommendation: Require PostgreSQL locally (via Docker or native install). Include Docker Compose snippet in the README for easy local PostgreSQL. The prior PITFALLS.md warns strongly against SQLite/PostgreSQL divergence; honor that.

3. **Bootstrap 5 via CDN or installed as static file?**
   - What we know: CDN is faster to set up for Phase 1; static file installation is more production-robust and works offline.
   - What's unclear: Team preference; whether offline development is needed.
   - Recommendation: CDN for Phase 1 (lowest friction, no build pipeline). Can switch to local static files in a later phase if needed.

4. **`whitenoise.runserver_nostatic` in development?**
   - What we know: Adding `whitenoise.runserver_nostatic` to `INSTALLED_APPS` before `django.contrib.staticfiles` makes `runserver` use WhiteNoise to serve static files — same as production. This catches static file bugs earlier.
   - What's unclear: Minor overhead in development. Team may prefer Django's default static serving.
   - Recommendation: Include `whitenoise.runserver_nostatic` in `INSTALLED_APPS` in `development.py` for parity with production behavior.

---

## Sources

### Primary (HIGH confidence)

- PyPI: Django 5.2.11 — https://pypi.org/project/Django/ (verified 2026-02-19)
- PyPI: gunicorn 25.1.0 — https://pypi.org/project/gunicorn/ (verified 2026-02-19)
- PyPI: psycopg2-binary 2.9.11 — https://pypi.org/project/psycopg2-binary/ (verified 2026-02-19)
- PyPI: dj-database-url 3.1.2 — https://pypi.org/project/dj-database-url/ (verified 2026-02-19)
- PyPI: python-dotenv 1.2.1 — https://pypi.org/project/python-dotenv/ (verified 2026-02-19)
- Django download page — https://www.djangoproject.com/download/ (Django 5.2.11 LTS confirmed current; Django 6.0.2 is latest non-LTS)
- End of life dates — https://endoflife.date/django (5.2 LTS security support to April 2028)
- WhiteNoise 6.11.0 docs — https://whitenoise.readthedocs.io/en/stable/django.html (`STORAGES` dict config, middleware placement)
- Render free tier limits — https://render.com/docs/free (30-day PostgreSQL expiry, 15-min spin-down confirmed)
- Render Django deploy docs — https://render.com/docs/deploy-django (`render.yaml`, `build.sh`, `RENDER_EXTERNAL_HOSTNAME`)
- Django session docs — https://docs.djangoproject.com/en/5.2/topics/http/sessions/ (default `SESSION_COOKIE_AGE=1209600`, `SESSION_EXPIRE_AT_BROWSER_CLOSE=False`)
- LearnDjango auth tutorial — https://learndjango.com/tutorials/django-login-and-logout-tutorial (POST logout requirement, SignUpView pattern)
- LearnDjango custom user model — https://learndjango.com/tutorials/django-custom-user-model (AbstractUser vs AbstractBaseUser decision)
- Django.wiki custom user with email — https://django.wiki/snippets/authentication-authorization/custom-user-model-email/ (AbstractBaseUser + CustomUserManager code)

### Secondary (MEDIUM confidence)

- Render Python version docs — https://render.com/docs/python-version (`PYTHON_VERSION` env var in render.yaml)
- Django deprecation timeline — https://docs.djangoproject.com/en/dev/internals/deprecation/ (`STATICFILES_STORAGE` removal)

---

## Metadata

**Confidence breakdown:**
- Standard stack versions: HIGH — all verified against PyPI on 2026-02-19
- Django version decision (5.2 LTS): HIGH — confirmed on djangoproject.com/download
- Authentication patterns: HIGH — verified against official Django docs and LearnDjango
- Render deployment config: HIGH — verified against render.com/docs/deploy-django
- Session persistence: HIGH — verified against docs.djangoproject.com/en/5.2/topics/http/sessions/
- WhiteNoise STORAGES dict: HIGH — verified against whitenoise.readthedocs.io/en/stable
- Free tier limitations: HIGH — verified against render.com/docs/free

**Research date:** 2026-02-19
**Valid until:** 2026-03-19 (30 days; library versions may have patch releases; Render free tier policies stable)
