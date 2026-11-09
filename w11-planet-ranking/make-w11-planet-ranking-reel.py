"""Woche 11, Do 12.11.2026: "Best planet to live on: Mars is NOT #1" (Provokations-Format, streitbares Ranking).
Countdown #7 -> #1 der Planeten ausser der Erde, jeder Koerper dreht sich gross in der Mitte; #1 ist die Venus -
nicht die Oberflaeche, sondern ~50 km hoch in der Atmosphaere.

Fakten (NASA Planetary Fact Sheets, NASA Langley HAVOC-Studie 2014/15, MESSENGER):
  Jupiter: kein fester Boden, ~2,5 g an der Wolkenobergrenze, starke Strahlungsguertel. Saturn: kein Boden, Winde bis
  ~1.800 km/h. Neptun: ~-200 Grad C an der Wolkenobergrenze, schnellste Winde (~2.000 km/h). Uranus: ~-220 Grad C (kaelteste
  Planetenatmosphaere), 84-Jahre-Umlauf mit 98 Grad Neigung -> jeder Pol ~42 Jahre Dunkelheit. Merkur: ~430 Grad C Tag,
  ~-180 Grad C Nacht, Wassereis in dauerhaft beschatteten Polkratern (MESSENGER). Mars: Mittel ~-60 Grad C, Druck <1 % der
  Erde, hohe Strahlung an der Oberflaeche. Venus: Oberflaeche ~465 Grad C, 92 bar; in ~50-55 km Hoehe ~1 bar und
  ~0-50 Grad C, Schwerkraft 0,9 g; Luft (N2/O2) ist in CO2 ein Traggas -> Habitat wuerde schweben (HAVOC-Konzept).
  Schwefelsaeure-Wolken -> im ersten Kommentar genannt.

Hook-Varianten:
  1 "Best planet to live on: Mars is NOT #1" (gewaehlt)  2 "Ranking every planet you could live on"
  3 "Everyone says Mars. Everyone is wrong."  4 "The best place to live in space is hell's attic"  5 "#1 will annoy Elon fans" (verworfen: Person)

    python make-w11-planet-ranking-reel.py [--preview DIR]  ->  w11-planet-ranking.mp4, -cover.png
"""

import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import ACC, FG, SEC
from reelkit import (body_sprite, paste_center, stext, ease, header_bg, frame_save, downscale, encode, cinematic)

OUT = Path(__file__).resolve().parent
NAME = "w11-planet-ranking"
W, H = 1080, 1920
CY = 1060
LIGHT = (-0.55, -0.35, 0.76)
XF = 0.3

# (Start, Rang, Name, kind, Durchmesser, Ringneigung, Zeile 1, Zeile 2)
ITEMS = [(0.0, 7, "JUPITER", "jupiter", 440, None, "No ground to stand on.", "2.5x gravity, lethal radiation."),
         (2.0, 6, "SATURN", "saturn", 330, 18, "No ground either.", "Winds up to 1,800 km/h."),
         (4.0, 5, "NEPTUNE", "neptune", 420, None, "Around -200 °C.", "The fastest winds in the solar system."),
         (6.0, 4, "URANUS", "uranus", 420, None, "Around -220 °C.", "Each pole gets 42 years of night."),
         (8.0, 3, "MERCURY", "mercury", 420, None, "430 °C by day, -180 °C at night.", "But there's ice in its polar craters."),
         (10.0, 2, "MARS", "mars", 440, None, "-60 °C, almost no air, radiation.", "Livable only in sealed habitats."),
         (12.4, 1, "VENUS", "venus", 460, None, "The surface is 465 °C. Don't land.", "But 50 km up: Earth-like air pressure, 0-50 °C."),
         (15.4, 1, "VENUS", "venus", 460, None, "A balloon full of breathable air", "would float there. NASA studied cloud cities.")]
SAVE_AT = 18.4
TOTAL = 21.0


class Reel:
    def __init__(self):
        self.bg = header_bg(91, ["Best planet to live on:", "Mars is NOT #1"], "NOT #1")
        self.end = downscale(frame_save(["Save it for the next", "'let's move to Mars' talk"],
                                        sub="Send it to someone who'd pick Mars"), W, H)

    def body(self, i, t):
        _, _, _, kind, d, ring, _, _ = ITEMS[i]
        return body_sprite(kind, d, lon0=120 + 10 * t, light=LIGHT, ring_tilt=ring)

    def frame(self, t):
        if t >= SAVE_AT:
            return Image.blend(self.frame(SAVE_AT - 1e-3), self.end, ease((t - SAVE_AT) / 0.35))
        i = max(j for j, it in enumerate(ITEMS) if t >= it[0])
        t0, rank, name, kind, *_ , l1, l2 = ITEMS[i]
        im = self.bg.copy()
        new_body = i == 0 or ITEMS[i - 1][3] != kind
        paste_center(im, self.body(i, t), W / 2, CY)
        if new_body and i > 0 and t - t0 < XF:
            prev = self.bg.copy()
            paste_center(prev, self.body(i - 1, t), W / 2, CY)
            im = Image.blend(prev, im, ease((t - t0) / XF))
        a = ease((t - t0) / 0.25) if new_body else 1.0
        stext(im, f"#{rank}", 96 if rank > 1 else 120, 540, ACC, a)
        stext(im, name, 52, 670 if rank > 1 else 690, FG, a)
        b = ease((t - t0) / 0.3)
        stext(im, l1, 40, 1350, (255, 120, 100) if "Don't" in l1 else FG, b)
        stext(im, l2, 34, 1404, FG, b)
        if t >= 15.4:
            stext(im, "Agree? Comment your #1", 40, 1500, ACC, ease((t - 15.6) / 0.3))
        stext(im, "Earth excluded · planet maps: NASA, Mercury: Solar System Scope (CC BY 4.0)", 22, 1700, SEC, 1.0,
              bold=False)
        stext(im, "Send this to someone who'd pick Mars", 34, 1740, FG, 1.0)
        return im


def main():
    r = Reel()
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (1.0, 3.0, 7.0, 9.0, 11.0, 13.5, 16.5):
            cinematic(r.frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved")
        return
    encode(OUT / f"{NAME}.mp4", r.frame, TOTAL)
    cinematic(r.frame(13.5), 0).save(OUT / f"{NAME}-cover.png")
    print("cover saved")


if __name__ == "__main__":
    main()
