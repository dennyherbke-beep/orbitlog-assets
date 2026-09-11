"""Woche 3, Freitag - Numbers & scale: "A day on Venus is longer than its year".
Layout B (Zahlengrafik), 1080 x 1350, 1 Bild - gleiches Muster wie w2-stars-vs-sand.

Fakten: Venus rotiert retrograd in 243 Erdtagen (siderische Rotationsperiode) um die
eigene Achse, umkreist die Sonne aber schon in 225 Erdtagen. Quelle: NASA Venus Fact
Sheet (NSSDCA).

    python make-w3-venus-day-year.py   ->  w3-venus-day-year.png
"""

import sys
from pathlib import Path

from PIL import ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import (S, FG, SEC, ACC, HAIR, f, fmono, tracked, canvas, glow,
                      furniture, downscale)

OUT = Path(__file__).resolve().parent
W, H = 1080 * S, 1350 * S
M = 96 * S


def ctext(d, s, font, fill, cx, y, track=0):
    total = sum(d.textlength(ch, font=font) + track for ch in s) - (track if s else 0)
    if track:
        tracked(d, (cx - total / 2, y), s, font, fill, track)
    else:
        d.text((cx - total / 2, y), s, font=font, fill=fill)


def build():
    img, _ = canvas(W, H)
    img = glow(img, [W * 0.18, H * 0.30, W * 0.82, H * 0.66], strength=0.16, blur_frac=0.14)
    d = ImageDraw.Draw(img)
    cx = W // 2

    furniture(d, W, M, "VENUS: DAY VS. YEAR")
    ctext(d, "A DAY ON VENUS LASTS LONGER THAN ITS YEAR", fmono(23 * S), SEC, cx, int(H * 0.25), track=3 * S)

    # zwei Balken: 243 Tage (Rotation) vs. 225 Tage (Umlauf) - rechts Platz fuer die Zahl lassen
    bar_x0, bar_x1 = M, W - M - 190 * S
    max_val = 243
    bar_w_full = bar_x1 - bar_x0

    def hbar(y, val, color, label, sub):
        bw = bar_w_full * (val / max_val)
        d.rounded_rectangle([bar_x0, y, bar_x0 + bw, y + 64 * S], radius=14 * S, fill=color)
        d.text((bar_x0, y - 46 * S), label, font=f(30 * S, bold=True), fill=FG)
        d.text((bar_x0 + bw + 20 * S, y + 12 * S), f"{val} days", font=f(34 * S, bold=True), fill=color)
        d.text((bar_x0, y + 80 * S), sub, font=f(24 * S), fill=SEC)

    y1 = int(H * 0.34)
    hbar(y1, 243, ACC, "One Venus DAY (one full spin)", "Venus spins backwards, and very slowly.")

    y2 = y1 + 210 * S
    hbar(y2, 225, SEC, "One Venus YEAR (one full orbit)", "It circles the Sun faster than it rotates.")

    ctext(d, "Spin longer than orbit - a day outlasts the year.",
          f(34 * S, bold=True), FG, cx, int(H * 0.66))

    ctext(d, "Because Venus also orbits the Sun while it spins, sunrise to sunrise",
          f(26 * S), SEC, cx, int(H * 0.72))
    ctext(d, "(a 'solar day') takes about 117 Earth days - explained in the first comment.",
          f(26 * S), SEC, cx, int(H * 0.72) + 36 * S)

    ctext(d, "Source: NASA Venus Fact Sheet (NSSDCA)",
          fmono(20 * S), SEC, cx, int(H * 0.90))
    return img


if __name__ == "__main__":
    downscale(build(), 1080, 1350).save(OUT / "w3-venus-day-year.png")
    print("saved w3-venus-day-year.png")
