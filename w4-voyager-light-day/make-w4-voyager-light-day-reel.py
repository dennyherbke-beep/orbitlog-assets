"""Woche 4, Sonntag - Reel "Voyager 1 is about to be one light-day from Earth". 8 Frames, 1080x1920.
Anlass: NASA/JPL - Voyager 1 erreicht am 18.11.2026 um 2:16:07 Uhr PST eine Entfernung von einem
Lichttag (25.902.068.356 km = ca. 25,9 Mrd. km) und ist damit das erste menschengemachte Objekt
in dieser Entfernung. Alle Werte: NASA-Seite "Voyager 1: What Is a Light-Day".

Lichtlaufzeiten (NASA): Mond 1,3 s (384.400 km), Sonne 8 min 20 s (149,6 Mio. km),
Neptun ~4 h 10 min (~4,5 Mrd. km), Voyager 1 = 24 h. Geschwindigkeit ~61.000 km/h (17 km/s);
Licht ist damit rund 17.700x schneller. Naechster Stern in Flugrichtung: AC+79 3888 (Gliese 445),
> 17 Lichtjahre entfernt (17 ly x 365,25 = ~6.200 Lichttage), Vorbeiflug in ~40.000 Jahren in
1,7 Lichtjahren Abstand. Sonde: NASA/JPL-Caltech Kuenstlerdarstellung PIA17462 ("Voyager 1 Entering
Interstellar Space", NASA-Bilder grundsaetzlich gemeinfrei, Credit im Bild); Mond/Sonne/Neptun eigene Grafik.

    python make-w4-voyager-light-day-reel.py -> w4-voyager-light-day-01..08.png, -cover.png, .mp4
"""

import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono
from reelkit import (W, H, M, TOP_SAFE, BOT_SAFE, new_frame, header, footer_handle, ruler, ctext,
                     ctext_block, frame_cta, sphere, tex_moon, blob, band, grain, finish, TEX)

OUT = Path(__file__).resolve().parent
CY = TOP_SAFE + 300 * S


def tex_neptune():
    img = Image.new("RGB", (TEX, TEX), (66, 96, 208))
    band(img, 70, 120, (46, 70, 165), alpha=90, blur=16)
    band(img, 250, 290, (46, 70, 165), alpha=70, blur=16)
    blob(img, 320, 235, 65, 42, (38, 60, 150), blur=14)
    return grain(img, 10, 4)


def sun(img, cx, cy, r):
    core, edge = (255, 244, 214), (255, 150, 50)
    blob(img, cx, cy, int(r * 2.0), int(r * 2.0), ACC, blur=int(r * 0.8), alpha=90)
    d = ImageDraw.Draw(img)
    for i in range(r, 0, -1):
        t = i / r
        col = tuple(int(edge[k] + (core[k] - edge[k]) * (1 - t)) for k in range(3))
        d.ellipse([cx - i, cy - i, cx + i, cy + i], fill=col)


SRC = Image.open(OUT / "PIA17462.jpg").convert("RGB")     # NASA/JPL-Caltech, 8192 x 4610
CROP = (3900, 205, 6300, 3400)                             # um die Sonde (Hochformat)
_PROBE = {}


def probe(img, cx, cy, h):
    """NASA-Rendering der Sonde: Ausschnitt per Screen-Blend (der schwarze Bildhintergrund
    verschwindet im Marken-Hintergrund), Rand weich ausgeblendet. Mittig auf cx/cy, Hoehe h."""
    if h not in _PROBE:
        crop = SRC.crop(CROP)
        w = int(h * crop.width / crop.height)
        crop = crop.resize((w, h), Image.LANCZOS)
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rectangle([w * 0.18, h * 0.07, w * 0.92, h * 0.95], fill=255)
        _PROBE[h] = (crop, mask.filter(ImageFilter.GaussianBlur(min(w, h) * 0.09)))
    crop, mask = _PROBE[h]
    box = (cx - crop.width // 2, cy - crop.height // 2)
    region = img.crop((box[0], box[1], box[0] + crop.width, box[1] + crop.height))
    img.paste(ImageChops.screen(region, crop), box, mask)


def credit(d):
    ctext(d, "Artist's concept: NASA/JPL-Caltech", fmono(18 * S), SEC, H - BOT_SAFE + 44 * S)


def frame_title():
    img, d = new_frame(1)
    header(d, "VOYAGER 1 · NOV 18, 2026")
    probe(img, W // 2, TOP_SAFE + 330 * S, 620 * S)
    d = ImageDraw.Draw(img)
    y = TOP_SAFE + 640 * S
    for ln in ["One light-day", "from Earth"]:
        ctext(d, ln, f(88 * S, bold=True), FG, y)
        y += 104 * S
    ctext(d, "how far is that, really? →", f(34 * S), SEC, y + 24 * S)
    footer_handle(d)
    credit(d)
    return img


def ladder(idx, name, drawer, dist, time_big, note, with_credit=False):
    img, d = new_frame(10 + idx)
    header(d, f"LIGHT TRAVEL TIME · {idx}/4")
    drawer(img)
    d = ImageDraw.Draw(img)
    y = CY + 240 * S
    ctext(d, name, f(50 * S, bold=True), FG, y)
    ctext(d, time_big, f(112 * S, bold=True), ACC, y + 74 * S)
    ctext(d, dist, f(36 * S, bold=True), SEC, y + 226 * S)
    ctext_block(d, note, f(30 * S), SEC, y + 290 * S, 42 * S, W - 2 * M - 60 * S)
    ruler(d, idx)
    footer_handle(d)
    if with_credit:
        credit(d)
    return img


def frame_round_trip():
    img, d = new_frame(6)
    header(d, "WHY IT MATTERS")
    probe(img, W // 2, CY, 420 * S)
    d = ImageDraw.Draw(img)
    y = CY + 240 * S
    ctext(d, "One round trip", f(60 * S, bold=True), FG, y)
    ctext(d, "2 days", f(120 * S, bold=True), ACC, y + 76 * S)
    ctext_block(d, "Send a command, wait a day for it to arrive, a day for the reply. "
                   "The probe flies ~61,000 km/h - light is nearly 18,000× faster.",
                f(30 * S), SEC, y + 250 * S, 42 * S, W - 2 * M - 60 * S)
    ruler(d, 5)
    footer_handle(d)
    credit(d)
    return img


def frame_next():
    img, d = new_frame(7)
    header(d, "WHAT'S NEXT")
    probe(img, W // 2 - 260 * S, CY, 380 * S)
    d = ImageDraw.Draw(img)
    x0, x1 = W // 2 - 150 * S, W // 2 + 300 * S
    for i in range(0, 18, 2):
        d.line([x0 + (x1 - x0) * i / 18, CY, x0 + (x1 - x0) * (i + 1) / 18, CY], fill=HAIR, width=3 * S)
    blob(img, x1 + 40 * S, CY, 60 * S, 60 * S, (255, 236, 200), blur=30 * S, alpha=150)
    d = ImageDraw.Draw(img)
    d.ellipse([x1 + 24 * S, CY - 16 * S, x1 + 56 * S, CY + 16 * S], fill=(255, 250, 235))
    y = CY + 240 * S
    ctext(d, "Next stop: a star", f(58 * S, bold=True), FG, y)
    ctext(d, "17+ light-years away", f(58 * S, bold=True), ACC, y + 72 * S)
    ctext_block(d, "That's over 6,000 light-days. Voyager 1 passes within 1.7 light-years "
                   "of it in about 40,000 years.", f(30 * S), SEC, y + 190 * S, 42 * S,
                W - 2 * M - 60 * S)
    ruler(d, 6)
    footer_handle(d)
    credit(d)
    return img


def main():
    cx = W // 2
    frames = [
        frame_title(),
        ladder(1, "Earth → Moon", lambda im: sphere(im, cx, CY, 230, tex_moon(), (230, 220, 190)),
               "384,400 km", "1.3 seconds", "A signal to the Moon is practically instant."),
        ladder(2, "Earth → Sun", lambda im: sun(im, cx, CY, int(120 * S)),
               "149.6 million km", "8 min 20 s", "Sunlight is always a little over 8 minutes old."),
        ladder(3, "Earth → Neptune",
               lambda im: sphere(im, cx, CY, 210, tex_neptune(), (80, 110, 220)),
               "≈ 4.5 billion km", "4 h 10 min", "The outermost planet - Voyager 2 needed 12 years to get there."),
        ladder(4, "Earth → Voyager 1", lambda im: probe(im, cx, CY, 470 * S),
               "25.9 billion km", "24 hours", "One full light-day - the first human-made object to get this far.",
               with_credit=True),
        frame_round_trip(),
        frame_next(),
        frame_cta(("Follow for one", "every day")),
    ]
    finish(frames, OUT, "w4-voyager-light-day", cover_idx=4)


if __name__ == "__main__":
    main()
