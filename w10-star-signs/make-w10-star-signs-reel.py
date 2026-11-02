"""Woche 10, Montag 02.11.2026 - "Your star sign is probably WRONG" (Identitaet + Finde-dein-Datum).

Neue Regel: das Reel braucht einen Empfaenger -> jeder sucht sein Geburtsdatum und schickt es dem Freund,
der Horoskope liest. Raster ab Frame 1 sichtbar, Sonne laeuft einmal durchs Jahr, Vergleich Horoskop/Himmel
je Datum, Aufloesung Ophiuchus.

Hook-Varianten:
  1. Your star sign is probably WRONG                       <- gewaehlt (Identitaet, kurz)
  2. The Sun wasn't in your sign when you were born
  3. There are 13 star signs. Nobody told you.
  4. Scorpio lasts 7 days
  5. Find your birthday. Your horoscope won't like it.

Fakten: Sonne je Sternbild fuer 2026 aus den IAU-Grenzen berechnet (astropy get_sun + get_constellation,
stuendlich), Eintritt je +/- 1 Tag je Jahr. Horoskop-Daten = uebliche tropische Grenzen. Abweichung an 325
von 365 Tagen (89 %), Tagesvergleich 12 UTC. Sternbildlinien: d3-celestial (BSD-3, Olaf Frohn).

    python make-w10-star-signs-reel.py  ->  w10-star-signs.mp4, -cover.png
    CHECK_DIR=... CHECK_ONLY=1          ->  nur Schluesselbilder
"""

import datetime as dt
import json
import math
import os
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from brandkit import S, FG, SEC, ACC, HAIR, f, downscale
from reelkit import W as CW, H as CH, deep_sky, header_band, cinematic
from bodies import star
from brandkit import canvas

OUT = Path(__file__).resolve().parent
W, H, FPS, LOOP = 1080, 1920, 30, 16.0
T_START, T_YEAR, T_CTA = 0.5, 12.5, 13.0     # Jahreslauf 0,5-13 s, danach Aufloesung/CTA

# Kurz-ID, Anzeigename, Eintritt der Sonne 2026 (Monat, Tag), Datumstext
SIGNS = [
    ("Cap", "Capricorn", (1, 20), "Jan 20 – Feb 15"),
    ("Aqr", "Aquarius", (2, 16), "Feb 16 – Mar 11"),
    ("Psc", "Pisces", (3, 12), "Mar 12 – Apr 18"),
    ("Ari", "Aries", (4, 19), "Apr 19 – May 13"),
    ("Tau", "Taurus", (5, 14), "May 14 – Jun 20"),
    ("Gem", "Gemini", (6, 21), "Jun 21 – Jul 20"),
    ("Cnc", "Cancer", (7, 21), "Jul 21 – Aug 10"),
    ("Leo", "Leo", (8, 11), "Aug 11 – Sep 16"),
    ("Vir", "Virgo", (9, 17), "Sep 17 – Oct 30"),
    ("Lib", "Libra", (10, 31), "Oct 31 – Nov 22"),
    ("Sco", "Scorpio", (11, 23), "Only Nov 23 – 29"),
    ("Sgr", "Sagittarius", (12, 18), "Dec 18 – Jan 19"),
    ("Oph", "Ophiuchus", (11, 30), "Nov 30 – Dec 17"),
]
NAME = {s[0]: s[1] for s in SIGNS}
TROPICAL = [((1, 20), "Aquarius"), ((2, 19), "Pisces"), ((3, 21), "Aries"), ((4, 20), "Taurus"), ((5, 21), "Gemini"),
            ((6, 21), "Cancer"), ((7, 23), "Leo"), ((8, 23), "Virgo"), ((9, 23), "Libra"), ((10, 23), "Scorpio"),
            ((11, 22), "Sagittarius"), ((12, 22), "Capricorn")]
ORDER = sorted(SIGNS, key=lambda s: s[2])    # Reihenfolge am Himmel


def real_sign(d):
    cur = "Sgr"
    for s in ORDER:
        if (d.month, d.day) >= s[2]:
            cur = s[0]
    return cur


def horoscope(d):
    cur = "Capricorn"
    for md, n in TROPICAL:
        if (d.month, d.day) >= md:
            cur = n
    return cur


def sun_radec(d):
    """Sonnenposition aus der Standard-Naeherung (Astronomical Almanac), genau auf ~0,01 Grad."""
    n = (d - dt.date(2000, 1, 1)).days + 0.0
    L = 280.460 + 0.9856474 * n
    g = math.radians(357.528 + 0.9856003 * n)
    lam = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    eps = math.radians(23.439)
    return math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam)), math.asin(math.sin(eps) * math.sin(lam))


def vec(ra, dec):
    return np.array([math.cos(dec) * math.cos(ra), math.cos(dec) * math.sin(ra), math.sin(dec)])


class Fig:
    """Sternbild in Zellen-Koordinaten: gnomonisch um den Schwerpunkt, Norden oben, Osten links."""

    def __init__(self, key, data, days):
        feat = next(x for x in data["features"] if x["id"] == key)
        self.lines = [[vec(math.radians(p[0]), math.radians(p[1])) for p in ln] for ln in feat["geometry"]["coordinates"]]
        pts = [p for ln in self.lines for p in ln]
        c = np.mean(pts, axis=0)
        self.c = c / np.linalg.norm(c)
        self.e = np.cross([0, 0, 1.0], self.c)
        self.e /= np.linalg.norm(self.e)
        self.n = np.cross(self.c, self.e)
        self.path = [(d, vec(*sun_radec(d))) for d in days]

    def xy(self, v):
        k = np.dot(v, self.c)
        return -np.dot(v, self.e) / k, -np.dot(v, self.n) / k

    def fit(self, box):
        pts = [self.xy(p) for ln in self.lines for p in ln] + [self.xy(v) for _, v in self.path]
        x0, x1 = min(p[0] for p in pts), max(p[0] for p in pts)
        y0, y1 = min(p[1] for p in pts), max(p[1] for p in pts)
        k = min((box[2] - box[0]) / (x1 - x0), (box[3] - box[1]) / (y1 - y0))
        ox = (box[0] + box[2]) / 2 - k * (x0 + x1) / 2
        oy = (box[1] + box[3]) / 2 - k * (y0 + y1) / 2
        self.map = lambda v: (ox + k * self.xy(v)[0], oy + k * self.xy(v)[1])


GX0, GX1, GY0 = 56, 1006, 576
CELL_W, CELL_H, GAP = (GX1 - GX0 - 2 * 10) / 3, 166, 10


def cell_box(i):
    if i == 12:
        y = GY0 + 4 * (CELL_H + GAP)
        return GX0, y, GX1, y + CELL_H
    x = GX0 + (i % 3) * (CELL_W + 10)
    y = GY0 + (i // 3) * (CELL_H + GAP)
    return x, y, x + CELL_W, y + CELL_H


def build_figs():
    data = json.loads((OUT / "constellations.lines.json").read_text(encoding="utf-8"))
    year = [dt.date(2026, 1, 1) + dt.timedelta(days=i) for i in range(365)]
    figs = {}
    for i, s in enumerate(SIGNS):
        days = [d for d in year if real_sign(d) == s[0]]
        if s[0] == "Sgr":
            days = sorted(days, key=lambda d: (d.month < 6, d))      # Dez vor Jan
        fg = Fig(s[0], data, days)
        x0, y0, x1, y1 = cell_box(i)
        fg.fit((x0 + 12, y0 + 12, x0 + 128, y1 - 12) if i < 12 else (x0 + 24, y0 + 10, x0 + 214, y1 - 10))
        figs[s[0]] = fg
    return figs


FIGS = build_figs()


def fig_layer(key, col, a_line, a_star, r_star):
    ss = 3
    im = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    fg = FIGS[key]
    pts = [fg.map(v) for _, v in fg.path]
    for p, q in zip(pts[::2], pts[1::2]):                            # Sonnenbahn gestrichelt
        d.line([p[0] * ss, p[1] * ss, q[0] * ss, q[1] * ss], fill=ACC + (70,), width=2 * ss // 2)
    for ln in fg.lines:
        xy = [fg.map(p) for p in ln]
        d.line([(x * ss, y * ss) for x, y in xy], fill=col + (a_line,), width=int(1.6 * ss), joint="curve")
    for ln in fg.lines:
        for p in ln:
            x, y = fg.map(p)
            r = r_star * ss
            d.ellipse([x * ss - r, y * ss - r, x * ss + r, y * ss + r], fill=(255, 255, 255, a_star))
    return im.resize((W, H), Image.LANCZOS)


def sun_sprite(d_px):
    k = S
    size = int(d_px * 6)
    box = Image.new("RGB", (size * k, size * k), (0, 0, 0))
    star(box, size * k // 2, size * k // 2, d_px, "sun")
    return box.resize((size, size), Image.LANCZOS)


def add_screen(im, sprite, cx, cy):
    x, y = int(cx - sprite.width / 2), int(cy - sprite.height / 2)
    box = (x, y, x + sprite.width, y + sprite.height)
    im.paste(ImageChops.screen(im.crop(box), sprite), box)


def background():
    img, _ = canvas(CW, CH)
    deep_sky(img, 104, band=(0.72, 0.30))
    shade = Image.new("L", img.size, 0)
    ImageDraw.Draw(shade).rectangle([0, 0, CW, 560 * S], fill=125)
    shade = shade.filter(ImageFilter.GaussianBlur(50 * S))
    img.paste(Image.new("RGB", img.size, (5, 7, 12)), (0, 0), shade)
    shade = Image.new("L", img.size, 0)                  # Vergleichszeile unter dem Raster lesbar halten
    ImageDraw.Draw(shade).rectangle([0, 1450 * S, CW, 1600 * S], fill=225)
    shade = shade.filter(ImageFilter.GaussianBlur(14 * S))
    img.paste(Image.new("RGB", img.size, (5, 7, 12)), (0, 0), shade)
    header_band(img, ["Your star sign is", "probably WRONG"], "WRONG", y=236 * S)
    d = ImageDraw.Draw(img, "RGBA")
    for i, s in enumerate(SIGNS):
        x0, y0, x1, y1 = cell_box(i)
        d.rounded_rectangle([x0 * S, y0 * S, x1 * S, y1 * S], 16 * S, fill=(12, 16, 26, 205), outline=HAIR + (255,), width=2)
        if i < 12:
            tx = (x0 + 138) * S
            d.text((tx, (y0 + 44) * S), s[1], font=f(30 * S, bold=True), fill=FG)
            d.text((tx, (y0 + 88) * S), s[3].replace(" – ", "–"), font=f(23 * S), fill=SEC)
        else:
            tx = (x0 + 238) * S
            d.text((tx, (y0 + 18) * S), "THE 13TH SIGN", font=f(25 * S, bold=True), fill=ACC)
            d.text((tx, (y0 + 50) * S), s[1], font=f(44 * S, bold=True), fill=FG)
            d.text((tx, (y0 + 112) * S), s[3].replace(" – ", "–") + " · not in your horoscope", font=f(25 * S), fill=SEC)
    return downscale(img, W, H)


BG = background()
DIM = {s[0]: fig_layer(s[0], (150, 170, 215), 120, 170, 1.5) for s in SIGNS}
LIT = {s[0]: fig_layer(s[0], (255, 214, 150), 255, 255, 2.2) for s in SIGNS}
SUN_S, SUN_L = sun_sprite(26), sun_sprite(34)
_days_static = None


def date_at(t):
    u = min(1.0, max(0.0, (t - T_START) / T_YEAR))
    return dt.date(2026, 1, 1) + dt.timedelta(days=min(364, int(u * 365)))


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def frame(t):
    day = date_at(t)
    key = real_sign(day)
    done = t >= T_YEAR + T_START
    im = BG.copy().convert("RGBA")
    seen = {real_sign(dt.date(2026, 1, 1) + dt.timedelta(days=i)) for i in range((day - dt.date(2026, 1, 1)).days + 1)}
    for s in SIGNS:
        im.alpha_composite(LIT[s[0]] if s[0] in seen else DIM[s[0]])
    d = ImageDraw.Draw(im, "RGBA")
    i = next(n for n, s in enumerate(SIGNS) if s[0] == key)
    show_oph = done or key == "Oph"
    if not done:
        x0, y0, x1, y1 = cell_box(i)
        d.rounded_rectangle([x0, y0, x1, y1], 16, outline=ACC + (255,), width=4)
    else:
        x0, y0, x1, y1 = cell_box(12)
        pulse = 0.55 + 0.45 * math.sin((t - T_CTA) * 3.2)
        d.rounded_rectangle([x0, y0, x1, y1], 16, outline=ACC + (int(255 * pulse),), width=4)
    im = im.convert("RGB")
    if not done:
        fg = FIGS[key]
        p = next((v for dd, v in fg.path if dd == day), fg.path[0][1])
        add_screen(im, SUN_S, *fg.map(p))

    d = ImageDraw.Draw(im)
    sub, col = (("Find your birthday: that's where the Sun really was", SEC) if not done else
                ("On about 9 of 10 days, the Sun isn't in your horoscope sign", ACC))
    fo = f(31)
    d.text(((W - d.textlength(sub, font=fo)) / 2, 504), sub, font=fo, fill=col)
    y = GY0 + 5 * (CELL_H + GAP) + 6
    if t < T_CTA + 0.2:
        al = 1 - ease((t - T_CTA) / 0.2)
        k = lambda c: tuple(int(v * al) for v in c)
        d.text((GX0 + 8, y + 4), day.strftime("%b %d").upper(), font=f(58, bold=True), fill=k(FG))
        fo, fb = f(30), f(34, bold=True)
        h, r = horoscope(day), NAME[key]
        x = GX0 + 262
        d.text((x, y + 0), "Your horoscope says", font=fo, fill=k(SEC))
        d.text((x + d.textlength("Your horoscope says  ", font=fo), y - 3), h, font=fb, fill=k(FG))
        d.text((x, y + 42), "The Sun is really in", font=fo, fill=k(SEC))
        d.text((x + d.textlength("Your horoscope says  ", font=fo), y + 39), r, font=fb, fill=k(ACC))
    else:
        al = ease((t - T_CTA - 0.2) / 0.35)
        k = lambda c: tuple(int(v * al) for v in c)
        for n, (s, fo, c) in enumerate([("Send this to the friend who reads their horoscope", f(38, bold=True), FG),
                                        ("Save it for the next time someone asks your sign", f(30), ACC)]):
            d.text(((W - d.textlength(s, font=fo)) / 2, y + n * 50), s, font=fo, fill=k(c))
    return im


def main():
    chk = Path(os.environ.get("CHECK_DIR", OUT))
    for t in (0.1, 11.3, 11.9, 15.0):
        cinematic(frame(t), 0).save(chk / f"_check-signs-{t:.1f}.png")
    if os.environ.get("CHECK_ONLY"):
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = OUT / "w10-star-signs.mp4"
    n = int(LOOP * FPS)
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart",
        str(out)], stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(11.3), 0).save(OUT / "w10-star-signs-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
