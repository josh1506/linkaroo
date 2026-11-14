# UX audit and refinement plan: Linkaroo (2026-11-14)

**Scope:** `/premium-ux`. Keep brand identity, information architecture, copy, layouts and features. Refinements only.
**Method:** 15 page states (landing, auth, form errors, dashboard/list/tracker with data **and empty**, detail, update, public 404) rendered as real users and captured in headless Edge at **1440 / 768 / 375 / 320 px** (true viewports; phones via exact-width iframe). An in-page audit script measured WCAG contrast, names/labels, headings, landmarks, IDs, target size, overflow, and inventoried the type and spacing scale. Reproduce with `tools/ux-audit/` (see its README).
**Not run:** axe-core (injecting a third-party script into the page was blocked by the session's permission policy), real screen readers, real devices.

## What's already solid
- One type family (system-ui) and a compact scale (16/20/24/32 px). Consistent 16 px card radius and a single shadow.
- Labels are associated with every input. Django 5.2 already sets `aria-invalid` and `aria-describedby` on fields with errors.
- No horizontal overflow at 320/768 (fixed in UPG-001). Zoom allowed. Visible keyboard focus rings.
- **Motion:** the app has no custom animation. The only motion is Bootstrap's modal/button transitions, which respect `prefers-reduced-motion`. Nothing to remove.

## Findings (by user friction)

| # | Finding | Evidence | Severity |
|---|---|---|---|
| U1 | **Empty dashboard shows raw chart errors.** New users see red "Not enough columns given to draw the requested chart" boxes. Top 5 and Active URL cards are blank. | `overview-empty@1440.png` | **High**: first-run experience |
| U2 | **Empty tables give no guidance.** Header-only table plus an off-brand blue "1" pagination button; no "no links yet" or next step. Same on the click log. | `list-empty@1440.png`, `tracker-empty` | High |
| U3 | **Dead/broken short links show Django's bare, unbranded "Not Found".** This is the page *visitors* (not users) see. | `404-shortlink@1440.png` | High (trust) |
| U4 | **Contrast below WCAG AA.** White text on light green `#8BC34A` = **2.10:1** (promo cards, Login/Register buttons, landing "Subscriptions"). White on primary `#388E3C` = **4.12:1** (sidebar nav, header, feature text, CTA; needs 4.5:1). | audit: 14 distinct failures, 28 of 30 page-views | High (a11y) |
| U5 | Invalid fields aren't visually marked; error lists are bulleted default text above the input. | `create-error@1440.png` | Medium |
| U6 | No "you are here" in sidebar/nav (visual or `aria-current`). Pagination marks **every** page `aria-current="page"`. | audit `nav-no-current-page` on 22 views; HTML | Medium |
| U7 | Heading structure: dashboard and login have no `h1`; levels skip (h1→h4, h2→h5) on 22 views. | audit | Medium (screen-reader navigation) |
| U8 | No skip link and no `nav` landmark in the app shell. | audit, 30 views | Medium |
| U9 | Images: logo `alt="logo"` next to the visible word "Linkaroo" (announced twice); hero `alt="background"`; 4 empty `<img src="">` in Features. | audit | Low |
| U10 | Charts give no loading indication and reserve no height, so cards grow when Google Charts draws (layout shift). Charts are unlabeled SVG for screen readers. | code: no min-height; `[id*=chart]` empty until load | Low–Medium |
| U11 | Pagination is Bootstrap blue (`#0d6efd`), the only off-brand color in the app; shown even with a single page. | `list@1440.png` | Low |
| U12 | Mobile gutters are asymmetric (28 px left vs 52 px right at 320 px) and content is narrower than the nav block. | `update@320.png` | Low |
| U13 | "Subscribe Now" and "Contact Us" buttons do nothing (features don't exist). | audit `button-does-nothing` | Product decision (**not changed**: features/IA are out of scope) |

## Plan (restrained, in priority order)

| Step | Change | Visual impact | Verification |
|---|---|---|---|
| 1 | **U1/U2/U11 empty states:** dashboard renders "no data yet" messages instead of drawing charts when there's nothing to plot. Empty tables show one row: message plus the existing "Create Link" action. Pagination hidden when there's only one page, brand-colored otherwise. | Only empty states change; populated pages identical | Tests on empty and populated users; screenshot diff |
| 2 | **U4 contrast with brand kept:** text on light-green surfaces becomes a dark green ink (`#14301A`, about 7:1) instead of white, keeping the green surface. Primary green `#388E3C` deepens one shade to `#2E7D32` (same Material green family; white text 5.1:1). | Subtle; same palette | Recomputed contrast must show 0 failures |
| 3 | **U3 branded 404/500:** use the landing shell (navbar + brand colors). 404 copy: "This link doesn't exist or has been removed", plus a link home. 500 is a standalone static page (no DB/template-context dependency). | New pages only | Test: unknown alias → 404 with branded content |
| 4 | **U5 field errors:** red border on `aria-invalid` inputs; error text styled as small red text without bullets. | Error state only | `create-error` screenshot |
| 5 | **U6–U9 semantics:** skip link (visible on focus), `<nav aria-label>`, `aria-current` plus subtle active style on the current sidebar item, correct pagination `aria-current`, h1 per page and no skipped levels (tag changes keep the same visual size classes), decorative `alt=""`, remove empty `<img>`, visually-hidden table captions. | Only the active-nav indicator is visible | Audit rerun: 0 structure issues; desktop geometry unchanged except nav item |
| 6 | **U10 charts:** reserved min-height and "Loading chart…" placeholder text replaced on draw; containers get `role="img"` and an `aria-label` from the card title. | Removes chart-load jump | Screenshot + DOM check |
| 7 | **U12 mobile gutters:** symmetric content padding at <992 px. | Phones only | 320/375 screenshots |

**Explicitly not doing:** new fonts, color palette, layout, IA or copy rewrites; animations (none are needed, and motion would be decorative); changes to the dead promo buttons (U13 needs a product decision).

## Results
See the "Results" section appended after implementation.
