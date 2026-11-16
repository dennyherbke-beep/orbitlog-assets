"""Woche 12, Di 17.11.2026 - "Diese Woche am Himmel" (Termin + Handlung), Regel 13: 10-s-Loop.
Leoniden-Maximum 17.11. ~15 UT (Sonnenlaenge 235,27 Grad, astropy) -> beste Nacht 17./18.11. Basis: w7-orionids.

Hook-Varianten:
  1. SHOOTING STARS tonight / right next to Jupiter            <- gewaehlt (Termin + Bezug zum Mars-Jupiter-Reel)
  2. Go outside after 1 a.m. tonight
  3. The Leonids peak TONIGHT
  4. Shooting stars from the Lion - tonight
  5. Most people will miss this (again)

Fakten: IMO 2026 - Leoniden aktiv 6.-30.11., ZHR ~15 -> realistisch 10-15 pro Stunde unter dunklem Himmel; Radiant
RA 10h12m, Dec +22 (Sichel des Loewen); 71 km/s (schnellste Meteore); Mutterkoerper Komet 55P/Tempel-Tuttle.
50 N/10 E: Radiant 00 MEZ 9 Grad hoch (Ost), 02 MEZ 28 Grad (Ost), 04 MEZ 47 Grad (Suedost); Mond 54 % geht gegen
Mitternacht unter. Jupiter (RA 148,2 / +13,7) und Mars (149,3 / +14,6) stehen 8-9 Grad vom Radianten neben Regulus
(astropy 8.0.2, GCRS, 18.11. 02 UT). Darstellung: Norden oben, Zeitraffer, im Bild vermerkt.

    python make-w12-leonids-reel.py  ->  w12-leonids.mp4, -cover.png
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
W, H, FPS, LOOP = 1080, 1920, 30, 10.0
HOR = 1400
PROJ = A.Proj(160.0, 19.0, 22.0, W / 2, 1000)
RADIANT = (hms(10, 12, 0), 21.6)
PLANETS = {"Jupiter": (148.17, 13.68, -2.4, (255, 244, 222)), "Mars": (149.25, 14.61, 0.0, (255, 150, 90))}

BRIGHT = {   # J2000, mag, Farbe
    "Regulus": (hms(10, 8, 22.3), dms(11, 58, 2), 1.35, (205, 220, 255)),
    "Algieba": (hms(10, 19, 58.4), dms(19, 50, 29), 2.08, (255, 200, 150)),
    "Denebola": (hms(11, 49, 3.6), dms(14, 34, 19), 2.13, (225, 234, 255)),
    "Zosma": (hms(11, 14, 6.5), dms(20, 31, 25), 2.56, (225, 234, 255)),
    "Chertan": (hms(11, 14, 14.4), dms(15, 25, 46), 3.33, (225, 234, 255)),
    "Adhafera": (hms(10, 16, 41.4), dms(23, 25, 2), 3.43, (235, 240, 255)),
    "Rasalas": (hms(9, 52, 45.8), dms(26, 0, 25), 3.88, (255, 214, 170)),
    "Ras Elased": (hms(9, 45, 51.1), dms(23, 46, 27), 2.98, (255, 230, 190)),
    "Eta Leo": (hms(10, 7, 19.9), dms(16, 45, 45), 3.48, (240, 244, 255)),
    "Castor": (hms(7, 34, 35.9), dms(31, 53, 18), 1.58, (225, 234, 255)),
    "Pollux": (hms(7, 45, 18.9), dms(28, 1, 34), 1.14, (255, 212, 166)),
    "Procyon": (hms(7, 39, 18.1), dms(5, 13, 30), 0.34, (255, 248, 236)),
    "Alphard": (hms(9, 27, 35.2), -dms(8, 39, 31), 1.98, (255, 196, 150)),
}
ORION_LINES = [("Ras Elased", "Rasalas"), ("Rasalas", "Adhafera"), ("Adhafera", "Algieba"), ("Algieba", "Eta Leo"),
               ("Eta Leo", "Regulus"), ("Algieba", "Zosma"), ("Zosma", "Denebola"), ("Denebola", "Chertan"),
               ("Chertan", "Regulus"), ("Chertan", "Zosma")]


def faint_stars():
    rng = np.random.default_rng(17)
    n = 40000
    ra = rng.uniform(100, 220, n)
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
    for name, (r_, d_, mag, col) in PLANETS.items():                    # Planeten als helle Punkte
        x, y = PROJ.xy(r_, d_)
        A.bright_star(img, x * S, y * S, 0.7 if name == "Jupiter" else 1.4, col, k=S * 0.75)
    jx, jy = PROJ.xy(*PLANETS["Jupiter"][:2])
    mx, my = PROJ.xy(*PLANETS["Mars"][:2])
    for txt, (x, y), col in [("Leo", (P("Denebola")[0] - 30, P("Denebola")[1] + 30), (190, 200, 222)),
                             ("Regulus", (P("Regulus")[0] + 18, P("Regulus")[1] + 6), (190, 200, 222)),
                             ("Jupiter", (jx - 150, jy + 10), (255, 236, 200)),
                             ("Mars", (mx - 100, my - 46), (255, 170, 120))]:
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
    y = header_band(img, ["SHOOTING STARS tonight -", "right next to Jupiter"], "SHOOTING STARS")
    d = ImageDraw.Draw(img)
    sub = "Leonids · night of Nov 17-18 · best after 1 a.m."
    d.text(((W * S - d.textlength(sub, font=f(30 * S))) / 2, y + 6 * S), sub, font=f(30 * S), fill=SEC)
    note = "sped up · real rate: 10-15 per hour"
    d.text((W * S - 30 * S - d.textlength(note, font=f(22 * S)), (HOR - 92) * S), note, font=f(22 * S), fill=SEC)
    for n, (txt, fo, col) in enumerate([("Save this for 1 a.m. tonight", f(40 * S, bold=True), FG),
                                        ("Send it to someone who'll stay up with you", f(32 * S), SEC)]):
        d.text(((W * S - d.textlength(txt, font=fo)) / 2, (HOR + 118 + n * 54) * S), txt, font=fo, fill=col)
    return downscale(img, W, H)


def meteors():
    """Zufaellige Spuren auf Grosskreisen durch den Radianten (im Bild Geraden durch R)."""
    rng = random.Random(21)
    rx, ry = PROJ.xy(*RADIANT)
    out, t0 = [], 0.25
    while t0 < 8.4:
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
    back = max(ease((t - 5.0) / 0.7), 1 - ease((t - 0.7) / 0.9))   # Loop beginnt mit dem Strahlenbild (erstes Bild zaehlt)
    prev = t < 1.8                                                    # Spuren der vorigen Runde       # Spuren zum Radianten zurueckverlaengern
    for m in METEORS:
        if back > 0 and (prev or m[0] + m[1] * 1.6 < t):                         # wie Langzeitbelichtung stehen lassen
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
            if t0 > t and not prev:
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
    lab = [("1 · Tonight, Nov 17-18 (peak)", -1.0, 2.5), ("2 · After 1 a.m., look EAST", 2.5, 5.0),
           ("3 · All trails point back to Leo", 5.0, 7.6), ("Comet dust hitting us at 71 km/s", 7.6, 9.6),
           ("1 · Tonight, Nov 17-18 (peak)", 9.6, 11.0)]
    for txt, a, b in lab:
        al = ease((t - a) / 0.35) * (1 - ease((t - b) / 0.35))
        if al > 0:
            fo = f(42, bold=True)
            col = ACC if txt.startswith("Comet") else FG
            d.text(((W - d.textlength(txt, font=fo)) / 2, HOR + 34), txt, font=fo, fill=col + (int(255 * al),),
                   stroke_width=3, stroke_fill=(3, 4, 6, int(255 * al)))
    return im.convert("RGB")


def main():
    bg = background()
    chk = Path(os.environ.get("CHECK_DIR", OUT))
    for t in (0.0, 3.5, 6.5, 8.5):
        cinematic(frame(bg, t), 0).save(chk / f"_check-leonids-{t:.1f}.png")
    if os.environ.get("CHECK_ONLY"):
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = OUT / "w12-leonids.mp4"
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
    cinematic(frame(bg, 6.5), 0).save(OUT / "w12-leonids-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
