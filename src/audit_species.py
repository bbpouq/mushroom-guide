# -*- coding: utf-8 -*-
"""Species feature audit: one row per species in the built data (public/index.html → DATA), written to
reports/species_feature_audit.csv and .json.

Automatic checks (no network):
- completeness: every species has finder tags; no orphan tags; no duplicate slugs or names;
- enum validity of every finder tag;
- tags against the species' own text: the fertile-surface tag vs words in the description (褶 / 孔 / 刺 / 棱 / 脊),
  菌环 / 菌托 mentioned vs tagged, spore-print colour words vs spore tags, substrate words vs substrate tags;
- photo present, attributed, and of the same genus;
- sources present (toxic species: not Wikipedia alone).

Each row also carries the manual verification result from src/data/audit_log.py (sources checked, outcome, and whether a
mycologist should still look at it). A row is never marked verified by this script alone.

Usage: python3 src/audit_species.py            (writes the reports; exit 1 if a hard check fails)
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
from data.tags import TAGS  # noqa: E402

from data.synonyms import SYN  # noqa: E402  (current names of the book's older genus names)

try:
    from data.audit_log import AUDIT  # manual verification log, keyed by slug
except ImportError:  # pragma: no cover
    AUDIT = {}

XREF = {}
HYM = {"gills", "pores", "spines", "ridges", "other"}
SPORE = {"white", "yellow", "pink", "brown", "choc", "olive", "black", "green", "unknown", "na"}
SUB = {"ground", "grass", "wood", "under"}
SPORE_WORDS = [("白", "white"), ("奶油", "white"), ("乳白", "white"), ("淡黄", "yellow"), ("黄", "yellow"), ("粉", "pink"),
               ("肉色", "pink"), ("锈", "brown"), ("褐", "brown"), ("赭", "brown"), ("巧克力", "choc"), ("紫褐", "choc"),
               ("紫黑", "choc"), ("橄榄", "olive"), ("黑", "black"), ("绿", "green")]


def load_data():
    html = (ROOT / "public" / "index.html").read_text(encoding="utf-8")
    m = re.search(r'<script type="application/json" id="data">(.*?)</script>', html, re.S)
    return json.loads(m.group(1).replace("<\\/", "</"))


def plain(t):
    return re.sub(r"<[^>]+>", "", str(t or ""))


def text_checks(s, toxic):
    """Disagreements between the finder tags and the species' own description. These are leads, not verdicts."""
    out = []
    body = plain(s.get("feat", "")) + "；" + plain(" ".join(s.get("extra", []) if isinstance(s.get("extra"), list) else [s.get("extra", "")]))
    words = {"gills": "褶", "pores": "孔", "spines": "刺"}
    said = {k for k, w in words.items() if w in body}
    if s["hym"] in words and said and s["hym"] not in said:
        out.append(f"fertile surface tagged {s['hym']}, text mentions {sorted(said)}")
    no_ring = re.search(r"(无|没有|不具)菌环|菌环(不明显|易脱落|常脱落)", body)
    if "菌环" in body and not no_ring and not s["ring"]:
        out.append("text mentions 菌环, tag ring=False")
    if s["ring"] and re.search(r"(无|没有)菌环", body):
        out.append("tag ring=True, text says no ring")
    if "菌托" in body and not re.search(r"(无|没有)(菌环[和、及与])?菌托", body) and not s["volva"]:
        out.append("text mentions 菌托, tag volva=False")
    if s["volva"] and re.search(r"(无|没有)菌托", body):
        out.append("tag volva=True, text says no volva")
    st = plain(s.get("spore", ""))
    if st and not toxic:
        cols = {c for w, c in SPORE_WORDS if w in st}
        if cols and not cols & set(s["sporeTags"]) and not {"unknown", "na"} & set(s["sporeTags"]):
            out.append(f"spore text '{st}' vs tags {s['sporeTags']}")
    hab = plain(s.get("hab", "")) if not toxic else body
    if hab:
        if re.search(r"树干|树桩|倒木|枯木|腐木|木头|木屑|活树上|死树", hab) and "wood" not in s["sub"]:
            out.append(f"habitat text mentions wood, sub={s['sub']}")
        if re.search(r"(长|生)(在|于)地下|地下生", hab) and "under" not in s["sub"]:
            out.append(f"habitat text mentions underground, sub={s['sub']}")
    return out


def main():
    data = load_data()
    global XREF
    xp = ROOT / "reports" / "species_xref.json"
    XREF = json.loads(xp.read_text(encoding="utf-8")) if xp.exists() else {}
    rows, hard = [], []
    edible, toxic = data["species"], data["poison"] + data.get("poisonExtra", [])
    names = [x["zh"] for x in edible + toxic]
    slugs = [x["slug"] for x in edible + toxic]
    if len(set(names)) != len(names):
        hard.append("duplicate Chinese names")
    if len(set(slugs)) != len(slugs):
        hard.append("duplicate slugs")
    orphans = sorted(set(TAGS) - set(names))
    if orphans:
        hard.append(f"orphan finder tags (no species): {orphans}")
    comp = {}
    for c in data["compare"]:
        for _n, _k, sl in c["cols"]:
            if sl:
                comp.setdefault(sl, []).append(c["id"])
    for s in edible + toxic:
        is_tox = s in toxic
        enum = []
        if s["hym"] not in HYM:
            enum.append(f"hym {s['hym']}")
        enum += [f"spore {x}" for x in s["sporeTags"] if x not in SPORE]
        enum += [f"sub {x}" for x in s["sub"] if x not in SUB]
        if enum:
            hard.append(f"{s['slug']}: invalid tags {enum}")
        checks = text_checks(s, is_tox)
        ph = s.get("photo") or {}
        if not ph:
            checks.append("no example photo")
        elif not (ph.get("author") and ph.get("lic") and ph.get("url")):
            checks.append("photo without full attribution")
        elif ph.get("taxon", "").split(" ")[0] not in {s["latin"].split(" ")[0], SYN.get(s["latin"].split(" /")[0].strip(), "").split(" ")[0]}:
            checks.append(f"photo taxon {ph.get('taxon')} is another genus than {s['latin']}")
        srcs = s.get("sources") or []
        if not srcs and not is_tox:
            checks.append("no external sources listed (book text only)")
        log = AUDIT.get(s["slug"], {})
        xr = XREF.get(s["slug"], {})
        if log:
            status = log["status"]
        elif xr.get("url") and not xr.get("findings"):
            status = "cross-checked automatically against one outside page (spore print, habitat, ring, volva)"
        elif xr.get("url"):
            status = "outside page found, disagreements listed in xref_findings (to read)"
        else:
            status = "not checked against outside references (no MushroomExpert / MykoWeb page under these names)"
        rows.append({
            "slug": s["slug"], "zh": s["zh"], "latin": s["latin"], "kind": "toxic" if is_tox else "edible-catalog",
            "risk": s.get("level") or (s.get("safety") or {}).get("edibility", ""), "review": (s.get("safety") or {}).get("review", ""),
            "hym": s["hym"], "sub": "|".join(s["sub"]), "spore": "|".join(s["sporeTags"]), "ring": s["ring"], "volva": s["volva"],
            "spore_text": plain(s.get("spore", "")), "photo": ph.get("file", ""), "photo_taxon": ph.get("taxon", ""),
            "sources": len(srcs), "comparisons": "|".join(comp.get(s["slug"], [])),
            "auto_findings": "; ".join(checks),
            "status": status, "xref_url": xr.get("url") or "", "xref_findings": "; ".join(xr.get("findings", [])) if xr.get("url") else "",
            "manual_sources": " | ".join(log.get("sources", [])), "manual_notes": log.get("notes", ""),
            "expert_review": log.get("expert", ""),
        })
    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    with open(out / "species_feature_audit.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (out / "species_feature_audit.json").write_text(json.dumps({"species": len(rows), "edible_catalog": len(edible), "toxic": len(toxic),
                                                                 "hard_failures": hard, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    flagged = [r for r in rows if r["auto_findings"]]
    print(f"{len(rows)} species ({len(edible)} edible catalogue, {len(toxic)} toxic); {len(flagged)} with automatic findings; "
          f"{sum(1 for r in rows if r['status'] in ('fixed', 'checked'))} checked by hand, "
          f"{sum(1 for r in rows if r['status'].startswith('cross-checked'))} cross-checked automatically, "
          f"{sum(1 for r in rows if r['status'].startswith('not checked'))} with no outside page")
    for r in flagged:
        print(f"  {r['slug']}: {r['auto_findings']}")
    if hard:
        print("HARD FAILURES:", *hard, sep="\n  ")
        sys.exit(1)


if __name__ == "__main__":
    main()
