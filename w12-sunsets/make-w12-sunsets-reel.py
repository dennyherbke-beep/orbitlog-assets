"""Woche 12, Mi 18.11.2026 - Raster-Loop "What a SUNSET looks like on other worlds" (Winner-Format Raster, Regel 13:
8-s-Loop). 2x3-Raster, in jedem Feld geht die Sonne gleichzeitig unter und wieder auf; Himmelsfarbe je Welt.

Fakten / Farbquellen:
  NASA Goddard, Planetary Spectrum Generator (G. Villanueva, 2017: simulierte Sonnenuntergaenge auf Erde, Mars,
  Venus, Titan, Uranus): Mars tagsueber butterscotch, um die Sonne blau (Staub streut Blau nach vorn; Curiosity-Foto
  Gale-Krater 2015). Venus: dichte Wolken, Sonnenscheibe vom Boden nicht sichtbar, gelb-oranges Daemmerlicht
  (Venera-Fotos). Titan: orangefarbener Dunst (Huygens 2005), Sonne nur schwach. Uranus (Wolkenobergrenze, kein
  Boden): blauer Himmel, beim Untergang tuerkis. Mond: keine Atmosphaere -> Himmel bleibt schwarz, Sonne bleibt
  weiss bis zum Untergang.
  Scheinbare Sonnengroesse ~ 1/Abstand: Mars 0,66x, Titan/Saturn 0,10x, Uranus 0,05x der Erdansicht.
  Farben sind Naeherungen der Simulationen, im Bild als "simulated colors" gekennzeichnet.

Hook-Varianten:
  1 "What a SUNSET looks like / on other worlds"  (gewaehlt)   2 "Sunsets on Mars are BLUE"
  3 "Your sunset vs. the rest of the Solar System"   4 "The Moon has no sunset colors"   5 "Rate these sunsets 1-6"

    python make-w12-sunsets-reel.py [--preview DIR]  ->  w12-sunsets.mp4, -cover.png
"""

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bodies import fbm
from brandkit import S, FG, SEC, ACC, HAIR, f, downscale
from reelkit import new_frame, header_band, encode, cinematic, stext

OUT = Path(__file__).resolve().parent
NAME = "w12-sunsets"
W, H, LOOP = 1080, 1920, 8.0
GRID_TOP, CW, CH = 540, 500, 330
X0 = (W - 2 * CW) // 2
HOR = 230                                    # Horizont in der Zelle

# Name, Tag (oben, Horizont), Untergang (oben, Horizont), Glow-Farbe, Glow-Radius, Sonnen-d (px), Scheibe sichtbar, Boden
WORLDS = [
    ("Earth", ((58, 112, 205), (160, 200, 238)), ((28, 34, 82), (246, 128, 56)), (255, 168, 84), 120, 26, True, (22, 26, 22)),
    ("Mars", ((150, 112, 82), (210, 166, 124)), ((34, 34, 48), (112, 92, 84)), (120, 170, 245), 55, 17, True, (70, 34, 20)),
    ("Venus*", ((150, 108, 46), (206, 152, 78)), ((50, 30, 14), (112, 62, 26)), (236, 160, 80), 260, 0, False, (54, 34, 18)),
    ("Titan*", ((112, 72, 30), (172, 112, 50)), ((26, 18, 12), (78, 44, 20)), (206, 134, 60), 90, 4, True, (36, 26, 16)),
    ("Moon", ((2, 2, 4), (4, 4, 6)), ((2, 2, 4), (4, 4, 6)), (255, 250, 240), 14, 26, True, (88, 86, 84)),
    ("Uranus*", ((70, 150, 196), (152, 214, 226)), ((18, 46, 80), (56, 172, 176)), (150, 236, 230), 70, 2, False, None),
]
NOTES = ["", "blue sunset", "Sun hidden by clouds", "orange haze", "no air, no colors", "cloud tops"]


def cell_origin(i):
    return X0 + (i % 2) * CW, GRID_TOP + (i // 2) * CH


def terrain_mask(i, ground):
    """Bodensilhouette je Welt (Maske 0..1, Zellgroesse)."""
    if ground is None:                                               # Uranus: Wolkenbank statt Boden
        n = fbm(40 + i, h=CH // 2, w=CW // 2, octaves=4, base=3, wrap=False)
        n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((CW, CH), Image.BICUBIC), np.float32) / 255
        y = np.arange(CH, dtype=np.float32)[:, None]
        return np.clip((y - HOR - 10 + 40 * (n - 0.5)) / 30, 0, 1) * 0.85
    x = np.arange(CW, dtype=np.float32)
    rng = np.random.default_rng(i)
    a, b = rng.uniform(0.008, 0.02, 2)
    prof = HOR + 10 + 14 * np.sin(x * a + i) + 7 * np.sin(x * b * 3 + 2 * i)
    if i == 0:
        prof = HOR + 16 + 0 * x                                         # Erde: Meereshorizont
    y = np.arange(CH, dtype=np.float32)[:, None]
    return np.clip(y - prof[None, :] + 1, 0, 1)


def cell_image(i, ph):
    """Zelle zum Untergangs-Grad ph (0 = Tag, 1 = Sonne 6 Grad unter dem Horizont)."""
    name, day, dusk, glow_c, glow_r, sun_d, disc, ground = WORLDS[i]
    k = min(1.0, ph * 1.25)                                             # Himmelsfarbe
    top = np.array(day[0]) * (1 - k) + np.array(dusk[0]) * k
    hor = np.array(day[1]) * (1 - k) + np.array(dusk[1]) * k
    dark = max(0.0, ph - 0.75) * 2.2                                    # nach Untergang dunkler
    y = np.arange(CH, dtype=np.float32)[:, None, None]
    t = np.clip(y / HOR, 0, 1) ** 1.4
    sky = (top * (1 - t) + hor * t) * (1 - 0.6 * dark)
    sky = np.broadcast_to(sky, (CH, CW, 3)).astype(np.float32).copy()
    sx, sy = CW * 0.58, HOR - 150 + ph * 175                            # Sonne sinkt
    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float32)
    r = np.hypot(xx - sx, (yy - sy) * 1.15)
    g = np.exp(-r / glow_r) * (1.0 - 0.5 * dark) * (0.45 + 0.55 * k)
    if name.startswith("Venus"):
        g = np.exp(-r / glow_r) * 0.55 * (1 - ph * 0.7)
    sky = sky + g[..., None] * np.array(glow_c) * (0.9 if name != "Moon" else 0.5)
    if name == "Moon":                                                   # Sterne bleiben sichtbar
        rng = np.random.default_rng(5)
        for _ in range(60):
            px, py = rng.integers(0, CW), rng.integers(0, HOR)
            sky[py, px] = 150
    if disc and sun_d > 0:
        if sun_d >= 6:
            m = np.clip(sun_d / 2 - r + 0.5, 0, 1)
            sky = sky * (1 - m[..., None]) + np.array([255, 250, 238]) * m[..., None]
        else:
            sky = sky + np.exp(-(r / (sun_d + 0.8)) ** 2)[..., None] * np.array([255, 248, 236])
    im = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8))
    tm = TERRAIN[i]
    gcol = np.array(ground if ground is not None else (36, 120, 140)) * (1 - 0.55 * k)
    if ground is None:
        gcol = np.array((60, 150, 168)) * (1 - 0.6 * k)
    a = np.asarray(im, np.float32) * (1 - tm[..., None]) + gcol * tm[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


TERRAIN = [terrain_mask(i, w[7]) for i, w in enumerate(WORLDS)]


def background():
    img, _ = new_frame(44)
    header_band(img, ["What a SUNSET looks like", "on other worlds"], "SUNSET")
    d = ImageDraw.Draw(img)
    foot = "Simulated colors (NASA Goddard PSG) · *no solid surface / no view of the Sun"
    d.text(((W * S - d.textlength(foot, font=f(22 * S))) / 2, (GRID_TOP + 3 * CH + 16) * S), foot, font=f(22 * S), fill=SEC)
    cta = "Send this to someone who loves sunsets"
    d.text(((W * S - d.textlength(cta, font=f(34 * S, bold=True))) / 2, (GRID_TOP + 3 * CH + 52) * S), cta,
           font=f(34 * S, bold=True), fill=FG)
    sv = "Save it: which one would you watch?"
    d.text(((W * S - d.textlength(sv, font=f(26 * S))) / 2, (GRID_TOP + 3 * CH + 98) * S), sv, font=f(26 * S), fill=SEC)
    return downscale(img, W, H)


BG = background()


def frame(t):
    ph = 0.5 - 0.5 * math.cos(2 * math.pi * (t + 2.0) / LOOP)          # 0 -> 1 -> 0, nahtlos; Start mitten im Untergang
    ph = 0.15 + 0.85 * ph                                               # Start: Sonne schon tief (erstes Bild zaehlt)
    im = BG.copy()
    for i, w in enumerate(WORLDS):
        x0, y0 = cell_origin(i)
        c = cell_image(i, ph)
        d = ImageDraw.Draw(c)
        st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
        d.text((16, 12), w[0], font=f(32, bold=True), fill=ACC if w[0] == "Earth" else FG, **st)
        if NOTES[i]:
            d.text((16, 52), NOTES[i], font=f(22), fill=(230, 232, 238), **st)
        d.rectangle([0, 0, CW - 1, CH - 1], outline=(8, 10, 14), width=4)
        im.paste(c, (x0, y0))
    return im


def main():
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (0.0, 2.0, 4.0):
            cinematic(frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved")
        return
    encode(OUT / f"{NAME}.mp4", frame, LOOP)
    cinematic(frame(0.0), 0, grain_sigma=0).save(OUT / f"{NAME}-cover.png")


if __name__ == "__main__":
    main()
