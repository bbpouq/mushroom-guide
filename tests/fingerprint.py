# -*- coding: utf-8 -*-
"""A behavioural fingerprint of one deployment of the site, shared by the smoke and shadow tests.

fingerprint(browser, base_url) loads the page fresh for a list of deep links and records:
- which view (and 拾菌 sub-page) each link opens, and whether a species sheet opened;
- catalogue sizes (edible, toxic, comparisons, recipes);
- the emergency phone links;
- whether each safety sentence that must never disappear is in the page source;
- JavaScript errors.

The smoke test checks it against EXPECTED_ROUTES and SAFETY; the shadow test diffs a candidate build against production.
"""
import urllib.request

# sentences and phone numbers that must stay on the site (CLAUDE.md, safety rules)
SAFETY = [
    "有任何疑问，就不要吃",
    "本清单不能确认任何蘑菇是否可食用",
    "本食谱仅适用于已经由可靠方式确认身份的食用菌。烹饪不能使有毒蘑菇变得安全。不要仅凭本应用的识别结果决定是否食用。",
    "历史观察数据反映过去记录的分布和季节性，不代表当前地点一定有蘑菇，也不能作为实时出菇预测。",
    "不要等症状",
    "不要自己催吐",
]
TELS = ["tel:18002221222", "tel:911"]

# deep link -> (view id, 拾菌 sub-page or None, sheet open)
EXPECTED_ROUTES = {
    "": ("v-home", None, False),
    "home": ("v-home", None, False),
    "explore": ("v-explore", "now", False),
    "explore-intel": ("v-explore", "intel", False),
    "guide-calendar": ("v-explore", "cal", False),
    "guide-offline": ("v-explore", "offline", False),
    "finder": ("v-finder", None, False),
    "species": ("v-species", None, False),
    "toxic": ("v-toxic", None, False),
    "guide-check": ("v-guide", None, False),
    "recipes": ("v-recipes", None, False),
    "learn": ("v-learn", None, False),
    "log": ("v-log", None, False),
    "data-center": ("v-log", None, False),
    "emergency": ("v-emergency", None, False),
    "sp-boletus-edulis": ("v-species", None, True),
}

STATE = """() => ({
  view: (document.querySelector('.view.is-active') || {}).id || null,
  pane: document.querySelector('#v-explore.is-active') ? ([...document.querySelectorAll('.xp__pane')].find(p => !p.hidden) || {dataset: {}}).dataset.xp || null : null,
  sheet: !!(document.getElementById('sheet') && document.getElementById('sheet').open),
})"""
FACTS = """() => ({
  edible: DATA.species.length, toxic: toxicAll.length, compare: DATA.compare.length, recipes: DATA.recipes.length,
  tels: [...new Set([...document.querySelectorAll('a[href^="tel:"]')].map(a => a.getAttribute('href')))].sort(),
})"""


def source(url):
    req = urllib.request.Request(url, headers={"Cache-Control": "no-cache", "User-Agent": "mycotrail-ci"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def fingerprint(browser, base):
    base = base.rstrip("/") + "/"
    html = source(base).decode("utf-8")
    fp = {"routes": {}, "errors": [], "safety": {s: s in html for s in SAFETY}}
    for h in EXPECTED_ROUTES:
        ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, service_workers="block")
        pg = ctx.new_page()
        pg.on("pageerror", lambda e, h=h: fp["errors"].append(f"#{h}: {e}"))
        pg.goto(base + ("#" + h if h else ""), wait_until="load")
        pg.wait_for_timeout(900)
        st = pg.evaluate(STATE)
        fp["routes"][h] = (st["view"], st["pane"], st["sheet"])
        if h == "":
            facts = pg.evaluate(FACTS)
            fp.update({k: facts[k] for k in ["edible", "toxic", "compare", "recipes", "tels"]})
        ctx.close()
    return fp


def route_problems(fp):
    out = []
    for h, want in EXPECTED_ROUTES.items():
        got = tuple(fp["routes"].get(h) or ())
        if got != want:
            out.append(f"#{h or '(none)'}: expected {want}, got {got}")
    return out


def safety_problems(fp):
    out = [f"missing safety sentence: {s}" for s, ok in fp["safety"].items() if not ok]
    out += [f"missing emergency link: {t}" for t in TELS if t not in fp.get("tels", [])]
    return out
