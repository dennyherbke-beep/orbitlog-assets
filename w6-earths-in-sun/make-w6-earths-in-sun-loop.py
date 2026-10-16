"""Umbau 16.10.2026 (Woche 8, Mo 19.10.): "How many EARTHS fit inside the Sun?" als durchgehende
Massstab-Animation (Typ a, feste Kopfzeile) statt 8 Folien (make-w6-earths-in-sun-reel.py).
Ablauf: (1) eine Reihe aus 109 Erden legt sich massstaeblich quer ueber die Sonne, (2) die Sonne fuellt
sich von unten mit Erden (Symbol: 1 Punkt ~ 1.000 Erden), Zaehler laeuft bis 1,3 Mio., (3) Twist:
"...and the Sun is just an average star". 11,5 s.

Fakten: Sonnendurchmesser 1.391.400 km / Erddurchmesser 12.742 km = 109 (NASA Sun Facts, NASA Planetary
Fact Sheet); Volumenverhaeltnis 109^3 ~ 1,3 Mio. Mit Luecken (Kugelpackung) passen nur ~960.000 ganze
Erden - steht im ersten Kommentar.

Hook-Varianten:
  1 "How many EARTHS fit inside the Sun?" (gewaehlt)   2 "Most people guess 100. It's not even close."
  3 "109 Earths across. How many inside?"   4 "Fill the Sun with Earths"   5 "The Sun could swallow 1.3 million Earths"

    python make-w6-earths-in-sun-loop.py [--preview DIR]  ->  w6-earths-in-sun-loop.mp4, -loop-cover.png
"""

import math
import random
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageEnhance

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, f, downscale
from bodies import planet, star
from reelkit import W as WS, new_frame, header_band, cinematic

OUT = Path(__file__).resolve().parent
W, H = 1080, 1920
FPS = 30
LOOP = 11.5
SUN_D = 763                                   # px -> 1 Erde = 7 px, 109 quer
SCX, SCY = 540, 1020
EARTH_TRUE = SUN_D / 109
DOT = 20                                      # Symbol-Erde im Fuellbild
TOTAL = 1_300_000


def background():
    img, _ = new_frame(51)
    header_band(img, ["How many EARTHS", "fit inside the Sun?"], "EARTHS")
    star(img, SCX * S, SCY * S, SUN_D, "sun", corona=0.9, spots=False)
    d = ImageDraw.Draw(img)
    y = 1488 * S
    note = "Symbolic fill: each dot ≈ 1,000 Earths · details in the comments"
    d.text(((WS - d.textlength(note, font=f(24 * S))) / 2, y), note, font=f(24 * S), fill=SEC)
    cta = "Send this to someone who guessed 100"
    d.text(((WS - d.textlength(cta, font=f(34 * S, bold=True))) / 2, y + 40 * S), cta,
           font=f(34 * S, bold=True), fill=FG)
    return downscale(img, W, H)


def earth_sprite(d_px):
    size = int(d_px * 2 + 6)
    im = Image.new("RGB", (size * S, size * S), (0, 0, 0))
    planet(im, size * S // 2, size * S // 2, d_px, "earth", light=(-0.2, -0.2, 0.95), lon0=200, glow=False)
    im = ImageEnhance.Brightness(downscale(im, size, size)).enhance(1.35)
    m = Image.new("L", (size * 4, size * 4), 0)
    c, r = size * 2, d_px * 2
    ImageDraw.Draw(m).ellipse([c - r, c - r, c + r, c + r], fill=255)
    return im, m.resize((size, size), Image.LANCZOS)


def fill_positions():
    """Hex-Raster innerhalb der Sonnenscheibe, Reihenfolge von unten nach oben mit etwas Streuung."""
    rng = random.Random(4)
    pts, rr = [], SUN_D / 2 - DOT * 0.6
    dy = DOT * 0.87
    row = 0
    y = SCY - rr
    while y <= SCY + rr:
        off = (DOT / 2) if row % 2 else 0
        x = SCX - rr + off
        while x <= SCX + rr:
            if (x - SCX) ** 2 + (y - SCY) ** 2 <= rr * rr:
                pts.append((x, y, -y + rng.uniform(0, 90)))
            x += DOT
        y += dy
        row += 1
    pts.sort(key=lambda p: p[2])
    return [(x, y) for x, y, _ in pts]


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ctext(d, s, font, fill, y, **kw):
    d.text(((W - d.textlength(s, font=font)) / 2, y), s, font=font, fill=fill, **kw)


def frame(bg, dot, tiny, pts, t):
    im = bg.copy()
    d = ImageDraw.Draw(im)
    st = dict(stroke_width=3, stroke_fill=(8, 10, 14))
    row = ease((t - 0.3) / 2.0)                                  # Phase 1: Reihe aus 109 Erden
    fill = ease((t - 2.8) / 5.2) ** 1.6                          # Phase 2: Volumen
    fade = 1 - ease((t - 10.6) / 0.8)                            # Ausblenden fuer den Loop
    n_row = int(109 * row)
    x0 = SCX - SUN_D / 2 + EARTH_TRUE / 2
    if fade > 0.02 and fill < 0.98:
        for k in range(n_row):
            sp, m = tiny
            im.paste(sp, (int(x0 + k * EARTH_TRUE - sp.width / 2), int(SCY - sp.height / 2)), m)
    n = int(len(pts) * fill * fade)
    sp, m = dot
    for x, y in pts[:n]:
        im.paste(sp, (int(x - sp.width / 2), int(y - sp.height / 2)), m)
    d = ImageDraw.Draw(im)
    # Zaehler ueber der Sonne
    if fill <= 0 and t < 10:
        if row > 0:
            ctext(d, f"{n_row} Earths across", f(54, bold=True), FG, 532, **st)
            if row >= 1:
                ctext(d, "Now fill the whole ball …", f(28), SEC, 598, **st)
        else:
            ctext(d, "Guess before it fills ↓", f(40, bold=True), SEC, 548, **st)
    elif t < 10.6:
        val = TOTAL * fill
        txt = f"{val:,.0f} Earths" if fill < 1 else "1.3 MILLION Earths"
        ctext(d, txt, f(58, bold=True), ACC if fill >= 1 else FG, 528, **st)
        ctext(d, "109 × 109 × 109", f(28), SEC, 598, **st)
    # Massstabs-Erde unten links + Twist
    if 8.4 < t < 10.6:
        a = ease((t - 8.4) / 0.4)
        col = tuple(int(c * a) for c in FG)
        ctext(d, "…and the Sun is just an average star.", f(36, bold=True), col, 1418, **st)
    else:
        ex, ey = 360, 1440
        d.ellipse([ex - 16, ey - 16, ex + 16, ey + 16], outline=ACC, width=2)
        im.paste(tiny[0], (int(ex - tiny[0].width / 2), int(ey - tiny[0].height / 2)), tiny[1])
        d.text((ex + 28, ey - 19), "← 1 Earth, to scale", font=f(28), fill=FG, **st)
    return im


def main():
    bg = background()
    dot, tiny = earth_sprite(DOT - 2), earth_sprite(EARTH_TRUE)
    pts = fill_positions()
    print(f"{len(pts)} dots -> 1 dot = {TOTAL / len(pts):,.0f} Earths")
    if "--preview" in sys.argv:
        prev = Path(sys.argv[sys.argv.index("--preview") + 1])
        prev.mkdir(parents=True, exist_ok=True)
        for t in (0.2, 2.4, 5.5, 9.4):
            cinematic(frame(bg, dot, tiny, pts, t), 0).save(prev / f"earths-{t:.1f}.png")
        print("preview saved")
        return
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    n = int(LOOP * FPS)
    out = OUT / "w6-earths-in-sun-loop.mp4"
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{LOOP:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg, dot, tiny, pts, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg, dot, tiny, pts, 2.4), 0).save(OUT / "w6-earths-in-sun-loop-cover.png")
    print(f"saved {out.name} ({LOOP:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
