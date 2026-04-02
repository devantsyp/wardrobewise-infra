---
status: resolved
trigger: "simplify-garment-categories"
created: 2026-04-01T00:00:00Z
updated: 2026-04-01T00:00:00Z
---

## Current Focus

hypothesis: confirmed — CATEGORY_CHOICES in models.py was the single source of truth
test: ran migration and verified all 6 existing garments migrated to new slug values
expecting: all garments show valid new category slugs
next_action: complete — archived

## Symptoms

expected: Garment category dropdown shows 8 simplified options
actual: Garment category dropdown shows 16 granular options
errors: No errors — this is a feature change to simplify UX
reproduction: Navigate to garment details/create/edit page and view the category dropdown
started: Planned change, not a regression

## Eliminated

## Evidence

- timestamp: 2026-04-01T00:00:00Z
  checked: wardrobe/models.py CATEGORY_CHOICES
  found: DB values are display strings (e.g., "T-Shirts & Tops"), not slugs. max_length=50.
  implication: Data migration must map old display-string values to new slugs.

- timestamp: 2026-04-01T00:00:00Z
  checked: wardrobe/forms.py
  found: GarmentForm is a ModelForm with no explicit choices override — inherits from model automatically.
  implication: Only models.py needs choices updated; form inherits automatically.

- timestamp: 2026-04-01T00:00:00Z
  checked: wardrobe/views.py
  found: No filtering, querying, or hardcoded references to category values.
  implication: No view changes needed.

- timestamp: 2026-04-01T00:00:00Z
  checked: templates/wardrobe/*.html
  found: Uses form.category.field.choices (dynamic) and garment.get_category_display (built-in). No hardcoded category strings.
  implication: No template changes needed.

- timestamp: 2026-04-01T00:00:00Z
  checked: wardrobe/services/analysis.py
  found: No references to category values or CATEGORY_CHOICES.
  implication: No analysis service changes needed.

- timestamp: 2026-04-01T00:00:00Z
  checked: wardrobe/admin.py
  found: list_filter includes 'category' — works dynamically with whatever choices are on the model.
  implication: No admin changes needed.

- timestamp: 2026-04-01T00:00:00Z
  checked: existing migrations 0001/0002
  found: Hardcode old choices in AlterField/CreateModel — this is fine, they're historical records.
  implication: New migration (0005) will handle AlterField with new choices + RunPython data migration.

## Resolution

root_cause: CATEGORY_CHOICES in wardrobe/models.py defined 16 options using display strings as DB values (e.g., "T-Shirts & Tops"). No other file hardcoded these values — forms, templates, admin, and the analysis service all reference the model dynamically.
fix: Replaced CATEGORY_CHOICES with 8 slug-based entries. Wrote migration 0005 that first runs RunPython to remap old display-string DB values to new slugs, then AlterField to update the field definition.
verification: python manage.py migrate ran OK; manage.py check reports 0 issues; shell query confirmed all 6 existing garments now have valid new slug category values (shirts x4, bottoms x1, hoodies_sweatshirts x1).
files_changed:
  - wardrobe/models.py (CATEGORY_CHOICES replaced)
  - wardrobe/migrations/0005_simplify_garment_categories.py (new migration)
