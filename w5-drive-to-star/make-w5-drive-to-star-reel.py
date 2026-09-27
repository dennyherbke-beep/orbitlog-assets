"""Woche 5, Mittwoch - animiertes Reel "Driving to the nearest star at 100 km/h" (ersetzt das
fruehere Standbild aus make-w5-drive-to-star.py). 1080x1920, 30 fps, ~17 s, stille Audiospur.

Ablauf: Intro (Auto an der Erde) -> Fahrt: Auto faehrt eine logarithmisch skalierte Strasse
zu Proxima Centauri, ein Zaehler zeigt die Fahrzeit, Zwischenstationen leuchten beim Passieren
auf -> Endbild "46 million years / light: 4.2 years" -> Speicheranreiz (frame_save).

Fahrzeiten bei 100 km/h, nonstop (1 Jahr = 8,766 h):
  Mond 384,400 km -> 160 Tage (~5 Monate) | Sonne 149.6 Mio. km -> 171 Jahre
  Neptun ~4.5 Mrd. km -> ~5,100 Jahre      | Voyager 1 25.9 Mrd. km -> ~29,500 Jahre
  Proxima Centauri 4.2465 Lj = 4.0175e13 km -> 45.8 Mio. Jahre (~46 Mio.)
Strasse: x = log10(1 + d/d0) / log10(1 + D/d0), d0 = 100,000 km (sonst laege der Mond auf der
Startlinie) - im Bild als "log scale" gekennzeichnet.

    python make-w5-drive-to-star-reel.py  ->  w5-drive-to-star.mp4, w5-drive-to-star-cover.png
"""

import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageChops, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono, downscale
from bodies import planet, star
from reelkit import W as WS, H as HS, new_frame, sphere, blob, grain, frame_save, TEX

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920              # Ausgabe; Hintergrund wird mit Supersampling (S) vorgerendert
FPS = 30
T_INTRO, T_DRIVE, T_HOLD, T_SAVE = 2.0, 9.0, 3.5, 2.5

D0 = 1e5                       # km, Log-Offset
D_END = 4.2465 * 9.4607e12     # km bis Proxima
L = math.log10(1 + D_END / D0)
ROAD_Y = 1150
X0, X1 = 240, 930              # Strasse: Erde .. Proxima
STOPS = [("Moon", 384_400, "5 months", 1), ("Sun", 149.6e6, "171 years", -1),
         ("Neptune", 4.5e9, "5,100 years", -1), ("Voyager 1", 25.9e9, "29,500 years", 1)]


def xpos(d):
    return X0 + (X1 - X0) * math.log10(1 + d / D0) / L


def dist(u):
    return D0 * (10 ** (u * L) - 1)


def fmt_time(d):
    h = d / 100
    days, years = h / 24, h / 8766
    if days < 365:
        return f"{days:,.0f}", "days"
    if years < 1e6:
        return f"{years:,.0f}", "years"
    return f"{years / 1e6:.0f} million", "years"


def tex_red_dwarf():
    t = Image.new("RGB", (TEX, TEX), (236, 108, 70))
    blob(t, 200, 190, 90, 70, (255, 150, 96), blur=40, alpha=160)
    blob(t, 330, 320, 60, 44, (190, 70, 46), blur=26, alpha=140)
    return grain(t, 16, 3)


def tex_earth():
    t = Image.new("RGB", (TEX, TEX), (40, 90, 160))
    for x, y, rx, ry in [(175, 190, 85, 55), (330, 150, 55, 65), (245, 330, 70, 45)]:
        blob(t, x, y, rx, ry, (83, 122, 66), blur=9)
    for x, y, rx, ry in [(150, 130, 95, 30), (350, 250, 85, 26)]:
        blob(t, x, y, rx, ry, (255, 255, 255), blur=20, alpha=110)
    return t


def base():
    """Statischer Hintergrund: Sternfeld, Erde, Proxima (mit Supersampling gerendert)."""
    img, _ = new_frame(5)
    planet(img, X0 * S - 160 * S, ROAD_Y * S, 76, "earth")
    star(img, X1 * S + 70 * S, ROAD_Y * S, 96, "red_dwarf")
    return downscale(img, W, H)


def ctext(d, s, font, fill, y, cx=W / 2):
    d.text((cx - d.textlength(s, font=font) / 2, y), s, font=font, fill=fill)


# ---------------------------------------------------------------- Auto (Seitenprofil)
# Modellkoordinaten: 100 Einheiten lang, Fahrtrichtung rechts, Boden bei y = 36.
CAR_LEN = 118                  # px in der Ausgabe
K = CAR_LEN / 100 * 6          # Render-Aufloesung (6x Supersampling)
WHEELS = (22, 80)
WHEEL_Y, TIRE_R, RIM_R = 27.5, 8.5, 5.6


def spline(pts, n=10):
    """Catmull-Rom durch die Stuetzpunkte - runde Karosserielinien statt Ecken."""
    out = []
    ext = [pts[0]] + pts + [pts[-1]]
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t * t
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t ** 3) for j in range(2)))
    return out + [pts[-1]]


ROOF = [(0.8, 21), (2.6, 17.2), (12, 15.3), (23, 8.4), (32, 4.0), (46, 3.0), (60, 3.5), (68.5, 6.2),
        (78, 12.9), (90, 14.9), (97, 16.6), (99.4, 19.8)]
BODY = [(1, 27)] + spline(ROOF) + [(99.5, 27)]
GLASS = spline([(26.8, 13.4), (33.6, 6.2), (45, 4.5), (58.8, 4.9), (66, 7.3), (75.6, 13.4)]) + [(26.8, 13.4)]
_CAR = {}


def _grad(size, stops):
    """Vertikaler Farbverlauf ueber mehrere Stuetzstellen [(t, (r,g,b)), ...]."""
    w, h = size
    col = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        for (t0, c0), (t1, c1) in zip(stops, stops[1:]):
            if t0 <= t <= t1:
                a = (t - t0) / (t1 - t0)
                col.putpixel((0, y), tuple(int(c0[i] + (c1[i] - c0[i]) * a) for i in range(3)))
                break
    return col.resize((w, h))


def _wheel(ang):
    """Rad mit Reifen, Felgenbett, 5 Speichen, Nabe - gedreht um ang (rad)."""
    n = int(TIRE_R * 2 * K) + 4
    im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = n / 2
    R, r = TIRE_R * K, RIM_R * K
    d.ellipse([c - R, c - R, c + R, c + R], fill=(26, 27, 31))                    # Reifen
    d.ellipse([c - R * 0.93, c - R * 0.93, c + R * 0.93, c + R * 0.93], outline=(48, 50, 56), width=int(K * 0.5))
    d.ellipse([c - r, c - r, c + r, c + r], fill=(118, 124, 134))                  # Felgenhorn
    d.ellipse([c - r * 0.88, c - r * 0.88, c + r * 0.88, c + r * 0.88], fill=(34, 36, 42))  # Felgenbett
    for k in range(5):
        a = ang + k * 2 * math.pi / 5
        for da, w in ((0.0, 0.34), ):
            pts = [(c + math.cos(a + s) * r * 0.86, c + math.sin(a + s) * r * 0.86) for s in (-0.17, 0.17)]
            pts += [(c + math.cos(a + s) * r * 0.22, c + math.sin(a + s) * r * 0.22) for s in (0.5, -0.5)]
            d.polygon(pts, fill=(196, 202, 212))
            d.line([pts[0], pts[3]], fill=(236, 240, 246), width=max(1, int(K * 0.25)))
    d.ellipse([c - r * 0.26, c - r * 0.26, c + r * 0.26, c + r * 0.26], fill=(160, 166, 176))
    d.ellipse([c - r * 0.1, c - r * 0.1, c + r * 0.1, c + r * 0.1], fill=(70, 74, 82))
    return im


def _body():
    w, h = int(100 * K) + 2, int(38 * K)
    P = lambda pts: [(x * K, y * K) for x, y in pts]
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    # Karosserie-Maske mit ausgeschnittenen Radlaeufen
    mask = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.polygon(P(BODY), fill=255)
    for wx in WHEELS:
        rr = (TIRE_R + 1.6) * K
        md.ellipse([wx * K - rr, WHEEL_Y * K - rr, wx * K + rr, WHEEL_Y * K + rr], fill=0)
    paint = _grad((w, h), [(0.0, (255, 214, 150)), (0.18, (250, 170, 84)), (0.42, (226, 124, 44)),
                           (0.62, (170, 78, 26)), (0.75, (96, 40, 14)), (1.0, (60, 24, 10))])
    img.paste(paint, (0, 0), mask)
    d = ImageDraw.Draw(img)

    # Radlauf-Kanten (dunkle Innenschatten)
    for wx in WHEELS:
        rr = (TIRE_R + 1.6) * K
        d.arc([wx * K - rr, WHEEL_Y * K - rr, wx * K + rr, WHEEL_Y * K + rr], 180, 360,
              fill=(58, 22, 8), width=int(K * 0.9))

    # Scheiben mit Verlauf + Spiegelung, B-/C-Saeule
    gm = Image.new("L", (w, h), 0)
    ImageDraw.Draw(gm).polygon(P(GLASS), fill=255)
    img.paste(_grad((w, h), [(0.0, (120, 150, 185)), (0.25, (46, 62, 86)), (1.0, (16, 20, 30))]), (0, 0), gm)
    refl = Image.new("L", (w, h), 0)
    ImageDraw.Draw(refl).polygon(P([(40, 3), (47, 3), (38, 13.4), (31, 13.4)]), fill=70)
    ImageDraw.Draw(refl).polygon(P([(62, 3), (65.5, 3), (58, 13.4), (54.5, 13.4)]), fill=55)
    refl = Image.composite(refl, Image.new("L", (w, h), 0), gm)
    img.paste(Image.new("RGB", (w, h), (230, 240, 255)), (0, 0), refl)
    d.polygon(P([(50.2, 4.4), (52.4, 4.5), (52.4, 13.4), (50.2, 13.4)]), fill=(28, 30, 36))   # B-Saeule
    rh = Image.new("L", (w, h), 0)                                                          # Dachglanz
    ImageDraw.Draw(rh).line(P(spline([(24, 8.2), (33, 3.9), (46, 3.1), (60, 3.6), (68, 6.1)])), fill=150, width=int(K * 0.7))
    img.paste(Image.new("RGB", (w, h), (255, 236, 200)), (0, 0), rh.filter(ImageFilter.GaussianBlur(K * 0.4)))
    d.line(P(GLASS[:-1]), fill=(40, 22, 12), width=int(K * 0.6))                                          # Dichtung

    # Fugen, Sicke, Griffe, Spiegel
    line = (120, 52, 18)
    d.line(P([(33, 13.6), (33.8, 17), (33, 25.5)]), fill=line, width=int(K * 0.35))       # Tuer hinten
    d.line(P([(52.4, 13.6), (52.4, 25.5)]), fill=line, width=int(K * 0.35))               # Tuer vorne
    d.line(P([(76.2, 13.8), (75.2, 20), (71, 25.5)]), fill=line, width=int(K * 0.35))     # Kotfluegel
    d.line(P([(4, 18.2), (96, 18.8)]), fill=(255, 226, 180), width=int(K * 0.45))         # Lichtkante
    d.line(P([(4, 19.1), (96, 19.7)]), fill=(150, 66, 22), width=int(K * 0.3))
    for hx in (38.5, 57.5):
        d.rounded_rectangle(P([(hx, 16.1), (hx + 5, 17.3)]), radius=K * 0.5, fill=(90, 38, 14))
        d.line(P([(hx + 0.4, 16.2), (hx + 4.6, 16.2)]), fill=(255, 220, 170), width=max(1, int(K * 0.2)))
    d.polygon(P([(73.6, 11.4), (77.4, 11.2), (78.4, 13.2), (74.4, 14.4)]), fill=(206, 112, 40))   # Spiegel
    d.line(P([(73.6, 11.4), (77.4, 11.2)]), fill=(255, 214, 150), width=max(1, int(K * 0.25)))

    # Stossfaenger/Schweller dunkel, Lichter
    d.polygon(P([(1, 24), (99.5, 24), (99.5, 27), (1, 27)]), fill=(38, 30, 28))
    for wx in WHEELS:
        rr = (TIRE_R + 1.6) * K
        ImageDraw.Draw(mask).ellipse([wx * K - rr, WHEEL_Y * K - rr, wx * K + rr, WHEEL_Y * K + rr], fill=0)
    d.polygon(P([(92.5, 16.4), (97.8, 17.6), (98.8, 20.2), (93.5, 19.8)]), fill=(255, 250, 230))   # Scheinwerfer
    d.polygon(P([(1.2, 19.8), (4.6, 19.4), (4.4, 22.2), (1.2, 22.4)]), fill=(210, 30, 30))       # Ruecklicht
    d.line(P([(1.4, 20.4), (4.2, 20.2)]), fill=(255, 120, 110), width=max(1, int(K * 0.3)))
    # Radlaeufe erneut freistellen (Schweller-Balken darf nicht hineinragen)
    a = img.split()[3]
    cut = Image.new("L", (w, h), 255)
    for wx in WHEELS:
        rr = (TIRE_R + 1.6) * K
        ImageDraw.Draw(cut).ellipse([wx * K - rr, WHEEL_Y * K - rr, wx * K + rr, WHEEL_Y * K + rr], fill=0)
    img.putalpha(ImageChops.multiply(a, cut))
    return img


def car_sprite(ang):
    """Fertiges Auto (Karosserie + gedrehte Raeder + Bodenschatten), heruntergerechnet."""
    step = round((ang % (2 * math.pi / 5)) / (2 * math.pi / 5) * 24) % 24
    if step in _CAR:
        return _CAR[step]
    body = _CAR.setdefault("body", _body())
    w, h = body.size
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh = Image.new("L", (w, h), 0)
    ImageDraw.Draw(sh).ellipse([4 * K, 34.2 * K, 96 * K, 37.6 * K], fill=150)
    sh = sh.filter(ImageFilter.GaussianBlur(K * 1.2))
    im.paste(Image.new("RGBA", (w, h), (0, 0, 0, 255)), (0, 0), sh)
    whl = _wheel(step / 24 * 2 * math.pi / 5)
    for wx in WHEELS:
        im.alpha_composite(whl, (int(wx * K - whl.width / 2), int(WHEEL_Y * K - whl.height / 2)))
    im.alpha_composite(body)
    small = im.resize((int(w / 6), int(h / 6)), Image.LANCZOS)
    _CAR[step] = small
    return small


def car(img, front_x, ground_y, ang):
    spr = car_sprite(ang)
    ppu = spr.width / 100                         # px pro Modelleinheit
    img.paste(spr, (int(front_x - spr.width), int(ground_y - 36 * ppu)), spr)


def frame(bg, u, phase_t=0.0, final=False):
    img = bg.copy()
    # Scheinwerfer-Glow vor dem Auto
    cx = X0 + (X1 - X0) * u
    if 0 < u < 1:
        blob(img, int(cx + 50), ROAD_Y - 22, 70, 12, (255, 226, 160), blur=14, alpha=80)
    d = ImageDraw.Draw(img)

    d.text((96, 250), "DRIVING TO THE NEAREST STAR", font=fmono(26), fill=ACC)
    ctext(d, "At 100 km/h, nonstop,", f(52, bold=True), FG, 380)
    ctext(d, "how long is the trip?", f(52, bold=True), FG, 446)

    num, unit = ("0", "days") if u == 0 else fmt_time(dist(u))
    if final:
        num, unit = "46 million", "years"
    ctext(d, num, f(150 if len(num) < 8 else 128, bold=True), ACC, 590)
    ctext(d, unit + (" on the road" if not final else ""), f(48, bold=True), FG, 790)

    # Strasse: gefahrener Teil hell, Rest gestrichelt
    d.line([X0, ROAD_Y, X1, ROAD_Y], fill=HAIR, width=8)
    x = X0
    while x < X1:
        d.line([x, ROAD_Y, min(x + 14, X1), ROAD_Y], fill=ACC if x < cx else (90, 96, 112), width=3)
        x += 28
    for name, dd, t, side in STOPS:
        sx = xpos(dd)
        hit = cx >= sx
        col = ACC if hit else SEC
        d.line([sx, ROAD_Y - 14, sx, ROAD_Y + 14], fill=col, width=3)
        ly = ROAD_Y - 118 if side < 0 else ROAD_Y + 34
        d.text((sx - d.textlength(name, font=f(26, bold=True)) / 2, ly), name, font=f(26, bold=True),
               fill=FG if hit else SEC)
        d.text((sx - d.textlength(t, font=fmono(22)) / 2, ly + 36), t, font=fmono(22), fill=col)
    d.text((X0 - 192, ROAD_Y + 60), "Earth", font=f(26, bold=True), fill=FG)
    lbl = "Proxima Centauri"
    d.text((X1 + 90 - d.textlength(lbl, font=f(26, bold=True)), ROAD_Y + 78), lbl, font=f(26, bold=True), fill=FG)
    car(img, cx, ROAD_Y + 2, (cx - X0) / (TIRE_R * CAR_LEN / 100))   # Front auf aktueller Position, Raeder rollen
    d = ImageDraw.Draw(img)

    ctext(d, "road on a log scale - otherwise the Moon would sit on the start line",
          fmono(20), SEC, ROAD_Y + 190)
    if final:
        a = min(1.0, phase_t / 0.6)
        col = tuple(int(c * a + 11 * (1 - a)) for c in FG)
        ctext(d, "Light makes the same trip in", f(40), col, 1440)
        ctext(d, "4.2 years", f(64, bold=True), tuple(int(c * a + 11 * (1 - a)) for c in ACC), 1496)
    ctext(d, "@theorbitlog", fmono(22), SEC, H - 300 + 6)
    return img


def ease(t):
    return t * t * (3 - 2 * t)


def main():
    bg = base()
    save = downscale(frame_save(("Save this", "for the next time", "a road trip feels long")), W, H)
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    total = T_INTRO + T_DRIVE + T_HOLD + T_SAVE
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", str(total), "-movflags", "+faststart",
        str(OUT / "w5-drive-to-star.mp4")], stdin=subprocess.PIPE)
    n = int(total * FPS)
    for i in range(n):
        t = i / FPS
        if t < T_INTRO:
            im = frame(bg, 0.0)
        elif t < T_INTRO + T_DRIVE:
            im = frame(bg, ease((t - T_INTRO) / T_DRIVE))
        elif t < T_INTRO + T_DRIVE + T_HOLD:
            im = frame(bg, 1.0, t - T_INTRO - T_DRIVE, final=True)
        else:
            im = save
        proc.stdin.write(im.tobytes())
    proc.stdin.close()
    proc.wait()
    frame(bg, 1.0, 1.0, final=True).save(OUT / "w5-drive-to-star-cover.png")
    print(f"saved w5-drive-to-star.mp4 ({total:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
