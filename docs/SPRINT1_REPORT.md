# Sprint 1 — Design System Refinement (v49)

Scope: Sprint 1 of the UI/UX PRD only. Sprint 2 (tab workspaces, homepage changes, settings sheet) has **not** been started.
The product decisions confirmed for Sprint 2 — tab memory, removing 继续探索 and the settings entry — are untouched.
The one exception is the theme choice, whose tokens and mechanism belong to the design system (see below).

## 1. Summary of changes

**Tokens**
- **Typography:** all 254 hard-coded font sizes now use semantic tokens.
  - Scale: Display 32–40, H1 28–32, H2 21–24, H3 18, Body 16, Body-sm 15, Secondary 14, Footnote 13, Caption 12, Caption-sm 11.
  - Outdoor mode keeps its larger sizes through `--fs-field-*`.
  - Mapping: 11→caption-sm, 12→caption, 13→footnote, 14/14.5→secondary, 15→body-sm, 16→body, 17–20→H3 (18), 21–24→H2, 26–32→H1, 34–56→Display.
- **Spacing:** 92 margin, padding and gap values now use `--space-*`.
  - 49 off-scale values (6, 7, 9, 10, 14, 18 px) snapped to the nearest 4px step, ties rounding down so nothing grows into overflow.
  - Hairlines up to 3px stay.
- **Radius:** 67 radii now use `--radius-xs/sm/md/(base)/lg/pill` (4 / 8 / 12 / 14 / 22 / 999).
- **Colour:** 35 hard-coded colours in components replaced by semantic tokens:
  - `--color-on-danger`;
  - `--on-photo`, `--on-photo-muted`, `--on-photo-fill`;
  - `--scrim`;
  - `--toast-bg`, `--toast-fg`;
  - `--hero-input-*`.
- **Dark theme:** completed. Every PRD palette token and `--color-on-danger` has a dark value. The four per-component
  dark overrides for text on red now come from the token.

**Theme**
- System / Light / Dark, default System, stored in `localStorage` `mushroom-guide:theme` and applied before first paint.
- Independent of outdoor mode. Included in the full backup's settings.
- Control: 拾菌 › 离线使用 › 外观. Sprint 2's settings sheet will also show it.

**New components** (all on `public/design-system.html`)
- **Segmented control `.seg`:** now used by the calendar mode switch, the comparison 并排 / 逐个看 switch and the journal's three steps.
  - Selected = raised segment plus bold text, so not colour alone.
  - 44px hit area.
- **Toggle `.toggle`** (checkbox with `role="switch"`): now used by 只记大概位置 and 显示底图.
- **Bottom sheet `.bsheet`:**
  - Rises from the bottom on phones (grabber, safe area) and is centred from 640px.
  - Backdrop tap, Esc and the close button all cancel.
  - Now used by the import preview and the wipe dialog; their ids are unchanged.
- **Skeleton `.skel`:** shimmer, static under reduced motion. Now used while the journal loads (list and home preview).
- **Error state `.err-state`:** amber, not red, because red stays for toxicity and emergency. Now used when the browser blocks storage.

**Interactive states**
- Disabled (50%, not-allowed) and busy (`aria-busy`, spinner, static under reduced motion) are now shared by every button, chip and icon button.
- The full-backup export shows busy while it runs.
- Focus rings are the same on all controls.

**Accessibility fixes found during QA (all real, not test artefacts)**
- Leaflet's map attribution link in dark mode.
- The header's MycoTrail subtitle over the green map.
- Calendar sticky month labels over scrolling cells: muted text, and the translucent current-month cell (1.5:1 in dark mode).
- Outdoor-mode month chips wrapping as "1 / 月".
- The focus box shown around page titles after navigation.

**Build-time style lint** (`style_lint()` in `src/build_site.py`)
- The build fails on any of these in component CSS:
  - a colour literal;
  - a pixel font size;
  - spacing over 3px that isn't a token;
  - a radius over 2px that isn't a token.
- Allowed: custom-property definitions (the tokens), forest-black `rgba(10, 14, 11, a)` shadows and scrims, `calc()` / `env()`, relative units.
- Any other exception must carry `/* ds-ok: reason */`. There are 2: the header-photo top padding (88px / 120px).
- Checked against the old stylesheet: it reports 442 violations there, and 0 now.

## 2. Files changed

- `src/template.html`: tokens, migration, components, theme, accessibility fixes.
- `src/build_site.py`: style lint, design page.
- `tests/test_site.py`: 13 new checks.
- `public/index.html` and `public/design-system.html`: generated.
- `public/sw.js`: `CACHE` v48 → v49.
- `docs/DESIGN_SYSTEM.md`, `docs/SPRINT1_REPORT.md`, `docs/sprint1/*.webp`, `CLAUDE.md`.

No data model, IndexedDB schema, backup format, routing, finder rule, recipe or safety text changed.

## 3. Screenshots (`docs/sprint1/`)

- **Before (v48) / after (v49) pairs:**
  - home 375 light and dark;
  - 拾菌 375 outdoor mode;
  - emergency 375;
  - journal 375 dark;
  - journal form 375 light and dark;
  - comparison 375 dark;
  - offline panel 375;
  - home, species and finder at 768;
  - home light and dark, 拾菌 dark, journal, species (outdoor) and emergency dark at 1440.
- **New:** `new-theme-375-light/dark` (appearance control), `new-design-system-768`.
- **Full set:** 66 screens before and after (6 views × 375/768/1440 × light/dark, plus outdoor mode at 375 and 1440). Pairs
  differ by 0–12% of pixels. The largest changes are spacing snaps on the emergency page and outdoor-mode chips; each was
  reviewed by eye.

## 4. Tests

- **Existing:** 217 / 217 pass.
- **New:** 13, all pass, for **230 / 230**:
  - theme default, switch, persistence and pre-paint application, independence from outdoor mode, and 跟随系统 clearing the stored choice;
  - segmented calendar switch;
  - switches for location options;
  - import preview as a bottom sheet;
  - Esc and backdrop cancel without changes;
  - skeleton and error helpers;
  - blocked-storage error state;
  - design-system page components, theme switch and no overflow.
- **Offline regression:** passes. It covers offline reload, the catalog and photos offline, writing a record with a photo
  offline, and the record and photo surviving a wipe of all caches.
- **Build:** the safety checks, banned phrases, recipe and habitat rules and the new style lint all pass.

## 5. Accessibility and layout QA (automated, headless Chromium)

- **axe-core WCAG 2.2 AA, top of each view:** 10 views × 375/768/1440 × light/dark × outdoor mode on/off = **120 combinations, 0 violations**.
- **axe-core, deep-scroll positions:** 12 positions × 375/1440 × light/dark × outdoor mode = **96 checks, 0 violations**. Positions:
  - calendar, habitats, field guide, outdoor safety, offline, appearance;
  - checklist, kitchen;
  - season intelligence;
  - data centre, timeline, my species.
- **Horizontal overflow:** none in the 120 combinations.
- **Card dimensions:** cards in the same row of every grid have equal widths (species, toxic, home entries, habitats, recipes).
- **Wrapping:** checked by the real line boxes of every chip, button, segment and tab label.
  - One label wraps: the long "出门前下载全部照片（约 3.x MB）" button in outdoor mode at 375px, onto two lines inside the button. Accepted.
  - The three journal step labels fit on one line at 375 and 390px. At 320px (below the 375px target) they wrap onto two centred lines.

## 6. Known issues and exceptions

- **System serif title:** it shows only where a CJK serif exists (Apple). The test browser and many Android phones fall back to sans.
- **Spacing snaps:** about 4px less padding in a few places, such as the call buttons; reviewed and accepted.
- **Style-lint exceptions:** 2, both documented inline. Tokens can still be misused semantically (for example a caption token on a heading); the lint only enforces that tokens are used.
- **Theme control location:** for now it lives in the 拾菌 offline section. Sprint 2 adds the header settings entry.
- **Leaflet:** its own CSS still sets colours in its markup; we override only what we show (attribution).

## 7. Not verified on real devices

None of the following has been tested. All results above come from headless Chromium.
- iPhone Safari and the iPhone Home-Screen app: safe-area insets, bottom sheet gestures, theme switch before paint, the system serif.
- Android Chrome, desktop Safari and Firefox.
- VoiceOver and TalkBack reading of the new switch, segmented control and sheets.
- Outdoor readability in real sunlight.
