"""Woche 9, So 01.11.2026: "Our solar system vs. a MONSTER black hole" (Remake-Regel 6, Vorbild fromworldsbeyond_
"How Big Is TON 618, the Largest Known Black Hole?" 28K / 269x, Snapshot 09.10.2026; Typ a Massstab-Zoom).
Durchgehender Zoom, 17 s: Erde -> Sonne daneben -> Planetenbahnen bis Neptun -> Voyager 1 -> Ereignishorizont von
TON 618 umschliesst das ganze Sonnensystem.

Fakten (vor Produktion geprueft, 26.10.2026):
  Masse TON 618: Schaetzungen 40,7 Mrd. (Ge et al. 2019, C-IV-Linie) bis 66 Mrd. Sonnenmassen (Shemmer et al. 2004).
  Schwarzschild-Radius = 2,95 km pro Sonnenmasse -> 1,20e11 km = ~800 AU (40,7 Mrd.) bzw. ~1.300 AU (66 Mrd.).
  Im Bild der vorsichtige Wert: Durchmesser ~1.600 AU; Neptunbahn 30,07 AU (Durchmesser ~60 AU) -> passt ~26x hinein.
  Licht braucht fuer 1.600 AU ~9 Tage (1 AU = 8,3 Lichtminuten). Rotverschiebung z = 2,22 -> Licht ~10,8 Mrd. Jahre
  unterwegs. Voyager 1 ~170 AU (Ende 2026, NASA). Sonne = 109 Erddurchmesser.
  "Biggest" ist umstritten (Phoenix A u. a., unsichere Schaetzungen) -> Hook "a MONSTER black hole", Text "one of the
  biggest known". Darstellung: Sonnensystem zum Vergleich in den Horizont gelegt, Akkretionsscheibe illustriert.

Hook-Varianten:
  1 "Our solar system vs. a MONSTER black hole" (gewaehlt)   2 "How big is TON 618?"
  3 "This black hole could swallow our solar system 26 times over"   4 "From Earth to the biggest black holes"
  5 "Light needs 9 days to cross this black hole"

    python make-w9-ton618-reel.py [--preview DIR]  ->  w9-ton618.mp4, -cover.png
"""

import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bodies import planet, star, fbm
from brandkit import S, FG, SEC, ACC, f, downscale
from reelkit import new_frame, header_band, cinematic

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
LOOP = 17.0
CX, CY = 540, 1080
R_BH = 800.0                                   # Ereignishorizont-Radius in AU (vorsichtiger Wert)
ORBITS = [("Mercury", 0.39), ("Venus", 0.72), ("Earth", 1.0), ("Mars", 1.52), ("Jupiter", 5.2), ("Saturn", 9.54),
          ("Uranus", 19.2), ("Neptune", 30.07)]
VOYAGER = 170.0
CAPTIONS = [(0.0, "This is Earth.", ""),
            (1.2, "The Sun:", "109 Earths wide."),
            (3.6, "Our solar system:", "Neptune orbits 30 times farther out than Earth."),
            (6.2, "Voyager 1, our farthest probe:", "about 170 times Earth's distance."),
            (8.4, "Now TON 618,", "one of the biggest black holes known."),
            (10.8, "Its event horizon: ~1,600 AU across.", "Neptune's orbit fits 26 times across it."),
            (13.4, "Light needs about 9 days", "just to cross it."),
            (15.6, "", "")]


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def lerp_log(a, b, s):
    return math.exp(math.log(a) + (math.log(b) - math.log(a)) * s)


# ---------------------------------------------------------------- Stufe A: Erde neben der Sonne

CY_A = 1170                                     # Bildmitte der Stufe A (tiefer, damit die Erde nicht unter den Text rutscht)
SUN_D, SUN_C = 1500, 1000                       # vorgerenderte Sonne: Scheibendurchmesser / Sprite-Halbgroesse


def sun_sprite():
    big = Image.new("RGB", (2 * SUN_C * S, 2 * SUN_C * S), (0, 0, 0))
    star(big, SUN_C * S, SUN_C * S, SUN_D, "sun", corona=0.0, spots=False)
    return downscale(big, 2 * SUN_C, 2 * SUN_C)


def stage_a(bg, SUN, t):
    """Erde oben, Sonne darunter (Abstand nicht massstaeblich); Zoom heraus, Kamera folgt erst, wenn die Sonne passt."""
    de = lerp_log(320, 7, ease((t - 0.9) / 2.4))
    ds = de * 109
    gap = de * 1.2
    ey, sy = 0.0, de / 2 + gap + ds / 2
    focus = ease((2200 - ds) / 1400)
    cam = ey + ((ey - de / 2 + sy + ds / 2) / 2 - ey) * focus
    eys, sys_ = CY_A + (ey - cam), CY_A + (sy - cam)
    k = SUN_D / ds                                                     # Ausgabe-px -> Sprite-px
    sun = SUN.transform((W, H), Image.AFFINE, (k, 0, SUN_C - CX * k, 0, k, SUN_C - sys_ * k), resample=Image.BILINEAR)
    glow = Image.new("RGB", (W, H), (0, 0, 0))                         # Korona in Ausgabe-px statt mitskaliert
    r = ds / 2
    ImageDraw.Draw(glow).ellipse([CX - r - 50, sys_ - r - 50, CX + r + 50, sys_ + r + 50], fill=(150, 80, 25))
    glow = glow.filter(ImageFilter.GaussianBlur(36))
    im = ImageChops.lighter(ImageChops.add(bg, glow), sun)
    if de >= 3:
        e = Image.new("RGB", (W * S, H * S), (0, 0, 0))
        planet(e, int(CX * S), int(eys * S), de, "earth", light=(0, 1, 0.5), lon0=200 + 8 * t)
        e = downscale(e, W, H)
        im.paste(e, (0, 0), e.convert("L").point(lambda p: min(255, p * 6)))
    d = ImageDraw.Draw(im)
    st = dict(stroke_width=4, stroke_fill=(8, 10, 14))
    if t > 1.6 and eys > 700:
        d.text((CX + max(de / 2, 6) + 14, eys - 18), "Earth", font=f(28, bold=True), fill=ACC, **st)
    return im


# ---------------------------------------------------------------- Stufe B/C: Bahnen, Voyager, Schwarzes Loch

class Disk:
    def __init__(self):
        n = fbm(77, h=256, w=512, octaves=5, base=6)
        self.noise = np.asarray(Image.fromarray((n * 255).astype(np.uint8)).resize((1024, 256)), np.float32) / 255

    def render(self, rpx, t):
        """Akkretionsscheibe + Photonenring um einen Horizont mit Radius rpx (Ausgabe-px), schraeg gesehen."""
        ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)                # direkt im Ausgabeformat (speicherschonend)
        dx, dy = (xs - CX) / rpx, (ys - CY) / rpx
        tilt = 0.42
        rr = np.sqrt(dx * dx + (dy / tilt) ** 2)                      # Scheibe in schraeger Ebene
        ang = (np.arctan2(dy / tilt, dx) + t * 0.25) % (2 * np.pi)
        u = (ang / (2 * np.pi) * 1023).astype(int)
        v = np.clip((rr - 1.4) / 1.8 * 255, 0, 255).astype(int)
        tex = self.noise[v, u]
        band = np.clip((rr - 1.45) / 0.25, 0, 1) * np.clip((3.1 - rr) / 1.2, 0, 1)
        heat = np.clip(1.6 - (rr - 1.45) / 1.6, 0, 1)
        k = band * (0.55 + 0.6 * tex)
        dop = 1 + 0.35 * np.clip(-dx / 3, -1, 1)                      # Doppler: linke Seite heller
        col = np.stack([235 * k * dop, (110 + 100 * heat) * k * dop, (36 + 100 * heat ** 2) * k * dop], -1) * 0.8
        rad = np.sqrt(dx * dx + dy * dy)
        ring = np.exp(-((rad - 1.05) / 0.03) ** 2) * 0.9                 # Photonenring
        col += np.stack([255 * ring, 225 * ring, 180 * ring], -1)
        front = (dy > 0) | (rad > 1.0)                                 # hinterer Teil der Scheibe vom Schatten verdeckt
        shadow = rad < 1.0
        col = col * front[..., None]
        img = np.clip(col, 0, 255).astype(np.uint8)
        im = Image.fromarray(img).filter(ImageFilter.GaussianBlur(1.2))
        glow = im.filter(ImageFilter.GaussianBlur(max(4, rpx * 0.12))).point(lambda p: int(p * 0.6))
        im = ImageChops.add(im, glow)
        m = Image.fromarray((shadow * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1))
        return im, m


KEYS = [(3.6, 260.0), (5.8, 12.0), (7.8, 2.6), (10.0, 0.5), (17.0, 0.42)]   # (Zeit, px pro AU)


def scale_at(t):
    if t <= KEYS[0][0]:
        return KEYS[0][1]
    for (t0, s0), (t1, s1) in zip(KEYS, KEYS[1:]):
        if t <= t1:
            return lerp_log(s0, s1, ease((t - t0) / (t1 - t0)))
    return KEYS[-1][1]


def stage_bc(bg, D, t):
    s = scale_at(t)
    im = bg.copy()
    d = ImageDraw.Draw(im)
    st = dict(stroke_width=4, stroke_fill=(8, 10, 14))
    rbh = R_BH * s
    bh_a = ease((1100 - rbh) / 400)
    if bh_a > 0:
        disk, shadow = D.render(rbh, t)
        im = ImageChops.add(im, disk.point(lambda p: int(p * bh_a)))
        im.paste((0, 0, 0), (0, 0, W, H), shadow.point(lambda p: int(p * bh_a)))
        d = ImageDraw.Draw(im)
    # Bahnen + Planeten
    for i, (name, a) in enumerate(ORBITS):
        r = a * s
        if r < 3 or r > 1400:
            continue
        al = min(1.0, (r - 3) / 12) * (0.75 if bh_a > 0.5 else 1.0)
        d.ellipse([CX - r, CY - r, CX + r, CY + r], outline=tuple(int(v * al) for v in (70, 86, 120)), width=2)
        ang = 1.1 + i * 0.83 + t * 0.05 / max(0.3, a) ** 0.5
        px, py = CX + r * math.cos(ang), CY + r * math.sin(ang)
        pr = 4 if name in ("Jupiter", "Saturn") else 3
        d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=(210, 220, 240))
        if 60 < r < 700 and (name in ("Earth", "Jupiter", "Neptune") or r > 120):
            d.text((px + 8, py - 30), name, font=f(24, bold=name == "Neptune"), fill=SEC, **st)
    # Sonne
    sr = max(3.0, min(14.0, 0.00465 * s * 30))
    layer = Image.new("RGB", (W, H), (0, 0, 0))
    ImageDraw.Draw(layer).ellipse([CX - sr * 3, CY - sr * 3, CX + sr * 3, CY + sr * 3], fill=(140, 90, 30))
    layer = layer.filter(ImageFilter.GaussianBlur(sr * 1.5))
    ImageDraw.Draw(layer).ellipse([CX - sr, CY - sr, CX + sr, CY + sr], fill=(255, 236, 190))
    im = ImageChops.add(im, layer)
    d = ImageDraw.Draw(im)
    # Voyager 1
    vr = VOYAGER * s
    va = ease((t - 6.0) / 0.5)
    if va > 0 and vr < 1200:
        vx, vy = CX + vr * math.cos(-0.95), CY + vr * math.sin(-0.95)
        if vr < 6:
            vx, vy = CX + 6 * math.cos(-0.95), CY + 6 * math.sin(-0.95)
        c = tuple(int(v * va) for v in ACC)
        d.line([CX, CY, vx, vy], fill=tuple(int(v * va * 0.5) for v in ACC), width=2)
        d.ellipse([vx - 5, vy - 5, vx + 5, vy + 5], fill=c)
        if vr > 50:
            d.text((vx + 12, vy - 34), "Voyager 1", font=f(26, bold=True), fill=c, **st)
    if bh_a > 0.5:
        a = ease((t - 9.0) / 0.6)
        d.text((CX - d.textlength("TON 618", font=f(40, bold=True)) / 2, CY + rbh * 1.02 + 60), "TON 618",
               font=f(40, bold=True), fill=tuple(int(v * a) for v in ACC), **st)
        sub = "~40 billion Suns (estimate)"
        d.text((CX - d.textlength(sub, font=f(26)) / 2, CY + rbh * 1.02 + 108), sub, font=f(26),
               fill=tuple(int(v * a) for v in FG), **st)
        if t > 10.6:
            a2 = ease((t - 10.6) / 0.5)
            ln = "our solar system, for scale"
            r = 30.07 * s
            d.text((CX - d.textlength(ln, font=f(22)) / 2, CY + r + 10), ln, font=f(22),
                   fill=tuple(int(v * a2) for v in SEC), **st)
    return im


_PROT = None


def protect(bg, im):
    """Kopfzeile (bis ~y 520) und Fusszeile (ab ~y 1690) immer aus dem Hintergrund zeigen."""
    global _PROT
    if _PROT is None:
        y = np.arange(H, dtype=np.float32)[:, None]
        a = np.clip((560 - y) / 60, 0, 1) + np.clip((y - 1650) / 70, 0, 1)
        _PROT = Image.fromarray((np.broadcast_to(a, (H, W)) * 255).astype(np.uint8))
    return Image.composite(bg, im, _PROT)


def background():
    img, _ = new_frame(61)
    header_band(img, ["Our solar system vs.", "a MONSTER black hole"], "MONSTER")
    im = downscale(img, W, H)
    d = ImageDraw.Draw(im)
    st = dict(stroke_width=4, stroke_fill=(8, 10, 14))
    note = "Sizes to scale · distances in stage 1 not to scale · disk illustrated"
    d.text(((W - d.textlength(note, font=f(22))) / 2, 1700), note, font=f(22), fill=SEC, **st)
    cta = "Send this to someone who thinks Earth is big"
    d.text(((W - d.textlength(cta, font=f(34, bold=True))) / 2, 1740), cta, font=f(34, bold=True), fill=FG, **st)
    return im


def frame(bg, SUN, D, t):
    if t < 3.3:
        im = stage_a(bg, SUN, t)
    elif t < 3.8:
        im = Image.blend(stage_a(bg, SUN, 3.3), stage_bc(bg, D, t), ease((t - 3.3) / 0.5))
    else:
        im = stage_bc(bg, D, t)
    if t >= 3.3:
        im = protect(bg, im)
    d = ImageDraw.Draw(im)
    st = dict(stroke_width=4, stroke_fill=(8, 10, 14))
    cap = [c for c in CAPTIONS if t >= c[0]][-1]
    ca = ease((t - cap[0]) / 0.4)
    for j, ln in enumerate(cap[1:]):
        if ln:
            fo = f(42, bold=True) if j == 0 else f(34)
            d.text(((W - d.textlength(ln, font=fo)) / 2, 550 + j * 58), ln, font=fo,
                   fill=tuple(int(v * ca) for v in FG), **st)
    if t >= 15.6:
        a = ease((t - 15.6) / 0.3)
        for j, (ln, fo, c) in enumerate([("Its light traveled", f(44, bold=True), FG),
                                          ("~11 billion years to reach us.", f(44, bold=True), ACC)]):
            d.text(((W - d.textlength(ln, font=fo)) / 2, 550 + j * 60), ln, font=fo,
                   fill=tuple(int(v * a) for v in c), **st)
    return im


def main():
    bg = background()
    SUN = sun_sprite()
    D = Disk()
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (0.6, 1.8, 2.8, 4.6, 7.0, 8.9, 12.0):
            cinematic(frame(bg, SUN, D, t), 0).save(prev / f"ton-{t:.1f}.png")
        print("preview saved")
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(LOOP * FPS)
    out = OUT / "w9-ton618.mp4"
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg, SUN, D, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg, SUN, D, 12.0), 0).save(OUT / "w9-ton618-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
