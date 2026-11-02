"""Woche 10, Dienstag 03.11.2026 - "REAL photo or FAKE?" (Empfaenger: Freunde herausfordern).

5 Bilder, je 1,9 s raten mit ablaufendem Balken, dann Stempel + ein Satz Aufloesung. 3 echte Fotos, die falsch
aussehen, 2 eigene Renderings, die im Reel offen als solche aufgeloest werden. Echte Fotos unbearbeitet (nur
Beschnitt/Zoom), Credit erst mit der Aufloesung sichtbar, damit er die Antwort nicht verraet.

Hook-Varianten:
  1. REAL photo or FAKE? Bet you can't get 5/5              <- gewaehlt (Herausforderung)
  2. 3 of these are real. Can you spot them?
  3. These space photos look fake. Some are.
  4. Only one of these is impossible
  5. Test your space eyes

Fakten: Hyperion PIA14580 (Cassini, 16.09.2011) · Mars-Sonnenuntergang PIA19400 (Curiosity, Sol 956, 15.04.2015,
Farbe kalibriert) · Mimas PIA12570 (Cassini, naechster Vorbeiflug 2010; Herschel ~130 km bei ~396 km Durchmesser).
Mars hat heute keine fluessigen Ozeane; ein urzeitlicher Nordozean wird diskutiert. Jupiter hat reale, aber sehr
schwache Staubringe.

    python make-w10-real-or-fake-reel.py  ->  w10-real-or-fake.mp4, -cover.png
    CHECK_DIR=... CHECK_ONLY=1            ->  nur Schluesselbilder
"""

import math
import os
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import bodies
from bodies import fbm, planet, smooth, texture
from brandkit import S, FG, SEC, ACC, f, downscale, canvas
from reelkit import W as CW, H as CH, deep_sky, header_band, cinematic

OUT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
T_GUESS, T_REVEAL, T_END = 1.9, 1.6, 3.0
LOOP = 5 * (T_GUESS + T_REVEAL) + T_END
PW, PH, PX, PY = 960, 840, 60, 520               # Bildflaeche
GREEN, RED = (96, 226, 150), (255, 92, 92)


def fit_photo(name, cover=False, focus=(0.5, 0.5), crop=None):
    im = Image.open(OUT / name).convert("RGB")
    if crop:                                                          # Motiv naeher holen (nur Beschnitt)
        im = im.crop([int(c * s) for c, s in zip(crop, im.size + im.size)])
    k = (max if cover else min)(PW * 1.1 / im.width, PH * 1.1 / im.height)
    im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
    out = Image.new("RGB", (int(PW * 1.1), int(PH * 1.1)), (0, 0, 0))
    out.paste(im, (int((out.width - im.width) * focus[0]), int((out.height - im.height) * focus[1])))
    return out


def fake_base(seed):
    img, _ = canvas(int(PW * 1.1 * S), int(PH * 1.1 * S))
    deep_sky(img, seed, n=1500, band=None)
    return img


def fake_mars():
    """Mars-Karte mit erfundenem Nordozean, Wolken und Atmosphaere. Bewusst plausibel, im Reel als Fake aufgeloest."""
    tex, meta = texture("mars")
    th, tw = tex.shape[:2]
    lat = np.linspace(90, -90, th)[:, None] * np.ones((1, tw), np.float32)
    n = 0.45 * fbm(31, th, tw, octaves=7, base=6) + 0.55 * fbm(33, th, tw, octaves=8, base=18, persistence=0.62)
    coast = (lat + (n - 0.5) * 95 - 14) / 90
    sea = smooth(0.0, 0.012, coast)
    depth = smooth(0.0, 0.32, coast)[..., None]
    water = np.array([34, 86, 132], np.float32) * (1 - depth) + np.array([10, 34, 78], np.float32) * depth
    t = (tex * np.array([0.86, 0.80, 0.78], np.float32)) * (1 - sea[..., None]) + water * sea[..., None]
    clouds = smooth(0.56, 0.74, fbm(32, th, tw, octaves=8, base=10, persistence=0.6))[..., None] * 0.68
    cap = smooth(68, 80, lat + (n - 0.5) * 14)[..., None]
    t = t * (1 - clouds) + 240 * clouds
    t = t * (1 - cap) + 244 * cap
    bodies._TEX["fake_mars"] = (t.astype(np.float32), dict(meta, atmo=(120, 170, 235), atmo_k=0.8, spec=0.22, ocean=sea.astype(np.float32)))
    img = fake_base(41)
    planet(img, img.width // 2, img.height // 2, 800, "fake_mars", lon0=70, tilt=-6, light=(-0.6, -0.42, 0.68))
    return downscale(img, int(PW * 1.1), int(PH * 1.1))


def fake_jupiter():
    img = fake_base(42)
    planet(img, img.width // 2, img.height // 2, 420, "jupiter", lon0=150, tilt=8, ring_tilt=16, light=(-0.62, -0.35, 0.70))
    return downscale(img, int(PW * 1.1), int(PH * 1.1))


ITEMS = [
    (fit_photo("PIA14580.jpg", cover=True, crop=(0.2, 0.2, 0.8, 0.8)), True, "A moon that looks like a sponge",
     "Hyperion, a moon of Saturn. Cassini, 2011.", "Photo: NASA/JPL-Caltech/Space Science Institute"),
    (fake_mars(), False, "An ocean on Mars, seen from orbit",
     "We rendered this. Mars has no liquid oceans today.", "Render: Orbit Log, Mars map: NASA"),
    (fit_photo("PIA19400.jpg", cover=True, focus=(0.3, 0.72)), True, "A blue sunset on Mars",
     "Curiosity rover, 2015. Mars dust lets blue light through.", "Photo: NASA/JPL-Caltech/MSSS/Texas A&M Univ."),
    (fake_jupiter(), False, "Jupiter's giant bright rings",
     "We rendered this. Jupiter's real rings are faint dust.", "Render: Orbit Log, Jupiter map: NASA"),
    (fit_photo("PIA12570.jpg"), True, "A moon with a crater a third its width",
     "Mimas, a moon of Saturn. Cassini, 2010.", "Photo: NASA/JPL-Caltech/Space Science Institute"),
]
MASK = Image.new("L", (PW, PH), 0)
ImageDraw.Draw(MASK).rounded_rectangle([0, 0, PW - 1, PH - 1], 22, fill=255)


def stamp(text, col):
    fo = f(170, bold=True)
    tmp = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = int(tmp.textlength(text, font=fo))
    im = Image.new("RGBA", (tw + 120, 300), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([14, 30, im.width - 15, 270], 26, fill=(6, 8, 12, 150), outline=col + (255,), width=12)
    d.text((60, 30), text, font=fo, fill=col + (255,))
    return im.rotate(-7, expand=True, resample=Image.BICUBIC)


STAMP = {True: stamp("REAL", GREEN), False: stamp("FAKE", RED)}


def background():
    img, _ = canvas(CW, CH)
    deep_sky(img, 77, band=(0.2, 0.62))
    shade = Image.new("L", img.size, 0)
    ImageDraw.Draw(shade).rectangle([0, 0, CW, CH], fill=135)
    img.paste(Image.new("RGB", img.size, (5, 7, 12)), (0, 0), shade)
    header_band(img, ["REAL photo or FAKE?", "Bet you can't get 5/5"], "FAKE", y=236 * S)
    return downscale(img, W, H)


BG = background()


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def back_out(x):
    x = min(1.0, max(0.0, x)) - 1
    return 1 + 2.4 * x ** 3 + 1.4 * x ** 2


def centered(d, y, s, fo, fill):
    d.text(((W - d.textlength(s, font=fo)) / 2, y), s, font=fo, fill=fill)


def frame(t):
    im = BG.copy()
    d = ImageDraw.Draw(im)
    per = T_GUESS + T_REVEAL
    if t >= 5 * per:                                                   # Endkarte
        u = t - 5 * per
        al = ease(u / 0.3)
        k = lambda c: tuple(int(v * al) for v in c)
        centered(d, 640, "Your score?", f(92, bold=True), k(FG))
        centered(d, 760, "3 real. 2 fake.", f(54), k(ACC))
        centered(d, 900, "The real ones looked the most fake.", f(40), k(SEC))
        centered(d, 1130, "Send this to someone who", f(50, bold=True), k(FG))
        centered(d, 1192, "thinks they'd get 5/5", f(50, bold=True), k(FG))
        centered(d, 1284, "Save it to test your friends", f(38), k(ACC))
        return im
    i = int(t // per)
    pic, real, claim, fact, credit = ITEMS[i]
    u = t - i * per
    z = 1.0 + 0.1 * (1 - u / per)                                      # langsam herauszoomen, von 1,1 auf 1,0
    cw, ch = PW * z, PH * z
    x0, y0 = (pic.width - cw) / 2, (pic.height - ch) / 2
    view = pic.transform((PW, PH), Image.AFFINE, (cw / PW, 0, x0, 0, ch / PH, y0), Image.BILINEAR)
    im.paste(view, (PX, PY), MASK)
    d = ImageDraw.Draw(im)
    centered(d, 1374, f"{i + 1}/5 · {claim}", f(40, bold=True), FG)
    if u < T_GUESS:
        bw = 760 * (1 - u / T_GUESS)
        d.rounded_rectangle([160, 1456, 920, 1466], 5, fill=(38, 44, 58))
        if bw > 8:
            d.rounded_rectangle([540 - bw / 2, 1456, 540 + bw / 2, 1466], 5, fill=ACC)
    else:
        v = u - T_GUESS
        sc = max(0.05, back_out(v / 0.22))
        st = STAMP[real]
        sp = st.resize((max(1, int(st.width * sc)), max(1, int(st.height * sc))), Image.BILINEAR)
        im.paste(sp, (int(PX + PW / 2 - sp.width / 2), int(PY + PH * 0.80 - sp.height / 2)), sp)
        al = ease((v - 0.1) / 0.2)
        k = lambda c: tuple(int(a * al) for a in c)
        d = ImageDraw.Draw(im)
        centered(d, 1438, fact, f(33), k(GREEN if real else RED))
        centered(d, 1490, credit, f(23), k(SEC))
    return im


def main():
    chk = Path(os.environ.get("CHECK_DIR", OUT))
    for t in (1.0, 3.0, 4.2, 6.5, 13.3, 16.8):
        cinematic(frame(t), 0).save(chk / f"_check-rf-{t:.1f}.png")
    if os.environ.get("CHECK_ONLY"):
        return
    out = OUT / "w10-real-or-fake.mp4"
    n = int(LOOP * FPS)
    proc = subprocess.Popen([
        imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart",
        str(out)], stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(1.0), 0).save(OUT / "w10-real-or-fake-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
