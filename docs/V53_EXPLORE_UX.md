# v53 — 拾菌 Explore UX polish

Scope: the PRD "MycoTrail v53 · Explore UX Polish". It reworks the existing 拾菌 view in place. The routing
(`parse()` / `apply()` / `show()`, `#explore-<sub>`), the v52 navigation (`XP`, `xpShow()`), settings, theme, outdoor
mode, the offline caches and the journal data model are unchanged. Service worker `CACHE` is now `mushroom-guide-v53`.
`MEDIA` is unchanged because no photo files were replaced.

## Fixed v52 regressions

- **做孢子印 was missing.** When v52 split the sections, the spore-print panel was matched by text that also appears
  in the rules, so it was dropped. It is restored as a fold under 采集与观察 (`#spore-print`), with one added line:
  a matching spore colour rules out only some toxic species and does not prove a mushroom safe.
- **四条守则 appeared twice** (采集守则 and 采集与观察). The rules now live only in 采集守则. 采集与观察 links to them.

## P1-A: header and first screen

- Removed the header photo, the eyebrow and the long lead. The view now has the title 拾菌 and one short line that
  ends with 「不是实时出菇预测」. The `explore` key stays in `fetch_photos.HEROES`, but the template no longer has
  the marker.
- Removed every `panel__num` chapter number (01–06) from 拾菌.
- The navigation is not sticky. The current category is a raised segment and the current sub-page has an underline
  and a bold label, so the state is shown by shape and weight, not by colour alone.
- `#explore` still opens 找菌 › 本月探索.
- The three category buttons are now a full 44 px tall (`.xnav__cats .seg__btn`). Before, they were 36 px with a 44 px hit area.
- The phone tab bar's inactive labels now use the foreground colour. At 320 px the muted grey over a photo behind the
  glass bar measured 3.53:1 in axe. That already happened in v52; it is fixed here.

## P1-B: 找菌

| Sub-page | Before (v52) | v53 |
|---|---|---|
| 本月探索 | Month strip, 「看全部」, 季节变化 | Month strip; title 「N 月在整个 PNW 常见」; empty state; three labelled next steps: 「在图鉴里看 N 月的全部种类」, 季节情报, 生境探索 |
| 季节情报 | Month chips plus up to 8 species cards with habitat and look-alikes (copied the species list) | Month chips (the strip scrolls to the chosen month); 「N 月 → N+1 月：记录怎么变」 (the old 季节变化 block, now following the chosen month); 三地对比 table for that month (level and count per region, 样本不足 under 30 records, selected region highlighted); a note on sampling bias and timeliness |
| 产季日历 | Mode, month and search in one row; state lost on refresh | Mode control, then search and month (the month picker has a visible label and only shows in 按月份看); a status line such as 「3 月 · 整个 PNW · 搜索“鸡油”：2 种」; an empty search says what to try and that not listed does not mean safe |
| 生境探索 | Numbered panel; 「附近出现其他（哪怕不能吃的）菌，往往是好兆头」 | Plain heading; compact folding cards (unchanged build output, `habitat_cards()`); intro rewritten without the "good sign" inference |

- **「三地合计」 → 「整个 PNW」** on every all-regions chip (home and 拾菌). The data is still BC + WA + OR combined.
  The chip's `title` says so, and data lines still name the three regions.
- **Persistence.** The region was already kept in `localStorage` `mushroom-guide:region`. The intel month and the
  calendar mode, month and search are now kept for the tab session in `sessionStorage` `mushroom-guide:xpstate`
  (`xs`, `xsSave()`). They survive a refresh, back/forward and switching tabs.
- **Photos.** The thumbnails are the existing licensed example photos (author and licence are shown in the species sheet). A card
  without a photo still shows its text name.

## P1-C: 野外指南

- **采集守则**: one source. Rule 2 now reads 「先查当地规定，不确定就只看不采」: the land manager of each place decides,
  rules can change every year, check their latest rules, protected areas are look-and-photograph only, and the site does
  not judge whether any place allows picking.
- **装备与准备**: 出发前清单 with check marks for offline map, power (charged phone and power bank), headlamp, weather
  forecast, trip plan and a whistle or satellite messenger. The source is AdventureSmart. 采菌用具 and 什么时候找 stay as
  short lists.
- **采集与观察**: numbered steps 观察 → 拍照 (one photo per part: cap, gills, stem and base, habitat) → 记录 (菌记) →
  依法采集（若允许） (「不允许或不确定，就只看、只拍、只记」), then the spore-print fold.
- **户外安全**: two large buttons come first and sit outside any fold: 911 (`tel:911`) and 中毒急救 (`#emergency`). The
  S.T.O.P. panel and its sources follow. The emergency page itself is unchanged.

## P1-D: 工具

- **离线下载**: the heading, then a one-line summary such as 「文字资料已可离线；缩略图部分完成（6 / 93）；高清图未下载（0 / 85）。个人菌记单独存在这台设备上，不需要下载。」.
  The summary starts with 「现在离线。」 when the device is offline. Below it is one row each for 网络, 文字资料, 缩略图,
  高清图, 3D 模型, 个人菌记 and 外部链接. Each photo and 3D row has a text state pill from `ostate()`: 未下载, 下载中,
  下载失败, 部分完成 or 已完成. The pill is not colour alone, and the failure colour is amber, not red. A status line under the
  buttons (`#off-dl`, `role=status`) shows progress and the outcome. The 个人菌记 row counts records and photos and says
  they are not a download and are deleted with site data, with a link to 导出备份. The download buttons come after the
  status.
- **户外模式**: a `.toggle` switch (`role=switch`, `data-field-switch`) with the state written next to it (已打开 / 已关闭).
  It is bound to the same `fieldSet()` as the header sun button and the settings switch. It is independent of the theme.
  The 外观 button opens the existing settings sheet.

## Safety copy

- Rewrote 「附近出现其他（哪怕不能吃的）菌，往往是好兆头」 as: 「看到其他菌，只说明最近的湿度和温度可能适合出菇，不代表某一种菌就在附近。」
- Mycorrhiza wording: the habitat intro says 「常长在相应树木附近，但不一定紧挨树干」. The glossary wording from v51 is unchanged.
- Salad and raw wording: none on the page. The build's banned list already covered it.
- Sampling bias and timeliness are stated in 季节情报: the counts show when people photograph and upload, are biased
  toward cities, trails, weekends and popular species, keep rising with more users, are refreshed monthly, and cannot
  reflect this year's weather.
- The build now also fails on 「好兆头」「一定能找到」「必定出现」「肯定有菌」「只在相应树」.

## Tests

`tests/test_site.py` keeps the v52 checks. Three were rewritten for the new markup:
- the 小图 text became a count line;
- the intel test now checks the three-region table;
- the outdoor test now looks for a switch instead of a button.

New v53 checks:
- AC-01 and AC-02: direct links with a per-frame record, so no other sub-page is ever painted.
- Compact header; navigation not sticky; 整个 PNW; the 本月探索 label and its target.
- AC-03: all 10 sub-pages at 320, 375, 390, 768 and 1024 px. Each width checks one pane, no overflow, 44 px targets and a selected state that does not rely on colour.
- AC-05: no numbering; one rules source; collecting order; spore print; permit wording; checklist; emergency first.
- Habitat cards.
- Sampling-bias note.
- AC-04 and AC-08: calendar and intel state across refresh, tab switches, back and forward; empty calendar search.
- AC-07: outdoor switch × theme × settings.
- Keyboard Enter and focus ring.
- AC-10: banned certainty phrases.
- AC-06 offline states:
  - unit checks of all five states;
  - separate rows;
  - first visit;
  - a failed download (photo requests aborted);
  - a partial cache;
  - the offline summary.
- AC-09: the journal survives navigation, downloads and a reload.
- Outdoor mode on in light and dark at 375 px.

Results (this release, Playwright Chromium): `tests/test_site.py` **324 / 324 passed** (the 285 v52 checks, 3 of them rewritten for the new markup,
plus 39 new v53 checks). A separate QA sweep covered 288 combinations:
- 12 views: the 10 拾菌 sub-pages, home and the emergency page;
- 6 widths: 320, 375, 390, 768, 1024 and 1440 px;
- light and dark;
- outdoor mode off and on.

It found 0 axe WCAG 2.2 AA violations, no horizontal overflow and no uneven card rows. One label still wraps on the home view at 320 px
(「我可能吃了不确定的菌」); that is outside 拾菌 and also happens in v52.

All of these ran in Playwright Chromium only. They have not been run on real iOS or Android devices, in Safari or in Firefox.

## Known limits

- The AdventureSmart site could not be fetched from the build environment, so the checklist items were not re-checked
  against the live page this round. They match what the S.T.O.P. panel already cited: trip plan, headlamp, warm clothing,
  whistle, charged phone, offline maps. Weather and a power bank are general trip-planning advice.
- The download size estimate now counts only header photos the page shows (the explore photo is no longer one).
- The 三地对比 table counts records, and records follow uploaders. The note says so, but readers may still read high
  numbers as abundance.
