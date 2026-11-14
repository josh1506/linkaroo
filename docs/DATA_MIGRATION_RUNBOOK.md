# Data migration runbook: Linkaroo (2026-11-14)

**Rule:** production data is irreplaceable. Nothing in this document has touched production. Applying anything below to production needs **separate, explicit authorization**. Destructive steps (C1) need their own additional authorization.

**Evidence base:** a throwaway PostgreSQL 17 container (`postgres:17-alpine`, 384 MB cap, localhost only, no volume) loaded with **synthetic** data: 2,000 users, 20,000 links, ~2,000,000 clicks over 365 days, skewed toward recent days and popular links. The app's real ORM queries were measured with `EXPLAIN (ANALYZE, BUFFERS)` (server-side time, which excludes Docker network overhead). Laptop-class hardware: treat durations as **relative**, not production SLAs.

## 1. Current schema and data shape

| Table | Key / constraints | Indexes | Size at 2M clicks (rehearsal) |
|---|---|---|---|
| `auth_user` | int PK | Django defaults | 0.6 MB |
| `url_tracker_url` | UUID PK; `custom_url` UNIQUE; `owner_id` FK → user (CASCADE, nullable) | unique + `_like` pattern index on `custom_url`, `owner_id` | 5.5 MB |
| `url_tracker_urltracker` (clicks) | UUID PK; `url_id` FK → url (CASCADE); `url_owner_id` FK → user (CASCADE, nullable, **denormalized**) | PK 76 MB, `url_id` 14 MB, `url_owner_id` 17 MB | **269 MB** (161 MB heap) |

**Sizing rule of thumb (measured):** each **1M clicks ≈ 135 MB** (heap + indexes). `pg_dump -Fc -Z6` ≈ **39 MB per 1M clicks**, about 5 s per 1M to dump. Restore with `-j 2` takes about 15 s per 1M. Clicks dominate everything else by about 50×. Write volume is one INSERT per recorded click (capped at 30/min per client per link since F5).

**Production volume: UNKNOWN.** Run the read-only `python manage.py data_fingerprint` (row counts) or `SELECT pg_total_relation_size(...)` with read-only credentials to size real backups and windows before scheduling anything.

## 2. Queries that touch the schema (measured, heaviest user: 10 links, ~75k clicks)

| # | Query (source) | Server time | Plan |
|---|---|---|---|
| Q1 | Redirect: `URL` by `custom_url` (`url_redirect_view`) | **0.14 ms** | Unique index; nothing to gain |
| Q2 | Dashboard: links + all-time `Count('tracker')` | 25 ms | Nested loop over `url_id` index, all user clicks |
| Q3 | Dashboard: clicks per link per day, last 7 days | 14 ms | `url_id` index, then date filter |
| Q4 | Click log page (`ORDER BY created_at DESC LIMIT 10`) | 35 ms | All user clicks, then top-N sort |
| Q5 | Click log paginator `COUNT(*)` | ~30 ms | as Q4 |
| Q6 | Link list page | 0.2 ms | `owner_id` index |
| — | INSERT click (redirect) | ~1–5 ms | PK + 2 FK index maintenance |

## 3. Candidate changes and decisions

### M1: composite index `urltracker (url_id, created_at)`: **REJECTED (measured)**
- Built `CONCURRENTLY` in rehearsal: 18.5 s, **+77 MB** (+38 MB per 1M clicks), plus extra write cost on every click.
- Planner kept using the `url_id` index for Q3/Q4: 14 → 13 ms and 35 → 32 ms (noise). Only the count used an index-only scan.
- **Lock evidence, useful for any future index:** a plain `CREATE INDEX` **blocked every click INSERT for 15.9 s** (only 7 inserts got through during the build). `CREATE INDEX CONCURRENTLY` let 927 inserts through (p50 5 ms, p99 150 ms, worst 3.5 s). **Never build an index on the click table without `CONCURRENTLY`** (in Django: `django.contrib.postgres.operations.AddIndexConcurrently` in a non-atomic migration).
- Revisit only if a single user's clicks reach the millions. The better lever then is query shape (keyset pagination on the click log, pre-aggregated daily counts), not this index.

### M2: widen `url.link` varchar(200) → varchar(2048): **IMPLEMENTED in code, rehearsed; production apply needs authorization**
- **Why:** a realistic 247-character UTM campaign URL is rejected today ("at most 200 characters"). Tests `test_create_accepts_long_campaign_link` and `test_create_rejects_link_over_2048`.
- **Migration:** `app/url_tracker/migrations/0004_widen_url_link.py`.
- **Schema impact:** `ALTER TABLE url_tracker_url ALTER COLUMN link TYPE varchar(2048)`. **Metadata-only** in PostgreSQL: verified **no table rewrite** (same `pg_relation_filenode`). **Backfill volume: 0 rows.**
- **Locks:** needs `ACCESS EXCLUSIVE` on `url_tracker_url` (the redirect table) for milliseconds. The hazard is the lock queue: measured behind a 6 s transaction, **every redirect stalled 5.5 s**. The migration therefore sets `SET LOCAL lock_timeout = '2s'`. Measured: it fails fast with `canceling statement due to lock timeout`, leaving the column unchanged, and a **plain re-run succeeds** once the blocker ends. With the timeout, worst redirect stall was 2 s.
- **Compatibility (expand-only):** old app code + new schema works (old form validates ≤200; longer rows still display). New code + old schema can't happen if migrate runs before the code switch (standard order).
- **Rollback, proven in rehearsal:** after any link longer than 200 exists, migrating backwards fails (`value too long for type character varying(200)`). The migration's reverse step now **refuses with an explanatory error** before attempting it. It's atomic, so the column and migration state stay intact. **Roll back by redeploying the previous application code and keeping 0004 applied.** Backwards migration is only possible while no long links exist.
- **SQLite (local/staging):** Django rebuilds the table, which is fine at local sizes.

### C1: retire the denormalized `urltracker.url_owner`: **PLAN ONLY (destructive, not authorized)**
- Since security fix F7, authorization uses `url__owner`; `url_owner` is written on every click but only read by the admin.
- **Drift evidence:** `bulk_create` and raw SQL bypass `URLTracker.save()`, leaving `url_owner` NULL. The local demo data has **400 / 400** drifted rows. The `data_fingerprint` check `click_owner_drift` measures this.
- **Expand/contract sequence** (each step a separate release):
  1. *Stop depending:* nothing in the app reads it (done).
  2. *Stop writing:* remove the `save()` override. This needs a nullable field with a default (already nullable). Old code still writes it, which is harmless.
  3. *Observe* one release cycle. Confirm no reader via code search, logs and admin.
  4. *Contract (destructive):* `RemoveField`. That's a metadata-only `DROP COLUMN` in PostgreSQL, but it also **drops the 17 MB index and the FK** and is **irreversible for data**. A down migration recreates an empty column, not the data. Requires a verified backup (section 4) taken right before, **plus explicit authorization**.
- Alternative if the column must stay: a batched backfill (`UPDATE … SET url_owner_id = u.owner_id FROM url_tracker_url u WHERE … AND id IN (next 10,000 ids)`). Commit per batch, checkpoint on last id, safe to re-run. **Volume = `click_owner_drift`** (expected ~0 in production because redirects use `save()`). Not needed for correctness any more.

### Not proposed now (product decisions first)
- Soft-delete or retention for clicks (today: link or user deletion **hard-deletes** all click history via CASCADE).
- Case-insensitive alias uniqueness (would need a duplicate audit first; the `data_fingerprint` integrity section is where that check would go).

## 4. Backup and restore validation (rehearsed)

| Step | Command (run against the **target** environment with its own credentials) | Rehearsal result |
|---|---|---|
| 1. Fingerprint source (read-only) | `python manage.py data_fingerprint --json > before.json` | 46 s for 2M clicks |
| 2. Backup | `pg_dump -Fc -Z 6 -d <db> -f linkaroo-<date>.dump` | **10 s, 77 MB** |
| 3. Dump readable | `pg_restore -l linkaroo-<date>.dump` | 65 data/index/constraint entries |
| 4. Restore into a **new** database (never over the source) | `createdb <db>_restore_check && pg_restore -d <db>_restore_check --exit-on-error --no-owner -j 2 <dump>` | **29 s, exit 0** |
| 5. Fingerprint restore and compare | `DB_NAME=<db>_restore_check python manage.py data_fingerprint --json > after.json` then diff | **All tables and integrity counts MATCH** (2,001,426 clicks) |
| 6. Negative control | change 1 row in the restore copy and re-fingerprint | **Detected** (checksum mismatch with equal row counts) |

`data_fingerprint` (`app/url_tracker/management/commands/`) never writes: it runs in a `READ ONLY, REPEATABLE READ` transaction on PostgreSQL (one consistent snapshot) and rolls back. Covered by `tests/test_data_fingerprint.py`.
**RPO/RTO:** unknown until production backup frequency is known. Measured restore throughput (~15 s per 1M clicks on this hardware) gives a first RTO estimate once volume is known.

## 5. Production runbook for M2 (requires authorization; not executed)

1. **Pre-checks (read-only):** `python manage.py showmigrations url_tracker` (expect 0001–0003 applied). Run `data_fingerprint --json > before.json`. Check for long transactions: `SELECT pid, now() - xact_start, state, left(query, 60) FROM pg_stat_activity WHERE xact_start < now() - interval '5 seconds';`.
2. **Backup** and **verify restore** per section 4, in a scratch database. Abort if anything differs.
3. Low-traffic window. Deploy code with migration 0004. Run `python manage.py migrate url_tracker 0004`.
   - On `canceling statement due to lock timeout`: nothing changed. Wait for or terminate the blocking session (investigate first; don't kill blindly), then re-run.
4. **Verify:** `showmigrations` shows 0004. `SELECT character_maximum_length FROM information_schema.columns WHERE table_name='url_tracker_url' AND column_name='link'` = 2048. Run `data_fingerprint --json > after.json`: row counts and all checksums except `url_tracker_url` (only if links were edited) must match `before.json`, and integrity counts must be unchanged. Smoke test: an existing short link redirects (302), a 247-char link can be created, the dashboard loads.
5. **Abort/rollback:** before step 3, nothing to do. After step 3, redeploy previous code and **leave 0004 applied** (section 3, M2). Restore from backup only for data corruption, which this migration can't cause (no data is rewritten).

## 6. Not done / limits
- No production access of any kind. Production size, PostgreSQL version and backup tooling are unknown.
- Rehearsal used synthetic data and a 384 MB container: lock behaviour is representative, durations aren't.
- Rehearsal artifacts (container, dump) were deleted afterwards. Re-create them from the commands above.
