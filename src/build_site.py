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

from data.book import GROUPS, POISON, RECIPES  # noqa: E402
from data.guide import COOK, FEATURED, FEATURES, GLOSS, HABITATS, KEEP, RECIPES6  # noqa: E402
from data.north_america import NA_GROUP, NA_SPECIES, NA_TOXIC, NA_POISON_NOTES  # noqa: E402
from data.tags import TAGS  # noqa: E402
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
        if "少量" in plain:
            flags.append("少量食用")
        if "上品" in plain:
            flags.append("上品")
        if GROUP_KEYS[gi] == "amanita":
            flags.append("高风险")
        species.append(dict(zh=zh, en=en, latin=latin, page=page, season=season,
                            months=SEASON_MONTHS[season], feat=feat, hab=hab, spore=spore,
                            kitchen=kitchen, warn=warn, group=GROUP_KEYS[gi], flags=flags))

# ---- North American additions go first ----
groups.insert(0, NA_GROUP)
species[0:0] = [dict(s) for s in NA_SPECIES]
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
    item.update(TAGS[item["zh"]])
    item["slug"] = slug(item["latin"])
assert len({x["slug"] for x in species}) == len(species), "duplicate species slug"
known = {x["slug"] for x in species + poison + poison_extra}
for c in COMPARE:
    for name, kind, sl in c["cols"]:
        assert sl is None or sl in known, f"compare '{c['id']}' links unknown slug {sl}"

recipes = [dict(r) for r in RECIPES6]
rindex = [dict(p=p, zh=zh.replace(" ★", ""), en=en, star=p in FEATURED) for p, zh, en in RECIPES]

DATA = dict(groups=groups, species=species, poison=poison, poisonExtra=poison_extra,
            compare=COMPARE, recipes=recipes, rindex=rindex)


def kv(items):
    return "".join(
        f'<div class="kv"><div class="kv-k">{k}{f"<small>{s}</small>" if s else ""}</div><div class="kv-v">{v}</div></div>'
        for k, s, v in items)


html = ((SRC / "template.html").read_text(encoding="utf-8")
        .replace("/*__DATA__*/null", json.dumps(DATA, ensure_ascii=False))
        .replace("<!--HABITATS-->", kv(HABITATS))
        .replace("<!--FEATURES-->", kv(FEATURES))
        .replace("<!--COOK-->", kv(COOK))
        .replace("<!--KEEP-->", kv(KEEP))
        .replace("<!--GLOSS-->", kv(GLOSS))
        .replace("<!--N_EDIBLE-->", str(len(species)))
        .replace("<!--N_TOXIC-->", str(len(poison) + len(poison_extra))))
OUT.write_text(html, encoding="utf-8")
print(f"wrote {OUT.relative_to(ROOT)}: {len(species)} edible, {len(poison) + len(poison_extra)} toxic, "
      f"{len(COMPARE)} comparisons, {len(html.encode()) // 1024} KB")
