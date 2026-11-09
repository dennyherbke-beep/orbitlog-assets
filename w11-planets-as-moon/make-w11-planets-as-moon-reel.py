"""Woche 11, Mo 09.11.2026: "What if planets replaced our MOON?" (Remake-Kandidat 7, docs/reel-algorithmus.md;
Vorbild astrophysicsmania DeXv8ILuMdv, 75,7K / 1,4K Shares - dort KI-Einzelbild, hier eigene Animation).
Abendhimmel nach Osten (Vollmond-Aufgang bei Sonnenuntergang: Erdschatten + Venusguertel), der Mond wird
nacheinander durch Merkur, Mars, Venus, Neptun, Jupiter, Saturn ersetzt - jeweils in 384.400 km Abstand,
Winkelgroesse massstabsgetreu (gleicher px/Grad fuer alle). Endframe: Save + Send.

Fakten (NASA Planetary Fact Sheet, Durchmesser aequatorial, km):
  Mond 3.475 · Merkur 4.879 · Mars 6.792 · Venus 12.104 · Neptun 49.528 · Jupiter 142.984 · Saturn 120.536,
  Saturn-A-Ring aussen 136.775 km Radius. Winkel = 2*atan(r/384.400). Mond 0,52 Grad, Jupiter 21 Grad, Saturn-Ringe 39 Grad.
  Faust auf Armlaenge ~10 Grad. Gezeiten/Stabilitaet: im ersten Kommentar ehrlich aufgeloest (Erde wuerde das nicht ueberstehen).

Hook-Varianten:
  1 "What if planets replaced our MOON?" (erste Fassung)  0 "Our Moon is embarrassingly SMALL" (gewaehlt 09.11., Denny: provokanter)  2 "Your sky if Jupiter were our Moon"  3 "The Moon is tiny. Watch."
  4 "Pick your Moon"  5 "Saturn at the Moon's distance would look like THIS"

    python make-w11-planets-as-moon-reel.py [--preview DIR]  ->  w11-planets-as-moon.mp4, -cover.png
"""

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bodies import planet, smooth, _ring
from brandkit import S, FG, SEC, ACC, f, downscale
from reelkit import new_frame, header_band, frame_save, encode

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
PX_DEG = 22.0                    # gleicher Massstab fuer alle Koerper
HOR_Y = 1440
CY = 1030                        # Mittelpunkt der Koerper
DIST = 384400.0
LIGHT = (0.08, 0.10, 0.99)       # Sonne knapp hinter dem Betrachter (Vollphase bei Sonnenuntergang)

# name, kind, Durchmesser km, Zeile 2, Ringe
BODIES = [("OUR MOON", "moon", 3475, "This is the real size. Tiny.", None),
          ("MERCURY", "mercury", 4879, "1.4x wider than the Moon", None),
          ("MARS", "mars", 6792, "2x wider than the Moon", None),
          ("VENUS", "venus", 12104, "3.5x wider than the Moon", None),
          ("NEPTUNE", "neptune", 49528, "14x wider than the Moon", None),
          ("JUPITER", "jupiter", 142984, "41x wider - two fists at arm's length", None),
          ("SATURN", "saturn", 120536, "Its rings would span 39 degrees of sky", 16)]
SEG = [2.6, 1.9, 1.9, 1.9, 2.1, 2.6, 3.4]       # Sekunden je Koerper
XF = 0.35                                        # Ueberblendung
END = 2.6                                        # Save-Endframe
TOTAL = sum(SEG) + END
STARTS = np.cumsum([0] + SEG[:-1])


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ang_px(diam_km):
    return 2 * math.degrees(math.atan(diam_km / 2 / DIST)) * PX_DEG


# ---------------------------------------------------------------- Szene

def sky():
    """Daemmerung nach Osten: Erdschatten (blaugrau) am Horizont, Venusguertel (rosa) darueber, oben Sterne."""
    stars, _ = new_frame(311)
    stars = np.asarray(downscale(stars, W, H), np.float32)
    ys = np.arange(H, dtype=np.float32)[:, None]
    el = (HOR_Y - ys) / PX_DEG
    zen = np.array([10, 16, 36], np.float32)
    mid = np.array([38, 52, 96], np.float32)
    img = zen + (mid - zen) * np.exp(-np.clip(el, 0, 90) / 14.0)[..., None]
    belt = np.exp(-((el - 6.0) / 4.0) ** 2)[..., None] * np.array([92, 48, 50], np.float32)
    shadow = smooth(4.5, 0.0, el)[..., None] * np.array([-10, -4, 8], np.float32)
    img = np.broadcast_to(img, (H, W, 3)) + belt + shadow
    vis = smooth(12, 35, el)[..., None]                       # Sterne erst hoeher oben sichtbar
    img = img + np.clip(stars - 14, 0, 255) * vis * 0.75
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))


def ground():
    """Huegel + Baumreihe + Ortslichter als RGBA-Ebene (liegt vor den Koerpern)."""
    rng = np.random.default_rng(7)
    x = np.arange(W, dtype=np.float32)
    hill = HOR_Y + 30 + 16 * np.sin(x / 230) + 9 * np.sin(x / 71 + 1.1)
    trees = np.zeros(W, np.float32)
    for _ in range(60):
        c, w, h = rng.uniform(0, W), rng.uniform(10, 34), rng.uniform(16, 58)
        trees = np.maximum(trees, h * np.clip(1 - np.abs(x - c) / w, 0, 1) ** 0.8)
    edge = hill - trees
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    d.polygon([(0, H)] + [(int(i), float(edge[i])) for i in range(0, W, 2)] + [(W, float(edge[-1])), (W, H)],
              fill=(8, 10, 15, 255))
    for _ in range(40):
        lx = rng.uniform(0, W)
        ly = hill[int(lx)] + rng.uniform(16, 80)
        r = rng.uniform(0.8, 1.7)
        d.ellipse([lx - r, ly - r, lx + r, ly + r], fill=(255, 198, 125, 255))
    return lay


def sprite(kind, diam_km, ring):
    """Koerper einmal rendern -> (RGB, Maske) in Ausgabe-px. Leichte Dunst-Toenung wie tief am Himmel."""
    d = ang_px(diam_km)
    box = int(max(d * (2.6 if ring else 1.5), 40)) // 2 * 2
    img = Image.new("RGB", (box * S, box * S), (0, 0, 0))
    c = box * S // 2
    # Ringe separat: bei Vollphase (Sonne hinter dem Betrachter) liegt der Ringschatten verdeckt hinter der
    # Kugel; das Schattenband aus bodies._ring wuerde hier eine falsche Luecke zeichnen -> Schatten aus.
    if ring:
        _ring(img, c, c, int(d * S) // 2, ring, (0.0, -1.0, 0.0), back=True)
    planet(img, c, c, d, kind, light=LIGHT, lon0=0 if kind == "moon" else 180)
    if ring:
        _ring(img, c, c, int(d * S) // 2, ring, (0.0, -1.0, 0.0), back=False)
    sm = downscale(img, box, box)
    a = np.asarray(sm, np.float32) * np.array([1.0, 0.95, 0.88]) * (1.35 if d < 40 else 1.0)
    mask = sm.convert("L").point(lambda v: min(255, v * 4))
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)), mask


# ---------------------------------------------------------------- Frames

class Reel:
    def __init__(self):
        base = sky()
        hb, _ = new_frame(0)
        hb = Image.new("RGB", hb.size, (0, 0, 0))
        header_band(hb, ["Our Moon is", "embarrassingly SMALL"], "SMALL")
        self.head = downscale(hb, W, H)
        self.head_mask = self.head.convert("L").point(lambda v: min(255, v * 3))
        self.base = base
        self.ground = ground()
        self.sprites = [sprite(k, dk, rg) for _, k, dk, _, rg in BODIES]
        self.moon_px = ang_px(3475)
        self.end = downscale(frame_save(["Save it for the", "next full Moon"],
                                        sub="Send it to someone who'd pick Saturn"), W, H)

    def scene(self, i, t_local):
        im = self.base.copy()
        spr, m = self.sprites[i]
        rise = 26 * t_local                                    # langsames Aufsteigen
        im.paste(spr, (int(W / 2 - spr.width / 2), int(CY - rise - spr.height / 2)), m)
        im.paste(self.ground, (0, 0), self.ground)
        im.paste(self.head, (0, 0), self.head_mask)
        return im

    def text(self, im, i, a, t_local=0.0):
        if a <= 0.01:
            return im
        base = im.copy()
        a_out, a = a, 1.0
        d = ImageDraw.Draw(im)
        st = dict(stroke_width=4, stroke_fill=(8, 10, 14))
        name, _, _, sub, _ = BODIES[i]
        c = lambda col: tuple(int(v * a) for v in col)
        fo = f(64, bold=True)
        d.text(((W - d.textlength(name, font=fo)) / 2, 560), name, font=fo, fill=c(ACC), **st)
        fo2 = f(36, bold=True)
        d.text(((W - d.textlength(sub, font=fo2)) / 2, 640), sub, font=fo2, fill=c(FG), **st)
        if i == 0:                                             # Markierung um den winzigen Mond
            r = 34
            y = CY - 26 * t_local
            d.ellipse([W / 2 - r, y - r, W / 2 + r, y + r], outline=c(ACC), width=3)
        # Vergleichsmassstab unten links: Mond in gleicher Groesse
        if i > 0:
            fo3 = f(26, bold=True)
            d.text((60, 1560), "Moon at the same scale:", font=fo3, fill=SEC, **st)
            mx = 60 + d.textlength("Moon at the same scale:", font=fo3) + 22
            r = self.moon_px / 2
            d.ellipse([mx - r, 1576 - r, mx + r, 1576 + r], fill=(222, 218, 206))
        return Image.blend(base, im, a_out) if a_out < 1 else im

    def frame(self, t):
        if t >= sum(SEG):
            a = ease((t - sum(SEG)) / XF)
            last = self.frame(sum(SEG) - 1e-3)
            return Image.blend(last, self.end, a)
        i = int(np.searchsorted(STARTS, t, side="right") - 1)
        tl = t - STARTS[i]
        im = self.scene(i, tl)
        if i > 0 and tl < XF:                                  # Ueberblendung vom vorigen Koerper (ohne Text)
            im = Image.blend(self.scene(i - 1, SEG[i - 1]), im, ease(tl / XF))
        im = self.text(im, i, ease((tl - (XF if i else 0)) / 0.25), tl)
        d = ImageDraw.Draw(im)
        st = dict(stroke_width=4, stroke_fill=(8, 10, 14))
        note = "Each at the Moon's distance (384,400 km) · sizes to scale · illustration"
        d.text(((W - d.textlength(note, font=f(22))) / 2, 1700), note, font=f(22), fill=SEC, **st)
        cta = "Send this to someone who'd pick Saturn"
        d.text(((W - d.textlength(cta, font=f(34, bold=True))) / 2, 1740), cta, font=f(34, bold=True), fill=FG, **st)
        return im


def main():
    r = Reel()
    if "--preview" in sys.argv:
        from reelkit import cinematic
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (1.5, 4.5, 8.5, 10.6, 12.6, 15.5, 17.3):
            cinematic(r.frame(t), 0).save(prev / f"pam-{t:04.1f}.png")
        print("preview saved")
        return
    encode(OUT / "w11-planets-as-moon.mp4", r.frame, TOTAL)
    from reelkit import cinematic
    cinematic(r.frame(15.5), 0).save(OUT / "w11-planets-as-moon-cover.png")
    print("cover saved")


if __name__ == "__main__":
    main()
