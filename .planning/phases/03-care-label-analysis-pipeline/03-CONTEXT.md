# Phase 3: Care Label Analysis Pipeline - Context

**Gathered:** 2026-03-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Users trigger a GPT-4o Vision analysis of a care label photo from the garment detail page and receive structured plain-English laundry instructions. Rate limiting (10/day per user), image deduplication, a global budget guard ($9 cumulative), and admin visibility are all enforced. Creating/editing garments and uploading photos are Phase 2 — this phase adds the analysis layer on top.

</domain>

<decisions>
## Implementation Decisions

### Result display

- Simple bullet-point list format — no cards, no sections, no icons
- Displayed inline on the garment detail page (not a separate page)
- Structured as: AI-generated summary sentence first, then bullet list
- Warnings and prohibitions (e.g., "Do not bleach") styled with visual distinction (different color or warning icon) to stand out from positive instructions
- Unknown/unclear fields shown as: "Ironing: Unable to determine — check label manually" (not omitted)
- Delicates flag shown as a warning badge near the instructions (when true)
- Small care label thumbnail shown alongside the instructions section for cross-reference
- Analysis timestamp shown: "Analyzed 2 days ago" style
- If same care label submitted again (dedup hit): subtle muted note below timestamp — "(from previous analysis)"
- If analysis fails: inline error with Retry button in the care instructions section
- Pre-analysis placeholder: "No care instructions yet. Upload a care label photo and click Analyze to get started." with Analyze button nearby
- No distinction between AI-original and user-edited instructions in read mode
- Raw JSON stored immutably — admin only, never shown to users
- AI caveats (e.g., "label partially obscured") not surfaced to users — clean results only
- No action buttons beyond Edit and Re-analyze (no copy, share, print)
- Analysis badge on wardrobe grid: analyzed garments show a visual indicator badge
- Instructions section sits below garment fields on the detail page (below color/fabric/notes)

### Analysis flow & trigger

- Analyze button lives on the garment detail page — not on the wardrobe grid
- Single-step flow: create garment → save → on detail page, click "Analyze Care Label"
- Button label: "Analyze Care Label"
- Button is disabled (with tooltip) if no care label photo exists
- Loading state: button shows spinner + "Analyzing..." — page stays in place
- Synchronous call — page waits, then reloads to show results (no HTMX, standard POST)
- When rate-limited (10/10): Analyze button is hidden/replaced by the rate limit message inline
- When global budget guard hit: Analyze button replaced by "Analysis temporarily unavailable" message
- No confirmation step before triggering — direct action
- Daily limit and budget guard show different messages (see Rate limit UI)

### Edit experience

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

### Rate limit UI

- Daily counter "X / 10 today" displayed in site-wide navigation — visible only on analysis-relevant pages (wardrobe grid, garment detail)
- Counter always visible (shows "0 / 10 today" from the start of each day)
- Counter is color-coded: normal → warning color approaching limit → red/blocked when 10/10 hit
- Page reload updates the counter naturally (consistent with synchronous POST approach)
- When limit hit: inline block near Analyze button area: "Daily limit reached (10/10). Resets in [countdown]."
- Countdown is a live timer counting down to the user's local midnight
- Flash message on first page load after midnight reset: "Your daily analysis allowance has reset — 10 analyses available today."
- Daily limit message and budget guard message are distinct:
  - Daily limit: "Daily limit reached — resets at midnight" with countdown
  - Budget guard: "Analysis temporarily unavailable"

### Claude's Discretion

- Exact color thresholds for warning/red states on the counter
- Specific styling of the Delicate warning badge
- Exact error message copy for disabled Analyze button (no care label tooltip)
- Layout/spacing of the edit form fields
- Loading skeleton or spinner style during Analyze button loading state

</decisions>

<specifics>
## Specific Ideas

- The countdown timer is based on the user's local timezone — "midnight" means midnight where the user is
- The live countdown appears inline in the blocked-state message on the garment detail page (primary location, especially for mobile), not just in the nav

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-care-label-analysis-pipeline*
*Context gathered: 2026-03-27*
