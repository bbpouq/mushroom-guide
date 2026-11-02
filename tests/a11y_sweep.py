# -*- coding: utf-8 -*-
"""Accessibility and layout sweep: axe-core (WCAG 2.2 AA) and horizontal overflow on every view, every 拾菌 sub-page and
the finder's states, at several widths, light and dark, outdoor mode off and on.

Needs axe-core: npm install axe-core@4.14.0 (or set AXE_PATH to axe.min.js).
Usage: python3 tests/a11y_sweep.py [--quick]   (--quick: 375 and 1440 px only)
Exit code 1 on any violation or overflow; a summary goes to $GITHUB_STEP_SUMMARY when it is set.
"""
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_site import serve  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
AXE = os.environ.get("AXE_PATH") or str(ROOT / "node_modules" / "axe-core" / "axe.min.js")
VIEWS = ["home", "species", "finder", "toxic", "guide", "recipes", "learn", "log", "emergency"] + \
    ["explore-" + s for s in ["now", "intel", "cal", "hab", "rules", "prep", "pick", "safety", "offline", "field"]]
WIDTHS = [(375, 812), (1440, 900)] if "--quick" in sys.argv else [(320, 640), (375, 812), (390, 844), (768, 1024), (1024, 768), (1440, 900)]
RULES = "{runOnly: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa']}"


def main():
    axe = Path(AXE).read_text(encoding="utf-8")
    httpd, url = serve()
    found, combos = [], 0
    with sync_playwright() as p:
        b = p.chromium.launch()
        for w, h in WIDTHS:
            for scheme in ["light", "dark"]:
                for field in [False, True]:
                    ctx = b.new_context(viewport={"width": w, "height": h}, color_scheme=scheme, is_mobile=w < 768, has_touch=w < 1024, reduced_motion="reduce")
                    if field:
                        ctx.add_init_script("try{localStorage.setItem('mushroom-guide:field','on')}catch(e){}")
                    pg = ctx.new_page()
                    pg.goto(url); pg.wait_for_timeout(500)
                    pg.add_script_tag(content=axe)
                    tag = f"{w}/{scheme}{'/outdoor' if field else ''}"

                    def sweep(name):
                        nonlocal combos
                        combos += 1
                        v = pg.evaluate(f"axe.run(document, {RULES}).then(r => r.violations.map(v => v.id + ' (' + v.nodes.length + '): ' + v.nodes.slice(0, 2).map(n => String(n.target)).join(' | ')))")
                        sw = pg.evaluate("document.documentElement.scrollWidth")
                        found.extend(f"{tag} {name}: {x}" for x in v)
                        if sw > w:
                            found.append(f"{tag} {name}: page is {sw}px wide")
                    for v in VIEWS:
                        pg.evaluate(f"navigate('{v}')"); pg.wait_for_timeout(350)
                        sweep(v)
                    # the finder's states: intro, a question, results with an unknown answer, a conflict
                    pg.evaluate("navigate('finder')"); pg.wait_for_timeout(300)
                    if pg.locator("#finder-start").count():
                        pg.click("#finder-start")
                    pg.click('[data-f="hym"][data-v="gills"]'); pg.click('#finder-steps [data-f="volva"][data-unk="unseen"]'); pg.wait_for_timeout(250)
                    sweep("finder results")
                    pg.click('#finder-steps .wiz__dot[data-step="3"]'); pg.click('[data-f="ring"][data-v="no"]'); pg.wait_for_timeout(250)
                    sweep("finder conflict")
                    ctx.close()
        b.close()
    httpd.shutdown()
    lines = [f"## Accessibility sweep: {combos} combinations", ""]
    lines += ["**0 axe violations, no horizontal overflow.**"] if not found else [f"**{len(found)} problems:**", ""] + [f"- {x}" for x in found[:80]]
    print("\n".join(lines))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    sys.exit(1 if found else 0)


if __name__ == "__main__":
    main()
