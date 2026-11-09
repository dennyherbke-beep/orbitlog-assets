"""Woche 11, Di 10.11.2026: "Pluto IS a planet. Change my mind." (neues Provokations-Format, Hot Take).
Pluto (New-Horizons-Karte) dreht sich gross in der Mitte, Charon kreist (nicht massstaeblich). Argumente erscheinen
nacheinander, eine Punktetafel unten fuellt sich (4 Haken, 1 Kreuz), dann Gegenargument und Abstimmung in den Kommentaren.

Fakten (NASA New Horizons / IAU 2006):
  Pluto rund (hydrostatisches Gleichgewicht), umrundet die Sonne, 5 bekannte Monde (Charon, Styx, Nix, Kerberos, Hydra),
  Berge aus Wassereis (bis ~3,5 km), Stickstoff-Gletscher (Sputnik Planitia), duenne Atmosphaere mit blauem Dunst.
  IAU-Kriterium 3: hat seine Bahnumgebung nicht freigeraeumt (Kuiperguertel). Gegenargument (u. a. Alan Stern): auch
  die Bahnen von Erde, Mars, Jupiter und Neptun sind nicht voellig frei (erdnahe Asteroiden, Trojaner) -> als Kritik
  formuliert, nicht als Tatsache.

Hook-Varianten:
  1 "Pluto IS a planet. Change my mind." (gewaehlt)  2 "They demoted Pluto for ONE rule"  3 "Pluto passes 4 of 5 tests"
  4 "Unpopular opinion: Pluto is a planet"  5 "Count the planets. Wrong."

    python make-w11-pluto-hot-take-reel.py [--preview DIR]  ->  w11-pluto-hot-take.mp4, -cover.png
"""

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import ACC, FG, SEC
from reelkit import (body_sprite, paste_center, stext, mark, ease, header_bg, frame_save, downscale, encode,
                     cinematic)
from PIL import Image

OUT = Path(__file__).resolve().parent
NAME = "w11-pluto-hot-take"
W, H = 1080, 1920
PX, PY, PD = 540, 1090, 500           # Pluto-Mitte und Durchmesser
LIGHT = (-0.55, -0.35, 0.76)

# (Start, Zeile 1, Zeile 2, Punkt: True/False/None)
BEATS = [(0.0, "Here's my case.", "", None),
         (2.2, "It's round.", "", True),
         (4.0, "It orbits the Sun.", "", True),
         (5.8, "It has 5 moons.", "", True),
         (7.6, "Ice mountains, glaciers,", "and a blue sky.", True),
         (9.8, "It hasn't cleared its orbit.", "The one rule it breaks (2006).", False),
         (12.6, "Critics say no planet's path", "is perfectly clear. Not even Earth's.", None),
         (15.4, "So: planet or not?", "Comment PLANET or NOT", None)]
SAVE_AT = 18.0
TOTAL = 20.6


def charon_pos(t):
    a = math.radians(200 + 26 * t)                    # Umlauf (stark beschleunigt, nicht massstaeblich)
    return PX + 410 * math.cos(a), PY - 40 + 120 * math.sin(a), math.sin(a) > 0   # vorne, wenn unten


class Reel:
    def __init__(self):
        self.bg = header_bg(77, ["Pluto IS a planet.", "Change my mind."], "IS")
        self.end = downscale(frame_save(["Save it for your", "next Pluto argument"],
                                        sub="Send it to someone who still counts 9 planets"), W, H)
        self.charon = body_sprite("charon", 120, lon0=0, light=LIGHT)

    def scene(self, t):
        im = self.bg.copy()
        cx, cy, front = charon_pos(t)
        if not front:
            paste_center(im, self.charon, cx, cy)
        paste_center(im, body_sprite("pluto", PD, lon0=150 + 9 * t, light=LIGHT), PX, PY)
        if front:
            paste_center(im, self.charon, cx, cy)
        return im

    def frame(self, t):
        if t >= SAVE_AT:
            return Image.blend(self.frame(SAVE_AT - 1e-3), self.end, ease((t - SAVE_AT) / 0.35))
        im = self.scene(t)
        k = max(i for i, b in enumerate(BEATS) if t >= b[0])
        t0, l1, l2, ok = BEATS[k]
        a = ease((t - t0) / 0.3)
        col = (255, 110, 100) if ok is False else (ACC if k in (0, 7) else FG)
        stext(im, l1, 50, 560, col, a)
        stext(im, l2, 36, 628, FG if ok is not False else SEC, a)
        # Punktetafel: 5 Felder, fuellen sich mit den Argumenten
        marks = [b for b in BEATS if b[3] is not None]
        for j, b in enumerate(marks):
            x = 540 + (j - 2) * 110
            box = Image.new("RGB", (84, 84), (20, 26, 38))
            im.paste(box, (x - 42, 1440 - 42), Image.new("L", (84, 84), 150))
            if t >= b[0]:
                mark(im, x, 1440, 54, ok=b[3], a=ease((t - b[0]) / 0.25))
        stext(im, "Pluto's planet checklist", 26, 1500, SEC, 1.0, bold=False)
        stext(im, "Charon not to scale · surface: NASA New Horizons", 22, 1700, SEC, 1.0, bold=False)
        stext(im, "Send this to someone who still counts 9 planets", 34, 1740, FG, 1.0)
        return im


def main():
    r = Reel()
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (1.0, 8.5, 11.0, 13.5, 16.5, 19.5):
            cinematic(r.frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved")
        return
    encode(OUT / f"{NAME}.mp4", r.frame, TOTAL)
    cinematic(r.frame(11.0), 0).save(OUT / f"{NAME}-cover.png")
    print("cover saved")


if __name__ == "__main__":
    main()
