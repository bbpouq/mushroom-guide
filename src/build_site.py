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

# the "where to look" lists name only species we recommend (no unevaluated or high-risk ones)
_ok = set()
for s in species:
    if s["safety"].get("recommend") and s["safety"]["review"] == "Verified":  # "糙皮侧耳（平菇）" -> 糙皮侧耳, 平菇
        _ok.add(re.sub(r"（[^）]*）", "", s["zh"]))
        _ok.update(x for m in re.findall(r"（([^）]*)）", s["zh"]) for x in m.split("、"))
for _hab, _trees, _names in HABITATS:
    for _n in re.split(r"[、；]", re.sub(r"（[^）]*）", "", _names)):
        _n = re.sub(r"^.*?：", "", _n).strip()
        assert _n in _ok, f"habitat '{_hab}' names '{_n}', which is not a recommended species"

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


def habitat_cards(items):
    """生境探索: one folding card per habitat with its trees and the recommended species seen there (photo, season, link)."""
    by_name = {}
    for s in species:
        if s["safety"].get("recommend") and s["safety"]["review"] == "Verified":
            for n in [re.sub(r"（[^）]*）", "", s["zh"])] + [x for m in re.findall(r"（([^）]*)）", s["zh"]) for x in m.split("、")]:
                by_name[n] = s
    out = []
    for hab, trees, names in items:
        chips = []
        for part in re.split(r"[、；]", names):
            where = re.match(r"^(.*?)：", part)
            label = re.sub(r"^.*?：", "", part).strip()
            s = by_name[re.sub(r"（[^）]*）", "", label).strip()]
            img = f'<img class="habitat__img" src="photos/{s["photo"]["file"]}" alt="" loading="lazy" decoding="async">' if s.get("photo") else ""
            note = (where.group(1) + " · " if where else "") + (re.search(r"（([^）]*)）", label).group(1) + " · " if "（" in label else "")
            chips.append(f'<li><a class="habitat__sp" href="#sp-{s["slug"]}">{img}<span><b>{s["zh"]}</b><small>{note}{s["season"]}</small></span></a></li>')
        thumbs = "".join(c.split("<span>")[0].split('">', 1)[1] for c in chips[:3] if "<img" in c)
        out.append(f'<details class="habitat"><summary class="habitat__head"><span class="habitat__thumbs" aria-hidden="true">{thumbs}</span>'
                   f'<span class="habitat__name"><b>{hab}</b><small>{("常见树种：" + trees) if trees else "&nbsp;"}</small></span></summary>'
                   f'<div class="habitat__body"><p class="habitat__lead">本站推荐的种类里，这类生境常见：</p><ul class="habitat__list">{"".join(chips)}</ul>'
                   f'<p class="habitat__note">点开每种菌看它的易混毒菌和全年记录。生境只帮你决定去哪里找，不保证一定有，也不能证明手上的菌是哪一种。</p></div></details>')
    return '<div class="habitat__grid">' + "".join(out) + "</div>"


def kv(items):
    return "".join(
        f'<div class="kv"><div class="kv-k">{k}{f"<small>{s}</small>" if s else ""}</div><div class="kv-v">{v}</div></div>'
        for k, s, v in items)


html = ((SRC / "template.html").read_text(encoding="utf-8")
        .replace("/*__DATA__*/null", json.dumps(DATA, ensure_ascii=False).replace("</", "<\\/"))
        .replace("/*__MEDIA__*/", MEDIA)
        .replace("<!--HABITATS-->", habitat_cards(HABITATS))
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
for bad in ["只吃一两勺", "只吃一小份", "只吃一勺", "只吃一两块", "第一次吃少量", "先少量", "少量试", "试吃", "或再核对一次", "鹅膏类（", "任何杂菌", "朝车声", "去除生菌", "可去除", "生拌", "生刨", "可薄切生"]:
    assert bad not in html, f"unsafe advice is back on the page: {bad}"
OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)}: {len(species)} edible, {len(poison) + len(poison_extra)} toxic, "
      f"{len(COMPARE)} comparisons, {len(html.encode()) // 1024} KB")

# every file the service worker pre-caches must exist, or installing it fails and the site never works offline
_sw = (OUT.parent / "sw.js").read_text(encoding="utf-8")
for _f in re.findall(r'"\./([^"]+)"', re.search(r"const SHELL = \[(.*?)\];", _sw).group(1)):
    assert (OUT.parent / _f).exists(), f"sw.js pre-caches a missing file: {_f}"

# ---- design-system lint (round 10, Sprint 1): components use tokens; any exception says why in /* ds-ok: reason */ ----
def style_lint(css):
    """Return violations: colour literals, pixel font sizes, off-scale spacing and radii outside the token definitions.
    Custom properties (--name: value) are the token definitions and are exempt. Allowed without a note: forest-black
    rgba(10, 14, 11, a) for shadows and scrims, hairlines up to 3px, calc()/env() expressions, %, em, rem and 0."""
    css = re.sub(r"/\*(?!\s*ds-ok)[\s\S]*?\*/", "", css)  # drop ordinary comments, keep ds-ok notes
    bad = []
    for m in re.finditer(r"(?<![\w-])([a-z-]+)\s*:\s*([^;{}]+)", css):
        prop, val = m.group(1), m.group(2)
        if prop.startswith("--") or "ds-ok:" in val or prop in ("content", "src", "font-family", "grid-template-areas"):
            continue
        line = css.count("\n", 0, m.start()) + 1
        if re.search(r"#[0-9a-fA-F]{3,8}\b|\brgba?\((?!10, 14, 11)|\bhsla?\(", val):
            bad.append(f"line {line}: colour literal in {prop}: {val.strip()[:60]}")
        if prop == "font-size" and re.search(r"(?<![\w.])\d+(\.\d+)?px", val) and "calc" not in val:
            bad.append(f"line {line}: pixel font-size {val.strip()[:40]} (use var(--fs-*))")
        if re.match(r"(margin|padding|gap|row-gap|column-gap)(-|$)", prop) and "calc" not in val and "env(" not in val:
            for n in re.findall(r"(?<![\w.-])(\d+)px", val):
                if int(n) > 3:
                    bad.append(f"line {line}: off-token spacing {prop}: {val.strip()[:40]} (use var(--space-*))"); break
        if "radius" in prop:
            for n in re.findall(r"(?<![\w.-])(\d+)px", val):
                if int(n) > 2:
                    bad.append(f"line {line}: off-token radius {val.strip()[:40]} (use var(--radius-*))"); break
    return bad


_tpl = (SRC / "template.html").read_text(encoding="utf-8")
_lint = style_lint(_tpl[_tpl.index("<style>"):_tpl.index("</style>")])
assert not _lint, "design-system lint (fix, or add /* ds-ok: reason */):\n  " + "\n  ".join(_lint[:40])


# ---- design system showcase (public/design-system.html): the site's own CSS and icons, so it can never drift ----
def design_page():
    tpl = (SRC / "template.html").read_text(encoding="utf-8")
    css = tpl[tpl.index("<style>"):tpl.index("</style>") + 8]
    s0 = tpl.index("<symbol id=")
    sprite = tpl[tpl.rindex("<svg", 0, s0):tpl.index("</svg>", s0) + 6]
    sw = lambda name, var, note="": f'<div class="ds-sw"><span style="background:var({var})"></span><b>{name}</b><code>{var}</code><small>{note}</small></div>'
    colors = "".join(sw(*c) for c in [
        ("Forest 900", "--forest-900", "品牌深绿"), ("Forest 700", "--color-primary", "交互色（选中、主按钮）"), ("Moss 500", "--color-secondary", "次要装饰，不作文字"),
        ("Moss 100", "--color-primary-surface", "浅绿底"), ("Cream 50", "--surface-0", "页面背景"), ("Surface 1", "--surface-1", "卡片"),
        ("Surface 2", "--surface-2", "弹层、输入框"), ("Paper 100", "--color-muted", "次级背景"), ("Bark 500", "--bark-500", "自然棕，只作装饰"),
        ("Amber 500", "--color-accent", "填充，文字用深色"), ("Text", "--color-foreground", "正文 11.8:1"), ("Text secondary", "--color-muted-foreground", "次级文字 5.5:1"),
        ("Border", "--color-border", "分隔线"), ("Danger", "--color-destructive", "只用于毒性和急救"), ("Danger text", "--color-danger-text", "危险文字 6.1:1")])
    types = "".join(f'<p style="font-size:var({v});{ff}margin:.2em 0">{n} · <code>{v}</code> 认识蘑菇，探索森林</p>' for n, v, ff in [
        ("Display", "--fs-display", "font-family:var(--font-display);font-weight:var(--fw-700);"), ("H1", "--fs-h1", "font-family:var(--font-display);font-weight:var(--fw-700);"),
        ("H2", "--fs-h2", "font-weight:var(--fw-700);"), ("H3", "--fs-h3", "font-weight:var(--fw-700);"), ("Body", "--fs-body", ""), ("Secondary", "--fs-secondary", ""), ("Caption", "--fs-caption", "")])
    space = "".join(f'<div class="ds-sp"><span style="width:var(--space-{i})"></span><code>--space-{i} · {px}px</code></div>'
                    for i, px in [(1, 4), (2, 8), (3, 12), (4, 16), (5, 24), (6, 32), (8, 40), (7, 48), (9, 64)])
    body = f"""<main class="ds">
<header class="ds-head"><h1 class="view__title">拾菌记 设计系统</h1><p>Nature Editorial × Modern Field App · 组件直接使用网站的 CSS 和图标。色块显示当前主题下的实际颜色。</p>
<div class="link-row"><div class="seg" role="group" aria-label="外观"><button type="button" class="seg__btn" data-ds-theme="system" aria-pressed="true">跟随系统</button><button type="button" class="seg__btn" data-ds-theme="light" aria-pressed="false">浅色</button><button type="button" class="seg__btn" data-ds-theme="dark" aria-pressed="false">深色</button></div>
<label class="toggle"><input type="checkbox" role="switch" id="ds-field"><span class="toggle__track" aria-hidden="true"></span><span>户外模式</span></label><a class="btn" href="./">回到拾菌记</a></div></header>
<section><h2>颜色</h2><div class="ds-grid">{colors}</div></section>
<section><h2>字体层级</h2>{types}</section>
<section><h2>间距（4px 基础）</h2>{space}</section>
<section><h2>按钮与状态</h2><p class="muted-note">默认 · 悬停 · 按下（缩小）· 键盘聚焦（双环）· 不可用 · 进行中（aria-busy）</p><div class="link-row"><button class="btn btn--primary" type="button">主按钮</button><button class="btn" type="button">次按钮</button><button class="btn btn--danger" type="button">危险操作</button><button class="btn" type="button" disabled>不可用</button><button class="btn" type="button" aria-busy="true">导出中</button><button class="icon-btn" type="button" aria-label="搜索"><svg class="icon" aria-hidden="true"><use href="#i-search"/></svg></button></div></section>
<section><h2>分段控件 Segmented Control</h2><div class="seg" role="group" aria-label="显示方式"><button type="button" class="seg__btn" aria-pressed="true">全年日历</button><button type="button" class="seg__btn" aria-pressed="false">按月份看</button></div>
<ol class="seg seg--steps" aria-label="步骤" style="margin-top:16px"><li><button type="button" class="seg__btn" aria-current="step">照片与物种</button></li><li><button type="button" class="seg__btn">地点与环境</button></li><li><button type="button" class="seg__btn">备注与保存</button></li></ol></section>
<section><h2>开关 Toggle</h2><label class="toggle"><input type="checkbox" role="switch" checked><span class="toggle__track" aria-hidden="true"></span><span>只记大概位置（约 1 公里）</span></label><br><label class="toggle"><input type="checkbox" role="switch" disabled><span class="toggle__track" aria-hidden="true"></span><span>不可用</span></label></section>
<section><h2>底部面板 Bottom Sheet</h2><p class="muted-note">手机上从底部升起，电脑上居中；点背景、Esc 或关闭按钮都会取消。</p><button class="btn" type="button" onclick="document.getElementById('ds-sheet').showModal()">打开示例面板</button>
<dialog class="bsheet" id="ds-sheet" aria-labelledby="ds-sheet-t"><div class="bsheet__box"><span class="bsheet__grab" aria-hidden="true"></span><div class="bsheet__head"><h2 class="bsheet__title" id="ds-sheet-t">示例面板</h2><button class="icon-btn" type="button" aria-label="关闭" onclick="this.closest('dialog').close()"><svg class="icon" aria-hidden="true"><use href="#i-x"/></svg></button></div><p>确认之前，什么都不会改动。</p><div class="bsheet__actions"><button class="btn" type="button" onclick="this.closest('dialog').close()">取消</button><button class="btn btn--primary" type="button" onclick="this.closest('dialog').close()">确认</button></div></div></dialog></section>
<section><h2>加载占位 Skeleton 与错误状态</h2><div class="skel-list" aria-hidden="true"><div class="skel skel--row"><span class="skel skel--thumb"></span><span class="skel__lines"><span class="skel skel--line"></span><span class="skel skel--line skel--short"></span></span></div></div>
<div class="err-state" role="status" style="margin-top:16px"><svg class="icon" aria-hidden="true"><use href="#i-alert"/></svg><div><b>这里不能保存记录</b><p>错误状态用琥珀色，不用红色：红色只留给毒性和急救。</p></div></div></section>
<section><h2>筛选 Chip / 分段</h2><div class="chip-list"><button class="chip" type="button" aria-pressed="true">三地合计</button><button class="chip" type="button" aria-pressed="false">BC</button><button class="chip" type="button" aria-pressed="false">华盛顿</button></div>
<ol class="jsteps" style="margin-top:16px"><li><button type="button" class="jsteps__btn" aria-current="step">照片与物种</button></li><li><button type="button" class="jsteps__btn">地点与环境</button></li><li><button type="button" class="jsteps__btn">备注与保存</button></li></ol></section>
<section><h2>输入</h2><div class="search-field"><svg class="icon" aria-hidden="true"><use href="#i-search"/></svg><label class="sr-only" for="ds-q">搜索</label><input id="ds-q" type="search" placeholder="搜中文名、英文名、学名或术语"></div>
<p><label class="finds__label" for="ds-s">选择</label><select class="finds__input" id="ds-s"><option>林地地面</option></select></p>
<label class="finds__check"><input type="checkbox" checked><span>只记大概位置（约 1 公里）</span></label></section>
<section><h2>标签</h2><div class="badges"><span class="badge badge--choice">上品</span><span class="badge badge--cook">须煮熟</span><span class="badge badge--risk">高风险</span><span class="badge badge--local">西北太平洋常见</span><span class="sp-card__review">待核实</span></div>
<p><span class="level level--deadly"><svg class="icon icon--sm" aria-hidden="true"><use href="#i-skull"/></svg>致命</span> <span class="level level--poison">有毒</span></p></section>
<section><h2>安全提示（最醒目，不加动画）</h2><div class="callout callout--danger" role="note"><svg class="icon" aria-hidden="true"><use href="#i-alert"/></svg><div><b>有任何疑问，就不要吃。</b>烹饪不能使有毒蘑菇变得安全。</div></div>
<div class="callout callout--info" role="note"><svg class="icon" aria-hidden="true"><use href="#i-shield"/></svg><div>普通说明使用中性底色。</div></div></section>
<section><h2>卡片</h2><div class="jcard__list"><a class="jcard" href="#"><span class="jcard__pic"><svg class="icon" aria-hidden="true"><use href="#i-mushroom"/></svg></span><span class="jcard__text"><b>美味齿菌（羊蹄菇）</b><span>2026-10-03</span><span class="jcard__st jcard__st--candidate">候选（个人判断）</span></span></a></div>
<div class="home-act" style="margin-top:16px"><a class="home-act__item home-act__item--id" href="#"><span class="home-act__icon"><svg class="icon icon--lg" aria-hidden="true"><use href="#i-filter"/></svg></span><span class="home-act__text"><b>识别一朵菌</b><span>主行动卡片</span></span></a><a class="home-act__item home-act__item--ex" href="#"><span class="home-act__icon"><svg class="icon icon--lg" aria-hidden="true"><use href="#i-compass"/></svg></span><span class="home-act__text"><b>探索森林</b><span>次行动卡片</span></span></a></div></section>
<section><h2>空状态</h2><div class="empty-state empty-state--left"><p>还没有记录。空状态总要给出下一步。</p><a class="btn btn--primary" href="#"><svg class="icon icon--sm" aria-hidden="true"><use href="#i-plus"/></svg>记下第一次发现</a></div></section>
</main>"""
    extra = """<style>.ds{max-width:960px;margin:0 auto;padding:24px 16px 64px}.ds section{margin-top:40px}.ds h2{font-size:var(--fs-h2)}
.ds-grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(200px,1fr))}.ds-sw{display:grid;gap:2px;padding:8px;border-radius:14px;background:var(--surface-1)}
.ds-sw span{height:48px;border-radius:10px;border:.5px solid var(--color-border)}.ds-sw small,.ds-sw code{font-size:12px;color:var(--color-muted-foreground)}
.ds-sp{display:flex;align-items:center;gap:12px;margin:4px 0}.ds-sp span{height:12px;background:var(--color-primary);border-radius:3px}</style>"""
    script = """<script>
document.addEventListener("click", e => { const b = e.target.closest("[data-ds-theme]"); if (!b) return; const v = b.dataset.dsTheme;
  if (v === "system") delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = v;
  document.querySelectorAll("[data-ds-theme]").forEach(x => x.setAttribute("aria-pressed", x === b)); });
document.getElementById("ds-field").addEventListener("change", e => { if (e.target.checked) document.documentElement.dataset.field = "on"; else delete document.documentElement.dataset.field; });
document.querySelectorAll("dialog").forEach(d => d.addEventListener("click", e => { if (e.target === d) d.close(); }));
</script>"""
    return (f'<!doctype html><html lang="zh-Hans"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            f'<meta name="robots" content="noindex"><title>拾菌记 设计系统</title>{css}{extra}</head><body>{sprite}{body}{script}</body></html>')


(OUT.parent / "design-system.html").write_text(design_page(), encoding="utf-8")
