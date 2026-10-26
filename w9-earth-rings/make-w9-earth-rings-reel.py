"""Woche 9, Mi 28.10.2026: "What if Earth had SATURN's rings?" (Typ d, Winner-Variante von w8-counter-earth-reel).
Eine Animation in 4 Phasen, 15,5 s:
(1) Erde aus dem All mit Saturns Ringen, auf Erdgroesse skaliert. (2) Blick vom Boden auf 41 Grad Nord (New York, Rom)
an einem Sommerabend: riesiger Bogen am Suedhimmel, Erdschatten schneidet ihn ab. (3) Breitengrad wandert Richtung
Aequator: Bogen steigt hoeher und wird schmaler. (4) Wendung: Die Erde hatte vielleicht wirklich Ringe (466 Mio. Jahre).

Fakten (vor Produktion geprueft):
  Saturn-Radius 60.268 km; B-Ring innen ~92.000 km (1,53 R_S), A-Ring aussen ~136.775 km (2,27 R_S) (NASA Saturn Fact
  Sheet). Auf die Erde (6.371 km) skaliert: 9.750-14.460 km vom Erdmittelpunkt = ~3.400-8.100 km Hoehe.
  Ringe liegen in der Aequatorebene; im Nord-Sommer beleuchtet die Sonne die Nordseite (Bild: Sonnendeklination +23,4).
  Himmelsansicht physikalisch berechnet (Strahl-Ebene-Schnitt, Erdschatten-Zylinder).
  Tomkins, Martin & Cawood 2024 (Earth and Planetary Science Letters, Monash University): 21 Einschlagkrater aus dem
  Ordovizium liegen nahe dem damaligen Aequator -> Hypothese eines Rings vor ~466 Mio. Jahren (aus einem zerbrochenen
  Asteroiden). Als Studie/Hypothese gekennzeichnet.

Hook-Varianten:
  1 "What if Earth had SATURN's rings?" (gewaehlt)   2 "This is what the sky would look like with rings"
  3 "Earth with rings. The view from your city."   4 "Earth may have had rings once"   5 "Rings over New York?"

    python make-w9-earth-rings-reel.py [--preview DIR]  ->  w9-earth-rings.mp4, -cover.png
"""

import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bodies import planet, smooth
from brandkit import S, FG, SEC, ACC, f, downscale
from reelkit import W as WS, H as HS, new_frame, header_band, cinematic

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
LOOP = 15.5
R_IN, R_OUT = 1.24, 2.27                       # Ringe in Planetenradien (C- bis A-Ring)
DECL = math.radians(23.4)                      # Nord-Sommer
SUN_DEP = math.radians(7)                      # Sonne 7 Grad unter dem Westhorizont
AZ_HALF = 70.0                                 # Weitwinkel: +-70 Grad Azimut ueber die Bildbreite
PX_DEG = W / (2 * AZ_HALF)                     # gleicher Massstab fuer Hoehe (zylindrische Projektion)
HOR_Y = 1420
CAPTIONS = [(0.0, "Same rings, scaled to Earth.", "3,400 to 8,100 km above us."),
            (3.5, "From New York or Rome,", "a summer evening would look like this."),
            (9.0, "Closer to the equator,", "the arch climbs toward the top of the sky."),
            (12.0, "", "")]


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ring_profile(rad):
    """Helligkeitsprofil wie bodies._ring (C-, B-, A-Ring, Cassini-Teilung, Encke-Luecke), rad in Planetenradien."""
    p = smooth(1.24, 1.30, rad) * (1 - smooth(1.50, 1.53, rad)) * 0.28
    p = p + smooth(1.52, 1.56, rad) * (1 - smooth(1.93, 1.95, rad)) * 1.0
    p = p + smooth(2.02, 2.04, rad) * (1 - smooth(2.25, 2.27, rad)) * 0.72
    p = p * (1 - smooth(2.20, 2.205, rad) * (1 - smooth(2.215, 2.22, rad)) * 0.8)
    return p * (0.9 + 0.1 * np.sin(rad * 140))


# ---------------------------------------------------------------- Himmelsansicht

class Sky:
    def __init__(self):
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
        self.az = np.radians((xs - W / 2) / PX_DEG)          # 0 = Sueden, + = Westen (rechts)
        self.el = np.radians((HOR_Y - ys) / PX_DEG)
        rng = np.random.default_rng(4)
        # Landschaftssilhouette: sanfte Huegel + Baumreihe
        x = np.arange(W, dtype=np.float32)
        hill = HOR_Y + 40 + 14 * np.sin(x / 210) + 10 * np.sin(x / 77 + 1.3)
        trees = np.zeros(W, np.float32)
        for _ in range(70):
            c, w, h = rng.uniform(0, W), rng.uniform(14, 40), rng.uniform(18, 60)
            trees = np.maximum(trees, h * np.sqrt(np.clip(1 - ((x - c) / w) ** 2, 0, 1)))
        self.ground = hill - trees
        self.lights = [(rng.uniform(0, W), rng.uniform(18, 70), rng.uniform(0.9, 1.8)) for _ in range(45)]   # Ortslichter knapp unter der Kante

    def render(self, base, lat_deg):
        """Ring + Daemmerung + Boden fuer Breitengrad lat_deg auf base (RGB 1080x1920)."""
        phi = math.radians(lat_deg)
        o = np.array([math.cos(phi), 0.0, math.sin(phi)])
        up = o
        east = np.array([0.0, 1.0, 0.0])
        north = np.array([-math.sin(phi), 0.0, math.cos(phi)])
        south = -north
        # Blick nach Sueden, zylindrische Projektion: links Osten, rechts Westen
        ce, se = np.cos(self.el)[..., None], np.sin(self.el)[..., None]
        horiz = np.cos(self.az)[..., None] * south + np.sin(self.az)[..., None] * (-east)
        d = ce * horiz + se * up
        elev = np.degrees(np.arcsin(np.clip(d @ up, -1, 1)))
        # Sonne: Deklination +23,4, steht 7 Grad unter dem Westhorizont (Azimut grob WNW)
        west = -east
        s = west * math.cos(SUN_DEP) - up * math.sin(SUN_DEP) + north * 0.35
        s = s / np.linalg.norm(s)
        img = np.asarray(base, np.float32).copy()
        # Daemmerung: Glimmen zum Westen (rechts) und zum Horizont
        toward = np.clip(d @ s, -1, 1)
        below_zen = (self.el < math.pi / 2)
        glow = below_zen * np.exp(-np.clip(elev, 0, 90) / 9.0) * (0.35 + 0.65 * np.clip(toward + 0.2, 0, 1) ** 2)
        img += glow[..., None] * np.array([150, 92, 70])[None, None, :] * 0.9
        img += (below_zen * np.exp(-np.clip(elev, 0, 90) / 28.0) * 0.4)[..., None] * np.array([40, 52, 90])[None, None, :]
        # Ring: Schnitt Blickstrahl mit Aequatorebene (z=0)
        dz = d[..., 2]
        with np.errstate(divide="ignore", invalid="ignore"):
            t = np.where(dz < -1e-6, -o[2] / dz, -1)
        p = o[None, None, :] + d * t[..., None]
        rad = np.linalg.norm(p, axis=-1)
        prof = np.where((t > 0) & (elev > -6), ring_profile(rad), 0)
        # Erdschatten: Zylinder mit Radius 1 entlang -s
        along = p @ s
        perp = np.linalg.norm(p - along[..., None] * s[None, None, :], axis=-1)
        lit = 1 - smooth(1.02, 0.97, perp) * (along < 0)
        tone = np.stack([196 + 36 * smooth(1.45, 1.6, rad), 176 + 38 * smooth(1.45, 1.6, rad),
                         150 + 22 * smooth(1.45, 1.6, rad)], -1)
        warm = np.array([1.0, 0.86, 0.72])                      # Abendlicht
        ring = tone * warm * (0.12 + 0.88 * lit)[..., None]
        a = np.clip(prof * 0.95, 0, 0.92)[..., None]
        img = img * (1 - a) + ring * a
        out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        # Boden
        dr = ImageDraw.Draw(out)
        pts = [(0, H)] + [(x, float(self.ground[x])) for x in range(0, W, 3)] + [(W, float(self.ground[-1])), (W, H)]
        dr.polygon(pts, fill=(9, 11, 15))
        for x, y, r in self.lights:
            y = max(self.ground[int(x)], HOR_Y + 40) + y
            dr.ellipse([x - r, y - r, x + r, y + r], fill=(255, 196, 120))
        return out


# ---------------------------------------------------------------- Weltraumansicht

def space_view(base, t):
    img = Image.new("RGB", (WS, HS), (0, 0, 0))
    planet(img, WS // 2, int(1080 * S), 300, "earth", light=(-0.75, -0.25, 0.6), lon0=200 + 12 * t, tilt=-8,
           ring_tilt=17)
    sm = downscale(img, W, H)
    m = sm.convert("L").point(lambda v: min(255, v * 4))
    out = base.copy()
    out.paste(sm, (0, 0), m)
    return out


def background():
    img, _ = new_frame(53)
    header_band(img, ["What if Earth had", "SATURN's rings?"], "SATURN's")
    return downscale(img, W, H)


def overlay_text(im, t):
    d = ImageDraw.Draw(im)
    st = dict(stroke_width=4, stroke_fill=(8, 10, 14))
    cap = [c for c in CAPTIONS if t >= c[0]][-1]
    ca = ease((t - cap[0]) / 0.4)
    for j, ln in enumerate(cap[1:]):
        if ln:
            fo = f(42, bold=True) if j == 0 else f(36)
            c = FG
            d.text(((W - d.textlength(ln, font=fo)) / 2, 550 + j * 58), ln, font=fo,
                   fill=tuple(int(v * ca) for v in c), **st)
    if 3.5 <= t < 12.0:
        lat = lat_at(t)
        tag = f"{abs(lat):.0f}° N · looking south"
        d.text((60, 1610), tag, font=f(26, bold=True), fill=ACC, **st)
    if t >= 12.0:                                                 # Wendung
        a = ease((t - 12.0) / 0.4)
        for j, (ln, fo, c) in enumerate([("Plot twist:", f(40, bold=True), FG),
                                          ("Earth may have HAD rings,", f(52, bold=True), ACC),
                                          ("466 million years ago.", f(52, bold=True), ACC),
                                          ("Study: Monash University, 2024", f(30), FG)]):
            d.text(((W - d.textlength(ln, font=fo)) / 2, 540 + [0, 58, 124, 196][j]), ln, font=fo,
                   fill=tuple(int(v * a) for v in c), **st)
    note = "Saturn's rings scaled to Earth · sky computed, illustration"
    d.text(((W - d.textlength(note, font=f(22))) / 2, 1700), note, font=f(22), fill=SEC, **st)
    cta = "Send this to someone who'd move for this view"
    d.text(((W - d.textlength(cta, font=f(34, bold=True))) / 2, 1740), cta, font=f(34, bold=True), fill=FG, **st)


def lat_at(t):
    return 41 - 31 * ease((t - 9.0) / 2.6)


def frame(bg, sky, t):
    if t < 3.5 or t >= 12.0:
        im = space_view(bg, t)
        if 3.1 <= t < 3.5:                                       # Ueberblendung ins Himmelsbild
            im = Image.blend(im, sky.render(bg, 41), ease((t - 3.1) / 0.4))
        if 12.0 <= t < 12.4:
            im = Image.blend(sky.render(bg, lat_at(t)), im, ease((t - 12.0) / 0.4))
    else:
        im = sky.render(bg, lat_at(t))
    overlay_text(im, t)
    return im


def main():
    bg = background()
    sky = Sky()
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (1.5, 5.5, 10.0, 11.8, 13.5):
            cinematic(frame(bg, sky, t), 0).save(prev / f"rings-{t:.1f}.png")
        print("preview saved")
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(LOOP * FPS)
    out = OUT / "w9-earth-rings.mp4"
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg, sky, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg, sky, 5.5), 0).save(OUT / "w9-earth-rings-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
