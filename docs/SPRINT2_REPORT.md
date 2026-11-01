# Sprint 2 (v50)

Based on v49. No feature was rewritten. Theme, outdoor mode, offline caching, IndexedDB data and safety rules are unchanged
in behaviour except where listed. Every item below was tested in headless Chromium. No real device was used.

## P0

**Theme (kept from Sprint 1, one system)**
- **First paint:** the pre-paint script `themePaint()` now also sets the browser-bar colour, so there is no flash.
  - Before, the bar started dark green and changed after load.
  - `themeSet()` reuses `themePaint()`; nothing is duplicated.
- **Following the system:** while 跟随系统 is selected, a light/dark change of the phone now also updates the browser bar.
  The CSS already followed.
- **3D model:** it now redraws in the right colours when a theme is picked by hand. Before, it only reacted to system changes.
- **Tests:**
  - theme and bar colour are set before `<body>` exists;
  - live system switch;
  - a manual choice beats the system;
  - all theme controls agree;
  - the choice survives a reload.

**Safety copy audit.** Every variant of the core eating advice was collected from the built page and compared.

Fixed at the source:

| Where | Was | Now |
|---|---|---|
| 厨房指南 must-cook list | 羊肚菌、**鹅膏类（赭盖鹅膏、橙黄鹅膏）**、紫丁香蘑、**粉紫香蘑**… must be cooked | 羊肚菌、紫丁香蘑、褐疣柄牛肝菌、蜜环菌; all wild mushrooms cooked; **鹅膏属本站没有评估，不提供吃法** (the amanitas and 粉紫香蘑 are 未评估 since the hotfix) |
| 猴头菇 note | 第一次吃**少量**、彻底煮熟 (trial portion, banned) | 要彻底煮熟；吃之前请有经验的人当面确认 |
| 虾味红菇 kitchen | 第一次吃**先少量** (banned) | 要彻底煮熟，吃后不舒服马上联系毒物中心 |
| 采摘 | 有疑问的扔掉，**或再核对一次** | 有疑问的扔掉 |

The build now also bans 「第一次吃少量」「先少量」「少量试」「试吃」「或再核对一次」「鹅膏类（」.
The other messages were checked and agree across pages:
- 有任何疑问，就不要吃;
- 当面确认能减少认错，但不能保证安全;
- 彻底煮熟;
- cooking, freezing or drying cannot make a toxic mushroom safe.

## P1

- **Settings entry (header gear, bottom sheet):**
  - 外观 (the same `data-theme-pick` buttons and `themeSet()`);
  - 户外模式 switch (the same `fieldSet()` as the header sun);
  - links to 离线使用, 数据管理与备份 and 中毒急救.

  It keeps no state of its own. The 数据管理 link needed a new route (`#data-center`); it did not work before.
- **Tab memory:**
  - leaving a tab and coming back restores its last page and that page's scroll position;
  - tapping the current tab again opens its first page at the top;
  - browser back is unchanged.

  This matters most for 识菌, which has seven pages.
- **Home:** the 继续探索 links that repeated the tab bar are removed. The safety note, emergency entry, deadly look-alikes and 今日一菌 stay.
- **Finder:**
  - The questions now come before the results and the 3D model, so on a 375px phone the first question starts about 610px down (it was about 830px).
  - The 3D model has a 回到问题 button; 在模型上看 still scrolls to it.
  - The 查看候选 bar used to stick over the progress row. It is now a pill floating above the tab bar, hidden while the results are on screen.
- **Species sheet:**
  - The section jumps come right after the quick facts, inside the first screen on a 375px phone (about 770px; was about 1020px).
  - The safety summary is one row: grade, review status, and "编辑核对，非真菌学专家审核".
  - The note (for example the 卷边桩菇 disambiguation) and the warning line stay visible. Only the review explanation, date and basis link fold under 资料审核说明.
  - Latin and English names share one line.

## P2

- **Offline:**
  - the 离线 pill now links to 离线使用;
  - the offline toast says what still works (catalog, finder, journal) and what doesn't (photos not downloaded, external links).
- **Mobile:** every bottom sheet (settings, import, wipe) can be dragged down from its grabber to close, which counts as cancel.
- **Home visual polish:** only the removal above. No other visual change this sprint.

## Files changed

- Source: `src/template.html`, `src/build_site.py`, `src/data/north_america.py`
- Tests: `tests/test_site.py` (17 new; 1 updated for tab memory)
- Generated and release: `public/index.html`, `public/design-system.html`, `public/sw.js` (v50)
- Docs: `docs/SPRINT2_REPORT.md`, `docs/sprint2/*.webp` (before/after: finder, sheet, kitchen; new settings sheet), `CLAUDE.md`

## Tests

- `tests/test_site.py`: **247 / 247**. That is 230 before plus 17 new.
- The back-button check was rewritten because the 识菌 tab now reopens its last page by design.
- Offline regression passes:
  - offline reload, catalog and photos;
  - writing a record with a photo offline;
  - the record and photo surviving a full cache wipe.
- **axe-core WCAG 2.2 AA:**
  - 10 views × 375/768/1440 × light/dark × outdoor mode = 120 combinations, 0 violations;
  - the open settings sheet in 12 combinations, 0 violations;
  - no horizontal overflow, equal card widths in every grid.
- **Wrapping:** the only wrapping label is still the long download button in outdoor mode at 375px.

## Not done

- **Real-device theme check.** iOS Safari, the iOS Home-Screen app, Android Chrome and desktop Safari/Firefox were not tested. Only Chromium is installed here, with no WebKit or Firefox engine. The status-bar colour of an installed iOS app depends on `apple-mobile-web-app-status-bar-style`, which was not changed.
- **Home visual polish** beyond removing the duplicate links.
- **Finder step photos.** Each needs a licensed, correctly identified image.

## Known issues

- On iOS, Safari may ignore `theme-color` in some modes; this has not been verified.
- At 320px the journal step labels and the header are tight (they fit, measured). The finder hero and notice still take about 450px above the first question.
- Tab memory is kept in memory only; a reload starts each tab from its first page.
