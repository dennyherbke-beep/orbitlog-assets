"""Woche 5, Sonntag - Reel "69 years ago today: Earth's first artificial moon" (Sputnik 1).
Anlass: 04.10.1957 Start von Sputnik 1; 04.-10.10. UN-Weltraumwoche. 8 Frames, 1080x1920,
Foto der Sputnik-1-Replik im National Air and Space Museum (NASA/NSSDC, gemeinfrei, Credit im
Bild, content/permission-log.md) + eigene Vektorgrafik (keine Flaggen/Hoheitszeichen - VERBOTE: Space-Race-Geschichte
nur sachlich, kein Wettlauf-Framing).

Fakten (NASA History "Sputnik and the Origins of the Space Age"; NSSDCA 1957-001B):
  Start 04.10.1957; polierte Metallkugel 58 cm Durchmesser, 83,6 kg, vier Stabantennen;
  Umlaufzeit ~96 min (~15 Umlaeufe/Tag, ~8 km/s = ~29.000 km/h; die Kugel selbst war kaum
  mit blossem Auge sichtbar - gesehen wurde meist die Raketenstufe, daher nicht behauptet); Funksignal (20,005 / 40,002 MHz) 21 Tage lang, bis die Batterien
  leer waren - weltweit von Funkamateuren empfangen; verglueht 04.01.1958 nach ~3 Monaten
  (~1.440 Umlaeufe laut NASA). UN-Weltraumwoche 4.-10.10. (1999 von der UN-Generalversammlung beschlossen, Res. 54/68, erinnert an Sputnik 1
  und das Inkrafttreten des Weltraumvertrags am 10.10.1967).

    python make-w5-sputnik-reel.py  ->  w5-sputnik-01..08.png, -cover.png, .mp4
"""

import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono
from bodies import planet
from reelkit import (W, H, M, TOP_SAFE, new_frame, header, footer_handle, ruler, ctext,
                     ctext_block, frame_save, sphere, blob, finish, TEX)

OUT = Path(__file__).resolve().parent
GY = TOP_SAFE + 400 * S
TY = TOP_SAFE + 800 * S


PHOTO = Image.open(OUT / "sputnik-replica-nssdc.jpg").convert("RGB")   # NASA/NSSDC, gemeinfrei
P_CX, P_CY, P_D = 865, 305, 375      # Kugelmitte und -durchmesser im Foto (px)
_CACHE = {}


def sputnik(img, cx, cy, d_px):
    """Foto der Sputnik-1-Replik (NASM, NASA/NSSDC) per Screen-Blend: der schwarze
    Fotohintergrund verschwindet im Marken-Hintergrund. Kugelmitte auf cx/cy, Kugel ~d_px breit."""
    k = d_px * S / P_D
    if k not in _CACHE:
        ph = PHOTO.resize((int(PHOTO.width * k), int(PHOTO.height * k)), Image.LANCZOS)
        m = Image.new("L", ph.size, 0)
        e = int(min(ph.size) * 0.06)
        ImageDraw.Draw(m).rectangle([e, e, ph.width - e, ph.height - e], fill=255)
        _CACHE[k] = (ph, m.filter(ImageFilter.GaussianBlur(e * 0.8)))
    ph, m = _CACHE[k]
    box = (int(cx - P_CX * k), int(cy - P_CY * k))
    region = img.crop((box[0], box[1], box[0] + ph.width, box[1] + ph.height))
    img.paste(ImageChops.screen(region, ph), box, m)


def credit(d):
    ctext(d, "Sputnik 1 replica (NASM) · photo: NASA/NSSDC", fmono(18 * S), SEC, H - 300 * S + 44 * S)


def orbit(img, cx, cy, rx, ry, col=HAIR):
    ImageDraw.Draw(img).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], outline=col, width=3 * S)


def tex_earth():
    img = Image.new("RGB", (TEX, TEX), (40, 90, 160))
    for x, y, rx, ry in [(175, 190, 85, 55), (330, 150, 55, 65), (245, 330, 70, 45)]:
        blob(img, x, y, rx, ry, (83, 122, 66), blur=9)
    for x, y, rx, ry in [(150, 130, 95, 30), (350, 250, 85, 26)]:
        blob(img, x, y, rx, ry, (255, 255, 255), blur=20, alpha=110)
    return img


def stat(d, label, big, sub, big_col=ACC):
    ctext(d, label, f(46 * S, bold=True), FG, TY)
    ctext(d, big, f(92 * S, bold=True), big_col, TY + 66 * S)
    ctext_block(d, sub, f(34 * S), SEC, TY + 196 * S, 46 * S, W - 2 * M - 40 * S)


def frame_title():
    img, d = new_frame(1)
    header(d, "OCT 4, 1957 · SPUTNIK 1")
    sputnik(img, W // 2 + 160 * S, TOP_SAFE + 310 * S, 260)
    d = ImageDraw.Draw(img)
    credit(d)
    y = TOP_SAFE + 800 * S
    ctext(d, "69 years ago today,", f(74 * S, bold=True), FG, y)
    ctext(d, "Earth got its first", f(74 * S, bold=True), FG, y + 90 * S)
    ctext(d, "artificial moon", f(74 * S, bold=True), ACC, y + 180 * S)
    footer_handle(d)
    return img


def frame_size():
    img, d = new_frame(2)
    header(d, "HOW BIG")
    sputnik(img, W // 2 + 150 * S, GY, 300)
    d = ImageDraw.Draw(img)
    credit(d)
    stat(d, "A polished metal ball", "58 cm across",
         "Smaller than a bicycle wheel, 83.6 kg - with four long radio antennas.")
    ruler(d, 1)
    footer_handle(d)
    return img


def frame_orbit():
    img, d = new_frame(3)
    header(d, "HOW FAST")
    cx, cy = W // 2, GY
    orbit(img, cx, cy, 330 * S, 150 * S, ACC)
    planet(img, cx, cy, 190, "earth")
    d = ImageDraw.Draw(img)
    sx, sy = cx + 330 * S * math.cos(math.radians(-35)), cy + 150 * S * math.sin(math.radians(-35))
    d.ellipse([sx - 10 * S, sy - 10 * S, sx + 10 * S, sy + 10 * S], fill=FG)
    stat(d, "Once around Earth every", "96 minutes",
         "About 15 laps a day - at roughly 29,000 km/h.")
    ruler(d, 2)
    footer_handle(d)
    return img


def frame_beep():
    img, d = new_frame(4)
    header(d, "WHAT IT DID")
    cx, cy = W // 2, GY
    sputnik(img, cx - 60 * S, cy, 190)
    d = ImageDraw.Draw(img)
    credit(d)
    for k in range(4):
        rr = (140 + k * 55) * S
        d.arc([cx - 60 * S - rr, cy - rr, cx - 60 * S + rr, cy + rr], -35, 35, fill=ACC, width=4 * S)
    stat(d, "It just went", "beep ... beep",
         "For 21 days, radio amateurs around the world could tune in - until its batteries ran out.")
    ruler(d, 3)
    footer_handle(d)
    return img


def frame_end():
    img, d = new_frame(5)
    header(d, "HOW IT ENDED")
    cx, cy = W // 2, GY
    blob(img, cx, cy, 130 * S, 40 * S, (255, 150, 70), blur=40 * S, alpha=150)
    blob(img, cx + 60 * S, cy, 50 * S, 22 * S, (255, 226, 170), blur=14 * S, alpha=230)
    stat(d, "Jan 4, 1958:", "it burned up",
         "After about three months and some 1,400 orbits, it fell back into the atmosphere.")
    ruler(d, 4)
    footer_handle(d)
    return img


def frame_since():
    img, d = new_frame(6)
    header(d, "69 YEARS LATER")
    y = GY - 150 * S
    for t, big in [("1957", "first satellite - 96 minutes around Earth"),
                   ("2026", "Voyager 1 nears one light-day from home")]:
        d.text((M + 20 * S, y), t, font=f(80 * S, bold=True), fill=ACC)
        d.text((M + 260 * S, y + 30 * S), big, font=f(34 * S), fill=FG)
        y += 200 * S
    stat(d, "From a beeping ball to", "interstellar space",
         "Today thousands of satellites orbit Earth - and it all started with this one.")
    ruler(d, 5)
    footer_handle(d)
    return img


def frame_week():
    img, d = new_frame(7)
    header(d, "OCT 4-10")
    sputnik(img, W // 2 + 110 * S, GY, 220)
    d = ImageDraw.Draw(img)
    credit(d)
    stat(d, "This week is", "World Space Week",
         "Declared by the UN in 1999 to mark Sputnik 1 and the Outer Space Treaty, which entered into force on Oct 10, 1967.")
    ruler(d, 6)
    footer_handle(d)
    return img


def main():
    frames = [
        frame_title(),
        frame_size(),
        frame_orbit(),
        frame_beep(),
        frame_end(),
        frame_since(),
        frame_week(),
        frame_save(("Save this", "for your next", "space trivia night")),
    ]
    finish(frames, OUT, "w5-sputnik", cover_idx=0)


if __name__ == "__main__":
    main()
