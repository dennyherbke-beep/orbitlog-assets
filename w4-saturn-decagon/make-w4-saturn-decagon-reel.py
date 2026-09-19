"""Woche 4, Montag - Signature-Reel "Saturn just grew a 10-sided shape". 8 Frames, 1080x1920.
Anlass: NASA/ESA-Hubble-Meldung vom 02.09.2026 (Science Advances, 03.09.2026, A. Sanchez-Lavega
et al.): Um Saturns Suedpol hat sich eine 10-seitige (dekagonale) Atmosphaerenwelle gebildet -
seit 2023 zunehmend deutlich, 2024 in erdgebundenen Aufnahmen bemerkt, 2025 klar sichtbar
(Hubble, 29.08.2025). Das Sechseck am Nordpol besteht dagegen seit ueber 40 Jahren.
Eigene Vektorgrafik (Polaransicht), kein Hubble-Foto -> keine Lizenzfrage.

    python make-w4-saturn-decagon-reel.py  ->  w4-saturn-decagon-01..08.png, -cover.png, .mp4
"""

import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono, wrap
from reelkit import (W, H, M, TOP_SAFE, new_frame, header, footer_handle, ruler, ctext,
                     ctext_block, frame_cta, sphere, tex_saturn, grain, finish)

OUT = Path(__file__).resolve().parent
GOLD_A = np.array([232, 208, 158], float)
GOLD_B = np.array([196, 160, 104], float)
CREAM = (255, 240, 208)


def polar_disc(img, cx, cy, r):
    """Saturn von oben auf einen Pol gesehen: konzentrische Baender, Randabdunklung, Wirbel."""
    D = 2 * r
    yy, xx = np.mgrid[0:D, 0:D]
    x, y = (xx - r + 0.5) / r, (yy - r + 0.5) / r
    rad = np.sqrt(x * x + y * y)
    t = 0.5 + 0.5 * np.sin(rad * 34 + 1.2 * np.sin(rad * 9) + 0.6 * np.sin(np.arctan2(y, x) * 3))
    col = GOLD_A[None, None, :] * (1 - t[..., None]) + GOLD_B[None, None, :] * t[..., None]
    limb = 0.30 + 0.70 * np.sqrt(np.clip(1 - rad ** 2, 0, 1))
    light = 0.86 + 0.14 * np.clip(-(x + y) / 1.4, -1, 1)
    col = np.clip(col * (limb * light)[..., None], 0, 255).astype(np.uint8)
    disc = grain(Image.fromarray(col, "RGB"), 12, 3)
    mask = Image.new("L", (D, D), 0)
    ImageDraw.Draw(mask).ellipse([2, 2, D - 3, D - 3], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.6))
    halo = Image.new("L", img.size, 0)
    ImageDraw.Draw(halo).ellipse([cx - r * 1.12, cy - r * 1.12, cx + r * 1.12, cy + r * 1.12], fill=90)
    halo = halo.filter(ImageFilter.GaussianBlur(r * 0.14))
    img.paste(Image.new("RGB", img.size, (170, 120, 60)), (0, 0), halo)
    img.paste(disc, (cx - r, cy - r), mask)
    ImageDraw.Draw(img).ellipse([cx - r * 0.07, cy - r * 0.07, cx + r * 0.07, cy + r * 0.07],
                                fill=(96, 70, 42))


def ring_points(cx, cy, rad, sides, rot=-90, wave=0.0):
    pts = []
    n = 720 if wave else sides
    for k in range(n):
        a = math.radians(rot + 360 * k / n)
        rr = rad * (1 + wave * math.cos(sides * math.radians(360 * k / n)))
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def jet(img, pts, width, color=CREAM, glow_col=ACC, alpha=255):
    """Leuchtende geschlossene Linie (Jetstream)."""
    g = Image.new("L", img.size, 0)
    ImageDraw.Draw(g).line(pts + [pts[0]], fill=200, width=int(width * 3.2), joint="curve")
    g = g.filter(ImageFilter.GaussianBlur(width * 1.6))
    img.paste(Image.new("RGB", img.size, glow_col), (0, 0), g)
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).line(pts + [pts[0]], fill=alpha, width=int(width), joint="curve")
    img.paste(Image.new("RGB", img.size, color), (0, 0), m)


def disc_frame(seed, label, sides, big, sub_hl, sub, idx, wave=0.0):
    img, d = new_frame(seed)
    header(d, label)
    r = 330 * S
    cx, cy = W // 2, TOP_SAFE + 70 * S + r
    polar_disc(img, cx, cy, r)
    jet(img, ring_points(cx, cy, r * 0.62, sides, wave=wave), 9 * S)
    d = ImageDraw.Draw(img)
    y = cy + r + 90 * S
    ctext(d, big, f(84 * S, bold=True), FG, y)
    y += 112 * S
    ctext(d, sub_hl, f(46 * S, bold=True), ACC, y)
    y += 74 * S
    ctext_block(d, sub, f(30 * S), SEC, y, 42 * S, W - 2 * M - 40 * S)
    ruler(d, idx)
    footer_handle(d)
    return img


def frame_title():
    img, d = new_frame(1)
    header(d, "SATURN · NEW DISCOVERY")
    sphere(img, W // 2, TOP_SAFE + 300 * S, 300, tex_saturn(), (218, 196, 150), ring=True)
    d = ImageDraw.Draw(img)
    y = TOP_SAFE + 660 * S
    for ln in ["Saturn just grew", "a 10-sided shape"]:
        ctext(d, ln, f(80 * S, bold=True), FG, y)
        y += 96 * S
    ctext(d, "at its south pole - NASA Hubble, Sept 2026", f(32 * S), SEC, y + 24 * S)
    footer_handle(d)
    return img


def frame_compare():
    img, d = new_frame(4)
    header(d, "TWO POLES · TWO SHAPES")
    r = 215 * S
    cy = TOP_SAFE + 330 * S
    for cx, sides, name, note in [(W // 4 + 10 * S, 6, "NORTH", "6 sides\nover 40 years"),
                                  (3 * W // 4 - 10 * S, 10, "SOUTH", "10 sides\nnew")]:
        polar_disc(img, cx, cy, r)
        jet(img, ring_points(cx, cy, r * 0.62, sides), 7 * S)
        d = ImageDraw.Draw(img)
        ctext(d, name, fmono(28 * S), ACC, cy + r + 50 * S, cx=cx)
        yy = cy + r + 100 * S
        for k, ln in enumerate(note.split("\n")):
            ctext(d, ln, f(40 * S, bold=(k == 0)), FG if k == 0 else SEC, yy, cx=cx)
            yy += 54 * S
    d = ImageDraw.Draw(img)
    ctext_block(d, "The same planet, two very different polar patterns.", f(34 * S), SEC,
                cy + r + 330 * S, 46 * S, W - 2 * M - 120 * S)
    ruler(d, 3)
    footer_handle(d)
    return img


def frame_timeline():
    img, d = new_frame(5)
    header(d, "HOW IT WAS FOUND")
    rows = [("2023", "First faint hints in Hubble images"),
            ("2024", "Noticed in ground-based images"),
            ("2025", "Clearly visible - Hubble, Aug 29"),
            ("SEPT 2026", "Published in Science Advances")]
    x_dot = M + 24 * S
    y0 = TOP_SAFE + 210 * S
    step = 250 * S
    d.line([x_dot, y0, x_dot, y0 + step * (len(rows) - 1)], fill=HAIR, width=4 * S)
    for i, (yr, txt) in enumerate(rows):
        y = y0 + i * step
        last = i == len(rows) - 1
        rr = 18 * S if last else 13 * S
        d.ellipse([x_dot - rr, y - rr, x_dot + rr, y + rr], fill=ACC if last else SEC)
        d.text((x_dot + 60 * S, y - 46 * S), yr, font=f(54 * S, bold=True), fill=ACC if last else FG)
        for k, ln in enumerate(wrap(d, txt, f(32 * S), W - 2 * M - 120 * S)):
            d.text((x_dot + 60 * S, y + 26 * S + k * 42 * S), ln, font=f(32 * S), fill=SEC)
    ruler(d, 4)
    footer_handle(d)
    return img


def frame_wave():
    img, d = new_frame(6)
    header(d, "WHAT IT IS")
    r = 330 * S
    cx, cy = W // 2, TOP_SAFE + 70 * S + r
    polar_disc(img, cx, cy, r)
    jet(img, ring_points(cx, cy, r * 0.62, 10, wave=0.05), 9 * S)
    d = ImageDraw.Draw(img)
    y = cy + r + 90 * S
    ctext(d, "Not a solid shape -", f(64 * S, bold=True), FG, y)
    ctext(d, "a giant wave", f(64 * S, bold=True), ACC, y + 78 * S)
    ctext_block(d, "It reaches through several layers of Saturn's atmosphere. "
                   "Simulations suggest a wave trapped by a curving jet stream.",
                f(30 * S), SEC, y + 190 * S, 42 * S, W - 2 * M - 40 * S)
    ruler(d, 5)
    footer_handle(d)
    return img


def frame_growing():
    img, d = new_frame(7)
    header(d, "STILL CHANGING")
    r = 330 * S
    cx, cy = W // 2, TOP_SAFE + 70 * S + r
    polar_disc(img, cx, cy, r)
    for rad, w, a in [(0.36, 3, 90), (0.49, 5, 150), (0.62, 9, 255)]:
        jet(img, ring_points(cx, cy, r * rad, 10), w * S, alpha=a)
    d = ImageDraw.Draw(img)
    y = cy + r + 90 * S
    ctext(d, "It's still", f(72 * S, bold=True), FG, y)
    ctext(d, "getting stronger", f(72 * S, bold=True), ACC, y + 86 * S)
    ctext_block(d, "The decagon appears to be strengthening - scientists may be watching a "
                   "new atmospheric feature form in real time.",
                f(30 * S), SEC, y + 210 * S, 42 * S, W - 2 * M - 40 * S)
    ruler(d, 6)
    footer_handle(d)
    return img


def main():
    frames = [
        frame_title(),
        disc_frame(2, "SATURN · NORTH POLE", 6, "The Hexagon", "6 sides · 40+ years",
                   "A six-sided jet-stream pattern that has held its shape for decades.", 1),
        disc_frame(3, "SATURN · SOUTH POLE", 10, "The Decagon", "10 sides · brand new",
                   "The first large, regular-sided pattern seen in Saturn's southern hemisphere.", 2),
        frame_compare(),
        frame_timeline(),
        frame_wave(),
        frame_growing(),
        frame_cta(("Follow for one", "every day")),
    ]
    finish(frames, OUT, "w4-saturn-decagon", cover_idx=2)


if __name__ == "__main__":
    main()
