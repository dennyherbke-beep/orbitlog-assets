"""Woche 12, Fr 20.11.2026 - Raster-Loop "Venus spins the WRONG way" (Winner-Format Raster + leichte Provokation,
Regel 13: 8-s-Loop). 2x4-Raster, alle 8 Planeten drehen sich gleichzeitig; Pfeil zeigt die Drehrichtung.

Fakten (NASA Planetary Fact Sheet, siderische Rotation): Merkur 58,6 d · Venus 243 d RUECKWAERTS (retrograd) ·
Erde 23,9 h · Mars 24,6 h · Jupiter 9,9 h · Saturn 10,7 h · Uranus 17,2 h, Achse 98 Grad gekippt (rollt auf der
Seite, formal ebenfalls retrograd) · Neptun 16,1 h. Venus: ein Sterntag (243 d) ist laenger als ihr Jahr (225 d);
von der Oberflaeche geht die Sonne im Westen auf. Ursache unklar (Einschlag oder Gezeiten der dichten Atmosphaere).
Darstellung: Drehung stark beschleunigt und fuer den Loop gerundet (Jupiter/Saturn 2 Umdrehungen, Erde/Mars/
Uranus/Neptun 1 Umdrehung pro Loop, Merkur still, Venus 1 Umdrehung rueckwaerts - die Wolkendecke der Venus rotiert tatsaechlich in ~4 Tagen
retrograd) - im Bild als "sped up" vermerkt.
Licht von vorn (keine Nachtseite), damit die Drehung sichtbar ist. Venus-Textur = Wolkendecke mit Y-Muster (tex_venus_uv).

Hook-Varianten:
  1 "Venus spins the WRONG way" (gewaehlt)  2 "On Venus the Sun rises in the WEST"  3 "One planet spins backwards"
  4 "A day on Venus is longer than its year"  5 "Uranus is lying on its side"

    python make-w12-venus-spin-reel.py [--preview DIR]  ->  w12-venus-spin.mp4, -cover.png
"""

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import numpy as np
import bodies
from bodies import planet


def tex_venus_uv():
    """Venus-Wolkendecke mit dem typischen Y-Muster (UV-Aufnahmen, z. B. Akatsuki/Pioneer Venus), damit die
    Drehung sichtbar ist - die Wolkendecke rotiert tatsaechlich retrograd in ~4 Tagen."""
    lat = bodies.lat_grid()
    h, w = lat.shape
    lon = np.radians(np.linspace(-180, 180, w, dtype=np.float32))[None, :]
    n = bodies.fbm(43, octaves=6, base=5)
    arm = np.exp(-((np.abs(lat) - (18 + 16 * np.cos(lon))) / 9) ** 2) * (0.5 + 0.5 * np.cos(lon))
    stem = np.exp(-(np.angle(np.exp(1j * (lon - np.pi))) / 0.45) ** 2) * np.exp(-(lat / 22) ** 2)
    dark = np.clip(0.75 * arm + 0.55 * stem + 0.35 * (n - 0.5), 0, 1)
    img = bodies.mix(bodies.col((244, 224, 178)), bodies.col((170, 128, 74)), dark)
    return img, dict(atmo=(255, 226, 170), atmo_k=0.7)


bodies.TEXTURES["venus_uv"] = tex_venus_uv
from brandkit import S, FG, SEC, ACC, f, downscale
from reelkit import new_frame, header_band, encode, cinematic

OUT = Path(__file__).resolve().parent
NAME = "w12-venus-spin"
W, H, LOOP, FPS = 1080, 1920, 8.0, 30
GRID_TOP, CW, CH = 520, 500, 250
X0 = (W - 2 * CW) // 2
D = 170
RED, GREEN = (255, 96, 86), (110, 220, 140)

# Name, Textur, Tag-Text, Umdrehungen pro Loop (+ = vorwaerts), Achsneigung, Ringe
PLANETS = [("Mercury", "mercury", "1 day: 59 Earth days", 0, 0, None),
           ("Venus", "venus_uv", "243 days, BACKWARDS", -1, 0, None),
           ("Earth", "earth", "1 day: 24 hours", 1, 23, None),
           ("Mars", "mars", "1 day: 24.6 hours", 1, 25, None),
           ("Jupiter", "jupiter", "1 day: 10 hours", 2, 3, None),
           ("Saturn", "saturn", "1 day: 10.7 hours", 2, 27, 18),
           ("Uranus", "uranus", "17 h, lying on its side", 1, 98, None),
           ("Neptune", "neptune", "1 day: 16 hours", 1, 28, None)]


def cell_origin(i):
    return X0 + (i % 2) * CW, GRID_TOP + (i // 2) * CH


def background():
    img, _ = new_frame(61)
    header_band(img, ["Venus spins", "the WRONG way"], "WRONG")
    d = ImageDraw.Draw(img)
    for i, p in enumerate(PLANETS):
        x0, y0 = cell_origin(i)
        if p[0] == "Venus":
            d.rounded_rectangle([(x0 + 6) * S, (y0 + 6) * S, (x0 + CW - 6) * S, (y0 + CH - 6) * S], 18 * S,
                                outline=RED, width=4 * S)
    for txt, fo, col, y in [("Sped up, speeds not to scale · green = same way as Earth", f(22 * S), SEC, 1540),
                            ("Send this to someone who knows Venus is the weird one", f(30 * S, bold=True), FG, 1576),
                            ("Save it: on Venus the Sun rises in the WEST", f(24 * S), SEC, 1618)]:
        d.text(((W * S - d.textlength(txt, font=fo)) / 2, y * S), txt, font=fo, fill=col)
    return downscale(img, W, H)


BG = background()
_CACHE = {}


def sphere(i, rot):
    """Planet i bei Drehwinkel rot (Grad) als (RGB, Maske), gecacht je ganzzahligem Grad."""
    name, kind, _, turns, tilt, ring = PLANETS[i]
    key = (i, int(rot) % 360)
    if key not in _CACHE:
        dd = 112 if ring else D
        box = int(dd * (2.3 if ring else 1.3))
        can = Image.new("RGB", (box * S, box * S), (0, 0, 0))
        planet(can, box * S // 2, box * S // 2, dd, kind, light=(-0.25, -0.2, 0.95), lon0=(200 - key[1]) % 360,
               tilt=tilt, ring_tilt=ring, glow=False)
        sm = downscale(can, box, box)
        _CACHE[key] = (sm, sm.convert("L").point(lambda v: 255 if v > 2 else 0))
    return _CACHE[key]


def arrow(d, cx, cy, sign, vertical, a=1.0):
    """Gebogener Pfeil unter (bzw. neben) dem Planeten; sign +1 = vorwaerts (nach rechts), -1 = rueckwaerts."""
    col = GREEN if sign > 0 else RED
    if vertical:                                                  # Uranus: Drehung von unten nach oben
        pts = [(cx - D * 0.66 - 6 * math.sin(k / 10 * math.pi), cy + D * 0.4 - k * D * 0.08) for k in range(11)]
    else:
        pts = [(cx - D * 0.4 + k * D * 0.08, cy + D * 0.62 + 10 * math.sin(k / 10 * math.pi)) for k in range(11)]
        if sign < 0:
            pts = pts[::-1]
    d.line(pts, fill=col, width=6, joint="curve")
    (x1, y1), (x0, y0) = pts[-1], pts[-3]
    ang = math.atan2(y1 - y0, x1 - x0)
    for s_ in (2.5, -2.5):
        d.line([(x1, y1), (x1 - 18 * math.cos(ang + s_ / 6), y1 - 18 * math.sin(ang + s_ / 6))], fill=col, width=6)


def frame(t):
    im = BG.copy()
    d = ImageDraw.Draw(im)
    u = t / LOOP
    for i, (name, kind, txt, turns, tilt, ring) in enumerate(PLANETS):
        x0, y0 = cell_origin(i)
        cx, cy = x0 + (140 if ring else 120), y0 + CH // 2 - 14
        tx = x0 + (296 if ring else 236)
        sign = -1 if name == "Venus" else 1
        rgb, m = sphere(i, 360 * turns * u)                      # Merkur steht fast still
        im.paste(rgb, (int(cx - rgb.width / 2), int(cy - rgb.height / 2)), m)
        arrow(d, cx, cy, sign, name == "Uranus")
        st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
        d.text((tx, y0 + 66), name, font=f(38, bold=True), fill=RED if name == "Venus" else FG, **st)
        d.text((tx, y0 + 118), txt, font=f(24, bold=name == "Venus"), fill=(235, 236, 240), **st)
        if name == "Venus":
            d.text((tx, y0 + 152), "Its day > its year", font=f(24), fill=ACC, **st)
    return im


def main():
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (0.0, 2.0):
            cinematic(frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved")
        return
    encode(OUT / f"{NAME}.mp4", frame, LOOP, fps=FPS)
    cinematic(frame(0.0), 0, grain_sigma=0).save(OUT / f"{NAME}-cover.png")


if __name__ == "__main__":
    main()
