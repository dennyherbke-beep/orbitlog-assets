"""Woche 6, Mittwoch - Raster-Reel "What the SUN looks like from each planet" (Typ a,
docs/reel-algorithmus.md). 3x3-Raster, in jedem Feld geht die Sonne gleichzeitig auf und unter -
in der scheinbaren Groesse, die sie von dort hat. 8 s, nahtloser Loop.

Fakten (NASA Planetary Fact Sheet, mittlere Sonnenabstaende in AU):
  Scheinbarer Sonnendurchmesser ~ 1/Abstand: Merkur 0,387 -> 2,6x · Venus 0,723 -> 1,4x · Erde 1x ·
  Mars 1,524 -> 0,66x · Jupiter 5,20 -> 0,19x · Saturn 9,58 -> 0,10x · Uranus 19,2 -> 0,05x ·
  Neptun 30,1 -> 0,03x · Pluto 39,5 -> 0,025x. Helligkeit ~ 1/Abstand^2: an Neptun ~1/900 des
  Sonnenlichts auf der Erde - immer noch ~400x heller als unser Vollmond (Vollmond ~1/400.000).
  Venus: vom Boden aus wegen der Wolkendecke nicht sichtbar; Gasplaneten ohne Oberflaeche
  (Blick von den Wolkenobergrenzen) -> Sternchen + first_comment.
  Sonnengroesse fuer die Erde: 60 px (Darstellungsmassstab, alle anderen proportional).

Hook-Varianten:
  1 "What the SUN looks like from each planet" (gewaehlt)   2 "Sunrise on every planet"
  3 "From Neptune, the Sun is just a bright star"   4 "Mercury's Sun is 2.6x bigger"
  5 "How big is the Sun from Pluto?"

    python make-w6-sun-from-planets-reel.py  ->  w6-sun-from-planets.mp4, -cover.png
"""

import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, downscale
from bodies import planet, star
from reelkit import W as WS, new_frame, header_band, blob

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
LOOP = 8.0
SUN_EARTH = 60                                   # px Sonnendurchmesser von der Erde aus
BODIES = [("Mercury", "mercury", 0.387, ""), ("Venus", "venus", 0.723, "*"), ("Earth", "earth", 1.0, ""),
          ("Mars", "mars", 1.524, ""), ("Jupiter", "jupiter", 5.20, "*"), ("Saturn", "saturn", 9.58, "*"),
          ("Uranus", "uranus", 19.2, "*"), ("Neptune", "neptune", 30.1, "*"), ("Pluto", "moon", 39.5, "")]
GRID_TOP, CELL_W, CELL_H = 540, 340, 330
GROUND = 250
R = 900                                          # Ausgabe-px Durchmesser der Boden-Kugel


def cell_origin(i):
    return (W - 3 * CELL_W) // 2 + (i % 3) * CELL_W, GRID_TOP + (i // 3) * CELL_H


def surface_center(i):
    x0, y0 = cell_origin(i)
    return x0 + CELL_W // 2, y0 + GROUND + R // 2 - 6


def background():
    img, _ = new_frame(31)
    header_band(img, ["What the SUN looks like", "from each planet"], "SUN")
    for i, (name, kind, au, mark) in enumerate(BODIES):
        x0, y0 = cell_origin(i)
        x0, y0 = x0 * S, y0 * S
        cw, ch = CELL_W * S, CELL_H * S
        cell = img.crop((x0, y0, x0 + cw, y0 + ch))
        sky = Image.new("RGB", cell.size, (0, 0, 0))                          # zarter Himmelsschimmer
        blob(sky, cw // 2, int(GROUND * S), int(cw * 0.7), int(110 * S), (40, 46, 70), blur=int(60 * S))
        cell = ImageChops.add(cell, sky)
        planet(cell, cw // 2, int((GROUND + R / 2 - 6) * S), R, kind, light=(0.0, -0.9, 0.45), glow=False)
        img.paste(cell, (x0, y0))
        d = ImageDraw.Draw(img)
        d.rectangle([x0 + 4 * S, y0 + 4 * S, x0 + cw - 4 * S, y0 + ch - 4 * S], outline=HAIR, width=2 * S)
    d = ImageDraw.Draw(img)
    foot = "Sun size compared with the view from Earth · *no solid ground / clouds"
    d.text(((WS - d.textlength(foot, font=f(24 * S))) / 2, (GRID_TOP + 3 * CELL_H + 24) * S), foot,
           font=f(24 * S), fill=SEC)
    cta = "Send this to someone who loves sunsets"
    d.text(((WS - d.textlength(cta, font=f(34 * S, bold=True))) / 2, (GRID_TOP + 3 * CELL_H + 62) * S), cta,
           font=f(34 * S, bold=True), fill=FG)
    return downscale(img, W, H)


def surface_sprites(bg):
    """Boden je Zelle als RGBA-Ausschnitt (wird ueber die Sonne gelegt, damit sie hinter dem Horizont aufgeht)."""
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


def sun_sprite(d_px):
    """Sonne mit Granulation/Korona (bodies.star); sehr kleine Sonnen als heller Stern mit Glow."""
    size = max(160, int(d_px * 3.2))
    im = Image.new("RGB", (size * S, size * S), (0, 0, 0))
    if d_px >= 20:
        star(im, size * S // 2, size * S // 2, d_px, spots=d_px > 40, corona=1.0)
    else:                                                                  # Glow schrumpft mit dem Abstand
        g = int((6 + 2.0 * d_px) * S)
        blob(im, size * S // 2, size * S // 2, g, g, (255, 200, 120), blur=int(g * 0.4), alpha=int(110 + 6 * d_px))
        blob(im, size * S // 2, size * S // 2, int(max(2.5, d_px) * S), int(max(2.5, d_px) * S),
             (255, 250, 236), blur=S, alpha=255)
    im = downscale(im, size, size)
    mask = im.convert("L").point(lambda p: min(255, int(p * 1.6)))
    return im, mask


def frame(bg, surf, suns, t):
    im = bg.copy()
    ph = 0.5 - 0.5 * math.cos(2 * math.pi * t / LOOP)                     # 0 -> 1 -> 0, nahtlos
    for i, (name, kind, au, mark) in enumerate(BODIES):
        x0, y0 = cell_origin(i)
        sp, m = suns[i]
        cx = x0 + CELL_W // 2 + 60
        horizon = y0 + GROUND
        cy = horizon + 30 - ph * 175
        cell = im.crop((x0, y0, x0 + CELL_W, y0 + CELL_H))
        cell.paste(sp, (int(cx - x0 - sp.width / 2), int(cy - y0 - sp.height / 2)), m)
        cell.paste(surf[i], (0, 0), surf[i])
        d = ImageDraw.Draw(cell)
        st = dict(stroke_width=2, stroke_fill=(8, 10, 14))
        d.text((16, GROUND + 22), name + mark, font=f(30, bold=True), fill=ACC if name == "Earth" else FG, **st)
        r = 1 / au
        lab = f"{r:.1f}x" if r >= 0.95 else (f"{r:.2f}x" if r >= 0.1 else f"{r:.3f}x")
        tw = d.textlength(lab, font=f(30, bold=True))
        d.text((CELL_W - tw - 16, GROUND + 22), lab, font=f(30, bold=True), fill=ACC, **st)
        im.paste(cell, (x0, y0))
    return im


def main():
    bg = background()
    surf = surface_sprites(bg)
    suns = [sun_sprite(SUN_EARTH / au) for _, _, au, _ in BODIES]
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(LOOP * FPS)
    out = OUT / "w6-sun-from-planets.mp4"
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(frame(bg, surf, suns, i / FPS).convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()
    frame(bg, surf, suns, LOOP / 2).convert("RGB").save(OUT / "w6-sun-from-planets-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
