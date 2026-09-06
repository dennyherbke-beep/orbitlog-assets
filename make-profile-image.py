"""Erzeugt das Profilbild (Ringplanet, Markenfarben) als PNG - gerendert mit Beleuchtung,
Ringperspektive, Bandstruktur, Planetenschatten auf dem Ring, Sternfeld, Bloom und Korn.

    python make-profile-image.py

Benoetigt: numpy, Pillow.
Ausgabe: profile-theorbitlog.png (1080) + -320.png im selben Ordner.
Design-System / Farben: docs/strategie.md.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

OUT = Path(__file__).resolve().parent

# --- Parameter -----------------------------------------------------------------
SS = 2160                       # Renderaufloesung (-> 1080)
RP = 0.198 * SS                 # Planetenradius in px
TILT = np.radians(20.0)         # Ringneigung (aus der Bildebene heraus)
ROLL = np.radians(30.0)         # Drehung in der Bildebene: >0 = links unten -> rechts oben
RING_IN = 1.18 * RP
RING_OUT = 1.82 * RP
LIGHT = np.array([-0.55, 0.60, 0.58], np.float32)   # x rechts, y oben, z zum Betrachter
LIGHT /= np.linalg.norm(LIGHT)

BG_IN = np.array([0.090, 0.115, 0.155], np.float32)
BG_OUT = np.array([0.024, 0.032, 0.047], np.float32)
ALBEDO = np.array([0.930, 0.936, 0.948], np.float32)
RING_LIT = np.array([1.00, 0.80, 0.52], np.float32)
RING_DARK = np.array([0.50, 0.30, 0.13], np.float32)
AMBER = np.array([1.00, 0.706, 0.329], np.float32)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def blur_rgb(arr, radius):
    im = Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(radius)), np.float32) / 255.0


def build():
    n = SS
    cx = cy = n / 2.0
    Y, X = np.mgrid[0:n, 0:n].astype(np.float32)
    u = X - cx
    v = Y - cy
    dist = np.hypot(u, v)

    # --- Hintergrund ---------------------------------------------------------
    rad = np.clip(dist / (n * 0.72), 0.0, 1.0)
    t = smoothstep(0.0, 1.0, rad)[..., None]
    img = BG_IN * (1 - t) + BG_OUT * t
    img *= (1.0 - 0.30 * smoothstep(0.45, 1.15, rad))[..., None]
    g1 = np.exp(-(((u + 0.34 * n) ** 2 + (v - 0.30 * n) ** 2) / (2 * (0.30 * n) ** 2)))
    g2 = np.exp(-(((u - 0.32 * n) ** 2 + (v + 0.30 * n) ** 2) / (2 * (0.40 * n) ** 2)))
    img += AMBER * (0.050 * g1)[..., None]
    img += np.array([0.35, 0.5, 0.9], np.float32) * (0.026 * g2)[..., None]

    # --- Sternfeld ---------------------------------------------------------------
    rng = np.random.default_rng(7)
    stars = np.zeros((n, n), np.float32)
    m = 520
    sx = rng.integers(0, n, m)
    sy = rng.integers(0, n, m)
    mag = rng.random(m) ** 2.6
    keep = np.hypot(sx - cx, sy - cy) > RP * 1.04
    stars[sy[keep], sx[keep]] = mag[keep]
    bi = rng.integers(0, m, 10)
    for k in bi:
        yy, xx = sy[k] % n, sx[k] % n
        if np.hypot(xx - cx, yy - cy) > RP * 1.15:
            stars[yy, xx] = 1.0
            stars[max(0, yy - 2):yy + 3, xx] = np.maximum(stars[max(0, yy - 2):yy + 3, xx], 0.5)
            stars[yy, max(0, xx - 2):xx + 3] = np.maximum(stars[yy, max(0, xx - 2):xx + 3], 0.5)
    s_rgb = np.stack([stars] * 3, -1) * np.array([0.92, 0.94, 1.0], np.float32)
    s_rgb = blur_rgb(s_rgb, 0.6) + blur_rgb(s_rgb, 2.4) * 0.45
    img = 1.0 - (1.0 - img) * (1.0 - np.clip(s_rgb, 0, 1))

    # --- Ring (analytisch, perspektivisch) ---------------------------------------
    sin_t = np.sin(TILT)
    ca, sa = np.cos(ROLL), np.sin(ROLL)
    ur = u * ca - v * sa                 # in die um ROLL gedrehte Ringebene
    vr = u * sa + v * ca
    lx = LIGHT[0] * ca - LIGHT[1] * sa   # Licht mitdrehen
    ly = LIGHT[0] * sa + LIGHT[1] * ca

    r_eq = np.sqrt(ur ** 2 + (vr / sin_t) ** 2)
    cth = np.divide(ur, r_eq, out=np.zeros_like(u), where=r_eq > 1e-6)
    sth = np.divide(-vr / sin_t, r_eq, out=np.zeros_like(u), where=r_eq > 1e-6)
    e2 = ly * sin_t + LIGHT[2] * np.cos(TILT)
    ill = cth * lx + sth * e2
    ill_n = np.clip(0.50 + 0.60 * ill, 0.10, 1.25)

    s = np.clip((r_eq - RING_IN) / (RING_OUT - RING_IN), 0.0, 1.0)
    prof = 0.60 + 0.40 * np.sin(s * 10.0 + 0.3)
    prof *= 1.0 - 0.80 * np.exp(-((s - 0.42) ** 2) / (2 * 0.026 ** 2))    # Cassini
    prof *= 1.0 - 0.40 * np.exp(-((s - 0.72) ** 2) / (2 * 0.028 ** 2))
    prof *= 1.0 - 0.25 * np.exp(-((s - 0.90) ** 2) / (2 * 0.030 ** 2))
    edge = smoothstep(0.0, 0.03, s) * (1.0 - smoothstep(0.965, 1.0, s))
    aa = 1.6
    band = np.clip(prof, 0, 1) * edge
    band *= smoothstep(RING_IN - aa, RING_IN + aa, r_eq)
    band *= 1.0 - smoothstep(RING_OUT - aa, RING_OUT + aa, r_eq)

    # Planetenschatten auf den Ring
    Pz = r_eq * sth * np.cos(TILT)
    P = np.stack([ur, -vr, Pz], -1) / RP
    Lr = np.array([lx, ly, LIGHT[2]], np.float32)
    cr = np.stack([
        P[..., 1] * Lr[2] - P[..., 2] * Lr[1],
        P[..., 2] * Lr[0] - P[..., 0] * Lr[2],
        P[..., 0] * Lr[1] - P[..., 1] * Lr[0],
    ], -1)
    perp = np.linalg.norm(cr, axis=-1)
    shadow = smoothstep(1.06, 0.72, perp) * ((P * Lr).sum(-1) < 0.0)

    ring_a = np.clip(band * (0.42 + 0.72 * ill_n), 0.0, 1.0) * (1.0 - 0.80 * shadow)
    ring_col = RING_DARK + (RING_LIT - RING_DARK) * np.clip(ill_n, 0, 1)[..., None]
    front = smoothstep(-11.0, 11.0, vr)

    def over(base, col, a):
        a = a[..., None]
        return base * (1 - a) + col * a

    # Ring-Glimmen + Ring hinter dem Planeten
    ring_glow = blur_rgb(ring_col * ring_a[..., None], 9) * 0.30
    img = 1.0 - (1.0 - img) * (1.0 - np.clip(ring_glow, 0, 1))
    img = over(img, ring_col, ring_a * (1 - front))

    # --- Planet ------------------------------------------------------------------
    xn, yn = u / RP, -v / RP
    r2 = xn ** 2 + yn ** 2
    inside = r2 <= 1.0
    zn = np.sqrt(np.clip(1.0 - r2, 0.0, 1.0))
    N = np.stack([xn, yn, zn], -1)
    lam = np.clip((N * LIGHT).sum(-1), 0.0, 1.0)
    hlf = LIGHT + np.array([0, 0, 1], np.float32)
    hlf /= np.linalg.norm(hlf)
    spec = np.clip((N * hlf).sum(-1), 0.0, 1.0) ** 12 * 0.10   # breit, kein Glanzpunkt

    inten = 0.20 + 0.86 * lam ** 1.12 + 0.10 * smoothstep(0.75, 1.0, lam)

    lat = np.clip(yn, -1, 1)
    belt = (0.5 + 0.32 * np.sin(6.2 * lat + 0.5) + 0.14 * np.sin(13.0 * lat + 1.0))
    belt -= 0.42 * np.exp(-((lat - 0.16) / 0.055) ** 2)
    belt -= 0.34 * np.exp(-((lat + 0.30) / 0.05) ** 2)
    inten *= 1.0 + 0.085 * (belt - 0.5) * 2.0 * np.sqrt(zn)

    pcol = ALBEDO * inten[..., None] + spec[..., None]
    warm = np.array([1.03, 0.99, 0.94], np.float32)
    lit = smoothstep(0.2, 0.9, lam)[..., None]
    pcol = pcol * (1 - 0.10 * lit) + (pcol * warm) * (0.10 * lit)

    fres = 1.0 - zn
    rim = smoothstep(0.42, 1.0, fres) * np.clip(1.0 - lam * 1.35, 0.0, 1.0)
    pcol = pcol + AMBER * (0.62 * rim)[..., None]
    dark = smoothstep(0.5, 0.0, lam) * smoothstep(0.35, 1.0, fres)
    pcol = pcol * (1.0 - 0.30 * dark[..., None])

    pcol = np.clip(pcol, 0.0, 1.0)
    a_planet = np.clip((RP - dist) / 1.7 + 0.5, 0.0, 1.0) * inside
    img = over(img, pcol, a_planet)

    # Schatten des vorderen Rings auf den Planeten
    fr_sh = np.zeros_like(u)
    off = int(0.02 * RP)
    fr_sh[off:, :] = (ring_a * front)[:-off, :]
    img = over(img, img * 0.82, np.clip(fr_sh, 0, 1) * a_planet * 0.7)

    # Ring vor dem Planeten
    ring_a_front = np.clip(band * (0.55 + 0.6 * ill_n), 0.0, 1.0) * (1.0 - 0.5 * shadow)
    img = over(img, ring_col, ring_a_front * front)

    # --- Bloom + Korn ----------------------------------------------------------
    lumin = img @ np.array([0.2126, 0.7152, 0.0722], np.float32)
    brt = np.clip(lumin - 0.66, 0, 1)[..., None] * img
    img = 1.0 - (1.0 - img) * (1.0 - blur_rgb(brt, 16) * 0.45)
    img += rng.standard_normal((n, n, 1)).astype(np.float32) * 0.005

    img = np.clip(img, 0.0, 1.0)
    full = Image.fromarray((img * 255).astype(np.uint8), "RGB")
    return full.resize((1080, 1080), Image.LANCZOS)


if __name__ == "__main__":
    im = build()
    im.save(OUT / "profile-theorbitlog.png")
    im.resize((320, 320), Image.LANCZOS).save(OUT / "profile-theorbitlog-320.png")
    print("saved:", OUT / "profile-theorbitlog.png")
