# Dependency upgrade plan: Linkaroo (2026-11-14)

**Scope:** `/dependency-upgrade`. Inventory, CVEs, breaking changes and a staged path. Only the security patch (Batch 1a) was applied. Everything else is a proposal.
**Evidence:** project manifests, installed environment, `uv pip list --outdated`, `pip-audit`, Django release notes and supported-versions page, PyPI metadata, and throwaway trial environments (`uv venv` in a scratch folder; the project's `.venv` and manifests were not touched until Batch 1a).

## 1. Inventory

| Item | Finding |
|---|---|
| Manifests | `requirements/{base,local,production,stage}.txt`. Exact pins of **top-level** packages, with transitive deps pinned by hand. |
| Lockfile | Was none. **Now** `requirements/production.lock` and `requirements/dev.lock` (uv, universal, sha256-hashed). Regenerate with the command in each file's header. |
| Python runtime | **Not pinned** anywhere except CI (`3.12`). Local `.venv` is CPython 3.12.14. Production runtime is **unknown** (no Dockerfile, Procfile, runtime.txt or `.python-version`). |
| Stale manifest | Root `base.txt` pinned **Django 5.0.1** (47 CVEs) and nothing referenced it. **Removed in Batch 1a.** |
| Frontend | Bootstrap **5.3.2** CSS/JS from jsDelivr (pinned, SRI). Google Charts `loader.js` with `google.charts.load('current')`, so the version **floats** (no SRI possible). |

| Package | Pinned | Latest | Used by our code? | Notes |
|---|---|---|---|---|
| Django | 5.2.17 → **5.2.19** (applied) | 6.1.3 (5.2.19 latest LTS) | yes | 5.2 = LTS, extended support to **April 2028** |
| asgiref | 3.8.1 | 3.13.0 | transitive (Django ≥3.8.1) | Django 6.0 needs ≥3.9.1 |
| sqlparse | 0.6.0 | 0.6.1 | transitive (Django, debug-toolbar) | |
| typing_extensions | 4.9.0 | 4.16.0 | **no**: only needed by asgiref on Python < 3.11 | Dead pin on 3.12 |
| tzdata | (unpinned) | 2026.x | transitive, **Windows only** | |
| django-jazzmin | 3.0.1 | 3.0.5 | admin theme | 3.0.5 declares Django 6.0 support |
| django-extensions | 3.2.3 | 4.1 | `ActivatorModel` only | 4.1 declares Django ≤5.2: **no Django 6 support declared** |
| python-dotenv | 1.2.2 | 1.2.4 | settings | |
| whitenoise | 6.6.0 | 6.12.0 | **no**: not in `MIDDLEWARE`, never imported | Dead dependency |
| psycopg2-binary | 2.9.10 | 2.9.13 | production DB driver | psycopg maintainers advise against `-binary` in production; Django recommends psycopg 3 |
| django-debug-toolbar | 5.2.0 | 8.0.0 | local only | |

## 2. CVEs and advisories

| Package | Status | Applies to Linkaroo? |
|---|---|---|
| **Django 5.2.17** | **9 CVEs fixed in 5.2.18 and 5.2.19** (official release notes). **`pip-audit` reported "No known vulnerabilities"**: its database lagged the vendor. **Treat Django's security release notes as the source of truth.** | **Yes, two:** CVE-2026-84429 (moderate, quadratic HTTP header parsing DoS, any client) and CVE-2026-108147 (low, base64 multipart buffered in memory, any POST endpoint). CVE-2026-87975 (moderate, formsets with editable UUID PKs): our PKs are UUIDs but we use no model formsets (low exposure). The rest are GIS/cache-middleware/i18n-cache issues: not used. **Fixed by Batch 1a.** |
| Other Python packages | `pip-audit`: none known | — |
| Bootstrap 5.3.2 | No known advisories for 5.x (the known Bootstrap CVEs affect 3.x/4.x); GitHub advisory search was inconclusive | Low |
| Google Charts | Unpinned third-party script (supply-chain risk, not a CVE) | Covered by CSP allowlist; see Batch 3 |

## 3. Breaking-change classification

| Change | Class | Our exposure (evidence) |
|---|---|---|
| Django 5.2.17 → 5.2.19 | Patch / security | 5.2.18 changed `parse_header_parameters()` parsing of malformed headers. 5.2.19 changes cache keys for `Vary`-less requests (no cache middleware here). **Tests: 73/73.** |
| asgiref 3.8 → 3.13, django-extensions 3.2.3 → 4.1, jazzmin 3.0.1 → 3.0.5, sqlparse/dotenv/psycopg2 patches | Minor / patch | Trial env: 73/73 with Deprecation **and** PendingDeprecation warnings as errors, no migrations, deploy check unchanged, audit clean |
| Django 5.2 → **6.x** | **Major** | Python ≥ 3.12 (production runtime unknown: **blocker to verify**). `asgiref` ≥ 3.9.1. Removals we checked: positional `Model.save()` args (our overrides pass `*args` through; no positional callers), `URLField` default scheme (already explicit `https`), `DEFAULT_AUTO_FIELD` (set explicitly), `FORMS_URLFIELD_ASSUME_HTTPS` (not used). PBKDF2 iterations 1.0M → 1.2M (hashes upgrade on next login). **Our code emits zero `RemovedInDjango60/61` warnings in tested paths.** Third-party blockers: **django-extensions** (no Django 6 classifier) and debug-toolbar (local only). |
| psycopg2 → psycopg 3 | Driver swap | Same backend `django.db.backends.postgresql`. Needs a real PostgreSQL smoke test, which can't be done locally (no server). |

**Deprecated/legacy usage found:**
- `ENGINE: 'django.db.backends.postgresql_psycopg2'`: a legacy alias Django still maps to `postgresql` (`django/db/utils.py`). Cosmetic; rename to `django.db.backends.postgresql`.
- `google.charts.load('current')`: floating version.

## 4. Staged path

Ranges are the **compatible windows**. Requirements keep exact pins, and a lockfile records hashes.

| Batch | Changes | Compatible range | Risk | Verification | Status |
|---|---|---|---|---|---|
| **1a Security** | Django 5.2.17 → **5.2.19**; delete stale root `base.txt` | `Django>=5.2.19,<5.3` | Low | 73/73 tests (strict warnings), deploy check, audit | **Applied** |
| 1b Patch | jazzmin 3.0.5, psycopg2-binary 2.9.13, python-dotenv 1.2.4, sqlparse 0.6.1 | `django-jazzmin>=3.0.5,<3.1`, `psycopg2-binary>=2.9.13,<2.10`, `python-dotenv>=1.2.4,<1.3`, `sqlparse>=0.6.1,<0.7` | Low | Trial env 73/73; project venv from lock 73/73 | **Applied** |
| 2 Hygiene | Generate **hashed lockfiles** per environment (`uv pip compile --generate-hashes`, Linux + Windows variants). Pin the runtime (`.python-version` = 3.12, plus deployment docs). Drop dead pins: `typing_extensions` (not needed on 3.12), `whitenoise` (unused; *or* enable it if static files aren't served by a proxy, a deployment decision). Canonical DB engine name. | n/a | Low | `requirements/{production,dev}.lock` (universal, hashed); `.python-version`; CI installs with `--require-hashes` and fails on lock drift | **Applied**: locks, runtime pin, `typing_extensions` dropped, engine renamed. WhiteNoise left (hosting decision) |
| 3 Minor | asgiref 3.13.0, django-extensions 4.1. Bootstrap 5.3.2 → 5.3.9 (recompute SRI from downloaded files). Pin Google Charts to a numbered release. | `asgiref>=3.9.1,<4` (already Django-6-ready), `django-extensions>=4.1,<5` | Low–Medium | Trial env 73/73; visual diff via `tools/ux-audit` for Bootstrap | **Python part applied** (asgiref 3.13.0, django-extensions 4.1). Bootstrap/Charts pin still proposed |
| 4 Driver | psycopg2-binary → `psycopg[binary]` 3.x (or `psycopg[c]` built against system libpq in production) | `psycopg>=3.2,<4` | Medium | **Needs** a staging PostgreSQL: migrate, CRUD, redirect, dashboard queries | Proposed; blocked on staging DB |
| 5 Major | Django **6.2 LTS** (planned April 2027). Skip 6.0/6.1: their support ends **before** 5.2 LTS (Apr/Dec 2027 vs Apr 2028). Prerequisites: confirm production Python ≥ 3.12; jazzmin with 6.2 support; django-extensions with Django 6 support **or** inline `ActivatorModel` (3 fields, manager, `save()`; no migration change); swap the custom CSP middleware for Django's built-in CSP (6.0+). | `Django>=6.2,<6.3` | High (major) | Full suite + `-W error`, admin smoke, staging soak | Planned |

## 5. Rollback

- **Batch 1a:** `git revert` the commit, then `pip install -r requirements/production.txt` (5.2.17). No migrations or data changes in either direction.
- **Batches 1b–3:** one commit each; revert plus reinstall. Once lockfiles exist, roll back by deploying the previous lock.
- **Batch 4 (driver):** revert to `psycopg2-binary`; same backend, so no data impact.
- **Batch 5 (major):** deploy from a tagged 5.2 release. Take a DB backup before the first 6.x deploy, since 6.x may ship new migrations for contrib apps. Don't run 6.x migrations against production without the backup and a staging rehearsal.

## 6. Unknowns / blockers
- Production Python version and hosting (blocks Django 6 planning and the psycopg build choice).
- No PostgreSQL available locally: driver changes are untested against a real DB.
- `pip-audit` lag: add a check of Django's security release notes (or subscribe to django-announce) to the release routine.
