"""Woche 9, Fr 30.10.2026: "HALLOWEEN FIREBALLS: the 2 best nights" (Termin + Handlung, Andromeda-/Orioniden-Muster).
Eine Animation, 17 s: Blick nach Osten gegen 23 Uhr, Stier mit Aldebaran, Hyaden und Plejaden, darunter Orion.
Langsame Meteore und Feuerkugeln strahlen aus dem Radianten. Dann Kalender: die zwei besten Naechte. Dann Anleitung.

Fakten (vor Produktion geprueft, 26.10.2026):
  Suedliche Tauriden aktiv ~20.09.-20.11., Maximum ~5.11. (IMO-Kalender 2026); Noerdliche Tauriden aktiv ~20.10.-10.12.,
  Maximum Nacht 11./12.11. (AMS). Je ~5 Meteore/Std., aber langsam (~27-30 km/s) und reich an Feuerkugeln ("Halloween
  fireballs", NASA MSFC). Mond: Vollmond 26.10., ~25 % am 5.11., Neumond 9.11., ~4 % am 12.11. (AMS).
  Ursprung: Komet 2P/Encke bzw. dessen Truemmerstrom (NASA). Radiant S ~RA 3h30 Dec +14, N ~RA 3h52 Dec +22.
  Sterne: RA/Dec J2000 aus dem Bright Star Catalogue, Projektion gnomonisch, Lage am Himmel vereinfacht.
  Regel 9 geprueft: einziges gemeinfreies NASA-Foto (MSFC-Allsky 2012, 637x480, Daemmerung) ungeeignet -> eigene Grafik.

Hook-Varianten:
  1 "HALLOWEEN FIREBALLS: the 2 best nights" (gewaehlt)   2 "Fireballs are falling all through November"
  3 "Look east for slow, bright meteors"   4 "The meteor shower that makes fireballs"   5 "Mark Nov 5 and Nov 12"

    python make-w9-taurids-reel.py [--preview DIR]  ->  w9-taurids.mp4, -cover.png
"""

import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import FG, SEC, ACC, HAIR, f, downscale
from reelkit import new_frame, header_band, cinematic

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
LOOP = 17.0
C_RA, C_DEC = 4.25, 17.0                       # Bildmitte (Stunden, Grad)
SCALE = 33.0                                   # px pro Grad
ROT = math.radians(-38)                        # aufgehendes Sternbild im Osten: Norden nach links oben
CX, CY = 500, 1110
GROUND = 1470
RADIANT = (3.62, 17.5)                         # zwischen S- und N-Radiant (Ende Okt./Anfang Nov.)

# (Name, RA h, Dec Grad, mag, Farbe)
STARS = [("Aldebaran", 4.598, 16.51, 0.85, (255, 196, 140)), ("Elnath", 5.438, 28.61, 1.65, (225, 232, 255)),
         ("", 5.627, 21.14, 3.0, (230, 236, 255)), ("", 4.330, 15.63, 3.65, (255, 226, 190)),
         ("", 4.382, 17.54, 3.76, (255, 226, 190)), ("", 4.477, 19.18, 3.53, (255, 220, 180)),
         ("", 4.478, 15.87, 3.4, (245, 240, 230)), ("", 4.011, 12.49, 3.4, (220, 230, 255)),
         ("", 3.791, 24.105, 2.87, (210, 222, 255)), ("", 3.819, 24.05, 3.6, (210, 222, 255)),
         ("", 3.748, 24.11, 3.7, (210, 222, 255)), ("", 3.763, 24.37, 3.9, (210, 222, 255)),
         ("", 3.772, 23.95, 4.1, (210, 222, 255)), ("", 3.753, 24.47, 4.3, (210, 222, 255)),
         ("Capella", 5.278, 46.0, 0.08, (255, 238, 200)), ("Betelgeuse", 5.919, 7.41, 0.5, (255, 170, 110)),
         ("", 5.419, 6.35, 1.6, (215, 225, 255)), ("Rigel", 5.242, -8.2, 0.13, (205, 220, 255)),
         ("", 5.533, -0.30, 2.2, (215, 225, 255)), ("", 5.603, -1.2, 1.7, (215, 225, 255)),
         ("", 5.679, -1.94, 1.8, (215, 225, 255)), ("", 5.796, -9.67, 2.0, (215, 225, 255)),
         ("", 3.0, 4.09, 2.5, (255, 200, 160)), ("Hamal", 2.120, 23.46, 2.0, (255, 214, 170))]
LINES = [(0, 6), (6, 4), (4, 3), (3, 7), (6, 5), (5, 1), (0, 2)]        # Stier-Kopf + Hoerner (vereinfacht)
ORION = [(15, 16), (16, 18), (18, 19), (19, 20), (20, 21), (15, 20), (17, 18)]

CAPTIONS = [(0.0, "Slow, bright meteors", "from the dust of Comet Encke."),
            (5.6, "Mark your calendar:", "Nov 4-5 and Nov 11-12."),
            (11.6, "Look east after 10 pm.", "About 5 an hour - but some are fireballs."),
            (15.4, "", "")]


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def proj(ra_h, dec):
    """Gnomonische Projektion um die Bildmitte, Osten links, dann gedreht."""
    a, d = math.radians(ra_h * 15), math.radians(dec)
    a0, d0 = math.radians(C_RA * 15), math.radians(C_DEC)
    cosc = math.sin(d0) * math.sin(d) + math.cos(d0) * math.cos(d) * math.cos(a - a0)
    xi = math.cos(d) * math.sin(a - a0) / cosc
    eta = (math.cos(d0) * math.sin(d) - math.sin(d0) * math.cos(d) * math.cos(a - a0)) / cosc
    x, y = -math.degrees(xi) * SCALE, -math.degrees(eta) * SCALE
    return (CX + x * math.cos(ROT) - y * math.sin(ROT), CY + x * math.sin(ROT) + y * math.cos(ROT))


def ground_profile():
    rng = np.random.default_rng(12)
    x = np.arange(W, dtype=np.float32)
    hill = GROUND + 18 * np.sin(x / 190) + 10 * np.sin(x / 63 + 0.7)
    trees = np.zeros(W, np.float32)
    for _ in range(55):
        c, w, h = rng.uniform(0, W), rng.uniform(14, 40), rng.uniform(16, 58)
        trees = np.maximum(trees, h * np.sqrt(np.clip(1 - ((x - c) / w) ** 2, 0, 1)))
    return hill - trees


def background():
    img, _ = new_frame(31)
    header_band(img, ["HALLOWEEN FIREBALLS:", "the 2 best nights"], "HALLOWEEN FIREBALLS:")
    sm = downscale(img, W, H)
    arr = np.asarray(sm, np.float32)
    ys = np.arange(H, dtype=np.float32)[:, None]
    glow = np.exp(-np.clip(GROUND - ys, 0, None) / 160.0) * (ys < GROUND + 60)        # Stadtlicht-Dunst am Horizont
    arr = arr + glow[..., None] * np.array([46, 40, 52])[None, None, :]
    sm = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(sm)
    # Sternbildlinien
    pts = [proj(s[1], s[2]) for s in STARS]
    for i, j in LINES + ORION:
        d.line([pts[i], pts[j]], fill=(58, 70, 96), width=2)
    # Sterne mit Glow
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    dl = ImageDraw.Draw(layer)
    for (name, ra, dec, mag, c), (x, y) in zip(STARS, pts):
        r = max(1.8, 7.6 - 1.4 * mag)
        dl.ellipse([x - r, y - r, x + r, y + r], fill=c)
    sm = ImageChops.add(sm, layer.filter(ImageFilter.GaussianBlur(6)))
    sm = ImageChops.lighter(sm, layer)
    d = ImageDraw.Draw(sm)
    st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
    for (name, ra, dec, mag, c), (x, y) in zip(STARS, pts):
        if name in ("Aldebaran", "Betelgeuse", "Rigel"):
            d.text((x + 12, y - 8), name, font=f(22), fill=SEC, **st)
    px, py = proj(3.78, 24.2)
    d.text((px + 18, py - 30), "Pleiades", font=f(22), fill=SEC, **st)
    tx, ty = proj(4.45, 22.0)
    d.text((tx - 30, ty - 44), "TAURUS", font=f(26, bold=True), fill=(120, 134, 168), **st)
    ox, oy = proj(5.6, -4.0)
    d.text((ox + 30, oy + 8), "ORION", font=f(26, bold=True), fill=(120, 134, 168), **st)
    # Boden
    g = ground_profile()
    d.polygon([(0, H)] + [(x, float(g[x])) for x in range(0, W, 3)] + [(W, float(g[-1])), (W, H)], fill=(8, 10, 14))
    d.text((60, 1610), "Looking east · about 11 pm", font=f(26, bold=True), fill=ACC, **st)
    cta = "Send this to the friend you'd watch it with"
    d.text(((W - d.textlength(cta, font=f(34, bold=True))) / 2, 1740), cta, font=f(34, bold=True), fill=FG, **st)
    return sm, g


class Meteors:
    """Langsame Meteore aus dem Radianten; einige als Feuerkugeln mit Aufblitzen."""

    def __init__(self):
        rng = np.random.default_rng(23)
        self.m = []
        t = 0.3
        while t < LOOP - 0.8:
            ang = rng.uniform(math.radians(-25), math.radians(205))       # weg vom Radianten, seitlich oder nach unten
            fire = rng.random() < 0.4
            self.m.append(dict(t0=t, ang=ang, r0=rng.uniform(70, 220), length=rng.uniform(380, 700) * (1.3 if fire else 1),
                               dur=rng.uniform(1.0, 1.6) * (1.25 if fire else 1), fire=fire,
                               w=rng.uniform(3.0, 4.2) * (2.0 if fire else 1)))
            t += rng.uniform(0.45, 0.9)

    def draw(self, t, ground):
        layer = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(layer)
        rx, ry = proj(*RADIANT)
        for m in self.m:
            s = (t - m["t0"]) / m["dur"]
            if not 0 <= s <= 1:
                continue
            ca, sa = math.cos(m["ang"]), math.sin(m["ang"])
            head = m["r0"] + m["length"] * s
            tail = m["r0"] + m["length"] * max(0.0, s - 0.45)
            fade = math.sin(math.pi * s) ** 0.6
            n = 22
            for k in range(n):                                                 # sich verjuengender Schweif
                a0 = tail + (head - tail) * k / n
                a1 = tail + (head - tail) * (k + 1) / n
                q = (k + 1) / n
                if m["fire"]:
                    c = (255, int(150 + 80 * q), int(60 + 120 * q * q))
                else:
                    c = (int(190 + 60 * q), int(220 + 30 * q), 255)
                c = tuple(int(v * fade * (0.15 + 0.85 * q)) for v in c)
                x0, y0, x1, y1 = rx + a0 * ca, ry + a0 * sa, rx + a1 * ca, ry + a1 * sa
                d.line([x0, y0, x1, y1], fill=c, width=max(1, int(m["w"] * q)))
            hx, hy = rx + head * ca, ry + head * sa
            br = (m["w"] + 4) * fade * (2.4 if m["fire"] and 0.55 < s < 0.8 else 1.0)
            d.ellipse([hx - br, hy - br, hx + br, hy + br], fill=(255, 250, 235))
        layer = ImageChops.add(ImageChops.add(layer, layer.filter(ImageFilter.GaussianBlur(7))),
                               layer.filter(ImageFilter.GaussianBlur(22)))
        cut = Image.new("L", (W, H), 255)
        ImageDraw.Draw(cut).polygon([(0, H)] + [(x, float(ground[x])) for x in range(0, W, 3)] + [(W, float(ground[-1])), (W, H)],
                                    fill=0)
        ImageDraw.Draw(cut).rectangle([0, 0, W, 690], fill=0)                 # Textzone oben frei halten
        return layer, cut


def calendar(im, t):
    a = ease((t - 5.8) / 0.5) * (1 - ease((t - 11.3) / 0.4))
    if a <= 0:
        return im
    panel = Image.new("RGB", (W, H), (0, 0, 0))
    m = Image.new("L", (W, H), 0)
    x0, y0, x1, y1 = 70, 1160, 1010, 1420
    ImageDraw.Draw(m).rounded_rectangle([x0, y0, x1, y1], 28, fill=int(205 * a))
    panel.paste((10, 13, 20), (0, 0, W, H))
    im = Image.composite(panel, im, m)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([x0, y0, x1, y1], 28, outline=tuple(int(v * a) for v in HAIR), width=2)
    cols = [("Nov 4-5", "South Taurids", "peak · Moon 25%", True),
            ("Nov 9", "New Moon", "darkest skies", False),
            ("Nov 11-12", "North Taurids", "peak · Moon 4%", True)]
    cw = (x1 - x0) / 3
    for i, (date, l1, l2, best) in enumerate(cols):
        cx = x0 + cw * (i + 0.5)
        pop = ease((t - 6.1 - i * 0.35) / 0.35) * a
        c_date = ACC if best else FG
        for txt, fo, c, y in ((date, f(46, bold=True), c_date, y0 + 34), (l1, f(28, bold=True), FG, y0 + 104),
                              (l2, f(24), SEC, y0 + 144)):
            d.text((cx - d.textlength(txt, font=fo) / 2, y), txt, font=fo, fill=tuple(int(v * pop) for v in c))
        if best:
            tag = "BEST NIGHT"
            fo = f(22, bold=True)
            tw = d.textlength(tag, font=fo)
            d.rounded_rectangle([cx - tw / 2 - 14, y0 + 192, cx + tw / 2 + 14, y0 + 228], 16,
                                fill=tuple(int(v * pop) for v in ACC))
            d.text((cx - tw / 2, y0 + 196), tag, font=fo, fill=tuple(int(v * pop) for v in (12, 14, 20)))
        if i < 2:
            xx = x0 + cw * (i + 1)
            d.line([xx, y0 + 40, xx, y1 - 40], fill=tuple(int(v * a) for v in HAIR), width=2)
    return im


def frame(bg, ground, M, t):
    im = bg.copy()
    layer, cut = M.draw(t, ground)
    im = Image.composite(ImageChops.add(im, layer), im, cut)
    d = ImageDraw.Draw(im)
    st = dict(stroke_width=4, stroke_fill=(8, 10, 14))
    # Radiant
    ra = ease((t - 1.2) / 0.5) * (1 - ease((t - 5.4) / 0.4))
    if ra > 0:
        rx, ry = proj(*RADIANT)
        c = tuple(int(v * ra) for v in ACC)
        d.ellipse([rx - 16, ry - 16, rx + 16, ry + 16], outline=c, width=3)
        d.text((rx - 150, ry - 52), "Radiant: they all", font=f(24, bold=True), fill=c, **st)
        d.text((rx - 150, ry + 22), "seem to come from here", font=f(24, bold=True), fill=c, **st)
    im = calendar(im, t)
    d = ImageDraw.Draw(im)
    cap = [c for c in CAPTIONS if t >= c[0]][-1]
    ca = ease((t - cap[0]) / 0.4)
    for j, ln in enumerate(cap[1:]):
        if ln:
            fo = f(42, bold=True) if j == 0 else f(36)
            d.text(((W - d.textlength(ln, font=fo)) / 2, 550 + j * 58), ln, font=fo,
                   fill=tuple(int(v * ca) for v in FG), **st)
    if t >= 15.4:                                                   # Save-Grund am Ende
        a = ease((t - 15.4) / 0.3)
        for j, (ln, fo, c) in enumerate([("Save this for Nov 4.", f(52, bold=True), ACC)]):
            d.text(((W - d.textlength(ln, font=fo)) / 2, 560), ln, font=fo, fill=tuple(int(v * a) for v in c), **st)
    return im


def main():
    bg, ground = background()
    M = Meteors()
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (2.2, 4.0, 8.0, 13.0, 16.6):
            cinematic(frame(bg, ground, M, t), 0).save(prev / f"taurids-{t:.1f}.png")
        print("preview saved")
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(LOOP * FPS)
    out = OUT / "w9-taurids.mp4"
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg, ground, M, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg, ground, M, 8.0), 0).save(OUT / "w9-taurids-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
