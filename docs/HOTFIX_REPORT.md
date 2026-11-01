# Production safety hotfix (2026-11-01)

Release: service worker `mushroom-guide-v45`. Scope: safety and high-priority content only. No redesign, no new
features, no change to how journal data is stored.

## P0 — *Paxillus involutus*

**Finding: the reported premise does not match the data.** A full search of `src/`, the built page and the tests shows:

| Name | Where it appears | Classification |
|---|---|---|
| *Paxillus involutus* / 卷边桩菇 / Brown roll rim | `data/book.py` toxic list, `data/safety.py`, toxic list on the page, photo | **Deadly Toxic / 致命**, since before round 7 |
| 卷缘齿菌 | was the display name of *Hydnum repandum* (hedgehog mushroom) | Edible, Verified (MykoWeb) |

*Paxillus involutus* was never in the edible catalogue, a recipe, the kitchen guide, 今日一菌, a season recommendation or a
habitat list. Every kitchen line that said "卷缘齿菌" was about *Hydnum repandum*.

The confusion itself is the hazard: the name 卷缘齿菌 was read as *Paxillus involutus* in two separate reports. So the hotfix:

1. Renames *Hydnum repandum* to **美味齿菌（羊蹄菇）** at the data source (`book.py`, `tags.py`, `guide.py`).
   "卷缘齿菌" survives only as a search alias and in the disambiguation notes.
2. Searching 卷缘齿菌 / 卷缘 / roll-rim now lists the toxic *Paxillus involutus* **first**, then the hedgehog mushroom.
3. Removes the hedgehog mushroom from the generic kitchen steps the hotfix listed:
   - the cleaning line;
   - the cutting line;
   - the basic 香芹蒜香 recipe;
   - the blanching row.
   Its own recipe (黄油百里香煎齿菌) stays, now named with the new name. Its edibility is sourced.
4. *Paxillus involutus* note: "不能吃，煮熟也不行", with the gills-vs-spines difference. No text anywhere says blanching
   makes any mushroom safe; the blanching row says "不能去毒".
5. Build check: no edible may belong to *Paxillus, Galerina, Gyromitra, Inocybe, Omphalotus, Pleurocybella, Lepiota,
   Hypholoma*; no Latin name may be both edible and toxic.
6. Test check: no recipe mentions Paxillus / 卷边桩菇 / 卷缘齿菌, and the kitchen guide contains none of these names.

If you want the hedgehog mushroom removed from the site entirely, that is a one-line data change. It was not done, because
its edibility is sourced.

## P0 — high-risk genera and unsourced edibility

- 26 edible-list species with only the book as support → **Not Evaluated**. Each one:
  - gets no cooking advice (the build replaces the kitchen note);
  - loses the 上品 badge;
  - is never recommended or used in recipes;
  - shows a 未评估 badge.
- *Cortinarius caperatus* stays Edible (MykoWeb), but is **no longer recommended**: its genus holds deadly orellanine species.
- Build rule: species of `HIGH_RISK` genera (Amanita, Cortinarius, Chlorophyllum, Macrolepiota, Lepiota, Galerina,
  Gyromitra, Paxillus, Inocybe) can never be recommended.
- No classification was changed from images or resemblance. Every Edible has an external reference (see
  `SAFETY_REAUDIT.md`).

## P1

- **Checklist:**
  - renamed 「食用前风险检查」, with the exact warning;
  - spore print, cut-open, smell and look-alike items now say they cannot prove safety;
  - the call item says some poisonings take hours to weeks.
- **Recipes:** the blanket "keep one or two raw samples of every dish" line is removed.
- **Emergency — keeping a sample:** the exact sample-keeping paragraph is added. Sources: Cascade Mycological Society
  (checked), Arizona Poison and Drug Information Center (search snippet only, page blocked from the build sandbox).
- **Emergency — timeline:**
  - The table now gives latency ranges per toxin from NAMA: amatoxins 6–24 h, *A. smithiana* 4–11 h, orellanine
    36 h–3 weeks, GI irritants 20 min–4 h.
  - The fixed points "约 36 小时 / 约 72 小时" are gone.
  - The page states that times vary and that an early improvement is not safety.
  - The species symptom texts were rewritten the same way.
- **Season data:**
  - Every region shows record count, coverage years and 样本不足 under 30. Per-region years were fetched from
    iNaturalist (`--region-years`).
  - The calendar shows source, region, coverage years, sample size and update date.
  - No probabilities anywhere.

## P2

- English view eyebrows (Explore, Learn, Emergency, Kitchen guide, ...) replaced with Chinese.
- Wikipedia is no longer cited on the emergency page (replaced by NAMA). It is never the only source for any species, and
  a build check now enforces that for toxic species.

## Changed files

`CLAUDE.md`, `public/index.html` (generated), `public/sw.js` (v45), `src/build_site.py`, `src/data/book.py`,
`src/data/guide.py`, `src/data/safety.py`, `src/data/seasonality.py` (regenerated), `src/data/tags.py`,
`src/fetch_seasonality.py`, `src/template.html`, `tests/test_site.py`, `docs/HOTFIX_REPORT.md`, `docs/SAFETY_REAUDIT.md`,
`docs/OPEN_ISSUES.md`, `docs/TEST_REPORT.md`.

## Tests

- `build_site.py`: passes with the new rules.
- `test_site.py`: **176 / 176** (8 new hotfix checks).
- axe-core WCAG 2.2 AA on the emergency page, the checklist, a species season block, the calendar and a Not Evaluated
  species: 375 and 1440 px, light and dark, 0 violations, no horizontal overflow.
- An old-format journal record (v1 fields only) is shown and left byte-identical.

## Not resolved — this is not a passed audit

See `OPEN_ISSUES.md`. In short:

- No mycologist has reviewed any classification.
- Two emergency sources could only be read as search snippets.
- BC DPIC numbers could not be re-checked from the sandbox.
- Real-device testing has not been done.

## Follow-up (v46, same day)

Review notes and what was found on the live page:

| Note | Live v45 | Done in v46 |
|---|---|---|
| 卷缘齿菌 still in the 阔叶林 list | No: the list said 美味齿菌（羊蹄菇）(*Hydnum repandum*). *Paxillus* was never there. A note naming 卷缘齿菌 most likely comes from a cached older copy | 美味齿菌 removed from the list as asked. Every habitat list now names only Verified + recommended species (the book's list also named 鸡油菌 *C. cibarius*, 皱盖罗鳞伞, 夏松露, 木耳, 高大环柄菇, 粗鳞青褶伞, 荷叶离褶伞 and others). Build check with exact names |
| Checklist still asks for a raw sample every time | Yes | Item removed (9 → 8 items); the checklist points to the emergency page for suspected poisoning |
| Season data lacks coverage, sample size, update date | Species charts and calendar had them; the "N 月常见" and 季节变化 lists did not | Both lists now state source, region, coverage years, sample size, update date and the 样本不足 cut-off |
| "Learn" English label | Not present in v45 (replaced) | No change needed; a test now covers the absence of English eyebrows |
| "你必须确定它无毒" | Yes (field guide) | Replaced: no method can guarantee a wild mushroom is safe; field guides and this app cannot be the only basis |
| "请有经验的人当面确认" implies safety | Yes, several places | Now says in-person confirmation reduces misidentification but cannot guarantee safety (home, field guide, checklist, species sheet, comparisons, today card, recipes note, learn quiz) |

Tests: 180 / 180.

axe-core:
- Changed views: no new issues.
- Field guide, when scrolled to the bottom: two pre-existing contrast reports on the calendar's sticky header, which is off screen at that point (top −264 px).
- The same cells pass when the calendar is on screen, so these look like an axe false positive. Not changed.
