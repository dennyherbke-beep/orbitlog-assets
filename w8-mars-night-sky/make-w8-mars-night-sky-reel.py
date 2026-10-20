"""Woche 8, Sa 24.10.2026 - erstes Remake nach Regel 6 (docs/reel-algorithmus.md): Vorbild "Sky at Night on
Mars" (echoesofunboundcuriosity, instagram.com/reel/DbWPjm4I_N7, 978K Likes / 23,8K Reposts). Uebernommen: Thema
+ Hook-Struktur. Eigen: komplette Grafik, eigener Twist (Erde ist gerade Abendstern des Mars), korrigierte Fakten
(das Vorbild behauptet "no atmosphere" - Mars hat eine duenne Atmosphaere, daher auch der blaue Sonnenuntergang).

Hook-Varianten:
  1. The night sky on MARS / Find the blue star.          <- gewaehlt (Vorbild-Hook + Suchauftrag)
  2. On Mars, EARTH is the evening star
  3. Mars has no light pollution. This is its sky.
  4. Sunsets on Mars are blue. Then this happens.
  5. Look up on Mars tonight - that blue dot is us

Szene (15 s Loop), Blick nach Westen kurz nach Sonnenuntergang:
  0-3,5 s  blaue Daemmerung verblasst, Sterne + Milchstrasse kommen       "1 · Sunset on Mars glows blue"
  3,5-7,5  Erde markiert                                                   "2 · That blue 'star' is Earth"
  7,5-10,5 Fernglas-Einblick: Erde (62 % beleuchtet) + Mond                "3 · Binoculars: Earth and our Moon"
  10,5-13,5 Phobos steigt im Westen auf (beschleunigt, vergroessert)       "4 · Phobos rises in the WEST"
  13,5-15  Daemmerung kehrt zurueck (Loop)

Fakten:
  JPL Horizons, Beobachter Marsmittelpunkt (500@499), 24.10.2026 00:00 UTC (abgerufen 20.10.2026):
    Erde -2,0 mag, Elongation 37,5 Grad oestlich der Sonne ("/T" = Abendhimmel), Phasenwinkel 76 Grad
    (-> 62 % beleuchtet), 1,50 AE. Mond +3,2 mag, 4,3' von der Erde (RA 21h08m22s/-17d56' vs. 21h08m06s/-17d58').
    Erde bleibt Abendstern bis zur unteren Konjunktion (Marsopposition Feb. 2027).
  Blaue Sonnenuntergaenge: NASA/JPL Curiosity, Gale-Krater, Sol 956 (2015) - Staub streut Blau nahe der Sonne.
  Phobos: Umlauf 7 h 39 min < Marstag -> geht im Westen auf, im Osten unter; scheinbar ~1/3 Monddurchmesser.
  Atmosphaere ~1 % des Erddrucks; keine Lichtverschmutzung. Hier vereinfacht: Himmel bleibt waehrend der
  Phobos-Sequenz stehen (Zeitraffer nur fuer Phobos, im Bild vermerkt).

    python make-w8-mars-night-sky-reel.py  ->  w8-mars-night-sky.mp4, -cover.png
    CHECK_ONLY=1 CHECK_DIR=<dir>           ->  nur Kontroll-Frames
"""

import importlib.util
import math
import os
import random
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from brandkit import S, FG, SEC, ACC, f, downscale, canvas
from reelkit import header_band, deep_sky, cinematic
from bodies import planet, asteroid, fbm

_spec = importlib.util.spec_from_file_location("andro", ROOT / "w6-andromeda-weekend" / "make-w6-andromeda-weekend-loop.py")
A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(A)

OUT = Path(__file__).resolve().parent
W, H, FPS, LOOP = 1080, 1920, 30, 15.0
HOR = 1400                                          # Horizont (Ausgabe-px)
PX_DEG = 20                                         # Bildmassstab am Himmel
SUN = (700, HOR + 100)                              # Sonne ~5 Grad unter dem Horizont
ECL = math.radians(58)                              # Neigung der Ekliptik gegen den Horizont (Bildannahme)
EARTH = (SUN[0] - 37.5 * PX_DEG * math.cos(ECL), SUN[1] - 37.5 * PX_DEG * math.sin(ECL))
EARTH_COL = (168, 202, 255)
PHOBOS_X = 420


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def twilight(t):
    """1 = helle Daemmerung, 0 = Nacht. Faellt am Anfang, steigt am Loop-Ende wieder an."""
    return 1 - ease(t / 3.2) + ease((t - 13.6) / 1.4)


def sky_glow(strength):
    """Marsdaemmerung (Ausgabe-px, float): blauer Kern um die Sonne, darum butterscotch, oben dunkel."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt((xx - SUN[0]) ** 2 + ((yy - SUN[1]) * 1.35) ** 2)
    blue = np.exp(-r / 270)[..., None] * np.array([120, 170, 245])
    tan = np.exp(-r / 720)[..., None] * np.array([96, 66, 46])
    up = np.clip((HOR - yy) / HOR, 0, 1)[..., None]
    return (blue + tan * (1 - 0.5 * up)) * strength


def milky_way(img):
    """Kraeftige Milchstrasse diagonal (links unten -> rechts oben) mit Staubbahnen, warmem Kern nahe dem
    Horizont und dichtem Sternfeld im Band. Arbeitet auf der Supersampling-Leinwand."""
    w, h = W // 2, H // 2
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ang = math.radians(-62)
    dist = (xx - w * 0.30) * math.sin(ang) - (yy - h * 0.62) * math.cos(ang)  # Abstand zur Bandachse
    along = (xx - w * 0.30) * math.cos(ang) + (yy - h * 0.62) * math.sin(ang)
    n1 = fbm(31, h, w, octaves=7, base=5, wrap=False)
    n2 = fbm(32, h, w, octaves=7, base=9, wrap=False)
    core = np.exp(-(dist / (78 + 18 * n1)) ** 2)
    lanes = 1 - 0.8 * np.clip((n2 - 0.48) * 4, 0, 1) * np.exp(-(dist / 40) ** 2)   # Staubbahnen in der Mitte
    warm = np.clip(0.5 - along / 900, 0, 1)                                       # Kern (Sagittarius) warm
    lum = core * (0.35 + 0.9 * n1) * lanes * 80
    rgb = lum[..., None] * (np.array([0.80, 0.84, 1.0]) * (1 - warm[..., None]) + np.array([1.0, 0.86, 0.68]) * warm[..., None])
    lay = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).resize(img.size, Image.BICUBIC)
    img.paste(ImageChops.add(img, lay))
    rng = np.random.default_rng(33)                                               # dichtes Sternfeld im Band
    d = ImageDraw.Draw(img)
    for _ in range(9000):
        x, y = rng.uniform(0, w), rng.uniform(0, h)
        if core[int(y), int(x)] < rng.random():
            continue
        b = rng.random() ** 4
        r = (0.35 + 0.7 * b) * S
        c = int(120 + 120 * b)
        d.ellipse([x * 2 * S - r, y * 2 * S - r, x * 2 * S + r, y * 2 * S + r], fill=(c, c, min(255, c + 12)))


def rock(img, x, y, size, seed, dusk):
    """Halb eingesunkener Felsblock aus dem Asteroiden-Renderer (Streiflicht von der Sonnenseite)."""
    d = int(size) + 8
    can = Image.new("RGB", (d * S, d * S), (0, 0, 0))
    tone = tuple(int(c) for c in np.array([60, 40, 30]) + dusk * np.array([90, 60, 42]))
    asteroid(can, can.width // 2, can.height // 2, size, seed=seed, rot=seed * 37 % 360,
             light=(0.55 if x < SUN[0] else -0.55, -0.45, 0.55), color=tone)
    m = can.convert("L").point(lambda p: 255 if p > 2 else 0)
    ImageDraw.Draw(m).rectangle([0, int(can.height * 0.62), can.width, can.height], fill=0)  # unten im Sand
    sh = Image.new("L", img.size, 0)                                              # Schatten auf dem Boden
    ImageDraw.Draw(sh).ellipse([(x - size * 0.7) * S, (y + size * 0.02) * S, (x + size * 0.8) * S,
                                (y + size * 0.16) * S], fill=150)
    img.paste((4, 3, 3, 255), (0, 0), sh.filter(ImageFilter.GaussianBlur(size * 0.08 * S)))
    img.paste(can, (int((x - d / 2) * S), int((y - d * 0.62) * S)), m)


def ground(dusk):
    """Marsboden auf Supersampling-Leinwand (RGBA): ferner Kraterrand links, Duenen, Felsbloecke,
    Staubtextur. dusk 0..1 hellt den Boden mit Daemmerungslicht von der Sonnenseite auf."""
    w, h = W * S, H * S
    rnd = random.Random(11)
    xs = np.arange(w) / S
    prof = (HOR + 6 * np.sin(xs / 61) + 4 * np.sin(xs / 23 + 1)
            - 70 * np.exp(-((xs - 190) / 170) ** 2) - 26 * np.exp(-((xs - 920) / 120) ** 2))  # Kraterrand / Huegel
    yy = np.arange(h)[:, None] / S
    mask = (yy >= prof[None, :]).astype(np.float32)
    n1 = np.asarray(Image.fromarray((fbm(5, h // 8, w // 8, octaves=6, base=6, wrap=False) * 255).astype(np.uint8))
                    .resize((w, h), Image.BICUBIC), np.float32) / 255
    depth = np.clip((yy - prof[None, :]) / 520, 0, 1)                         # 0 = Horizont, 1 = vorn
    dune = 0.5 + 0.5 * np.sin(xs[None, :] / 37 + yy / 9 + 3 * n1)              # Duenenrippel
    base = np.array([22, 13, 9]) + dusk * np.array([66, 40, 27])
    k = (0.55 + 0.6 * n1 + 0.18 * dune * depth) * (1 - 0.55 * depth)
    side = np.exp(-np.abs(xs[None, :] - SUN[0]) / 420) * (1 - depth) * dusk    # Streiflicht zur Sonne hin
    rgb = base[None, None, :] * k[..., None] + side[..., None] * np.array([40, 46, 58])
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA")
    img.putalpha(Image.fromarray((mask * 255).astype(np.uint8)))
    img = img.filter(ImageFilter.GaussianBlur(0.6 * S))
    for i in range(22):                                                       # Felsbloecke, vorn groesser
        y = rnd.uniform(1650, H - 20) if i > 4 else rnd.uniform(HOR + 20, HOR + 60)   # Textzone frei
        sc = (y - HOR) / (H - HOR)
        rock(img, rnd.uniform(-20, W + 20), y, (12 + 190 * sc ** 2) * rnd.uniform(0.6, 1.2), i + 3, dusk)
    return img


def background(dusk):
    """Komplettes Standbild ohne Erde/Phobos/Beschriftung. dusk 0 = Nacht, 1 = Daemmerung."""
    img, _ = canvas(W * S, H * S)
    if dusk < 1:
        deep_sky(img, 27, n=9000, band=None)                                  # dunkler als jeder Ort auf der Erde
        milky_way(img)
    arr = np.asarray(img, np.float32) * (1 - 0.88 * dusk)
    glow = np.asarray(Image.fromarray(np.clip(sky_glow(1.0), 0, 255).astype(np.uint8)).resize(img.size, Image.BICUBIC),
                      np.float32)
    arr = arr + glow * (0.06 + 0.94 * dusk)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    g = ground(dusk)
    img.paste(g, (0, 0), g)
    shade = Image.new("L", img.size, 0)                                       # Kopfzeile lesbar halten
    ImageDraw.Draw(shade).rectangle([0, 0, W * S, 540 * S], fill=130)
    img.paste(Image.new("RGB", img.size, (5, 7, 12)), (0, 0), shade.filter(ImageFilter.GaussianBlur(60 * S)))
    y = header_band(img, ["The night sky on MARS", "Find the blue star."], "MARS")
    d = ImageDraw.Draw(img)
    sub = "No light pollution anywhere on the planet"
    d.text(((W * S - d.textlength(sub, font=f(30 * S))) / 2, y + 6 * S), sub, font=f(30 * S), fill=SEC)
    for n, (txt, fo, col) in enumerate([("Save this for your next clear night", f(38 * S, bold=True), FG),
                                        ("Send it to someone who'd move to Mars", f(30 * S), SEC)]):
        d.text(((W * S - d.textlength(txt, font=fo)) / 2, (1540 + n * 50) * S), txt, font=fo, fill=col)
    return downscale(img, W, H)


def binocular_view(r=150):
    """Fernglas-Einblick: Erde 62 % beleuchtet (Phasenwinkel 76 Grad, Sonne rechts unten) + Mond oberhalb links."""
    can = Image.new("RGB", (2 * r * S, 2 * r * S), (3, 4, 8))
    sx, sy = math.cos(ECL), math.sin(ECL)                                      # Richtung zur Sonne im Bild
    ph = math.radians(76)
    light = (sx * math.sin(ph), sy * math.sin(ph), math.cos(ph))
    planet(can, int(r * 1.12 * S), int(r * 1.10 * S), 104, "earth", light=light, lon0=250)
    planet(can, int(r * 0.48 * S), int(r * 0.62 * S), 28, "moon", light=light)
    view = downscale(can, 2 * r, 2 * r)
    m = Image.new("L", (8 * r, 8 * r), 0)
    ImageDraw.Draw(m).ellipse([0, 0, 8 * r - 1, 8 * r - 1], fill=255)
    return view, m.resize((2 * r, 2 * r), Image.LANCZOS)


def phobos_sprite(d=96):
    """Phobos als schmale Sichel: Sonne unter dem Westhorizont -> Licht streifend von unten rechts."""
    can = Image.new("RGB", ((d + 40) * S, (d + 40) * S), (0, 0, 0))
    asteroid(can, can.width // 2, can.height // 2, d, seed=8, rot=0, light=(0.35, 0.92, 0.30), color=(160, 146, 130))
    spr = downscale(can, d + 40, d + 40)
    return spr, spr.convert("L").point(lambda p: min(255, p * 4))


BINO, BINO_MASK = binocular_view()
PHOBOS, PHOBOS_MASK = phobos_sprite()


def label(d, txt, x, y, al, col=FG, size=30, anchor="l"):
    fo = f(size, bold=True)
    if anchor == "c":
        x -= d.textlength(txt, font=fo) / 2
    elif anchor == "r":
        x -= d.textlength(txt, font=fo)
    d.text((x, y), txt, font=fo, fill=col + (int(255 * al),), stroke_width=3, stroke_fill=(5, 6, 10, int(255 * al)))


def frame(bg_night, bg_dusk, t):
    tw = twilight(t)
    im = Image.blend(bg_night, bg_dusk, tw)
    ex, ey = EARTH
    A.bright_star(im, ex, ey, -2.0 + 2.5 * tw, EARTH_COL, k=0.6)            # in heller Daemmerung schwaecher
    ph = ease((t - 10.5) / 0.4) * (1 - ease((t - 13.5) / 0.4))
    if ph > 0:                                                                # Phobos steigt im Westen auf
        u = min(1.0, max(0.0, (t - 10.4) / 3.2))
        px, py = PHOBOS_X - 120 * u, HOR + 20 - 470 * u
        clip = Image.new("L", (W, H), 0)                                      # hinter dem Horizont verdeckt
        ImageDraw.Draw(clip).rectangle([0, 0, W, HOR - 4], fill=255)
        layer = Image.new("L", (W, H), 0)
        layer.paste(PHOBOS_MASK.point(lambda p: int(p * ph)), (int(px - PHOBOS.width / 2), int(py - PHOBOS.height / 2)))
        sprite = Image.new("RGB", (W, H), 0)
        sprite.paste(PHOBOS, (int(px - PHOBOS.width / 2), int(py - PHOBOS.height / 2)))
        im.paste(sprite, (0, 0), ImageChops.multiply(layer, clip))
    im = im.convert("RGBA")
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    mark = ease((t - 3.6) / 0.4) * (1 - ease((t - 10.4) / 0.4))
    if mark > 0:                                                              # Erde markieren
        r = 30 + 4 * math.sin(t * 4)
        d.ellipse([ex - r, ey - r, ex + r, ey + r], outline=ACC + (int(255 * mark),), width=3)
        label(d, "Earth", ex + r + 14, ey - 34, mark, ACC, 34)
        label(d, "that's us", ex + r + 14, ey + 4, mark, SEC, 26)
    sun = ease((t - 0.2) / 0.4) * (1 - ease((t - 3.4) / 0.4))
    if sun > 0:
        label(d, "Sun just set here", SUN[0], HOR - 52, sun, SEC, 26, "c")
    ins = ease((t - 7.5) / 0.5) * (1 - ease((t - 10.4) / 0.4))
    if ins > 0:                                                               # Fernglas-Einblick
        cx, cy, R = 770, 820, BINO.width // 2
        d.line([ex + 26, ey - 8, cx - R * 0.96, cy - R * 0.2], fill=ACC + (int(160 * ins),), width=2)
        im.alpha_composite(ov)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(ov)
        im.paste(BINO, (cx - R, cy - R), BINO_MASK.point(lambda p: int(p * ins)))
        d.ellipse([cx - R - 3, cy - R - 3, cx + R + 3, cy + R + 3], outline=(150, 160, 185, int(255 * ins)), width=5)
        label(d, "Moon", cx - R * 0.62, cy - R * 0.62, ins, FG, 24, "c")
        label(d, "Earth", cx + R * 0.12, cy + R * 0.62, ins, FG, 24, "c")
        label(d, "binocular view · both enlarged", cx, cy + R + 14, ins, SEC, 22, "c")
    if ph > 0:
        u = min(1.0, max(0.0, (t - 10.4) / 3.2))
        px, py = PHOBOS_X - 120 * u, HOR + 20 - 470 * u
        label(d, "Phobos", px + 70, py - 40, ph, ACC, 30)
        label(d, "sped up + enlarged", px + 70, py - 2, ph, SEC, 22)
        if u > 0.12:                                                          # Spur vom Aufgangspunkt
            d.line([PHOBOS_X + 4, HOR - 8, px + 10, py + 62], fill=ACC + (int(170 * ph),), width=3)
    im.alpha_composite(ov)
    d = ImageDraw.Draw(im)
    lab = [("1 · Sunset on Mars glows blue", -1.0, 3.5),
           ("2 · That blue \"star\" is Earth", 3.5, 7.5),
           ("3 · Binoculars: Earth and our Moon", 7.5, 10.5),
           ("4 · Phobos rises in the WEST", 10.5, 13.5),
           ("1 · Sunset on Mars glows blue", 13.5, 16.0)]
    for txt, a, b in lab:
        al = ease((t - a) / 0.35) * (1 - ease((t - b) / 0.35))
        if al > 0:
            fo = f(40, bold=True)
            col = ACC if "Earth" in txt else FG
            d.text(((W - d.textlength(txt, font=fo)) / 2, HOR + 44), txt, font=fo, fill=col + (int(255 * al),),
                   stroke_width=3, stroke_fill=(3, 4, 6, int(255 * al)))
    if 3.5 < t < 7.5:
        al = ease((t - 3.9) / 0.4) * (1 - ease((t - 7.2) / 0.3))
        sub = "Right now Earth is Mars' evening star"
        d.text(((W - d.textlength(sub, font=f(28))) / 2, HOR + 98), sub, font=f(28), fill=SEC + (int(255 * al),))
    return im.convert("RGB")


def main():
    bg_night, bg_dusk = background(0.0), background(1.0)
    chk = Path(os.environ.get("CHECK_DIR", OUT))
    for t in (0.5, 5.5, 9.0, 12.4):
        cinematic(frame(bg_night, bg_dusk, t), 0).save(chk / f"_check-mars-{t:.1f}.png")
    if os.environ.get("CHECK_ONLY"):
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = OUT / "w8-mars-night-sky.mp4"
    n = int(LOOP * FPS)
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart",
        str(out)], stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg_night, bg_dusk, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg_night, bg_dusk, 5.5), 0).save(OUT / "w8-mars-night-sky-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
