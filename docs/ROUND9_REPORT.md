# Round 9 — UI/UX redesign

Release: service worker `mushroom-guide-v48`. Screenshots: `docs/round9/` (375px light, 1440px dark).

## What changed

| Area | Delivered | Status |
|---|---|---|
| Design system | PRD palette as tokens (Text Secondary darkened for AA), type scale tokens, system-serif display titles, 4px spacing, calmer background, showcase page `design-system.html`, `docs/DESIGN_SYSTEM.md` | Done, tested |
| Navigation | Three tabs unchanged; each tab now keeps its own scroll position; section chips renamed to the PRD's sub-navigation (拾菌: 本月探索 / 季节情报 / 产季日历 / 生境探索 / 采集指南 / 户外安全 / 离线; 菌记: 新记录 / 地图 / 我的记录 / 我的物种 / 年度报告 / 照片 / 去过的地点 / 数据管理), one swipeable row on phones | Done, tested |
| Home | Hero 「走进森林，发现自然。」 with search (species, English and Latin names, **glossary terms**, recent searches kept on this device); two main actions (识别一朵菌, 探索森林); safety note; 「这个季节，森林里有什么？」 with region chips and data notes; 我的菌记 preview (last 3, or an empty state with 记下第一次发现); other entries, deadly look-alikes, 今日一菌 below | Done, tested |
| Identify | Round 8's explanations (matched / kept-despite / unconfirmed, missing-information alarm, comparison links) stay | Unchanged this round |
| Explore | 生境探索 cards (5 habitats, trees, recommended species with photo and season, folding) | Done, tested |
| Journal | New record in three steps (照片与物种 → 地点与环境 → 备注与保存), save from any step, GPS optional | Done, tested |
| Accessibility | axe-core WCAG 2.2 AA on all 10 views, 375/1440, light/dark: 0 violations (fixed emergency call-button label contrast) | Done |

## Kept unchanged

Data, backups, IndexedDB, offline caching, finder rules, safety boundaries, recipes, learning, the 3D model, field mode
and every round 1–8 feature. No feature was removed.

## Not done or only in part

- **Finder step photos.** Real feature photos per answer were not added: each would need a licensed, correctly identified photo. The 3D model's "在模型上看" stays.
- **Species page reorder.** The PRD's ten sections (cap, gills, stem, base …) were not built: the data is tagged by five features, not by those parts. Making them would mean writing new, sourced descriptions.
- **Recipes and Learn.** No favourites, recipe search or redesign of these pages this round.
- **Journal views.** No map/list segmented toggle; the map and the timeline are both on the page, reached by the section chips.
- **Loading states.** Skeleton screens were not built; loading states are short text.
- **Display serif.** The serif title face shows only where the system has a CJK serif (Apple devices). Headless Chromium in the test environment fell back to the sans.
- **Device tests.** Not run on any real device (iPhone Safari, iPhone PWA, Android Chrome, desktop Safari). Only headless Chromium at 375/390/768/1024/1440 px was used. These are **not verified**.

## Tests

- `python3 tests/test_site.py`: **217 / 217**. 11 new checks cover:
  - home hero, actions, season and journal preview;
  - glossary search and recent searches;
  - per-tab scroll memory;
  - habitat cards (recommended species only);
  - the three-step form, with save from step 1 without GPS.
- The class-collision check now skips Leaflet's own markup.
- Offline regression is unchanged and passing:
  - offline reload, catalog and photos;
  - offline record with photo;
  - journal surviving a cache wipe.
