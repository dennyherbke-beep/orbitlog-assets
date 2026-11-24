"""Woche 13, Sa 28.11.2026 - Typ f/a "Jupiter's giant storm is SHRINKING" (10-s-Loop, Regel 13).
Jupiter (Karte) im Massstab, darauf der Grosse Rote Fleck als Ellipse, die von ~1880 bis 2017 schrumpft; daneben
Erd-Kugeln im selben Massstab als Zaehleinheit.

Fakten (NASA/Hubble, NASA Juno): Fleckbreite spaetes 19. Jh. grob ~40.000 km (Schaetzung aus Beobachtungen), 1979 Voyager
~23.300 km, 2017 ~16.350 km (Hubble/Juno, ~1,3 Erddurchmesser; Erde 12.742 km). Jupiter-Durchmesser 139.822 km (mittl.).
Die Schrumpfung verlangsamt sich zuletzt; Ursache nicht abschliessend geklaert -> im Reel nicht erklaert.
Massstab Reel: Jupiter 640 px -> 1 px = 218 km; Erde 58 px.

Hook-Varianten: 1 "Jupiter's giant storm is SHRINKING" (gewaehlt) 2 "The Great Red Spot was 3 Earths wide"
3 "Earth used to fit in Jupiter's storm 3 times" 4 "Will the Great Red Spot disappear?" 5 "A 350-year-old storm is fading"
    python make-w13-red-spot-reel.py [--preview DIR]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import ACC, FG, SEC
from reelkit import header_bg, encode, cinematic, stext, ease, body_sprite, paste_center

OUT = Path(__file__).resolve().parent
NAME = "w13-red-spot"
W, H, LOOP = 1080, 1920, 10.0
JD, JX, JY = 640, 540, 880
KM_PX = 139822 / JD
EARTH_KM = 12742
SPR_J = body_sprite("jupiter", JD, lon0=40)
SPR_E = body_sprite("earth", EARTH_KM / KM_PX * 1.0, lon0=200)
BG = header_bg(101, ["Jupiter's giant storm", "is SHRINKING"], "SHRINKING")
KEYS = [(1880, 40000), (1979, 23300), (2017, 16350)]


def width_km(year):
    return float(np.interp(year, [k[0] for k in KEYS], [k[1] for k in KEYS]))


def year_at(t):
    return 1880 + (2017 - 1880) * ease((t - 0.8) / 6.6)


def spot(w_px, h_px):
    """Roter Sturm als weich auslaufende Ellipse mit Wirbelstruktur."""
    pad = 20
    im = Image.new("RGBA", (int(w_px) + 2 * pad, int(h_px) + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    box = [pad, pad, pad + w_px, pad + h_px]
    d.ellipse(box, fill=(160, 64, 40, 215))
    for i, c in enumerate([(190, 88, 56), (170, 70, 44), (200, 104, 68)]):
        s = 0.18 * (i + 1)
        d.ellipse([pad + w_px * s / 2, pad + h_px * s / 2, pad + w_px * (1 - s / 2), pad + h_px * (1 - s / 2)],
                  outline=c + (150,), width=max(1, int(h_px * 0.06)))
    return im.filter(ImageFilter.GaussianBlur(max(1.0, h_px * 0.04)))


def frame(t):
    im = BG.copy()
    yr = year_at(t)
    wk = width_km(yr)
    w_px = wk / KM_PX
    hide = ease((t - 9.2) / 0.6)                                      # Loop-Reset: Fleck blendet kurz aus
    paste_center(im, SPR_J, JX, JY)
    sp = spot(w_px, w_px * 0.68)
    # Fleck unterhalb des Aequators (ca. 22 Grad Sued), Mitte der sichtbaren Scheibe leicht links
    cx, cy = JX - 30, JY + 105
    if hide < 0.99:
        layer = im.copy()
        layer.paste(sp, (int(cx - sp.width / 2), int(cy - sp.height / 2)), sp)
        im = Image.blend(layer, im, hide) if hide > 0.01 else layer
    # Erd-Reihe als Zaehleinheit
    ry = JY + JD // 2 + 50
    n = wk / EARTH_KM
    ed = EARTH_KM / KM_PX
    x0 = JX - (3.2 * ed) / 2
    full = int(n)
    for i in range(full):
        paste_center(im, SPR_E, x0 + (i + 0.5) * ed, ry)
    frac = n - full
    if frac > 0.03:                                                   # Rest als Teil-Erde (links abgeschnitten)
        rgb, m = SPR_E
        l = int((rgb.width - ed) / 2)
        r = l + int(ed * frac)
        im.paste(rgb.crop((l, 0, r, rgb.height)), (int(x0 + full * ed), int(ry - rgb.height / 2)), m.crop((l, 0, r, rgb.height)))
    stext(im, f"{n:.1f} Earths wide", 50, ry + 44, ACC)
    stext(im, f"{int(round(yr))}", 64, ry + 112, FG)
    stext(im, f"Great Red Spot: ~{int(round(wk, -2)):,} km".replace(",", ","), 32, ry + 192, SEC, bold=False)
    stext(im, "1880s width is an estimate · Illustration, to scale · NASA/Hubble, Juno", 20, 1520, SEC, bold=False, stroke=3)
    stext(im, "Send this to someone who thinks space never changes", 30, 1560, FG)
    stext(im, "Save it: Jupiter's storm went from 3 Earths wide to 1.3", 24, 1606, SEC, bold=False, stroke=3)
    return im


def main():
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1]); prev.mkdir(parents=True, exist_ok=True)
        for t in (0.0, 4.0, 8.0):
            cinematic(frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        print("preview saved"); return
    encode(OUT / f"{NAME}.mp4", frame, LOOP)
    cinematic(frame(8.0), 0, grain_sigma=0).save(OUT / f"{NAME}-cover.png")


if __name__ == "__main__":
    main()
