"""Woche 1, Sonntag - Reel "Planet sizes, to scale". 8 Standbild-Frames, 1080x1920.
Planeten als eigene Vektor-Grafik (keine NASA-Fotos): schattierte 3D-Kugeln (Lambert-
Beleuchtung) mit Oberflaechenmerkmalen (Kontinente, Wolken, Kraterflecken, Baender,
Sturmflecken) statt flacher Kreise, plus Sternfeld-Hintergrund und Atmosphaeren-Glow.
Durchmesser linear zueinander skaliert (Jupiter = 820 px). Spec: docs/canva-vorlagen-woche1.md,
Post 5.

    python make-w1-planet-sizes.py   ->  w1-planet-sizes-01.png ... -08.png (+ montage)

Naechster Schritt: Frames in einer Schnitt-App zu einem Reel (MP4, ~2.5 s/Frame,
Musik) zusammensetzen -> w1-planet-sizes.mp4 + Cover-Bild.
"""

import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono, tracked, canvas, ring_mark, downscale

OUT = Path(__file__).resolve().parent
W = 1080 * S
H = 1920 * S
M = 96 * S
TOP_SAFE = 250 * S
BOT_SAFE = 250 * S
BASELINE = H - BOT_SAFE - 260 * S

PLANETS = ["Mercury", "Mars", "Venus", "Earth", "Neptune", "Jupiter"]
DIAMETERS = {"Mercury": 4879, "Mars": 6779, "Venus": 12104, "Earth": 12742,
             "Neptune": 49244, "Jupiter": 139820}
GLOW_COLOR = {"Mercury": (170, 160, 150), "Mars": (205, 110, 75), "Venus": (226, 198, 150),
              "Earth": (80, 140, 210), "Neptune": (80, 110, 220), "Jupiter": (214, 172, 120)}
MAX_DIAM = max(DIAMETERS.values())
MAX_PX = 820

TEX = 512  # interne Textur-/Schattierungsaufloesung pro Planet


# ---------------------------------------------------------------- Schattierung

def _build_shade():
    """Lambert-Kugel: Normalen aus der Kreisflaeche, eine Lichtquelle oben links."""
    light = (-0.55, -0.65, 0.62)
    n = sum(c * c for c in light) ** 0.5
    lx, ly, lz = (c / n for c in light)
    img = Image.new("L", (TEX, TEX), 0)
    px = img.load()
    r = TEX / 2
    for j in range(TEX):
        ny = (j - r + 0.5) / r
        row_base = ny * ly
        for i in range(TEX):
            nx = (i - r + 0.5) / r
            d2 = nx * nx + ny * ny
            if d2 <= 1.0:
                nz = (1.0 - d2) ** 0.5
                inten = max(0.0, nx * lx + row_base + nz * lz)
                px[i, j] = int(min(255, 40 + inten * 215))
    return img


def _build_mask():
    img = Image.new("L", (TEX, TEX), 0)
    ImageDraw.Draw(img).ellipse([2, 2, TEX - 3, TEX - 3], fill=255)
    return img.filter(ImageFilter.GaussianBlur(1.2))


_MAPS = {}


def maps():
    if not _MAPS:
        _MAPS["shade"] = _build_shade()
        _MAPS["mask"] = _build_mask()
    return _MAPS["shade"], _MAPS["mask"]


def blob(img, cx, cy, rx, ry, color, blur=10, alpha=255):
    layer = Image.new("RGB", img.size, color)
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=alpha)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    img.paste(layer, (0, 0), m)


def band(img, y0, y1, color, alpha=255, blur=10):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rectangle([0, y0, TEX, y1], fill=alpha)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    img.paste(Image.new("RGB", img.size, color), (0, 0), m)


# ---------------------------------------------------------------- Texturen

def tex_mercury():
    img = Image.new("RGB", (TEX, TEX), (162, 152, 144))
    rnd = random.Random(1)
    for _ in range(22):
        cx, cy = rnd.randint(60, TEX - 60), rnd.randint(60, TEX - 60)
        r = rnd.randint(10, 34)
        shade = rnd.randint(-38, -14)
        col = tuple(max(0, c + shade) for c in (162, 152, 144))
        blob(img, cx, cy, r, r, col, blur=r * 0.4)
    return img


def tex_mars():
    img = Image.new("RGB", (TEX, TEX), (196, 101, 66))
    dark = (140, 68, 42)
    blob(img, 210, 270, 95, 60, dark, blur=16)
    blob(img, 340, 190, 60, 42, dark, blur=14)
    blob(img, 300, 340, 40, 26, dark, blur=10)
    blob(img, 256, 70, 80, 30, (236, 228, 220), blur=10)  # Polkappe
    return img


def tex_venus():
    img = Image.new("RGB", (TEX, TEX), (226, 199, 148))
    band(img, 120, 190, (203, 172, 118), alpha=90, blur=34)
    band(img, 300, 380, (240, 214, 168), alpha=70, blur=34)
    return img


def tex_earth():
    img = Image.new("RGB", (TEX, TEX), (40, 90, 160))
    land = (83, 122, 66)
    for cx, cy, rx, ry in [(175, 190, 85, 55), (330, 150, 55, 65), (245, 330, 70, 45), (380, 300, 38, 30)]:
        blob(img, cx, cy, rx, ry, land, blur=9)
    for cx, cy, rx, ry in [(150, 130, 95, 30), (350, 250, 85, 26), (230, 370, 100, 28)]:
        blob(img, cx, cy, rx, ry, (255, 255, 255), blur=20, alpha=110)
    return img


def tex_neptune():
    img = Image.new("RGB", (TEX, TEX), (66, 96, 208))
    band(img, 70, 120, (46, 70, 165), alpha=90, blur=16)
    band(img, 250, 290, (46, 70, 165), alpha=70, blur=16)
    blob(img, 320, 235, 65, 42, (38, 60, 150), blur=14)  # Great Dark Spot
    return img


def tex_jupiter():
    img = Image.new("RGB", (TEX, TEX), (206, 164, 112))
    n = 8
    for i in range(n):
        if i % 2 == 0:
            y0, y1 = int(TEX * i / n), int(TEX * (i + 1) / n)
            band(img, y0, y1, (170, 120, 76), alpha=210, blur=6)
    blob(img, 335, 300, 48, 30, (178, 86, 56), blur=6)  # Great Red Spot
    return img


TEXTURES = {"Mercury": tex_mercury, "Mars": tex_mars, "Venus": tex_venus,
            "Earth": tex_earth, "Neptune": tex_neptune, "Jupiter": tex_jupiter}


def diam_px(km):
    return km / MAX_DIAM * MAX_PX


def sphere(img, cx, bottom_y, size_px, name):
    shade, mask = maps()
    d = max(2, int(size_px * S))
    r = d // 2
    top = bottom_y - d

    glow_r = int(r * 1.5)
    blob(img, cx, top + r, glow_r, glow_r, GLOW_COLOR[name], blur=int(r * 0.55), alpha=110)

    tex = TEXTURES[name]()
    shaded = ImageChops.multiply(tex, Image.merge("RGB", (shade, shade, shade)))
    shaded = shaded.resize((d, d), Image.LANCZOS)
    m = mask.resize((d, d), Image.LANCZOS)
    img.paste(shaded, (cx - r, top), m)
    return top


# ---------------------------------------------------------------- Hintergrund / Rahmen

def starfield(img, seed, n=150):
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        r = rnd.uniform(0.6, 1.8) * S
        op = rnd.randint(70, 200)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(op, op, min(255, op + 20)))
    for _ in range(n // 10):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        r = rnd.uniform(2.0, 3.4) * S
        glow = Image.new("L", img.size, 0)
        ImageDraw.Draw(glow).ellipse([x - r * 3, y - r * 3, x + r * 3, y + r * 3], fill=90)
        glow = glow.filter(ImageFilter.GaussianBlur(r * 1.4))
        img.paste(Image.new("RGB", img.size, FG), (0, 0), glow)
        d.ellipse([x - r, y - r, x + r, y + r], fill=FG)


def header(d, label):
    tracked(d, (M, TOP_SAFE), label, fmono(26 * S), ACC, 5 * S)


def footer_handle(d):
    text = "@theorbitlog"
    tw = d.textlength(text, font=fmono(22 * S))
    d.text((W / 2 - tw / 2, H - BOT_SAFE + 6 * S), text, font=fmono(22 * S), fill=SEC)


# ---------------------------------------------------------------- Frames

def frame_title():
    img, d = canvas(W, H)
    starfield(img, seed=1)
    d = ImageDraw.Draw(img)
    header(d, "TO SCALE")
    y = TOP_SAFE + int(H * 0.16)
    fo = f(88 * S, bold=True)
    for ln in ["Planet sizes,", "to scale"]:
        d.text((M, y), ln, font=fo, fill=FG)
        y += 100 * S
    d.text((M, y + 16 * S), "watch them grow →", font=f(34 * S), fill=SEC)
    footer_handle(d)
    return img


def frame_planet(i):
    name = PLANETS[i]
    km = DIAMETERS[name]
    img, d = canvas(W, H)
    starfield(img, seed=10 + i)
    d = ImageDraw.Draw(img)
    header(d, f"PLANET SIZES · {i + 1}/6")

    bar_x, bar_w = M, 14 * S
    bar_top, bar_bot = TOP_SAFE + 90 * S, BASELINE
    d.rectangle([bar_x, bar_top, bar_x + bar_w, bar_bot], fill=HAIR)
    frac = km / MAX_DIAM
    fill_top = bar_bot - int((bar_bot - bar_top) * frac)
    d.rectangle([bar_x, fill_top, bar_x + bar_w, bar_bot], fill=ACC)

    d.line([M, BASELINE, W - M, BASELINE], fill=HAIR, width=2 * S)
    sphere(img, W // 2, BASELINE, diam_px(km), name)
    d = ImageDraw.Draw(img)

    fo, fs = f(56 * S, bold=True), f(32 * S)
    ty = BASELINE + 44 * S
    tw = d.textlength(name, font=fo)
    d.text((W / 2 - tw / 2, ty), name, font=fo, fill=FG)
    sub = f"{km:,} km"
    tw2 = d.textlength(sub, font=fs)
    d.text((W / 2 - tw2 / 2, ty + 68 * S), sub, font=fs, fill=SEC)
    footer_handle(d)
    return img


def frame_cta():
    img, d = canvas(W, H)
    starfield(img, seed=99)
    d = ImageDraw.Draw(img)
    ring_mark(img, W // 2, TOP_SAFE + int(H * 0.20), 46 * S)
    fo = f(58 * S, bold=True)
    y = TOP_SAFE + int(H * 0.32)
    for ln in ["Follow for one", "every day"]:
        tw = d.textlength(ln, font=fo)
        d.text((W / 2 - tw / 2, y), ln, font=fo, fill=FG)
        y += 72 * S
    handle = "@theorbitlog"
    fa = fmono(34 * S)
    tw = d.textlength(handle, font=fa)
    d.text((W / 2 - tw / 2, y + 20 * S), handle, font=fa, fill=ACC)
    return img


def main():
    frames = [frame_title()] + [frame_planet(i) for i in range(6)] + [frame_cta()]
    for n, im in enumerate(frames, 1):
        downscale(im, 1080, 1920).save(OUT / f"w1-planet-sizes-{n:02d}.png")
    th_w, th_h = 240, 427
    mont = Image.new("RGB", (th_w * 4, th_h * 2), (0, 0, 0))
    for i, im in enumerate(frames):
        mont.paste(downscale(im, 1080, 1920).resize((th_w, th_h)), ((i % 4) * th_w, (i // 4) * th_h))
    mont.save(OUT / "w1-planet-sizes_montage.png")
    print("saved 8 frames + montage")


if __name__ == "__main__":
    main()
