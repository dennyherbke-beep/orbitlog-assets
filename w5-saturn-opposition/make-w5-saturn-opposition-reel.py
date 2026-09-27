"""Woche 5, Donnerstag - Space-Tech-Reel "Saturn is closest this Sunday - what you'll see".
Anlass: Saturn-Opposition am 04.10.2026, ~12 UTC. 8 Frames, 1080x1920, eigene Vektorgrafik.

Fakten (EarthSky "Saturn at opposition", 2026; NASA JPL Night Sky Network):
  Opposition 04.10.2026 ~12:00 UTC, Erde zwischen Sonne und Saturn, Saturn geht bei
  Sonnenuntergang auf und ist die ganze Nacht sichtbar; Abstand ~1,26 Mrd. km (8,43 AU);
  Helligkeit 0,3 mag; Scheibe 19,7"; Ringneigung -7,5 Grad (Ringebenen-Durchgang 23.03.2025,
  Ringe oeffnen sich seither langsam). Fernglas: helles ovales Scheibchen; jedes kleine
  Teleskop zeigt die Ringe. Titan (~8,5 mag) in kleinen Teleskopen sichtbar (Standardwissen).
  Lichtlaufzeit 1,26e9 km / 299.792 km/s = 4.203 s = 70 min.

    python make-w5-saturn-opposition-reel.py  ->  w5-saturn-opposition-01..08.png, -cover.png, .mp4
"""

import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono
from bodies import planet, star
from reelkit import (W, H, M, TOP_SAFE, new_frame, header, footer_handle, ruler, ctext,
                     ctext_block, frame_save, sphere, tex_saturn, blob, finish)

OUT = Path(__file__).resolve().parent
GY = TOP_SAFE + 400 * S
TY = TOP_SAFE + 800 * S
RING = (226, 208, 166)


def saturn(img, cx, cy, d_px, tilt_deg=7.5):
    """Saturn mit Ringen (bodies.planet); Neigung ~1,6x ueberzeichnet, damit auf dem Handy sichtbar."""
    planet(img, cx, cy, d_px, "saturn", ring_tilt=tilt_deg * 1.6, light=(-0.35, -0.3, 0.88))


def eyepiece(img, cx, cy, rad):
    """Runder Okular-/Fernglas-Ausschnitt: dunkler Kreis mit weichem Rand."""
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=255)
    img.paste(Image.new("RGB", img.size, (3, 4, 7)), (0, 0), m.filter(ImageFilter.GaussianBlur(6 * S)))
    ImageDraw.Draw(img).ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=HAIR, width=4 * S)


def stat(d, label, big, sub, big_col=ACC):
    ctext(d, label, f(46 * S, bold=True), FG, TY)
    ctext(d, big, f(92 * S, bold=True), big_col, TY + 66 * S)
    ctext_block(d, sub, f(34 * S), SEC, TY + 196 * S, 46 * S, W - 2 * M - 40 * S)


def frame_title():
    img, d = new_frame(1)
    header(d, "SUN OCT 4 · SATURN AT OPPOSITION")
    saturn(img, W // 2, TOP_SAFE + 470 * S, 330)
    d = ImageDraw.Draw(img)
    y = TOP_SAFE + 790 * S
    ctext(d, "Saturn is closest", f(80 * S, bold=True), FG, y)
    ctext(d, "this Sunday", f(80 * S, bold=True), ACC, y + 96 * S)
    ctext(d, "here's what you'll actually see →", f(34 * S), SEC, y + 220 * S)
    footer_handle(d)
    return img


def frame_what():
    img, d = new_frame(2)
    header(d, "WHAT 'OPPOSITION' MEANS")
    y = GY
    sun_x, earth_x, sat_x = M + 90 * S, W // 2 - 60 * S, W - M - 110 * S
    d.line([sun_x, y, sat_x, y], fill=HAIR, width=3 * S)
    star(img, sun_x, y, 120, "sun", spots=False)
    planet(img, earth_x, y, 60, "earth", light=(-1.0, 0.0, 0.25))
    planet(img, sat_x, y, 90, "saturn", ring_tilt=12, light=(-1.0, 0.0, 0.3))
    d = ImageDraw.Draw(img)
    for x, t in [(sun_x, "Sun"), (earth_x, "Earth"), (sat_x, "Saturn")]:
        ctext(d, t, f(32 * S, bold=True), FG, y + 110 * S, cx=x)
    ctext(d, "(not to scale)", fmono(22 * S), SEC, y + 170 * S)
    stat(d, "Earth sits right between", "Sun and Saturn",
         "So Saturn rises as the Sun sets - and stays up all night.", big_col=ACC)
    ruler(d, 1)
    footer_handle(d)
    return img


def frame_distance():
    img, d = new_frame(3)
    header(d, "HOW FAR")
    saturn(img, W // 2, GY, 220)
    d = ImageDraw.Draw(img)
    stat(d, "Closest for 2026:", "1.26 billion km",
         "Its light needs about 70 minutes to reach your eyes.")
    ruler(d, 2)
    footer_handle(d)
    return img


def frame_eye():
    img, d = new_frame(4)
    header(d, "1 · NAKED EYE")
    cx, cy = W // 2, GY
    blob(img, cx, cy, 70 * S, 70 * S, (255, 236, 190), blur=26 * S, alpha=150)
    d = ImageDraw.Draw(img)
    d.ellipse([cx - 11 * S, cy - 11 * S, cx + 11 * S, cy + 11 * S], fill=(255, 246, 222))
    stat(d, "A bright, steady 'star'", "look east at dusk",
         "No gear needed. It's the brightest point in that part of the sky - and it hardly twinkles.")
    ruler(d, 3)
    footer_handle(d)
    return img


def frame_binoculars():
    img, d = new_frame(5)
    header(d, "2 · BINOCULARS")
    cx, cy, rad = W // 2, GY, 300 * S
    for dx in (-rad * 0.52, rad * 0.52):
        eyepiece(img, int(cx + dx), cy, int(rad * 0.62))
    d = ImageDraw.Draw(img)
    for dx in (-rad * 0.52, rad * 0.52):
        x = cx + dx
        blob(img, int(x), cy, 22 * S, 12 * S, (240, 222, 180), blur=5 * S, alpha=230)
    d = ImageDraw.Draw(img)
    stat(d, "A tiny bright oval", "not a dot",
         "Steady binoculars - ideally on a tripod - already show that Saturn isn't round.")
    ruler(d, 4)
    footer_handle(d)
    return img


def frame_telescope():
    img, d = new_frame(6)
    header(d, "3 · ANY SMALL TELESCOPE")
    cx, cy, rad = W // 2, GY, 300 * S
    eyepiece(img, cx, cy, rad)
    saturn(img, cx, cy, 150)
    d = ImageDraw.Draw(img)
    tx, ty = cx + 230 * S, cy - 60 * S
    d.ellipse([tx - 5 * S, ty - 5 * S, tx + 5 * S, ty + 5 * S], fill=(255, 226, 170))
    d.text((tx - 60 * S, ty - 60 * S), "Titan", font=f(28 * S, bold=True), fill=SEC)
    stat(d, "The rings - and Titan", "the real payoff",
         "Even a beginner telescope shows the rings. The faint dot nearby is Titan, Saturn's biggest moon.")
    ruler(d, 5)
    footer_handle(d)
    return img


def frame_rings():
    img, d = new_frame(7)
    header(d, "WHY THE RINGS LOOK THIN")
    saturn(img, W // 2, GY, 220)
    d = ImageDraw.Draw(img)
    stat(d, "Tilted toward us by only", "7.5°",
         "In 2025 we saw them edge-on. They're slowly opening again - wider every year until the early 2030s.")
    ruler(d, 6)
    footer_handle(d)
    return img


def main():
    frames = [
        frame_title(),
        frame_what(),
        frame_distance(),
        frame_eye(),
        frame_binoculars(),
        frame_telescope(),
        frame_rings(),
        frame_save(("Save this", "for Sunday night -", "Saturn is up till dawn")),
    ]
    finish(frames, OUT, "w5-saturn-opposition", cover_idx=0)


if __name__ == "__main__":
    main()
