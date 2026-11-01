# Changes, round 7 "Safety & Reliability Release" (2026-11-01)

Data
- New `src/data/safety.py`: edibility, review status, date, basis, refs, symptoms, notes for all 86 species.
- *Amanita smithiana*: 有毒 → 致命.
- *Paxillus involutus* / *Hydnum repandum*: disambiguation notes, symptoms and sources.
- Recipes and kitchen guide: no "任何" / "杂菌"; named species only; base recipe no longer mentions amanitas.
- `seasonality.py`: latest research-grade observation date per species (`fetch_seasonality.py --last-only`).

Site
- Species and toxic sheets: safety block (分级, 资料审核 with status, date and basis link, 中毒表现, 注意) and the line
  "可食只说明这个物种本身…".
- Cards of unverified species show 待核实 / 资料有分歧.
- 今日一菌, "N 月可以找" and 季节变化 feature only verified, recommended species.
- Recipes view and species kitchen section carry the exact notice
  「本食谱仅适用于已经由可靠方式确认身份的食用菌。烹饪不能使有毒蘑菇变得安全。不要仅凭本应用的识别结果决定是否食用。」
- Season charts: source, coverage years, total, latest record, update date; 数据不足 for totals or regions under 30; the
  standard sentence 「历史观察数据反映过去记录的分布和季节性…」 on charts, data notes and the explorer.
- Habitat caveat on species sheets and in the field guide.
- Finder: skipping all five questions says nothing could be narrowed (no list).
- Journal: validated import (bad JSON, foreign files, newer versions, malformed records and duplicates are reported; existing
  records never change on failure; photos only from embedded images); delete confirm and toast give the photo count;
  photos are removed only after the record is.

Build and tests
- Build fails on: missing/invalid safety record, edible in a toxic genus, recipes with unverified species, 杂菌/任何 in
  recipes, non-https sources, sw.js pre-caching a missing file.
- 15 new end-to-end checks (153 → 168).
- Service worker `CACHE` → `mushroom-guide-v44`.
