"""Render pages as real users (read-only GETs on the LOCAL demo DB) to static HTML for headless screenshots + audit.

Usage (from website/): python tools/ux-audit/snapshot.py <out_dir> <audit_js_path>
Assets resolve to the running dev server via <base href>. Output: <out_dir>/<name>.html + pages.txt
"""
import os, sys, re
sys.path.insert(0, os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
os.environ.setdefault("SECRET_KEY", "snapshot-only")
import django
django.setup()
from django.conf import settings
settings.ALLOWED_HOSTS = ["*"]
from django.test import Client
from django.contrib.auth.models import User

out_dir, audit_js = sys.argv[1], sys.argv[2]
os.makedirs(out_dir, exist_ok=True)
STATIC_URL_FILE = "file:///" + os.path.join(os.getcwd(), "static").replace("\\", "/")
audit_url = "file:///" + audit_js.replace("\\", "/")

demo, empty = User.objects.get(username="demo"), User.objects.get(username="empty-demo")
link = demo.url.order_by("created_at").first()
anon, full, blank = Client(), Client(), Client()
full.force_login(demo); blank.force_login(empty)

pages = [
    ("landing", anon, "/", {}), ("login", anon, "/auth/login/", {}), ("signup", anon, "/auth/signup/", {}),
    ("login-error", anon, "/auth/login/", {"post": {"username": "demo", "password": "wrong-password"}}),
    ("overview", full, "/urls/", {}), ("list", full, "/urls/list/", {}), ("create", full, "/urls/create/", {}),
    ("create-error", full, "/urls/create/", {"post": {"link": "not a url", "title": "", "custom_url": "admin", "description": ""}}),
    ("detail", full, f"/urls/detail/{link.pk}/", {}), ("update", full, f"/urls/update/{link.pk}/", {}),
    ("tracker", full, "/urls/tracker/list/", {}),
    ("overview-empty", blank, "/urls/", {}), ("list-empty", blank, "/urls/list/", {}), ("tracker-empty", blank, "/urls/tracker/list/", {}),
    ("404-shortlink", anon, "/no-such-alias-xyz/", {}),
]
lines = []
for name, client, path, opt in pages:
    r = client.post(path, opt["post"]) if "post" in opt else client.get(path)
    html = r.content.decode("utf-8", "replace")
    # Load CSS/JS/images straight from the project's static/ folder (no dev server needed).
    html = html.replace('"/static/', f'"{STATIC_URL_FILE}/').replace("'/static/", f"'{STATIC_URL_FILE}/")
    if "<head>" not in html:
        html = f'<html><head><meta charset="utf-8"></head><body>{html}</body></html>'
    html = re.sub(r"</body>", f'<script src="{audit_url}"></script></body>', html, count=1, flags=re.I) if "</body>" in html.lower() else html + f'<script src="{audit_url}"></script>'
    with open(os.path.join(out_dir, f"{name}.html"), "w", encoding="utf-8") as f:
        f.write(html)
    lines.append(f"{name}\t{r.status_code}\t{path}")
open(os.path.join(out_dir, "pages.txt"), "w").write("\n".join(lines))
print("\n".join(lines))
