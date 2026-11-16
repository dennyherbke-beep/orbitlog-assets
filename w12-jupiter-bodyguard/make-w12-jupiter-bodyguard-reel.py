"""Woche 12, Do 19.11.2026 - Remake-Kandidat 1 (jr_scientist_ "Asteroid vs. Jupiter", 731K Likes): Himmelskoerper als
Figuren mit Sprechblasen, eigene Grafik (bodies.py), ehrliche Aufloesung. Regel 13: 12 s, Loop.

Ablauf:
  0-2,6   Asteroid fliegt Richtung Erde (gestrichelte Bahn)       Asteroid: "Next stop: EARTH."   Erde: "uh oh"
  2,6-5,4 Jupiters Schwerkraft biegt die Bahn ab                  Jupiter: "Not today."
  5,4-8   Asteroid fliegt davon                                   Erde: "My hero!"
  8-11,4  Komet kommt von aussen, Jupiter lenkt ihn NACH INNEN    Jupiter: "...but sometimes I send them TO you."  Erde: "WHAT?!"
  11,4-12 Ueberblendung zum Start

Fakten (NASA/JPL; Horner & Jones 2008-2010, Int. J. Astrobiology): Jupiter wirft viele Kometen aus dem Sonnensystem,
lenkt aber auch Asteroiden/Kometen in die innere Bahnregion -> Schutzwirkung umstritten, netto unklar.
Shoemaker-Levy 9 traf 1994 Jupiter. Darstellung nicht massstaeblich.

Hook-Varianten:
  1 "Is Jupiter really / Earth's BODYGUARD?" (gewaehlt)  2 "Jupiter saves Earth. Sometimes."  3 "Jupiter has a secret"
  4 "Thank Jupiter for this. Or don't."  5 "The planet that protects us... or not"

    python make-w12-jupiter-bodyguard-reel.py [--preview DIR]  ->  w12-jupiter-bodyguard.mp4, -cover.png
"""

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bodies import asteroid
from brandkit import S, FG, SEC, ACC, f, downscale
from reelkit import new_frame, header_band, encode, cinematic, body_sprite, paste_center, ease

OUT = Path(__file__).resolve().parent
NAME = "w12-jupiter-bodyguard"
W, H, LOOP = 1080, 1920, 12.0
JUP, EARTH = (770, 1010), (170, 1420)
INK = (14, 16, 22)


def bg():
    img, _ = new_frame(52)
    header_band(img, ["Is Jupiter really", "Earth's BODYGUARD?"], "BODYGUARD")
    d = ImageDraw.Draw(img)
    for txt, fo, col, y in [("Illustration · not to scale", f(22 * S), SEC, 1560),
                            ("Send this to someone who thinks Jupiter protects us", f(32 * S, bold=True), FG, 1596),
                            ("Save it: the full answer is in the caption", f(24 * S), SEC, 1640)]:
        d.text(((W * S - d.textlength(txt, font=fo)) / 2, y * S), txt, font=fo, fill=col)
    return downscale(img, W, H)


BG = bg()
JUP_SPR = body_sprite("jupiter", 560, lon0=210, light=(-0.6, -0.3, 0.74))
EARTH_SPR = body_sprite("earth", 130, lon0=20, light=(0.55, -0.45, 0.70))


def rock_sprites(d, n=24, seed=3, color=(132, 124, 114)):
    out = []
    for k in range(n):
        can = Image.new("RGB", ((d + 20) * S, (d + 20) * S), (0, 0, 0))
        asteroid(can, can.width // 2, can.height // 2, d, seed=seed, rot=360 * k / n, light=(0.7, -0.4, 0.6), color=color)
        sm = downscale(can, d + 20, d + 20)
        out.append((sm, sm.convert("L").point(lambda v: 255 if v > 3 else 0)))
    return out


ROCK = rock_sprites(96)
COMET = rock_sprites(54, seed=9, color=(150, 156, 166))


def bez(p0, p1, p2, u):
    return ((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
            (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1])


A0, A1, A2 = (40, 720), (640, 700), (1160, 620)                  # Asteroid: abgelenkt nach rechts oben
C0, C1, C2 = (1140, 580), (500, 880), (90, 1330)                 # Komet: von aussen um Jupiter herum nach innen


def asteroid_pos(t):
    u = 0.07 + 0.93 * ease(t / 8.0) if t < 8 else 1.2
    if t < 2.6:                                                    # zuerst geradeaus Richtung Erde
        s = 0.07 + 0.25 * t / 2.6
        sx, sy = A0[0] + (EARTH[0] + 380 - A0[0]) * s, A0[1] + (EARTH[1] - 60 - A0[1]) * s
        bx, by = bez(A0, A1, A2, u)
        return sx + (bx - sx) * ease(t / 2.6), sy + (by - sy) * ease(t / 2.6)
    return bez(A0, A1, A2, u)


def dashed(d, p, q, col, w=4, seg=18):
    L = math.hypot(q[0] - p[0], q[1] - p[1])
    for s in range(0, int(L), seg * 2):
        a, b = s / L, min(L, s + seg) / L
        d.line([p[0] + (q[0] - p[0]) * a, p[1] + (q[1] - p[1]) * a, p[0] + (q[0] - p[0]) * b, p[1] + (q[1] - p[1]) * b],
               fill=col, width=w)


def bubble(im, txt, x, y, a, tail, size=38, col=INK, bg=(250, 250, 246)):
    """Sprechblase mit Spitze zum Sprecher (tail = Punkt). x, y = Mitte der Blase."""
    if a <= 0.01:
        return
    lay = im.copy()
    d = ImageDraw.Draw(lay)
    fo = f(size, bold=True)
    tw = d.textlength(txt, font=fo)
    w, h = tw + 44, size + 34
    box = [x - w / 2, y - h / 2, x + w / 2, y + h / 2]
    bx = min(max(tail[0], box[0] + 30), box[2] - 30)
    by = box[3] if tail[1] > y else box[1]
    d.polygon([(bx - 16, by), (bx + 16, by), tail], fill=bg)
    d.rounded_rectangle(box, 22, fill=bg)
    d.text((x - tw / 2, y - size / 2 - 4), txt, font=fo, fill=col)
    im.paste(Image.blend(im, lay, a))


def fade(t, a, b, k=0.3):
    return ease((t - a) / k) * (1 - ease((t - b) / k))


def frame(t):
    im = BG.copy()
    d = ImageDraw.Draw(im)
    pa = fade(t, -1, 2.9)                                          # gestrichelte Bahn Richtung Erde
    if pa > 0:
        dashed(d, A0, (EARTH[0] + 40, EARTH[1] - 60), tuple(int(c * pa) for c in (255, 96, 86)))
    ca = fade(t, 8.0, 11.6)                                        # Kometenbahn nach innen
    if ca > 0:
        pts = [bez(C0, C1, C2, k / 40) for k in range(41)]
        for k in range(0, 40, 2):
            d.line([pts[k], pts[k + 1]], fill=tuple(int(c * ca) for c in (255, 180, 84)), width=4)
    paste_center(im, JUP_SPR, *JUP)
    paste_center(im, EARTH_SPR, *EARTH)
    rx, ry = asteroid_pos(t)
    ta = fade(t, 2.4, 8.4)                                         # Spur der abgelenkten Bahn
    if ta > 0:
        t0 = 1.2
        pts = [asteroid_pos(t0 + max(0.0, t - t0) * k / 30) for k in range(31)]
        for k in range(30):
            c = int(150 * ta * k / 30)
            d.line([pts[k], pts[k + 1]], fill=(c, c, int(c * 1.1)), width=3)
    if t < 8.2:
        spr = ROCK[int(t * 6) % len(ROCK)]
        paste_center(im, spr, rx, ry)
    if 8.0 <= t < 11.8:
        u = ease((t - 8.0) / 3.4)
        cx, cy = bez(C0, C1, C2, u)
        paste_center(im, COMET[int(t * 8) % len(COMET)], cx, cy)
    # Sprechblasen
    bubble(im, "Next stop: EARTH.", 330, 610, fade(t, -1, 2.6), (rx, ry - 40))
    bubble(im, "uh oh", EARTH[0] + 40, EARTH[1] - 140, fade(t, 0.8, 2.6), (EARTH[0], EARTH[1] - 70), 34)
    bubble(im, "Not today.", JUP[0] + 120, JUP[1] - 380, fade(t, 2.8, 5.4), (JUP[0] + 60, JUP[1] - 285), 44)
    bubble(im, "Wheeeee", min(rx, 900) - 60, max(ry, 640) + 90, fade(t, 4.4, 6.6), (min(rx, 960), max(ry, 640) + 40), 32)
    bubble(im, "My hero!", EARTH[0] + 60, EARTH[1] - 140, fade(t, 5.6, 8.0), (EARTH[0], EARTH[1] - 70), 36)
    bubble(im, "...but sometimes I", JUP[0] - 60, JUP[1] - 400, fade(t, 8.2, 11.6), (JUP[0] - 60, JUP[1] - 280), 36)
    bubble(im, "send them TO you.", JUP[0] - 60, JUP[1] - 330, fade(t, 8.2, 11.6), (JUP[0] - 60, JUP[1] - 280), 36,
           col=(200, 40, 30))
    bubble(im, "WHAT?!", EARTH[0] + 50, EARTH[1] - 140, fade(t, 9.4, 11.6), (EARTH[0], EARTH[1] - 70), 40)
    return im


def main():
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (0.0, 1.8, 4.0, 6.5, 9.0, 10.6):
            cinematic(frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved")
        return
    encode(OUT / f"{NAME}.mp4", frame, LOOP)
    cinematic(frame(1.8), 0, grain_sigma=0).save(OUT / f"{NAME}-cover.png")


if __name__ == "__main__":
    main()
