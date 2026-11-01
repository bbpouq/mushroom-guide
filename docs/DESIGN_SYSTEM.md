# Design system (round 9: Nature Editorial × Modern Field App)

Live showcase: `public/design-system.html` (https://bbpouq.github.io/mushroom-guide/design-system.html).
The build generates it from the site's own `<style>` block and icon sprite, so it cannot drift from the app.

## Colour tokens (`:root` in `src/template.html`)

| PRD token | CSS variable | Value | Use | Contrast on cream |
|---|---|---|---|---|
| Forest 900 | `--forest-900` | #243B30 | brand surfaces (primary action card) | — |
| Forest 700 | `--color-primary` | #3F6149 | interaction: selected chips, primary buttons, links | 6.4:1 |
| Moss 500 | `--color-secondary` | #819477 | quiet drawings only | 3.0:1 (never text) |
| Moss 100 | `--color-primary-surface` | #E8EDE3 | light green fills | — |
| Cream 50 | `--surface-0` | #F8F6EF | page | — |
| Paper 100 | `--color-muted` | #EFEDE3 | secondary fills | — |
| Bark 500 | `--bark-500` | #967A5A | decoration only | 3.7:1 (never text) |
| Amber 500 | `--color-accent` | #C18B43 | fills, dark text on it | 2.8:1 (never text) |
| Text Primary | `--color-foreground` | #29352D | body text | 11.8:1 |
| Text Secondary | `--color-muted-foreground` | **#5E665D** | secondary text | 5.5:1 |
| Border | `--color-border` | #E2E3D9 | hairlines | — |
| Danger | `--color-destructive` | #B84D42 | danger fills (white text 5.0:1) | 4.7:1 |
| Danger text | `--color-danger-text` | #A3392F | danger text | 6.1:1 |

The PRD's Text Secondary (#788077) is 3.77:1 on cream, which fails WCAG AA for normal text, so it was darkened to
#5E665D. Cards, sheets and hover use four surface layers 1–3% apart (`--surface-0…3`). Dark mode keeps its own tuned
values (forest black, weights −40); axe-core reports no contrast failures in either theme.

Green marks interaction only, never "safe" or "edible". Red is only for toxicity and emergency.

## Tokens added in Sprint 1

- Type: `--fs-body-sm` 15, `--fs-footnote` 13, `--fs-caption-sm` 11, `--fs-h3` 18 (was 19); outdoor mode `--fs-field-body` 18, `--fs-field-title` 20, `--fs-field-display` 34.
- Radius: `--radius-xs` 4, `--radius-md` 12, `--radius-pill` 999 (with `--radius-sm` 8, `--radius` 14, `--radius-lg` 22).
- Colour: `--color-on-danger` (white; `#1B0505` in dark), `--on-photo` / `--on-photo-muted` / `--on-photo-fill`, `--scrim`, `--toast-bg` / `--toast-fg`,
  `--hero-input-bg` / `-fg` / `-muted`; dark values for every PRD palette token.

## Lint (build fails otherwise)

`style_lint()` in `src/build_site.py` rejects, in component CSS: colour literals, pixel font sizes, spacing > 3px that is not
`var(--space-*)`, radii > 2px that are not `var(--radius-*)`. Allowed: token definitions, forest-black `rgba(10, 14, 11, a)`,
`calc()` / `env()`, relative units. Any other case needs `/* ds-ok: reason */` in the declaration (2 today).

## Type

| Level | Token | Size | Face |
|---|---|---|---|
| Display | `--fs-display` | 32–40px | system serif (`--font-display`: Songti SC on Apple, Noto Serif CJK where installed) |
| H1 | `--fs-h1` | 28–32px | system serif |
| H2 | `--fs-h2` | 21–24px | system sans |
| H3 | `--fs-h3` | 19px | system sans |
| Body | `--fs-body` | 16px | system sans, line-height 1.65 |
| Secondary | `--fs-secondary` | 14px | |
| Caption | `--fs-caption` | 12px | |

No web fonts: where no CJK serif is installed (many Android phones, Linux), the display face falls back to the sans.

## Spacing

4px base: `--space-1` 4, `-2` 8, `-3` 12, `-4` 16, `-5` 24, `-6` 32, `-8` 40, `-7` 48, `-9` 64 (`-7` predates the PRD and
stays 48 so existing layouts do not move).

## Components and where they are reused

| PRD component | Implementation | Used in |
|---|---|---|
| BottomNavigation / DesktopNavigation | `.botnav`, `.topnav`, `.subnav` | every view |
| PageHeader | `.view__head` (+ header photo) | every view |
| Section navigation | `.jump-row` (one swipeable row on phones) | 拾菌, 菌记, 厨房指南 |
| SpeciesCard | `.sp-card` (`--toxic`, `--poison`) | 图鉴, 毒菌 |
| HabitatCard | `.habitat` (folding card) | 拾菌 › 生境探索 |
| SeasonCard | `.now__item`, `.intel__item` | home, 拾菌 |
| JournalCard | `.jcard` | home preview |
| SearchBar | `.search-field` | home, 图鉴, 菌记 |
| SegmentedControl | `.chip-list` + `aria-pressed`, `.jsteps` | region, filters, journal steps |
| Primary / Secondary / Danger / Icon button | `.btn--primary`, `.btn`, `.btn--danger`, `.icon-btn` | everywhere |
| Dialog / sheet | `.sheet` (species), `.imp` (import, wipe), `#zoom` | |
| Toast | `.toast` | everywhere |
| EmptyState | `.empty-state`, `.empty-state--left`, `.finds__empty` | journal, home, search, season |
| SafetyWarning | `.callout--danger`, `.safety` | sheets, finder, recipes, checklist |
| SpeciesBadge / IdentificationStatus | `.badge--*`, `.sp-card__review`, `.jcard__st`, `.mine__st` | |

New in Sprint 1: segmented control `.seg` (+ `.seg--steps`), switch `.toggle` (checkbox `role="switch"`), bottom sheet
`.bsheet` (bottom on phones, centred from 640px; backdrop, Esc and close all cancel), skeleton `.skel` (`skelRows(n)`), error
state `.err-state` (`errState(title, text)`, amber: red stays for toxicity). States: hover and pressed use a tint and a short
shrink; focus is the 3px ring on every control; disabled is 50% with a not-allowed cursor; busy is `aria-busy="true"` with a
spinner (static under reduced motion). Theme: System / Light / Dark, `localStorage` `mushroom-guide:theme`, applied before paint.

## Motion

150–250ms with `--spring` for taps. Views fade with opacity only. Everything stops under `prefers-reduced-motion` and
in field mode. Warnings never animate.
