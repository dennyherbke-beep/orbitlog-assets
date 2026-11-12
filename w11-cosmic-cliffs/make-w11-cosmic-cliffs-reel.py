"""Woche 11, So 15.11.2026 - erstes "News-Card"-Reel nach dem Discover-Lauf vom 12.11.2026 (fromworldsbeyond_:
Webb-/Hubble-Bild + Meldungs-Hook "What looks like X is actually Y", 298x / 210x Median). Regel 9 (echtes Bild),
Regel 12 (provokanter Hook, korrekte Sache). Musik-Test 2: Denny postet per Handy-App mit Trend-Musik.

Bild: ESA/Webb weic2205a "Cosmic Cliffs" in Carina (NIRCam), Credit NASA, ESA, CSA, STScI (CC BY 4.0, Credit
sichtbar Pflicht), https://esawebb.org/images/weic2205a/ - lokal webb-weic2205a.jpg (14575 x 8441).

Hook-Varianten:
  1. These are NOT / mountains.                         <- gewaehlt (kurz, widerspricht dem ersten Eindruck)
  2. What looks like mountains is actually ...
  3. This is not Earth. This is 7,600 light-years away.
  4. Webb photographed a mountain range in space
  5. Your brain gets this photo wrong

Ablauf (19 s, feste Kopfzeile):
  0-5    Hochformat-Ausschnitt, langsamer Schwenk + Zoom ueber die "Gipfel"   "REAL IMAGE · James Webb ..."
  5-10.5 Zoom heraus auf das ganze Bild                                       "It's a wall of gas and dust" ...
  11-16  Zoom auf den Hauptkamm                                               7 Lichtjahre / Babysterne
  16-19  abgedunkelt, Save- + Send-CTA
Fakten (NASA/ESA-Bildtext): Rand einer Gaskavitaet in NGC 3324 (Carinanebel), ~7.600 Lichtjahre; hoechste
"Gipfel" ~7 Lichtjahre hoch; Infrarot zeigt zuvor verborgene Sternentstehung.

    python make-w11-cosmic-cliffs-reel.py        -> w11-cosmic-cliffs.mp4, -cover.png
    CHECK_ONLY=1 CHECK_DIR=<dir>                 -> nur Kontroll-Frames
"""

import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from brandkit import S, FG, SEC, ACC, f
from reelkit import header_band, cinematic, encode, stext, ease

Image.MAX_IMAGE_PIXELS = None
OUT = Path(__file__).resolve().parent
W, H, SECONDS = 1080, 1920, 19.0

src = Image.open(OUT / "webb-weic2205a.jpg").convert("RGB")
L0 = src.resize((round(src.width * 3840 / src.height), 3840), Image.LANCZOS)
LEVELS = [L0, L0.reduce(2), L0.reduce(4)]
del src
IW, IH = L0.size
K = IW / 1600                                     # Vorschau-Koordinaten (1600 breit) -> L0


def view(cx, cy, vw):
    """Ausschnitt (Mittelpunkt, Breite in L0-px, Hochformat 9:16) -> 1080x1920, ausserhalb schwarz."""
    vh = vw * H / W
    lvl = 0
    while lvl < 2 and vw / 2 ** (lvl + 1) >= W:   # Pyramide: Quelle nie mehr als 2x groesser als Ausgabe
        lvl += 1
    s = 2 ** lvl
    box = ((cx - vw / 2) / s, (cy - vh / 2) / s, (cx + vw / 2) / s, (cy + vh / 2) / s)
    return LEVELS[lvl].transform((W, H), Image.EXTENT, box, Image.BICUBIC, fillcolor=(0, 0, 0))


def lerp(a, b, u):
    return a + (b - a) * u


A0 = (330 * K, IH / 2, 2160.0)                    # Start: linker Gipfel, volle Hoehe
A1 = (560 * K, IH / 2 + 60, 1880.0)
B = (IW / 2, IH / 2, IW * 1.0)                    # ganzes Bild
C = (720 * K, 400 * K, 1500.0)                    # Hauptkamm (hellster Gipfel)


def camera(t):
    if t < 5:
        u = ease(t / 5)
        return [lerp(a, b, u) for a, b in zip(A0, A1)]
    if t < 9.5:
        u = ease((t - 5) / 4.5)
        cx, cy = lerp(A1[0], B[0], u), lerp(A1[1], B[1], u)
        vw = A1[2] * (B[2] / A1[2]) ** u          # Zoom geometrisch -> gleichmaessig
        return cx, cy, vw
    if t < 11:
        return B
    u = ease((t - 11) / 5)
    return lerp(B[0], C[0], u), lerp(B[1], C[1], u), B[2] * (C[2] / B[2]) ** u


def head_layer():
    """Kopfzeile + Credit als RGBA (einmal berechnet)."""
    can = Image.new("RGB", (W * S, H * S), (0, 0, 0))
    header_band(can, ["These are NOT", "mountains."], "NOT")
    d = ImageDraw.Draw(can)
    txt = "Image: NASA, ESA, CSA, STScI"
    d.text(((W * S - d.textlength(txt, font=f(24 * S))) / 2, 1590 * S), txt, font=f(24 * S), fill=SEC)
    lay = can.convert("RGBA")
    lay.putalpha(can.convert("L").point(lambda p: 255 if p > 8 else p * 30))
    return lay.resize((W, H), Image.LANCZOS)


HEAD = head_layer()
SHADE = Image.new("L", (W, H), 0)
ImageDraw.Draw(SHADE).rectangle([0, 0, W, 520], fill=150)
ImageDraw.Draw(SHADE).rectangle([0, 1380, W, H], fill=120)
SHADE = SHADE.filter(ImageFilter.GaussianBlur(70))

TEXTS = [  # (Zeile 1, Zeile 2, von, bis)
    ("REAL IMAGE", "James Webb Space Telescope", 0.4, 5.0),
    ("It's a wall of gas and dust", "7,600 light-years away, in the Carina Nebula", 5.6, 10.6),
    ("The tallest \"peak\": ~7 light-years high", "Light itself needs 7 years to climb it", 11.0, 13.6),
    ("Inside: stars being born right now", "Webb's infrared eyes see through the dust", 13.6, 16.1),
    ("Save it: a wallpaper from Webb", "Send this to someone who'd think it's Earth", 16.3, 19.5),
]


def frame(t):
    im = view(*camera(t))
    if t > 16:                                    # Endphase abdunkeln
        im = Image.blend(im, Image.new("RGB", (W, H), (4, 5, 9)), 0.45 * ease((t - 16) / 0.6))
    im.paste((5, 7, 12), (0, 0), SHADE)
    im = im.convert("RGBA")
    im.alpha_composite(HEAD)
    im = im.convert("RGB")
    for l1, l2, a, b in TEXTS:
        al = ease((t - a) / 0.35) * (1 - ease((t - b + 0.3) / 0.3))
        if al > 0:
            col = ACC if a in (0.4, 16.3) else FG
            stext(im, l1, 46, 1430, col, al)
            stext(im, l2, 32, 1500, SEC, al, bold=False)
    return im


def main():
    chk = Path(os.environ.get("CHECK_DIR", OUT))
    for t in (0.0, 2.5, 7.5, 10.2, 12.5, 15.0, 18.0):
        cinematic(frame(t), 0).save(chk / f"_check-cliffs-{t:04.1f}.png")
    if os.environ.get("CHECK_ONLY"):
        return
    encode(OUT / "w11-cosmic-cliffs.mp4", frame, SECONDS)
    cinematic(frame(2.5), 0, grain_sigma=0).save(OUT / "w11-cosmic-cliffs-cover.png")


if __name__ == "__main__":
    main()
