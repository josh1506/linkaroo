"""Read-only data fingerprint + integrity checks, for backup/restore validation and migration reconciliation.

    python manage.py data_fingerprint [--json] [--database default]

Prints per-table row counts and an order-independent SHA-256 content checksum, plus integrity counts. Run it on
the source and on the restored copy (or before/after a migration) and compare. Never writes: on PostgreSQL it runs
in a READ ONLY, REPEATABLE READ transaction (one consistent snapshot across all tables).
"""
import hashlib
import json

from django.core.management.base import BaseCommand
from django.db import connections, transaction

TABLES = ['auth_user', 'url_tracker_url', 'url_tracker_urltracker']

INTEGRITY = {
    # Clicks pointing at a missing link (FK should make this 0).
    'orphan_clicks': "SELECT count(*) FROM url_tracker_urltracker t LEFT JOIN url_tracker_url u ON u.id = t.url_id WHERE u.id IS NULL",
    # Denormalized url_owner drift (authorization no longer relies on it; relevant before any contract/drop).
    'click_owner_drift': "SELECT count(*) FROM url_tracker_urltracker t JOIN url_tracker_url u ON u.id = t.url_id "
                         "WHERE t.url_owner_id IS DISTINCT FROM u.owner_id",
    'links_without_owner': "SELECT count(*) FROM url_tracker_url WHERE owner_id IS NULL",
    'links_longer_than_200': "SELECT count(*) FROM url_tracker_url WHERE length(link) > 200",
    'aliases_null_or_empty': "SELECT count(*) FROM url_tracker_url WHERE custom_url IS NULL OR custom_url = ''",
}


class Command(BaseCommand):
    help = "Read-only row counts, content checksums and integrity checks (for backup/restore and migration reconciliation)."

    def add_arguments(self, parser):
        parser.add_argument('--database', default='default')
        parser.add_argument('--json', action='store_true', help='Machine-readable output for diffing.')

    def handle(self, *args, **opts):
        connection = connections[opts['database']]
        result = {'vendor': connection.vendor, 'tables': {}, 'integrity': {}}
        with transaction.atomic(using=opts['database']):
            with connection.cursor() as cursor:
                if connection.vendor == 'postgresql':
                    cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY")
                for table in TABLES:
                    result['tables'][table] = self._fingerprint(cursor, connection, table)
                for name, sql in INTEGRITY.items():
                    cursor.execute(sql)
                    result['integrity'][name] = cursor.fetchone()[0]
            transaction.set_rollback(True, using=opts['database'])  # belt and braces: nothing to commit
        if opts['json']:
            self.stdout.write(json.dumps(result, indent=2, sort_keys=True))
            return
        for table, info in result['tables'].items():
            self.stdout.write(f"{table:<26} rows={info['rows']:<10} sha256={info['sha256'][:16]}...")
        for name, value in result['integrity'].items():
            self.stdout.write(f"{name:<26} {value}")

    @staticmethod
    def _fingerprint(cursor, connection, table):
        qn = connection.ops.quote_name
        columns = [c.name for c in connection.introspection.get_table_description(cursor, table)]
        cursor.execute(f"SELECT {', '.join(qn(c) for c in sorted(columns))} FROM {qn(table)}")
        acc, rows = 0, 0
        while True:
            batch = cursor.fetchmany(5000)
            if not batch:
                break
            for row in batch:
                # Order-independent: sum of per-row hashes mod 2**256. Values are normalized via str().
                digest = hashlib.sha256('\x1f'.join('' if v is None else str(v) for v in row).encode()).digest()
                acc = (acc + int.from_bytes(digest, 'big')) % (1 << 256)
                rows += 1
        return {'rows': rows, 'sha256': f"{acc:064x}"}
