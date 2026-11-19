# UX audit + visual regression (local, no extra dependencies)

Renders page states as real users, screenshots them at true 1440 / 768 / 375 / 320 px viewports in headless
Microsoft Edge (phones via an exact-width iframe, because headless windows can't go below ~500 px), runs an
in-page accessibility/consistency audit, and pixel-diffs before vs after.

Prerequisites: the project venv, the **local** dev DB with demo users `demo` (has links + clicks) and
`empty-demo` (no links), and Microsoft Edge at the default path (override with `EDGE=...`). No dev server needed;
static files are loaded from `static/`. Google Charts loads from gstatic (network).

```bash
# from website/
.venv/Scripts/python.exe tools/ux-audit/snapshot.py <out>/html "$(cygpath -m "$PWD/tools/ux-audit/audit.js")"
bash tools/ux-audit/shoot.sh <out>/html <out>/shots    # PNGs + <page>@{1440,375}.audit.json
bash tools/ux-audit/diff.sh <before>/shots <after>/shots   # % of pixels changed per screenshot
```

The audit checks WCAG contrast (relative luminance), input labels, control names, target size, image alt text,
heading order/h1, landmarks, skip link, duplicate IDs, table captions, nav `aria-current`, zoom and horizontal
overflow, and inventories font sizes, families, radii, shadows and card paddings. It's a focused checker, **not a
replacement for axe-core or a screen-reader pass**.
