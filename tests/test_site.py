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
            tabs = pg.eval_on_selector_all(f"{nav} a", "els => els.map(e => e.textContent.trim())")
            for v in ["explore", "log", "home"]:
                pg.click(f'{nav} a[href="#{v}"]'); pg.wait_for_timeout(80)
            pg.click('.subnav a[href="#species"]'); pg.wait_for_timeout(80)
            cur = pg.eval_on_selector_all(f"{nav} a[aria-current]", "els => els.map(e => e.textContent.trim())")
            check(f"{w}px three tabs {tabs}, sub-nav reaches the catalog and 识菌 stays current {cur}",
                  tabs == ["识菌", "拾菌", "菌记"] and pg.evaluate("document.querySelector('.view.is-active').id") == "v-species" and cur == ["识菌"])
            pg.go_back(); pg.wait_for_timeout(150)
            check(f"{w}px back button", pg.evaluate("document.querySelector('.view.is-active').id") == "v-home")
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
        pg.goto(url + "#explore"); pg.wait_for_timeout(400)
        n_now = pg.locator("#now-track .now__item").count()
        pg.click("#now-track .now__item >> nth=0"); pg.wait_for_timeout(500)
        check(f"'this month' strip lists species ({n_now}) and opens one", n_now > 0 and pg.evaluate("document.getElementById('sheet').open"))
        pg.goto(url + "#explore"); pg.wait_for_timeout(400)
        pg.click('#v-explore [data-jump="guide-calendar"]'); pg.wait_for_timeout(1100)
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
        clip = pg.evaluate("""[...document.querySelectorAll('#tox-grid .sp-card, #grid .sp-card')].slice(0, 6).every(c =>
            getComputedStyle(c).overflow === 'hidden' && getComputedStyle(c).borderRadius !== '0px')""")
        check("card photos are clipped to the card's rounded corners", clip)
        n_tx = pg.locator("#tox-grid .sp-card").count()
        pg.click("#tox-grid .sp-card >> nth=0"); pg.wait_for_timeout(500)
        check(f"toxic list uses the species card pattern ({n_tx} cards) and opens a sheet",
              n_tx == 22 and pg.locator("#tox-grid .sp-card__photo").count() == n_tx and pg.evaluate("document.getElementById('sheet').open"))
        pg.goto(url + "#guide-calendar"); pg.reload(); pg.wait_for_timeout(1000)
        all_rows = pg.locator("#cal tbody tr").count()
        pg.click('[data-cal-region="bc"]'); pg.wait_for_timeout(150)
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
              and pg.locator("#finder-steps .wiz__dot").count() == 5 and "1 / 5" in pg.inner_text("#finder-steps legend"))
        for k, v in [("hym", "gills"), ("sub", "wood"), ("spore", "white")]:
            pg.click(f'[data-f="{k}"][data-v="{v}"]'); pg.wait_for_timeout(50)
        res = pg.inner_text("#finder-results")
        check("finder results do not widen the phone page", pg.evaluate("document.documentElement.scrollWidth") <= 390)
        check("finder gills+wood+white", "发光类脐菇" in res and "蜜环菌" in res and "纹缘盔孢伞" not in pg.inner_text(".res-block--toxic"))
        check("finder results say they are candidates only and link to the emergency page",
              "不判断能不能吃" in res and pg.locator('#finder-results .res-safe a[href="#emergency"]').count() == 1)
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
        pg.goto(url + "#explore"); pg.wait_for_timeout(2500)
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
        pg.evaluate("navigate('species')"); pg.wait_for_timeout(300)
        check("loads offline, and the catalog opens offline", pg.locator("#grid .sp-card").count() > 50)
        check("offline: the header says so and external links are marked",
              pg.locator(".hdr [data-net-pill]").is_visible() and pg.evaluate("document.documentElement.classList.contains('is-offline')"))
        pg.goto(url + "#sp-boletus-edulis"); pg.wait_for_timeout(600)
        check("offline: a species photo still shows (downloaded before)",
              pg.evaluate("(() => { const i = document.querySelector('#sheet .photo__img'); return i.complete && i.naturalWidth > 0; })()"))
        ctx.set_offline(False)
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
        pg.select_option("#finds-sp", "cantharellus-formosus"); pg.fill("#finds-place", "地图测试林")
        pg.click("#finds-gps"); pg.wait_for_timeout(600)
        gps = pg.inner_text("#finds-gps-out")
        png = __import__("base64").b64decode("iVBORw0KGgoAAAANSUhEUgAAAAIAAAACCAIAAAD91JpzAAAAFklEQVR4nGP4z8DAwMDAxMDAwMDAAAANHQEDasKb6QAAAABJRU5ErkJggg==")
        pg.set_input_files("#finds-photo", files=[{"name": "a.png", "mimeType": "image/png", "buffer": png}]); pg.wait_for_timeout(600)
        thumbs = pg.locator("#finds-thumbs .finds__thumb img").count()
        pg.click('#finds-form button[type="submit"]'); pg.wait_for_timeout(500)
        check(f"a find saves GPS ({gps}) and a photo ({thumbs})", "47.60620" in gps and thumbs == 1
              and pg.locator("#finds-list img.finds__pic").count() == 1)
        pg.select_option("#finds-sp", ""); pg.fill("#finds-other", "褐色小伞菌")
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
        pg.fill("#finds-notes", "改过的备注"); pg.click('#finds-form button[type="submit"]'); pg.wait_for_timeout(300)
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
        pg.evaluate("show('explore')"); pg.wait_for_timeout(400)
        ex = pg.inner_text("#v-explore")
        bad_hab = [n for n in ["美味齿菌", "卷缘齿菌", "、鸡油菌、", "皱盖罗鳞伞", "夏松露", "木耳", "高大环柄菇", "粗鳞青褶伞", "荷叶离褶伞"] if n in ex.split("去哪里找")[-1].split("采摘")[0]]
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
