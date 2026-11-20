"""Woche 13, Di 24.11.2026 - Himmelstermin-Reel "The Full Moon is hiding URANUS this week" (8-s-Loop, Regel 13).
Sternkarte Stier (Plejaden, Hyaden, Aldebaran) mit Uranus; Mondlicht blendet (Vollmond 24.11.) und blendet wieder aus
(Mondfreie Abende 5.-13.12.). Ort/Zeit gerechnet mit astropy (builtin-Ephemeriden):
  Uranus-Opposition 2026-11-25 ~23:00 UTC (Sonnenabstand max.), RA 4h05m, Dec +20,7 Grad, 18,44 AU, Sternbild Stier,
  ~5,3 Grad oestlich der Plejaden. Vollmond 24.11. (Beleuchtung 100 % um 22 UTC), Mond 24.11. 19 UTC bei RA 61,6 / Dec +25,9.
  Neumond 9.12.; 5.-13.12. am Abend ohne stoerenden Mond. Helligkeit Uranus ~5,7 mag (Naked-Eye-Grenze).
Sterne: Standard-Koordinaten (Hipparcos-Naeherung) der hellsten Plejaden/Hyaden/Aldebaran/Lambda Tau.

Hook-Varianten: 1 "The Full Moon is hiding URANUS this week" (gewaehlt)  2 "Uranus is closest this week - you can't see it"
3 "A planet you CAN see - barely" 4 "Find URANUS: 5 degrees from the Pleiades" 5 "Rate: can you spot it?"
    python make-w13-uranus-moon-reel.py [--preview DIR]
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
NAME = "w13-uranus-moon"
W, H, LOOP = 1080, 1920, 8.0
CY0, CHH = 560, 930                      # Kartenbereich y
RA0, DEC0, SC = 62.5, 20.5, 56.0         # Mitte (Grad), Pixel pro Grad
COS = math.cos(math.radians(DEC0))

STARS = [  # RA, Dec, mag, Name
    (68.980, 16.509, 0.85, "Aldebaran"), (64.948, 15.628, 3.65, ""), (65.733, 17.543, 3.76, ""),
    (67.154, 19.180, 3.53, ""), (67.166, 15.871, 3.40, ""), (60.170, 12.490, 3.40, ""),
    (56.871, 24.105, 2.87, ""), (57.291, 24.053, 3.62, ""), (56.219, 24.113, 3.70, ""), (56.457, 24.367, 3.88, ""),
    (56.582, 23.948, 4.18, ""), (56.302, 24.467, 4.30, ""), (57.297, 24.137, 5.05, ""),
]
URANUS = (61.273, 20.670)
MOON = (61.56, 25.88)


def xy(ra, dec):
    return W / 2 - (ra - RA0) * COS * SC, CY0 + CHH / 2 - (dec - DEC0) * SC


YY, XX = np.mgrid[0:CHH, 0:W].astype(np.float32)


def splat(canvas, x, y, mag, k=1.0):
    r = 2.4 + max(0.0, 5.4 - mag) * 1.6
    d2 = (XX - x) ** 2 + (YY - (y - CY0)) ** 2
    core = np.exp(-d2 / (2 * (r * 0.55) ** 2))
    halo = np.exp(-d2 / (2 * (r * 2.4) ** 2)) * 0.25 * max(0.0, (4.5 - mag) / 4)
    canvas += (core + halo)[..., None] * np.array([218, 228, 255], np.float32) * k


def background():
    img, _ = new_frame(61)
    header_band(img, ["The Full Moon is hiding", "URANUS this week"], "URANUS")
    d = ImageDraw.Draw(img)
    info = "Closest + brightest: Nov 25 · about magnitude 5.7 · binoculars help"
    d.text(((W * S - d.textlength(info, font=f(24 * S))) / 2, 1500 * S), info, font=f(24 * S), fill=SEC)
    cta = "Send this to someone with binoculars"
    d.text(((W * S - d.textlength(cta, font=f(36 * S, bold=True))) / 2, 1545 * S), cta, font=f(36 * S, bold=True), fill=FG)
    sv = "Save it: look again Dec 5-13, no Moon"
    d.text(((W * S - d.textlength(sv, font=f(27 * S))) / 2, 1596 * S), sv, font=f(27 * S), fill=SEC)
    return downscale(img, W, H)


BG = background()
mx, my = xy(*MOON)
ux, uy = xy(*URANUS)
px, py = xy(56.87, 24.1)


def frame(t):
    m = 0.5 + 0.5 * math.cos(2 * math.pi * t / LOOP)              # 1 = Vollmond, 0 = mondfrei
    m = m * m * (3 - 2 * m)
    cv = np.zeros((CHH, W, 3), np.float32)
    r = np.hypot(XX - mx, YY - (my - CY0))
    cv += (np.exp(-r / 330) * 70 * m + np.exp(-r / 70) * 70 * m)[..., None] * np.array([1.0, 1.0, 1.1], np.float32)
    cv += np.array([7, 9, 15], np.float32)
    for ra, dec, mag, _ in STARS:
        x, y = xy(ra, dec)
        splat(cv, x, y, mag, k=1.0 if mag < 3.0 else (1 - 0.8 * m if mag < 4 else 1 - 0.97 * m))
    # Uranus: schwacher Punkt (5,7 mag), vom Mondlicht verschluckt
    splat(cv, ux, uy, 5.7, k=0.9 * (1 - 0.9 * m) + 0.25)
    # Mond (Vollmond ~0,5 Grad = 28 px)
    d2 = np.hypot(XX - mx, YY - (my - CY0))
    cv += (np.clip(15 - d2, 0, 1) * 235 * m)[..., None] * np.array([1.0, 0.98, 0.93], np.float32)
    im = BG.copy()
    cur = np.asarray(im, np.float32)
    yy = np.arange(CHH, dtype=np.float32)[:, None, None]
    fade = np.clip(np.minimum(yy, CHH - 1 - yy) / 70.0, 0, 1)
    cur[CY0:CY0 + CHH] = np.clip(cur[CY0:CY0 + CHH] * (1 - fade) + cv * fade, 0, 255)
    pic = Image.fromarray(cur.astype(np.uint8))
    # sanfter Kartenrand
    d = ImageDraw.Draw(pic)
    fs = lambda s, b=False: f(s, bold=b)
    st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
    # Uranus-Ring pulsiert
    ph = (t % 2.0) / 2.0
    for k, a in ((0, 1.0), (1, 0.45)):
        rr = 26 + 34 * ((ph + 0.5 * k) % 1.0)
        al = (1 - ((ph + 0.5 * k) % 1.0)) * a
        col = tuple(int(c * al + 11 * (1 - al)) for c in (110, 232, 232))
        d.ellipse([ux - rr, uy - rr, ux + rr, uy + rr], outline=col, width=3)
    d.ellipse([ux - 24, uy - 24, ux + 24, uy + 24], outline=(110, 232, 232), width=3)
    d.text((ux + 40, uy + 6), "URANUS", font=fs(40, True), fill=(110, 232, 232), **st)
    d.text((ux + 42, uy + 50), "magnitude ~5.7", font=fs(24), fill=SEC, **st)
    # Plejaden + Aldebaran
    d.text((px - 62, py - 70), "Pleiades", font=fs(30, True), fill=FG, **st)
    ax, ay = xy(68.98, 16.51)
    d.text((ax - 40, ay + 22), "Aldebaran", font=fs(28, True), fill=FG, **st)
    # gestrichelte Linie Plejaden -> Uranus + Abstand
    n = 18
    for i in range(n):
        if i % 2 == 0:
            a0, a1 = i / n, (i + 1) / n
            d.line([px + (ux - px) * a0, py + 24 + (uy - py - 24) * a0, px + (ux - px) * a1, py + 24 + (uy - py - 24) * a1],
                   fill=(150, 160, 180), width=2)
    d.text(((px + ux) / 2 + 14, (py + uy) / 2 - 8), "~5°", font=fs(34, True), fill=ACC, **st)
    d.text(((px + ux) / 2 + 14, (py + uy) / 2 + 34), "half a fist at arm's length", font=fs(22), fill=SEC, **st)
    # Mond-Label (blendet mit m)
    lab = Image.new("RGBA", pic.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(lab)
    a = int(255 * m)
    ld.text((mx + 36, my - 20), "Full Moon", font=fs(34, True), fill=(255, 245, 225, a), stroke_width=3, stroke_fill=(8, 10, 14, a))
    ld.text((mx + 36, my + 20), "Nov 24", font=fs(24), fill=(200, 205, 220, a), stroke_width=3, stroke_fill=(8, 10, 14, a))
    b = int(255 * (1 - m))
    ld.text((W / 2 - 190, CY0 + CHH - 110), "Dec 5-13: dark evenings", font=fs(32, True), fill=(255, 180, 84, b),
            stroke_width=3, stroke_fill=(8, 10, 14, b))
    pic = Image.alpha_composite(pic.convert("RGBA"), lab).convert("RGB")
    return pic


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
