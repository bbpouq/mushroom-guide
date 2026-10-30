# -*- coding: utf-8 -*-
"""Regenerate the app icons in public/ (needs Pillow: pip install pillow)."""
from pathlib import Path
from PIL import Image, ImageDraw

PUBLIC = Path(__file__).resolve().parent.parent / "public"
GREEN, WHITE = (21, 128, 61, 255), (255, 255, 255, 255)


def icon(size, pad):
    big = size * 4
    im = Image.new("RGBA", (big, big), GREEN)
    d = ImageDraw.Draw(im)
    u, o = big * (1 - 2 * pad) / 24, big * pad
    P = lambda x, y: (o + x * u, o + y * u)  # 24-unit grid
    d.chord([*P(2.5, 4.5), *P(21.5, 19.5)], 180, 360, fill=WHITE)            # cap
    d.rounded_rectangle([*P(8.6, 12.8), *P(15.4, 20.5)], radius=3.2 * u, fill=WHITE)  # stem
    d.rectangle([*P(2.5, 11.95), *P(21.5, 12.8)], fill=GREEN)               # gap under cap
    return im.resize((size, size), Image.LANCZOS)


icon(192, 0.17).save(PUBLIC / "icon-192.png")
icon(512, 0.17).save(PUBLIC / "icon-512.png")
icon(512, 0.25).save(PUBLIC / "icon-maskable-512.png")
icon(180, 0.15).convert("RGB").save(PUBLIC / "apple-touch-icon.png")
print("icons written to", PUBLIC)
