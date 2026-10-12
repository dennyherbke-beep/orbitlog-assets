"""Woche 7 - Reel "Could you read a BOOK at noon on Pluto?" (Typ d absurde Frage; greift die
Kommentare unter w6-sun-from-planets auf: "Fuer Pluto ist das keine Sonne mehr, nur ein Stern").
Feste Kopfzeile, eine durchgehende Szene: Abendlandschaft auf der Erde, die Sonne geht unter, der
Himmel dunkelt ab, ein Helligkeitsmesser faellt - bis er die Mittagshelligkeit auf Pluto erreicht.
Dort friert das Bild ein: "This is NOON on Pluto". 15 s.

Fakten (NASA "Pluto Time" 2015; Helligkeit ~ 1/Abstand^2; Plutos Sonnenabstand 29,7-49,3 AU, 2026 ~35 AU):
  Sonnenlicht auf Pluto ~1/900 bis 1/2.400 des irdischen (2026 ~1/1.200) - mittags etwa so hell wie
  auf der Erde kurz nach Sonnenuntergang (NASA "Pluto Time"). Bei ~100.000 lux Mittagssonne auf der
  Erde sind das ~40-110 lux -> Lesen moeglich. Sonne von Pluto aus ~ -18,3 bis -19,4 mag, also
  170-470x heller als unser Vollmond (-12,7 mag) -> "hundreds of times". Kein Augenschutz-Thema im
  Reel (keine Aussage, ob man hineinschauen kann).

Hook-Varianten:
  1 "Could you read a BOOK at noon on Pluto?" (gewaehlt)   2 "This is what NOON looks like on Pluto"
  3 "Is the Sun from Pluto just another star?"   4 "Your daily 'Pluto Time' is tonight"
  5 "How dark is a day on Pluto?"

    python make-w7-pluto-noon-reel.py  ->  w7-pluto-noon.mp4, -cover.png
"""

import math
import os
import random
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, f, downscale
from bodies import star
from reelkit import new_frame, header_band, cinematic

OUT = Path(__file__).resolve().parent
W, H, FPS, DUR = 1080, 1920, 30, 15.0
SKY0, HOR = 560, 1330                             # Himmelsbereich (Ausgabe-px)
T_SET, T_PLUTO = 1.4, 9.0
DAY_TOP, DAY_HOR = np.array([58, 118, 200]), np.array([160, 200, 236])
DUSK_TOP, DUSK_HOR = np.array([22, 32, 72]), np.array([226, 128, 72])
BAR_X, BAR_Y0, BAR_Y1 = 960, 640, 1240            # Helligkeitsmesser (log, 100.000 -> 1 lux)
PLUTO_LUX = 82


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def lux_y(lux):
    return BAR_Y0 + (BAR_Y1 - BAR_Y0) * (5 - math.log10(lux)) / 5


def overlay_static():
    """Kopfzeile, Silhouette, Text unten - alles, was ueber dem Himmel liegt (RGBA)."""
    img, _ = new_frame(59)
    header_band(img, ["Could you read a BOOK", "at noon on Pluto?"], "BOOK")
    d = ImageDraw.Draw(img)
    rnd = random.Random(8)
    pts = [(0, H * S)]
    for i in range(41):
        pts.append((W * S * i / 40, (HOR + math.sin(i * 0.31) * 20 + rnd.uniform(-8, 8)) * S))
    pts.append((W * S, H * S))
    d.polygon(pts, fill=(4, 5, 8))
    for x in (W * 0.12, W * 0.24, W * 0.82):
        for k in range(4):
            w = (50 - k * 10) * S
            d.polygon([(x * S - w, (HOR - k * 36 + 10) * S), (x * S + w, (HOR - k * 36 + 10) * S),
                       (x * S, (HOR - (k + 1) * 36 - 14) * S)], fill=(4, 5, 8))
    for n, (txt, fo, col) in enumerate([("Send this to someone who still", f(34 * S, bold=True), FG),
                                        ("says Pluto is a planet", f(34 * S, bold=True), FG)]):
        d.text(((W * S - d.textlength(txt, font=fo)) / 2, (HOR + 110 + n * 48) * S), txt, font=fo, fill=col)
    img = downscale(img, W, H)
    alpha = Image.new("L", (W, H), 255)
    ImageDraw.Draw(alpha).rectangle([0, SKY0, W, HOR + 40], fill=0)     # Himmel bleibt frei
    sil = Image.new("L", (W, H), 0)                                      # Silhouette wieder deckend
    sd = ImageDraw.Draw(sil)
    sd.polygon([(x / S, y / S) for x, y in pts], fill=255)
    for x in (W * 0.12, W * 0.24, W * 0.82):
        for k in range(4):
            w = 50 - k * 10
            sd.polygon([(x - w, HOR - k * 36 + 10), (x + w, HOR - k * 36 + 10), (x, HOR - (k + 1) * 36 - 14)], fill=255)
    alpha = Image.fromarray(np.maximum(np.array(alpha), np.array(sil)))
    out = img.convert("RGBA")
    out.putalpha(alpha)
    return out


def sun_sprite():
    n = 220
    im = Image.new("RGB", (n * S, n * S), (0, 0, 0))
    star(im, n * S // 2, n * S // 2, 70, spots=False, corona=1.0)
    im = downscale(im, n, n)
    return im, im.convert("L").point(lambda p: min(255, int(p * 1.6)))


def sky(p):
    h = HOR + 40 - SKY0
    y = np.linspace(0, 1, h)[:, None] ** 1.4
    top = DAY_TOP + (DUSK_TOP - DAY_TOP) * p
    hor = DAY_HOR + (DUSK_HOR - DAY_HOR) * p
    g = top[None, None, :] * (1 - y[..., None]) + hor[None, None, :] * y[..., None]
    fade = np.clip(np.linspace(0, 1, h) / 0.16, 0, 1)[:, None, None]       # weicher Uebergang zur Kopfzeile
    g = np.array([11, 14, 20]) * (1 - fade) + g * fade
    g = np.repeat(g, W, axis=1)
    return Image.fromarray(g.astype(np.uint8), "RGB")


def frame(stat, sun, t):
    p = ease((t - T_SET) / (T_PLUTO - T_SET))
    im = Image.new("RGB", (W, H), (11, 14, 20))
    im.paste(sky(p), (0, SKY0))
    sy = 780 + min(p / 0.4, 1.2) * 560                                    # Sonne erreicht den Horizont bei p = 0,4
    im.paste(sun[0], (int(640 - sun[0].width / 2), int(sy - sun[0].height / 2)), sun[1])
    im = im.convert("RGBA")
    im.alpha_composite(stat)
    d = ImageDraw.Draw(im)
    st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
    if p < 0.4:                                                           # bis Sonnenuntergang nur ~1 Zehnerpotenz
        lg = 5 - p / 0.4
    else:                                                                 # danach steiler Abfall bis Pluto-Mittag
        lg = 4 - (4 - math.log10(PLUTO_LUX)) * (p - 0.4) / 0.6
    lux = 10 ** lg
    d.rounded_rectangle([BAR_X - 14, BAR_Y0, BAR_X + 14, BAR_Y1], 14, fill=(20, 24, 34), outline=(90, 96, 112), width=2)
    ly = lux_y(lux)
    d.rounded_rectangle([BAR_X - 9, ly, BAR_X + 9, BAR_Y1 - 5], 9, fill=ACC)
    py = lux_y(PLUTO_LUX)
    d.line([BAR_X - 40, py, BAR_X + 26, py], fill=FG, width=3)
    for n, ln in enumerate(["Noon on", "Pluto"]):
        fo = f(26, bold=True)
        d.text((BAR_X - 50 - d.textlength(ln, font=fo), py - 30 + n * 30), ln, font=fo, fill=FG, **st)
    fo = f(26, bold=True)
    d.text((BAR_X - 50 - d.textlength("Noon on Earth", font=fo), BAR_Y0 - 6), "Noon on Earth", font=fo, fill=FG, **st)
    d.text((BAR_X - d.textlength("light", font=f(22)) / 2, BAR_Y1 + 10), "light", font=f(22), fill=SEC, **st)
    if t < T_PLUTO:                                                       # Statuszeile waehrend der Daemmerung
        txt = "Noon on Earth" if t < T_SET + 0.3 else "Sunset... still too bright" if p < 0.45 else "Getting darker..."
        k = 1.0
        fo = f(46, bold=True)
        d.text(((W - d.textlength(txt, font=fo)) / 2 - 60, 880), txt, font=fo, fill=FG, **st)
    else:
        lines = [("This is NOON on Pluto", ACC, 58, T_PLUTO),
                 ("Yes - you could read a book.", FG, 40, T_PLUTO + 1.6),
                 ("The Sun there is still hundreds", FG, 34, T_PLUTO + 3.0),
                 ("of times brighter than our full Moon", FG, 34, T_PLUTO + 3.0)]
        ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
        d2 = ImageDraw.Draw(ov)
        y = 880
        for txt, col, size, t0 in lines:
            k = ease((t - t0) / 0.5)
            fo = f(size, bold=True)
            if k > 0:
                d2.text(((W - d2.textlength(txt, font=fo)) / 2 - 60, y), txt, font=fo, fill=col + (int(255 * k),),
                        stroke_width=3, stroke_fill=(8, 10, 14, int(255 * k)))
            y += size + 22
        im.alpha_composite(ov)
    return im.convert("RGB")


def main():
    stat = overlay_static()
    sun = sun_sprite()
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = OUT / "w7-pluto-noon.mp4"
    n = int(DUR * FPS)
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{DUR:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(stat, sun, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(stat, sun, 0.5), 0).save(OUT / "w7-pluto-noon-cover.png")
    chk = Path(os.environ.get("CHECK_DIR", OUT))
    cinematic(frame(stat, sun, 5.0), 0).save(chk / "_check-noon-mid.png")
    cinematic(frame(stat, sun, DUR - 0.1), 0).save(chk / "_check-noon-end.png")
    print(f"saved {out.name} ({DUR:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
