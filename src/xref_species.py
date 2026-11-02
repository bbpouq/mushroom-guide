# -*- coding: utf-8 -*-
"""Cross-check each species' finder tags against outside descriptions (MushroomExpert, MykoWeb California Fungi).

For every species in the built data it tries a few page URLs built from the Latin name (current names first, see SYN), pulls
the spore print colour, the ecology / habitat sentence and what the page says about the ring and volva, and compares them with
the tags. The result goes to reports/species_xref.json: per species the URL used, the extracted text and the disagreements.
Disagreements are leads for a person to read, never automatic changes. Needs network.

Usage: python3 src/xref_species.py
"""
import html
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from audit_species import load_data  # noqa: E402

from data.synonyms import SYN  # noqa: E402
COLOURS = [("white", r"\bwhit|\bcream|\bbuff"), ("yellow", r"yellow|ochr"), ("pink", r"pink|salmon|flesh-colored"), ("brown", r"\bbrown|rust|cinnamon|tawny"),
           ("choc", r"chocolate|purple-brown|purplish brown|dark brown"), ("olive", r"olive"), ("black", r"black"), ("green", r"green")]


def fetch(url):
    try:
        raw = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 mycotrail-audit"}), timeout=25).read().decode("utf-8", "replace")
    except Exception:
        return None
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"(?s)<(script|style).*?</\1>", " ", raw))))


def urls(latin):
    names = [SYN.get(latin, latin)] + ([latin] if latin in SYN else [])
    out = []
    for n in names:
        g, *sp = n.replace("（", " ").split()
        if not sp:
            continue
        out += [f"https://www.mushroomexpert.com/{g.lower()}_{sp[0].lower()}.html", f"https://www.mykoweb.com/CAF/species/{g}_{sp[0].lower()}.html"]
    return out


def main():
    data = load_data()
    res = {}
    for s in data["species"] + data["poison"]:
        latin = re.split(r"\s*/\s*|（", s["latin"])[0].strip()
        got = None
        for u in urls(latin):
            t = fetch(u)
            if t and len(t) > 1500 and "Not Found" not in t[:300]:
                got = (u, t)
                break
        row = {"latin": s["latin"], "url": got[0] if got else None, "findings": []}
        if got:
            u, t = got
            m = re.search(r"Spore [Pp]rint\s*:?\s*([^.]{0,80})", t)
            row["spore_text"] = m.group(1).strip() if m else ""
            m = re.search(r"(Ecology|Habitat)\s*:?\s*(.{0,260})", t)
            row["ecology"] = m.group(2).strip() if m else ""
            if row["spore_text"] and not {"unknown", "na"} & set(s["sporeTags"]):
                cols = {c for c, rx in COLOURS if re.search(rx, row["spore_text"], re.I)}
                if cols and not cols & set(s["sporeTags"]):
                    row["findings"].append(f"spore print '{row['spore_text']}' vs tags {s['sporeTags']}")
            eco = row["ecology"].lower()
            if re.search(r"wood chip|woodchip|mulch|on (dead |decaying |rotting )?wood|stumps|logs|on the wood", eco) and "wood" not in s["sub"]:
                row["findings"].append(f"ecology mentions wood: '{row['ecology'][:120]}', sub={s['sub']}")
            if re.search(r"lawn|grass|meadow|pasture", eco) and "grass" not in s["sub"]:
                row["findings"].append(f"ecology mentions grass/lawns, sub={s['sub']}")
            if re.search(r"\bon the ground|terrestrial", eco) and not {"ground", "grass"} & set(s["sub"]):
                row["findings"].append(f"ecology mentions ground, sub={s['sub']}")
            if re.search(r"\bvolva\b", t, re.I) and not s["volva"] and re.search(r"with a (sacklike |saccate )?volva|volva (encasing|around)", t, re.I):
                row["findings"].append("page describes a volva, tag volva=False")
            if s["ring"] and re.search(r"without a ring|ring absent|no ring\b", t, re.I):
                row["findings"].append("page mentions no ring, tag ring=True")
        else:
            row["findings"].append("no MushroomExpert / MykoWeb page found under these names")
        res[s["slug"]] = row
        print(s["slug"], "->", row["url"] or "-", "|", "; ".join(row["findings"]) or "ok", flush=True)
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "species_xref.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
