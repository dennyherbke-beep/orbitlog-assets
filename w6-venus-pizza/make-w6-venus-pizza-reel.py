"""Woche 6, Sonntag - Reel "Could you bake a pizza on Venus?" (Typ d - absurde Frage,
docs/reel-algorithmus.md). Ersetzt w6-hottest-planet-reel (gleiche Fakten, neuer Aufhaenger).
7 Frames, Frage als feste Kopfzeile ueber allen Frames, langsamer Zoom, 17,5 s.

Fakten (NASA Science Venus/Mercury Facts; Neapolitanische Pizza: Holzofen ~430-480 C, Backzeit
60-90 s laut Associazione Verace Pizza Napoletana):
  Venus-Oberflaeche ~465 C (NASA: ~475 C / 900 F), Tag und Nacht. Bodendruck ~92 bar, ~90x Erde,
  vergleichbar mit ~1 km Wassertiefe im Ozean (NASA). Wolken aus Schwefelsaeure.
  Merkur: Tag bis ~430 C, Nacht bis ~-180 C (keine Atmosphaere), naeher an der Sonne als Venus.
  "~90 Sekunden" = Backzeit einer neapolitanischen Pizza bei ~450 C (Naeherung - auf Venus
  fehlt u. a. Sauerstoff, Waermeuebertragung im dichten CO2 anders) -> first_comment.

Hook-Varianten:
  1 "Could you bake a pizza on Venus?" (gewaehlt)   2 "Venus is hotter than a pizza oven"
  3 "Why Venus beats Mercury at being hot"   4 "The planet that's literally a pizza oven"
  5 "Could you cook dinner on another planet?"

    python make-w6-venus-pizza-reel.py  ->  w6-venus-pizza-01..07.png, -cover.png, .mp4
"""

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f
from bodies import planet
from reelkit import (W, H, M, new_frame, header_band, footer_handle, ctext, ctext_block, frame_save,
                     blob, grain, finish)

OUT = Path(__file__).resolve().parent
GY = 860 * S                 # Mitte der Grafik (unter der Kopfzeile)
TY = 1180 * S                # Textblock
HOT = (255, 120, 70)
COLD = (130, 180, 255)
Q = (["Could you bake a", "pizza on Venus?"], "Venus?")


def base(seed):
    img, _ = new_frame(seed)
    header_band(img, *Q)
    return img


def stat(img, label, big, sub, big_col=ACC):
    d = ImageDraw.Draw(img)
    ctext(d, label, f(46 * S, bold=True), FG, TY)
    ctext(d, big, f(88 * S, bold=True), big_col, TY + 64 * S)
    ctext_block(d, sub, f(34 * S), SEC, TY + 186 * S, 46 * S, W - 2 * M - 40 * S)
    footer_handle(d)


def pizza(img, cx, cy, r, baked=1.0, seed=3):
    """Neapolitanische Pizza von oben: Rand mit Leopardenflecken, Tomate, Mozzarella, Basilikum.
    baked 0..1 steuert die Braeunung."""
    rnd = random.Random(seed)
    crust = tuple(int(a + (b - a) * baked) for a, b in zip((236, 214, 168), (214, 160, 92)))
    blob(img, cx, cy, int(r * 1.08), int(r * 1.08), (0, 0, 0), blur=int(r * 0.12), alpha=120)
    blob(img, cx, cy, r, r, crust, blur=int(r * 0.03))
    if baked > 0.5:
        for _ in range(26):                                                   # Leopardenflecken
            a = rnd.uniform(0, 2 * math.pi)
            rr = r * rnd.uniform(0.86, 0.97)
            s = r * rnd.uniform(0.02, 0.05)
            blob(img, int(cx + math.cos(a) * rr), int(cy + math.sin(a) * rr), int(s), int(s),
                 (70, 40, 22), blur=int(s * 0.5), alpha=int(200 * (baked - 0.5) * 2))
    blob(img, cx, cy, int(r * 0.8), int(r * 0.8), (200, 52, 34), blur=int(r * 0.04))     # Tomate
    for _ in range(9):                                                        # Mozzarella
        a, rr = rnd.uniform(0, 2 * math.pi), r * rnd.uniform(0.1, 0.6)
        s = r * rnd.uniform(0.11, 0.17)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        blob(img, int(x), int(y), int(s), int(s * 0.85), (246, 238, 214), blur=int(s * 0.25))
        if baked > 0.6:
            blob(img, int(x + s * 0.2), int(y + s * 0.15), int(s * 0.3), int(s * 0.25), (214, 168, 96),
                 blur=int(s * 0.2), alpha=150)
    d = ImageDraw.Draw(img)
    for _ in range(5):                                                        # Basilikum
        a, rr = rnd.uniform(0, 2 * math.pi), r * rnd.uniform(0.15, 0.55)
        x, y = cx + math.cos(a) * rr, cy + math.sin(a) * rr
        ang = rnd.uniform(0, math.pi)
        lx, ly = math.cos(ang) * r * 0.09, math.sin(ang) * r * 0.09
        d.polygon([(x - lx, y - ly), (x - ly * 0.45, y + lx * 0.45), (x + lx, y + ly), (x + ly * 0.45, y - lx * 0.45)],
                  fill=(46, 120, 52))


def thermometer(img, x, y, h, frac, col):
    d = ImageDraw.Draw(img)
    w = 34 * S
    d.rounded_rectangle([x - w / 2, y - h, x + w / 2, y], w / 2, outline=HAIR, width=4 * S)
    d.rounded_rectangle([x - w / 2 + 8 * S, y - h * frac, x + w / 2 - 8 * S, y - 8 * S], w / 2, fill=col)
    d.ellipse([x - w, y - 10 * S, x + w, y + w * 1.3], fill=col)


def f1():
    img = base(1)
    planet(img, W // 2 + 200 * S, GY + 40 * S, 380, "venus", light=(-0.7, -0.3, 0.6))
    pizza(img, W // 2 - 170 * S, GY + 80 * S, 170 * S, baked=0.0)
    d = ImageDraw.Draw(img)
    ctext(d, "Yes or no?", f(76 * S, bold=True), FG, TY + 40 * S)
    ctext(d, "comment before the answer ↓", f(36 * S), SEC, TY + 150 * S)
    footer_handle(d)
    return img


def f2():
    img = base(2)
    blob(img, W // 2, GY + 140 * S, 300 * S, 90 * S, (255, 140, 40), blur=60 * S, alpha=170)
    pizza(img, W // 2, GY + 20 * S, 220 * S, baked=0.6)
    thermometer(img, W - M - 40 * S, GY + 200 * S, 380 * S, 0.8, HOT)
    stat(img, "A pizza oven runs at", "~450 °C",
         "A Neapolitan pizza bakes in 60 to 90 seconds at that heat.", big_col=HOT)
    return img


def f3():
    img = base(3)
    planet(img, W // 2, GY + 40 * S, 460, "venus", light=(-0.7, -0.3, 0.6))
    blob(img, W // 2, GY + 40 * S, 300 * S, 300 * S, HOT, blur=90 * S, alpha=45)
    stat(img, "The ground on Venus:", "~465 °C",
         "Day and night, pole to equator. No cooling down, ever.", big_col=HOT)
    return img


def f4():
    img = base(4)
    blob(img, W // 2, GY + 60 * S, 330 * S, 330 * S, (255, 150, 60), blur=110 * S, alpha=80)
    pizza(img, W // 2, GY + 40 * S, 240 * S, baked=1.0)
    stat(img, "So technically:", "yes, in ~90 seconds",
         "Venus is basically a planet-sized pizza oven.")
    return img


def f5():
    img = base(5)
    cx, cy = W // 2, GY + 40 * S
    pizza(img, cx, cy, 170 * S, baked=1.0)
    d = ImageDraw.Draw(img)
    for i in range(10):                                                     # Druckpfeile von allen Seiten
        a = i * 2 * math.pi / 10
        x0, y0 = cx + math.cos(a) * 340 * S, cy + math.sin(a) * 340 * S
        x1, y1 = cx + math.cos(a) * 230 * S, cy + math.sin(a) * 230 * S
        d.line([x0, y0, x1, y1], fill=COLD, width=7 * S)
        for s_ in (-1, 1):
            d.line([x1, y1, x1 + math.cos(a + s_ * 0.5) * 26 * S, y1 + math.sin(a + s_ * 0.5) * 26 * S],
                   fill=COLD, width=7 * S)
    stat(img, "The catch: the air is", "90x denser",
         "Like standing 1 km deep in the ocean. Your oven - and you - would be crushed.", big_col=COLD)
    return img


def f6():
    img = base(6)
    planet(img, W // 2 - 200 * S, GY + 40 * S, 260, "mercury", light=(-0.8, -0.2, 0.55))
    planet(img, W // 2 + 210 * S, GY + 40 * S, 300, "venus", light=(-0.7, -0.3, 0.6))
    d = ImageDraw.Draw(img)
    ctext(d, "Mercury", f(32 * S, bold=True), SEC, GY + 200 * S, cx=W // 2 - 200 * S)
    ctext(d, "Venus", f(32 * S, bold=True), ACC, GY + 200 * S, cx=W // 2 + 210 * S)
    stat(img, "And why not Mercury?", "-180 °C at night",
         "It's closer to the Sun, but has no air to hold the heat. Venus's thick CO2 blanket does.",
         big_col=COLD)
    return img


def main():
    frames = [f1(), f2(), f3(), f4(), f5(), f6(),
              frame_save(("Send this", "to your pizza-obsessed", "friend"), sub="Save it for your next quiz night")]
    finish(frames, OUT, "w6-venus-pizza", cover_idx=0, motion=True)


if __name__ == "__main__":
    main()
