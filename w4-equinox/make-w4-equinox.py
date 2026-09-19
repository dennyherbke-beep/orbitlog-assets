"""Woche 4, Dienstag - Explained image: "Equinox - the Sun crosses the equator". Layout A-Stil
(Kicker + Headline + Subline unten), 1080 x 1350, 1 Bild, aber mit eigener Illustration statt Foto.

Fakten: Herbst-Tagundnachtgleiche 2026 am 23.09. gegen 00:05 UTC (= 22.09., 20:05 Uhr EDT; Star Walk nennt 00:06, EarthSky/Almanac 00:05); die Sonne
steht dann senkrecht ueber dem Aequator, Herbstanfang im Norden, Fruehling im Sueden (NASA Skywatching
Sept. 2026, Star Walk). Erdachse 23,4 Grad geneigt - zeigt zur Tagundnachtgleiche weder zur Sonne
noch von ihr weg. Die Terminator-Linie (Tag/Nacht-Grenze) verlaeuft dann durch beide Pole.

    python make-w4-equinox.py   ->  w4-equinox.png
"""

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, HANDLE, f, fmono, tracked, wrap, canvas, glow, downscale
from reelkit import sphere, blob, grain, TEX

OUT = Path(__file__).resolve().parent
W, H = 1080 * S, 1350 * S
M = 96 * S
LIGHT = (-1.0, 0.0, 0.12)     # Sonne von links, Terminator fast senkrecht durch die Pole


def tex_earth():
    """Ozean, unregelmaessige Kontinente (Kuestensaum + Land), Polkappen, Wolkenschleier."""
    rnd = random.Random(11)
    img = Image.new("RGB", (TEX, TEX), (34, 96, 182))
    blob(img, TEX // 2, TEX // 2, 230, 230, (50, 120, 205), blur=90, alpha=160)
    for _ in range(16):
        cx, cy = rnd.randint(90, TEX - 90), rnd.randint(90, TEX - 90)
        for _ in range(rnd.randint(3, 5)):
            ox, oy = cx + rnd.randint(-38, 38), cy + rnd.randint(-34, 34)
            rx, ry = rnd.randint(20, 48), rnd.randint(16, 36)
            blob(img, ox, oy, rx + 5, ry + 5, (128, 150, 96), blur=3)
            blob(img, ox, oy, rx, ry, rnd.choice([(70, 124, 62), (92, 132, 70), (118, 128, 76)]), blur=4)
    for cy in (6, TEX - 6):
        blob(img, TEX // 2, cy + (14 if cy < 100 else -14), 120, 34, (244, 248, 252), blur=14)
    for _ in range(9):
        blob(img, rnd.randint(60, TEX - 60), rnd.randint(60, TEX - 60), rnd.randint(50, 100),
             rnd.randint(9, 20), (255, 255, 255), blur=16, alpha=100)
    return grain(img, 10, 5)


def arrow(d, x0, x1, y, col, w):
    d.line([x0, y, x1, y], fill=col, width=w)
    d.polygon([(x1 + 22 * S, y), (x1 - 4 * S, y - 12 * S), (x1 - 4 * S, y + 12 * S)], fill=col)


def build():
    img, _ = canvas(W, H)
    cx, cy, R = int(W * 0.56), int(H * 0.335), 250 * S
    img = glow(img, [-W * 0.35, cy - R * 1.4, W * 0.30, cy + R * 1.4], color=ACC, strength=0.34,
               blur_frac=0.13)
    sphere(img, cx, cy, 2 * R // S, tex_earth(), (90, 150, 230), light=LIGHT)
    d = ImageDraw.Draw(img)

    # Sonnenstrahlen von links auf die beleuchtete Halbkugel
    for k in (-0.62, -0.31, 0.0, 0.31, 0.62):
        y = cy + int(R * k)
        x_edge = cx - int(math.sqrt(R * R - (R * k) ** 2))
        arrow(d, M, x_edge - 46 * S, y, ACC, 4 * S)
    tracked(d, (M, cy - R - 40 * S), "SUNLIGHT", fmono(22 * S), ACC, 4 * S)

    # Achse, Aequator, Pole
    d.line([cx, cy - R - 70 * S, cx, cy + R + 70 * S], fill=SEC, width=3 * S)
    eq = 0.16
    d.arc([cx - R, cy - int(R * eq), cx + R, cy + int(R * eq)], 0, 180, fill=(235, 240, 250), width=3 * S)
    d.text((cx - 12 * S, cy - R - 130 * S), "N", font=fmono(30 * S), fill=FG)
    d.text((cx - 12 * S, cy + R + 82 * S), "S", font=fmono(30 * S), fill=FG)

    # Beschriftungen
    d.text((cx + int(R * 0.30), cy + int(R * 0.56)), "night", font=f(30 * S), fill=SEC)
    d.text((cx - int(R * 0.62), cy + int(R * 0.56)), "day", font=f(30 * S), fill=FG)
    d.text((M, cy + R + 70 * S), "Sun directly over the equator", font=f(28 * S, bold=True), fill=ACC)
    d.text((M, cy + R + 108 * S), "Day/night boundary runs pole to pole", font=f(26 * S), fill=SEC)

    # Text unten (Layout A)
    kicker = "EXPLAINED"
    hl = wrap(d, "Equinox: the Sun crosses the equator", f(68 * S, bold=True), W - 2 * M)
    sub = wrap(d, "Around 00:05 UTC on Sept 23 (8:05 pm EDT on Sept 22) autumn begins in the north, "
                  "spring in the south - and day and night are nearly equal everywhere.",
               f(30 * S), W - 2 * M)
    block_h = 46 * S + len(hl) * 80 * S + 18 * S + len(sub) * 42 * S
    y = H - M - block_h
    tracked(d, (M, y), kicker, fmono(27 * S), ACC, 6 * S)
    y += 46 * S
    for ln in hl:
        d.text((M, y), ln, font=f(68 * S, bold=True), fill=FG)
        y += 80 * S
    y += 18 * S
    for ln in sub:
        d.text((M, y), ln, font=f(30 * S), fill=SEC)
        y += 42 * S

    cr = fmono(20 * S)
    d.text((M, M), "Illustration: Orbit Log", font=cr, fill=SEC)
    d.text((W - M - d.textlength(HANDLE, font=cr), M), HANDLE, font=cr, fill=SEC)
    return img


if __name__ == "__main__":
    downscale(build(), 1080, 1350).save(OUT / "w4-equinox.png")
    print("saved w4-equinox.png")
