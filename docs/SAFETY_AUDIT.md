# Safety audit, round 7 (2026-11-01)

Scope: all 64 edible and 22 toxic species, every recipe, the kitchen guide, the finder, the season data and the finds journal.
Audit by the site editor against the external references below. **No mycologist has reviewed this site.** "Verified" in
this document means "an external reference states the same edibility or toxicity", nothing more.

## 1. The reported "卷缘齿菌 Paxillus involutus" problem

The report paired the wrong names. In this project:

| Chinese name | Latin name | Classification on the site | Since |
|---|---|---|---|
| 卷边桩菇 | *Paxillus involutus* | Toxic, **致命** (toxic list, never in edibles, recipes or recommendations) | before round 7 |
| 卷缘齿菌（羊蹄菇） | *Hydnum repandum* | Edible (hedgehog mushroom), MykoWeb confirms | before round 7 |

So no edible entry showed *Paxillus involutus*. The two names do look alike, though, so round 7:

- gave *Paxillus involutus* a full safety record: Deadly Toxic, symptoms (immune haemolytic anaemia after years of eating,
  per MykoWeb and NAMA), sources and a note that it is not 卷缘齿菌;
- added a note to *Hydnum repandum* that it is not 卷边桩菇 (spines under the cap vs gills);
- added a build check: no edible species may belong to *Paxillus, Galerina, Gyromitra, Inocybe, Omphalotus,
  Pleurocybella, Lepiota* or *Hypholoma*, and no Latin name may be both edible and toxic.

## 2. Findings and fixes

| # | Finding | Severity | Fix |
|---|---|---|---|
| 1 | *Amanita smithiana* was labelled 有毒; MykoWeb says "deadly poisonous" (kidney failure) | P0 | Upgraded to 致命 |
| 2 | Recipes said "任何牛肝菌" and used "杂菌 400 g" (any mushroom) | P0 | Named species only; build fails on 杂菌/任何 in recipe fields |
| 3 | Kitchen base recipe "香芹蒜香" mentioned 鹅膏类 as a cookable group and used "可食菌 500 g" | P0 | Names 美味牛肝菌 / 太平洋金鸡油菌 / 卷缘齿菌 only |
| 4 | Recipes could use a species with only one supporting source | P0 | Recipes may use only Edible + Verified + recommended species (build fails otherwise) |
| 5 | 今日一菌 and "N 月可以找" could feature species without outside confirmation (e.g. *Amanita fulva*, *A. caesarea*) | P0 | Only `recommendable()` species are featured |
| 6 | Toxic entries lacked symptoms; Paxillus lacked sources | P0 | Every toxic species has symptoms and latency (NAMA) |
| 7 | Review status was one generic sentence | P1 | Per-species status, date and basis link on every sheet; card badge for unverified ones |
| 8 | Season charts did not show coverage, last record or small regional samples | P1 | Added; "数据不足" below 30 records; standard history-not-forecast sentence |
| 9 | Habitat / associated trees could read as identification evidence | P1 | Caveat on species sheets and the field guide |
| 10 | Journal import could merge malformed records and fetch any URL in a crafted backup | P1 | Records are validated field by field; only embedded images are accepted; failures change nothing |
| 11 | Journal delete did not say photos go too, and deleted photos even if saving failed | P1 | Confirm and toast name the photo count; photos removed only after the record is saved |

## 3. Status after the audit

| Edibility | Verified | In Review | Disputed |
|---|---|---|---|
| Edible | 37 | 26 | 1 (*Lyophyllum decastes*) |
| Toxic | 8 | 1 (*Inocybe erubescens*: genus-level source only) | 2 (*Verpa bohemica*, *Turbinellus floccosus*: treated as toxic) |
| Deadly Toxic | 10 | 1 (*Amanita virosa*: European species, treated as deadly) | 0 |

The 26 In Review edibles are mostly European book species with no North American reference found (truffles, *Calocybe
gambosa*, *Amanita caesarea*, ...). They stay in the catalogue with an "待核实" badge but are never recommended or used in recipes.
Disputed species are always handled on the cautious side.

## 4. What this audit cannot do

- It is not a mycological review. Every classification needs a qualified person to check it (see `OPEN_ISSUES.md`).
- Regional variation (a species safe in one region, a look-alike in another) is only covered where a source says so.
