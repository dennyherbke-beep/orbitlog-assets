"""Woche 9, Sa 31.10.2026: "The star that could EXPLODE any night" (Remake-Regel 6, Vorbild cosmic_adventure777
"The night sky after Betelgeuse goes supernova" 7,7K / 46x, Snapshot 09.10.2026; Typ e Bedrohung -> Aufloesung).
Eine Animation, 18 s: Orion am Abendhimmel (Katalogpositionen) -> Betelgeuse wird zur Supernova (Halbmond-hell,
Vergleichs-Inset) -> sichtbar am Taghimmel -> verblasst, Orion fehlt eine Schulter -> Aufloesung: ungefaehrlich.

Fakten (vor Produktion geprueft, 26.10.2026):
  Betelgeuse: Roter Ueberriese, Entfernung je nach Studie ~550-650 Lj ("over 500 light-years").
  Supernova-Helligkeit: etwa wie der Halbmond fuer >3 Monate (Goldberg & Bauer, zit. Astronomy.com), am Taghimmel
  sichtbar, nachts jahrelang mit blossem Auge. Zeitpunkt nicht vorhersagbar, eher in Zehn- bis Hunderttausenden Jahren
  (Joyce et al. 2020: ~100.000 Jahre). Gefahr erst unter ~50 Lj (NASA) -> ungefaehrlich.
  Orion steht Anfang November ab ~22 Uhr im Osten/Suedosten. Sterne: RA/Dec J2000, Bright Star Catalogue.

Hook-Varianten:
  1 "The star that could EXPLODE any night" (gewaehlt)   2 "Find this star tonight. It's about to die."
  3 "What the sky looks like when Betelgeuse explodes"   4 "Orion is going to lose a shoulder"
  5 "A star you can see will go supernova"

    python make-w9-betelgeuse-reel.py [--preview DIR]  ->  w9-betelgeuse.mp4, -cover.png
"""

import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bodies import planet
from brandkit import S, FG, SEC, ACC, HAIR, f, downscale
from reelkit import new_frame, header_band, cinematic

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
LOOP = 18.0
C_RA, C_DEC = 5.55, 0.5
SCALE = 40.0
ROT = math.radians(-24)
CX, CY = 560, 1090
GROUND = 1480
T_BOOM = 4.2

# (Name, RA h, Dec Grad, mag, Farbe)
STARS = [("Betelgeuse", 5.919, 7.41, 0.5, (255, 150, 90)), ("Rigel", 5.242, -8.20, 0.13, (200, 218, 255)),
         ("Bellatrix", 5.419, 6.35, 1.64, (215, 225, 255)), ("Saiph", 5.796, -9.67, 2.06, (215, 225, 255)),
         ("", 5.533, -0.30, 2.23, (215, 225, 255)), ("", 5.603, -1.20, 1.69, (215, 225, 255)),
         ("", 5.679, -1.94, 1.77, (215, 225, 255)), ("", 5.585, 9.93, 3.39, (215, 225, 255)),
         ("", 5.590, -5.91, 2.77, (215, 225, 255)), ("", 5.598, -5.40, 4.0, (200, 215, 245)),
         ("Aldebaran", 4.598, 16.51, 0.85, (255, 196, 140)), ("", 4.83, 6.96, 3.2, (230, 236, 255)),
         ("", 4.85, 5.6, 3.7, (230, 236, 255)), ("", 6.38, -17.96, 1.98, (215, 225, 255))]
LINES = [(0, 7), (7, 2), (0, 6), (2, 4), (4, 5), (5, 6), (6, 3), (4, 1)]
BET = 0

CAPTIONS = [(0.0, "Betelgeuse is a dying giant star,", "over 500 light-years away."),
            (T_BOOM, "When it explodes,", "it'll shine like a half Moon."),
            (8.6, "Bright enough to see in daylight", "for about 3 months."),
            (11.8, "Then it fades for years,", "and Orion loses a shoulder."),
            (14.6, "", "")]


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def proj(ra_h, dec):
    a, d = math.radians(ra_h * 15), math.radians(dec)
    a0, d0 = math.radians(C_RA * 15), math.radians(C_DEC)
    cosc = math.sin(d0) * math.sin(d) + math.cos(d0) * math.cos(d) * math.cos(a - a0)
    xi = math.cos(d) * math.sin(a - a0) / cosc
    eta = (math.cos(d0) * math.sin(d) - math.sin(d0) * math.cos(d) * math.cos(a - a0)) / cosc
    x, y = -math.degrees(xi) * SCALE, -math.degrees(eta) * SCALE
    return (CX + x * math.cos(ROT) - y * math.sin(ROT), CY + x * math.sin(ROT) + y * math.cos(ROT))


def ground_profile():
    rng = np.random.default_rng(17)
    x = np.arange(W, dtype=np.float32)
    hill = GROUND + 16 * np.sin(x / 170) + 9 * np.sin(x / 57 + 2.1)
    trees = np.zeros(W, np.float32)
    for _ in range(50):
        c, w, h = rng.uniform(0, W), rng.uniform(14, 40), rng.uniform(16, 60)
        trees = np.maximum(trees, h * np.sqrt(np.clip(1 - ((x - c) / w) ** 2, 0, 1)))
    return hill - trees


GROUND_P = ground_profile()


def ground_mask():
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon([(0, H)] + [(x, float(GROUND_P[x])) for x in range(0, W, 3)]
                              + [(W, float(GROUND_P[-1])), (W, H)], fill=255)
    return m


GMASK = ground_mask()


def night_sky(with_bet=True, bet_dim=1.0):
    img, _ = new_frame(44)
    header_band(img, ["The star that could", "EXPLODE any night"], "EXPLODE")
    sm = downscale(img, W, H)
    d = ImageDraw.Draw(sm)
    pts = [proj(s[1], s[2]) for s in STARS]
    for i, j in LINES:
        if not with_bet and BET in (i, j):
            continue
        d.line([pts[i], pts[j]], fill=(58, 70, 96), width=2)
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    dl = ImageDraw.Draw(layer)
    for k, ((name, ra, dec, mag, c), (x, y)) in enumerate(zip(STARS, pts)):
        if k == BET:
            if not with_bet:
                continue
            c = tuple(int(v * bet_dim) for v in c)
        r = max(1.8, 8.0 - 1.45 * mag)
        dl.ellipse([x - r, y - r, x + r, y + r], fill=c)
    mx, my = proj(5.588, -5.39)                                             # Orionnebel, schwach
    dl.ellipse([mx - 9, my - 7, mx + 9, my + 7], fill=(70, 60, 90))
    sm = ImageChops.add(sm, layer.filter(ImageFilter.GaussianBlur(7)))
    sm = ImageChops.lighter(sm, layer)
    d = ImageDraw.Draw(sm)
    st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
    rx, ry = proj(5.242, -8.20)
    d.text((rx + 14, ry - 6), "Rigel", font=f(22), fill=SEC, **st)
    ox, oy = proj(5.2, 1.5)
    d.text((ox - 20, oy - 10), "ORION", font=f(26, bold=True), fill=(120, 134, 168), **st)
    sm.paste((8, 10, 14), (0, 0, W, H), GMASK)
    return sm


def day_sky():
    ys = np.arange(H, dtype=np.float32)[:, None]
    t = np.clip(ys / GROUND, 0, 1)
    top, hor = np.array([46, 98, 178]), np.array([168, 200, 232])
    arr = top[None, None, :] * (1 - t[..., None] ** 1.6) + hor[None, None, :] * t[..., None] ** 1.6
    arr = np.broadcast_to(arr, (H, W, 3)).astype(np.float32).copy()
    im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    hb = Image.new("RGB", (W * S, H * S), (0, 0, 0))
    header_band(hb, ["The star that could", "EXPLODE any night"], "EXPLODE")
    hb = downscale(hb, W, H)
    im.paste(hb, (0, 0), hb.convert("L").point(lambda p: min(255, p * 6)))
    im.paste((34, 44, 36), (0, 0, W, H), GMASK)
    return im


def supernova(im, x, y, k, day=False):
    """Punktquelle mit Glow und Beugungsspitzen; k = Helligkeit 0..1."""
    if k <= 0:
        return im
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    core = 6 + 10 * k
    for rad, c in ((170 * k, (26, 38, 80)), (70 * k, (90, 125, 210)), (24 * k, (215, 228, 255))):
        d.ellipse([x - rad, y - rad, x + rad, y + rad], fill=c)
    layer = layer.filter(ImageFilter.GaussianBlur(16 * k + 3))
    if day:
        layer = layer.point(lambda p: int(p * 0.35))
    d = ImageDraw.Draw(layer)
    L = 260 * k
    for ang in (0, 90, 45, 135):
        a = math.radians(ang + 12)
        ln = L if ang in (0, 90) else L * 0.45
        for wdt, c in ((5, (60, 80, 140)), (2, (200, 215, 255))):
            d.line([x - ln * math.cos(a), y - ln * math.sin(a), x + ln * math.cos(a), y + ln * math.sin(a)],
                   fill=tuple(int(v * k) for v in c), width=wdt)
    d.ellipse([x - core, y - core, x + core, y + core], fill=(255, 255, 255))
    return ImageChops.add(im, layer)


class Assets:
    def __init__(self):
        self.night = night_sky()
        self.night_dim = [night_sky(True, b) for b in (0.6, 0.3)]
        self.night_gone = night_sky(False)
        self.day = day_sky()
        size = 110
        m = Image.new("RGB", (size * S, size * S), (0, 0, 0))
        planet(m, size * S // 2, size * S // 2, 90, "moon", light=(1, 0, 0.02), lon0=0)
        self.moon = downscale(m, size, size)


def moon_inset(im, A, a):
    if a <= 0:
        return im
    box = Image.new("RGB", (300, 200), (10, 13, 20))
    box.paste(A.moon, (20, 30), A.moon.convert("L").point(lambda p: min(255, p * 4)))
    bd = ImageDraw.Draw(box)
    bd.text((140, 64), "Half Moon", font=f(26, bold=True), fill=FG)
    bd.text((140, 100), "same", font=f(22), fill=SEC)
    bd.text((140, 126), "brightness", font=f(22), fill=SEC)
    bd.rectangle([0, 0, 299, 199], outline=HAIR, width=2)
    mask = Image.new("L", box.size, int(230 * a))
    im.paste(box, (720, 690), mask)
    return im


def frame(A, t):
    st = dict(stroke_width=4, stroke_fill=(8, 10, 14))
    bx, by = proj(5.919, 7.41)
    if t < 8.6:
        im = A.night.copy()
        k = ease((t - T_BOOM) / 0.6) * (1 + 0.15 * math.sin(t * 3))
        if t >= T_BOOM:
            glow = ease((t - T_BOOM) / 0.6)                                 # Himmel hellt auf, Landschaft wird sichtbar
            arr = np.asarray(im, np.float32)
            arr += glow * np.array([10, 16, 30])[None, None, :]
            im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            im.paste((22, 28, 34), (0, 0, W, H), GMASK.point(lambda p: int(p * glow)))
        im = supernova(im, bx, by, min(1.0, k))
        im = moon_inset(im, A, ease((t - 5.4) / 0.5) * (1 - ease((t - 8.2) / 0.4)))
        if t < T_BOOM:                                                      # Markierung vor der Explosion
            a = ease((t - 0.6) / 0.5)
            d = ImageDraw.Draw(im)
            c = tuple(int(v * a) for v in ACC)
            d.ellipse([bx - 22, by - 22, bx + 22, by + 22], outline=c, width=3)
            d.text((bx + 30, by - 18), "Betelgeuse", font=f(30, bold=True), fill=c, **st)
    elif t < 11.8:
        im = A.day.copy()
        if t < 9.0:
            im = Image.blend(A.night, im, ease((t - 8.6) / 0.4))
        im = supernova(im, bx, by, 0.45, day=True)
        d = ImageDraw.Draw(im)
        d.text((60, 1610), "Daytime · same view", font=f(26, bold=True), fill=ACC, **st)
    else:                                                                   # verblasst -> Schulter fehlt
        s = (t - 11.8) / 2.4
        if s < 0.33:
            im = Image.blend(A.day, A.night_dim[0], ease(s / 0.33))
        elif s < 0.66:
            im = Image.blend(A.night_dim[0], A.night_dim[1], ease((s - 0.33) / 0.33))
        else:
            im = Image.blend(A.night_dim[1], A.night_gone, ease((s - 0.66) / 0.34))
        if 11.8 <= t < 14.6:
            im = supernova(im, bx, by, max(0.0, 0.5 - 0.5 * ease((t - 11.8) / 2.4)))
        if t >= 13.6:
            a = ease((t - 13.6) / 0.4)
            d = ImageDraw.Draw(im)
            dash = tuple(int(v * a) for v in ACC)
            for k in range(12):
                a0 = math.radians(k * 30)
                d.arc([bx - 26, by - 26, bx + 26, by + 26], math.degrees(a0), math.degrees(a0) + 16, fill=dash, width=3)
            d.text((bx + 34, by - 18), "gone", font=f(28, bold=True), fill=dash, **st)
    d = ImageDraw.Draw(im)
    if t < 8.6 or t >= 11.8:
        d.text((60, 1610), "Looking east · after 10 pm in November", font=f(26, bold=True), fill=ACC, **st)
    cap = [c for c in CAPTIONS if t >= c[0]][-1]
    ca = ease((t - cap[0]) / 0.4)
    for j, ln in enumerate(cap[1:]):
        if ln:
            fo = f(42, bold=True) if j == 0 else f(36)
            d.text(((W - d.textlength(ln, font=fo)) / 2, 550 + j * 58), ln, font=fo,
                   fill=tuple(int(v * ca) for v in FG), **st)
    if t >= 14.6:                                                           # Aufloesung + Handlung
        a = ease((t - 14.6) / 0.4)
        for j, (ln, fo, c) in enumerate([("Dangerous? No.", f(52, bold=True), ACC),
                                          ("It's far too far away.", f(38), FG),
                                          ("Could be tonight - or in 100,000 years.", f(32), FG)]):
            d.text(((W - d.textlength(ln, font=fo)) / 2, 540 + [0, 70, 122][j]), ln, font=fo,
                   fill=tuple(int(v * a) for v in c), **st)
    cta = "Send this to someone who'd want to see it"
    d.text(((W - d.textlength(cta, font=f(34, bold=True))) / 2, 1740), cta, font=f(34, bold=True), fill=FG, **st)
    return im


def main():
    A = Assets()
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (2.5, 6.5, 10.0, 13.2, 16.0):
            cinematic(frame(A, t), 0).save(prev / f"bet-{t:.1f}.png")
        print("preview saved")
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(LOOP * FPS)
    out = OUT / "w9-betelgeuse.mp4"
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(A, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(A, 6.5), 0).save(OUT / "w9-betelgeuse-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
