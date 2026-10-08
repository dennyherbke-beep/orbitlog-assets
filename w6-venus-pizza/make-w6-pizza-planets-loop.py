"""Woche 6, Sonntag - Umbau 08.10.2026: "Could you bake a PIZZA on each planet?" als Raster-Loop
(Format des Winners w6-sun-from-planets, Typ d absurde Frage). Ersetzt die Folien-Version
make-w6-venus-pizza-reel.py (bleibt als Archiv liegen). 3x3-Raster, in jedem Feld liegt eine rohe
Pizza auf dem Boden; das Thermometer laeuft auf die Temperatur dort, die Pizza backt, bleibt roh
oder friert ein. 9 s, nahtloser Loop (0 -> 1 -> 0).

Fakten (NASA Planetary Fact Sheet, mittlere Temperaturen; Merkur/Mond Tagseite laut NASA Science):
  Merkur Tagseite ~430 C · Venus ~465 C (Tag und Nacht, Druck ~90x Erde) · Erde ~15 C ·
  Mond Tagseite ~120 C · Mars ~-65 C · Jupiter -110 C · Saturn -140 C · Uranus -195 C ·
  Neptun -200 C (Gasplaneten: Wolkenobergrenze bei 1 bar, keine feste Oberflaeche -> Sternchen).
  Pizzaofen (neapolitanisch) ~430-480 C, Backzeit 60-90 s (AVPN). "Baked" fuer Merkur/Venus ist eine
  Naeherung (kein Sauerstoff, Venus zerdrueckt alles) -> Caption/first_comment.

Hook-Varianten:
  1 "Could you bake a PIZZA on each planet?" (gewaehlt)   2 "Which planet is a pizza oven?"
  3 "Your pizza on every planet"   4 "Only 2 planets can bake a pizza"   5 "Pizza delivery: solar system edition"

    python make-w6-pizza-planets-loop.py  ->  w6-pizza-planets.mp4, w6-pizza-planets-cover.png
"""

import math
import os
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, downscale
import numpy as np

from bodies import planet, fbm, mix, col, smooth
from reelkit import W as WS, new_frame, header_band, blob

OUT = Path(__file__).resolve().parent
W, H, FPS, LOOP = 1080, 1920, 30, 9.0
HOT, COLD = (255, 120, 70), (140, 190, 255)
# Name, Textur, Temperatur C, Ergebnis, Markierung
BODIES = [("Mercury", "mercury", 430, "BAKED", "¹"), ("Venus", "venus", 465, "BAKED", "²"),
          ("Earth", "earth", 15, "RAW", ""), ("Moon", "moon", 120, "WARM", "¹"),
          ("Mars", "mars", -65, "FROZEN", ""), ("Jupiter", "jupiter", -110, "FROZEN", "*"),
          ("Saturn", "saturn", -140, "FROZEN", "*"), ("Uranus", "uranus", -195, "FROZEN", "*"),
          ("Neptune", "neptune", -200, "FROZEN", "*")]
GRID_TOP, CELL_W, CELL_H = 540, 340, 330
GROUND = 250
R = 900
PZ = 220                                           # Pizza-Durchmesser (Ausgabe-px)


def cell_origin(i):
    return (W - 3 * CELL_W) // 2 + (i % 3) * CELL_W, GRID_TOP + (i // 3) * CELL_H


def background():
    img, _ = new_frame(37)
    header_band(img, ["Could you bake a PIZZA", "on each planet?"], "PIZZA")
    for i, (name, kind, temp, res, mark) in enumerate(BODIES):
        x0, y0 = cell_origin(i)
        x0, y0 = x0 * S, y0 * S
        cw, ch = CELL_W * S, CELL_H * S
        cell = img.crop((x0, y0, x0 + cw, y0 + ch))
        sky = Image.new("RGB", cell.size, (0, 0, 0))
        blob(sky, cw // 2, int(GROUND * S), int(cw * 0.7), int(110 * S), (40, 46, 70), blur=int(60 * S))
        cell = ImageChops.add(cell, sky)
        planet(cell, cw // 2, int((GROUND + R / 2 - 6) * S), R, kind, light=(0.0, -0.9, 0.45), glow=False)
        img.paste(cell, (x0, y0))
        d = ImageDraw.Draw(img)
        d.rectangle([x0 + 4 * S, y0 + 4 * S, x0 + cw - 4 * S, y0 + ch - 4 * S], outline=HAIR, width=2 * S)
    d = ImageDraw.Draw(img)
    y = (GRID_TOP + 3 * CELL_H + 22) * S
    for ln in ["¹day side  ²and crushed by air 90x denser than Earth's", "*no solid ground - cloud tops"]:
        d.text(((WS - d.textlength(ln, font=f(24 * S))) / 2, y), ln, font=f(24 * S), fill=SEC)
        y += 32 * S
    cta = "Send this to your pizza-obsessed friend"
    d.text(((WS - d.textlength(cta, font=f(34 * S, bold=True))) / 2, y + 14 * S), cta,
           font=f(34 * S, bold=True), fill=FG)
    return downscale(img, W, H)


def pizza_sprite(state):
    """Pizza mit Rausch-Texturen (Rand mit Leopardenflecken, Tomate, Mozzarella, Basilikum), von oben
    berechnet und perspektivisch gestaucht. state: 'raw', 'baked' oder 'frozen'. RGBA in Ausgabe-px."""
    N = 480
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    dx, dy = (xx - N / 2) / (N / 2), (yy - N / 2) / (N / 2)
    ang = np.arctan2(dy, dx)
    n1, n2, n3 = fbm(11, N, N, wrap=False), fbm(12, N, N, wrap=False), fbm(13, N, N, base=8, wrap=False)
    r = np.sqrt(dx * dx + dy * dy) * (1 + 0.006 * np.sin(ang * 5) + 0.035 * (n1 - 0.5))   # leicht unrund
    baked = state == "baked"
    # Rand: Wulst mit Lichtkante, Farbe je nach Backgrad
    crust_c = col((200, 132, 62) if baked else (232, 196, 138))
    rim = np.clip(np.sin(np.pi * (r - 0.78) / 0.22), 0, 1)
    img = crust_c * (0.72 + 0.38 * rim[..., None]) * (0.85 + 0.3 * n2[..., None])
    if baked:                                                             # Leopardenflecken
        spots = smooth(0.70, 0.78, n3) * (r > 0.80)
        img = mix(img, col((58, 32, 18)), spots * 0.9)
    # Tomatensauce mit unregelmaessigem Rand
    sauce_edge = 0.80 + 0.04 * (n1 - 0.5)
    sauce = smooth(sauce_edge + 0.01, sauce_edge - 0.01, r)
    sauce_c = col((172, 34, 20) if baked else (196, 44, 26)) * (0.8 + 0.4 * n2[..., None])
    img = mix(img, sauce_c, sauce)
    # Mozzarella: unregelmaessige Flecken
    rng = np.random.default_rng(7)
    cheese = np.zeros((N, N), np.float32)
    for _ in range(9):
        a_, rr = rng.uniform(0, 2 * np.pi), rng.uniform(0.08, 0.55)
        cx, cy, rad = np.cos(a_) * rr, np.sin(a_) * rr, rng.uniform(0.11, 0.17)
        d = np.sqrt((dx - cx) ** 2 + (dy - cy) ** 2) / (rad * (0.8 + 0.4 * n3))
        cheese = np.maximum(cheese, smooth(1.0, 0.85, d))
    cheese_c = col((246, 238, 216)) * (0.9 + 0.12 * n1[..., None])
    if baked:                                                             # goldene Blasen
        cheese_c = mix(cheese_c, col((212, 150, 70)), smooth(0.62, 0.8, n3) * 0.85)
    img = mix(img, cheese_c, cheese * (r < 0.8))
    # Basilikum
    for _ in range(5):
        a_, rr = rng.uniform(0, 2 * np.pi), rng.uniform(0.15, 0.55)
        cx, cy, rot = np.cos(a_) * rr, np.sin(a_) * rr, rng.uniform(0, np.pi)
        u = (dx - cx) * np.cos(rot) + (dy - cy) * np.sin(rot)
        v = -(dx - cx) * np.sin(rot) + (dy - cy) * np.cos(rot)
        leaf = smooth(1.0, 0.9, np.sqrt((u / 0.12) ** 2 + (v / 0.07) ** 2))
        leaf_c = col((28, 74, 30) if baked else (48, 128, 52)) * (0.8 + 0.3 * smooth(0.0, 0.012, np.abs(v)))[..., None]
        img = mix(img, leaf_c, leaf)
    if state == "frozen":                                                 # Reif: entsaettigt, blaeulich, Eiskristalle
        grey = img.mean(axis=2, keepdims=True)
        img = mix(img, grey, np.full((N, N), 0.5, np.float32))
        img = mix(img, col((214, 230, 255)), np.full((N, N), 0.35, np.float32) + 0.35 * smooth(0.6, 0.9, n3))
        sparkle = (np.random.default_rng(3).random((N, N)) > 0.992).astype(np.float32)
        img = mix(img, col((255, 255, 255)), sparkle)
    alpha = smooth(1.0, 0.985, r)
    rgba = np.dstack([np.clip(img, 0, 255), alpha * 255]).astype(np.uint8)
    sp = Image.fromarray(rgba, "RGBA")
    return sp.resize((PZ, int(PZ * 0.58)), Image.LANCZOS)                 # perspektivisch gestaucht


def frame(bg, sprites, t):
    im = bg.copy().convert("RGBA")
    ph = 0.5 - 0.5 * math.cos(2 * math.pi * t / LOOP)
    p = min(1.0, max(0.0, (ph - 0.1) / 0.75))                                 # Temperaturverlauf
    for i, (name, kind, temp, res, mark) in enumerate(BODIES):
        x0, y0 = cell_origin(i)
        target = sprites["baked" if res == "BAKED" else "frozen" if res == "FROZEN" else "raw"]
        raw = sprites["raw"]
        k = p if res in ("BAKED", "FROZEN") else 0.0
        pz = Image.blend(raw, target, k)
        px, py = x0 + CELL_W // 2 - PZ // 2, y0 + GROUND - 50 - pz.height // 2
        sh = Image.new("RGBA", (PZ + 40, 60), (0, 0, 0, 0))                   # Schatten auf dem Boden
        blob(sh, sh.width // 2, 30, PZ // 2 + 4, 16, (0, 0, 0), blur=8, alpha=150)
        im.alpha_composite(sh, (px - 20, py + pz.height - 38))
        if res == "BAKED" and p > 0.2:                                        # Hitzeschimmer
            glow = Image.new("RGBA", (PZ + 80, 120), (0, 0, 0, 0))
            blob(glow, glow.width // 2, 60, int(PZ * 0.6), 34, (255, 130, 50), blur=18, alpha=int(150 * p))
            im.alpha_composite(glow, (px - 40, py - 40))
        im.alpha_composite(pz, (px, py))
        d = ImageDraw.Draw(im)
        st = dict(stroke_width=2, stroke_fill=(8, 10, 14))
        d.text((x0 + 16, y0 + GROUND + 22), name + mark, font=f(30, bold=True),
               fill=ACC if name == "Earth" else FG, **st)
        cur = 20 + (temp - 20) * p
        lab = f"{cur:+.0f}°C" if abs(cur) >= 1 else "0°C"
        col = HOT if cur > 60 else COLD if cur < 0 else FG
        tw = d.textlength(lab, font=f(30, bold=True))
        d.text((x0 + CELL_W - tw - 16, y0 + GROUND + 22), lab, font=f(30, bold=True), fill=col, **st)
        a = min(1.0, max(0.0, (ph - 0.82) / 0.12))                            # Ergebnis-Stempel
        if a > 0:
            rc = {"BAKED": HOT, "FROZEN": COLD, "RAW": SEC, "WARM": ACC}[res]
            fo = f(40, bold=True)
            tw = d.textlength(res, font=fo)
            d.text((x0 + (CELL_W - tw) / 2, y0 + 70), res, font=fo, fill=rc + (int(255 * a),),
                   stroke_width=3, stroke_fill=(8, 10, 14, int(255 * a)))
    return im.convert("RGB")


def main():
    bg = background()
    sprites = {s: pizza_sprite(s) for s in ("raw", "baked", "frozen")}
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = OUT / "w6-pizza-planets.mp4"
    n = int(LOOP * FPS)
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(frame(bg, sprites, i / FPS).tobytes())
    proc.stdin.close()
    proc.wait()
    frame(bg, sprites, LOOP / 2).save(OUT / "w6-pizza-planets-cover.png")
    frame(bg, sprites, 0.3).save(Path(os.environ.get("CHECK_DIR", OUT)) / "_check-pizza-start.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
