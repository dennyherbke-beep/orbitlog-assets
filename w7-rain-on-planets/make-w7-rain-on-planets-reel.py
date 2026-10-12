"""Woche 7 - Raster-Reel "What it RAINS on each planet" (Typ a, zweite Winner-Variante von
w6-sun-from-planets). 3x3-Raster, in jedem Feld faellt der jeweilige Niederschlag - gleichzeitig,
nahtloser Loop (6 s).

Fakten (NASA Science / JPL; vorhergesagte Phaenomene im Bild mit * gekennzeichnet):
  Merkur: keine Atmosphaere, kein Wetter. Venus: Schwefelsaeure-Regen, verdampft vor dem Boden
  (Virga). Erde: Wasser. Mars: Schnee aus Kohlendioxid ("Trockeneis", MRO 2012) und Wassereis
  (Phoenix 2008) -> "dry-ice snow". Jupiter: Ammoniak-Wasser-Hagel ("mushballs", Juno 2020).
  Saturn*: Helium-Regen tief im Inneren (Modell, erklaert Saturns Ueberschusswaerme).
  Uranus*/Neptun*: Diamant-Regen tief im Inneren (vorhergesagt, Laborexperimente SLAC 2017/2022
  stuetzen es). Pluto: Methan-Schnee/-Reif auf Bergspitzen (New Horizons, Nature Comms 2020).
  Pluto als Zwergplanet benannt (wie im Sonnen-Reel).
  Realistische Bedingungen (08.10.2026, Wunsch Denny): Himmelsfarbe je Welt (Venus gelber Dunst,
  Erde graue Wolken, Mars butterscotch, Gasplaneten getoent, Pluto schwarz mit blauem Dunstsaum),
  Fallgeschwindigkeit qualitativ nach Schwerkraft/Dichte (Jupiter-Hagel schnell, Mars-Schnee,
  Diamanten, Pluto-Methan langsam), Venus-Superrotation -> schraeger, seitlich treibender Regen.

Hook-Varianten:
  1 "What it RAINS on each planet" (gewaehlt)   2 "On Neptune it might rain diamonds"
  3 "Weather report: solar system"   4 "The only planet where rain hits the ground"
  5 "Venus rains acid - but it never lands"

    python make-w7-rain-on-planets-reel.py  ->  w7-rain-on-planets.mp4, -cover.png
"""

import math

import numpy as np
import random
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
W, H, FPS, LOOP = 1080, 1920, 30, 6.0
# Name, Textur, Niederschlag (Beschriftung), Stil, Markierung
BODIES = [("Mercury", "mercury", "nothing", None, ""), ("Venus", "venus", "acid", "acid", ""),
          ("Earth", "earth", "water", "water", ""), ("Mars", "mars", "dry-ice snow", "snow", ""),
          ("Jupiter", "jupiter", "ammonia hail", "hail", ""), ("Saturn", "saturn", "helium rain", "helium", "*"),
          ("Uranus", "uranus", "diamonds", "diamond", "*"), ("Neptune", "neptune", "diamonds", "diamond", "*"),
          ("Pluto", "pluto", "methane snow", "msnow", "")]
# Himmel: (oben, Horizont, Deckkraft, Wolkenfarbe oder None)
SKY = {"Mercury": ((0, 0, 0), (0, 0, 0), 0, None),
       "Venus": ((168, 122, 52), (226, 182, 104), 0.95, (236, 206, 140)),
       "Earth": ((78, 88, 104), (140, 152, 168), 0.95, (110, 118, 132)),
       "Mars": ((140, 100, 72), (206, 160, 118), 0.9, (222, 206, 190)),
       "Jupiter": ((104, 76, 52), (188, 152, 112), 0.9, (214, 186, 146)),
       "Saturn": ((120, 102, 68), (200, 180, 136), 0.85, None),
       "Uranus": ((62, 120, 136), (150, 208, 214), 0.85, None),
       "Neptune": ((16, 36, 104), (58, 96, 190), 0.9, None),
       "Pluto": ((0, 0, 0), (54, 84, 136), 0.55, None)}
# Bewegung je Stil: k = Fallzyklen pro Loop (Tempo), m = seitliche Zyklen pro Loop (Wind), Sway in px
MOTION = {"acid": (1, 1, 0),      # dichte, langsame Venus-Wolkenluft, Superrotation -> stark schraeg
          "water": (4, 0, 0),     # Erde: Regentropfen ~9 m/s, leichter Wind
          "snow": (1, 0, 10),     # Mars: winzige CO2-Flocken, dünne Luft, sinken langsam und taumeln
          "hail": (5, 0, 0),      # Jupiter: schwere 'mushballs', hohe Schwerkraft -> schnell
          "helium": (1, 0, 0),    # Saturn: Tropfen sinken langsam durch dichtes Wasserstoff-Fluid
          "diamond": (1, 0, 4),   # Uranus/Neptun: sinken langsam ins Innere
          "msnow": (1, 0, 6)}     # Pluto: Methan-Reif, kaum Schwerkraft -> sehr langsam
GRID_TOP, CELL_W, CELL_H = 540, 340, 330
GROUND = 250
R = 900
TOP_Y = 64                                         # Niederschlag beginnt unter der Beschriftung
SPAN = GROUND - 8 - TOP_Y


def cell_origin(i):
    return (W - 3 * CELL_W) // 2 + (i % 3) * CELL_W, GRID_TOP + (i // 3) * CELL_H


def background():
    img, _ = new_frame(61)
    header_band(img, ["What it RAINS", "on each planet"], "RAINS")
    for i, (name, kind, lab, style, mark) in enumerate(BODIES):
        x0, y0 = cell_origin(i)
        x0, y0 = x0 * S, y0 * S
        cw, ch = CELL_W * S, CELL_H * S
        cell = img.crop((x0, y0, x0 + cw, y0 + ch))
        top, bot, cov, cloud = SKY[name]
        if cov:                                                           # Himmelsfarbe der jeweiligen Welt
            tt = np.linspace(0, 1, ch)[:, None, None]
            grad = (np.array(top) * (1 - tt) + np.array(bot) * tt) * np.ones((1, cw, 1))
            sky = Image.fromarray(grad.astype(np.uint8), "RGB")
            m = Image.fromarray((np.linspace(cov * 0.75, cov, ch)[:, None] * np.ones((1, cw)) * 255).astype(np.uint8))
            cell.paste(sky, (0, 0), m)
        else:
            sky = Image.new("RGB", cell.size, (0, 0, 0))
            blob(sky, cw // 2, int(GROUND * S), int(cw * 0.7), int(110 * S), (40, 46, 70), blur=int(60 * S))
            cell = ImageChops.add(cell, sky)
        if cloud:                                                         # Wolkendecke als Quelle
            rng = np.random.default_rng(i)
            for _ in range(16):
                cx_, cy_ = rng.uniform(-0.1, 1.1) * cw, rng.uniform(0.02, 0.2) * ch
                blob(cell, int(cx_), int(cy_), int(rng.uniform(60, 120) * S), int(rng.uniform(22, 40) * S), cloud,
                     blur=int(18 * S), alpha=int(rng.uniform(120, 200)))
        planet(cell, cw // 2, int((GROUND + R / 2 - 6) * S), R, kind, light=(0.0, -0.9, 0.45), glow=False)
        img.paste(cell, (x0, y0))
        d = ImageDraw.Draw(img)
        d.rectangle([x0 + 4 * S, y0 + 4 * S, x0 + cw - 4 * S, y0 + ch - 4 * S], outline=HAIR, width=2 * S)
        fo = f(30 * S, bold=True)
        txt = lab + mark
        d.text((x0 + (cw - d.textlength(txt, font=fo)) / 2, y0 + 18 * S), txt, font=fo,
               fill=SEC if style is None else ACC, stroke_width=2 * S, stroke_fill=(8, 10, 14))
        fo = f(30 * S, bold=True)
        d.text((x0 + 16 * S, y0 + (GROUND + 22) * S), name, font=fo, fill=ACC if name == "Earth" else FG,
               stroke_width=2 * S, stroke_fill=(8, 10, 14))
    d = ImageDraw.Draw(img)
    y = (GRID_TOP + 3 * CELL_H + 22) * S
    for ln in ["*predicted, deep inside the planet · Pluto is a dwarf planet"]:
        d.text(((WS - d.textlength(ln, font=f(24 * S))) / 2, y), ln, font=f(24 * S), fill=SEC)
    cta = "Send this to someone who hates rainy days"
    d.text(((WS - d.textlength(cta, font=f(34 * S, bold=True))) / 2, y + 40 * S), cta,
           font=f(34 * S, bold=True), fill=FG)
    return downscale(img, W, H)


def particles(style, seed):
    """Feste Partikelliste je Stil: (x, Startphase, Geschwindigkeits-Faktor k [ganzzahlig], Groesse)."""
    rnd = random.Random(seed)
    n, ks = {"acid": (26, (2,)), "water": (30, (3,)), "snow": (22, (1,)), "hail": (12, (2,)),
             "helium": (24, (2,)), "diamond": (14, (1,)), "msnow": (18, (1,))}[style]
    return [(rnd.uniform(20, CELL_W - 20), rnd.random(), rnd.choice(ks), rnd.uniform(0.7, 1.3)) for _ in range(n)]


def draw_particle(d, style, x, y, frac, t, sz, j, slant=0.0):
    """frac = 0 (oben) .. 1 (Boden)."""
    edge = min(1.0, frac / 0.08, (1 - frac) / 0.08)
    if style == "acid":                                                   # Virga: verdampft auf halber Hoehe
        a = edge * max(0.0, 1 - max(0.0, frac - 0.35) / 0.3)
        if a > 0:
            d.line([x, y, x + 16 * sz * slant, y + 16 * sz], fill=(92, 110, 20, int(240 * a)), width=3)
    elif style == "water":
        d.line([x, y, x - 4, y + 22 * sz], fill=(214, 232, 255, int(235 * edge)), width=3)
    elif style in ("snow", "msnow"):
        col = (245, 248, 255) if style == "snow" else (255, 214, 226)
        r = 4.5 * sz
        d.ellipse([x - r, y - r, x + r, y + r], fill=col + (int(235 * edge),))
    elif style == "hail":
        r = 8 * sz
        d.ellipse([x - r, y - r, x + r, y + r], fill=(236, 226, 206, int(250 * edge)), outline=(150, 130, 110, int(200 * edge)))
    elif style == "helium":
        d.line([x, y, x, y + 14 * sz], fill=(236, 240, 250, int(200 * edge)), width=2)
        d.ellipse([x - 3.5, y + 12 * sz, x + 3.5, y + 19 * sz], fill=(250, 252, 255, int(230 * edge)),
                  outline=(90, 80, 60, int(160 * edge)))
    elif style == "diamond":
        s = 9 * sz
        d.polygon([(x, y - s), (x + s * 0.7, y), (x, y + s), (x - s * 0.7, y)], fill=(225, 245, 255, int(240 * edge)),
                  outline=(255, 255, 255, int(255 * edge)))
        g = 0.5 + 0.5 * math.sin(2 * math.pi * (2 * t / LOOP + j * 0.37))       # Funkeln, loopt sauber
        if g > 0.75:
            L = s * 1.8 * (g - 0.75) / 0.25
            d.line([x - L, y, x + L, y], fill=(255, 255, 255, int(220 * edge)), width=2)
            d.line([x, y - L, x, y + L], fill=(255, 255, 255, int(220 * edge)), width=2)


def frame(bg, parts, t):
    im = bg.copy().convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for i, (name, kind, lab, style, mark) in enumerate(BODIES):
        if style is None:
            continue
        x0, y0 = cell_origin(i)
        k, m, sw = MOTION[style]
        cell_ov = Image.new("RGBA", (CELL_W, CELL_H), (0, 0, 0, 0))
        dc = ImageDraw.Draw(cell_ov)
        for j, (px, ph, _, sz) in enumerate(parts[i]):
            frac = (ph + k * t / LOOP) % 1.0
            xx = (px + m * CELL_W * (t / LOOP + frac / max(k, 1) * 0.0) + 0.55 * m * SPAN * frac) % CELL_W
            sway = sw * math.sin(2 * math.pi * (2 * t / LOOP + ph)) if sw else 0.0
            draw_particle(dc, style, xx + sway, TOP_Y + frac * SPAN, frac, t, sz, j, slant=0.55 * m)
        mask = Image.new("L", (CELL_W, CELL_H), 0)                        # nicht ueber den Zellrand malen
        ImageDraw.Draw(mask).rectangle([6, 6, CELL_W - 6, CELL_H - 6], fill=255)
        cell_ov.putalpha(ImageChops.multiply(cell_ov.getchannel("A"), mask))
        ov.alpha_composite(cell_ov, (x0, y0))
    im.alpha_composite(ov)
    return im.convert("RGB")


def main():
    bg = background()
    parts = [particles(s, i) if s else None for i, (_, _, _, s, _) in enumerate(BODIES)]
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = OUT / "w7-rain-on-planets.mp4"
    n = int(LOOP * FPS)
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg, parts, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg, parts, 1.3), 0).save(OUT / "w7-rain-on-planets-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
