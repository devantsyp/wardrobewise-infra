# Domain Pitfalls

**Domain:** Django + OpenAI Vision + AWS S3 + Render (Group Project)
**Project:** LaundryAdvisor
**Researched:** 2026-02-19
**Confidence:** HIGH (training data through Aug 2025, all pitfalls are well-established in this stack's community)

---

## Critical Pitfalls

Mistakes that cause rewrites, lost data, or blown budgets.

---

### Pitfall 1: Committing Secrets or Hardcoding API Keys

**What goes wrong:** A team member hardcodes `OPENAI_API_KEY`, `AWS_SECRET_ACCESS_KEY`, or `SECRET_KEY` directly in `settings.py` or a view, pushes to GitHub, and the key is live. OpenAI and AWS both have automated scanners that find exposed keys; AWS accounts have been billed thousands of dollars within hours.

**Why it happens:** Local dev "it works on my machine" shortcuts. One teammate doesn't notice the `.env` pattern is established.

**Consequences:** Exposed OpenAI key = $10 budget gone in minutes. Exposed AWS key = S3 bill or bucket wiped. Requires rotating all credentials immediately.

**Prevention:**
- Commit `.env.example` with placeholder values on Day 1, before any real secrets exist.
- Add `.env` to `.gitignore` before the first commit — not after.
- Use `python-decouple` or `django-environ` and fail loudly (`raise ImproperlyConfigured`) if a required env var is missing.
- Run `git grep -r "sk-"` and `git grep -r "AKIA"` in CI or pre-commit hook to catch key patterns.
- Set AWS IAM policy to restrict the S3 key to only the target bucket — limits blast radius.

**Detection:** GitHub secret scanning alerts. AWS GuardDuty / "unusual activity" emails. Unexpected OpenAI usage spikes in the dashboard.

**Phase:** Address in Phase 1 (project setup). The `.env` pattern and `.gitignore` must be in place before any teammate clones the repo.

---

### Pitfall 2: Blowing the $10 OpenAI Budget Before Demo Day

**What goes wrong:** No hard server-side enforcement. GPT-4o Vision costs ~$0.01–$0.03 per image analysis call. With 5 teammates doing development testing plus any demo load, $10 disappears in a few days if the budget is not tracked and capped at the application layer.

**Why it happens:** Relying only on the rate limit (10/user/day) without tracking cumulative spend. Dev testing bypasses the per-user limit if you're logged in as different accounts. No monitoring until the key stops working.

**Consequences:** API key stops working mid-demo. No analyses possible. Can't increase the budget mid-project if the key owner is unavailable.

**Prevention:**
- Store every API call in the database: timestamp, user, model, input tokens, output tokens, estimated cost.
- Add a global `APIBudgetGuard` check: if total spend >= $9.00 (leave headroom), refuse new calls and alert.
- Keep a single shared OpenAI key in Render environment — not in individual developer `.env` files — to centralize tracking.
- For local dev testing, use a fixed mock/fixture response rather than real API calls.
- The 10/user/day limit helps but is not enough alone — you need cumulative spend tracking.

**Detection:** `AnalysisLog` admin view showing cumulative spend. OpenAI dashboard usage tab.

**Phase:** Address in Phase 2 (AI integration). Build the `AnalysisLog` model and budget guard before wiring up any view that calls the API.

---

### Pitfall 3: Render Ephemeral Filesystem — Media Files Lost on Deploy

**What goes wrong:** Uploads work perfectly in local dev because Django saves files to `MEDIA_ROOT` on disk. On Render, every deploy or dyno restart wipes the filesystem. Any uploaded images stored locally are permanently deleted. Users lose all their garment photos.

**Why it happens:** `DEFAULT_FILE_STORAGE` is not set to S3 in production. Developer tests uploads locally, they "work", and the S3 integration is assumed to be optional or deferred.

**Consequences:** Production data loss. Users upload garments, deploy happens (or Render's free tier spins down and restores), all photos are gone. Requires re-upload of all images and rebuilding trust.

**Prevention:**
- Configure `django-storages` with S3 from the very first deploy. Do not ship to Render without S3 configured.
- Use environment-variable-switched storage: `DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'` when `USE_S3=True` in env.
- Local dev uses `FileSystemStorage` (default) with a local `media/` directory.
- Never commit the `media/` directory. It must be in `.gitignore`.
- Test the full upload → S3 → retrieve flow in staging before any real user data is collected.

**Detection:** Uploaded files return 404 after a Render deploy. `media/` directory in the repo. `DEFAULT_FILE_STORAGE` not set in production settings.

**Phase:** Address in Phase 2 (S3 + file upload). Do not defer S3 integration to a later phase.

---

### Pitfall 4: Django Migration Conflicts in a Group Project

**What goes wrong:** Two teammates each add a field to the same model in separate branches. Both run `makemigrations`. Both create `0003_xxx.py`. When merged, Django detects two migrations with the same parent (`0002`) — a conflict. Running `migrate` fails.

**Why it happens:** No coordination on who "owns" migration generation. Teammates work on the same model concurrently without communicating.

**Consequences:** Blocked deploys. The fix (`mergemigrations`) usually works but can confuse teammates unfamiliar with it. On Render, a failed `migrate` during the build step means the deploy fails.

**Prevention:**
- Only one person generates migrations for a model change at a time. Communicate in the team channel before running `makemigrations`.
- When a conflict is detected: `python manage.py makemigrations --merge` creates a merge migration. Review it, commit, and push.
- Keep migration files small and focused — one logical change per migration.
- Never squash migrations on a shared branch without team coordination.
- Add `python manage.py migrate --check` to Render build command to catch unapplied migrations before deploy.

**Detection:** Git merge shows two files both named `000N_auto_...` with the same parent. `django.db.migrations.exceptions.NodeNotFoundError` on `migrate`.

**Phase:** Establish the convention in Phase 1 (project setup). Add team norms to `CONTRIBUTING.md` before the first model is written.

---

### Pitfall 5: `collectstatic` Failing on Render Deploy

**What goes wrong:** The Render build command includes `python manage.py collectstatic --noinput` but the command fails because: (a) `STATIC_ROOT` is not set, (b) `whitenoise` is not in `INSTALLED_APPS` or middleware, (c) `DEBUG=False` in production causes Django to raise an error when it can't find a static file, or (d) `boto3`/`django-storages` is configured for static files but the S3 bucket doesn't exist or credentials are wrong.

**Why it happens:** Static files work in local dev with `DEBUG=True`. The production configuration is untested until the first deploy attempt.

**Consequences:** Every deploy fails. Nothing ships. Team loses hours debugging Render build logs.

**Prevention:**
- Use `whitenoise` for static files. Do not put static files in S3 (only media files in S3). This is simpler and avoids the double-storage-backend complexity.
- Required settings:
  ```python
  STATIC_URL = '/static/'
  STATIC_ROOT = BASE_DIR / 'staticfiles'
  STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
  MIDDLEWARE = ['whitenoise.middleware.WhiteNoiseMiddleware', ...]  # after SecurityMiddleware
  ```
- Test `DEBUG=False` + `collectstatic` locally before first deploy.
- Render start command: `gunicorn project.wsgi` — not `python manage.py runserver`.

**Detection:** Render build logs show `CommandError: You're using the staticfiles app...`. 500 errors on static asset requests in production.

**Phase:** Address in Phase 1 (deployment scaffolding). Get a "hello world" deploying to Render with whitenoise before any feature work.

---

## Moderate Pitfalls

---

### Pitfall 6: django-storages / boto3 Wrong Credentials or Region

**What goes wrong:** S3 upload fails silently or raises a cryptic `botocore.exceptions.ClientError: An error occurred (InvalidAccessKeyId)` or `NoSuchBucket`. Frequent causes: wrong `AWS_STORAGE_BUCKET_NAME`, bucket region mismatch (`AWS_S3_REGION_NAME` not set), or credentials with insufficient IAM permissions.

**Prevention:**
- Set `AWS_S3_REGION_NAME` explicitly — do not rely on auto-detection, which fails in some boto3 versions.
- The IAM policy for the S3 key needs: `s3:PutObject`, `s3:GetObject`, `s3:DeleteObject`, `s3:ListBucket` on the specific bucket ARN.
- Test credentials locally with `boto3.client('s3').list_buckets()` before wiring into Django.
- Required `settings.py` block:
  ```python
  AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
  AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
  AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
  AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')
  AWS_S3_FILE_OVERWRITE = False  # prevent name collisions
  AWS_DEFAULT_ACL = None         # required for buckets with ACLs disabled
  ```

**Detection:** `ClientError (403)` on upload. Images uploaded but return 403 on retrieval (missing `GetObject` permission or public access blocked incorrectly).

**Phase:** Phase 2 (S3 setup). Validate S3 connectivity with a standalone script before integrating into Django models.

---

### Pitfall 7: S3 Public vs. Private Bucket Misconfiguration

**What goes wrong:** Two failure modes in opposite directions:
1. Bucket is fully public → all user garment photos are world-readable with guessable URLs. A privacy disaster.
2. Bucket is fully private → `<img src="{{ item.photo.url }}">` in templates returns 403. Images don't load.

**Prevention:**
- Use private bucket + pre-signed URLs for user-uploaded content. django-storages generates these automatically when `AWS_QUERYSTRING_AUTH = True` (the default). Do not set `AWS_DEFAULT_ACL = 'public-read'`.
- For presigned URLs, set a reasonable expiry: `AWS_QUERYSTRING_EXPIRE = 3600` (1 hour).
- In templates, use `{{ item.photo.url }}` — django-storages handles signing. Never construct S3 URLs manually.
- Keep Block Public Access enabled on the bucket at the AWS console level as a backstop.

**Detection:** Images show in browser with a long query string (correct — presigned). Images load without any query string (bucket is public — wrong). Images return 403 (private but not using presigned URLs — wrong).

**Phase:** Phase 2 (S3 setup). Decision must be made before any uploads are wired up.

---

### Pitfall 8: MIME Type Spoofing on File Uploads

**What goes wrong:** A user renames `malware.php` to `malware.jpg` and uploads it. Django's `ImageField` with `Pillow` validates the image by trying to open it, which catches most cases — but an attacker can craft a valid-looking image that embeds a script. On the browser side, validating `file.type` only reads the browser-provided MIME type, which the client controls entirely.

**Prevention:**
- Use `django.core.validators.FileExtensionValidator` to restrict extensions to `['jpg', 'jpeg', 'png', 'webp']`.
- Use `Pillow` to verify the file is a real image server-side: open it with `Image.open()` and call `.verify()`. Do this in a custom form validator, not just a model field.
- Limit upload size at the Django level: `DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024` (10 MB).
- Also set max size in the Nginx/Gunicorn layer (Render handles this, but set `DATA_UPLOAD_MAX_MEMORY_SIZE` regardless).
- Never execute or serve uploaded files as scripts — S3 serves them as downloads with the correct content-type if you set `AWS_S3_OBJECT_PARAMETERS`.

**Detection:** Upload endpoint accepts non-image files. `file.content_type` check passes for renamed files (client-provided — not trustworthy).

**Phase:** Phase 2 (file upload handling). Build validation into the upload form from the start.

---

### Pitfall 9: OpenAI Vision API Returns Malformed or Inconsistent JSON

**What goes wrong:** You prompt GPT-4o with "respond only in JSON" and parse the response with `json.loads()`. The model occasionally returns JSON wrapped in a markdown code block (` ```json\n{...}\n``` `), returns partial JSON when the context is long, or returns a well-formed JSON object with missing keys you assumed were always present.

**Why it happens:** Relying on prompt engineering alone to enforce structure. `json.loads()` raises `JSONDecodeError` on markdown-wrapped JSON. Missing keys cause `KeyError` in downstream code.

**Prevention:**
- Use the OpenAI structured outputs / `response_format` parameter with a JSON schema. As of GPT-4o (2024-08-06+), this guarantees valid JSON matching your schema — no markdown wrapping, no missing required keys.
  ```python
  response = client.chat.completions.create(
      model="gpt-4o",
      response_format={"type": "json_object"},
      messages=[...]
  )
  ```
- Define a Pydantic model for the expected output and validate the parsed JSON against it. Treat any validation failure as a low-confidence result.
- Always use `.get('field', default)` instead of `['field']` when accessing parsed JSON fields, even with schema enforcement.
- Store the raw JSON string in the database before any parsing. If parsing fails, you have the original to debug with.

**Detection:** `json.loads()` raising `JSONDecodeError` in production logs. `KeyError` in view code processing the response.

**Phase:** Phase 2 (AI integration). Design the response schema and validation layer before writing any view code that consumes the API.

---

### Pitfall 10: Rate Limiting Implemented Per-Request Instead of Per-Day

**What goes wrong:** The 10/user/day limit is implemented by checking request count in the current Django session or with a simple in-memory counter. On Render, a new dyno gets a fresh process — in-memory counters reset. Session-based counters reset on logout. The limit is trivially bypassed.

**Prevention:**
- Implement rate limiting in the database: `AnalysisLog` model with `user`, `created_at`, and `analysis_type` fields.
- Check count with:
  ```python
  from django.utils import timezone
  today = timezone.now().date()
  count = AnalysisLog.objects.filter(
      user=request.user,
      created_at__date=today
  ).count()
  if count >= 10:
      # block and return error
  ```
- The check and the creation of the log entry must be in a database transaction to prevent race conditions under concurrent requests.
- "Midnight reset" is automatic because you're filtering by `__date=today` — no cron job needed.

**Detection:** User can submit more than 10 analyses per day. Different browser sessions bypass the limit.

**Phase:** Phase 2 (AI integration). Build the `AnalysisLog` model before wiring up the analysis view.

---

### Pitfall 11: Analysis Deduplication Key Is Too Broad or Too Narrow

**What goes wrong:**
- Too broad: Cache key is just `user_id + item_id`. Re-uploading a different care label photo for the same item re-uses the cached result from the old photo. User gets stale analysis.
- Too narrow: Cache key includes the full image binary hash. Identical images uploaded twice (same bytes) each trigger a new API call. No deduplication benefit.

**Prevention:**
- Cache key should be a hash of the actual image content (e.g., `SHA-256` of the uploaded file bytes) stored in the `WardrobeItem` model as `care_label_hash`.
- On upload: hash the file, check `WardrobeItem.objects.filter(care_label_hash=hash, user=user).exists()`. If a prior analysis exists with the same hash, return it without calling the API.
- When the user re-uploads a care label photo, compute the new hash and compare to the stored hash. If different, invalidate the cached analysis and create a new one.
- The `AnalysisLog` should reference the `care_label_hash` used for that call, enabling future deduplication across users (if desired).

**Detection:** Uploading the same image twice triggers two API calls. Uploading a different image for the same item returns the old analysis.

**Phase:** Phase 2 (AI integration). Design the deduplication key into the `WardrobeItem` model from the start — retrofitting is painful.

---

### Pitfall 12: Render Cold Start During Demo

**What goes wrong:** Render's free tier spins down web services after 15 minutes of inactivity. The first request after spin-down takes 30–60 seconds to respond. During a demo or grading session, the first page load appears broken.

**Prevention:**
- During the demo period, upgrade to Render's paid tier ($7/month) or use a cron-based "keep-alive" ping (a UptimeRobot free monitor hitting the health check URL every 5 minutes).
- Add a `/healthz/` endpoint that returns HTTP 200 with minimal processing. Use this as the uptime monitor target.
- Set Render's health check path to `/healthz/` in the service settings.
- Warn the team: "first hit after idle is slow — open the app a minute before showing anyone."

**Detection:** First request times out. Render dashboard shows "Deploying" or "Spinning up" state.

**Phase:** Phase 3 (deployment + demo prep). Address before the final submission deadline.

---

### Pitfall 13: `DATABASE_URL` Not Parsed Correctly in Django Settings

**What goes wrong:** Render provides the PostgreSQL connection as a single `DATABASE_URL` env var (e.g., `postgres://user:pass@host/db`). Django's `DATABASES` setting expects a dictionary. If you manually parse the URL or use `dj-database-url` incorrectly, you get `OperationalError: could not connect` in production while SQLite works fine locally.

**Prevention:**
- Use `dj-database-url` (the standard solution):
  ```python
  import dj_database_url
  DATABASES = {
      'default': dj_database_url.config(
          default=env('DATABASE_URL'),
          conn_max_age=600,
          conn_health_checks=True,
      )
  }
  ```
- Local dev uses the same `DATABASE_URL` pattern pointing to a local PostgreSQL or the Render dev database — do not use SQLite locally if PostgreSQL is used in production. Schema differences cause migration surprises.
- `conn_max_age=600` enables persistent connections on Render — essential for performance on a web service handling multiple requests.

**Detection:** `django.db.utils.OperationalError` in Render logs. Works locally with SQLite but fails in production.

**Phase:** Phase 1 (project setup). Configure `dj-database-url` before writing any models.

---

### Pitfall 14: Requirements Drift in a Group Project

**What goes wrong:** Teammate A installs `Pillow` with `pip install Pillow` and doesn't update `requirements.txt`. The code works for Teammate A but fails with `ModuleNotFoundError` for everyone else who pulls the branch. On Render, the build installs from `requirements.txt`, so the deployed app is also broken.

**Prevention:**
- Team norm: any `pip install` is immediately followed by `pip freeze > requirements.txt` and committed in the same commit as the code that uses the package.
- Alternatively, use `pip-tools`: maintain a `requirements.in` with direct dependencies and run `pip-compile` to generate pinned `requirements.txt`. This avoids committing every transitive dependency's exact version.
- Add a CI check: `pip install -r requirements.txt && python -c "import django; import boto3; import openai; import PIL"` to verify all critical packages resolve.
- Use a virtual environment (`venv`) — never install packages globally. The `.venv/` directory must be in `.gitignore`.

**Detection:** `ModuleNotFoundError` on teammate's machine after pulling. Render build fails with `No module named 'storages'`.

**Phase:** Phase 1 (project setup). Pin the full initial `requirements.txt` (Django, psycopg2, boto3, django-storages, openai, dj-database-url, whitenoise, Pillow, gunicorn, python-decouple) before any feature work begins.

---

## Minor Pitfalls

---

### Pitfall 15: `DEBUG=True` Accidentally Left On in Production

**What goes wrong:** If `DEBUG=True` reaches Render, Django serves detailed error pages with full stack traces, local file paths, and environment variable values to any user who triggers a 500 error. This is a security issue and causes `collectstatic` to behave differently than expected.

**Prevention:**
- Set `DEBUG = env.bool('DEBUG', default=False)` in `settings.py`. Render environment should not have `DEBUG` set at all (defaults to `False`).
- Add `ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['yourdomain.onrender.com'])` — required when `DEBUG=False`.

**Detection:** Production error pages show full Django debug info. `ALLOWED_HOSTS` `DisallowedHost` errors in Render logs.

**Phase:** Phase 1 (project setup).

---

### Pitfall 16: OpenAI Synchronous Calls Blocking Django on Slow Responses

**What goes wrong:** GPT-4o Vision calls take 5–15 seconds on complex images. A synchronous Django view blocks the worker thread for the entire duration. With Gunicorn's default 2–4 workers on Render's free tier, concurrent analyses from multiple users can exhaust all workers and make the site unresponsive.

**Why it happens:** The project explicitly rules out Celery to reduce complexity. But long synchronous calls in Django views are a real bottleneck.

**Prevention:**
- This project accepts the tradeoff (Celery ruled out). Mitigate by:
  - Setting a request timeout on the OpenAI call: `client.chat.completions.create(..., timeout=30)`.
  - Setting Gunicorn timeout high enough: `gunicorn --timeout 60 project.wsgi`.
  - Showing a loading spinner in the UI so the user knows the request is in progress.
  - The 10/user/day limit naturally caps concurrent load.

**Detection:** Gunicorn worker timeout errors in Render logs (`[CRITICAL] WORKER TIMEOUT`).

**Phase:** Phase 2 (AI integration). Configure Gunicorn timeout in the Render start command before deploying AI views.

---

### Pitfall 17: `.env.example` Outdated — New Keys Not Communicated

**What goes wrong:** A teammate adds a new required environment variable (e.g., `OPENAI_ORG_ID`) to the code but forgets to add it to `.env.example`. Other teammates clone/pull and get a cryptic error. On Render, the variable isn't set and the feature silently fails or crashes.

**Prevention:**
- Team norm: any new `env('NEW_VAR')` call requires updating `.env.example` in the same commit.
- Use `raise ImproperlyConfigured("NEW_VAR is required")` for missing critical vars — fails loudly at startup instead of at request time.
- Review `.env.example` as part of every PR checklist.

**Phase:** Phase 1 (project setup). Establish the norm before the first environment variable is introduced.

---

### Pitfall 18: Laundry Basket Washing Plan Logic Is Over-Engineered or Under-Engineered

**What goes wrong:** The basket washing plan (grouping garments by temperature + color + delicate) seems simple but edge cases multiply fast: what if a garment has no wash temperature (AI returned `null`)? What if cold-wash and warm-wash items are both "light colors"? Over-engineering adds unneeded complexity; under-engineering produces a plan with wrong groupings.

**Prevention:**
- Define the grouping rules explicitly before implementation (document in a comment or design doc):
  - Primary sort: delicate vs. normal care
  - Secondary sort: wash temperature (cold / warm / hot / unknown)
  - Tertiary sort: color (dark / light / white / unknown)
- Garments with unknown temperature are flagged, not silently assigned to a group.
- AI confidence fields drive the "confirm before washing" prompts — surface them in the plan UI.

**Detection:** Garments with `null` wash temperature crash the grouping function. Two garments with different temperatures appear in the same load.

**Phase:** Phase 3 (basket feature). Write unit tests for the grouping algorithm before wiring it to real garment data.

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Phase 1: Project setup | Secrets committed before `.gitignore` is created | Create `.gitignore` + `.env.example` as the very first commit |
| Phase 1: Project setup | SQLite used locally, PostgreSQL in production — schema divergence | Use PostgreSQL locally from Day 1 via `DATABASE_URL` |
| Phase 1: Deployment scaffolding | `collectstatic` breaks first Render deploy | Configure whitenoise + `STATIC_ROOT` before any feature code |
| Phase 2: S3 integration | Media lost on Render deploy (ephemeral filesystem) | Wire S3 as `DEFAULT_FILE_STORAGE` before testing any uploads on Render |
| Phase 2: S3 integration | Bucket public/private misconfiguration | Decide private-with-presigned-URLs early; never `public-read` for user data |
| Phase 2: AI integration | Budget exhausted during development testing | Build `AnalysisLog` + budget guard before the first real API call |
| Phase 2: AI integration | JSON parsing failures from Vision API | Use `response_format={"type": "json_object"}` + Pydantic validation from day one |
| Phase 2: AI integration | Rate limit bypassable (in-memory counter) | DB-backed rate limit check only — no in-memory or session counters |
| Phase 2: AI integration | Deduplication key mismatch | Hash image bytes → store hash on model → check before calling API |
| Phase 2: File upload | MIME type spoofing | Server-side Pillow validation + extension whitelist in form validator |
| Phase 3: Collaboration | Migration conflicts | One person owns migration generation per model; `--merge` when conflicts occur |
| Phase 3: Collaboration | Requirements drift | `pip freeze` after every install; review `.env.example` in every PR |
| Phase 3: Basket feature | Grouping edge cases (null temperatures) | Define rules explicitly; unit test before integration |
| Phase 4: Demo / submission | Render cold start during demo | Keep-alive ping (UptimeRobot) or paid tier before demo day |
| Phase 4: Demo / submission | Gunicorn worker timeout on slow AI calls | Set `--timeout 60` in Render start command |

---

## Sources

- Training data (through Aug 2025): Django, django-storages, boto3, openai-python, dj-database-url, whitenoise, Render documentation — confidence HIGH for all established patterns in this stack.
- Note: WebSearch and WebFetch tools were not available during this research session. All claims reflect well-established, documented behavior of these libraries as of the knowledge cutoff. Patterns marked as requiring external validation are called out per pitfall.
- Items that should be verified against current docs before implementation:
  - OpenAI `response_format={"type": "json_object"}` — confirm it is still the correct parameter for GPT-4o structured output (OpenAI has iterated on this API surface).
  - Render free tier spin-down behavior — confirm 15-minute inactivity timeout is still current.
  - `AWS_DEFAULT_ACL = None` — confirm this is still required for buckets with Object Ownership set to "Bucket owner enforced" (AWS changed ACL behavior in 2023).
