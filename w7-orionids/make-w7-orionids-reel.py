"""Woche 7, Samstag 17.10.2026 - "Diese Woche am Himmel" (Andromeda-Muster: realistischer Himmel + Termin +
Handlung): Orioniden-Maximum in der Nacht 21./22.10.2026.

Hook-Varianten:
  1. SHOOTING STARS next week - made of Halley's Comet     <- gewaehlt (Termin + Staunen)
  2. Halley's Comet comes back next week. Sort of.
  3. Set an alarm for Wednesday night
  4. You can see pieces of HALLEY'S COMET next week
  5. The meteor shower nobody talks about

Szene (12 s Loop): realistischer Himmel Richtung Suedosten vor der Morgendaemmerung (echte Sternpositionen
J2000, gnomonisch, Norden oben - gegen 3-4 Uhr steht Orion nahe dem Meridian, also aufrecht), Meteore
fliegen auf Grosskreisen vom Radianten weg (in gnomonischer Projektion = Geraden durch den Radianten),
dann werden die Spuren zum Radianten zurueckverlaengert. Zeitraffer, im Bild gekennzeichnet.

Fakten: IMO/EarthSky/RMG 2026 - aktiv ca. 2.10.-7.11., Maximum Nacht 21./22.10. (RASC: 21.10. 18 UTC,
breites Maximum ueber mehrere Naechte), ZHR ~20, unter realem Himmel 10-20 pro Stunde; Radiant
RA 6h20m, Dec +16 Grad (noerdlich von Betelgeuse); Mond ~80 % beleuchtet, geht gegen 3 Uhr unter
(New York 03:12) -> beste Zeit danach bis zur Daemmerung; Mutterkoerper Komet 1P/Halley; 66 km/s.

    python make-w7-orionids-reel.py  ->  w7-orionids.mp4, -cover.png
"""

import importlib.util
import math
import os
import random
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from brandkit import S, FG, SEC, ACC, f, downscale
from reelkit import header_band, cinematic
from bodies import fbm

_spec = importlib.util.spec_from_file_location("andro", ROOT / "w6-andromeda-weekend" / "make-w6-andromeda-weekend-loop.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)
hms, dms = A.hms, A.dms

OUT = Path(__file__).resolve().parent
W, H, FPS, LOOP = 1080, 1920, 30, 12.0
HOR = 1400
PROJ = A.Proj(92.0, 4.0, 22.0, W / 2, 1000)
RADIANT = (hms(6, 20, 0), 16.0)

BRIGHT = {   # J2000, mag, Farbe
    "Betelgeuse": (hms(5, 55, 10.3), dms(7, 24, 25), 0.50, (255, 178, 118)),
    "Rigel": (hms(5, 14, 32.3), -dms(8, 12, 6), 0.13, (200, 215, 255)),
    "Bellatrix": (hms(5, 25, 7.9), dms(6, 20, 59), 1.64, (212, 224, 255)),
    "Mintaka": (hms(5, 32, 0.4), -dms(0, 17, 57), 2.23, (215, 226, 255)),
    "Alnilam": (hms(5, 36, 12.8), -dms(1, 12, 7), 1.69, (210, 222, 255)),
    "Alnitak": (hms(5, 40, 45.5), -dms(1, 56, 34), 1.77, (210, 222, 255)),
    "Saiph": (hms(5, 47, 45.4), -dms(9, 40, 11), 2.09, (212, 224, 255)),
    "Meissa": (hms(5, 35, 8.3), dms(9, 56, 3), 3.33, (215, 226, 255)),
    "Aldebaran": (hms(4, 35, 55.2), dms(16, 30, 33), 0.85, (255, 188, 138)),
    "Elnath": (hms(5, 26, 17.5), dms(28, 36, 27), 1.65, (220, 230, 255)),
    "Castor": (hms(7, 34, 35.9), dms(31, 53, 18), 1.58, (225, 234, 255)),
    "Pollux": (hms(7, 45, 18.9), dms(28, 1, 34), 1.14, (255, 212, 166)),
    "Alhena": (hms(6, 37, 42.7), dms(16, 23, 57), 1.93, (240, 244, 255)),
    "Procyon": (hms(7, 39, 18.1), dms(5, 13, 30), 0.34, (255, 248, 236)),
    "Sirius": (hms(6, 45, 8.9), -dms(16, 42, 58), -1.46, (220, 232, 255)),
}
ORION_LINES = [("Betelgeuse", "Meissa"), ("Meissa", "Bellatrix"), ("Bellatrix", "Mintaka"), ("Betelgeuse", "Alnitak"),
               ("Mintaka", "Alnilam"), ("Alnilam", "Alnitak"), ("Alnitak", "Saiph"), ("Mintaka", "Rigel")]


def faint_stars():
    rng = np.random.default_rng(17)
    n = 40000
    ra = rng.uniform(35, 150, n)
    dec = np.degrees(np.arcsin(rng.uniform(math.sin(math.radians(-35)), math.sin(math.radians(55)), n)))
    m = 4 + np.log10(1 + rng.random(n) * (10 ** (0.5 * 5.5) - 1)) / 0.5
    b, _ = A.galactic_b(np.radians(ra), np.radians(dec))
    keep = rng.random(n) < 0.35 + 0.65 * np.exp(-(b / 18) ** 2)
    tint = rng.choice(4, n, p=[0.55, 0.2, 0.15, 0.1])
    return ra[keep], dec[keep], m[keep], tint[keep]


def render_sky(ss=2, limit=6.6):
    W2, H2 = W * ss, H * ss
    p = A.Proj(92.0, 4.0, 22.0 * ss, W2 / 2, 1000 * ss)
    t = np.linspace(0, 1, H2)[:, None, None]
    sky = (np.array([5, 7, 13]) * (1 - t) + np.array([15, 19, 33]) * t) * np.ones((1, W2, 1))
    glow = np.exp(-np.clip((HOR * ss - np.arange(H2)) / (240 * ss), 0, None))[:, None, None]
    sky = sky + glow * np.array([26, 26, 36])                           # Restlicht am Horizont
    ra, dec = p.inverse_grid(W2 // 8 + 1, H2 // 8 + 1, step=8)          # Wintermilchstrasse (schwach)
    b, _ = A.galactic_b(ra, dec)
    n1 = fbm(5, b.shape[0], b.shape[1], octaves=5, base=4, wrap=False)
    band = np.exp(-(b / 10) ** 2) * (0.45 + 0.8 * n1) * 22
    lay = np.asarray(Image.fromarray(np.clip(band, 0, 255).astype(np.uint8)).resize((W2, H2), Image.BICUBIC), np.float32)
    sky = sky + lay[..., None] * np.array([0.85, 0.87, 1.0])
    img = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8), "RGB")
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    fr, fd, fm, ft = FAINT
    for i in range(len(fr)):
        x, y = p.xy(fr[i], fd[i])
        if -5 <= x < W2 + 5 and -5 <= y < H2 + 5:
            A.star_disc(d, x, y, fm[i], A.TINTS[ft[i]], limit, k=ss)
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    for name, (r_, d_, mag, col) in BRIGHT.items():
        x, y = p.xy(r_, d_)
        A.bright_star(img, x, y, max(mag, 0.0), col, k=ss * 0.9)
    return img


FAINT = faint_stars()


def P(name):
    return PROJ.xy(*BRIGHT[name][:2])


def background():
    img = render_sky(S)
    d = ImageDraw.Draw(img, "RGBA")
    for a, b in ORION_LINES:                                            # Orion dezent verbinden
        (ax, ay), (bx, by) = P(a), P(b)
        d.line([ax * S, ay * S, bx * S, by * S], fill=(150, 170, 215, 60), width=2 * S)
    st = dict(stroke_width=3 * S, stroke_fill=(5, 6, 10))
    for txt, (x, y), col in [("Orion", (P("Saiph")[0] - 150, P("Saiph")[1] + 10), (190, 200, 222)),
                             ("Betelgeuse", (P("Betelgeuse")[0] - 175, P("Betelgeuse")[1] - 14), (255, 190, 140)),
                             ("Taurus", (P("Aldebaran")[0] - 130, P("Aldebaran")[1] + 6), (190, 200, 222))]:
        d.text((x * S, y * S), txt, font=f(26 * S, bold=True), fill=col, **st)
    rnd = random.Random(8)                                              # Horizont mit Baeumen
    pts = [(0, H * S)] + [(W * S * i / 40, (HOR + math.sin(i * 0.4 + 1) * 18 + rnd.uniform(-8, 8)) * S)
                          for i in range(41)] + [(W * S, H * S)]
    d.polygon(pts, fill=(3, 4, 6))
    for x in (W * 0.06, W * 0.15, W * 0.86, W * 0.95):
        for k in range(4):
            w = (46 - k * 9) * S
            d.polygon([(x * S - w, (HOR - k * 34 + 10) * S), (x * S + w, (HOR - k * 34 + 10) * S),
                       (x * S, (HOR - (k + 1) * 34 - 12) * S)], fill=(3, 4, 6))
    shade = Image.new("L", img.size, 0)                                 # Kopfzeile lesbar halten
    ImageDraw.Draw(shade).rectangle([0, 0, W * S, 560 * S], fill=120)
    shade = shade.filter(ImageFilter.GaussianBlur(60 * S))
    img.paste(Image.new("RGB", img.size, (5, 7, 12)), (0, 0), shade)
    y = header_band(img, ["SHOOTING STARS next week -", "made of Halley's Comet"], "SHOOTING STARS")
    d = ImageDraw.Draw(img)
    sub = "Orionids · peak night Wed Oct 21 · best after 3 a.m."
    d.text(((W * S - d.textlength(sub, font=f(30 * S))) / 2, y + 6 * S), sub, font=f(30 * S), fill=SEC)
    note = "sped up · real rate: 10-20 per hour"
    d.text((W * S - 30 * S - d.textlength(note, font=f(22 * S)), (HOR - 92) * S), note, font=f(22 * S), fill=SEC)
    for n, (txt, fo, col) in enumerate([("Save this for Wednesday night", f(40 * S, bold=True), FG),
                                        ("Send it to someone who'll get up with you", f(32 * S), SEC)]):
        d.text(((W * S - d.textlength(txt, font=fo)) / 2, (HOR + 118 + n * 54) * S), txt, font=fo, fill=col)
    return downscale(img, W, H)


def meteors():
    """Zufaellige Spuren auf Grosskreisen durch den Radianten (im Bild Geraden durch R)."""
    rng = random.Random(21)
    rx, ry = PROJ.xy(*RADIANT)
    out, t0 = [], 0.25
    while t0 < 10.6:
        phi = rng.uniform(0, 2 * math.pi)
        a, ln = rng.uniform(50, 380), rng.uniform(180, 380)
        x0, y0 = rx + math.cos(phi) * a, ry + math.sin(phi) * a
        x1, y1 = rx + math.cos(phi) * (a + ln), ry + math.sin(phi) * (a + ln)
        if not (20 < x1 < W - 20 and 600 < y1 < HOR - 40 and 600 < y0):
            continue
        out.append((t0, rng.uniform(0.45, 0.75), (x0, y0), (x1, y1), rng.uniform(0.6, 1.0)))
        t0 += rng.uniform(0.3, 0.7)
    return out


METEORS = meteors()


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def draw_meteor(d, m, t):
    t0, dur, (x0, y0), (x1, y1), br = m
    u = (t - t0) / dur
    if u <= 0 or u > 1.6:
        return
    head = min(1.0, u)
    tail = max(0.0, head - 0.55) if u <= 1 else (u - 1) / 0.6 * head + 0.45 * (1 - (u - 1) / 0.6)
    fade = 1.0 if u <= 1 else max(0.0, 1 - (u - 1) / 0.6)
    n = 24
    for k in range(n):
        a = tail + (head - tail) * k / n
        b = tail + (head - tail) * (k + 1) / n
        w = (k + 1) / n
        c = (int(200 + 55 * w), int(230 + 25 * w), int(220 + 35 * w), int(255 * br * fade * w ** 1.6))
        d.line([x0 + (x1 - x0) * a, y0 + (y1 - y0) * a, x0 + (x1 - x0) * b, y0 + (y1 - y0) * b],
               fill=c, width=max(1, int(1.5 + 4 * w)))


def frame(bg, t):
    im = bg.copy().convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    back = ease((t - 6.0) / 0.8) * (1 - ease((t - 11.3) / 0.6))       # Spuren zum Radianten zurueckverlaengern
    for m in METEORS:
        if back > 0 and m[0] + m[1] * 1.6 < t:                         # wie Langzeitbelichtung stehen lassen
            (x0, y0), (x1, y1) = m[2], m[3]
            d.line([x0, y0, x1, y1], fill=(225, 240, 235, int(90 * back * m[4])), width=2)
        draw_meteor(d, m, t)
    glow = ov.filter(ImageFilter.GaussianBlur(6))
    im.alpha_composite(glow)
    im.alpha_composite(glow)
    im.alpha_composite(ov)
    rx, ry = PROJ.xy(*RADIANT)
    d = ImageDraw.Draw(im)
    if back > 0:
        for t0, dur, (x0, y0), (x1, y1), br in METEORS:
            if t0 > t:
                continue
            L = math.hypot(x0 - rx, y0 - ry)
            for s_ in range(0, int(L * back), 18):
                q0, q1 = s_ / L, min(L, s_ + 9) / L
                d.line([x0 + (rx - x0) * q0, y0 + (ry - y0) * q0, x0 + (rx - x0) * q1, y0 + (ry - y0) * q1],
                       fill=(255, 180, 84, int(170 * back)), width=2)
        r = 26 + 4 * math.sin(t * 4)
        d.ellipse([rx - r, ry - r, rx + r, ry + r], outline=(255, 180, 84, int(255 * back)), width=4)
        fo = f(30, bold=True)
        d.text((rx + r + 12, ry - 18), "Radiant", font=fo, fill=(255, 180, 84, int(255 * back)),
               stroke_width=3, stroke_fill=(5, 6, 10, int(255 * back)))
    lab = [("1 · Night of Oct 21-22 (peak)", 0.0, 3.0), ("2 · After the Moon sets, ~3 a.m. to dawn", 3.0, 6.0),
           ("3 · All trails point back to Orion", 6.0, 9.0), ("Each one: dust from Halley's Comet, 66 km/s", 9.0, 11.4)]
    for txt, a, b in lab:
        al = ease((t - a) / 0.35) * (1 - ease((t - b) / 0.35))
        if al > 0:
            fo = f(42, bold=True)
            col = ACC if txt.startswith("Each") else FG
            d.text(((W - d.textlength(txt, font=fo)) / 2, HOR + 34), txt, font=fo, fill=col + (int(255 * al),),
                   stroke_width=3, stroke_fill=(3, 4, 6, int(255 * al)))
    return im.convert("RGB")


def main():
    bg = background()
    chk = Path(os.environ.get("CHECK_DIR", OUT))
    for t in (2.0, 7.5, 10.0):
        cinematic(frame(bg, t), 0).save(chk / f"_check-orionids-{t:.1f}.png")
    if os.environ.get("CHECK_ONLY"):
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = OUT / "w7-orionids.mp4"
    n = int(LOOP * FPS)
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart",
        str(out)], stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg, 10.0), 0).save(OUT / "w7-orionids-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
