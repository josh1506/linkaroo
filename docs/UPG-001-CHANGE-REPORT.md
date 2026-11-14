# UPG-001 — Change report (local implementation)

- **Branch:** `upgrade/upg-001` (base `master` @ `9eac668`), 11 local commits, **not pushed, not deployed**.
- **Date:** 2026-11-14. **Environment:** Windows 11, CPython 3.12.14 venv (`.venv`, git-ignored), Django 5.0.1 as pinned, SQLite.
- **Scope:** local changes only per `UPGRADE_REQUEST.md`. No production access, no schema migrations, no credential rotation.

## 1. What changed and why

| Commit | Change | Finding |
|---|---|---|
| `4e21623` | Characterization tests: redirect contract, URL CRUD, auth, ownership (tests dir had no `__init__.py`, so 0 tests ran) | Q: no tests |
| `a56b305` | `get_queryset()` scoped to `owner=request.user` on detail/update/delete | **S1 IDOR** (another user could view/retarget/delete links); R1 500 on unknown pk |
| `91c35a2` | Secrets from env; boolean `DEBUG`/`PRODUCTION`; secure cookies + SSL redirect by default; HSTS/proxy opt-in; debug toolbar local-only; fixed `manage.stage.py`/`wsg.stage.py`/`asgi.py`; `psycopg2-binary` added to production reqs; `.env.example` | **S2** `DEBUG=False` evaluated truthy; **S3** hardcoded key/password; **S4** hardening |
| `ea8bc53` | Alias rules (slug chars, ≤64, reserved route names) for new/changed aliases only; blank alias on edit keeps existing alias; login throttle 5 fails / 15 min per IP+username (HTTP 429), checked before `authenticate()` | **S5**, **S6** |
| `f189fb6` | Day buckets use `TIME_ZONE` for labels and counts; dashboard = 1 annotated + 1 grouped query; `select_related` on click log; redirect skips User fetch | **D1** analytics bug; **P1/P2** N+1 |
| `222272f` | Responsive layout (<992px), zoom allowed, visible focus, scrollable auth pages, error summaries, heading copy fixes | **U1** |
| `cfcb663` | `sqlparse` 0.4.4→0.6.0, `python-dotenv` 1.0.1→1.2.2; admin smoke test | Dependency CVEs |
| `391593a`, `bb0cc6e` | Errors logged to stderr in all environments (5xx by default) | **P4** silent prod errors |
| `b95aee7` | Hero SVG path precision 6→1 decimals | **P3** |

**Preserved deliberately:** 302 redirect + click on GET, 404 unknown alias, 405 non-GET (incl. HEAD), existing aliases (even ones that fail new rules), URL/UUID routes, auth flows and password hashes, schema (no migrations), desktop visual layout, brand colors.

## 2. Verification (actual results)

| Check | Before | After |
|---|---|---|
| `python manage.py test` | 0 tests ran | **31 passed** (4 security tests failed on original code: IDOR ×3, 500 on unknown pk) |
| `manage.py check` | 1 warning (W004 missing `media/` dir) | same, pre-existing |
| `makemigrations --check` | no changes | no changes |
| `check --deploy` (staging/production settings, DEBUG=False) | 7 warnings incl. W018 DEBUG on, insecure cookies, no SSL redirect | 1: W004 HSTS=0 (intentional until HTTPS confirmed) |
| `DEBUG=False` env | `settings.DEBUG == 'False'` (truthy) | `False` |
| `pip-audit -r requirements/production.txt` | 61 known vulns | 47, all Django 5.0.1 |
| Hardcoded secrets in tree | 2 | 0 (still in git history) |

**Browser flow (local dev server, demo data):** create (reserved alias rejected with inline message → valid alias saved) → GET alias 302 + click recorded → edit with blank alias keeps alias → delete via modal (focus moves into dialog, Esc closes, focus returns) → alias 404. Keyboard focus ring present on all sidebar controls.

## 3. Measured differences

Seeded 50 links / 5,000 clicks, SQLite, test client, median of 15–200 runs (local laptop; relative comparison only):

| Endpoint | Queries before → after | Median before → after |
|---|---|---|
| Dashboard `/urls/` | 953 → **4** | 1216 ms → **48 ms** |
| Click log `/urls/tracker/list/` | 14 → 4 | 22 → 17 ms |
| Link list `/urls/list/` | 4 → 4 | ~unchanged |
| Redirect `/<alias>/` | 3 → **2** | 2.2 → 1.0 ms |

Analytics equivalence (old vs new helpers, 3,000 clicks): **identical** values at a time where UTC and Manila share a date; in 00:00–08:00 Manila the only difference is the intended fix (window ends on local today).

Responsive (320 / 768px, all 7 pages): horizontal overflow **827px → none**; app pages scroll; auth form width 89–96px → full width. Desktop 1440px element geometry: **identical** to original on all pages (only extra element is the `.table-responsive` wrapper).

Hero SVG: 547 KB → 319 KB (gzip 157 → 97 KB); render diff 0.03% pixels >32/255 (edge anti-aliasing).

**Not measured:** Lighthouse/Core Web Vitals and axe (no tooling installed; would need `npx lighthouse`/axe download), production latency, real-device testing.

## 4. Rollout (requires separate approval — nothing here is deployed)

1. **Rotate** the Django `SECRET_KEY` and the production DB password that were committed in history (logs out all sessions when key changes). Decide whether to purge history (`git filter-repo`) — coordinate with anyone who has clones.
2. Set env on the server: `SECRET_KEY`, `DB_PASSWORD` (now **required** — production refuses to start without it), `DJANGO_ALLOWED_HOSTS`, `DEBUG=False`. If TLS terminates at a proxy, set `BEHIND_TLS_PROXY=True` **before** deploy or `SECURE_SSL_REDIRECT` will loop. If the site is not on HTTPS yet, set `SECURE_SSL_REDIRECT=False` and `SECURE_COOKIES=False` temporarily (cookies marked Secure are dropped over plain http → logins fail).
3. `pip install -r requirements/production.txt` (now includes `psycopg2-binary`; debug toolbar no longer installed in prod).
4. Deploy; no migrations. Run `manage.production.py check --deploy`.
5. Smoke: an existing alias redirects (302) and its click count increases; login works; dashboard renders; admin loads.
6. After HTTPS is confirmed stable: `SECURE_HSTS_SECONDS=3600`, then 31536000.
7. Login throttle uses the default per-process cache: with multiple workers each has its own counter. Configure a shared `CACHES` backend if strict limits matter.

**Monitor:** stderr for `ERROR django.request`, redirect 404 rate, login 429 rate, dashboard latency.

## 5. Rollback

All changes are code/config only (no data or schema change) → `git revert <commit>` per change, or redeploy `master@9eac668`. Notes:
- Reverting `91c35a2` reintroduces the hardcoded secrets — rotate regardless.
- If secure-cookie/SSL settings cause login or redirect-loop problems, set `SECURE_COOKIES=False` / `SECURE_SSL_REDIRECT=False` via env (no code rollback needed).
- If the throttle misbehaves behind a proxy (all users share `REMOTE_ADDR`, keyed per username so impact is per account), revert `ea8bc53`.

## 6. Needs your decision / approval

| Item | Evidence | Recommendation |
|---|---|---|
| **Django 5.0.1 → 5.2.17 LTS** (47 open CVEs, 5.0 EOL) | Trial venv: with `django-jazzmin` 2.6.0 the admin change form **crashes** (`length_is` filter removed in 5.1); with **jazzmin 3.0.1**: 31/31 tests pass, `check` clean, no migrations, **0 known vulns**. One 6.0 deprecation (URLField `assume_scheme`). | Approve: `Django==5.2.17`, `django-jazzmin==3.0.1`, `asgiref>=3.8.1`; also bump `django-debug-toolbar` (local only) |
| Exposed secrets | Present in 2 commits of public history | Rotate now; optionally purge history |
| What "Active URL" means (dashboard) | Currently "has ≥1 click"; model's `status`/activate dates are ignored by redirect | Product decision |
| HEAD requests → 405 | Link unfurlers/previews may fail | Allow HEAD → 302 without counting a click |
| Bot/prefetch clicks counted | Every GET counts | Decide on filtering (changes analytics meaning) |
| Brand contrast | White on `#8BC34A` ≈ 2.1:1, white on `#388E3C` ≈ 4.1:1 (AA needs 4.5:1 for body text) | Darker text on light green, or a darker primary shade — brand call |
| Google Charts from gstatic | Third-party script on authenticated page, no SRI | Self-host a chart lib or add CSP allowlist |
| Marketing claims not implemented | "Geographic data/referral sources" (landing, README), subscriptions, contact form (POSTs to `/` → 405), "Subscribe/Contact Us" buttons do nothing | Remove claims or build features |
| CI | None exists | Add GitHub Actions: tests + `pip-audit` + `check --deploy` |

## 7. Remaining risks

- Destination URLs are not checked against phishing/malware lists (main abuse vector for a public shortener).
- No signup throttling, email verification, or password reset.
- Deleting a link/user hard-deletes its click history (cascade).
- No backups or restore drill evidenced; production deployment details unknown.
- Composite index on `(url, created_at)` not added (schema change); revisit if dashboard queries slow with large click volumes.
- Pre-existing `staticfiles.W004` (`media/` in `STATICFILES_DIRS` doesn't exist).

## 8. Reproduce

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/Scripts/python.exe -r requirements/local.txt
SECRET_KEY=local-test .venv/Scripts/python.exe manage.py test
SECRET_KEY=x DB_PASSWORD=x DJANGO_ALLOWED_HOSTS=example.com .venv/Scripts/python.exe manage.production.py check --deploy
.venv/Scripts/python.exe -m pip install pip-audit && .venv/Scripts/python.exe -m pip_audit -r requirements/production.txt
```
