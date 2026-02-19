# Technology Stack

**Project:** LaundryAdvisor
**Researched:** 2026-02-19
**Confidence note:** Web search and Context7 were unavailable in this research session. All version claims are based on training data (cutoff August 2025) and are marked with confidence levels. Before pinning versions in requirements.txt, run `pip index versions <package>` or check PyPI for the latest patch release.

---

## Recommended Stack

### Core Framework

| Technology | Pinned Version | Purpose | Why |
|------------|---------------|---------|-----|
| Python | 3.12.x | Runtime | LTS-grade stability, `django-storages` and `openai` SDK well-tested on 3.12; avoid 3.13 (too new, compatibility risk as of Aug 2025) |
| Django | 5.1.x | Web framework, ORM, admin, auth | Latest non-LTS stable; includes async-ready ORM, improved `JSONField`, built-in `LoginRequired` mixin. Django 5.0 LTS ends April 2025; 5.1 extends through Dec 2025. Use 5.1 unless Render's Python buildpack forces an older version. [MEDIUM confidence — verify on djangoproject.com/download] |
| gunicorn | 22.x | WSGI server for production | Standard WSGI server for Django on Render; Render's "Start Command" expects `gunicorn project.wsgi`. Do NOT use `python manage.py runserver` in production. [HIGH confidence] |

### Database

| Technology | Pinned Version | Purpose | Why |
|------------|---------------|---------|-----|
| PostgreSQL | 16.x (Render-managed) | Primary database | Render's managed PostgreSQL defaults to PG 15/16. Use Django ORM exclusively — no raw SQL. JSONField (used for AI output storage) is a first-class PostgreSQL feature in Django 3.1+. [HIGH confidence] |
| psycopg2-binary | 2.9.9 | Django ↔ PostgreSQL adapter | `psycopg2-binary` is the correct package for Render (pre-compiled wheel, no system libpq-dev needed). Do NOT use bare `psycopg2` unless you control the build environment. psycopg3 (`psycopg`) is an option but django-storages and most Django docs still reference psycopg2; stick with psycopg2-binary for team predictability. [HIGH confidence] |

### File Storage (AWS S3)

| Technology | Pinned Version | Purpose | Why |
|------------|---------------|---------|-----|
| django-storages | 1.14.x | Django storage backend for S3 | The canonical library for Django + S3. Provides `S3Boto3Storage` backend. Replaces `DEFAULT_FILE_STORAGE` in Django settings. Works with `ImageField` transparently. [HIGH confidence] |
| boto3 | 1.34.x | AWS SDK (S3 client) | django-storages[s3] depends on boto3. Pin a compatible minor version. boto3 versions track closely; 1.34.x was stable as of Aug 2025. Install via `pip install django-storages[s3]` which pulls boto3 automatically. [MEDIUM confidence — patch version may have moved; verify on PyPI] |
| Pillow | 10.3.x | Image validation and processing | Required for Django `ImageField` to function. Also enables MIME type inspection and dimension checks before S3 upload. Pin to 10.x (stable, well-maintained). [HIGH confidence] |

### AI / OpenAI

| Technology | Pinned Version | Purpose | Why |
|------------|---------------|---------|-----|
| openai | 1.35.x | OpenAI Python SDK | Version 1.x SDK (released Nov 2023) is the current generation. Uses `client = openai.OpenAI(api_key=...)` pattern. GPT-4o Vision is called via `client.chat.completions.create(model="gpt-4o", ...)` with image content blocks. Structured JSON output uses `response_format={"type": "json_object"}`. Pin to 1.x — the 0.x API is deprecated and broken on current endpoints. [HIGH confidence] |

### Environment / Configuration

| Technology | Pinned Version | Purpose | Why |
|------------|---------------|---------|-----|
| python-dotenv | 1.0.x | `.env` file loader for local dev | Loads `.env` into `os.environ` before Django settings read them. Call `load_dotenv()` at the top of `manage.py` and `wsgi.py`. On Render, env vars are set in the dashboard — `load_dotenv()` is a no-op when the vars are already present. [HIGH confidence] |
| dj-database-url | 2.1.x | Parse `DATABASE_URL` into Django `DATABASES` dict | Render injects `DATABASE_URL` as a single connection string. `dj_database_url.config(default=os.getenv("DATABASE_URL"))` is the standard integration. Use version 2.x which supports psycopg2 and psycopg3. [HIGH confidence] |

### Static Files

| Technology | Pinned Version | Purpose | Why |
|------------|---------------|---------|-----|
| whitenoise | 6.7.x | Serve static files from Django on Render | Render does not provide a static file CDN out of the box. Whitenoise compresses and caches static files (CSS, JS, admin assets) without a separate nginx layer. Add `whitenoise.middleware.WhiteNoiseMiddleware` early in `MIDDLEWARE`. Run `python manage.py collectstatic` in Render's build command. [HIGH confidence] |

### Supporting Libraries

| Library | Pinned Version | Purpose | When to Use |
|---------|---------------|---------|-------------|
| django-crispy-forms | 2.3.x | Bootstrap-friendly form rendering | Use for login, registration, wardrobe-item forms. Reduces template boilerplate for form fields. Pair with `crispy-bootstrap5`. Only add if using Bootstrap 5 in templates. [MEDIUM confidence] |
| crispy-bootstrap5 | 2024.x | Bootstrap 5 template pack for crispy-forms | Required companion to django-crispy-forms when using Bootstrap 5. [MEDIUM confidence] |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| WSGI server | gunicorn | uvicorn | Django on Render is WSGI; uvicorn is ASGI. No async views needed here. |
| DB adapter | psycopg2-binary | psycopg (v3) | psycopg3 is modern but adds migration friction and less community Q&A for team projects as of 2025. |
| Storage backend | django-storages S3 | direct boto3 in views | django-storages integrates with `ImageField` transparently; direct boto3 requires custom upload logic everywhere. |
| OpenAI output parsing | `response_format=json_object` + `json.loads()` | pydantic structured outputs | Pydantic structured outputs with `openai` 1.x `parse()` method is powerful but adds complexity. For this project's constrained JSON schema, `json_object` mode + manual field extraction is simpler and more debuggable. |
| Static files | whitenoise | S3 static files via django-storages | Serving statics from S3 requires a second S3 bucket configuration and CORS setup. Whitenoise is zero-configuration for a Render web service. |
| Task queue | (none) | Celery + Redis | PROJECT.md explicitly excludes async queues. OpenAI calls are synchronous with a per-user rate limit; Celery overhead is unjustified. |
| Frontend | Django templates | React/HTMX | Spec says server-rendered templates only. HTMX could enhance UX later but is out of scope for v1. |
| Auth | Django built-in auth | django-allauth | Social login is out of scope. Built-in `django.contrib.auth` covers registration, login, logout, and password reset. |
| Form styling | django-crispy-forms | plain Django forms | Optional — only add crispy-forms if Bootstrap 5 is in the template stack. Raw Django form rendering works fine. |

---

## Integration Patterns

### S3 Storage: Local vs Render

**Local development** — use local filesystem storage to avoid S3 credentials in dev:

```python
# settings/local.py or settings.py with env-switch
if os.getenv("USE_S3", "False") == "True":
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "us-east-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_S3_FILE_OVERWRITE = False       # prevent name collisions
    AWS_DEFAULT_ACL = None              # use bucket policy, not per-object ACL
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"
else:
    # Local dev: store in /media/ on disk
    MEDIA_ROOT = BASE_DIR / "media"
    MEDIA_URL = "/media/"
```

In `.env.example`:
```
USE_S3=False
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
```

On Render, set `USE_S3=True` and all `AWS_*` vars in the Render dashboard environment variables panel. Never commit actual credentials.

**S3 Bucket Policy:** Create a dedicated IAM user with `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` on the single bucket. Block all public access at the bucket level; use presigned URLs or keep objects private (garment photos are user-specific).

---

### OpenAI GPT-4o Vision: Structured JSON Output

Use `response_format={"type": "json_object"}` with an explicit schema description in the system prompt. Do NOT rely on the model's default output format.

```python
import json
import openai

client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def analyze_care_label(image_url: str) -> dict:
    """
    Call GPT-4o Vision with the S3 URL of a care label image.
    Returns a parsed dict matching the care instruction schema.
    Raises openai.OpenAIError on API failure.
    """
    system_prompt = """
You are a laundry care label expert. Analyze the care label in the image and return
ONLY a JSON object with this exact schema — no extra keys, no markdown, no explanation:

{
  "wash_temperature": "30C" | "40C" | "60C" | "hand_wash" | "do_not_wash" | null,
  "wash_cycle": "normal" | "gentle" | "permanent_press" | null,
  "drying_method": "tumble_low" | "tumble_medium" | "line_dry" | "flat_dry" | "do_not_tumble" | null,
  "ironing": "low" | "medium" | "high" | "do_not_iron" | "steam_ok" | null,
  "bleach": "any_bleach" | "non_chlorine" | "do_not_bleach" | null,
  "dry_clean": "dry_clean" | "do_not_dry_clean" | null,
  "special_notes": "string or null",
  "confidence": "high" | "medium" | "low",
  "uncertain_fields": ["list of field names where confidence is low, or empty array"]
}

If a symbol is unclear or absent, return null for that field and include it in uncertain_fields.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_url,
                            "detail": "high",  # use "high" for care label text/symbols
                        },
                    },
                    {
                        "type": "text",
                        "text": "Analyze this care label and return the JSON object.",
                    },
                ],
            },
        ],
        max_tokens=500,  # care label JSON is small; cap to control cost
    )
    raw_json = response.choices[0].message.content
    return json.loads(raw_json)
```

**Cost control notes:**
- `"detail": "high"` costs more tokens than `"low"` but is needed for symbol recognition. Profile on a test batch.
- `max_tokens=500` is a hard cap — the JSON response for care labels is ~200-300 tokens. This prevents runaway costs.
- `model="gpt-4o"` is current as of Aug 2025. Verify the model name hasn't been superseded by `gpt-4o-2024-11-20` or similar. [MEDIUM confidence — model naming conventions change frequently]

---

### Daily Rate Limiting (10 analyses/user/day)

Use a Django model to track usage. Avoid Redis/cache-based solutions — they require extra infrastructure.

```python
# models.py
from django.db import models
from django.utils import timezone

class AIAnalysisLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    garment = models.ForeignKey("Garment", on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    raw_response = models.JSONField()  # store full OpenAI response for audit

    class Meta:
        indexes = [models.Index(fields=["user", "created_at"])]


def get_analyses_today(user) -> int:
    today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return AIAnalysisLog.objects.filter(user=user, created_at__gte=today_start).count()

DAILY_LIMIT = 10

def check_rate_limit(user):
    if get_analyses_today(user) >= DAILY_LIMIT:
        raise PermissionError("Daily analysis limit reached. Resets at midnight.")
```

**Deduplication:** Before calling OpenAI, check if `Garment.ai_analysis` is already populated and the care label image has not changed. Store a SHA-256 hash of the uploaded file in the garment model; if the hash matches the last analysis, return the cached result.

---

### Render Deployment Configuration

**Build Command** (set in Render dashboard):
```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

**Start Command** (set in Render dashboard):
```bash
gunicorn laundry_advisor.wsgi:application --bind 0.0.0.0:$PORT --workers 2
```

**Environment Variables** (set in Render dashboard, never committed):
```
SECRET_KEY=<generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())">
DEBUG=False
DATABASE_URL=<auto-injected by Render managed PostgreSQL>
ALLOWED_HOSTS=<your-app>.onrender.com
USE_S3=True
AWS_STORAGE_BUCKET_NAME=
AWS_S3_REGION_NAME=us-east-1
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
OPENAI_API_KEY=
```

**settings.py Render integration:**
```python
import os
import dj_database_url
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()  # no-op on Render; loads .env locally

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ["SECRET_KEY"]
DEBUG = os.getenv("DEBUG", "False") == "True"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost 127.0.0.1").split()

DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL", "postgres://localhost/laundry_advisor"),
        conn_max_age=600,
    )
}

# Whitenoise for static files
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # immediately after SecurityMiddleware
    # ... rest of middleware
]

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```

**Render-specific gotchas:**
- Render's filesystem is ephemeral. Any file written to disk (e.g., uploaded images before S3 push) is lost on restart. Always upload to S3 before saving the model.
- `PORT` is injected by Render automatically; gunicorn must bind to `0.0.0.0:$PORT`.
- Free-tier Render instances sleep after 15 minutes of inactivity. First request after sleep is slow (~30s). Use a paid plan or accept this for demo purposes.
- Run `migrate` in the build command, not the start command, to avoid migration races on restart.

---

## requirements.txt — Pinned for Team Reproducibility

```text
# Core
Django==5.1.*
gunicorn==22.*
psycopg2-binary==2.9.*
dj-database-url==2.1.*
python-dotenv==1.0.*

# Storage
django-storages[s3]==1.14.*
Pillow==10.3.*

# AI
openai==1.35.*

# Static files
whitenoise==6.7.*

# Forms (optional — add if using Bootstrap 5)
# django-crispy-forms==2.3.*
# crispy-bootstrap5==2024.*
```

**Team setup instructions** (for README):
```bash
# Clone and setup
git clone <repo-url>
cd laundry_advisor
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your local values

# Initialize database
python manage.py migrate
python manage.py createsuperuser

# Run
python manage.py runserver
```

---

## What NOT to Use and Why

| Library / Pattern | Reason to Avoid |
|-------------------|----------------|
| Celery + Redis | Explicitly out of scope. Adds two extra services (worker + broker) for a feature that doesn't need async: OpenAI calls are synchronous and fast enough for direct request handling at 10/day/user. |
| Django REST Framework (DRF) | The frontend is Django templates, not an API consumer. DRF adds boilerplate without benefit. Use standard Django views returning rendered templates. If you later need an API, add it incrementally. |
| django-environ | Redundant with python-dotenv + dj-database-url. Two .env loaders create confusion. Stick to one. |
| psycopg (v3) | More modern, but breaks compatibility with several third-party packages still on psycopg2. Use psycopg2-binary for predictable team onboarding. |
| `response_format={"type": "json_schema"}` (strict mode) | Available in openai 1.x for certain models, but GPT-4o Vision support for strict mode was incomplete as of Aug 2025. Use `json_object` mode with a schema-described system prompt. [MEDIUM confidence — verify current GPT-4o vision capabilities] |
| Storing base64 images in DB | Do NOT encode images as base64 and pass to OpenAI directly. Generate short-lived presigned S3 URLs and pass the URL. This keeps DB size manageable and avoids base64 encoding overhead. |
| `DEBUG=True` on Render | `DEBUG=True` in production exposes stack traces and disables security checks. Always set `DEBUG=False` in the Render dashboard. |
| Bare `openai.api_key = ...` (global pattern) | Deprecated in openai 1.x. Always instantiate `client = openai.OpenAI(api_key=...)` per-module or use a module-level singleton. |

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Django 5.1 as recommended version | MEDIUM | As of Aug 2025, 5.1 was current. Django 5.2 (LTS) may have released by Feb 2026. Verify on djangoproject.com/download before pinning. |
| psycopg2-binary for Render | HIGH | Well-established pattern; Render's build environment confirmed to support pre-compiled wheels. |
| django-storages[s3] S3 integration | HIGH | Stable, well-documented pattern since Django 2.x. |
| openai SDK 1.x patterns | HIGH | Version 1.x released Nov 2023, fully stable. Core API (chat.completions.create with image_url) is stable. |
| `response_format={"type": "json_object"}` for GPT-4o Vision | MEDIUM | Confirmed working as of Aug 2025 for GPT-4o; verify that Vision inputs are still supported with json_object mode on current model versions. |
| gunicorn on Render | HIGH | Render's official Django deployment docs recommend gunicorn. |
| whitenoise for static files | HIGH | Render's official Django docs recommend whitenoise for static file serving. |
| dj-database-url + DATABASE_URL | HIGH | Render injects DATABASE_URL; dj-database-url is the canonical parser. |
| boto3 version compatibility | MEDIUM | boto3 patch versions change frequently; `django-storages[s3]` will pull a compatible boto3 — pin the major+minor but let pip resolve the patch. |
| Django 5.2 LTS timing | LOW | Django 5.2 LTS was planned for April 2025 release. By Feb 2026, it may be the current LTS. Research this and prefer the LTS if available. |

---

## Sources

Note: All sources below are based on training knowledge (cutoff August 2025). External lookup was unavailable in this research session. Verify version numbers at these URLs before pinning in requirements.txt.

- Django releases: https://www.djangoproject.com/download/
- psycopg2-binary on PyPI: https://pypi.org/project/psycopg2-binary/
- django-storages docs: https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
- openai Python SDK: https://github.com/openai/openai-python
- OpenAI Vision guide: https://platform.openai.com/docs/guides/vision
- OpenAI JSON mode: https://platform.openai.com/docs/guides/text-generation/json-mode
- dj-database-url: https://github.com/jazzband/dj-database-url
- whitenoise docs: https://whitenoise.readthedocs.io/en/stable/django.html
- Render Django deployment: https://render.com/docs/deploy-django
- Render environment variables: https://render.com/docs/environment-variables
