"""Woche 14, Di 01.12.2026 - Experiment Typ f "The Sun built a BUBBLE around us" (Heliosphaere, 8-s-Loop, vereinfachte Kugel).
Fakten: Heliopause ~120 AU (Voyager 1 hat sie im Aug 2012 bei ~121 AU gekreuzt, Voyager 2 im Nov 2018 bei ~119 AU);
Terminationsschock ~84-94 AU (Voyager 2 / Voyager 1); Neptunbahn 30 AU. Die Heliosphaere schirmt einen grossen Teil der
galaktischen kosmischen Strahlung ab. Ihre wahre Form ist umstritten (Komet vs. Kugel/Croissant) -> im Bild "simplified, shape debated".
Animation: Sonnenwind-Teilchen stroemen nach aussen, galaktische Strahlen laufen von aussen ein und enden an der Grenze.
Massstab: 400 px = 120 AU (3,33 px/AU). Eigene Grafik (bodies.star), keine Fremdbilder.
Hook-Varianten: 1 "The Sun built a BUBBLE around us" (gewaehlt) 2 "We live inside a star's BUBBLE" 3 "Space has an edge - and we crossed it"
4 "Voyager left the bubble. Did you know?" 5 "Is the Sun protecting you right now?"
    python make-w14-sun-bubble-reel.py [--preview DIR]
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, f, downscale
from reelkit import new_frame, header_band, encode, cinematic, body_sprite, paste_center, stext

OUT = Path(__file__).resolve().parent
NAME = "w14-sun-bubble"
W, H, LOOP = 1080, 1920, 8.0
CX, CY, RB = 540, 1010, 400.0              # Zentrum, Heliopause-Radius (120 AU)
PXAU = RB / 120.0


def background():
    img, _ = new_frame(76)
    header_band(img, ["The Sun built a", "BUBBLE around us"], "BUBBLE")
    d = ImageDraw.Draw(img)
    foot = "Simplified, shape debated · distances in AU (1 AU = Earth-Sun)"
    d.text(((W * S - d.textlength(foot, font=f(22 * S))) / 2, 1478 * S), foot, font=f(22 * S), fill=SEC)
    cta = "Send this to someone who thinks space is empty"
    d.text(((W * S - d.textlength(cta, font=f(36 * S, bold=True))) / 2, 1520 * S), cta, font=f(36 * S, bold=True), fill=FG)
    sv = "Save it: Voyager 1 left the bubble in 2012"
    d.text(((W * S - d.textlength(sv, font=f(28 * S))) / 2, 1578 * S), sv, font=f(28 * S), fill=SEC)
    bg = np.asarray(downscale(img, W, H), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.hypot(xx - CX, yy - CY)
    inner = 0.22 * np.clip(1 - r / RB, 0, 1) ** 1.5
    edge = np.exp(-((r - RB) / 7.0) ** 2) * 0.9 + np.exp(-np.clip(r - RB, 0, None) / 40.0) * (r > RB) * 0.12
    shock = np.exp(-((r - 90 * PXAU) / 3.0) ** 2) * 0.25
    col_in = np.array([70, 110, 220], np.float32)
    col_edge = np.array([140, 190, 255], np.float32)
    bg = bg + (inner[..., None] * col_in + edge[..., None] * col_edge + shock[..., None] * col_edge)
    return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))


BG = background()
SUN = body_sprite("sun", 34)
rng = np.random.default_rng(3)
WIND = [(rng.uniform(0, 2 * math.pi), rng.uniform(0, 1), rng.uniform(0.7, 1.3)) for _ in range(150)]
CR = [(rng.uniform(0, 2 * math.pi), rng.uniform(0, 1)) for _ in range(46)]


def frame(t):
    im = BG.copy()
    d = ImageDraw.Draw(im, "RGBA")
    # Neptunbahn
    rn = 30 * PXAU
    d.ellipse([CX - rn, CY - rn, CX + rn, CY + rn], outline=(200, 210, 230, 110), width=2)
    # Sonnenwind: von innen nach aussen, verblasst zur Grenze
    for a, ph, sp in WIND:
        u = (t / LOOP + ph) % 1.0
        r = 14 + u * (RB - 14)
        x, y = CX + r * math.cos(a), CY + r * math.sin(a)
        al = int(210 * (1 - u ** 3))
        s = 2.2 - 0.8 * u
        d.ellipse([x - s, y - s, x + s, y + s], fill=(255, 214, 140, al))
    # Galaktische Strahlen: von aussen, enden an der Grenze
    for a, ph in CR:
        u = (t / LOOP + ph) % 1.0
        r = RB + 150 - u * 150
        if r < RB - 2:
            continue
        x, y = CX + r * math.cos(a), CY + r * math.sin(a)
        x2, y2 = CX + (r + 14) * math.cos(a), CY + (r + 14) * math.sin(a)
        al = int(230 * min(1, (1 - u) * 3) * min(1, u * 6 + 0.2))
        d.line([x, y, x2, y2], fill=(190, 230, 255, al), width=2)
    paste_center(im, SUN, CX, CY)
    # Voyager-Punkte ausserhalb
    for ang, name in ((-34, "Voyager 1"), (36, "Voyager 2")):
        a = math.radians(ang)
        rv = RB + 78
        x, y = CX + rv * math.cos(a), CY + rv * math.sin(a)
        d.ellipse([x - 7, y - 7, x + 7, y + 7], fill=(255, 255, 255, 255), outline=(8, 10, 14, 255), width=2)
        stext(im, name, 26, y - 44 if ang < 0 else y + 16, fill=FG, cx=min(x, 960), stroke=3)
    # Beschriftung
    stext(im, "Sun", 24, CY + 22, fill=(255, 224, 170), bold=True, cx=CX, stroke=3)
    stext(im, "Neptune's orbit · 30 AU", 22, CY - rn - 34, fill=(215, 222, 238), bold=False, cx=CX, stroke=3)
    stext(im, "EDGE OF THE BUBBLE · ~120 AU", 28, CY - RB - 52, fill=ACC, cx=CX, stroke=4)
    stext(im, "Sun's wind pushes out", 24, CY + RB - 70, fill=(255, 224, 170), bold=False, cx=CX, stroke=3)
    stext(im, "Cosmic rays stopped here", 24, CY + RB + 26, fill=(200, 232, 255), bold=False, cx=CX, stroke=3)
    return im


def main():
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (0.0, 4.0):
            cinematic(frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved")
        return
    encode(OUT / f"{NAME}.mp4", frame, LOOP)
    cinematic(frame(2.0), 0, grain_sigma=0).save(OUT / f"{NAME}-cover.png")


if __name__ == "__main__":
    main()
