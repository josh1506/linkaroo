# Changelog

## Unreleased: UPG-001 modernization (branch `upgrade/upg-001`, not yet deployed)

### What users will notice
- **Security:** you can no longer view, edit or delete other people's links. Logins lock for 15 minutes after 5 failed attempts (admin too).
- **Sign-up:** limited to 5 new accounts per network per hour.
- **Links:** destinations up to 2048 characters (long campaign/UTM links now work). Only `http://` and `https://` destinations for new or changed links. A destination typed without a scheme becomes `https://`. Links can't point back at this site.
- **Custom aliases:** letters, numbers, `-` and `_`, max 64 characters; route names like `admin` are reserved. Existing aliases keep working unchanged. Leaving the alias blank while editing keeps the current one (it used to generate a new one and break shared links).
- **Analytics:** daily charts use local (Manila) days, which fixes clicks missing from "today" between midnight and 8 am. Each visitor's clicks on one link are recorded at most 30 times per minute (the redirect always works).
- **Dashboard & pages:** helpful empty states instead of chart errors, a branded "Link not found" page, readable contrast, keyboard skip link and focus rings, layouts that work on phones, and a much faster dashboard.
- **Sessions:** everyone will be logged out once when the site's secret key is rotated.

### Under the hood
- Django 5.0.1 → **5.2.19 LTS** (5.0 was end-of-life with 47 known CVEs); dependencies hash-locked; Python 3.12 pinned.
- Secrets read from the environment; correct `DEBUG` handling; secure cookies, HTTPS redirect, Content-Security-Policy; errors logged to stderr.
- Migration `0004_widen_url_link` (metadata-only on PostgreSQL; see `docs/DATA_MIGRATION_RUNBOOK.md`).
- CI workflow, 79 automated tests, `data_fingerprint` command for backup/restore verification.

See `docs/RELEASE_CHECKLIST.md` for release status (currently **no-go** pending the environment and ownership items listed there).
