# Sprint 3 — Field Experience (v51)

Static HTML/CSS/JS, routing, IndexedDB, localStorage and the service worker are unchanged in kind. No framework, backend or
dependency was added. Everything below was tested in headless Chromium; no real device was used.

## Phase 0 (v50.1 clean-up)

- **厨房指南:** 「最好的幼嫩个体留给沙拉…」 → 「留给主菜，或煮熟后冷冻…不论哪种做法，野生菌都要彻底煮熟」. The build now bans 留给沙拉 / 做沙拉 / 凉拌 / 生拌野.
- **术语「菌根」:** 「菌根菌只在相应树木附近出现」 → 通常在相应树种附近; there may be more than one host tree; the mushroom may grow some distance from the trunk; host trees narrow the search but never prove a species.
- **继续探索:** confirmed removed in v50. 最近看过 stays.
- **Tab memory:**
  - now also survives a refresh (`sessionStorage`, this tab only);
  - a stored view is used only if it belongs to that tab;
  - back and the settings deep link (`#data-center`) were re-tested.
- **Theme × outdoor mode:** checked in all combinations (see tests).

## P1: Finder

- **Next question chosen from the answers so far.**
  - If a deadly species with a volva is still a candidate, the next question is the stem base, with the reason shown
    (「候选里还有带菌托的致命鹅膏，所以先看柄基」).
  - Otherwise the question that on average leaves the fewest candidates (「这一题最能缩小剩下的 N 个候选」).
  - This only orders questions; no probabilities or scores are shown.
- **Navigation:**
  - The header shows how many questions are left (「还剩 N 题」), not a fixed "5 / 5".
  - Skipped questions are remembered and not asked again.
  - 上一题 follows the order actually asked, and the progress row still opens any question.
- **Progress is kept:**
  - answers stay on the device for 6 hours (`localStorage` `mushroom-guide:finder`), so leaving, switching tabs or a reload never loses them;
  - 重新开始 needs a second tap when there are answers.
- **No candidates at all:** the finder now says so plainly. The site covers only 86 species, so an empty result does not mean the mushroom is safe.
- **Wording:** no 识别成功, 安全 or 可以食用 in results. 「这些在本站被列为可食种」 became 「这些种在本站的食用菌图鉴里（其中有的未评估）」.
- **Not done:** real, sourced photos per answer. Each would need a licensed, correctly identified picture of that feature.

## P1: Species pages (edible and toxic share one hierarchy)

1. Photo, names, risk class (toxic: level; edible: grade and review status).
2. 快速鉴别 / 关键特征. Toxic pages now get the same feature table (cap underside, spore print, ring, volva, substrate).
3. 易混毒菌 / 易混与区别.
4. **新: 鉴别限制.** Built only from data the page already has:
   - photos and lists cannot confirm a species;
   - variation with age and weather;
   - the volva may be buried;
   - a ring may have fallen off;
   - the spore print is unclear;
   - few local records;
   - not evaluated, or sources disagree;
   - for toxic pages: no single feature rules it out.
5. 生态与季节 (and 厨房 on edible pages).
6. 资料来源, with photo credit and licence.

**Not done:** labelling cap, gills and stem on the photos. That needs per-photo coordinates, which we do not have. Zoom is unchanged.

## P1: Comparisons (9 groups)

- **One dimension order everywhere:**
  - 菌盖 → 菌褶/菌孔 → 菌柄 → 柄基 → 变色/气味 → 孢子印 → 生境 → 其他;
  - rows the authors marked as key differences first, tagged 关键;
  - 结论 last.

  Row texts are unchanged.
- **Warning on every group:** individual variation, young and old specimens, and that a feature you cannot see (a buried volva) is not "absent". No single difference rules out a deadly species.
- **Layout:** the side-by-side and one-at-a-time views stay. Every column name links to the full species page.

## P2: Outdoor mode

- **Kept:** search, the two main actions, the journal preview, safety and the emergency button.
- **Now also hidden:** the seasonal extras (home season discovery, 季节情报).
- **Theme:** the user's theme stays untouched (tested).
- **Exit:** the header sun or the settings switch.
- **Targets:** 52px, as before.

## P2: Offline and data

New offline test (one online visit, then offline):
- the page starts;
- the photo count in 离线使用 equals what is really in the cache, with no false "cached";
- a photo never downloaded shows as a grey frame;
- the finder works;
- the journal can add, edit, export and preview an import.

Earlier tests still pass:
- a record with a photo written offline;
- records surviving a full cache wipe;
- the old-format data migration.

## Files changed

- Source: `src/template.html`, `src/build_site.py`, `src/data/guide.py`
- Tests: `tests/test_site.py`
- Generated and release: `public/index.html`, `public/design-system.html`, `public/sw.js` (v51)
- Docs: `docs/SPRINT3_REPORT.md`, `docs/sprint3/*.webp`, `CLAUDE.md`

## Tests

- `tests/test_site.py`: **266 / 266**. That is 247 before plus 19 new.
- Four older finder checks were adapted to the dynamic order: questions opened by their progress dot, a two-tap reset, and the progress dot instead of "1 / 5".
- **axe-core WCAG 2.2 AA:**
  - 120 view combinations (10 views × 375/768/1440 × light/dark × outdoor mode);
  - 24 checks on open species and toxic sheets and the comparisons;
  - the finder after an answer in 4 combinations.

  All 0 violations, with no horizontal overflow.

## Not done / known issues

- **Feature photos:** none per finder answer, and no part labels on species photos (see above).
- **Real devices:** iPhone Safari, the iPhone Home-Screen app, Android Chrome and desktop Safari/Firefox were not tested.
- **Offline gaps:** the very first visit while offline cannot work, because nothing is cached yet. Storage eviction by the browser was not tested.
- **Tab memory:** kept only for the current browser tab (`sessionStorage`). A new tab starts fresh.
- **Comparison order:** it relies on the authors' bold marks; groups without bold rows keep the dimension order only.
