# 野菌速查手册 (Wild Mushroom Field Guide)

A Simplified-Chinese, mobile-first field guide to wild mushrooms, shared with friends who forage
(many in the Pacific Northwest). It is a single static page with a feature finder, toxic
look-alike comparisons, an emergency page, field/kitchen guides and recipes, installable as an
offline PWA. Site copy is Simplified Chinese; the owner writes in both Chinese and English.

Live: https://bbpouq.github.io/mushroom-guide/ (GitHub Pages, deployed by `.github/workflows/pages.yml`)

## Commands

```sh
python3 src/build_site.py            # regenerate public/index.html from src/ (always do this after editing src/)
python3 tests/test_site.py           # 57 end-to-end checks; must end with "ALL PASSED"
cd public && python3 -m http.server  # preview at http://localhost:8000 (offline mode needs http, not file://)
python3 src/make_icons.py            # regenerate app icons (Pillow)
```

Test setup, once: `pip install playwright pillow && python3 -m playwright install chromium`.

## Layout

```
src/
  data/book.py           European species, top-10 toxic, recipe index (rewritten from the book; page numbers = English original)
  data/north_america.py  North American additions: NA_GROUP, NA_SPECIES, NA_TOXIC (each entry cites sources)
  data/tags.py           Feature-finder tags for every edible AND toxic species, keyed by Chinese name
  data/compare.py        Side-by-side look-alike comparisons (cols reference species slugs)
  data/guide.py          Field/kitchen panels, glossary, the 6 featured recipes
  template.html          All CSS + markup + JS; build_site.py injects DATA JSON and the guide panels
  build_site.py          Assembles public/index.html; validates tags, slugs and comparison links
  make_icons.py          App icons
public/                  Deployed as-is: index.html (generated, do not hand-edit), sw.js, manifest, icons
tests/test_site.py       Playwright checks (starts its own server)
.github/workflows/pages.yml  Pages deploy on push to main; fails if public/index.html is stale (rebuild before committing)
```

Never hand-edit `public/index.html`; edit `src/` and rebuild. When shipping a user-visible change,
bump `CACHE` in `public/sw.js` (e.g. `mushroom-guide-v4`) so installed phones refresh promptly.

## Content rules (safety and copyright come first)

- **Safety first.** Never weaken or remove a warning, the "有任何疑问，就不要吃" message, look-alike notes,
  must-cook flags or the emergency page. New edible species must list their dangerous look-alikes (`warn`).
- **No book images, ever.** The source book's photos and recipe photos are copyrighted; the site is public.
  Only add photos the owner took or properly licensed images (e.g. CC on Wikimedia Commons) with attribution.
  Species cards link out to iNaturalist and Wikipedia for photos instead.
- **Non-book content needs sources.** Anything not from the book (North American species, toxic additions,
  comparisons, emergency info) must carry `sources` with links. Prefer UBC Beaty Museum "Mushrooms Up!",
  MushroomExpert, MykoWeb/California Fungi, NAMA, state or provincial agencies, USDA Forest Service and
  peer-reviewed papers. Do not state facts you cannot source.
- Safety notes we added that are not in the book are labelled `【编者注】`.
- Book text is our own Chinese rewrite. Keep rewriting, and never paste passages from the book or the web.
- Every species, edible or toxic, needs an entry in `data/tags.py`; the build fails otherwise.
- The finder must stay conservative: toxic species are matched leniently (a "no volva" or "no ring"
  answer still lists deadly amanitas and galerina, with the reason shown), and results put toxic first.
- Permits and seasons vary by place. Phrase them as "check local rules" / "因地区而异".

## Design system (from the ui-ux-pro-max skill)

- Style: Minimalism / Swiss: grid, strong type hierarchy, thin rules, little decoration.
- Palette tokens in `:root` (light) plus dark-mode overrides: primary green `#15803D`, accent amber
  `#D97706` (fills only; text on it is black), danger red reserved for toxicity and emergency.
  Style everything through tokens; no raw hex in components.
- Type: Outfit (headings) and Work Sans (body), with Noto Sans SC for Chinese. Base 16px.
- Layering: use only the z-index scale `--z-sticky 10`, `--z-header 20`, `--z-nav 30`, `--z-toast 40`
  (dialogs use the top layer).
- **Class names are component-prefixed** (`sp-card__name`, `badge--choice`, `tox-card`, ...). Never give an
  element a class that another component uses as its root. A badge once had the class `top`, inherited the
  sticky header's positioning and floated over the search bar. The test suite checks for this.
- Composable building blocks that may be combined with a component class: `btn`, `chip`, `icon`, `icon-btn`, `latin`.
- Touch targets at least 44px on coarse pointers; SVG icons only (no emoji); visible labels on inputs;
  respect `prefers-reduced-motion`; no horizontal overflow at 375px (wide tables must reflow on phones).
- Phone: sticky header plus bottom nav (at most 5 tabs). Tablet: top nav. Desktop (1024px and up): sidebar.

## Routing (keep it script-driven)

The page is often opened inside sandboxed previews (chat apps, file viewers) where following an `href="#x"`
navigates the frame away and blanks the page. All in-page links are intercepted in JS. History is
updated with `pushState` inside try/catch, so it works where allowed and fails silently elsewhere.

- Views: `#species`, `#finder`, `#toxic`, `#guide`, `#recipes`, `#emergency`
- Deep links: `#sp-<slug>` opens a species sheet, `#tx-<slug>` scrolls to a toxic card, `#cmp-<id>` to a comparison
- Slugs come from the Latin name (`Boletus edulis` becomes `boletus-edulis`). Hash names stay plain ASCII.
- In-page jumps use `<button data-jump="id">`, not anchors.
- Scroll offsets come from `html { scroll-padding-top }` (header height is measured into `--header-h`).
  Do not also add `scroll-margin` to targets; the two add up.

## Before you finish a change

1. `python3 src/build_site.py`, then `python3 tests/test_site.py` must end with "ALL PASSED".
2. Look at the changed view at 375px and 1440px, in both light and dark mode.
3. For a release, bump the `CACHE` version in `public/sw.js`. Commit and push to `main`; GitHub Pages deploys it.

## Ideas not yet built

- A 12-month season calendar showing all species at once.
- A "before you eat" checklist (dig out the base, spore print, smell, compare with look-alikes).
- A personal finds log kept in localStorage (per device only; wrap storage in try/catch).
- Photos: only owner-taken or properly licensed images, with attribution.
