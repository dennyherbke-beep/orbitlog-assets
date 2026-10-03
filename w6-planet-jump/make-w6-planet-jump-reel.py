"""Woche 6, Samstag - Loop-Reel "How high could you jump on each planet?" (neues Format, Test).
Eine durchgehende Animation unter fester Kopfzeile statt Folienfolge (Nischen-Analyse 04.10.2026:
virale Space-Reels = Header-Band + loopendes Vergleichsbild). 3x3-Raster, Astronaut springt auf
jeder Oberflaeche mit der Hoehe/Flugzeit der jeweiligen Schwerkraft. ~7,7 s, nahtloser Loop.

Fakten (NASA Planetary Fact Sheet, Oberflaechen-/Wolkenobergrenzen-Schwerkraft in m/s^2):
  Merkur 3,70 · Venus 8,87 · Erde 9,81 · Mond 1,62 · Mars 3,71 · Jupiter 24,79 · Saturn 10,44 ·
  Uranus 8,87 · Neptun 11,15. Annahme: gleicher Absprung wie ein 0,5-m-Sprung auf der Erde
  (v0 = sqrt(2*9,81*0,5) = 3,13 m/s) -> Hoehe h = 0,5 m * 9,81/g, Flugzeit t = 2*v0/g.
  Erde 0,50 m / 0,64 s, Mond 3,03 m / 3,86 s, Jupiter 0,20 m / 0,25 s.
  Gasplaneten haben keine feste Oberflaeche (Schwerkraft auf Hoehe der Wolkenobergrenze) -> Sternchen.
  Raumanzug-Gewicht ignoriert (first_comment). Flugzeiten fuer den nahtlosen Loop auf ganze
  Sprungzahlen je Loop gerundet (Abweichung < 5 %).

Hook-Varianten (Formatvorlage):
  1 "How high could you jump on each planet?" (gewaehlt, Vergleichsraster)
  2 "On the Moon you'd jump 6x higher"   3 "Jupiter would pin you to the ground"
  4 "Your jump, on every planet"   5 "Which planet would make you an Olympic high jumper?"

    python make-w6-planet-jump-reel.py  ->  w6-planet-jump.mp4, -cover.png
"""

import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono, ring_mark, downscale
from bodies import planet
from reelkit import W as WS, H as HS, new_frame

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
G_EARTH, H_EARTH = 9.81, 0.5
V0 = math.sqrt(2 * G_EARTH * H_EARTH)
BODIES = [("Mercury", "mercury", 3.70, False), ("Venus", "venus", 8.87, False), ("Earth", "earth", 9.81, False),
          ("Moon", "moon", 1.62, False), ("Mars", "mars", 3.71, False), ("Jupiter", "jupiter", 24.79, True),
          ("Saturn", "saturn", 10.44, True), ("Uranus", "uranus", 8.87, True), ("Neptune", "neptune", 11.15, True)]
LOOP = 2 * 2 * V0 / 1.62                     # zwei Mondspruenge (~7,7 s)
GRID_TOP, CELL_W, CELL_H = 520, 340, 340     # Ausgabe-px
GROUND = 262                                 # Bodenlinie innerhalb der Zelle
PX_PER_M = 200 / 3.03                        # Mondsprung = 200 px


def cell_origin(i):
    col, row = i % 3, i // 3
    return (W - 3 * CELL_W) // 2 + col * CELL_W, GRID_TOP + row * CELL_H


def header_band(img):
    """Feste Kopfzeile wie bei grossen Nischen-Accounts: Marke + Handle, Schlagzeile mit Akzentwort."""
    d = ImageDraw.Draw(img)
    y = 250 * S
    ring_mark(img, 120 * S, y + 34 * S, 15 * S)
    d = ImageDraw.Draw(img)
    d.text((170 * S, y + 4 * S), "Orbit Log", font=f(34 * S, bold=True), fill=FG)
    d.text((170 * S, y + 46 * S), "@theorbitlog", font=fmono(22 * S), fill=SEC)
    y += 120 * S
    t1, t2a, t2b = "How high could you jump", "on each ", "planet?"
    fo = f(60 * S, bold=True)
    d.text(((WS - d.textlength(t1, font=fo)) / 2, y), t1, font=fo, fill=FG)
    w2 = d.textlength(t2a + t2b, font=fo)
    x = (WS - w2) / 2
    d.text((x, y + 72 * S), t2a, font=fo, fill=FG)
    d.text((x + d.textlength(t2a, font=fo), y + 72 * S), t2b, font=fo, fill=ACC)


def background():
    img, _ = new_frame(11)
    header_band(img)
    for i, (name, kind, g, gas) in enumerate(BODIES):
        x0, y0 = cell_origin(i)
        x0, y0 = x0 * S, y0 * S
        cw, ch = CELL_W * S, CELL_H * S
        cell = img.crop((x0, y0, x0 + cw, y0 + ch))
        R = 900                                                           # grosse Kugel = Boden-Horizont
        kw = dict(light=(-0.4, -0.8, 0.45), glow=False)
        if kind == "saturn":
            kw["ring_tilt"] = None
        planet(cell, cw // 2, int(GROUND * S + R * S / 2 - 6 * S), R, kind, **kw)
        img.paste(cell, (x0, y0))
        d = ImageDraw.Draw(img)
        h = H_EARTH * G_EARTH / g
        ly = y0 + (GROUND + 22) * S                                       # Beschriftung auf der Oberflaeche
        st = dict(stroke_width=2 * S, stroke_fill=(8, 10, 14))
        d.text((x0 + 18 * S, ly), name + ("*" if gas else ""), font=f(30 * S, bold=True),
               fill=ACC if name == "Earth" else FG, **st)
        val = f"{h:.1f} m" if h >= 1 else f"{h * 100:.0f} cm"
        tw = d.textlength(val, font=f(30 * S, bold=True))
        d.text((x0 + cw - tw - 18 * S, ly), val, font=f(30 * S, bold=True), fill=ACC, **st)
        d.rectangle([x0 + 4 * S, y0 + 4 * S, x0 + cw - 4 * S, y0 + ch - 4 * S], outline=HAIR, width=2 * S)
    d = ImageDraw.Draw(img)
    foot = "Same push-off as a 0.5 m jump on Earth · *no solid surface"
    d.text(((WS - d.textlength(foot, font=f(26 * S))) / 2, (GRID_TOP + 3 * CELL_H + 24) * S), foot,
           font=f(26 * S), fill=SEC)
    cta = "Send this to your gym buddy"
    d.text(((WS - d.textlength(cta, font=f(34 * S, bold=True))) / 2, (GRID_TOP + 3 * CELL_H + 64) * S), cta,
           font=f(34 * S, bold=True), fill=FG)
    return downscale(img, W, H)


def astronaut_sprite(h=52):
    """Kleiner Astronaut (Seitenansicht), 4x gezeichnet und verkleinert (Kantenglaettung)."""
    k = 4
    sw, sh = int(h * 0.75 * k), int(h * k)
    sp = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    d = ImageDraw.Draw(sp)
    u = sh / 58
    white, shade, visor = (240, 242, 246, 255), (176, 184, 196, 255), (255, 186, 92, 255)
    d.rounded_rectangle([sw * 0.12, 18 * u, sw * 0.40, 40 * u], 5 * u, fill=shade)            # Rucksack
    d.rounded_rectangle([sw * 0.30, 18 * u, sw * 0.82, 42 * u], 9 * u, fill=white)            # Rumpf
    d.ellipse([sw * 0.30, 0, sw * 0.88, 22 * u], fill=white)                                 # Helm
    d.rounded_rectangle([sw * 0.56, 5 * u, sw * 0.86, 15 * u], 5 * u, fill=visor)             # Visier
    d.rounded_rectangle([sw * 0.34, 40 * u, sw * 0.52, 58 * u], 4 * u, fill=white)            # Bein hinten
    d.rounded_rectangle([sw * 0.58, 40 * u, sw * 0.76, 58 * u], 4 * u, fill=white)            # Bein vorn
    d.rounded_rectangle([sw * 0.70, 22 * u, sw * 0.96, 30 * u], 4 * u, fill=shade)            # Arm
    sp = sp.resize((sw // k, sh // k), Image.LANCZOS)
    return sp


def frame(bg, sprite, shadow, t):
    im = bg.copy()
    for i, (name, kind, g, gas) in enumerate(BODIES):
        x0, y0 = cell_origin(i)
        period = LOOP / max(1, round(LOOP / (2 * V0 / g)))               # ganze Spruenge pro Loop
        tau = (t % period) / period                                       # 0..1 Flugphase
        z = 4 * tau * (1 - tau) * (H_EARTH * G_EARTH / g) * PX_PER_M      # Parabel
        cx, gy = x0 + CELL_W // 2, y0 + GROUND
        sc = max(0.35, 1 - z / 260)                                       # Schatten schrumpft mit Hoehe
        sw = int(shadow.width * sc)
        sd = shadow.resize((max(1, sw), max(1, int(shadow.height * sc))))
        im.paste((0, 0, 0), (cx - sd.width // 2, gy - sd.height // 2), sd)
        im.paste(sprite, (cx - sprite.width // 2, int(gy - sprite.height - z)), sprite)
    return im


def main():
    bg = background()
    sprite = astronaut_sprite()
    shadow = Image.new("L", (60, 16), 0)
    ImageDraw.Draw(shadow).ellipse([0, 0, 59, 15], fill=150)
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = round(LOOP * FPS)
    out = OUT / "w6-planet-jump.mp4"
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{n / FPS:.3f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(frame(bg, sprite, shadow, i / FPS).convert("RGB").tobytes())
    proc.stdin.close()
    proc.wait()
    frame(bg, sprite, shadow, LOOP * 0.25).convert("RGB").save(OUT / "w6-planet-jump-cover.png")
    print(f"saved {out.name} ({n / FPS:.2f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
