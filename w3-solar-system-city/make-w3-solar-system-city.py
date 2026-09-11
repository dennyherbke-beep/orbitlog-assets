"""Woche 3, Sonntag - Reel "If the solar system fit in your city". 8 Standbild-Frames,
1080x1920. Schrumpft die Sonne auf einen Beachball (30 cm) und zeigt, wie weit die
Planeten in diesem Modell entfernt waeren - realistische Groessenordnung fuer eine Stadt.
Eigene Vektor-Grafik (schattierte Kugeln, Technik wie w2-moon-distance), keine NASA-Fotos.

Herleitung: Sonnendurchmesser 1.391.000 km -> Modell-Durchmesser 0.3 m,
Skalenfaktor k = 0.3 / 1.391.000.000 m = 2.1567e-10. Mittlere Bahnradien (AU, NASA
Planetary Fact Sheet) * 149.597.870.700 m/AU * k = Modell-Entfernung in Metern:
Mercury 0.387 AU -> 12.5 m; Venus 0.723 AU -> 23.3 m; Earth 1.000 AU -> 32.3 m;
Mars 1.524 AU -> 49.2 m; Jupiter 5.203 AU -> 167.9 m; Saturn 9.537 AU -> 307.7 m;
Uranus 19.191 AU -> 619.3 m; Neptune 30.069 AU -> 970.3 m.

    python make-w3-solar-system-city.py   ->  w3-solar-system-city-01..08.png (+ montage)

Naechster Schritt: Frames zu einem Reel zusammensetzen (ffmpeg, ~2.5 s/Frame, ohne Musik -
gleiche Begruendung wie bei w1-planet-sizes-reel/w2-moon-distance) -> .mp4 + Cover.
"""

import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono, tracked, wrap, canvas, ring_mark, downscale

OUT = Path(__file__).resolve().parent
W = 1080 * S
H = 1920 * S
M = 96 * S
TOP_SAFE = 250 * S
BOT_SAFE = 300 * S

GLOW_COLOR = {"Mercury": (170, 160, 150), "Venus": (226, 198, 150), "Earth": (80, 140, 210),
              "Mars": (205, 110, 75), "Jupiter": (214, 172, 120), "Saturn": (218, 196, 150),
              "Uranus": (150, 210, 220), "Neptune": (80, 110, 220)}

TEX = 512


# ---------------------------------------------------------------- Schattierung (wie w2-moon-distance)

def _build_shade():
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


def tex_mercury():
    img = Image.new("RGB", (TEX, TEX), (162, 152, 144))
    rnd = random.Random(1)
    for _ in range(22):
        cx, cy = rnd.randint(60, TEX - 60), rnd.randint(60, TEX - 60)
        r = rnd.randint(10, 34)
        col = tuple(max(0, c + rnd.randint(-38, -14)) for c in (162, 152, 144))
        blob(img, cx, cy, r, r, col, blur=r * 0.4)
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


def tex_mars():
    img = Image.new("RGB", (TEX, TEX), (196, 101, 66))
    dark = (140, 68, 42)
    blob(img, 210, 270, 95, 60, dark, blur=16)
    blob(img, 340, 190, 60, 42, dark, blur=14)
    blob(img, 300, 340, 40, 26, dark, blur=10)
    blob(img, 256, 70, 80, 30, (236, 228, 220), blur=10)
    return img


def tex_jupiter():
    img = Image.new("RGB", (TEX, TEX), (206, 164, 112))
    n = 8
    for i in range(n):
        if i % 2 == 0:
            y0, y1 = int(TEX * i / n), int(TEX * (i + 1) / n)
            band(img, y0, y1, (170, 120, 76), alpha=210, blur=6)
    blob(img, 335, 300, 48, 30, (178, 86, 56), blur=6)
    return img


def tex_saturn():
    img = Image.new("RGB", (TEX, TEX), (222, 198, 150))
    n = 7
    for i in range(n):
        if i % 2 == 0:
            y0, y1 = int(TEX * i / n), int(TEX * (i + 1) / n)
            band(img, y0, y1, (196, 168, 118), alpha=150, blur=10)
    return img


def tex_uranus():
    img = Image.new("RGB", (TEX, TEX), (176, 222, 224))
    band(img, 220, 260, (156, 206, 210), alpha=90, blur=40)
    return img


def tex_neptune():
    img = Image.new("RGB", (TEX, TEX), (66, 96, 208))
    band(img, 70, 120, (46, 70, 165), alpha=90, blur=16)
    band(img, 250, 290, (46, 70, 165), alpha=70, blur=16)
    blob(img, 320, 235, 65, 42, (38, 60, 150), blur=14)
    return img


TEXTURES = {"Mercury": tex_mercury, "Venus": tex_venus, "Earth": tex_earth, "Mars": tex_mars,
            "Jupiter": tex_jupiter, "Saturn": tex_saturn, "Uranus": tex_uranus, "Neptune": tex_neptune}


def sphere(img, cx, cy, d_px, name, ring=False):
    shade, mask = maps()
    d = max(2, int(d_px * S))
    r = d // 2

    glow_r = int(r * 1.5)
    blob(img, cx, cy, glow_r, glow_r, GLOW_COLOR[name], blur=int(r * 0.55), alpha=110)

    if ring:
        rd = ImageDraw.Draw(img)
        rx, ry = int(r * 1.9), int(r * 0.55)
        rd.arc([cx - rx, cy - ry, cx + rx, cy + ry], 20, 160, fill=(214, 196, 158), width=max(2, int(r * 0.05)))

    tex = TEXTURES[name]()
    shaded = ImageChops.multiply(tex, Image.merge("RGB", (shade, shade, shade)))
    shaded = shaded.resize((d, d), Image.LANCZOS)
    m = mask.resize((d, d), Image.LANCZOS)
    img.paste(shaded, (cx - r, cy - r), m)

    if ring:
        rd = ImageDraw.Draw(img)
        rx, ry = int(r * 1.9), int(r * 0.55)
        rd.arc([cx - rx, cy - ry, cx + rx, cy + ry], 200, 340, fill=(236, 220, 182), width=max(2, int(r * 0.05)))


# ---------------------------------------------------------------- Hintergrund / Rahmen

def starfield(img, seed, n=170):
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        r = rnd.uniform(0.6, 1.8) * S
        op = rnd.randint(70, 200)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(op, op, min(255, op + 20)))
    for _ in range(n // 12):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        r = rnd.uniform(2.0, 3.4) * S
        gl = Image.new("L", img.size, 0)
        ImageDraw.Draw(gl).ellipse([x - r * 3, y - r * 3, x + r * 3, y + r * 3], fill=90)
        gl = gl.filter(ImageFilter.GaussianBlur(r * 1.4))
        img.paste(Image.new("RGB", img.size, FG), (0, 0), gl)
        d.ellipse([x - r, y - r, x + r, y + r], fill=FG)


def header(d, label):
    tracked(d, (M, TOP_SAFE), label, fmono(26 * S), ACC, 5 * S)


def footer_handle(d):
    text = "@theorbitlog"
    tw = d.textlength(text, font=fmono(22 * S))
    d.text((W / 2 - tw / 2, H - BOT_SAFE + 6 * S), text, font=fmono(22 * S), fill=SEC)


def ruler(d, step, total=8):
    """Kleine Fortschrittsanzeige unten (symbolisch, nicht laengenmasstaeblich)."""
    y = H - BOT_SAFE - 70 * S
    x0 = W / 2 - (total - 1) * 26 * S / 2
    for i in range(total):
        x = x0 + i * 26 * S
        r = 6 * S if i != step else 9 * S
        col = ACC if i == step else HAIR
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)


# ---------------------------------------------------------------- Content

CONTENT = [
    ("Mercury", "12 m away", "about the length of a city bus"),
    ("Venus", "23 m away", "about the length of a tennis court"),
    ("Mars", "49 m away", "about half a soccer field"),
    ("Jupiter", "168 m away", "nearly two soccer fields - and the size of a chestnut"),
    ("Saturn", "308 m away", "about three soccer fields, rings and all"),
    ("Neptune", "970 m away", "nearly a kilometer - likely the edge of your neighborhood"),
]


def sun_beachball(img, cx, cy, r):
    core = (255, 244, 214)
    edge = (255, 150, 50)
    glow_r = int(r * 2.0)
    blob(img, cx, cy, glow_r, glow_r, ACC, blur=int(r * 0.8), alpha=90)
    for i in range(r, 0, -1):
        t = i / r
        col = tuple(int(edge[k] + (core[k] - edge[k]) * (1 - t)) for k in range(3))
        d = ImageDraw.Draw(img)
        d.ellipse([cx - i, cy - i, cx + i, cy + i], fill=col)


def frame_title():
    img, d = canvas(W, H)
    starfield(img, seed=1)
    d = ImageDraw.Draw(img)
    header(d, "TO SCALE")
    sun_beachball(img, W - int(W * 0.20), TOP_SAFE + int(H * 0.14), int(W * 0.09))
    d = ImageDraw.Draw(img)
    y = TOP_SAFE + int(H * 0.28)
    fo = f(80 * S, bold=True)
    for ln in ["If the solar", "system fit in", "your city"]:
        d.text((M, y), ln, font=fo, fill=FG)
        y += 92 * S
    d.text((M, y + 16 * S), "shrink the Sun to a beach ball →", font=f(32 * S), fill=SEC)
    footer_handle(d)
    return img


def frame_planet(i):
    name, dist, comp = CONTENT[i]
    img, d = canvas(W, H)
    starfield(img, seed=10 + i)
    d = ImageDraw.Draw(img)
    header(d, f"SOLAR SYSTEM · {i + 1}/6")

    cy = TOP_SAFE + int((H - TOP_SAFE - BOT_SAFE) * 0.36)
    size = {"Mercury": 70, "Venus": 110, "Mars": 84, "Jupiter": 210, "Saturn": 190, "Neptune": 130}[name]
    sphere(img, W // 2, cy, size, name, ring=(name == "Saturn"))
    d = ImageDraw.Draw(img)

    ty = cy + int(size * S * 0.62) + 70 * S
    fo = f(46 * S, bold=True)
    tw = d.textlength(name, font=fo)
    d.text((W / 2 - tw / 2, ty), name, font=fo, fill=FG)
    ty += 66 * S

    fb = f(64 * S, bold=True)
    tw = d.textlength(dist, font=fb)
    d.text((W / 2 - tw / 2, ty), dist, font=fb, fill=ACC)
    ty += 88 * S

    fs = f(30 * S)
    for ln in wrap(d, comp, fs, W - 2 * M):
        tw = d.textlength(ln, font=fs)
        d.text((W / 2 - tw / 2, ty), ln, font=fs, fill=SEC)
        ty += 42 * S

    ruler(d, i)
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
        downscale(im, 1080, 1920).save(OUT / f"w3-solar-system-city-{n:02d}.png")
    th_w, th_h = 240, 427
    mont = Image.new("RGB", (th_w * 4, th_h * 2), (0, 0, 0))
    for i, im in enumerate(frames):
        mont.paste(downscale(im, 1080, 1920).resize((th_w, th_h)), ((i % 4) * th_w, (i // 4) * th_h))
    mont.save(OUT / "w3-solar-system-city_montage.png")
    print("saved", len(frames), "frames + montage")


if __name__ == "__main__":
    main()
