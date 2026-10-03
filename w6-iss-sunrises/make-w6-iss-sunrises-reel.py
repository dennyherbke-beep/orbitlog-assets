"""Woche 6, Mittwoch - Reel "You get one sunrise a day. Astronauts get ...?" (Rate-Format).
8 Frames, 1080x1920, eigene Vektorgrafik (ISS stilisiert), langsamer Zoom je Frame.

Fakten (NASA "Space Station Facts and Figures", NASA Spot the Station):
  Bahnhoehe ~400 km (schwankt ~370-460), ~28.000 km/h (17.500 mph), ein Umlauf ~90 min
  (genauer ~92-93 min) -> ~15,5 Umlaeufe/Tag, NASA: "16 sunrises and 16 sunsets each day".
  Tag/Nacht je Umlauf ~45 min (vereinfacht, Anteil schwankt mit der Bahnlage).
  Los Angeles - New York ~3.940 km -> bei 28.000 km/h ~8,4 min.
  ISS mit blossem Auge sichtbar als heller, ruhig ziehender Punkt ohne Blinklicht, nur in der
  Daemmerung (Station sonnenbeschienen, Boden dunkel); Sichtungszeiten: NASA "Spot the Station"
  (kostenlos, Web/App).

Hook-Varianten (Formatvorlage Woche 6):
  1 "You get one sunrise a day. Astronauts get ...?" (gewaehlt)   2 "Astronauts see 16 sunrises a day"
  3 "Their 'day' lasts 45 minutes"   4 "Guess how many sunrises astronauts see every day"
  5 "LA to New York in 9 minutes"

    python make-w6-iss-sunrises-reel.py  ->  w6-iss-sunrises-01..08.png, -cover.png, .mp4
"""

import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono
from bodies import planet, star
from reelkit import (W, H, M, TOP_SAFE, new_frame, header, footer_handle, ruler, ctext,
                     ctext_block, frame_save, blob, finish)

OUT = Path(__file__).resolve().parent
GY = TOP_SAFE + 400 * S
TY = TOP_SAFE + 800 * S

PANEL = (176, 128, 60)        # Solarzellen (goldbraun wie auf NASA-Fotos)
PANEL_D = (120, 84, 38)
TRUSS = (196, 200, 206)
MODULE = (226, 228, 232)
MODULE_D = (150, 156, 164)


def stat(d, label, big, sub, big_col=ACC):
    ctext(d, label, f(46 * S, bold=True), FG, TY)
    ctext(d, big, f(92 * S, bold=True), big_col, TY + 66 * S)
    ctext_block(d, sub, f(34 * S), SEC, TY + 196 * S, 46 * S, W - 2 * M - 40 * S)


def iss(img, cx, cy, scale=1.0, angle=-12):
    """Stilisierte ISS von oben (auf eigener Ebene gezeichnet, leicht gedreht, mit Schatten)."""
    k = scale * S
    size = int(760 * k)
    layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    _iss_draw(layer, size // 2, size // 2, k)
    layer = layer.rotate(angle, resample=Image.BICUBIC)
    shadow = layer.split()[3].filter(ImageFilter.GaussianBlur(14 * k)).point(lambda p: p * 0.6)
    img.paste((0, 0, 0), (int(cx - size / 2 + 18 * k), int(cy - size / 2 + 24 * k)), shadow)
    img.paste(layer, (int(cx - size / 2), int(cy - size / 2)), layer)


def _iss_draw(img, cx, cy, k):
    """Hauptgitter, 8 Solarfluegel (4 Paare) mit Zellraster + Helligkeitsverlauf,
    Modulkette quer zum Gitter, Radiatoren."""
    d = ImageDraw.Draw(img)
    tw = 620 * k                                                       # Gitterlaenge
    # Radiatoren (weiss, schraeg hinter dem Gitter)
    for sx in (-1, 1):
        x = cx + sx * 120 * k
        d.polygon([(x - 26 * k, cy + 14 * k), (x + 26 * k, cy + 14 * k), (x + 34 * k, cy + 120 * k),
                   (x - 18 * k, cy + 120 * k)], fill=(214, 218, 224), outline=MODULE_D)
    # Solarfluegel: je Seite 2 Paare (oben + unten)
    for sx in (-1, 1):
        for off in (0.62, 0.88):
            x = cx + sx * tw / 2 * off
            for sy in (-1, 1):
                y0, y1 = cy + sy * 16 * k, cy + sy * 250 * k
                ya, yb = min(y0, y1), max(y0, y1)
                for half in (-1, 1):
                    xa = x + half * 6 * k
                    xb = x + half * 44 * k
                    l, r = min(xa, xb), max(xa, xb)
                    n = 12
                    for i in range(n):                                     # Zellen mit Lichtverlauf
                        t = (i / (n - 1)) if sy > 0 else 1 - i / (n - 1)
                        c = tuple(int(v * (1.12 - 0.3 * t)) for v in PANEL)
                        y_a, y_b = ya + (yb - ya) * i / n, ya + (yb - ya) * (i + 1) / n
                        d.rectangle([l, y_a, r, y_b], fill=c)
                        d.line([l, y_a, r, y_a], fill=PANEL_D, width=max(1, int(1.2 * k)))
                    d.rectangle([l, ya, r, yb], outline=PANEL_D, width=max(1, int(1.5 * k)))
                    d.line([(l + r) / 2, ya, (l + r) / 2, yb], fill=PANEL_D, width=max(1, int(1 * k)))
                d.line([x, ya, x, yb], fill=TRUSS, width=max(1, int(3 * k)))   # Mast
    # Hauptgitter
    d.rectangle([cx - tw / 2, cy - 9 * k, cx + tw / 2, cy + 9 * k], fill=TRUSS, outline=MODULE_D)
    for i in range(0, 41):
        x = cx - tw / 2 + tw * i / 40
        d.line([x, cy - 9 * k, x + tw / 80, cy + 9 * k], fill=MODULE_D, width=max(1, int(1 * k)))
    # Modulkette (quer), Zylinder mit Schattierung
    mods = [(-150, 30, 40), (-105, 60, 34), (-40, 70, 38), (35, 80, 36), (110, 60, 32), (165, 50, 28)]
    for y_off, length, w in mods:
        y = cy + y_off * k
        x0, x1 = cx - w / 2 * k, cx + w / 2 * k
        d.rounded_rectangle([x0, y - length / 2 * k, x1, y + length / 2 * k], 8 * k, fill=MODULE,
                            outline=MODULE_D, width=max(1, int(1.5 * k)))
        d.rectangle([x1 - w * 0.28 * k, y - length / 2 * k + 3 * k, x1 - 2 * k, y + length / 2 * k - 3 * k],
                    fill=(196, 200, 208))
    # Seitenmodule (Labore links/rechts am Knoten)
    for sx in (-1, 1):
        d.rounded_rectangle([cx + sx * 20 * k - (60 * k if sx < 0 else 0), cy + 22 * k,
                             cx + sx * 20 * k + (60 * k if sx > 0 else 0), cy + 56 * k], 8 * k,
                            fill=MODULE, outline=MODULE_D, width=max(1, int(1.5 * k)))


def earth_limb(img, glow_strength=1.0):
    """Erdrand unten im Bild (unterhalb des Textblocks) mit Sonnenaufgangs-Leuchten am Horizont."""
    R, cy = 1100, H // S + 860
    planet(img, W // 2, cy * S, 2 * R, "earth", light=(0.85, -0.5, 0.15))
    dx = 0.28 * W / S
    y = (cy - math.sqrt(R * R - dx * dx)) * S
    x = W // 2 + dx * S
    blob(img, int(x), int(y), int(300 * S * glow_strength), int(40 * S), (255, 170, 80),
         blur=int(40 * S), alpha=int(220 * glow_strength))
    blob(img, int(x), int(y), int(70 * S), int(14 * S), (255, 246, 220), blur=int(10 * S),
         alpha=int(255 * glow_strength))


def frame_hook():
    img, d = new_frame(1)
    earth_limb(img)
    iss(img, W // 2, TOP_SAFE + 360 * S, 0.9)
    d = ImageDraw.Draw(img)
    header(d, "GUESS FIRST")
    y = TOP_SAFE + 780 * S
    ctext(d, "You get one sunrise", f(76 * S, bold=True), FG, y)
    ctext(d, "a day.", f(76 * S, bold=True), FG, y + 90 * S)
    ctext(d, "Astronauts get ...?", f(76 * S, bold=True), ACC, y + 200 * S)
    ctext(d, "comment your guess ↓", f(34 * S), SEC, y + 330 * S)
    footer_handle(d)
    return img


def frame_height():
    img, d = new_frame(2)
    earth_limb(img, 0.4)
    iss(img, W // 2, GY, 0.6)
    d = ImageDraw.Draw(img)
    header(d, "WHERE THEY LIVE")
    stat(d, "The space station flies", "~400 km up",
         "About the distance from London to Paris - just straight up.")
    ruler(d, 1)
    footer_handle(d)
    return img


def frame_speed():
    img, d = new_frame(3)
    header(d, "HOW FAST")
    y = GY
    d.line([M + 60 * S, y, W - M - 60 * S, y], fill=HAIR, width=4 * S)
    for x, t in [(M + 60 * S, "Los Angeles"), (W - M - 60 * S, "New York")]:
        d.ellipse([x - 12 * S, y - 12 * S, x + 12 * S, y + 12 * S], fill=ACC)
        ctext(d, t, f(32 * S, bold=True), FG, y + 34 * S, cx=x)
    ctext(d, "under 9 minutes", f(54 * S, bold=True), ACC, y - 110 * S)
    stat(d, "It moves at about", "28,000 km/h",
         "Roughly 8 km every second.")
    ruler(d, 2)
    footer_handle(d)
    return img


def orbit_diagram(img, cx, cy, r, mark_sunrise=False):
    d = ImageDraw.Draw(img)
    star(img, M + 30 * S, cy, 90, spots=False, corona=0.8)
    planet(img, cx, cy, 300, "earth", light=(-1.0, 0.0, 0.2))
    d = ImageDraw.Draw(img)
    box = [cx - r, cy - r, cx + r, cy + r]
    d.arc(box, 90, 270, fill=ACC, width=6 * S)                         # Tagseite (zur Sonne)
    d.arc(box, 270, 90, fill=(80, 100, 150), width=6 * S)              # Nachtseite
    if mark_sunrise:
        for ang in (90, 270):
            x, y = cx + r * math.cos(math.radians(ang)), cy + r * math.sin(math.radians(ang))
            d.ellipse([x - 14 * S, y - 14 * S, x + 14 * S, y + 14 * S], fill=(255, 236, 190))
    return d


def frame_lap():
    img, d = new_frame(4)
    header(d, "ONE LAP")
    d = orbit_diagram(img, W // 2 + 80 * S, GY, 260 * S)
    stat(d, "Once around Earth:", "~90 minutes",
         "Faster than most movies.")
    ruler(d, 3)
    footer_handle(d)
    return img


def frame_halves():
    img, d = new_frame(5)
    header(d, "DAY AND NIGHT")
    d = orbit_diagram(img, W // 2 + 80 * S, GY, 260 * S, mark_sunrise=True)
    ctext(d, "45 min day", f(34 * S, bold=True), ACC, GY + 290 * S, cx=W // 2 - 120 * S)
    ctext(d, "45 min night", f(34 * S, bold=True), (140, 160, 210), GY - 20 * S, cx=W - M - 20 * S)
    stat(d, "So every lap brings", "a sunrise",
         "and a sunset - about 45 minutes apart.")
    ruler(d, 4)
    footer_handle(d)
    return img


def frame_reveal():
    img, d = new_frame(6)
    earth_limb(img, 1.0)
    d = ImageDraw.Draw(img)
    header(d, "ANSWER")
    ctext(d, "16", f(300 * S, bold=True), ACC, TOP_SAFE + 120 * S)
    stat(d, "Astronauts see about", "16 sunrises a day",
         "24 hours ÷ ~90 minutes = 16 laps. Was your guess close?")
    ruler(d, 5)
    footer_handle(d)
    return img


def frame_spot():
    img, d = new_frame(7)
    header(d, "SEE IT YOURSELF")
    sx, sy = W // 2 - 260 * S, GY + 160 * S
    for i in range(10):                                                # Spur eines ruhig ziehenden Punkts
        t = i / 9
        x, y = sx + t * 520 * S, sy - math.sin(t * math.pi) * 180 * S
        r = (3 + 6 * t) * S
        blob(img, int(x), int(y), int(r * 2), int(r * 2), (255, 244, 220), blur=int(r), alpha=int(60 + 190 * t))
    d = ImageDraw.Draw(img)
    stat(d, "It's the brightest moving", "'star' at dusk",
         "Steady, no blinking lights. NASA's free 'Spot the Station' tells you when it passes over you.")
    ruler(d, 6)
    footer_handle(d)
    return img


def main():
    frames = [
        frame_hook(),
        frame_height(),
        frame_speed(),
        frame_lap(),
        frame_halves(),
        frame_reveal(),
        frame_spot(),
        frame_save(("Save this", "and check", "Spot the Station tonight"),
                   sub="Send it to someone who'd love to wave at it"),
    ]
    finish(frames, OUT, "w6-iss-sunrises", cover_idx=0, motion=True)


if __name__ == "__main__":
    main()
