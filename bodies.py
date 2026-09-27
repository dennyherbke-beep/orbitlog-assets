"""Realistische Himmelskoerper fuer alle Grafiken (ab Woche 5, 27.09.2026).

Statt flacher Texturen auf einer Scheibe: prozedurale Equirectangular-Texturen (fraktales
Rauschen), echte Kugelprojektion (Baender/Kontinente kruemmen sich zum Rand, Rotation per
`lon0`), weicher Terminator, Atmosphaerensaum, Wolken, Krater, Saturnringe mit Cassini-Teilung
und Sterne mit Granulation, Randverdunkelung und Korona.

    from bodies import planet, star
    planet(img, cx, cy, d_px, "earth")                 # d_px in Ausgabe-Pixeln (x S intern)
    planet(img, cx, cy, d_px, "saturn", ring_tilt=12)  # Ring mit Neigung in Grad
    star(img, cx, cy, d_px, "sun")                     # "sun" | "red_dwarf"

Benoetigt: Pillow, numpy. Baut auf brandkit.S auf (Supersampling-Faktor der Leinwand).
"""

import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from brandkit import S

TW, TH = 1024, 512            # Texturgroesse (equirectangular)
_TEX = {}


# ---------------------------------------------------------------- Rauschen

def fbm(seed, h=TH, w=TW, octaves=6, base=4, persistence=0.52, wrap=True):
    """Fraktales Wertrauschen 0..1 (horizontal nahtlos, da equirectangular)."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        gw, gh = base * 2 ** o, max(2, base * 2 ** o // 2)
        g = rng.random((gh + 1, gw + 1)).astype(np.float32)
        if wrap:
            g[:, -1] = g[:, 0]
        layer = np.asarray(Image.fromarray(g).resize((w, h), Image.BICUBIC), np.float32)
        out += layer * amp
        total += amp
        amp *= persistence
    out /= total
    out -= out.min()
    return out / max(1e-6, out.max())


def lat_grid(h=TH, w=TW):
    lat = np.linspace(90, -90, h, dtype=np.float32)[:, None] * np.ones((1, w), np.float32)
    return lat


def mix(a, b, t):
    t = np.clip(t, 0, 1)[..., None]
    return a * (1 - t) + b * t


def col(c):
    return np.array(c, np.float32)[None, None, :]


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- Texturen

def _craters(img, seed, n, rmin, rmax, dark=0.8, rim=1.18):
    rng = np.random.default_rng(seed)
    h, w, _ = img.shape
    yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(n):
        cx, cy = rng.uniform(0, w), rng.uniform(h * 0.1, h * 0.9)
        r = rng.uniform(rmin, rmax)
        sx = r / max(0.25, math.cos(math.radians((0.5 - cy / h) * 180)))   # Equirect-Streckung
        x0, x1 = int(max(0, cx - sx * 1.4)), int(min(w, cx + sx * 1.4))
        y0, y1 = int(max(0, cy - r * 1.4)), int(min(h, cy + r * 1.4))
        if x1 <= x0 or y1 <= y0:
            continue
        dx = (xx[y0:y1, x0:x1] - cx) / sx
        dy = (yy[y0:y1, x0:x1] - cy) / r
        d = np.sqrt(dx * dx + dy * dy)
        f = np.ones_like(d)
        f = np.where(d < 0.85, dark + (1 - dark) * d / 0.85, f)
        f = np.where((d >= 0.85) & (d < 1.15), rim - (rim - 1) * np.abs(d - 1.0) / 0.15, f)
        img[y0:y1, x0:x1] *= f[..., None]


def tex_earth():
    lat = lat_grid()
    n = fbm(11, octaves=7, base=3)
    land = smooth(0.49, 0.53, n)
    deep, shallow = col((12, 38, 92)), col((30, 86, 150))
    ocean = mix(deep, shallow, smooth(0.40, 0.52, n))
    veg = fbm(12, octaves=6, base=6)
    desert = smooth(0.35, 0.7, veg) * (1 - smooth(20, 40, np.abs(lat))) + smooth(0.62, 0.8, veg) * 0.5
    ground = mix(col((58, 104, 48)), col((176, 150, 104)), desert)
    ground = mix(ground, col((96, 88, 72)), smooth(0.66, 0.78, n) * 0.6)          # Gebirge
    img = mix(ocean, ground, land)
    ice = smooth(66, 74, np.abs(lat) + (fbm(13, octaves=4) - 0.5) * 12)
    img = mix(img, col((236, 242, 248)), ice)
    cl = fbm(14, octaves=7, base=5)
    swirl = fbm(15, octaves=3, base=3)
    clouds = smooth(0.58, 0.80, cl * 0.75 + swirl * 0.35)
    img = mix(img, col((248, 250, 252)), clouds * 0.8)
    return img, dict(atmo=(110, 170, 255), atmo_k=0.9, spec=0.35)


def tex_moon():
    n = fbm(21, octaves=7, base=5)
    maria = smooth(0.50, 0.66, fbm(22, octaves=6, base=4))
    img = mix(col((182, 180, 174)), col((104, 104, 108)), maria * 0.8)
    img = img * (0.82 + 0.3 * n[..., None])
    _craters(img, 23, 90, 3, 10)
    _craters(img, 24, 14, 10, 26, dark=0.86, rim=1.12)
    return np.clip(img, 0, 255), dict(atmo=None)


def tex_mercury():
    n = fbm(31, octaves=7, base=6)
    img = mix(col((150, 140, 132)), col((190, 180, 170)), n)
    _craters(img, 32, 140, 2, 9)
    _craters(img, 33, 12, 9, 22)
    return np.clip(img, 0, 255), dict(atmo=None)


def tex_venus():
    lat = lat_grid()
    n = fbm(41, octaves=6, base=4)
    t = np.sin(np.radians(lat) * 3 + n * 5)
    img = mix(col((214, 176, 112)), col((244, 222, 176)), (t + 1) / 2 * 0.6 + n * 0.4)
    return img, dict(atmo=(255, 226, 170), atmo_k=0.7)


def tex_mars():
    lat = lat_grid()
    n = fbm(51, octaves=7, base=4)
    img = mix(col((196, 102, 60)), col((222, 140, 88)), n)
    dark = smooth(0.46, 0.60, fbm(52, octaves=6, base=5)) * (1 - smooth(50, 65, np.abs(lat)))
    img = mix(img, col((120, 60, 38)), dark * 0.7)
    cap = smooth(72, 80, lat + (fbm(53, octaves=3) - 0.5) * 8)
    img = mix(img, col((244, 238, 232)), cap)
    return img, dict(atmo=(255, 170, 130), atmo_k=0.35)


def _banded(seed, lat, palette, turb=4.0, freq=1.0):
    n = fbm(seed, octaves=6, base=6)
    warp = (fbm(seed + 1, octaves=5, base=8) - 0.5) * turb
    x = (lat * freq + warp + n * 2) / 180 * (len(palette) - 1) * 3
    idx = np.abs(np.sin(x * math.pi / 3))
    k = len(palette) - 1
    f = idx * k
    i0 = np.clip(np.floor(f).astype(int), 0, k - 1)
    t = (f - i0)[..., None]
    pal = np.array(palette, np.float32)
    return pal[i0] * (1 - t) + pal[i0 + 1] * t


def tex_jupiter():
    lat = lat_grid()
    img = _banded(61, lat * 1.0, [(236, 222, 196), (200, 160, 118), (156, 108, 76), (226, 206, 176)], turb=7, freq=2.4)
    fine = fbm(63, octaves=7, base=16)
    img = img * (0.9 + 0.2 * fine[..., None])
    yy, xx = np.mgrid[0:TH, 0:TW]
    d = ((xx - TW * 0.62) / 46.0) ** 2 + ((yy - TH * 0.62) / 22.0) ** 2           # Grosser Roter Fleck
    img = mix(img, col((196, 96, 64)), smooth(1.4, 0.5, d))
    img = mix(img, col((236, 186, 150)), smooth(0.35, 0.0, d) * 0.6)
    return np.clip(img, 0, 255), dict(atmo=(255, 230, 190), atmo_k=0.4)


def tex_saturn():
    lat = lat_grid()
    img = _banded(71, lat, [(236, 220, 180), (214, 190, 142), (196, 168, 118), (228, 208, 164)], turb=3, freq=1.6)
    img = img * (0.94 + 0.1 * fbm(72, octaves=6, base=12)[..., None])
    img = mix(img, col((170, 170, 150)), smooth(70, 84, lat) * 0.6)                # Nordpol dunkler
    return np.clip(img, 0, 255), dict(atmo=(255, 236, 196), atmo_k=0.35)


def tex_neptune():
    lat = lat_grid()
    img = _banded(81, lat, [(58, 94, 206), (40, 70, 180), (70, 110, 220)], turb=2, freq=1.2)
    streak = smooth(0.72, 0.8, fbm(82, octaves=6, base=10)) * smooth(30, 20, np.abs(lat + 20))
    img = mix(img, col((226, 236, 255)), streak * 0.8)
    yy, xx = np.mgrid[0:TH, 0:TW]
    d = ((xx - TW * 0.55) / 40.0) ** 2 + ((yy - TH * 0.64) / 20.0) ** 2           # Dunkler Fleck
    img = mix(img, col((24, 40, 120)), smooth(1.2, 0.3, d))
    return img, dict(atmo=(120, 160, 255), atmo_k=0.8)


def tex_uranus():
    lat = lat_grid()
    img = mix(col((170, 222, 226)), col((140, 206, 214)), smooth(-10, 40, lat) * 0.6)
    img = img * (0.97 + 0.05 * fbm(91, octaves=4)[..., None])
    return img, dict(atmo=(170, 230, 240), atmo_k=0.8)


TEXTURES = {"earth": tex_earth, "moon": tex_moon, "mercury": tex_mercury, "venus": tex_venus,
            "mars": tex_mars, "jupiter": tex_jupiter, "saturn": tex_saturn, "neptune": tex_neptune,
            "uranus": tex_uranus}


def texture(kind):
    if kind not in _TEX:
        _TEX[kind] = TEXTURES[kind]()
    return _TEX[kind]


# ---------------------------------------------------------------- Projektion

def _disc(d):
    """Normalen einer Kugel mit Durchmesser d (px) + weicher Rand-Alpha."""
    r = d / 2
    ys, xs = np.mgrid[0:d, 0:d].astype(np.float32)
    nx, ny = (xs + 0.5 - r) / r, (ys + 0.5 - r) / r
    rr = np.sqrt(nx * nx + ny * ny)
    nz = np.sqrt(np.clip(1 - rr * rr, 0, 1))
    alpha = np.clip((1 - rr) * r / 1.2, 0, 1)
    return nx, ny, nz, alpha


def _sample(tex, nx, ny, nz, lon0, tilt):
    # Achsneigung um die Blickachse drehen, dann Laenge/Breite berechnen
    ct, st = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    x, y = nx * ct - ny * st, nx * st + ny * ct
    lat = np.degrees(np.arcsin(np.clip(-y, -1, 1)))
    lon = np.degrees(np.arctan2(x, nz)) + lon0
    u = ((lon % 360) / 360 * (TW - 1)).astype(int)
    v = ((90 - lat) / 180 * (TH - 1)).astype(int)
    return tex[np.clip(v, 0, TH - 1), np.clip(u, 0, TW - 1)]


def planet(img, cx, cy, d_px, kind, light=(-0.55, -0.45, 0.70), lon0=180.0, tilt=0.0,
           ring_tilt=None, glow=True):
    """Realistische Planetenkugel auf img (RGB, Supersampling-Leinwand). cx/cy in Leinwand-px,
    d_px in Ausgabe-px (wird mit S multipliziert). light: Richtung zur Sonne (x rechts, y unten,
    z zum Betrachter). ring_tilt: Neigung der Saturnringe in Grad (None = keine Ringe)."""
    tex, meta = texture(kind)
    d = max(4, int(d_px * S))
    nx, ny, nz, alpha = _disc(d)
    base = _sample(tex, nx, ny, nz, lon0, tilt)

    lx, ly, lz = light
    ln = math.sqrt(lx * lx + ly * ly + lz * lz)
    lx, ly, lz = lx / ln, ly / ln, lz / ln
    ndl = nx * lx + ny * ly + nz * lz
    lit = smooth(-0.08, 0.35, ndl) * (0.35 + 0.65 * np.clip(ndl, 0, 1)) + 0.025
    limb = 0.75 + 0.25 * nz                                                       # leichte Randabdunklung
    rgb = base * (lit * limb)[..., None]

    if meta.get("spec"):                                                          # Glanz auf Ozeanen
        hx, hy, hz = lx, ly, lz + 1
        hn = math.sqrt(hx * hx + hy * hy + hz * hz)
        spec = np.clip((nx * hx + ny * hy + nz * hz) / hn, 0, 1) ** 60
        ocean = (base[..., 2] > base[..., 0] + 30).astype(np.float32)
        rgb += (spec * ocean * meta["spec"] * 255)[..., None]

    if meta.get("atmo"):                                                          # Atmosphaerensaum
        rim = (1 - nz) ** 2.5 * smooth(-0.25, 0.3, ndl) * meta.get("atmo_k", 0.6)
        rgb = rgb * (1 - rim[..., None] * 0.6) + col(meta["atmo"]) * rim[..., None]

    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    sprite = Image.fromarray(rgb, "RGB")
    mask = Image.fromarray((alpha * 255).astype(np.uint8), "L")

    r = d // 2
    if glow and meta.get("atmo"):
        _halo(img, cx, cy, r, meta["atmo"], strength=int(55 * meta.get("atmo_k", 0.6)), scale=1.18)
    if ring_tilt is not None:
        _ring(img, cx, cy, r, ring_tilt, light, back=True)
    img.paste(sprite, (int(cx - r), int(cy - r)), mask)
    if ring_tilt is not None:
        _ring(img, cx, cy, r, ring_tilt, light, back=False)


def _halo(img, cx, cy, r, color, strength=70, scale=1.35):
    m = Image.new("L", img.size, 0)
    R = r * scale
    ImageDraw.Draw(m).ellipse([cx - R, cy - R, cx + R, cy + R], fill=strength)
    m = m.filter(ImageFilter.GaussianBlur(r * 0.25))
    img.paste(Image.new("RGB", img.size, tuple(color)), (0, 0), m)


def _ring(img, cx, cy, r, tilt, light, back):
    """Saturnringe: radiales Helligkeitsprofil (C-, B-Ring, Cassini-Teilung, A-Ring, Encke-Luecke),
    als Ellipse mit Neigung; hintere Haelfte vor, vordere nach der Kugel."""
    k = max(0.02, math.sin(math.radians(tilt)))
    R_out = r * 2.27
    w = int(R_out * 2) + 4
    h = int(R_out * 2 * k) + 4
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    ex = (xs - w / 2) / R_out
    ey = (ys - h / 2) / (R_out * k)
    rad = np.sqrt(ex * ex + ey * ey) * 2.27                                       # in Planetenradien
    prof = np.zeros_like(rad)
    prof += smooth(1.24, 1.30, rad) * (1 - smooth(1.50, 1.53, rad)) * 0.28        # C-Ring (schwach)
    prof += smooth(1.52, 1.56, rad) * (1 - smooth(1.93, 1.95, rad)) * 1.0         # B-Ring (hell)
    prof += smooth(2.02, 2.04, rad) * (1 - smooth(2.25, 2.27, rad)) * 0.72        # A-Ring
    prof *= 1 - (smooth(2.20, 2.205, rad) * (1 - smooth(2.215, 2.22, rad))) * 0.8  # Encke-Luecke
    prof *= 0.9 + 0.1 * np.sin(rad * 140)                                          # feine Ringstruktur
    colr = np.stack([prof * 232, prof * 214, prof * 172], -1)
    # Schatten des Planeten auf den Ringen (hinter dem Planeten, abgewandt von der Sonne)
    lx = light[0]
    shadow = (np.abs(ey * R_out * k) < r * 0.9) & (np.sign(ex) == -np.sign(lx if lx else 1)) & (ey < 0)
    colr[shadow] *= 0.25
    alpha = np.clip(prof * 1.25, 0, 1)
    half = (ys < h / 2) if back else (ys >= h / 2)
    alpha = alpha * half
    spr = Image.fromarray(np.clip(colr, 0, 255).astype(np.uint8), "RGB")
    m = Image.fromarray((alpha * 255).astype(np.uint8), "L")
    img.paste(spr, (int(cx - w / 2), int(cy - h / 2)), m)


# ---------------------------------------------------------------- Sterne

STARS = {"sun": dict(core=(255, 250, 232), mid=(255, 214, 128), edge=(236, 120, 40), glow=(255, 170, 70)),
         "red_dwarf": dict(core=(255, 196, 150), mid=(244, 118, 70), edge=(170, 42, 22), glow=(255, 96, 56))}


def star(img, cx, cy, d_px, kind="sun", corona=1.0, spots=True):
    """Selbstleuchtende Sternkugel: Randverdunkelung (Farbe zum Rand hin roeter), Granulation,
    optionale Flecken, Korona/Glow. Keine Schattenseite."""
    p = STARS[kind]
    d = max(4, int(d_px * S))
    nx, ny, nz, alpha = _disc(d)
    mu = nz
    tex = np.asarray(Image.fromarray((fbm(7 if kind == "sun" else 8, octaves=5, base=64) * 255).astype(np.uint8))
                     .resize((d, d), Image.BICUBIC), np.float32) / 255
    gran = 0.93 + 0.12 * tex
    c = mix(col(p["edge"]), col(p["mid"]), smooth(0.0, 0.55, mu))
    c = mix(c, col(p["core"]), smooth(0.6, 1.0, mu) * 0.55)
    inten = (0.55 + 0.45 * mu ** 0.7) * gran
    rgb = c * inten[..., None]
    if spots:
        rng = np.random.default_rng(3 if kind == "sun" else 4)
        for _ in range(2 if kind == "sun" else 1):
            sx, sy, sr = rng.uniform(-0.4, 0.4), rng.uniform(-0.3, 0.3), rng.uniform(0.025, 0.045)
            dd = np.sqrt((nx - sx) ** 2 + ((ny - sy) * 1.3) ** 2)
            rgb *= (1 - smooth(sr * 2.2, sr * 1.0, dd) * 0.3 - smooth(sr * 0.9, sr * 0.3, dd) * 0.45)[..., None]
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    r = d // 2
    if corona:
        _halo(img, cx, cy, r, p["glow"], strength=int(70 * corona), scale=1.6)
        _halo(img, cx, cy, r, p["mid"], strength=int(110 * corona), scale=1.12)
    img.paste(Image.fromarray(rgb, "RGB"), (int(cx - r), int(cy - r)),
              Image.fromarray((alpha * 255).astype(np.uint8), "L"))
