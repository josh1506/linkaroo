# Release readiness: UPG-001 / 2026-11-14

- **Candidate:** branch `upgrade/upg-001`, 24 commits on top of `master@9eac668` (+ this checklist), 100 files, +2.5k/−0.2k lines. **Not pushed. Not deployed.**
- **Release owner / approver / environment:** UNKNOWN (no owner, approver, window or production details on record).
- **Deployment authorization:** **PENDING**. None given.

## Decision: **NO-GO for production.** GO to push the branch for review, run CI, and deploy to staging.

The code-level evidence is strong: 78 tests, every CI step passes locally, security fixes have regression tests, the migration was rehearsed on PostgreSQL. But production can't be configured or rolled back safely yet. B1–B7 below must close first. None of them is a code defect. They are environment, process and ownership gaps that only the project owner can close.

## Checks (pass / fail / unknown, with evidence)

| Check | Status | Evidence |
|---|---|---|
| Scope/diff and code review | **FAIL (B4)** | All 24 commits AI-authored. No human review yet. Per-change reports: `docs/UPG-001-CHANGE-REPORT.md`, `docs/THREAT_MODEL.md`, `docs/UX_AUDIT.md`, `docs/DEPENDENCY_UPGRADE_PLAN.md`, `docs/DATA_MIGRATION_RUNBOOK.md` |
| Tests | PASS | `python -W error::DeprecationWarning -W error::PendingDeprecationWarning manage.py test`: **78/78** run twice (79 s each, identical set), then **79/79** after adding `test_config.py`, 0 skips/xfail, no flakes |
| CI | **UNKNOWN (B3)** | `.github/workflows/ci.yml` has **never run** (branch not pushed). Each CI step run locally: check, makemigrations --check, lock in sync, `--require-hashes` install, deploy checklist (only W004 HSTS, intentional), pip-audit: **all PASS** |
| Build artifacts | PASS | `collectstatic` (production settings) collected 232 files. WSGI app imports under production settings. Stage entrypoint loads. All Python compiles |
| Lint / typecheck | N/A | None configured in repo (not added: out of scope) |
| Authorization / object boundaries | PASS | 32 security tests: anonymous, wrong owner (404 on read/update/delete), staff-only admin, no mass assignment, CSRF, lockout incl. admin, spraying cap, proxy-spoof resistance, CSP, XSS escaping (`test_security.py`) |
| Secrets | **FAIL (B1)** | No secrets in the tree (scanned). The old `SECRET_KEY` and DB password are **in public git history**, so treat them as compromised until rotated |
| Dependency advisories | PASS (with caveat) | Django 5.2.19 LTS. `pip-audit` clean. Django's own security notes checked (5.2.18/5.2.19: 9 CVEs, fixed). Hashed lockfiles |
| API / old-client compatibility | PASS | No JSON API. Public contract `GET /<alias>/` → 302 + click, unknown → 404, non-GET → 405 is unchanged and tested. Existing aliases (even ones that fail new rules) still redirect and stay editable (tested) |
| Schema migration and locking | PASS (rehearsed) / production apply PENDING | One migration, `0004_widen_url_link`: metadata-only, 0-row backfill, `lock_timeout 2s`, guarded reverse. Rehearsed on PostgreSQL 17 with 2M clicks (`DATA_MIGRATION_RUNBOOK.md`) |
| Backup and restore | **UNKNOWN for production (B6)** | Procedure rehearsed: dump 10 s, restore 29 s, fingerprints match, 1-row tamper detected. No production backup exists or has been verified |
| Staging smoke / performance | **FAIL: no staging (B5)** | Local benchmark (50 links / 5k clicks): dashboard **953 → 4 queries, 1216 → 41 ms**, redirect 2 queries / 0.5 ms. PostgreSQL query plans measured in rehearsal. No Lighthouse/CWV measured |
| Monitoring / alerts | **Accepted risk A1** (needs sign-off) | Errors (5xx) logged to stderr with tracebacks. No metrics, alerting, error tracking or uptime checks exist |
| Feature flags / abort / rollback owner | **FAIL (B7)** | Env-var kill switches exist (section 4). No rollback owner or abort authority named |
| Release notes / support contact | PASS / UNKNOWN | `CHANGELOG.md` (user-visible changes). The README's support email is unverified (the domain appears not to be in use) |
| Human go/no-go | **PENDING** | — |

## Test matrix (UPGRADE_REQUEST acceptance criteria → evidence)

| Scenario | Level | Expected | Evidence (actual) |
|---|---|---|---|
| Register / login / logout | Integration | Works; existing password hashes still valid | `users/tests.py` (6) PASS |
| Create / edit / delete link; owner set | Integration | Works, owner from session | `test_views.OwnerFlowTests` PASS; browser walkthrough done in UPG-001 |
| Visit short link | Integration | 302 to stored link + 1 click; 404 unknown; 405 non-GET | `RedirectContractTests`, `CsrfAndMethodTests` PASS |
| Analytics accurate | Integration | Totals equal raw rows; local-day buckets | `AnalyticsDayBucketTests`, equivalence run vs old helpers (identical except intended TZ fix) |
| Wrong owner / anonymous / non-staff | Security | 404 / login redirect / no admin | `ObjectAuthorizationTests` PASS |
| Malformed input (schemes, aliases, long links, XSS titles) | Integration | Safe validation error, no 500 | `DestinationValidationTests`, `AliasValidationTests`, `test_create_rejects_link_over_2048`, XSS escape test PASS |
| Abuse: brute force, spraying, sign-up floods, click inflation | Security | 429 / capped | `AuthenticationAbuseTests`, `ClickRecordingAbuseTests` PASS |
| Concurrent / retried request | Integration | Correct under retries | Migration retry after lock timeout rehearsed. **Not covered:** concurrent alias creation race (unique constraint protects data; the user would see a 500, not a form error), accepted risk A8 |
| Small screens / keyboard / reduced motion | UX/a11y | Usable at 320 px, focus visible, no motion | `test_ux.py` (10) PASS; screenshot audit 0 contrast failures; no animations exist. **Not run:** axe-core, real screen reader, real devices (A3) |
| Performance | Perf | No regression | Query budgets asserted (`QueryBudgetTests`); benchmark above |
| Migration forward / abort / back | Recovery | Safe | Rehearsed on PostgreSQL 17 (5 scenarios) |
| Backup → restore → reconcile | Recovery | Identical | Rehearsed; production **not done (B6)** |
| App rollback | Ops | Prior behaviour restored | **Hazards found**: see section 5 |

## Blockers (must close before production)

| ID | Blocker | Owner action |
|---|---|---|
| **B1** | Credentials exposed in public history | Rotate `SECRET_KEY` and the DB password **after** the new release is verified (section 5 explains the order). Rotating the key logs every user out |
| **B2** | Production environment undefined in the repo: hosting, Python version (≥3.12 needed for the Django 6 path; 3.12 used here), PostgreSQL version, **WSGI server (none declared)**, static file serving (`DEBUG=False` and WhiteNoise not enabled, so something else must serve `/static/`), TLS/proxy topology | Document it, then set the env vars in section 3. Mis-set values cause outages (HTTPS redirect loops, Secure cookies over http break login, missing `DB_PASSWORD` refuses to start) |
| **B3** | CI never ran | Push the branch, open a PR, require a green CI run |
| **B4** | No human code review | Review the PR (security-relevant commits first: `a56b305`, `91c35a2`, `ea8bc53`, `57cd461`, `a44e107`, `3b5aff1`, `1ef82a5`) |
| **B5** | No staging environment | Deploy to staging on PostgreSQL. Smoke test (section 6). Run migration 0004 there first |
| **B6** | No verified production backup | Take a backup and verify the restore with `data_fingerprint` (runbook section 4) before migrating |
| **B7** | No release owner, approver, window or abort authority | Name them |

## Accepted risks (proceed only with explicit owner sign-off)

| ID | Risk | Mitigation |
|---|---|---|
| A1 | No metrics, alerts or error tracking; stderr logs only | Watch logs during the observation window. Add uptime and error tracking next (external services need approval) |
| A2 | Rate limits live in per-process memory (per worker, evictable) | Configure a shared `CACHES` backend (database or Redis) |
| A3 | No axe-core, Lighthouse, screen-reader or real-device testing | Run them on staging |
| A4 | "Subscribe Now" / "Contact Us" do nothing; marketing copy claims geographic/referral analytics that don't exist | Product decision |
| A5 | HSTS off; CSP in enforce mode by default | Start with `CSP_REPORT_ONLY=True` on staging/production, then enforce; ramp HSTS after TLS is confirmed |
| A6 | Malicious destinations behind the short domain (phishing) | Abuse reporting and link-disable procedure needed (threat model F12) |
| A7 | Google Charts loaded from a third party | CSP-allowlisted; pin or self-host later |
| A8 | Concurrent creation of the same alias: one request gets a 500 (unique constraint holds) | Low likelihood; handle `IntegrityError` as a form error later |

## 3. Production configuration (all documented in `.env.example`; enforced by `test_config.py`)

Required: `SECRET_KEY` (new, long, random), `DB_PASSWORD`, `DJANGO_ALLOWED_HOSTS` (real hostnames; also enables the "no self-referencing links" check), `DEBUG=False`.
Topology-dependent: `BEHIND_TLS_PROXY`, `TRUSTED_PROXY_COUNT` (**must** match the number of proxies, or one client can lock out everyone), `SECURE_SSL_REDIRECT`, `SECURE_COOKIES`.
Tunables: `CSP_REPORT_ONLY`, `SECURE_HSTS_SECONDS`, `CLICK_RECORD_LIMIT_PER_MINUTE`, `SIGNUPS_PER_CLIENT_PER_HOUR`, `LOG_LEVEL`, `DJANGO_LOG_LEVEL`, `DB_NAME/USER/HOST/PORT`.

## 4. Kill switches (env, no redeploy of code needed beyond restart)
`CSP_REPORT_ONLY=True` (CSP stops blocking) · `CLICK_RECORD_LIMIT_PER_MINUTE=0` (record every click) · raise `SIGNUPS_PER_CLIENT_PER_HOUR` · `SECURE_SSL_REDIRECT=False` / `SECURE_COOKIES=False` (only if TLS is broken) · `DJANGO_LOG_LEVEL=WARNING` (also log 4xx). There is no feature-flag system. The UI and security fixes have no runtime toggle; reverting them means redeploying.

## 5. Rollback (app vs data)

**Hazards found while preparing this checklist:**
1. **DEBUG trap:** `master` reads `DEBUG` as a raw string, so `DEBUG=False` **enables** debug pages. If you roll back to `master`, **unset `DEBUG`** (don't set it to `False`).
2. **Password trap:** `master` hardcodes the DB password. After B1 rotation, `master` **can't connect**.

**Therefore the first production release must go in this order:** (1) deploy this release using the *current* DB password via `DB_PASSWORD`; (2) verify (section 6); (3) observe; (4) only then rotate the DB password and `SECRET_KEY` (B1); (5) tag the release. Every later rollback targets the **previous release tag**, never `master`.

- **App rollback:** redeploy the previous tag (or, before step 4 only, `master` with `DEBUG` unset). Old code is compatible with the widened `link` column.
- **Data rollback:** none expected. Migration 0004 rewrites no data. **Don't migrate backwards** once links longer than 200 characters exist (the migration refuses). Restore from backup only for corruption, into a new database first, then reconcile with `data_fingerprint`.
- **Abort thresholds** (proposed; owner to confirm): 5xx > 1% of requests over 5 min; any redirect 5xx; short-link 404 rate above pre-release baseline; login success rate drop > 20%; any `DisallowedRedirect`/`ImproperlyConfigured` in logs. Abort = app rollback.

## 6. Smoke test (staging, then production)
1. `python manage.py check --deploy` → only W004 (if HSTS is still 0).
2. `python manage.py data_fingerprint --json > before.json` (read-only).
3. `python manage.py migrate` → 0004 applies (on lock timeout: no change, re-run).
4. An existing short link → 302 to the same destination, and its click count rises by 1.
5. Unknown alias → branded 404. `POST /<alias>/` → 405.
6. Log in as an existing user (old password works), dashboard loads with charts, create a link with a 247-char URL, edit it, delete it via the dialog.
7. Admin: staff login works and the URL change form opens (Jazzmin on Django 5.2).
8. Response headers: `Content-Security-Policy`, `Set-Cookie ...; Secure; HttpOnly`, no debug page on a 404.
9. `data_fingerprint` again: counts/checksums unchanged except rows touched by the smoke test.
10. Observation window: 24 h of watching stderr for 5xx/`DisallowedRedirect`/429 spikes.
