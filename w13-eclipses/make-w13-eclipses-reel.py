"""Woche 13, Mi 25.11.2026 - Raster-Loop "What an ECLIPSE looks like on other worlds" (Winner-Variante von w12-sunsets, 8-s-Loop).
2x3-Raster, ein gemeinsamer Winkelmassstab (53 px pro Grad) in allen Feldern; in jedem Feld laeuft ein Mond/Planet vor der Sonne.

Winkelgroessen (Durchmesser, gerechnet aus Durchmesser / Abstand):
  Erde:    Sonne 0,53 Grad, Mond 0,52-0,55 Grad -> totale Finsternis moeglich (Korona).
  Mars:    Sonne 0,35 Grad (1,52 AU), Phobos 22 km bei ~6.000 km Hoehe = ~0,21 Grad -> nur partiell.
  Jupiter: Sonne 0,10 Grad (5,2 AU), Io 3.642 km aus ~350.000 km (Wolkenobergrenze) = ~0,6 Grad -> total, Io 6x so breit.
  Mond:    Erde 12.742 km aus 384.400 km = 1,9 Grad vs. Sonne 0,53 -> Erde verdeckt Sonne, roter Ring (Atmosphaere).
  Pluto:   Sonne 0,0134 Grad (39,5 AU), Charon 1.212 km aus 19.591 km = ~3,5 Grad (~260x) -> total, nur von der Charon-Seite.
  Merkur:  Sonne 1,37 Grad (0,387 AU), kein Mond -> keine Sonnenfinsternis.
Farben/Himmel sind Naeherungen, im Bild als "colors approximated" gekennzeichnet. Eigene Animation, keine Fremdbilder.

Hook-Varianten: 1 "What an ECLIPSE looks like on other worlds" (gewaehlt) 2 "Io covers the Sun 6 times over"
3 "Only Earth gets PERFECT eclipses" (strittig) 4 "Eclipses on Mars are a joke" 5 "Rate these eclipses 1-6"
    python make-w13-eclipses-reel.py [--preview DIR]
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, f, downscale
from reelkit import new_frame, header_band, encode, cinematic

OUT = Path(__file__).resolve().parent
NAME = "w13-eclipses"
W, H, LOOP = 1080, 1920, 8.0
GRID_TOP, CW, CH = 540, 500, 330
X0 = (W - 2 * CW) // 2
SX, SY = CW // 2, 150                      # Sonnenposition in der Zelle

# Name, Notiz, Himmel oben, Himmel Horizont, Boden, Sonne r(px), Occulter r(px), y-Versatz, Stil
WORLDS = [
    ("Earth", "Moon: total", (58, 112, 205), (160, 200, 238), (22, 26, 22), 14.0, 14.8, 0.0, "earth"),
    ("Mars", "Phobos: only partial", (150, 112, 82), (210, 166, 124), (70, 34, 20), 9.3, 5.6, 3.0, "mars"),
    ("Jupiter*", "Io: total, 6x wider than the Sun", (22, 30, 58), (150, 128, 104), None, 2.7, 16.0, 0.0, "jupiter"),
    ("Moon", "Earth: red ring of all sunsets", (2, 2, 4), (4, 4, 6), (88, 86, 84), 14.0, 50.0, 0.0, "moon"),
    ("Pluto", "Charon: ~260x wider than the Sun", (2, 2, 5), (6, 5, 8), (96, 78, 66), 1.0, 93.0, 0.0, "pluto"),
    ("Mercury", "no moon, no eclipse", (2, 2, 4), (4, 4, 6), (92, 88, 84), 36.0, 0.0, 0.0, "mercury"),
]
YY, XX = np.mgrid[0:CH, 0:CW].astype(np.float32)


def cell_origin(i):
    return X0 + (i % 2) * CW, GRID_TOP + (i // 2) * CH


def smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def horizon(i):
    x = np.arange(CW, dtype=np.float32)
    rng = np.random.default_rng(10 + i)
    a, b = rng.uniform(0.01, 0.03, 2)
    base = CH - 52 if i != 0 else CH - 46
    prof = base + 6 * np.sin(x * a + i) + 3 * np.sin(x * b * 3 + 2 * i)
    if i == 0:
        prof = base + 0 * x
    return prof


PROF = [horizon(i) for i in range(6)]
RNG = np.random.default_rng(7)
STARS = [(int(RNG.integers(0, CW)), int(RNG.integers(0, CH - 60)), float(RNG.uniform(70, 170))) for _ in range(70)]


def cell_image(i, t):
    name, note, top, hor, ground, rs, ro, oy, style = WORLDS[i]
    A = ro + rs + (28 if ro > 0 else 0)
    ox = A * math.sin(2 * math.pi * t / LOOP + 0.04) if ro > 0 else 0.0
    rr = np.hypot(XX - SX, YY - SY)
    dd = np.hypot(XX - (SX + ox), YY - (SY + oy))
    dist = math.hypot(ox, oy)
    if ro <= 0 or dist >= ro + rs:
        cov = 0.0
    elif dist <= abs(ro - rs):
        cov = 1.0 if ro >= rs else (ro / rs) ** 2
    else:
        cov = float(np.clip((ro + rs - dist) / (2 * min(ro, rs)), 0, 1))
    tot = float(smooth((cov - 0.85) / 0.15)) if style in ("earth", "jupiter", "moon", "pluto") else 0.0
    dim = 1 - (0.88 * tot if style == "earth" else 0.35 * cov * (style == "mars"))
    y = np.arange(CH, dtype=np.float32)[:, None, None]
    tt = np.clip(y / CH, 0, 1) ** 1.3
    sky = (np.array(top, np.float32) * (1 - tt) + np.array(hor, np.float32) * tt) * dim
    sky = np.broadcast_to(sky, (CH, CW, 3)).astype(np.float32).copy()
    if style in ("moon", "pluto", "mercury"):
        for sx, sy, v in STARS:
            sky[sy, sx] = v
    sun_m = np.clip(rs + 0.5 - rr, 0, 1)
    occ_m = np.clip(ro + 0.5 - dd, 0, 1) if ro > 0 else np.zeros_like(rr)
    sun_lit = sun_m * (1 - occ_m)
    glow_r = max(rs * 1.6, 6.0)
    glow = np.exp(-rr / glow_r) * (1 - 0.92 * tot) * (0.65 if rs >= 8 else 0.9)
    if style in ("jupiter", "pluto"):
        glow = np.exp(-rr / 5.0) * (1 - tot)
        sun_lit = np.maximum(sun_lit, np.exp(-(rr / (rs + 0.7)) ** 2)) * (1 - occ_m)
    col_sun = np.array([255, 246, 228], np.float32)
    sky = sky + glow[..., None] * np.array([255, 214, 150], np.float32) * (0.9 if style != "mars" else 0.8)
    sky = sky * (1 - sun_lit[..., None]) + col_sun * sun_lit[..., None]
    if style == "earth" and tot > 0:
        th = np.arctan2(YY - SY, XX - SX)
        streak = 0.55 + 0.45 * np.cos(5 * th + 0.6) ** 2
        cor = np.exp(-np.clip(rr - rs, 0, None) / (rs * 1.1)) * streak * (rr > rs - 1) * tot
        sky = sky + cor[..., None] * np.array([235, 240, 255], np.float32) * 0.85
    elif style == "mercury":
        th = np.arctan2(YY - SY, XX - SX)
        cor = np.exp(-np.clip(rr - rs, 0, None) / (rs * 0.9)) * (0.6 + 0.4 * np.cos(4 * th + t) ** 2) * 0.45
        sky = sky + cor[..., None] * np.array([255, 224, 170], np.float32)
    if ro > 0:
        if style == "moon":
            ring = np.exp(-np.clip(dd - ro, 0, None) / 3.2) * (dd > ro - 0.5) * (0.35 + 0.65 * smooth(cov))
            sky = sky + ring[..., None] * np.array([255, 96, 40], np.float32) * 1.05
            glow2 = np.exp(-np.clip(dd - ro, 0, None) / 18) * (dd > ro) * 0.25 * smooth(cov)
            sky = sky + glow2[..., None] * np.array([255, 120, 70], np.float32)
        dark = np.array([8, 8, 12], np.float32)
        if style in ("pluto", "jupiter"):                             # schwacher Randschimmer (Streulicht/Atmosphaere)
            rim = np.exp(-np.clip(dd - ro, 0, None) / 2.6) * (dd > ro - 0.5) * 0.55
            rim = rim * (np.array([150, 120, 100], np.float32) if style == "pluto" else np.array([200, 150, 110], np.float32))[None, None, :] if False else rim
            sky = sky + rim[..., None] * (np.array([150, 120, 100], np.float32) if style == "pluto" else np.array([200, 150, 110], np.float32))
            if style == "pluto":
                dark = np.array([16, 13, 15], np.float32)
        if style == "mars":                                           # Phobos: Kartoffelform
            th2 = np.arctan2(YY - (SY + oy), XX - (SX + ox))
            shape = 1 + 0.12 * np.sin(3 * th2 + 1) + 0.07 * np.sin(5 * th2)
            occ_m = np.clip(ro * shape * 1.15 + 0.5 - dd, 0, 1)
            dark = np.array([34, 30, 28], np.float32)
        sky = sky * (1 - occ_m[..., None]) + dark * occ_m[..., None]
    if ground is not None:
        pr = PROF[i]
        gm = np.clip(YY - pr[None, :] + 1, 0, 1)
        gcol = np.array(ground, np.float32) * (1 - 0.6 * tot * (style == "earth"))
        gshade = gcol * (1 - 0.45 * np.clip((YY - pr[None, :]) / 60, 0, 1))[..., None]
        sky = sky * (1 - gm[..., None]) + gshade * gm[..., None]
    else:                                                               # Jupiter: Wolkenbank
        n = np.sin(XX * 0.03 + 2) * 6 + np.sin(XX * 0.011) * 10
        gm = np.clip(YY - (CH - 70 + n) + 1, 0, 1) * 0.92
        sky = sky * (1 - gm[..., None]) + np.array([176, 140, 104], np.float32) * gm[..., None]
    return Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8))


def background():
    img, _ = new_frame(73)
    header_band(img, ["What an ECLIPSE looks like", "on other worlds"], "ECLIPSE")
    d = ImageDraw.Draw(img)
    foot = "Same scale in every panel · colors approximated · *cloud tops"
    d.text(((W * S - d.textlength(foot, font=f(22 * S))) / 2, (GRID_TOP + 3 * CH + 16) * S), foot, font=f(22 * S), fill=SEC)
    cta = "Send this to an eclipse chaser"
    d.text(((W * S - d.textlength(cta, font=f(36 * S, bold=True))) / 2, (GRID_TOP + 3 * CH + 52) * S), cta, font=f(36 * S, bold=True), fill=FG)
    sv = "Save it: Io hides the Sun 6 times over"
    d.text(((W * S - d.textlength(sv, font=f(26 * S))) / 2, (GRID_TOP + 3 * CH + 98) * S), sv, font=f(26 * S), fill=SEC)
    return downscale(img, W, H)


BG = background()


def frame(t):
    im = BG.copy()
    st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
    for i, w in enumerate(WORLDS):
        x0, y0 = cell_origin(i)
        c = cell_image(i, t)
        d = ImageDraw.Draw(c)
        d.text((16, 12), w[0], font=f(32, bold=True), fill=ACC if w[0] == "Earth" else FG, **st)
        d.text((16, 52), w[1], font=f(22), fill=(230, 232, 238), **st)
        d.rectangle([0, 0, CW - 1, CH - 1], outline=(8, 10, 14), width=4)
        im.paste(c, (x0, y0))
    return im


def main():
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (0.0, 1.0, 3.0):
            cinematic(frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved")
        return
    encode(OUT / f"{NAME}.mp4", frame, LOOP)
    cinematic(frame(0.0), 0, grain_sigma=0).save(OUT / f"{NAME}-cover.png")


if __name__ == "__main__":
    main()
