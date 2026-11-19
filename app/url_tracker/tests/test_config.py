import re
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class EnvExampleTests(SimpleTestCase):
    """Every environment variable the settings/app read must be documented in .env.example (deploy checklist input)."""

    def test_env_example_documents_every_variable(self):
        base = Path(settings.BASE_DIR)
        pattern = re.compile(r"""(?:os\.environ(?:\.get)?\(|os\.environ\[|env_bool\()['"]([A-Z][A-Z0-9_]+)['"]""")
        used = set()
        for path in list((base / "config").rglob("*.py")) + list((base / "app").rglob("*.py")):
            used |= set(pattern.findall(path.read_text(encoding="utf-8")))
        used.discard("DJANGO_SETTINGS_MODULE")
        documented = set(re.findall(r"^([A-Z][A-Z0-9_]+)=", (base / ".env.example").read_text(encoding="utf-8"), re.M))
        self.assertGreater(len(used), 10)  # guard: the scan must actually find the settings
        self.assertEqual(sorted(used - documented), [])
