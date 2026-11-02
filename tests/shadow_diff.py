# -*- coding: utf-8 -*-
"""Shadow test: run the same behavioural fingerprint on a candidate build (public/ of this checkout, served locally)
and on production (the live site), and report every difference.

Differences in routes or catalogue sizes are reported, not failed: they are often the point of a change. It fails only
when the candidate is worse than production on things that must never regress: a safety sentence or an emergency link
that production has and the candidate lost, a deep link that production opens correctly and the candidate does not,
or JavaScript errors that production does not have.

Usage: python3 tests/shadow_diff.py [PROD_URL]
"""
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fingerprint import EXPECTED_ROUTES, TELS, fingerprint  # noqa: E402
from test_site import serve  # noqa: E402


def main():
    prod_url = (sys.argv[1] if len(sys.argv) > 1 else "https://bbpouq.github.io/mushroom-guide/").rstrip("/") + "/"
    httpd, cand_url = serve()
    with sync_playwright() as p:
        b = p.chromium.launch()
        cand = fingerprint(b, cand_url)
        try:
            prod = fingerprint(b, prod_url)
        except Exception as e:  # production unreachable: report, do not block the candidate
            prod = None
            prod_err = str(e)
        b.close()
    httpd.shutdown()

    lines, fail = ["## Shadow test: this build vs production", "", f"Production: {prod_url}", ""], []
    if prod is None:
        lines.append(f"Production could not be loaded ({prod_err}); only the candidate's own checks ran.")
        prod = {"routes": {}, "safety": {}, "tels": [], "errors": [], "edible": "?", "toxic": "?", "compare": "?", "recipes": "?"}
    lines += ["| | production | this build |", "|---|---|---|"]
    for k in ["edible", "toxic", "compare", "recipes"]:
        mark = "" if prod[k] == cand[k] else " (changed)"
        lines.append(f"| {k} | {prod[k]} | {cand[k]}{mark} |")
    lines.append("")
    route_diff = [h for h in EXPECTED_ROUTES if prod["routes"].get(h) != cand["routes"].get(h)]
    if route_diff:
        lines += ["Routes that behave differently:", ""] + [f"- `#{h}`: production {prod['routes'].get(h)}, this build {cand['routes'].get(h)}" for h in route_diff] + [""]
    for h in route_diff:  # a regression only when production was right and the candidate is not
        if prod["routes"].get(h) == EXPECTED_ROUTES[h] and cand["routes"].get(h) != EXPECTED_ROUTES[h]:
            fail.append(f"deep link #{h} regressed: {cand['routes'].get(h)} instead of {EXPECTED_ROUTES[h]}")
    for s, ok in cand["safety"].items():
        if not ok:
            fail.append(f"safety sentence missing in this build: {s}")
    for t in TELS:
        if t not in cand["tels"]:
            fail.append(f"emergency link missing in this build: {t}")
    new_errors = [e for e in cand["errors"] if e not in prod["errors"]]
    fail += [f"new JavaScript error: {e}" for e in new_errors]
    lines += ["**No regressions against production.**"] if not fail else ["**Regressions:**", ""] + [f"- {x}" for x in fail]
    print("\n".join(lines))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
