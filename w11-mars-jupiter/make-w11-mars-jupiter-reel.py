"""Woche 11, Sa 14.11.2026: Mars-Jupiter-Begegnung (Termin + Handlung; 12.11.: 2-s-Einstieg mit Planetenkugeln, Provokations-Hook "Most people will sleep through THIS").
Berechneter Morgenhimmel nach Sueden (50 Grad N, Mo 16.11., 05 UT): Jupiter + Mars als Lichtpunkte, Regulus, Algieba,
Baumgrenze. Dann Zoom (echter Winkelmassstab, Sterngrenze steigt) bis ins Fernglas-Sichtfeld (7 Grad): beide Planeten
im selben Bild, Jupiter mit vier Lichtpunkten (Galileische Monde, Stellung illustrativ).

Himmelsdaten (astropy 8.0.2, builtin-Ephemeriden, 09.11.2026):
  Minimum 1,19 Grad am 16.11. ~03 UT. 14.-18.11.: 1,19-1,42 Grad. 16.11. 05 UT, 50 N/10 E: Jupiter alt 53,0 az 166,8;
  Mars alt 54,0 az 165,9 (links oberhalb); Regulus alt 50,5 az 161,1; Algieba alt 57,4 az 153,0; Sonne -15 Grad; Mond
  unter dem Horizont. New York 10 UT (5 Uhr EST): Jupiter alt 59, az 147, Abstand 1,2 Grad. Jupiter geht ~22:30 MEZ auf.

Hook-Varianten:
  1 "Most people will sleep through THIS" (gewaehlt)  2 "Monday 5 a.m.: two planets, one view"
  3 "Mars and Jupiter meet on Monday"  4 "Set an alarm. Seriously."  5 "Grab binoculars on Monday"

    python make-w11-mars-jupiter-reel.py [--preview DIR]  ->  w11-mars-jupiter.mp4, -cover.png
"""

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import ACC, FG, SEC, S
from reelkit import stext, ease, header_band, frame_save, downscale, encode, cinematic, new_frame, body_sprite, paste_center

OUT = Path(__file__).resolve().parent
NAME = "w11-mars-jupiter"
W, H = 1080, 1920
Y0 = 1050                                        # Bildschirm-y der Blickmitte
JUP = (53.0, 166.8)                              # (alt, az)
MARS = (54.05, 165.9)
REGULUS = (50.5, 161.1)
ALGIEBA = (57.4, 153.0)
T_JUP, T_MARS = 1.8, 3.4                         # 12.11.: Mittelteil verdichtet (Denny: zu lang)
ZOOM0, ZOOM1 = 7.0, 8.8
SAVE_AT = 14.2
TOTAL = 16.8
INTRO, XF = 2.0, 0.4                             # 12.11.: Einstieg mit beiden Planeten als Kugeln (erstes Bild zaehlt)

BEATS = [(0.0, "Monday, Nov 16 · before sunrise", "Look SOUTH, about halfway up.", FG),
         (T_JUP, "The brightest dot: JUPITER.", "", FG),
         (T_MARS, "The orange one just above: MARS.", "", FG),
         (5.0, "Only 1.2° apart.", "About a pinky's width at arm's length.", ACC),
         (ZOOM0, "Now grab binoculars.", "", FG),
         (ZOOM1 + 0.2, "Both planets in ONE view.", "Those dots next to Jupiter are its moons.", ACC),
         (11.8, "Best: 5-6 a.m. Monday.", "Sat to Wed mornings work too.", ACC)]


def view(t):
    """Massstab k (px/Grad) und Blickmitte (alt, az) je Zeitpunkt."""
    z = ease((t - ZOOM0) / (ZOOM1 - ZOOM0))
    k = 14 * (150 / 14) ** z
    # Zoom um das Planetenpaar: dessen Bildposition wandert linear von der Weitwinkel-Lage in die Mitte
    c = math.cos(math.radians(53.6))
    y_w, x_w = Y0 - (53.6 - 38.0) * 14, W / 2 + (166.3 - 164.0) * c * 14
    y_t, x_t = y_w + (Y0 - y_w) * z, x_w + (W / 2 - x_w) * z
    alt0 = 53.6 - (Y0 - y_t) / k
    az0 = 166.3 - (x_t - W / 2) / (c * k)
    return k, alt0, az0


def proj(p, k, alt0, az0):
    alt, az = p
    return W / 2 + (az - az0) * math.cos(math.radians(alt)) * k, Y0 - (alt - alt0) * k


class Reel:
    def __init__(self):
        rng = np.random.default_rng(16)
        n = 12000
        self.st_alt = np.degrees(np.arcsin(rng.uniform(0, 1, n))) * 0.98            # gleichmaessig auf der Halbkugel
        self.st_az = rng.uniform(100, 230, n)
        self.st_mag = np.clip(9.5 + np.log10(rng.uniform(1e-6, 1, n)) / 0.35, 0.5, 9.5)  # Potenzgesetz: wenige helle
        self.st_col = rng.choice([(255, 236, 214), (226, 232, 255), (255, 250, 244), (255, 214, 180)], n)
        hb = Image.new("RGB", (W * S, H * S), (0, 0, 0))
        header_band(hb, ["Most people will", "sleep through THIS"], "THIS")
        self.head = downscale(hb, W, H)
        self.head_m = self.head.convert("L").point(lambda v: min(255, v * 3))
        x = np.arange(W + 400, dtype=np.float32)
        r2 = np.random.default_rng(3)
        trees = np.zeros_like(x)
        for _ in range(110):
            c, w, h = r2.uniform(0, W + 400), r2.uniform(8, 30), r2.uniform(14, 70)
            trees = np.maximum(trees, h * np.clip(1 - np.abs(x - c) / w, 0, 1) ** 0.8)
        self.ridge = 18 * np.sin(x / 210) + 9 * np.sin(x / 63 + 1.3) + trees
        ys = np.arange(H, dtype=np.float32)[:, None]
        self.ys = ys
        sky, _ = new_frame(41)
        self.intro_bg = downscale(sky, W, H)
        # scheinbare Groessen 16.11.: Jupiter ~43" (4,6 AE), Mars ~9" (1,0 AE) -> Verhaeltnis ~4,6; Licht von Osten = links
        self.jup = body_sprite("jupiter", 500, lon0=200, light=(-0.25, -0.05, 0.96))
        self.mars = body_sprite("mars", 109, lon0=60, light=(-0.45, -0.10, 0.88))
        self.end = downscale(frame_save(["Save it for", "Monday, 5 a.m."],
                                        sub="Send it to the friend who'd get up with you"), W, H)

    def sky(self, k, alt0):
        alt = alt0 + (Y0 - self.ys) / k                                              # Hoehe je Bildzeile
        zen = np.array([6, 9, 22], np.float32)
        low = np.array([22, 30, 58], np.float32)
        img = zen + (low - zen) * np.exp(-np.clip(alt, 0, 90) / 18)[..., None]
        img = np.broadcast_to(img[:, None, :] if img.ndim == 2 else img, (H, 1, 3))
        return np.repeat(img.reshape(H, 1, 3), W, axis=1).astype(np.float32)

    def stars(self, im, k, alt0, az0, lim):
        x = W / 2 + (self.st_az - az0) * np.cos(np.radians(self.st_alt)) * k
        y = Y0 - (self.st_alt - alt0) * k
        sel = (x > -5) & (x < W + 5) & (y > -5) & (y < H + 5) & (self.st_mag < lim)
        d = ImageDraw.Draw(im)
        for xi, yi, m, c in zip(x[sel], y[sel], self.st_mag[sel], self.st_col[sel]):
            b = np.clip((lim - m) / 3.0, 0.15, 1.0)
            r = 0.6 + 1.6 * np.clip((lim - 1.5 - m) / 4, 0, 1)
            col = tuple(int(v * b) for v in c)
            d.ellipse([xi - r, yi - r, xi + r, yi + r], fill=col)

    @staticmethod
    def point(im, x, y, core, col, glow):
        g = Image.new("L", im.size, 0)
        ImageDraw.Draw(g).ellipse([x - glow, y - glow, x + glow, y + glow], fill=150)
        g = g.filter(ImageFilter.GaussianBlur(glow * 0.45))
        im.paste(col, (0, 0), g)
        d = ImageDraw.Draw(im)
        d.ellipse([x - core, y - core, x + core, y + core], fill=(255, 252, 244) if col[2] > 150 else col)

    def scene(self, t):
        k, alt0, az0 = view(t)
        im = Image.fromarray(np.clip(self.sky(k, alt0), 0, 255).astype(np.uint8))
        z = ease((t - ZOOM0) / (ZOOM1 - ZOOM0))
        self.stars(im, k, alt0, az0, lim=4.6 + 3.6 * z)
        for p, core, col, glow in [(REGULUS, 2.2, (214, 226, 255), 9), (ALGIEBA, 1.8, (255, 220, 180), 7)]:
            self.point(im, *proj(p, k, alt0, az0), core, col, glow)
        jx, jy = proj(JUP, k, alt0, az0)
        mx, my = proj(MARS, k, alt0, az0)
        self.point(im, mx, my, 3.2 + 2 * z, (255, 150, 90), 14)
        self.point(im, jx, jy, 4.4 - 1.2 * z, (255, 244, 222), 24 - 14 * z)
        if z > 0.6:                                                                   # Galileische Monde (illustrativ)
            d = ImageDraw.Draw(im)
            a = int(255 * ease((z - 0.6) / 0.4))
            for off in (-0.15, -0.08, 0.05, 0.12):
                ox = jx + off * k
                d.ellipse([ox - 2.4, jy - 2.4, ox + 2.4, jy + 2.4], fill=(a, a, int(a * 0.95)))
        hor = Y0 + alt0 * k                                                           # Baumgrenze
        if hor < H + 80:
            d = ImageDraw.Draw(im)
            off = int((az0 - 164.0) * k) % 400
            pts = [(0, H)] + [(i, float(hor - self.ridge[i + off] * (k / 14))) for i in range(0, W, 3)] + [(W, H)]
            d.polygon(pts, fill=(5, 7, 10))
        if z > 0:                                                                     # Fernglas-Kreis (7 Grad)
            rad = 3.5 * k
            m = Image.new("L", im.size, 0)
            ImageDraw.Draw(m).ellipse([W / 2 - rad, Y0 - rad, W / 2 + rad, Y0 + rad], fill=255)
            m = m.filter(ImageFilter.GaussianBlur(6))
            dark = Image.new("RGB", im.size, (2, 3, 6))
            im = Image.composite(im, Image.blend(im, dark, 0.92 * ease((z - 0.55) / 0.45)), m)
        im.paste(self.head, (0, 0), self.head_m)
        return im, (jx, jy), (mx, my), k

    def intro(self, t):
        """Einstieg: Mars (links oben, wie am Himmel) und Jupiter als Kugeln, vergroessert, langsamer Zoom."""
        z = 1 + 0.05 * t / INTRO
        im = self.intro_bg.copy()
        for spr, x, y in [(self.mars, 330, 900), (self.jup, 640, 1210)]:
            rgb, m = spr
            sz = (int(rgb.width * z), int(rgb.height * z))
            paste_center(im, (rgb.resize(sz, Image.BICUBIC), m.resize(sz, Image.BICUBIC)),
                         W / 2 + (x - W / 2) * z, 1050 + (y - 1050) * z)
        im.paste(self.head, (0, 0), self.head_m)
        stext(im, "Mars meets Jupiter", 50, 560, ACC)
        stext(im, "Monday morning, Nov 16", 34, 628, FG)
        stext(im, "Mars", 34, 800, (255, 170, 120))
        stext(im, "Jupiter", 34, 1490, FG)
        stext(im, "Illustration · both enlarged, true size ratio", 22, 1700, SEC, bold=False)
        stext(im, "Send this to the friend who'd get up with you", 34, 1740, FG)
        return im

    def reel_frame(self, t):
        """Gesamtablauf: Einstieg (INTRO s), dann der bisherige Ablauf ab 0."""
        if t < INTRO - XF:
            return self.intro(t)
        if t < INTRO:
            return Image.blend(self.intro(t), self.frame(0.0), ease((t - INTRO + XF) / XF))
        return self.frame(t - INTRO)

    def frame(self, t):
        if t >= SAVE_AT:
            return Image.blend(self.frame(SAVE_AT - 1e-3), self.end, ease((t - SAVE_AT) / 0.35))
        im, (jx, jy), (mx, my), k = self.scene(t)
        d = ImageDraw.Draw(im)
        st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
        if T_JUP <= t < ZOOM0:                                                        # Beschriftungen
            a = ease((t - T_JUP) / 0.3)
            c = tuple(int(v * a) for v in FG)
            d.line([(jx + 14, jy + 8), (jx + 120, jy + 70)], fill=c, width=2)
            d.text((jx + 126, jy + 56), "Jupiter", font=_f(32), fill=c, **st)
        if T_MARS <= t < ZOOM0:
            a = ease((t - T_MARS) / 0.3)
            c = tuple(int(v * a) for v in (255, 170, 120))
            d.line([(mx - 4, my - 8), (mx + 30, my - 110)], fill=c, width=2)
            d.text((mx + 4, my - 156), "Mars", font=_f(32), fill=c, **st)
            rx, ry = proj(REGULUS, k, *view(t)[1:])
            d.text((rx - 70, ry + 14), "Regulus", font=_f(24, False), fill=tuple(int(v * a) for v in SEC), **st)
        if t >= ZOOM1:
            a = ease((t - ZOOM1) / 0.4)
            d.text((jx + 40, jy + 30), "Jupiter + moons", font=_f(30), fill=tuple(int(v * a) for v in FG), **st)
            d.text((mx - 150, my - 60), "Mars", font=_f(30), fill=tuple(int(v * a) for v in (255, 170, 120)), **st)
        if t < ZOOM0:
            d.text((W / 2 - 14, Y0 + view(t)[1] * 14 - 10), "S", font=_f(40), fill=ACC, **st)
        k_, t0l, l1, l2, c = None, *max((b for b in BEATS if t >= b[0]), key=lambda b: b[0])
        a = ease((t - t0l) / 0.3)
        stext(im, l1, 46 if len(l1) > 28 else 50, 560, c, a)
        stext(im, l2, 34, 628, FG, a)
        stext(im, "Sky computed for 50° N, Nov 16, 6 a.m. · moon positions illustrative", 22, 1700, SEC, 1.0,
              bold=False)
        stext(im, "Send this to the friend who'd get up with you", 34, 1740, FG, 1.0)
        return im


def _f(px, bold=True):
    from brandkit import f
    return f(px, bold=bold)


def main():
    r = Reel()
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (0.0, 2.5, 6.0, 8.0, 10.5, 14.5):
            cinematic(r.reel_frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved")
        return
    encode(OUT / f"{NAME}.mp4", r.reel_frame, TOTAL + INTRO)
    cinematic(r.intro(1.0), 0).save(OUT / f"{NAME}-cover.png")
    print("cover saved")


if __name__ == "__main__":
    main()
