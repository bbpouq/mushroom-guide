# -*- coding: utf-8 -*-
"""End-to-end checks for public/ (run after every change).

Setup once:  pip install playwright && python3 -m playwright install chromium
Run:         python3 tests/test_site.py
Starts a local server on public/, checks routing, deep links, back button, finder,
share, offline, sandboxed previews, layering and overflow at 375/768/1024/1440 px.
Exit code 1 on any failure.
"""
import functools
import http.server
import socketserver
import sys
import threading
from pathlib import Path

from playwright.sync_api import sync_playwright

PUBLIC = Path(__file__).resolve().parent.parent / "public"
VIEWS = ["species", "finder", "toxic", "guide", "log", "recipes", "emergency"]
NAV = {375: ".botnav", 768: ".topnav", 1024: ".sidenav__list", 1440: ".sidenav__list"}
failures = []


def check(label, ok):
    print(("PASS " if ok else "FAIL ") + label)
    if not ok:
        failures.append(label)


def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass
    handler = functools.partial(Quiet, directory=str(PUBLIC))
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, f"http://127.0.0.1:{httpd.server_address[1]}/"


# classes that own a top-level style rule; an element carrying two of them may inherit
# unrelated positioning (this is how a badge once floated over the sticky search bar).
# Building blocks meant to be combined with a component class ("btn", "chip", ...) are allowed.
COLLISIONS = r"""() => { const ok = new Set(["latin", "btn", "chip", "icon", "icon-btn"]); const bare = new Set();
  for (const sh of document.styleSheets) { let rs; try { rs = sh.cssRules } catch { continue }
    const walk = R => { for (const r of R) { if (r.cssRules && !r.selectorText) walk(r.cssRules); if (!r.selectorText) continue;
      for (const s of r.selectorText.split(",")) { const m = s.trim().match(/^\.([\w-]+)(?:[:\[][^ ]*)?$/); if (m) bare.add(m[1]); } } };
    walk(rs); }
  const out = new Set();
  for (const el of document.querySelectorAll("body *")) {
    const own = [...el.classList].filter(c => bare.has(c) && !c.includes("--") && !c.startsWith("is-") && !ok.has(c));
    if (own.length > 1) out.add(el.tagName.toLowerCase() + "." + [...el.classList].join("."));
  }
  return [...out]; }"""
OVER_SEARCH = r"""() => { const sb = document.querySelector('.search-bar').getBoundingClientRect(); const bad = new Set();
  for (let x = sb.left + 4; x < sb.right - 4; x += 37) for (let y = sb.top + 3; y < sb.bottom - 3; y += 9) {
    const el = document.elementFromPoint(x, y);
    if (el && !el.closest('.search-bar') && !el.closest('.hdr') && !el.closest('.botnav')) bad.add(el.tagName + '.' + (el.className.baseVal ?? el.className)); }
  return {top: Math.round(sb.top), header: Math.round(document.querySelector('.hdr').getBoundingClientRect().bottom), leaked: [...bad]}; }"""


def run():
    httpd, url = serve()
    html = (PUBLIC / "index.html").read_text(encoding="utf-8")
    with sync_playwright() as p:
        b = p.chromium.launch()

        # ---------- layout at four widths ----------
        for w, h in [(375, 812), (768, 1024), (1024, 768), (1440, 900)]:
            ctx = b.new_context(viewport={"width": w, "height": h}, is_mobile=w < 768, has_touch=w < 1024)
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(url); pg.wait_for_timeout(500)
            coll = set()
            for v in VIEWS:
                pg.evaluate(f"show('{v}')")
                coll |= set(pg.evaluate(COLLISIONS))
                sw = pg.evaluate("document.documentElement.scrollWidth")
                check(f"{w}px {v}: no horizontal overflow ({sw})", sw <= w)
            check(f"{w}px no class collisions {sorted(coll)}", not coll)
            pg.evaluate("show('species')"); pg.evaluate("window.scrollTo(0, 900)"); pg.wait_for_timeout(150)
            ov = pg.evaluate(OVER_SEARCH)
            check(f"{w}px sticky search under header and unobscured {ov}", not ov["leaked"] and (w >= 1024 or ov["top"] == ov["header"]))
            pg.evaluate("window.scrollTo(0, 0)")
            nav = NAV[w]
            for v in ["finder", "toxic", "guide", "log", "species"]:
                pg.click(f'{nav} a[href="#{v}"]'); pg.wait_for_timeout(80)
            check(f"{w}px nav cycles", pg.evaluate("document.querySelector('.view.is-active').id") == "v-species")
            pg.go_back(); pg.wait_for_timeout(150)
            check(f"{w}px back button", pg.evaluate("document.querySelector('.view.is-active').id") == "v-log")
            check(f"{w}px no JS errors {errs}", not errs)
            ctx.close()

        # ---------- deep links, finder, share, offline (phone) ----------
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        pg = ctx.new_page()
        pg.goto(url + "#species"); pg.wait_for_timeout(400)
        pg.click('#v-species a[href="#guide-calendar"]'); pg.wait_for_timeout(1100)
        rows = pg.locator("#cal tbody tr").count()
        check(f"season calendar opens from species view with rows ({rows})",
              pg.evaluate("document.querySelector('.view.is-active').id") == "v-guide" and rows > 30
              and pg.locator("#cal tbody tr >> nth=0").locator("td").count() == 12)
        pg.goto(url + "#sp-tricholoma-matsutake"); pg.wait_for_timeout(700)
        check("deep link opens species sheet", pg.evaluate("document.getElementById('sheet').open") and "松茸" in pg.inner_text("#sheet-title"))
        check("sheet shows a 12-month Pacific Northwest seasonality chart",
              pg.locator("#sheet .obs-chart__col").count() == 12 and "月" in pg.inner_text("#sheet .obs-chart__readout"))
        check("sheet shows the spore print text, not the finder tag", "白色" in pg.inner_text("#sheet") and "white" not in pg.inner_text("#sheet"))
        pg.click('#sheet a[href="#guide-check"]'); pg.wait_for_timeout(1100)
        check("sheet links to the before-you-eat checklist",
              pg.evaluate("document.querySelector('.view.is-active').id") == "v-guide" and not pg.evaluate("document.getElementById('sheet').open")
              and 0 <= pg.evaluate("document.getElementById('guide-check').getBoundingClientRect().top") < 200)
        pg.click("#eat-check li >> nth=0"); pg.click("#eat-check li >> nth=1")
        check("checklist counts ticks", pg.inner_text("#eat-check-count") == "已核对 2 / 9")
        pg.goto(url + "#sp-tricholoma-matsutake"); pg.wait_for_timeout(700)
        pg.click('#sheet a[href="#recipes"]'); pg.wait_for_timeout(300)
        check("recipes reachable on a phone from a species sheet", pg.evaluate("document.querySelector('.view.is-active').id") == "v-recipes")
        pg.goto(url + "#sp-tricholoma-matsutake"); pg.wait_for_timeout(700)
        pg.click('#sheet a[data-log-sp]'); pg.wait_for_timeout(1100)
        check("sheet 'log this find' opens the log with the species chosen",
              pg.evaluate("document.querySelector('.view.is-active').id") == "v-log" and pg.input_value("#finds-sp") == "tricholoma-matsutake")
        pg.fill("#finds-place", "测试步道"); pg.click('#finds-form button[type="submit"]'); pg.wait_for_timeout(200)
        pg.reload(); pg.wait_for_timeout(700)
        check("a saved find survives a reload", "松茸" in pg.inner_text("#finds-list") and "测试步道" in pg.inner_text("#finds-list"))
        pg.click("#finds-list [data-del]"); pg.wait_for_timeout(100)
        armed = pg.locator("#finds-list .finds__item").count() == 1
        pg.click("#finds-list [data-del]"); pg.wait_for_timeout(200)
        check("deleting a find takes two taps", armed and pg.locator("#finds-list .finds__item").count() == 0)
        pg.goto(url + "#sp-tricholoma-matsutake"); pg.wait_for_timeout(700)
        pg.click("[data-close]"); pg.wait_for_timeout(150)
        check("closing a directly opened sheet goes to #species", pg.evaluate("location.hash") == "#species")
        pg.click(".sp-card >> nth=3"); pg.wait_for_timeout(250)
        check("card click sets #sp- hash", pg.evaluate("location.hash").startswith("#sp-"))
        pg.go_back(); pg.wait_for_timeout(250)
        check("back closes sheet", not pg.evaluate("document.getElementById('sheet').open"))
        for target in ["tx-galerina-marginata", "cmp-matsutake"]:
            pg.goto(url + "#" + target); pg.wait_for_timeout(1100)
            top = pg.evaluate(f"document.getElementById('{target}').getBoundingClientRect().top")
            check(f"#{target} scrolls just under header (top={round(top)})", 0 <= top < 200)
        pg.click(".sos-pill"); pg.wait_for_timeout(150)
        check("SOS -> emergency view with tel link", pg.evaluate("document.querySelector('.view.is-active').id") == "v-emergency"
              and pg.locator('a[href="tel:18002221222"]').count() == 1)
        pg.click('.botnav a[href="#finder"]'); pg.wait_for_timeout(100)
        for k, v in [("hym", "gills"), ("sub", "wood"), ("spore", "white")]:
            pg.click(f'[data-f="{k}"][data-v="{v}"]'); pg.wait_for_timeout(50)
        res = pg.inner_text("#finder-results")
        check("finder gills+wood+white", "发光类脐菇" in res and "蜜环菌" in res and "纹缘盔孢伞" not in res)
        pg.click("#finder-reset")
        for k, v in [("hym", "gills"), ("sub", "ground"), ("spore", "white"), ("volva", "no")]:
            pg.click(f'[data-f="{k}"][data-v="{v}"]'); pg.wait_for_timeout(50)
        res = pg.inner_text("#finder-results")
        check("finder keeps deadly amanitas when volva=no", "毒鹅膏" in res and "菌托常埋在土里" in res)
        ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=url.rstrip("/"))
        pg.goto(url + "#sp-boletus-edulis"); pg.wait_for_timeout(500)
        pg.evaluate("navigator.share = undefined"); pg.click("[data-share]"); pg.wait_for_timeout(250)
        check("share copies deep link", pg.evaluate("navigator.clipboard.readText()").endswith("#sp-boletus-edulis"))
        pg.goto(url + "#guide"); pg.wait_for_timeout(2500)
        check("service worker ready", "已可离线" in pg.inner_text("#offline-status"))
        ctx.set_offline(True); pg.reload(); pg.wait_for_timeout(1000)
        check("loads offline", pg.locator(".sp-card").count() > 50)
        ctx.close()

        # ---------- sandboxed preview (how many apps show an attached HTML file) ----------
        host = b.new_page(viewport={"width": 390, "height": 844})
        host.set_content('<iframe id=f sandbox="allow-scripts" style="width:390px;height:844px;border:0"></iframe>')
        host.eval_on_selector("#f", "(f, h) => f.srcdoc = h", html); host.wait_for_timeout(900)
        fr = host.frames[1]
        ok = []
        for v in ["finder", "toxic", "guide", "log", "species"]:
            fr.click(f'.botnav a[href="#{v}"]'); host.wait_for_timeout(80)
            ok.append(fr.evaluate("document.querySelector('.view.is-active').id") == f"v-{v}")
        fr.click(".sp-card >> nth=0"); host.wait_for_timeout(200)
        opened = fr.evaluate("document.getElementById('sheet').open")
        check(f"sandbox: tabs {ok}, sheet opens, frame survives", all(ok) and opened and len(host.frames) == 2)
        b.close()
    httpd.shutdown()
    print(f"\n{'ALL PASSED' if not failures else str(len(failures)) + ' FAILED'}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    run()
