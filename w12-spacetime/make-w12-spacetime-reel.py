"""Woche 12, Sa 21.11.2026 - Remake-Kandidat 3 (nebulory "The Solar System through Einstein's eyes", 162K): Raumzeit
als Gitter-Tuch, Sonne + innere Planeten in Mulden. Eigene Grafik, als vereinfachtes Modell gekennzeichnet (Typ f).
Regel 13: 10-s-Loop (Merkur 3, Venus 2, Erde 1 Umlauf pro Loop - beschleunigt, Verhaeltnis gerundet).

Fakten: Allgemeine Relativitaetstheorie (Einstein 1915) - Masse kruemmt die Raumzeit, Koerper folgen der Kruemmung
(Geodaeten). Die "Gummituch"-Analogie ist eine Vereinfachung (2D statt 4D, braucht selbst Schwerkraft nach unten) ->
im Bild "simplified model". Merkurs Periheldrehung (43"/Jh.) war 1915 der erste Test, den nur Einstein erklaerte.

Hook-Varianten:
  1 "The Solar System / through EINSTEIN's eyes" (gewaehlt, Vorbild-Hook)  2 "Gravity isn't a pull"
  3 "This is what gravity really looks like"  4 "Why Earth never falls into the Sun"  5 "Newton was (a little) wrong"

    python make-w12-spacetime-reel.py [--preview DIR]  ->  w12-spacetime.mp4, -cover.png
"""

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, f, downscale
from reelkit import new_frame, header_band, encode, cinematic, body_sprite, stext, ease

OUT = Path(__file__).resolve().parent
NAME = "w12-spacetime"
W, H, LOOP = 1080, 1920, 10.0
CX, CY, FOC, DIST, ELEV = 540, 900, 1500, 24.0, math.radians(40)
# Name, Bahnradius, Umlaeufe pro Loop, Muldentiefe, Sprite-Durchmesser, Startwinkel
BODIES = [("Mercury", 3.0, 3, 0.7, 36, 0.6), ("Venus", 4.6, 2, 1.1, 56, 2.4), ("Earth", 6.4, 1, 1.2, 62, 4.2)]
SUN_A, SUN_W = 11.0, 2.0


def zfield(x, y, pos):
    z = -SUN_A / np.sqrt(x * x + y * y + SUN_W ** 2)
    for (px, py), (_, _, _, a, _, _) in zip(pos, BODIES):
        z = z - a / np.sqrt((x - px) ** 2 + (y - py) ** 2 + 0.35 ** 2)
    return z + SUN_A / 9.0


def proj(x, y, z):
    d = y * math.cos(ELEV) - z * math.sin(ELEV) + DIST
    u = y * math.sin(ELEV) + z * math.cos(ELEV)
    return CX + FOC * x / d, CY - FOC * u / d, d


def positions(t):
    out = []
    for _, r, n, _, _, a0 in BODIES:
        a = a0 + 2 * math.pi * n * t / LOOP
        out.append((r * math.cos(a), r * math.sin(a)))
    return out


def background():
    img, _ = new_frame(73)
    header_band(img, ["The Solar System", "through EINSTEIN's eyes"], "EINSTEIN's")
    return downscale(img, W, H)


BG = background()
SUN = body_sprite("sun", 170, spots=False)
SPR = {n: body_sprite(n.lower(), dpx, light=(-0.8, -0.2, 0.55)) for n, _, _, _, dpx, _ in BODIES}
G = np.linspace(-11, 11, 45)
FINE = np.linspace(-11, 11, 160)


def grid_layer(pos):
    """Gitter auf doppelter Aufloesung zeichnen, dann verkleinern (Kantenglaettung)."""
    k = 2
    lay = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    for axis in (0, 1):
        for g in G:
            xs, ys = (np.full_like(FINE, g), FINE) if axis == 0 else (FINE, np.full_like(FINE, g))
            zs = np.maximum(zfield(xs, ys, pos), -4.6)
            pts = [proj(x, y, z) for x, y, z in zip(xs, ys, zs)]
            for (x0, y0, d0), (x1, y1, d1), z in zip(pts, pts[1:], zs):
                rr = math.hypot(xs[0] if axis == 0 else 0, 0)
                fade = max(0.0, min(1.0, (32 - d0) / 14))                  # hinten dunkler
                glow = min(1.0, max(0.0, -z / 3.5))                                    # tiefer = heller (Sonnenlicht)
                c = (int(70 + 120 * glow), int(120 + 110 * glow), int(200 + 55 * glow), int(255 * (0.35 + 0.55 * fade)))
                d.line([x0 * k, y0 * k, x1 * k, y1 * k], fill=c, width=2 * k if glow > 0.5 else k + 1)
    return lay.resize((W, H), Image.LANCZOS)


def frame(t):
    im = BG.copy().convert("RGBA")
    pos = positions(t)
    im.alpha_composite(grid_layer(pos))
    im = im.convert("RGB")
    sx, sy, _ = proj(0, 0, -4.6 + 0.9)
    items = [(proj(0, 0, 0)[2], "Sun", sx, sy)]
    for (px, py), (name, _, _, _, dpx, _) in zip(pos, BODIES):
        z = float(zfield(np.array(px), np.array(py), pos)) + dpx / 120
        x, y, dd = proj(px, py, z)
        items.append((dd, name, x, y))
    for dd, name, x, y in sorted(items, key=lambda r: -r[0]):              # hinten zuerst
        rgb, m = SUN if name == "Sun" else SPR[name]
        sc = DIST / dd
        if abs(sc - 1) > 0.03:
            rgb, m = rgb.resize((int(rgb.width * sc), int(rgb.height * sc))), m.resize((int(m.width * sc), int(m.height * sc)))
        im.paste(rgb, (int(x - rgb.width / 2), int(y - rgb.height / 2)), m)
        if name == "Earth":
            stext(im, "Earth", 26, y - 62 * sc, ACC, 1.0, cx=x)
    beats = [("Mass bends space", -1.0, 3.4), ("Planets follow the curve", 3.4, 6.8), ("That's gravity.", 6.8, 10.4)]
    for txt, a, b in beats:
        al = ease((t - a) / 0.35) * (1 - ease((t - b + 0.35) / 0.35))
        stext(im, txt, 50, 1440, ACC if txt.startswith("That") else FG, al)
    stext(im, "Simplified model · sped up, not to scale", 22, 1530, SEC, bold=False, stroke=3)
    stext(im, "Send this to someone who thinks gravity is a pull", 32, 1566, FG)
    stext(im, "Save it: the simplest picture of gravity", 24, 1610, SEC, bold=False, stroke=3)
    return im


def main():
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (0.0, 4.0, 8.0):
            cinematic(frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved")
        return
    encode(OUT / f"{NAME}.mp4", frame, LOOP)
    cinematic(frame(0.0), 0, grain_sigma=0).save(OUT / f"{NAME}-cover.png")


if __name__ == "__main__":
    main()
