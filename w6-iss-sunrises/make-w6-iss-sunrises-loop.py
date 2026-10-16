"""Umbau 16.10.2026 (Woche 8, Sa 24.10.): "Astronauts see 16 SUNRISES a day" als durchgehende Animation
(Typ a Zaehler + Handlung) statt 8 Folien (make-w6-iss-sunrises-reel.py).
Erde mit Tag-/Nachtseite (Sonne links), die ISS kreist in massstaeblicher Hoehe, faellt in den Erdschatten und
kommt wieder heraus - jeder Austritt = Sonnenaufgang, Zaehler laeuft mit. ISS = freigestelltes NASA-Foto iss056e201248 (gemeinfrei, stark vergroessert). 24-h-Uhr beschleunigt nach der ersten
Runde. Vergleich "You: 1". Endzeile = Handlung (NASA Spot the Station). 14 s.

Fakten: NASA Space Station Facts and Figures (~400 km Hoehe, ~28.000 km/h, ~90 Min. pro Runde, 16 Sonnenauf-
und -untergaenge pro Tag). Hier: Runde = 1,5 h -> genau 16 Runden in 24 h; echte Umlaufzeit ~92-93 Min. (erster
Kommentar). Bahnhoehe 420 km massstaeblich zum Erdradius 6.371 km. Bahnebene schraeg von oben gesehen,
Erde nicht rotierend (Vereinfachung).

Hook-Varianten:
  1 "Astronauts see 16 SUNRISES a day" (gewaehlt)   2 "You get one sunrise a day. Astronauts get …?"
  3 "A sunrise every 90 minutes"   4 "The ISS just flew into the night - again"   5 "Count the sunrises"

    python make-w6-iss-sunrises-loop.py [--preview DIR]  ->  w6-iss-sunrises-loop.mp4, -loop-cover.png
"""

import math
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageEnhance

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, f, downscale
from bodies import planet
from reelkit import W as WS, new_frame, header_band, blob, cinematic

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
LOOP = 14.0
ECX, ECY, ED = 540, 1000, 600                 # Erde
R_ORB = ED / 2 * (6371 + 420) / 6371          # massstaeblich
TILT = 0.40                                   # Bahnellipse: Hoehe/Breite
PERIOD = 1.5                                  # h pro Runde
ISS_PHOTO = Path(__file__).resolve().parent.parent / "textures" / "iss-nasa-iss056e201248.png"   # NASA, gemeinfrei
ISS_W = 130                                   # px, stark vergroessert (im Bild vermerkt)
TH0 = 0.0                                     # Start im Erdschatten am rechten Rand


def background():
    img, _ = new_frame(53)
    blob(img, -260 * S, ECY * S, 420 * S, 700 * S, (120, 84, 30), blur=int(180 * S))     # Sonne links
    header_band(img, ["Astronauts see 16", "SUNRISES a day"], "SUNRISES")
    planet(img, ECX * S, ECY * S, ED, "earth", light=(-1.0, -0.12, 0.18), lon0=250, tilt=-12)
    d = ImageDraw.Draw(img)
    d.text((40 * S, (ECY - 18) * S), "← Sun", font=f(28 * S), fill=SEC)
    y = 1442 * S
    note = "Orbit height to scale · station enlarged · 1 lap ≈ 90 min, sped up"
    d.text(((WS - d.textlength(note, font=f(24 * S))) / 2, y), note, font=f(24 * S), fill=SEC)
    cta = "Save this: find the ISS over your city"
    d.text(((WS - d.textlength(cta, font=f(34 * S, bold=True))) / 2, y + 40 * S), cta,
           font=f(34 * S, bold=True), fill=FG)
    sub = "free: NASA “Spot the Station”"
    d.text(((WS - d.textlength(sub, font=f(28 * S))) / 2, y + 92 * S), sub, font=f(28 * S), fill=ACC)
    return downscale(img, W, H)


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def hours(t):
    """Uhrzeit: erste Runde langsam (0-3,5 s), dann beschleunigt bis 24 h (11 s), danach Halt."""
    if t < 3.5:
        return PERIOD * t / 3.5
    if t < 11.0:
        u = (t - 3.5) / 7.5
        return PERIOD + (24 - PERIOD) * (u ** 1.35)
    return 24.0


def pos(h):
    th = TH0 + 2 * math.pi * h / PERIOD
    x, s = R_ORB * math.cos(th), math.sin(th)
    sx, sy = ECX + x, ECY + R_ORB * s * TILT
    front = s > 0
    shadow = x > 0 and abs(R_ORB * s) < ED / 2
    hidden = (not front) and (sx - ECX) ** 2 + ((sy - ECY)) ** 2 < (ED / 2) ** 2
    return sx, sy, shadow, hidden


def sunrises(h):
    """Anzahl Schattenaustritte bis Stunde h."""
    th_exit = math.asin(min(1.0, (ED / 2) / R_ORB))                 # Austrittswinkel nach Bahnmitte
    total = (TH0 + 2 * math.pi * h / PERIOD - th_exit) / (2 * math.pi)
    first = (TH0 - th_exit) / (2 * math.pi)
    return max(0, math.floor(total) - math.floor(first))


def iss_sprites():
    """Freigestelltes NASA-Foto (iss056e201248): beleuchtet und im Erdschatten (fast dunkel)."""
    ph = Image.open(ISS_PHOTO).convert("RGBA")
    ph = ph.resize((ISS_W, int(ph.height * ISS_W / ph.width)), Image.LANCZOS)
    rgb, a = ph.convert("RGB"), ph.getchannel("A")
    lit = ImageEnhance.Brightness(rgb).enhance(1.15)
    dark = ImageEnhance.Brightness(rgb).enhance(0.16)
    return (lit, a), (dark, a)


def draw_iss(im, x, y, sprite):
    sp, a = sprite
    im.paste(sp, (int(x - sp.width / 2), int(y - sp.height / 2)), a)


def frame(bg, iss, t):
    im = bg.copy()
    d = ImageDraw.Draw(im)
    h = hours(t)
    fade = 1 - ease((t - 13.3) / 0.6)
    # Bahn (nur sichtbare Teile)
    pts = []
    for k in range(361):
        sx, sy, sh, hid = pos(k / 360 * PERIOD)
        pts.append(None if hid else (sx, sy, sh))
    for a, b in zip(pts, pts[1:]):
        if a and b:
            d.line([a[0], a[1], b[0], b[1]], fill=(70, 78, 100) if a[2] else (120, 130, 160), width=2)
    # Spur der letzten Minuten
    for j in range(14, 0, -1):
        hh = h - j * 0.012
        if hh < 0:
            continue
        sx, sy, sh, hid = pos(hh)
        if not hid and not sh:
            r = 3.2 * (1 - j / 15)
            d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(200, 190, 150))
    sx, sy, sh, hid = pos(h)
    n = sunrises(h)
    # Aufblitzen beim Sonnenaufgang
    since = None
    for back in range(1, 8):
        if sunrises(hours(max(0, t - back / FPS))) < n:
            since = back
            break
    if since:                                                      # Blitz am Schattenaustritt
        th_exit = math.asin(min(1.0, (ED / 2) / R_ORB))
        fx, fy = ECX + R_ORB * math.cos(th_exit), ECY + R_ORB * math.sin(th_exit) * TILT
        rr = 40 + since * 8
        a = 1 - since / 8
        glow = Image.new("RGB", im.size, (0, 0, 0))
        blob(glow, int(fx), int(fy), rr, rr, (int(255 * a), int(200 * a), int(110 * a)), blur=18)
        from PIL import ImageChops
        im = ImageChops.add(im, glow)
        d = ImageDraw.Draw(im)
    if not hid:
        draw_iss(im, sx, sy, iss[1] if sh else iss[0])
        d = ImageDraw.Draw(im)
    st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
    # Zaehler + Uhr
    hh, mm = int(h) % 25, int((h % 1) * 60)
    clock = f"{hh:02d}:{mm:02d}"
    d.text((W - 60 - d.textlength(clock, font=f(44, bold=True)), 600), clock, font=f(44, bold=True), fill=FG, **st)
    d.text((W - 60 - d.textlength("time of day", font=f(24)), 654), "time of day", font=f(24), fill=SEC, **st)
    if fade > 0:
        lab = f"ISS sunrises: {n}"
        col = tuple(int(c * fade) for c in ACC)
        d.text((60, 1330), lab, font=f(52, bold=True), fill=col, **st)
        you = 1 if h >= 6.5 else 0
        d.text((60 + d.textlength(lab, font=f(52, bold=True)) + 40, 1346), f"You: {you}", font=f(36, bold=True),
               fill=tuple(int(c * fade) for c in SEC), **st)
    if h < 1.6 and t < 3.6:
        status = "night side · no sunlight" if sh else "back in sunlight!"
        d.text((60, 600), status, font=f(30, bold=True), fill=FG if sh else ACC, **st)
    return im


def main():
    bg = background()
    iss = iss_sprites()
    print("sunrises in 24 h:", sunrises(24.0))
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (0.6, 2.2, 7.0, 12.0):
            cinematic(frame(bg, iss, t), 0).save(prev / f"iss-{t:.1f}.png")
        print("preview saved")
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(LOOP * FPS)
    out = OUT / "w6-iss-sunrises-loop.mp4"
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg, iss, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg, iss, 7.0), 0).save(OUT / "w6-iss-sunrises-loop-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
