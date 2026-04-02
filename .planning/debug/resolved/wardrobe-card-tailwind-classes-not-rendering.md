---
status: resolved
trigger: "wardrobe-card-tailwind-classes-not-rendering"
created: 2026-04-01T00:00:00Z
updated: 2026-04-01T00:01:00Z
---

## Current Focus

hypothesis: @theme resets all colors including built-in green/amber, and @source inline only covers custom palettes — so border-green-500 and amber-* classes are undefined and generate no CSS
test: Read main.css and confirm green/amber are absent from both @theme and @source inline directives
expecting: Fix by adding green and amber color definitions to @theme and safelisting their utility classes via @source inline
next_action: Add green and amber palettes to main.css, rebuild CSS

## Symptoms

expected: Garment cards with completed analysis should have a visible green border (border-2 border-green-500). Delicate badge should be amber-colored (bg-amber-100 text-amber-800).
actual: Badge text appears black (default color). Green border is invisible/missing entirely.
errors: No Python errors. Pure CSS/Tailwind rendering issue.
reproduction: Visit /wardrobe/ after analyzing a garment. Cards show no green border. Delicate badge text is black.
started: After previous fix was applied. Never worked correctly.

## Eliminated

- hypothesis: Template uses dynamic/concatenated class names that Tailwind can't scan
  evidence: wardrobe_list.html line 22 uses full static string "border-2 border-green-500" and lines 49 use full "bg-amber-100 text-amber-800" — Tailwind can detect these fine
  timestamp: 2026-04-01T00:00:00Z

- hypothesis: Tailwind content paths don't include templates directory
  evidence: Project uses Tailwind v4 (@import "tailwindcss") which auto-scans; content config not the issue
  timestamp: 2026-04-01T00:00:00Z

## Evidence

- timestamp: 2026-04-01T00:00:00Z
  checked: templates/wardrobe/wardrobe_list.html lines 22, 49
  found: Full static class strings present — "border-2 border-green-500" on line 22, "bg-amber-100 text-amber-800 text-xs font-semibold" on line 49
  implication: JIT scanning is not the issue; classes are detectable as static strings

- timestamp: 2026-04-01T00:00:00Z
  checked: assets/src/main.css @theme block and @source inline directives
  found: @theme has "--color-*: initial" which resets ALL built-in Tailwind colors including green and amber. @source inline only covers custom palettes (deep-space, dark-teal, lavender, thistle, lilac-ash, red). Neither green nor amber colors are defined in @theme, so border-green-500 and bg-amber-100 / text-amber-800 generate no CSS output.
  implication: ROOT CAUSE CONFIRMED — green and amber color tokens must be added to @theme and their utilities safelisted

## Resolution

root_cause: assets/src/main.css resets all Tailwind built-in colors via "--color-*: initial" in @theme, then only re-defines custom palettes. The classes border-green-500, bg-amber-100, and text-amber-800 reference colors that no longer exist, so Tailwind generates no CSS for them.
fix: Added green (50–950) and amber (50–950) color definitions to @theme block in assets/src/main.css, then added two @source inline() lines to safelist bg/text/border/ring utilities for both palettes including hover variants. Rebuilt CSS — all three classes confirmed present in assets/css/app.css.
verification: Confirmed via grep: .bg-amber-100{background-color:var(--color-amber-100)}, .text-amber-800{color:var(--color-amber-800)}, .border-green-500{border-color:var(--color-green-500)} all present in compiled output.
files_changed:
  - assets/src/main.css
  - assets/css/app.css
