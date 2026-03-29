# Roadmap: LaundryAdvisor

## Overview

LaundryAdvisor is built in five phases that follow strict technical dependencies: secure scaffolding and auth must exist before any user data is created, real S3 storage must be working before the AI pipeline can use genuine image URLs, the AI analysis pipeline must produce real AnalysisResult rows before the basket grouping algorithm can be validated, and a dedicated final phase confirms the production environment is fully operational before the app is handed to any external audience. Each phase delivers a coherent, independently verifiable capability.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Scaffolding and Auth** - Secure project foundation, working auth, and a deployed Django app on Render
- [ ] **Phase 2: Wardrobe CRUD with S3** - Full garment catalog management with image uploads to AWS S3
- [ ] **Phase 3: Care Label Analysis Pipeline** - GPT-4o Vision integration with rate limiting, deduplication, and budget guard
- [ ] **Phase 4: Laundry Basket** - Multi-garment basket selection and compatible-load grouping plan
- [ ] **Phase 5: Production Deployment** - Live, publicly accessible app with PostgreSQL and S3 operational on Render

## Phase Details

### Phase 1: Scaffolding and Auth
**Goal**: A running Django app is deployed on Render, any team member can clone and run it locally in minutes, and users can register, log in, and stay logged in.
**Depends on**: Nothing (first phase)
**Requirements**: SETUP-01, SETUP-02, SETUP-03, SETUP-04, AUTH-01, AUTH-02, AUTH-03, AUTH-04
**Success Criteria** (what must be TRUE):
  1. Any team member can clone the repo, copy `.env.example` to `.env`, fill in secrets, run `pip install -r requirements.txt`, and reach the app at `localhost:8000` without additional configuration steps
  2. `.env` and `venv/` are absent from the git history; `.gitignore` and `.env.example` are present in the first commit
  3. User can register a new account with email and password, log in, and log out from any page
  4. User's login session persists across browser refresh without requiring re-authentication
  5. The deployed Render app responds to HTTP requests and returns a non-error page (deployment baseline is confirmed working)
**Plans:** 3 plans

Plans:
- [ ] 01-01-PLAN.md — Django project scaffolding: split settings, custom user model, Tailwind CSS v4 with color palette, health check, .gitignore, .env.example
- [ ] 01-02-PLAN.md — Auth flow and templates: registration/login/logout views, styled base template with nav, landing page hero, flash message toasts
- [ ] 01-03-PLAN.md — Render deployment: production settings (WhiteNoise, dj-database-url), render.yaml Blueprint, build.sh, deploy verification

### Phase 2: Wardrobe CRUD with S3
**Goal**: Users can build a persistent garment catalog — creating, viewing, editing, and deleting garments — with photos stored durably on AWS S3.
**Depends on**: Phase 1
**Requirements**: WARD-01, WARD-02, WARD-03, WARD-04, WARD-05, WARD-06, WARD-07, WARD-08
**Success Criteria** (what must be TRUE):
  1. User can create a garment record with name, color, fabric/material, category, and optional notes
  2. User can upload a garment photo and a care label photo (images only, max 10 MB each); uploaded files are stored in S3 and survive a Render redeploy
  3. User can view their full wardrobe as a photo grid showing all their garments
  4. User can open a garment detail page showing all fields, both photos, and a placeholder for care instructions
  5. User can edit any garment field and delete a garment; deleted garments no longer appear in the wardrobe grid
**Plans:** 3 plans

Plans:
- [ ] 02-01-PLAN.md — Wardrobe app foundation: Garment model, GarmentForm with file validation, S3 storage config (dev + prod), signals for file cleanup, Django admin
- [ ] 02-02-PLAN.md — Views and templates: 5 FBVs (list/detail/create/edit/delete), responsive photo grid, garment detail page, shared create/edit form with floating labels and file upload preview
- [ ] 02-03-PLAN.md — AWS S3 setup and verification: guide user through bucket creation + IAM credentials + Render env vars, then browser verification of full CRUD flow

### Phase 3: Care Label Analysis Pipeline
**Goal**: Users can trigger a GPT-4o Vision analysis of a care label image and receive structured plain-English laundry instructions, with rate limiting, deduplication, budget protection, and admin visibility all enforced.
**Depends on**: Phase 2
**Requirements**: ANLZ-01, ANLZ-02, ANLZ-03, ANLZ-04, ANLZ-05, ANLZ-06, ANLZ-07, ANLZ-08, ANLZ-09, ANLZ-10, ANLZ-11
**Success Criteria** (what must be TRUE):
  1. User follows the sequential flow (upload item photo → add details → upload care label → click Analyze) and receives structured care instructions: wash temp/cycle, drying method, ironing guidance, bleach warnings, and delicates flag
  2. The raw GPT-4o JSON response is stored immutably in the database and the user's edited final instructions are stored separately; both persist across sessions
  3. After reaching 10 analyses in a day, the user sees a clear UI message blocking further analysis and showing the daily limit; the counter resets at midnight and is visible in the UI at all times
  4. Submitting the same care label image a second time returns the stored result immediately without making a new API call
  5. When cumulative API spend approaches the $10 budget limit, all analysis calls are halted globally; the Django admin panel shows per-user usage logs and API call history
**Plans:** 2/3 plans executed

Plans:
- [ ] 03-01-PLAN.md — Models + service layer: CareAnalysis and UsageLog models, services/analysis.py with GPT-4o Vision call, rate limiting, budget guard, image dedup, context processor, requirements update
- [ ] 03-02-PLAN.md — Analyze view + templates: analyze endpoint, garment detail care instructions display (all states), nav counter, wardrobe grid badge, rate limit UI with countdown
- [ ] 03-03-PLAN.md — Edit instructions + admin: edit/reset/delete analysis views, edit form, Django admin for CareAnalysis and UsageLog with read-only audit

### Phase 4: Laundry Basket
**Goal**: Users can select multiple analyzed garments and receive a multi-load washing plan that groups compatible garments and separates incompatible ones.
**Depends on**: Phase 3
**Requirements**: BSKT-01, BSKT-02, BSKT-03, BSKT-04
**Success Criteria** (what must be TRUE):
  1. User can select multiple garments from their wardrobe to add to a laundry basket; only garments with a completed analysis appear as selectable options
  2. The app produces a multi-load washing plan that groups garments by temperature compatibility, color group (whites/lights/darks), and fabric sensitivity (delicates vs. normal)
  3. Each load in the plan displays the included garments, recommended wash settings, and any applicable warnings (e.g., "air dry only", "no bleach", "do not wash together")
**Plans**: TBD

Plans:
- [ ] 04-01: `laundry` app and `group_into_loads()` — pure Python grouping function with unit tests covering edge cases (null temperatures, dry-clean-only, delicates conflicts)
- [ ] 04-02: Basket views and templates — basket selection UI (multi-select from wardrobe), load plan display template with per-load items, settings, and warnings

### Phase 5: Production Deployment
**Goal**: The app is live, publicly accessible on Render, with PostgreSQL and S3 fully operational in the production environment and all secrets properly isolated from the repository.
**Depends on**: Phase 4
**Requirements**: DEPLOY-01, DEPLOY-02, DEPLOY-03, DEPLOY-04, DEPLOY-05
**Success Criteria** (what must be TRUE):
  1. The app is publicly accessible at a Render URL; any external user can register, log in, create garments, upload photos to S3, and run a care label analysis end-to-end without local setup
  2. The Render-managed PostgreSQL database is connected and operational; data persists across Render redeployments
  3. AWS S3 is configured and functional in the production environment; uploaded images survive a Render redeploy and are served via presigned URLs
  4. No secrets or environment variable values are present in the git repository; all production secrets are confirmed to exist only in the Render dashboard
  5. `GET /healthz/` returns HTTP 200, confirming the app is up and suitable for uptime monitoring
**Plans**: TBD

Plans:
- [ ] 05-01: Production environment audit — verify all env vars are in Render dashboard, confirm no secrets in repo (`git grep` audit), final `requirements.txt` pin, `render.yaml` verified
- [ ] 05-02: End-to-end production validation — PostgreSQL persistence confirmed, S3 uploads confirmed, health check endpoint live, full user flow tested on Render URL

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Scaffolding and Auth | 3/3 | Complete | 2026-02-22 |
| 2. Wardrobe CRUD with S3 | 0/3 | Not started | - |
| 3. Care Label Analysis Pipeline | 2/3 | In Progress|  |
| 4. Laundry Basket | 0/2 | Not started | - |
| 5. Production Deployment | 0/2 | Not started | - |
