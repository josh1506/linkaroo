#!/usr/bin/env bash
# Pixel-diff two screenshot folders with headless Edge (canvas compare; no image libraries needed).
# Usage: diff.sh <before_dir> <after_dir> [threshold=32]  -> prints % of pixels whose max channel delta > threshold
EDGE="${EDGE:-/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe}"
A="$1"; B="$2"; T="${3:-32}"; HTML="$B/_diff.html"
{
  echo '<!doctype html><meta charset="utf-8"><pre id="out"></pre><script>'
  echo "const T=$T, pairs=["
  for f in "$A"/*.png; do n=$(basename "$f"); [ -f "$B/$n" ] && echo "['$n','file:///$(cygpath -m "$f")','file:///$(cygpath -m "$B/$n")'],"; done
  cat <<'JS'
];
const load = (src) => new Promise((ok, ko) => { const i = new Image(); i.onload = () => ok(i); i.onerror = ko; i.src = src; });
(async () => { const rows = [];
  for (const [name, a, b] of pairs) {
    const [ia, ib] = await Promise.all([load(a), load(b)]); const w = Math.max(ia.width, ib.width), h = Math.max(ia.height, ib.height);
    const px = (img) => { const c = document.createElement('canvas'); c.width = w; c.height = h; const x = c.getContext('2d'); x.fillStyle = '#f0f'; x.fillRect(0, 0, w, h); x.drawImage(img, 0, 0); return x.getImageData(0, 0, w, h).data; };
    const da = px(ia), db = px(ib); let changed = 0;
    for (let i = 0; i < da.length; i += 4) if (Math.max(Math.abs(da[i] - db[i]), Math.abs(da[i+1] - db[i+1]), Math.abs(da[i+2] - db[i+2])) > T) changed++;
    rows.push(`${(100 * changed / (w * h)).toFixed(2).padStart(6)}%  ${name}`);
  }
  document.getElementById('out').textContent = 'DIFF\n' + rows.sort().reverse().join('\n');
})().catch(e => document.getElementById('out').textContent = 'ERR ' + e);
JS
  echo '</script>'
} > "$HTML"
timeout 300 "$EDGE" --headless=new --disable-gpu --allow-file-access-from-files --virtual-time-budget=120000 --dump-dom "file:///$(cygpath -m "$HTML")" 2>/dev/null \
  | sed -n '/<pre id="out">/,/<\/pre>/p' | sed 's/<[^>]*>//g'
