# Species feature audit (2026-11)

Scope: the PRD 「全收录物种描述与特征识别一致性审计」. It started from one real misreading: 林中鸡's very fine pores, chosen
as 「其他：…橙色硬壳」, made the species disappear from the finder. The audit then checked every species' finder tags, its
own text and the filtering logic.

**This is not a mycologist's review.** Each species is in one of four states, listed per species in
`reports/species_feature_audit.csv`:

| State | Count | Meaning |
|---|---|---|
| fixed | 22 | A tag was changed on evidence: an outside page, or the site's own sourced text, cited per row |
| checked | 8 | Checked by hand against an outside page; the tags agree |
| cross-checked automatically | 36 | `src/xref_species.py` compared spore print, habitat, ring and volva with one MushroomExpert / MykoWeb page; no disagreement |
| not checked | 20 | No outside page under these names. These are mostly book-only European species; they are listed below for an expert |

No row claims two independent sources plus expert sign-off, so the site still says "资料整理，非真菌学专家审核".

## Confirmed code defects (P0) and what changed

| Misreading | Before (v55) | After |
|---|---|---|
| 林中鸡 answered as 「其他形态」 or 「近光滑」 (very fine pores, 2–4 per mm) | 林中鸡 dropped | Listed, marked 冲突 with the reason |
| A jack-o'-lantern's thick gills answered as chanterelle ridges | 发光类脐菇 (toxic) dropped | Listed |
| An amanita egg answered as a puffball (其他形态) | All deadly amanitas dropped | Listed |
| 有菌托 answered for *A. smithiana* (veil remnants on the bulb) | 史密斯鹅膏 (deadly) dropped | Listed |
| Gills + wood (wood-chip mulch) + white spore print | 致命小环柄菇 (deadly) dropped | Listed |
| Galerina whose ring has gone, looking terrestrial | Dropped under 「林地」 | Listed |
| Morel on bark mulch answered 「木头上」 | 羊肚菌 dropped | Listed |

Before/after phone screenshots in light and dark: `docs/species_audit/`.

## Matching rules (`fEval()` in `src/template.html`)

One function decides both whether a species stays listed and what its card says:
- **吻合**: the answer agrees.
- **冲突**: the answer disagrees, but a careful observer could give it; the species stays listed and the card shows why.
- **未知**: the field was not observed, or does not apply.

The rules:
- **Unknown answers** (还没看 / 拿不准 / 看不到) never narrow the list.
- **吻合** counts only answered, agreeing fields.
- **Fertile surface:** an exact match is 吻合.
  - Generic mix-up: blunt ridges ↔ true gills (`HYM_NEAR`).
  - Species-specific mix-ups live in the data (`hymAlt` + `hymWhy`): very fine pores, an amanita egg, a jack-o'-lantern.
  - Anything else excludes, so the finder still narrows.
- **Toxic species** are matched leniently:
  - A 「没有菌环 / 菌托」 answer never removes them.
  - A 「有菌环」 answer removes them only if they have no ring and no known cause for one (*Cortinarius* / *Inocybe* veil remnants).
  - A 「有菌托」 answer removes them only if they have no volva and are not *Amanita*.
  - Ground / grass / wood never removes them; only 「埋在土里」 can.
  - An easily misread spore colour (white ↔ cream/yellow, brown ↔ chocolate, …) never removes them.
- **Edible species** are matched exactly, plus their documented mix-ups. A ring that is often lost (`ringVar`) is never required.

## Schema v2 (`src/data/tags.py`)

| Field | v1 | v2 |
|---|---|---|
| `hym` | gills / pores / spines / ridges / other | Same values. 「other」 now means "no cap underside" (honeycomb, ball, jelly, coral). The old option text 「橙色硬壳」 was removed: it described the cap, not a fertile surface |
| `hymAlt`, `hymWhy` | — | Other answers an observer may give, and the sentence shown on the card and the species sheet |
| `spore` | colours or `unknown` | Colours, `unknown` (not documented) or `na` (no print possible, e.g. truffles) |
| `sub` | one or more of ground / grass / wood / under | Unchanged; 13 species gained a documented substrate (mulch, buried roots, lawns) |
| `ring`, `volva` | true / false | Unchanged meaning ("present when intact"), plus `ringVar`: the ring is often lost or faint |

Migration: v1 entries need no change. The new fields default to empty / false. The finder's option labels now come from
`FEAT.hym`, the same words the species sheet uses.

## Tools

- `python3 src/audit_species.py` writes `reports/species_feature_audit.csv` and `.json`, one row per species:
  - tags, photo and sources;
  - automatic findings (tags vs the species' own text, photo genus, enums, completeness);
  - the cross-check result and the manual log (`src/data/audit_log.py`).
  - It exits 1 on duplicates, orphan tags or invalid enums. CI runs it in the build job and uploads the table.
- `python3 src/xref_species.py` (needs network) refreshes `reports/species_xref.json`. It uses current names from
  `src/data/synonyms.py`.

## Tests

`tests/test_site.py` adds three groups:
- the ten documented misreadings above;
- a matrix over all 86 species:
  - their own tags agree with no conflict;
  - no answers keeps every species;
  - 吻合 counts only answered fields;
  - toxic species survive every ring, volva, substrate and near-spore answer;
  - volvate deadly amanitas survive the puffball reading;
  - a clearly different fertile surface still narrows;
- the new option wording and the sheet notes.

## Still needs a mycologist

- **Not checked against any outside page (book-only or not found):**
  - edible: 绣球菌, 松茸, 紫丁香蘑, 草地横膜马勃, 木耳, 橙黄疣柄牛肝菌, 野蘑菇, 林生蘑菇, 异色疣柄牛肝菌, 粉紫香蘑, 半离羊肚菌,
    网盖牛肝菌, 乳牛肝菌, 白林地蘑菇, 橙盖鹅膏, 香杏丽蘑, 肉色杯伞;
  - toxic: 细鳞丝膜菌, 鳞柄白鹅膏, 贝形圆孢侧耳, 变红丝盖伞.
- **Questions:**
  - Which *Laetiporus* species occur in the PNW (*L. conifericola*, *L. gilbertsonii*), and should the page name them?
  - Western *Hericium* species, for the page text.
  - *Omphalotus olivascens* PNW records.
  - The egg-stage wording for every volvate *Amanita*.
  - A second regional source for *Lepiota subincarnata* on wood-chip mulch.
  - Honeycomb head vs *Gyromitra* / *Verpa* wording.
- **Fields the finder cannot ask yet:**
  - The PRD suggests splitting the fertile-surface question from the overall fruiting-body form.
  - v2 handles this through 「other = no cap underside」 and `hymAlt`.
  - A separate question would need checked tags for every species, so it was not added.
