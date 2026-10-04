"""Woche 6, Donnerstag - Reel "If an asteroid were heading for Earth - we already know how to push
it away" (Typ e Bedrohung -> Aufloesung, docs/reel-algorithmus.md). Eine durchgehende Animation unter
fester Kopfzeile: Asteroid auf Kollisionskurs -> Raumsonde trifft ihn -> Bahn knickt ab, verfehlt die
Erde -> Beleg: NASA DART 2022. ~17,5 s.

Fakten (NASA DART / Planetary Defense, ESA; Sky & Telescope 2023):
  DART traf am 26.09.2022 mit 6,1 km/s (~22.000 km/h) den ~150 m grossen Asteroidenmond Dimorphos
  (umkreist Didymos, ~780 m). Umlaufzeit von 11 h 55 min auf 11 h 23 min verkuerzt (-32 min; Mindest-
  ziel waren 73 s). Erstes Mal, dass Menschen die Bewegung eines Himmelskoerpers gezielt veraendert
  haben. Didymos/Dimorphos waren nie eine Gefahr fuer die Erde - es war ein Test.
  Darstellung: Szenario ausdruecklich hypothetisch ("If ..."); Ablenkung im Bild stark ueberzeichnet
  (real: winzige Aenderung, die ueber Jahre zum Verfehlen anwaechst) -> first_comment.

Hook-Varianten:
  1 "If an asteroid were heading for Earth - we already know how to push it away" (gewaehlt)
  2 "We already crashed a spacecraft into an asteroid. On purpose."   3 "How to save Earth from an asteroid"
  4 "This is how we'd stop an asteroid"   5 "Humans have already moved an asteroid"

    python make-w6-asteroid-dart-reel.py  ->  w6-asteroid-dart.mp4, -cover.png
"""

import math
import random
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, downscale
from bodies import planet
from reelkit import new_frame, header_band, blob

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
T_TOTAL = 17.5
EARTH = (800, 900)
A0 = (90, 610)                                   # Asteroid-Start
T_HIT = 8.0
RED, GREEN = (235, 84, 70), (110, 210, 140)


def lerp(a, b, t):
    return a + (b - a) * t


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ast_pos(t):
    """Vor dem Treffer auf Kollisionskurs Richtung Erde, danach auf abgeknickter Bahn knapp vorbei."""
    hit = (lerp(A0[0], EARTH[0], 0.48), lerp(A0[1], EARTH[1], 0.48))
    if t <= T_HIT:
        u = t / T_HIT
        return lerp(A0[0], hit[0], u), lerp(A0[1], hit[1], u)
    u = (t - T_HIT) / 4.5
    ang = math.atan2(EARTH[1] - A0[1], EARTH[0] - A0[0]) - math.radians(34)
    sp = math.hypot(hit[0] - A0[0], hit[1] - A0[1]) / T_HIT * 4.5 * 3.2
    return hit[0] + math.cos(ang) * sp * u, hit[1] + math.sin(ang) * sp * u


def background():
    img, _ = new_frame(41)
    header_band(img, ["If an asteroid were heading", "for Earth - we know how", "to push it away"], "push it away")
    planet(img, EARTH[0] * S, EARTH[1] * S, 250, "earth", light=(-0.8, -0.3, 0.5))
    d = ImageDraw.Draw(img)
    cta = "Send this to someone who worries about asteroids"
    d.text(((W * S - d.textlength(cta, font=f(32 * S, bold=True))) / 2, 1585 * S), cta, font=f(32 * S, bold=True), fill=FG)
    return downscale(img, W, H)


def asteroid_sprite(r=46):
    """Unregelmaessiger, schattierter Gesteinsbrocken mit Kratern (4x gezeichnet)."""
    k = 4
    size = r * 2 + 8
    im = Image.new("RGBA", (size * k, size * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rnd = random.Random(5)
    c = size * k / 2
    pts = []
    for i in range(36):
        a = i / 36 * 2 * math.pi
        rr = r * k * (0.78 + 0.22 * math.sin(a * 3 + 1) * 0.6 + rnd.uniform(-0.08, 0.08))
        pts.append((c + math.cos(a) * rr, c + math.sin(a) * rr * 0.82))
    d.polygon(pts, fill=(122, 108, 96, 255))
    shade = Image.new("L", im.size, 0)                                       # Licht von links oben
    ImageDraw.Draw(shade).ellipse([c - r * k * 1.3, c - r * k * 1.3, c + r * k * 0.5, c + r * k * 0.5], fill=255)
    shade = shade.filter(ImageFilter.GaussianBlur(r * k * 0.45))
    lit = Image.new("RGBA", im.size, (176, 160, 140, 255))
    im = Image.composite(lit, im, Image.composite(shade, Image.new("L", im.size, 0), im.split()[3]))
    d = ImageDraw.Draw(im)
    for _ in range(9):
        x, y = c + rnd.uniform(-0.55, 0.55) * r * k, c + rnd.uniform(-0.45, 0.45) * r * k
        s = rnd.uniform(0.07, 0.17) * r * k
        d.ellipse([x - s, y - s * 0.8, x + s, y + s * 0.8], fill=(84, 74, 66, 255))
        d.arc([x - s, y - s * 0.8, x + s, y + s * 0.8], 200, 340, fill=(196, 182, 162, 255), width=max(1, k))
    a = im.split()[3]
    im.putalpha(a)
    return im.resize((size, size), Image.LANCZOS)


def probe_sprite():
    """DART-artige Sonde: Kastenkoerper + zwei lange Solarflaechen (4x gezeichnet)."""
    k = 4
    w, h = 120, 34
    im = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 11 * k, 42 * k, 23 * k], 3 * k, fill=(70, 96, 170, 255))          # Panel links
    d.rounded_rectangle([78 * k, 11 * k, 120 * k, 23 * k], 3 * k, fill=(70, 96, 170, 255))     # Panel rechts
    for x in range(4, 42, 6):
        d.line([x * k, 11 * k, x * k, 23 * k], fill=(40, 60, 120, 255), width=k)
        d.line([(x + 76) * k, 11 * k, (x + 76) * k, 23 * k], fill=(40, 60, 120, 255), width=k)
    d.rectangle([42 * k, 16 * k, 78 * k, 18 * k], fill=(190, 190, 196, 255))
    d.rounded_rectangle([48 * k, 4 * k, 72 * k, 30 * k], 3 * k, fill=(206, 168, 92, 255))     # Koerper (Folie)
    d.ellipse([54 * k, 10 * k, 66 * k, 22 * k], fill=(232, 232, 236, 255))                      # Antenne
    return im.resize((w, h), Image.LANCZOS)


def dashed(d, p0, p1, col, width=4, dash=18, gap=12):
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    n = int(L // (dash + gap)) + 1
    for i in range(n):
        a, b = i * (dash + gap) / L, min(1, (i * (dash + gap) + dash) / L)
        d.line([lerp(p0[0], p1[0], a), lerp(p0[1], p1[1], a), lerp(p0[0], p1[0], b), lerp(p0[1], p1[1], b)],
               fill=col, width=width)


def caption(d, top, big, sub, col=ACC, alpha=1.0):
    def mix(c):
        return tuple(int(v * alpha + 11 * (1 - alpha)) for v in c)
    fo1, fo2, fo3 = f(40, bold=True), f(72, bold=True), f(32)
    y = 1240
    d.text(((W - d.textlength(top, font=fo1)) / 2, y), top, font=fo1, fill=mix(FG))
    d.text(((W - d.textlength(big, font=fo2)) / 2, y + 56), big, font=fo2, fill=mix(col))
    if sub:
        d.text(((W - d.textlength(sub, font=fo3)) / 2, y + 150), sub, font=fo3, fill=mix(SEC))


PHASES = [  # (Start, Ende, oben, gross, unten, Farbe)
    (0.0, 4.6, "Years before impact,", "we'd spot it", "Telescopes track its path toward Earth.", RED),
    (4.6, 8.6, "The plan: hit it", "with a spacecraft", "at about 22,000 km/h", ACC),
    (8.6, 12.6, "A tiny nudge, early enough", "= a clean miss", "Exaggerated here so you can see it.", GREEN),
    (12.6, 17.5, "Not science fiction:", "NASA DART, 2022", "It hit asteroid moon Dimorphos and cut its orbit by 32 minutes.", ACC),
]


def frame(bg, ast, probe, t):
    im = bg.copy()
    d = ImageDraw.Draw(im)
    hit = ast_pos(T_HIT)
    if t < T_HIT + 0.3:                                                        # Kollisionskurs (rot)
        dashed(d, A0, (EARTH[0] - 40, EARTH[1] - 14), RED, width=4)
        if t < 4.6:
            d.text((330, 640), "IMPACT PATH", font=f(28, bold=True), fill=RED)
    if t > T_HIT:                                                              # neue Bahn (gruen)
        end = ast_pos(T_HIT + 4.5)
        u = ease((t - T_HIT) / 1.2)
        dashed(d, hit, (lerp(hit[0], end[0], u), lerp(hit[1], end[1], u)), GREEN, width=4)
    ax, ay = ast_pos(t)
    if ax < W + 80 and ay > -80:
        rot = ast.rotate(t * 25, resample=Image.BICUBIC)
        im.paste(rot, (int(ax - rot.width / 2), int(ay - rot.height / 2)), rot)
    if 4.6 <= t < T_HIT:                                                       # Sonde fliegt an
        u = ease((t - 4.6) / (T_HIT - 4.6))
        sx, sy = lerp(120, hit[0] - 40, u), lerp(1150, hit[1] + 30, u) - math.sin(u * math.pi) * 120
        blob(im, int(sx - 40), int(sy + 4), 18, 8, (255, 190, 110), blur=6, alpha=200)
        im.paste(probe, (int(sx - probe.width / 2), int(sy - probe.height / 2)), probe)
    if T_HIT <= t < T_HIT + 1.2:                                               # Einschlagblitz + Truemmer
        u = (t - T_HIT) / 1.2
        blob(im, int(hit[0]), int(hit[1]), int(30 + 150 * u), int(30 + 150 * u), (255, 236, 190),
             blur=int(20 + 30 * u), alpha=int(255 * (1 - u)))
        rnd = random.Random(9)
        dd = ImageDraw.Draw(im)
        for _ in range(26):
            a, v = rnd.uniform(math.pi * 0.6, math.pi * 1.6), rnd.uniform(60, 200)
            x, y = hit[0] + math.cos(a) * v * u, hit[1] + math.sin(a) * v * u
            dd.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(200, 186, 166))
    d = ImageDraw.Draw(im)
    for t0, t1, top, big, sub, col in PHASES:
        if t0 <= t < t1:
            a = min(1.0, (t - t0) / 0.35, (t1 - t) / 0.35 if t1 < T_TOTAL else 1.0)
            caption(d, top, big, sub if len(sub) < 46 else None, col, a)
            if len(sub) >= 46:                                                 # lange Zeile umbrechen
                words, line, y = sub.split(), "", 1390
                for w in words:
                    if d.textlength(line + " " + w, font=f(32)) > W - 160:
                        d.text(((W - d.textlength(line, font=f(32))) / 2, y), line, font=f(32),
                               fill=tuple(int(c * a + 11 * (1 - a)) for c in SEC))
                        line, y = w, y + 42
                    else:
                        line = (line + " " + w).strip()
                d.text(((W - d.textlength(line, font=f(32))) / 2, y), line, font=f(32),
                       fill=tuple(int(c * a + 11 * (1 - a)) for c in SEC))
    return im


def main():
    bg = background()
    ast, probe = asteroid_sprite(), probe_sprite()
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(T_TOTAL * FPS)
    out = OUT / "w6-asteroid-dart.mp4"
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{T_TOTAL:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(frame(bg, ast, probe, i / FPS).convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()
    frame(bg, ast, probe, 2.5).convert("RGB").save(OUT / "w6-asteroid-dart-cover.png")
    print(f"saved {out.name} ({T_TOTAL:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
