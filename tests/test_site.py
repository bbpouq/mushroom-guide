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
VIEWS = ["home", "species", "finder", "toxic", "guide", "log", "recipes", "emergency"]
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


def settle(pg, limit=5000):
    """Wait until smooth scrolling has stopped (scrollY unchanged across two reads)."""
    last, waited = None, 0
    while waited < limit:
        pg.wait_for_timeout(150); waited += 150
        y = pg.evaluate("scrollY")
        if y == last:
            return
        last = y


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
            pg.evaluate("show('species')"); pg.evaluate("window.scrollTo(0, document.getElementById('grid').getBoundingClientRect().top + scrollY + 300)"); pg.wait_for_timeout(150)
            ov = pg.evaluate(OVER_SEARCH)
            check(f"{w}px sticky search under header and unobscured {ov}", not ov["leaked"] and (w >= 1024 or ov["top"] == ov["header"]))
            pg.evaluate("window.scrollTo(0, 0)")
            nav = NAV[w]
            for v in ["finder", "toxic", "home", "log", "species"]:
                pg.click(f'{nav} a[href="#{v}"]'); pg.wait_for_timeout(80)
            check(f"{w}px nav cycles", pg.evaluate("document.querySelector('.view.is-active').id") == "v-species")
            pg.go_back(); pg.wait_for_timeout(150)
            check(f"{w}px back button", pg.evaluate("document.querySelector('.view.is-active').id") == "v-log")
            check(f"{w}px no JS errors {errs}", not errs)
            ctx.close()

        # ---------- deep links, finder, share, offline (phone) ----------
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=3)
        pg = ctx.new_page()
        pg.goto(url); pg.wait_for_timeout(400)
        check("the site opens on the home view", pg.evaluate("document.querySelector('.view.is-active').id") == "v-home")
        pg.fill("#home-q", "amanita"); pg.wait_for_timeout(150)
        first = pg.locator("#home-results .home-results__item >> nth=0")
        check("home search lists toxic matches first", "home-results__item--toxic" in first.get_attribute("class")
              and pg.locator("#home-results .home-results__item").count() >= 3)
        first.click(); pg.wait_for_timeout(500)
        check("a home search result opens its sheet over the home view", pg.evaluate("document.getElementById('sheet').open")
              and pg.evaluate("document.querySelector('.view.is-active').id") == "v-home")
        pg.click("#sheet [data-close]"); pg.wait_for_timeout(300)
        pg.fill("#home-q", "zzzz"); pg.wait_for_timeout(150)
        check("an empty home search says that not listed is not safe", "不代表它安全" in pg.inner_text("#home-results"))
        pg.fill("#home-q", "")
        check("home has four entry cards and a season section", pg.locator(".home-entry__item").count() == 4
              and pg.locator("#season-cols .season__col").count() == 2)
        pg.goto(url + "#guide-gloss"); pg.wait_for_timeout(900)
        check("#guide-gloss opens the glossary", pg.evaluate("document.getElementById('guide-gloss').open"))
        pg.goto(url + "#home"); pg.wait_for_timeout(400)
        name0 = pg.inner_text("#today-name")
        txt = pg.inner_text("#today")
        check(f"'today' card shows a species ({name0}) with how to eat it and the safety line",
              bool(name0) and "怎么吃" in txt and "有任何疑问，就不要吃" in txt and "不能只凭照片鉴定" in txt
              and pg.evaluate("document.querySelector('#today .today__img').naturalWidth > 0"))
        size = []
        for _ in range(10):
            size.append(pg.evaluate("[document.getElementById('today').offsetHeight, Math.round(document.querySelector('#today [data-today=\"1\"]').getBoundingClientRect().top + scrollY)]"))
            pg.click('#today [data-today="1"]'); pg.wait_for_timeout(40)
        check(f"'today' card keeps one size and its arrows stay put across days {sorted(set(map(tuple, size)))}",
              len(set(map(tuple, size))) == 1)
        pg.click('#today [data-today="0"]'); pg.wait_for_timeout(100)
        hd = pg.evaluate("document.querySelector('#today .today__img').currentSrc")
        check(f"'today' photo uses the high-resolution copy on a dense phone screen ({hd.rsplit('/', 1)[-1]})", hd.endswith("-hd.webp"))
        pg.click('#today [data-today="1"]'); pg.wait_for_timeout(150)
        name1 = pg.inner_text("#today-name"); kick1 = pg.inner_text("#today .today__kicker")
        pg.click('#today [data-today="0"]'); pg.wait_for_timeout(150)
        check(f"'today' card steps to the next day ({name1}) and back to today", "明天" in kick1 and pg.inner_text("#today-name") == name0
              and "今日一菌" in pg.inner_text("#today .today__kicker"))
        pg.click("#today .btn--primary"); pg.wait_for_timeout(500)
        check("'today' card opens the full species sheet",
              pg.evaluate("document.getElementById('sheet').open") and pg.inner_text("#sheet-title") == name0)
        pg.goto(url + "#rc-bruschetta"); pg.wait_for_timeout(900)
        check("recipe deep link opens the recipe", pg.evaluate("document.querySelector('.view.is-active').id") == "v-recipes"
              and pg.evaluate("document.querySelector('#rc-bruschetta details').open"))
        pg.goto(url + "#home"); pg.wait_for_timeout(400)
        n_now = pg.locator("#now-track .now__item").count()
        pg.click("#now-track .now__item >> nth=0"); pg.wait_for_timeout(500)
        check(f"'this month' strip lists species ({n_now}) and opens one", n_now > 0 and pg.evaluate("document.getElementById('sheet').open"))
        pg.goto(url + "#guide"); pg.wait_for_timeout(400)
        pg.click('#v-guide [data-jump="guide-calendar"]'); pg.wait_for_timeout(1100)
        rows = pg.locator("#cal tbody tr").count()
        check(f"season calendar opens from the guide view with rows ({rows})",
              pg.evaluate("document.querySelector('.view.is-active').id") == "v-guide" and rows > 30
              and pg.locator("#cal tbody tr >> nth=0").locator("td").count() == 12)
        pg.goto(url + "#sp-tricholoma-matsutake"); pg.wait_for_timeout(700)
        check("deep link opens species sheet", pg.evaluate("document.getElementById('sheet').open") and "松茸" in pg.inner_text("#sheet-title"))
        check("sheet shows a 12-month Pacific Northwest seasonality chart",
              pg.locator("#sheet .obs-chart__col").count() == 12 and "月" in pg.inner_text("#sheet .obs-chart__readout"))
        pg.wait_for_timeout(500)
        check("sheet shows an example photo with author and licence",
              pg.evaluate("(() => { const i = document.querySelector('#sheet .photo__img'); return !!i && i.complete && i.naturalWidth > 0; })()")
              and "CC" in pg.inner_text("#sheet .photo__cap") and "不能只凭照片鉴定" in pg.inner_text("#sheet .photo__cap"))
        check("sheet shows the spore print text, not the finder tag", "白色" in pg.inner_text("#sheet") and "white" not in pg.inner_text("#sheet"))
        pg.click('#sheet a[href="#guide-check"]'); settle(pg)
        check("sheet links to the before-you-eat checklist",
              pg.evaluate("document.querySelector('.view.is-active').id") == "v-guide" and not pg.evaluate("document.getElementById('sheet').open")
              and 0 <= pg.evaluate("document.getElementById('guide-check').getBoundingClientRect().top") < 200)
        pg.click("#eat-check li >> nth=0"); pg.click("#eat-check li >> nth=1")
        check("checklist counts ticks", pg.inner_text("#eat-check-count") == "已核对 2 / 9")
        pg.goto(url + "#sp-tricholoma-matsutake"); pg.wait_for_timeout(700)
        pg.click('#sheet a[href="#recipes"]'); pg.wait_for_timeout(300)
        check("recipes reachable on a phone from a species sheet", pg.evaluate("document.querySelector('.view.is-active').id") == "v-recipes")
        pg.goto(url + "#guide"); pg.wait_for_timeout(400)
        pg.click('#v-guide .jump-row a[href="#recipes"]'); pg.wait_for_timeout(300)
        check("recipes reachable from the guide's jump row", pg.evaluate("document.querySelector('.view.is-active').id") == "v-recipes")
        n_rc = pg.locator("#rc-grid .rc-card").count()
        check(f"recipes: {n_rc} cards, each with a photo", n_rc >= 20 and pg.locator("#rc-grid .rc-card__img").count() == n_rc)
        pg.click('#rc-filter [data-rc-style="中式"]'); pg.wait_for_timeout(150)
        styles = pg.eval_on_selector_all("#rc-grid .rc-card__meta span:last-child", "els => els.map(e => e.textContent)")
        check("recipe filter shows only that style", styles and all(x == "中式" for x in styles))
        pg.click('#rc-filter [data-rc-style="全部"]')
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
        pg.goto(url + "#sp-tricholoma-matsutake"); pg.reload(); pg.wait_for_timeout(700)
        pg.click("[data-close]"); pg.wait_for_timeout(150)
        check("closing a directly opened sheet goes to #species", pg.evaluate("location.hash") == "#species")
        pg.click(".sp-card >> nth=3"); pg.wait_for_timeout(250)
        check("card click sets #sp- hash", pg.evaluate("location.hash").startswith("#sp-"))
        pg.go_back(); pg.wait_for_timeout(250)
        check("back closes sheet", not pg.evaluate("document.getElementById('sheet').open"))
        pg.goto(url + "#tx-galerina-marginata"); pg.reload(); pg.wait_for_timeout(800)
        check("#tx- deep link opens that toxic species' sheet",
              pg.evaluate("document.getElementById('sheet').open") and "纹缘盔孢伞" in pg.inner_text("#sheet-title")
              and pg.evaluate("document.querySelector('.view.is-active').id") == "v-toxic")
        pg.click("#sheet [data-close]"); pg.wait_for_timeout(300)
        check("closing a toxic sheet returns to #toxic", pg.evaluate("location.hash") == "#toxic")
        n_tx = pg.locator("#tox-grid .sp-card").count()
        pg.click("#tox-grid .sp-card >> nth=0"); pg.wait_for_timeout(500)
        check(f"toxic list uses the species card pattern ({n_tx} cards) and opens a sheet",
              n_tx == 22 and pg.locator("#tox-grid .sp-card__photo").count() == n_tx and pg.evaluate("document.getElementById('sheet').open"))
        pg.goto(url + "#sp-tricholoma-matsutake"); pg.wait_for_timeout(700)
        body = pg.inner_text("#sheet-body")
        check("species sheet: photo first, quick facts, sections and typed sources",
              pg.evaluate("document.querySelector('#sheet-body .photo').compareDocumentPosition(document.getElementById('sheet-title')) & 4") > 0
              and pg.locator("#sheet-body .sheet__q").count() == 3 and pg.locator("#sheet-body .sheet__sec").count() == 5
              and pg.locator("#sheet-body .src-type").count() >= 2 and pg.locator("#sheet-body .look-pair").count() >= 1)
        pg.click("#sheet-body .photo__zoom"); pg.wait_for_timeout(300)
        check("tapping a photo opens the high-resolution copy full screen", pg.evaluate("document.getElementById('zoom').open")
              and pg.evaluate("document.getElementById('zoom-img').src").endswith("-hd.webp") and "不能只凭照片鉴定" in pg.inner_text("#zoom-cap"))
        pg.click("#zoom [data-zoom-close]"); pg.wait_for_timeout(150)
        check("closing the zoom leaves the sheet open", not pg.evaluate("document.getElementById('zoom').open") and pg.evaluate("document.getElementById('sheet').open"))
        pg.click("#sheet [data-close]"); pg.wait_for_timeout(300)
        pg.goto(url + "#cmp-chanterelle"); pg.wait_for_timeout(1000)
        card = "#cmp-chanterelle"
        sw0 = pg.locator(f"{card} .cmp__tab").count()
        pg.click(f'{card} [data-cmp-k="1"]'); pg.wait_for_timeout(100)
        one = pg.inner_text(f"{card} .cmp__one")
        pg.click(f'{card} [data-cmp-mode="side"]'); pg.wait_for_timeout(100)
        check("comparisons show photos and switch between one-at-a-time and side by side",
              sw0 == 4 and "发光类脐菇" in one and pg.locator(f"{card} .cmp__col").count() == 4
              and pg.locator(f"{card} .cmp__pic img").count() >= 3 and "不足以单独确认" in pg.inner_text(card))
        for target in ["cmp-matsutake"]:
            pg.goto(url + "#" + target); pg.wait_for_timeout(1100)
            top = pg.evaluate(f"document.getElementById('{target}').getBoundingClientRect().top")
            check(f"#{target} scrolls just under header (top={round(top)})", 0 <= top < 200)
        pg.click(".sos-pill"); pg.wait_for_timeout(150)
        check("SOS -> emergency view with tel link", pg.evaluate("document.querySelector('.view.is-active').id") == "v-emergency"
              and pg.locator('a[href="tel:18002221222"]').count() == 1)
        pg.click('.botnav a[href="#finder"]'); pg.wait_for_timeout(100)
        pg.locator("#model").scroll_into_view_if_needed(); pg.wait_for_timeout(400)
        pg.wait_for_timeout(1500)  # the WebGL version loads lazily; the 2D canvas is the fallback
        painted = pg.evaluate("""(() => { const st = document.querySelector('.model__stage'), c = st.querySelector('.model__canvas');
            if (st.classList.contains('is-webgl')) return c.width > 0 && c.height > 0 ? 999 : 0;
            const d = c.getContext('2d').getImageData(0, 0, c.width, c.height).data;
            let n = 0; for (let i = 3; i < d.length; i += 4 * 97) if (d[i] > 0) n++; return n; })()""")
        pg.click('#model-parts [data-model-part="volva"]'); pg.wait_for_timeout(200)
        check(f"3D model draws ({painted} samples) and explains a picked part", painted > 50 and "菌托" in pg.inner_text("#model-desc"))
        pg.click('#finder-steps .wiz__dot[data-step="3"]'); pg.wait_for_timeout(100)
        pg.click('#finder-steps [data-model-part="ring"]'); pg.wait_for_timeout(300)
        check("a finder question's 'see on model' selects that part",
              pg.get_attribute('#model-parts [data-model-part="ring"]', "aria-pressed") == "true")
        pg.click('#finder-steps .wiz__dot[data-step="0"]'); pg.wait_for_timeout(100)
        check("the finder asks one question at a time with progress", pg.locator("#finder-steps .wiz__q").count() == 1
              and pg.locator("#finder-steps .wiz__dot").count() == 5 and "1 / 5" in pg.inner_text("#finder-steps legend"))
        for k, v in [("hym", "gills"), ("sub", "wood"), ("spore", "white")]:
            pg.click(f'[data-f="{k}"][data-v="{v}"]'); pg.wait_for_timeout(50)
        res = pg.inner_text("#finder-results")
        check("finder results do not widen the phone page", pg.evaluate("document.documentElement.scrollWidth") <= 390)
        check("finder gills+wood+white", "发光类脐菇" in res and "蜜环菌" in res and "纹缘盔孢伞" not in pg.inner_text(".res-block--toxic"))
        check("finder shows what matched and what is unchecked, with no score",
              "相符：" in res and "未确认：" in res and "%" not in res and "还没确认 2 项" in res)
        pg.click('[data-wiz="prev"]'); pg.wait_for_timeout(50)
        check("the finder can step back to change an answer", "3 / 5" in pg.inner_text("#finder-steps legend")
              and pg.get_attribute('[data-f="spore"][data-v="white"]', "aria-pressed") == "true")
        pg.click("#finder-reset")
        for k, v in [("hym", "gills"), ("sub", "ground"), ("spore", "white"), ("ring", ""), ("volva", "no")]:
            pg.click(f'[data-f="{k}"][data-v="{v}"]'); pg.wait_for_timeout(50)
        res = pg.inner_text("#finder-results")
        check("finder keeps deadly amanitas when volva=no, warns early and allows skipping",
              "毒鹅膏" in res and "菌托常埋在土里" in res and "仍可能是这些致命毒菌" in res and "菌环" in pg.inner_text(".res-open"))
        pg.click("#finder-reset"); pg.click('[data-f="hym"][data-v="gills"]'); pg.click('[data-f="sub"][data-v="ground"]')
        pg.click('[data-f="spore"][data-v="white"]'); pg.click('[data-f="ring"][data-v=""]'); pg.click('[data-f="volva"][data-v="yes"]'); pg.wait_for_timeout(50)
        check("seeing a volva raises the amanita alarm at once", "你看到了菌托" in pg.inner_text("#finder-results"))
        ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=url.rstrip("/"))
        pg.goto(url + "#sp-boletus-edulis"); pg.wait_for_timeout(500)
        pg.evaluate("navigator.share = undefined"); pg.click("[data-share]"); pg.wait_for_timeout(250)
        check("share copies deep link", pg.evaluate("navigator.clipboard.readText()").endswith("#sp-boletus-edulis"))
        pg.goto(url + "#guide"); pg.wait_for_timeout(2500)
        check("service worker ready", "已可离线" in pg.inner_text("#offline-status"))
        pg.locator("#off-photos").scroll_into_view_if_needed()
        pg.click('[data-dl="small"]')
        for _ in range(60):
            pg.wait_for_timeout(250)
            if "小图 " in pg.inner_text("#off-photos") and pg.locator("#off-bar").is_hidden():
                break
        n_small = pg.evaluate("photoSets.small.length")
        check(f"'download every photo' stores all {n_small} small photos", f"小图 {n_small} / {n_small}" in pg.inner_text("#off-photos"))
        sw = (PUBLIC / "sw.js").read_text(encoding="utf-8")
        check("the page and the service worker use the same photo cache",
              pg.evaluate("MEDIA_CACHE") in sw and pg.evaluate("MEDIA_CACHE").startswith("mushroom-guide-media"))
        ctx.set_offline(True); pg.reload(); pg.wait_for_timeout(1000)
        check("loads offline", pg.locator(".sp-card").count() > 50)
        check("offline: the header says so and external links are marked",
              pg.locator(".hdr [data-net-pill]").is_visible() and pg.evaluate("document.documentElement.classList.contains('is-offline')"))
        pg.goto(url + "#sp-boletus-edulis"); pg.wait_for_timeout(600)
        check("offline: a species photo still shows (downloaded before)",
              pg.evaluate("(() => { const i = document.querySelector('#sheet .photo__img'); return i.complete && i.naturalWidth > 0; })()"))
        ctx.set_offline(False)
        ctx.close()

        # ---------- field mode (phone) ----------
        ctx = b.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True)
        pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url); pg.wait_for_timeout(500)
        pg.click(".hdr [data-field-toggle]"); pg.wait_for_timeout(200)
        pg.reload(); pg.wait_for_timeout(500)
        nav_h = pg.evaluate("document.querySelector('.botnav__link').getBoundingClientRect().height")
        check(f"field mode is remembered, enlarges the tab bar ({nav_h}) and hides decoration",
              pg.evaluate("document.documentElement.dataset.field") == "on" and nav_h >= 64
              and pg.locator("#today").is_hidden() and pg.locator(".view__hero >> nth=0").is_hidden()
              and pg.get_attribute(".hdr [data-field-toggle]", "aria-pressed") == "true"
              and pg.evaluate("parseFloat(getComputedStyle(document.body).fontSize)") >= 18)
        for v in VIEWS:
            pg.evaluate(f"show('{v}')")
            if pg.evaluate("document.documentElement.scrollWidth") > 375:
                errs.append("overflow in field mode: " + v)
        pg.click(".hdr [data-field-toggle]"); pg.wait_for_timeout(100)
        check(f"field mode turns off again, no overflow or errors {errs}", "field" not in pg.evaluate("Object.keys(document.documentElement.dataset)") and not errs)
        ctx.close()

        # ---------- sandboxed preview (how many apps show an attached HTML file) ----------
        host = b.new_page(viewport={"width": 390, "height": 844})
        host.set_content('<iframe id=f sandbox="allow-scripts" style="width:390px;height:844px;border:0"></iframe>')
        host.eval_on_selector("#f", "(f, h) => f.srcdoc = h", html); host.wait_for_timeout(900)
        fr = host.frames[1]
        ok = []
        for v in ["finder", "toxic", "home", "log", "species"]:
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
