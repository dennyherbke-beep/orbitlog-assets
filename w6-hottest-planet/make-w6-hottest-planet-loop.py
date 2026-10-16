"""Umbau 16.10.2026 (Woche 8, Di 20.10.): "The HOTTEST planet isn't the closest one" als Raster-Loop im
Winner-Format (feste Kopfzeile + eine durchgehende Animation) statt 7 Folien (make-w6-hottest-planet-reel.py).
3x3-Raster, je Feld Planet + Thermometer, alle Thermometer steigen gleichzeitig. Merkur schwankt zwischen
Tag (430 C) und Nacht (-180 C), Venus bleibt bei 464 C und wird als HOTTEST markiert. 10 s, Loop.

Fakten: NASA Planetary Fact Sheet, Zeile "Mean Temperature (C)": Venus 464, Erde 15, Mars -65, Jupiter -110,
Saturn -140, Uranus -195, Neptun -200, Pluto -225. Merkur Mittel 167, aber Tag ~430 / Nacht ~-180
(NASA Science Mercury Facts). Uranus-Rekordminimum -224 C (Tropopause) nur im ersten Kommentar - nach
Mittelwert ist Neptun kaelter, deshalb hier kein "coldest planet"-Twist.

Hook-Varianten:
  1 "The HOTTEST planet isn't the closest one" (gewaehlt)   2 "Mercury is closest to the Sun. It's NOT the hottest."
  3 "Guess the hottest planet before the thermometers stop"   4 "Twice as far from the Sun - and still hotter"
  5 "Which planet would melt lead?"

    python make-w6-hottest-planet-loop.py [--preview]  ->  w6-hottest-planet-loop.mp4, -loop-cover.png
"""

import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageChops, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, downscale
from bodies import planet
from reelkit import W as WS, new_frame, header_band, blob, cinematic

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
LOOP = 10.0
# Name, Textur, Mitteltemperatur C, Kugel-Durchmesser px (Saturn kleiner wegen Ringen)
BODIES = [("Mercury", "mercury", 430, 150), ("Venus", "venus", 464, 150), ("Earth", "earth", 15, 150),
          ("Mars", "mars", -65, 150), ("Jupiter", "jupiter", -110, 150), ("Saturn", "saturn", -140, 96),
          ("Uranus", "uranus", -195, 150), ("Neptune", "neptune", -200, 150), ("Pluto", "pluto", -225, 150)]
GRID_TOP, CELL_W, CELL_H = 540, 340, 330
PCX, PCY = 125, 158                         # Kugelmitte im Feld
T_MIN, T_MAX = -240, 480                    # Thermometer-Skala
TX, TY0, TY1 = 282, 40, 236                 # Roehre: Mitte x, oben, unten (Feld-px)
DAY, NIGHT = (-0.6, -0.3, 0.75), (0.35, -0.1, -0.93)


def cell_origin(i):
    return (W - 3 * CELL_W) // 2 + (i % 3) * CELL_W, GRID_TOP + (i // 3) * CELL_H


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def temp_color(t):
    stops = [(-240, (90, 140, 255)), (-100, (140, 190, 255)), (0, (232, 238, 248)), (150, (255, 190, 90)),
             (480, (255, 70, 40))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if t <= b:
            k = (t - a) / (b - a)
            return tuple(int(ca[j] + (cb[j] - ca[j]) * max(0, k)) for j in range(3))
    return stops[-1][1]


def background():
    img, _ = new_frame(47)
    header_band(img, ["The HOTTEST planet", "isn't the closest one"], "HOTTEST")
    for i, (name, kind, _, dpx) in enumerate(BODIES):
        x0, y0 = cell_origin(i)
        x0, y0 = x0 * S, y0 * S
        cw, ch = CELL_W * S, CELL_H * S
        cell = img.crop((x0, y0, x0 + cw, y0 + ch))
        if name == "Venus":
            glow_l = Image.new("RGB", cell.size, (0, 0, 0))
            blob(glow_l, PCX * S, PCY * S, 120 * S, 120 * S, (70, 30, 10), blur=int(50 * S))
            cell = ImageChops.add(cell, glow_l)
        if name != "Mercury":                                     # Merkur wechselt je Frame die Beleuchtung
            planet(cell, PCX * S, PCY * S, dpx, kind, light=DAY, glow=True,
                   ring_tilt=18 if name == "Saturn" else None, lon0=200 if name == "Earth" else 180)
        img.paste(cell, (x0, y0))
        d = ImageDraw.Draw(img)
        d.rectangle([x0 + 4 * S, y0 + 4 * S, x0 + cw - 4 * S, y0 + ch - 4 * S], outline=HAIR, width=2 * S)
    d = ImageDraw.Draw(img)
    y = (GRID_TOP + 3 * CELL_H + 22) * S
    note = "Mean temperatures (NASA) · Mercury: day vs. night · *dwarf planet"
    d.text(((WS - d.textlength(note, font=f(24 * S))) / 2, y), note, font=f(24 * S), fill=SEC)
    cta = "Send this to whoever says Mercury"
    d.text(((WS - d.textlength(cta, font=f(34 * S, bold=True))) / 2, y + 40 * S), cta,
           font=f(34 * S, bold=True), fill=FG)
    return downscale(img, W, H)


def mercury_sprites(n=24):
    """Merkur zwischen Tag- und Nachtbeleuchtung, als Ausschnitt in Feldgroesse (RGBA)."""
    out = []
    for k in range(n):
        a = k / (n - 1)
        light = tuple(DAY[j] + (NIGHT[j] - DAY[j]) * a for j in range(3))
        im = Image.new("RGB", (CELL_W * S, CELL_H * S), (0, 0, 0))
        planet(im, PCX * S, PCY * S, 150, "mercury", light=light, glow=False)
        im = downscale(im, CELL_W, CELL_H)
        mask = im.convert("L").point(lambda p: 255 if p > 5 else p * 50)
        out.append((im, mask))
    return out


def mercury_state(t):
    """0 = Tag, 1 = Nacht."""
    if t < 5.0:
        return 0.0
    if t < 6.0:
        return ease(t - 5.0)
    if t < 7.4:
        return 1.0
    return 1.0 - ease((t - 7.4) / 0.8)


def level(t):
    """Fuellstand 0..1 aller Thermometer: steigen, halten, fallen (nahtloser Loop)."""
    if t < 3.0:
        return ease((t - 0.4) / 2.6)
    if t < 8.6:
        return 1.0
    return 1.0 - ease((t - 8.6) / 1.2)


def frame(bg, merc, t):
    im = bg.copy()
    lv = level(t)
    night = mercury_state(t)
    for i, (name, kind, temp, _) in enumerate(BODIES):
        x0, y0 = cell_origin(i)
        cell = im.crop((x0, y0, x0 + CELL_W, y0 + CELL_H))
        if name == "Mercury":
            sp, m = merc[round(night * (len(merc) - 1))]
            cell.paste(sp, (0, 0), m)
            temp = 430 + (-180 - 430) * night
        d = ImageDraw.Draw(cell)
        st = dict(stroke_width=2, stroke_fill=(8, 10, 14))
        cur = T_MIN + (temp - T_MIN) * lv
        # Thermometer: Roehre, Kugel, Fuellung
        d.rounded_rectangle([TX - 13, TY0 - 4, TX + 13, TY1 + 10], radius=13, fill=(22, 26, 36), outline=(70, 78, 96), width=2)
        d.ellipse([TX - 24, TY1 - 4, TX + 24, TY1 + 44], fill=(22, 26, 36), outline=(70, 78, 96), width=2)
        c = temp_color(cur)
        top = TY1 - (TY1 - TY0) * (cur - T_MIN) / (T_MAX - T_MIN)
        d.rounded_rectangle([TX - 7, top, TX + 7, TY1 + 16], radius=7, fill=c)
        d.ellipse([TX - 17, TY1 + 3, TX + 17, TY1 + 37], fill=c)
        for tick in (-200, 0, 200, 400):
            ty = TY1 - (TY1 - TY0) * (tick - T_MIN) / (T_MAX - T_MIN)
            d.line([TX - 22, ty, TX - 15, ty], fill=(110, 118, 136), width=2)
        # Beschriftung
        label = name + ("*" if name == "Pluto" else "")
        d.text((16, 12), label, font=f(30, bold=True), fill=ACC if name == "Earth" else FG, **st)
        val = f"{cur:+.0f} °C".replace("+0 ", "0 ").replace("-0 ", "0 ")
        d.text((16, CELL_H - 58), val, font=f(36, bold=True), fill=c, **st)
        if name == "Mercury":
            d.text((16, 48), "closest to the Sun", font=f(22), fill=SEC, **st)
            if lv > 0.95:
                tag = "night side" if night > 0.5 else "day side"
                d.text((16, 74), tag, font=f(22, bold=True), fill=ACC, **st)
        if name == "Venus" and 3.4 < t < 9.0:
            a = ease((t - 3.4) / 0.4) * (1 - ease((t - 8.6) / 0.4))
            col = tuple(int(HAIR[j] + (ACC[j] - HAIR[j]) * a) for j in range(3))
            d.rectangle([3, 3, CELL_W - 4, CELL_H - 4], outline=col, width=4)
            if a > 0.5:
                d.text((16, 48), "HOTTEST", font=f(28, bold=True), fill=ACC, **st)
                d.text((16, 82), "2x farther out", font=f(22), fill=SEC, **st)
        im.paste(cell, (x0, y0))
    return im


def main():
    bg = background()
    merc = mercury_sprites()
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (1.5, 4.0, 6.5, 9.2):
            cinematic(frame(bg, merc, t), 0).save(prev / f"hottest-{t:.1f}.png")
        print("preview saved")
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(LOOP * FPS)
    out = OUT / "w6-hottest-planet-loop.mp4"
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg, merc, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg, merc, 4.0), 0).save(OUT / "w6-hottest-planet-loop-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
