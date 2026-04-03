# Requirements: LaundryAdvisor

**Defined:** 2026-02-19
**Core Value:** Decode a confusing care label and tell the user exactly how to wash a specific garment — so they never ruin a piece of clothing again.

## v1 Requirements

### Authentication (AUTH)

- [ ] **AUTH-01**: User can register an account with email and password
- [ ] **AUTH-02**: User can log in with email and password
- [ ] **AUTH-03**: User can log out from any page
- [ ] **AUTH-04**: User session persists across browser refresh

### Wardrobe Management (WARD)

- [ ] **WARD-01**: User can create a garment with name, color, fabric/material, category, and optional notes
- [ ] **WARD-02**: User can upload a garment item photo (image files only, max 10MB, stored on AWS S3)
- [ ] **WARD-03**: User can upload a care label photo for a garment (image files only, max 10MB, stored on AWS S3)
- [ ] **WARD-04**: User can view their full wardrobe as a photo grid
- [ ] **WARD-05**: User can view a garment detail page showing all fields, photos, and care instructions
- [ ] **WARD-06**: User can edit any garment field (name, color, fabric, category, notes)
- [ ] **WARD-07**: User can delete a garment from their wardrobe
- [ ] **WARD-08**: User can edit individual care instruction fields and save a final version separate from the AI output

### Care Label Analysis (ANLZ)

- [ ] **ANLZ-01**: User follows a sequential garment creation flow: upload item photo → provide optional details → upload care label photo → click "Analyze" button
- [ ] **ANLZ-02**: Clicking "Analyze" triggers a synchronous GPT-4o Vision API call using the uploaded care label image and any optional text provided
- [ ] **ANLZ-03**: Analysis returns structured JSON containing: wash temperature/cycle, drying method, ironing guidance, bleach warnings, delicates/special-care flag, confidence score per field, and confirmation prompts for uncertain fields
- [x] **ANLZ-04**: Raw GPT-4o JSON response is stored immutably in the database as an audit log
- [ ] **ANLZ-05**: User-edited final instructions are stored separately from the raw AI output
- [ ] **ANLZ-06**: Each user is limited to 10 care label analyses per day, resetting at midnight
- [ ] **ANLZ-07**: User is shown a clear UI message when their daily analysis limit is reached
- [ ] **ANLZ-08**: Remaining daily analysis count is visible in the UI
- [ ] **ANLZ-09**: Repeat analysis calls for the same care label image are deduplicated using a content hash — stored results are returned without a new API call
- [ ] **ANLZ-10**: A global API budget guard halts all analysis calls when cumulative API spend approaches the $10 limit
- [x] **ANLZ-11**: Django admin panel displays per-user analysis usage logs and API call history for monitoring

### Laundry Basket (BSKT)

- [ ] **BSKT-01**: User can select multiple analyzed garments from their wardrobe to add to a laundry basket
- [x] **BSKT-02**: Only garments with a completed analysis are eligible for basket selection
- [x] **BSKT-03**: App generates a multi-load washing plan, grouping garments by temperature compatibility, color group (whites/lights/darks), and fabric sensitivity (delicates vs. normal)
- [ ] **BSKT-04**: Each load in the plan displays the list of included garments, recommended wash settings, and applicable warnings (e.g., "do not wash together", "air dry only", "no bleach")

### Project Setup (SETUP)

- [ ] **SETUP-01**: Project is version-controlled with a git remote repository accessible to all team members
- [ ] **SETUP-02**: All dependencies are managed via a Python virtual environment and pinned in `requirements.txt`
- [ ] **SETUP-03**: A `.env.example` file is committed to the repository listing all required environment variable keys with no secret values
- [ ] **SETUP-04**: `.env` and `venv/` are excluded from version control via `.gitignore`

### Deployment (DEPLOY)

- [ ] **DEPLOY-01**: Application is deployed and publicly accessible on Render
- [ ] **DEPLOY-02**: Render-managed PostgreSQL database is connected and operational in production
- [ ] **DEPLOY-03**: AWS S3 storage is configured and functional in the production environment
- [ ] **DEPLOY-04**: All production secrets and environment variables are configured in the Render dashboard — none committed to the repository
- [ ] **DEPLOY-05**: A health check endpoint (`/healthz/`) is available for uptime monitoring

## v2 Requirements

### Authentication

- **AUTH-V2-01**: User can reset password via email link
- **AUTH-V2-02**: OAuth login (Google or GitHub)

### Wardrobe

- **WARD-V2-01**: User can search and filter their wardrobe by name, color, fabric, or category
- **WARD-V2-02**: Confidence score per decoded field is displayed on garment detail page
- **WARD-V2-03**: Wash history is tracked per garment
- **WARD-V2-04**: User can share a garment care card via a public URL

### Analysis

- **ANLZ-V2-01**: Fabric type is inferred from care label text and stored alongside care instructions
- **ANLZ-V2-02**: "Ruined an item?" feedback loop to flag incorrect AI analysis

## Out of Scope

| Feature | Reason |
|---------|---------|
| Native mobile app | Web-first (mobile-responsive); validate web before native |
| Celery / async task queue | Adds infrastructure complexity; synchronous calls sufficient for v1 |
| Real-time features (WebSockets) | No use case in v1 that requires it |
| OAuth / social login | Email/password sufficient for v1 |
| 2FA | Not required for this audience in v1 |
| Social / community features | Out of product scope — wardrobe management, not social |
| Outfit styling / fashion recommendations | Different product category |
| Multi-language support | English only for v1 |
| Barcode / brand lookup | Requires maintained dataset; out of scope |
| Video uploads | No use case; image-only |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| SETUP-01 | Phase 1 | Pending |
| SETUP-02 | Phase 1 | Pending |
| SETUP-03 | Phase 1 | Pending |
| SETUP-04 | Phase 1 | Pending |
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| AUTH-04 | Phase 1 | Pending |
| WARD-01 | Phase 2 | Pending |
| WARD-02 | Phase 2 | Pending |
| WARD-03 | Phase 2 | Pending |
| WARD-04 | Phase 2 | Pending |
| WARD-05 | Phase 2 | Pending |
| WARD-06 | Phase 2 | Pending |
| WARD-07 | Phase 2 | Pending |
| WARD-08 | Phase 2 | Pending |
| ANLZ-01 | Phase 3 | Pending |
| ANLZ-02 | Phase 3 | Pending |
| ANLZ-03 | Phase 3 | Pending |
| ANLZ-04 | Phase 3 | Complete |
| ANLZ-05 | Phase 3 | Pending |
| ANLZ-06 | Phase 3 | Pending |
| ANLZ-07 | Phase 3 | Pending |
| ANLZ-08 | Phase 3 | Pending |
| ANLZ-09 | Phase 3 | Pending |
| ANLZ-10 | Phase 3 | Pending |
| ANLZ-11 | Phase 3 | Complete |
| BSKT-01 | Phase 4 | Pending |
| BSKT-02 | Phase 4 | Complete |
| BSKT-03 | Phase 4 | Complete |
| BSKT-04 | Phase 4 | Pending |
| DEPLOY-01 | Phase 5 | Pending |
| DEPLOY-02 | Phase 5 | Pending |
| DEPLOY-03 | Phase 5 | Pending |
| DEPLOY-04 | Phase 5 | Pending |
| DEPLOY-05 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 36 total
- Mapped to phases: 36
- Unmapped: 0

---
*Requirements defined: 2026-02-19*
*Last updated: 2026-02-19 after roadmap creation*
