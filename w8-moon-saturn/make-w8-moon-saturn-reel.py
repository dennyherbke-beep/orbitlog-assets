"""Woche 8, Ersatz-Reel "Diese Woche am Himmel" (Andromeda-Muster: realistischer Himmel + Termin + Handlung):
der fast volle Mond steht am Fr 23. und Sa 24.10.2026 abends neben Saturn.

Hook-Varianten:
  1. This Friday the Moon points you to SATURN          <- gewaehlt (Termin + Handlung)
  2. That bright "star" next to the Moon on Friday? It's Saturn.
  3. You can see Saturn this weekend - the Moon shows you where
  4. Look left of the Moon on Friday night
  5. The Moon's light is 1 second old. Saturn's is 71 minutes.

Szene (14 s Loop): Blick nach Suedosten, Berlin 21:00 MESZ (19:00 UTC), Hoehe/Azimut gnomonisch, Horizont
unten. Mond und Saturn an den JPL-Horizons-Positionen (topozentrisch Berlin), Hintergrundsterne J2000 ueber
Sternzeit umgerechnet. Fr -> Sa: Mond wandert eine Nacht weiter (gleiche Uhrzeit), danach Lichtlaufzeiten,
danach Teleskop-Einblendung mit Ringen. Mond 8x vergroessert (im Bild vermerkt).

Fakten (JPL Horizons, abgerufen 17.10.2026):
  Fr 23.10. 19:00 UTC: Mond Az 145,4 / Hoehe 33,9 (~95 %), Saturn Az 133,2 / 29,3 -> Saturn ~11 Grad links unten
  Sa 24.10. 19:00 UTC: Mond Az 129,7 / 35,0 (~98 %), Saturn Az 134,3 / 29,7 -> Saturn ~6,5 Grad darunter
  (USA ~21 Uhr EDT: Fr ~8 Grad links unten, Sa ~9 Grad unten rechts - "below" passt fuer beide)
  Saturn 0,4 mag, 8,49 AE = 1,27 Mrd. km, Licht 70,6 min; Mond 380.000 km, Licht 1,27 s;
  Ringneigung ~7,4 Grad (Astronomy.com, Okt. 2026). Vollmond 26.10. 04:11 UTC.

    python make-w8-moon-saturn-reel.py  ->  w8-moon-saturn.mp4, -cover.png
    CHECK_ONLY=1 CHECK_DIR=<dir>         ->  nur Kontroll-Frames
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
from bodies import planet

_spec = importlib.util.spec_from_file_location("andro", ROOT / "w6-andromeda-weekend" / "make-w6-andromeda-weekend-loop.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)
hms, dms = A.hms, A.dms

OUT = Path(__file__).resolve().parent
W, H, FPS, LOOP = 1080, 1920, 30, 14.0
HOR = 1400
AZ0, ALT0, SCALE = 138.0, 17.0, 20.0                # Bildmitte (Grad), px pro Grad
PROJ = A.Proj(-AZ0, ALT0, SCALE, W / 2, 1050)       # Proj erwartet "Osten links" -> Azimut negativ einsetzen
LAT, LON = 52.5, 13.4
JD = 2461337.2917                                   # 2026-10-23 19:00 UTC
MOON_D = 80                                         # px, 8x vergroessert (echt ~10 px)

MOON_FRI, MOON_SAT = (145.390, 33.863), (129.717, 34.980)
SAT_FRI, SAT_SAT = (133.202, 29.288), (134.299, 29.727)

STARS = {   # J2000, mag
    "Fomalhaut": (hms(22, 57, 39.0), -dms(29, 37, 20), 1.16, (238, 242, 255)),
    "Diphda": (hms(0, 43, 35.4), -dms(17, 59, 12), 2.04, (255, 222, 186)),
    "Markab": (hms(23, 4, 45.7), dms(15, 12, 19), 2.49, (226, 234, 255)),
    "Scheat": (hms(23, 3, 46.5), dms(28, 4, 58), 2.42, (255, 196, 150)),
    "Algenib": (hms(0, 13, 14.2), dms(15, 11, 1), 2.83, (214, 226, 255)),
    "Alpheratz": (hms(0, 8, 23.3), dms(29, 5, 26), 2.06, (225, 234, 255)),
    "Hamal": (hms(2, 7, 10.4), dms(23, 27, 45), 2.00, (255, 206, 160)),
    "Sheratan": (hms(1, 54, 38.4), dms(20, 48, 29), 2.64, (240, 244, 255)),
    "Menkar": (hms(3, 2, 16.8), dms(4, 5, 23), 2.54, (255, 190, 140)),
    "Enif": (hms(21, 44, 11.2), dms(9, 52, 30), 2.39, (255, 204, 156)),
    "Sadalmelik": (hms(22, 5, 47.0), -dms(0, 19, 11), 2.94, (255, 232, 196)),
    "Sadalsuud": (hms(21, 31, 33.5), -dms(5, 34, 16), 2.90, (255, 236, 210)),
    "Deneb Algedi": (hms(21, 47, 2.4), -dms(16, 7, 38), 2.87, (240, 244, 255)),
    "Baten Kaitos": (hms(1, 51, 27.6), -dms(10, 20, 6), 3.73, (255, 214, 170)),
    "gamma Psc": (hms(23, 17, 9.9), dms(3, 16, 57), 3.69, (255, 220, 180)),
    "Alrescha": (hms(2, 2, 2.8), dms(2, 45, 49), 3.82, (235, 240, 255)),
}


def altaz(ra, dec):
    """J2000-RA/Dec (Grad) -> Azimut (von Nord ueber Ost) / Hoehe fuer Berlin, 23.10.2026 19:00 UTC."""
    gmst = (280.46061837 + 360.98564736629 * (JD - 2451545.0)) % 360
    ha = math.radians(gmst + LON - ra)
    d, la = math.radians(dec), math.radians(LAT)
    alt = math.asin(math.sin(d) * math.sin(la) + math.cos(d) * math.cos(la) * math.cos(ha))
    az = math.atan2(-math.cos(d) * math.sin(ha), math.sin(d) * math.cos(la) - math.cos(d) * math.sin(la) * math.cos(ha))
    return math.degrees(az) % 360, math.degrees(alt)


def xy(az, alt, k=1.0):
    x, y = PROJ.xy(-az, alt)
    return x * k, y * k


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def lerp(a, b, u):
    return tuple(p + (q - p) * u for p, q in zip(a, b))


def faint_field(rng, n=700):
    """Wenige schwache Sterne (Mondlicht: Grenzgroesse ~4,5), gleichverteilt im Bild."""
    out = []
    for _ in range(n):
        m = 3.6 + math.log10(1 + rng.random() * (10 ** (0.5 * 1.4) - 1)) / 0.5
        out.append((rng.uniform(0, W), rng.uniform(560, HOR), m, A.TINTS[rng.randrange(4)]))
    return out


def background():
    """Himmel ohne Mond/Saturn: Verlauf, Mondlicht-Aufhellung (am Fr/Sa-Mittel), Sterne, Horizont, Texte."""
    W2, H2 = W * S, H * S
    yy, xx = np.mgrid[0:H2, 0:W2].astype(np.float32)
    t = yy / H2
    sky = np.stack([7 + 13 * t, 10 + 18 * t, 20 + 28 * t], -1)
    mx, my = xy(*lerp(MOON_FRI, MOON_SAT, 0.5), S)
    r = np.sqrt((xx - mx) ** 2 + (yy - my) ** 2) / S
    sky += (np.exp(-r / 260) * 34)[..., None] * np.array([0.75, 0.85, 1.0])   # Mondlicht streut im Himmel
    sky += (np.exp(-np.clip((HOR * S - yy) / (220 * S), 0, None)) * 18)[..., None] * np.array([1.0, 1.0, 1.25])
    img = Image.fromarray(np.clip(sky, 0, 255).astype(np.uint8), "RGB")
    ov = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for x, y, m, col in faint_field(random.Random(4)):
        A.star_disc(d, x * S, y * S, m, col, 4.6, k=S)
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img, "RGBA")
    pos = {n: altaz(ra, de) for n, (ra, de, *_) in STARS.items()}
    for n, (ra, de, mag, col) in STARS.items():
        az, alt = pos[n]
        if alt > 0 and xy(az, alt)[1] > 600:                            # nicht in die Kopfzeile
            x, y = xy(az, alt, S)
            A.bright_star(img, x, y, max(mag, 0.0), col, k=S * 0.9)
    d = ImageDraw.Draw(img, "RGBA")
    st = dict(stroke_width=3 * S, stroke_fill=(5, 6, 10))
    fx, fy = xy(*pos["Fomalhaut"], S)
    if fy < HOR * S:
        d.text((fx + 16 * S, fy - 12 * S), "Fomalhaut", font=f(24 * S, bold=True), fill=(170, 182, 210), **st)
    rnd = random.Random(8)                                              # Horizont mit Baeumen + Haus
    pts = [(0, H * S)] + [(W * S * i / 40, (HOR + math.sin(i * 0.5 + 2) * 16 + rnd.uniform(-7, 7)) * S)
                          for i in range(41)] + [(W * S, H * S)]
    d.polygon(pts, fill=(3, 4, 6))
    for x in (W * 0.05, W * 0.13, W * 0.90):
        for k in range(4):
            w = (44 - k * 9) * S
            d.polygon([(x * S - w, (HOR - k * 32 + 10) * S), (x * S + w, (HOR - k * 32 + 10) * S),
                       (x * S, (HOR - (k + 1) * 32 - 12) * S)], fill=(3, 4, 6))
    hx = W * 0.62
    d.rectangle([hx * S, (HOR - 70) * S, (hx + 130) * S, (HOR + 10) * S], fill=(3, 4, 6))
    d.polygon([((hx - 12) * S, (HOR - 70) * S), ((hx + 142) * S, (HOR - 70) * S), ((hx + 65) * S, (HOR - 122) * S)],
              fill=(3, 4, 6))
    d.rectangle([(hx + 22) * S, (HOR - 48) * S, (hx + 46) * S, (HOR - 26) * S], fill=(120, 92, 48))
    for az in (90, 135, 180):                                           # Himmelsrichtungen am Horizont
        x, _ = xy(az, 0.5, S)
        lab = {90: "E", 135: "SE", 180: "S"}[az]
        if 20 * S < x < (W - 20) * S:
            d.text((x - d.textlength(lab, font=f(24 * S, bold=True)) / 2, (HOR + 14) * S), lab,
                   font=f(24 * S, bold=True), fill=(130, 140, 160))
    shade = Image.new("L", img.size, 0)                                 # Kopfzeile lesbar halten
    ImageDraw.Draw(shade).rectangle([0, 0, W * S, 560 * S], fill=120)
    shade = shade.filter(ImageFilter.GaussianBlur(60 * S))
    img.paste(Image.new("RGB", img.size, (5, 7, 12)), (0, 0), shade)
    y = header_band(img, ["This Friday the Moon", "points you to SATURN"], "SATURN")
    d = ImageDraw.Draw(img)
    sub = "Fri Oct 23 + Sat Oct 24 · after dark · look southeast"
    d.text(((W * S - d.textlength(sub, font=f(30 * S))) / 2, y + 6 * S), sub, font=f(30 * S), fill=SEC)
    note = "Moon enlarged 8x · view around 9 p.m. local time"
    d.text((W * S - 30 * S - d.textlength(note, font=f(20 * S)), (HOR - 150) * S), note, font=f(20 * S), fill=SEC)
    for n, (txt, fo, col) in enumerate([("Save this for Friday night", f(40 * S, bold=True), FG),
                                        ("Send it to someone you'd show Saturn to", f(32 * S), SEC)]):
        d.text(((W * S - d.textlength(txt, font=fo)) / 2, (HOR + 160 + n * 54) * S), txt, font=fo, fill=col)
    return downscale(img, W, H)


def moon_sprite(light):
    pad = 40
    can = Image.new("RGB", ((MOON_D + 2 * pad) * S, (MOON_D + 2 * pad) * S), (0, 0, 0))
    planet(can, can.width // 2, can.height // 2, MOON_D, "moon", light=light, glow=False)
    spr = np.asarray(downscale(can, MOON_D + 2 * pad, MOON_D + 2 * pad), np.float32) * 1.7   # fast voll = gleissend hell
    return Image.fromarray(np.clip(spr, 0, 255).astype(np.uint8), "RGB")


def scope_view(d_view=330):
    """Teleskop-Einblick: Saturn mit Ringen (7,4 Grad), rundes Okularfeld."""
    can = Image.new("RGB", (d_view * S, d_view * S), (4, 5, 8))
    planet(can, can.width // 2, can.height // 2, 112, "saturn", light=(0.08, -0.03, 1.0), ring_tilt=7.4)
    spr = downscale(can, d_view, d_view)
    m = Image.new("L", (d_view * 4, d_view * 4), 0)
    ImageDraw.Draw(m).ellipse([0, 0, d_view * 4 - 1, d_view * 4 - 1], fill=255)
    return spr, m.resize((d_view, d_view), Image.LANCZOS)


MOON_FRI_SPR = moon_sprite((0.42, 0.22, 0.88))     # Phasenwinkel ~29 Grad, Sonne rechts unten unter dem Horizont
MOON_SAT_SPR = moon_sprite((0.27, 0.14, 0.95))     # ~17 Grad
SCOPE, SCOPE_MASK = scope_view()


def paste_moon(im, spr, x, y, a):
    if a <= 0:
        return
    m = spr.convert("L").point(lambda p: min(255, p * 3))
    m = m.point(lambda p: int(p * a))
    im.paste(spr, (int(x - spr.width / 2), int(y - spr.height / 2)), m)


def label(d, txt, x, y, al, col=FG, size=30, anchor="l"):
    fo = f(size, bold=True)
    if anchor == "c":
        x -= d.textlength(txt, font=fo) / 2
    elif anchor == "r":
        x -= d.textlength(txt, font=fo)
    d.text((x, y), txt, font=fo, fill=col + (int(255 * al),), stroke_width=3, stroke_fill=(5, 6, 10, int(255 * al)))


def frame(bg, t):
    go = ease((t - 3.6) / 1.2) * (1 - ease((t - 13.2) / 0.8))          # 0 = Freitag, 1 = Samstag
    moon = lerp(MOON_FRI, MOON_SAT, go)
    sat = lerp(SAT_FRI, SAT_SAT, go)
    mx, my = xy(*moon)
    sx, sy = xy(*sat)
    im = bg.copy()
    glow = Image.new("L", (W, H), 0)                                    # Mondhof
    gd = ImageDraw.Draw(glow)
    for rr, a in ((190, 30), (115, 58), (70, 110)):
        gd.ellipse([mx - rr, my - rr, mx + rr, my + rr], fill=a)
    glow = glow.filter(ImageFilter.GaussianBlur(40))
    im.paste(Image.new("RGB", (W, H), (190, 200, 222)), (0, 0), glow)
    paste_moon(im, MOON_FRI_SPR, mx, my, 1 - go)
    paste_moon(im, MOON_SAT_SPR, mx, my, go)
    A.bright_star(im, sx, sy, 0.4, (255, 226, 170), k=1.0)             # Saturn: ruhiger, gelblicher Punkt
    im = im.convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    mark = ease(t / 0.4) * (1 - ease((t - 10.4) / 0.4)) + ease((t - 13.3) / 0.4)
    if mark > 0:                                                        # Saturn markieren
        r = 22 + 3 * math.sin(t * 4)
        d.ellipse([sx - r, sy - r, sx + r, sy + r], outline=ACC + (int(255 * mark),), width=3)
        label(d, "Saturn", sx - r - 14, sy - 18, mark, ACC, 30, "r")
        label(d, "Moon", mx + MOON_D / 2 + 22, my - 18, mark, FG, 30)
    if 4.8 > t > 3.7:                                                   # Hinweis waehrend des Sprungs
        al = ease((t - 3.7) / 0.3) * (1 - ease((t - 4.5) / 0.3))
        label(d, "next night, same time", mx, my + MOON_D / 2 + 26, al, SEC, 26, "c")
    dist = ease((t - 7.6) / 0.4) * (1 - ease((t - 10.2) / 0.4))
    if dist > 0:                                                        # Lichtlaufzeiten
        label(d, "light: 1.3 seconds old", mx + MOON_D / 2 + 22, my + 18, dist, SEC, 26)
        label(d, "light: 71 minutes old", sx - 30, sy + 24, dist, ACC, 26, "r")
    ins = ease((t - 10.4) / 0.5) * (1 - ease((t - 13.0) / 0.4))
    if ins > 0:                                                         # Teleskop-Einblick
        cx, cy, R = 790, 940, SCOPE.width // 2
        d.line([sx + 14, sy + 6, cx - R * 0.94, cy - R * 0.34], fill=ACC + (int(160 * ins),), width=2)
        im.alpha_composite(ov)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        im.paste(SCOPE, (cx - R, cy - R), SCOPE_MASK.point(lambda p: int(p * ins)))
        d.ellipse([cx - R - 3, cy - R - 3, cx + R + 3, cy + R + 3], outline=(150, 160, 185, int(255 * ins)), width=5)
        label(d, "small telescope, 25x+", cx, cy + R + 14, ins, SEC, 24, "c")
    im.alpha_composite(ov)
    d = ImageDraw.Draw(im)
    lab = [("1 · Friday: Saturn lower left of the Moon", 0.0, 3.6),
           ("2 · Saturday: Saturn right below the Moon", 4.8, 7.6),
           ("Saturn is 3,300x farther away than the Moon", 7.6, 10.4),
           ("3 · Any small telescope shows its rings", 10.4, 13.2)]
    for txt, a, b in lab:
        al = ease((t - a) / 0.35) * (1 - ease((t - b) / 0.35))
        if a == 0.0:
            al = max(al, ease((t - 13.4) / 0.4))
        if al > 0:
            fo = f(40, bold=True)
            col = ACC if txt.startswith("Saturn is") else FG
            d.text(((W - d.textlength(txt, font=fo)) / 2, HOR + 64), txt, font=fo, fill=col + (int(255 * al),),
                   stroke_width=3, stroke_fill=(3, 4, 6, int(255 * al)))
    return im.convert("RGB")


def main():
    bg = background()
    chk = Path(os.environ.get("CHECK_DIR", OUT))
    for t in (2.0, 6.0, 9.0, 11.8):
        cinematic(frame(bg, t), 0).save(chk / f"_check-moon-saturn-{t:.1f}.png")
    if os.environ.get("CHECK_ONLY"):
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = OUT / "w8-moon-saturn.mp4"
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
    cinematic(frame(bg, 2.0), 0).save(OUT / "w8-moon-saturn-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
