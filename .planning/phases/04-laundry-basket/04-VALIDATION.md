---
phase: 4
slug: laundry-basket
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-02
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Django test runner (built-in, Django 5.2) |
| **Config file** | none — uses `manage.py test` |
| **Quick run command** | `DJANGO_SETTINGS_MODULE=laundry_advisor.settings.dev python manage.py test laundry --verbosity=1` |
| **Full suite command** | `DJANGO_SETTINGS_MODULE=laundry_advisor.settings.dev python manage.py test` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `DJANGO_SETTINGS_MODULE=laundry_advisor.settings.dev python manage.py test laundry --verbosity=1`
- **After every plan wave:** Run `DJANGO_SETTINGS_MODULE=laundry_advisor.settings.dev python manage.py test`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** ~10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-01-* | 01 | 0 | BSKT-02, BSKT-03 | unit | `python manage.py test laundry.tests.test_grouping` | ❌ W0 | ⬜ pending |
| 04-01-* | 01 | 1 | BSKT-03 | unit | `python manage.py test laundry.tests.test_grouping.GroupingLogicTest` | ❌ W0 | ⬜ pending |
| 04-02-* | 02 | 2 | BSKT-01, BSKT-02 | integration | `python manage.py test laundry.tests.test_views.BasketSelectionTest` | ❌ W0 | ⬜ pending |
| 04-02-* | 02 | 2 | BSKT-04 | integration | `python manage.py test laundry.tests.test_views.PlanDisplayTest` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `laundry/tests/__init__.py` — package marker
- [ ] `laundry/tests/test_grouping.py` — unit test stubs for `group_into_loads()` covering:
  - null/unknown temperature defaults to coldest load (30°C)
  - dry-clean-only garments routed to `special_care`, not loads
  - hand-wash-only garments routed to `special_care`
  - Whites / Lights / Darks classification
  - delicates separation when mixed with normals at same temp+color
  - delicates merged into load when no normals at that temp+color
  - warnings: air-dry, no-bleach, delicate-cycle extracted correctly
  - loads sorted by garment count descending
  - all special-care basket: empty loads list, non-empty `special_care`
  - empty garments list: returns empty loads and `special_care`
- [ ] `laundry/tests/test_views.py` — integration test stubs for BSKT-01 and BSKT-04

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live plan update on basket change | BSKT-01 | JS debounce / DOM rendering | Add garments to basket, verify plan updates without page reload |
| Stale plan warning on wardrobe change | BSKT-04 | Depends on re-analysis timestamp | Re-analyze a garment after saving plan, reload plan page, verify stale warning shown |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
