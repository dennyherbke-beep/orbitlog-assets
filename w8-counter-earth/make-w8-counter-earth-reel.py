"""Woche 8, Fr 23.10.2026: "What if there's a SECOND Earth behind the Sun?" (Typ d absurde Frage, Snapshot-Idee
15.10.2026 nach astrolensofficial). Schraege Draufsicht aufs innere Sonnensystem, eine Animation in 5 Phasen:
(1) Gegenerde auf derselben Bahn, immer gegenueber - von uns aus hinter der Sonne? (2) Bahnen sind Ellipsen -> sie
wuerde hervorlugen (Inset "View from Earth"). (3) Ihre Schwerkraft wuerde an Venus und Mars ziehen. (4) STEREO-Sonden
schauen seit 2006 hinter die Sonne. (5) Aufloesung "No second Earth." 15 s.

Fakten (vor Produktion geprueft):
  Idee: Antichthon des Philolaos (Pythagoreer, 5. Jh. v. Chr.). Erdbahn-Exzentrizitaet 0,0167 (NASA Planetary Fact
  Sheet): bei gleicher Bahn und halber Umlaufzeit Versatz wuerde die wahre Anomalie bis ~4e = 3,8 Grad von der exakten
  Gegenposition abweichen -> von der Erde aus bis ~1,9 Grad neben der Sonne (~3,6 Sonnendurchmesser von je 0,53 Grad).
  Der Lagrange-Punkt L3 ist instabil (Stoerung durch Venus). NASA STEREO-A/B (Start Okt. 2006) wanderten vor und
  hinter der Erde um die Sonne; 2011 sahen beide zusammen die ganze Sonne inkl. Rueckseite.
  Darstellung: Bahnen nicht massstaeblich, Exzentrizitaet stark uebertrieben (im Bild vermerkt).

Hook-Varianten:
  1 "What if there's a SECOND Earth behind the Sun?" (gewaehlt)   2 "Could a planet hide behind the Sun forever?"
  3 "Ancient Greeks believed in a second Earth"   4 "The planet we can never see"   5 "Is there a twin Earth hiding from us?"

    python make-w8-counter-earth-reel.py [--preview DIR]  ->  w8-counter-earth.mp4, -cover.png
"""

import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, downscale
from bodies import planet, star
from reelkit import W as WS, new_frame, header_band, blob, cinematic

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
LOOP = 15.0
SCX, SCY = 540, 1010
FLAT = 0.62                                   # schraege Draufsicht: y-Stauchung
A_E, A_V, A_M = 320, 225, 430                 # Bahnradien (nicht massstaeblich)
E_MAX = 0.10                                  # stark uebertriebene Exzentrizitaet
OMEGA = 0.33                                  # rad/s fuer die Erde
CAPTIONS = [(0.0, "Same orbit, always opposite us.", "Hidden behind the Sun forever?"),
            (4.0, "But orbits are ellipses.", "It would peek out from behind the Sun."),
            (8.0, "And its gravity would tug", "on Venus and Mars."),
            (11.0, "Spacecraft have looked", "behind the Sun since 2006."),
            (13.0, "", "")]


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def kepler(M, e):
    E = M
    for _ in range(8):
        E = E - (E - e * math.sin(E) - M) / (1 - e * math.cos(E))
    nu = 2 * math.atan2(math.sqrt(1 + e) * math.sin(E / 2), math.sqrt(1 - e) * math.cos(E / 2))
    r = 1 - e * math.cos(E)
    return nu, r


def orb(a, M, e):
    """Bahnposition (Ebene) mit der Sonne im Brennpunkt -> (x, y) in px, ungestaucht."""
    nu, r = kepler(M, e)
    return a * r * math.cos(nu), a * r * math.sin(nu)


def scr(x, y):
    return SCX + x, SCY + y * FLAT


def body_sprite(d, kind, lon0=180.0):
    size = int(d + 8)
    im = Image.new("RGB", (size * S, size * S), (0, 0, 0))
    planet(im, size * S // 2, size * S // 2, d, kind, light=(0, 0, 1), lon0=lon0, glow=False)
    im = downscale(im, size, size)
    m = Image.new("L", (size * 4, size * 4), 0)
    c, rr = size * 2, d * 2
    ImageDraw.Draw(m).ellipse([c - rr, c - rr, c + rr, c + rr], fill=255)
    return im, m.resize((size, size), Image.LANCZOS)


def lit_sprite(d, kind, lon0=180.0, n=16):
    """Sprites mit Licht aus n Richtungen (Sonne in der Mitte der Szene)."""
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n
        size = int(d + 8)
        im = Image.new("RGB", (size * S, size * S), (0, 0, 0))
        planet(im, size * S // 2, size * S // 2, d, kind, light=(math.cos(a), math.sin(a) * FLAT, 0.35), lon0=lon0,
               glow=False)
        im = downscale(im, size, size)
        m = Image.new("L", (size * 4, size * 4), 0)
        c, rr = size * 2, d * 2
        ImageDraw.Draw(m).ellipse([c - rr, c - rr, c + rr, c + rr], fill=255)
        out.append((im, m.resize((size, size), Image.LANCZOS)))
    return out


def probe_sprite(w=44):
    """Kleine Raumsonde (STEREO-artig): Bus mit Goldfolie, zwei Solarpaneele mit Zellraster, schattiert."""
    k = 4
    im = Image.new("RGBA", (w * k, w * k // 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    W2, H2 = im.size
    bw, bh = W2 * 0.26, H2 * 0.62
    for i in range(int(bh)):                                         # Bus: goldener Verlauf
        t = i / bh
        c = (int(235 - 90 * t), int(190 - 80 * t), int(90 - 50 * t), 255)
        d.line([W2 / 2 - bw / 2, H2 / 2 - bh / 2 + i, W2 / 2 + bw / 2, H2 / 2 - bh / 2 + i], fill=c)
    pw, ph = W2 * 0.34, H2 * 0.40
    for side in (-1, 1):
        x0 = W2 / 2 + side * (bw / 2 + 4 * k) - (pw if side < 0 else 0)
        d.rectangle([x0, H2 / 2 - ph / 2, x0 + pw, H2 / 2 + ph / 2], fill=(40, 58, 110, 255))
        for gx in range(1, 5):
            xx = x0 + pw * gx / 5
            d.line([xx, H2 / 2 - ph / 2, xx, H2 / 2 + ph / 2], fill=(110, 130, 180, 255), width=k // 2)
        d.line([x0, H2 / 2, x0 + pw, H2 / 2], fill=(110, 130, 180, 255), width=k // 2)
        d.line([W2 / 2 + side * bw / 2, H2 / 2, W2 / 2 + side * (bw / 2 + 4 * k), H2 / 2], fill=(200, 200, 210, 255), width=k)
    im = im.resize((w, w // 2), Image.LANCZOS)
    return im.convert("RGB"), im.getchannel("A")


def background():
    img, _ = new_frame(71)
    header_band(img, ["What if there's a SECOND", "Earth behind the Sun?"], "SECOND")
    d = ImageDraw.Draw(img)
    y = 1470 * S
    note = "Not to scale · orbit shapes exaggerated"
    d.text(((WS - d.textlength(note, font=f(24 * S))) / 2, y), note, font=f(24 * S), fill=SEC)
    cta = "What would you have named it? Comment ↓"
    d.text(((WS - d.textlength(cta, font=f(34 * S, bold=True))) / 2, y + 40 * S), cta,
           font=f(34 * S, bold=True), fill=FG)
    return downscale(img, W, H)


class Assets:
    def __init__(self):
        size = 300
        im = Image.new("RGB", (size * S, size * S), (0, 0, 0))
        star(im, size * S // 2, size * S // 2, 86, "sun", corona=1.0, spots=False)
        im = downscale(im, size, size)
        self.sun = (im, im.convert("L").point(lambda p: min(255, p * 3)))
        self.earth = lit_sprite(40, "earth", lon0=200)
        self.twin = lit_sprite(40, "earth", lon0=20)
        self.venus = lit_sprite(32, "venus")
        self.mars = lit_sprite(26, "mars")
        self.probe = probe_sprite()
        mini = Image.new("RGB", (80 * S, 80 * S), (0, 0, 0))
        star(mini, 40 * S, 40 * S, 30, "sun", corona=0.6, spots=False)
        mini = downscale(mini, 80, 80)
        self.sun_mini = (mini, mini.convert("L").point(lambda p: min(255, p * 3)))
        self.twin_mini = body_sprite(16, "earth", lon0=20)


def paste_c(im, spr, x, y):
    sp, m = spr
    im.paste(sp, (int(x - sp.width / 2), int(y - sp.height / 2)), m)


def lit(sprites, x, y):
    """Sprite mit Licht von der Sonne (Szenenmitte) waehlen."""
    a = math.atan2(-(y - SCY) / FLAT, -(x - SCX)) % (2 * math.pi)
    return sprites[round(a / (2 * math.pi) * len(sprites)) % len(sprites)]


def dashed(d, p0, p1, fill, dash=12, gap=9, width=2):
    L = math.dist(p0, p1)
    n = int(L // (dash + gap)) + 1
    for i in range(n):
        a, b = i * (dash + gap) / L, min(1, (i * (dash + gap) + dash) / L)
        d.line([p0[0] + (p1[0] - p0[0]) * a, p0[1] + (p1[1] - p0[1]) * a,
                p0[0] + (p1[0] - p0[0]) * b, p0[1] + (p1[1] - p0[1]) * b], fill=fill, width=width)


def arrow(d, p0, p1, fill, width=4):
    d.line([p0, p1], fill=fill, width=width)
    ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
    for s in (2.6, -2.6):
        d.line([p1, (p1[0] + 16 * math.cos(ang + s), p1[1] + 16 * math.sin(ang + s))], fill=fill, width=width)


def frame(bg, A, t):
    im = bg.copy()
    d = ImageDraw.Draw(im)
    st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
    e = E_MAX * ease((t - 4.2) / 2.0)
    M = 1.9 + OMEGA * t
    ex, ey = orb(A_E, M, e)
    cx, cy = orb(A_E, M + math.pi, e)
    twin_a = ease((t - 0.8) / 0.8) * (1 - ease((t - 13.2) / 0.6))
    planets_a = ease((t - 8.0) / 0.6)
    probes_a = ease((t - 11.0) / 0.6)
    # Bahnen
    pts = [scr(*orb(A_E, k / 120 * 2 * math.pi, e)) for k in range(121)]
    d.line(pts, fill=(84, 96, 126), width=2)
    if planets_a > 0:
        c = tuple(int(v * planets_a) for v in (60, 70, 96))
        for a in (A_V, A_M):
            d.ellipse([SCX - a, SCY - a * FLAT, SCX + a, SCY + a * FLAT], outline=c, width=2)
    # Sonde-Sichtkegel (hinter allem)
    E_s, C_s = scr(ex, ey), scr(cx, cy)
    if probes_a > 0:
        cone = Image.new("RGB", im.size, (0, 0, 0))
        dc = ImageDraw.Draw(cone)
        fx, fy = scr(-ex * 1.05, -ey * 1.05)                     # Bereich hinter der Sonne (von der Erde aus)
        for sgn in (1, -1):
            px, py = scr(*orb(A_E * 1.0, M + sgn * 1.75, e))
            ang = math.atan2(fy - py, fx - px) + math.pi / 2
            dx, dy = 46 * math.cos(ang), 46 * math.sin(ang)
            dc.polygon([(px, py), (fx + dx, fy + dy), (fx - dx, fy - dy)],
                       fill=tuple(int(v * probes_a) for v in (46, 40, 20)))
        cone = cone.filter(ImageFilter.GaussianBlur(6))
        im = ImageChops.add(im, cone)
        d = ImageDraw.Draw(im)
    # Sichtlinie von der Erde durch die Sonne
    if twin_a > 0:
        far = (SCX + (SCX - E_s[0]) * 1.25, SCY + (SCY - E_s[1]) * 1.25)
        dashed(d, E_s, far, tuple(int(v * twin_a) for v in (200, 170, 110)))
    # Koerper nach Tiefe zeichnen (hinten = kleineres y)
    items = [(SCY, "sun", SCX, SCY), (E_s[1], "earth", *E_s)]
    if twin_a > 0:
        items.append((C_s[1], "twin", *C_s))
    if planets_a > 0:
        vx, vy = scr(*orb(A_V, 0.4 + OMEGA * 1.62 * t, 0))
        mx, my = scr(*orb(A_M, 4.2 + OMEGA * 0.53 * t, 0))
        items += [(vy, "venus", vx, vy), (my, "mars", mx, my)]
    for _, kind, x, y in sorted(items, key=lambda i: i[0]):
        if kind == "sun":
            paste_c(im, A.sun, x, y)
        elif kind == "twin":
            sp, m = lit(A.twin, x, y)
            im.paste(sp, (int(x - sp.width / 2), int(y - sp.height / 2)), m.point(lambda p: int(p * twin_a)))
        else:
            spr = {"earth": A.earth, "venus": A.venus, "mars": A.mars}[kind]
            if kind in ("venus", "mars"):
                sp, m = lit(spr, x, y)
                im.paste(sp, (int(x - sp.width / 2), int(y - sp.height / 2)), m.point(lambda p: int(p * planets_a)))
            else:
                paste_c(im, lit(spr, x, y), x, y)
    d = ImageDraw.Draw(im)
    d.text((E_s[0] + 26, E_s[1] - 14), "Earth", font=f(26, bold=True), fill=ACC, **st)
    if twin_a > 0.3:
        d.text((C_s[0] + 26, C_s[1] - 14), "Earth 2?", font=f(26, bold=True), fill=FG, **st)
    if planets_a > 0.3:
        for (x, y), name in (((vx, vy), "Venus"), ((mx, my), "Mars")):
            d.text((x + 20, y + 8), name, font=f(22), fill=SEC, **st)
            if t < 11.2:                                          # Zugpfeile vom Zwilling
                ang = math.atan2(C_s[1] - y, C_s[0] - x)
                arrow(d, (x + 26 * math.cos(ang), y + 26 * math.sin(ang)),
                      (x + 70 * math.cos(ang), y + 70 * math.sin(ang)), ACC, width=3)
    if probes_a > 0:
        for sgn, name in ((1, "STEREO-A"), (-1, "STEREO-B")):
            px, py = scr(*orb(A_E, M + sgn * 1.75, e))
            sp, m = A.probe
            im.paste(sp, (int(px - sp.width / 2), int(py - sp.height / 2)), m.point(lambda p: int(p * probes_a)))
            d = ImageDraw.Draw(im)
            d.text((px - 50, py + 18), name, font=f(22, bold=True), fill=FG, **st)
    # Inset: Blick von der Erde (Phase 2)
    ins = ease((t - 4.4) / 0.5) * (1 - ease((t - 7.9) / 0.4))
    if ins > 0:
        bx0, by0, bw, bh = 330, 1316, 420, 112
        box = Image.new("RGB", (bw, bh), (6, 8, 12))
        bd = ImageDraw.Draw(box)
        # Winkel zwischen Sonne und Zwilling, von der Erde aus (ungestauchte Ebene)
        a_sun = math.atan2(-ey, -ex)
        a_tw = math.atan2(cy - ey, cx - ex)
        sep = (a_tw - a_sun + math.pi) % (2 * math.pi) - math.pi
        paste_c(box, A.sun_mini, bw / 2, bh / 2)
        off = math.copysign(min(170, 26 + abs(sep) * 420), sep) if abs(sep) > 0.01 else 0
        tx = bw / 2 + off                                         # nichtlinear, damit es im Kasten bleibt
        if abs(off) > 18:
            paste_c(box, A.twin_mini, tx, bh / 2)
            bd.text((tx - 30, bh / 2 + 14), "Earth 2", font=f(18, bold=True), fill=FG)
        bd.rectangle([0, 0, bw - 1, bh - 1], outline=HAIR, width=2)
        bd.text((10, 6), "View from Earth", font=f(20, bold=True), fill=SEC)
        mask = Image.new("L", box.size, int(255 * ins))
        im.paste(box, (bx0, by0), mask)
        d = ImageDraw.Draw(im)
    # Phasentext
    cap = [c for c in CAPTIONS if t >= c[0]][-1]
    ca = ease((t - cap[0]) / 0.4)
    col = tuple(int(v * ca) for v in FG)
    for j, ln in enumerate(cap[1:]):
        if ln:
            fo = f(40, bold=True) if j == 0 else f(32)
            d.text(((W - d.textlength(ln, font=fo)) / 2, 548 + j * 54), ln, font=fo,
                   fill=col if j == 0 else tuple(int(v * ca) for v in SEC), **st)
    if t >= 13.0:                                                 # Aufloesung
        a = ease((t - 13.0) / 0.4) * (1 - ease((t - 14.6) / 0.4))
        for j, (ln, fo, c) in enumerate([("No second Earth.", f(64, bold=True), ACC),
                                          ("We'd have seen it - or felt its pull.", f(32), FG)]):
            d.text(((W - d.textlength(ln, font=fo)) / 2, 548 + j * 82), ln, font=fo,
                   fill=tuple(int(v * a) for v in c), **st)
    return im


def main():
    bg = background()
    A = Assets()
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (2.5, 6.5, 9.5, 12.2, 13.8):
            cinematic(frame(bg, A, t), 0).save(prev / f"twin-{t:.1f}.png")
        print("preview saved")
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(LOOP * FPS)
    out = OUT / "w8-counter-earth.mp4"
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
    cinematic(frame(bg, A, 2.5), 0).save(OUT / "w8-counter-earth-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
