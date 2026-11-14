#!/usr/bin/env bash
# Usage: shoot.sh <html_dir> <out_dir>
# >=768px: page rendered directly. 375/320px: page inside an iframe of exact width (headless window min width ~500px).
EDGE="/c/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"
IN="$1"; OUT="$2"; mkdir -p "$OUT" "$IN/_wrap"
edge() { timeout 90 "$EDGE" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1 --allow-file-access-from-files "$@" 2>/dev/null; }
for f in "$IN"/*.html; do
  page=$(basename "$f" .html)
  for spec in 1440x1800 768x2000 375x2400 320x2400; do
    w=${spec%x*}; h=${spec#*x}; png=$(cygpath -w "$OUT/$page@$w.png")
    if [ "$w" -ge 768 ]; then
      url="file:///$(cygpath -m "$f")"; win=$w
    else
      wrap="$IN/_wrap/$page@$w.html"
      cat > "$wrap" <<HTML
<!doctype html><html><body style="margin:0;background:#fff">
<iframe src="../$page.html" style="width:${w}px;height:${h}px;border:0;display:block"></iframe>
<pre id="__audit" style="display:none"></pre>
<script>addEventListener('message', e => { if (e.data && e.data.audit) document.getElementById('__audit').textContent = e.data.audit; });</script>
</body></html>
HTML
      url="file:///$(cygpath -m "$wrap")"; win=520
    fi
    edge --window-size=$win,$h --virtual-time-budget=6000 --screenshot="$png" "$url" >/dev/null
    if [ "$w" = 1440 ] || [ "$w" = 375 ]; then
      edge --window-size=$win,$h --virtual-time-budget=9000 --dump-dom "$url" \
        | sed -n 's/.*<pre id="__audit"[^>]*>\(.*\)<\/pre>.*/\1/p' | sed 's/&quot;/"/g; s/&amp;/\&/g; s/&lt;/</g; s/&gt;/>/g' > "$OUT/$page@$w.audit.json"
    fi
  done
done
echo "pngs: $(ls "$OUT"/*.png 2>/dev/null | wc -l)  audits(non-empty): $(find "$OUT" -name '*.audit.json' -size +0 | wc -l)"
