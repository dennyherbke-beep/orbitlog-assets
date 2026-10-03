"""Woche 6, Dienstag - Rennen-Reel "Travel time to MARS at 6 different speeds" (Typ a,
docs/reel-algorithmus.md). Eine durchgehende Animation: 6 Bahnen Erde -> Mars, eine logarithmisch
laufende Uhr, jede Ankunft blendet die Reisezeit ein. ~16 s.

Fakten (NASA Mars Facts, NASA Parker Solar Probe, NASA ISS Facts):
  Mittlere Entfernung Erde-Mars ~225 Mio. km (naechste Annaeherung ~55 Mio., maximal ~400 Mio.).
  Gerade Linie, konstante Geschwindigkeit (echte Missionen fliegen Bahnboegen, ~7 Monate) -> first_comment.
  Zu Fuss 5 km/h -> 45 Mio. h = ~5.100 Jahre · Auto 100 km/h -> 2,25 Mio. h = ~257 Jahre ·
  Verkehrsflugzeug 900 km/h -> 250.000 h = ~28,5 Jahre · ISS-Tempo 28.000 km/h -> ~335 Tage ·
  Parker Solar Probe (schnellstes Raumfahrzeug, ~692.000 km/h) -> ~13,5 Tage ·
  Licht 299.792 km/s -> ~12,5 min.

Hook-Varianten:
  1 "Travel time to MARS at 6 different speeds" (gewaehlt, Rennen)   2 "How long would you walk to Mars?"
  3 "Driving to Mars takes 257 years"   4 "Race to Mars: walking vs. light"   5 "Which one gets to Mars first?"

    python make-w6-mars-race-reel.py  ->  w6-mars-race.mp4, -cover.png
"""

import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono, downscale
from bodies import planet
from reelkit import new_frame, header_band, blob

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
D_KM = 225e6
# (Name, km/h, Sprite)
RACERS = [("Walking", 5, "walk"), ("Car", 100, "car"), ("Airliner", 900, "plane"),
          ("Space station speed", 28_000, "iss"), ("Fastest spacecraft", 692_000, "probe"),
          ("Light", 1_079_252_849, "light")]
T = [D_KM / v * 3600 for _, v, _ in RACERS]                     # Reisezeit in s
LANE_Y0, LANE_DY = 680, 148
X_START, X_END = 170, 905
T_HOLD0, T_RUN, T_TOTAL = 0.8, 12.6, 16.0
E0, E1 = 60.0, T[0] * 1.08


def lane_y(i):
    return LANE_Y0 + i * LANE_DY


def elapsed(t):
    """Logarithmische Uhr: Sekunde 0,8 -> 1 min, Sekunde 13,4 -> ~5.500 Jahre."""
    if t <= T_HOLD0:
        return 0.0
    u = min(1.0, (t - T_HOLD0) / T_RUN)
    u = u * u * (3 - 2 * u) * 0.25 + u * 0.75                     # sanfter Start/Ende
    return 10 ** (math.log10(E0) + u * (math.log10(E1) - math.log10(E0)))


def fmt(s):
    if s < 3600:
        return f"{s / 60:.1f} min" if s < 1200 else f"{s / 60:.0f} min"
    if s < 86400 * 2:
        return f"{s / 3600:.0f} hours"
    if s < 86400 * 365.25 * 2:
        return f"{s / 86400:.0f} days" if s >= 86400 * 20 else f"{s / 86400:.1f} days"
    y = s / (86400 * 365.25)
    return f"{y:,.0f} years" if y >= 100 else f"{y:.1f} years"


def background():
    img, _ = new_frame(21)
    header_band(img, ["Travel time to MARS", "at 6 different speeds"], "MARS")
    d = ImageDraw.Draw(img)
    for i, (name, v, _) in enumerate(RACERS):
        y = lane_y(i) * S
        for x in range(X_START, X_END, 22):                           # gestrichelte Bahn
            d.line([x * S, y + 30 * S, (x + 10) * S, y + 30 * S], fill=HAIR, width=3 * S)
        sp = f"{v:,} km/h" if v < 10_000_000 else "300,000 km/s"
        d.text((X_START * S, y - 62 * S), name, font=f(30 * S, bold=True), fill=FG)
        d.text((X_START * S + d.textlength(name + "  ", font=f(30 * S, bold=True)), y - 58 * S), sp,
               font=f(26 * S), fill=SEC)
    for i in range(len(RACERS)):
        y = lane_y(i) * S
        planet(img, 100 * S, y + 6 * S, 74, "earth", light=(0.8, -0.3, 0.5))
        planet(img, 985 * S, y + 6 * S, 62, "mars", light=(-0.8, -0.3, 0.5))
    d = ImageDraw.Draw(img)
    foot = "Average distance, 225 million km, straight line"
    d.text(((W * S - d.textlength(foot, font=f(26 * S))) / 2, 1560 * S), foot, font=f(26 * S), fill=SEC)
    cta = "Send this to someone who wants to move to Mars"
    d.text(((W * S - d.textlength(cta, font=f(32 * S, bold=True))) / 2, 1600 * S), cta,
           font=f(32 * S, bold=True), fill=FG)
    return downscale(img, W, H)


# ---------------------------------------------------------------- Sprites (4x gezeichnet)

def _canvas(w, h):
    k = 4
    im = Image.new("RGBA", (w * k, h * k), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im), k


def _done(im, w, h):
    return im.resize((w, h), Image.LANCZOS)


def sprite_walk(step):
    im, d, k = _canvas(40, 56)
    c = (236, 238, 242, 255)
    d.ellipse([14 * k, 0, 26 * k, 12 * k], fill=c)
    d.line([20 * k, 12 * k, 20 * k, 34 * k], fill=c, width=5 * k)
    a = 9 if step else -9
    d.line([20 * k, 34 * k, (20 + a) * k, 54 * k], fill=c, width=5 * k)
    d.line([20 * k, 34 * k, (20 - a) * k, 54 * k], fill=c, width=5 * k)
    d.line([20 * k, 18 * k, (20 - a) * k, 30 * k], fill=c, width=4 * k)
    d.line([20 * k, 18 * k, (20 + a) * k, 30 * k], fill=c, width=4 * k)
    return _done(im, 40, 56)


def sprite_car():
    im, d, k = _canvas(96, 44)
    d.rounded_rectangle([4 * k, 18 * k, 92 * k, 34 * k], 7 * k, fill=(214, 64, 52, 255))
    d.polygon([(24 * k, 18 * k), (34 * k, 5 * k), (64 * k, 5 * k), (76 * k, 18 * k)], fill=(214, 64, 52, 255))
    d.polygon([(30 * k, 17 * k), (37 * k, 8 * k), (49 * k, 8 * k), (49 * k, 17 * k)], fill=(150, 196, 230, 255))
    d.polygon([(53 * k, 17 * k), (53 * k, 8 * k), (62 * k, 8 * k), (70 * k, 17 * k)], fill=(150, 196, 230, 255))
    for x in (24, 72):
        d.ellipse([(x - 9) * k, 26 * k, (x + 9) * k, 44 * k], fill=(26, 26, 30, 255))
        d.ellipse([(x - 4) * k, 31 * k, (x + 4) * k, 39 * k], fill=(170, 170, 176, 255))
    d.rectangle([86 * k, 21 * k, 92 * k, 26 * k], fill=(255, 226, 150, 255))
    return _done(im, 96, 44)


def sprite_plane():
    im, d, k = _canvas(110, 44)
    w = (240, 242, 246, 255)
    d.rounded_rectangle([8 * k, 18 * k, 106 * k, 30 * k], 6 * k, fill=w)
    d.polygon([(8 * k, 20 * k), (2 * k, 2 * k), (16 * k, 2 * k), (26 * k, 20 * k)], fill=(70, 110, 200, 255))
    d.polygon([(46 * k, 26 * k), (70 * k, 26 * k), (52 * k, 44 * k), (40 * k, 44 * k)], fill=(200, 206, 214, 255))
    for x in range(36, 96, 8):
        d.ellipse([x * k, 21 * k, (x + 3) * k, 24 * k], fill=(70, 110, 200, 255))
    d.polygon([(98 * k, 19 * k), (106 * k, 22 * k), (98 * k, 25 * k)], fill=(70, 110, 200, 255))
    return _done(im, 110, 44)


def sprite_iss():
    im, d, k = _canvas(96, 48)
    gold, dark = (186, 136, 64, 255), (120, 84, 38, 255)
    for x in (10, 24, 62, 76):
        d.rectangle([x * k, 4 * k, (x + 10) * k, 44 * k], fill=gold, outline=dark, width=k)
        for y in range(8, 44, 6):
            d.line([x * k, y * k, (x + 10) * k, y * k], fill=dark, width=k)
    d.rectangle([4 * k, 22 * k, 92 * k, 26 * k], fill=(200, 204, 210, 255))
    d.rounded_rectangle([40 * k, 14 * k, 56 * k, 36 * k], 4 * k, fill=(232, 234, 238, 255))
    return _done(im, 96, 48)


def sprite_probe():
    im, d, k = _canvas(80, 52)
    d.rounded_rectangle([60 * k, 2 * k, 72 * k, 50 * k], 5 * k, fill=(244, 244, 240, 255))   # Hitzeschild
    d.polygon([(22 * k, 14 * k), (60 * k, 18 * k), (60 * k, 34 * k), (22 * k, 38 * k)], fill=(176, 150, 96, 255))
    d.rectangle([4 * k, 22 * k, 24 * k, 30 * k], fill=(70, 90, 160, 255))                   # Solarpaneele
    d.line([22 * k, 26 * k, 2 * k, 26 * k], fill=(200, 200, 205, 255), width=2 * k)
    return _done(im, 80, 52)


SPRITES = {}


def racer(im, kind, x, y, t, frame_i):
    if kind == "light":
        tail = 120
        g = Image.new("L", im.size, 0)
        gd = ImageDraw.Draw(g)
        for j in range(24):
            a = int(255 * (j + 1) / 24)
            x0 = x - tail + tail * j / 24
            gd.line([x0, y, x0 + tail / 24 + 1, y], fill=a, width=6)
        im.paste((255, 244, 210), (0, 0), g.filter(ImageFilter.GaussianBlur(2)))
        blob(im, int(x), int(y), 18, 18, (255, 236, 180), blur=8, alpha=230)
        ImageDraw.Draw(im).ellipse([x - 7, y - 7, x + 7, y + 7], fill=(255, 252, 240))
        return
    if kind == "walk":
        sp = sprite_walk((frame_i // 6) % 2)
    else:
        if kind not in SPRITES:
            SPRITES[kind] = {"car": sprite_car, "plane": sprite_plane, "iss": sprite_iss, "probe": sprite_probe}[kind]()
        sp = SPRITES[kind]
    im.paste(sp, (int(x - sp.width / 2), int(y - sp.height / 2)), sp)


def frame(bg, t, i):
    im = bg.copy()
    d = ImageDraw.Draw(im)
    e = elapsed(t)
    clock = "Ready..." if e == 0 else "Time passed: " + fmt(e)
    fo = f(44, bold=True)
    d.text(((W - d.textlength(clock, font=fo)) / 2, 540), clock, font=fo, fill=ACC)
    for n, ((name, v, kind), tt) in enumerate(zip(RACERS, T)):
        y = lane_y(n)
        p = min(1.0, e / tt)
        x = X_START + 20 + (X_END - X_START - 40) * p
        racer(im, kind, x, y + 8, t, i)
        if p >= 1.0:
            lab = fmt(tt)
            fl = f(30, bold=True)
            d = ImageDraw.Draw(im)
            tw = d.textlength(lab, font=fl)
            d.rounded_rectangle([X_END - tw - 40, y - 66, X_END + 6, y - 22], 12, fill=(40, 30, 12))
            d.text((X_END - tw - 17, y - 62), lab, font=fl, fill=ACC)
    return im


def main():
    bg = background()
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(T_TOTAL * FPS)
    out = OUT / "w6-mars-race.mp4"
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{T_TOTAL:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(frame(bg, i / FPS, i).convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()
    frame(bg, 7.4, 0).convert("RGB").save(OUT / "w6-mars-race-cover.png")
    print(f"saved {out.name} ({T_TOTAL:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
