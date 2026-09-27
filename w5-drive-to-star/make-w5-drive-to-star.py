"""Woche 5, Mittwoch - Numbers & scale: "Driving to the nearest star at 100 km/h: 46 million years".
Layout B (Zahlengrafik), 1080 x 1350, 1 Bild - gleiches Muster wie w4-neutron-star.
Ab Woche 5 mit Speicheranreiz (Lesezeichen + Zeile) unten im Bild.

Rechnung: Proxima Centauri 4.2465 Lj (NASA) x 9.4607e12 km = 4.0175e13 km;
/ 100 km/h = 4.0175e11 h; / 8,766 h pro Jahr = 45.8 Mio. Jahre -> "46 million years".
Licht braucht 4.2 Jahre. Zum Vergleich (first_comment): Voyager 1 (~61,000 km/h) ~75,000 Jahre.
  4.0175e13 / 61,000 / 8,766 = 75,100 Jahre.

    python make-w5-drive-to-star.py   ->  w5-drive-to-star.png
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono, tracked, canvas, glow, furniture, downscale
from reelkit import bookmark, blob, sphere, grain, TEX

OUT = Path(__file__).resolve().parent
W, H = 1080 * S, 1350 * S
M = 96 * S


def ctext(d, s, font, fill, cx, y, track=0):
    total = sum(d.textlength(ch, font=font) + track for ch in s) - (track if s else 0)
    if track:
        tracked(d, (cx - total / 2, y), s, font, fill, track)
    else:
        d.text((cx - total / 2, y), s, font=font, fill=fill)


def tex_red_dwarf():
    t = Image.new("RGB", (TEX, TEX), (236, 108, 70))
    blob(t, 200, 190, 90, 70, (255, 150, 96), blur=40, alpha=160)
    blob(t, 330, 320, 60, 44, (190, 70, 46), blur=26, alpha=140)
    return grain(t, 16, 3)


def road(img, y):
    """Gestrichelte Strasse von links (Auto-Punkt) zum roten Zwergstern rechts."""
    d = ImageDraw.Draw(img)
    x0, x1 = M + 40 * S, W - M - 110 * S
    d.line([x0, y, x1, y], fill=HAIR, width=10 * S)
    x = x0 + 20 * S
    while x < x1 - 30 * S:
        d.line([x, y, x + 26 * S, y], fill=ACC, width=4 * S)
        x += 52 * S
    d.rounded_rectangle([x0 - 26 * S, y - 20 * S, x0 + 26 * S, y + 6 * S], radius=8 * S, fill=FG)
    for wx in (x0 - 14 * S, x0 + 14 * S):
        d.ellipse([wx - 7 * S, y + 2 * S, wx + 7 * S, y + 16 * S], fill=(60, 66, 80))
    sx = W - M - 60 * S
    sphere(img, sx, y, 64, tex_red_dwarf(), (255, 110, 70), light=(0.0, 0.0, 1.0))  # Stern: selbstleuchtend, nur Randverdunkelung
    d = ImageDraw.Draw(img)
    d.text((x0 - 40 * S, y + 36 * S), "you, 100 km/h", font=fmono(22 * S), fill=SEC)
    tw = d.textlength("Proxima Centauri", font=fmono(22 * S))
    d.text((sx - tw + 40 * S, y + 50 * S), "Proxima Centauri", font=fmono(22 * S), fill=SEC)


def build():
    img, _ = canvas(W, H)
    img = glow(img, [W * 0.10, H * 0.12, W * 0.90, H * 0.50], strength=0.16, blur_frac=0.14)
    d = ImageDraw.Draw(img)
    cx = W // 2

    furniture(d, W, M, "NUMBERS & SCALE")
    ctext(d, "DRIVING TO THE NEAREST STAR AT 100 KM/H", fmono(23 * S), SEC, cx, int(H * 0.19), track=3 * S)
    ctext(d, "46 million", f(176 * S, bold=True), ACC, cx, int(H * 0.25))
    ctext(d, "years", f(84 * S, bold=True), FG, cx, int(H * 0.25) + 226 * S)

    road(img, int(H * 0.62))
    d = ImageDraw.Draw(img)
    ctext(d, "Nonstop, no breaks. Light makes the same trip in 4.2 years.", f(30 * S), SEC, cx, int(H * 0.72))

    y = int(H * 0.80)
    bookmark(d, M + 30 * S, y + 22 * S, 50 * S)
    d.text((M + 80 * S, y), "Save this for the next time a road trip feels long.", font=f(30 * S, bold=True), fill=FG)

    ctext(d, "Distance: Proxima Centauri, 4.25 light-years (NASA)", fmono(20 * S), SEC, cx, int(H * 0.91))
    return img


if __name__ == "__main__":
    downscale(build(), 1080, 1350).save(OUT / "w5-drive-to-star.png")
    print("saved w5-drive-to-star.png")
