# v53.2 — 拾菌 navigation visual polish

> Update (2026-11, owner's request): the category control now uses the shared `.seg` look of the comparison toggle
> (并排 / 逐个看): a raised light segment on a neutral track, bold text. The solid forest-green fill and the
> `--xnav-on` / `--xnav-on-text` tokens described below were removed. The sub-page tab strip is unchanged.

CSS changes plus a few small script changes to the 拾菌 navigation (`#explore-nav`). Routing, content, the information
architecture, the data model, local storage, the service worker and the safety content are unchanged. `public/sw.js` is
not touched, not even the `CACHE` version: the service worker loads pages network-first, and all the CSS and script are inline in
`index.html`, so installed phones get the new look the next time they open the page online.

## Primary navigation (找菌 / 野外指南 / 工具)

- Full-width segmented control with three equal segments on a neutral track (`--color-muted`) that has a faint inset
  shadow. From 768px wide the track is capped at 560px and left-aligned.
- Selected: solid forest green with white bold text, through two new semantic tokens:
  - light: `--xnav-on` `#3F6149` with `--xnav-on-text` white, 6.96:1;
  - dark: `#4A7556` with white, 5.29:1. It is lighter than the light-mode green so it stands off the forest-black page.
  - The selected segment has a small 1px lift. There is no glow.
- Not selected: muted text on the track; the text turns to the foreground colour on hover.
- 44px tall, 52px in outdoor mode.
- The rule is scoped to `#explore-nav`, so the shared `.seg__btn` look (settings, calendar, comparisons) is unchanged.

## Secondary navigation (sub-pages)

- A tab strip, not a filled control: transparent tabs, a 0.5px hairline under the whole strip, and a 3px forest
  indicator (`::after`) under the current tab. The current tab also gets bold weight and the foreground colour.
  Other tabs use readable muted text.
- 16px between tabs. Labels never wrap. When the tabs don't fit (320px, or a large outdoor-mode font) the strip becomes
  one horizontally scrollable row. The current tab is scrolled into view, clear of the edge fade. The edge that has more
  tabs behind it fades out, using a mask, only while the strip can scroll (`xnavEdges()`). Scrolling the strip only moves
  it sideways; the page never jumps.
- At 375px and 390px all four tabs fit, so nothing scrolls.

## State changes

- The segment background, tab text colour and indicator change over 180ms (`--xnav-dur`). The transitions use colour,
  opacity and transform; nothing changes layout.
- The new pane fades in, opacity only (`xp-in`). The 户外安全 pane never animates: emergency content does not move.
- The old pane is hidden in the same step the new one is shown, so old content is never visible during a switch.
- `prefers-reduced-motion: reduce` turns all of this off, and so does outdoor mode.
- Routing is unchanged: `#explore-<sub>` links and old `#guide-*` links still work, history entries are still added,
  back, forward and refresh restore the sub-page, and a new sub-page still scrolls to the navigation under the sticky
  header.

## Context and accessibility

- Every pane keeps its own heading. The navigation adds no second large title.
- Each tab has `aria-controls` pointing at its pane, and `aria-pressed` / `aria-current` are unchanged. A polite live
  region (`#xp-live`) announces 「分类 › 子页」 when the sub-page changes, so screen-reader users hear where they are.
- The selected state never relies on colour alone: the selected segment is filled and bold, and the current tab has an
  indicator bar and bold text.
- Focus rings: 3px ring tokens. On the tabs the ring is drawn inset so the scrolling strip cannot clip it.

## Tests

`tests/test_site.py`: the v53 AC-03 check now looks for the 3px `::after` indicator instead of a box shadow. New checks:

- AT-1/4 in light and dark: each category, when selected, is the one solid green segment, with text contrast ≥ 4.5:1.
- AT-2 in light and dark: every one of the 10 sub-pages shows a 3px indicator and bold text, with no fill.
- AT-3 at 320px: one scrollable row, labels on one line, the current tab in view, an edge fade, and no page overflow.
- AT-3 at 375px and 390px: every strip fits without scrolling.
- AT-5: the live announcement, `aria-controls`, and a single `aria-current` / `aria-pressed`.
- Pane fade: present, about 180ms, and none on the safety pane.
- AT-6: back and refresh.
- AT-7/8: outdoor mode keeps 52px targets, and reduced motion turns the animation off.

Results: `tests/test_site.py` **335 / 335 passed** (324 from v53 plus 11 new). The QA sweep covered 288 combinations:
the 10 拾菌 sub-pages, home and the emergency page × 320 / 375 / 390 / 768 / 1024 / 1440px × light / dark × outdoor mode
off / on. It found 0 axe WCAG 2.2 AA violations, no horizontal overflow and no uneven card rows. The only wrapping label
is 「我可能吃了不确定的菌」 on the home view at 320px, which was already the case before this change and is outside 拾菌.

Screenshots: `docs/v53_2/` has before/after pairs at 320, 375, 390 and 1440px, light and dark, including outdoor mode.

All checks ran in Playwright Chromium. No real iOS or Android device, Safari or Firefox was used. Mask images and
`scroll-padding-inline` are widely supported, but they were not checked on those browsers.
