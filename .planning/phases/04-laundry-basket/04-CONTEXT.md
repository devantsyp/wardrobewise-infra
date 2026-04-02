# Phase 4: Laundry Basket - Context

**Gathered:** 2026-04-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Users select multiple analyzed garments and receive a multi-load washing plan that groups compatible garments (by temperature, color group, and fabric sensitivity) and separates incompatible ones. Creating individual garment analyses is Phase 3; production deployment is Phase 5.

</domain>

<decisions>
## Implementation Decisions

### Page Structure
- Dedicated `/basket/` page, own URL (not a modal)
- Page heading: "Plan Your Laundry Basket"
- Page subtitle below heading explaining how to use the basket (for first-time users)
- "Plan Laundry" nav link always visible in the main navigation (no badge/count on the nav link)
- Basket page is a single-page experience: selection grid above, plan results section below

### Basket Selection — Grid
- Photo grid with checkboxes, same column count as the wardrobe grid (responsive)
- Only analyzed garments shown (unanalyzed garments hidden entirely)
- Clicking a card toggles selection only — no navigation to garment detail from basket page
- Visual treatment for selected cards: checkbox + border highlight (brand accent color)
- Card info shown: garment photo + name + category

### Basket Selection — Controls
- Single row above the grid (inline): [Category dropdown] [Select All] [Clear All] — — — [X selected / Y available]
- Category filter: dropdown select
- Select All: selects all analyzed garments regardless of active filter
- Clear All: clears all selected garments regardless of active filter
- Minimum 2 garments required to generate a plan
- Maximum 20 garments per basket
- Sticky "Create Laundry Plan (X)" button fixed at bottom of viewport; full-width bar on mobile
- Button is greyed out with tooltip when fewer than 2 garments selected: "Select at least 2 garments to plan"
- Inline notice shown when user tries to select a 21st garment: "Maximum 20 garments reached"

### Basket Selection — Behaviour
- Clicking "Create Laundry Plan (X)" scrolls smoothly to the plan results section below
- Plan auto-updates live when selection changes (no re-click needed after first generate)
- Spinner or skeleton shown while grouping computes (even if near-instant)
- Selection persists until manually cleared (not cleared after viewing plan)

### Multiple Named Baskets
- Users can have up to 5 named baskets
- Basket selector: dropdown near the page heading showing the active basket name
- New basket creation: modal with a name field + Create/Cancel
- Basket names are not required to be unique (duplicates allowed)
- Baskets listed in dropdown by most recently used first
- Rename and delete available via a separate "Manage Baskets" modal/page
- Delete requires a confirmation step: "Are you sure you want to delete [Name]? This cannot be undone."
- First visit with no baskets: show "Create your first basket" prompt

### Plan Results Section
- Appears below the grid on the same page, separated by a section heading (e.g. "Your Laundry Plan")
- Hidden entirely until the user generates a plan (no empty state for plan section)
- Summary line at top of results: e.g. "Your plan: 3 loads, 12 garments"
- Load cards ordered by number of garments descending (biggest load first)

### Load Cards
- Card-based layout, one card per load
- Card header: "Load [N]: [Color Group] — [Temp] ([X garments])" e.g. "Load 1: Darks — 30°C (5 garments)"
- Card body: mini photo thumbnails with garment name below each
- Card body: wash settings relevant to the load (temperature, cycle, anything that explains the grouping)
- Card body: grouping rationale shown e.g. "Grouped by: Color (Darks) | Temp (30°C)"
- Warnings: inline badges on each garment thumbnail AND a summary warnings section at the card bottom

### Special Care Section
- Shown only when at least one garment is dry-clean-only, hand-wash-only, or otherwise non-machine-washable
- Flat list format: mini thumbnail + garment name + care method per item (no sub-grouping by care type)
- Same card style as load cards but with a distinct header color (e.g. amber/yellow) to signal attention
- If ALL selected garments are special care: notice at top of plan results ("No machine-wash loads for your selection"), then Special Care section

### Grouping Logic
- Color groups: Whites / Lights / Darks (3 groups)
- Delicates separated only when mixing would be problematic (temperature or cycle conflict with normal garments)
- Garments with null/unknown wash temperature: grouped with the coldest load
- Conflicting care instructions (e.g. contradictory data in analysis): Claude's discretion — apply safest interpretation
- 3 compatibility axes: temperature, color group, fabric sensitivity (delicates flag)

### Plan Saving
- "Save Plan" button at the top of the plan results section (explicit save, not auto-save)
- Saved plan is stored alongside the basket in the database
- When returning to a basket with a saved plan, the plan is shown immediately
- If garment analyses were updated since plan was saved: show "Plan may be outdated — re-plan for latest results" notice
- When no plan has been saved yet: plan section is hidden

### Edge Cases
- Garment deleted from wardrobe: silently removed from basket selection
- Garment's analysis deleted: silently removed from basket selection
- Empty analyzed wardrobe: basket page shows empty state with link to wardrobe ("No analyzed garments yet. Analyze some garments first.")

### Claude's Discretion
- Exact spinner/skeleton design for plan loading state
- Exact wording of section headings and button labels (beyond what's specified above)
- Compression/storage format for saved plan JSON
- Keyboard accessibility implementation details
- How stale-plan detection is implemented (e.g. timestamp comparison on analysis vs plan save date)

</decisions>

<specifics>
## Specific Ideas

- Fixed bottom sticky button: full-width bar on mobile (like an iOS action bar)
- "Plan Laundry" in the nav, not "Basket" or "Laundry Basket"
- "Create Laundry Plan (X)" as the button label — explicit about output, live count in parens
- "X selected / Y available" as the count label above the grid
- Plan results section has its own heading (e.g. "Your Laundry Plan") as visual divider from selection grid
- Load card header format: "Load N: Color Group — Temp (X garments)"
- Special Care section uses same card component as loads but with an amber/yellow header color

</specifics>

<deferred>
## Deferred Ideas

- Category filter on the wardrobe page — user wants this but it's outside Phase 4 scope; add to Phase 5 or backlog

</deferred>

---

*Phase: 04-laundry-basket*
*Context gathered: 2026-04-02*
