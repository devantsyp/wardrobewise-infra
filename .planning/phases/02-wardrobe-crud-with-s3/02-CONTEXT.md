# Phase 2: Wardrobe CRUD with S3 - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Full garment catalog management — users can create, view, edit, and delete garments, with garment and care label photos stored durably on AWS S3. AI analysis and laundry basket features are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Wardrobe Grid Layout
- Fixed-size cards, tight/dense grid
- Each card shows: garment photo (square 1:1 crop) with garment name below
- Grid columns: responsive CSS grid (auto-fill based on screen width, no fixed column count)
- Ordered: newest first (creation date descending)
- Clicking a card: navigate to the garment detail page
- No-photo fallback: styled placeholder (clothing hanger icon or pattern) — not a plain grey box
- Page header: "My Wardrobe" heading above the grid
- "Add Clothing" button: top-right corner, styled with app's color palette, prominent/noticeable

### Empty State
- Simple message + prominent Add button
- No illustration required

### Garment Form Fields
- Form layout: single page (all fields + photo uploads on one page)
- Label style: floating labels (placeholder floats up when field is focused/filled)
- Required fields: name + category only
- Name field: free text, max 100 characters
- Category field: predefined dropdown — fixed list:
  T-Shirts & Tops, Shirts, Jeans, Pants, Dresses, Skirts, Jackets & Blazers,
  Coats & Outerwear, Shorts, Sweaters & Knitwear, Hoodies & Sweatshirts,
  Underwear & Loungewear, Socks, Activewear, Sleepwear & Robes
- Color field: free text ("navy blue", "off-white", etc.)
- Fabric/material field: free text
- Notes field: optional, max 500 characters
- Post-create redirect: garment detail page (not back to the grid)

### Photo Handling
- Both garment photo and care label photo are optional
- Accepted formats: images only (JPG/PNG), max 10 MB each
- Hint text shown below each upload field: "JPG or PNG, max 10 MB"
- Thumbnail preview shown immediately after a file is selected (before form submit)
- Upload errors: inline error message below the upload field
- Upload progress: no progress bar; submit button is disabled during upload
- S3 path structure: `user_<id>/garment_<id>/garment.jpg` and `user_<id>/garment_<id>/care_label.jpg`
- Image serving: direct S3 URLs (public bucket)
- On edit with existing photo: show current photo as thumbnail with a "Replace" button below
- Photo replacement: delete the old S3 file when a new one is uploaded
- Removing without replacing: not supported (user must upload a replacement to change a photo)

### Garment Detail Page
- Page title: garment name as H1 at the top
- "← Back to Wardrobe" link at top of page
- All fields displayed: name, category, color, fabric, notes, date added ("Added: Feb 25, 2026")
- Photos: stacked vertically — garment photo full-width (edge to edge) at top, care label photo smaller below
- Photos have clearly labeled headings: "Garment Photo" and "Care Label"
- Photos are display-only (no tap-to-expand)
- Care instruction placeholder: simple text "Care instructions coming soon" (no disabled Analyze button yet)
- Edit and Delete buttons both on the detail page only (not accessible from grid cards)
- Delete button: red/danger styling; Edit button: neutral styling

### Edit Behavior
- Edit form: separate page using the same form as create, pre-populated with current values
- Cancel button on edit form: returns user to the garment detail page
- Post-edit redirect: garment detail page
- Save errors: error banner at top of the form page

### Delete Behavior
- Delete requires a confirmation dialog: "Delete this garment? This cannot be undone."
- On confirm: delete S3 files immediately, then delete garment record (and cascade-delete any linked AnalysisResult)
- Post-delete redirect: wardrobe grid
- No success toast after delete (navigation back to grid is confirmation enough)

### Security and Data Isolation
- All wardrobe pages require login (redirect to login if unauthenticated)
- Strict user isolation: all queries filter by `request.user`
- Accessing another user's garment URL returns 404 (not 403) — does not reveal existence

### Claude's Discretion
- Exact loading skeleton or spinner design during form submit
- Spacing, typography, and specific Tailwind classes
- Mobile-specific layout adjustments within the responsive grid
- Exact S3 bucket policy configuration (public read vs. signed URLs — user chose direct URLs, Claude handles bucket permissions)

</decisions>

<specifics>
## Specific Ideas

- Category list should balance coverage and simplicity — the provided 15-category list reflects this intent
- "Add Clothing" button must stand out and use the app's deep-space color palette to feel consistent
- Garment photo is the hero on the detail page; care label is a smaller secondary reference image
- The app already has flash/toast infrastructure from Phase 1 — use it for auth-style inline form errors on the wardrobe forms

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-wardrobe-crud-with-s3*
*Context gathered: 2026-02-25*
