"""Woche 13, Fr 27.11.2026 (Tag nach Thanksgiving) - Raster-Loop "How much would YOU weigh on other worlds?"
(Winner-Variante des Raster-Formats, Kommentar-Hook "Comment your weight", 8-s-Loop).

Oberflaechenschwerkraft (NASA Planetary Fact Sheet, m/s^2; Erde 9,80): Mond 1,62, Mars 3,73, Venus 8,87,
Jupiter 24,79 (1 bar, Wolkenobergrenze), Saturn 10,44 (1 bar), Pluto 0,62. Faktor = g / 9,80.
Beispiel 70 kg (154 lb) auf der Erde -> Gewichtskraft entspricht der Skalenanzeige auf der Erde. Koerper nicht massstaeblich.

Hook-Varianten: 1 "Post-Thanksgiving weigh-in on OTHER WORLDS" (gewaehlt) 2 "Comment your weight - I'll tell you Mars"
3 "You'd weigh 2.5x on Jupiter" 4 "The Moon: the only diet that works" 5 "Where would you weigh the least?"
    python make-w13-weight-worlds-reel.py [--preview DIR]
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import ACC, FG, SEC
from reelkit import header_bg, encode, cinematic, stext, ease, body_sprite, paste_center

OUT = Path(__file__).resolve().parent
NAME = "w13-weight-worlds"
W, H, LOOP = 1080, 1920, 8.0
KG = 70.0
GT, CW, CH = 600, 500, 330
X0 = (W - 2 * CW) // 2
G0 = 9.80
# Name, Sprite-Art, g, Durchmesser px, ring_tilt, lon0
WORLDS = [("Moon", "moon", 1.62, 150, None, 20), ("Mars", "mars", 3.73, 150, None, 60),
          ("Venus", "venus", 8.87, 160, None, 0), ("Jupiter*", "jupiter", 24.79, 190, None, 40),
          ("Saturn*", "saturn", 10.44, 110, 22, 0), ("Pluto", "pluto", 0.62, 120, None, 150)]
SPR = [body_sprite(k, d, lon0=l, ring_tilt=rt) for _, k, g, d, rt, l in WORLDS]
BG = header_bg(97, ["Post-Thanksgiving weigh-in", "on OTHER WORLDS"], "OTHER WORLDS")


def frame(t):
    im = BG.copy()
    stext(im, "If you weigh 70 kg (154 lb) on Earth...", 34, 528, FG)
    k = ease((t + 0.6) / 1.4) * (1 - 0.62 * ease((t - 7.0) / 1.0))        # Bild 0 zeigt schon laufende Werte, Loop schliesst
    for i, (name, kind, g, dpx, rt, lon) in enumerate(WORLDS):
        x0, y0 = X0 + (i % 2) * CW, GT + (i // 2) * CH
        cx, cy = x0 + CW // 2, y0 + 120
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([x0 + 6, y0 + 6, x0 + CW - 6, y0 + CH - 6], radius=22, outline=(70, 78, 100), width=2)
        paste_center(im, SPR[i], cx - 120, cy)
        fac = g / G0
        shown = KG + (KG * fac - KG) * k                        # Zaehler laeuft von 70 zum Zielwert
        up = fac > 1
        col = ACC if up else FG
        stext(im, name, 30, y0 + 24, FG, cx=cx + 120)
        stext(im, f"{shown:.0f} kg", 54, y0 + 78, col, cx=cx + 120)
        stext(im, f"{shown * 2.2046:.0f} lb", 28, y0 + 148, SEC, cx=cx + 120, bold=False)
        stext(im, f"x {fac:.2f}", 26, y0 + 190, col if k > 0.9 else SEC, cx=cx + 120, bold=False)
        bar = int(300 * min(shown / (KG * 2.6), 1))              # Balken: Gewicht relativ zu Jupiter-Maximum
        d.rounded_rectangle([x0 + 100, y0 + 262, x0 + 100 + 300, y0 + 274], radius=6, fill=(40, 46, 62))
        d.rounded_rectangle([x0 + 100, y0 + 262, x0 + 100 + max(bar, 4), y0 + 274], radius=6, fill=col)
    y = GT + 3 * CH + 10
    stext(im, "Comment your weight on Earth", 40, y, ACC)
    stext(im, "Bodies not to scale · *cloud tops (1 bar) · NASA fact sheet", 21, y + 52, SEC, bold=False, stroke=3)
    stext(im, "Send this to someone who ate too much pie", 32, y + 86, FG)
    stext(im, "Save it: you'd weigh 2.5x on Jupiter, 6x less on the Moon", 24, y + 132, SEC, bold=False, stroke=3)
    return im


def main():
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1]); prev.mkdir(parents=True, exist_ok=True)
        for t in (0.0, 3.0):
            cinematic(frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved"); return
    encode(OUT / f"{NAME}.mp4", frame, LOOP)
    cinematic(frame(3.0), 0, grain_sigma=0).save(OUT / f"{NAME}-cover.png")


if __name__ == "__main__":
    main()
