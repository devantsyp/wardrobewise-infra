# LaundryAdvisor

## What This Is

LaundryAdvisor is a full-stack web application that helps users build a persistent wardrobe catalog by uploading garment photos and care label images. The app uses GPT-4o Vision to decode care label symbols into structured, plain-English laundry instructions. Users can then assemble a "Laundry Basket" from saved garments and receive a combined washing plan — grouping what can go together and separating what can't.

## Core Value

Decode a confusing care label and tell the user exactly how to wash a specific garment — so they never ruin a piece of clothing again.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] User can register, log in, and log out
- [ ] User can create, view, edit, and delete wardrobe items
- [ ] Each wardrobe item stores: name, description/notes (optional), color, fabric/material, category, item photo (S3), care label photo (S3), and saved final laundry instructions
- [ ] User can upload garment + care label images (and optional text) to trigger a GPT-4o Vision analysis
- [ ] Analysis returns structured JSON: wash temp/cycle, drying method, ironing guidance, bleach warnings, delicates/special-care flags, confidence fields, and confirmation prompts for uncertain results
- [ ] Raw model output and user-edited final instructions are both stored in the database
- [ ] User can edit individual instruction fields and overwrite AI-generated warnings
- [ ] User can view their full wardrobe as a photo grid
- [ ] User can assemble a Laundry Basket by selecting multiple saved garments
- [ ] Basket generates a multi-load washing plan grouped by temperature + color + delicate/normal
- [ ] Each load in the plan shows: items included, recommended settings, and any warnings
- [ ] Each user is limited to 10 care label analyses per day (resets at midnight)
- [ ] Users are blocked with a clear UI message when the daily limit is reached
- [ ] Stored analysis results can be revisited without triggering a new API call
- [ ] Repeat analysis calls for the same item are deduplicated/cached
- [ ] Django admin panel exposes per-user usage logs and API call history

### Out of Scope

- Mobile native app — web-first (mobile-responsive) only
- OAuth / social login — email/password auth sufficient for v1
- Real-time features (WebSockets, live updates) — synchronous calls only
- Celery / async task queues — OpenAI calls are synchronous
- Video uploads — image files only
- Multi-language support — English only for v1
- Paid tiers / billing — flat 10 analyses/day limit for all users

## Context

- Group project: multiple contributors sharing a single Git repo
- Team must be able to clone and run locally with minimal setup (venv + requirements.txt + .env)
- `.env.example` committed to repo; `.env` and `venv/` excluded via `.gitignore`
- PostgreSQL database hosted on Render (used in both local dev and production via env-var-switched connection strings)
- Production environment variables (Django secret key, DB URL, S3 credentials, OpenAI API key) configured in Render dashboard — never committed to repo
- Project must be deployed and publicly accessible on Render upon completion

## Constraints

- **AI / Cost**: OpenAI GPT-4o Vision — $10 API budget; 10 analyses per user per day (midnight reset); dedupe to avoid waste
- **File Uploads**: Images only (validate MIME type); max 10 MB per file
- **Backend**: Django (Python) with Django ORM + migrations
- **Database**: PostgreSQL — Django ORM only, no raw SQL
- **Frontend**: Django templates + HTML/CSS (server-rendered, no SPA framework); mobile-responsive, web-first
- **Storage**: AWS S3 for all media; only S3 URLs/keys stored in DB
- **Deployment**: Render (web service + managed PostgreSQL)
- **Testing**: Django test suite + Postman for endpoint testing
- **Collaboration**: Git remote (GitHub/GitLab); venv for isolation; `.env` for local secrets

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| GPT-4o Vision for care label interpretation | Strong vision capability, widely adopted, JSON mode available | — Pending |
| Synchronous OpenAI calls (no Celery) | Reduces infrastructure complexity for a group project | — Pending |
| Django templates (server-rendered) | Keeps the stack unified, no separate JS build pipeline | — Pending |
| AWS S3 for image storage | Scalable, decoupled from Render's ephemeral filesystem | — Pending |
| 10 analyses/day per user (midnight reset) | Balances usability with $10 API budget constraint | — Pending |
| Django admin for usage monitoring | Zero custom UI work, sufficient for internal visibility | — Pending |
| Store raw JSON + user-edited final version separately | Preserves AI output for audit while letting user correct mistakes | — Pending |

---
*Last updated: 2026-02-19 after initialization*
