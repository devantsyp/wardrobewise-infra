"""
Pure-Python grouping algorithm for the Laundry Basket feature.

group_into_loads() takes a list of garment dicts and returns a structured
plan with machine-wash loads and a special-care list.

No ORM calls — the view layer assembles the garment dict list.
"""

import re
from collections import defaultdict


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DARKS_KEYWORDS = [
    'dark blue', 'dark grey', 'dark gray', 'dark brown',
    'dark green', 'dark red', 'dark',
    'black', 'navy', 'charcoal',
]

WHITES_KEYWORDS = ['white', 'cream', 'ivory', 'off-white', 'off white']

# Special care detection keywords mapped to display label
SPECIAL_CARE_PATTERNS = [
    ('dry clean', 'Dry clean only'),
    ('dryclean', 'Dry clean only'),
    ('dry-clean', 'Dry clean only'),
    ('hand wash only', 'Hand wash only'),
    ('hand-wash only', 'Hand wash only'),
    ('hand wash', 'Hand wash only'),
    ('do not wash', 'Do not wash'),
    ('do not machine wash', 'Do not machine wash'),
    ('spot clean', 'Spot clean only'),
    ('no washing', 'Do not wash'),
]

# Temperature buckets (Celsius)
TEMP_BUCKETS = [30, 40, 60]

# Celsius regex — matches patterns like 30°C, 30 degrees C, 40C, etc.
_CELSIUS_RE = re.compile(
    r'(\d+)\s*(?:°[Cc]|degrees?\s*[Cc]|[Cc]\b)',
    re.IGNORECASE,
)

# Keyword fallback for temperature
_TEMP_KEYWORDS = [
    ('cold', 30),
    ('cool', 30),
    ('warm', 40),
    ('hot', 60),
]

# Warning detection: (keywords to scan, canonical warning label)
_WARNING_RULES = [
    (['air dry', 'lay flat', 'line dry', 'hang to dry'], 'air dry only'),
    (['no bleach', 'do not bleach', 'non-chlorine', 'bleach free'], 'no bleach'),
    (['delicate cycle', 'gentle cycle', 'delicate wash'], 'delicate cycle'),
    (['do not tumble dry', 'no tumble'], 'no tumble dry'),
]


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _classify_color(color: str) -> str:
    """Return 'darks', 'whites', or 'lights' for a free-text color string."""
    lower = color.lower()
    for kw in DARKS_KEYWORDS:
        if kw in lower:
            return 'darks'
    for kw in WHITES_KEYWORDS:
        if kw in lower:
            return 'whites'
    return 'lights'


def _extract_temperature(washing: str):
    """
    Parse Celsius temperature from washing instructions.

    Returns (temperature: int | None, explicit: bool).
    - temperature: integer Celsius, or None if unparseable.
    - explicit: True if parsed from an explicit numeric value, False if keyword fallback.
    """
    lower = washing.lower()

    # 1. Try explicit Celsius regex
    match = _CELSIUS_RE.search(washing)
    if match:
        return int(match.group(1)), True

    # 2. Keyword fallback
    for kw, temp in _TEMP_KEYWORDS:
        if kw in lower:
            return temp, False

    # 3. Unparseable
    return None, False


def _normalise_bucket(temp: int | None) -> int:
    """Snap temperature to nearest of [30, 40, 60]."""
    if temp is None:
        return 30
    if temp <= 35:
        return 30
    if temp <= 50:
        return 40
    return 60


def _extract_warnings(washing: str, drying: str, bleach: str) -> list[str]:
    """Return list of canonical warning strings applicable to a garment."""
    combined = (washing + ' ' + drying + ' ' + bleach).lower()
    warnings = []
    for keywords, label in _WARNING_RULES:
        for kw in keywords:
            if kw in combined:
                warnings.append(label)
                break  # each warning added at most once per garment
    return warnings


def _is_special_care(washing: str) -> str | None:
    """
    Check if garment requires special care (non-machine-washable).

    Returns care_method string if special care, else None.
    """
    lower = washing.lower()
    for keyword, label in SPECIAL_CARE_PATTERNS:
        if keyword in lower:
            return label
    return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def group_into_loads(garments: list[dict]) -> dict:
    """
    Group garments into machine-wash loads and a special-care list.

    Args:
        garments: list of dicts with keys:
            pk, name, photo_url, category, color,
            washing, drying, bleach, is_delicate

    Returns:
        {
            'loads': [...sorted by garment count desc...],
            'special_care': [...],
        }
    """
    loads_out = []
    special_care_out = []

    # --- Step 1: separate special-care garments ---
    machine_wash = []
    for g in garments:
        care_method = _is_special_care(g.get('washing', ''))
        if care_method:
            special_care_out.append({
                'pk': g['pk'],
                'name': g['name'],
                'photo_url': g.get('photo_url'),
                'care_method': care_method,
            })
        else:
            machine_wash.append(g)

    if not machine_wash:
        return {'loads': [], 'special_care': special_care_out}

    # --- Step 2-4: classify and group ---
    # Group by (color_group, temperature_bucket)
    color_temp_groups: dict[tuple, list[dict]] = defaultdict(list)

    garment_meta = {}  # pk -> {color_group, temp_bucket, temp_label, warnings}

    for g in machine_wash:
        color_group = _classify_color(g.get('color', ''))
        raw_temp, explicit = _extract_temperature(g.get('washing', ''))
        temp_bucket = _normalise_bucket(raw_temp)
        temp_label = f"{temp_bucket}°C"
        warnings = _extract_warnings(
            g.get('washing', ''),
            g.get('drying', ''),
            g.get('bleach', ''),
        )

        garment_meta[g['pk']] = {
            'color_group': color_group,
            'temp_bucket': temp_bucket,
            'temp_label': temp_label,
            'is_delicate': g.get('is_delicate', False),
            'warnings': warnings,
            'garment': g,
        }
        color_temp_groups[(color_group, temp_bucket)].append(g['pk'])

    # --- Step 4 (continued): handle delicates splitting ---
    for (color_group, temp_bucket), pks in color_temp_groups.items():
        temp_label = f"{temp_bucket}°C"
        delicate_pks = [pk for pk in pks if garment_meta[pk]['is_delicate']]
        normal_pks = [pk for pk in pks if not garment_meta[pk]['is_delicate']]

        if delicate_pks and normal_pks:
            # Mixed — split into two loads
            for group_pks, cycle in [(delicate_pks, 'delicate'), (normal_pks, 'normal')]:
                load = _build_load(
                    color_group, temp_bucket, temp_label, cycle,
                    group_pks, garment_meta,
                )
                loads_out.append(load)
        elif delicate_pks:
            # All delicate
            load = _build_load(
                color_group, temp_bucket, temp_label, 'delicate',
                delicate_pks, garment_meta,
            )
            loads_out.append(load)
        else:
            # All normal
            load = _build_load(
                color_group, temp_bucket, temp_label, 'normal',
                normal_pks, garment_meta,
            )
            loads_out.append(load)

    # --- Step 7: sort by garment count descending ---
    loads_out.sort(key=lambda load: len(load['garments']), reverse=True)

    return {'loads': loads_out, 'special_care': special_care_out}


def _build_load(
    color_group: str,
    temperature: int,
    temp_label: str,
    cycle: str,
    pks: list[int],
    garment_meta: dict,
) -> dict:
    """Build a single load dict from a list of garment PKs."""
    garments_list = []
    all_warnings = set()

    for pk in pks:
        meta = garment_meta[pk]
        g = meta['garment']
        garment_warnings = meta['warnings']
        all_warnings.update(garment_warnings)
        garments_list.append({
            'pk': g['pk'],
            'name': g['name'],
            'photo_url': g.get('photo_url'),
            'warnings': garment_warnings,
        })

    return {
        'color_group': color_group,
        'temperature': temperature,
        'temp_label': temp_label,
        'cycle': cycle,
        'garments': garments_list,
        'warnings': sorted(all_warnings),
    }
