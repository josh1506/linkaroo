# Threat Model — Linkaroo / whole application

- **Date:** 2026-11-14 · **Code:** branch `upgrade/upg-001` (after UPG-001 stages 0–6) · **Standard:** OWASP ASVS **5.0.0** (IDs verified against `OWASP/ASVS@v5.0.0`).
- **Method:** source review + local probes on a throwaway in-memory test DB via Django's test client. No production, no network scanning, no real data. Secret values are never reproduced here.
- **Status:** F1–F10 **remediated locally** (see *Remediation status*). F11 and F12 are owner/operational items. Regression tests: `app/url_tracker/tests/test_security.py` (each finding first reproduced as an `@expectedFailure` test).

## Context

### Assets and classification
| Asset | Where | Class |
|---|---|---|
| Short-link alias → destination mapping | `url_tracker_url` (`custom_url`, `link`) | PUBLIC (resolvable by anyone); **integrity-critical** — retargeting = phishing via a trusted link |
| Link title / description | `url_tracker_url` | CONFIDENTIAL to owner |
| Click events (timestamp, link, owner) | `url_tracker_urltracker` | CONFIDENTIAL to owner. **No IP, user agent, referrer or geo stored** (good minimization) |
| Accounts: username, first/last name, email | `auth_user` | CONFIDENTIAL (personal data) |
| Password hashes | `auth_user.password` (PBKDF2-SHA256, Django default) | RESTRICTED |
| Sessions | `django_session` + `sessionid` cookie | RESTRICTED |
| `SECRET_KEY`, DB password | env (`.env`, git-ignored) — **old values remain in public git history** | RESTRICTED |
| Login-throttle counters (IP + username) | process memory (LocMem cache), 15-min TTL | INTERNAL, transient |
| Error logs (path, status, traceback) | stderr | INTERNAL; contains aliases/paths, no bodies/cookies |

### Actors and roles
Anonymous visitor · authenticated user (owner of their links) · staff/superuser (Django admin, all data) · automated attacker (bots, credential stuffers, link farmers) · compromised dependency/CDN. **Tenancy:** single database, per-user ownership via `URL.owner`; no organizations/teams.

### Entrypoints and trust boundaries
```
Internet ──► [B1 public]   GET /<alias>/                 anonymous, writes a click row, 302 to user-supplied URL
         ──► [B1 public]   GET / (landing), /auth/login|signup/, POST login/signup
         ──► [B2 owner]    /urls/... (overview, list, create, detail/update/delete <uuid>, tracker list)
         ──► [B3 admin]    /admin/ (Jazzmin) — staff only, full read/write on all users and links
Browser  ──► [B4 3rd-party] cdn.jsdelivr.net (Bootstrap, SRI pinned), www.gstatic.com (Google Charts, no SRI) on the owner dashboard
App      ──► [B5 data]     SQLite (local/staging) / PostgreSQL (production, credentials from env)
```

## Controls verified (passing regression tests)
| Control | ASVS | Evidence |
|---|---|---|
| Owner-scoped read/update/delete → 404 for other users and unknown IDs | 8.2.2 | `ObjectAuthorizationTests.test_wrong_owner_gets_404_on_read_write_delete` |
| Login required on all owner endpoints | 8.2.1 | `test_anonymous_redirected_to_login_for_every_owner_endpoint` |
| Analytics scoped to owner | 8.2.2 | `test_wrong_owner_sees_no_analytics` |
| No mass assignment of `owner` / `is_staff` | 8.2.3 | `test_owner_field_not_mass_assignable`, `test_signup_cannot_grant_staff` |
| Admin is staff-only | 8.2.1 | `test_non_staff_cannot_reach_admin`, `test_admin.py` |
| CSRF on every state-changing POST; redirect endpoint GET-only | 3.3.2 | `CsrfAndMethodTests` |
| `javascript:` / `data:` / `vbscript:` / `file:` destinations rejected | 2.2.1 | `test_script_and_data_schemes_rejected` |
| Site login lockout (5 failures / 15 min, IP+username, 429) | 6.3.1 | `test_site_login_locks_after_5_failures` |
| Failed login doesn't reveal account existence | 6.3.8 | `test_failed_login_message_does_not_reveal_whether_user_exists` |
| Cookies `Secure` + `HttpOnly` + `SameSite=Lax`; nosniff; `X-Frame-Options: DENY`; COOP | 3.3.1, 3.3.2, 3.3.4 | settings dump (production settings) |
| Template autoescaping; no `|safe`, `mark_safe`, raw SQL, `csrf_exempt` | 1.x | `grep` of `app/` and `config/` — none found |
| Secrets read from env, none hardcoded in tree; `DEBUG` parsed as boolean | 13.x | UPG-001 change report |

## Threat register (open)
| ID | Threat / abuse case | Boundary | Likelihood | Impact | Evidence (local probe) | Gap → proposed control | ASVS | Test |
|---|---|---|---|---|---|---|---|---|
| **F1** | Brute force / credential stuffing on **staff** accounts via `/admin/login/` | B3 | High (default path, well-known) | **High** — staff can read all PII and retarget any link | 10 failures then correct password → logged in | Throttle lives only in the site login view. Move counting into the auth form and set `admin.site.login_form` | 6.3.1, 8.4.2 | `test_admin_login_locks_after_5_failures` |
| **F2** | Password spraying: one client, many usernames | B1 | High | Medium–High (account takeover) | 60 failures across 60 usernames, 0 × 429 | Add per-client cap (e.g. 30 failures / 15 min) next to the per-account key | 6.3.1, 2.4.1 | `test_password_spraying_capped_per_client` |
| **F3** | Attacker locks out any user when deployed behind a reverse proxy (all clients share `REMOTE_ADDR`) | B1 | Medium (deployment-dependent; unknown) | Medium (targeted DoS) | 5 failures from the shared IP → victim gets 429 | Resolve client IP from `X-Forwarded-For` **only** for a configured `TRUSTED_PROXY_COUNT` (default 0 = ignore header, so it can't be spoofed) | 6.1.1 | `test_lockout_of_one_client_does_not_lock_other_clients_behind_proxy` |
| **F4** | Mass account creation (phishing-link farms, spam) | B1 | High | Medium (abuse, reputation, domain blocklisting) | 20 sign-ups from one IP accepted | Per-client sign-up limit (e.g. 5 / hour) | 2.4.1 | `test_signup_rate_limited_per_client` |
| **F5** | Anonymous click inflation / DB write amplification | B1→B5 | High | Medium (analytics integrity, storage growth/DoS) | 500 GETs from one IP → 500 rows | **Product decision needed.** Option: still redirect, but record at most N clicks per client+link per window | 2.4.1, 2.3.2 | to add with chosen policy |
| **F6** | Redirect loops via links pointing at the shortener's own domain; each hop writes a click | B1→B5 | Medium | Low–Medium (amplification) | 2 links pointing at each other: 20 hops, 20 rows | Reject destinations whose host is in `ALLOWED_HOSTS` (non-wildcard) or the request host | 2.2.1 | `test_destination_on_own_domain_rejected` |
| **F7** | Previous owner keeps seeing click history after a link is reassigned (stale denormalized `url_owner`) | B2 | Low (needs admin reassignment) | Low–Medium (confidentiality) | Reassigned link's clicks still listed for old owner | Filter the click list by `url__owner` (authoritative) instead of `url_owner` | 8.2.2, 8.3.2 | `test_previous_owner_loses_click_history_after_reassignment` |
| **F8** | `ftps://` destinations accepted but Django refuses to redirect (400) → dead links; FTP is legacy | B1 | Low | Low | ftps link saved; redirect → 400 `DisallowedRedirect` | Accept only `http`/`https` for new or changed links; existing links keep working | 2.2.1 | `test_only_http_https_destinations_accepted` |
| **F9** | Generated aliases from a non-cryptographic PRNG (Mersenne Twister) | B1 | Low | Low (aliases are public, but users may treat them as unlisted) | `random.choice` in `generate_unique_link` | `secrets.choice`; same 12-char format, no data change | 11.5.1 | `test_generated_alias_uses_csprng` |
| **F10** | No Content-Security-Policy; Google Charts loaded without SRI on an authenticated page | B4 | Low–Medium | Medium if a third party is compromised | No CSP header; gstatic `<script>` without `integrity` | CSP with nonce (needs moving the inline `<script>` to static or a nonce). Self-host the chart library or document the SRI exception | 3.4.3, 3.6.1 | header test once implemented |
| **F11** | Previously committed `SECRET_KEY` / DB password reused in a live deployment | B5 | Unknown | **Critical if live** (session forgery / DB access) | Present in 2 commits of public history | **Owner action:** rotate both; consider purging history | 13.x | n/a (operational) |
| **F12** | Malicious destinations (phishing/malware) behind a trusted short domain | B1 | High for any public shortener | High (reputation, blocklisting) | Any http(s) destination accepted | **Documented exception to ASVS 3.7.2/3.7.3** (redirecting off-site is the product). Compensating: scheme allowlist (done), sign-up limits (F4), abuse reporting + disable-link procedure, optional reputation check (external service — needs approval) | 3.7.2, 3.7.3 | — |

## Remediation status (2026-11-14, branch `upgrade/upg-001`, not deployed)
| ID | Fix | Commit | Re-probe after fix | Config it depends on |
|---|---|---|---|---|
| F1 | Lockout moved into a form mixin; `admin.site.login_form` uses it | `57cd461` | 10 failures → right password rejected | — |
| F2 | Per-client cap of 30 failures / 15 min, plus 5 per account | `57cd461` | 60 sprayed attempts → 30 × 429 | — |
| F3 | Client IP from `X-Forwarded-For` only for `TRUSTED_PROXY_COUNT` proxies | `57cd461` | Victim behind a proxy logs in (302) | **Set `TRUSTED_PROXY_COUNT`** to the real proxy count when deployed behind one. With the default 0 and a proxy, the gap remains. |
| F4 | `SIGNUPS_PER_CLIENT_PER_HOUR` (default 5), 429 | `a44e107` | 20 attempts → 5 accounts | — |
| F5 | Always redirect; record at most `CLICK_RECORD_LIMIT_PER_MINUTE` (default 30) clicks per client per link | `a44e107` | 500 GETs → 30 rows | Clients behind a shared NAT are under-counted beyond 30/min/link. 0 disables the cap. |
| F6 | New/changed destinations whose host matches `ALLOWED_HOSTS` are rejected | `3b5aff1` | Loop links rejected | **Needs real hostnames in `ALLOWED_HOSTS`** (true for staging/production). With `*` (local) there's no check. |
| F7 | Click log filters `url__owner` | `a44e107` | Previous owner sees nothing | — |
| F8 | New/changed destinations: `http`/`https` only; unchanged legacy links stay editable and keep redirecting | `3b5aff1` | ftps rejected | — |
| F9 | `secrets.choice` for generated aliases (same format) | `3b5aff1` | — | — |
| F10 | CSP middleware: strict app policy, separate admin policy; dashboard inline JS → `json_script` + static file | `1ef82a5` | Chrome: charts render; injected inline script blocked; admin works | `CSP_REPORT_ONLY=True` for staged rollout. Admin keeps `'unsafe-inline'` scripts (Jazzmin). |

All limits use the default per-process LocMem cache. Configure a shared `CACHES` backend in production so limits hold across workers and survive eviction.

## Privacy and data handling
- **Minimized:** clicks store no IP, user agent, referrer or geo. The landing page and README claim geographic/referrer analytics that **do not exist**. Don't add raw IP collection without a privacy review.
- **Transient:** throttle keys hold IP and username in process memory for at most 15 minutes. They are not persisted or logged.
- **Logs:** errors only (5xx) by default. Paths may contain aliases. No request bodies, cookies or credentials.
- **Gaps:** no self-service account deletion or export, no retention limit on clicks, and deleting a link or user hard-deletes its history. If users are in the Philippines, assess Data Privacy Act data-subject rights (access, erasure). This is an assessment prompt, not a compliance claim.
- **Admin:** staff see all users' emails and names. There's no MFA and no extra layer on `/admin/` (ASVS 8.4.2).

## Residual risks and sign-off
- Rate limits use per-process LocMem: limits are per worker, and counters can be evicted (300-entry default cull). Use a shared cache (database or Redis) in production for reliable limits.
- No password reset or email verification, so users who forget their password are locked out and email addresses are unverified.
- No backup/restore evidence. Production topology (proxy/TLS) is unknown, which is why F3's fix is opt-in configuration.
- Sign-off: **pending project owner**: F5 default (30/min) is a product trade-off, F11 rotation is outstanding, F12 abuse handling needs an owner, and deployment must set `TRUSTED_PROXY_COUNT` / real `ALLOWED_HOSTS` / shared `CACHES`.

## Probing constraints followed
Local throwaway DB and test client only. No production or network targets, no brute force against real hosts, no data dumps. Secret values are not reproduced. ASVS IDs come from the official v5.0.0 sources.
