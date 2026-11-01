# 拾菌记 MycoTrail (Pacific Northwest Mushroom Field Guide & Explorer)

Brand (since 2026-11, formerly 野菌速查手册): 中文名 **拾菌记**, English **MycoTrail**, slogan 「拾自然之菌，记森林之迹。」 /
"Explore the forest. Know your fungi." Title: `拾菌记 MycoTrail — Pacific Northwest 野菌探索指南`; PWA name 拾菌记 MycoTrail,
short_name 拾菌记. 野菌速查手册 may appear only as a description or SEO keyword, never as the brand. The mark is one golden
chanterelle on forest green (`src/brand/mark.svg`, original artwork); never a toxic mushroom or a skull.

A Simplified-Chinese, mobile-first field guide to wild mushrooms, shared with friends who forage
(many in the Pacific Northwest). It is a single static page with a feature finder, toxic
look-alike comparisons, an emergency page, field/kitchen guides and recipes, installable as an
offline PWA. Site copy is Simplified Chinese; the owner writes in both Chinese and English.

Live: https://bbpouq.github.io/mushroom-guide/ (GitHub Pages, deployed by `.github/workflows/pages.yml`)

## Commands

```sh
python3 src/build_site.py            # regenerate public/index.html from src/ (always do this after editing src/)
python3 tests/test_site.py           # 153 end-to-end checks; must end with "ALL PASSED"
cd public && python3 -m http.server  # preview at http://localhost:8000 (offline mode needs http, not file://)
python3 src/make_icons.py            # regenerate icons, favicon, og.png and brand/ logos from src/brand/mark.svg (Playwright)
python3 src/fetch_seasonality.py     # refresh iNaturalist month counts (needs network; the build itself never fetches)
python3 src/fetch_photos.py          # pick example photos for species that lack one (--all to re-pick); needs network + Pillow
```

Test setup, once: `pip install playwright pillow && python3 -m playwright install chromium`.

## Layout

```
src/
  data/book.py           European species, top-10 toxic, recipe index (rewritten from the book; page numbers = English original)
  data/north_america.py  North American additions: NA_SPECIES, NA_TOXIC (each entry cites sources), NA_GROUP_OF (which
                         group each joins), TOXIC_ORDER (toxic list order, most dangerous in the PNW first),
                         plus NA_SPECIES_NOTES / NA_POISON_NOTES: 【编者注】 added to book entries, keyed by Latin name
  data/tags.py           Feature-finder tags for every edible AND toxic species, keyed by Chinese name
  data/compare.py        Side-by-side look-alike comparisons (cols reference species slugs)
  data/seasonality.py    Generated: iNaturalist research-grade observations per month in BC/WA/OR (combined and per region)
                         plus records per year, keyed by slug.
                         Book species with a different PNW taxon are mapped in fetch_seasonality.PNW_TAXON
  data/photos.py         Generated: one example photo per species (public/photos/<slug>.webp) with author, licence, link,
                         and HEROES: the header photo behind each view's large title, keyed by the <!--HERO:key--> marker
                         (home-porcini, species, finder, toxic, explore, kitchen, log, recipes; none on the emergency view; a third number
                         in fetch_photos.HEROES is the observation id, for photos outside the taxon's featured set). To change a
                         header photo, add a new key rather than reusing an old one: the offline MEDIA cache keeps old file names.
                         RECIPE_PHOTOS (dish photos, keyed by recipe id) is optional; without one a recipe shows its
                         main mushroom's example photo, captioned as such
                         Pin a better photo in fetch_photos.PINNED rather than editing this file
  data/guide.py          Field/kitchen panels, glossary, recipes: RECIPES6 (rewritten from the book) and RECIPES_ORIG
                         (our own; every recipe names its mushrooms in `sp` and carries a safety tip)
  template.html          All CSS + markup + JS; build_site.py injects DATA JSON and the guide panels
  build_site.py          Assembles public/index.html; validates tags, slugs and comparison links
  brand/mark.svg         Master brand mark (golden chanterelle); make_icons.py renders everything else from it
  make_icons.py          App icons, favicon (icon.svg, favicon-32.png), apple-touch-icon, og.png share image, public/brand/ logos
public/                  Deployed as-is: index.html (generated, do not hand-edit), sw.js, manifest, icons, og.png,
                         brand/ (logos: zh/en lockups light/dark, one-colour marks, app icon SVG),
                         vendor/three-0.160.0.module.min.js (MIT, licence beside it; loaded lazily for the 3D model),
                         vendor/leaflet-1.9.4.js + .css (BSD-2, licence beside it; loaded when the finds map scrolls into view)
tests/test_site.py       Playwright checks (starts its own server)
.github/workflows/pages.yml  Pages deploy on push to main; fails if public/index.html is stale (rebuild before committing)
```

Never hand-edit `public/index.html`; edit `src/` and rebuild. When shipping a user-visible change,
bump `CACHE` in `public/sw.js` (e.g. `mushroom-guide-v4`) so installed phones refresh promptly.
Photos and the 3D library live in a separate cache, `MEDIA` in `sw.js` (`mushroom-guide-media-1`), that survives
releases so photos downloaded for a trip are kept. Bump it only when existing photo files are replaced by different
pictures (e.g. after `fetch_photos.py --all`). The build copies the name into the page; both must match.

## Content rules (safety and copyright come first)

- **Safety first.** Never weaken or remove a warning, the "有任何疑问，就不要吃" message, look-alike notes,
  must-cook flags or the emergency page. New edible species must list their dangerous look-alikes (`warn`).
- **No book images, ever.** The source book's photos and recipe photos are copyrighted; the site is public.
  Only add photos the owner took or properly licensed images, always shown with author, licence and a link.
  Example photos come from iNaturalist: CC0, public domain, CC BY, BY-SA, BY-NC and BY-NC-SA are accepted
  (the site is free and non-commercial; if that ever changes, NC photos must be replaced). No "ND" licences.
  Every photo caption says it is only an example and not enough to identify a mushroom.
- **Non-book content needs sources.** Anything not from the book (North American species, toxic additions,
  comparisons, emergency info) must carry `sources` with links. Prefer UBC Beaty Museum "Mushrooms Up!",
  MushroomExpert, MykoWeb/California Fungi, NAMA, state or provincial agencies, USDA Forest Service and
  peer-reviewed papers. Do not state facts you cannot source.
- Safety notes we added that are not in the book are labelled `【编者注】`.
- Book text is our own Chinese rewrite. Keep rewriting, and never paste passages from the book or the web.
- The site is written for North American (mostly Pacific Northwest) readers. Do not frame content as "European":
  species are ordered by Pacific Northwest records, seasons come from local records where there are >= 30, and
  species with < 30 local records carry a "西北太平洋少见" badge. Editor's notes may still name Europe when they
  explain how a local species differs.
- Site copy never says "原书" or cites book page numbers (readers have no context for them; the build fails on
  "原书"). The book is credited once, by full title, in the footer. Page numbers stay in `data/book.py` only.
- Every species, edible or toxic, needs an entry in `data/tags.py`; the build fails otherwise.
- The finder must stay conservative: toxic species are matched leniently (a "no volva" or "no ring"
  answer still lists deadly amanitas and galerina, with the reason shown), and results put toxic first.
- Our own recipes must use only mushrooms the site covers, say "cook thoroughly" where it matters, and repeat
  the species' key look-alike warning in the tip. Never suggest eating a mushroom raw, anywhere on the site
  (the kitchen guide says to cook every wild mushroom thoroughly).
- Permits and seasons vary by place. Phrase them as "check local rules" / "因地区而异".
- **No trial portions, no detox claims (2026-11 safety audit).** Never advise "first time, eat only a spoonful / a small
  portion": the advice is "have an experienced person confirm it in person, cook thoroughly". Never say blanching, boiling,
  pickling, freezing or drying removes toxins; say they cannot make a toxic mushroom safe (source: KU Health System Poison
  Control). No "works with any mushroom" recipes: name the species. The build fails on a list of banned phrases
  (`build_site.py`); add to it rather than removing from it.
- The emergency page says: call now, do not wait for symptoms, do not induce vomiting unless poison control says so, no
  home remedies, keep the mushroom and leftovers (source: California Poison Control). "我可能吃了不确定的菌" on the home
  view opens it. The guide's lost-in-the-woods panel follows S.T.O.P. and "stay put" (BC SAR Association, AdventureSmart).
- Species pages state their review status honestly: compiled by the editor from the listed sources, not reviewed by a
  mycologist, with the build date (`DATA.built`). Never invent reviewers, review dates or expert sign-off.

- **学习 (`#learn`)**: quizzes are generated only from the site's own data (species structure tags, comparison rows and
  look-alike pairs, example photos, glossary, 3D part notes) plus a short list of sourced safety true/false lines (`SAFETY_Q`,
  each with its source). Never ask "is it edible", never treat the 结论 row of a comparison as a question, never offer two right
  answers. 今日 5 题 is seeded by the date; wrong answers go to the 错题本 and leave it when answered right. Progress (species
  seen, terms known, answers, days) lives in `localStorage` `mushroom-guide:learn:v1`, this device only; no ranking, no
  streaks, and the page says that a score is not identification skill or permission to eat.

## House UI rules (2026-11, apply to every change)

1. No pure black and no dark frames: depth comes from four surface layers 1-3% apart in lightness
   (`--surface-0` page, `--surface-1` cards, `--surface-2` sheets/popovers/inputs, `--surface-3` hover). Shadows and scrims use
   forest black `rgba(10, 14, 11, a)`, never `rgba(0, 0, 0, a)` or `#000`.
2. Inputs on focus: no outline or border, a deeper double ring (`0 0 0 1.5px` primary 62% + `0 0 0 6px` primary 16%).
3. Font weights only through `var(--fw-400 … --fw-800)`; dark mode lowers every weight by 40.
4. Titles that "type in" (`typeIn()`): each character fades in from `blur(6px)`, 120ms, 30ms apart. Never on warnings;
   off under reduced motion and in field mode.
5. Icons sit 0.125em lower (`.icon { vertical-align: -0.125em }`). 6. Numbers are `tabular-nums` site-wide.
7. Every `<details>` folds with grid rows 0fr → 1fr (`foldify()`; call it after rendering new details).
8. Body text uses `text-wrap: pretty` (headings keep `balance`).
9. Springs as CSS `linear()` easings generated by `springEase(k, c)`: drag 1200/80 (`--spring-drag`, no overshoot),
   taps/toggles 380/18 (`--spring`, a small bounce).
10. A copy button shows a check mark for 2.5s, then returns to its icon (`copied(btn)`).

## Design system (iOS-style glass, since 2026-10)

- Style (since 2026-11): "modern nature science × field journal": iOS-style translucent bars over warm ivory (`#F5F2EA`
  light, forest black `#0C0F0D` dark) with a faint moss/amber aura behind (`body::before`). Large bold titles, hairline (0.5px) separators, filled capsule
  chips and buttons, cards with soft depth. No English eyebrows, thick rules or decorative numbering.
- Glass (`backdrop-filter`, tokens `--glass`, `--glass-strong`, `--glass-blur`) only on bars and floating layers:
  header, tab bar, sidebar, sticky search bar, sheet, toast, calendar sticky rows. Cards are translucent
  (`--color-card`) without blur, which stays fast on phones. `prefers-reduced-transparency` and browsers without
  backdrop-filter get opaque fills (`--color-card-solid`, `--color-background`).
- Palette tokens in `:root` (light) plus dark-mode overrides: forest green `#2D5A3D` (dark `#9CCB9F`), moss `#5E7334`,
  muted amber `#C98A2B` (fills only; text on it is black), danger red reserved for toxicity and emergency.
  Green marks interaction only; never use it as a "safe/edible" verdict (the 上品 and 西北太平洋常见 badges are amber and grey).
  Style everything through tokens; no raw hex in components.
- Motion (since 2026-11): views fade in with a springy header; cards ease in as they scroll into view
  (IntersectionObserver adds `is-reveal` / `is-shown`, skipped under reduced motion); controls shrink on press;
  header photos drift slowly; the phone species sheet can be dragged down to close. Never animate warnings.
  Animate `.view` with opacity only: a transform on it moves the sticky search bar inside.
- The finder (特征识别) is a step-by-step guide: one question at a time with a progress row (tap any step to change it),
  "不知道，跳过" on every question, 上一题, and a short "why this matters". It asks only the five features every species is tagged
  with in `data/tags.py`; do not add questions without checked tags for every species. Results never score or rank by
  probability: each candidate shows 相符 / 仍列出 (kept despite a contradicting answer) / 未确认, deadly matches are named in an
  alert as soon as one answer is given, a volva answer raises the amanita alarm, and toxic species come first.
- The finder has an interactive 3D mushroom (`#model`): drag to rotate, tap a part for its explanation; each
  finder question has a "在模型上看" button. three.js (vendored, imported only when the model scrolls into view)
  renders it with soft light and shadows; a small 2D-canvas lathe renderer is the fallback when WebGL or the import
  fails. Part colours are the `--model-*` tokens. Both pause when off screen.
- Home view (`#home`, the default) has a hero photo with a search box (edible and toxic species, toxic first; an empty
  result says not being listed does not mean safe), four entry cards (识别 / 图鉴 / 毒菌与近似种 / 记录), the "认出来，不等于
  可以吃" note, the "今日一菌" card (`#today`): one in-season, common (>= 300 PNW records) edible per day, never a
  "高风险" one, picked by date; photo with the name over it, then 认识它, 怎么吃 (kitchen note plus recipes that use it), its
  look-alike warning and "有任何疑问，就不要吃". Arrows step to other days. The card keeps one size on every day: JS reserves
  the tallest possible body (measured off screen per width), and the description, habitat and look-alike note are clamped to a few
  lines like the species cards (full text in the sheet). Never clamp the kitchen note. Then "N 月可以找", 季节变化 (species whose
  historical iNaturalist records rise or fall next month, labelled as past records, not a forecast) and learning links.
- The species view is the edible 图鉴 (catalog). The species sheet opens with the photo (tap to zoom the 1024px copy full
  screen, `#zoom`), names, a one-line summary and three quick facts, then sticky section jumps: 快速鉴别 (the tagged features),
  易混毒菌 (warning plus photo pairs of every comparison it is in), 生态与季节, 厨房, 资料来源 (sources labelled by kind:
  官方机构 / 学术文献 / 专业参考 / 社区观察 / 百科 / 图书, plus where the season data and photo come from).
- Comparisons show each mushroom's photo (tap to zoom) and switch between 并排 and 逐个看 (default on phones for 3+ columns),
  and say that no single difference is enough to eat. SpeciesSpecies
  cards lead with a full-width photo, clipped by the card (`.sp-card { overflow: hidden }`, never round the photo itself).
  Toxic species use the same card (`sp-card sp-card--toxic`, a red or amber band drawn inside the clip by `::before`) in the same grid, and open the same sheet with the full description, notes, look-alikes and sources. Desktop cards tilt toward the pointer; header photos move with parallax.
- The page grid uses `minmax(0, 1fr)` and `main { min-width: 0 }` so a scrolling strip can never widen the page.
- Type: the platform system font (SF Pro / PingFang SC on Apple, Noto Sans SC or YaHei elsewhere). No web fonts.
- Layering: use only the z-index scale `--z-sticky 10`, `--z-header 20`, `--z-nav 30`, `--z-toast 40`
  (dialogs use the top layer).
- **Class names are component-prefixed** (`sp-card__name`, `badge--choice`, `tox-card`, ...). Never give an
  element a class that another component uses as its root. A badge once had the class `top`, inherited the
  sticky header's positioning and floated over the search bar. The test suite checks for this.
- Composable building blocks that may be combined with a component class: `btn`, `chip`, `icon`, `icon-btn`, `latin`.
- Field mode (户外模式, `html[data-field="on"]`, remembered in `localStorage` `mushroom-guide:field`, set before first
  paint by an inline script): toggled by the sun button in the header, the sidebar and the guide's offline section.
  Bigger type (18px body) and targets (52px), stronger contrast, solid surfaces, no blur, no animation, no header photos,
  and the home view keeps only search, entries and safety (today card, season, learning links, 3D model and footer hidden).
- Offline: the guide's 离线使用 section reports what is on this device (network, text, photos small/HD counts, 3D library,
  external links need network) and downloads every photo on request (small, or small + HD) into the `MEDIA` cache.
  When offline, the header shows a 离线 pill and external links get "（需联网）"; uncached images show as grey frames.
- Touch targets at least 44px on coarse pointers (chips keep a 34px look with a 44px hit area via `::after`); SVG icons only (no emoji); visible labels on inputs;
  respect `prefers-reduced-motion`; no horizontal overflow at 375px (wide tables must reflow on phones).
- Information architecture (since 2026-11): three tabs, the journey 认识蘑菇 → 探索森林 → 记录发现.
  **识菌** (identify) = views home (overview: search, 开始识别, entries, safety, deadly look-alikes strip, 最近看过, today card),
  finder (+ 3D model, 看哪些特征, glossary `#guide-gloss`, `#learn-features`), species, toxic, guide (now 厨房指南: checklist
  `#guide-check`, kitchen `#guide-kitchen`), recipes and learn (学习, `#learn`). **拾菌** (explore) = view explore: region chips (remembered in
  `mushroom-guide:region`, they drive the month strip, 季节变化 and the calendar), "N 月在…常见", 季节变化, calendar
  (`#guide-calendar`), field guide (`#guide-field`, lost panel) and offline (`#guide-offline`). **菌记** (journal) = view log.
  The emergency page belongs to no tab and stays one tap away (header SOS). `TAB` in the script maps views to tabs.
  Never add a fourth tab; 食谱 and 厨房 stay inside 识菌.
- Nav: one sticky header for every size (brand left, the three tabs as `.topnav` from 768px, search / field mode / SOS
  right) and a `.subnav` row of 识菌 pages shown only while a 识菌 view is open (`html[data-tab="id"]`). Phones also get a
  3-tab bottom bar. Tab icons are Lucide-style strokes (book-open, compass, notebook-pen). No sidebar.

## Routing (keep it script-driven)

The page is often opened inside sandboxed previews (chat apps, file viewers) where following an `href="#x"`
navigates the frame away and blanks the page. All in-page links are intercepted in JS. History is
updated with `pushState` inside try/catch, so it works where allowed and fails silently elsewhere.

- Views: `#home` (default, 识菌 overview), `#explore` (拾菌), `#log` (菌记), `#learn` (识菌 › 学习), `#species`, `#finder`, `#toxic`, `#guide` (厨房指南), `#recipes`, `#emergency`.
  `#guide-*` and `#learn-*` links open whichever view now holds that id (sections moved between views keep their ids).
- Deep links: `#sp-<slug>` opens a species sheet, `#tx-<slug>` opens a toxic species sheet (same sheet, closing goes
  back to `#toxic`), `#cmp-<id>` scrolls to a comparison,
  `#guide-<section>` to a section of the guide view (e.g. `#guide-check`, the before-you-eat checklist;
  `#guide-calendar`, the season calendar built from `data/seasonality.py`), `#rc-<id>` opens a recipe in the recipes view, `#guide-gloss` opens the glossary.
  A sheet opened from any view stays over that view; closing it returns there and keeps the scroll position. The old `#guide-log` link still opens `#log`.
- The finds journal (`#log`) keeps records in `localStorage` under `mushroom-guide:finds:v1` (same key as the first version;
  newer fields: status none/candidate/expert, verifier, lat/lon/alt/acc, hab, trees, photos) and photos as resized JPEG blobs in
  IndexedDB (`mushroom-guide` / `photos`). This device only, never uploaded. Choosing a species makes a find a "候选"; only the
  person marks "专家当面确认（自记）", naming who confirmed it (plus organisation, date and method; photo-only opinions do not
  count). GPS is read only when the person taps "记下当前位置"; "只记大概位置" stores coordinates cut to 0.01° (~1 km) and no
  altitude. Up to 8 photos, each labelled with the part it shows (`parts`). Filters add region (rough BC / WA / OR from
  coordinates). Export chooses coordinate precision (exact / ~1 km / none) and warns when exact coordinates leave the
  device. A 年度探索报告 shows the year's counts, months and a photo wall.
  Records can be edited, filtered (text, species, year, month), shown on a timeline grouped by month, exported as JSON
  (with photos) or CSV, and imported (merged by id). Every storage call fails soft.
- The finds map uses Leaflet with only the person's points; the OpenStreetMap basemap loads only after "显示底图" is ticked
  (the note says the tile server sees the area). The season explorer in the guide filters the calendar by region
  (BC / 华盛顿 / 俄勒冈), has a month view and a species search; species with < 30 records in that region are listed apart.
  The species sheet shows records per region and per year, saying that more records mostly mean more uploaders.
- Slugs come from the Latin name (`Boletus edulis` becomes `boletus-edulis`). Hash names stay plain ASCII.
- In-page jumps use `<button data-jump="id">`, not anchors.
- Scroll offsets come from `html { scroll-padding-top }` (header height is measured into `--header-h`).
  Do not also add `scroll-margin` to targets; the two add up.

## Performance and accessibility (round 6, 2026-11)

- Only the first view is built at load; every other view is built the first time it opens (`LAZY` / `ensure(v)` in the
  script; `apply()` and `show()` call `ensure`). A new view with heavy rendering goes into `LAZY`, and code that touches a
  view's DOM before navigating there calls `ensure` first (see the `data-log-sp` handler).
- Views fade in only after first paint (`html.is-ready`); the first page shows at once. The tab (`data-tab`) is set by an
  inline script before paint so the 识菌 sub-nav never pops in and shifts the page.
- The today card measures the likely tallest bodies at once and the rest when idle, all in one hidden box (one layout),
  and caches the height per width in `localStorage` (`mushroom-guide:today-h:*`). Never measure in a loop.
- `DATA` ships as `<script type="application/json" id="data">` (escaped `</`) and is read with `JSON.parse`.
- Header photos get a 640px copy (`hero-*-640.webp`, made by the build from the 1024px file) via `srcset`; the home photo
  loads with `fetchpriority="high"`. Long card lists use `content-visibility: auto`.
- Baseline (Lighthouse 13, gzip as on GitHub Pages): desktop 99–100 performance; mobile (simulated slow 4G, 4× CPU) ~77;
  accessibility, best practices and SEO 100. axe-core reports no WCAG 2.2 AA violations on any view, sheet or dialog in
  light and dark at 375px and 1440px. Landmarks need unique labels; headings must not skip levels (add an sr-only h2).

## Before you finish a change

1. `python3 src/build_site.py`, then `python3 tests/test_site.py` must end with "ALL PASSED".
2. Look at the changed view at 375px and 1440px, in both light and dark mode.
3. For a release, bump the `CACHE` version in `public/sw.js`. Commit and push to `main`; GitHub Pages deploys it.

## Aesthetic Judgment

When doing design, creative, or artistic work — anything requiring aesthetic judgment such as UI design, visual assets, layouts, color choices, typography, animation, branding, or creative direction — read `TASTES.md` if it exists and apply its constraints to your output.
