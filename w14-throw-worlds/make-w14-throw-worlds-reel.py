"""Woche 14, Mo 30.11.2026 - Rennen "Throw a ball 45 mph on other WORLDS" (Typ a Vergleich/Rennen, 10-s-Loop, 7x Zeitraffer).
Ideale Wurfparabel ohne Luftwiderstand: v = 20 m/s (72 km/h = 45 mph), Winkel 45 Grad.
  Reichweite R = v^2 * sin(2a) / g = 400 / g ; Flugzeit T = 2 v sin(a) / g ; Scheitel h = (v sin a)^2 / (2 g) = 100 / g
Oberflaechenbeschleunigung g (NASA Planetary Fact Sheets): Pluto 0,62 · Mond 1,62 · Mars 3,71 · Erde 9,81 · Jupiter 24,79 (bei 1 bar, Wolkenobergrenze, keine feste Oberflaeche)
  -> Reichweiten 645 m / 247 m / 108 m / 41 m / 16 m. Alle Baelle starten gleichzeitig (Zeitraffer 7x), Parabeln im selben Massstab.
Eigene Animation, Planeten-Kugeln aus NASA-Karten (bodies.py). Hook-Varianten: 1 "Throw a ball 45 mph on other WORLDS" (gewaehlt)
2 "You could throw a baseball 645 m on Pluto" 3 "One throw. Five worlds." 4 "Where would YOU play baseball?" 5 "Rate these throws"
    python make-w14-throw-worlds-reel.py [--preview DIR]
"""
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, f, downscale
from reelkit import new_frame, header_band, encode, cinematic, body_sprite, stext, ease

OUT = Path(__file__).resolve().parent
NAME = "w14-throw-worlds"
W, H, LOOP = 1080, 1920, 10.0
SPEED, T0 = 7.0, 0.15
V, ANG = 20.0, math.radians(45)
PX = 1.35                                  # Pixel pro Meter (waagerecht und senkrecht)
X0 = 62
BAND = 56

# (Name, g, Bodenfarbe, Boden-y, Sprite-kind)
LANES = [
    ("Pluto", 0.62, (92, 74, 64), 830, "pluto"),
    ("Moon", 1.62, (96, 94, 92), 1010, "moon"),
    ("Mars", 3.71, (112, 56, 34), 1150, "mars"),
    ("Earth", 9.81, (46, 92, 52), 1270, "earth"),
    ("Jupiter*", 24.79, (170, 134, 98), 1390, "jupiter"),
]
SPR = {ln[0]: body_sprite(ln[4], 52, light=(-0.2, -0.2, 0.95)) for ln in LANES}


def background():
    img, _ = new_frame(75)
    header_band(img, ["Throw a ball 45 mph", "on other WORLDS"], "WORLDS")
    d = ImageDraw.Draw(img)
    for name, g, col, gy, kind in LANES:
        d.rectangle([40 * S, gy * S, (W - 40) * S, (gy + BAND) * S], fill=col)
        d.rectangle([40 * S, gy * S, (W - 40) * S, (gy + 3) * S], fill=tuple(min(255, c + 40) for c in col))
    foot = "Same throw: 72 km/h at 45° · 7x speed · ideal throw, no air drag · *cloud tops"
    d.text(((W * S - d.textlength(foot, font=f(21 * S))) / 2, 1478 * S), foot, font=f(21 * S), fill=SEC)
    cta = "Send this to a baseball fan"
    d.text(((W * S - d.textlength(cta, font=f(40 * S, bold=True))) / 2, 1520 * S), cta, font=f(40 * S, bold=True), fill=FG)
    sv = "Save it: on Pluto the ball flies 645 m"
    d.text(((W * S - d.textlength(sv, font=f(28 * S))) / 2, 1578 * S), sv, font=f(28 * S), fill=SEC)
    return downscale(img, W, H)


BG = background()


def ball(d, x, y, r=13):
    d.ellipse([x - r - 2, y - r - 2, x + r + 2, y + r + 2], fill=(8, 10, 14))
    d.ellipse([x - r, y - r, x + r, y + r], fill=(238, 238, 232))
    d.ellipse([x - r * 0.55, y - r * 0.6, x + r * 0.15, y + r * 0.1], fill=(252, 252, 248))
    d.arc([x - r * 1.5, y - r * 0.9, x - r * 0.2, y + r * 0.9], -50, 50, fill=(200, 50, 44), width=2)
    d.arc([x + r * 0.2, y - r * 0.9, x + r * 1.5, y + r * 0.9], 130, 230, fill=(200, 50, 44), width=2)


def pos(g, t):
    tr = max(0.0, t - T0) * SPEED
    tf = 2 * V * math.sin(ANG) / g
    tr = min(tr, tf)
    x = V * math.cos(ANG) * tr
    y = V * math.sin(ANG) * tr - 0.5 * g * tr * tr
    return x, max(0.0, y), tr >= tf


def frame(t):
    im = BG.copy()
    d = ImageDraw.Draw(im)
    for name, g, col, gy, kind in LANES:
        rgb, m = SPR[name]
        im.paste(rgb, (int(X0 + 8 - rgb.width / 2), int(gy + BAND / 2 - rgb.height / 2)), m)
        stext(im, f"{name}", 32, gy + 6, fill=FG, bold=True, cx=X0 + 8 + 120, stroke=3)
        stext(im, f"{g / 9.81:.2f} g" if g < 9 else ("1 g" if g == 9.81 else f"{g / 9.81:.1f} g"), 24, gy + 14,
              fill=(236, 238, 244), bold=False, cx=980, stroke=3)
        # Spur
        tf = 2 * V * math.sin(ANG) / g
        steps = 60
        tcur = min(max(0.0, t - T0) * SPEED, tf)
        for k in range(1, steps):
            tk = tcur * k / steps
            if tk <= 0:
                continue
            px = X0 + V * math.cos(ANG) * tk * PX
            py = gy - (V * math.sin(ANG) * tk - 0.5 * g * tk * tk) * PX
            if k % 2 == 0:
                d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=(255, 236, 190))
        x, y, landed = pos(g, t)
        bx, by = X0 + x * PX, gy - y * PX - 13
        ball(d, bx, by)
        if landed:
            rng_m = V * V * math.sin(2 * ANG) / g
            a = ease((t - T0 - tf / SPEED) / 0.25)
            lab = f"{rng_m:.0f} m"
            if rng_m < 200:
                stext(im, lab, 46, gy - 62, fill=ACC, a=a, cx=bx + 100, stroke=4)
            else:
                stext(im, lab, 46, by - 70, fill=ACC, a=a, cx=min(bx, 940), stroke=4)
    return im


def main():
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (0.0, 0.6, 3.0, 8.5):
            cinematic(frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved")
        return
    encode(OUT / f"{NAME}.mp4", frame, LOOP)
    cinematic(frame(8.5), 0, grain_sigma=0).save(OUT / f"{NAME}-cover.png")


if __name__ == "__main__":
    main()
