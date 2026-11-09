"""Woche 11, Mi 11.11.2026: "The Sun isn't yellow." (Provokations-Format "Du wurdest angelogen").
Animation: blauer Taghimmel mit gelber Sonne ueber Huegeln -> Kamera steigt, Himmel wird schwarz, Sterne erscheinen,
die Sonne wird weiss. Danach die Erklaerung (Streuung) und der Beweis (Schnee ist weiss).

Fakten (NASA, u. a. NASA Space Place / SDO-FAQ):
  Sonnenlicht ist ein Gemisch aller sichtbaren Farben und wirkt fuer das Auge weiss; aus dem All (ISS) sehen Astronauten
  eine weisse Sonne. Die Atmosphaere streut kurzwelliges (blaues) Licht aus dem direkten Strahl (Rayleigh-Streuung) ->
  Himmel blau, Sonnenscheibe leicht gelblich, bei tiefem Stand (laengerer Weg) orange/rot. Das Strahlungsmaximum liegt
  bei ~500 nm (blau-gruen), das Gesamtspektrum ergibt trotzdem Weiss. Snow-Argument: weisse Flaechen reflektieren das
  einfallende Licht unveraendert -> zeigen dessen Farbe.

Hook-Varianten:
  1 "The Sun isn't yellow. You were taught wrong." (gewaehlt)  2 "Every kid draws the Sun wrong"
  3 "Astronauts see a different Sun"  4 "What color is the Sun? Not yellow."  5 "Your teacher lied about the Sun"

    python make-w11-sun-not-yellow-reel.py [--preview DIR]  ->  w11-sun-not-yellow.mp4, -cover.png
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import ACC, FG, SEC, S
from reelkit import (body_sprite, paste_center, stext, ease, new_frame, header_band, frame_save, downscale, encode,
                     cinematic)

OUT = Path(__file__).resolve().parent
NAME = "w11-sun-not-yellow"
W, H = 1080, 1920
SUN_Y, SUN_D = 1080, 300
RISE0, RISE1 = 3.2, 7.4          # Aufstieg durch die Atmosphaere

BEATS = [(0.0, "What color is the Sun?", "Most people say yellow.", FG),
         (3.2, "Now leave the atmosphere.", "", FG),
         (7.4, "It's WHITE.", "That's how astronauts see it.", ACC),
         (10.2, "Air scatters blue light out of the beam.", "What's left looks yellow. At sunset, orange.", FG),
         (13.2, "Proof: snow looks white.", "It reflects sunlight's true color.", FG),
         (15.8, "So what color did you draw it?", "Comment below", ACC)]
SAVE_AT = 18.2
TOTAL = 20.8


def phase(t):
    return ease((t - RISE0) / (RISE1 - RISE0))


class Reel:
    def __init__(self):
        stars, _ = new_frame(131)
        self.stars = np.asarray(downscale(stars, W, H), np.float32)
        hb = Image.new("RGB", (W * S, H * S), (0, 0, 0))
        header_band(hb, ["The Sun isn't yellow.", "You were taught wrong."], "isn't")
        self.head = downscale(hb, W, H)
        self.head_m = self.head.convert("L").point(lambda v: min(255, v * 3))
        y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        self.day = (np.array([46, 104, 196], np.float32) * (1 - y) + np.array([150, 196, 240], np.float32) * y
                    ) * np.ones((1, W, 1), np.float32)
        ys = np.arange(H, dtype=np.float32)[:, None]
        dy = np.sqrt(((np.arange(W) - W / 2) ** 2)[None, :] + (ys - SUN_Y) ** 2)
        self.glare = np.exp(-dy / 260.0)[..., None]                      # Streulicht um die Sonne (nur im Himmel)
        sun = body_sprite("sun", SUN_D, spots=False)
        rgb = np.asarray(sun[0], np.float32)
        lum = rgb.max(-1, keepdims=True)
        self.sun_y = (Image.fromarray(np.clip(rgb * np.array([1.0, 0.80, 0.30]), 0, 255).astype(np.uint8)),
                      sun[1])
        white = lum * np.array([1.0, 0.99, 0.97]) * 1.1
        self.sun_w = (Image.fromarray(np.clip(white, 0, 255).astype(np.uint8)), sun[1])
        x = np.arange(W, dtype=np.float32)
        self.hill = 1560 + 30 * np.sin(x / 190) + 18 * np.sin(x / 63 + 0.7)
        self.end = downscale(frame_save(["Save it for the next", "kid who asks"],
                                        sub="Send it to someone who drew the Sun yellow"), W, H)

    def scene(self, t):
        p = phase(t)
        img = self.day * (1 - p) + self.stars * p + self.glare * np.array([255, 225, 140]) * 0.30 * (1 - p)
        im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        a = Image.blend(self.sun_y[0], self.sun_w[0], p)
        x0, y0 = int(W / 2 - a.width / 2), int(SUN_Y - a.height / 2)       # additiv: kein dunkler Rand im Taghimmel
        box = (x0, y0, x0 + a.width, y0 + a.height)
        im.paste(ImageChops.screen(im.crop(box), a), box)
        disc = Image.new("L", a.size, 0)                                     # Scheibe deckend in Sonnenfarbe
        r = SUN_D / 2 - 1
        ImageDraw.Draw(disc).ellipse([a.width / 2 - r, a.height / 2 - r, a.width / 2 + r, a.height / 2 + r], fill=255)
        im.paste(a, (x0, y0), disc)
        d = ImageDraw.Draw(im)
        off = p * 900                                                       # Boden faellt weg
        pts = [(0, H)] + [(int(i), float(self.hill[i] + off)) for i in range(0, W, 4)] + [(W, float(self.hill[-1] + off)), (W, H)]
        d.polygon(pts, fill=(14, 30, 22))
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
        stext(im, l2, 34, 630, FG, a)
        if t >= RISE0 and t < RISE1 + 0.6:
            alt = int(400 * phase(t) ** 2.2)
            stext(im, f"altitude {alt} km", 30, 1400, ACC, 1.0)
        stext(im, "Illustration · Sun drawn larger than in the real sky", 22, 1700, SEC, 1.0, bold=False)
        stext(im, "Send this to someone who drew the Sun yellow", 34, 1740, FG, 1.0)
        return im


def main():
    r = Reel()
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (1.0, 5.0, 8.5, 11.5, 14.0, 16.5):
            cinematic(r.frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved")
        return
    encode(OUT / f"{NAME}.mp4", r.frame, TOTAL)
    cinematic(r.frame(8.5), 0).save(OUT / f"{NAME}-cover.png")
    print("cover saved")


if __name__ == "__main__":
    main()
