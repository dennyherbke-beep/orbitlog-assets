"""Woche 5, Samstag - Reel "A meteor shower you can watch before bedtime" (Draconiden 2026).
8 Frames, 1080x1920, eigene Vektorgrafik (Meteorspuren schematisch).

Fakten (EarthSky "Draconid meteor shower 2026", Royal Museums Greenwich):
  aktiv 6.-10.10.2026, Maximum 09.10.; beste Zeit ab Einbruch der Dunkelheit am Abend des
  08.10. - ungewoehnlich: der Radiant (Drache) steht abends am hoechsten, daher mehr Meteore
  am Abend als vor der Morgendaemmerung. Normal ~10 pro Stunde unter dunklem Himmel;
  Ausbrueche mit Hunderten pro Stunde 1933, 1946, 2011, 2018 - fuer 2026 nicht vorhergesagt.
  Neumond 10.10.2026, 15:50 UTC -> Mond stoert nicht. Ursprungskomet 21P/Giacobini-Zinner.
  Beste Sicht von der Nordhalbkugel (Drache zirkumpolar).

    python make-w5-draconids-reel.py  ->  w5-draconids-01..08.png, -cover.png, .mp4
"""

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono
from reelkit import (W, H, M, TOP_SAFE, new_frame, header, footer_handle, ruler, ctext,
                     ctext_block, frame_save, blob, finish)

OUT = Path(__file__).resolve().parent
GY = TOP_SAFE + 400 * S
TY = TOP_SAFE + 800 * S


def meteor(img, x0, y0, ang, length, width, bright=255):
    """Meteorspur: duenner Schweif, der zum Kopf hin heller und breiter wird, mit Glow."""
    x1, y1 = x0 + math.cos(ang) * length, y0 + math.sin(ang) * length
    glow = Image.new("L", img.size, 0)
    gd = ImageDraw.Draw(glow)
    n = 40
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        a = int(bright * t1 ** 1.6)
        gd.line([x0 + (x1 - x0) * t0, y0 + (y1 - y0) * t0, x0 + (x1 - x0) * t1, y0 + (y1 - y0) * t1],
                fill=a, width=max(1, int(width * (0.3 + 0.7 * t1))))
    halo = glow.filter(ImageFilter.GaussianBlur(width * 1.4))
    img.paste(Image.new("RGB", img.size, (170, 210, 255)), (0, 0), halo)
    img.paste(Image.new("RGB", img.size, (245, 250, 255)), (0, 0), glow)
    blob(img, int(x1), int(y1), int(width * 2.2), int(width * 2.2), (230, 240, 255), blur=int(width), alpha=bright)


def shower(img, rx, ry, n, seed, spread=(0.15, 0.95), lmax=320, arc=(0, 2 * math.pi)):
    """n Meteore, die vom Radianten (rx, ry) weg zeigen; arc begrenzt die Richtungen."""
    rnd = random.Random(seed)
    for _ in range(n):
        ang = rnd.uniform(*arc)
        dist = rnd.uniform(*spread) * 520 * S
        x0, y0 = rx + math.cos(ang) * dist, ry + math.sin(ang) * dist
        meteor(img, x0, y0, ang, rnd.uniform(0.4, 1.0) * lmax * S, rnd.uniform(2.5, 5.0) * S,
               bright=rnd.randint(170, 255))


def radiant_mark(d, x, y):
    d.ellipse([x - 16 * S, y - 16 * S, x + 16 * S, y + 16 * S], outline=ACC, width=3 * S)


def stat(d, label, big, sub, big_col=ACC):
    ctext(d, label, f(46 * S, bold=True), FG, TY)
    ctext(d, big, f(92 * S, bold=True), big_col, TY + 66 * S)
    ctext_block(d, sub, f(34 * S), SEC, TY + 196 * S, 46 * S, W - 2 * M - 40 * S)


def frame_title():
    img, d = new_frame(1)
    header(d, "THU OCT 8 · DRACONIDS")
    rx, ry = W // 2, TOP_SAFE + 160 * S
    shower(img, rx, ry, 16, 3, spread=(0.12, 0.85), lmax=240, arc=(0.15 * math.pi, 0.85 * math.pi))
    shower(img, rx, ry, 6, 4, spread=(0.10, 0.45), lmax=160, arc=(-0.1 * math.pi, 1.1 * math.pi))
    d = ImageDraw.Draw(img)
    radiant_mark(d, rx, ry)
    y = TOP_SAFE + 820 * S
    ctext(d, "A meteor shower", f(78 * S, bold=True), FG, y)
    ctext(d, "before bedtime", f(78 * S, bold=True), ACC, y + 94 * S)
    ctext(d, "most showers peak before dawn - not this one →", f(32 * S), SEC, y + 216 * S)
    footer_handle(d)
    return img


def frame_when():
    img, d = new_frame(2)
    header(d, "WHEN")
    shower(img, W // 2, GY, 4, 11, lmax=260)
    d = ImageDraw.Draw(img)
    stat(d, "Best: Thursday, Oct 8", "right after dark",
         "The peak runs into the night of Oct 8-9. Active roughly Oct 6-10.")
    ruler(d, 1)
    footer_handle(d)
    return img


def frame_why_evening():
    img, d = new_frame(3)
    header(d, "WHY THE EVENING")
    hy = GY + 170 * S
    d.line([M, hy, W - M, hy], fill=HAIR, width=3 * S)
    d.text((M, hy + 14 * S), "horizon", font=fmono(22 * S), fill=SEC)
    rx, ry = W // 2, GY - 150 * S
    shower(img, rx, ry, 5, 21, spread=(0.1, 0.5), lmax=200)
    d = ImageDraw.Draw(img)
    radiant_mark(d, rx, ry)
    d.text((rx + 30 * S, ry - 16 * S), "radiant (Draco)", font=fmono(24 * S), fill=ACC)
    stat(d, "Their source point is highest", "at nightfall",
         "Meteors seem to fly out of the constellation Draco - and Draco rides high in the evening sky.")
    ruler(d, 2)
    footer_handle(d)
    return img


def frame_rate():
    img, d = new_frame(4)
    header(d, "HOW MANY")
    shower(img, W // 2, GY, 3, 31, lmax=260)
    d = ImageDraw.Draw(img)
    stat(d, "Under a dark sky:", "about 10 per hour",
         "A modest shower - bits of dust from comet 21P/Giacobini-Zinner hitting our atmosphere.")
    ruler(d, 3)
    footer_handle(d)
    return img


def frame_surprise():
    img, d = new_frame(5)
    header(d, "THE WILD CARD")
    shower(img, W // 2, GY, 26, 41, lmax=240)
    d = ImageDraw.Draw(img)
    stat(d, "In 1933, 1946, 2011 and 2018:", "hundreds per hour",
         "The Draconids are known for surprise outbursts. None is predicted for 2026 - but it's why people look.")
    ruler(d, 4)
    footer_handle(d)
    return img


def frame_moon():
    img, d = new_frame(6)
    header(d, "THE MOON STAYS OUT OF IT")
    r = 120 * S
    for a in range(0, 360, 12):   # gestrichelter Umriss: der Neumond ist unsichtbar
        d.arc([W // 2 - r, GY - r, W // 2 + r, GY + r], a, a + 7, fill=SEC, width=3 * S)
    ctext(d, "new Moon = invisible", fmono(26 * S), SEC, GY + r + 30 * S)
    stat(d, "New Moon: Oct 10", "dark skies",
         "Only a thin crescent before dawn - nothing to wash out the evening meteors.")
    ruler(d, 5)
    footer_handle(d)
    return img


def frame_how():
    img, d = new_frame(7)
    header(d, "HOW TO WATCH")
    items = ["Get away from streetlights", "Face north, lie back", "Give your eyes 20 minutes",
             "No telescope - just your eyes"]
    y = GY - 180 * S
    for n, t in enumerate(items, 1):
        d.text((M + 40 * S, y), f"{n}", font=f(64 * S, bold=True), fill=ACC)
        d.text((M + 130 * S, y + 12 * S), t, font=f(44 * S, bold=True), fill=FG)
        y += 130 * S
    ctext_block(d, "Best from the Northern Hemisphere. Southern skies see few or none.",
                f(34 * S), SEC, TY + 200 * S, 46 * S, W - 2 * M - 40 * S)
    ruler(d, 6)
    footer_handle(d)
    return img


def main():
    frames = [
        frame_title(),
        frame_when(),
        frame_why_evening(),
        frame_rate(),
        frame_surprise(),
        frame_moon(),
        frame_how(),
        frame_save(("Save this", "for Thursday, Oct 8", "- and look up after dark")),
    ]
    finish(frames, OUT, "w5-draconids", cover_idx=0)


if __name__ == "__main__":
    main()
