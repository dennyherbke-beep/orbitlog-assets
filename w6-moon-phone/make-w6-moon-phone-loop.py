"""Woche 6/8, Do 22.10.2026 - Mond-Handy-Reel als Loop im Winner-Muster (Termin + Handlung, wie
w6-andromeda-weekend): feste Kopfzeile, ein Handy, eine durchgehende Szene. Ersetzt die Folien-Version
make-w6-moon-phone-reel.py (bleibt als Archiv liegen). Umbau 14.10.2026.

Hook-Varianten:
  1. "Your phone CAN shoot the HUNTER'S MOON"          <- gewaehlt (Termin + Handlung)
  2. "Your Moon photos look like a white blob?"
  3. "Stop pinching to zoom on the Moon"
  4. "4 taps for a sharp Hunter's Moon"
  5. "Same phone. Real craters."

Szene (12 s, nahtloser Loop): Sucher zeigt den Mond als weissen Fleck (Automatik belichtet auf den dunklen
Himmel) -> 1 Tippen + Halten (AE/AF-Sperre) -> 2 Belichtung runter (Mond bekommt Struktur, Himmel wird
schwarz) -> 3 Zoomtaste 3x statt Pinch -> 4 abstuetzen + 3-s-Timer, Ausloesen -> "Same phone. Real
craters." -> zurueck. Mond aus der NASA-LRO-Karte (bodies.planet), fast voll beleuchtet, leicht warm
(tief am Horizont). Sucherbild ist Illustration - im first_comment offengelegt.

Fakten: Vollmond (Hunter's Moon) 26.10.2026 04:12 UTC = Nacht 25./26.10. in Nordamerika und Europa,
geht bei Sonnenuntergang im Osten auf. Praxis: siehe make-w6-moon-phone-reel.py.

    python make-w6-moon-phone-loop.py  ->  w6-moon-phone-loop.mp4, -loop-cover.png
"""

import math
import os
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, f, fmono, canvas, downscale
from bodies import planet
from reelkit import header_band, deep_sky, cinematic

OUT = Path(__file__).resolve().parent
W, H, FPS, LOOP = 1080, 1920, 30, 12.0
PX0, PY0, PX1, PY1 = 305, 580, 775, 1380            # Handy (Ausgabe-px)
VX0, VY0, VX1, VY1 = 317, 592, 763, 1198            # Sucher
CY_CTRL = 1236                                      # Zoomstufen-Leiste
MOON = (540, 860)                                   # Mondmitte im Sucher bei 1x
D1, ZMAX = 100, 3.0                                 # Monddurchmesser bei 1x, Zoomstufe
GAIN = 6.0                                          # Ueberbelichtung im Automatikmodus
STEPS = [("Auto mode: a white blob", 0.0, 1.5, 0), ("1 · Tap and hold the Moon", 1.5, 3.3, 1),
         ("2 · Drag brightness way down", 3.3, 5.8, 2), ("3 · Tap 3x - don't pinch", 5.8, 8.0, 3),
         ("4 · Lean it on something + 3 s timer", 8.0, 10.0, 4), ("Same phone. Real craters.", 10.0, 11.2, 5)]


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def state(t):
    """Belichtung g und Zoom z zum Zeitpunkt t (am Loop-Ende zurueck auf den Anfangszustand)."""
    back = ease((t - 11.2) / 0.7)
    g = GAIN - 1.5 * ease((t - 2.0) / 0.6) - (GAIN - 2.8) * ease((t - 3.7) / 1.6)
    z = 1 + (ZMAX - 1) * ease((t - 6.2) / 1.1)
    return g + (GAIN - g) * back, z + (1 - z) * back


def moon_sprite():
    """Mond einmal in voller Groesse (D1 * ZMAX) rendern -> float-Array, schwarzer Hintergrund."""
    d = int(D1 * ZMAX)
    can = Image.new("RGB", ((d + 20) * S, (d + 20) * S), (0, 0, 0))
    planet(can, can.width // 2, can.height // 2, d, "moon", light=(0.2, -0.06, 1.0), glow=False)
    arr = np.asarray(downscale(can, d + 20, d + 20), np.float32)
    return arr * np.array([1.0, 0.95, 0.86])                          # tief am Horizont leicht warm


def trees(w, h):
    """Baumgrenze als Silhouetten-Maske fuer den Sucher (unteres Ende)."""
    m = Image.new("L", (w * 2, h * 2), 0)
    d = ImageDraw.Draw(m)
    rnd = np.random.default_rng(3)
    base = h * 2 - 70
    pts = [(0, h * 2)] + [(x, base + 10 * math.sin(x / 70) + rnd.uniform(-5, 5)) for x in range(0, w * 2 + 20, 20)]
    d.polygon(pts + [(w * 2, h * 2)], fill=255)
    for x, s in [(60, 1.0), (170, 0.7), (720, 0.9), (840, 1.2)]:
        for k in range(5):
            wd = (60 - k * 11) * s
            yb = base - k * 34 * s + 8
            d.polygon([(x - wd, yb), (x + wd, yb), (x, yb - 50 * s)], fill=255)
    return np.asarray(m.resize((w, h), Image.LANCZOS), np.float32) / 255


VW, VH = VX1 - VX0, VY1 - VY0
SPRITE = moon_sprite()
TREES = trees(VW, VH)
YY, XX = np.mgrid[0:VH, 0:VW].astype(np.float32)


def viewfinder(t, seed):
    """Sucherbild: Himmel (hell + verrauscht bei Ueberbelichtung), Baeume, Mond mit Blendung."""
    g, z = state(t)
    e = (g - 1) / (GAIN - 1)                                          # 1 = Automatik, 0 = korrekt belichtet
    rng = np.random.default_rng(seed)
    grad = (YY / VH)[..., None]
    sky = (np.array([6, 8, 14]) + e * np.array([30, 36, 52])) * (0.8 + 0.4 * grad)
    sky = sky + rng.normal(0, 2 + 9 * e, (VH, VW, 1))                 # Sensorrauschen bei langer Belichtung
    mx, my = MOON[0] - VX0, MOON[1] - VY0
    ty = (YY - my) / z + my                                           # Baeume zoomen mit (um die Mondmitte)
    tx = (XX - mx) / z + mx
    tm = TREES[np.clip(ty.astype(int), 0, VH - 1), np.clip(tx.astype(int), 0, VW - 1)] * (ty < VH)
    img = sky * (1 - tm[..., None]) + np.array([2, 2, 3]) * tm[..., None]
    d = max(8, int(round(D1 * z)))
    pad = int(10 * d / (D1 * ZMAX))
    spr = np.asarray(Image.fromarray(np.clip(SPRITE, 0, 255).astype(np.uint8)).resize((d + 2 * pad, d + 2 * pad),
                                                                                    Image.LANCZOS), np.float32)
    spr = np.clip(spr * g, 0, 255)
    if e > 0.02:                                                      # Blendung um den ausgebrannten Mond
        r = d / 2
        rr = np.sqrt((XX - mx) ** 2 + (YY - my) ** 2)
        halo = np.exp(-np.clip(rr - r, 0, None) / (r * 0.9)) * 210 * e ** 1.3
        img = img + halo[..., None] * np.array([1.0, 1.0, 0.95])
    x0, y0 = int(mx - spr.shape[1] / 2), int(my - spr.shape[0] / 2)
    sx0, sy0 = max(0, -x0), max(0, -y0)
    x0c, y0c = max(0, x0), max(0, y0)
    x1c, y1c = min(VW, x0 + spr.shape[1]), min(VH, y0 + spr.shape[0])
    if x1c > x0c and y1c > y0c:
        reg = img[y0c:y1c, x0c:x1c]
        img[y0c:y1c, x0c:x1c] = 255 - (255 - reg) * (255 - spr[sy0:sy0 + y1c - y0c, sx0:sx0 + x1c - x0c]) / 255
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), "RGB")


def vf_mask():
    m = Image.new("L", (VW * 4, VH * 4), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, VW * 4 - 1, VH * 4 + 200], 46 * 4, fill=255)
    return m.resize((VW, VH), Image.LANCZOS)


def background():
    img, _ = canvas(W * S, H * S)
    deep_sky(img, 22, band=(0.62, 0.42))
    shade = Image.new("L", img.size, 0)                               # Kopfzeile lesbar halten
    ImageDraw.Draw(shade).rectangle([0, 0, W * S, 560 * S], fill=120)
    shade = shade.filter(ImageFilter.GaussianBlur(60 * S))
    img.paste(Image.new("RGB", img.size, (5, 7, 12)), (0, 0), shade)
    y = header_band(img, ["Your phone CAN shoot", "the HUNTER'S MOON"], "HUNTER'S MOON")
    d = ImageDraw.Draw(img)
    sub = "Full Moon · night of Oct 25-26 · rises at sunset in the east"
    d.text(((W * S - d.textlength(sub, font=f(28 * S))) / 2, y + 2 * S), sub, font=f(28 * S), fill=SEC)
    k = S                                                             # Handy-Gehaeuse (generisch, ohne Marke)
    d.rounded_rectangle([(PX0 - 4) * k, (PY0 - 4) * k, (PX1 + 4) * k, (PY1 + 4) * k], 70 * k, fill=(70, 76, 88))
    d.rounded_rectangle([PX0 * k, PY0 * k, PX1 * k, PY1 * k], 66 * k, fill=(30, 33, 40))
    d.rounded_rectangle([(VX0 - 1) * k, (VY0 - 1) * k, (VX1 + 1) * k, (PY1 - 12) * k], 50 * k, fill=(3, 4, 6))
    d.rounded_rectangle([(PX1 + 2) * k, 760 * k, (PX1 + 8) * k, 860 * k], 3 * k, fill=(60, 66, 78))
    d.rounded_rectangle([(PX0 - 8) * k, 720 * k, (PX0 - 2) * k, 780 * k], 3 * k, fill=(60, 66, 78))
    for n, (txt, fo, col) in enumerate([("Save this for Oct 25-26", f(40 * S, bold=True), FG),
                                        ("Send it to the friend with the blurry Moon pics", f(30 * S), SEC)]):
        d.text(((W * S - d.textlength(txt, font=fo)) / 2, (1512 + n * 52) * S), txt, font=fo, fill=col)
    return downscale(img, W, H)


def sun_icon(d, x, y, r, col):
    d.ellipse([x - r, y - r, x + r, y + r], fill=col)
    for i in range(8):
        a = i * math.pi / 4
        d.line([x + math.cos(a) * r * 1.6, y + math.sin(a) * r * 1.6,
                x + math.cos(a) * r * 2.4, y + math.sin(a) * r * 2.4], fill=col, width=max(2, int(r * 0.35)))


def overlay(t):
    """Bedienelemente + Beschriftung auf 2x-Ebene."""
    k = 2
    ov = Image.new("RGBA", (W * k, H * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    back = 1 - ease((t - 11.2) / 0.5)
    a = lambda v: int(255 * max(0.0, min(1.0, v)))
    _, z = state(t)
    mx, my = MOON
    lock = ease((t - 2.0) / 0.3) * (1 - ease((t - 6.0) / 0.4))        # AE/AF-Rahmen
    if 1.6 < t < 2.5:                                                  # Tipp-Kreis
        p = (t - 1.6) / 0.9
        r = (30 + 50 * p) * k
        d.ellipse([mx * k - r, my * k - r, mx * k + r, my * k + r], outline=(255, 255, 255, a(0.8 * (1 - p))), width=4 * k)
    if lock > 0:
        r = 78 * k
        col = ACC + (a(lock),)
        for sx in (-1, 1):                                             # Eckwinkel statt Vollrahmen
            for sy in (-1, 1):
                cx, cy = mx * k + sx * r, my * k + sy * r
                d.line([cx, cy, cx - sx * 26 * k, cy], fill=col, width=3 * k)
                d.line([cx, cy, cx, cy - sy * 26 * k], fill=col, width=3 * k)
        tw = d.textlength("AE/AF LOCK", font=fmono(20 * k))
        d.rounded_rectangle([(540 - 70) * k, (VY0 + 18) * k, (540 + 70) * k, (VY0 + 50) * k], 8 * k, fill=ACC + (a(lock),))
        d.text((540 * k - tw / 2, (VY0 + 21) * k), "AE/AF LOCK", font=fmono(20 * k), fill=(20, 16, 10, a(lock)))
    sl = ease((t - 3.3) / 0.3) * (1 - ease((t - 6.0) / 0.4))          # Belichtungsregler
    if sl > 0:
        x, y0, y1 = (mx + 120) * k, (my - 110) * k, (my + 110) * k
        d.line([x, y0, x, y1], fill=ACC + (a(sl),), width=3 * k)
        kn = y0 + (y1 - y0) * (0.5 + 0.42 * ease((t - 3.7) / 1.6))
        sun_icon(d, x, kn, 11 * k, ACC + (a(sl),))
    for i, txt in enumerate(["0.5", "1x", "3x"]):                      # Zoomstufen
        bx, by = (540 + (i - 1) * 86) * k, CY_CTRL * k
        on = i == 2 and 5.9 < t < 11.4
        if i == 1:
            on = not (5.9 < t < 11.4)
        d.ellipse([bx - 30 * k, by - 30 * k, bx + 30 * k, by + 30 * k], fill=(70, 56, 30, 255) if on else (28, 31, 38, 255),
                  outline=ACC + (255,) if on else None, width=2 * k)
        fo = f(22 * k, bold=True)
        d.text((bx - d.textlength(txt, font=fo) / 2, by - 15 * k), txt, font=fo, fill=(ACC if on else FG) + (255,))
    sx, sy = 540 * k, 1312 * k                                         # Ausloeser
    press = 1 - 0.12 * math.exp(-((t - 9.8) / 0.08) ** 2)
    d.ellipse([sx - 38 * k, sy - 38 * k, sx + 38 * k, sy + 38 * k], outline=FG + (255,), width=4 * k)
    r = 30 * k * press
    d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(236, 238, 242, 255))
    tm = ease((t - 8.0) / 0.3) * (1 - ease((t - 10.6) / 0.4))          # Timer
    if tm > 0:
        tx, ty = (VX0 + 42) * k, (VY0 + 36) * k
        col = ACC + (a(tm),)
        d.ellipse([tx - 16 * k, ty - 16 * k, tx + 16 * k, ty + 16 * k], outline=col, width=3 * k)
        d.line([tx, ty, tx, ty - 10 * k], fill=col, width=3 * k)
        d.line([tx, ty, tx + 8 * k, ty], fill=col, width=3 * k)
        d.text((tx + 24 * k, ty - 18 * k), "3s", font=f(28 * k, bold=True), fill=col)
        for n, t0 in enumerate((8.3, 8.8, 9.3)):                       # Countdown
            p = (t - t0) / 0.5
            if 0 <= p < 1:
                fo = f(int((120 - 30 * p) * k), bold=True)
                s = str(3 - n)
                d.text((540 * k - d.textlength(s, font=fo) / 2, 1036 * k), s, font=fo,
                       fill=(242, 244, 248, a(1 - p)), stroke_width=3 * k, stroke_fill=(3, 4, 6, a(0.6 * (1 - p))))
    for txt, t0, t1, step in STEPS:                                    # Schritt-Text unter dem Handy
        if step == 0:
            al = max(1 - ease((t - t1) / 0.3), ease((t - 11.4) / 0.4))
        elif step == 5:
            al = ease((t - t0) / 0.3) * back
        else:
            al = ease((t - t0) / 0.3) * (1 - ease((t - t1) / 0.3))
        if al > 0:
            fo = f(40 * k, bold=True)
            col = ACC if step == 5 else FG
            d.text(((W * k - d.textlength(txt, font=fo)) / 2, 1404 * k), txt, font=fo, fill=col + (a(al),),
                   stroke_width=3 * k, stroke_fill=(3, 4, 6, a(al)))
    cur = next((s for _, t0, t1, s in STEPS if t0 <= t < t1), 0)       # Fortschritt 1-4
    for i in range(4):
        x, y = (540 + (i - 1.5) * 34) * k, 1474 * k
        on = 1 <= cur and i < cur
        d.ellipse([x - 7 * k, y - 7 * k, x + 7 * k, y + 7 * k], fill=(ACC if on else (70, 78, 94)) + (255,))
    return ov.resize((W, H), Image.LANCZOS)


def frame(bg, mask, t, seed):
    im = bg.copy().convert("RGBA")
    vf = viewfinder(t, seed)
    fl = math.exp(-max(0.0, t - 9.8) / 0.12) * 0.55 if 9.8 <= t < 10.6 else 0  # Ausloese-Blitz im Sucher
    if fl > 0:
        vf = Image.blend(vf, Image.new("RGB", vf.size, (230, 232, 236)), fl)
    im.paste(vf, (VX0, VY0), mask)
    im.alpha_composite(overlay(t))
    return im.convert("RGB")


def main():
    bg, mask = background(), vf_mask()
    chk = Path(os.environ.get("CHECK_DIR", OUT))
    for t in [float(v) for v in os.environ.get("CHECK_T", "0.5,2.6,4.6,7.6,8.6,10.5").split(",")]:
        cinematic(frame(bg, mask, t, 0), 0).save(chk / f"_check-moon-{t:.1f}.png")
    if os.environ.get("CHECK_ONLY"):
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = OUT / "w6-moon-phone-loop.mp4"
    n = int(LOOP * FPS)
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart",
        str(out)], stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg, mask, i / FPS, i), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg, mask, 10.5, 0), 0).save(OUT / "w6-moon-phone-loop-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
