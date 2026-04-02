# Phase 4: Laundry Basket - Research

**Researched:** 2026-04-02
**Domain:** Django app creation, pure-Python grouping algorithm, Django templates + vanilla JS, JSON API endpoints
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Page Structure**
- Dedicated `/basket/` page, own URL (not a modal)
- Page heading: "Plan Your Laundry Basket"
- Page subtitle below heading explaining how to use the basket (for first-time users)
- "Plan Laundry" nav link always visible in the main navigation (no badge/count on the nav link)
- Basket page is a single-page experience: selection grid above, plan results section below

**Basket Selection — Grid**
- Photo grid with checkboxes, same column count as the wardrobe grid (responsive)
- Only analyzed garments shown (unanalyzed garments hidden entirely)
- Clicking a card toggles selection only — no navigation to garment detail from basket page
- Visual treatment for selected cards: checkbox + border highlight (brand accent color)
- Card info shown: garment photo + name + category

**Basket Selection — Controls**
- Single row above the grid (inline): [Category dropdown] [Select All] [Clear All] --- [X selected / Y available]
- Category filter: dropdown select
- Select All: selects all analyzed garments regardless of active filter
- Clear All: clears all selected garments regardless of active filter
- Minimum 2 garments required to generate a plan
- Maximum 20 garments per basket
- Sticky "Create Laundry Plan (X)" button fixed at bottom of viewport; full-width bar on mobile
- Button is greyed out with tooltip when fewer than 2 garments selected: "Select at least 2 garments to plan"
- Inline notice shown when user tries to select a 21st garment: "Maximum 20 garments reached"

**Basket Selection — Behaviour**
- Clicking "Create Laundry Plan (X)" scrolls smoothly to the plan results section below
- Plan auto-updates live when selection changes (no re-click needed after first generate)
- Spinner or skeleton shown while grouping computes (even if near-instant)
- Selection persists until manually cleared (not cleared after viewing plan)

**Multiple Named Baskets**
- Users can have up to 5 named baskets
- Basket selector: dropdown near the page heading showing the active basket name
- New basket creation: modal with a name field + Create/Cancel
- Basket names are not required to be unique (duplicates allowed)
- Baskets listed in dropdown by most recently used first
- Rename and delete available via a separate "Manage Baskets" modal/page
- Delete requires a confirmation step: "Are you sure you want to delete [Name]? This cannot be undone."
- First visit with no baskets: show "Create your first basket" prompt

**Plan Results Section**
- Appears below the grid on the same page, separated by a section heading (e.g. "Your Laundry Plan")
- Hidden entirely until the user generates a plan (no empty state for plan section)
- Summary line at top of results: e.g. "Your plan: 3 loads, 12 garments"
- Load cards ordered by number of garments descending (biggest load first)

**Load Cards**
- Card-based layout, one card per load
- Card header: "Load [N]: [Color Group] -- [Temp] ([X garments])" e.g. "Load 1: Darks -- 30 degrees C (5 garments)"
- Card body: mini photo thumbnails with garment name below each
- Card body: wash settings relevant to the load (temperature, cycle, anything that explains the grouping)
- Card body: grouping rationale shown e.g. "Grouped by: Color (Darks) | Temp (30 degrees C)"
- Warnings: inline badges on each garment thumbnail AND a summary warnings section at the card bottom

**Special Care Section**
- Shown only when at least one garment is dry-clean-only, hand-wash-only, or otherwise non-machine-washable
- Flat list format: mini thumbnail + garment name + care method per item (no sub-grouping by care type)
- Same card style as load cards but with a distinct header color (amber/yellow) to signal attention
- If ALL selected garments are special care: notice at top of plan results ("No machine-wash loads for your selection"), then Special Care section

**Grouping Logic**
- Color groups: Whites / Lights / Darks (3 groups)
- Delicates separated only when mixing would be problematic (temperature or cycle conflict with normal garments)
- Garments with null/unknown wash temperature: grouped with the coldest load
- Conflicting care instructions: Claude's discretion - apply safest interpretation
- 3 compatibility axes: temperature, color group, fabric sensitivity (delicates flag)

**Plan Saving**
- "Save Plan" button at the top of the plan results section (explicit save, not auto-save)
- Saved plan is stored alongside the basket in the database
- When returning to a basket with a saved plan, the plan is shown immediately
- If garment analyses were updated since plan was saved: show "Plan may be outdated" notice
- When no plan has been saved yet: plan section is hidden

**Edge Cases**
- Garment deleted from wardrobe: silently removed from basket selection
- Garment's analysis deleted: silently removed from basket selection
- Empty analyzed wardrobe: basket page shows empty state with link to wardrobe

### Claude's Discretion
- Exact spinner/skeleton design for plan loading state
- Exact wording of section headings and button labels (beyond what's specified above)
- Compression/storage format for saved plan JSON
- Keyboard accessibility implementation details
- How stale-plan detection is implemented (e.g. timestamp comparison on analysis vs plan save date)

### Deferred Ideas (OUT OF SCOPE)
- Category filter on the wardrobe page -- user wants this but it's outside Phase 4 scope; add to Phase 5 or backlog

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BSKT-01 | User can select multiple analyzed garments from their wardrobe to add to a laundry basket | Basket model with JSONField `garment_pks`; basket view handles selection POST; JS on basket page manages checkbox state and persists selection |
| BSKT-02 | Only garments with a completed analysis are eligible for basket selection | `Exists()` subquery annotation already proven in wardrobe views; basket page queries with `has_analysis=True` filter; unanalyzed garments hidden from DOM |
| BSKT-03 | App generates a multi-load washing plan, grouping garments by temperature compatibility, color group (whites/lights/darks), and fabric sensitivity (delicates vs. normal) | Pure Python `group_into_loads()` in `laundry/services/grouping.py`; invoked via `POST /basket/api/plan/` JSON endpoint; returns structured dict |
| BSKT-04 | Each load in the plan displays the list of included garments, recommended wash settings, and applicable warnings | Load card template section; per-garment warning badges; summary warning pills at card bottom; special care card for non-machine-washable items |

</phase_requirements>

---

## Summary

Phase 4 introduces a new `laundry` Django app that sits alongside the existing `wardrobe` app. The core algorithmic work is a pure-Python function `group_into_loads()` that takes a list of garment+analysis dicts and returns a structured plan: a list of machine-wash loads plus a special-care list. This function has no ORM calls, making it trivially unit-testable without database setup.

The UI is a single Django template at `/basket/` with two sections: a multi-select garment photo grid and a plan results section that appears below. Interactivity uses vanilla JS inline scripts only (consistent with phases 1-3 -- no JS framework, no npm packages). The plan is fetched via a JSON endpoint (`POST /basket/api/plan/`) that calls `group_into_loads()` and returns serialized load data; JS renders this into the DOM. Selection state lives in a JS `Set` in memory, persisted across page loads via `Basket.garment_pks` (a JSONField list of PKs in the DB).

Named baskets require a `Basket` model with `name`, `user`, `garment_pks` (JSONField), `saved_plan` (JSONField, nullable), `plan_saved_at` (DateTimeField, nullable), and `last_used_at` (DateTimeField with auto_now=True). Basket CRUD uses simple POST forms with Django messages redirects, consistent with existing wardrobe patterns. Zero new Python packages are required.

**Primary recommendation:** Create the `laundry` app first (Plan 04-01: model + service + unit tests covering all edge cases), then views and templates (Plan 04-02). The grouping function must be written and tested before the template work begins because the template work depends on the plan JSON structure.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 5.2 (pinned in requirements.txt) | App framework, ORM, routing, templates | Already in project |
| Python stdlib (re, json) | 3.13 | Text parsing for grouping algorithm, JSON serialisation | No external dependency needed |
| Django JSONField | Built-in (Django 5.x) | Store garment_pks and saved_plan in Basket model | Native to Django; no extra package |
| Django JsonResponse | Built-in | Return plan JSON from API endpoint | Standard Django pattern |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| django-tailwind-cli | 4.5.x (pinned) | Compile Tailwind CSS v4 | Run `tailwind build --force` after creating new templates with new utility classes |
| Django login_required | Built-in | Auth guard on all basket views | Same pattern as all wardrobe views |
| Django messages framework | Built-in | Basket create/rename/delete feedback | Same pattern as wardrobe CRUD |

### No New Packages Required

Phase 4 adds zero new Python packages. All functionality (ORM, JSONField, templates, JsonResponse, messages) is provided by Django 5.2 already installed.

**Installation:** none needed.

---

## Architecture Patterns

### Recommended Project Structure

```
laundry/
    __init__.py
    apps.py
    migrations/
        __init__.py
    models.py              # Basket model only
    services/
        __init__.py
        grouping.py        # group_into_loads() -- pure Python, no ORM
    tests/
        __init__.py
        test_grouping.py   # Unit tests: group_into_loads() edge cases
        test_views.py      # Integration tests: basket views
    urls.py                # app_name = 'laundry'
    views.py               # basket, plan_api, basket_create, basket_rename, basket_delete

templates/laundry/
    basket.html            # Main basket page (selection grid + plan results)
```

### Pattern 1: Pure-Python Grouping Service

**What:** `group_into_loads()` receives a list of plain dicts (assembled in the view from ORM objects) and returns a structured result dict. No ORM calls inside the function.

**When to use:** Separation of ORM from algorithm allows unit tests that create plain dicts without database fixtures -- faster, simpler, and more exhaustive testing. The view layer handles the DB query; the service layer handles algorithm.

**Input/output contract:**
```python
# laundry/services/grouping.py

def group_into_loads(garments: list[dict]) -> dict:
    """
    Args:
        garments: list of dicts, each with:
            pk: int
            name: str
            photo_url: str | None
            category: str
            color: str          -- Garment.color free-text field
            washing: str        -- CareAnalysis.washing (user-edited)
            drying: str         -- CareAnalysis.drying
            bleach: str         -- CareAnalysis.bleach
            is_delicate: bool   -- CareAnalysis.is_delicate

    Returns:
        {
            'loads': [
                {
                    'color_group': 'darks',   # 'whites' | 'lights' | 'darks'
                    'temperature': 30,        # int Celsius or None
                    'temp_label': '30C',      # display string e.g. 'Coolest wash'
                    'cycle': 'normal',        # 'normal' | 'delicate'
                    'garments': [
                        {'pk': ..., 'name': ..., 'photo_url': ..., 'warnings': [...]}
                    ],
                    'warnings': ['air dry only', ...]
                },
                ...  # sorted by len(garments) descending
            ],
            'special_care': [
                {
                    'pk': int,
                    'name': str,
                    'photo_url': str | None,
                    'care_method': str   # human-readable reason e.g. 'Dry clean only'
                },
                ...
            ]
        }
    """
```

### Pattern 2: Django JSONField for Plan and Selection Storage

**What:** `Basket.saved_plan` stores the full plan dict as JSONField (nullable). `Basket.garment_pks` stores a list of integer PKs as JSONField.

**Model definition:**
```python
# laundry/models.py
from django.conf import settings
from django.db import models


class Basket(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='baskets',
    )
    name = models.CharField(max_length=100)
    garment_pks = models.JSONField(default=list)        # [int, int, ...]
    saved_plan = models.JSONField(null=True, blank=True) # plan dict or null
    plan_saved_at = models.DateTimeField(null=True, blank=True)
    last_used_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_used_at']

    def __str__(self):
        return f"{self.name} ({self.user})"
```

### Pattern 3: JSON Plan API Endpoint

**What:** `POST /basket/api/plan/` receives `{"garment_pks": [1, 2, 3]}` as JSON body, fetches garments + analyses scoped to `request.user`, builds garment dicts, calls `group_into_loads()`, returns `JsonResponse`.

**Pattern:**
```python
# laundry/views.py

@login_required
@require_POST
def plan_api(request):
    import json
    from django.db.models import Exists, OuterRef
    try:
        body = json.loads(request.body)
        pks = [int(pk) for pk in body.get('garment_pks', [])]
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    # Fetch only analyzed garments belonging to this user
    garments = Garment.objects.filter(
        pk__in=pks,
        user=request.user,
    ).select_related('care_analysis')

    garment_dicts = []
    for g in garments:
        try:
            a = g.care_analysis
        except Exception:
            continue  # skip if analysis missing (edge case: deleted since page load)
        garment_dicts.append({
            'pk': g.pk,
            'name': g.name,
            'photo_url': g.garment_photo.url if g.garment_photo else None,
            'category': g.category,
            'color': g.color,
            'washing': a.washing,
            'drying': a.drying,
            'bleach': a.bleach,
            'is_delicate': a.is_delicate,
        })

    from laundry.services.grouping import group_into_loads
    plan = group_into_loads(garment_dicts)
    return JsonResponse(plan)
```

### Pattern 4: Vanilla JS for Interactive Plan Updates

**What:** Inline `<script>` block in `basket.html`. No JS framework, no npm. Consistent with phases 1-3.

**Key JS responsibilities:**
1. Track selected PKs in a `Set`
2. On checkbox change: update counter display, toggle sticky button state, enforce 20-garment maximum
3. First "Create Laundry Plan" click: scroll to plan section, fetch, render
4. After first plan generated: auto-fetch on every selection change (debounced 300ms)
5. Category filter: JS hides/shows cards client-side (no server round-trip)
6. CSRF: read `{% csrf_token %}` value into a JS variable; send as `X-CSRFToken` header

**CSRF injection:**
```html
<script>
const CSRF_TOKEN = '{{ csrf_token }}';
// ...
const resp = await fetch('/basket/api/plan/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': CSRF_TOKEN,
    },
    body: JSON.stringify({ garment_pks: Array.from(selectedPks) }),
});
</script>
```

**Inline debounce (no library):**
```javascript
let debounceTimer;
function debouncedPlanUpdate() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(fetchAndRenderPlan, 300);
}
```

### Pattern 5: Basket Scoped to User

**What:** All basket queries scoped with `user=request.user`. Max-5 limit enforced at create time, not DB level.

```python
# Basket create view guard
if Basket.objects.filter(user=request.user).count() >= 5:
    messages.error(request, "You can have at most 5 baskets.")
    return redirect('laundry:basket')
```

### Grouping Algorithm Logic (Prescriptive)

The `group_into_loads()` function applies these rules in order:

**Step 1 - Special care routing (first pass over all garments):**
Detect non-machine-washable garments by checking the `washing` field for keywords:
```
'dry clean', 'dryclean', 'dry-clean',
'hand wash only', 'hand-wash only', 'hand wash',
'do not wash', 'do not machine wash',
'spot clean', 'no washing',
```
Route matching garments to `special_care` list. `care_method` is derived from the first matching keyword pattern (e.g., "Dry clean only", "Hand wash only").

**Step 2 - Color group classification:**
Classify each remaining garment's color group from `Garment.color` (free-text, case-insensitive):
```python
DARKS_KEYWORDS = [
    'black', 'navy', 'dark blue', 'dark grey', 'dark gray',
    'charcoal', 'dark brown', 'dark green', 'dark red', 'dark',
]
WHITES_KEYWORDS = ['white', 'cream', 'ivory', 'off-white', 'off white']
# Default: 'lights'
```
Check darks first, then whites, default to lights.

**Step 3 - Temperature extraction:**
Parse integer Celsius from `washing` field:
1. Regex: `r'(\d+)\s*(?:°C|degrees?\s*C|°c)'` -- extracts explicit Celsius
2. Keyword fallback: `'cold'` -> 30, `'cool'` -> 30, `'warm'` -> 40, `'hot'` -> 60
3. `None` if unparseable -> use 30 (coldest bucket) and display label "Coolest wash"

**Step 4 - Grouping key:**
`(color_group, temperature_bucket, is_delicate_cycle)`

Delicates (`is_delicate=True`) are placed in a separate load from non-delicates only when both types exist in the same (color_group, temperature) bucket. If all garments in a bucket are delicates, no separation needed.

`temperature_bucket` normalises continuous temperatures into buckets: 30 (cold), 40 (warm), 60 (hot). Temperatures outside these buckets round to nearest.

**Step 5 - Warning extraction per garment:**
Scan `drying`, `bleach`, and `washing` fields:
- "air dry", "lay flat", "line dry", "hang to dry" -> "air dry only"
- "no bleach", "do not bleach", "non-chlorine", "bleach free" -> "no bleach"
- "delicate cycle", "gentle cycle", "delicate wash" -> "delicate cycle"
- "do not tumble dry", "no tumble" -> "no tumble dry"

**Step 6 - Sort loads descending by garment count.**

### Anti-Patterns to Avoid

- **ORM calls inside `group_into_loads()`:** The function must be pure Python. ORM calls belong in the view that assembles the garment dict list.
- **Storing garment snapshot data beyond PKs in the basket:** Store only PKs in `Basket.garment_pks`; fetch fresh analysis data at plan-generation time. Avoids stale data after re-analysis.
- **Auto-saving the plan on every generation:** Only save on explicit "Save Plan" POST per locked decision.
- **Returning plan HTML from the API endpoint:** The API returns JSON; the JS renders the HTML client-side. Mixing server-side HTML rendering with the plan API creates a maintenance burden.
- **Missing `app_name` in `laundry/urls.py`:** Without `app_name = 'laundry'`, all `{% url 'laundry:basket' %}` template reversals fail with `NoReverseMatch`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON storage in DB | `TextField` + manual `json.dumps/loads` | Django `JSONField` | Native Django 5.x; handles null, serialisation, and ORM filtering correctly |
| CSRF in AJAX | Cookie-parsing JS | `{{ csrf_token }}` injected into JS variable | Established Django practice; avoids SameSite cookie issues |
| User isolation | Custom middleware or session checks | `filter(user=request.user)` + `get_object_or_404(..., user=request.user)` | Proven pattern from wardrobe views; returns 404 on cross-user access |
| JS debounce | Lodash import | Inline `setTimeout`/`clearTimeout` (~5 lines) | No JS packages in project; trivial inline |
| Analysed-garment filtering | Custom Python loop | `Exists()` subquery annotation (already in wardrobe views) | Single DB query; no N+1 |

**Key insight:** Phase 4 adds zero new external dependencies. All complexity is algorithm + UI, both solvable within the existing stack.

---

## Common Pitfalls

### Pitfall 1: Missing `app_name` Causes All URL Reversals to Fail

**What goes wrong:** `{% url 'laundry:basket' %}` raises `NoReverseMatch`.

**Why it happens:** Django requires `app_name` in `urls.py` for namespace reversal.

**How to avoid:** Set `app_name = 'laundry'` in `laundry/urls.py`. Include with `path('basket/', include('laundry.urls'))` in `laundry_advisor/urls.py`. Mirror the pattern in `wardrobe/urls.py` which already sets `app_name = 'wardrobe'`.

### Pitfall 2: `tailwind build` Not Re-Run After New Template Created

**What goes wrong:** New Tailwind classes in `basket.html` (e.g., `animate-pulse`, `ring-2`, `fixed`, `inset-x-0`, `z-40`, `z-50`) are absent from compiled CSS. Sticky bar invisible; selection ring absent; skeleton not animating.

**Why it happens:** Tailwind CLI scans templates for class names. A new template file not yet scanned at last build time has no compiled utilities. The `@source inline()` block in `main.css` only covers color utilities explicitly; structural utilities rely on template scanning.

**How to avoid:** Run `python manage.py tailwind build --force` after creating `basket.html`. If classes remain missing, add `@source inline(...)` entries to `assets/src/main.css`.

**Warning signs:** Layout appears unstyled; sticky button not visible; grid not responsive.

### Pitfall 3: Deleted or Unanalyzed Garments in `garment_pks` Cause Silent Mismatch

**What goes wrong:** A garment is deleted from the wardrobe after being added to a basket. Its PK remains in `Basket.garment_pks`, but the ORM query returns fewer objects than PKs.

**Why it happens:** No cascade signal removes the PK from baskets when a garment is deleted.

**How to avoid:** In the basket view and plan API, always filter:
```python
Garment.objects.filter(pk__in=basket.garment_pks, user=request.user)
```
Silently accept the smaller result set. Per locked decision: deleted garments are silently excluded. Do not raise an error or show a warning.

### Pitfall 4: `request.body` Read Twice Raises RawPostDataException

**What goes wrong:** Reading `request.body` in a helper function after already reading it in the view raises `RawPostDataException`.

**Why it happens:** Django's request body is a stream; it can only be read once.

**How to avoid:** In `plan_api`, read `body = request.body` once at the top, then parse and pass parsed data to all helpers. Never re-read `request.body`.

### Pitfall 5: Color Classification on Free-Text `Garment.color`

**What goes wrong:** Users write "navy blue", "NAVY", "dark navy", "very dark navy" -- all should be "darks". Case-sensitive matching misses variations.

**Why it happens:** `Garment.color` is a free-text `CharField(max_length=100)` with no vocabulary enforcement.

**How to avoid:** Always `.lower()` the color string before matching. Use ordered keyword check: darks first (longest/most specific keywords before short ones), then whites, default lights.

### Pitfall 6: Temperature Bucket Normalisation Edge Cases

**What goes wrong:** `washing = "Wash at maximum 40C"` should produce temperature 40, but `"maximum"` before the number may confuse a naive regex.

**Why it happens:** GPT-4o outputs free-text washing instructions; the exact phrasing varies.

**How to avoid:** The regex `r'(\d+)\s*(?:°C|degrees?\s*C|°c|C\b)'` with case-insensitive flag is broad enough to catch most patterns. Unit tests must cover: `"30°C"`, `"30 degrees C"`, `"cold"`, `"warm"`, `"hot"`, `"max 40C"`, `"Unable to determine"` (null case), and an empty string.

### Pitfall 7: `auto_now=True` Fields Cannot Be Set Manually

**What goes wrong:** Attempting `basket.last_used_at = some_datetime; basket.save()` silently ignores the manual assignment -- `auto_now=True` always overwrites with `now()`.

**Why it happens:** Django's `auto_now` fields are set at the ORM level, not by user code.

**How to avoid:** Use `auto_now=True` on `last_used_at` and accept that every `.save()` updates it (correct behavior). For `plan_saved_at`, use a plain nullable DateTimeField and set it explicitly only on the "Save Plan" POST.

---

## Code Examples

### Exists() Annotation for Analysed-Only Garments (proven pattern from wardrobe/views.py)

```python
from django.db.models import Exists, OuterRef
from wardrobe.models import CareAnalysis, Garment

analyzed_garments = Garment.objects.filter(user=request.user).annotate(
    has_analysis=Exists(CareAnalysis.objects.filter(garment=OuterRef('pk')))
).filter(has_analysis=True)
```

Source: `wardrobe/views.py` -- `garment_list` view already uses this exact pattern.

### Stale Plan Detection

```python
# In basket view, after loading basket with saved_plan:
from django.db.models import Max

if basket.saved_plan and basket.plan_saved_at:
    last_analysis_update = CareAnalysis.objects.filter(
        garment__pk__in=basket.garment_pks,
        garment__user=request.user,
    ).aggregate(latest=Max('updated_at'))['latest']

    plan_is_stale = (
        last_analysis_update is not None
        and last_analysis_update > basket.plan_saved_at
    )
```

### Category Filter (JS, no server round-trip)

```javascript
// Cards have data-category attribute set in template
// <div class="garment-card" data-category="{{ garment.category }}">

function filterByCategory(category) {
    document.querySelectorAll('.garment-card').forEach(card => {
        const match = category === '' || card.dataset.category === category;
        card.style.display = match ? '' : 'none';
    });
}

document.getElementById('category-filter').addEventListener('change', function() {
    filterByCategory(this.value);
});
```

### Loading Skeleton Display Pattern

```javascript
function showSkeleton() {
    document.getElementById('plan-skeleton').style.display = '';
    document.getElementById('plan-results').style.display = 'none';
}

function hideSkeleton() {
    document.getElementById('plan-skeleton').style.display = 'none';
    document.getElementById('plan-results').style.display = '';
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `TextField` + manual `json.dumps()` for structured storage | Django `JSONField` | Django 3.1+ | No custom serialisation layer needed; nullable; queryable |
| Separate `django-jsonfield` package | Native `models.JSONField` | Django 3.1 LTS | One fewer dependency; already available in this project |

---

## Open Questions

1. **Temperature extraction from free-text `washing` field**
   - What we know: `CareAnalysis.washing` is GPT-4o prose (e.g., "Machine wash cold (30 degrees C)", "Wash in warm water", "Cold wash only"). No structured temperature field exists.
   - What's unclear: GPT-4o may say "cold", "warm", "hot" without explicit Celsius; or include Fahrenheit; or use "Unable to determine".
   - Recommendation: Two-stage parse: (1) regex for explicit Celsius notation, (2) keyword map (cold=30, cool=30, warm=40, hot=60). Return None for "Unable to determine" or any unparseable string and use "Coolest wash" label per copywriting contract. Unit tests must cover all cases.

2. **Stale-plan detection granularity**
   - What we know: CONTEXT.md designates this as Claude's discretion. `CareAnalysis.updated_at` is DateTimeField with auto_now=True. `Basket.plan_saved_at` is a nullable DateTimeField to be created in Phase 4.
   - Recommendation: Compare `basket.plan_saved_at` against `MAX(care_analysis.updated_at)` for all garments in `garment_pks`. Single aggregated query; no per-garment loop. Implementation is a 4-line check in the basket detail view.

3. **Basket page URL: `/basket/` or `/basket/<pk>/`**
   - What we know: CONTEXT.md says "Dedicated /basket/ page, own URL". Multiple baskets are supported (up to 5).
   - Recommendation: Use `/basket/` as the landing URL -- shows the active basket (most recently used). Switching baskets POSTs to a "set active" endpoint or uses a query parameter (`/basket/?basket_id=3`). The active basket ID can be tracked in the user session or via a `is_active` flag. Simplest: query parameter on GET, or session key `active_basket_id`. Keeping all baskets on a single URL path is cleanest for the single-page experience.

---

## Environment Availability

Step 2.6: External dependencies audited.

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | App runtime | Yes | 3.13.5 | -- |
| Django 5.2 | App framework, JSONField, test runner | Yes | 5.2 | -- |
| SQLite | JSONField storage in dev | Yes | Built-in Python 3.13 | -- |
| Tailwind CLI binary | CSS compilation | Yes (in .django_tailwind_cli/) | Per project install | Re-download via `python manage.py tailwind download_cli` |

No missing dependencies. Phase 4 adds zero new packages.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Django test runner (Django 5.2 built-in) |
| Config file | none -- uses `manage.py test` |
| Quick run command | `DJANGO_SETTINGS_MODULE=laundry_advisor.settings.dev python manage.py test laundry --verbosity=1` |
| Full suite command | `DJANGO_SETTINGS_MODULE=laundry_advisor.settings.dev python manage.py test` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BSKT-02 | Only analyzed garments shown on basket page | unit | `python manage.py test laundry.tests.test_grouping.EligibilityQueryTest` | No -- Wave 0 |
| BSKT-03 | Grouping by temp/color/delicate, special care routing | unit | `python manage.py test laundry.tests.test_grouping.GroupingLogicTest` | No -- Wave 0 |
| BSKT-01 | Basket selection view + selection persistence | integration | `python manage.py test laundry.tests.test_views.BasketSelectionTest` | No -- Wave 0 |
| BSKT-04 | Plan display: garments, settings, warnings | integration | `python manage.py test laundry.tests.test_views.PlanDisplayTest` | No -- Wave 0 |

### Sampling Rate

- **Per task commit:** `DJANGO_SETTINGS_MODULE=laundry_advisor.settings.dev python manage.py test laundry --verbosity=1`
- **Per wave merge:** `DJANGO_SETTINGS_MODULE=laundry_advisor.settings.dev python manage.py test`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `laundry/tests/__init__.py` -- package marker
- [ ] `laundry/tests/test_grouping.py` -- unit test stubs covering:
  - null temperature defaults to coldest load (30)
  - dry-clean-only garments routed to special_care
  - hand-wash-only garments routed to special_care
  - Whites / Lights / Darks classification from color string
  - delicates separated when mixed with normals at same temp+color bucket
  - delicates merged into single load when no normals in same bucket
  - air-dry, no-bleach, delicate-cycle warnings extracted correctly
  - loads sorted descending by garment count
  - all-special-care basket: empty loads list, non-empty special_care
  - empty garment list: returns empty loads and empty special_care
- [ ] `laundry/tests/test_views.py` -- integration test stubs for BSKT-01 and BSKT-04

No additional framework install needed -- Django test runner already available.

---

## Sources

### Primary (HIGH confidence)

- Existing project codebase (direct file reads):
  - `wardrobe/models.py` -- CareAnalysis fields available for grouping
  - `wardrobe/views.py` -- Exists() annotation pattern, user isolation pattern
  - `wardrobe/services/analysis.py` -- service layer structure, lazy client pattern
  - `laundry_advisor/settings/base.py` -- INSTALLED_APPS, JSONField availability confirmed
  - `assets/src/main.css` -- full Tailwind palette, @source inline() coverage
  - `templates/base.html` -- nav structure, toast pattern
  - `templates/wardrobe/wardrobe_list.html` -- grid structure, card pattern
  - `requirements.txt` -- confirmed Django 5.2, zero new packages needed
- `.planning/phases/04-laundry-basket/04-CONTEXT.md` -- all locked decisions
- `.planning/phases/04-laundry-basket/04-UI-SPEC.md` -- all component specs and Tailwind classes
- `.planning/phases/04-laundry-basket/04-VALIDATION.md` -- test infrastructure contract

### Secondary (MEDIUM confidence)

- Django 5.2 documentation patterns (JSONField, JsonResponse, require_POST, auto_now, Exists subquery) -- confirmed consistent with existing codebase usage

### Tertiary (LOW confidence)

- Temperature keyword mapping (cold=30C, warm=40C, hot=60C) -- reasonable laundry standard heuristic but GPT-4o output variability not empirically tested; unit tests must cover edge cases explicitly

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all packages already in requirements.txt, zero new deps
- Architecture: HIGH -- all patterns are direct extensions of proven wardrobe app patterns; Basket model is a straightforward new model
- Grouping algorithm: MEDIUM -- logic is correct but GPT-4o free-text variability in `washing` field adds uncertainty to temperature/special-care detection; mitigated by unit test coverage
- UI/JS: HIGH -- vanilla JS patterns are simple and consistent with phases 1-3; no new JS libraries

**Research date:** 2026-04-02
**Valid until:** 2026-05-02 (30 days -- stable stack, no fast-moving dependencies)
