# Phase 4: Laundry Basket - Research

**Researched:** 2026-04-02
**Domain:** Django app creation, pure-Python grouping logic, Django template UI with Tailwind CSS v4
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
- Single row above the grid (inline): [Category dropdown] [Select All] [Clear All] — — — [X selected / Y available]
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
- Card header: "Load [N]: [Color Group] — [Temp] ([X garments])" e.g. "Load 1: Darks — 30°C (5 garments)"
- Card body: mini photo thumbnails with garment name below each
- Card body: wash settings relevant to the load (temperature, cycle, anything that explains the grouping)
- Card body: grouping rationale shown e.g. "Grouped by: Color (Darks) | Temp (30°C)"
- Warnings: inline badges on each garment thumbnail AND a summary warnings section at the card bottom

**Special Care Section**
- Shown only when at least one garment is dry-clean-only, hand-wash-only, or otherwise non-machine-washable
- Flat list format: mini thumbnail + garment name + care method per item (no sub-grouping by care type)
- Same card style as load cards but with a distinct header color (e.g. amber/yellow) to signal attention
- If ALL selected garments are special care: notice at top of plan results ("No machine-wash loads for your selection"), then Special Care section

**Grouping Logic**
- Color groups: Whites / Lights / Darks (3 groups)
- Delicates separated only when mixing would be problematic (temperature or cycle conflict with normal garments)
- Garments with null/unknown wash temperature: grouped with the coldest load
- Conflicting care instructions (e.g. contradictory data in analysis): Claude's discretion — apply safest interpretation
- 3 compatibility axes: temperature, color group, fabric sensitivity (delicates flag)

**Plan Saving**
- "Save Plan" button at the top of the plan results section (explicit save, not auto-save)
- Saved plan is stored alongside the basket in the database
- When returning to a basket with a saved plan, the plan is shown immediately
- If garment analyses were updated since plan was saved: show "Plan may be outdated — re-plan for latest results" notice
- When no plan has been saved yet: plan section is hidden

**Edge Cases**
- Garment deleted from wardrobe: silently removed from basket selection
- Garment's analysis deleted: silently removed from basket selection
- Empty analyzed wardrobe: basket page shows empty state with link to wardrobe ("No analyzed garments yet. Analyze some garments first.")

### Claude's Discretion
- Exact spinner/skeleton design for plan loading state
- Exact wording of section headings and button labels (beyond what's specified above)
- Compression/storage format for saved plan JSON
- Keyboard accessibility implementation details
- How stale-plan detection is implemented (e.g. timestamp comparison on analysis vs plan save date)

### Deferred Ideas (OUT OF SCOPE)
- Category filter on the wardrobe page — user wants this but it's outside Phase 4 scope; add to Phase 5 or backlog
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BSKT-01 | User can select multiple analyzed garments from their wardrobe to add to a laundry basket | New `laundry` Django app with Basket model + ManyToMany to Garment; view filters to `has_analysis` garments only |
| BSKT-02 | Only garments with a completed analysis are eligible for basket selection | Queryset filter: `Garment.objects.filter(user=request.user, care_analysis__isnull=False)` excludes unanalyzed; same `Exists()` annotation pattern used in Phase 3 |
| BSKT-03 | App generates a multi-load washing plan, grouping by temperature compatibility, color group, and fabric sensitivity | Pure Python `group_into_loads(garments)` function in `laundry/services/grouping.py`; consumes `CareAnalysis` fields already stored |
| BSKT-04 | Each load displays included garments, recommended wash settings, and applicable warnings | Template renders load card per group dict returned by `group_into_loads()`; warnings extracted from `CareAnalysis.drying`, `CareAnalysis.bleach`, `CareAnalysis.is_delicate` |
</phase_requirements>

---

## Summary

Phase 4 adds a dedicated `laundry` Django app alongside the existing `wardrobe` app. The phase has two distinct concerns: (1) a grouping algorithm expressed as a pure Python function that consumes already-stored `CareAnalysis` data, and (2) a browser UI for basket management and plan display built on the established Django/Tailwind v4 stack.

The grouping logic is the intellectually interesting part. All the data it needs already exists in `CareAnalysis` (washing temperature, is_delicate, drying, bleach fields). The algorithm classifies each garment into a color group (Whites/Lights/Darks) inferred from the garment's `color` field and care instructions, then sub-groups by temperature bucket and delicates flag. Null temperature defaults to the coldest load. Dry-clean-only and hand-wash-only garments are separated into a Special Care section before machine-wash grouping begins.

The UI requires Alpine.js-style interactivity (live plan updates, sticky button state, checkbox toggling, modal dialogs, category filter). The project has no JavaScript framework currently installed — the established pattern is vanilla Tailwind with Django templates. For Phase 4's interaction needs, inline `<script>` tags with vanilla JS or a minimal Alpine.js CDN inclusion is the pragmatic approach that avoids adding a build-step dependency.

**Primary recommendation:** Create a new `laundry` Django app with three models (Basket, BasketGarment, SavedPlan), implement `group_into_loads()` as a standalone pure-Python function with comprehensive unit tests using Django's built-in test runner, and build the UI with Django templates + vanilla JavaScript (no new npm dependencies).

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django | 5.2 (pinned) | Web framework, ORM, templates | Already in use across all phases |
| django-tailwind-cli | >=4.5,<5.0 | Tailwind CSS v4 build | Already in use; build pattern established |
| Pillow | >=10.0,<12.0 | Image handling for garment photos | Already in use |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Vanilla JS (inline `<script>`) | Browser-native | Checkbox selection, sticky button state, category filter, live plan update, modal dialogs | No npm dependency needed; interactions are straightforward DOM manipulation |
| Django test runner (`manage.py test`) | Django 5.2 built-in | Unit tests for `group_into_loads()` | pytest is not installed; Django test runner is already functional (verified) |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Vanilla JS | Alpine.js CDN | Alpine would be cleaner for reactive state (live plan, sticky count), but adds an external CDN dependency and a new pattern not used elsewhere in the project |
| Django test runner | pytest + pytest-django | pytest is cleaner but not installed; Django runner handles the `group_into_loads()` unit tests equally well |

**Installation:** No new packages required. No changes to `requirements.txt`.

---

## Architecture Patterns

### Recommended Project Structure

```
laundry/
├── __init__.py
├── apps.py
├── admin.py
├── migrations/
│   └── 0001_initial.py
├── models.py              # Basket, BasketGarment, SavedPlan
├── urls.py                # app_name = 'laundry'
├── views.py               # basket_detail, basket_create, basket_manage, basket_save_plan
├── services/
│   ├── __init__.py
│   └── grouping.py        # group_into_loads() pure function
└── tests/
    ├── __init__.py
    └── test_grouping.py   # unit tests for group_into_loads()

templates/
└── laundry/
    ├── basket_detail.html    # main single-page basket+plan view
    └── basket_manage.html    # rename/delete baskets modal/page
```

### Pattern 1: New Django App Registration

**What:** Create `laundry` as a separate Django app following the established `wardrobe` app pattern.
**When to use:** Feature set has its own models, URLs, views, and templates.

```python
# laundry/apps.py
from django.apps import AppConfig

class LaundryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'laundry'

# laundry_advisor/settings/base.py — add to INSTALLED_APPS
INSTALLED_APPS = [
    ...
    'wardrobe',
    'laundry',   # new
]

# laundry_advisor/urls.py — add URL include
path('basket/', include('laundry.urls')),
```

### Pattern 2: Data Models

**What:** Three models in `laundry/models.py` covering the basket container, basket membership, and saved plan.

```python
from django.conf import settings
from django.db import models


class Basket(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='baskets',
    )
    name = models.CharField(max_length=100)
    garments = models.ManyToManyField(
        'wardrobe.Garment',
        through='BasketGarment',
        related_name='baskets',
    )
    last_used_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-last_used_at']

    def __str__(self):
        return self.name


class BasketGarment(models.Model):
    basket = models.ForeignKey(Basket, on_delete=models.CASCADE)
    garment = models.ForeignKey('wardrobe.Garment', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('basket', 'garment')]


class SavedPlan(models.Model):
    basket = models.OneToOneField(
        Basket,
        on_delete=models.CASCADE,
        related_name='saved_plan',
    )
    plan_json = models.JSONField()
    saved_at = models.DateTimeField(auto_now=True)
    # Used for stale detection: compare to max(CareAnalysis.updated_at)
    # for garments in basket at save time.
    snapshot_analysis_max_updated = models.DateTimeField(null=True, blank=True)
```

**Key design notes:**
- `ManyToManyField` through `BasketGarment` allows garments to be in multiple baskets.
- `last_used_at` auto-updates on Basket save — use `Basket.objects.filter(pk=pk).update(last_used_at=now())` to touch timestamp without triggering full save when switching active basket.
- `SavedPlan.snapshot_analysis_max_updated` enables stale detection: at save time, store `max(CareAnalysis.updated_at)` for all basket garments; on load, compare against current max to detect staleness.
- Cross-app FK: `'wardrobe.Garment'` string reference avoids circular import.

### Pattern 3: Garment Eligibility Query

**What:** Filter queryset to only garments belonging to user AND having a completed analysis.
**Why:** Reuses the established Phase 3 annotation pattern; `care_analysis__isnull=False` is a join-based filter requiring no annotation.

```python
# laundry/views.py
from django.db.models import Exists, OuterRef
from wardrobe.models import CareAnalysis, Garment

def _analyzed_garments(user):
    """Return garments with completed analyses for user, ordered by creation date."""
    return (
        Garment.objects
        .filter(user=user, care_analysis__isnull=False)
        .select_related('care_analysis')
        .order_by('-created_at')
    )
```

Note: `care_analysis__isnull=False` implicitly joins via the OneToOneField reverse relation. `select_related('care_analysis')` avoids N+1 when `group_into_loads()` reads `care_analysis` fields.

### Pattern 4: Grouping Service — `group_into_loads()`

**What:** Pure Python function that takes a list of Garment objects (with `care_analysis` pre-fetched) and returns a structured plan dict.
**Why pure Python:** No Django ORM calls inside the function — makes unit testing trivial (no database required).

```python
# laundry/services/grouping.py

TEMP_COLD = 30    # °C threshold
TEMP_WARM = 40
TEMP_HOT  = 60

SPECIAL_CARE_KEYWORDS = (
    'dry clean', 'dry-clean', 'hand wash', 'hand-wash',
    'do not wash', 'no machine', 'spot clean',
)


def _color_group(garment) -> str:
    """Classify garment into Whites / Lights / Darks."""
    color = (garment.color or '').lower()
    if color in ('white', 'cream', 'ivory', 'off-white', 'ecru'):
        return 'Whites'
    if color in ('black', 'navy', 'dark', 'charcoal', 'dark blue',
                 'dark green', 'dark grey', 'dark gray', 'burgundy',
                 'dark brown', 'dark red'):
        return 'Darks'
    return 'Lights'


def _temp_bucket(washing_text: str) -> int:
    """Extract temperature bucket (30/40/60) from care instruction text.
    Returns TEMP_COLD (30) when temperature is unknown or null."""
    if not washing_text:
        return TEMP_COLD
    import re
    match = re.search(r'(\d{2,3})\s*°?\s*[cC]', washing_text)
    if match:
        temp = int(match.group(1))
        if temp <= 30:
            return TEMP_COLD
        if temp <= 40:
            return TEMP_WARM
        return TEMP_HOT
    return TEMP_COLD  # null/unknown → coldest load


def _is_special_care(analysis) -> bool:
    """Returns True if garment cannot go in a washing machine."""
    washing = (analysis.washing or '').lower()
    return any(kw in washing for kw in SPECIAL_CARE_KEYWORDS)


def _extract_warnings(analysis) -> list[str]:
    """Extract human-readable warning strings from analysis fields."""
    warnings = []
    drying = (analysis.drying or '').lower()
    bleach = (analysis.bleach or '').lower()
    if 'air dry' in drying or 'do not tumble' in drying or 'hang dry' in drying:
        warnings.append('Air dry only')
    if 'no bleach' in bleach or 'do not bleach' in bleach or 'bleach free' in bleach:
        warnings.append('No bleach')
    if analysis.is_delicate:
        warnings.append('Delicate — gentle cycle')
    return warnings


def group_into_loads(garments) -> dict:
    """
    Group garments into machine-wash loads and a special-care list.

    Args:
        garments: iterable of Garment objects with care_analysis pre-fetched.

    Returns:
        {
          'loads': [
              {
                'color_group': 'Darks',
                'temp': 30,
                'is_delicate': False,
                'garments': [...],  # list of Garment objects
                'warnings': ['Air dry only'],  # union of all garment warnings
              },
              ...  # sorted by len(garments) descending
          ],
          'special_care': [
              {
                'garment': <Garment>,
                'care_method': 'Dry clean only',
              },
              ...
          ],
          'total_garments': N,
          'total_loads': M,
        }
    """
    machine_wash = []
    special_care = []

    for garment in garments:
        analysis = garment.care_analysis
        if _is_special_care(analysis):
            care_method = analysis.washing or 'Special care required'
            special_care.append({'garment': garment, 'care_method': care_method})
        else:
            machine_wash.append(garment)

    # Group machine-wash garments by (color_group, temp_bucket, is_delicate)
    # Delicates separation: delicates only get their own load when the temp
    # or cycle would conflict — i.e., their color+temp group contains normals.
    buckets: dict[tuple, list] = {}
    for garment in machine_wash:
        analysis = garment.care_analysis
        key = (
            _color_group(garment),
            _temp_bucket(analysis.washing),
            analysis.is_delicate,
        )
        buckets.setdefault(key, []).append(garment)

    # Merge delicate bucket into normal bucket when no conflict exists:
    # a delicates-only bucket with matching (color_group, temp) and no normal
    # garments in that same (color_group, temp) combination can be merged.
    merged_buckets: dict[tuple, list] = {}
    for (color_group, temp, is_del), items in buckets.items():
        normal_key = (color_group, temp, False)
        if is_del and normal_key not in buckets:
            # No normal garments in same color+temp — merge delicates in
            merged_buckets.setdefault(normal_key, []).extend(items)
        else:
            merged_buckets.setdefault((color_group, temp, is_del), []).extend(items)

    loads = []
    for (color_group, temp, is_del), garment_list in merged_buckets.items():
        all_warnings = []
        for g in garment_list:
            all_warnings.extend(_extract_warnings(g.care_analysis))
        # Deduplicate warnings while preserving order
        seen = set()
        unique_warnings = []
        for w in all_warnings:
            if w not in seen:
                seen.add(w)
                unique_warnings.append(w)
        loads.append({
            'color_group': color_group,
            'temp': temp,
            'is_delicate': is_del,
            'garments': garment_list,
            'warnings': unique_warnings,
        })

    # Sort: biggest load first
    loads.sort(key=lambda l: len(l['garments']), reverse=True)

    return {
        'loads': loads,
        'special_care': special_care,
        'total_garments': len(machine_wash) + len(special_care),
        'total_loads': len(loads),
    }
```

**Critical design note:** The function is pure with respect to the database. All ORM access happens in the view before calling `group_into_loads()`. Tests construct plain Python objects (or use Django test DB) — no mocking of ORM calls needed inside the function.

### Pattern 5: View Structure

```python
# laundry/views.py (sketch)

@login_required
def basket_detail(request, basket_pk):
    basket = get_object_or_404(Basket, pk=basket_pk, user=request.user)
    # Touch last_used_at without full model save
    Basket.objects.filter(pk=basket_pk).update(last_used_at=timezone.now())
    
    all_analyzed = _analyzed_garments(request.user)
    user_baskets = Basket.objects.filter(user=request.user)  # ordered by -last_used_at
    
    try:
        saved_plan = basket.saved_plan
    except SavedPlan.DoesNotExist:
        saved_plan = None
    
    context = {
        'basket': basket,
        'baskets': user_baskets,
        'analyzed_garments': all_analyzed,
        'categories': CATEGORY_CHOICES,  # for dropdown filter
        'saved_plan': saved_plan,
    }
    return render(request, 'laundry/basket_detail.html', context)
```

**Plan generation:** Because the plan auto-updates live on selection change, plan generation is handled client-side JavaScript calling a JSON endpoint (or done server-side on form POST). Given the "out of scope: WebSockets/async" constraint and the simplicity of the grouping function, plan generation on POST is the right approach — JavaScript sends a form POST with selected garment PKs, Django returns JSON or re-renders the plan section via HTMX-style form POST with `HX-Request` header check. However, since HTMX is not in the stack, the simplest approach is a separate `POST /basket/<pk>/plan/` endpoint that returns JSON, called by vanilla JS on each selection change.

### Pattern 6: JavaScript Interaction Pattern

**What:** Inline `<script>` with vanilla JS manages selection state, filter, sticky button, and live plan fetch.
**Established precedent:** No Alpine.js or HTMX in the project. Stick to inline scripts as used elsewhere.

```html
<script>
// Selection state: Set of garment PKs (strings)
const selected = new Set(
  JSON.parse('{{ basket_garment_pks_json|escapejs }}')
);

const MAX = 20;
const MIN = 2;

function updateButton() {
  const count = selected.size;
  const btn = document.getElementById('create-plan-btn');
  btn.textContent = `Create Laundry Plan (${count})`;
  btn.disabled = count < MIN;
  btn.classList.toggle('opacity-50', count < MIN);
}

function toggleGarment(pk) {
  if (selected.has(pk)) {
    selected.delete(pk);
  } else {
    if (selected.size >= MAX) {
      document.getElementById('max-notice').classList.remove('hidden');
      return;
    }
    selected.add(pk);
  }
  document.getElementById('max-notice').classList.add('hidden');
  updateCard(pk);
  updateButton();
  updateCountLabel();
  if (selected.size >= MIN) debouncedFetchPlan();
}

// Debounced plan fetch — avoid hammering server on rapid selection changes
let fetchTimer;
function debouncedFetchPlan() {
  clearTimeout(fetchTimer);
  fetchTimer = setTimeout(fetchPlan, 300);
}

async function fetchPlan() {
  showSpinner();
  const pks = Array.from(selected);
  const res = await fetch('{% url "laundry:plan_json" basket.pk %}', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': '{{ csrf_token }}',
    },
    body: JSON.stringify({ garment_pks: pks }),
  });
  const data = await res.json();
  renderPlan(data);
  hidePlanSection(false);
}
</script>
```

**Note on Tailwind CSS v4 dynamic classes:** Any class used only in inline scripts (e.g. `hidden`) must exist in templates or the `@source inline(...)` directives in `main.css`. `hidden` is a standard Tailwind utility — it will be picked up from templates automatically.

### Anti-Patterns to Avoid

- **Calling `group_into_loads()` inside a template tag:** The function should live in `services/grouping.py` and be called in the view or a JSON endpoint, never in a template.
- **Storing garment selection in Django sessions:** Selection state should be stored in the Basket model (database), not session, so it persists across devices and browser closes.
- **N+1 on garment → care_analysis:** Always use `select_related('care_analysis')` when fetching basket garments before calling `group_into_loads()`.
- **Direct float arithmetic for temperatures:** Temperature buckets are integer comparisons — no floats, no rounding issues.
- **Using Django messages for plan generation errors:** The plan endpoint returns JSON; errors are rendered client-side, not via Django's messages framework.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Color group inference | Custom regex on color names | Simple lookup list of known white/dark color names + `'Lights'` default | Garment colors are user-entered free text; a short whitelist + default covers 90% of cases reliably |
| Temperature extraction | Complex NLP parser | Single `re.search(r'(\d{2,3})\s*°?\s*[cC]', text)` regex | Care instruction text from GPT-4o is consistently formatted; a simple pattern is sufficient |
| Modal dialogs | Custom JS modal library | Inline `<div>` toggle with `hidden` class | Project already uses this pattern (no dialog library in stack) |
| Sticky button | JS scroll-position calculations | `position: fixed; bottom: 0` with Tailwind `fixed bottom-0 inset-x-0` | CSS handles this without JS |
| Basket last-used ordering | Custom timestamp logic | `Basket.Meta.ordering = ['-last_used_at']` + `auto_now=True` | Django ORM handles ordering automatically |

**Key insight:** The grouping domain looks complex but the data is already clean and structured (GPT-4o normalized it in Phase 3). Temperature is a number in text, color group is inferrable from a short lookup list, and delicates is already a boolean field. Don't over-engineer the classification.

---

## Common Pitfalls

### Pitfall 1: Cross-App QuerySet — Garment Deleted Mid-Session

**What goes wrong:** User opens basket page, deletes a garment from another tab, then triggers plan generation. The POST contains a PK that no longer exists.
**Why it happens:** Selection state is client-side; garment deletion is server-side.
**How to avoid:** In the plan JSON endpoint, filter selected PKs against the database: `Garment.objects.filter(pk__in=pks, user=request.user, care_analysis__isnull=False)`. Silently ignore missing PKs (per user decision in CONTEXT.md). If the filtered set drops below 2, return a JSON error response.
**Warning signs:** `DoesNotExist` or `ValueError` in plan endpoint logs.

### Pitfall 2: `last_used_at` Auto-Update on Basket List Renders

**What goes wrong:** Simply rendering the basket list re-saves the Basket object, updating `last_used_at` and scrambling the dropdown order.
**Why it happens:** `auto_now=True` fires on every `.save()` call, including incidental saves.
**How to avoid:** Use `Basket.objects.filter(pk=pk).update(last_used_at=timezone.now())` explicitly only when the user switches active basket. Do not call `basket.save()` for read operations.

### Pitfall 3: Tailwind CSS v4 Dynamic Classes Not Compiled

**What goes wrong:** Classes added only in inline `<script>` strings (e.g., `'opacity-50'`, `'hidden'`) are not included in the compiled CSS, causing invisible styling failures.
**Why it happens:** Tailwind v4's content scanner only parses template files (`.html`), not JS strings.
**How to avoid:** Ensure all dynamic classes appear in at least one template directly (not just in JS strings). Add a safety comment block to `main.css` `@source inline(...)` with any purely-JS-generated classes that don't appear in HTML: `@source inline("opacity-50 cursor-not-allowed")`. Run `tailwind build --force` when adding new classes from templates.
**Warning signs:** Style is correct in dev (where all classes compile) but missing in prod; or wrong class compiled.

### Pitfall 4: 5-Basket Limit Not Enforced Server-Side

**What goes wrong:** Client disables the "New Basket" button after 5, but a direct POST request bypasses this, creating a 6th basket.
**Why it happens:** Client-side guards are cosmetic only.
**How to avoid:** In the basket create view, check `Basket.objects.filter(user=request.user).count() >= 5` before creating. Return a 400 or redirect with an error message if the limit is reached.

### Pitfall 5: Plan JSON Endpoint CSRF

**What goes wrong:** Vanilla JS fetch to plan JSON endpoint fails with 403 Forbidden.
**Why it happens:** Django CSRF middleware requires `X-CSRFToken` header on non-safe methods (POST, PUT, DELETE).
**How to avoid:** Read `{{ csrf_token }}` from the template and pass it in `X-CSRFToken` header in every fetch call. This is already established in the Phase 3 analysis form pattern.

### Pitfall 6: Stale Plan Detection Edge Case

**What goes wrong:** `SavedPlan.snapshot_analysis_max_updated` is null when garments had no `updated_at` at save time, causing false-positive stale notices.
**Why it happens:** `CareAnalysis.updated_at` is `auto_now=True` so it is always set — but the SavedPlan field is nullable to handle the case where basket is saved with no garments.
**How to avoid:** When saving a plan, compute `CareAnalysis.objects.filter(garment__in=basket_garments).aggregate(Max('updated_at'))['updated_at__max']`. When loading, compare against current max — show stale notice only if current max is strictly after `snapshot_analysis_max_updated`.

---

## Code Examples

Verified patterns from existing project code:

### Existence Annotation (Phase 3 established pattern — reuse for basket view)

```python
# Source: wardrobe/views.py (garment_list)
from django.db.models import Exists, OuterRef

garments = Garment.objects.filter(user=request.user).annotate(
    has_analysis=Exists(CareAnalysis.objects.filter(garment=OuterRef('pk'))),
)
```

For basket: use `filter(care_analysis__isnull=False)` instead of annotation since we only want analyzed garments (no need to annotate — just filter).

### Cross-App Model Reference

```python
# laundry/models.py
garments = models.ManyToManyField(
    'wardrobe.Garment',          # string ref avoids circular import
    through='BasketGarment',
    related_name='baskets',
)
```

### User Isolation (Phase 2 established pattern — always apply)

```python
# Source: wardrobe/views.py (garment_detail)
basket = get_object_or_404(Basket, pk=basket_pk, user=request.user)
```

### Template Color Classes (verified against assets/src/main.css)

Available for Special Care amber header: `bg-amber-100`, `text-amber-800`, `border-amber-300`
Brand accent for selected card border: `border-deep-space-500` or `border-dark-teal-500`
Plan results section divider: existing `text-deep-space-900` heading pattern

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Django test runner (built-in, Django 5.2) |
| Config file | none — uses `manage.py test` |
| Quick run command | `DJANGO_SETTINGS_MODULE=laundry_advisor.settings.dev python manage.py test laundry.tests.test_grouping --verbosity=2` |
| Full suite command | `DJANGO_SETTINGS_MODULE=laundry_advisor.settings.dev python manage.py test` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BSKT-01 | User can select garments for basket | integration (view POST) | `python manage.py test laundry.tests.test_views.BasketSelectionTest` | Wave 0 |
| BSKT-02 | Only analyzed garments are eligible | unit | `python manage.py test laundry.tests.test_grouping.EligibilityQueryTest` | Wave 0 |
| BSKT-03 | Grouping by temp + color + delicates | unit | `python manage.py test laundry.tests.test_grouping.GroupingLogicTest` | Wave 0 |
| BSKT-04 | Load cards display garments + settings + warnings | integration (view/template) | `python manage.py test laundry.tests.test_views.PlanDisplayTest` | Wave 0 |

### Sampling Rate

- **Per task commit:** `DJANGO_SETTINGS_MODULE=laundry_advisor.settings.dev python manage.py test laundry --verbosity=1`
- **Per wave merge:** `DJANGO_SETTINGS_MODULE=laundry_advisor.settings.dev python manage.py test`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- `laundry/tests/__init__.py` — package marker
- `laundry/tests/test_grouping.py` — unit tests for `group_into_loads()` covering:
  - null/unknown temperature defaults to coldest load (30°C)
  - dry-clean-only garments routed to special_care, not loads
  - hand-wash-only garments routed to special_care
  - Whites / Lights / Darks classification
  - delicates separation when mixed with normals at same temp+color
  - delicates merged into load when no normals at that temp+color
  - warnings: air-dry, no-bleach, delicate-cycle extracted correctly
  - loads sorted by garment count descending
  - all special-care basket: empty loads list, non-empty special_care
  - empty garments list: returns empty loads and special_care

---

## Open Questions

1. **Color group inference from free-text garment color**
   - What we know: `Garment.color` is a free-text CharField (max 100). Values are user-entered (e.g., "Navy Blue", "forest green", "dark red/maroon").
   - What's unclear: Should color group inference also consider `CareAnalysis.washing` or `ai_summary` to detect garment hue? Or is the `Garment.color` field alone sufficient?
   - Recommendation: Use `Garment.color` alone with a short whitelist for known dark/white values; default to Lights. This matches the user's expectation that the field is the canonical color source. Flag to user if color is blank — treat blank color as "Lights" (safest choice for unknown colors).

2. **JSON endpoint vs. server-side render for live plan updates**
   - What we know: Plan auto-updates on selection change. No HTMX or WebSockets in stack.
   - What's unclear: Should the plan be rendered server-side (Django template, returned as HTML fragment) or client-side (JSON → JS renders HTML)?
   - Recommendation: JSON endpoint returning a plan data structure; JS constructs the plan HTML. This avoids returning raw HTML from a POST endpoint and keeps the grouping logic testable independently of template rendering.

3. **Basket "active" concept across page loads**
   - What we know: Users can have up to 5 baskets. The basket page URL is `/basket/<pk>/`. "Most recently used" ordering is by `last_used_at`.
   - What's unclear: When a user navigates to `/basket/` (no PK), should they be redirected to the most recently used basket, or shown a basket picker?
   - Recommendation: Redirect to the most recently used basket (`Basket.objects.filter(user=request.user).first()` via `last_used_at` ordering). Show "create first basket" if none exist.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.13 | Runtime | Yes | 3.13.5 | — |
| Django 5.2 | Web framework + ORM | Yes | 5.2 (in .venv) | — |
| Django test runner | Unit/integration tests | Yes | Django 5.2 built-in | — |
| django-tailwind-cli | CSS build | Yes | >=4.5 (pinned) | — |
| Pillow | Garment image fields | Yes | >=10.0 (pinned) | — |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** None.

**Note:** pytest is not installed in the project venv. Django's built-in test runner is used (confirmed functional via `manage.py test --help`).

---

## Project Constraints (from CLAUDE.md)

No `CLAUDE.md` exists in the working directory. No project-level constraints to carry forward beyond what is captured in STATE.md and the decisions above.

**Key constraints from STATE.md (carry-forward):**
- No Celery / async task queues — synchronous calls only
- Django 5.2 LTS confirmed
- Split settings (base/dev/prod) — new app config changes go in `base.py`
- S3 storage active in production — garment photo URLs served directly without signed URLs
- `get_object_or_404(Model, pk=pk, user=request.user)` pattern for user isolation (returns 404 not 403)
- `STORAGES` dict must be extended with `STORAGES["key"] = {...}` not reassigned whole dict
- `tailwind build --force` required when template classes change

---

## Sources

### Primary (HIGH confidence)

- Existing codebase — `wardrobe/models.py`, `wardrobe/views.py`, `wardrobe/services/analysis.py`, `templates/`, `assets/src/main.css` — all patterns verified by reading live project files
- `requirements.txt` — exact pinned versions confirmed by reading file
- `.planning/STATE.md` — accumulated decisions from Phases 1–3 verified as current
- `manage.py test --help` — Django test runner confirmed functional (ran successfully)

### Secondary (MEDIUM confidence)

- Django 5.2 documentation patterns (ManyToManyField through table, `auto_now`, `select_related`) — consistent with what is used in wardrobe app; no contradictions found
- Tailwind CSS v4 `@source inline()` directive pattern — confirmed in `assets/src/main.css`

### Tertiary (LOW confidence)

- Grouping algorithm design (color group inference, temperature bucket thresholds, delicates merge logic) — derived from CONTEXT.md spec + general laundry domain knowledge; not sourced from external documentation

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are pinned in requirements.txt and already in use
- Architecture: HIGH — new app follows identical pattern to existing `wardrobe` app
- Grouping algorithm: MEDIUM — design is sound but exact thresholds (which colors are "Darks") depend on user-entered free text; may need iteration
- Pitfalls: HIGH — drawn from Phase 1–3 execution notes in STATE.md plus Django patterns

**Research date:** 2026-04-02
**Valid until:** 2026-05-02 (stable stack; no fast-moving dependencies)
