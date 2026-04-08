# Project Research Summary

**Project:** Wardrobe Wise
**Domain:** Laundry Care Advisor / Wardrobe Management Web App
**Researched:** 2026-02-19
**Confidence:** MEDIUM-HIGH (training data through August 2025; web search unavailable during research session)

## Executive Summary

Wardrobe Wise is a server-rendered Django web application that uses GPT-4o Vision to decode ISO 3758 care label symbols into plain-English laundry instructions, and groups a user's garments into compatible wash loads. The recommended approach is a straightforward three-app Django project (accounts, wardrobe, laundry) deployed on Render with AWS S3 for file storage, PostgreSQL as the database, and the OpenAI Python SDK for AI analysis — no async task queue, no SPA frontend, no native mobile app. All four research files converge on the same clean build order: auth first, then wardrobe CRUD with S3, then AI analysis pipeline, then laundry basket grouping, then deploy polish.

The primary technical risks are not architectural — they are operational. Budget exhaustion from unguarded OpenAI calls, secrets committed to git before a `.gitignore` is in place, and media files lost to Render's ephemeral filesystem are the three failure modes most likely to derail the project during development. All three must be addressed in Phase 1 and Phase 2 before any feature work begins. The stack is mature and well-understood; the pitfalls are team-discipline and configuration issues, not hard technical problems.

A secondary risk is the synchronous OpenAI call blocking Gunicorn workers. The project rules out Celery, which is the right tradeoff at this scale, but it means Gunicorn's worker timeout must be set to 60 seconds, a loading state must be shown in the UI, and the per-user daily rate limit (10 analyses/day) must be enforced via a database-backed log — not an in-memory counter — to survive Render restarts and multi-worker deployments.

## Key Findings

### Recommended Stack

The stack is Django 5.1 (verify whether 5.2 LTS has shipped — it was planned for April 2025), PostgreSQL 16 on Render, gunicorn as the WSGI server, django-storages with boto3 for S3 file storage, the openai 1.x SDK for GPT-4o Vision calls, whitenoise for static file serving, and dj-database-url to parse Render's injected `DATABASE_URL`. Python 3.12 is the recommended runtime (3.13 carries compatibility risk). The entire stack is deployed to Render via `render.yaml` with environment variables set in the Render dashboard — no secrets committed.

**Core technologies:**
- Python 3.12 + Django 5.1: Runtime and web framework — mature, well-tested combination; LTS status should be re-verified before pinning
- PostgreSQL 16 (Render-managed): Primary database — `JSONField` first-class support, ORM-only access, no raw SQL
- gunicorn 22.x: WSGI server — Render's official recommendation; must use `--timeout 60` to survive OpenAI call latency
- django-storages[s3] 1.14.x + boto3 1.34.x: S3 file backend — transparent `ImageField` integration, private bucket with presigned URLs
- openai 1.35.x: GPT-4o Vision calls — `client.chat.completions.create()` with `response_format={"type": "json_object"}` and explicit schema in system prompt
- whitenoise 6.7.x: Static file serving on Render — zero-configuration, no nginx layer needed
- dj-database-url 2.1.x + python-dotenv 1.0.x + psycopg2-binary 2.9.x: Deployment plumbing — standard Render/Django trio

See `STACK.md` for pinned versions, integration patterns, and full `requirements.txt`.

### Expected Features

All five ISO 3758 care symbol families (washing, bleaching, drying, ironing, dry cleaning) must be decoded into structured plain-English output. The AI must surface a confidence score and list uncertain fields rather than silently guessing. The laundry basket grouping logic is non-trivial: it must resolve three axes simultaneously (water temperature, color group, fabric sensitivity) with defined priority rules when axes conflict.

**Must have (table stakes):**
- User registration and persistent login — wardrobe data requires a session identity
- Garment catalog with item photo and care label photo storage
- Care label upload and GPT-4o Vision decode with confidence fields
- Structured care instruction display per garment (wash temp, cycle, drying, ironing, bleach, dry-clean)
- Manual edit/override of any AI-decoded field
- Laundry basket assembly and multi-load grouping plan
- AI usage rate-limit display (10/day counter with reset time)
- Mobile-responsive layout — users photograph labels on their phones

**Should have (competitive differentiators, v1.1):**
- Confidence score display per decoded field — builds trust, surfaces AI uncertainty
- Garment categories and tags — "all my gym clothes"
- Basic wardrobe search and filter — needed once catalog exceeds ~20 items
- Fabric type inference from label text — augments care instructions
- Onboarding care label symbol guide — static content, increases user confidence

**Defer to v2+:**
- Wash history per garment
- "Ruined an item?" feedback loop
- Brand-based care defaults (requires maintained dataset)
- Shareable care card (public URL per garment)

**Never (for this product):**
- Native mobile app before web is validated
- Social/community features
- Outfit styling or fashion recommendations
- Celery/Redis async queue in v1

See `FEATURES.md` for the full feature dependency graph and ISO 3758 symbol family breakdown.

### Architecture Approach

The recommended architecture is a three-app Django project (`accounts`, `wardrobe`, `laundry`) with a project-level `services/` package for all external integrations. This separation prevents circular imports, allows each team member to own one app, and isolates third-party coupling. The basket grouping algorithm is a pure Python function operating on an in-memory queryset — no complex SQL, trivially unit-testable, easy to modify as rules evolve. The data model uses discrete typed columns for analysis results (not a single JSONField) so basket queries can use ORM filters without parsing JSON; the raw GPT-4o response is stored separately as an immutable audit log.

**Major components:**
1. `accounts` app — user registration, login, logout, UserProfile model; all other apps FK to `User`
2. `wardrobe` app — WardrobeItem CRUD, ImageField upload to S3 via django-storages, AnalysisResult model, UsageLog model, rate-limit enforcement
3. `laundry` app — basket selection UI, `group_into_loads()` pure Python function, load recommendation display
4. `services/openai_client.py` — GPT-4o Vision calls, JSON parsing, AnalysisError raising; no Django model imports
5. `config/settings/` — base/development/production split from day one to prevent `DEBUG=True` in production

See `ARCHITECTURE.md` for the full data model, data flow diagrams, grouping algorithm implementation, and Render deployment YAML.

### Critical Pitfalls

1. **Secrets committed to git** — Create `.gitignore` and `.env.example` as the very first commit before any teammate clones the repo; add `git grep` for `sk-` and `AKIA` patterns in a pre-commit hook; use IAM policy to restrict S3 key to one bucket
2. **OpenAI budget exhaustion** — Build `AnalysisLog` model with cumulative spend tracking and a global budget guard (halt at $9.00) before wiring any view that calls the API; use fixture mocks for local dev testing
3. **Render ephemeral filesystem deletes media** — Configure django-storages S3 as `DEFAULT_FILE_STORAGE` before the first Render deploy; never test uploads on Render without S3 configured; do not defer S3 to a later phase
4. **Django migration conflicts on a team** — Establish the convention in Phase 1: one person generates migrations per model per branch; use `--merge` when conflicts occur; add `migrate --check` to Render build command
5. **Rate limit bypassed via in-memory counter** — Implement rate limiting exclusively via database query on `AnalysisLog`; in-memory and session counters reset on Render restart; the check and log-entry creation must be wrapped in a DB transaction

See `PITFALLS.md` for 14 additional pitfalls with phase-by-phase warnings and detection signals.

## Implications for Roadmap

Research across all four files converges on the same five-phase build order. Dependencies are strict: auth must precede wardrobe CRUD, wardrobe CRUD with real S3 uploads must precede AI analysis, and AI analysis results must exist before the basket grouping algorithm can be validated. No phase can be meaningfully parallelized because each builds on the previous phase's data.

### Phase 1: Project Scaffolding, Auth, and Deployment Baseline

**Rationale:** Security configuration (secrets, `.gitignore`) and deployment scaffolding (`collectstatic`, whitenoise, Render) must be in place before any teammate writes a single model. Django migration conflicts emerge from uncoordinated concurrent model work — the team norms must be established before the first model. Getting a "hello world" deploy to Render working early surfaces `collectstatic` failures, `ALLOWED_HOSTS` errors, and `DATABASE_URL` parsing issues in a low-stakes context.

**Delivers:** Running Django app on Render with working auth (register, login, logout), split settings (dev/prod), PostgreSQL connection, whitenoise static files, and a health check endpoint.

**Addresses:** User registration and persistent login (table stakes), mobile-responsive base template

**Avoids:** Secrets committed to git (Pitfall 1), `collectstatic` failing on first deploy (Pitfall 5), `DATABASE_URL` misconfiguration (Pitfall 13), `DEBUG=True` in production (Pitfall 15), requirements drift (Pitfall 14)

### Phase 2: Wardrobe CRUD with S3 File Storage

**Rationale:** The AI analysis pipeline requires real S3 URLs to images — it cannot be built or tested meaningfully with placeholder files. S3 must be working and validated (private bucket, presigned URL display, IAM permissions confirmed) before any OpenAI call is attempted. MIME type validation and upload size limits belong here, not as an afterthought.

**Delivers:** Garment catalog with item photo and care label photo storage in S3, wardrobe list/detail/edit/delete views, Django admin registered, garment status field (pending/analyzed/failed).

**Uses:** django-storages 1.14.x, boto3, Pillow for image validation, `STORAGES` dict configuration in settings

**Implements:** `wardrobe` app (WardrobeItem model, ImageField, form validators), `services/s3_helpers.py` (presigned URL template tag)

**Avoids:** Media files lost on Render deploy (Pitfall 3), S3 credentials/region misconfiguration (Pitfall 6), public bucket privacy disaster (Pitfall 7), MIME type spoofing (Pitfall 8)

### Phase 3: AI Analysis Pipeline

**Rationale:** The analysis pipeline is the core value of the product and carries the highest operational risk (budget, rate limiting, JSON parsing failures). Building it after S3 is confirmed working means the OpenAI call can use real S3 URLs or base64-encoded real images — not test fixtures — so prompt engineering is tuned to production conditions. The `AnalysisLog` model and budget guard must be created before the first real API call is made.

**Delivers:** Care label upload triggers GPT-4o Vision analysis, structured AnalysisResult saved to discrete columns, per-garment care instruction display, manual edit/override of any field, rate-limit counter in UI (10/day), AnalysisLog with budget guard.

**Uses:** openai 1.35.x SDK, `response_format={"type": "json_object"}`, base64 image encoding for private S3 bucket, image SHA-256 deduplication hash on WardrobeItem

**Implements:** `services/openai_client.py`, AnalysisResult model, UsageLog model, rate-limit decorator, analysis view

**Avoids:** Budget exhaustion (Pitfall 2), malformed JSON from Vision API (Pitfall 9), bypassable rate limit (Pitfall 10), deduplication key mismatch (Pitfall 11), blocking worker timeout — set `gunicorn --timeout 60` here (Pitfall 16)

### Phase 4: Laundry Basket and Wash Load Grouping

**Rationale:** The grouping algorithm requires real AnalysisResult data with diverse garment types to validate correctness. Unit tests for `group_into_loads()` must be written before the view is wired up — the edge cases (null wash temperature, dry-clean-only items, delicates) are only catchable with deliberate test cases, not incidental integration testing. The laundry app is intentionally kept thin; it reads wardrobe data but owns no models in v1.

**Delivers:** Laundry basket selection UI (multi-select from wardrobe), `group_into_loads()` pure Python function, load recommendation display grouped by temperature/color/delicates, flagging of unanalyzed or low-confidence garments.

**Implements:** `laundry` app, `laundry/grouping.py`, basket template, "add to basket" / "remove from basket" selection

**Avoids:** Grouping edge cases crashing on null temperatures (Pitfall 18)

### Phase 5: Polish and Demo Preparation

**Rationale:** Deploy reliability must be confirmed before any external audience sees the app. Render's free-tier cold start is a demo-killing failure mode that requires action (keep-alive ping or paid tier upgrade) before the submission deadline. Search/filter and confidence score display are low-effort v1.1 features that can be added during polish without touching core architecture.

**Delivers:** Error pages (404, 500, 429), health check endpoint, keep-alive monitor configured, confidence score display per decoded field, garment search/filter, fabric type display from AI output, `CONTRIBUTING.md` with team norms documented, final production environment variable audit.

**Avoids:** Render cold start during demo (Pitfall 12), `.env.example` drift (Pitfall 17)

### Phase Ordering Rationale

- Auth must precede everything because all views require a user identity to associate wardrobe items
- S3 must precede AI analysis because GPT-4o Vision needs real image URLs; faking this produces a prompt tuned to test data
- AI analysis must precede basket grouping because `group_into_loads()` requires `AnalysisResult` rows with diverse real data to validate
- Deployment baseline is in Phase 1, not Phase 5, because catching Render configuration failures early avoids crisis during feature development
- The `AnalysisLog` + budget guard is built in Phase 3 before the first real API call — not after

### Research Flags

Phases where standard patterns apply (skip research-phase during planning):
- **Phase 1:** Django project scaffolding, auth, whitenoise, dj-database-url — all well-documented, HIGH confidence patterns with no known gotchas beyond the pitfalls already catalogued
- **Phase 5:** Polish and deployment — standard Render configuration; no novel patterns

Phases likely needing `/gsd:research-phase` during planning if deeper implementation detail is needed:
- **Phase 2:** S3 presigned URL generation within Django template tags — the `STORAGES` dict configuration syntax changed in Django 4.2 and should be verified against current django-storages docs before implementation
- **Phase 3:** GPT-4o Vision with `response_format={"type": "json_object"}` — OpenAI has iterated frequently on structured output API surface; verify current parameter support for Vision inputs before writing the service layer; also verify current `gpt-4o` model name (may be versioned as `gpt-4o-2024-11-20` or similar)

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | MEDIUM-HIGH | Core patterns (Django+Render+S3+OpenAI 1.x) are HIGH confidence. Django version (5.1 vs 5.2 LTS) and exact boto3/openai patch versions are MEDIUM — verify on PyPI before pinning. GPT-4o structured output API surface needs current-docs verification. |
| Features | MEDIUM | Table stakes (auth, catalog, AI decode, basket plan) are HIGH confidence — core value prop is clear. Differentiators (tags, fabric inference, search) are MEDIUM — based on training data about comparable apps, not live App Store research. Anti-features list is HIGH confidence. |
| Architecture | HIGH | Django three-app pattern with service layer and pure Python grouping algorithm is a mature, well-established convention. Data model choices (discrete columns + raw JSONField audit log, OneToOne AnalysisResult, DB-backed UsageLog) are sound and consistent with Django best practices. |
| Pitfalls | HIGH | All identified pitfalls are well-documented in the Django/AWS/OpenAI/Render community. Secrets management, ephemeral filesystem, migration conflicts, and rate-limit implementation are recurring real failures in comparable projects. |

**Overall confidence:** MEDIUM-HIGH

### Gaps to Address

- **Django version pinning:** Django 5.2 LTS was planned for April 2025. By February 2026 it may be current. Verify on `djangoproject.com/download` before writing `requirements.txt`. Prefer the LTS if available.
- **OpenAI model name:** `gpt-4o` model naming conventions change frequently. Verify the current model identifier on `platform.openai.com/docs` before writing the service layer. The model may be `gpt-4o-2024-11-20` or a newer variant.
- **`response_format={"type": "json_object"}` for Vision inputs:** Confirmed working as of August 2025 but OpenAI iterates on this surface. Verify current support before implementation.
- **`AWS_DEFAULT_ACL = None` requirement:** AWS changed Object Ownership behavior in 2023. Confirm this setting is still required for buckets with "Bucket owner enforced" Object Ownership before configuring S3.
- **Render free-tier cold start timeout:** Confirm 15-minute inactivity spin-down is still current before choosing between keep-alive ping or paid tier upgrade.
- **Comparable app feature norms:** Feature research is based on training data about Stylebook, Cladwell, and Laundry Symbols apps. Validate against current App Store reviews before finalizing the v1.1 feature list.

## Sources

### Primary (HIGH confidence)
- Django documentation — project structure, auth, ORM, admin, migration system, F() expressions
- django-storages documentation — S3Boto3Storage, `STORAGES` dict configuration (Django 4.2+)
- OpenAI Python SDK (1.x) — `chat.completions.create`, `response_format`, base64 image encoding
- Render platform documentation — `render.yaml`, Gunicorn configuration, ephemeral filesystem behavior, `DATABASE_URL` injection
- ISO 3758:2012 — care labelling symbol standard (five symbol families, dot/bar/letter coding)

### Secondary (MEDIUM confidence)
- Training data on wardrobe management apps (Stylebook, Cladwell, Laundry Symbols by Ariel) — feature norms
- Training data on Django group project patterns — migration conflict conventions, requirements management
- ASTM D5489 — US care symbol standard (North American garments)

### Tertiary (LOW confidence — verify before use)
- Django 5.2 LTS release date and availability — planned April 2025, may be current by Feb 2026
- Current GPT-4o model identifier — naming conventions change; verify on OpenAI platform docs
- AWS `AWS_DEFAULT_ACL = None` requirement — AWS Object Ownership policy changed 2023; verify current behavior

---
*Research completed: 2026-02-19*
*Ready for roadmap: yes*
