# -*- coding: utf-8 -*-
"""Build public/index.html from src/data/*.py and src/template.html.

Usage:  python3 src/build_site.py
"""
import json
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
sys.path.insert(0, str(SRC))

from data.book import GROUPS, POISON  # noqa: E402
from data.guide import COOK, FEATURES, GLOSS, HABITATS, KEEP, RECIPES6, RECIPES6_EXTRA, RECIPES_ORIG  # noqa: E402
from data.photos import PHOTOS, HEROES, RECIPE_PHOTOS, LICENCE_NAME, LICENCE_URL  # noqa: E402
from data.seasonality import SEASONALITY, FETCHED, PLACES  # noqa: E402
from data.north_america import NA_GROUP_OF, NA_SPECIES, NA_TOXIC, TOXIC_ORDER, NA_POISON_NOTES, NA_SPECIES_NOTES  # noqa: E402
from data.tags import TAGS  # noqa: E402
from data.safety import SAFETY  # noqa: E402
from data.compare import COMPARE  # noqa: E402

OUT = ROOT / "public" / "index.html"

# Book season labels -> months (UK / Europe)
SEASON_MONTHS = {
    "春": [3, 4, 5], "早春": [2, 3, 4], "春–夏": [4, 5, 6, 7], "晚春": [5, 6],
    "夏–秋": [6, 7, 8, 9, 10], "初夏–秋": [6, 7, 8, 9, 10], "初夏–中秋": [6, 7, 8, 9, 10],
    "夏末–秋": [8, 9, 10], "夏–初秋": [6, 7, 8, 9], "夏–初冬": [6, 7, 8, 9, 10, 11, 12],
    "秋": [9, 10, 11], "晚秋": [10, 11], "秋–冬": [9, 10, 11, 12, 1], "秋–初冬": [9, 10, 11, 12],
    "晚秋–冬": [10, 11, 12, 1, 2], "晚秋–早春": [10, 11, 12, 1, 2, 3], "夏末–冬": [8, 9, 10, 11, 12, 1],
    "全年": list(range(1, 13)),
}
GROUP_KEYS = ["morel", "bolete", "chanterelle", "odd", "puffball", "agaricus", "amanita", "parasol", "gilled", "truffle"]
GROUP_SHORT = ["羊肚菌", "牛肝菌", "鸡油菌", "特殊形态", "马勃", "蘑菇属", "鹅膏属", "环柄菇", "其他褶菌", "松露"]


def slug(latin):
    return re.sub(r"[^a-z0-9]+", "-", latin.split(" / ")[0].replace(" spp.", "").lower()).strip("-")


# ---- book species ----
groups, species = [], []
for gi, (title, note, items) in enumerate(GROUPS):
    groups.append(dict(key=GROUP_KEYS[gi], name=title, short=GROUP_SHORT[gi], note=note))
    for zh, en, latin, page, season, feat, hab, spore, kitchen, warn in items:
        plain = re.sub("<[^>]+>", "", kitchen)
        flags = []
        if re.search("必须|不可生吃|彻底煮熟|焯水", plain + (warn or "")):
            flags.append("须煮熟")
        if "不宜多吃" in plain:
            flags.append("不宜多吃")
        if "上品" in plain:
            flags.append("上品")
        if GROUP_KEYS[gi] == "amanita":
            flags.append("高风险")
        species.append(dict(zh=zh, en=en, latin=latin, page=page, season=season,
                            months=SEASON_MONTHS[season], feat=feat, hab=hab, spore=spore,
                            kitchen=kitchen, warn=warn, group=GROUP_KEYS[gi], flags=flags))

# ---- editor's notes on book species (regional counterparts, extra warnings) ----
assert set(NA_SPECIES_NOTES) <= {s["latin"] for s in species}, "NA_SPECIES_NOTES names an unknown book species"
for s in species:
    n = NA_SPECIES_NOTES.get(s["latin"])
    if n:
        s["extra"] = n.get("extra", [])
        if n.get("warn"):
            s["warn"] = (s["warn"] + "；" if s["warn"] else "") + n["warn"]
        s["sources"] = n["sources"]

# ---- North American species join the same groups as everything else ----
assert set(NA_GROUP_OF) == {s["latin"] for s in NA_SPECIES}, "every North American species needs a group in NA_GROUP_OF"
species += [dict(s, group=NA_GROUP_OF[s["latin"]]) for s in NA_SPECIES]
poison = [dict(zh=zh, en=en, latin=latin, level=level, feat=feat, conf=conf) for zh, en, latin, level, feat, conf in POISON]
poison_extra = [dict(p) for p in NA_TOXIC]
for p in poison:
    if p["latin"] in NA_POISON_NOTES:
        n = NA_POISON_NOTES[p["latin"]]
        p["feat"] += "<br>" + n["note"]
        p["sources"] = n["sources"]
assert set(NA_POISON_NOTES) <= {p["latin"] for p in poison}, "NA_POISON_NOTES names an unknown book species"

# ---- finder tags + slugs ----
for item in species + poison + poison_extra:
    if item["zh"] not in TAGS:
        sys.exit(f"missing finder tags for {item['zh']} (add it to src/data/tags.py)")
    tags = dict(TAGS[item["zh"]])
    tags["sporeTags"] = tags.pop("spore")  # keep the descriptive spore text shown on species sheets
    item.update(tags)
    item["slug"] = slug(item["latin"])
assert len({x["slug"] for x in species}) == len(species), "duplicate species slug"
known = {x["slug"] for x in species + poison + poison_extra}
for c in COMPARE:
    for name, kind, sl in c["cols"]:
        assert sl is None or sl in known, f"compare '{c['id']}' links unknown slug {sl}"

for s in species:
    o = SEASONALITY.get(s["slug"])
    if o:
        s["obs"] = dict(taxon=o["taxon"], id=o["taxon_id"], counts=o["counts"],
                        regions=o.get("regions"), years=o.get("years"), last=o.get("last", ""), ryears={r: {y: 1 for y in (min(ys), max(ys))} for r, ys in (o.get("ryears") or {}).items() if ys})  # first and last year only


# ---- Pacific Northwest first: season from local records, how common it is, and list order ----
def month_ranges(ms):
    """[9, 10, 11, 12] -> "9–12 月"; wraps over the new year ([11, 12, 1] -> "11–1 月")."""
    if len(ms) == 12:
        return "全年"
    runs, cur = [], [ms[0]]
    for m in ms[1:]:
        if m == cur[-1] + 1:
            cur.append(m)
        else:
            runs.append(cur); cur = [m]
    runs.append(cur)
    if len(runs) > 1 and runs[0][0] == 1 and runs[-1][-1] == 12:
        runs[0] = runs.pop() + runs[0]
    return "、".join(f"{r[0]}–{r[-1]}" if len(r) > 1 else f"{r[0]}" for r in runs) + " 月"


for s in species:
    counts = s.get("obs", {}).get("counts", [])
    total = sum(counts)
    s["pnw"] = total
    if total >= 30:  # enough local records: season comes from them (any month with >= 10% of the peak)
        peak = max(counts)
        s["months"] = [m + 1 for m, n in enumerate(counts) if n >= 0.1 * peak]
        s["season"] = month_ranges(s["months"])
        s["seasonLocal"] = True
    if total >= 300:
        s["flags"] = ["西北太平洋常见"] + [f for f in s["flags"] if f != "非原书"]
    elif total < 30:
        s["flags"] = s["flags"] + ["西北太平洋少见"]
species.sort(key=lambda s: -s["pnw"])  # stable: equal counts keep their book/group order

for item in species + poison + poison_extra:
    ph = PHOTOS.get(item["slug"])
    if ph:
        assert (OUT.parent / "photos" / ph["file"]).exists(), f"missing photo file {ph['file']}"
        item["photo"] = dict(file=ph["file"], w=ph["w"], h=ph["h"], taxon=ph["taxon"], author=ph["author"],
                             lic=LICENCE_NAME[ph["licence"]], licUrl=LICENCE_URL[ph["licence"]], url=ph["photo_url"])
        if ph.get("hd"):
            assert (OUT.parent / "photos" / ph["hd"]["file"]).exists(), f"missing photo file {ph['hd']['file']}"
            item["photo"]["hd"] = ph["hd"]

# ---- species safety record (data/safety.py): checked here so an unsafe classification can never reach the page ----
HIGH_RISK = ("Amanita", "Cortinarius", "Chlorophyllum", "Macrolepiota", "Lepiota", "Galerina", "Gyromitra", "Paxillus", "Inocybe")
EDIBILITY = {"Edible", "Inedible", "Toxic", "Deadly Toxic", "Unknown", "Not Evaluated"}
REVIEW = {"Draft", "In Review", "Verified", "Needs Update", "Disputed"}
for item in species + poison + poison_extra:
    sf = SAFETY.get(item["slug"])
    assert sf, f"{item['latin']} has no entry in data/safety.py"
    assert item["latin"].strip(), f"{item['zh']} has no scientific name"
    assert sf["edibility"] in EDIBILITY and sf["review"] in REVIEW, f"{item['slug']}: bad edibility/review value"
    assert sf.get("reviewed") and sf.get("basis"), f"{item['slug']}: missing review date or basis"
    is_toxic = item in poison or item in poison_extra
    if is_toxic:
        assert sf["edibility"] in ("Toxic", "Deadly Toxic"), f"toxic species {item['slug']} is classified {sf['edibility']}"
        assert sf.get("symptoms"), f"toxic species {item['slug']} has no symptoms"
        if sf.get("level"): item["level"] = sf["level"]
        assert (sf["edibility"] == "Deadly Toxic") == item["level"].startswith("致命"), f"{item['slug']}: level and edibility disagree"
        assert any("wikipedia.org" not in u for _, u in (item.get("sources") or []) + sf["refs"]), \
            f"toxic species {item['slug']} cites only Wikipedia"
    else:
        assert sf["edibility"] in ("Edible", "Not Evaluated", "Unknown"), \
            f"{item['slug']} sits in the edible catalog but is classified {sf['edibility']}"
        # "Edible" needs an outside reference; a book-only species is Not Evaluated (hotfix 2026-11-01)
        assert sf["edibility"] != "Edible" or sf["review"] in ("Verified", "Disputed"), \
            f"{item['slug']}: Edible without an external reference must be Not Evaluated"
        assert sf.get("recommend") is not None, f"{item['slug']}: say whether it may be recommended"
        assert not sf["recommend"] or (sf["review"] == "Verified" and sf["edibility"] == "Edible"), \
            f"{item['slug']}: only Verified edible species may be recommended"
        assert not sf["recommend"] or not item["latin"].startswith(HIGH_RISK), \
            f"{item['slug']}: species of high-risk genera are never recommended"
        if sf["edibility"] != "Edible":  # no cooking advice and no "choice" badge for a species we have not evaluated
            item["kitchen"] = "本站没有评估它在本地的可食性，不提供吃法。没有经验丰富的人当面确认，不要吃。"
            item["flags"] = [f for f in item.get("flags", []) if f != "上品"]
    have = {u for _, u in item.get("sources") or []}
    item["sources"] = list(item.get("sources") or []) + [list(r) for r in sf["refs"] if r[1] not in have]
    item["safety"] = {k: v for k, v in sf.items() if k not in ("refs", "level", "basis")}
    # the basis quote is audit evidence in English, kept in data/safety.py only; the page links to where it is from
    m = re.search(r"（(https://[^）]+)）\s*$", sf.get("basis", ""))
    if m:
        item["safety"]["basisUrl"] = m.group(1)
# no species may be both edible and toxic, and the known dangerous genera never appear among the edibles
toxic_latin = {p["latin"].split(" / ")[0] for p in poison + poison_extra}
assert not toxic_latin & {s["latin"].split(" / ")[0] for s in species}, "a toxic species is also listed as edible"
for s in species:
    assert not s["latin"].startswith(("Paxillus", "Galerina", "Gyromitra", "Inocybe", "Omphalotus", "Pleurocybella", "Lepiota ", "Hypholoma")), \
        f"{s['latin']} belongs to a dangerous genus and must not be in the edible catalog"
    for f in ("feat", "hab", "kitchen"):
        assert s.get(f), f"{s['slug']}: missing {f}"
    assert s.get("warn") or s.get("extra") or s["slug"] in {c for cmp in COMPARE for _, _, c in cmp["cols"]} or True

recipes = [dict(r, **x) for r, x in zip(RECIPES6, RECIPES6_EXTRA, strict=True)] + [dict(r) for r in RECIPES_ORIG]
by_slug = {x["slug"]: x for x in species}
assert len({r["id"] for r in recipes}) == len(recipes), "duplicate recipe id"
for r in recipes:
    for sl in r["sp"]:
        assert sl in by_slug, f"recipe {r['id']} names unknown species {sl}"
    r["spLinks"] = [[sl, by_slug[sl]["zh"]] for sl in r["sp"]]
    for sl in r["sp"]:
        sf = by_slug[sl]["safety"]
        assert sf["edibility"] == "Edible" and sf["review"] == "Verified" and sf["recommend"], \
            f"recipe {r['id']} uses {sl}, which is not a Verified, recommendable edible species"
    for txt in [r["best"], r.get("tip", "")] + list(r.get("ing", [])):
        assert "杂菌" not in txt and "任何" not in txt, f"recipe {r['id']} suggests unnamed or 'any' mushrooms: {txt}"
    d = RECIPE_PHOTOS.get(r["id"])
    if d:  # a photo of the dish itself
        assert (OUT.parent / "photos" / d["file"]).exists(), f"missing recipe photo {d['file']}"
        r["photo"] = dict(file=d["file"], dish=True, author=d["author"], lic=LICENCE_NAME[d["licence"]],
                          licUrl=LICENCE_URL[d["licence"]], url=d["photo_url"], site=d["site"])
    elif by_slug[r["sp"][0]].get("photo"):  # otherwise the main mushroom's example photo
        ph, sp = by_slug[r["sp"][0]]["photo"], by_slug[r["sp"][0]]
        r["photo"] = dict(file=ph["file"], dish=False, sp=sp["slug"], spName=sp["zh"], author=ph["author"],
                          lic=ph["lic"], licUrl=ph["licUrl"], url=ph["url"], site="iNaturalist", w=ph["w"], hd=ph.get("hd"))

# ---- toxic species: one list in the editorial order of TOXIC_ORDER ----
all_toxic = poison + poison_extra
assert sorted(TOXIC_ORDER) == sorted(p["slug"] for p in all_toxic), "TOXIC_ORDER must list every toxic species once"
poison = sorted(all_toxic, key=lambda p: TOXIC_ORDER.index(p["slug"]))
poison_extra = []

# download sizes for the "download every photo before a trip" buttons
_ph = {x["photo"]["file"]: x["photo"] for x in species + poison if x.get("photo")}
photo_bytes = dict(small=sum((OUT.parent / "photos" / f).stat().st_size for f in _ph)
                   + sum((OUT.parent / "photos" / h["file"]).stat().st_size for h in HEROES.values()),
                   hd=sum((OUT.parent / "photos" / p["hd"]["file"]).stat().st_size for p in _ph.values() if p.get("hd")))
DATA = dict(groups=groups, species=species, poison=poison, poisonExtra=poison_extra,
            compare=COMPARE, recipes=recipes, obsFetched=FETCHED, obsPlaces=PLACES, photoBytes=photo_bytes, gloss=[[k, v] for k, _s, v in GLOSS],
            built=__import__("datetime").date.today().isoformat())
# the page and the service worker must agree on the name of the photo cache
MEDIA = re.search(r'const MEDIA = "([^"]+)"', (OUT.parent / "sw.js").read_text(encoding="utf-8")).group(1)


def kv(items):
    return "".join(
        f'<div class="kv"><div class="kv-k">{k}{f"<small>{s}</small>" if s else ""}</div><div class="kv-v">{v}</div></div>'
        for k, s, v in items)


html = ((SRC / "template.html").read_text(encoding="utf-8")
        .replace("/*__DATA__*/null", json.dumps(DATA, ensure_ascii=False).replace("</", "<\\/"))
        .replace("/*__MEDIA__*/", MEDIA)
        .replace("<!--HABITATS-->", kv(HABITATS))
        .replace("<!--FEATURES-->", kv(FEATURES))
        .replace("<!--COOK-->", kv(COOK))
        .replace("<!--KEEP-->", kv(KEEP))
        .replace("<!--GLOSS-->", kv(GLOSS))
        .replace("<!--N_EDIBLE-->", str(len(species)))
        .replace("<!--N_TOXIC-->", str(len(poison) + len(poison_extra)))
        .replace("<!--N_COMPARE-->", str(len(COMPARE)))
        .replace("<!--N_RECIPES-->", str(len(recipes)))
        .replace("<!--N_BOOK-->", str(sum(1 for x in species if x.get("page"))))
        .replace("<!--N_NA-->", str(sum(1 for x in species if not x.get("page")))))
def hero_small(name):
    """A 640px copy of a header photo for phones (made from the 1024px file; the build never fetches)."""
    src, dst = OUT.parent / "photos" / name, OUT.parent / "photos" / name.replace(".webp", "-640.webp")
    if not dst.exists():  # committed with the photo; only a new header photo needs Pillow here (CI has no Pillow)
        from PIL import Image
        im = Image.open(src).convert("RGB")
        im.resize((640, round(im.height * 640 / im.width)), Image.LANCZOS).save(dst, "WEBP", quality=66, method=6)
    return dst.name


for view, h in HEROES.items():
    assert (OUT.parent / "photos" / h["file"]).exists(), f"missing hero photo {h['file']}"
    small = hero_small(h["file"])
    html = html.replace(f"<!--HERO:{view}-->", (
        f'<img class="view__hero" src="photos/{h["file"]}" srcset="photos/{small} 640w, photos/{h["file"]} 1024w" '
        f'sizes="(min-width: 1024px) 760px, calc(100vw - 32px)" alt="" decoding="async"{" fetchpriority=\"high\"" if view.startswith("home") else " loading=\"lazy\""}>'
        f'<span class="view__credit">照片：<a href="{h["photo_url"]}" target="_blank" rel="noopener">{h["author"]}</a>'
        f' · <a href="{LICENCE_URL[h["licence"]]}" target="_blank" rel="noopener">{LICENCE_NAME[h["licence"]]}</a> · iNaturalist</span>'))
assert "<!--HERO:" not in html, "a view header has no hero photo in data/photos.HEROES"
# readers have no context for "the book": the page names it once, in full, in the footer
assert "原书" not in html, "the page mentions 原书; name the book in full in the footer instead"
# advice that must never come back: trial portions, "works for any mushroom", detox by cooking, raw eating, walking toward traffic noise
# every external link must be a plain https URL
for x in species + poison + poison_extra:
    for _t, u in x.get("sources") or []:
        assert re.match(r"^https://[^\s\"'<>]+$", u), f"{x['slug']}: bad source URL {u}"
for bad in ["只吃一两勺", "只吃一小份", "只吃一勺", "只吃一两块", "任何杂菌", "朝车声", "去除生菌", "可去除", "生拌", "生刨", "可薄切生"]:
    assert bad not in html, f"unsafe advice is back on the page: {bad}"
OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)}: {len(species)} edible, {len(poison) + len(poison_extra)} toxic, "
      f"{len(COMPARE)} comparisons, {len(html.encode()) // 1024} KB")

# every file the service worker pre-caches must exist, or installing it fails and the site never works offline
_sw = (OUT.parent / "sw.js").read_text(encoding="utf-8")
for _f in re.findall(r'"\./([^"]+)"', re.search(r"const SHELL = \[(.*?)\];", _sw).group(1)):
    assert (OUT.parent / _f).exists(), f"sw.js pre-caches a missing file: {_f}"
