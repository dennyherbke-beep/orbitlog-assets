"""Woche 14, So 29.11.2026 - Raster-Loop "What MOONS look like from other worlds" (Winner-Variante von w13-eclipses, 8-s-Loop).
2x3-Raster, ein gemeinsamer Winkelmassstab (75 px pro Grad). Winkeldurchmesser = Monddurchmesser / Abstand zur Oberflaeche
(bei Gasriesen: zur Wolkenobergrenze):
  Erde:    Mond 3.474 km / 384.400 km                      = 0,52 Grad
  Mars:    Phobos 22,2 km / (9.376-3.390 km)               = 0,21 Grad (geht im WESTEN auf, ~2x pro Marstag); Deimos 12,4 km / 20.073 km = 0,035 Grad
  Jupiter: Io 3.643 / 351.800 = 0,59; Europa 3.122 / 601.000 = 0,30; Ganymed 5.268 / 1.000.000 = 0,30; Kallisto 4.821 / 1.813.000 = 0,15 Grad
  Saturn:  Titan 5.150 / 1.161.600 = 0,25; Tethys 1.066 / 235.000 = 0,26; Rhea 1.527 / 467.000 = 0,19 Grad
  Neptun:  Triton 2.707 / 330.000 = 0,47 Grad (umkreist rueckwaerts)
  Pluto:   Charon 1.212 / 19.591 = 3,5 Grad (~7x unser Mond), gebundene Rotation: steht fest am Himmel (nur von einer Seite sichtbar)
Eigene Animation, Mondtexturen NASA (Mond-Karte) eingefaerbt als Stellvertreter, Charon-Karte NASA. Im Bild: "colors approximated".
Hook-Varianten: 1 "What MOONS look like from other worlds" (gewaehlt) 2 "Pluto's moon is 7x bigger than OURS" 3 "Only Earth has ONE moon"
4 "Rate these night skies 1-6" 5 "Which world has the best moons?"
    python make-w14-moons-sky-reel.py [--preview DIR]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, f, downscale
from reelkit import new_frame, header_band, encode, cinematic, body_sprite

OUT = Path(__file__).resolve().parent
NAME = "w14-moons-sky"
W, H, LOOP = 1080, 1920, 8.0
GRID_TOP, CW, CH = 540, 500, 330
X0 = (W - 2 * CW) // 2
K = 75.0                                    # px pro Grad
HOR = CH - 52
LIGHT = (-0.25, -0.2, 0.95)

# (Anzeigename, Notiz, Himmel oben, Himmel unten, Boden)
WORLDS = [
    ("Earth", "1 Moon", (14, 22, 50), (48, 62, 100), (20, 24, 20)),
    ("Mars", "Phobos rises in the WEST", (30, 20, 22), (92, 58, 44), (70, 34, 20)),
    ("Jupiter*", "Io: 1.1x our Moon", (6, 8, 20), (60, 48, 40), None),
    ("Saturn*", "Titan: half our Moon", (6, 8, 18), (52, 46, 38), None),
    ("Neptune*", "Triton: orbits backwards", (4, 8, 26), (22, 44, 90), None),
    ("Pluto", "Charon: 7x our Moon, never moves", (2, 2, 5), (14, 10, 14), (96, 78, 66)),
]
# Monde: (Welt, Name, Winkel-Grad, Textur-Tint, Kreuzungen pro Loop (negativ = rueckwaerts), Phase, Bogenhoehe, kind)
MOONS = [
    (0, "Moon", 0.52, (1.0, 1.0, 1.0), 1, 0.30, 150, "moon"),
    (1, "Phobos", 0.21, (0.62, 0.56, 0.5), -2, 0.15, 120, "moon"),
    (1, "Deimos", 0.035, (0.8, 0.75, 0.7), 1, 0.55, 90, "moon"),
    (2, "Io", 0.59, (1.15, 0.95, 0.42), 1, 0.15, 150, "moon"),
    (2, "Europa", 0.30, (1.0, 0.94, 0.85), 1, 0.45, 100, "moon"),
    (2, "Ganymede", 0.30, (0.82, 0.78, 0.72), 1, 0.72, 130, "moon"),
    (2, "Callisto", 0.152, (0.55, 0.5, 0.46), 1, 0.92, 80, "moon"),
    (3, "Titan", 0.254, (1.25, 0.78, 0.32), 1, 0.20, 140, "moon"),
    (3, "Tethys", 0.26, (1.0, 1.0, 1.02), 1, 0.52, 100, "moon"),
    (3, "Rhea", 0.187, (0.85, 0.83, 0.8), 1, 0.80, 125, "moon"),
    (4, "Triton", 0.47, (1.1, 0.88, 0.84), -1, 0.40, 140, "moon"),
    (5, "Charon", 3.5, (1.0, 1.0, 1.0), 0, 0.50, 0, "charon"),
]
SPR = {}
for m in MOONS:
    d = m[2] * K
    if d >= 6:
        SPR[m[1]] = body_sprite(m[7], d, light=LIGHT, tint=m[3], lon0=180.0)

YY, XX = np.mgrid[0:CH, 0:CW].astype(np.float32)


def cell_origin(i):
    return X0 + (i % 2) * CW, GRID_TOP + (i // 2) * CH


def build_cell(i):
    name, note, top, bot, ground = WORLDS[i]
    t = np.clip(np.arange(CH, dtype=np.float32) / HOR, 0, 1)[:, None, None] ** 1.2
    sky = np.array(top, np.float32) * (1 - t) + np.array(bot, np.float32) * t
    sky = np.broadcast_to(sky, (CH, CW, 3)).astype(np.float32).copy()
    rng = np.random.default_rng(40 + i)
    for _ in range(95):
        sx, sy = int(rng.integers(0, CW)), int(rng.integers(0, HOR - 6))
        sky[sy, sx] = np.clip(sky[sy, sx] + rng.uniform(50, 150), 0, 255)
    base = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8)).convert("RGBA")
    x = np.arange(CW, dtype=np.float32)
    r2 = np.random.default_rng(10 + i)
    a, b = r2.uniform(0.01, 0.03, 2)
    prof = HOR + 6 * np.sin(x * a + i) + 3 * np.sin(x * b * 3 + 2 * i)
    if i == 0:
        prof = HOR + 0 * x
    gm = np.clip(YY - prof[None, :] + 1, 0, 1)
    if ground is None:                                           # Wolkenbank (Gasriesen)
        n = np.sin(XX * 0.03 + i) * 6 + np.sin(XX * 0.011 + i) * 10
        gm = np.clip(YY - (HOR + n) + 1, 0, 1) * 0.94
        gcol = np.array({2: (176, 140, 104), 3: (190, 168, 120), 4: (60, 96, 170)}[i], np.float32)
    else:
        gcol = np.array(ground, np.float32)
    shade = gcol[None, None, :] * (1 - 0.5 * np.clip((YY - HOR) / 60, 0, 1))[..., None]
    shade = np.broadcast_to(shade, (CH, CW, 3))
    g = np.dstack([shade, gm * 255]).astype(np.uint8)
    return base, Image.fromarray(g, "RGBA")


CELLS = [build_cell(i) for i in range(6)]


def background():
    img, _ = new_frame(74)
    header_band(img, ["What MOONS look like", "from other worlds"], "MOONS")
    d = ImageDraw.Draw(img)
    foot = "Same scale in every panel · *cloud tops · colors approximated"
    d.text(((W * S - d.textlength(foot, font=f(22 * S))) / 2, (GRID_TOP + 3 * CH + 16) * S), foot, font=f(22 * S), fill=SEC)
    cta = "Send this to someone who loves the Moon"
    d.text(((W * S - d.textlength(cta, font=f(36 * S, bold=True))) / 2, (GRID_TOP + 3 * CH + 52) * S), cta, font=f(36 * S, bold=True), fill=FG)
    sv = "Save it: Pluto's Charon never moves"
    d.text(((W * S - d.textlength(sv, font=f(26 * S))) / 2, (GRID_TOP + 3 * CH + 98) * S), sv, font=f(26 * S), fill=SEC)
    return downscale(img, W, H)


BG = background()


def cell_frame(i, t):
    base, ground = CELLS[i]
    c = base.copy()
    for (wi, nm, deg, tint, k, ph, amp, kind) in MOONS:
        if wi != i:
            continue
        d = deg * K
        if k == 0:                                               # Charon: fest am Himmel
            cx, cy = 340, 195
        else:
            fr = (ph + k * t / LOOP) % 1.0
            margin = d / 2 + 6
            cx = -margin + fr * (CW + 2 * margin)
            cy = HOR + 10 - amp * np.sin(np.pi * fr)
        if nm in SPR:
            rgb, m = SPR[nm]
            c.paste(rgb, (int(cx - rgb.width / 2), int(cy - rgb.height / 2)), m)
        else:                                                    # Deimos: Punkt
            ImageDraw.Draw(c).ellipse([cx - 1.5, cy - 1.5, cx + 1.5, cy + 1.5], fill=(200, 196, 190))
    c = Image.alpha_composite(c, ground).convert("RGB")
    dr = ImageDraw.Draw(c)
    st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
    dr.text((16, 12), WORLDS[i][0], font=f(32, bold=True), fill=ACC if i == 0 else FG, **st)
    dr.text((16, 52), WORLDS[i][1], font=f(22), fill=(230, 232, 238), **st)
    dr.rectangle([0, 0, CW - 1, CH - 1], outline=(8, 10, 14), width=4)
    return c


def frame(t):
    im = BG.copy()
    for i in range(6):
        im.paste(cell_frame(i, t), cell_origin(i))
    return im


def main():
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (0.0, 2.0, 4.5):
            cinematic(frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved")
        return
    encode(OUT / f"{NAME}.mp4", frame, LOOP)
    cinematic(frame(0.0), 0, grain_sigma=0).save(OUT / f"{NAME}-cover.png")


if __name__ == "__main__":
    main()
