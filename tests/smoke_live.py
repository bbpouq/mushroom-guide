# -*- coding: utf-8 -*-
"""Smoke test of a deployed site (default: the live GitHub Pages site). Run after every deploy and once a day.

1. Waits (up to --wait seconds) until the live index.html and sw.js are byte-identical to public/ in this checkout,
   so it tests what was just deployed and not a cached older copy.
2. Loads every deep link in fingerprint.EXPECTED_ROUTES and checks it opens the right view / 拾菌 sub-page / sheet.
3. Checks that every safety sentence and the emergency phone links are present, and that there are no JavaScript errors.
4. Checks that the service worker installs and the page reports 已可离线.

Usage: python3 tests/smoke_live.py [URL] [--wait 600] [--no-match]
Exit code 1 on any failure; a short report goes to $GITHUB_STEP_SUMMARY when it is set.
"""
import hashlib
import os
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fingerprint import fingerprint, route_problems, safety_problems, source  # noqa: E402

PUBLIC = Path(__file__).resolve().parent.parent / "public"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    url = (args[0] if args else "https://bbpouq.github.io/mushroom-guide/").rstrip("/") + "/"
    wait = int(sys.argv[sys.argv.index("--wait") + 1]) if "--wait" in sys.argv else 600
    problems, notes = [], []

    if "--no-match" not in sys.argv:
        want = {f: hashlib.sha256((PUBLIC / f).read_bytes()).hexdigest() for f in ["index.html", "sw.js"]}
        t0 = time.time()
        while True:
            got = {}
            for f in want:
                try:
                    got[f] = hashlib.sha256(source(url + f + "?v=" + str(int(time.time())))).hexdigest()
                except Exception as e:  # network hiccup: retry
                    got[f] = f"error: {e}"
            if got == want:
                notes.append(f"live files match this commit after {int(time.time() - t0)} s")
                break
            if time.time() - t0 > wait:
                problems.append(f"live files still differ from this commit after {wait} s: " + ", ".join(f for f in want if got[f] != want[f]))
                break
            time.sleep(20)

    with sync_playwright() as p:
        b = p.chromium.launch()
        fp = fingerprint(b, url)
        problems += route_problems(fp) + safety_problems(fp) + fp["errors"]
        notes.append(f"catalogue: {fp['edible']} edible, {fp['toxic']} toxic, {fp['compare']} comparisons, {fp['recipes']} recipes")
        # the service worker installs and the page says it works offline
        ctx = b.new_context(viewport={"width": 390, "height": 844})
        pg = ctx.new_page()
        pg.goto(url + "#guide-offline")
        ok = False
        for _ in range(40):
            pg.wait_for_timeout(500)
            if "已可离线" in (pg.inner_text("#offline-status") or ""):
                ok = True
                break
        if not ok:
            problems.append("the service worker did not report 已可离线 within 20 s")
        ctx.close()
        b.close()

    report = [f"## Smoke test: {url}", ""] + [f"- {n}" for n in notes] + [""]
    report += ["**All checks passed.**"] if not problems else ["**Problems:**", ""] + [f"- {x}" for x in problems]
    print("\n".join(report))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write("\n".join(report) + "\n")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
