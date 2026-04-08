# Architecture Patterns

**Domain:** Django laundry care advisor (server-rendered, multi-contributor team project)
**Researched:** 2026-02-19
**Confidence:** HIGH (Django patterns are mature and well-established; no breaking changes through training cutoff)

---

## Recommended Architecture

### Overview

A three-app Django project organized by domain responsibility. The project root holds configuration; domain logic is split into `accounts`, `wardrobe`, and `laundry` apps. A shared `services/` layer at the project level contains all third-party integrations (OpenAI, S3 helpers). Django templates with minimal JavaScript render all views.

```
laundry_advisor/               ← Django project root (settings, urls, wsgi)
├── config/                    ← settings split by environment
│   ├── settings/
│   │   ├── base.py
│   │   ├── development.py
│   │   └── production.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/              ← Django app: auth, user profile
│   ├── wardrobe/              ← Django app: items, image uploads, analysis
│   └── laundry/               ← Django app: basket logic, sorting views
├── services/                  ← Project-level: OpenAI client, S3 helpers
│   ├── __init__.py
│   ├── openai_client.py       ← GPT-4o Vision calls
│   └── s3_helpers.py          ← presigned URL generation (if needed)
├── templates/                 ← Project-level templates (base.html, partials)
├── static/                    ← CSS, JS, icons
├── requirements/
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
├── manage.py
└── .env                       ← never committed
```

### Why Three Apps (Not One, Not Six)

- **`accounts`** — Owns everything user-identity-related. Wraps Django's built-in auth. Adding a custom `UserProfile` model here keeps it isolated; other apps FK to `User`, not to `UserProfile`.
- **`wardrobe`** — Owns `WardrobeItem`, `AnalysisResult`, and the image-upload + GPT analysis flow. These are tightly coupled (you cannot analyze without an item, you cannot display results without analysis), so they belong together.
- **`laundry`** — Owns the laundry basket concept: grouping items into wash loads. Depends on `wardrobe` but has its own views and logic. Keeping it separate means the grouping algorithm can evolve independently without touching wardrobe CRUD.
- **`services/`** — Not a Django app (no models, no migrations). A plain Python package at project level that any app can import. This prevents circular imports and keeps third-party coupling in one place.

---

## Component Boundaries

| Component | Responsibility | Communicates With | Does NOT Own |
|-----------|---------------|-------------------|--------------|
| `accounts` app | Registration, login, logout, user profile model | Django auth, `wardrobe` (via FK) | Analysis logic, basket logic |
| `wardrobe` app | WardrobeItem CRUD, image upload to S3, trigger analysis, store results, enforce rate limit | `services/openai_client.py`, Django ORM, S3 via django-storages | Basket grouping algorithm |
| `laundry` app | Laundry basket views, grouping algorithm, load recommendations | `wardrobe` models (read-only queries), Django ORM | Item ownership, image handling |
| `services/openai_client.py` | GPT-4o Vision API call, parse structured JSON response | OpenAI SDK | Django models, HTTP request/response |
| `services/s3_helpers.py` | Presigned URL generation (if browser-direct upload ever needed) | boto3 | Django views directly |
| Django admin | Usage monitoring, user management, data inspection | All models via `admin.py` in each app | Business logic |

---

## Data Model Sketch

```python
# accounts/models.py
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    created_at = models.DateTimeField(auto_now_add=True)
    # extensible: add preferences, notification settings, etc.

# wardrobe/models.py
class WardrobeItem(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="wardrobe_items")
    name = models.CharField(max_length=200)
    item_photo = models.ImageField(upload_to="items/%Y/%m/")        # stored in S3 via django-storages
    care_label_photo = models.ImageField(upload_to="labels/%Y/%m/") # stored in S3 via django-storages
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class AnalysisResult(models.Model):
    item = models.OneToOneField(WardrobeItem, on_delete=models.CASCADE, related_name="analysis")
    # Structured fields parsed from GPT-4o response JSON
    wash_temperature = models.CharField(max_length=50)   # e.g. "cold", "warm", "hot"
    color_group = models.CharField(max_length=50)        # e.g. "whites", "darks", "colors"
    is_delicate = models.BooleanField(default=False)
    dry_clean_only = models.BooleanField(default=False)
    tumble_dry = models.BooleanField(default=True)
    raw_instructions = models.JSONField()                # full GPT-4o structured output preserved
    confidence_score = models.FloatField(null=True, blank=True)  # GPT-4o logprobs if available
    analyzed_at = models.DateTimeField(auto_now_add=True)
    gpt_model_version = models.CharField(max_length=50, default="gpt-4o")

class UsageLog(models.Model):
    """Tracks analysis calls per user per day for rate limiting."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="usage_logs")
    date = models.DateField(db_index=True)              # date only, not datetime
    analysis_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [("user", "date")]

    @classmethod
    def get_today_count(cls, user):
        from django.utils import timezone
        today = timezone.now().date()
        log, _ = cls.objects.get_or_create(user=user, date=today)
        return log.analysis_count

    @classmethod
    def increment(cls, user):
        from django.utils import timezone
        today = timezone.now().date()
        cls.objects.update_or_create(
            user=user, date=today,
            defaults={},
        )
        cls.objects.filter(user=user, date=today).update(
            analysis_count=models.F("analysis_count") + 1
        )

# laundry/models.py  — intentionally thin, basket is ephemeral
# No persistent Basket model: basket state is computed on demand from WardrobeItem + AnalysisResult.
# If persistence is later needed (saved baskets), add a LaundryBasket model here.
```

### Model Design Rationale

- `AnalysisResult` is `OneToOne` with `WardrobeItem` — each item has exactly one current analysis. Re-analysis overwrites the record. This simplifies queries and avoids orphan rows.
- `UsageLog` uses a `unique_together` on `(user, date)` so `get_or_create` is safe under concurrent requests. The `update()` with `F()` expression is atomic — no race condition on the count.
- Store structured fields as discrete columns (not only `JSONField`) so the basket grouping query can `filter(analysis__wash_temperature="cold")` without parsing JSON in Python.
- `raw_instructions = JSONField()` preserves the full GPT response for debugging and future re-parsing without re-calling the API.

---

## Data Flow

### Request/Response Cycle: Image Upload + Analysis

```
Browser (multipart form POST)
    │
    ▼
wardrobe/views.py :: AnalyzeItemView
    │  1. Authenticate user (LoginRequired mixin)
    │  2. Validate form (WardrobeItemForm)
    │  3. Check rate limit: UsageLog.get_today_count(user) >= 10 → 429 response
    │
    ▼
WardrobeItem.save()  ← django-storages intercepts ImageField.save()
    │  4. django-storages streams file bytes to S3
    │  5. Returns S3 URL → stored in WardrobeItem.item_photo / care_label_photo
    │
    ▼
services/openai_client.py :: analyze_care_label(item_photo_url, care_label_url)
    │  6. Build messages payload with image URLs (GPT-4o accepts S3 URLs directly
    │     if bucket is public, OR encode as base64 for private buckets)
    │  7. Call openai.chat.completions.create(model="gpt-4o", response_format="json_object")
    │  8. Parse JSON → validate required fields → raise AnalysisError if malformed
    │
    ▼
wardrobe/views.py (continued)
    │  9. AnalysisResult.objects.update_or_create(item=item, defaults={...parsed fields})
    │  10. UsageLog.increment(user)
    │  11. redirect("wardrobe:item-detail", pk=item.pk)
    │
    ▼
Browser (GET redirect → Django template renders results)
```

### Key Decision: Synchronous OpenAI Call

The project spec says no Celery. This means the OpenAI call blocks the HTTP worker for 3-15 seconds during analysis. This is acceptable with the following constraints:

- Gunicorn with `--workers=4` on Render: concurrent users are served by other workers while one waits on OpenAI.
- Set `OPENAI_TIMEOUT = 30` seconds. If OpenAI times out, catch the exception, show a user-facing error, do NOT increment the usage counter, and leave the item in an "unanalyzed" state.
- Add a `status` field to `WardrobeItem` (`choices: pending/analyzed/failed`) so the UI can show the correct state after a timeout.

```python
# WardrobeItem.status field (add to model)
class AnalysisStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    ANALYZED = "analyzed", "Analyzed"
    FAILED = "failed", "Analysis Failed"

status = models.CharField(
    max_length=20,
    choices=AnalysisStatus.choices,
    default=AnalysisStatus.PENDING,
)
```

---

## S3 Upload Flow

**Recommended: Server-side upload via django-storages (not presigned URLs)**

```
Browser → Django view → django-storages → S3
```

Rationale: The project is server-rendered with Django templates. Presigned URL uploads (browser-direct to S3) require JavaScript fetch calls and async handling — complexity that conflicts with the "no SPA" constraint. django-storages + boto3 is the standard Django-native approach.

### Configuration

```python
# config/settings/base.py

# django-storages with boto3
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "bucket_name": env("AWS_STORAGE_BUCKET_NAME"),
            "region_name": env("AWS_S3_REGION_NAME"),
            "access_key": env("AWS_ACCESS_KEY_ID"),
            "secret_key": env("AWS_SECRET_ACCESS_KEY"),
            "default_acl": "private",          # private bucket; use presigned URLs for display
            "file_overwrite": False,            # never overwrite; use UUID filenames
            "max_memory_size": 5 * 1024 * 1024, # 5MB in memory before temp file
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        # Keep static files local on Render, served via WhiteNoise
    },
}
```

### Private Bucket + Image Display

Use private S3 bucket. For displaying item photos in templates, generate presigned URLs in the view or template tag:

```python
# wardrobe/templatetags/s3_tags.py
import boto3
from django import template
register = template.Library()

@register.simple_tag
def presigned_url(s3_field, expiry=3600):
    """Generate a time-limited presigned URL for a private S3 object."""
    s3 = boto3.client("s3")
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.AWS_STORAGE_BUCKET_NAME, "Key": s3_field.name},
        ExpiresIn=expiry,
    )
```

For the GPT-4o call with a private bucket, pass the image as base64 instead of URL:

```python
# services/openai_client.py
import base64
import httpx

def _image_to_base64(s3_field) -> str:
    """Download image from S3 and encode as base64 for GPT-4o."""
    with s3_field.open("rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")
```

---

## Basket Grouping Logic

**Recommended: Pure Python function operating on in-memory QuerySet results**

```python
# laundry/grouping.py

from dataclasses import dataclass
from typing import List
from wardrobe.models import WardrobeItem

@dataclass
class LaundryLoad:
    name: str
    items: List[WardrobeItem]
    wash_temperature: str
    notes: str = ""

def group_into_loads(items: List[WardrobeItem]) -> List[LaundryLoad]:
    """
    Groups wardrobe items into compatible laundry loads.

    Rules (in priority order):
    1. Dry-clean-only items → separate load each (or flagged for manual handling)
    2. Delicates → cold, delicate cycle, grouped together regardless of color
    3. Whites → hot or warm, separate from colors
    4. Darks → cold, separate from lights
    5. Colors → warm, remaining items
    6. Temperature overrides color: if item needs cold, it joins the cold group
       even if color would suggest warm

    Args:
        items: WardrobeItem instances with prefetched .analysis

    Returns:
        List of LaundryLoad objects, ordered by recommendation priority
    """
    dry_clean = []
    delicates = []
    whites = []
    darks = []
    colors = []

    for item in items:
        if not hasattr(item, "analysis"):
            continue  # skip unanalyzed items
        a = item.analysis
        if a.dry_clean_only:
            dry_clean.append(item)
        elif a.is_delicate:
            delicates.append(item)
        elif a.color_group == "whites":
            whites.append(item)
        elif a.color_group == "darks":
            darks.append(item)
        else:
            colors.append(item)

    loads = []
    if dry_clean:
        loads.append(LaundryLoad("Dry Clean Only", dry_clean, "n/a", "Take to dry cleaner"))
    if delicates:
        loads.append(LaundryLoad("Delicates", delicates, "cold", "Gentle cycle, mesh bag recommended"))
    if whites:
        loads.append(LaundryLoad("Whites", whites, "warm", "Can use bleach if needed"))
    if darks:
        loads.append(LaundryLoad("Darks", darks, "cold", "Turn inside out"))
    if colors:
        loads.append(LaundryLoad("Colors", colors, "warm", ""))
    return loads
```

### Why Pure Python, Not a DB Query

- The grouping algorithm applies multi-factor logic (temperature + color + delicates, with priority overrides) that would require complex SQL with CASE expressions and ordering — harder to test, harder to change.
- A user's wardrobe is small (tens to low hundreds of items). Fetching all analyzed items for a user and grouping in Python is fast enough; no N+1 risk when using `select_related("analysis")`.
- Pure Python function is trivially unit-testable with mock `WardrobeItem` objects.
- The algorithm will change as the product evolves (e.g., adding fabric type). Python logic is far easier to modify than SQL.

```python
# laundry/views.py
def basket_view(request):
    items = (
        WardrobeItem.objects
        .filter(owner=request.user, status="analyzed")
        .select_related("analysis")  # single JOIN query, no N+1
    )
    loads = group_into_loads(list(items))
    return render(request, "laundry/basket.html", {"loads": loads})
```

---

## Patterns to Follow

### Pattern 1: Service Layer for External Calls

**What:** `services/openai_client.py` is a plain Python module, not a Django view or model method. It takes primitive inputs and returns a parsed dict.

**When:** Any time code touches an external API (OpenAI, S3, future integrations).

**Why:** Views and models stay testable without mocking HTTP. The service can be tested with recorded fixtures. Contributors know exactly where to find external integration code.

```python
# services/openai_client.py
def analyze_care_label(item_b64: str, label_b64: str) -> dict:
    """
    Call GPT-4o Vision and return structured care instructions.

    Returns:
        {
            "wash_temperature": "cold" | "warm" | "hot",
            "color_group": "whites" | "darks" | "colors",
            "is_delicate": bool,
            "dry_clean_only": bool,
            "tumble_dry": bool,
            "raw_instructions": dict,
        }

    Raises:
        AnalysisError: if OpenAI call fails or returns unparseable JSON
        openai.APITimeoutError: if request exceeds OPENAI_TIMEOUT
    """
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY, timeout=30.0)
    response = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,  # defined as module-level constant
            },
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{item_b64}"}},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{label_b64}"}},
                    {"type": "text", "text": "Analyze the care label and item. Return JSON."},
                ],
            },
        ],
    )
    raw = json.loads(response.choices[0].message.content)
    return _validate_and_normalize(raw)  # raises AnalysisError if fields missing
```

### Pattern 2: Fat Models, Thin Views

**What:** Business logic (rate limit check, usage tracking) lives on model managers or model classmethods. Views orchestrate the sequence but contain no logic.

**When:** Always.

**Example:** `UsageLog.get_today_count(user)` and `UsageLog.increment(user)` on the model, called from the view.

### Pattern 3: Environment-Split Settings

**What:** `config/settings/base.py` → `development.py` and `production.py` inherit from base.

**When:** From day one — prevents accidentally running debug mode in production on Render.

```python
# development.py
from .base import *
DEBUG = True
DATABASES = {"default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3")}
STORAGES = {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}}
# Use local storage in dev — no S3 needed for local development

# production.py
from .base import *
DEBUG = False
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")
# S3 storages from base.py apply
```

### Pattern 4: Django Admin for Monitoring (Zero Extra Code)

Register all models in `admin.py` with useful `list_display`. This covers the "usage monitoring" requirement with no custom dashboard needed.

```python
# wardrobe/admin.py
@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ["user", "date", "analysis_count"]
    list_filter = ["date"]
    ordering = ["-date", "-analysis_count"]
    date_hierarchy = "date"
```

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Calling OpenAI from the Model's `save()` Method

**What:** Overriding `WardrobeItem.save()` to trigger the GPT-4o call.

**Why bad:** `save()` is called in tests, fixtures, admin actions, migrations, shell sessions. A live OpenAI HTTP call in `save()` will break every test that creates a `WardrobeItem`, make fixtures slow, and cause mysterious failures. You cannot control when `save()` fires.

**Instead:** Call `services.openai_client.analyze_care_label()` explicitly in the view after the model is saved. The call is visible, intentional, and skippable in tests.

### Anti-Pattern 2: Storing Only JSONField for Analysis Results

**What:** Saving the entire GPT-4o JSON blob in one `JSONField` and querying it with `filter(analysis__data__wash_temperature="cold")`.

**Why bad:** Django JSONField lookups work but are slow (no index), DB-specific (PostgreSQL's `@>` operator), and break if GPT-4o changes its output schema. The basket grouping algorithm would need to parse JSON in Python anyway.

**Instead:** Parse GPT-4o output into discrete typed columns at save time. Store `raw_instructions = JSONField()` as an immutable audit log.

### Anti-Pattern 3: One Monolithic Django App

**What:** Putting all models, views, and logic in a single app (e.g., `core/`).

**Why bad:** On a team project, multiple contributors editing the same `models.py`, `views.py`, and `urls.py` causes constant merge conflicts. Django's migration system creates a single migration sequence per app — one monolithic app serializes all DB changes.

**Instead:** Three apps as described above. Each contributor can own one app.

### Anti-Pattern 4: Hardcoded Rate Limit in View Logic

**What:** `if usage_count >= 10: return HttpResponseForbidden(...)` scattered in multiple views.

**Why bad:** Rate limit value is not configurable; if you change the limit, you find it scattered. Multiple views means multiple places to update.

**Instead:** Extract to a decorator or mixin, read limit from `settings.ANALYSIS_RATE_LIMIT_PER_DAY = 10`.

```python
# wardrobe/decorators.py
def analysis_rate_limit(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        limit = getattr(settings, "ANALYSIS_RATE_LIMIT_PER_DAY", 10)
        if UsageLog.get_today_count(request.user) >= limit:
            return render(request, "wardrobe/rate_limited.html", status=429)
        return view_func(request, *args, **kwargs)
    return wrapper
```

---

## Scalability Considerations

| Concern | At 100 users | At 10K users | At 1M users |
|---------|--------------|--------------|-------------|
| OpenAI latency blocking workers | 4 Gunicorn workers sufficient | Workers saturate; add Celery task queue | Celery + Redis required |
| S3 uploads blocking workers | Acceptable (fast network) | Consider client-side presigned uploads | Direct browser-to-S3 required |
| Rate limit DB query | Trivial | Add DB index on `(user, date)` (already via unique_together) | Redis counter preferred |
| Basket grouping | Pure Python, fast | Pure Python still fast (items per user bounded) | Still Python; add caching if wardrobe sizes grow |
| PostgreSQL | Render starter tier | Render standard tier, add connection pooling (pgBouncer) | Managed RDS + read replicas |

---

## Suggested Build Order

Dependencies determine the sequence. Each phase must complete before the next starts.

```
Phase 1: Project Scaffolding + Auth
    ├── Django project created, settings split (base/dev/prod)
    ├── PostgreSQL connected (dev: SQLite, prod: Render PostgreSQL)
    ├── accounts app: User, UserProfile models
    ├── Django auth views wired (login, logout, register)
    └── Base template + nav
         ↓ REQUIRED BEFORE: everything (auth gates all views)

Phase 2: Wardrobe CRUD + S3 Upload (no analysis yet)
    ├── wardrobe app: WardrobeItem model, migrations
    ├── django-storages + boto3 configured
    ├── Item create/list/detail/delete views (status=PENDING)
    ├── Image upload working (S3 in prod, local in dev)
    └── django-admin registered
         ↓ REQUIRED BEFORE: analysis (need items to analyze)

Phase 3: Analysis Pipeline
    ├── AnalysisResult model + UsageLog model, migrations
    ├── services/openai_client.py: GPT-4o Vision call
    ├── Analysis view (POST → analyze → save results → redirect)
    ├── Rate limit decorator applied to analysis view
    ├── Error states: timeout, API error, unanalyzed items
    └── Item detail shows analysis results
         ↓ REQUIRED BEFORE: basket (need analysis data to group)

Phase 4: Laundry Basket
    ├── laundry app: basket view
    ├── grouping.py: group_into_loads() pure Python function
    ├── Basket template showing loads with items
    └── "Add to basket" / "Remove from basket" selection UI
         ↓ REQUIRED BEFORE: nothing (terminal phase)

Phase 5: Polish + Deployment
    ├── WhiteNoise for static files on Render
    ├── render.yaml / Procfile configured
    ├── Environment variables on Render dashboard
    ├── Django admin usage monitoring finalized
    └── Error pages (404, 500, 429)
```

### Critical Build Order Rule

**Never build Phase 3 (analysis) before Phase 2 (items exist).** The OpenAI call needs real S3 URLs to images. Testing the analysis pipeline against placeholder images leads to prompt engineering tuned to test data, not real photos.

**Never build Phase 4 (basket) before Phase 3 (analysis results exist).** The grouping algorithm needs `AnalysisResult` rows. Without data, it cannot be validated against real garment diversity.

---

## Render Deployment Notes

```yaml
# render.yaml
services:
  - type: web
    name: wardrobe-wise
    env: python
    buildCommand: "pip install -r requirements/production.txt && python manage.py collectstatic --noinput && python manage.py migrate"
    startCommand: "gunicorn config.wsgi:application --workers 4 --timeout 60"
    envVars:
      - key: DJANGO_SETTINGS_MODULE
        value: config.settings.production
      - key: SECRET_KEY
        sync: false
      - key: DATABASE_URL
        fromDatabase:
          name: wardrobe-wise-db
          property: connectionString
      - key: AWS_ACCESS_KEY_ID
        sync: false
      - key: AWS_SECRET_ACCESS_KEY
        sync: false
      - key: AWS_STORAGE_BUCKET_NAME
        sync: false
      - key: OPENAI_API_KEY
        sync: false

databases:
  - name: wardrobe-wise-db
    databaseName: wardrobe-wise
    user: wardrobe-wise
```

Key Render constraints:
- `--timeout 60` on Gunicorn covers the ~30s OpenAI call plus buffer. Default is 30s which will kill the worker during analysis.
- `collectstatic` runs in build command, not start command. Static files served by WhiteNoise — no Nginx needed.
- Render's ephemeral filesystem means local file uploads are lost on deploy. S3 is not optional for production.

---

## Sources

- Django documentation: application design and project structure patterns (HIGH confidence — standard Django conventions, stable since Django 3.0)
- django-storages S3Boto3Storage documentation, v1.14+ `STORAGES` dict configuration (HIGH confidence — `STORAGES` dict replaced `DEFAULT_FILE_STORAGE` string in Django 4.2)
- OpenAI API: `gpt-4o` vision capabilities, `response_format={"type": "json_object"}`, base64 image encoding (HIGH confidence — stable API pattern as of August 2025)
- Render platform: `render.yaml` schema, Gunicorn worker configuration, ephemeral filesystem behavior (HIGH confidence)
- Django `F()` expressions for atomic counter increments: Django ORM documentation (HIGH confidence)
- Note: WebSearch and WebFetch were unavailable during this research session. All findings are based on training data through August 2025. Django 5.1 and django-storages 1.14 patterns are confirmed current as of training cutoff. Verify django-storages `STORAGES` dict configuration syntax against current docs before implementation.
