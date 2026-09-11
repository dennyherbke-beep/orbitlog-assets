"""Woche 3, Dienstag - Explained image: "Every Dot Here Is a Galaxy" (Hubble Deep Field).
Einzelbild 1080x1350 im Explained-Image-Layout (wie w2-andromeda), aber mit einer eigenen,
dichten Sternfeld/Fernfeld-Illustration statt eines echten Hubble-Fotos (kein Lizenzrisiko,
gleiche Entscheidung wie bei w2-andromeda / w1-planet-sizes-reel).

    python make-w3-deep-field.py   ->  w3-deep-field.png
"""

import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, BG, FG, SEC, ACC, HANDLE, f, fmono, tracked, wrap, downscale

OUT = Path(__file__).resolve().parent
W, H = 1080 * S, 1350 * S
M = 96 * S

KICKER = "EXPLAINED"
HEADLINE = "Every Dot Here Is a Galaxy"
SUBLINE = ("In 1995, Hubble stared at one 'empty' patch of sky for 10 days and found "
           "about 3,000 galaxies packed into an area the size of a grain of sand held at arm's length.")
CREDIT = "Illustration, not a telescope photo"


def _mask_ellipse(size, box, alpha, blur=None):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).ellipse(box, fill=alpha)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    return m


def tiny_galaxy(rgb, alpha, cx, cy, r, color, kind, rnd):
    """Malt eine winzige Galaxie (Ellipse oder schwacher Spiral-Fleck) direkt ins Bild."""
    if kind == "spiral":
        core = _mask_ellipse(rgb.size[0], [cx - r * 0.35, cy - r * 0.35, cx + r * 0.35, cy + r * 0.35],
                             220, blur=r * 0.25)
        disk = _mask_ellipse(rgb.size[0], [cx - r, cy - r * 0.42, cx + r, cy + r * 0.42],
                             150, blur=r * 0.35)
        rgb.paste(Image.new("RGB", rgb.size, tuple(min(255, c + 30) for c in color)), (0, 0), core)
        rgb.paste(Image.new("RGB", rgb.size, color), (0, 0), disk)
        alpha.paste(Image.new("L", rgb.size, 255), (0, 0), ImageChops.lighter(core, disk))
    else:
        m = _mask_ellipse(rgb.size[0], [cx - r, cy - r * 0.72, cx + r, cy + r * 0.72],
                          200, blur=r * 0.4)
        rgb.paste(Image.new("RGB", rgb.size, color), (0, 0), m)
        alpha.paste(Image.new("L", rgb.size, 255), (0, 0), m)


PALETTE = [(232, 214, 176), (196, 210, 232), (226, 186, 168), (208, 220, 198),
           (240, 232, 210), (188, 198, 224), (216, 176, 176)]


def deep_field(w, h, seed=21, n=520):
    """Dichtes Feld winziger Hintergrundgalaxien plus ein paar helle Vordergrund-Sterne
    mit Beugungsspitzen (Hubble-typischer Look), rein illustrativ."""
    rgb = Image.new("RGB", (w, h), (0, 0, 0))
    alpha = Image.new("L", (w, h), 0)
    rnd = random.Random(seed)

    for _ in range(n):
        cx, cy = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(2.0, 7.5) * S
        color = rnd.choice(PALETTE)
        kind = "spiral" if rnd.random() < 0.30 else "blob"
        ang = rnd.uniform(0, 360)
        sprite_sz = int(r * 6)
        spr_rgb = Image.new("RGB", (sprite_sz, sprite_sz), (0, 0, 0))
        spr_a = Image.new("L", (sprite_sz, sprite_sz), 0)
        tiny_galaxy(spr_rgb, spr_a, sprite_sz / 2, sprite_sz / 2, r, color, kind, rnd)
        spr_rgb = spr_rgb.rotate(ang, resample=Image.BICUBIC)
        spr_a = spr_a.rotate(ang, resample=Image.BICUBIC)
        px, py = int(cx - sprite_sz / 2), int(cy - sprite_sz / 2)
        rgb.paste(spr_rgb, (px, py), spr_a)
        alpha.paste(Image.new("L", spr_a.size, 255), (px, py), spr_a)

    # ein paar helle Vordergrundsterne (Beugungsspitzen) - unsere eigene Galaxie im Vordergrund
    d = ImageDraw.Draw(rgb)
    da = ImageDraw.Draw(alpha)
    for _ in range(14):
        cx, cy = rnd.uniform(0, w), rnd.uniform(0, h)
        r = rnd.uniform(2.5, 5) * S
        glow = Image.new("L", (w, h), 0)
        ImageDraw.Draw(glow).ellipse([cx - r * 4, cy - r * 4, cx + r * 4, cy + r * 4], fill=100)
        glow = glow.filter(ImageFilter.GaussianBlur(r * 1.6))
        rgb.paste(Image.new("RGB", (w, h), FG), (0, 0), glow)
        alpha.paste(glow, (0, 0), glow)
        spike = int(r * 7)
        d.line([cx - spike, cy, cx + spike, cy], fill=FG, width=max(1, int(S * 0.6)))
        d.line([cx, cy - spike, cx, cy + spike], fill=FG, width=max(1, int(S * 0.6)))
        da.line([cx - spike, cy, cx + spike, cy], fill=200, width=max(1, int(S * 0.6)))
        da.line([cx, cy - spike, cx, cy + spike], fill=200, width=max(1, int(S * 0.6)))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=FG)
        da.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)

    return rgb, alpha


def vgrad(w, h, y0, y1, p0, p1, power=1.0):
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    for yy in range(h):
        t = min(1.0, max(0.0, (yy - y0) / (y1 - y0)))
        d.line([(0, yy), (w, yy)], fill=int(p0 + (p1 - p0) * (t ** power)))
    return m


def build():
    img = Image.new("RGB", (W, H), (2, 3, 6))
    field_rgb, field_a = deep_field(W, H)
    img.paste(field_rgb, (0, 0), field_a)

    img = Image.composite(Image.new("RGB", (W, H), BG), img,
                          vgrad(W, H, int(H * 0.42), H, 0, 255, 1.4))
    img = Image.composite(Image.new("RGB", (W, H), BG), img,
                          vgrad(W, H, 0, int(H * 0.16), 150, 0, 1.0))

    d = ImageDraw.Draw(img)
    fo, fs = f(66 * S, bold=True), f(32 * S)
    hl = wrap(d, HEADLINE, fo, W - 2 * M)
    sl = wrap(d, SUBLINE, fs, W - 2 * M)
    block_h = 46 * S + len(hl) * 78 * S + 18 * S + len(sl) * 44 * S
    y = H - M - block_h
    tracked(d, (M, y), KICKER, fmono(27 * S), ACC, 6 * S)
    y += 46 * S
    for ln in hl:
        d.text((M, y), ln, font=fo, fill=FG)
        y += 78 * S
    y += 18 * S
    for ln in sl:
        d.text((M, y), ln, font=fs, fill=SEC)
        y += 44 * S

    cr = fmono(20 * S)
    d.text((M, M), CREDIT, font=cr, fill=SEC)
    tw = d.textlength(HANDLE, font=cr)
    d.text((W - M - tw, M), HANDLE, font=cr, fill=SEC)

    return downscale(img, 1080, 1350)


if __name__ == "__main__":
    build().save(OUT / "w3-deep-field.png")
    print("saved w3-deep-field.png")
