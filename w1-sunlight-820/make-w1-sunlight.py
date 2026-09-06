"""Woche 1, Freitag - Numbers & scale: "Sunlight takes 8:20 to reach Earth".
Layout B (Zahlengrafik), 1080 x 1350, 1 Bild.

    python make-w1-sunlight.py   ->  w1-sunlight-820.png
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

    furniture(d, W, M, "SUN TO EARTH")
    ctext(d, "LIGHT TRAVEL TIME", fmono(30 * S), SEC, cx, int(H * 0.27), track=6 * S)

    big = f(290 * S, bold=True)
    bb = d.textbbox((0, 0), "8:20", font=big)
    ctext(d, "8:20", big, ACC, cx, int(H * 0.33) - bb[1])

    ctext(d, "minutes for sunlight to reach Earth", f(40 * S), FG, cx, int(H * 0.575))
    d.line([cx - 100 * S, int(H * 0.66), cx + 100 * S, int(H * 0.66)], fill=HAIR, width=2 * S)
    ctext(d, "You always see the Sun as it was about 8 minutes ago.",
          f(30 * S), SEC, cx, int(H * 0.69))

    ctext(d, "Source: 149.6M km / speed of light = 499 s",
          fmono(22 * S), SEC, cx, int(H * 0.90))
    return img


if __name__ == "__main__":
    downscale(build(), 1080, 1350).save(OUT / "w1-sunlight-820.png")
    print("saved w1-sunlight-820.png")
