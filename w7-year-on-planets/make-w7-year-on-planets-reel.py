"""Woche 7 - Reel "How long is a YEAR on each planet?" (Typ a Bahn-/Rennen-Animation, Backlog-
Prioritaet aus docs/reel-algorithmus.md, eigene Umsetzung des Planetenbahnen-Prinzips). Alle Planeten
starten auf einer Linie, laufen mit massstaeblichem Tempo um die Sonne; an der Start-/Ziellinie
zaehlt jede Bahn ihre Runden. Ende: Jupiter schliesst seine erste Runde (= 11,9 Erdjahre) ab. 15 s.

Fakten (NASA Planetary Fact Sheet, siderische Umlaufzeiten in Erdjahren):
  Merkur 0,241 · Venus 0,615 · Erde 1,000 · Mars 1,881 · Jupiter 11,86 · Saturn 29,46 ·
  Uranus 84,0 · Neptun 164,8. Bahnradien NICHT massstaeblich (gleichmaessig verteilt, Hinweis im
  Bild); Bahnen als Kreise vereinfacht.

Hook-Varianten:
  1 "How long is a YEAR on each planet?" (gewaehlt)   2 "One lap of Jupiter = 12 of ours"
  3 "Your birthday on every planet"   4 "Neptune hasn't finished 2 laps since we found it"
  5 "Race: all 8 planets around the Sun"

    python make-w7-year-on-planets-reel.py  ->  w7-year-on-planets.mp4, -cover.png
"""

import math
import os
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, downscale
from bodies import planet, star
from reelkit import W as WS, new_frame, header_band, cinematic

OUT = Path(__file__).resolve().parent
W, H, FPS = 1080, 1920, 30
RUN, HOLD = 12.0, 3.5
DUR = RUN + HOLD
CX, CY = 540, 1010
# Name, Textur, Umlaufzeit (Jahre), Bahnradius px, Durchmesser px, Ring
PL = [("Mercury", "mercury", 0.241, 78, 18, False), ("Venus", "venus", 0.615, 128, 26, False),
      ("Earth", "earth", 1.0, 178, 28, False), ("Mars", "mars", 1.881, 226, 22, False),
      ("Jupiter", "jupiter", 11.86, 290, 50, False), ("Saturn", "saturn", 29.46, 350, 42, True),
      ("Uranus", "uranus", 84.0, 403, 32, False), ("Neptune", "neptune", 164.8, 452, 32, False)]
END_YEARS = 11.86


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def years(t):
    return END_YEARS * ease(t / RUN)


def background():
    img, _ = new_frame(53)
    header_band(img, ["How long is a YEAR", "on each planet?"], "YEAR")
    d = ImageDraw.Draw(img)
    for _, _, _, r, _, _ in PL:
        d.ellipse([(CX - r) * S, (CY - r) * S, (CX + r) * S, (CY + r) * S], outline=HAIR, width=2 * S)
    d.line([CX * S, (CY - 470) * S, CX * S, (CY - 60) * S], fill=(90, 96, 112), width=2 * S)   # Start/Ziel
    star(img, CX * S, CY * S, 54, spots=False, corona=1.0)
    d = ImageDraw.Draw(img)
    note = "Orbit sizes not to scale · speeds to scale"
    d.text(((WS - d.textlength(note, font=f(24 * S))) / 2, (CY + 480) * S), note, font=f(24 * S), fill=SEC)
    return downscale(img, W, H)


def sprite(kind, dpx, ring):
    n = int(dpx * (2.6 if ring else 1.6))
    im = Image.new("RGB", (n * S, n * S), (0, 0, 0))
    planet(im, n * S // 2, n * S // 2, dpx, kind, light=(0, 0, 1), ring_tilt=24 if ring else None, glow=False)
    im = downscale(im, n, n)
    m = im.convert("L").point(lambda p: 255 if p > 10 else p * 25)
    return im, m


def frame(bg, sprites, t):
    im = bg.copy().convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    y_now = years(t)
    speed = (years(t + 1 / FPS) - years(t - 1 / FPS)) * FPS / 2                 # Jahre pro Sekunde
    for i, (name, kind, per, r, dpx, ring) in enumerate(PL):
        ang = -math.pi / 2 + 2 * math.pi * y_now / per
        trail = min(330.0, max(8.0, math.degrees(2 * math.pi * speed * 0.35 / per)))   # Bewegungsspur
        a0 = math.degrees(ang) - trail
        for k in range(12):
            frac = (k + 1) / 12
            d.arc([CX - r, CY - r, CX + r, CY + r], a0 + trail * k / 12, a0 + trail * (k + 1) / 12,
                  fill=(255, 180, 84, int(150 * frac)), width=4)
    im.alpha_composite(ov)
    for i, (name, kind, per, r, dpx, ring) in enumerate(PL):
        ang = -math.pi / 2 + 2 * math.pi * y_now / per
        sp, m = sprites[i]
        x, y = CX + r * math.cos(ang), CY + r * math.sin(ang)
        im.paste(sp, (int(x - sp.width / 2), int(y - sp.height / 2)), m)
    d = ImageDraw.Draw(im)
    st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
    for i, (name, kind, per, r, dpx, ring) in enumerate(PL):                   # Rundenzaehler an der Linie
        laps = int(y_now / per + 1e-6)
        fo = f(22, bold=True)
        y = CY - r - 13
        tw = d.textlength(name, font=fo)
        d.text((CX - 12 - tw, y), name, font=fo, fill=SEC, **st)
        lab = f"{laps} lap" + ("" if laps == 1 else "s")
        d.text((CX + 12, y), lab, font=fo, fill=ACC if laps else FG, **st)
    fo = f(54, bold=True)
    txt = f"Earth years passed: {y_now:4.1f}"
    kc = 1 - ease((t - RUN - 0.6) / 0.4)                                       # Zaehler weicht der Aufloesung
    if kc > 0:
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(ov).text(((W - d.textlength(txt, font=fo)) / 2, CY + 520), txt, font=fo,
                                fill=FG + (int(255 * kc),), stroke_width=3, stroke_fill=(8, 10, 14, int(255 * kc)))
        im.alpha_composite(ov)
    if t > RUN + 0.8:                                                          # Aufloesung
        k = ease((t - RUN - 0.8) / 0.5)
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d2 = ImageDraw.Draw(ov)
        for n, (ln, col, size) in enumerate([("1 year on Jupiter = 12 of ours", ACC, 44),
                                             ("Neptune needs 165", FG, 40),
                                             ("Send this to someone with a birthday soon", SEC, 32)]):
            fo = f(size, bold=True)
            d2.text(((W - d2.textlength(ln, font=fo)) / 2, CY + 515 + n * 58), ln, font=fo,
                    fill=col + (int(255 * k),), stroke_width=3, stroke_fill=(8, 10, 14, int(255 * k)))
        im.alpha_composite(ov)
    return im.convert("RGB")


def main():
    bg = background()
    sprites = [sprite(k, dpx, ring) for _, k, _, _, dpx, ring in PL]
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = OUT / "w7-year-on-planets.mp4"
    n = int(DUR * FPS)
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{DUR:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg, sprites, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg, sprites, 5.5), 0).save(OUT / "w7-year-on-planets-cover.png")
    cinematic(frame(bg, sprites, DUR - 0.1), 0).save(Path(os.environ.get("CHECK_DIR", OUT)) / "_check-year-end.png")
    print(f"saved {out.name} ({DUR:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
