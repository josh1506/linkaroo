// UX/a11y audit run inside a rendered page (headless Edge). Writes JSON into <pre id="__audit"> for --dump-dom.
(function () {
  function run() {
    const out = { url: document.title, viewport: innerWidth, issues: {}, inventory: {} };
    const add = (k, v) => { (out.issues[k] = out.issues[k] || []).push(v); };
    const visible = (el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
    const short = (el) => (el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : ''));
    const text = (el) => (el.innerText || el.value || '').trim().replace(/\s+/g, ' ').slice(0, 40);

    // --- contrast (WCAG 2.x relative luminance) ---
    const parse = (c) => { const m = c.match(/rgba?\(([^)]+)\)/); if (!m) return null; const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number); return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 }; };
    const lum = ({ r, g, b }) => { const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
    const blend = (top, bottom) => ({ r: top.r * top.a + bottom.r * (1 - top.a), g: top.g * top.a + bottom.g * (1 - top.a), b: top.b * top.a + bottom.b * (1 - top.a), a: 1 });
    const bgOf = (el) => { const stack = []; for (let n = el; n; n = n.parentElement) { const s = getComputedStyle(n); if (s.backgroundImage !== 'none' && !s.backgroundImage.includes('gradient')) return null; const c = parse(s.backgroundColor); if (c && c.a > 0) { stack.push(c); if (c.a >= 1) break; } } let bg = { r: 255, g: 255, b: 255, a: 1 }; for (let i = stack.length - 1; i >= 0; i--) bg = blend(stack[i], bg); return bg; };
    const seen = new Set();
    for (const el of document.querySelectorAll('body *')) {
      if (!visible(el) || ['SCRIPT', 'STYLE', 'svg', 'path', 'IMG'].includes(el.tagName) || el.closest('svg')) continue;
      const own = [...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim());
      if (!own) continue;
      const s = getComputedStyle(el); const fg = parse(s.color); const bg = bgOf(el); if (!fg || !bg) continue;
      const fgB = blend(fg, bg); const L1 = lum(fgB), L2 = lum(bg); const ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
      const size = parseFloat(s.fontSize); const bold = parseInt(s.fontWeight, 10) >= 700; const large = size >= 24 || (bold && size >= 18.66);
      const need = large ? 3 : 4.5;
      if (ratio < need) { const key = `${s.color}|${bgOf(el) && JSON.stringify(bg)}|${size}`; if (!seen.has(key)) { seen.add(key); add('contrast', `${ratio.toFixed(2)}:1 (needs ${need}) ${size}px "${text(el)}" ${short(el)} fg=${s.color}`); } }
    }

    // --- names / labels ---
    for (const el of document.querySelectorAll('input:not([type=hidden]), select, textarea')) {
      const labelled = (el.id && document.querySelector(`label[for="${el.id}"]`)) || el.closest('label') || el.getAttribute('aria-label') || el.getAttribute('aria-labelledby');
      if (!labelled) add('input-without-label', `${short(el)} placeholder="${el.placeholder || ''}"`);
      if (el.getAttribute('aria-invalid') === null && el.closest('form') && el.closest('form').querySelector('.errorlist, .alert-danger')) {
        const errs = el.parentElement && el.parentElement.querySelector('.errorlist');
        if (errs && !el.getAttribute('aria-describedby')) add('error-not-associated', `${short(el)} has an adjacent error list but no aria-describedby/aria-invalid`);
      }
    }
    for (const el of document.querySelectorAll('a[href], button')) {
      if (!visible(el)) continue;
      const name = (el.innerText || '').trim() || el.getAttribute('aria-label') || el.getAttribute('title') || (el.querySelector('img[alt]') && el.querySelector('img[alt]').alt);
      if (!name) add('control-without-name', short(el));
      const r = el.getBoundingClientRect(); if ((r.width < 24 || r.height < 24) && getComputedStyle(el).display !== 'inline') add('target-under-24px', `${Math.round(r.width)}x${Math.round(r.height)} "${text(el)}" ${short(el)}`);
      if (el.tagName === 'A' && /^>\s*$/.test(el.innerText || '')) add('ambiguous-link-text', short(el));
      if (el.tagName === 'BUTTON' && !el.closest('form') && !el.dataset.bsToggle && !el.dataset.bsDismiss && !el.getAttribute('onclick')) add('button-does-nothing', `"${text(el)}" ${short(el)}`);
    }
    for (const img of document.querySelectorAll('img')) {
      if (!img.hasAttribute('alt')) add('img-without-alt', img.getAttribute('src'));
      else if (/^(logo|background|image)$/i.test(img.alt)) add('img-alt-not-descriptive', `alt="${img.alt}" ${img.getAttribute('src')}`);
      if (img.getAttribute('src') === '') add('img-empty-src', short(img));
    }

    // --- structure ---
    const hs = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].filter(visible).map((h) => +h.tagName[1]);
    out.inventory.headings = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].filter(visible).map((h) => `${h.tagName}:${text(h)}`);
    if (!hs.includes(1)) add('no-h1', 'page has no visible h1');
    if (hs.filter((x) => x === 1).length > 1) add('multiple-h1', String(hs.filter((x) => x === 1).length));
    for (let i = 1; i < hs.length; i++) if (hs[i] > hs[i - 1] + 1) add('heading-level-skip', `h${hs[i - 1]} -> h${hs[i]}`);
    if (!document.querySelector('main, [role=main]')) add('no-main-landmark', '');
    if (!document.querySelector('nav, [role=navigation]') && document.querySelectorAll('a[href]').length > 3) add('no-nav-landmark', '');
    if (!document.querySelector('a[href^="#"][class*=skip], a.visually-hidden-focusable, a.skip-link')) add('no-skip-link', '');
    if (!document.documentElement.lang) add('no-lang', '');
    const ids = {}; for (const el of document.querySelectorAll('[id]')) ids[el.id] = (ids[el.id] || 0) + 1;
    for (const [k, v] of Object.entries(ids)) if (v > 1) add('duplicate-id', `${k} x${v}`);
    for (const t of document.querySelectorAll('table')) if (!t.querySelector('caption') && !t.getAttribute('aria-label')) add('table-without-caption', short(t));
    for (const nav of document.querySelectorAll('[aria-current]')) if (nav.getAttribute('aria-current') === 'page' && !nav.classList.contains('active') && nav.tagName === 'LI') add('aria-current-misused', short(nav));
    const navLinks = [...document.querySelectorAll('aside a, header nav a')]; if (navLinks.length && !navLinks.some((a) => a.getAttribute('aria-current'))) add('nav-no-current-page', `${navLinks.length} nav links, none marked aria-current`);
    if (/user-scalable=no|maximum-scale=1/.test((document.querySelector('meta[name=viewport]') || {}).content || '')) add('zoom-disabled', '');

    // --- overflow / responsive ---
    const sw = Math.max(document.documentElement.scrollWidth, document.body.scrollWidth); if (sw > innerWidth + 1) add('horizontal-overflow', `${sw}px > ${innerWidth}px`);

    // --- inventory: type + spacing scale ---
    const sizes = {}, families = {}, weights = {}, radii = {}, shadows = {}, pads = {};
    for (const el of document.querySelectorAll('body *')) {
      if (!visible(el) || el.closest('svg')) continue; const s = getComputedStyle(el);
      if ([...el.childNodes].some((n) => n.nodeType === 3 && n.textContent.trim())) { sizes[s.fontSize] = (sizes[s.fontSize] || 0) + 1; families[s.fontFamily.split(',')[0]] = (families[s.fontFamily.split(',')[0]] || 0) + 1; weights[s.fontWeight] = (weights[s.fontWeight] || 0) + 1; }
      if (s.borderTopLeftRadius !== '0px') radii[s.borderTopLeftRadius] = (radii[s.borderTopLeftRadius] || 0) + 1;
      if (s.boxShadow !== 'none') shadows[s.boxShadow.slice(0, 40)] = (shadows[s.boxShadow.slice(0, 40)] || 0) + 1;
      if (/card|shadow|rounded/.test(el.className)) pads[s.padding] = (pads[s.padding] || 0) + 1;
    }
    out.inventory.fontSizes = sizes; out.inventory.fontFamilies = families; out.inventory.fontWeights = weights; out.inventory.radii = radii; out.inventory.shadows = Object.keys(shadows).length; out.inventory.cardPaddings = pads;
    out.inventory.loading = { chartsContainers: document.querySelectorAll('[id*=chart], #chart_div').length, chartsWithPlaceholderText: [...document.querySelectorAll('[id*=chart], #chart_div')].filter((c) => c.textContent.trim()).length };
    out.inventory.emptyTableBodies = [...document.querySelectorAll('tbody')].filter((b) => !b.querySelector('tr')).length;

    const json = JSON.stringify(out);
    if (window.parent !== window) { window.parent.postMessage({ audit: json }, '*'); return; }
    const pre = document.createElement('pre'); pre.id = '__audit'; pre.style.display = 'none'; pre.textContent = json; document.body.appendChild(pre);
  }
  // let charts/fonts settle
  window.addEventListener('load', () => setTimeout(run, 2500));
})();
