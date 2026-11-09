"""Woche 11, Fr 13.11.2026: "You step onto Mars without a suit." (Provokations-Format, unbequeme Wahrheit; v2).
v1 (sieben Gruende neben einem rotierenden Mars) war laut Denny "langweilig" -> v2 mit Spannungskurve und laufender Uhr:
Zoom vom All auf die Oberflaeche, eine Silhouette steht im Staub, die Uhr laeuft: 0 s Luft kocht, 15 s Bewusstlosigkeit
(Vignette schliesst sich), ~2 min vorbei. Dann "With a suit?": Raureif am Bildrand (-60 Grad C), Strahlungsspuren (100x),
Staubsturm verschluckt die Szene. Schluss: "Still want a ticket? YES or NO". Keine drastischen Bilder, nur Physik.

Fakten (NASA Mars Fact Sheet; NASA zu Vakuum-Exposition; Curiosity RAD, Hassler et al. 2014; NASA Opportunity 2018):
  Druck ~0,6 kPa = <1 % der Erde, unter der Armstrong-Grenze (6,3 kPa): freiliegende Koerperfluessigkeiten (Speichel,
  Traenenfilm) beginnen zu sieden. Bewusstlosigkeit nach ~15 s (kein Sauerstoff). Ohne Rettung toedlich nach etwa
  1-2 Minuten (Tierversuche/Unfaelle: bis ~90 s ueberlebbar). Mittel ~-60 Grad C. Oberflaechendosis ~0,64 mSv/Tag vs.
  ~2,4 mSv/Jahr Erd-Hintergrund -> ~100x. Globale Staubstuerme ueber Monate (2018, Ende von Opportunity).

Hook-Varianten:
  1 "You step onto Mars without a suit." (gewaehlt)  2 "How long would you last on Mars?"  3 "Mars gives you 15 seconds"
  4 "Mars is a terrible place to live." (v1)  5 "Here's what Mars does to you"

    python make-w11-mars-terrible-reel.py [--preview DIR]  ->  w11-mars-terrible.mp4, -cover.png
"""

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bodies import fbm
from brandkit import ACC, FG, SEC, S, fmono
from reelkit import (body_sprite, stext, ease, new_frame, header_band, frame_save, downscale, encode, cinematic)

OUT = Path(__file__).resolve().parent
NAME = "w11-mars-terrible"
W, H = 1080, 1920
HOR = 1240                      # Horizont
FEET = 1470                     # Fusslinie der Silhouette
LAND = 2.6                      # Ende des Anflugs

# (Start, Zeile 1, Zeile 2, Farbe Zeile 1)
BEATS = [(0.0, "Day 1. The door opens.", "", FG),
         (LAND, "The air is less than 1% of Earth's.", "The water in your mouth and eyes starts to boil.", FG),
         (6.2, "You pass out.", "No oxygen is reaching your brain.", (255, 120, 100)),
         (9.6, "Without help, it's over", "in about 2 minutes.", (255, 120, 100)),
         (12.4, "OK. With a suit, then.", "Average temperature: -60 °C.", ACC),
         (14.6, "Radiation:", "about 100x Earth's dose. Every day.", ACC),
         (16.8, "Dust storms can cover", "the whole planet for months.", ACC),
         (19.4, "Still want a ticket?", "Comment YES or NO", ACC)]
SAVE_AT = 22.0
TOTAL = 24.6


def clock(t):
    """Uhr auf dem Mars (Sekunden): echtzeitnah bis 15 s, dann schneller bis 2 min."""
    if t < LAND:
        return None
    if t < 6.2:
        return (t - LAND) * 1.0
    if t < 9.6:
        return 3.6 + (t - 6.2) / 3.4 * 11.4
    if t < 12.4:
        return 15 + ease((t - 9.6) / 1.6) * 105
    return None


class Reel:
    def __init__(self):
        hb = Image.new("RGB", (W * S, H * S), (0, 0, 0))
        header_band(hb, ["You step onto Mars", "without a suit."], "without")
        self.head = downscale(hb, W, H)
        self.head_m = self.head.convert("L").point(lambda v: min(255, v * 3))
        stars, _ = new_frame(23)
        self.space = downscale(stars, W, H)
        self.mars = body_sprite("mars", 900, lon0=40, light=(-0.55, -0.35, 0.76))
        self.surface = self.build_surface()
        self.dust_tex = fbm(17, h=256, w=256, octaves=5, base=3)
        self.frost = self.build_frost()
        self.end = downscale(frame_save(["Save it before you", "buy a ticket to Mars"],
                                        sub="Send it to the friend who'd move to Mars"), W, H)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        self.rad = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - 980) / (H / 2)) ** 2)

    def build_surface(self):
        ys = np.arange(H, dtype=np.float32)[:, None, None]
        sky_t = np.clip(ys / HOR, 0, 1)
        sky = np.array([118, 86, 70], np.float32) * (1 - sky_t) + np.array([214, 168, 126], np.float32) * sky_t
        img = np.broadcast_to(sky, (H, W, 3)).copy()
        n = fbm(5, h=512, w=512, octaves=6, base=6)
        n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((W, H - HOR), Image.BICUBIC), np.float32) / 255
        g = np.arange(H - HOR, dtype=np.float32)[:, None] / (H - HOR)
        ground = (np.array([150, 82, 48], np.float32) * (0.75 + 0.5 * n[..., None])
                  * (0.85 + 0.25 * g[..., None]))
        img[HOR:] = ground
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        x = np.arange(W, dtype=np.float32)
        for k, (base, amp, col) in enumerate([(HOR - 70, 40, (170, 112, 82)), (HOR - 25, 26, (152, 92, 62))]):
            ridge = base + amp * np.sin(x / (260 - 70 * k) + k) + amp * 0.5 * np.sin(x / 57 + 2 * k)
            d.polygon([(0, HOR + 2)] + [(int(i), float(ridge[i])) for i in range(0, W, 3)] + [(W, HOR + 2)], fill=col)
        rng = np.random.default_rng(9)
        for _ in range(55):                                      # Steine mit Schatten (Licht von links oben)
            ry = rng.uniform(HOR + 20, H)
            sc = 0.3 + (ry - HOR) / (H - HOR) * 1.6
            rx, rw, rh = rng.uniform(0, W), rng.uniform(10, 34) * sc, rng.uniform(6, 18) * sc
            d.ellipse([rx - rw + 6 * sc, ry - rh * 0.3, rx + rw + 12 * sc, ry + rh * 0.6], fill=(92, 46, 26))
            d.ellipse([rx - rw, ry - rh, rx + rw, ry + rh * 0.5], fill=(122, 66, 40))
            d.ellipse([rx - rw * 0.7, ry - rh * 0.9, rx + rw * 0.2, ry - rh * 0.2], fill=(176, 104, 66))
        sun = Image.new("L", (W, H), 0)                          # kleine, blasse Sonne (Mars: ~2/3 Erdgroesse)
        ImageDraw.Draw(sun).ellipse([780, 330, 806, 356], fill=255)
        im.paste((246, 240, 228), (0, 0), sun.filter(ImageFilter.GaussianBlur(3)))
        halo = Image.new("L", (W, H), 0)
        ImageDraw.Draw(halo).ellipse([733, 283, 853, 403], fill=90)
        im.paste((200, 200, 214), (0, 0), halo.filter(ImageFilter.GaussianBlur(30)))  # blauer Sonnenhof (Mars)
        self.draw_figure(d)
        return im

    @staticmethod
    def draw_figure(d):
        """Silhouette einer Person (Gegenlicht), Fuesse auf FEET, Mitte x=540."""
        c, k = (34, 20, 16), 1.0
        x, y = 540, FEET
        d.ellipse([x - 22 * k, y - 300 * k, x + 22 * k, y - 252 * k], fill=c)                 # Kopf
        d.polygon([(x - 38, y - 248), (x + 38, y - 248), (x + 30, y - 120), (x - 30, y - 120)], fill=c)  # Rumpf
        d.polygon([(x - 38, y - 244), (x - 50, y - 240), (x - 62, y - 130), (x - 48, y - 128)], fill=c)  # Arme
        d.polygon([(x + 38, y - 244), (x + 50, y - 240), (x + 62, y - 130), (x + 48, y - 128)], fill=c)
        d.polygon([(x - 30, y - 122), (x - 4, y - 122), (x - 10, y), (x - 32, y)], fill=c)          # Beine
        d.polygon([(x + 4, y - 122), (x + 30, y - 122), (x + 32, y), (x + 10, y)], fill=c)
        d.ellipse([x - 70, y - 8, x + 70, y + 10], fill=(96, 50, 30))                           # Schatten

    def build_frost(self):
        n = fbm(33, h=480, w=270, octaves=6, base=14, wrap=False)
        n = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        edge = np.minimum(np.minimum(xx, W - xx), np.minimum(yy, H - yy)) / 80.0
        return edge, n

    def scene(self, t):
        if t < LAND:                                              # Anflug: Mars waechst, Ueberblendung auf den Boden
            im = self.space.copy()
            z = 0.42 + 2.6 * ease(t / LAND) ** 2
            rgb, m = self.mars
            size = int(rgb.width * z)
            rgb2, m2 = rgb.resize((size, size), Image.BICUBIC), m.resize((size, size), Image.BICUBIC)
            im.paste(rgb2, (W // 2 - size // 2, 1000 - size // 2), m2)
            if t > LAND - 0.6:
                im = Image.blend(im, self.surface, ease((t - LAND + 0.6) / 0.6))
            im.paste(self.head, (0, 0), self.head_m)
            return im
        im = self.surface.copy()
        a = np.asarray(im, np.float32)
        if 12.4 <= t < 19.4:                                      # Raureif am Bildrand
            edge, n = self.frost
            fa = ease((t - 12.4) / 1.4) * (1 - ease((t - 16.8) / 0.8))
            m = np.clip((n * 0.9 - edge) * 4.0, 0, 1) * fa
            a = a * (1 - 0.22 * fa) + a.mean(-1, keepdims=True) * np.array([0.8, 0.92, 1.12]) * 0.22 * fa   # kalter Farbstich
            a = a * (1 - m[..., None] * 0.6) + np.array([226, 238, 248]) * m[..., None] * 0.6
        if 16.8 <= t < 20.0:                                      # Staubsturm zieht auf
            sa = ease((t - 16.8) / 1.6) * (1 - ease((t - 19.4) / 0.6))
            sh = int((t - 16.8) * 60) % 256
            dn = np.roll(self.dust_tex, sh, axis=1)
            dn = np.asarray(Image.fromarray((dn * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), np.float32) / 255
            dm = np.clip(sa * (0.55 + 0.6 * dn), 0, 0.93)
            a = a * (1 - dm[..., None]) + np.array([196, 120, 70]) * dm[..., None]
        if 6.2 <= t < 12.6:                                       # Bewusstlosigkeit: Vignette schliesst sich
            va = ease((t - 6.2) / 2.8)
            if t > 11.8:
                va *= 1 - ease((t - 11.8) / 0.8)
            v = np.clip((self.rad - (1.15 - 0.95 * va)) * 2.5, 0, 1) * va
            a = a * (1 - v[..., None] * 0.97)
        im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
        d = ImageDraw.Draw(im)
        if LAND <= t < 6.6:                                       # Blaeschen am Kopf
            rng = np.random.default_rng(int(t * 30))
            for j in range(18):
                ph = (t * 0.9 + j / 18) % 1.0
                bx = 540 + math.sin(j * 2.1) * 34 + math.sin(t * 3 + j) * 6
                by = FEET - 270 - ph * 120
                r = 2 + (j % 3)
                al = int(200 * (1 - ph))
                d.ellipse([bx - r, by - r, bx + r, by + r], outline=(240, 236, 228, al), width=2)
        if 14.6 <= t < 17.2:                                      # Strahlungsspuren
            ra = ease((t - 14.6) / 0.4) * (1 - ease((t - 16.8) / 0.4))
            rng = np.random.default_rng(int(t * 30))
            for _ in range(int(14 * ra)):
                x0, y0 = rng.uniform(0, W), rng.uniform(0, H)
                ang, ln = rng.uniform(0, math.pi), rng.uniform(40, 160)
                d.line([(x0, y0), (x0 + math.cos(ang) * ln, y0 + math.sin(ang) * ln)], fill=(220, 255, 230), width=2)
        im.paste(self.head, (0, 0), self.head_m)
        return im

    def frame(self, t):
        if t >= SAVE_AT:
            return Image.blend(self.frame(SAVE_AT - 1e-3), self.end, ease((t - SAVE_AT) / 0.35))
        im = self.scene(t)
        k = max(i for i, b in enumerate(BEATS) if t >= b[0])
        t0, l1, l2, c = BEATS[k]
        a = ease((t - t0) / 0.3)
        stext(im, l1, 46 if len(l1) > 30 else 52, 560, c, a)
        stext(im, l2, 34, 628, FG, a)
        s = clock(t)
        if s is not None:
            txt = f"{int(s) // 60}:{int(s) % 60:02d}"
            d = ImageDraw.Draw(im)
            fo = fmono(110)
            d.text(((W - d.textlength(txt, font=fo)) / 2, 720), txt, font=fo, fill=FG, stroke_width=5,
                   stroke_fill=(8, 10, 14))
            stext(im, "time on Mars", 26, 850, SEC, 1.0, bold=False)
        stext(im, "Illustration · facts: NASA, Curiosity RAD", 22, 1700, SEC, 1.0, bold=False)
        stext(im, "Send this to the friend who'd move to Mars", 34, 1740, FG, 1.0)
        return im


def main():
    r = Reel()
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (1.2, 4.0, 8.5, 11.0, 13.5, 15.5, 18.2, 20.5):
            cinematic(r.frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved")
        return
    encode(OUT / f"{NAME}.mp4", r.frame, TOTAL)
    cinematic(r.frame(4.0), 0).save(OUT / f"{NAME}-cover.png")
    print("cover saved")


if __name__ == "__main__":
    main()
