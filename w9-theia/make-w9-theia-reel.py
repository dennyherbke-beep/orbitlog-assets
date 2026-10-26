"""Woche 9, Di 27.10.2026: "A PLANET crashed into Earth. That's why we have a Moon." (Remake-Regel 6, Vorbild
nebulory "Another World Crashed Into Earth to Create Our Moon?" 10,2K Likes / 41x, Snapshot 23.10.2026; Typ f).
Eine Animation in 6 Phasen, 17 s:
(1) Ur-Erde ohne Mond, Theia kommt von rechts oben. (2) Streifender Einschlag, Blitz, beide schmelzen, Truemmer
fliegen in den Orbit. (3) Truemmerscheibe um die Erde. (4) Sie ballt sich zum Mond, der viel naeher kreist als heute.
(5) Der Mond wandert nach aussen, die Erde kuehlt zur heutigen Erde ab. (6) Beleg: Apollo-Gestein.

Fakten (vor Produktion geprueft):
  Giant-Impact-Hypothese = fuehrende Erklaerung (NASA Science "Moon formation"): vor ~4,5 Mrd. Jahren traf ein etwa
  marsgrosser Koerper (Theia) die junge Erde, aus den Truemmern entstand der Mond. Mars-Durchmesser ~0,53 Erde.
  Mond bildete sich bei wenigen Erdradien (Roche-Grenze ~2,9 R_E, Modelle 3-6 R_E) -> heute 60,3 R_E (384.400 km):
  "mehr als 10x naeher" ist konservativ. Mond entfernt sich 3,8 cm/Jahr (Lunar Laser Ranging, NASA).
  Apollo-Proben: Sauerstoff-Isotope nahezu identisch mit der Erde (NASA). Simulation stark vereinfacht (im Bild vermerkt).

Hook-Varianten:
  1 "A PLANET crashed into Earth. That's why we have a Moon." (gewaehlt)   2 "The Moon is made of Earth"
  3 "Earth was hit by a planet the size of Mars"   4 "4.5 billion years ago, Earth had no Moon"
  5 "Where did the Moon actually come from?"

    python make-w9-theia-reel.py [--preview DIR]  ->  w9-theia.mp4, -cover.png
"""

import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import bodies
from bodies import planet, fbm, mix, col, smooth
from brandkit import S, FG, SEC, ACC, f, downscale
from reelkit import W as WS, new_frame, header_band, cinematic

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
LOOP = 17.0
CX, CY = 540, 1080
LIGHT = (-0.8, -0.35, 0.5)                    # Sonne links oben, fuer alle Koerper
TILT = 0.30                                   # Scheibenebene: y-Stauchung
T_HIT = 3.2
CAPTIONS = [(0.0, "4.5 billion years ago,", "Earth had no Moon."),
            (1.2, "Then a Mars-sized planet,", "Theia, came in at an angle."),
            (T_HIT, "Both melted.", "Debris flew into orbit."),
            (6.2, "The debris formed a ring", "and clumped together."),
            (9.3, "The young Moon circled", "more than 10x closer than today."),
            (12.3, "It's still drifting away:", "3.8 cm every year."),
            (14.9, "", "")]


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- eigene Texturen

def tex_protoearth():
    """Junge Erde: dunkle Basaltkruste, glimmende Risse (nur auf der Nachtseite sichtbar leuchtend)."""
    n = fbm(301, octaves=7, base=4)
    cracks = smooth(0.035, 0.0, np.abs(fbm(302, octaves=6, base=6) - 0.5))
    img = mix(col((54, 46, 42)), col((104, 92, 82)), n)
    img = mix(img, col((150, 70, 30)), cracks * 0.6)
    lava = cracks[..., None] * col((255, 120, 40))
    return img, dict(atmo=(255, 150, 90), atmo_k=0.25, night=lava)


def tex_magma():
    """Nach dem Einschlag: Magmaozean, ueberall selbstleuchtend (night = Emission auch auf der Schattenseite)."""
    n = fbm(311, octaves=7, base=5)
    v = smooth(0.06, 0.0, np.abs(fbm(312, octaves=6, base=5) - 0.5))
    img = mix(col((120, 34, 10)), col((255, 132, 36)), n * 0.7 + v * 0.6)
    img = mix(img, col((255, 226, 150)), v * 0.7)
    return img, dict(atmo=(255, 120, 40), atmo_k=0.9, night=img * 0.85)


def tex_theia():
    """Theia: unbekanntes Aussehen -> neutral-braune Gesteinskugel (Mars-Karte entsaettigt)."""
    img = bodies._map("mars.jpg")
    lum = img.mean(-1, keepdims=True) / 255
    img = mix(img, lum * col((176, 160, 144)), np.full(lum.shape[:2], 0.8, np.float32))
    return np.clip(img, 0, 255), dict(atmo=None)


bodies.TEXTURES.update(protoearth=tex_protoearth, magma=tex_magma, theia=tex_theia)


def sphere(d, kind, lon0=0.0, light=LIGHT):
    """Kugel als (Bild, Maske) in Ausgabe-px, mit Rand fuer Halo."""
    size = int(d * 1.5) + 8
    im = Image.new("RGB", (size * S, size * S), (0, 0, 0))
    planet(im, size * S // 2, size * S // 2, d, kind, light=light, lon0=lon0)
    im = downscale(im, size, size)
    m = im.convert("L").point(lambda p: min(255, p * 6))
    disc = Image.new("L", (size * 4, size * 4), 0)
    c, rr = size * 2, d * 2
    ImageDraw.Draw(disc).ellipse([c - rr, c - rr, c + rr, c + rr], fill=255)
    m = ImageChops.lighter(m, disc.resize((size, size), Image.LANCZOS))
    return im, m


def paste_c(im, spr, x, y, alpha=1.0):
    sp, m = spr
    if alpha < 1:
        m = m.point(lambda p: int(p * alpha))
    im.paste(sp, (int(x - sp.width / 2), int(y - sp.height / 2)), m)


# ---------------------------------------------------------------- Szene

def earth_d(t):
    """Kamera: Erddurchmesser in px (Zoom heraus fuer Scheibe und Mondbahn)."""
    return 380 - 150 * ease((t - 5.0) / 1.6) - 100 * ease((t - 9.0) / 1.4)


def moon_a(t):
    """Mondbahnradius in Erdradien (Bild nicht massstaeblich: heute waeren es 60 R_E)."""
    return 4.0 + 2.5 * ease((t - 12.3) / 2.2)


def moon_th(t):
    return -2.2 + 0.55 * t


IMP = math.radians(-40)                       # Einschlagstelle auf dem Erdrand (Bildwinkel)


class Particles:
    def __init__(self, n=1400):
        rng = np.random.default_rng(9)
        self.R = 1.25 + rng.gamma(2.2, 0.75, n)            # Scheibenradius in Erdradien
        self.th0 = rng.uniform(0, 2 * math.pi, n)
        self.delay = rng.uniform(0, 1.0, n)
        self.size = rng.uniform(1.2, 3.2, n)
        self.hot = rng.uniform(0.6, 1.0, n)
        self.jit = rng.normal(0, 0.05, (n, 2))

    def positions(self, t, D):
        r = D / 2
        om = 1.4 * self.R ** -1.5
        th = self.th0 + om * (t - T_HIT)
        R = self.R.copy()
        # Verklumpen: Teilchen wandern zur Mondposition (6,6 s .. 9,4 s)
        k = np.clip((t - 6.6 - self.delay * 0.8) / 2.0, 0, 1)
        k = k * k * (3 - 2 * k)
        mth = moon_th(t)
        dth = (mth - th + math.pi) % (2 * math.pi) - math.pi
        th = th + dth * k
        R = R + (moon_a(t) - R) * k
        x = CX + R * r * np.cos(th)
        y = CY + R * r * np.sin(th) * TILT
        # Auswurf: vom Einschlagpunkt auf die Bahn hinaus (3,2 s .. ~5,2 s)
        s = np.clip((t - T_HIT - self.delay * 0.7) / 1.3, 0, 1)
        s = 1 - (1 - s) ** 3
        ix, iy = CX + r * math.cos(IMP), CY + r * math.sin(IMP)
        x = ix + (x - ix) * s + self.jit[:, 0] * r * (1 - s)
        y = iy + (y - iy) * s + self.jit[:, 1] * r * (1 - s)
        vis = (t >= T_HIT + self.delay * 0.7) & (k < 0.97)
        front = np.sin(th) > 0
        return x, y, vis, front, k

    def draw(self, t, D, front_layer):
        x, y, vis, front, k = self.positions(t, D)
        layer = Image.new("RGB", (W, H), (0, 0, 0))
        d = ImageDraw.Draw(layer)
        cool = ease((t - 5.5) / 3.0)
        for i in np.nonzero(vis & (front == front_layer))[0]:
            h = self.hot[i] * (1 - cool * 0.75)
            c = (int(120 + 135 * h), int(90 + 110 * h * h), int(70 + 40 * h ** 3))
            s = self.size[i] * (1 - k[i] * 0.5)
            d.ellipse([x[i] - s, y[i] - s, x[i] + s, y[i] + s], fill=c)
        glow = layer.filter(ImageFilter.GaussianBlur(5)).point(lambda p: int(p * 0.9))
        return ImageChops.add(layer, glow)


def flash(t):
    a = ease((t - T_HIT + 0.05) / 0.12) * (1 - ease((t - T_HIT - 0.15) / 1.4))
    if a <= 0:
        return None
    r = earth_d(t) / 2
    ix, iy = CX + r * math.cos(IMP), CY + r * math.sin(IMP)
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    d = ImageDraw.Draw(layer)
    for rad, c in ((340, (120, 60, 20)), (200, (255, 150, 60)), (90, (255, 236, 200))):
        rr = rad * (0.6 + 0.6 * ease((t - T_HIT) / 0.6))
        d.ellipse([ix - rr, iy - rr, ix + rr, iy + rr], fill=tuple(int(v * a) for v in c))
    return layer.filter(ImageFilter.GaussianBlur(40))


def background():
    img, _ = new_frame(97)
    header_band(img, ["A PLANET crashed into Earth.", "That's why we have a Moon."], "PLANET")
    d = ImageDraw.Draw(img)
    y = 1500 * S
    note = "Simulation · leading hypothesis · not to scale"
    d.text(((WS - d.textlength(note, font=f(24 * S))) / 2, y), note, font=f(24 * S), fill=SEC)
    cta = "Send this to someone who stares at the Moon"
    d.text(((WS - d.textlength(cta, font=f(34 * S, bold=True))) / 2, y + 40 * S), cta,
           font=f(34 * S, bold=True), fill=FG)
    return downscale(img, W, H)


def frame(bg, P, t):
    im = bg.copy()
    D = earth_d(t)
    r = D / 2
    st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
    im = ImageChops.add(im, P.draw(t, D, False))                       # Scheibe hinten
    # Mond (hinter der Erde, wenn auf der oberen Bahnhaelfte)
    ma = ease((t - 8.4) / 1.0)
    mth, maa = moon_th(t), moon_a(t)
    mx, my = CX + maa * r * math.cos(mth), CY + maa * r * math.sin(mth) * TILT
    moon = sphere(max(6, D * 0.273), "moon", lon0=0) if ma > 0 else None
    if moon and math.sin(mth) <= 0:
        paste_c(im, moon, mx, my, ma)
    # Erde: Ur-Erde -> Magma -> heutige Erde
    lon = 30 * t
    hot = ease((t - T_HIT) / 0.5)
    today = ease((t - 12.6) / 1.8)
    if hot <= 0:
        earth = sphere(D, "protoearth", lon)
    elif today <= 0:
        earth = sphere(D, "magma", lon)
        if hot < 1:
            pre = sphere(D, "protoearth", lon)
            earth = (Image.blend(pre[0], earth[0], hot), ImageChops.lighter(pre[1], earth[1]))
    else:
        mag = sphere(D, "magma", lon)
        now = sphere(D, "earth", 200 + lon)
        earth = (Image.blend(mag[0], now[0], today), ImageChops.lighter(mag[1], now[1]))
    # Theia: Anflug, Einschlag, verschmilzt
    if t < T_HIT + 0.9:
        dT = 0.53 * D
        p = ease((t - 0.8) / (T_HIT - 0.8)) if t < T_HIT else 1 + (t - T_HIT) * 0.35
        cdist = r + dT / 2
        tx_c, ty_c = CX + cdist * math.cos(IMP), CY + cdist * math.sin(IMP)
        sx, sy = tx_c + 520, ty_c - 330                                 # schraeger Anflug
        tx, ty = sx + (tx_c - sx) * p, sy + (ty_c - sy) * p
        th_a = ease((t - 0.8) / 0.4) * (1 - ease((t - T_HIT) / 0.8))
        if th_a > 0:
            paste_c(im, sphere(dT * (0.75 + 0.25 * min(p, 1)), "theia", 40), tx, ty, th_a)
        paste_c(im, earth, CX, CY)
    else:
        paste_c(im, earth, CX, CY)
    if moon and math.sin(mth) > 0:
        paste_c(im, moon, mx, my, ma)
    im = ImageChops.add(im, P.draw(t, D, True))                        # Scheibe vorn
    fl = flash(t)
    if fl:
        im = ImageChops.add(im, fl)
    d = ImageDraw.Draw(im)
    # Beschriftungen
    if 1.2 <= t < T_HIT:
        a = ease((t - 1.2) / 0.4)
        p = ease((t - 0.8) / (T_HIT - 0.8))
        cdist = r + 0.53 * D / 2
        tx = CX + cdist * math.cos(IMP) + 520 * (1 - p)
        ty = CY + cdist * math.sin(IMP) - 330 * (1 - p)
        d.text((tx - 60, ty + 0.3 * D), "Theia", font=f(30, bold=True), fill=tuple(int(v * a) for v in ACC), **st)
    if ma > 0.5:
        d.text((mx + D * 0.18 if mx < 820 else mx - D * 0.18 - 80, my - 12), "Moon", font=f(26, bold=True), fill=ACC, **st)
    if t < T_HIT:
        d.text((CX - 70, CY + r + 18), "Young Earth", font=f(26, bold=True), fill=SEC, **st)
    if t >= 13.8:                                                       # heutige Entfernung
        a = ease((t - 13.8) / 0.5)
        ln = "Today: 384,400 km, about 30 Earths away"
        d.text(((W - d.textlength(ln, font=f(30, bold=True))) / 2, CY + 130), ln, font=f(30, bold=True),
               fill=tuple(int(v * a) for v in FG), **st)
    # Phasentext
    cap = [c for c in CAPTIONS if t >= c[0]][-1]
    ca = ease((t - cap[0]) / 0.4)
    for j, ln in enumerate(cap[1:]):
        if ln:
            fo = f(40, bold=True) if j == 0 else f(34)
            c = FG if j == 0 else SEC
            d.text(((W - d.textlength(ln, font=fo)) / 2, 560 + j * 56), ln, font=fo,
                   fill=tuple(int(v * ca) for v in c), **st)
    if t >= 14.9:                                                       # Aufloesung + Beleg
        a = ease((t - 14.9) / 0.4) * (1 - ease((t - 16.6) / 0.4))
        for j, (ln, fo, c) in enumerate([("The Moon is made of Earth", f(56, bold=True), ACC),
                                          ("(and Theia).", f(56, bold=True), ACC),
                                          ("Apollo rocks match Earth's chemistry.", f(32), FG)]):
            d.text(((W - d.textlength(ln, font=fo)) / 2, 540 + j * 70), ln, font=fo,
                   fill=tuple(int(v * a) for v in c), **st)
    return im


def main():
    bg = background()
    P = Particles()
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (2.4, 3.4, 4.6, 7.0, 10.5, 14.2, 15.6):
            cinematic(frame(bg, P, t), 0).save(prev / f"theia-{t:.1f}.png")
        print("preview saved")
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(LOOP * FPS)
    out = OUT / "w9-theia.mp4"
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg, P, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg, P, 2.4), 0).save(OUT / "w9-theia-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
