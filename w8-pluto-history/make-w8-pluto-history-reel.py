"""Woche 8, So 25.10.2026: "Pluto was a planet for 76 YEARS - here's what changed" (Typ f Story-Zeitstrahl,
vorgemerkt von Denny 08.10.2026). Feste Kopfzeile, grosse Jahreszahl, Zeitstrahl unten mit Marker; in der Mitte
eine durchgehende Szene: Pluto schrumpft von der erwarteten Erdgroesse auf die echte, Charon taucht auf, Kuipergürtel-
Nachbarn, Eris, Stempel "DWARF PLANET", New-Horizons-Nahansicht mit dem Herz, Twist: noch keine Runde um die Sonne.

Fakten (vor Produktion geprueft):
  18.02.1930 Clyde Tombaugh findet Pluto (Lowell Observatory) - gesucht wurde Lowells "Planet X", mehrere Erdmassen.
  22.06.1978 James Christy entdeckt Charon -> Pluto-Masse ~0,2 % der Erdmasse (0,0022, NASA Fact Sheet).
  1992 QB1 (Jewitt & Luu): erstes weiteres Kuipergürtel-Objekt. 29.07.2005 Eris bekannt gegeben (Brown, Trujillo,
  Rabinowitz): Durchmesser 2.326 km (Pluto 2.377 km), ~27 % massereicher. 24.08.2006 IAU-Generalversammlung Prag:
  Planet muss seine Bahnumgebung freigeraeumt haben -> Pluto Zwergplanet. 14.07.2015 New Horizons Vorbeiflug
  (Tombaugh Regio = "Herz"). Umlaufzeit 248 Jahre -> erste volle Runde seit Entdeckung ~2178.
  Groessen ab 1978 massstaeblich zur Erde (Pluto 0,187 Erddurchmesser, Charon 0,095). Eris ohne eigene Karte: Mond-Karte
  als Stellvertreter (bei kleiner Darstellung, im Bild vermerkt).

Hook-Varianten:
  1 "Pluto was a planet for 76 YEARS" (gewaehlt)   2 "How Pluto lost its planet title - in 6 dates"
  3 "Pluto shrank. Then it got demoted."   4 "1930: planet. 2006: not a planet. What happened?"
  5 "Pluto hasn't even finished one orbit since we found it"
  Twist-Bahn: Perihel 1989,7, e = 0,249 (NASA Fact Sheet) -> seit 1930 mehr als 39 % des Weges, weil nahe dem Perihel.

    python make-w8-pluto-history-reel.py [--preview DIR]  ->  w8-pluto-history.mp4, -cover.png
"""

import math
import random
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, downscale
from bodies import planet, star
from reelkit import W as WS, new_frame, header_band, cinematic

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
LOOP = 16.0
CY = 1010                                         # Szenenmitte
E_D = 300                                         # Erde
P_TRUE = E_D * 2377 / 12742                       # 56 px
C_TRUE = E_D * 1212 / 12742                       # 28 px
ERIS = E_D * 2326 / 12742
STEPS = [  # (Startzeit, Jahr, Zeile 1, Zeile 2)
    (0.0, "1930", "Pluto is found - planet #9", "Expected: about the size of Earth"),
    (2.4, "1978", "Its moon Charon is found", "Now we can weigh Pluto: 0.2% of Earth"),
    (4.6, "1992", "More icy worlds out there", "Pluto has neighbours"),
    (6.6, "2005", "Eris is found", "Almost Pluto's size - and heavier"),
    (8.8, "2006", "New rule: a planet must clear its orbit", "Pluto can't. Dwarf planet."),
    (11.0, "2015", "New Horizons flies past", "...and finds a giant heart"),
    (13.4, "248 yrs", "One orbit takes 248 years", "It hasn't finished one lap since 1930"),
]
TL_X0, TL_X1, TL_Y = 120, 960, 1388
YEARS = [1930, 1978, 1992, 2005, 2006, 2015]
HEART_LON = 205.0                                 # Tombaugh Regio ("Herz") mittig, per Test 16.10.


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def sphere(d, kind, lon0=180.0, light=(-0.55, -0.35, 0.75)):
    size = int(d + 8)
    im = Image.new("RGB", (size * S, size * S), (0, 0, 0))
    planet(im, size * S // 2, size * S // 2, d, kind, light=light, lon0=lon0, glow=False)
    im = downscale(im, size, size)
    m = Image.new("L", (size * 4, size * 4), 0)
    c, rr = size * 2, d * 2
    ImageDraw.Draw(m).ellipse([c - rr, c - rr, c + rr, c + rr], fill=255)
    return im, m.resize((size, size), Image.LANCZOS)


class Assets:
    def __init__(self):
        self.earth = sphere(E_D, "earth", lon0=200)
        self.pluto_big = sphere(560, "pluto", lon0=HEART_LON, light=(-0.35, -0.3, 0.88))
        sz = 160
        sim = Image.new("RGB", (sz * S, sz * S), (0, 0, 0))
        star(sim, sz * S // 2, sz * S // 2, 46, "sun", corona=0.9, spots=False)
        sim = downscale(sim, sz, sz)
        self.sun = (sim, sim.convert("L").point(lambda p: min(255, p * 3)))
        self.pluto_dot = sphere(30, "pluto", lon0=HEART_LON)
        self.pluto_sizes = {}
        self.charon = sphere(C_TRUE, "charon")
        self.eris = sphere(ERIS, "moon", lon0=90)
        rnd = random.Random(3)
        self.kbo = [(rnd.uniform(-20, 480), rnd.uniform(-190, 190), rnd.uniform(3, 9)) for _ in range(55)]
        self.kbo_spr = {r: sphere(max(4, int(r * 2)), "moon", lon0=rnd.uniform(0, 360)) for r in range(3, 10)}

    def pluto(self, d):
        d = max(20, int(round(d / 4) * 4))                        # Cache in 4-px-Schritten
        if d not in self.pluto_sizes:
            self.pluto_sizes[d] = sphere(d, "pluto", lon0=180)
        return self.pluto_sizes[d]


def paste_c(im, spr, x, y, alpha=1.0):
    sp, m = spr
    if alpha < 1:
        m = m.point(lambda p: int(p * alpha))
    im.paste(sp, (int(x - sp.width / 2), int(y - sp.height / 2)), m)


def background():
    img, _ = new_frame(81)
    header_band(img, ["Pluto was a planet", "for 76 YEARS"], "76 YEARS")
    d = ImageDraw.Draw(img)
    y = 1470 * S
    note = "Sizes to scale with Earth from 1978 · Eris: stand-in map"
    d.text(((WS - d.textlength(note, font=f(24 * S))) / 2, y), note, font=f(24 * S), fill=SEC)
    cta = "PLANET or DWARF PLANET? Comment ↓"
    d.text(((WS - d.textlength(cta, font=f(34 * S, bold=True))) / 2, y + 40 * S), cta,
           font=f(34 * S, bold=True), fill=FG)
    return downscale(img, W, H)


PL_A, PL_E, PL_FLAT = 380, 0.249, 0.42             # Pluto-Bahn: Halbachse px, Exzentrizitaet, Neigung der Ansicht


def pluto_xy(year, sx):
    """Position auf der Pluto-Bahn (Perihel 1989,7, Umlauf 248 Jahre, Kepler), Perihel rechts."""
    M = 2 * math.pi * (year - 1989.7) / 248
    E = M
    for _ in range(10):
        E -= (E - PL_E * math.sin(E) - M) / (1 - PL_E * math.cos(E))
    x = PL_A * (math.cos(E) - PL_E)
    y = PL_A * math.sqrt(1 - PL_E ** 2) * math.sin(E)
    return sx + x, CY - y * PL_FLAT


def tl_x(year):
    return TL_X0 + (TL_X1 - TL_X0) * (year - 1930) / (2015 - 1930)


def frame(bg, A, t):
    im = bg.copy()
    d = ImageDraw.Draw(im)
    st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
    k = max(i for i, s in enumerate(STEPS) if t >= s[0])
    # Szene
    shrink = ease((t - 2.6) / 1.2)                                # 1930 -> 1978
    zoom = ease((t - 11.0) / 1.0)                                  # 2015 Nahansicht
    earth_a = 1 - zoom
    ex, px = 330, 700
    if earth_a > 0.01:
        paste_c(im, A.earth, ex, CY, earth_a)
        d = ImageDraw.Draw(im)
        d.text((ex - 36, CY + E_D / 2 + 14), "Earth", font=f(28, bold=True), fill=tuple(int(v * earth_a) for v in SEC), **st)
    kbo_a = ease((t - 4.7) / 0.6) * (1 - zoom)
    if kbo_a > 0.01:
        for x, y, r in A.kbo:
            if abs(x - (px - 540)) < 60 and abs(y) < 60:
                continue
            paste_c(im, A.kbo_spr[int(r)], 540 + x, CY + y, kbo_a * 0.85)
    eris_a = ease((t - 6.7) / 0.5) * (1 - zoom)
    if eris_a > 0.01:
        paste_c(im, A.eris, px + 160, CY + 70, eris_a)
        d = ImageDraw.Draw(im)
        d.text((px + 140, CY + 110), "Eris", font=f(26, bold=True), fill=tuple(int(v * eris_a) for v in FG), **st)
    if zoom < 0.02:
        pd = E_D + (P_TRUE - E_D) * shrink
        if t < 2.6:
            pd = E_D * (0.9 + 0.1 * ease(t / 0.8))
        paste_c(im, A.pluto(pd), px, CY)
        d = ImageDraw.Draw(im)
        lab = "Pluto (expected)" if t < 2.6 else "Pluto"
        d.text((px - d.textlength(lab, font=f(28, bold=True)) / 2, CY + max(pd / 2, 40) + 14), lab,
               font=f(28, bold=True), fill=ACC, **st)
        ch_a = ease((t - 3.0) / 0.6)
        if ch_a > 0:
            ang = (t - 3.0) * 0.8
            paste_c(im, A.charon, px + 70 * math.cos(ang), CY + 26 * math.sin(ang), ch_a)
            d = ImageDraw.Draw(im)
            d.text((px + 40, CY - 74), "Charon", font=f(22), fill=tuple(int(v * ch_a) for v in SEC), **st)
    elif t < 13.4:
        big = A.pluto_big
        sc = 0.12 + 0.88 * zoom
        sp, m = big
        w = max(4, int(sp.width * sc))
        cx = px + (540 - px) * zoom
        paste_c(im, (sp.resize((w, w), Image.LANCZOS), m.resize((w, w), Image.LANCZOS)), cx, CY)
        d = ImageDraw.Draw(im)
        if t > 12.0 and t < 13.4:
            d.text((cx + 110, CY + 40), "← the 'heart'", font=f(30, bold=True), fill=ACC, **st)
    # Stempel 2006
    stamp = ease((t - 9.6) / 0.25) * (1 - ease((t - 10.9) / 0.2))
    if stamp > 0:
        lay = Image.new("RGBA", (440, 120), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        c = (255, 120, 90, int(235 * stamp))
        ld.rounded_rectangle([6, 6, 434, 114], radius=14, outline=c, width=7)
        txt = "DWARF PLANET"
        ld.text(((440 - ld.textlength(txt, font=f(58, bold=True))) / 2, 18), txt, font=f(58, bold=True), fill=c)
        lay = lay.rotate(-12, expand=True, resample=Image.BICUBIC)
        sc = 1.6 - 0.6 * ease((t - 9.6) / 0.25)
        lay = lay.resize((int(lay.width * sc), int(lay.height * sc)), Image.LANCZOS)
        im.paste(lay, (int(px - lay.width / 2), int(CY - lay.height / 2)), lay)
        d = ImageDraw.Draw(im)
    # Twist: Bahnbogen
    if t >= 13.4:
        a = ease((t - 13.4) / 0.5) * (1 - ease((t - 15.4) / 0.5))
        year = 1930 + (2026 - 1930) * ease((t - 13.5) / 1.4)
        sx = 540 + PL_A * PL_E                                     # Sonne im Brennpunkt
        paste_c(im, A.sun, sx, CY, a)
        d = ImageDraw.Draw(im)
        pts = [pluto_xy(1989.7 + 248 * k / 240, sx) for k in range(241)]
        d.line(pts, fill=tuple(int(v * a * 0.6) for v in SEC), width=3)
        arc = [pluto_xy(1930 + (year - 1930) * k / 120, sx) for k in range(121)]
        d.line(arc, fill=tuple(int(v * a) for v in ACC), width=7)
        x0, y0 = pluto_xy(1930, sx)
        x1, y1 = pluto_xy(year, sx)
        paste_c(im, A.pluto_dot, x1, y1, a)
        d = ImageDraw.Draw(im)
        d.text((x0 - 70, y0 - 44), "1930", font=f(26, bold=True), fill=tuple(int(v * a) for v in SEC), **st)
        d.text((x1 + 22, y1 - 40), "today", font=f(28, bold=True), fill=tuple(int(v * a) for v in ACC), **st)
        d.text((540 - 220, CY + 150), "back at the 1930 spot: 2178", font=f(26, bold=True),
               fill=tuple(int(v * a) for v in SEC), **st)
        d.text((sx - 22, CY + 40), "Sun", font=f(22), fill=tuple(int(v * a) for v in SEC), **st)
    # Jahr + Text
    s = STEPS[k]
    ca = ease((t - s[0]) / 0.35)
    yr = s[1]
    fo = f(84, bold=True)
    d.text(((W - d.textlength(yr, font=fo)) / 2, 520), yr, font=fo, fill=tuple(int(v * ca) for v in ACC), **st)
    for j, ln in enumerate(s[2:]):
        fo = f(36, bold=True) if j == 0 else f(30)
        d.text(((W - d.textlength(ln, font=fo)) / 2, 628 + j * 48), ln, font=fo,
               fill=tuple(int(v * ca) for v in (FG if j == 0 else SEC)), **st)
    # Zeitstrahl
    d.line([TL_X0, TL_Y, TL_X1, TL_Y], fill=HAIR, width=4)
    yr_now = 2015 if k >= 5 else int(s[1]) if s[1].isdigit() else 2015
    for y in YEARS:
        x = tl_x(y)
        on = y <= yr_now
        r = 7 if on else 5
        d.ellipse([x - r, TL_Y - r, x + r, TL_Y + r], fill=ACC if on else HAIR)
    d.line([TL_X0, TL_Y, tl_x(yr_now), TL_Y], fill=ACC, width=4)
    for y in (1930, 1978, 2006, 2015):
        lab = str(y)
        d.text((tl_x(y) - d.textlength(lab, font=f(20)) / 2, TL_Y + 14), lab, font=f(20), fill=SEC)
    return im


def main():
    bg = background()
    A = Assets()
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (1.5, 4.0, 7.8, 9.9, 12.5, 14.6):
            cinematic(frame(bg, A, t), 0).save(prev / f"pluto-{t:.1f}.png")
        print("preview saved")
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(LOOP * FPS)
    out = OUT / "w8-pluto-history.mp4"
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
    cinematic(frame(bg, A, 1.5), 0).save(OUT / "w8-pluto-history-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
