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
VIEWS = ["home", "explore", "learn", "species", "finder", "toxic", "guide", "log", "recipes", "emergency"]
NAV = {375: ".botnav", 768: ".topnav", 1024: ".topnav", 1440: ".topnav"}
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
    if (el.closest(".leaflet-container")) continue;  // the vendored map library's own markup
    const own = [...el.classList].filter(c => bare.has(c) && !c.includes("--") && !c.startsWith("is-") && !c.startsWith("leaflet-") && !ok.has(c));
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
            tabs = pg.eval_on_selector_all(f"{nav} a", "els => els.map(e => e.textContent.trim())")
            for v in ["explore", "log", "home"]:
                pg.click(f'{nav} a[href="#{v}"]'); pg.wait_for_timeout(80)
            pg.click('.subnav a[href="#finder"]'); pg.wait_for_timeout(80)  # 识菌 reopens its last page (tab memory); go through two pages
            id_last = "v-finder"
            pg.click('.subnav a[href="#species"]'); pg.wait_for_timeout(80)
            cur = pg.eval_on_selector_all(f"{nav} a[aria-current]", "els => els.map(e => e.textContent.trim())")
            check(f"{w}px three tabs {tabs}, sub-nav reaches the catalog and 识菌 stays current {cur}",
                  tabs == ["识菌", "拾菌", "菌记"] and pg.evaluate("document.querySelector('.view.is-active').id") == "v-species" and cur == ["识菌"])
            pg.go_back(); pg.wait_for_timeout(150)
            check(f"{w}px back button ({id_last})", pg.evaluate("document.querySelector('.view.is-active').id") == id_last)
            check(f"{w}px no JS errors {errs}", not errs)
            ctx.close()

        # ---------- deep links, finder, share, offline (phone) ----------
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=3)
        pg = ctx.new_page()
        man = __import__("json").loads((PUBLIC / "manifest.webmanifest").read_text(encoding="utf-8"))
        check("brand: title, manifest, share preview and header say 拾菌记 MycoTrail, with no old name on show",
              "<title>拾菌记 MycoTrail" in html and man["short_name"] == "拾菌记" and 'property="og:image"' in html
              and "野菌速查" not in html.split("<title>")[1].split("</title>")[0] and (PUBLIC / "og.png").exists() and (PUBLIC / "icon.svg").exists())
        pg.goto(url); pg.wait_for_timeout(400)
        check("header shows the brand", pg.inner_text(".hdr .brand__name") == "拾菌记" and "MycoTrail" in pg.inner_text(".hdr .brand__sub"))
        pg.goto(url + "#guide-calendar"); pg.wait_for_timeout(800)
        check("old #guide- links still work after the move (calendar now under 拾菌)", pg.evaluate("document.querySelector('.view.is-active').id") == "v-explore")
        pg.goto(url + "#guide-kitchen"); pg.wait_for_timeout(800)
        check("the kitchen guide sits under 识菌", pg.evaluate("document.querySelector('.view.is-active').id") == "v-guide"
              and pg.evaluate("document.documentElement.dataset.tab") == "id" and pg.locator('.subnav a[aria-current]').inner_text() == "厨房指南")
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
        pg.goto(url + "#explore-now"); pg.wait_for_timeout(400)
        n_now = pg.locator("#now-track .now__item").count()
        pg.click("#now-track .now__item >> nth=0"); pg.wait_for_timeout(500)
        check(f"'this month' strip lists species ({n_now}) and opens one", n_now > 0 and pg.evaluate("document.getElementById('sheet').open"))
        pg.goto(url + "#explore"); pg.wait_for_timeout(400)
        pg.click('[data-xp-go="cal"]'); pg.wait_for_timeout(1100)
        rows = pg.locator("#cal tbody tr").count()
        check(f"season calendar opens from the guide view with rows ({rows})",
              pg.evaluate("document.querySelector('.view.is-active').id") == "v-explore" and rows > 30
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
        check("checklist counts ticks", pg.inner_text("#eat-check-count") == "已核对 2 / 8")
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
        check("picking a species makes a find a candidate, never confirmed",
              pg.evaluate("document.querySelector('[name=finds-status]:checked').value") == "candidate")
        pg.evaluate("jstep(2)"); pg.fill("#finds-place", "测试步道"); pg.click('#finds-form button[type="submit"]'); pg.wait_for_timeout(200)
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
        clip = pg.evaluate("""[...document.querySelectorAll('#tox-grid .sp-card, #grid .sp-card')].slice(0, 6).every(c =>
            getComputedStyle(c).overflow === 'hidden' && getComputedStyle(c).borderRadius !== '0px')""")
        check("card photos are clipped to the card's rounded corners", clip)
        n_tx = pg.locator("#tox-grid .sp-card").count()
        pg.click("#tox-grid .sp-card >> nth=0"); pg.wait_for_timeout(500)
        check(f"toxic list uses the species card pattern ({n_tx} cards) and opens a sheet",
              n_tx == 22 and pg.locator("#tox-grid .sp-card__photo").count() == n_tx and pg.evaluate("document.getElementById('sheet').open"))
        pg.goto(url + "#guide-calendar"); pg.reload(); pg.wait_for_timeout(1000)
        all_rows = pg.locator("#cal tbody tr").count()
        pg.click('#v-explore [data-cal-region="bc"]'); pg.wait_for_timeout(150)
        bc_rows = pg.locator("#cal tbody tr").count()
        pg.click('[data-cal-mode="month"]'); pg.wait_for_timeout(150)
        month_txt = pg.inner_text("#cal")
        pg.fill("#cal-q", "松茸"); pg.wait_for_timeout(150)
        one = pg.locator("#cal .cal-month__list li").count()
        check(f"season explorer: region ({all_rows} -> {bc_rows} rows), month view and search",
              0 < bc_rows < all_rows and "高峰" in month_txt and "不能作为实时出菇预测" in month_txt and one == 1)
        pg.goto(url + "#sp-tricholoma-matsutake"); pg.wait_for_timeout(700)
        check("the species sheet shows records by region and by year, with the upload caveat",
              pg.locator("#sheet-body .obs-chart__regions span").count() == 3 and pg.locator("#sheet-body .obs-years__col").count() >= 3
              and "不代表这种菌变多了" in pg.inner_text("#sheet-body"))
        body = pg.inner_text("#sheet-body")
        check("species sheet: photo first, quick facts, sections and typed sources",
              pg.evaluate("document.querySelector('#sheet-body .photo').compareDocumentPosition(document.getElementById('sheet-title')) & 4") > 0
              and pg.locator("#sheet-body .sheet__q").count() == 3 and pg.locator("#sheet-body .sheet__sec").count() == 6
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
        check("safety copy: no trial portions or detox claims, and cooking is said not to make toxic mushrooms safe",
              not any(x in html for x in ["只吃一两勺", "只吃一小份", "任何杂菌", "朝车声", "生拌"]) and "都不能让有毒的菌变安全" in html)
        check("emergency page says do not induce vomiting or wait, and the guide has S.T.O.P. for getting lost",
              "不要自己催吐" in html and "不要等症状出现" in html and "S.T.O.P." in html and 'href="tel:911"' in html)
        pg.goto(url + "#home"); pg.wait_for_timeout(300)
        pg.click(".home-safety__sos"); pg.wait_for_timeout(300)
        check("'I may have eaten an uncertain mushroom' opens the emergency page", pg.evaluate("document.querySelector('.view.is-active').id") == "v-emergency")
        pg.click(".sos-pill"); pg.wait_for_timeout(150)
        check("SOS -> emergency view with tel link", pg.evaluate("document.querySelector('.view.is-active').id") == "v-emergency"
              and pg.locator('a[href="tel:18002221222"]').count() == 1)
        pg.click('.botnav a[href="#home"]'); pg.click('.subnav a[href="#finder"]'); pg.wait_for_timeout(100)
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
              and pg.locator("#finder-steps .wiz__dot").count() == 5 and pg.get_attribute('#finder-steps .wiz__dot[data-step="0"]', "aria-current") == "step")
        FIDX = {"hym": 0, "sub": 1, "spore": 2, "ring": 3, "volva": 4}
        def ans(k, v):  # the finder now picks the next question itself; open each one by its progress dot
            pg.click(f'#finder-steps .wiz__dot[data-step="{FIDX[k]}"]'); pg.click(f'[data-f="{k}"][data-v="{v}"]'); pg.wait_for_timeout(50)
        for k, v in [("hym", "gills"), ("sub", "wood"), ("spore", "white")]:
            ans(k, v)
        res = pg.inner_text("#finder-results")
        check("finder results do not widen the phone page", pg.evaluate("document.documentElement.scrollWidth") <= 390)
        check("finder gills+wood+white", "发光类脐菇" in res and "蜜环菌" in res and "纹缘盔孢伞" not in pg.inner_text(".res-block--toxic"))
        check("finder results say they are candidates only and link to the emergency page",
              "不判断能不能吃" in res and pg.locator('#finder-results .res-safe a[href="#emergency"]').count() == 1)
        check("finder shows what matched and what is unchecked, with no score",
              "相符：" in res and "未确认：" in res and "%" not in res and "还没确认 2 项" in res)
        pg.click('[data-wiz="prev"]'); pg.wait_for_timeout(50)
        check("the finder can step back to change an answer", pg.get_attribute('#finder-steps .wiz__dot[data-step="2"]', "aria-current") == "step"
              and pg.get_attribute('[data-f="spore"][data-v="white"]', "aria-pressed") == "true")
        pg.click("#finder-reset"); pg.click("#finder-reset")  # two taps: one tap never wipes the answers
        for k, v in [("hym", "gills"), ("sub", "ground"), ("spore", "white"), ("ring", ""), ("volva", "no")]:
            ans(k, v)
        res = pg.inner_text("#finder-results")
        check("finder keeps deadly amanitas when volva=no, warns early and allows skipping",
              "毒鹅膏" in res and "菌托常埋在土里" in res and "仍可能是这些致命毒菌" in res and "菌环" in pg.inner_text(".res-open"))
        pg.click("#finder-reset"); pg.click("#finder-reset")
        for k, v in [("hym", "gills"), ("sub", "ground"), ("spore", "white"), ("ring", ""), ("volva", "yes")]:
            ans(k, v)
        check("seeing a volva raises the amanita alarm at once", "你看到了菌托" in pg.inner_text("#finder-results"))
        ctx.grant_permissions(["clipboard-read", "clipboard-write"], origin=url.rstrip("/"))
        pg.goto(url + "#sp-boletus-edulis"); pg.wait_for_timeout(500)
        pg.evaluate("navigator.share = undefined"); pg.click("[data-share]"); pg.wait_for_timeout(250)
        check("share copies deep link", pg.evaluate("navigator.clipboard.readText()").endswith("#sp-boletus-edulis"))
        pg.goto(url + "#guide-offline"); pg.wait_for_timeout(2500)  # the old link opens 拾菌 › 工具 › 离线下载
        check("service worker ready", "已可离线" in pg.inner_text("#offline-status"))
        pg.locator("#off-photos").scroll_into_view_if_needed()
        pg.click('[data-dl="small"]')
        for _ in range(60):
            pg.wait_for_timeout(250)
            if " 张" in pg.inner_text("#off-photos") and pg.locator("#off-bar").is_hidden():
                break
        n_small = pg.evaluate("photoSets.small.length")
        check(f"'download every photo' stores all {n_small} small photos", f"{n_small} / {n_small} 张" in pg.inner_text("#off-photos") and "已完成" in pg.inner_text("#off-photos"))
        sw = (PUBLIC / "sw.js").read_text(encoding="utf-8")
        check("the page and the service worker use the same photo cache",
              pg.evaluate("MEDIA_CACHE") in sw and pg.evaluate("MEDIA_CACHE").startswith("mushroom-guide-media"))
        ctx.set_offline(True); pg.reload(); pg.wait_for_timeout(1000)
        pg.evaluate("navigate('species')"); pg.wait_for_timeout(300)
        check("loads offline, and the catalog opens offline", pg.locator("#grid .sp-card").count() > 50)
        check("offline: the header says so and external links are marked",
              pg.locator(".hdr [data-net-pill]").is_visible() and pg.evaluate("document.documentElement.classList.contains('is-offline')"))
        pg.goto(url + "#sp-boletus-edulis"); pg.wait_for_timeout(600)
        check("offline: a species photo still shows (downloaded before)",
              pg.evaluate("(() => { const i = document.querySelector('#sheet .photo__img'); return i.complete && i.naturalWidth > 0; })()"))
        # offline in the forest: write a record with a photo, then come back online after a cache wipe (what an update does)
        pg.goto(url + "#log"); pg.wait_for_timeout(800)
        pg.select_option("#finds-sp", "boletus-edulis"); pg.evaluate("jstep(2)"); pg.fill("#finds-place", "离线测试"); pg.evaluate("jstep(1)")
        pg.set_input_files("#finds-photo", str(PUBLIC / "photos" / "boletus-edulis.webp")); pg.wait_for_timeout(1200)
        pg.click("#finds-save"); pg.wait_for_timeout(600)
        off_ok = pg.evaluate("findsLoad().some(f => f.place === '离线测试' && f.photos.length === 1)")
        check("offline: a record with a photo can be written", off_ok)
        ctx.set_offline(False)
        pg.evaluate("caches.keys().then(ks => Promise.all(ks.map(k => caches.delete(k))))"); pg.wait_for_timeout(300)
        pg.reload(); pg.wait_for_timeout(1200)
        kept = pg.evaluate("(async () => { await findsReady; const f = findsLoad().find(f => f.place === '离线测试'); return !!(f && await photoDB.get(f.photos[0])); })()")
        check("back online after all caches were cleared (as an update does), the offline record and its photo are still there", kept)
        ctx.close()

        # ---------- 学习: quiz, wrong answers, term cards, progress (phone) ----------
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url + "#home"); pg.wait_for_timeout(400)
        pg.click('.subnav a[href="#learn"]'); pg.wait_for_timeout(300)
        bank = pg.evaluate("(() => { const B = buildBank(); return { n: B.length, bad: B.filter(q => !q.opts.some(o => o[0] === q.ans) || new Set(q.opts.map(o => o[0])).size !== q.opts.length).length, edible: B.filter(q => q.kind !== '安全' && /能吃|可食/.test(q.q)).length }; })()")
        check(f"学习 sits under 识菌 and the quiz bank is sound ({bank})", pg.evaluate("document.querySelector('.view.is-active').id") == "v-learn"
              and bank["n"] > 150 and bank["bad"] == 0 and bank["edible"] == 0)
        pg.click('[data-quiz="daily"]'); pg.wait_for_timeout(150)
        first = pg.inner_text(".quiz__q")
        pg.click('[data-quiz="daily"]'); pg.wait_for_timeout(150)
        check("today's quiz is the same each time it starts", pg.inner_text(".quiz__q") == first and "第 1 / 5 题" in pg.inner_text(".quiz__meta"))
        wrong_opt = pg.evaluate("(() => { const q = quiz.list[0]; return q.shown.find(o => o[0] !== q.ans)[0]; })()")
        pg.click(f'.quiz__opt[data-answer="{wrong_opt}"]'); pg.wait_for_timeout(150)
        check("a wrong answer explains why and goes into the wrong-answer book",
              "答错了" in pg.inner_text(".quiz__why") and pg.locator(".quiz__opt.is-right").count() == 1
              and "1 道题待复习" in pg.inner_text("#quiz-wrong-n"))
        pg.click('[data-quiz="wrong"]'); pg.wait_for_timeout(150)
        right_opt = pg.evaluate("quiz.list[0].ans")
        pg.click(f'.quiz__opt[data-answer="{right_opt}"]'); pg.wait_for_timeout(150)
        check("answering it right in the wrong-answer book clears it", "答对了" in pg.inner_text(".quiz__why") and "答错的题会放在这里" in pg.inner_text("#quiz-wrong-n"))
        pg.click('[data-quiz="safety"]'); pg.wait_for_timeout(150)
        check("safety questions are true/false with sources where the site has one", pg.locator(".quiz__opt").count() == 2)
        pg.click(".card >> nth=0 >> .card__face"); pg.click('.card >> nth=0 >> [data-term-v="known"]'); pg.wait_for_timeout(150)
        check("a term card flips and can be marked as known", "1" in pg.inner_text("#learn-progress .year__stat >> nth=1"))
        pg.goto(url + "#sp-boletus-edulis"); pg.wait_for_timeout(500); pg.click("#sheet [data-close]"); pg.goto(url + "#learn"); pg.wait_for_timeout(400)
        check(f"opening a species counts as seen in the progress {errs}", pg.inner_text("#learn-progress .year__stat >> nth=0").startswith("1") and not errs)
        ctx.close()

        # ---------- performance and keyboard (round 6) ----------
        ctx = b.new_context(viewport={"width": 1440, "height": 900})
        pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.add_init_script("window.__cls = 0; new PerformanceObserver(l => l.getEntries().forEach(e => { if (!e.hadRecentInput) window.__cls += e.value; })).observe({type: 'layout-shift', buffered: true});")
        pg.goto(url); pg.wait_for_timeout(1500)
        cls = pg.evaluate("window.__cls")
        check(f"first load: no layout shift ({cls:.3f}), off-screen views not built yet, data read as JSON",
              cls < 0.05 and pg.locator("#grid .sp-card").count() == 0 and pg.locator("#tox-grid .sp-card").count() == 0
              and pg.locator('script#data[type="application/json"]').count() == 1)
        pg.click('.subnav a[href="#species"]'); pg.wait_for_timeout(300)
        check("a view is built the first time it opens", pg.locator("#grid .sp-card").count() > 50)
        pg.focus("#grid .sp-card >> nth=0"); pg.keyboard.press("Enter"); pg.wait_for_timeout(400)
        on_close = pg.evaluate("document.activeElement.getAttribute('aria-label')")
        pg.keyboard.press("Escape"); pg.wait_for_timeout(300)
        check(f"keyboard: Enter opens a sheet with focus on close ({on_close}), Escape closes it and focus returns to the card {errs}",
              on_close == "关闭详情" and not pg.evaluate("document.getElementById('sheet').open")
              and "sp-card" in pg.evaluate("document.activeElement.className") and not errs)
        pg.goto(url + "#home"); pg.reload(); pg.wait_for_timeout(400); pg.keyboard.press("Tab")
        check("the first Tab reaches the skip link", "skip-link" in pg.evaluate("document.activeElement.className"))
        hero = pg.get_attribute("#v-home .view__hero", "srcset") or ""
        check("header photos offer a 640px copy for phones", "-640.webp 640w" in hero and (PUBLIC / "photos" / "hero-home-porcini-640.webp").exists())
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

        # ---------- finds journal: GPS, photo, edit, filters, map, backup (phone) ----------
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True,
                            geolocation={"latitude": 47.6062, "longitude": -122.3321, "accuracy": 12}, permissions=["geolocation"])
        pg = ctx.new_page(); errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url + "#log"); pg.wait_for_timeout(600)
        pg.select_option("#finds-sp", "cantharellus-formosus"); pg.evaluate("jstep(2)"); pg.fill("#finds-place", "地图测试林")
        pg.click("#finds-gps"); pg.wait_for_timeout(600)
        gps = pg.inner_text("#finds-gps-out")
        png = __import__("base64").b64decode("iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAFklEQVR4nGP4z8DAwMDAxMDAwMDAAAANHQEDasKb6QAAAABJRU5ErkJggg==")
        pg.set_input_files("#finds-photo", files=[{"name": "a.png", "mimeType": "image/png", "buffer": png}]); pg.wait_for_timeout(600)
        thumbs = pg.locator("#finds-thumbs .finds__thumb img").count()
        pg.click('#finds-form button[type="submit"]'); pg.wait_for_timeout(500)
        check(f"a find saves GPS ({gps}) and a photo ({thumbs})", "47.60620" in gps and thumbs == 1
              and pg.locator("#finds-list img.finds__pic").count() == 1)
        pg.evaluate("jstep(1)"); pg.select_option("#finds-sp", ""); pg.fill("#finds-other", "褐色小伞菌"); pg.evaluate("jstep(2)")
        pg.click("#finds-gps"); pg.wait_for_timeout(500); pg.check("#finds-fuzzy")
        pg.click('#finds-form button[type="submit"]'); pg.wait_for_timeout(300)
        saved = pg.evaluate("findsLoad()")
        fz = [f for f in saved if f.get("other") == "褐色小伞菌"][0]
        check(f"'only a rough location' stores coordinates cut to ~1 km ({fz['lat']}, {fz['lon']})",
              fz["fuzzy"] and fz["lat"] == 47.61 and fz["lon"] == -122.33 and fz["alt"] is None)
        first = [f for f in saved if f.get("sp") == "cantharellus-formosus"][0]
        check("the first photo is labelled 整体", list(first["parts"].values()) == ["整体"])
        pg.select_option("#finds-fregion", "wa"); pg.wait_for_timeout(200)
        n_wa = pg.locator("#finds-list .finds__item").count()
        pg.select_option("#finds-fregion", "bc"); pg.wait_for_timeout(200)
        check(f"filtering by region uses the coordinates ({n_wa} in WA)", n_wa == 2 and pg.locator("#finds-list .finds__item").count() == 0)
        pg.select_option("#finds-fregion", "")
        check("the year report counts the year's finds", not pg.locator("#finds-year").is_hidden() and "2" in pg.inner_text("#year-stats"))
        pg.click('#finds-list [data-edit] >> nth=1'); pg.wait_for_timeout(300)
        editing = pg.inner_text("#finds-title")
        pg.evaluate("jstep(3)"); pg.fill("#finds-notes", "改过的备注"); pg.click('#finds-form button[type="submit"]'); pg.wait_for_timeout(300)
        check("a find can be edited in place", editing == "编辑记录" and "改过的备注" in pg.inner_text("#finds-list")
              and pg.locator("#finds-list .finds__item").count() == 2)
        pg.select_option("#finds-fsp", "cantharellus-formosus"); pg.wait_for_timeout(200)
        check("filtering by species narrows the timeline", pg.locator("#finds-list .finds__item").count() == 1)
        pg.select_option("#finds-fsp", "")
        pg.locator("#fmap").scroll_into_view_if_needed(); pg.wait_for_timeout(1500)
        check("the map loads and shows both finds with coordinates", pg.locator("#fmap path.leaflet-interactive").count() == 2)
        pg.select_option("#finds-export-gps", "none")
        with pg.expect_download() as dl0:
            pg.click("#finds-export-json")
        shared = __import__("json").loads(open(dl0.value.path(), encoding="utf-8").read())
        check("exporting 'without coordinates' drops them", all(f.get("lat") is None for f in shared["finds"]))
        pg.select_option("#finds-export-gps", "exact")
        with pg.expect_download() as dl:
            pg.click("#finds-export-json")
        backup = dl.value.path()
        data = __import__("json").loads(open(backup, encoding="utf-8").read())
        check("the JSON backup holds both finds and the photo", len(data["finds"]) == 2 and len(data["photos"]) == 1)
        pg.evaluate("findsSave([])"); pg.reload(); pg.wait_for_timeout(600)
        pg.set_input_files("#finds-import", backup); pg.wait_for_timeout(600)
        check("importing shows a preview first and changes nothing before confirming",
              pg.evaluate("document.getElementById('imp').open") and "新记录，会加进来" in pg.inner_text("#imp") and pg.evaluate("findsLoad().length") == 0)
        pg.click("#imp-go"); pg.wait_for_timeout(1000)
        check(f"importing the backup restores the finds and photo {errs}", pg.locator("#finds-list .finds__item").count() == 2
              and pg.locator("#finds-list img.finds__pic").count() == 1 and not errs)
        ctx.close()

        # ---------- round 7: safety data, finder edge cases, journal import and delete (phone) ----------
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        pg = ctx.new_page(); errs = []; reqs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("request", lambda r: reqs.append(r.url))
        pg.goto(url); pg.wait_for_timeout(500)
        bad = pg.evaluate("""() => {
          const E = ["Edible","Inedible","Toxic","Deadly Toxic","Unknown","Not Evaluated"], R = ["Draft","In Review","Verified","Needs Update","Disputed"];
          const out = [];
          for (const s of DATA.species) if (!s.safety || !["Edible","Not Evaluated","Unknown"].includes(s.safety.edibility) || !R.includes(s.safety.review)
                                    || (s.safety.edibility === "Edible" && s.safety.review === "In Review")) out.push(s.slug);
          for (const p of toxicAll) if (!p.safety || !["Toxic","Deadly Toxic"].includes(p.safety.edibility) || !p.safety.symptoms
                                         || (p.safety.edibility === "Deadly Toxic") !== (p.level === "致命")) out.push(p.slug);
          for (const r of DATA.recipes) for (const sp of r.sp) { const s = DATA.species.find(x => x.slug === sp); if (!s || !recommendable(s)) out.push(r.id + ":" + sp); }
          return out; }""")
        check(f"every species has a valid safety record; recipes use only verified edibles {bad}", not bad)
        pax = pg.evaluate("(() => { const p = toxicAll.find(x => x.slug === 'paxillus-involutus'); return p && [p.safety.edibility, p.level]; })()")
        hyd = pg.evaluate("DATA.species.find(x => x.slug === 'hydnum-repandum').safety.note || ''")
        check(f"Paxillus involutus is deadly toxic and Hydnum repandum warns about the name {pax}",
              pax == ["Deadly Toxic", "致命"] and "Paxillus" in hyd)
        picks = pg.evaluate("Array.from({length: 60}, (_, i) => recommendable(todayPick(i).s)).every(Boolean)")
        check("today's mushroom is always a verified, recommended edible (60 days)", picks)
        unver = pg.evaluate("DATA.species.filter(s => s.safety.review !== 'Verified').length")
        pg.evaluate("show('species')"); pg.wait_for_timeout(300)
        check(f"species cards flag every unverified species ({unver})", pg.locator(".sp-card__review").count() == unver and unver > 0)
        pg.evaluate("show('recipes')"); pg.wait_for_timeout(200)
        check("recipes carry the exact safety notice",
              "本食谱仅适用于已经由可靠方式确认身份的食用菌。烹饪不能使有毒蘑菇变得安全。不要仅凭本应用的识别结果决定是否食用。" in pg.inner_text("#v-recipes"))
        pg.evaluate("openSpecies(DATA.species.findIndex(s => s.slug === 'hydnum-repandum'))"); pg.wait_for_timeout(300)
        sh = pg.inner_text("#sheet")
        check("a species sheet shows edibility, review status, season coverage and the history-not-forecast line",
              "资料审核" in sh and "非真菌学专家审核" in sh and "覆盖年份" in sh and "最近一条" in sh
              and "历史观察数据反映过去记录的分布和季节性，不代表当前地点一定有蘑菇，也不能作为实时出菇预测。" in sh)
        pg.evaluate("document.getElementById('sheet').close()")
        pg.evaluate("openToxic('paxillus-involutus')"); pg.wait_for_timeout(300)
        sh = pg.inner_text("#sheet")
        check("a toxic sheet shows symptoms and the name warning", "中毒表现" in sh and "溶血" in sh and "羊蹄菇" in sh)
        pg.evaluate("document.getElementById('sheet').close()")
        few = pg.evaluate("(() => { const s = DATA.species.find(x => x.obs && x.obs.counts.reduce((a, b) => a + b, 0) < 30); if (!s) return null; openSpecies(DATA.species.indexOf(s)); return document.getElementById('sheet').innerText.includes('样本不足'); })()")
        check("a species with fewer than 30 records says 样本不足", few is True)
        pg.evaluate("document.getElementById('sheet').close()")
        # finder: everything skipped, then contradicting answers
        pg.evaluate("show('finder')"); pg.wait_for_timeout(200)
        for _ in range(5):
            pg.click("#finder-steps [data-v='']"); pg.wait_for_timeout(60)
        check("skipping every finder question says nothing could be narrowed and lists no candidates",
              "都跳过了" in pg.inner_text("#finder-results") and pg.locator("#finder-results .res-item").count() == 0)
        pg.click("#finder-reset"); pg.wait_for_timeout(60)
        pg.click('[data-f="hym"][data-v="pores"]'); pg.wait_for_timeout(60)
        pg.click('#finder-steps .wiz__dot[data-step="4"]'); pg.wait_for_timeout(60)
        vol = pg.locator('#finder-steps [data-f="volva"]:not([data-v=""])').first
        vol.click(); pg.wait_for_timeout(100)
        items = pg.eval_on_selector_all("#finder-results .res-item", "els => els.map(e => e.classList.contains('res-item--toxic'))")
        check(f"contradicting finder answers still list toxic species first {errs}",
              not errs and (not items or items[0] or not any(items)) and items == sorted(items, reverse=True))
        # journal: invalid files never change existing records; duplicates are reported; web photo addresses are ignored
        rec = {"id": 111, "date": "2026-10-01", "sp": "boletus-edulis", "place": "测试", "photos": ["px1", "px2"], "parts": {}}
        pg.evaluate("r => findsSave([r])", rec)
        pg.evaluate("show('log')"); pg.wait_for_timeout(400)
        before = pg.evaluate("JSON.stringify(findsLoad())")
        tmp = Path(__import__("tempfile").mkdtemp())
        (tmp / "broken.json").write_text("{not json", encoding="utf-8")
        (tmp / "other.json").write_text('{"hello": 1}', encoding="utf-8")
        (tmp / "dup.json").write_text(__import__("json").dumps({"version": 3, "finds": [rec, {"id": 222, "date": 5}],
                                     "photos": {}}), encoding="utf-8")
        (tmp / "web.json").write_text(__import__("json").dumps({"version": 3, "finds": [{"id": 333, "date": "2026-10-02", "photos": ["w1"]}],
                                     "photos": {"w1": "https://example.invalid/track.jpg"}}), encoding="utf-8")
        msgs = []
        for name in ["broken", "other"]:
            pg.set_input_files("#finds-import", str(tmp / f"{name}.json")); pg.wait_for_timeout(400)
            msgs.append(pg.inner_text("#toast"))
        check(f"invalid backups leave existing records untouched {msgs}",
              pg.evaluate("JSON.stringify(findsLoad())") == before and all("没有改动" in m for m in msgs))
        pg.set_input_files("#finds-import", str(tmp / "dup.json")); pg.wait_for_timeout(400)
        m = pg.inner_text("#imp")
        check(f"a duplicate and a malformed record are reported in the preview, not imported",
              "内容相同" in m and "格式不对或重复，跳过" in m and pg.evaluate("document.getElementById('imp-go').disabled"))
        pg.click("[data-imp-cancel]"); pg.wait_for_timeout(200)
        check("cancelling an import changes nothing", pg.evaluate("findsLoad().length") == 1 and "没有改动" in pg.inner_text("#toast"))
        pg.set_input_files("#finds-import", str(tmp / "web.json")); pg.wait_for_timeout(400); pg.click("#imp-go"); pg.wait_for_timeout(500)
        check("an imported backup cannot make the page fetch a web address",
              not any("example.invalid" in u for u in reqs) and pg.evaluate("findsLoad().length") == 2)
        pg.click('[data-del="111"]'); pg.wait_for_timeout(100)
        check("deleting a find says how many photos go with it", "含 2 张照片" in pg.inner_text('[data-del="111"]'))
        pg.click('[data-del="111"]'); pg.wait_for_timeout(300)
        check("the delete toast names the photos removed", "2 张照片" in pg.inner_text("#toast")
              and pg.evaluate("findsLoad().length") == 1)
        # conflicts: same id, different content -> keep mine by default, replace only when chosen
        mine = pg.evaluate("findsLoad()[0]")
        (tmp / "conf.json").write_text(__import__("json").dumps({"backupVersion": 4, "finds": [dict(mine, notes="备份里的版本")], "photos": {},
                                       "learning": {"seen": ["sp:boletus-edulis"]}}), encoding="utf-8")
        pg.set_input_files("#finds-import", str(tmp / "conf.json")); pg.wait_for_timeout(400)
        check("a changed record shows up as a conflict, keeping this device's version by default",
              "内容不同" in pg.inner_text("#imp") and pg.evaluate("document.querySelector('[name=imp-conflict]:checked').value") == "keep")
        pg.click("#imp-go"); pg.wait_for_timeout(400)
        kept = pg.evaluate("findsLoad()[0].notes || ''")
        pg.set_input_files("#finds-import", str(tmp / "conf.json")); pg.wait_for_timeout(400)
        pg.check('[name="imp-conflict"][value="replace"]'); pg.click("#imp-go"); pg.wait_for_timeout(400)
        check(f"replacing a conflict happens only when chosen ({kept!r})", kept != "备份里的版本" and pg.evaluate("findsLoad()[0].notes") == "备份里的版本"
              and pg.evaluate("findsLoad().length") == 1)
        # full backup format, data center, orphan photos, wipe
        with pg.expect_download() as dl:
            pg.click("#finds-export-json")
        full = __import__("json").loads(open(dl.value.path(), encoding="utf-8").read())
        check("the full backup is versioned and carries records, photos, settings and learning",
              full["backupVersion"] == 4 and full["schemaVersion"] == 2 and full["exportedAt"] and "learning" in full and "prefs" in full
              and full["finds"][0]["createdAt"] and full["finds"][0]["updatedAt"])
        pg.wait_for_timeout(400)
        dc = pg.inner_text("#data-center")
        check("the data center shows counts, last backup, schema and migration", all(k in dc for k in ["记录", "最近完整备份", "schema 2", "旧版数据搬迁"])
              and "从未" not in dc.split("最近完整备份")[1][:20])
        pg.evaluate("photoDB.put('orphan-test', new Blob(['x'], {type: 'image/jpeg'}))"); pg.evaluate("renderDataCenter()"); pg.wait_for_timeout(300)
        pg.click("#dc-orphans"); pg.click("#dc-orphans"); pg.wait_for_timeout(500)
        check("orphan photos are found and removed after a confirm", "orphan-test" not in pg.evaluate("photoDB.keys()"))
        pg.click("#dc-wipe"); pg.wait_for_timeout(200)
        check("wiping needs an explicit tick", pg.evaluate("document.getElementById('wipe-go').disabled"))
        pg.check("#wipe-ok"); pg.click("#wipe-go"); pg.wait_for_timeout(500)
        check("wiping clears records and photos", pg.evaluate("findsLoad().length") == 0 and pg.evaluate("photoDB.keys()") == [])
        ctx.close()

        # ---------- safety hotfix (2026-11-01): Paxillus, unevaluated species, checklist, emergency, old journal data ----------
        ctx = b.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        old = [{"id": 1700000000000, "date": "2024-09-14", "sp": "hydnum-repandum", "place": "旧版记录", "notes": "v1"}]
        pg.goto(url + "manifest.webmanifest"); pg.evaluate("r => localStorage.setItem('mushroom-guide:finds:v1', JSON.stringify(r))", old)
        pg.goto(url); pg.wait_for_timeout(700)  # first start with the new data layer: the old records are copied into IndexedDB
        leak = pg.evaluate("""() => {
          const out = [];
          for (const s of DATA.species) if (/^(Paxillus|Galerina|Gyromitra|Inocybe|Omphalotus|Lepiota )/.test(s.latin)) out.push(s.slug);
          for (const r of DATA.recipes) if (/Paxillus|卷边桩菇|卷缘齿菌/.test(JSON.stringify(r))) out.push("recipe " + r.id);
          for (const s of DATA.species) if (recommendable(s) && /^(Amanita|Cortinarius|Chlorophyllum|Macrolepiota)/.test(s.latin)) out.push("recommended " + s.slug);
          for (const s of DATA.species) if (s.safety.edibility !== "Edible" && (recommendable(s) || s.flags.includes("上品") || !s.kitchen.includes("不提供吃法"))) out.push("unevaluated " + s.slug);
          return out; }""")
        check(f"no dangerous genus, Paxillus name or unevaluated species reaches edibles, recipes or recommendations {leak}", not leak)
        pg.evaluate("show('guide')"); pg.wait_for_timeout(300)
        g = pg.inner_text("#v-guide")
        check("the kitchen guide no longer uses 卷缘齿菌 or Paxillus anywhere", "卷缘齿菌" not in g and "Paxillus" not in g and "卷边桩菇" not in g)
        check("the checklist is a risk check with the exact warning",
              "食用前风险检查" in g and "本清单不能确认任何蘑菇是否可食用。孢子印、气味、形态特征及其他单项检查均不能排除所有毒菌。完成全部检查不代表可以安全食用。不要仅凭本应用决定是否食用。" in g)
        check("the checklist no longer asks for a raw sample every time; it points to the emergency page instead",
              "留一两朵" not in g and pg.locator("#eat-check li").count() == 8 and "按急救页面保留剩余蘑菇和剩菜" in g)
        check("no absolute 'you must be sure it is non-toxic' wording; in-person checks are not called a guarantee",
              "必须确定它无毒" not in g and "当面确认能减少认错，但不能保证安全" in pg.inner_text("#v-guide"))
        pg.evaluate("navigate('explore-hab')"); pg.wait_for_timeout(400)
        hab_txt = pg.inner_text("#xp-hab"); ex = pg.evaluate("document.getElementById('v-explore').textContent") + hab_txt
        bad_hab = [n for n in ["美味齿菌", "卷缘齿菌", "、鸡油菌、", "皱盖罗鳞伞", "夏松露", "木耳", "高大环柄菇", "粗鳞青褶伞", "荷叶离褶伞"] if n in hab_txt]
        check(f"the 'where to look' lists name only recommended species {bad_hab}", not bad_hab and "未评估和高风险的种类不列出" in ex and "必须确定它无毒" not in ex)
        check("the month and season lists say what data they rest on",
              all(k in pg.inner_text("#now-data") + pg.inner_text("#season-data") for k in ["iNaturalist", "覆盖", "样本", "更新于", "样本不足"]))
        pg.evaluate("show('recipes')"); pg.wait_for_timeout(200)
        check("recipes no longer ask to keep raw samples of every dish", "留一两朵" not in pg.inner_text("#v-recipes"))
        pg.evaluate("show('emergency')"); pg.wait_for_timeout(200)
        em = pg.inner_text("#v-emergency")
        check("the emergency page has the sample-keeping advice and timeline caveats",
              "如果怀疑误食，保留剩余蘑菇或剩菜，用纸袋或蜡纸包装，不要使用塑料袋，并冷藏。拍摄菌盖、菌褶、菌柄和菌基照片。不要为了留样而延误联系毒物中心。" in em
              and "早期症状缓解，不代表安全" in em and "不是固定规律" in em and "Wikipedia" not in em)
        pg.evaluate("show('home')"); pg.wait_for_timeout(200)
        pg.fill("#home-q", "卷缘齿菌"); pg.wait_for_timeout(250)
        first = pg.locator("#home-results a").first.get_attribute("href")
        check(f"searching 卷缘齿菌 lists the toxic Paxillus first, then the hedgehog ({first})",
              first == "#tx-paxillus-involutus" and pg.locator('#home-results a[href="#sp-hydnum-repandum"]').count() == 1)
        pg.evaluate("openSpecies(DATA.species.findIndex(s => s.slug === 'amanita-caesarea'))"); pg.wait_for_timeout(300)
        sh = pg.inner_text("#sheet")
        check("an unevaluated species sheet gives no cooking advice", "未评估" in sh and "不提供吃法" in sh and "上品" not in sh)
        pg.evaluate("document.getElementById('sheet').close()")
        pg.evaluate("show('log')"); pg.wait_for_timeout(400)
        check(f"an old-format journal record still shows and is unchanged {errs}",
              "旧版记录" in pg.inner_text("#finds-list") and not errs
              and pg.evaluate("localStorage.getItem('mushroom-guide:finds:v1')") == __import__("json").dumps(old, ensure_ascii=False, separators=(",", ":")))
        mig = pg.evaluate("metaGet('migration')")
        rec0 = pg.evaluate("findsLoad()[0]")
        check(f"old localStorage records are copied into IndexedDB with timestamps, and the old copy is kept {mig}",
              mig and mig["status"] == "done" and mig["count"] == 1 and rec0["id"] == 1700000000000
              and rec0["createdAt"].startswith("2023-11-14") and pg.evaluate("STORE") == "idb")
        ctx.close()

        # ---------- round 8: my species, revisits, photo archive, year report (phone) ----------
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, accept_downloads=True)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url + "#log"); pg.wait_for_timeout(600)
        recs = [{"id": 11, "date": "2025-09-10", "sp": "boletus-edulis", "status": "candidate", "place": "A 步道", "lat": 47.6, "lon": -122.3},
                {"id": 12, "date": "2026-10-01", "sp": "boletus-edulis", "status": "expert", "verifier": "王老师", "place": "A 步道"},
                {"id": 13, "date": "2026-10-02", "sp": "cantharellus-formosus", "status": "expert", "place": "B"},
                {"id": 14, "date": "2026-10-03", "other": "褐色小菇", "place": "a 步道"}]
        pg.evaluate("r => findsSave(r).then(() => renderFinds())", recs); pg.wait_for_timeout(600)
        mine = pg.inner_text("#my-species")
        nums = pg.eval_on_selector_all("#mine-body .year__stat b", "els => els.map(e => +e.textContent)")
        check(f"my species counts species, expert-confirmed (only with a named verifier), self-judged and unknown {nums}", nums == [2, 1, 1, 1])
        check("expert status is never inferred", "候选（自己判断）" in mine and mine.count("专家当面确认（自记）") >= 2)
        rv = pg.inner_text("#rv-body")
        check("revisit groups the same place (case-insensitive) across years", "去过 3 天" in rv and "2025" in rv and "2026" in rv)
        pg.click('[data-rv="p:a 步道"]'); pg.wait_for_timeout(300)
        check("revisit prefills the place and last coordinates for a new record",
              pg.input_value("#finds-place") == "a 步道" and pg.evaluate("draft.lat") == 47.6 and pg.evaluate("draft.id") is None)
        pg.select_option("#year-pick", "2026"); pg.wait_for_timeout(300)
        ys = pg.eval_on_selector_all("#year-stats .year__stat b", "els => els.map(e => +e.textContent)")
        check(f"the year report counts records, days, species and first-time species from real records {ys}", ys[:4] == [3, 3, 2, 1] and "鸡油菌" in pg.inner_text("#year-stats"))
        with pg.expect_download() as dl:
            pg.click("#year-share")
        check("the year report makes a share picture", dl.value.suggested_filename.endswith(".png"))
        check("the photo archive has an empty state with a next step", "还没有照片" in pg.inner_text("#pa-wall"))
        sw = pg.evaluate("document.documentElement.scrollWidth")
        check(f"the journal does not overflow at 390px ({sw}) {errs}", sw <= 390 and not errs)
        ctx.close()

        # ---------- round 8: season intelligence (phone) ----------
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url + "#explore-intel"); pg.wait_for_timeout(700)
        pg.click('[data-intel-m="10"]'); pg.wait_for_timeout(200)
        items = pg.locator("#intel-body tbody tr").count()
        txt = pg.inner_text("#intel")
        ok_rec = pg.evaluate("[...document.querySelectorAll('#intel-body tbody a')].every(a => recommendable(DATA.species.find(s => '#sp-' + s.slug === a.getAttribute('href'))))")
        check(f"season intelligence compares BC / WA / OR for a chosen month (recommended species only) with month changes and data notes ({items})",
              0 < items <= 10 and ok_rec and pg.locator("#intel-body thead th").count() == 4 and "10 月 → 11 月" in txt and "样本" in txt and "不是实时出菇预测" in txt)
        pg.click('[data-intel-m="2"]'); pg.wait_for_timeout(200)
        empty = pg.inner_text("#season-cols") + pg.inner_text("#intel-body")
        check("a quiet month says why, without implying there are no mushrooms", ("没有明显" in empty or "这不代表林子里没有菌" in empty) and not errs)
        ctx.close()

        # ---------- round 8: finder explanations (phone) ----------
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url + "#finder"); pg.wait_for_timeout(600)
        pg.click('[data-f="hym"][data-v="ridges"]'); pg.wait_for_timeout(200)
        res = pg.inner_text("#finder-results")
        check("the finder says information is missing while the volva question is unanswered", "信息不足" in res and "“菌托”" in res and "不要把任何候选当成答案" in res)
        check("candidates link to the comparisons they appear in", pg.locator('#finder-results .res-cmp a[href="#cmp-chanterelle"]').count() >= 1)
        check("candidates still show matched / kept-despite / unconfirmed features, with no score", "相符" in res and "未确认" in res and "%" not in res and "概率" not in res.replace("不计算匹配分数或概率", ""))
        for k, v in [("sub", "ground"), ("spore", "white"), ("ring", "no"), ("volva", "no")]:
            pg.click('#finder-steps .wiz__dot[data-step="%d"]' % ["hym", "sub", "spore", "ring", "volva"].index(k)); pg.click(f'[data-f="{k}"][data-v="{v}"]'); pg.wait_for_timeout(100)
        check(f"answering the key questions removes the missing-information alarm {errs}", "信息不足" not in pg.inner_text("#finder-results") and not errs)
        ctx.close()

        # ---------- round 9: home, tab memory, habitats, three-step journal (phone) ----------
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url); pg.wait_for_timeout(900)
        home = pg.inner_text("#v-home")
        check("home leads with the hero line, search and the two main actions",
              "走进森林，发现自然。" in home and pg.locator(".home-act__item").count() == 2
              and pg.locator('.home-act__item[href="#finder"]').count() == 1 and pg.locator('.home-act__item[href="#explore"]').count() == 1)
        hs = pg.evaluate("[...document.querySelectorAll('#home-season-track a')].map(a => recommendable(DATA.species.find(s => '#sp-' + s.slug === a.getAttribute('href'))))")
        check(f"home season discovery shows recommended species with its data notes ({len(hs)})",
              0 < len(hs) <= 8 and all(hs) and "样本" in pg.inner_text("#home-season-data") and "不是实时出菇预测" in pg.inner_text("#home-season-data"))
        check("home journal preview has an empty state with a next step", pg.locator('#home-jr-body a[href="#log"]').count() == 1)
        pg.fill("#home-q", "菌托"); pg.wait_for_timeout(200)
        check("home search also finds glossary terms", pg.locator('#home-results a[href="#guide-gloss"]').count() >= 1)
        pg.fill("#home-q", "松茸"); pg.wait_for_timeout(200); pg.click("#home-results a >> nth=0"); pg.wait_for_timeout(400)
        pg.click("#sheet [data-close]"); pg.wait_for_timeout(300); pg.fill("#home-q", ""); pg.focus("#home-q"); pg.wait_for_timeout(150)
        check("recent searches stay on this device and can be reused", pg.locator('#home-recentq [data-rq="松茸"]').count() == 1)
        pg.evaluate("window.scrollTo(0, 900)"); pg.wait_for_timeout(100)
        pg.click('.botnav a[href="#explore"]'); pg.wait_for_timeout(300); pg.click('.botnav a[href="#home"]'); pg.wait_for_timeout(300)
        check(f"switching tabs keeps each tab's scroll position ({pg.evaluate('scrollY')})", abs(pg.evaluate("scrollY") - 900) < 5)
        pg.click('.botnav a[href="#explore"]'); pg.wait_for_timeout(300)
        n_hab = pg.locator("#v-explore details.habitat").count()
        bad = pg.evaluate("[...document.querySelectorAll('.habitat__sp')].filter(a => !recommendable(DATA.species.find(s => '#sp-' + s.slug === a.getAttribute('href')))).length")
        check(f"habitat cards list only recommended species ({n_hab} cards)", n_hab == 5 and bad == 0)
        pg.click('.botnav a[href="#log"]'); pg.wait_for_timeout(700)
        check("a new record starts at step 1 of 3", pg.locator("#finds-form .jstep:not([hidden])").get_attribute("data-jstep") == "1"
              and pg.locator('[data-jgo="1"][aria-current="step"]').count() == 1)
        pg.click('[data-jnav="1"]'); pg.wait_for_timeout(100)
        check("next goes to place and habitat, where GPS is optional", pg.locator("#finds-form .jstep:not([hidden])").get_attribute("data-jstep") == "2" and pg.is_visible("#finds-gps"))
        pg.click('[data-jgo="1"]'); pg.select_option("#finds-sp", "hydnum-repandum"); pg.click("#finds-save"); pg.wait_for_timeout(500)
        check(f"a record saves from step 1 with only a species, no GPS {errs}", pg.evaluate("findsLoad().length") == 1 and pg.evaluate("findsLoad()[0].lat") is None and not errs)
        pg.click('.botnav a[href="#home"]'); pg.wait_for_timeout(400)
        check("the home journal preview shows the new record", "美味齿菌" in pg.inner_text("#home-jr-body"))
        ctx.close()

        # ---------- round 10 / Sprint 1: theme, components, design page (phone) ----------
        ctx = b.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, color_scheme="light")
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url + "#guide-theme"); pg.wait_for_timeout(700)
        check("the theme follows the system by default", pg.evaluate("document.documentElement.dataset.theme") is None
              and pg.get_attribute('[data-theme-pick="system"]', "aria-pressed") == "true")
        pg.click('[data-theme-pick="dark"]'); pg.wait_for_timeout(150)
        dark_bg = pg.evaluate("getComputedStyle(document.body).backgroundColor")
        check(f"choosing 深色 switches to dark at once ({dark_bg})", pg.evaluate("document.documentElement.dataset.theme") == "dark" and dark_bg != "rgb(248, 246, 239)")
        pg.keyboard.press("Escape"); pg.wait_for_timeout(150)
        pg.click("[data-field-toggle] >> nth=0"); pg.wait_for_timeout(150)
        check("outdoor mode is independent of the theme", pg.evaluate("document.documentElement.dataset.field") == "on" and pg.evaluate("document.documentElement.dataset.theme") == "dark")
        pg.reload(); pg.wait_for_timeout(600)
        check("the theme choice is remembered on this device and applied before paint",
              pg.evaluate("localStorage.getItem('mushroom-guide:theme')") == "dark" and pg.evaluate("document.documentElement.dataset.theme") == "dark")
        pg.keyboard.press("Escape"); pg.wait_for_timeout(150)
        pg.click("[data-field-toggle] >> nth=0"); pg.click("[data-open-settings]"); pg.click('#settings [data-theme-pick="system"]'); pg.keyboard.press("Escape"); pg.wait_for_timeout(150)
        check("跟随系统 clears the stored choice", pg.evaluate("localStorage.getItem('mushroom-guide:theme')") is None and pg.evaluate("document.documentElement.dataset.theme") is None)
        pg.evaluate("navigate('guide-calendar')"); pg.wait_for_timeout(400)
        pg.click('#v-explore [data-cal-mode="month"]'); pg.wait_for_timeout(150)
        check("the calendar mode switch is a segmented control", pg.get_attribute('[data-cal-mode="month"]', "class") == "seg__btn"
              and pg.get_attribute('[data-cal-mode="month"]', "aria-pressed") == "true")
        pg.evaluate("navigate('log')"); pg.wait_for_timeout(700)
        check("location options are switches", pg.get_attribute("#finds-fuzzy", "role") == "switch" and pg.get_attribute("#fmap-tiles", "role") == "switch")
        tmpd = Path(__import__("tempfile").mkdtemp())
        (tmpd / "one.json").write_text(__import__("json").dumps({"backupVersion": 4, "finds": [{"id": 99, "date": "2026-10-05"}], "photos": {}}), encoding="utf-8")
        pg.set_input_files("#finds-import", str(tmpd / "one.json")); pg.wait_for_timeout(400)
        check("the import preview is a bottom sheet", pg.get_attribute("#imp", "class") == "bsheet" and pg.evaluate("document.getElementById('imp').open"))
        pg.keyboard.press("Escape"); pg.wait_for_timeout(200)
        check("Esc cancels the sheet and changes nothing", not pg.evaluate("document.getElementById('imp').open") and "没有改动" in pg.inner_text("#toast") and pg.evaluate("findsLoad().length") == 0)
        pg.set_input_files("#finds-import", str(tmpd / "one.json")); pg.wait_for_timeout(400)
        pg.mouse.click(195, 20); pg.wait_for_timeout(200)
        check("tapping the backdrop cancels too", not pg.evaluate("document.getElementById('imp').open") and pg.evaluate("findsLoad().length") == 0)
        check("skeleton and error-state helpers render", pg.evaluate("skelRows(2).includes('skel--row') && errState('a', 'b').includes('err-state')"))
        pg.evaluate("STORE = 'none'; FINDS = null; renderFinds()"); pg.wait_for_timeout(200)
        check(f"blocked storage shows an error state with a next step {errs}", pg.locator("#finds-list .err-state").count() == 1 and "换成普通浏览器窗口" in pg.inner_text("#finds-list") and not errs)
        ctx.close()
        ctx = b.new_context(viewport={"width": 390, "height": 844})
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url + "design-system.html"); pg.wait_for_timeout(500)
        have = [pg.locator(s).count() > 0 for s in [".seg", ".toggle", "dialog.bsheet", ".skel", ".err-state", '.btn[aria-busy="true"]', ".ds-sw"]]
        pg.click('[data-ds-theme="dark"]'); pg.wait_for_timeout(100)
        check(f"the design system page shows every component and switches theme {have} {errs}", all(have) and pg.evaluate("document.documentElement.dataset.theme") == "dark" and not errs
              and pg.evaluate("document.documentElement.scrollWidth") <= 390)
        ctx.close()

        # ---------- Sprint 2: theme behaviour, settings, tab memory, finder, sheet, safety copy (phone) ----------
        ctx = b.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True, color_scheme="light")
        ctx.add_init_script("""new MutationObserver((ms, o) => { if (document.body) { window.__atBody = [document.documentElement.dataset.theme || 'system',
          document.querySelector('meta[name=theme-color]') && document.querySelector('meta[name=theme-color]').content]; o.disconnect(); } }).observe(document, { childList: true, subtree: true });""")
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url); pg.wait_for_timeout(600)
        check("system light: light browser bar", pg.evaluate("document.querySelector('meta[name=theme-color]').content") == "#F8F6EF")
        pg.emulate_media(color_scheme="dark"); pg.wait_for_timeout(200)
        check("following the system: the browser bar turns dark when the phone does",
              pg.evaluate("document.querySelector('meta[name=theme-color]').content") == "#0F1210" and pg.evaluate("getComputedStyle(document.body).backgroundColor") != "rgb(248, 246, 239)")
        pg.click("[data-open-settings]"); pg.wait_for_timeout(200)
        check("the header opens one settings sheet", pg.evaluate("document.getElementById('settings').open"))
        pg.click('#settings [data-theme-pick="light"]'); pg.wait_for_timeout(150)
        check("a manual choice beats the system, and every theme control agrees",
              pg.evaluate("getComputedStyle(document.body).backgroundColor") == "rgb(248, 246, 239)"
              and pg.evaluate("[...document.querySelectorAll('[data-theme-pick=light]')].every(b => b.getAttribute('aria-pressed') === 'true')")
              and pg.evaluate("document.querySelector('meta[name=theme-color]').content") == "#F8F6EF")
        pg.check("#set-field"); pg.wait_for_timeout(150)
        check("the outdoor switch in settings uses the same outdoor mode as the header", pg.evaluate("document.documentElement.dataset.field") == "on"
              and pg.get_attribute(".hdr__field", "aria-pressed") == "true" and pg.evaluate("document.documentElement.dataset.theme") == "light")
        pg.uncheck("#set-field"); pg.click('#settings a[href="#data-center"]'); pg.wait_for_timeout(500)
        check("a settings link closes the sheet and opens the page", not pg.evaluate("document.getElementById('settings').open")
              and pg.evaluate("document.querySelector('.view.is-active').id") == "v-log")
        pg.reload(); pg.wait_for_timeout(600)
        check(f"no flash: the chosen theme and bar colour are set before the body exists ({pg.evaluate('window.__atBody')})", pg.evaluate("window.__atBody") == ["light", "#F8F6EF"])
        pg.evaluate("themeSet('system')"); pg.emulate_media(color_scheme="light")
        # tab memory
        pg.evaluate("navigate('species')"); pg.wait_for_timeout(400); pg.evaluate("window.scrollTo(0, 700)"); pg.wait_for_timeout(100)
        pg.click('.botnav a[href="#explore"]'); pg.wait_for_timeout(300); pg.click('.botnav a[href="#home"]'); pg.wait_for_timeout(400)
        check(f"returning to 识菌 restores its last page and scroll ({pg.evaluate('scrollY')})", pg.evaluate("document.querySelector('.view.is-active').id") == "v-species" and abs(pg.evaluate("scrollY") - 700) < 5)
        pg.click('.botnav a[href="#home"]'); pg.wait_for_timeout(500)
        check("tapping the current tab again goes to its first page, at the top", pg.evaluate("document.querySelector('.view.is-active').id") == "v-home" and pg.evaluate("scrollY") < 5)
        pg.go_back(); pg.wait_for_timeout(400)
        check("browser back still works after tab taps", pg.evaluate("document.querySelector('.view.is-active').id") == "v-species")
        check("the home page has no duplicate 继续探索 links", pg.locator("#v-home .home-learn").count() == 0 and "继续探索" not in pg.inner_text("#v-home"))
        # finder and sheet
        pg.evaluate("navigate('finder')"); pg.wait_for_timeout(600)
        check("the first finder question starts within the first screen", pg.evaluate("document.querySelector('#finder-steps legend').getBoundingClientRect().top") < 812
              and pg.evaluate("document.getElementById('model').compareDocumentPosition(document.getElementById('finder-results')) & Node.DOCUMENT_POSITION_PRECEDING") > 0)
        pg.click('[data-f="hym"][data-v="gills"]'); pg.wait_for_timeout(400)
        jr = pg.evaluate("document.getElementById('finder-jump').getBoundingClientRect().top"); pr = pg.evaluate("document.querySelector('.wiz__progress').getBoundingClientRect().bottom")
        check(f"the candidates pill floats above the tab bar and does not cover the question ({pr} < {jr})", jr > pr and jr < 812)
        pg.goto(url + "#sp-hydnum-repandum"); pg.wait_for_timeout(700)
        sh = pg.inner_text("#sheet")
        check("species sheet: section jumps within the first screen; grade, review honesty and notes visible; details fold",
              pg.evaluate("document.querySelector('#sheet [class*=sheet__nav]').getBoundingClientRect().top") < 812
              and "非真菌学专家审核" in sh and "卷边桩菇" in sh and pg.locator("#sheet details.safety__more").count() == 1)
        pg.evaluate("document.getElementById('sheet').close()")
        # safety copy and offline pill
        pg.evaluate("navigate('guide')"); pg.wait_for_timeout(400)
        g = pg.inner_text("#v-guide")
        check("the kitchen guide gives no cooking advice for amanitas and no trial portions", "鹅膏属的种类本站没有评估，不提供吃法" in g and "赭盖鹅膏" not in g and "第一次吃少量" not in g and "先少量" not in g)
        check("the offline pill links to what works offline", pg.get_attribute("[data-net-pill]", "href") == "#guide-offline")
        # drag a sheet closed
        pg.click("[data-open-settings]"); pg.wait_for_timeout(200)
        box = pg.locator("#settings .bsheet__grab").bounding_box()
        pg.mouse.move(box["x"] + 10, box["y"] + 2); pg.mouse.down(); pg.mouse.move(box["x"] + 10, box["y"] + 160, steps=6); pg.mouse.up(); pg.wait_for_timeout(200)
        check(f"dragging a sheet down closes it {errs}", not pg.evaluate("document.getElementById('settings').open") and not errs)
        ctx.close()

        # ---------- Sprint 3: field experience (phone) ----------
        ctx = b.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True, accept_downloads=True)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url + "#guide-kitchen"); pg.wait_for_timeout(700)
        g = pg.inner_text("#v-guide")
        check("no salad wording for wild mushrooms; every method says cook thoroughly", "沙拉" not in g and "不论哪种做法，野生菌都要彻底煮熟" in g)
        pg.evaluate("navigate('finder')"); pg.wait_for_timeout(500)
        check("the mycorrhiza entry is no longer absolute", "菌根菌只在相应树木附近出现" not in pg.inner_text("#v-finder"))
        # tab memory survives a refresh
        pg.evaluate("navigate('toxic')"); pg.wait_for_timeout(300); pg.click('.botnav a[href="#log"]'); pg.wait_for_timeout(300)
        pg.reload(); pg.wait_for_timeout(700); pg.click('.botnav a[href="#home"]'); pg.wait_for_timeout(400)
        check("after a refresh, 识菌 still reopens its last page", pg.evaluate("document.querySelector('.view.is-active').id") == "v-toxic")
        # finder: dynamic order, persistence, safe reset, empty result
        pg.evaluate("navigate('finder')"); pg.wait_for_timeout(400)
        pg.click('[data-f="hym"][data-v="gills"]'); pg.wait_for_timeout(200)
        check("with deadly amanitas still possible, the next question is the stem base (volva); the header counts what is left",
              "还剩 4 题" in pg.inner_text("#finder-steps legend") and "菌托" in pg.inner_text("#finder-steps legend") and "致命鹅膏" in pg.inner_text("#finder-steps .wiz__next"))
        pg.click('[data-f="volva"][data-v="no"]'); pg.wait_for_timeout(200)
        nxt = pg.inner_text("#finder-steps legend")
        check(f"then the question that narrows most, with the reason shown ({nxt[:12]})", "最能缩小" in pg.inner_text("#finder-steps .wiz__next"))
        pg.click('.botnav a[href="#log"]'); pg.wait_for_timeout(300); pg.click('.botnav a[href="#home"]'); pg.wait_for_timeout(300)
        pg.reload(); pg.wait_for_timeout(700)
        kept = pg.evaluate("[fstate.hym, fstate.volva]")
        check(f"answers survive leaving the finder and a reload ({kept})", kept == ["gills", "no"])
        pg.evaluate("navigate('finder')"); pg.wait_for_timeout(400)
        pg.click("#finder-reset"); pg.wait_for_timeout(100)
        check("one tap on 重新开始 does not wipe the answers", pg.evaluate("fstate.hym") == "gills" and "再点一次" in pg.inner_text("#finder-reset"))
        pg.click("#finder-reset"); pg.wait_for_timeout(100)
        check("the second tap clears them", pg.evaluate("fstate.hym") is None)
        pg.evaluate("fstate.hym = 'pores'; fstate.sub = 'wood'; fstate.spore = 'pink'; renderFinder()"); pg.wait_for_timeout(200)
        r0 = pg.inner_text("#finder-results")
        check("no candidates at all: says the database is limited and toxic species are not ruled out", "一个候选都没有" in r0 and "不说明它无毒" in r0)
        check("the finder never claims success or safety", not any(w in r0 for w in ["识别成功", "可以食用", "确认是"]))
        pg.click("#finder-reset"); pg.click("#finder-reset")
        # species and toxic sheets share one hierarchy
        pg.goto(url + "#sp-cantharellus-formosus"); pg.wait_for_timeout(700)
        ids = pg.eval_on_selector_all("#sheet .sheet__sec", "els => els.map(e => e.id)")
        check(f"species sheet order: features, look-alikes, limits, habitat and season, kitchen, sources {ids}",
              ids == ["sh-id", "sh-look", "sh-limit", "sh-eco", "sh-kitchen", "sh-more"] and "都不能确认手上的菌是哪一种" in pg.inner_text("#sh-limit"))
        pg.evaluate("document.getElementById('sheet').close()")
        pg.goto(url + "#tx-amanita-phalloides"); pg.wait_for_timeout(700)
        ids = pg.eval_on_selector_all("#sheet .sheet__sec", "els => els.map(e => e.id)")
        lim = pg.inner_text("#sh-limit")
        check(f"toxic sheet uses the same hierarchy with a feature table {ids}", ids == ["sh-id", "sh-look", "sh-limit", "sh-more"]
              and pg.locator("#sh-id .fact").count() == 5 and "菌托常埋在土里" in lim and "任何一条都不足以排除它" in lim)
        pg.evaluate("document.getElementById('sheet').close()")
        # comparisons
        pg.evaluate("navigate('toxic')"); pg.wait_for_timeout(500)
        card = "#cmp-chanterelle"
        pg.click(f'{card} [data-cmp-mode="side"]'); pg.wait_for_timeout(100)
        labels = pg.eval_on_selector_all(f"{card} .cmp__row-label", "els => els.map(e => e.textContent)")
        keyfirst = [("关键" in l) for l in labels[:-1]]
        check(f"comparison rows: key differences first, 结论 last, variability warned ({labels})",
              labels[-1].startswith("结论") and keyfirst == sorted(keyfirst, reverse=True) and "看不到的特征" in pg.inner_text(card)
              and pg.locator(f"{card} .cmp__cols a").count() >= 3)
        # outdoor mode: fewer extras, journal and safety kept, theme untouched
        pg.evaluate("themeSet('dark')"); pg.evaluate("fieldSet(true)"); pg.evaluate("navigate('home')"); pg.wait_for_timeout(300)
        vis = lambda s: pg.evaluate(f"(() => {{ const e = document.querySelector('{s}'); return !!(e && e.offsetParent); }})()")
        check("outdoor mode keeps search, finder entry, journal and safety, hides seasonal extras, and leaves the theme alone",
              vis("#home-q") and vis(".home-act") and vis(".home-jr") and vis(".home-safety") and not vis(".home-season") and not vis("#today")
              and pg.evaluate("document.documentElement.dataset.theme") == "dark")
        pg.evaluate("fieldSet(false); themeSet('system')")
        check(f"no errors in the field-experience flow {errs}", not errs)
        ctx.close()
        # offline: incomplete cache, finder and journal without network
        ctx = b.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True, accept_downloads=True)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url + "#explore-offline"); pg.wait_for_timeout(2500)
        ready = "已可离线" in pg.inner_text("#offline-status")
        ctx.set_offline(True); pg.reload(); pg.wait_for_timeout(1200)
        pg.wait_for_timeout(1500); pg.evaluate("offlineReport()"); pg.wait_for_timeout(300)  # report and cache read at the same moment
        off = pg.inner_text("#off-photos") if pg.locator("#off-photos").count() else ""
        cached = pg.evaluate("""caches.open(MEDIA_CACHE).then(c => c.keys()).then(ks => photoSets.small.filter(f => ks.some(r => new URL(r.url).pathname.endsWith('/' + f))).length)""")
        import re as _re
        shown = int(_re.search(r"(\d+) / \d+ 张", off).group(1)) if _re.search(r"(\d+) / \d+ 张", off) else -1
        check(f"offline after one online visit: the page starts and reports exactly the photos really cached ({shown} = {cached})", ready and shown == cached and shown < pg.evaluate("photoSets.small.length"))
        pg.evaluate("navigate('finder')"); pg.wait_for_timeout(300)
        pg.click('[data-f="hym"][data-v="pores"]'); pg.wait_for_timeout(300)
        check("the finder works offline", pg.locator("#finder-results .res-item").count() > 0)
        pg.evaluate("navigate('log')"); pg.wait_for_timeout(700)
        pg.select_option("#finds-sp", "boletus-edulis"); pg.click("#finds-save"); pg.wait_for_timeout(400)
        rid = pg.evaluate("findsLoad()[0].id")
        pg.click(f'[data-edit="{rid}"]'); pg.evaluate("jstep(3)"); pg.fill("#finds-notes", "离线改的"); pg.click("#finds-save"); pg.wait_for_timeout(400)
        with pg.expect_download() as dl:
            pg.click("#finds-export-json")
        bk = dl.value.path(); pg.wait_for_timeout(300)
        pg.set_input_files("#finds-import", bk); pg.wait_for_timeout(400)
        same = "内容相同" in pg.inner_text("#imp"); pg.click("[data-imp-cancel]")
        check(f"journal add, edit, export and import preview all work offline {errs}", pg.evaluate("findsLoad().length") == 1
              and pg.evaluate("findsLoad()[0].notes") == "离线改的" and same and not errs)
        slug = pg.evaluate("""caches.open(MEDIA_CACHE).then(c => c.keys()).then(ks => DATA.species.find(s => s.photo && !ks.some(r => r.url.endsWith('/photos/' + s.photo.file))).slug)""")
        pg.goto(url + "#sp-" + slug); pg.wait_for_timeout(800)
        miss = pg.evaluate("(() => { const i = document.querySelector('#sheet .photo__img'); return !i.complete || i.naturalWidth === 0 || i.classList.contains('is-missing'); })()")
        check("an example photo that was never downloaded shows as a grey frame, not as cached", miss)
        ctx.set_offline(False); ctx.close()

        # ---------- v50.2: 拾菌 navigation (phone) ----------
        ctx = b.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url + "#explore"); pg.wait_for_timeout(700)
        active = lambda: pg.evaluate("[document.querySelector('[data-xp-cat][aria-pressed=true]').dataset.xpCat, document.querySelector('[data-xp-go][aria-current=page]').dataset.xpGo, [...document.querySelectorAll('.xp__pane')].filter(p => !p.hidden).map(p => p.dataset.xp)]")
        check(f"拾菌 opens on 找菌 › 本月探索 with one pane shown {active()}", active() == ["find", "now", ["now"]] and pg.is_visible("#explore-region"))
        h0 = pg.evaluate("document.getElementById('v-explore').scrollHeight")
        check(f"the 拾菌 page no longer stacks every section ({h0}px)", h0 < 4000)
        pg.click('[data-xp-cat="guide"]'); pg.wait_for_timeout(300); pg.click('[data-xp-go="prep"]'); pg.wait_for_timeout(300)
        nav_top = pg.evaluate("document.getElementById('explore-nav').getBoundingClientRect().top")
        check(f"a new sub-page starts at the top of the content ({nav_top})", nav_top < 200 and active() == ["guide", "prep", ["prep"]] and not pg.is_visible("#explore-region"))
        pg.click('[data-xp-cat="tools"]'); pg.wait_for_timeout(300)
        check("工具 opens 离线下载 first", active()[1] == "offline" and pg.is_visible("#offline-status"))
        pg.click('[data-xp-cat="guide"]'); pg.wait_for_timeout(300)
        check("each category keeps its last sub-page", active()[1] == "prep")
        pg.go_back(); pg.wait_for_timeout(300); a1 = active()[1]
        pg.go_back(); pg.wait_for_timeout(300); a2 = active()[1]
        pg.go_forward(); pg.wait_for_timeout(300); a3 = active()[1]
        check(f"back and forward restore the sub-page ({a1}, {a2}, {a3})", (a1, a2, a3) == ("offline", "prep", "offline"))
        pg.evaluate("navigate('explore-pick')"); pg.wait_for_timeout(300); pg.reload(); pg.wait_for_timeout(700)
        check("a refresh restores the current sub-page", active()[1] == "pick")
        pg.click('.botnav a[href="#log"]'); pg.wait_for_timeout(300); pg.click('.botnav a[href="#explore"]'); pg.wait_for_timeout(300)
        check("leaving 拾菌 and coming back keeps the sub-page", active()[1] == "pick")
        pg.click('.botnav a[href="#explore"]'); pg.wait_for_timeout(400)
        check("tapping 拾菌 again goes to 找菌 › 本月探索 at the top", active()[:2] == ["find", "now"] and pg.evaluate("scrollY") < 5)
        for h, sub in [("guide-calendar", "cal"), ("guide-field", "rules"), ("guide-offline", "offline"), ("guide-habitats", "hab")]:
            pg.goto(url + "#" + h); pg.wait_for_timeout(500)
            check(f"old link #{h} opens 拾菌 › {sub}", active()[1] == sub and pg.evaluate("document.querySelector('.view.is-active').id") == "v-explore")
        pg.goto(url + "#guide-theme"); pg.wait_for_timeout(500)
        check("old link #guide-theme opens the settings sheet (外观 lives there now)", pg.evaluate("document.getElementById('settings').open"))
        pg.keyboard.press("Escape"); pg.wait_for_timeout(150)
        focusable = pg.evaluate("[...document.querySelectorAll('.xp__pane[hidden] a, .xp__pane[hidden] button, .xp__pane[hidden] input, .xp__pane[hidden] select')].filter(e => e.offsetParent !== null).length")
        check(f"hidden sub-pages are out of the focus order ({focusable})", focusable == 0 and pg.locator(".xp__pane[hidden]").count() == 9)
        pg.evaluate("navigate('explore-field')"); pg.wait_for_timeout(300)
        pg.click('[data-xp-subs="tools"] [data-open-settings]'); pg.wait_for_timeout(200)
        check("工具 › 设置 opens the existing settings sheet", pg.evaluate("document.getElementById('settings').open"))
        pg.keyboard.press("Escape")
        txt = pg.evaluate("document.getElementById('v-explore').textContent")
        found = all(k in txt for k in ["四条守则", "出发前清单", "什么时候找", "依法采集", "做孢子印", "迷路或受伤", "这台设备上存了什么", "装到手机桌面", "户外模式", "季节情报", "产季日历"])
        check("every old 拾菌 section is still reachable from the new navigation", found and pg.locator("#xp-field [role=switch][data-field-switch]").count() == 1)
        pg.evaluate("themeSet('dark'); fieldSet(true); navigate('explore-now')"); pg.wait_for_timeout(300)
        hgt = pg.evaluate("document.querySelector('[data-xp-subs=find] .xnav__sub').getBoundingClientRect().height")
        check(f"outdoor mode and dark theme: the navigation stays usable ({hgt}px) and the theme is kept",
              hgt >= 52 and pg.evaluate("document.documentElement.dataset.theme") == "dark" and pg.evaluate("document.documentElement.scrollWidth") <= 375)
        pg.evaluate("fieldSet(false); themeSet('system')")
        check(f"no JavaScript errors in the 拾菌 navigation {errs}", not errs)
        ctx.close()

        # ---------- v53: 拾菌 Explore UX polish ----------
        SUBS = ["now", "intel", "cal", "hab", "rules", "prep", "pick", "safety", "offline", "field"]
        shown_sub = "[...document.querySelectorAll('.xp__pane')].filter(p => !p.hidden).map(p => p.dataset.xp)"
        # AC-01 / AC-02: direct links; record every frame so a flash of another sub-page would be caught
        FRAMES = "window.__panes = []; (function f() { const v = document.getElementById('v-explore'); if (v && v.classList.contains('is-active')) window.__panes.push([...document.querySelectorAll('.xp__pane')].filter(p => !p.hidden && p.offsetParent !== null).map(p => p.dataset.xp).join()); requestAnimationFrame(f); })();"
        for h, want in [("explore", "now"), ("guide-calendar", "cal")]:
            ctx = b.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True)
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.add_init_script(FRAMES)
            pg.goto(url + "#" + h); pg.wait_for_timeout(900)
            seen = set(pg.evaluate("window.__panes"))
            check(f"v53 AC-0{1 if want == 'now' else 2}: #{h} opens only 拾菌 › {want}, no other sub-page painted first ({seen}) {errs}",
                  seen == {want} and pg.evaluate(shown_sub) == [want] and not errs)
            ctx.close()
        ctx = b.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True, color_scheme="light")
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url + "#explore-now"); pg.wait_for_timeout(800)
        head = pg.inner_text("#v-explore .view__head")
        check(f"v53: the 拾菌 header is compact: no header photo, no eyebrow, a short lead ({len(head)} chars)",
              pg.locator("#v-explore .view__hero").count() == 0 and pg.locator("#v-explore .view__eyebrow").count() == 0 and len(head) < 60 and "不是实时出菇预测" in head)
        nav_y = pg.evaluate("document.getElementById('explore-nav').getBoundingClientRect().top")
        sticky = pg.evaluate("getComputedStyle(document.getElementById('explore-nav')).position")
        check(f"v53: the 拾菌 navigation sits in the first screen and is not sticky ({nav_y}px, {sticky})", nav_y < 260 and sticky not in ("sticky", "fixed"))
        regs = pg.evaluate("[...document.querySelectorAll('[data-cal-region=all]')].map(b => b.textContent.trim())")
        check(f"v53: the all-regions chip reads 整个 PNW everywhere and keeps its meaning ({regs})",
              regs and all(r == "整个 PNW" for r in regs) and "三地合计" not in pg.content()
              and all("BC" in pg.get_attribute(f"[data-cal-region=all] >> nth={i}", "title") for i in range(len(regs))))
        lbl = pg.inner_text("[data-now-all]")
        check(f"v53: 本月探索 names month, region and what the full-list button does ({lbl!r})",
              "看全部" not in pg.inner_text("#xp-now") and "月的全部种类" in lbl and "整个 PNW" in pg.inner_text("#now-title") and pg.locator("#now-track .now__item").count() > 0)
        pg.click("[data-now-all]"); pg.wait_for_timeout(500)
        check("v53: the full-list button opens the 图鉴 filtered to this month", pg.evaluate("document.querySelector('.view.is-active').id") == "v-species" and pg.evaluate("state.season") == "now")
        # every sub-page at 5 widths: one pane, no overflow, 44px targets, state not by colour alone
        for w in [320, 375, 390, 768, 1024]:
            pg.set_viewport_size({"width": w, "height": 800}); bad = []
            for s in SUBS:
                pg.evaluate(f"navigate('explore-{s}')"); pg.wait_for_timeout(260)  # after the 180ms selection transition (v53.2)
                sw = pg.evaluate("document.documentElement.scrollWidth")
                small = pg.evaluate("[...document.querySelectorAll('#explore-nav button:not([hidden])')].filter(b => b.offsetParent && b.getBoundingClientRect().height < 44).length")
                marks = pg.evaluate("(() => { const c = document.querySelector('[data-xp-cat][aria-pressed=true]'), g = document.querySelector('[data-xp-go][aria-current=page]'); return [c && getComputedStyle(c).backgroundColor !== 'rgba(0, 0, 0, 0)', g && getComputedStyle(g, '::after').opacity === '1' && getComputedStyle(g, '::after').height === '3px', g && +getComputedStyle(g).fontWeight >= 600]; })()")
                if sw > w or small or pg.evaluate(shown_sub) != [s] or not all(marks):
                    bad.append((s, sw, small, marks))
            check(f"v53 AC-03 at {w}px: every sub-page shows alone, no horizontal overflow, 44px nav targets, selected state shown by shape and weight {bad}", not bad)
        pg.set_viewport_size({"width": 375, "height": 812})
        # 野外指南: no chapter numbers, one rules source, the spore print is back, collecting order, permits, emergency first
        txt = pg.evaluate("document.getElementById('v-explore').textContent")
        import re as _re
        nums = pg.evaluate("[...document.querySelectorAll('#v-explore .panel__title, #v-explore h2, #v-explore h3')].map(h => h.textContent.trim()).filter(t => /^0\\d/.test(t))")
        check(f"v53 AC-05: no chapter numbers left in 拾菌 ({nums})", pg.locator("#v-explore .panel__num").count() == 0 and not nums)
        check(f"v53 AC-05: 四条守则 has one source ({txt.count('四条守则')}) and 采集与观察 links to it",
              txt.count("四条守则") == 1 and pg.locator("#v-explore ol.rules").count() == 1 and pg.locator('#xp-pick a[href="#explore-rules"]').count() == 1)
        pg.evaluate("navigate('explore-pick')"); pg.wait_for_timeout(300)
        pk = pg.inner_text("#xp-pick")
        order = [pk.find(k) for k in ["观察", "拍照", "记录", "依法采集（若允许）"]]
        check(f"v53: 采集与观察 runs 观察 → 拍照 → 记录 → 依法采集 and says to only look where collecting is not allowed {order}",
              all(i >= 0 for i in order) and order == sorted(order) and "不允许或不确定，就只看、只拍、只记" in pk)
        spore = pg.locator("#spore-print")
        pg.click("#spore-print summary"); pg.wait_for_timeout(400)
        check("v53: the spore-print method (lost in v52) is back as a fold under 采集与观察",
              spore.count() == 1 and pg.locator("#spore-print .steps li").count() == 4 and "绿色" in pg.inner_text("#spore-print") and "不能证明安全" in pg.inner_text("#spore-print"))
        pg.evaluate("navigate('explore-rules')"); pg.wait_for_timeout(200)
        rl = pg.inner_text("#xp-rules")
        check("v53: the permit rule says to follow the land manager's latest rules and promises nothing", "管理方" in rl and "最新的规定" in rl and "本站不判断任何地点能不能采" in rl)
        pg.evaluate("navigate('explore-prep')"); pg.wait_for_timeout(200)
        pr = pg.inner_text("#xp-prep")
        miss = [k for k in ["离线地图", "充电宝", "头灯", "天气预报", "告诉家人", "AdventureSmart"] if k not in pr]
        check(f"v53: 装备与准备 is a short checklist: offline map, power, light, weather, trip plan, with a source {miss}", not miss and pg.locator("#xp-prep .xp-check li").count() <= 7)
        pg.evaluate("navigate('explore-safety')"); pg.wait_for_timeout(300)
        tops = pg.evaluate("[...document.querySelectorAll('#xp-safety .xp-sos a')].map(a => [a.getAttribute('href'), Math.round(a.getBoundingClientRect().bottom)])")
        check(f"v53: 户外安全 puts 911 and 中毒急救 first, outside any fold ({tops})",
              [t[0] for t in tops] == ["tel:911", "#emergency"] and all(t[1] < 812 for t in tops) and pg.locator("#xp-safety details").count() == 0)
        # 找菌: habitats, season intelligence, calendar state
        pg.evaluate("navigate('explore-hab')"); pg.wait_for_timeout(300)
        hb = pg.inner_text("#xp-hab")
        sums = pg.evaluate("[...document.querySelectorAll('#xp-hab details.habitat')].map(d => [d.open, d.querySelector('.habitat__name b').textContent.trim().length > 0])")
        check(f"v53: 生境探索 shows compact folded cards with a text name (photos optional) and no 'good sign' inference ({len(sums)})",
              sums and all(not o and n for o, n in sums) and "好兆头" not in hb and "不代表某一种菌就在附近" in hb)
        pg.evaluate("navigate('explore-intel')"); pg.wait_for_timeout(300)
        pg.click('[data-intel-m="9"]'); pg.wait_for_timeout(200)
        cav = pg.inner_text(".intel__caveat")
        check("v53: 季节情报 states sampling bias and timeliness limits", all(k in cav for k in ["拍照上传", "不是菌有多少", "反映不了今年的天气", "不代表这个月就能找到"]))
        pg.evaluate("navigate('explore-cal')"); pg.wait_for_timeout(300)
        pg.click('[data-cal-mode="month"]'); pg.select_option("#cal-month", "3"); pg.fill("#cal-q", "鸡油"); pg.wait_for_timeout(200)
        st0 = pg.inner_text("#cal-state")
        pg.reload(); pg.wait_for_timeout(900)
        restored = [pg.evaluate("calState.mode"), pg.input_value("#cal-month"), pg.input_value("#cal-q"), pg.evaluate("intelMonth"), pg.evaluate(shown_sub)]
        check(f"v53 AC-04: calendar mode, month, search and the intel month survive a refresh ({restored}, {st0!r})",
              restored == ["month", "3", "鸡油", 9, ["cal"]] and "3 月" in st0 and "鸡油" in st0 and pg.is_visible("#cal-month"))
        pg.click('.botnav a[href="#log"]'); pg.wait_for_timeout(300); pg.click('.botnav a[href="#explore"]'); pg.wait_for_timeout(400)
        check("v53 AC-04: leaving for another tab and coming back keeps the calendar state", pg.evaluate(shown_sub) == ["cal"] and pg.input_value("#cal-q") == "鸡油")
        pg.go_back(); pg.wait_for_timeout(300); pg.go_forward(); pg.wait_for_timeout(300)
        check(f"v53 AC-08: back and forward keep the sub-page and its state {errs}", pg.evaluate(shown_sub) == ["cal"] and pg.evaluate("calState.mode") == "month" and not errs)
        pg.fill("#cal-q", "zzzz"); pg.wait_for_timeout(150)
        check("v53: an empty calendar search says what to try and that not listed is not safe", "没有列出不代表它安全" in pg.inner_text("#cal"))
        pg.fill("#cal-q", ""); pg.click('[data-cal-mode="cal"]')
        # 工具: outdoor switch, independent of the theme; settings reuse
        pg.evaluate("themeSet('dark'); navigate('explore-field')"); pg.wait_for_timeout(300)
        swt = pg.locator("#xp-field-switch")
        pg.click("#xp-field .xp-switch .toggle"); pg.wait_for_timeout(200)
        on = [pg.evaluate("document.documentElement.dataset.field"), swt.is_checked(), pg.inner_text("[data-field-state]"), pg.get_attribute(".hdr__field", "aria-pressed"), pg.evaluate("document.getElementById('set-field').checked"), pg.evaluate("document.documentElement.dataset.theme")]
        pg.click("#xp-field .xp-switch .toggle"); pg.wait_for_timeout(200)
        off = [pg.evaluate("document.documentElement.dataset.field || ''"), swt.is_checked(), pg.inner_text("[data-field-state]"), pg.evaluate("document.documentElement.dataset.theme")]
        check(f"v53 AC-07: the outdoor switch shows its state, stays in step with the header and settings, and leaves the theme alone {on} {off}",
              on == ["on", True, "已打开", "true", True, "dark"] and off == ["", False, "已关闭", "dark"] and swt.get_attribute("role") == "switch")
        pg.click('#xp-field [data-open-settings]'); pg.wait_for_timeout(200)
        check("v53 AC-07: 户外模式 links to the one existing settings sheet", pg.evaluate("document.getElementById('settings').open") and pg.locator("dialog#settings").count() == 1)
        pg.keyboard.press("Escape"); pg.evaluate("themeSet('system')")
        # keyboard: the sub-page buttons work with Enter and keep a visible focus
        pg.evaluate("navigate('explore-now')"); pg.wait_for_timeout(200)
        pg.focus('[data-xp-go="intel"]'); pg.keyboard.press("Enter"); pg.wait_for_timeout(300)
        ring = pg.evaluate("getComputedStyle(document.activeElement).outlineStyle")
        check(f"v53: keyboard Enter switches the sub-page and focus stays on the control with a visible ring ({ring})",
              pg.evaluate(shown_sub) == ["intel"] and pg.evaluate("document.activeElement.dataset.xpGo") == "intel" and ring != "none")
        xt = pg.evaluate("document.getElementById('v-explore').textContent")
        safe_bad = [k for k in ["好兆头", "一定能找到", "肯定有菌", "可以放心吃", "必定出现"] if k in xt] + _re.findall(r"(?<!不能)(?<!不)保证安全", xt)
        check(f"v53 AC-10: 拾菌 makes no safety guarantee or certainty claim {safe_bad}", not safe_bad)
        ctx.close()
        # 工具 › 离线下载: real states for text, thumbnails, HD and the personal journal (service worker blocked so routing sees every request)
        ctx = b.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True, service_workers="block")
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url + "#explore-offline"); pg.wait_for_timeout(1200)
        states = pg.evaluate("[[0, 5, false, 0], [5, 5, false, 0], [2, 5, false, 0], [2, 5, false, 3], [2, 5, true, 0]].map(a => ostate(...a).t)")
        check(f"v53 AC-06: the offline rows know five states ({states})", states == ["未下载", "已完成", "部分完成", "下载失败", "下载中"])
        rows = pg.evaluate("[...document.querySelectorAll('.offline__k')].map(k => k.textContent)")
        check(f"v53 AC-06: text, thumbnails, HD and the personal journal are separate rows, status before the download buttons ({rows})",
              all(k in rows for k in ["文字资料", "缩略图", "高清图", "个人菌记"]) and pg.evaluate("document.querySelector('.offline__list').compareDocumentPosition(document.getElementById('off-actions')) & 4") > 0)
        pg.evaluate("findsSave([{id: 77, date: '2026-10-01', sp: 'boletus-edulis', status: 'candidate'}])"); pg.wait_for_timeout(200)
        pg.evaluate("offlineReport()"); pg.wait_for_timeout(400)
        check("v53: the journal row counts this device's records and says they are not a download", "1 条记录" in pg.inner_text("#off-journal") and "不需要下载" in pg.inner_text("#off-journal"))
        summ = pg.inner_text("#off-summary")
        check(f"v53 AC-06: a first visit with nothing downloaded does not claim the photos are offline ({summ!r})",
              "缩略图未下载" in summ and "高清图未下载" in summ and "未下载" in pg.inner_text("#off-photos"))
        pg.route("**/photos/**", lambda r: r.abort())
        pg.click('[data-dl="small"]')
        for _ in range(80):
            pg.wait_for_timeout(250)
            if pg.locator("#off-bar").is_hidden() and pg.inner_text("#off-dl"):
                break
        pg.wait_for_timeout(300)
        check(f"v53 AC-06: a failed download says so, row and message ({pg.inner_text('#off-dl')[:30]!r})",
              "下载失败" in pg.inner_text("#off-photos") and "没下载成功" in pg.inner_text("#off-dl"))
        pg.unroute("**/photos/**")
        pg.evaluate("caches.open(MEDIA_CACHE).then(c => c.add(photoSets.small[0]))"); pg.wait_for_timeout(300)
        pg.evaluate("dl.failed = 0; offlineReport()"); pg.wait_for_timeout(400)
        check("v53 AC-06: one cached photo reads as partial, not as offline-ready", "部分完成" in pg.inner_text("#off-photos") and "部分完成" in pg.inner_text("#off-summary"))
        ctx.set_offline(True); pg.evaluate("offlineReport()"); pg.wait_for_timeout(400)
        check("v53 AC-06: offline, the summary says so and keeps the real counts", pg.inner_text("#off-summary").startswith("现在离线") and "1 / " in pg.inner_text("#off-photos"))
        ctx.set_offline(False)
        for s in SUBS:
            pg.evaluate(f"navigate('explore-{s}')"); pg.wait_for_timeout(60)
        pg.reload(); pg.wait_for_timeout(900)
        check(f"v53 AC-09: the journal survives every sub-page, downloads and a reload {errs}", pg.evaluate("findsLoad().length") == 1 and pg.evaluate("findsLoad()[0].id") == 77 and not errs)
        ctx.close()
        # outdoor mode × theme on the new pieces
        for scheme in ["light", "dark"]:
            ctx = b.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True, color_scheme=scheme)
            ctx.add_init_script("try{localStorage.setItem('mushroom-guide:field','on')}catch(e){}")
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(url + "#explore-safety"); pg.wait_for_timeout(700)
            bad = []
            for s in SUBS:
                pg.evaluate(f"navigate('explore-{s}')"); pg.wait_for_timeout(100)
                if pg.evaluate("document.documentElement.scrollWidth") > 375: bad.append(s)
            check(f"v53: outdoor mode on, {scheme}: every 拾菌 sub-page fits 375px and the switch reads 已打开 {bad} {errs}",
                  not bad and pg.inner_text("[data-field-state]") == "已打开" and pg.is_checked("#xp-field-switch") and not errs)
            ctx.close()

        # ---------- v53.2: 拾菌 navigation visual polish ----------
        NAVSTATE = """(() => { const cs = (e, p) => getComputedStyle(e, p);
          const cats = [...document.querySelectorAll('[data-xp-cat]')].map(b => [b.getAttribute('aria-pressed'), cs(b).backgroundColor, cs(b).color, +cs(b).fontWeight]);
          const subs = [...document.querySelectorAll('[data-xp-subs]:not([hidden]) [data-xp-go]')].map(b => [b.getAttribute('aria-current'), cs(b, '::after').opacity, cs(b, '::after').height, cs(b).backgroundColor, +cs(b).fontWeight, cs(b).color]);
          return { cats, subs }; })()"""
        LUM = "c => { const v = c.match(/[\\d.]+/g).slice(0, 3).map(x => x / 255).map(x => x <= .03928 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4); return .2126 * v[0] + .7152 * v[1] + .0722 * v[2]; }"
        for scheme, bg_want in [("light", "rgb(63, 97, 73)"), ("dark", "rgb(74, 117, 86)")]:
            ctx = b.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True, color_scheme=scheme)
            pg = ctx.new_page(); errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(url + "#explore-now"); pg.wait_for_timeout(700)
            bad = []
            for cat in ["find", "guide", "tools"]:
                pg.click(f'[data-xp-cat="{cat}"]'); pg.wait_for_timeout(250)
                st = pg.evaluate(NAVSTATE)
                on = [c for c in st["cats"] if c[0] == "true"]
                off = [c for c in st["cats"] if c[0] != "true"]
                ratio = pg.evaluate(f"(([a, b]) => {{ const L = {LUM}; const x = L(a), y = L(b); return (Math.max(x, y) + .05) / (Math.min(x, y) + .05); }})", [on[0][1], on[0][2]]) if on else 0
                if len(on) != 1 or on[0][1] != bg_want or ratio < 4.5 or any(c[1] == bg_want for c in off):
                    bad.append((cat, on, round(ratio, 2)))
            check(f"v53.2 AT-1/4 ({scheme}): each category, when selected, is the one solid forest-green segment with text at >= 4.5:1 {bad}", not bad)
            bad = []
            for sub in ["now", "intel", "cal", "hab", "rules", "prep", "pick", "safety", "offline", "field"]:
                pg.evaluate(f"navigate('explore-{sub}')"); pg.wait_for_timeout(250)
                st = pg.evaluate(NAVSTATE)
                cur = [s for s in st["subs"] if s[0] == "page"]
                rest = [s for s in st["subs"] if s[0] != "page"]
                if len(cur) != 1 or cur[0][1] != "1" or cur[0][2] != "3px" or cur[0][4] < 600 or cur[0][3] != "rgba(0, 0, 0, 0)" or any(s[1] != "0" for s in rest):
                    bad.append((sub, cur))
            check(f"v53.2 AT-2 ({scheme}): every sub-page tab shows a 3px indicator and bold text when current, unfilled unlike the categories {bad} {errs}", not bad and not errs)
            ctx.close()
        ctx = b.new_context(viewport={"width": 320, "height": 640}, is_mobile=True, has_touch=True)
        pg = ctx.new_page(); errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.goto(url + "#explore-pick"); pg.wait_for_timeout(800)
        strip = pg.evaluate("""(() => { const s = document.querySelector('[data-xp-subs=guide]'), r = s.getBoundingClientRect(), t = s.querySelector('[aria-current=page]').getBoundingClientRect();
          const tabs = [...s.children]; return { one: new Set(tabs.map(x => x.offsetTop)).size === 1, lines: tabs.every(x => x.getClientRects().length === 1 && x.getBoundingClientRect().height < 60),
          scrolls: s.scrollWidth > s.clientWidth, inview: t.left >= r.left - 1 && t.right <= r.right + 1, fade: s.classList.contains('has-more-l') || s.classList.contains('has-more-r'), sw: document.documentElement.scrollWidth }; })()""")
        check(f"v53.2 AT-3: at 320px the sub-page tabs are one scrollable row, labels on one line, the current tab scrolled into view, an edge fade, no page overflow {strip}",
              strip["one"] and strip["lines"] and strip["scrolls"] and strip["inview"] and strip["fade"] and strip["sw"] <= 320)
        for w in [375, 390]:
            pg.set_viewport_size({"width": w, "height": 800}); pg.wait_for_timeout(200)
            fit = pg.evaluate("[...document.querySelectorAll('[data-xp-subs]')].map(s => { s.hidden = false; const f = s.scrollWidth <= s.clientWidth + 1; return f; })")
            pg.evaluate("xpShow('pick')")
            check(f"v53.2 AT-3: at {w}px all sub-page tabs fit without scrolling {fit}", all(fit) and pg.evaluate("document.documentElement.scrollWidth") <= w)
        pg.set_viewport_size({"width": 375, "height": 800})
        pg.click('[data-xp-go="prep"]'); pg.wait_for_timeout(300)
        live = pg.inner_text("#xp-live")
        ctl = pg.evaluate("[...document.querySelectorAll('[data-xp-go]')].every(b => { const p = document.getElementById(b.getAttribute('aria-controls')); return p && p.dataset.xp === b.dataset.xpGo; })")
        check(f"v53.2 AT-5: switching announces 分类 › 子页 for screen readers, tabs point at their panes, one aria-current and one aria-pressed ({live!r})",
              live == "野外指南 › 装备与准备" and ctl and pg.locator("[data-xp-go][aria-current=page]").count() == 1 and pg.locator("[data-xp-cat][aria-pressed=true]").count() == 1)
        anim = pg.evaluate("[getComputedStyle(document.getElementById('xp-prep')).animationName, getComputedStyle(document.querySelector('[data-xp-cat]')).transitionDuration]")
        pg.evaluate("navigate('explore-safety')"); pg.wait_for_timeout(250)
        safe_anim = pg.evaluate("getComputedStyle(document.getElementById('xp-safety')).animationName")
        check(f"v53.2: the new pane fades in (opacity, ~180ms) and the safety pane never animates ({anim}, {safe_anim})",
              anim[0] == "xp-in" and "0.18s" in anim[1] and safe_anim == "none")
        pg.go_back(); pg.wait_for_timeout(300); a1 = pg.evaluate("document.querySelector('[data-xp-go][aria-current=page]').dataset.xpGo")
        pg.reload(); pg.wait_for_timeout(800); a2 = pg.evaluate("document.querySelector('[data-xp-go][aria-current=page]').dataset.xpGo")
        check(f"v53.2 AT-6: back and refresh keep navigation and content in step ({a1}, {a2}) {errs}",
              a1 == "prep" and a2 == "prep" and pg.evaluate("[...document.querySelectorAll('.xp__pane')].filter(p => !p.hidden).map(p => p.dataset.xp)") == ["prep"] and not errs)
        ctx.close()
        ctx = b.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True, reduced_motion="reduce", color_scheme="dark")
        ctx.add_init_script("try{localStorage.setItem('mushroom-guide:field','on')}catch(e){}")
        pg = ctx.new_page(); pg.goto(url + "#explore-rules"); pg.wait_for_timeout(700)
        rm = pg.evaluate("""[getComputedStyle(document.getElementById('xp-rules')).animationName, getComputedStyle(document.querySelector('[data-xp-cat]')).transitionDuration,
          getComputedStyle(document.querySelector('[data-xp-go=rules]'), '::after').transitionDuration,
          Math.min(...[...document.querySelectorAll('#explore-nav button:not([hidden])')].filter(b => b.offsetParent).map(b => b.getBoundingClientRect().height))]""")
        check(f"v53.2 AT-7/8: outdoor mode keeps 52px navigation targets, and reduced motion turns the fades and transitions off ({rm})",
              rm[0] == "none" and rm[1] in ("0s", "0ms") and rm[2] in ("0s", "0ms") and rm[3] >= 52)
        ctx.close()

        # ---------- sandboxed preview (how many apps show an attached HTML file) ----------
        host = b.new_page(viewport={"width": 390, "height": 844})
        host.set_content('<iframe id=f sandbox="allow-scripts" style="width:390px;height:844px;border:0"></iframe>')
        host.eval_on_selector("#f", "(f, h) => f.srcdoc = h", html); host.wait_for_timeout(900)
        fr = host.frames[1]
        ok = []
        for sel, v in [('.botnav a[href="#explore"]', "explore"), ('.botnav a[href="#log"]', "log"), ('.botnav a[href="#home"]', "home"),
                       ('.subnav a[href="#finder"]', "finder"), ('.subnav a[href="#species"]', "species")]:
            fr.click(sel); host.wait_for_timeout(80)
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
