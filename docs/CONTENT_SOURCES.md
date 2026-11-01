# Content sources and review model

## Safety data model (`src/data/safety.py`)

Every species slug, edible or toxic, has one record. The build (`src/build_site.py`) fails if a record is missing or invalid.

| Field | Values | Meaning |
|---|---|---|
| `edibility` | Edible / Inedible / Toxic / Deadly Toxic / Unknown / Not Evaluated | The species, never a specimen |
| `review` | Draft / In Review / Verified / Needs Update / Disputed | Editor check against outside references, not expert review |
| `reviewed` | date | When the editor last checked |
| `basis` | quote (URL) | Audit evidence; kept in the data file, only the link is shown on the site |
| `refs` | [[title, url], ...] | Added to the species' sources |
| `recommend` | bool (edible only) | May be featured or used in recipes; requires Verified |
| `symptoms` | text (toxic only, required) | Onset and course, from NAMA |
| `note` | text | Disambiguation or caution |

Rules enforced by the build: toxic ⇒ Toxic/Deadly Toxic with symptoms; Deadly Toxic ⇔ level 致命; edible ⇒ Edible;
recommend ⇒ Verified; recipes use only recommended species; every source URL is https.

## Sources used

| Kind | Source | Used for |
|---|---|---|
| 专业参考 | MykoWeb, California Fungi (mykoweb.com/CAF) | Edibility field per species |
| 学术/机构 | UBC Beaty Biodiversity Museum, Mushrooms Up! | BC species, toxicity |
| 专业参考 | North American Mycological Association, poisoning syndromes | Symptoms and latency |
| 专业参考 | MushroomExpert.com | Identification only (it does not state edibility) |
| 社区观察 | iNaturalist research-grade observations, BC/WA/OR | Seasons, counts, last record (fetched 2026-10-31) |
| 官方机构 | California Poison Control; America's Poison Centers; BC DPIC | Emergency page |
| 官方机构 | KU Health System Poison Control | "Processing does not remove toxins" |
| 图书 | The book credited in the footer | Book species text (rewritten), page numbers in data/book.py only |

## How to change a classification

1. Find an outside reference (list above, or a peer-reviewed paper). Do not rely on a single blog or forum.
2. Edit the record in `src/data/safety.py`: `basis` with the quote and URL, `refs`, `review`, `reviewed`.
3. If references disagree, set `Disputed` and keep the cautious classification.
4. `python3 src/build_site.py && python3 tests/test_site.py`.
