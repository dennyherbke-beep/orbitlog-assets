"""Woche 5, Dienstag - Reel "If the solar system fit in your city - Part 2: where's the nearest
star?". Fortsetzung von w3-solar-system-city (bisher staerkstes Reel, 785 Betrachter) im selben
Massstab: Sonne = Beachball 30 cm. 8 Frames, 1080x1920, eigene Vektorgrafik.

Herleitung (gleicher Skalenfaktor wie Teil 1): k = 0.3 m / 1.391.000 km = 2.1567e-10.
  Neptun 30.069 AU                      -> 970 m
  Voyager 1 bei 1 Lichttag = 25.9e9 km  -> 5.6 km   (Meilenstein 18.11.2026, NASA/JPL)
  1 Lichtjahr = 9.4607e12 km            -> 2,040 km (~ Paris-Athen, ~2,100 km Luftlinie)
  Proxima Centauri 4.2465 Lj            -> 8,660 km (~ London-Los Angeles, ~8,760 km)
     Durchmesser 0.154 Sonnenradien     -> 4.6 cm   (~ Golfball, 4.3 cm)
  Milchstrasse ~100,000 Lj Durchmesser  -> ~204 Mio. km (> echte Erde-Sonne-Distanz 150 Mio. km)
  Andromeda 2.5 Mio. Lj (2.537)         -> ~5.2 Mrd. km (> echter Neptun-Abstand ~4.5 Mrd. km)

    python make-w5-city-nearest-star-reel.py  ->  w5-city-nearest-star-01..08.png, -cover.png, .mp4
"""

import importlib.util
import sys
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono
from bodies import planet, star
from reelkit import (W, H, M, TOP_SAFE, new_frame, header, footer_handle, ruler, ctext,
                     ctext_block, frame_save, sphere, blob, grain, finish, TEX)

OUT = Path(__file__).resolve().parent


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


city = _load("city", ROOT / "w3-solar-system-city" / "make-w3-solar-system-city.py")
andro = _load("andro", ROOT / "w2-andromeda" / "make-w2-andromeda.py")


def tex_red_dwarf():
    img = Image.new("RGB", (TEX, TEX), (236, 108, 70))
    blob(img, 200, 190, 90, 70, (255, 150, 96), blur=40, alpha=160)
    blob(img, 330, 320, 60, 44, (190, 70, 46), blur=26, alpha=140)
    return grain(img, 16, 3)


def galaxy(img, cx, cy, size_px, flatten, angle, seed):
    """Wie andro.place_galaxy, aber mit schwachem, engem Halo (der Original-Halo graut im
    Hochformat den ganzen Frame ein)."""
    sprite = andro.make_galaxy(900, seed=seed).resize((900, int(900 * flatten)), Image.LANCZOS)
    sprite = sprite.rotate(angle, resample=Image.BICUBIC, expand=True)
    k = size_px / sprite.width
    sprite = sprite.resize((int(sprite.width * k), int(sprite.height * k)), Image.LANCZOS)
    blob(img, cx, cy, int(size_px * 0.42), int(size_px * 0.30), (150, 170, 220), blur=int(size_px * 0.15), alpha=45)
    img.paste(sprite, (cx - sprite.width // 2, cy - sprite.height // 2), sprite)


GY = TOP_SAFE + 400 * S     # Mitte der Grafik
TY = TOP_SAFE + 780 * S     # Beginn des Textblocks


def big_stat(d, y, label, value, comp):
    ctext(d, label, f(46 * S, bold=True), FG, y)
    ctext(d, value, f(96 * S, bold=True), ACC, y + 66 * S)
    return ctext_block(d, comp, f(34 * S), SEC, y + 200 * S, 46 * S, W - 2 * M - 40 * S)


def frame_title():
    img, d = new_frame(1)
    header(d, "TO SCALE · PART 2")
    star(img, W - int(W * 0.20), TOP_SAFE + int(H * 0.14), 200, "sun")
    d = ImageDraw.Draw(img)
    y = TOP_SAFE + int(H * 0.28)
    for ln in ["The solar system", "fits in your city.", "Where's the", "nearest star?"]:
        d.text((M, y), ln, font=f(76 * S, bold=True), fill=FG if y < TOP_SAFE + int(H * 0.28) + 180 * S else ACC)
        y += 90 * S
    d.text((M, y + 20 * S), "same scale: the Sun is a beach ball →", font=f(32 * S), fill=SEC)
    footer_handle(d)
    return img


def frame_recap():
    img, d = new_frame(2)
    header(d, "RECAP · PART 1")
    cy = GY
    star(img, W // 2 - 190 * S, cy, 240, "sun")
    planet(img, W // 2 + 230 * S, cy, 90, "neptune")
    d = ImageDraw.Draw(img)
    d.text((W // 2 - 280 * S, cy + 170 * S), "Sun: 30 cm", font=f(34 * S, bold=True), fill=FG)
    d.text((W // 2 + 160 * S, cy + 170 * S), "Neptune", font=f(34 * S, bold=True), fill=FG)
    big_stat(d, TY, "Neptune, the last planet:", "970 m away",
             "About the edge of your neighborhood. Now keep walking.")
    ruler(d, 1)
    footer_handle(d)
    return img


def frame_voyager():
    img, d = new_frame(3)
    header(d, "OUR FARTHEST SPACECRAFT")
    cy = GY
    blob(img, W // 2, cy, 60 * S, 60 * S, (200, 210, 230), blur=30 * S, alpha=120)
    d = ImageDraw.Draw(img)
    d.ellipse([W // 2 - 5 * S, cy - 5 * S, W // 2 + 5 * S, cy + 5 * S], fill=FG)
    ctext(d, "a speck of dust", fmono(26 * S), SEC, cy + 60 * S)
    big_stat(d, TY, "Voyager 1:", "5.6 km away",
             "One light-day from Earth this November - after 49 years of flying.")
    ruler(d, 2)
    footer_handle(d)
    return img


def frame_lightyear():
    img, d = new_frame(4)
    header(d, "ONE LIGHT-YEAR")
    y0 = GY
    d.line([M + 20 * S, y0, W - M - 20 * S, y0], fill=ACC, width=5 * S)
    for x in (M + 20 * S, W - M - 20 * S):
        d.line([x, y0 - 30 * S, x, y0 + 30 * S], fill=ACC, width=5 * S)
    ctext(d, "1 light-year", fmono(32 * S), SEC, y0 - 90 * S)
    big_stat(d, TY, "At this scale, one light-year is", "2,040 km",
             "Roughly Paris to Athens - and the nearest star is more than 4 of them away.")
    ruler(d, 3)
    footer_handle(d)
    return img


def frame_proxima():
    img, d = new_frame(5)
    header(d, "THE NEAREST STAR")
    star(img, W // 2, GY, 230, "red_dwarf")
    d = ImageDraw.Draw(img)
    ctext(d, "a golf ball", fmono(28 * S), SEC, GY + 170 * S)
    big_stat(d, TY, "Proxima Centauri:", "8,660 km",
             "About London to Los Angeles. Between the beach ball and the golf ball: almost nothing.")
    ruler(d, 4)
    footer_handle(d)
    return img


def frame_milkyway():
    img, d = new_frame(6)
    header(d, "OUR GALAXY")
    galaxy(img, W // 2, GY, int(W * 0.80), 0.55, -18, 4)
    d = ImageDraw.Draw(img)
    big_stat(d, TY, "The Milky Way would span", "204 million km",
             "Wider than the real distance from Earth to the Sun.")
    ruler(d, 5)
    footer_handle(d)
    return img


def frame_andromeda():
    img, d = new_frame(7)
    header(d, "THE NEXT BIG GALAXY")
    galaxy(img, W // 2, GY, int(W * 0.70), 0.40, -28, 11)
    d = ImageDraw.Draw(img)
    big_stat(d, TY, "Andromeda would be", "5.2 billion km",
             "Farther than the real Neptune - even with the Sun shrunk to a beach ball.")
    ruler(d, 6)
    footer_handle(d)
    return img


def main():
    frames = [
        frame_title(),
        frame_recap(),
        frame_voyager(),
        frame_lightyear(),
        frame_proxima(),
        frame_milkyway(),
        frame_andromeda(),
        frame_save(("Save this", "for the next time someone", "says space is crowded")),
    ]
    finish(frames, OUT, "w5-city-nearest-star", cover_idx=4)


if __name__ == "__main__":
    main()
