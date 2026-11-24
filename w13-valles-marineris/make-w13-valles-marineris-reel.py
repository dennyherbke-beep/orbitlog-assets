"""Woche 13, Do 26.11.2026 - Winner-Variante von w12-olympus-mons (Typ a, Massstab, Regel 13: 10-s-Loop).
Erst Tiefe (Querschnitt, Breiten gestaucht), dann Laenge von oben (gleicher Massstab, Linie neben US-Breite).

Fakten: Valles Marineris (NASA/USGS): ~4.000 km lang, bis ~200 km breit, bis ~7 km tief. Grand Canyon (US National Park
Service): 446 km (277 mi) lang, bis 29 km breit, rund 1,8 km (6.000 ft) tief. Luftlinie Kueste-zu-Kueste USA ~4.500 km.
Verhaeltnisse: 7/1,8 = ~4x tiefer, 4.000/446 = ~9x laenger.

Hook-Varianten: 1 "The Grand Canyon is a SCRATCH next to this" (gewaehlt) 2 "Mars has a canyon as wide as the USA"
3 "4x deeper, 9x longer" 4 "The Grand Canyon fits in here 9 times" 5 "Where would you hike on Mars?"
    python make-w13-valles-marineris-reel.py [--preview DIR]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bodies import fbm
from brandkit import ACC, FG, SEC
from reelkit import header_bg, encode, cinematic, stext, ease

OUT = Path(__file__).resolve().parent
NAME = "w13-valles-marineris"
W, H, LOOP = 1080, 1920, 10.0
SURF, VK = 760, 38.0                         # Oberflaeche y, px pro km Tiefe
BOT = 1100
ROCK = np.asarray(Image.fromarray((fbm(31, h=480, w=270, octaves=7, base=10, wrap=False) * 255).astype(np.uint8))
                  .resize((W, H), Image.BICUBIC), np.float32) / 255
NOISE = fbm(5, h=8, w=512, octaves=5, base=8, wrap=False)
BG = header_bg(91, ["The Grand Canyon is a", "SCRATCH next to this"], "SCRATCH")


def block(im, x0, x1, depth_km, base_col, name, steps):
    """Gesteinsblock mit Einschnitt (Terrassen) von der Oberflaeche nach unten."""
    xs = np.arange(x0, x1)
    u = (xs - (x0 + x1) / 2) / ((x1 - x0) * 0.34)                 # -1..1 = Canyonbreite
    n = NOISE[(hash(name) % 6), ((xs - x0) / (x1 - x0) * 511).astype(int)]
    prof = np.clip(1 - np.abs(u) ** 1.5 + 0.08 * (n - 0.5), 0, 1)
    prof = np.round(prof * steps) / steps * 0.6 + prof * 0.4        # Terrassenstufen
    cut = SURF + prof * depth_km * VK
    gy = np.arange(SURF, BOT, dtype=np.float32)[:, None]
    tex = ROCK[SURF:BOT, x0:x1]
    band = 0.85 + 0.15 * np.sin(gy * 0.35 + tex * 4)                # Schichtung
    shade = np.clip(1.15 - 0.55 * (gy - SURF) / (BOT - SURF), 0.5, 1.15)
    rgb = np.array(base_col, np.float32) * (0.65 + 0.6 * tex)[..., None] * (band * shade)[..., None]
    inside = (gy < cut[None, :])                                    # Luft ueber dem Einschnitt
    patch = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    mask = Image.fromarray(((~inside) * 255).astype(np.uint8)[:, :, 0] if inside.ndim == 3 else ((~inside) * 255).astype(np.uint8))
    im.paste(patch, (x0, SURF), mask)
    return cut


def scene_a(im, t):
    block(im, 40, 500, 1.83, (196, 132, 88), "gc", 7)
    block(im, 580, 1040, 7.0, (172, 84, 52), "vm", 11)
    d = ImageDraw.Draw(im)
    d.line([(0, SURF), (W, SURF)], fill=(210, 214, 226), width=2)
    for x in range(0, W, 30):
        d.line([(x, SURF), (x + 14, SURF)], fill=(8, 10, 14), width=2)
    # Tiefenmarken
    for xx, dk, lab, col in [(270, 1.83, "1.8 km deep", FG), (810, 7.0, "7 km deep", ACC)]:
        y1 = SURF + dk * VK
        d.line([(xx, SURF), (xx, y1)], fill=col, width=3)
        for yy in (SURF, y1):
            d.line([(xx - 12, yy), (xx + 12, yy)], fill=col, width=3)
        stext(im, lab, 34, y1 + 14, col, cx=xx)
    stext(im, "Grand Canyon", 36, SURF - 120, FG, cx=270)
    stext(im, "Valles Marineris", 36, SURF - 120, ACC, cx=810)
    stext(im, "Earth", 26, SURF - 76, SEC, cx=270, bold=False)
    stext(im, "Mars", 26, SURF - 76, SEC, cx=810, bold=False)


def scene_b(im, t):
    k = 0.2                                                         # px pro km
    p = ease((t - 4.9) / 2.2)
    d = ImageDraw.Draw(im)
    rows = [("USA, coast to coast: ~4,500 km", 4500, 800, (196, 200, 214), 10, 0.0),
            ("Grand Canyon: 446 km", 446, 920, (214, 150, 100), 6, 0.0),
            ("Valles Marineris: 4,000 km", 4000, 1040, (190, 84, 50), 40, 1.0)]
    rng = np.random.default_rng(4)
    for lab, km, y, col, th, branch in rows:
        L = km * k * p
        x0 = 90
        stext(im, lab, 32, y - 62, ACC if branch else FG, cx=max(x0 + km * k / 2, 260) if km * k < 700 else W / 2)
        d.rounded_rectangle([x0, y, x0 + max(L, 2), y + th], radius=th // 2, fill=col)
        if branch and L > 20:
            for i in range(26):
                bx = x0 + (i + 0.5) / 26 * 800
                if bx > x0 + L:
                    break
                s = rng.uniform(-1, 1)
                d.line([(bx, y + th / 2), (bx + 14 * s, y + th / 2 + np.sign(s) * rng.uniform(14, 34))], fill=col, width=4)
    stext(im, "same map scale, seen from above", 24, 1130, SEC, bold=False, stroke=3)


def frame(t):
    im = BG.copy()
    a = 1 - ease((t - 4.2) / 0.7)                                   # A blendet aus
    bb = ease((t - 4.4) / 0.7) * (1 - ease((t - 9.4) / 0.5))       # B ein, am Ende wieder aus (Loop)
    aa = a if t < 9.4 else ease((t - 9.4) / 0.5)
    if aa > 0.01:
        la = im.copy(); scene_a(la, t); im = Image.blend(im, la, aa) if aa < 0.999 else la
    if bb > 0.01:
        lb = im.copy(); scene_b(lb, t); im = Image.blend(im, lb, bb) if bb < 0.999 else lb
    beats = [("Valles Marineris on Mars: 4x deeper", -1, 4.4, ACC), ("...and 9x LONGER", 4.4, 9.4, ACC),
             ("Valles Marineris on Mars: 4x deeper", 9.4, 11, ACC)]
    for txt, a0, b0, col in beats:
        al = ease((t - a0) / 0.3) * (1 - ease((t - b0 + 0.3) / 0.3))
        stext(im, txt, 46, 1330 if False else 1440, col, al)
    stext(im, "Illustration · depths exaggerated vs. widths · NASA/USGS, NPS", 20, 1520, SEC, bold=False, stroke=3)
    stext(im, "Send this to someone who has hiked the Grand Canyon", 30, 1560, FG)
    stext(im, "Save it: Mars has a canyon almost as long as the USA is wide", 24, 1606, SEC, bold=False, stroke=3)
    return im


def main():
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1]); prev.mkdir(parents=True, exist_ok=True)
        for t in (0.0, 3.0, 8.0):
            cinematic(frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved"); return
    encode(OUT / f"{NAME}.mp4", frame, LOOP)
    cinematic(frame(3.0), 0, grain_sigma=0).save(OUT / f"{NAME}-cover.png")


if __name__ == "__main__":
    main()
