"""Woche 12, So 22.11.2026 - Remake-Kandidat 5 (blue_saturn_official Olympus Mons, 258K), Typ a Massstab, Regel 13:
10-s-Loop. Wendung: erst Hoehenvergleich (Breiten gestaucht), dann Morph in echte Proportionen -> Olympus Mons wird
ein flacher "Pfannkuchen", 600 km breit.

Fakten (NASA/JPL, USGS; Mars Global Surveyor MOLA): Olympus Mons ~21,9 km ueber dem Mars-Nullniveau (~26 km vom Fuss
bis zum Gipfel), ~600 km Durchmesser, Flaeche ~300.000 km^2 (etwa Polen 312.700 / Arizona 295.000 km^2), mittlere
Hangneigung nur ~5 Grad, Randsteilstufe bis ~8 km. Mount Everest 8,85 km ueber dem Meer. Mauna Kea 4,2 km ueber dem
Meer, ~10,2 km vom Meeresboden. Reiseflughoehe Verkehrsflugzeug ~11 km.

Hook-Varianten:
  1 "Everest is TINY / next to this" (gewaehlt)  2 "The tallest volcano on any planet"  3 "Mars has a mountain 2.5x Everest"
  4 "You could stand on top and not notice"  5 "This mountain is as big as Poland"

    python make-w12-olympus-mons-reel.py [--preview DIR]  ->  w12-olympus-mons.mp4, -cover.png
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bodies import fbm
from brandkit import S, FG, SEC, ACC, f, downscale
from reelkit import new_frame, header_band, encode, cinematic, stext, ease

OUT = Path(__file__).resolve().parent
NAME = "w12-olympus-mons"
W, H, LOOP = 1080, 1920, 10.0
BASE = 1360                                        # Grundlinie (y)
VK = 31.0                                          # px pro km (Hoehe) in der Vergleichsansicht
TK = 1.6                                           # px pro km in echten Proportionen (600 km -> 960 px)
# Name, Hoehe km, echte Breite km, Breite px (Vergleich), x Vergleich, x echt, Farbe, Gipfelfarbe
MOUNTS = [("Everest", 8.85, 30, 230, 190, 120, (112, 112, 120), (236, 240, 248)),
          ("Mauna Kea", 10.2, 110, 300, 420, 230, (70, 52, 44), (96, 76, 64)),
          ("Olympus Mons", 21.9, 600, 560, 770, 600, (176, 86, 52), (206, 120, 78))]
NOISE = fbm(19, h=64, w=512, octaves=5, base=6, wrap=False)
ROCK = np.asarray(Image.fromarray((fbm(23, h=480, w=270, octaves=7, base=10, wrap=False) * 255).astype(np.uint8))
                  .resize((W, H), Image.BICUBIC), np.float32) / 255           # Gesteinstextur


def morph(t):
    """0 = Vergleichsansicht, 1 = echte Proportionen."""
    return ease((t - 4.2) / 2.0) * (1 - ease((t - 9.0) / 0.9))


def profile(i, xs):
    """Relative Hoehe 0..1 ueber x in -1..1 (Everest zackig, Mauna Kea Kuppel, Olympus Schild mit Caldera + Randstufe)."""
    a = np.abs(xs)
    n = NOISE[i * 20, (np.clip((xs + 1) / 2, 0, 1) * 511).astype(int)]
    if i == 0:
        return np.clip(1 - a ** 0.9 + 0.12 * (n - 0.5) * (1 - a), 0, 1)
    if i == 1:
        return np.clip(1 - a ** 1.8 + 0.04 * (n - 0.5), 0, 1)
    shield = 0.72 * (1 - a ** 1.25) + 0.28 * (a < 0.97)                        # Randsteilstufe
    caldera = 0.06 * np.exp(-(xs / 0.09) ** 2)
    return np.clip((shield - caldera + 0.03 * (n - 0.5)) * (a < 1), 0, 1)


def background():
    img, _ = new_frame(83)
    header_band(img, ["Everest is TINY", "next to this"], "TINY")
    return downscale(img, W, H)


BG = background()


def plane(d, x, y, sc=1.0, col=(230, 232, 240)):
    pts = [(-30, 0), (24, -3), (34, 0), (24, 3), (-30, 3)]
    d.polygon([(x + px * sc, y + py * sc) for px, py in pts], fill=col)
    d.polygon([(x - 2 * sc, y), (x + 8 * sc, y), (x - 8 * sc, y + 16 * sc)], fill=col)
    d.polygon([(x - 26 * sc, y), (x - 20 * sc, y), (x - 30 * sc, y - 10 * sc)], fill=col)


def frame(t):
    im = BG.copy()
    d = ImageDraw.Draw(im, "RGBA")
    m = morph(t)
    vk = VK + (TK - VK) * m
    d.rectangle([0, BASE, W, BASE + 6], fill=(150, 156, 170, 255))
    if m < 0.98:                                                            # Meer bei Mauna Kea (4,2 km ueber Meer)
        sea = BASE - 6.0 * vk
        _, _, _, wpx, x1, x2, _, _ = MOUNTS[1]
        cx = x1 + (x2 - x1) * m
        half = wpx / 2 * (1 - m) + 110 * TK / 2 * m
        d.rectangle([cx - half - 50, sea, cx + half + 50, BASE], fill=(40, 90, 150, int(150 * (1 - m))))
    for i, (name, hk, wk, wpx, x1, x2, c, top) in enumerate(MOUNTS):
        cx = x1 + (x2 - x1) * m
        half = wpx / 2 * (1 - m) + wk * TK / 2 * m
        hpx = hk * vk
        xs = np.linspace(-1, 1, 160)
        hs = profile(i, xs)
        pts = [(cx + x * half, BASE - h * hpx) for x, h in zip(xs, hs)]
        poly = [(cx - half, BASE)] + pts + [(cx + half, BASE)]
        x0, x1 = int(max(0, cx - half - 2)), int(min(W, cx + half + 2))
        y0 = int(max(0, BASE - hpx - 4))
        if x1 > x0 + 1 and BASE > y0 + 1:                                   # Textur + Licht von links
            mask = Image.new("L", (W, H), 0)
            ImageDraw.Draw(mask).polygon(poly, fill=255)
            gx = np.arange(x0, x1, dtype=np.float32)[None, :]
            gy = np.arange(y0, BASE, dtype=np.float32)[:, None]
            light = np.clip(1.12 - 0.42 * (gx - cx) / max(half, 1), 0.62, 1.25)
            height = 0.82 + 0.3 * np.clip((BASE - gy) / max(hpx, 1), 0, 1)
            tex = ROCK[y0:BASE, x0:x1]
            rgb = np.array(c, np.float32) * (0.7 + 0.55 * tex)[..., None] * (light * height)[..., None]
            if i == 0:                                                      # Schnee am Everest-Gipfel
                snow = np.clip((BASE - gy - hpx * 0.6) / max(hpx * 0.08, 1), 0, 1) * (0.6 + 0.4 * tex)
                rgb = rgb * (1 - snow[..., None]) + np.array(top, np.float32) * (light[..., None] * 0.9) * snow[..., None]
            if i == 2:                                                      # Staubschleier am Fuss
                rgb = rgb * (0.85 + 0.15 * np.clip((BASE - gy) / max(hpx * 0.3, 1), 0, 1))[..., None]
            patch = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
            im.paste(patch, (x0, y0), mask.crop((x0, y0, x1, BASE)))
            d = ImageDraw.Draw(im, "RGBA")
        lab_a = 1 - ease(m / 0.4)                                            # ab Bild 0 sichtbar
        if lab_a > 0.02:
            ty = BASE - hpx - 74
            stext(im, name, 30, ty, ACC if i == 2 else FG, lab_a, cx=cx)
            stext(im, f"{hk:.1f} km" + (" *" if i == 1 else ""), 26, ty + 36, FG, lab_a, bold=False, cx=cx)
            d = ImageDraw.Draw(im, "RGBA")
    if m < 0.5:                                                             # Flugzeug in 11 km
        a = 1 - m * 2
        py = BASE - 11.0 * vk
        d.line([(0, py), (W, py)], fill=(200, 210, 230, int(70 * a)), width=2)
        px = -60 + (W + 120) * ((t / 4.2) % 1.0)
        plane(d, px, py - 2, 1.0, (230, 232, 240, int(255 * a)))
        stext(im, "airliner, 11 km", 22, py + 10, SEC, a, bold=False, cx=980)
    beats = [("Olympus Mons on Mars: 2.5x Everest", -1.0, 4.2, ACC),
             ("Now in true proportions...", 4.2, 6.6, FG),
             ("600 km wide. As big as Poland.", 6.6, 9.3, ACC),
             ("Olympus Mons on Mars: 2.5x Everest", 9.3, 11.0, ACC)]
    for txt, a0, b0, col in beats:
        al = ease((t - a0) / 0.3) * (1 - ease((t - b0 + 0.3) / 0.3))
        stext(im, txt, 46, 1420, col, al)
    stext(im, "* Mauna Kea from the sea floor · heights to scale, widths squeezed until the flip", 20, 1500, SEC,
          bold=False, stroke=3)
    stext(im, "Send this to someone who has climbed a mountain", 32, 1540, FG)
    stext(im, "Save it: the tallest volcano on any planet", 24, 1584, SEC, bold=False, stroke=3)
    return im


def main():
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (0.0, 3.0, 5.2, 7.5):
            cinematic(frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved")
        return
    encode(OUT / f"{NAME}.mp4", frame, LOOP)
    cinematic(frame(3.0), 0, grain_sigma=0).save(OUT / f"{NAME}-cover.png")


if __name__ == "__main__":
    main()
