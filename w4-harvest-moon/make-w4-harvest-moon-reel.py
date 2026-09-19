"""Woche 4, Samstag - Reel "Why is the Harvest Moon special?". 8 Frames, 1080x1920.
Anlass: Harvest Moon (Vollmond nahe der Herbst-Tagundnachtgleiche) am 26.09.2026, 16:49 UTC;
laut NASA-Skywatching geht er kurz nach Sonnenuntergang im Osten auf, Saturn steht in der Naehe,
der schwache Neptun (Helligkeit ~8, nur mit Fernglas/Teleskop) bildet ein weites Dreieck.

Erklaerung (Standardastronomie): Im Schnitt geht der Mond pro Nacht ~50 min spaeter auf; um die
Herbst-Tagundnachtgleiche verlaeuft seine Bahn (Ekliptik) am Abendhorizont flach, die taegliche
Verspaetung schrumpft in mittleren noerdlichen Breiten auf grob 30 min (weiter noerdlich weniger).
Die Uhrzeiten der Balkengrafik sind bewusst schematisch. Alles eigene Vektorgrafik.

    python make-w4-harvest-moon-reel.py  ->  w4-harvest-moon-01..08.png, -cover.png, .mp4
"""

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono, wrap
from reelkit import (W, H, M, TOP_SAFE, new_frame, header, footer_handle, ruler, ctext,
                     ctext_block, frame_cta, sphere, tex_moon, tex_saturn, blob, finish, TEX)

OUT = Path(__file__).resolve().parent
FRONT = (0.0, 0.0, 1.0)         # Vollmond: frontal beleuchtet
ORANGE = (255, 208, 160)
HORIZON_Y = TOP_SAFE + 900 * S


def moon_tex(tint=None):
    t = tex_moon()
    if tint:
        t = ImageChops.multiply(t, Image.new("RGB", (TEX, TEX), tint))
    return t


def hills(img, y, seed=5):
    """Dunkle Horizont-Silhouette (Huegel) ab Hoehe y bis Bildunterkante."""
    rnd = random.Random(seed)
    pts = [(0, H)]
    x = 0
    while x <= W + 60 * S:
        pts.append((x, y + rnd.randint(-26, 26) * S))
        x += rnd.randint(50, 110) * S
    pts.append((W, H))
    ImageDraw.Draw(img).polygon(pts, fill=(5, 7, 10))


def moon_rising(img, cy_offset, tint, glow_col, d_px=520):
    cx, cy = W // 2, HORIZON_Y - cy_offset
    sphere(img, cx, cy, d_px, moon_tex(tint), glow_col, light=FRONT)
    hills(img, HORIZON_Y)


def frame_title():
    img, d = new_frame(1)
    header(d, "SAT SEPT 26 · HARVEST MOON")
    moon_rising(img, 120 * S, ORANGE, (255, 150, 70))
    d = ImageDraw.Draw(img)
    y = TOP_SAFE + 90 * S
    for ln in ["Why is the", "Harvest Moon", "special?"]:
        ctext(d, ln, f(84 * S, bold=True), FG, y)
        y += 100 * S
    ctext(d, "it's not the color - it's the timing", f(32 * S), SEC, HORIZON_Y + 50 * S)
    footer_handle(d)
    return img


def frame_what():
    img, d = new_frame(2)
    header(d, "WHAT IT IS")
    sphere(img, W // 2, TOP_SAFE + 330 * S, 440, moon_tex(), (230, 220, 190), light=FRONT)
    d = ImageDraw.Draw(img)
    y = TOP_SAFE + 660 * S
    ctext(d, "The full Moon nearest", f(56 * S, bold=True), FG, y)
    ctext(d, "the autumn equinox", f(56 * S, bold=True), ACC, y + 70 * S)
    ctext(d, "Full Moon: Sept 26 · 16:49 UTC", fmono(32 * S), SEC, y + 190 * S)
    ruler(d, 1)
    footer_handle(d)
    return img


def rise_chart(seed, label, headline, hl_col, step_min, sub, idx, tint=None):
    """Drei Naechte, Mondaufgang jeweils spaeter - Abstand = step_min (schematisch)."""
    img, d = new_frame(seed)
    header(d, label)
    y = TOP_SAFE + 60 * S
    ctext(d, headline[0], f(66 * S, bold=True), FG, y)
    ctext(d, headline[1], f(66 * S, bold=True), hl_col, y + 80 * S)

    x0 = M + 150 * S
    px_per_min = 6.4 * S
    ytop = TOP_SAFE + 420 * S
    row = 190 * S
    d.line([x0, ytop - 40 * S, x0, ytop + row * 3 - 60 * S], fill=HAIR, width=3 * S)
    d.text((x0 - 20 * S, ytop - 100 * S), "sunset", font=fmono(22 * S), fill=SEC)
    for n in range(3):
        cy = ytop + n * row + 50 * S
        cx = x0 + int(step_min * n * px_per_min) + 52 * S
        d.text((M, cy - 18 * S), f"Night {n + 1}", font=f(30 * S), fill=SEC)
        sphere(img, cx, cy, 84, moon_tex(tint), (230, 200, 160), light=FRONT)
        d = ImageDraw.Draw(img)
        if n:
            gx0 = x0 + int(step_min * (n - 1) * px_per_min) + 52 * S + 52 * S
            gx1 = cx - 52 * S
            d.line([gx0, cy, gx1, cy], fill=hl_col, width=4 * S)
            tag = f"+{step_min} min"
            d.text(((gx0 + gx1) / 2 - d.textlength(tag, font=fmono(22 * S)) / 2, cy - 44 * S),
                   tag, font=fmono(22 * S), fill=hl_col)
    yy = ytop + row * 3 + 10 * S
    ctext_block(d, sub, f(32 * S), SEC, yy, 44 * S, W - 2 * M - 40 * S)
    ruler(d, idx)
    footer_handle(d)
    return img


def frame_why():
    img, d = new_frame(5)
    header(d, "THE REASON")
    # zwei Bahnen zum Horizont: steil vs. flach
    hy = TOP_SAFE + 760 * S
    d.line([M, hy, W - M, hy], fill=HAIR, width=3 * S)
    d.text((M, hy + 16 * S), "horizon", font=fmono(22 * S), fill=SEC)
    x0 = M + 40 * S
    L = 700 * S
    for ang, name, col, yl in [(58, "steep path", SEC, 0), (17, "shallow path", ACC, 1)]:
        a = math.radians(ang)
        x1, y1 = x0 + L * math.cos(a) * (0.55 if ang > 40 else 1.0), hy - L * math.sin(a) * (0.55 if ang > 40 else 1.0)
        d.line([x0, hy, x1, y1], fill=col, width=5 * S)
        d.text((x1 + 18 * S, y1 - 20 * S), name, font=f(30 * S, bold=True), fill=col)
    y = hy + 110 * S
    ctext(d, "Around the equinox the Moon's path", f(40 * S, bold=True), FG, y)
    ctext(d, "hugs the horizon.", f(40 * S, bold=True), ACC, y + 56 * S)
    ctext_block(d, "So each night it rises much closer to the same time.", f(32 * S), SEC,
                y + 140 * S, 44 * S, W - 2 * M - 60 * S)
    ctext(d, "(mid-northern latitudes, schematic)", fmono(22 * S), SEC, y + 250 * S)
    ruler(d, 4)
    footer_handle(d)
    return img


def frame_result():
    img, d = new_frame(6)
    header(d, "THE RESULT")
    for k in range(3):
        sphere(img, W // 2 + (k - 1) * 250 * S, TOP_SAFE + 250 * S + (k % 2) * 30 * S, 190,
               moon_tex(ORANGE), (255, 150, 70), light=FRONT)
    d = ImageDraw.Draw(img)
    y = TOP_SAFE + 520 * S
    ctext(d, "Bright moonrises", f(70 * S, bold=True), FG, y)
    ctext(d, "at dusk, night after night", f(52 * S, bold=True), ACC, y + 92 * S)
    ctext_block(d, "Traditionally the extra evening light helped farmers bring in the harvest - "
                   "hence the name.", f(32 * S), SEC, y + 200 * S, 44 * S, W - 2 * M - 40 * S)
    ruler(d, 5)
    footer_handle(d)
    return img


def frame_sky():
    img, d = new_frame(7)
    header(d, "SAT SEPT 26 · AFTER SUNSET · LOOK EAST")
    mx, my = int(W * 0.28), TOP_SAFE + 360 * S
    sx, sy = int(W * 0.72), TOP_SAFE + 200 * S
    nx, ny = int(W * 0.66), TOP_SAFE + 620 * S
    for a, b in [((mx, my), (sx, sy)), ((sx, sy), (nx, ny)), ((nx, ny), (mx, my))]:
        n = 26
        for i in range(0, n, 2):
            p0 = (a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n)
            p1 = (a[0] + (b[0] - a[0]) * (i + 1) / n, a[1] + (b[1] - a[1]) * (i + 1) / n)
            d.line([p0, p1], fill=HAIR, width=3 * S)
    sphere(img, mx, my, 210, moon_tex(), (230, 220, 190), light=FRONT)
    sphere(img, sx, sy, 84, tex_saturn(), (218, 196, 150), ring=True)
    blob(img, nx, ny, 30 * S, 30 * S, (80, 110, 220), blur=18 * S, alpha=140)
    d = ImageDraw.Draw(img)
    d.ellipse([nx - 9 * S, ny - 9 * S, nx + 9 * S, ny + 9 * S], fill=(150, 175, 255))
    d.ellipse([nx - 34 * S, ny - 34 * S, nx + 34 * S, ny + 34 * S], outline=SEC, width=2 * S)
    d.text((mx - 60 * S, my + 130 * S), "Harvest Moon", font=f(34 * S, bold=True), fill=FG)
    d.text((sx - 70 * S, sy + 90 * S), "Saturn", font=f(34 * S, bold=True), fill=FG)
    d.text((sx - 80 * S, sy + 130 * S), "easy, naked eye", font=f(26 * S), fill=SEC)
    d.text((nx - 70 * S, ny + 56 * S), "Neptune", font=f(34 * S, bold=True), fill=FG)
    d.text((nx - 110 * S, ny + 96 * S), "faint - needs binoculars", font=f(26 * S), fill=SEC)
    ctext(d, "positions schematic - not to scale", fmono(22 * S), SEC, TOP_SAFE + 900 * S)
    ruler(d, 6)
    footer_handle(d)
    return img


def main():
    frames = [
        frame_title(),
        frame_what(),
        rise_chart(3, "NORMALLY", ("Most nights the Moon", "rises ~50 min later"), FG, 50,
                   "Typical delay from one night to the next.", 2),
        rise_chart(4, "AT THE HARVEST MOON", ("Around the equinox:", "only ~30 min later"), ACC, 30,
                   "Rises close to the same time - for several nights.", 3, tint=ORANGE),
        frame_why(),
        frame_result(),
        frame_sky(),
        frame_cta(("Follow for one", "every day")),
    ]
    finish(frames, OUT, "w4-harvest-moon", cover_idx=0)


if __name__ == "__main__":
    main()
