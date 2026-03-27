# Phase 3: Care Label Analysis Pipeline - Research

**Researched:** 2026-03-27
**Domain:** OpenAI Vision API + Django rate-limiting + image deduplication + admin observability
**Confidence:** HIGH (core patterns), MEDIUM (model identifier recommendation — verify at implementation time)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Result display
- Simple bullet-point list format — no cards, no sections, no icons
- Displayed inline on the garment detail page (not a separate page)
- Structured as: AI-generated summary sentence first, then bullet list
- Warnings and prohibitions styled with visual distinction (different color or warning icon)
- Unknown/unclear fields shown as: "Ironing: Unable to determine — check label manually" (not omitted)
- Delicates flag shown as a warning badge near the instructions section (when true)
- Small care label thumbnail shown alongside the instructions section for cross-reference
- Analysis timestamp shown: "Analyzed 2 days ago" style
- If same care label submitted again (dedup hit): subtle muted note below timestamp — "(from previous analysis)"
- If analysis fails: inline error with Retry button in the care instructions section
- Pre-analysis placeholder: "No care instructions yet. Upload a care label photo and click Analyze to get started." with Analyze button nearby
- No distinction between AI-original and user-edited instructions in read mode
- Raw JSON stored immutably — admin only, never shown to users
- AI caveats not surfaced to users — clean results only
- No action buttons beyond Edit and Re-analyze (no copy, share, print)
- Analysis badge on wardrobe grid: analyzed garments show a visual indicator badge
- Instructions section sits below garment fields on the detail page

#### Analysis flow & trigger
- Analyze button lives on the garment detail page — not on the wardrobe grid
- Single-step flow: create garment → save → on detail page, click "Analyze Care Label"
- Button label: "Analyze Care Label"
- Button is disabled (with tooltip) if no care label photo exists
- Loading state: button shows spinner + "Analyzing..." — page stays in place
- Synchronous call — page waits, then reloads to show results (no HTMX, standard POST)
- When rate-limited (10/10): Analyze button is hidden/replaced by the rate limit message inline
- When global budget guard hit: Analyze button replaced by "Analysis temporarily unavailable" message
- No confirmation step before triggering — direct action
- Daily limit and budget guard show different messages

#### Edit experience
- Edit triggered by "Edit Instructions" button on the detail page
- Edit form replaces the instructions section in-place on the same page
- Per-field inputs for each of the 5 structured fields (washing, drying, ironing, bleach, delicates)
- Delicates flag is a checkbox in the edit form (user-editable)
- Unknown fields appear pre-filled with "Unable to determine" text — user replaces as needed
- Additional "Personal notes" free-text field for custom instructions beyond the 5 AI fields
- Care label thumbnail is shown alongside the edit form for reference
- "Reset to AI version" button in the edit form to restore original AI-generated text
- "Cancel" button to discard edits and return to read-only view
- "Save" posts the form; on success: page reloads detail view with flash "Instructions updated"
- "Delete Analysis" option (with confirmation) available — resets garment back to pre-analysis state
- Re-analyze button available after analysis exists
- If user has edited instructions and clicks Re-analyze: confirmation dialog warns "Re-analyzing will replace your edited instructions. Continue?"

#### Rate limit UI
- Daily counter "X / 10 today" displayed in site-wide navigation — visible only on analysis-relevant pages (wardrobe grid, garment detail)
- Counter always visible (shows "0 / 10 today" from the start of each day)
- Counter is color-coded: normal → warning color approaching limit → red/blocked when 10/10 hit
- Page reload updates the counter naturally (consistent with synchronous POST approach)
- When limit hit: inline block near Analyze button area: "Daily limit reached (10/10). Resets in [countdown]."
- Countdown is a live timer counting down to the user's local midnight
- Flash message on first page load after midnight reset: "Your daily analysis allowance has reset — 10 analyses available today."
- Daily limit message and budget guard message are distinct

### Claude's Discretion
- Exact color thresholds for warning/red states on the counter
- Specific styling of the Delicate warning badge
- Exact error message copy for disabled Analyze button (no care label tooltip)
- Layout/spacing of the edit form fields
- Loading spinner style during Analyze button loading state

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

## Summary

This phase adds an AI analysis layer on top of the Phase 2 wardrobe. The primary technical challenge is integrating the OpenAI Vision API synchronously (no Celery), storing results in a structured way that separates immutable AI output from user edits, and enforcing rate limits and a budget guard using the DB (required because Render restarts kill in-memory state).

The OpenAI piece is straightforward: use `client.chat.completions.create()` with the Chat Completions API, pass the care label image as a base64-encoded data URI (not an S3 URL — presigned URLs have documented failures with GPT-4o; public S3 URLs are fine but base64 is the most reliable path), and request structured JSON output via `response_format={"type": "json_object"}`. Store `response.usage.prompt_tokens + completion_tokens` to track cost.

The Django architecture centers on two new models: `CareAnalysis` (one per garment, holds both raw AI JSON and user-edited fields) and `UsageLog` (one row per API call, used for both rate limiting and cost accumulation). Rate limiting uses a DB COUNT query filtered to today's date — this is intentionally simple and Render-restart-safe. The budget guard reads the SUM of all `cost_usd` rows against a $9.00 threshold. Image deduplication uses a SHA-256 content hash stored on the `CareAnalysis`; on re-analyze, a matching hash returns the cached result instantly.

The nav counter ("X / 10 today") is a DB query that must avoid running on every page. Attach it via a context processor that checks `request.resolver_match.app_name` to limit it to the `wardrobe` namespace only, and use `functools.lru_cache` or store the count on the request object to avoid duplicate queries per render.

**Primary recommendation:** Use `gpt-4o` (alias) or the pinned snapshot `gpt-4o-2024-11-20` for all vision calls. Verify current availability on `platform.openai.com/docs/models` at implementation time — model naming is fast-moving.

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `openai` | `>=2.30,<3.0` | Official OpenAI Python SDK | Vendor-maintained, typed, sync client included |
| Django | `5.2` (already installed) | Framework | Already the project stack |
| `Pillow` | `>=10.0,<12.0` (already installed) | Read image bytes for base64 encoding | Already a project dependency |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `hashlib` (stdlib) | built-in | SHA-256 content hash for dedup | No install needed |
| `base64` (stdlib) | built-in | Encode image bytes for API call | No install needed |
| `decimal.Decimal` | built-in | Finance-safe cost accumulation | Use for all USD math, never float |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `response_format={"type":"json_object"}` | Pydantic structured outputs (`json_schema`) | `json_schema` enforces schema strictly but is more complex to set up; `json_object` is sufficient here since we validate fields ourselves |
| DB-backed rate limit (UsageLog COUNT) | `django-ratelimit` (cache-backed) | Cache resets on Render restart, making it unsafe; DB is restart-safe by design |
| SHA-256 content hash | Perceptual hash (ImageHash library) | Perceptual hash catches near-duplicates/resizes; SHA-256 is exact match only — sufficient since we control the upload path |
| Base64 image encoding | Public S3 URL via `image_url` | S3 public URLs work (querystring_auth=False already), but base64 is more reliable and avoids any future ACL issues |

**Installation:**
```bash
pip install "openai>=2.30,<3.0"
```

---

## Architecture Patterns

### Recommended Project Structure

The analysis feature belongs in the existing `wardrobe` app — it is tightly coupled to the `Garment` model. No new Django app needed.

```
wardrobe/
├── models.py          # Add CareAnalysis, UsageLog models
├── views.py           # Add analyze_care_label view, edit_instructions view
├── forms.py           # Add CareInstructionsEditForm
├── urls.py            # Add /wardrobe/<pk>/analyze/, /wardrobe/<pk>/instructions/edit/
├── admin.py           # Register CareAnalysis, UsageLog with read-only JSON display
├── services/
│   └── analysis.py    # OpenAI call, cost calc, dedup logic (pure functions, no HTTP side effects)
└── context_processors.py  # daily_usage_counter (wardrobe-namespace only)
```

### Pattern 1: CareAnalysis Model

**What:** One-to-one relationship to `Garment`. Stores both the immutable raw JSON and the user-editable structured fields separately. The `is_user_edited` flag lets the Reset to AI button know the original values.

```python
class CareAnalysis(models.Model):
    garment = models.OneToOneField(
        'wardrobe.Garment',
        on_delete=models.CASCADE,
        related_name='care_analysis',
    )
    # Deduplication
    image_hash = models.CharField(max_length=64, db_index=True)

    # Immutable AI output — never updated after creation
    raw_ai_json = models.JSONField()           # full GPT response dict
    ai_washing = models.TextField()
    ai_drying = models.TextField()
    ai_ironing = models.TextField()
    ai_bleach = models.TextField()
    ai_is_delicate = models.BooleanField(default=False)
    ai_summary = models.TextField()

    # User-editable copy (starts as a copy of ai_* fields)
    washing = models.TextField()
    drying = models.TextField()
    ironing = models.TextField()
    bleach = models.TextField()
    is_delicate = models.BooleanField(default=False)
    summary = models.TextField()
    personal_notes = models.TextField(blank=True)
    is_user_edited = models.BooleanField(default=False)

    analyzed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Dedup source flag
    from_cache = models.BooleanField(default=False)
```

### Pattern 2: UsageLog Model

**What:** One row per API call. Used for both daily rate limiting (COUNT by user + date) and cumulative budget guard (SUM of cost_usd).

```python
class UsageLog(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='usage_logs',
    )
    garment = models.ForeignKey(
        'wardrobe.Garment',
        on_delete=models.SET_NULL,
        null=True,
        related_name='usage_logs',
    )
    prompt_tokens = models.IntegerField()
    completion_tokens = models.IntegerField()
    cost_usd = models.DecimalField(max_digits=10, decimal_places=8)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at']),  # for budget guard SUM
        ]
```

**Daily count query (rate limiting):**
```python
from django.utils import timezone

today = timezone.now().date()
count = UsageLog.objects.filter(
    user=request.user,
    created_at__date=today,
).count()
```

**Cumulative cost query (budget guard):**
```python
from django.db.models import Sum
from decimal import Decimal

total = UsageLog.objects.aggregate(
    total=Sum('cost_usd')
)['total'] or Decimal('0')
BUDGET_GUARD_THRESHOLD = Decimal('9.00')
budget_exceeded = total >= BUDGET_GUARD_THRESHOLD
```

### Pattern 3: OpenAI Vision API Call

**What:** Read the care label image from storage, encode to base64, call Chat Completions API with structured JSON prompt.

```python
# Source: openai-python README + OpenAI vision docs
import base64
import hashlib
from openai import OpenAI

client = OpenAI()  # reads OPENAI_API_KEY from env

def compute_image_hash(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()

def call_vision_api(image_bytes: bytes, fabric_hint: str = "") -> dict:
    b64 = base64.b64encode(image_bytes).decode('utf-8')

    system_prompt = """You are a laundry care expert. Analyze the care label in the image.
Return a JSON object with exactly these fields:
- summary: one plain-English sentence summarising how to care for this item
- washing: wash temperature/cycle instruction (or "Unable to determine")
- drying: drying method instruction (or "Unable to determine")
- ironing: ironing guidance (or "Unable to determine")
- bleach: bleach instruction, including any prohibition (or "Unable to determine")
- is_delicate: true if the item requires special/delicate care, false otherwise
Do not include any caveats about label quality. Return clean, direct instructions only."""

    response = client.chat.completions.create(
        model="gpt-4o",          # or pinned: "gpt-4o-2024-11-20"
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"Analyze this care label.{' Fabric: ' + fabric_hint if fabric_hint else ''}"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            },
        ],
        max_tokens=500,
    )
    return response
```

**Cost calculation from response:**
```python
import json
from decimal import Decimal

# GPT-4o pricing (verify at: platform.openai.com/docs/pricing)
# As of Jan 2026: $2.50 / 1M input tokens, $10.00 / 1M output tokens
INPUT_COST_PER_TOKEN = Decimal('0.0000025')
OUTPUT_COST_PER_TOKEN = Decimal('0.00001')

def calculate_cost(usage) -> Decimal:
    return (
        Decimal(usage.prompt_tokens) * INPUT_COST_PER_TOKEN +
        Decimal(usage.completion_tokens) * OUTPUT_COST_PER_TOKEN
    )

parsed = json.loads(response.choices[0].message.content)
cost = calculate_cost(response.usage)
```

### Pattern 4: Analysis Service Function

**What:** Single entry-point function in `wardrobe/services/analysis.py`. Encapsulates dedup check, budget guard, API call, and UsageLog creation. Views call this; it raises specific exceptions for rate limit and budget violations.

```python
class RateLimitExceeded(Exception): pass
class BudgetGuardTripped(Exception): pass
class AnalysisError(Exception): pass

def analyze_care_label(garment, user) -> CareAnalysis:
    """
    Returns existing CareAnalysis (from cache) or creates new one.
    Raises RateLimitExceeded, BudgetGuardTripped, or AnalysisError.
    """
    # 1. Budget guard (global)
    if _budget_exceeded():
        raise BudgetGuardTripped()

    # 2. Rate limit (per user, per day)
    if _daily_count(user) >= 10:
        raise RateLimitExceeded()

    # 3. Read image bytes
    image_bytes = garment.care_label_photo.read()
    image_hash = compute_image_hash(image_bytes)

    # 4. Dedup check
    existing = CareAnalysis.objects.filter(image_hash=image_hash).first()
    if existing:
        # Return a copy linked to this garment, marked from_cache=True
        # (or update the garment's existing analysis if one exists)
        ...

    # 5. Call API
    try:
        response = call_vision_api(image_bytes, fabric_hint=garment.fabric)
    except Exception as e:
        raise AnalysisError(str(e)) from e

    # 6. Parse & save
    ...
    # 7. Log usage (only for real API calls, not dedup hits)
    UsageLog.objects.create(user=user, garment=garment, ...)
    return analysis
```

### Pattern 5: Analyze View

**What:** `POST /wardrobe/<pk>/analyze/` — validates preconditions, calls service, redirects to detail page. Uses Django messages framework for errors.

```python
@login_required
@require_POST
def analyze_care_label_view(request, pk):
    garment = get_object_or_404(Garment, pk=pk, user=request.user)
    try:
        analyze_care_label(garment, request.user)
        messages.success(request, "Care instructions analyzed successfully.")
    except RateLimitExceeded:
        messages.error(request, "daily_limit_reached")  # template key, not shown raw
    except BudgetGuardTripped:
        messages.error(request, "budget_guard_tripped")
    except AnalysisError as e:
        messages.error(request, f"analysis_failed:{e}")
    return redirect('wardrobe:garment_detail', pk=pk)
```

### Pattern 6: Nav Counter via Context Processor (wardrobe-namespace only)

**What:** Injects `daily_usage_count` and `daily_usage_limit` into template context only on wardrobe pages, avoiding a DB query on every page render.

```python
# wardrobe/context_processors.py
from django.utils import timezone
from wardrobe.models import UsageLog

def daily_usage_counter(request):
    if not request.user.is_authenticated:
        return {}
    # Only inject on wardrobe namespace pages
    try:
        if request.resolver_match.app_name != 'wardrobe':
            return {}
    except AttributeError:
        return {}

    today = timezone.now().date()
    count = UsageLog.objects.filter(
        user=request.user,
        created_at__date=today,
    ).count()
    return {
        'daily_usage_count': count,
        'daily_usage_limit': 10,
    }
```

Register in `settings/base.py` under `TEMPLATES[0]['OPTIONS']['context_processors']`.

### Pattern 7: Midnight Countdown Timer (vanilla JS)

**What:** Client-side countdown to user's local midnight. No library needed — `Date` in JS uses browser local timezone by default.

```javascript
function getMsUntilMidnight() {
    const now = new Date();
    const midnight = new Date(now);
    midnight.setHours(24, 0, 0, 0);  // next midnight in local time
    return midnight - now;
}

function formatCountdown(ms) {
    const totalSeconds = Math.floor(ms / 1000);
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = totalSeconds % 60;
    return `${h}h ${m}m ${s}s`;
}

function startCountdown(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    function tick() {
        const ms = getMsUntilMidnight();
        el.textContent = formatCountdown(ms);
        setTimeout(tick, 1000);
    }
    tick();
}
```

### Pattern 8: Django Admin for Audit Log

**What:** Register `CareAnalysis` and `UsageLog` with read-only JSON pretty-printing. No modifications allowed in admin for immutable records.

```python
# wardrobe/admin.py
import json
from django.contrib import admin
from django.utils.html import format_html
from wardrobe.models import CareAnalysis, UsageLog

@admin.register(CareAnalysis)
class CareAnalysisAdmin(admin.ModelAdmin):
    list_display = ('garment', 'garment__user', 'analyzed_at', 'from_cache', 'is_user_edited')
    list_filter = ('from_cache', 'is_user_edited', 'is_delicate')
    readonly_fields = ('garment', 'image_hash', 'raw_ai_json_pretty',
                       'analyzed_at', 'updated_at', 'from_cache')
    search_fields = ('garment__name', 'garment__user__email')

    def raw_ai_json_pretty(self, obj):
        formatted = json.dumps(obj.raw_ai_json, indent=2)
        return format_html('<pre style="white-space:pre-wrap">{}</pre>', formatted)
    raw_ai_json_pretty.short_description = 'Raw AI JSON'

@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'garment', 'prompt_tokens', 'completion_tokens', 'cost_usd', 'created_at')
    list_filter = ('created_at',)
    readonly_fields = ('user', 'garment', 'prompt_tokens', 'completion_tokens', 'cost_usd', 'created_at')
    search_fields = ('user__email',)

    def has_add_permission(self, request): return False
    def has_change_permission(self, request, obj=None): return False
    def has_delete_permission(self, request, obj=None): return False
```

### Anti-Patterns to Avoid

- **Storing the S3 URL in `image_url` for the API call:** S3 presigned URLs cause documented `invalid_image` errors with GPT-4o. Public S3 URLs (querystring_auth=False, which this project already uses) work, but base64 is more reliable and works regardless of bucket ACL.
- **Using Python `float` for cost math:** Always use `Decimal`. Float arithmetic accumulates error — a $9.00 budget guard computed with floats will misfire.
- **Running the nav counter context processor on all pages:** Context processors run on every request. Limit to wardrobe namespace via `request.resolver_match.app_name` check.
- **Cache-backed rate limiting:** `django-ratelimit` uses Django's cache backend. Render restarts clear in-memory cache. DB-backed COUNT is the correct choice here.
- **Using `chatgpt-4o-latest` as the model identifier:** This alias was removed from the API on February 17, 2026. Use `gpt-4o` (rolling alias) or a pinned dated snapshot.
- **Calling `garment.care_label_photo.read()` multiple times:** `FieldFile.read()` is a file stream — it can only be read once per open. Read into a variable immediately and reuse the bytes.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON field pretty-print in admin | Custom template | `format_html('<pre>...</pre>')` + `json.dumps(indent=2)` in a `readonly_fields` method | Simon Willison's pattern — 10 lines, zero deps |
| DB-backed rate limit counter | Custom locking scheme | `UsageLog.objects.filter(user, date).count()` | Django ORM COUNT is atomic-read-safe; no row-lock needed for read-only counting |
| Race condition on rate limit | Hand-rolled mutex | The check-then-insert pattern is good enough for 10/day limit — the worst case is one extra API call slipping through, not a security exploit | Simplicity wins; this is not a financial transaction |
| Cost accumulation | External cost-tracking service | `UsageLog.objects.aggregate(Sum('cost_usd'))` | Single SQL query; no external service needed at this scale |

**Key insight:** At 10 calls/day/user the rate limit race window is negligible. A strict read-then-write lock (select_for_update) is correct but adds transaction overhead not warranted here. Document the decision in code comments.

---

## Common Pitfalls

### Pitfall 1: Model Identifier Staleness
**What goes wrong:** You write `model="gpt-4o-2024-08-06"` and it works in dev, then OpenAI deprecates that snapshot later, breaking production silently.
**Why it happens:** OpenAI deprecates dated snapshots over time.
**How to avoid:** Use `"gpt-4o"` rolling alias OR use the most recent dated snapshot AND set a reminder to verify at `platform.openai.com/docs/models` before each deploy.
**Warning signs:** `model_not_found` error in logs; pricing page showing no entry for the identifier.

### Pitfall 2: FieldFile Stream Read-Once
**What goes wrong:** `garment.care_label_photo.read()` returns empty bytes the second time.
**Why it happens:** Django's `FieldFile` wraps a file-like object. After `.read()`, the pointer is at EOF.
**How to avoid:** `image_bytes = garment.care_label_photo.read()` once, pass `image_bytes` everywhere. Never call `.read()` again.
**Warning signs:** Base64 encoding produces an empty string; API returns error about invalid image.

### Pitfall 3: JSONField vs TextField for Raw AI Output
**What goes wrong:** Storing `response.choices[0].message.content` as-is in a `TextField` — this is already a JSON string, but querying it later requires `json.loads()` everywhere.
**Why it happens:** The API returns a string; it's tempting to store it directly.
**How to avoid:** Parse to dict first (`json.loads(...)`), store in `JSONField`. Django's `JSONField` handles serialization automatically.
**Warning signs:** `TypeError: string indices must be integers` when reading `raw_ai_json['summary']` in admin.

### Pitfall 4: Context Processor DB Query on All Pages
**What goes wrong:** Daily usage counter runs a DB query on every page — admin pages, login page, error pages.
**Why it happens:** Context processors have no built-in page-scope filtering.
**How to avoid:** Check `request.resolver_match.app_name == 'wardrobe'` before executing the query. Return `{}` early for all other namespaces.
**Warning signs:** Django Debug Toolbar shows an extra query on every page load.

### Pitfall 5: Midnight Reset Logic in UTC vs Local Time
**What goes wrong:** Django's `timezone.now().date()` returns UTC date. A user in UTC-5 who analyzes a garment at 11pm local (= 4am UTC next day) gets a fresh 0/10 count in Django's rate limit check but sees "0 / 10 today" in their browser — confusing.
**Why it happens:** Django stores datetimes in UTC; daily reset is defined as "user's local midnight."
**How to avoid:** The context decides midnight = user's local timezone. For the rate limit DB query, filter on UTC date (keeps it simple and consistent). For the countdown timer display, use the user's browser JS (which uses local time). Accept a small discrepancy: the "resets at midnight" message means local midnight, but the actual DB reset happens at the UTC midnight. Document this limitation. If exact local-midnight reset is required, store timezone on the user model — but that is out of scope for this phase.
**Warning signs:** Users complaining the counter doesn't reset at their midnight.

### Pitfall 6: Dedup Returns Wrong Garment's Analysis
**What goes wrong:** Image hash matches an analysis that belongs to a different user's garment. The dedup naively returns that result, leaking another user's data.
**Why it happens:** The hash is stored globally, not per-user.
**How to avoid:** On a dedup hit, copy the AI field values to create a NEW `CareAnalysis` for this garment, marked `from_cache=True`. Never return a foreign-user `CareAnalysis` instance directly.
**Warning signs:** Garment detail page shows another garment's name in the analysis.

### Pitfall 7: Re-analyze Does Not Delete Old UsageLog
**What goes wrong:** Re-analyzing a garment creates a new `UsageLog` entry but the old `CareAnalysis` is overwritten. Historical usage is preserved in `UsageLog` (correct), but the old `CareAnalysis.raw_ai_json` is lost.
**Why it happens:** `CareAnalysis` is one-to-one with `Garment` — updating it overwrites the old AI output.
**How to avoid:** On re-analyze, create a NEW `CareAnalysis` record (delete + recreate, or use `update_or_create` with the raw fields reset). The `UsageLog` accumulates naturally. The requirement says raw JSON is stored immutably — this means don't silently overwrite; on re-analyze, the previous raw JSON is gone by design (acceptable per context decisions).
**Warning signs:** Audit log shows more API calls than existing `CareAnalysis` records — this is expected and correct.

---

## Code Examples

### Full analyze_care_label service skeleton

```python
# wardrobe/services/analysis.py
import base64
import hashlib
import json
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from openai import OpenAI
from wardrobe.models import CareAnalysis, UsageLog

INPUT_COST_PER_TOKEN = Decimal('0.0000025')   # $2.50 / 1M — verify before deploy
OUTPUT_COST_PER_TOKEN = Decimal('0.00001')    # $10.00 / 1M — verify before deploy
DAILY_LIMIT = 10
BUDGET_GUARD_USD = Decimal('9.00')

client = OpenAI()  # OPENAI_API_KEY read from environment

class RateLimitExceeded(Exception): pass
class BudgetGuardTripped(Exception): pass
class AnalysisError(Exception): pass

def _daily_count(user) -> int:
    today = timezone.now().date()
    return UsageLog.objects.filter(user=user, created_at__date=today).count()

def _budget_exceeded() -> bool:
    from django.db.models import Sum
    total = UsageLog.objects.aggregate(t=Sum('cost_usd'))['t'] or Decimal('0')
    return total >= BUDGET_GUARD_USD

def _image_hash(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()

def _call_api(image_bytes: bytes, fabric_hint: str = "") -> tuple[dict, object]:
    """Returns (parsed_dict, usage_object)."""
    b64 = base64.b64encode(image_bytes).decode('utf-8')
    system = (
        "You are a laundry care expert. Analyze the care label image. "
        "Return a JSON object with keys: summary, washing, drying, ironing, bleach, is_delicate. "
        "For unknown fields use the string 'Unable to determine'. "
        "is_delicate must be boolean. No caveats or uncertainty text."
    )
    user_text = "Analyze this care label."
    if fabric_hint:
        user_text += f" Fabric: {fabric_hint}."
    resp = client.chat.completions.create(
        model="gpt-4o",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
            ]},
        ],
        max_tokens=500,
    )
    parsed = json.loads(resp.choices[0].message.content)
    return parsed, resp.usage

def analyze_care_label(garment, user) -> CareAnalysis:
    if _budget_exceeded():
        raise BudgetGuardTripped()
    if _daily_count(user) >= DAILY_LIMIT:
        raise RateLimitExceeded()

    image_bytes = garment.care_label_photo.read()
    img_hash = _image_hash(image_bytes)

    # Dedup: check if this exact image was analyzed before (any user)
    cached = CareAnalysis.objects.filter(image_hash=img_hash).first()
    if cached and cached.garment == garment:
        # Same garment, same image — mark from_cache and return
        cached.from_cache = True
        cached.save(update_fields=['from_cache'])
        return cached

    if cached and cached.garment != garment:
        # Different garment with same image — copy AI fields to new record
        parsed = {k: getattr(cached, f'ai_{k}') for k in ('washing','drying','ironing','bleach','summary')}
        parsed['is_delicate'] = cached.ai_is_delicate
        parsed['raw_ai_json'] = cached.raw_ai_json
        from_cache = True
        usage = None
    else:
        # Fresh API call
        try:
            parsed, usage = _call_api(image_bytes, fabric_hint=garment.fabric)
        except Exception as exc:
            raise AnalysisError(str(exc)) from exc
        parsed['raw_ai_json'] = parsed.copy()
        from_cache = False

    with transaction.atomic():
        # Delete existing analysis for this garment (re-analyze case)
        CareAnalysis.objects.filter(garment=garment).delete()
        analysis = CareAnalysis.objects.create(
            garment=garment,
            image_hash=img_hash,
            raw_ai_json=parsed.get('raw_ai_json', parsed),
            ai_summary=parsed.get('summary', ''),
            ai_washing=parsed.get('washing', ''),
            ai_drying=parsed.get('drying', ''),
            ai_ironing=parsed.get('ironing', ''),
            ai_bleach=parsed.get('bleach', ''),
            ai_is_delicate=bool(parsed.get('is_delicate', False)),
            summary=parsed.get('summary', ''),
            washing=parsed.get('washing', ''),
            drying=parsed.get('drying', ''),
            ironing=parsed.get('ironing', ''),
            bleach=parsed.get('bleach', ''),
            is_delicate=bool(parsed.get('is_delicate', False)),
            from_cache=from_cache,
        )
        if usage:
            cost = (
                Decimal(usage.prompt_tokens) * INPUT_COST_PER_TOKEN
                + Decimal(usage.completion_tokens) * OUTPUT_COST_PER_TOKEN
            )
            UsageLog.objects.create(
                user=user,
                garment=garment,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                cost_usd=cost,
            )
    return analysis
```

### Template: Analyze button with disabled state

```html
{% if garment.care_label_photo %}
  {% if daily_usage_count >= daily_usage_limit %}
    <!-- Rate limited -->
    <div class="...rate-limit-block...">
      Daily limit reached (10/10). Resets in
      <span id="midnight-countdown"></span>
    </div>
    <script>
      // countdown logic here (Pattern 7)
      startCountdown('midnight-countdown');
    </script>
  {% elif budget_guard_tripped %}
    <p>Analysis temporarily unavailable.</p>
  {% else %}
    <form method="POST" action="{% url 'wardrobe:analyze_care_label' garment.pk %}">
      {% csrf_token %}
      <button type="submit" id="analyze-btn">Analyze Care Label</button>
    </form>
    <script>
      document.querySelector('form').addEventListener('submit', function() {
        const btn = document.getElementById('analyze-btn');
        btn.disabled = true;
        btn.textContent = 'Analyzing...';
      });
    </script>
  {% endif %}
{% else %}
  <button disabled title="Upload a care label photo first to enable analysis">
    Analyze Care Label
  </button>
{% endif %}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `gpt-4-vision-preview` | `gpt-4o` (or `gpt-4o-2024-11-20`) | Dec 2024 (preview shutdown) | Must use `gpt-4o`, not the old preview identifier |
| `chatgpt-4o-latest` alias | `gpt-4o` rolling alias or dated snapshot | Feb 17, 2026 (removed from API) | Do NOT use `chatgpt-4o-latest` |
| `response_format={"type":"json_schema", "schema":...}` with Pydantic | Still valid — Structured Outputs | Introduced Aug 2024 | `json_object` is simpler; `json_schema` enforces schema strictly if needed |
| Responses API (`client.responses.create`) | Chat Completions (`client.chat.completions.create`) | Responses API launched 2025 | Both valid; Chat Completions is stable and sufficient for this use case |

**Deprecated/outdated:**
- `gpt-4-vision-preview`: shutdown December 2024 — do not use
- `chatgpt-4o-latest`: removed from API February 17, 2026 — do not use
- `openai` package v0.x: completely different API surface — ensure `pip install "openai>=2.30"`

---

## Open Questions

1. **Exact GPT-4o pricing at implementation time**
   - What we know: As of January 2026, GPT-4o is approximately $2.50/1M input tokens, $10.00/1M output tokens. Image tokens add to prompt_tokens count.
   - What's unclear: Exact per-image token cost depends on image resolution and `detail` parameter setting. OpenAI's pricing page must be checked at implementation time.
   - Recommendation: Verify at `platform.openai.com/docs/pricing` before writing the `INPUT_COST_PER_TOKEN` constant. Use `detail: "low"` (85 tokens flat) if per-call cost is a concern — but `auto` (the default) is fine for typical care label photos.

2. **`response_format={"type":"json_object"}` with vision — still supported?**
   - What we know: Multiple sources confirm it is compatible with GPT-4o vision inputs as of mid-2025. The prior decision locked this in.
   - What's unclear: Whether the newer Responses API changes anything for json_object.
   - Recommendation: Verify with a single test call before writing the full service layer. Chat Completions + json_object + vision is the well-documented path.

3. **Image detail parameter for care labels**
   - What we know: `detail: "auto"` is the default. `detail: "low"` is 85 tokens flat (cheapest). `detail: "high"` tiles the image.
   - What's unclear: Whether care labels (dense small text) need `detail: "high"` for reliable symbol recognition.
   - Recommendation: Start with `detail: "auto"` (the default, omit the parameter). Test against a real care label. Upgrade to `"high"` only if symbol/text recognition fails.

4. **S3 public URLs vs base64 for image passing**
   - What we know: This project uses `querystring_auth=False` — S3 URLs are publicly accessible. Public URLs should work with `image_url`. Presigned URLs have documented failures but are not used here.
   - What's unclear: Whether public S3 URLs are reliably accessible from OpenAI's servers (no documented failures found for public URLs, only presigned).
   - Recommendation: Use base64 encoding as primary approach — it is unambiguously reliable and adds negligible overhead for typical care label image sizes (< 1MB).

---

## Sources

### Primary (HIGH confidence)
- `developers.openai.com/api/docs/models/gpt-4o` — model identifiers, snapshot versions, capabilities confirmed
- `developers.openai.com/api/docs/deprecations` — `gpt-4o` has no announced API deprecation date; `chatgpt-4o-latest` removed Feb 17, 2026
- `pypi.org/project/openai/` — current package version 2.30.0 (March 25, 2026)
- `mljar.com/notebooks/openai-vision-local-image/` — verified base64 + chat completions pattern, model identifier `gpt-4o`
- `adamj.eu/tech/2023/03/23/django-context-processors-database-queries/` — avoid DB queries in context processors; use namespace filter
- `til.simonwillison.net/django/pretty-print-json-admin` — Django admin JSON pretty-print pattern
- Phase 2 `laundry_advisor/settings/prod.py` — `querystring_auth: False` confirmed; S3 URLs are public

### Secondary (MEDIUM confidence)
- OpenAI community forum thread `invalid_image-error-in-gpt-4o-when-using-s3-presigned-url/794549` — confirmed base64 as workaround for presigned URL failures; root cause unconfirmed but irrelevant (we use public URLs anyway)
- Multiple OpenAI community/official sources confirm `response.usage.prompt_tokens` and `completion_tokens` field names in chat completions
- `developers.openai.com/api/docs/guides/structured-outputs` — Structured Outputs (json_schema) compatible with vision inputs on gpt-4o

### Tertiary (LOW confidence)
- Pricing figures ($2.50/$10.00 per 1M tokens) from secondary web sources — verify at `platform.openai.com/docs/pricing` before using in code

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — openai SDK version confirmed on PyPI; Pillow/hashlib/base64 are stdlib or already installed
- Architecture patterns: HIGH — Django ORM patterns verified, OpenAI API call shape verified from official sources
- Pitfalls: HIGH — most from official docs or confirmed community patterns; race condition analysis from Django docs
- Pricing constants: LOW — must verify at implementation time

**Research date:** 2026-03-27
**Valid until:** 2026-04-27 (30 days — model availability and pricing can shift; re-verify model identifier and pricing constants before writing the service layer)
