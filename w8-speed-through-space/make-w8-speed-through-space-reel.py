"""Woche 8, Mi 21.10.2026: "You're moving at 2 MILLION km/h right now" (Typ f Physik-Konzept / Typ a Treppe,
Snapshot-Idee 15.10.2026 nach thereasonroomphysics "The Universe Is Moving"). Feste Kopfzeile, ein Tacho-Zaehler,
vier Szenen zoomen schrittweise heraus: Erde dreht sich -> Erde um die Sonne -> Sonne um die Milchstrasse ->
Milchstrasse relativ zur kosmischen Hintergrundstrahlung. Schluss: "...and you feel none of it." 16 s.

Fakten (vor Produktion geprueft):
  Erdrotation am Aequator 465 m/s = ~1.670 km/h (NASA) · Erdbahn 29,78 km/s = ~107.000 km/h (NASA Planetary Fact
  Sheet) · Sonne um das galaktische Zentrum ~230 km/s = ~828.000 km/h (NASA) · Milchstrasse/Lokale Gruppe relativ zur
  kosmischen Hintergrundstrahlung ~600 km/s = ~2,1-2,2 Mio. km/h (COBE/Planck-Dipol; Sonnensystem allein ~370 km/s).
  Geschwindigkeiten addieren sich nicht einfach (verschiedene Richtungen) -> erster Kommentar.
  Galaxie und Hintergrundstrahlung sind eigene Illustrationen (keine ESA/Planck-Karte, Lizenz).

Hook-Varianten:
  1 "You're moving at 2 MILLION km/h right now" (gewaehlt)   2 "You're not sitting still. Not even close."
  3 "How fast are you moving while you read this?"   4 "4 speeds you're moving at right now"
  5 "Earth is spinning. That's the SLOW part."

    python make-w8-speed-through-space-reel.py [--preview DIR]  ->  w8-speed-through-space.mp4, -cover.png
"""

import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, downscale
from bodies import planet, star, fbm, smooth
from reelkit import W as WS, new_frame, header_band, cinematic

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
LOOP = 16.0
SCX, SCY = 540, 1040
SCENE = 3.3                                       # s je Szene
XF = 0.5                                          # Ueberblendung
SPEEDS = [1670, 107_000, 828_000, 2_100_000]
LABELS = ["Earth spins (at the equator)", "Earth orbits the Sun", "The Sun orbits the Milky Way",
          "The Milky Way races through space*"]


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- Bausteine

def galaxy(size, seed=21):
    """Balkenspirale in Draufsicht (Milchstrasse): Bulge + Balken, 2 Haupt- und 2 Nebenarme, Staub an der
    Arm-Innenkante, Sternentstehungsknoten, Einzelsterne. RGBA."""
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    x, y = (xs - size / 2) / (size / 2), (ys - size / 2) / (size / 2)
    r = np.sqrt(x * x + y * y) + 1e-4
    th = np.arctan2(y, x)
    k = 0.24                                                        # Steigung der log. Spirale
    noise = fbm(seed, size, size, octaves=6, base=6, wrap=False)
    fine = fbm(seed + 1, size, size, octaves=5, base=24, wrap=False)
    arms = np.zeros_like(r)
    dust = np.zeros_like(r)
    for i, (amp, wid) in enumerate([(1.0, 0.33), (1.0, 0.33), (0.55, 0.26), (0.55, 0.26)]):
        phi = i * math.pi / 2 + (0.0 if i < 2 else 0.35)
        d = np.angle(np.exp(1j * (th - (np.log(r / 0.16) / k + phi))))   # Winkelabstand zum Arm
        arms += amp * np.exp(-(d / wid) ** 2)
        dust += amp * np.exp(-((d + 0.30) / 0.10) ** 2)                  # Staub auf der Innenseite
    arms *= smooth(0.12, 0.30, r) * np.exp(-r / 1.1)
    dust *= smooth(0.15, 0.35, r) * (1 - smooth(0.75, 0.95, r))
    xb, yb = x * math.cos(0.45) + y * math.sin(0.45), -x * math.sin(0.45) + y * math.cos(0.45)
    bar = np.exp(-(xb / 0.30) ** 2 - (yb / 0.09) ** 2)
    bulge = np.exp(-r / 0.07) + 0.6 * np.exp(-r / 0.16)
    disk = 0.22 * np.exp(-r / 0.35)
    lum = (arms * (0.55 + 0.75 * noise * fine) + bar * 0.9 + bulge * 1.3 + disk) * (1 - 0.65 * dust * noise)
    lum *= 1 - smooth(0.88, 1.0, r)
    warm, cool = np.array([255, 226, 170], np.float32), np.array([170, 196, 255], np.float32)
    t = smooth(0.08, 0.45, r)[..., None]
    rgb = warm * (1 - t) + cool * t
    rgb = rgb * np.clip(lum * 1.25, 0, 1.6)[..., None] * 0.9
    rng = np.random.default_rng(seed)
    knots = (rng.random(r.shape) < 0.0016) & (arms > 0.35)                # HII-Regionen
    rgb[knots] = [255, 150, 170]
    stars = (rng.random(r.shape) < 0.012) & (lum > 0.05)
    rgb[stars] = np.maximum(rgb[stars], 230)
    rgb = np.clip(rgb, 0, 255).astype(np.uint8)
    a = np.clip(lum * 520, 0, 255).astype(np.uint8)
    im = Image.fromarray(rgb, "RGB").filter(ImageFilter.GaussianBlur(0.6))
    out = im.convert("RGBA")
    out.putalpha(Image.fromarray(a, "L").filter(ImageFilter.GaussianBlur(1.2)))
    return out


def cmb(w, h, seed=31):
    """Illustration der Hintergrundstrahlung: fleckiges Feld in Mollweide-Ellipse (kein Planck-Bild)."""
    n = 0.45 * fbm(seed, h, w, octaves=6, base=24, wrap=False) + 0.55 * fbm(seed + 1, h, w, octaves=4, base=90, wrap=False)
    n = (n - n.mean()) / (n.std() * 2.6) + 0.5
    stops = np.array([[20, 40, 140], [60, 140, 220], [235, 225, 150], [235, 130, 50], [170, 30, 20]], np.float32)
    v = np.clip(n, 0, 0.999) * (len(stops) - 1)
    i = v.astype(int)
    fr = (v - i)[..., None]
    rgb = stops[i] * (1 - fr) + stops[np.minimum(i + 1, len(stops) - 1)] * fr
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    e = ((xs - w / 2) / (w / 2)) ** 2 + ((ys - h / 2) / (h / 2)) ** 2
    a = (np.clip((1 - e) * 60, 0, 1) * 200).astype(np.uint8)
    gray = rgb.mean(axis=2, keepdims=True)
    rgb = gray + (rgb - gray) * 0.7                               # weniger knallig
    out = Image.fromarray((rgb * 0.7).astype(np.uint8), "RGB").convert("RGBA")
    out.putalpha(Image.fromarray(a, "L"))
    return out


def sprite_planet(d, kind, **kw):
    size = int(d + 8)
    im = Image.new("RGB", (size * S, size * S), (0, 0, 0))
    planet(im, size * S // 2, size * S // 2, d, kind, glow=False, **kw)
    im = downscale(im, size, size)
    m = Image.new("L", (size * 4, size * 4), 0)
    c, rr = size * 2, d * 2
    ImageDraw.Draw(m).ellipse([c - rr, c - rr, c + rr, c + rr], fill=255)
    return im, m.resize((size, size), Image.LANCZOS)


def sprite_star(d):
    size = int(d * 3.2)
    im = Image.new("RGB", (size * S, size * S), (0, 0, 0))
    star(im, size * S // 2, size * S // 2, d, "sun", corona=1.0, spots=False)
    im = downscale(im, size, size)
    return im, im.convert("L").point(lambda p: min(255, p * 3))


def paste_c(im, spr, x, y):
    sp, m = spr
    im.paste(sp, (int(x - sp.width / 2), int(y - sp.height / 2)), m)


# ---------------------------------------------------------------- Layout

def background():
    img, _ = new_frame(61)
    header_band(img, ["You're moving at", "2 MILLION km/h"], "2 MILLION")
    d = ImageDraw.Draw(img)
    y = 1470 * S
    note = "*relative to the cosmic background radiation · illustrations"
    d.text(((WS - d.textlength(note, font=f(24 * S))) / 2, y), note, font=f(24 * S), fill=SEC)
    cta = "Why don't we feel any of it? Comment ↓"
    d.text(((WS - d.textlength(cta, font=f(34 * S, bold=True))) / 2, y + 40 * S), cta,
           font=f(34 * S, bold=True), fill=FG)
    return downscale(img, W, H)


class Assets:
    def __init__(self):
        self.earth_big = [sprite_planet(520, "earth", light=(-0.6, -0.3, 0.75), lon0=150 - k * 3, tilt=-23)
                          for k in range(40)]
        self.earth_small = sprite_planet(34, "earth", light=(-1, 0, 0.3), lon0=200)
        self.sun = sprite_star(110)
        g = galaxy(900)
        self.galaxy = g.resize((860, 860), Image.LANCZOS)
        self.galaxy_small = g.resize((230, 230), Image.LANCZOS).resize((230, 92), Image.LANCZOS)
        self.cmb = cmb(940, 470)


def scene(bg, A, k, u):
    """Szene k zur lokalen Zeit u (s) auf Kopie des Hintergrunds."""
    im = bg.copy()
    d = ImageDraw.Draw(im)
    if k == 0:                                                     # Erde dreht sich
        paste_c(im, A.earth_big[min(39, int(u / SCENE * 39))], SCX, SCY)
        d.arc([SCX - 300, SCY - 70, SCX + 300, SCY + 90], 20, 160, fill=ACC, width=4)   # Drehpfeil am Aequator
        d.polygon([(SCX + 298, SCY + 22), (SCX + 266, SCY + 32), (SCX + 288, SCY + 54)], fill=ACC)   # Erde dreht nach Osten
    elif k == 1:                                                   # Erde um die Sonne
        rx, ry = 390, 150
        d.ellipse([SCX - rx, SCY - ry, SCX + rx, SCY + ry], outline=(80, 90, 116), width=2)
        ang = math.radians(100) + u * 0.55
        ex, ey = SCX + rx * math.cos(ang), SCY + ry * math.sin(ang)
        for j in range(1, 30):                                     # Spur
            aj = ang - j * 0.02
            px, py = SCX + rx * math.cos(aj), SCY + ry * math.sin(aj)
            c = int(255 * (1 - j / 30))
            d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=(c, int(c * 0.7), int(c * 0.33)))
        front = math.sin(ang) > 0
        if not front:
            paste_c(im, A.earth_small, ex, ey)
        paste_c(im, A.sun, SCX, SCY)
        if front:
            paste_c(im, A.earth_small, ex, ey)
        d = ImageDraw.Draw(im)
        d.text((ex + 26, ey - 16), "Earth", font=f(26, bold=True), fill=FG, stroke_width=2, stroke_fill=(8, 10, 14))
    elif k == 2:                                                   # Sonne um die Milchstrasse
        g = A.galaxy.rotate(u * 4, resample=Image.BICUBIC)
        im.paste(g, (SCX - g.width // 2, SCY - g.height // 2), g)
        d = ImageDraw.Draw(im)
        rr = 0.52 * 430
        ang = math.radians(150) - u * 0.07
        sx, sy = SCX + rr * math.cos(ang), SCY + rr * math.sin(ang)
        d.arc([SCX - rr, SCY - rr, SCX + rr, SCY + rr], math.degrees(ang), math.degrees(ang) + 40, fill=ACC, width=3)
        d.ellipse([sx - 7, sy - 7, sx + 7, sy + 7], fill=ACC)
        d.ellipse([sx - 18, sy - 18, sx + 18, sy + 18], outline=ACC, width=2)
        d.text((sx - 150, sy + 24), "Sun · one lap ≈ 230 million years", font=f(24, bold=True), fill=FG,
               stroke_width=2, stroke_fill=(8, 10, 14))
    else:                                                          # Milchstrasse vs. Hintergrundstrahlung
        c = A.cmb
        im.paste(c, (SCX - c.width // 2, SCY - c.height // 2), c)
        d = ImageDraw.Draw(im)
        gx = SCX - 300 + u * 160
        for j in range(1, 12):
            xx = gx - 110 - j * 18
            d.line([xx, SCY - 18 + (j % 3) * 18, xx + 30, SCY - 18 + (j % 3) * 18], fill=(230, 235, 245), width=2)
        g = A.galaxy_small
        im.paste(g, (int(gx - g.width / 2), int(SCY - g.height / 2)), g)
        d = ImageDraw.Draw(im)
        d.text((gx - 70, SCY + 40), "Milky Way", font=f(26, bold=True), fill=FG, stroke_width=2, stroke_fill=(8, 10, 14))
        d.text((SCX - 300, SCY - 270), "Afterglow of the Big Bang", font=f(26), fill=SEC,
               stroke_width=2, stroke_fill=(8, 10, 14))
    return im


def frame(bg, A, t):
    if t >= 4 * SCENE:                                             # Schluss
        k, u = 0, SCENE * 0.5 + (t - 4 * SCENE) * 0.3
        im = scene(bg, A, 0, min(u, SCENE))
        lv = 3
    else:
        k = int(t // SCENE)
        u = t - k * SCENE
        im = scene(bg, A, k, u)
        if u < XF and k > 0:                                       # Ueberblendung von der vorigen Szene
            prev = scene(bg, A, k - 1, SCENE)
            im = Image.blend(prev, im, ease(u / XF))
        lv = k
    d = ImageDraw.Draw(im)
    st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
    lo = SPEEDS[lv - 1] if lv > 0 else 0
    hi = SPEEDS[lv]
    val = hi if t >= 4 * SCENE else lo + (hi - lo) * ease((t - lv * SCENE) / 2.0)
    num = f"{val:,.0f} km/h"
    d.text(((W - d.textlength(num, font=f(72, bold=True))) / 2, 540), num, font=f(72, bold=True),
           fill=ACC if lv == 3 else FG, **st)
    lab = LABELS[lv]
    d.text(((W - d.textlength(lab, font=f(32))) / 2, 632), lab, font=f(32), fill=SEC, **st)
    for j in range(4):                                             # Stufenanzeige
        x = W / 2 - 54 + j * 36
        r = 9 if j == lv else 6
        d.ellipse([x - r, 1420 - r, x + r, 1420 + r], fill=ACC if j <= lv else HAIR)
    if t >= 4 * SCENE:
        a = ease((t - 4 * SCENE) / 0.5)
        col = tuple(int(c * a) for c in FG)
        txt = "…and you feel none of it."
        d.text(((W - d.textlength(txt, font=f(52, bold=True))) / 2, 1290), txt, font=f(52, bold=True), fill=col, **st)
    return im


def main():
    bg = background()
    A = Assets()
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (2.5, 5.5, 8.8, 12.0, 14.5):
            cinematic(frame(bg, A, t), 0).save(prev / f"speed-{t:.1f}.png")
        print("preview saved")
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(LOOP * FPS)
    out = OUT / "w8-speed-through-space.mp4"
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg, A, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg, A, 12.0), 0).save(OUT / "w8-speed-through-space-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
