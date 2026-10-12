"""Woche 7, Donnerstag 15.10.2026 - Winner-Variante zum Andromeda-Reel (Kommentar-Frage "Why couldn't I see
it?"): derselbe Himmelsausschnitt (Cassiopeia -> Andromeda) im 2x2-Raster unter vier Lichtverschmutzungs-
Stufen. Kombiniert die beiden Winner-Formate (Raster-Loop + realistischer Himmel).

Hook-Varianten:
  1. Couldn't see ANDROMEDA? It's not your eyes.          <- gewaehlt (Frage aus den Kommentaren)
  2. Same sky, four places - where can you see ANDROMEDA?
  3. City lights hide a whole GALAXY from you.
  4. Why ANDROMEDA disappears in the city
  5. Your sky is hiding 2,000 stars

Ablauf (10 s Loop): Zelle fuer Zelle (City -> Suburbs -> Countryside -> Dark site) wird hervorgehoben,
Ring um die Andromeda-Position (rot gestrichelt = nicht sichtbar), Zeile darunter erklaert; zum Schluss alle
Zellen + Handlung "Fix: get away from city lights".

Fakten: Bortle-Skala (Bortle 2001, Sky & Telescope): Grenzgroesse Innenstadt (8-9) ~4 mag, helle Vorstadt
(6) ~5-5,5 mag, Land (4) ~6-6,5 mag, dunkler Ort (1-2) ~7 mag; M31 ~3,4 mag, aber geringe Flaechenhelligkeit -
in der Vorstadt hoechstens der Kern (Fernglas), ab laendlichem Himmel als Nebelfleck mit blossem Auge.
Sternpositionen/Renderer aus w6-andromeda-weekend/make-w6-andromeda-weekend-loop.py.

    python make-w7-andromeda-dark-sky-reel.py  ->  w7-andromeda-dark-sky.mp4, -cover.png
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
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from brandkit import S, FG, SEC, ACC, f, downscale, canvas
from reelkit import W as CW, H as CH, header_band, deep_sky, cinematic

_spec = importlib.util.spec_from_file_location("andro", ROOT / "w6-andromeda-weekend" / "make-w6-andromeda-weekend-loop.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

OUT = Path(__file__).resolve().parent
W, H, FPS, LOOP = 1080, 1920, 30, 10.0
GX0, GY0, CWID, CHGT, GAP = 30, 600, 502, 480, 16
RED = (235, 92, 80)
LEVELS = [  # Name, Bortle, Grenzgroesse, Galaxie-Gain, Milchstrasse, Lichtglocke (Staerke, Farbe), Urteil, Sterne
    ("City center", "Bortle 8-9", 3.9, 0.0, False, (78, (255, 168, 96)), "Andromeda: invisible", RED, 0),
    ("Suburbs", "Bortle 6", 5.0, 0.3, False, (40, (235, 170, 120)), "only the core, with binoculars", SEC, 260),
    ("Countryside", "Bortle 4", 6.0, 1.2, True, (12, (190, 170, 150)), "a faint, oval smudge", FG, 1300),
    ("Dark site", "Bortle 1-2", 6.9, 2.0, True, (0, (0, 0, 0)), "clear - plus the Milky Way", ACC, 3200),
]
LINES = ["City: only the brightest stars survive", "Suburbs: Andromeda's core, barely",
         "Countryside: there it is - a soft glow", "Dark site: a galaxy and the Milky Way",
         "Fix: get away from city lights"]
PROJ = A.Proj(14.0, 52.0, 14.0, CWID / 2, 225)


def cell_pos(i):
    return GX0 + (i % 2) * (CWID + GAP), GY0 + (i // 2) * (CHGT + GAP)


def silhouette(img, kind, ss):
    """Vordergrund je Ort: Hochhaeuser mit Fenstern, Haeuser, Baeume, Huegel."""
    d = ImageDraw.Draw(img)
    w, h = img.size
    base = h - 62 * ss
    rnd = random.Random(kind)
    dark = (6, 7, 10)
    if kind == 0:
        x = -10 * ss
        while x < w:
            bw, bh = rnd.randint(46, 90) * ss, rnd.randint(60, 120) * ss
            d.rectangle([x, base - bh + 60 * ss, x + bw, h], fill=dark)
            for wy in range(int(base - bh + 72 * ss), h - 10 * ss, 14 * ss):
                for wx in range(int(x + 8 * ss), int(x + bw - 8 * ss), 12 * ss):
                    if rnd.random() < 0.35:
                        c = rnd.choice([(255, 214, 150), (255, 236, 200), (210, 226, 255)])
                        d.rectangle([wx, wy, wx + 4 * ss, wy + 6 * ss], fill=tuple(int(v * 0.8) for v in c))
            x += bw + rnd.randint(2, 10) * ss
    elif kind == 1:
        d.rectangle([0, base + 30 * ss, w, h], fill=dark)
        x = 0
        while x < w:
            bw = rnd.randint(70, 110) * ss
            top = base + rnd.randint(-6, 12) * ss
            d.rectangle([x + 6 * ss, top, x + bw - 6 * ss, h], fill=dark)
            d.polygon([(x, top + 2 * ss), (x + bw / 2, top - 30 * ss), (x + bw, top + 2 * ss)], fill=dark)
            if rnd.random() < 0.6:
                wx = x + bw * rnd.uniform(0.3, 0.6)
                d.rectangle([wx, top + 18 * ss, wx + 8 * ss, top + 28 * ss], fill=(214, 170, 110))
            d.ellipse([x + bw - 8 * ss, base - 50 * ss, x + bw + 8 * ss, base - 34 * ss], fill=(255, 220, 170))  # Laterne
            d.line([x + bw, base - 36 * ss, x + bw, h], fill=dark, width=3 * ss)
            x += bw + rnd.randint(20, 60) * ss
    elif kind == 2:
        pts = [(0, h)] + [(w * i / 30, base + 26 * ss + math.sin(i * 0.5) * 8 * ss) for i in range(31)] + [(w, h)]
        d.polygon(pts, fill=dark)
        for x in rnd.sample(range(10, w // ss - 10, 18), 7):
            for k in range(4):
                bw = (30 - k * 6) * ss
                yb = base + 26 * ss - k * 22 * ss
                d.polygon([(x * ss - bw, yb), (x * ss + bw, yb), (x * ss, yb - 32 * ss)], fill=dark)
    else:
        pts = [(0, h)]
        for i in range(41):
            pts.append((w * i / 40, base + 30 * ss - 34 * ss * math.exp(-((i - 26) / 7) ** 2)
                        + math.sin(i * 0.9) * 4 * ss))
        pts.append((w, h))
        d.polygon(pts, fill=dark)


PAL = [(170, 192, 255), (214, 224, 255), (255, 250, 242), (255, 228, 186), (255, 198, 146)]


def faint_layer(img, n, seed, ss):
    """Zusaetzliche schwache Sterne (Potenzgesetz wie reelkit.deep_sky, aber ohne helle Ausreisser,
    damit das Cassiopeia-W erkennbar bleibt)."""
    rng = np.random.default_rng(seed)
    d = ImageDraw.Draw(img)
    w, h = img.size
    for _ in range(n):
        x, y, b = rng.uniform(0, w), rng.uniform(0, h), rng.random() ** 6
        c = PAL[rng.choice(5, p=[0.1, 0.25, 0.35, 0.2, 0.1])]
        r = (0.35 + 0.8 * b) * ss
        k = 0.22 + 0.55 * b ** 0.4
        d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v * k) for v in c))


def render_cell(i):
    name, bortle, limit, gain, mw, (glow, gcol), verdict, vcol, nstars = LEVELS[i]
    bright_all, fuzzy = A.BRIGHT, A.fuzzy
    A.BRIGHT = {k: v for k, v in bright_all.items() if v[2] <= limit - 0.6}
    if gain < 0.5:
        A.fuzzy = lambda *a: None                                     # M32/M110 nur unter dunklem Himmel
    sky = A.render_sky(CWID, CHGT, PROJ, limit=limit, ss=2, mw=mw, horizon_glow=False, star_k=0.85,
                       gal_gain=gain)
    A.BRIGHT, A.fuzzy = bright_all, fuzzy
    if mw:                                                            # Milchstrasse kraeftiger (dunkle Orte)
        from bodies import fbm
        ra, dec = PROJ.inverse_grid(CWID // 4, CHGT // 4, step=4)
        b, _ = A.galactic_b(ra, dec)
        n1 = fbm(7, CHGT // 4, CWID // 4, octaves=5, base=4, wrap=False)
        band = np.exp(-(b / 11) ** 2) * (0.5 + 0.9 * n1) * (40 if i == 3 else 16)
        lay = Image.fromarray(np.clip(band, 0, 255).astype(np.uint8)).resize(sky.size, Image.BICUBIC)
        arr = np.asarray(sky, np.float32) + np.asarray(lay, np.float32)[..., None] * np.array([0.85, 0.87, 1.0])
        sky = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    faint_layer(sky, nstars, 30, 2)
    arr = np.asarray(sky, np.float32)
    if glow:                                                          # Lichtglocke: unten stark, oben schwach
        y = np.linspace(0, 1, arr.shape[0])[:, None, None]
        arr = arr + glow * (0.3 + 0.7 * y ** 2.2) * (np.array(gcol, np.float32) / 255)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    dl = ImageDraw.Draw(img, "RGBA")                                  # Cassiopeia-W dezent verbinden
    wpts = [tuple(v * 2 for v in PROJ.xy(*bright_all[nm][:2])) for nm in A.W_STARS]
    dl.line(wpts, fill=(150, 170, 215, 70), width=3)
    silhouette(img, i, 2)
    img = img.resize((CWID, CHGT), Image.LANCZOS)
    d = ImageDraw.Draw(img)
    st = dict(stroke_width=3, stroke_fill=(5, 6, 9))
    d.text((16, 12), name, font=f(32, bold=True), fill=FG, **st)
    d.text((CWID - 16 - d.textlength(bortle, font=f(22)), 20), bortle, font=f(22), fill=SEC, **st)
    d.text(((CWID - d.textlength(verdict, font=f(26, bold=True))) / 2, CHGT - 44), verdict,
           font=f(26, bold=True), fill=vcol, **st)
    return img


def background(cells):
    img, _ = canvas(CW, CH)
    deep_sky(img, 71, band=(0.2, 0.34))
    y = header_band(img, ["Couldn't see ANDROMEDA?", "It's not your eyes."], "ANDROMEDA")
    d = ImageDraw.Draw(img)
    sub = "Same sky · same night · four places"
    d.text(((CW - d.textlength(sub, font=f(30 * S))) / 2, y + 2 * S), sub, font=f(30 * S), fill=SEC)
    for n, (txt, fo, col) in enumerate([("Save this for your next dark night", f(38 * S, bold=True), FG),
                                        ("Send it to someone who never found it", f(30 * S), SEC)]):
        d.text(((CW - d.textlength(txt, font=fo)) / 2, (1676 + n * 50) * S), txt, font=fo, fill=col)
    bg = downscale(img, W, H)
    for i, c in enumerate(cells):
        bg.paste(c, cell_pos(i))
    return bg


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def frame(bg, cells, t):
    im = bg.copy()
    k = int(t // 2)                                                   # 0..3 Zellen, 4 = alle
    ph = (t % 2) / 2
    on = ease(ph / 0.15) * (1 - ease((ph - 0.88) / 0.12)) if k < 4 else 0
    d = ImageDraw.Draw(im, "RGBA")
    for i in range(4):
        x, y = cell_pos(i)
        if k < 4 and i != k:
            d.rectangle([x, y, x + CWID, y + CHGT], fill=(0, 0, 0, int(95 * on)))
        hi = on if i == k else 0
        col = ACC if i == k else (70, 78, 96)
        d.rectangle([x - 2, y - 2, x + CWID + 1, y + CHGT + 1], outline=col + (int(120 + 135 * hi),), width=3)
        if i == k:                                                    # Ring um die Andromeda-Position
            gx, gy = PROJ.xy(*A.M31)
            gx, gy, r = x + gx, y + gy, 34 + 6 * math.sin(ph * math.pi)
            rc = RED if i == 0 else ACC
            if i == 0:
                for a in range(0, 360, 30):
                    d.arc([gx - r, gy - r, gx + r, gy + r], a, a + 16, fill=rc + (int(255 * on),), width=4)
                d.text((gx - 9, gy - 22), "?", font=f(34, bold=True), fill=rc + (int(255 * on),))
            else:
                d.ellipse([gx - r, gy - r, gx + r, gy + r], outline=rc + (int(255 * on),), width=4)
    txt = LINES[min(k, 4)]
    al = on if k < 4 else ease((t - 8) / 0.3) * (1 - ease((t - 9.7) / 0.3))
    fo = f(40, bold=True)
    d.text(((W - d.textlength(txt, font=fo)) / 2, 1588), txt, font=fo,
           fill=(ACC if k == 4 else FG) + (int(255 * al),))
    return im


def main():
    cells = [render_cell(i) for i in range(4)]
    bg = background(cells)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = OUT / "w7-andromeda-dark-sky.mp4"
    n = int(LOOP * FPS)
    chk = Path(os.environ.get("CHECK_DIR", OUT))
    for t in (1.0, 5.0, 8.8):
        cinematic(frame(bg, cells, t), 0).save(chk / f"_check-dark-{t:.1f}.png")
    if os.environ.get("CHECK_ONLY"):
        return
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart",
        str(out)], stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg, cells, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg, cells, 5.0), 0).save(OUT / "w7-andromeda-dark-sky-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
