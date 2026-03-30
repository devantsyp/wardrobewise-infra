---
status: resolved
trigger: "analyze-button-failure - Clicking Analyze on a care label image always fails with Analysis failed. Please try again."
created: 2026-03-29T00:00:00Z
updated: 2026-03-29T00:10:00Z
symptoms_prefilled: true
---

## Current Focus

hypothesis: CONFIRMED - OPENAI_API_KEY never loaded due to spaces around = in .env
test: ran python -c to load .env via django-environ and check os.environ
expecting: key to be present
next_action: COMPLETE - fixes applied and verified

## Symptoms

expected: User uploads a care label image, clicks Analyze, and gets back care instructions.
actual: The request fails every time with a generic "Analysis failed. Please try again." error message.
errors: "Analysis failed. Please try again." (displayed in UI)
reproduction: Open garment detail, upload a clear care label image, click Analyze button.
started: Since finishing Phase 3 implementation. Never worked in production.

## Eliminated

- hypothesis: OpenAI API key was valid but network/quota issue
  evidence: Key was never loaded into the environment at all — the problem was earlier, at env loading
  timestamp: 2026-03-29T00:05:00Z

- hypothesis: Bug in analysis service code or prompt
  evidence: Code is correct; failure was at _get_client() which calls OpenAI() with no key
  timestamp: 2026-03-29T00:05:00Z

## Evidence

- timestamp: 2026-03-29T00:03:00Z
  checked: wardrobe/views.py analyze_care_label_view
  found: catches AnalysisError and emits "Analysis failed. Please try again." — the exact error seen in UI
  implication: root cause is inside analyze_care_label() in services/analysis.py

- timestamp: 2026-03-29T00:04:00Z
  checked: wardrobe/services/analysis.py _call_api()
  found: any OpenAI exception is caught and re-raised as AnalysisError
  implication: the OpenAI() client itself is throwing on construction or on first call

- timestamp: 2026-03-29T00:05:00Z
  checked: laundry_advisor/settings/base.py and prod.py
  found: OPENAI_API_KEY is not referenced in Django settings at all — OpenAI() reads it directly from os.environ
  implication: key must be set in environment; need to check if it actually is

- timestamp: 2026-03-29T00:06:00Z
  checked: render.yaml
  found: OPENAI_API_KEY is completely absent from envVars section
  implication: production never has the key set — guaranteed failure in production

- timestamp: 2026-03-29T00:07:00Z
  checked: .env file
  found: line is "OPENAI_API_KEY = sk-proj-..." with spaces around =
  implication: django-environ rejects this line as "Invalid line" and key is never set in os.environ

- timestamp: 2026-03-29T00:08:00Z
  checked: ran django-environ read_env() against .env in Python shell
  found: "Invalid line: OPENAI_API_KEY = sk-proj-..." printed; os.environ['OPENAI_API_KEY'] = NOT SET
  implication: ROOT CAUSE CONFIRMED — spaces around = in .env cause silent parse failure

## Resolution

root_cause: |
  Two related problems, both preventing OPENAI_API_KEY from reaching the OpenAI client:
  1. LOCAL DEV: .env has "OPENAI_API_KEY = sk-proj-..." with spaces around the equals sign.
     django-environ's read_env() silently rejects this as an "Invalid line" and never sets
     os.environ['OPENAI_API_KEY']. The OpenAI() client initializes without a key and every
     API call raises an AuthenticationError, which is caught by _call_api() and re-raised as
     AnalysisError, which the view catches and displays as "Analysis failed. Please try again."
  2. PRODUCTION (Render): render.yaml had no OPENAI_API_KEY entry in envVars, so the key
     was never available in the production environment either.

fix: |
  1. Removed spaces from .env: changed "OPENAI_API_KEY = sk-proj-..." to "OPENAI_API_KEY=sk-proj-..."
  2. Added OPENAI_API_KEY with sync: false to render.yaml envVars so Render knows to expect
     it as a manually-set dashboard secret.

verification: |
  Ran python -c to load .env via django-environ and check os.environ['OPENAI_API_KEY'].
  Before fix: "Invalid line" warning printed, key NOT SET.
  After fix: key loads correctly as "sk-proj-39tiuAiA5vSg..."
  No "Invalid line" warning printed.

files_changed:
  - .env (removed spaces around = on OPENAI_API_KEY line)
  - render.yaml (added OPENAI_API_KEY with sync: false to envVars)
