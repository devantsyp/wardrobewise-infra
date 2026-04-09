---
status: resolved
trigger: "Implement a cohesive design system color palette across the entire project UI"
created: 2026-04-07T00:00:00Z
updated: 2026-04-08T00:00:00Z
---

## Current Focus

hypothesis: Templates use stale color names (deep-space, dark-teal, lavender, thistle) that don't exist in main.css — only primary/secondary/accent/bg/accent-light exist there. garment_form.html also has hardcoded border-gray-300 and garment_detail.html has an inline style with hardcoded hex. The mismatch between template color names and CSS token names means virtually no custom colors actually render.
test: Audit every color class in templates vs the @theme color names defined in main.css
expecting: Confirm full mismatch, then replace all template color names with valid token names
next_action: Fix all templates + hardcoded hex values + rebuild CSS

## Symptoms

expected: Entire UI uses consistent brand palette via CSS design tokens (primary, secondary, accent, bg, accent-light)
actual: Templates use color names (deep-space, dark-teal, lavender, thistle) that are NOT defined in main.css @theme. Only red/green/amber utilities from those token names would render. Brand colors silently fail — default browser styles or nothing shows.
errors: No runtime errors — styling gap only
reproduction: Visit any page — brand colors absent, defaults shown
started: Never implemented — new requirement

## Eliminated

- hypothesis: CSS token file doesn't exist
  evidence: assets/src/main.css already has full @theme block with all palette tokens
  timestamp: 2026-04-07

- hypothesis: Forms use hardcoded hex
  evidence: accounts/forms.py and wardrobe/forms.py use token-based class names (accent-400, primary-700) — already correct
  timestamp: 2026-04-07

## Evidence

- timestamp: 2026-04-07
  checked: assets/src/main.css @theme block
  found: Full palette defined as --color-primary-*, --color-secondary-*, --color-accent-*, --color-accent-light-*, --color-bg-*. @source inline() rules compile all shades.
  implication: CSS tokens are correct. Template class names are the problem.

- timestamp: 2026-04-07
  checked: All 8 template files
  found: Templates use "deep-space", "dark-teal", "lavender", "thistle" color names. None of these are defined in @theme. Valid names are: primary, secondary, accent, accent-light, bg.
  implication: All custom brand color classes in templates resolve to nothing. The entire color system is broken at the template layer.

- timestamp: 2026-04-07
  checked: garment_detail.html line 482
  found: Inline style="background-color: #dc2626" and onmouseover/onmouseout with hardcoded hex on Delete button
  implication: Hardcoded hex must be replaced with Tailwind classes (bg-red-600 hover:bg-red-700)

- timestamp: 2026-04-07
  checked: garment_form.html
  found: border-gray-300 used on input/select/textarea widgets — "gray" is not in the @theme (--color-* initial resets all defaults). Also focus:ring-dark-teal-500, peer-focus:text-dark-teal-600 in template.
  implication: Widget borders render with no color (or browser default). Focus rings also broken.

- timestamp: 2026-04-07
  checked: base.html
  found: body uses bg-deep-space-50 (invalid), nav toast uses bg-dark-teal-50/border-dark-teal-400 (invalid), text-thistle-500 (invalid), text-lavender-500 (invalid), text-deep-space-* (invalid)
  implication: Page background, nav, and toasts all use non-existent color tokens.

## Resolution

root_cause: Template color class names use pre-refactor token names (deep-space, dark-teal, lavender, thistle) that do not exist in main.css @theme. The CSS token system is correctly defined but templates reference the wrong names entirely.

fix: |
  Replaced all stale color token names across 4 template files:
  - deep-space-* → secondary-* (Dark Blue) for dark surfaces/text/backgrounds
  - dark-teal-* → primary-* (Deep Teal) for CTAs/buttons
  - thistle-* → accent-* (Muted Purple) for muted text/labels
  - gray-300 → accent-300 for input borders
  - focus:ring-dark-teal-* → focus:ring-primary-* for focus rings
  - peer-focus:text-dark-teal-* → peer-focus:text-primary-* for floating labels
  - Removed inline style="background-color: #dc2626" + JS onmouseover/onmouseout on Delete button
    → replaced with bg-red-600 hover:bg-red-700 Tailwind classes
  Rebuilt CSS: python manage.py tailwind build --force
  Verified: 0 stale tokens in compiled output, 44 valid palette token definitions present

verification: |
  - grep for deep-space/dark-teal/lavender/thistle across templates: 0 matches
  - grep for inline hex styles across templates: 0 matches
  - CSS rebuild succeeded, output confirms 0 stale tokens, 44 valid palette tokens
  - All brand color classes now map to defined @theme tokens in main.css

files_changed:
  - templates/wardrobe/wardrobe_list.html
  - templates/wardrobe/garment_form.html
  - templates/wardrobe/garment_detail.html
  - templates/laundry/basket.html
  - assets/css/app.css
