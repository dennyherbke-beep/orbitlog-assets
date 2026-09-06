"""Erzeugt das kleine Marken-Icon (Ringplanet) fuer CTA-/Cover-Slides - gleiche Geometrie,
Neigung und Farben wie das Profilbild (make-profile-image.py), aber freigestellt (RGBA,
transparenter Hintergrund) fuer den Einsatz als Icon in Post-Slides.

    python make-brand-mark.py
Ausgabe: brand-mark.png (600x600, transparent). Geladen von brandkit.ring_mark().
Benoetigt: numpy, Pillow.
"""

from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parent
SS = 1200
RP = 0.23 * SS
TILT = np.radians(20.0)
ROLL = np.radians(30.0)
RING_IN = 1.18 * RP
RING_OUT = 1.82 * RP
LIGHT = np.array([-0.55, 0.60, 0.58], np.float32)
LIGHT /= np.linalg.norm(LIGHT)

ALBEDO = np.array([0.930, 0.936, 0.948], np.float32)
RING_LIT = np.array([1.00, 0.80, 0.52], np.float32)
RING_DARK = np.array([0.50, 0.30, 0.13], np.float32)
AMBER = np.array([1.00, 0.706, 0.329], np.float32)


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def over(img, alpha, col, a):
    a = np.clip(a, 0.0, 1.0)
    new_alpha = a + alpha * (1 - a)
    new_img = col * a[..., None] + img * (alpha * (1 - a))[..., None]
    return new_img / np.maximum(new_alpha, 1e-6)[..., None], new_alpha


def build():
    n = SS
    cx = cy = n / 2.0
    Y, X = np.mgrid[0:n, 0:n].astype(np.float32)
    u = X - cx
    v = Y - cy
    dist = np.hypot(u, v)

    sin_t = np.sin(TILT)
    ca, sa = np.cos(ROLL), np.sin(ROLL)
    ur = u * ca - v * sa
    vr = u * sa + v * ca
    lx = LIGHT[0] * ca - LIGHT[1] * sa
    ly = LIGHT[0] * sa + LIGHT[1] * ca

    r_eq = np.sqrt(ur ** 2 + (vr / sin_t) ** 2)
    cth = np.divide(ur, r_eq, out=np.zeros_like(u), where=r_eq > 1e-6)
    sth = np.divide(-vr / sin_t, r_eq, out=np.zeros_like(u), where=r_eq > 1e-6)
    e2 = ly * sin_t + LIGHT[2] * np.cos(TILT)
    ill = cth * lx + sth * e2
    ill_n = np.clip(0.50 + 0.60 * ill, 0.10, 1.25)

    s = np.clip((r_eq - RING_IN) / (RING_OUT - RING_IN), 0.0, 1.0)
    prof = 0.60 + 0.40 * np.sin(s * 10.0 + 0.3)
    prof *= 1.0 - 0.80 * np.exp(-((s - 0.42) ** 2) / (2 * 0.026 ** 2))
    prof *= 1.0 - 0.40 * np.exp(-((s - 0.72) ** 2) / (2 * 0.028 ** 2))
    prof *= 1.0 - 0.25 * np.exp(-((s - 0.90) ** 2) / (2 * 0.030 ** 2))
    edge = smoothstep(0.0, 0.03, s) * (1.0 - smoothstep(0.965, 1.0, s))
    aa = 1.6
    band = np.clip(prof, 0, 1) * edge
    band *= smoothstep(RING_IN - aa, RING_IN + aa, r_eq)
    band *= 1.0 - smoothstep(RING_OUT - aa, RING_OUT + aa, r_eq)

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

    xn, yn = u / RP, -v / RP
    r2 = xn ** 2 + yn ** 2
    inside = r2 <= 1.0
    zn = np.sqrt(np.clip(1.0 - r2, 0.0, 1.0))
    N = np.stack([xn, yn, zn], -1)
    lam = np.clip((N * LIGHT).sum(-1), 0.0, 1.0)
    hlf = LIGHT + np.array([0, 0, 1], np.float32)
    hlf /= np.linalg.norm(hlf)
    spec = np.clip((N * hlf).sum(-1), 0.0, 1.0) ** 12 * 0.10
    inten = 0.20 + 0.86 * lam ** 1.12 + 0.10 * smoothstep(0.75, 1.0, lam)
    lat = np.clip(yn, -1, 1)
    belt = 0.5 + 0.32 * np.sin(6.2 * lat + 0.5) + 0.14 * np.sin(13.0 * lat + 1.0)
    belt -= 0.42 * np.exp(-((lat - 0.16) / 0.055) ** 2)
    belt -= 0.34 * np.exp(-((lat + 0.30) / 0.05) ** 2)
    inten *= 1.0 + 0.085 * (belt - 0.5) * 2.0 * np.sqrt(zn)
    pcol = ALBEDO * inten[..., None] + spec[..., None]
    fres = 1.0 - zn
    rim = smoothstep(0.42, 1.0, fres) * np.clip(1.0 - lam * 1.35, 0.0, 1.0)
    pcol = pcol + AMBER * (0.62 * rim)[..., None]
    dark = smoothstep(0.5, 0.0, lam) * smoothstep(0.35, 1.0, fres)
    pcol = pcol * (1.0 - 0.30 * dark[..., None])
    pcol = np.clip(pcol, 0.0, 1.0)
    a_planet = np.clip((RP - dist) / 1.7 + 0.5, 0.0, 1.0) * inside

    img = np.zeros((n, n, 3), np.float32)
    alpha = np.zeros((n, n), np.float32)
    img, alpha = over(img, alpha, ring_col, ring_a * (1 - front))

    fr_sh = np.zeros_like(u)
    off = int(0.02 * RP)
    fr_sh[off:, :] = (ring_a * front)[:-off, :]
    pcol_shadowed = pcol * (1.0 - 0.126 * np.clip(fr_sh, 0, 1))[..., None]
    img, alpha = over(img, alpha, pcol_shadowed, a_planet)

    ring_a_front = np.clip(band * (0.55 + 0.6 * ill_n), 0.0, 1.0) * (1.0 - 0.5 * shadow)
    img, alpha = over(img, alpha, ring_col, ring_a_front * front)

    rgba = np.concatenate([np.clip(img, 0, 1), alpha[..., None]], axis=-1)
    out = Image.fromarray((rgba * 255).astype(np.uint8), "RGBA")
    return out.resize((600, 600), Image.LANCZOS)


if __name__ == "__main__":
    im = build()
    im.save(OUT / "brand-mark.png")
    print("saved:", OUT / "brand-mark.png")
