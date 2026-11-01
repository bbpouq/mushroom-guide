# Test report, round 7 (2026-11-01)

## Automated

| Check | Result |
|---|---|
| `python3 src/build_site.py` (data validation, safety rules, banned phrases, recipe species, source URLs, resource files, sw.js shell) | pass |
| `python3 tests/test_site.py` (Playwright, Chromium) | **168 / 168 pass** (153 before, 15 new) |
| axe-core WCAG 2.2 AA: species sheet, toxic sheet, disputed species sheet, species list, recipes, journal, finder; 375 and 1440 px; light and dark | 0 violations |

New end-to-end checks (round 7):
1. Every species has a valid safety record; recipes use only verified, recommended edibles.
2. *Paxillus involutus* is Deadly Toxic / 致命; *Hydnum repandum* carries the name warning.
3. 今日一菌 is a verified, recommended edible on 60 consecutive days.
4. Every unverified species card shows its status badge.
5. Recipes view shows the exact safety notice.
6. Species sheet shows edibility, review status, season coverage, latest record and the history-not-forecast sentence.
7. Toxic sheet shows symptoms and the name warning.
8. A species with < 30 records says 数据不足.
9. Finder: all five questions skipped → no candidates, explanation shown.
10. Finder: contradicting answers (pores + volva) → no errors, toxic species first.
11. Journal: broken JSON and a foreign JSON file leave stored records byte-identical.
12. Journal: duplicate and malformed records are reported and not imported.
13. Journal: a backup with a web URL as a photo never makes the page request it.
14. Journal: delete confirmation shows the photo count.
15. Journal: delete toast names the removed photos and the record is gone.

Existing checks also cover GPS (granted, fuzzy), export without coordinates, JSON backup round trip, offline mode, the
sandboxed preview, layout at 375/768/1024/1440 px, class collisions and keyboard access.

## Manual (screenshots in a headless browser)

Species and toxic sheets, species cards and season block at 375 px dark and 1440 px light/dark: layout, contrast and wrapping
checked; no overflow.

## Not tested

- Real phones (iOS Safari, Android Chrome): PWA install, GPS denial dialogs, camera input, storage eviction.
- GPS permission denied is handled in code (toast, place name still saved) but the browser prompt itself is not automated.
- Lighthouse was not re-run this round (page grew 552 → 556 KB; no new requests).
- BC DPIC numbers: dpic.org was not reachable from the build sandbox; numbers unchanged from the previous verified round.
