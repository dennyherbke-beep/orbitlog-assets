"""Woche 7 - Raster-Reel "What the MOON looks like from each planet" (Typ a, Winner-Variante von
w6-sun-from-planets, docs/reel-algorithmus.md Winner-Regel). 3x3-Raster, in jedem Feld geht der
am groessten erscheinende Mond auf - in seiner scheinbaren Groesse relativ zu unserem Mond.
Mehrere Monde (Mars 2, Jupiter 4, Saturn 6, Uranus 5, Neptun 2) gehen gemeinsam auf - Groessen massstaeblich,
Anordnung frei. Charon steht still (Pluto und Charon sind gegenseitig gebunden), Merkur/Venus haben keinen Mond.
Ueberschrift "...from each planet and Pluto" (Pluto = Zwergplanet, Wunsch Denny 08.10.2026).
  Weitere Monde (x unser Mond): Deimos 0,07 · Europa 0,57 · Ganymed 0,57 · Kallisto 0,29 · Dione 0,39 ·
  Rhea 0,36 · Mimas 0,34 · Enceladus 0,31 · Umbriel 0,53 · Miranda 0,49 · Titania 0,42 · Oberon 0,30 ·
  Proteus 0,49.
8 s, nahtloser Loop.

Fakten (NASA Planetary/Satellite Fact Sheets, Bahnhalbachsen minus Planetenradius = Abstand von der
Oberflaeche bzw. Wolkenobergrenze; Winkel = Durchmesser/Abstand):
  Mond von der Erde 0,527 Grad = 1x · Phobos 22 km / 5.986 km -> 0,21 Grad = 0,40x ·
  Io 3.643 km / 350.200 km -> 0,60 Grad = 1,13x · Titan 0,254 Grad = 0,48x (Tethys 0,260 Grad,
  praktisch gleich gross) · Ariel 0,401 Grad = 0,76x · Triton 0,470 Grad = 0,89x ·
  Charon 1.212 km / 18.400 km -> 3,77 Grad = 7,2x. Charon steht von Pluto aus fest am Himmel
  (gebundene Rotation beider Koerper), nur von einer Pluto-Haelfte aus sichtbar.
  Mondgroesse fuer die Erde: 40 px (Darstellungsmassstab, alle anderen proportional).

Hook-Varianten:
  1 "What the MOON looks like from each planet" (gewaehlt)   2 "Moonrise on every planet"
  3 "Pluto's moon is 7x bigger than ours"   4 "Two planets have no moon at all"
  5 "From Jupiter, Io looks bigger than our Moon"

    python make-w7-moons-from-planets-reel.py  ->  w7-moons-from-planets.mp4, -cover.png
"""

import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, downscale
from bodies import planet
from reelkit import W as WS, new_frame, header_band, blob, cinematic

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
LOOP = 8.0
MOON_EARTH = 40                                  # px Monddurchmesser von der Erde aus
# Planet, Boden-Textur, Monde [(Name, Textur, Verhaeltnis zu unserem Mond, dx, dy)], Markierung.
# Mehrere Monde: die groessten am Himmel, gemeinsam aufgehend (Anordnung frei, Groessen massstaeblich).
BODIES = [("Mercury", "mercury", [], ""), ("Venus", "venus", [], ""),
          ("Earth", "earth", [("Moon", "moon", 1.0, 0, 0)], ""),
          ("Mars", "mars", [("Phobos", "moon", 0.40, -30, 10), ("Deimos", "moon", 0.067, 80, -40)], ""),
          ("Jupiter", "jupiter", [("Io", "venus", 1.13, -60, 15), ("Europa", "moon", 0.57, 20, -35),
                                  ("Ganymede", "mercury", 0.57, 90, 15), ("Callisto", "moon", 0.29, -125, -45)], "*"),
          ("Saturn", "saturn", [("Tethys", "moon", 0.49, -60, 15), ("Titan", "venus", 0.48, 20, -40),
                                ("Dione", "moon", 0.39, 90, 10), ("Rhea", "moon", 0.36, -15, 55),
                                ("Mimas", "moon", 0.34, 125, -50), ("Enceladus", "moon", 0.31, -125, -45)], "*"),
          ("Uranus", "uranus", [("Ariel", "moon", 0.76, -40, 10), ("Umbriel", "mercury", 0.53, 50, -35),
                                ("Miranda", "moon", 0.49, 115, 20), ("Titania", "moon", 0.42, -120, -40),
                                ("Oberon", "mercury", 0.30, 10, 55)], "*"),
          ("Neptune", "neptune", [("Triton", "mercury", 0.89, -20, 10), ("Proteus", "moon", 0.49, 90, -35)], "*"),
          ("Pluto", "pluto", [("Charon", "charon", 7.16, 0, 0)], "")]
GRID_TOP, CELL_W, CELL_H = 540, 340, 330
GROUND = 250
R = 900


def cell_origin(i):
    return (W - 3 * CELL_W) // 2 + (i % 3) * CELL_W, GRID_TOP + (i // 3) * CELL_H


def background():
    img, _ = new_frame(43)
    header_band(img, ["What the MOON looks like", "from each planet and Pluto"], "MOON")
    for i, (name, kind, moons, mark) in enumerate(BODIES):
        x0, y0 = cell_origin(i)
        x0, y0 = x0 * S, y0 * S
        cw, ch = CELL_W * S, CELL_H * S
        cell = img.crop((x0, y0, x0 + cw, y0 + ch))
        sky = Image.new("RGB", cell.size, (0, 0, 0))
        blob(sky, cw // 2, int(GROUND * S), int(cw * 0.7), int(110 * S), (32, 36, 58), blur=int(60 * S))
        cell = ImageChops.add(cell, sky)
        if name == "Pluto":                                                   # Charon steht fest am Himmel
            planet(cell, int(cw * 0.58), int((GROUND - 70) * S), MOON_EARTH * moons[0][2], moons[0][1],
                   light=(-0.8, -0.2, 0.55), glow=False)
        planet(cell, cw // 2, int((GROUND + R / 2 - 6) * S), R, kind, light=(0.0, -0.9, 0.45), glow=False)
        img.paste(cell, (x0, y0))
        d = ImageDraw.Draw(img)
        d.rectangle([x0 + 4 * S, y0 + 4 * S, x0 + cw - 4 * S, y0 + ch - 4 * S], outline=HAIR, width=2 * S)
    d = ImageDraw.Draw(img)
    y = (GRID_TOP + 3 * CELL_H + 22) * S
    for ln in ["Biggest moons in each sky, to scale with ours · *seen from the cloud tops"]:
        d.text(((WS - d.textlength(ln, font=f(24 * S))) / 2, y), ln, font=f(24 * S), fill=SEC)
    cta = "Send this to someone who loves the Moon"
    d.text(((WS - d.textlength(cta, font=f(34 * S, bold=True))) / 2, y + 40 * S), cta,
           font=f(34 * S, bold=True), fill=FG)
    return downscale(img, W, H)


def surface_sprites(bg):
    out = []
    for i in range(len(BODIES)):
        x0, y0 = cell_origin(i)
        crop = bg.crop((x0, y0, x0 + CELL_W, y0 + CELL_H)).convert("RGBA")
        m = Image.new("L", (CELL_W * 4, CELL_H * 4), 0)
        cx, cy = CELL_W // 2, GROUND + R // 2 - 6
        ImageDraw.Draw(m).ellipse([(cx - R / 2) * 4, (cy - R / 2) * 4, (cx + R / 2) * 4, (cy + R / 2) * 4], fill=255)
        crop.putalpha(m.resize((CELL_W, CELL_H), Image.LANCZOS))
        out.append(crop)
    return out


def moon_sprite(d_px, kind):
    size = max(60, int(d_px * 2.2))
    im = Image.new("RGB", (size * S, size * S), (0, 0, 0))
    planet(im, size * S // 2, size * S // 2, max(3, d_px), kind, light=(-0.75, -0.25, 0.6), glow=False)
    im = downscale(im, size, size)
    mask = im.convert("L").point(lambda p: 255 if p > 6 else int(p * 40))
    return im, mask


def frame(bg, surf, moons, t):
    im = bg.copy()
    ph = 0.5 - 0.5 * math.cos(2 * math.pi * t / LOOP)
    for i, (name, kind, ms, mark) in enumerate(BODIES):
        x0, y0 = cell_origin(i)
        cell = im.crop((x0, y0, x0 + CELL_W, y0 + CELL_H))
        d = ImageDraw.Draw(cell)
        st = dict(stroke_width=2, stroke_fill=(8, 10, 14))
        if ms and name != "Pluto":
            for j, (mname, mk, ratio, dx, dy) in enumerate(ms):
                sp, m = moons[i][j]
                cx, cy = CELL_W // 2 + dx, GROUND + 60 + dy - ph * 190
                cell.paste(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)), m)
            cell.paste(surf[i], (0, 0), surf[i])
            d = ImageDraw.Draw(cell)
            mname, _, ratio, dx, dy = ms[0]                               # Name nur am groessten Mond
            cx, cy = CELL_W // 2 + dx, GROUND + 60 + dy - ph * 190
            lab_y = cy + MOON_EARTH * ratio / 2 + 6
            if lab_y < GROUND - 30:
                tw = d.textlength(mname, font=f(22))
                d.text((cx - tw / 2, lab_y), mname, font=f(22), fill=SEC, **st)
            if len(ms) > 1 and ph > 0.6:
                more = f"+{len(ms) - 1} more"
                d.text((16, 16), more, font=f(22), fill=SEC, **st)
        elif name == "Pluto":
            d.text((16, 16), "Charon", font=f(24, bold=True), fill=FG, **st)
            d.text((16, 46), "never moves", font=f(24), fill=ACC, **st)
        else:
            tw = d.textlength("no moon", font=f(30, bold=True))
            d.text(((CELL_W - tw) / 2, 110), "no moon", font=f(30, bold=True), fill=SEC, **st)
        d.text((16, GROUND + 22), name + mark, font=f(30, bold=True), fill=ACC if name == "Earth" else FG, **st)
        ratio = ms[0][2] if ms else 0
        lab = "-" if not ratio else f"{ratio:.1f}x" if ratio >= 1 else f"{ratio:.2f}x"
        tw = d.textlength(lab, font=f(30, bold=True))
        d.text((CELL_W - tw - 16, GROUND + 22), lab, font=f(30, bold=True), fill=ACC, **st)
        im.paste(cell, (x0, y0))
    return im


def main():
    bg = background()
    surf = surface_sprites(bg)
    moons = [[moon_sprite(MOON_EARTH * r, k) for _, k, r, _, _ in ms] for _, _, ms, _ in BODIES]
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(LOOP * FPS)
    out = OUT / "w7-moons-from-planets.mp4"
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg, surf, moons, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg, surf, moons, LOOP / 2), 0).save(OUT / "w7-moons-from-planets-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
