"""Woche 13, Mo 23.11.2026 - Experiment-Reel (Typ f, Loop, Regel 13: 10 s) "One lap around the galaxy = 230M years".
Face-on-Galaxie (stilisiert, Spiralarme aus make-w2-andromeda), die Sonne umrundet das Zentrum einmal pro Loop,
Zaehler 0 -> 230 Mio. Jahre. Am Ende ist die Sonne wieder am Start ("Last time: the first dinosaurs").
Fakten: Umlaufzeit der Sonne um das galaktische Zentrum ~225-250 Mio. Jahre (NASA/ESA, meist 230 genannt), Bahngeschwindigkeit
~220 km/s, Abstand ~26.000 Lichtjahre. Erste Dinosaurier: Spaetes Trias, vor ~230 Mio. Jahren. Menschenleben 80 J / 230 Mio. = 3,5e-7.
Darstellung: Spiralarme vereinfacht (Milchstrasse hat mehr Arme/Balken), Illustration, im Bild vermerkt.
Empfaenger (Regel 11): Humor - "someone who says 'where did the year go'".

Hook-Varianten: 1 "One lap around the galaxy = 230M YEARS" (gewaehlt) 2 "The Sun just finished lap #20" 3 "Last time we were HERE: dinosaurs"
4 "Where did the year go? Try 230M years" 5 "Your whole life = 0.00000035 of one lap"

    python make-w13-galactic-year-reel.py [--preview DIR]
"""
import importlib.util
import math
import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from brandkit import S, FG, SEC, ACC, f, downscale
from reelkit import new_frame, header_band, encode, cinematic, stext, ease

spec = importlib.util.spec_from_file_location("andro", HERE.parent / "w2-andromeda" / "make-w2-andromeda.py")
andro = importlib.util.module_from_spec(spec)
spec.loader.exec_module(andro)

NAME = "w13-galactic-year"
W, H, LOOP, FPS = 1080, 1920, 10.0, 30
CX, CY, GD = 540, 930, 980          # Galaxie-Mittelpunkt und Durchmesser
ORBIT_R = 300
SUN_COL = (255, 214, 110)


def background():
    img, _ = new_frame(73)
    header_band(img, ["One lap around the", "galaxy = 230M YEARS"], "230M YEARS")
    bg = downscale(img, W, H)
    sprite = andro.make_galaxy(900, seed=5).resize((GD, GD), Image.LANCZOS)
    halo = Image.new("L", (W, H), 0)
    ImageDraw.Draw(halo).ellipse([CX - GD * .5, CY - GD * .5, CX + GD * .5, CY + GD * .5], fill=70)
    halo = halo.filter(ImageFilter.GaussianBlur(120))
    bg.paste(Image.new("RGB", (W, H), (110, 130, 200)), (0, 0), halo)
    bg.paste(sprite, (CX - GD // 2, CY - GD // 2), sprite)
    d = ImageDraw.Draw(bg)
    for txt, fo, col, y in [("Simplified illustration of the Milky Way, seen from above", f(22), SEC, 1500),
                            ("Send this to someone who says \"where did the year go?\"", f(30, bold=True), FG, 1548),
                            ("Save it: your whole life = 0.00000035 of one lap", f(26), SEC, 1596)]:
        d.text(((W - d.textlength(txt, font=fo)) / 2, y), txt, font=fo, fill=col)
    return bg


BG = background()


def pos(u):
    a = -math.pi / 2 + 2 * math.pi * u          # Start oben, im Uhrzeigersinn (von Norden gesehen)
    return CX + ORBIT_R * math.cos(a), CY + ORBIT_R * math.sin(a)


def glow_dot(im, x, y, r, col):
    layer = Image.new("L", im.size, 0)
    ImageDraw.Draw(layer).ellipse([x - r * 3, y - r * 3, x + r * 3, y + r * 3], fill=150)
    layer = layer.filter(ImageFilter.GaussianBlur(r * 1.3))
    im.paste(Image.new("RGB", im.size, col), (0, 0), layer)
    ImageDraw.Draw(im).ellipse([x - r, y - r, x + r, y + r], fill=(255, 250, 225))


def frame(t):
    im = BG.copy()
    u = t / LOOP
    # Bahn: gestrichelter Kreis, bereits zurueckgelegter Teil heller
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    n = 180
    for i in range(n):
        if i % 2:
            continue
        a0 = -math.pi / 2 + 2 * math.pi * i / n
        a1 = -math.pi / 2 + 2 * math.pi * (i + 1) / n
        done = (i / n) < u
        od.line([(CX + ORBIT_R * math.cos(a0), CY + ORBIT_R * math.sin(a0)),
                 (CX + ORBIT_R * math.cos(a1), CY + ORBIT_R * math.sin(a1))],
                fill=(255, 214, 110, 230 if done else 90), width=5 if done else 3)
    im.paste(ov, (0, 0), ov)
    # Start-Geist
    sx, sy = pos(0)
    d = ImageDraw.Draw(im)
    d.ellipse([sx - 12, sy - 12, sx + 12, sy + 12], outline=(255, 214, 110), width=3)
    near_end = ease((u - 0.92) / 0.08)
    # Sonne
    x, y = pos(u)
    glow_dot(im, x, y, 13, SUN_COL)
    # Label
    if u < 0.5:
        a = 1.0 if u < 0.35 else 1 - (u - 0.35) / 0.15
        lx = min(max(x, 190), 890)
        stext(im, "YOU ARE HERE", 34, int(y - 84), fill=ACC, a=a, stroke=5, cx=lx)
        stext(im, "(the Sun)", 26, int(y - 46), fill=(235, 236, 240), a=a, bold=False, stroke=4, cx=lx)
    # Zaehler
    myr = int(230 * u)
    stext(im, f"+{myr} million years", 54, 1380, fill=SUN_COL, stroke=6)
    stext(im, "Sun speed: 220 km/s  ·  still 230M years per lap", 26, 1448, fill=SEC, bold=False, stroke=4)
    if near_end > 0:
        stext(im, "Back at the start. Last time: the first dinosaurs.", 34, 1318, fill=FG,
              a=near_end, stroke=6)
    return im


def main():
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (0.0, 3.0, 9.8):
            cinematic(frame(t), 0).save(prev / f"{NAME}-{t:04.1f}.png")
        return
    encode(HERE / f"{NAME}.mp4", frame, LOOP, fps=FPS)
    cinematic(frame(0.0), 0, grain_sigma=0).save(HERE / f"{NAME}-cover.png")


if __name__ == "__main__":
    main()
