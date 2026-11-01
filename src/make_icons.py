# -*- coding: utf-8 -*-
"""Regenerate the 拾菌记 MycoTrail brand assets in public/ from the master mark (src/brand/mark.svg).

Renders with the pre-installed Chromium through Playwright (pip install playwright), so the PNGs match the SVGs:
    python3 src/make_icons.py
Writes: icon.svg (favicon), favicon-32.png, icon-192.png, icon-512.png, icon-maskable-512.png, apple-touch-icon.png,
og.png (1200x630 share image) and brand/ (logos: Chinese and English lockups, light and dark, one-colour marks).
"""
import os
import re
from pathlib import Path

from playwright.sync_api import sync_playwright

SRC = Path(__file__).resolve().parent
PUBLIC = SRC.parent / "public"
BRAND = PUBLIC / "brand"
FOREST, FOREST_DEEP, IVORY, INK = "#2D5A3D", "#1E3B2A", "#F5F2EA", "#1D231F"
FONT = '-apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", "Noto Sans SC", "Microsoft YaHei", "WenQuanYi Zen Hei", sans-serif'

mark = (SRC / "brand" / "mark.svg").read_text(encoding="utf-8")
inner = re.search(r"<svg[^>]*>(.*)</svg>", mark, re.S).group(1)
inner = re.sub(r"<!--.*?-->", "", inner, flags=re.S).strip()


def tile(size=512, radius=0, scale=1.0, bg=FOREST_DEEP):
    """The mark on a forest-green square; scale < 1 leaves the safe zone a maskable icon needs."""
    off = 256 * (1 - scale)
    rx = f' rx="{radius}"' if radius else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="{size}" height="{size}">'
            f'<rect width="512" height="512"{rx} fill="{bg}"/><g transform="translate({off} {off}) scale({scale})">{inner}</g></svg>')


def mono(colour):
    """One-colour mark: the silhouette only, for stamps, embossing and single-colour print."""
    sil = re.search(r'<path fill="[^"]+" d="([^"]+)"/>', inner).group(1)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path fill="{colour}" d="{sil}"/>'
            f'<g fill="none" stroke="{"#F5F2EA" if colour != "#F5F2EA" else "#1E3B2A"}" stroke-width="10" stroke-linecap="round">'
            + "".join(re.findall(r'<path d="[^"]+"/>', inner)) + "</g></svg>")


def lockup(word, sub, dark):
    """Horizontal logo: tile + name (+ small line). dark = for dark backgrounds."""
    fg, subc = (IVORY, "#C9D3C7") if dark else (INK, "#4F5A50")
    zh = not word.isascii()
    w = 560 if zh else 760
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} 160" width="{w}" height="160">'
            f'<g transform="translate(16 16) scale(0.25)"><rect width="512" height="512" rx="112" fill="{FOREST_DEEP}"/>{inner}</g>'
            f'<text x="176" y="{92 if zh else 90}" font-family=\'{FONT}\' font-size="{64 if zh else 60}" font-weight="700" fill="{fg}"'
            f'{"" if zh else " letter-spacing=\"-1\""}>{word}</text>'
            f'<text x="178" y="130" font-family=\'{FONT}\' font-size="22" fill="{subc}" letter-spacing="{0 if zh else 2}">{sub}</text></svg>')


def og():
    return f"""<html><body style="margin:0"><div style="width:1200px;height:630px;box-sizing:border-box;padding:84px 96px;
      background:{FOREST_DEEP};color:{IVORY};font-family:{FONT.replace(chr(34), chr(39))};display:flex;align-items:center;gap:72px">
      <div style="width:300px;height:300px;flex:none;border-radius:68px;overflow:hidden;background:#173023">{tile(300, 0, 1.0, "#173023")}</div>
      <div><div style="font-size:112px;font-weight:700;letter-spacing:-2px;line-height:1.05">拾菌记</div>
        <div style="font-size:48px;font-weight:600;color:#F2B23C;margin-top:8px">MycoTrail</div>
        <div style="font-size:38px;margin-top:36px;color:#E4E9E1">拾自然之菌，记森林之迹。</div>
        <div style="font-size:26px;margin-top:14px;color:#B7C4B6">Pacific Northwest Mushroom Field Guide</div></div></div></body></html>"""


def main():
    BRAND.mkdir(exist_ok=True)
    (PUBLIC / "icon.svg").write_text(tile(512, 112), encoding="utf-8")
    files = {
        "brand/mark.svg": mark,
        "brand/app-icon.svg": tile(512, 112),
        "brand/mark-mono-forest.svg": mono(FOREST_DEEP),
        "brand/mark-mono-ivory.svg": mono(IVORY),
        "brand/logo-zh-light.svg": lockup("拾菌记", "拾自然之菌，记森林之迹。", False),
        "brand/logo-zh-dark.svg": lockup("拾菌记", "拾自然之菌，记森林之迹。", True),
        "brand/logo-en-light.svg": lockup("MycoTrail", "EXPLORE THE FOREST. KNOW YOUR FUNGI.", False),
        "brand/logo-en-dark.svg": lockup("MycoTrail", "EXPLORE THE FOREST. KNOW YOUR FUNGI.", True),
    }
    for name, svg in files.items():
        (PUBLIC / name).write_text(svg, encoding="utf-8")
    exe = "/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None
    with sync_playwright() as p:
        b = p.chromium.launch(**({"executable_path": exe} if exe else {}))
        for name, size, svg, bg in [("favicon-32.png", 32, tile(32, 7 * 16), None), ("icon-192.png", 192, tile(192), None),
                                    ("icon-512.png", 512, tile(512), None), ("icon-maskable-512.png", 512, tile(512, 0, 0.72), None),
                                    ("apple-touch-icon.png", 180, tile(180), FOREST_DEEP)]:
            pg = b.new_page(viewport={"width": size, "height": size})
            pg.set_content(f'<html><body style="margin:0;background:{bg or "transparent"}">{svg}</body></html>')
            pg.screenshot(path=str(PUBLIC / name), omit_background=bg is None)
            pg.close()
        pg = b.new_page(viewport={"width": 1200, "height": 630})
        pg.set_content(og()); pg.wait_for_timeout(200)
        pg.screenshot(path=str(PUBLIC / "og.png")); pg.close()
        b.close()
    print("brand assets written to", PUBLIC)


if __name__ == "__main__":
    main()
