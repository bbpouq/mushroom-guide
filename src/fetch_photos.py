# -*- coding: utf-8 -*-
"""Pick one openly licensed example photo per species (edible and toxic) from iNaturalist, save a small
WebP copy to public/photos/<slug>.webp and write the attribution to src/data/photos.py.

Run by hand (needs network and Pillow); the site build only reads the saved files:
    python3 src/fetch_photos.py            # fetch photos for species that do not have one yet
    python3 src/fetch_photos.py --all      # re-pick every photo
Pin a specific iNaturalist photo for a species in PINNED if the automatic pick is poor.
"""
import io
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

from PIL import Image

SRC = Path(__file__).resolve().parent
ROOT = SRC.parent
OUT = ROOT / "public" / "photos"
sys.path.insert(0, str(SRC))
from data.book import GROUPS, POISON  # noqa: E402
from data.north_america import NA_SPECIES, NA_TOXIC  # noqa: E402

API = "https://api.inaturalist.org/v1"
UA = "mushroom-guide/1.0 (+https://github.com/bbpouq/mushroom-guide)"
# Licences we accept. The site is free and non-commercial, so NC licences are allowed; "no derivatives"
# licences are not, because we resize the photo. Every photo is shown with its author and licence.
OK = ["cc0", "pd", "cc-by", "cc-by-sa", "cc-by-nc", "cc-by-nc-sa"]
LICENCE_NAME = {"cc0": "CC0", "pd": "公有领域", "cc-by": "CC BY", "cc-by-sa": "CC BY-SA",
                "cc-by-nc": "CC BY-NC", "cc-by-nc-sa": "CC BY-NC-SA"}
LICENCE_URL = {"cc0": "https://creativecommons.org/publicdomain/zero/1.0/",
               "pd": "https://creativecommons.org/publicdomain/mark/1.0/",
               "cc-by": "https://creativecommons.org/licenses/by/4.0/",
               "cc-by-sa": "https://creativecommons.org/licenses/by-sa/4.0/",
               "cc-by-nc": "https://creativecommons.org/licenses/by-nc/4.0/",
               "cc-by-nc-sa": "https://creativecommons.org/licenses/by-nc-sa/4.0/"}
PINNED = {}  # slug -> iNaturalist photo id, to override the automatic pick
NAME_FIX = {"Agaricus silvicola": "Agaricus sylvicola"}  # spellings iNaturalist uses
WIDTH = 480
# Header photo for each view, shown behind the large title: (taxon, iNaturalist photo id from that taxon's photos).
# The emergency view has none on purpose.
HEROES = {"species": ("Cantharellus formosus", 168845865), "finder": ("Agaricus augustus", 22093962),
          "toxic": ("Amanita muscaria", 448681419), "guide": ("Aureoboletus mirabilis", 11502906),
          "log": ("Craterellus tubaeformis", 250397284), "recipes": ("Boletus edulis", 29239600)}
HERO_WIDTH = 1024


def slug(latin):  # same rule as build_site.slug
    return re.sub(r"[^a-z0-9]+", "-", latin.split(" / ")[0].replace(" spp.", "").lower()).strip("-")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()


def api(path, **params):
    return json.loads(get(f"{API}/{path}?{urllib.parse.urlencode(params)}"))


def taxon(name):
    """iNaturalist taxon for a name, falling back to a synonym match (e.g. Lepista nuda -> Collybia nuda)."""
    res = api("taxa", q=name, is_active="true", per_page=10)["results"]
    for t in res:
        if t["name"] == name:
            return t
    for t in res:
        if t.get("matched_term") == name and t["rank"] in ("species", "genus"):
            return t
    return None


def pick(t, pinned=None):
    """First acceptable photo: the pinned one, else the taxon's default photo, else its other photos."""
    full = api(f"taxa/{t['id']}")["results"][0]
    photos = [tp["photo"] for tp in full.get("taxon_photos", [])]
    if full.get("default_photo"):
        photos.insert(0, full["default_photo"])
    if pinned:
        photos = [p for p in photos if p["id"] == pinned] or [api(f"photos/{pinned}")["photos"][0]]
    for p in photos:
        if p.get("license_code") in OK:
            return full, p
    return full, None


def author(attribution):
    m = re.match(r"\(c\)\s*(.+?),\s*(some|no) rights reserved", attribution or "")
    return m.group(1).strip() if m else (attribution or "").strip()


def main():
    redo = "--all" in sys.argv
    OUT.mkdir(parents=True, exist_ok=True)
    names = ([s["latin"] for s in NA_SPECIES] + [sp[2] for _, _, items in GROUPS for sp in items]
             + [p[2] for p in POISON] + [p["latin"] for p in NA_TOXIC])
    try:
        from data.photos import PHOTOS as old
    except ImportError:
        old = {}
    out = {}
    for latin in names:
        sl = slug(latin)
        if sl in out:
            continue
        if not redo and sl in old and (OUT / old[sl]["file"]).exists() and sl not in PINNED:
            out[sl] = old[sl]
            continue
        name = latin.split(" / ")[0].replace(" spp.", "")
        t = taxon(NAME_FIX.get(name, name))
        time.sleep(1)
        if not t:
            print(f"  no taxon: {name}")
            continue
        full, p = pick(t, PINNED.get(sl))
        time.sleep(1)
        if not p:
            print(f"  no openly licensed photo: {name}")
            continue
        src = re.sub(r"/(square|small|medium|large|original)\.", "/medium.", p["url"])
        img = Image.open(io.BytesIO(get(src))).convert("RGB")
        if img.width > WIDTH:
            img = img.resize((WIDTH, round(img.height * WIDTH / img.width)), Image.LANCZOS)
        img.save(OUT / f"{sl}.webp", "WEBP", quality=72, method=6)
        out[sl] = dict(file=f"{sl}.webp", w=img.width, h=img.height, taxon=full["name"],
                       author=author(p.get("attribution")), licence=p["license_code"],
                       photo_url=f"https://www.inaturalist.org/photos/{p['id']}")
        print(f"  {p['license_code']:12s} {latin}  ->  {full['name']}  ({out[sl]['author']})")
        time.sleep(1)
    try:
        from data.photos import HEROES as old_heroes
    except ImportError:
        old_heroes = {}
    heroes = {}
    for view, (name, pid) in HEROES.items():
        if not redo and view in old_heroes and old_heroes[view]["id"] == pid and (OUT / old_heroes[view]["file"]).exists():
            heroes[view] = old_heroes[view]
            continue
        full = api(f"taxa/{taxon(name)['id']}")["results"][0]
        p = next(tp["photo"] for tp in full["taxon_photos"] if tp["photo"]["id"] == pid)
        time.sleep(1)
        assert p.get("license_code") in OK, f"hero photo {pid} has licence {p.get('license_code')}"
        img = Image.open(io.BytesIO(get(re.sub(r"/(square|small|medium|large|original)\.", "/large.", p["url"])))).convert("RGB")
        if img.width > HERO_WIDTH:
            img = img.resize((HERO_WIDTH, round(img.height * HERO_WIDTH / img.width)), Image.LANCZOS)
        img.save(OUT / f"hero-{view}.webp", "WEBP", quality=70, method=6)
        heroes[view] = dict(id=pid, file=f"hero-{view}.webp", author=author(p.get("attribution")),
                            licence=p["license_code"], photo_url=f"https://www.inaturalist.org/photos/{pid}")
        print(f"  hero {view}: {p['license_code']} ({heroes[view]['author']})")
        time.sleep(1)
    body = (f'# -*- coding: utf-8 -*-\n"""Example photos (public/photos/) with attribution. Generated by src/fetch_photos.py;\n'
            f'last run {date.today().isoformat()}. Do not edit by hand: pin a photo in fetch_photos.PINNED instead."""\n\n'
            f'LICENCE_NAME = {LICENCE_NAME!r}\nLICENCE_URL = {LICENCE_URL!r}\nPHOTOS = {{\n')
    body += "".join(f" {k!r}: {v!r},\n" for k, v in out.items())
    body += "}\nHEROES = {\n" + "".join(f" {k!r}: {v!r},\n" for k, v in heroes.items()) + "}\n"
    (SRC / "data" / "photos.py").write_text(body, encoding="utf-8")
    kb = sum(f.stat().st_size for f in OUT.glob("*.webp")) // 1024
    print(f"wrote src/data/photos.py ({len(out)} photos, {kb} KB in public/photos/)")


if __name__ == "__main__":
    main()
