# Open issues after round 7 and the 2026-11-01 safety hotfix

**Not a passed audit.** Items below are unresolved.

## Done and tested
- Safety data model for all 86 species, enforced by the build; per-species display on sheets and cards.
- *Amanita smithiana* → 致命; Paxillus / Hydnum disambiguation.
- Recipes and kitchen guide name species only; recipes limited to verified, recommended edibles; exact notice shown.
- Recommendations (今日一菌, N 月可以找, 季节变化) limited to verified, recommended edibles.
- Season transparency (coverage, total, latest record, update date, 数据不足, standard sentence); habitat caveat.
- Finder all-skipped state; journal import validation, duplicate and malformed reporting, no URL fetching; delete photo count.

## Modified but not verified on real devices
- Journal import/delete toasts on iOS Safari and Android Chrome.
- New safety block layout at in-between widths (tested 375 and 1440 px only).

## Hidden or flagged for lack of data
- 26 edible-list species are **Not Evaluated** (book-only source): no cooking advice, not recommended, not in recipes, 未评估 badge. Mostly European book species with no
  North American reference: *Agaricus arvensis, A. silvaticus, Amanita caesarea, A. crocea, A. fulva, Auricularia auricula-judae,
  Boletus badius, B. reticulatus, Calocybe gambosa, Cantharellus cibarius, Chlorophyllum rhacodes, Clitocybe geotropa,
  Gyroporus castaneus, Langermannia gigantea, Leccinum aurantiacum, L. versipelle, Lepista saeva, Macrolepiota procera,
  Mitrophora semilibera, Suillus bovinus, S. grevillei, S. luteus, Tuber aestivum, T. magnatum, T. melanosporum,
  Vascellum pratense*.
- Disputed: *Lyophyllum decastes* (edible, not recommended), *Verpa bohemica* and *Turbinellus floccosus* (treated as toxic).
- In Review toxic: *Amanita virosa* (treated as deadly), *Inocybe erubescens* (genus-level source only).
- 11 book species have no Pacific Northwest records at all (season chart shows "样本不足").
- *Cortinarius caperatus*: Edible per MykoWeb but not recommended (deadly genus).
- The season calendar still lists not-recommended species (it is a record of when they appear, and each opens a sheet with
  its warnings). Decide whether to filter it.

## Needs a mycologist
- Every classification and every look-alike list. No expert has reviewed the site.
- Whether the 26 In Review species should stay in the catalogue at all for PNW readers.
- Regional look-alikes (e.g. *Amanita* in the caesarea group, *Chlorophyllum* vs *C. molybdites* in the PNW).
- Symptom texts (taken from NAMA syndrome descriptions, applied per genus).

## Needs real-device testing
- PWA install and update to `mushroom-guide-v44` on iOS and Android.
- GPS denial, camera capture, storage quota/eviction in the journal.
- Field mode in sunlight.
- Re-verify BC DPIC numbers (dpic.org unreachable from the build sandbox).
- Open the Arizona Poison Center PDF and confirm the sample-keeping wording (only seen as a search snippet).
