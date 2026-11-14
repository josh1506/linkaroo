# Widen URL.link from varchar(200) to varchar(2048) so long campaign/UTM links can be saved.
#
# Rehearsed on PostgreSQL 17 with 20k links / 2M clicks (docs/DATA_MIGRATION_RUNBOOK.md):
# - Forward: metadata-only ALTER (no table rewrite, no backfill); instant on an idle table.
# - It needs an ACCESS EXCLUSIVE lock; behind a long transaction every redirect queues behind it, so a short
#   lock_timeout makes it fail fast instead (re-run the migration to retry).
# - Backward (narrowing) fails once any link is longer than 200 characters. Roll back the application code and
#   keep this migration applied instead; the old code works with the wider column.
from django.db import migrations, models
from django.db.models.functions import Length

LOCK_TIMEOUT = '2s'


def set_lock_timeout(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(f"SET LOCAL lock_timeout = '{LOCK_TIMEOUT}'")


def refuse_unsafe_narrowing(apps, schema_editor):
    URL = apps.get_model('url_tracker', 'URL')
    too_long = URL.objects.annotate(n=Length('link')).filter(n__gt=200).count()
    if too_long:
        raise RuntimeError(
            f"{too_long} link(s) are longer than 200 characters; narrowing url_tracker_url.link would fail or lose data. "
            "Keep this migration applied and roll back the application code instead."
        )
    set_lock_timeout(apps, schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ('url_tracker', '0003_urltracker_url_owner'),
    ]

    operations = [
        migrations.RunPython(set_lock_timeout, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='url',
            name='link',
            field=models.URLField(max_length=2048, verbose_name='Link'),
        ),
        # Reverse runs first when migrating backwards: refuse before narrowing.
        migrations.RunPython(migrations.RunPython.noop, refuse_unsafe_narrowing),
    ]
