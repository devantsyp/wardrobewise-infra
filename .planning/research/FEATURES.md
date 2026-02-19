# Feature Landscape

**Domain:** Laundry Care Advisor / Wardrobe Management Web App
**Researched:** 2026-02-19
**Confidence:** MEDIUM (training data; WebSearch restricted during this session)

---

## Table Stakes

Features users expect. Missing = product feels incomplete or users leave.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| User registration & persistent login | Wardrobe data must survive sessions; users will not re-enter a catalog each visit | Low | Standard Django auth; email/password minimum |
| Garment catalog / wardrobe list | Core value prop requires a persistent home for all items | Low-Med | Needs name, photo thumbnail, and quick care summary per item |
| Care label photo upload | Primary input mechanism; users take a photo of the label and expect a result | Med | Must handle poor lighting, skewed angles, partial visibility |
| Care symbol decoding into plain English | Users cannot read ISO 3758 symbols reliably; translation to "Wash at 30°C, gentle cycle" is the whole point | High | GPT-4o Vision; must surface confidence level when uncertain |
| Display of structured care instructions per garment | Wash temp, cycle type, drying method, ironing level, bleach flag, dry-clean flag must all be visible at a glance | Low-Med | Card/badge UI; structured output from AI step |
| Edit / correct AI-decoded instructions | AI makes mistakes; users must be able to override any field | Low | Simple form; does not require re-analysis |
| Garment photo storage | Users want a visual reference for each item, not just text | Low-Med | Store original upload; show thumbnail in catalog |
| "Laundry Basket" — assemble a wash load | Core workflow: pick garments, get grouping plan | Med | Multi-select from catalog |
| Multi-load washing plan output | Grouped by: water temperature, color group (lights/darks/colors), delicates flag | Med | Grouping logic detailed below |
| Rate-limit feedback to user | 10 analyses/day; users must know how many remain and when the limit resets | Low | In-UI counter; clear messaging |
| Mobile-responsive layout | Users photograph labels on their phones; the web UI must work on mobile browser | Med | CSS/responsive framework; no native app required |
| Basic search / filter in wardrobe | As catalog grows past ~20 items, users need to find a specific garment | Low | Filter by name, category, or color |

---

## Care Label Symbol Norms (ISO 3758 — What Must Be Decoded)

This governs what "table stakes" care decoding covers. Any app in this space must handle all five symbol families.

| Symbol Family | Examples | Plain-English Output Required |
|---------------|----------|-------------------------------|
| Washing (basin) | 1 dot = 30°C, 2 dots = 40°C, 3 = 50°C, 4 = 60°C, 5 = 70°C, 6 = 95°C; bar = permanent press; double bar = gentle | "Machine wash, cold (30°C), gentle cycle" |
| Bleaching (triangle) | Empty = any bleach OK; CL = chlorine only; two lines = non-chlorine only; X = do not bleach | "Do not bleach" |
| Drying (square) | Circle inside = tumble dry; dots = heat level; lines = flat/drip/hang dry; X = do not tumble dry | "Tumble dry, low heat" |
| Ironing (iron shape) | Dots = temperature level (1 = low, 2 = med, 3 = high); X = do not iron; steam lines crossed = no steam | "Iron on medium heat, no steam" |
| Dry cleaning (circle) | Letter codes (A/F/P/W) = solvent type; bar = gentle; X = do not dry clean | "Dry clean only, petroleum solvent" |

The AI must produce a structured result for each family. Unknown or unreadable symbols must be flagged with `confidence: low` rather than silently guessed.

---

## Laundry Grouping Logic — What Users Expect from a Wash Plan

A "multi-load plan" must group garments along three axes simultaneously:

| Grouping Axis | Values | Why |
|---------------|--------|-----|
| Water temperature | Cold (≤30°C), Warm (40°C), Hot (60°C+) | Mixing temps damages cold-sensitive items |
| Color group | Whites, Lights/Pastels, Darks/Brights | Dye transfer prevention |
| Fabric sensitivity | Delicates (hand-wash or gentle machine), Normal | Cycle agitation damage |

**Conflict resolution rules the plan must express:**
- A delicate item always goes in its own load regardless of color/temp match
- Whites + hot overrides — never merge whites-at-30 with darks-at-30
- When a garment's temp is ambiguous (low-confidence AI decode), flag it and exclude from auto-grouping; prompt user to confirm

The output is a list of loads: e.g., "Load 1: Whites — 40°C, normal cycle (5 items). Load 2: Darks — 30°C, gentle cycle (2 items)."

---

## Differentiators

Features that set the product apart. Not expected by default, but valued when present.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Confidence score display per decoded field | Surfaces AI uncertainty so users know when to double-check; builds trust | Low | Already implied by `confidence` fields in data model |
| Fabric type inference from label photo | AI often reads fiber content (100% cotton, 60% polyester) from text on label; store and display it | Low-Med | Augments care instructions; useful for outfit planning |
| Garment categories / tags | Users want "all my gym clothes" or "wool sweaters"; filtering by category is a power-user feature | Low | Freeform tags or predefined categories |
| Care instruction comparison across garments | "These 3 items all wash the same way — put them together" surfaced proactively | Med | Automated laundry basket suggestion |
| "Ruined an item?" feedback loop | User marks a garment as damaged; app learns which instructions were wrong and prompts re-analysis | High | Requires event logging; deferred to later phase |
| Wash history per garment | Log when a garment was last washed; surface stale items | Med | Optional feature; low initial demand |
| Shareable wardrobe / care card | Generate a printable or shareable care card for a garment (useful when lending clothes) | Low | Static rendered page; no auth required to view |
| Onboarding care label guide | Teach users the five symbol families before they upload anything | Low | Static content; increases confidence in AI output |
| Brand-based care defaults | Pre-fill care instructions for known brands (e.g., "Patagonia fleece is always cold/gentle") | High | Requires a maintained dataset; brittle; defer |

---

## Anti-Features

Features to explicitly NOT build in v1 (and why).

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Native mobile app (iOS/Android) | Doubles development surface with no v1 advantage; mobile-responsive web covers the photo-upload use case | Ship web-first, responsive; revisit after user validation |
| Social / community features (sharing wardrobes, following other users) | Laundry care is private and utility-driven; social layer adds complexity with zero clear v1 demand | Build sharing of a single care card only if requested |
| AI outfit recommendation / styling | Completely different domain (fashion taste vs. care logistics); dilutes the core value prop | Keep scope to care instructions, not aesthetics |
| Barcode / QR code product lookup | Requires a maintained product database; coverage is poor for clothing; fails silently | Label photo + GPT-4o Vision is more reliable and covers all garments |
| Automated purchase / reorder suggestions | Affiliate/commerce features add trust risk with no v1 user demand | Not in scope |
| Laundry pickup / delivery integration | Third-party logistics; entirely different domain; not core to the app | Out of scope entirely |
| Push notifications / reminder system | Requires notification infrastructure; no clear user pain point proven at v1 | Add only after user research confirms demand |
| Multi-user household sharing | Complex permission model; household "who washed what" is a v3+ feature | One wardrobe per account in v1 |
| Offline mode / PWA caching | Adds service-worker complexity; web-first users are online when doing laundry planning | Defer until after initial launch validation |

---

## Feature Dependencies

```
User Auth
  └── Garment Catalog (requires user identity to persist items)
        └── Care Label Upload + AI Decode (garment must exist before analysis)
              └── Structured Care Instruction Storage (depends on decode output)
                    └── Manual Edit of Instructions (depends on stored instructions)
                    └── Laundry Basket Assembly (selects from saved garments)
                          └── Multi-Load Wash Plan (depends on basket + stored instructions)

Rate Limiting
  └── AI Decode (enforced at analysis step; counter displayed in UI)

Search / Filter
  └── Garment Catalog (requires catalog to have items)

Mobile-Responsive Layout
  └── All UI features (cross-cutting concern)
```

---

## MVP Recommendation

**Prioritize (launch-blocking):**
1. User auth + garment catalog with photo storage
2. Care label photo upload + GPT-4o Vision decode → structured output with confidence fields
3. Per-garment care instruction display + manual edit
4. Laundry Basket assembly + multi-load grouping plan
5. AI usage rate-limit display (10/day counter)
6. Mobile-responsive layout

**Ship in v1.1 (post-launch, low effort):**
- Garment categories / tags
- Basic wardrobe search / filter
- Fabric type display from AI output
- Onboarding care label symbol guide (static content)
- Shareable care card (single garment, public URL)

**Defer to v2:**
- Wash history per garment
- Confidence-based auto-grouping exclusion with user prompt
- "Ruined an item?" feedback loop
- Brand-based care defaults (requires database)

**Never (for this product):**
- Native mobile app before web is validated
- Social / community features
- Outfit styling / fashion recommendations

---

## Sources

- ISO 3758:2012 (Textiles — Care labelling code using symbols) — international standard for care label symbols; five symbol families and dot/bar/letter coding are stable and well-established
- ASTM D5489 — US equivalent standard for care symbols (used on North American garments alongside ISO)
- Training data covering wardrobe management apps (Stylebook, Cladwell, Laundry Symbols apps on iOS/Android) — confidence: MEDIUM
- GPT-4o Vision capabilities for structured OCR/symbol decode — confidence: HIGH (well-documented as of August 2025 knowledge cutoff)

> Note: WebSearch was restricted during this research session. All findings are drawn from training knowledge (cutoff August 2025). Symbol standard details (ISO 3758) are stable and unlikely to have changed. App feature norms are MEDIUM confidence — validate against current App Store reviews of comparable apps (Stylebook, Cladwell, Laundry Symbols by Ariel) before finalizing roadmap.
