"""Woche 4, Freitag - Numbers & scale: "A sugar cube of neutron star weighs ~1 billion tons".
Layout B (Zahlengrafik), 1080 x 1350, 1 Bild - gleiches Muster wie w2-stars-vs-sand / w3-venus-day-year.

Fakten (NASA "Imagine the Universe"): Ein Neutronenstern packt etwa die Masse der Sonne in eine
Kugel von ~20 km Durchmesser; ein zuckerwuerfelgrosses Stueck seiner Materie wuerde auf der Erde
rund 1 Milliarde Tonnen (~1 Billion kg) wiegen - etwa so viel wie ein Berg. Werte in anderen
Quellen streuen (~0,4-4 Mrd. t), weil die Dichte im Stern nach innen zunimmt -> im first_comment
offengelegt.

    python make-w4-neutron-star.py   ->  w4-neutron-star.png
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import (S, FG, SEC, ACC, HAIR, f, fmono, tracked, canvas, glow, furniture, downscale)

OUT = Path(__file__).resolve().parent
W, H = 1080 * S, 1350 * S
M = 96 * S


def ctext(d, s, font, fill, cx, y, track=0):
    total = sum(d.textlength(ch, font=font) + track for ch in s) - (track if s else 0)
    if track:
        tracked(d, (cx - total / 2, y), s, font, fill, track)
    else:
        d.text((cx - total / 2, y), s, font=font, fill=fill)


def cube(img, cx, cy, a):
    """Isometrischer Zuckerwuerfel (Kantenlaenge a), Mittelpunkt cx/cy."""
    d = ImageDraw.Draw(img)
    dx, dy = a * 0.866, a * 0.5
    ty = cy - a / 2 - dy
    top = [(cx, ty), (cx + dx, ty + dy), (cx, ty + 2 * dy), (cx - dx, ty + dy)]
    left = [top[3], top[2], (cx, ty + 2 * dy + a), (cx - dx, ty + dy + a)]
    right = [top[2], top[1], (cx + dx, ty + dy + a), (cx, ty + 2 * dy + a)]
    d.polygon(top, fill=(250, 250, 252))
    d.polygon(left, fill=(196, 202, 214))
    d.polygon(right, fill=(150, 158, 174))
    for poly in (top, left, right):
        d.line(poly + [poly[0]], fill=(255, 255, 255), width=2 * S)


def build():
    img, _ = canvas(W, H)
    img = glow(img, [W * 0.10, H * 0.14, W * 0.90, H * 0.54], strength=0.16, blur_frac=0.14)
    d = ImageDraw.Draw(img)
    cx = W // 2

    furniture(d, W, M, "NEUTRON STAR")
    ctext(d, "A SUGAR CUBE OF NEUTRON-STAR MATTER WEIGHS", fmono(23 * S), SEC, cx, int(H * 0.21), track=3 * S)

    ctext(d, "1 billion", f(200 * S, bold=True), ACC, cx, int(H * 0.27))
    ctext(d, "tons", f(84 * S, bold=True), FG, cx, int(H * 0.27) + 250 * S)

    cy = int(H * 0.68)
    cube_cx = M + 110 * S
    cube(img, cube_cx, cy, 130 * S)
    d = ImageDraw.Draw(img)
    x = cube_cx + 190 * S
    d.text((x, cy - 96 * S), "About as much as", font=f(38 * S), fill=SEC)
    d.text((x, cy - 46 * S), "a mountain", font=f(64 * S, bold=True), fill=FG)
    d.text((x, cy + 46 * S), "- in the volume of a sugar cube.", font=f(32 * S), fill=SEC)

    ctext(d, "The star: about the mass of the Sun crushed into a ball", f(27 * S), SEC, cx, int(H * 0.80))
    ctext(d, "roughly 20 km across - the size of a city.", f(27 * S), SEC, cx, int(H * 0.80) + 38 * S)

    ctext(d, "Source: NASA - Imagine the Universe", fmono(20 * S), SEC, cx, int(H * 0.91))
    return img


if __name__ == "__main__":
    downscale(build(), 1080, 1350).save(OUT / "w4-neutron-star.png")
    print("saved w4-neutron-star.png")
