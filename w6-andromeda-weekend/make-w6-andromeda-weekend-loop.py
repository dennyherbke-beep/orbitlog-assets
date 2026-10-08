"""Woche 6, Freitag - Andromeda-Reel als realistischer Himmelsausschnitt (Umbau 08.10.2026 nach dem
Winner w6-sun-from-planets: feste Kopfzeile + eine durchgehende Szene). Ersetzt die Folien-Version
make-w6-andromeda-weekend-reel.py (bleibt als Archiv liegen).

Realistisch statt schematisch: echte Sternpositionen (J2000) in gnomonischer Projektion, Norden oben,
Osten links (Blick an den Himmel), Sterngroesse nach Helligkeit, dichtes Sternfeld bis ~9 mag,
Milchstrasse aus galaktischer Breite berechnet (laeuft tatsaechlich durch Cassiopeia), M31 in echter
Groesse/Lage (PA 38 Grad, ~3 x 1 Grad) mit M32/M110, Fernglas-Ausschnitt (7 Grad) zum Schluss.

Ablauf (12 s, nahtloser Loop): Himmel steht -> Cassiopeia-W leuchtet auf -> Linien -> Pfeil aus der
tieferen V-Haelfte (Spitze Schedar) zur Galaxie -> Ring um Andromeda -> Fernglas-Ansicht ->
"Its light left 2.5 million years ago" -> zurueck.

Fakten: Neumond 10.10.2026; M31 ~2,5 Mio. Lichtjahre, ~3,4 mag, mit blossem Auge als schwacher
laenglicher Fleck sichtbar; Oktober abends ~2 h nach Sonnenuntergang hoch im Osten/Nordosten;
Aufsuchen ueber die tiefere V-Haelfte (Caph-Schedar-Navi) von Cassiopeias W. Hintergrundsterne
unter 4 mag sind zufaellig verteilt (statistisch realistische Dichte), keine Katalogpositionen.

    python make-w6-andromeda-weekend-loop.py  ->  w6-andromeda-weekend-loop.mp4, -loop-cover.png
"""

import math
import os
import random
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, f, downscale
from reelkit import header_band

OUT = Path(__file__).resolve().parent
W, H, FPS, LOOP = 1080, 1920, 30, 12.0
HOR = 1400                                          # Horizont (Ausgabe-px)
RA0, DEC0, SCALE, CY0 = 12.5, 51.0, 30.0, 1000      # Projektionsmitte (Grad), px pro Grad, Bild-y der Mitte


def hms(h, m, s):
    return (h + m / 60 + s / 3600) * 15


def dms(d, m, s):
    return d + m / 60 + s / 3600


# Helle Sterne (J2000, Helligkeit mag, Farbe)
BRIGHT = {
    "Caph": (hms(0, 9, 10.7), dms(59, 8, 59), 2.27, (255, 246, 230)),
    "Schedar": (hms(0, 40, 30.4), dms(56, 32, 14), 2.24, (255, 214, 170)),
    "Navi": (hms(0, 56, 42.5), dms(60, 43, 0), 2.47, (215, 228, 255)),
    "Ruchbah": (hms(1, 25, 49.0), dms(60, 14, 7), 2.68, (240, 244, 255)),
    "Segin": (hms(1, 54, 23.7), dms(63, 40, 12), 3.37, (210, 224, 255)),
    "eta Cas": (hms(0, 49, 6.3), dms(57, 48, 55), 3.44, (255, 248, 236)),
    "Mirach": (hms(1, 9, 43.9), dms(35, 37, 14), 2.05, (255, 196, 150)),
    "mu And": (hms(0, 56, 45.2), dms(38, 29, 58), 3.87, (240, 244, 255)),
    "nu And": (hms(0, 49, 48.8), dms(41, 4, 44), 4.53, (225, 234, 255)),
    "Almach": (hms(2, 3, 54.0), dms(42, 19, 47), 2.10, (255, 206, 160)),
    "delta And": (hms(0, 39, 19.7), dms(30, 51, 40), 3.27, (255, 210, 170)),
    "Alpheratz": (hms(0, 8, 23.3), dms(29, 5, 26), 2.06, (225, 234, 255)),
    "Mirfak": (hms(3, 24, 19.4), dms(49, 51, 40), 1.79, (255, 244, 220)),
    "Alderamin": (hms(21, 18, 34.8), dms(62, 35, 8), 2.45, (255, 250, 240)),
    "Polaris": (hms(2, 31, 49.1), dms(89, 15, 51), 1.98, (255, 246, 222)),
}
W_STARS = ["Segin", "Ruchbah", "Navi", "Schedar", "Caph"]
M31 = (hms(0, 42, 44.3), dms(41, 16, 9))
M32 = (hms(0, 42, 41.8), dms(40, 51, 55))
M110 = (hms(0, 40, 22.1), dms(41, 41, 7))
GAL = np.array([[-0.0548755604, -0.8734370902, -0.4838350155],      # aequatorial -> galaktisch (J2000)
                [0.4941094279, -0.4448296300, 0.7469822445],
                [-0.8676661490, -0.1980763734, 0.4559837762]])


class Proj:
    """Gnomonische Projektion: Norden oben, Osten links."""

    def __init__(self, ra0, dec0, scale, cx, cy):
        self.ra0, self.dec0 = math.radians(ra0), math.radians(dec0)
        self.k = math.degrees(1) * scale
        self.cx, self.cy = cx, cy

    def xy(self, ra, dec):
        r, d = math.radians(ra), math.radians(dec)
        c = math.sin(self.dec0) * math.sin(d) + math.cos(self.dec0) * math.cos(d) * math.cos(r - self.ra0)
        x = math.cos(d) * math.sin(r - self.ra0) / c
        y = (math.cos(self.dec0) * math.sin(d) - math.sin(self.dec0) * math.cos(d) * math.cos(r - self.ra0)) / c
        return self.cx - x * self.k, self.cy - y * self.k

    def inverse_grid(self, w, h, ox=0, oy=0, step=1.0):
        X, Y = np.meshgrid(np.arange(w) * step + ox, np.arange(h) * step + oy)
        x, y = (self.cx - X) / self.k, (self.cy - Y) / self.k
        rho = np.sqrt(x * x + y * y) + 1e-12
        c = np.arctan(rho)
        dec = np.arcsin(np.cos(c) * math.sin(self.dec0) + y * np.sin(c) * math.cos(self.dec0) / rho)
        ra = self.ra0 + np.arctan2(x * np.sin(c), rho * math.cos(self.dec0) * np.cos(c) - y * math.sin(self.dec0) * np.sin(c))
        return ra, dec


def galactic_b(ra, dec):
    v = np.stack([np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)])
    g = np.tensordot(GAL, v, axes=1)
    return np.degrees(np.arcsin(np.clip(g[2], -1, 1))), np.degrees(np.arctan2(g[1], g[0]))


def faint_stars():
    """Statistisches Sternfeld 4-9,5 mag in RA/Dec (Dichte steigt ~0,5 dex pro mag, zur Milchstrasse hin dichter)."""
    rng = np.random.default_rng(42)
    n = 22000
    ra = rng.uniform(-40, 75, n)
    dec = np.degrees(np.arcsin(rng.uniform(math.sin(math.radians(15)), 1, n)))
    u = rng.random(n)
    m = 4 + np.log10(1 + u * (10 ** (0.5 * 5.5) - 1)) / 0.5
    b, _ = galactic_b(np.radians(ra), np.radians(dec))
    keep = rng.random(n) < 0.35 + 0.65 * np.exp(-(b / 18) ** 2)
    tint = rng.choice(4, n, p=[0.55, 0.2, 0.15, 0.1])
    return ra[keep], dec[keep], m[keep], tint[keep]


TINTS = [(244, 246, 255), (255, 236, 210), (214, 226, 255), (255, 214, 180)]


def star_disc(d, x, y, mag, col, limit, k=1.0):
    """Stern als Punkt; Groesse/Helligkeit aus der Magnitude (relativ zur Grenzgroesse)."""
    fl = 10 ** (-0.4 * (mag - limit))
    if fl < 0.35:
        return
    a = min(255, int(105 * fl ** 0.5))
    r = (0.55 + 0.55 * math.log10(1 + fl)) * k
    d.ellipse([x - r, y - r, x + r, y + r], fill=col + (a,))


def bright_star(img, x, y, mag, col, k=1.0):
    fl = 10 ** (-0.4 * (mag - 2.0))
    g = int((10 + 10 * fl ** 0.5) * k)
    halo = Image.new("L", (4 * g, 4 * g), 0)
    ImageDraw.Draw(halo).ellipse([g, g, 3 * g, 3 * g], fill=int(min(200, 110 * fl ** 0.5)))
    halo = halo.filter(ImageFilter.GaussianBlur(g * 0.45))
    img.paste(Image.new("RGB", halo.size, col), (int(x - 2 * g), int(y - 2 * g)), halo)
    r = (2.2 + 1.6 * fl ** 0.5) * k
    ImageDraw.Draw(img).ellipse([x - r, y - r, x + r, y + r], fill=tuple(min(255, c + 10) for c in col))


def galaxy_patch(scale_px_per_deg, gain=1.0):
    """M31 als Flaechenhelligkeit: heller Kern, Bulge, geneigte Scheibe (b/a ~0,3), angedeutete Staubbahn,
    PA 38 Grad. Rueckgabe RGBA, Mittelpunkt = Bildmitte."""
    size = int(scale_px_per_deg * 4.2) | 1
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32) - size // 2
    pa = math.radians(38)
    # Bildschirm: Norden = -y, Osten = -x. Grosse Achse zeigt nach PA (von Nord ueber Ost)
    ux, uy = -math.sin(pa), -math.cos(pa)
    u = (xx * ux + yy * uy) / scale_px_per_deg                       # Grad entlang grosser Achse
    v = (-xx * uy + yy * ux) / scale_px_per_deg                      # Grad entlang kleiner Achse
    re = np.sqrt(u ** 2 + (v / 0.32) ** 2)
    disk = np.exp(-re / 0.55)
    bulge = np.exp(-np.sqrt(u ** 2 + (v / 0.65) ** 2) / 0.12)
    core = np.exp(-np.sqrt(u ** 2 + v ** 2) / 0.025)
    dust = 1 - 0.35 * np.exp(-((v - 0.07 - 0.02 * u) / 0.025) ** 2) * (np.abs(u) < 1.4)
    I = (0.55 * disk + 0.9 * bulge + 1.2 * core) * dust * gain
    col_disk, col_core = np.array([200, 212, 236]), np.array([255, 236, 204])
    mixk = np.clip(bulge * 1.2, 0, 1)[..., None]
    rgb = col_disk * (1 - mixk) + col_core * mixk
    alpha = np.clip(I, 0, 1) * 255
    return Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), "RGBA")


def fuzzy(img, x, y, r, a):
    m = Image.new("L", (int(4 * r) + 2, int(4 * r) + 2), 0)
    ImageDraw.Draw(m).ellipse([r, r, 3 * r, 3 * r], fill=a)
    m = m.filter(ImageFilter.GaussianBlur(r * 0.6))
    img.paste(Image.new("RGB", m.size, (230, 232, 240)), (int(x - 2 * r), int(y - 2 * r)), m)


def render_sky(w, h, proj, limit, ss=1, mw=True, horizon_glow=True, star_k=1.0, gal_gain=1.0):
    """Himmel in Ausgabe-Groesse w x h (intern ss-fach): Gradient, Milchstrasse, Sterne, Galaxien."""
    W2, H2 = w * ss, h * ss
    p = Proj(math.degrees(proj.ra0), math.degrees(proj.dec0), proj.k / math.degrees(1) * ss, proj.cx * ss, proj.cy * ss)
    t = np.linspace(0, 1, H2)[:, None]
    top, bot = np.array([5, 7, 13]), np.array([16, 20, 34])
    sky = top * (1 - t[..., None]) + bot * t[..., None]
    sky = np.repeat(sky, W2, axis=1).astype(np.float32)
    if horizon_glow:                                                 # Restlicht am Horizont
        glow = np.exp(-np.clip((HOR * ss - np.arange(H2)) / (220 * ss), 0, None))[:, None, None]
        sky += glow * np.array([22, 22, 30])
    if mw:                                                           # Milchstrasse (galaktische Breite)
        step = 4
        ra, dec = p.inverse_grid(W2 // step + 1, H2 // step + 1, step=step)
        b, l = galactic_b(ra, dec)
        rng = np.random.default_rng(5)
        n1 = np.asarray(Image.fromarray((rng.random((H2 // 40 + 2, W2 // 40 + 2)) * 255).astype(np.uint8))
                        .resize(b.shape[::-1], Image.BICUBIC), np.float32) / 255
        n2 = np.asarray(Image.fromarray((rng.random((H2 // 12 + 2, W2 // 12 + 2)) * 255).astype(np.uint8))
                        .resize(b.shape[::-1], Image.BICUBIC), np.float32) / 255
        band = np.exp(-(b / 9.0) ** 2) * (0.55 + 0.6 * n1) * (0.75 + 0.35 * n2)
        rift = 1 - 0.45 * np.exp(-((b - 1.5) / 2.2) ** 2) * (n1 > 0.45)
        mwv = np.clip(band * rift, 0, 1.4)
        mwv = np.asarray(Image.fromarray((mwv * 180).astype(np.uint8)).resize((W2, H2), Image.BICUBIC)
                         .filter(ImageFilter.GaussianBlur(6 * ss)), np.float32) / 180
        sky += mwv[..., None] * np.array([30, 31, 38])
    img = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8), "RGB")
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    ra, dec, m, tint = FAINT
    for i in range(len(ra)):
        if m[i] > limit + 1.2:
            continue
        x, y = p.xy(ra[i], dec[i])
        if -5 <= x < W2 + 5 and -5 <= y < H2 + 5:
            star_disc(d, x, y, m[i], TINTS[tint[i]], limit, k=ss * star_k)
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    for x, y, r, a in [(*p.xy(*M32), 0.06, 70), (*p.xy(*M110), 0.10, 45)]:   # Begleitgalaxien
        fuzzy(img, x, y, max(1.5, r * p.k / math.degrees(1)), a)
    g = galaxy_patch(p.k / math.degrees(1), gain=gal_gain)
    gx, gy = p.xy(*M31)
    img.paste(g, (int(gx - g.width / 2), int(gy - g.height / 2)), g)
    for name, (r_, d_, mag, col) in BRIGHT.items():
        x, y = p.xy(r_, d_)
        if -40 <= x < W2 + 40 and -40 <= y < H2 + 40:
            bright_star(img, x, y, mag, col, k=ss * star_k)
    return img


FAINT = faint_stars()
PROJ = Proj(RA0, DEC0, SCALE, W / 2, CY0)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def background():
    sky = render_sky(W, H, PROJ, limit=6.3, ss=S)
    img = sky
    rnd = random.Random(5)                                           # Horizont mit Baeumen
    d = ImageDraw.Draw(img)
    pts = [(0, H * S)]
    for i in range(41):
        pts.append((W * S * i / 40, (HOR + math.sin(i * 0.35) * 20 + rnd.uniform(-8, 8)) * S))
    pts.append((W * S, H * S))
    d.polygon(pts, fill=(3, 4, 6))
    for x in (W * 0.08, W * 0.18, W * 0.93):
        for k in range(4):
            w = (50 - k * 10) * S
            d.polygon([(x * S - w, (HOR - k * 36 + 10) * S), (x * S + w, (HOR - k * 36 + 10) * S),
                       (x * S, (HOR - (k + 1) * 36 - 14) * S)], fill=(3, 4, 6))
    shade = Image.new("L", img.size, 0)                              # Kopfzeile lesbar halten
    ImageDraw.Draw(shade).rectangle([0, 0, W * S, 560 * S], fill=120)
    shade = shade.filter(ImageFilter.GaussianBlur(60 * S))
    img.paste(Image.new("RGB", img.size, (5, 7, 12)), (0, 0), shade)
    y = header_band(img, ["You can see another GALAXY", "this weekend. No telescope."], "GALAXY")
    d = ImageDraw.Draw(img)
    sub = "Oct 9-11 · New Moon · 2 h after sunset, look northeast"
    d.text(((W * S - d.textlength(sub, font=f(30 * S))) / 2, y + 6 * S), sub, font=f(30 * S), fill=SEC)
    for n, (txt, fo, col) in enumerate([("Save this for Saturday night", f(40 * S, bold=True), FG),
                                        ("Send it to your stargazing buddy", f(32 * S), SEC)]):
        d.text(((W * S - d.textlength(txt, font=fo)) / 2, (HOR + 118 + n * 54) * S), txt, font=fo, fill=col)
    return downscale(img, W, H)


def binocular_view(r_px):
    """Fernglas-Ansicht (7 Grad Gesichtsfeld) um M31, kreisfoermig, mit Rand-Vignette."""
    d = 2 * r_px
    scale = d / 7.0
    p = Proj(M31[0], M31[1], scale, r_px, r_px)
    img = render_sky(d, d, p, limit=9.0, ss=2, mw=False, horizon_glow=False, star_k=0.8, gal_gain=1.6)
    img = img.resize((d, d), Image.LANCZOS)
    m = Image.new("L", (d * 4, d * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, d * 4 - 1, d * 4 - 1], fill=255)
    m = m.resize((d, d), Image.LANCZOS)
    yy, xx = np.mgrid[0:d, 0:d] - r_px
    vig = np.clip(1.15 - 0.45 * (np.sqrt(xx ** 2 + yy ** 2) / r_px) ** 3, 0, 1)
    arr = (np.asarray(img, np.float32) * vig[..., None]).astype(np.uint8)
    out = Image.fromarray(arr, "RGB").convert("RGBA")
    out.putalpha(m)
    return out


def frame(bg, bino, t):
    im = bg.copy().convert("RGBA")
    ov = Image.new("RGBA", (W * 2, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    P = lambda name: tuple(v * 2 for v in PROJ.xy(*BRIGHT[name][:2]))
    fade = 1 - ease((t - 11.2) / 0.8)
    pulse = ease(t / 0.8) * fade * (1 - ease((t - 3.4) / 0.6))
    lines_p, arrow_p, ring_p = ease((t - 1.2) / 2.0), ease((t - 3.6) / 1.6), ease((t - 5.4) / 0.8) * fade
    bino_p = ease((t - 7.0) / 0.8) * fade
    pts = [P(n) for n in W_STARS]
    if pulse > 0:
        for px, py in pts:
            d.ellipse([px - 44, py - 44, px + 44, py + 44], outline=(255, 180, 84, int(170 * pulse)), width=4)
    seg = lines_p * (len(pts) - 1)
    for i in range(len(pts) - 1):
        k = min(1.0, max(0.0, seg - i))
        if k > 0:
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            d.line([ax, ay, ax + (bx - ax) * k, ay + (by - ay) * k], fill=(150, 170, 215, int(150 * fade)), width=4)
    gx, gy = (v * 2 for v in PROJ.xy(*M31))
    sx, sy = P("Schedar")
    if arrow_p > 0:                                                  # Spitze der tieferen V-Haelfte -> M31
        ax, ay = sx, sy + 40
        bx, by = gx, gy - 120
        ex, ey = ax + (bx - ax) * arrow_p, ay + (by - ay) * arrow_p
        col = (255, 180, 84, int(230 * fade))
        d.line([ax, ay, ex, ey], fill=col, width=7)
        if arrow_p > 0.9:
            ang = math.atan2(by - ay, bx - ax)
            for s_ in (-1, 1):
                d.line([ex, ey, ex - math.cos(ang + s_ * 0.5) * 40, ey - math.sin(ang + s_ * 0.5) * 40], fill=col, width=7)
    if ring_p > 0:
        r = 92
        d.ellipse([gx - r, gy - r, gx + r, gy + r], outline=(255, 180, 84, int(220 * ring_p)), width=4)
        fo = f(34 * 2, bold=True)
        tw = d.textlength("Andromeda", font=fo)
        d.text((gx - r - 20 - tw, gy - 36), "Andromeda", font=fo, fill=(255, 180, 84, int(255 * ring_p)),
               stroke_width=4, stroke_fill=(8, 10, 14, int(255 * ring_p)))
    if fade > 0 and t > 0.2:
        fo = f(30 * 2, bold=True)
        d.text((P("Segin")[0] - d.textlength("Cassiopeia", font=fo) - 30, P("Segin")[1] + 30), "Cassiopeia", font=fo,
               fill=(200, 210, 230, int(220 * min(1.0, lines_p * 2) * fade)), stroke_width=4, stroke_fill=(8, 10, 14, 200))
    lab = [("1 · Find the bright 'W' (Cassiopeia)", 0.0, 3.6), ("2 · Follow the deeper V down", 3.6, 5.4),
           ("3 · A faint, fuzzy smudge = Andromeda", 5.4, 7.0), ("Binoculars make it bigger", 7.0, 8.8),
           ("Its light left 2.5 million years ago", 8.8, 11.2)]
    for txt, a, b in lab:
        al = ease((t - a) / 0.35) * ((1 - ease((t - b) / 0.35)) if b < 11.2 else fade)
        if al > 0:
            fo = f(46 * 2, bold=True)
            col = ACC if txt.startswith("Its") else FG
            tw = d.textlength(txt, font=fo)
            d.text(((W * 2 - tw) / 2, (HOR + 28) * 2), txt, font=fo, fill=col + (int(255 * al),),
                   stroke_width=4, stroke_fill=(3, 4, 6, int(255 * al)))
    ov = ov.resize((W, H), Image.LANCZOS)
    if bino_p > 0:                                                   # Fernglas-Kreis rechts neben der Galaxie
        bx, by, br = 845, 1080, bino.width // 2
        b2 = bino.copy()
        b2.putalpha(bino.getchannel("A").point(lambda v: int(v * bino_p)))
        im.alpha_composite(b2, (bx - br, by - br))
        d2 = ImageDraw.Draw(im)
        d2.ellipse([bx - br, by - br, bx + br, by + br], outline=(255, 180, 84, int(255 * bino_p)), width=3)
        g1 = PROJ.xy(*M31)
        d2.line([g1[0] + 48, g1[1] - 10, bx - br * 0.72, by + br * 0.7], fill=(255, 180, 84, int(200 * bino_p)), width=2)
        fo = f(24, bold=True)
        tw = d2.textlength("7° binocular view", font=fo)
        d2.text((bx - tw / 2, by + br + 8), "7° binocular view", font=fo, fill=(200, 210, 230, int(255 * bino_p)))
    im.alpha_composite(ov)
    return im.convert("RGB")


def main():
    bg = background()
    bino = binocular_view(150)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = OUT / "w6-andromeda-weekend-loop.mp4"
    n = int(LOOP * FPS)
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(frame(bg, bino, i / FPS).tobytes())
    proc.stdin.close()
    proc.wait()
    frame(bg, bino, 7.9).save(OUT / "w6-andromeda-weekend-loop-cover.png")
    chk = Path(os.environ.get("CHECK_DIR", OUT))
    for t in (0.1, 4.8):
        frame(bg, bino, t).save(chk / f"_check-{t:.1f}.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
