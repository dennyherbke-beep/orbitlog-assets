"""Woche 8, Ersatz-Reel "Diese Woche am Himmel" (Termin + Handlung + Aha): Hunter's Moon 25./26.10.2026 und
die Mondtaeuschung - der aufgehende Mond wirkt riesig, ist aber genauso gross wie hoch am Himmel.

Hook-Varianten:
  1. Tonight's HUNTER'S MOON will look huge. It isn't.   <- gewaehlt (Termin + kontraintuitiv)
  2. The giant Moon on the horizon is a trick of your brain
  3. Your pinky can prove the Moon isn't bigger tonight
  4. Why does the rising Moon look so big?
  5. Watch the Moon rise tonight - then try this

Szene (14 s Loop): Blick nach Osten zur Daemmerung (Erdschattenband + rosa "Venusguertel"), Mond geht
orange am Horizont auf, steigt (Zeitraffer) und wird weiss, der Himmel wird dunkel. Danach Geisterkreis an der
Aufgangsstelle + Messklammern: beide Monde exakt gleich breit (im Bild bewusst gleich gross gezeichnet).
Mond vergroessert (im Bild vermerkt), Hoehe-Zeit-Zeitraffer gekennzeichnet.

Fakten: Vollmond 26.10.2026 04:11 UTC (Moongiant, Farmers' Almanac) -> Naechte 25./26. und 26./27. fast voll,
Aufgang um Sonnenuntergang im Osten. Mond ~0,5 Grad; der Mond am Horizont ist sogar ~1,5 % kleiner (man ist
etwa einen Erdradius weiter weg als beim hoch stehenden Mond). Kleiner Finger auf Armlaenge ~1 Grad -> deckt ihn
in beiden Faellen ab. Orange Farbe: Atmosphaere streut Blau heraus. Ursache der Taeuschung bis heute nicht
abschliessend geklaert (Vergleich mit Horizont-Objekten, "flaches Himmelsgewoelbe").

    python make-w8-moon-illusion-reel.py  ->  w8-moon-illusion.mp4, -cover.png
    CHECK_ONLY=1 CHECK_DIR=<dir>           ->  nur Kontroll-Frames
"""

import math
import os
import random
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, f, canvas, downscale
from bodies import planet
from reelkit import header_band, deep_sky, cinematic

OUT = Path(__file__).resolve().parent
W, H, FPS, LOOP = 1080, 1920, 30, 14.0
HOR = 1400
D = 150                                             # Monddurchmesser (Ausgabe-px), in beiden Positionen gleich
LOW, HIGH, BELOW = (310, HOR - 100), (740, 770), (310, HOR + 110)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def lerp(a, b, u):
    return tuple(p + (q - p) * u for p, q in zip(a, b))


def state(t):
    """Mondposition, Hoehe 0..1 (Farbe/Daemmerung) zum Zeitpunkt t; am Loop-Ende zurueck zum Aufgang."""
    rise = ease(t / 1.4)
    climb = ease((t - 3.2) / 2.4) * (1 - ease((t - 12.6) / 1.2))
    if t > 12.6:                                                      # zurueck: unter dem Horizont neu aufgehen
        u = ease((t - 12.6) / 1.2)
        return lerp(HIGH, BELOW, u) if u < 1 else BELOW, 1 - u
    pos = lerp(BELOW, LOW, rise)
    if climb > 0:                                                     # Bogen nach rechts oben (Mond zieht nach Sueden)
        x = LOW[0] + (HIGH[0] - LOW[0]) * climb
        y = LOW[1] + (HIGH[1] - LOW[1]) * math.sin(climb * math.pi / 2)
        pos = (x, y)
    return pos, climb


def sky_layers():
    W2, H2 = W * S, H * S
    yy = np.mgrid[0:H2, 0:1][0].astype(np.float32) / S
    h = np.clip((HOR - yy) / HOR, 0, 1)                              # 0 am Horizont, 1 oben
    # Daemmerung im Osten: blaugrauer Erdschatten direkt ueber dem Horizont, darueber rosa Venusguertel
    base = np.stack([30 + 40 * (1 - h), 44 + 40 * (1 - h), 82 + 40 * (1 - h)], -1)
    shadow = np.exp(-(((HOR - yy) - 60) / 70) ** 2)[..., None] * np.array([-8, -4, 10])
    belt = np.exp(-(((HOR - yy) - 230) / 110) ** 2)[..., None] * np.array([92, 46, 54])
    dusk = np.clip(np.repeat(base + shadow + belt, W2, axis=1), 0, 255).astype(np.uint8)
    dusk = Image.fromarray(dusk, "RGB")
    night, _ = canvas(W2, H2)
    deep_sky(night, 31, band=None)
    arr = np.asarray(night, np.float32) * 0.4                         # Vollmond ueberstrahlt die meisten Sterne
    moonlit = np.stack([12 + 14 * (1 - h), 17 + 18 * (1 - h), 32 + 26 * (1 - h)], -1)   # mondhelles Himmelsblau
    night = Image.fromarray(np.clip(arr + moonlit, 0, 255).astype(np.uint8), "RGB")
    return downscale(dusk, W, H), downscale(night, W, H)


def foreground():
    """Landschaft (Huegel, Baeume, Haeuser) + Kopfzeile + CTA als RGBA-Ebene ueber Himmel und Mond."""
    img = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rnd = random.Random(5)
    pts = [(0, H * S)]
    for i in range(61):
        x = W * i / 60
        y = HOR + 12 * math.sin(i * 0.31 + 1.2) + 6 * math.sin(i * 1.3) + rnd.uniform(-3, 3)
        pts.append((x * S, y * S))
    d.polygon(pts + [(W * S, H * S)], fill=(4, 5, 8, 255))
    for x, s in [(60, 1.0), (140, 0.75), (520, 0.8), (585, 1.05), (1010, 1.1)]:
        for k in range(5):
            wd = (44 - k * 8) * s
            yb = HOR - k * 30 * s + 12
            d.polygon([((x - wd) * S, yb * S), ((x + wd) * S, yb * S), (x * S, (yb - 46 * s) * S)], fill=(4, 5, 8, 255))
    for x0, w, h in [(690, 70, 54), (765, 96, 74), (870, 60, 46)]:       # Haeuser mit Fenstern
        d.rectangle([x0 * S, (HOR - h) * S, (x0 + w) * S, (HOR + 10) * S], fill=(4, 5, 8, 255))
        d.polygon([((x0 - 8) * S, (HOR - h) * S), ((x0 + w + 8) * S, (HOR - h) * S),
                   ((x0 + w / 2) * S, (HOR - h - 34) * S)], fill=(4, 5, 8, 255))
        d.rectangle([(x0 + w / 2 - 9) * S, (HOR - h + 14) * S, (x0 + w / 2 + 9) * S, (HOR - h + 32) * S],
                    fill=(150, 112, 56, 255))
    d.text((W / 2 * S - d.textlength("E", font=f(24 * S, bold=True)) / 2, (HOR + 18) * S), "E",
           font=f(24 * S, bold=True), fill=(130, 140, 160, 255))
    shade = Image.new("L", img.size, 0)                                 # Kopfzeile lesbar halten
    ImageDraw.Draw(shade).rectangle([0, 0, W * S, 560 * S], fill=130)
    shade = shade.filter(ImageFilter.GaussianBlur(60 * S))
    img.paste(Image.new("RGBA", img.size, (5, 7, 12, 255)), (0, 0), shade)
    head = Image.new("RGB", img.size, (0, 0, 0))
    y = header_band(head, ["Tonight's HUNTER'S MOON", "will look huge. It isn't."], "HUNTER'S MOON")
    d2 = ImageDraw.Draw(head)
    sub = "Full Moon · Sun Oct 25 + Mon Oct 26 · rises at sunset · look east"
    d2.text(((W * S - d2.textlength(sub, font=f(28 * S))) / 2, y + 6 * S), sub, font=f(28 * S), fill=SEC)
    note = "Moon enlarged · time sped up"
    d2.text((W * S - 30 * S - d2.textlength(note, font=f(20 * S)), (HOR - 190) * S), note, font=f(20 * S), fill=SEC)
    for n, (txt, fo, col) in enumerate([("Save this for tonight", f(40 * S, bold=True), FG),
                                        ("Send it to someone who swears it's bigger", f(32 * S), SEC)]):
        d2.text(((W * S - d2.textlength(txt, font=fo)) / 2, (HOR + 160 + n * 54) * S), txt, font=fo, fill=col)
    img.paste(head, (0, 0), head.convert("L").point(lambda p: 255 if p > 8 else p * 30))
    return img.resize((W, H), Image.LANCZOS)


def moon_sprite():
    pad = 30
    can = Image.new("RGB", ((D + 2 * pad) * S, (D + 2 * pad) * S), (0, 0, 0))
    planet(can, can.width // 2, can.height // 2, D, "moon", light=(0.06, -0.02, 1.0), glow=False)
    return np.asarray(downscale(can, D + 2 * pad, D + 2 * pad), np.float32)


DUSK, NIGHT = sky_layers()
FG_LAYER = foreground()
MOON = moon_sprite()
MASK = Image.fromarray(np.clip(MOON.max(axis=2) * 4, 0, 255).astype(np.uint8), "L")


def moon_img(h):
    """Tief: gedaempft und orange (Blau herausgestreut); hoch: hell und weiss."""
    tint = np.array([1.0, 0.70, 0.42]) * (1 - h) + np.array([1.0, 0.98, 0.94]) * h
    gain = 1.05 + 0.65 * h
    return Image.fromarray(np.clip(MOON * tint * gain, 0, 255).astype(np.uint8), "RGB")


def bracket(d, cx, cy, al, col):
    """Messklammer ueber dem Mond: exakt Monddurchmesser breit."""
    y = cy - D / 2 - 26
    x0, x1 = cx - D / 2, cx + D / 2
    c = col + (int(255 * al),)
    d.line([x0, y, x1, y], fill=c, width=4)
    d.line([x0, y - 14, x0, y + 14], fill=c, width=4)
    d.line([x1, y - 14, x1, y + 14], fill=c, width=4)
    for x in (x0, x1):                                               # gestrichelte Fuehrungslinien
        for yy in range(int(y + 18), int(cy), 14):
            d.line([x, yy, x, yy + 7], fill=col + (int(110 * al),), width=2)
    fo = f(26, bold=True)
    d.text((cx - d.textlength("0.5°", font=fo) / 2, y - 44), "0.5°", font=fo, fill=c,
           stroke_width=3, stroke_fill=(5, 6, 10, int(255 * al)))


def frame(t):
    (mx, my), h = state(t)
    dark = ease((t - 3.4) / 2.6) * (1 - ease((t - 12.6) / 1.2))
    im = Image.blend(DUSK, NIGHT, dark)
    glow = Image.new("L", (W, H), 0)                                  # Mondhof (hoch staerker)
    gd = ImageDraw.Draw(glow)
    for rr, a in ((D * 1.5, 26 + 30 * h), (D * 0.95, 40 + 50 * h)):
        gd.ellipse([mx - rr, my - rr, mx + rr, my + rr], fill=int(a))
    glow = glow.filter(ImageFilter.GaussianBlur(45))
    im.paste(Image.new("RGB", (W, H), tuple(int(c) for c in lerp((255, 170, 110), (200, 210, 235), h))), (0, 0), glow)
    im.paste(moon_img(h), (int(mx - MASK.width / 2), int(my - MASK.height / 2)), MASK)
    im = im.convert("RGBA")
    im.alpha_composite(FG_LAYER)
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    meas = ease((t - 6.0) / 0.5) * (1 - ease((t - 12.4) / 0.4))
    if meas > 0:
        gx, gy = LOW
        for k in range(48):                                           # Geisterkreis an der Aufgangsstelle
            a0 = k * 7.5
            d.arc([gx - D / 2, gy - D / 2, gx + D / 2, gy + D / 2], a0, a0 + 4, fill=(255, 196, 120, int(230 * meas)), width=4)
        bracket(d, gx, gy, meas, ACC)
        bracket(d, mx, my, meas, ACC)
    im.alpha_composite(ov)
    d = ImageDraw.Draw(im)
    lab = [("1 · At moonrise: it looks HUGE", 0.0, 3.2), ("2 · A few hours later: it looks small", 4.6, 6.0),
           ("3 · Measure it: exactly the same size", 6.0, 8.8), ("Your brain does this. Not the sky.", 8.8, 10.4),
           ("Test it: your pinky at arm's length covers both", 10.4, 12.4)]
    for txt, a, b in lab:
        al = ease((t - a) / 0.35) * (1 - ease((t - b) / 0.35))
        if a == 0.0:
            al = max(al, ease((t - 13.6) / 0.3))
        if al > 0:
            fo = f(40, bold=True)
            col = ACC if txt.startswith(("Your", "3", "Test")) else FG
            d.text(((W - d.textlength(txt, font=fo)) / 2, HOR + 64), txt, font=fo, fill=col + (int(255 * al),),
                   stroke_width=3, stroke_fill=(3, 4, 6, int(255 * al)))
    return im.convert("RGB")


def main():
    chk = Path(os.environ.get("CHECK_DIR", OUT))
    for t in (2.0, 5.2, 7.5, 11.4):
        cinematic(frame(t), 0).save(chk / f"_check-moon-illusion-{t:.1f}.png")
    if os.environ.get("CHECK_ONLY"):
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = OUT / "w8-moon-illusion.mp4"
    n = int(LOOP * FPS)
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart",
        str(out)], stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(2.0), 0).save(OUT / "w8-moon-illusion-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
