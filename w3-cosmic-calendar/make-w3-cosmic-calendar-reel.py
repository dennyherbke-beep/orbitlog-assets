"""Woche 3, Montag - Signature - Cosmic Scale, als REEL statt Karussell:
"Squeeze 13.8 billion years into one year". Carl Sagan's Cosmic Calendar (Cosmos, 1980).
8 Standbild-Frames, 1080x1920 - gleiches Muster wie w2-moon-distance / w3-solar-system-city
(Header/Footer/Ruler-Technik), Icons aus der urspruenglichen Karussell-Version uebernommen.

Entscheidung 2026-09-11: Signature-Slot ab jetzt als Reel statt Karussell, um den
staednigen Ziel-Wert von 2-3 Reels/Woche zu erreichen (Reels bringen deutlich mehr
Nicht-Follower-Reichweite als Karussells, s. docs/wachstum.md). Ersetzt die
Karussell-Fassung (make-w3-cosmic-calendar.py, jetzt nicht mehr in der Queue).

    python make-w3-cosmic-calendar-reel.py   ->  w3-cosmic-calendar-01..08.png (+ montage)

Naechster Schritt: Frames zu einem Reel zusammensetzen (ffmpeg, ~2.5 s/Frame, ohne Musik) ->
.mp4 + Cover.
"""

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono, tracked, wrap, canvas, ring_mark, downscale

OUT = Path(__file__).resolve().parent
W = 1080 * S
H = 1920 * S
M = 96 * S
TOP_SAFE = 250 * S
BOT_SAFE = 300 * S


def blob(img, cx, cy, rx, ry, color, blur=6, alpha=255):
    layer = Image.new("RGB", img.size, color)
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=alpha)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    img.paste(layer, (0, 0), m)


# ---------------------------------------------------------------- Icons (wie Karussell-Fassung)

def icon_galaxy(img, cx, cy, r, seed=5):
    rnd = random.Random(seed)
    blob(img, cx, cy, r * 1.4, r * 1.4, (150, 170, 220), blur=r * 0.5, alpha=70)
    blob(img, cx, cy, r * 0.30, r * 0.30, (255, 248, 224), blur=r * 0.16, alpha=255)
    for arm in range(2):
        base = arm * math.pi
        for t in range(22):
            frac = t / 22
            theta = frac * 2.1 * math.pi
            rr = r * 0.12 * math.exp(0.34 * theta)
            if rr > r * 0.95:
                break
            ang = theta + base
            x, y = cx + rr * math.cos(ang), cy + rr * math.sin(ang) * 0.55
            br = r * 0.10 * (1 - frac * 0.5)
            col = (int(255 - 105 * frac), int(241 - 71 * frac), int(214 + 12 * frac))
            blob(img, x, y, br, br, col, blur=br * 0.6, alpha=int(230 * (1 - frac * 0.3)))
    d = ImageDraw.Draw(img)
    for _ in range(9):
        x = cx + rnd.uniform(-r * 1.3, r * 1.3)
        y = cy + rnd.uniform(-r * 1.3, r * 1.3)
        rr = rnd.uniform(0.8, 1.6) * S
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=FG)


def icon_sun_earth(img, cx, cy, r):
    core, edge = (255, 244, 214), (255, 150, 50)
    blob(img, cx, cy, r * 1.5, r * 1.5, ACC, blur=r * 0.65, alpha=65)
    d = ImageDraw.Draw(img)
    orbit_x, orbit_y = r * 1.05, r * 0.30
    d.ellipse([cx - orbit_x, cy - orbit_y, cx + orbit_x, cy + orbit_y], outline=HAIR, width=max(1, int(S * 0.8)))
    rs = max(1, int(r * 0.58))
    for i in range(rs, 0, -1):
        t = i / rs
        col = tuple(int(edge[k] + (core[k] - edge[k]) * (1 - t)) for k in range(3))
        d = ImageDraw.Draw(img)
        d.ellipse([cx - i, cy - i, cx + i, cy + i], fill=col)
    ex, ey = cx + orbit_x * 0.94, cy - orbit_y * 0.18
    er = r * 0.13
    blob(img, ex, ey, er * 1.9, er * 1.9, (80, 140, 210), blur=er * 0.6, alpha=90)
    d = ImageDraw.Draw(img)
    d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=(70, 130, 200))


def icon_impact(img, cx, cy, r):
    gy = cy + r * 0.45
    blob(img, cx, gy, r * 1.05, r * 0.5, (58, 40, 30), blur=r * 0.22, alpha=210)
    blob(img, cx, gy, r * 0.42, r * 0.42, (255, 210, 148), blur=r * 0.22, alpha=225)
    blob(img, cx, gy, r * 0.20, r * 0.20, (255, 250, 235), blur=r * 0.10, alpha=255)
    d = ImageDraw.Draw(img)
    for ang in (15, 55, 200, 235, 300):
        rad = math.radians(ang)
        ex, ey = cx + math.cos(rad) * r * 0.68, gy + math.sin(rad) * r * 0.5
        d.line([cx, gy, ex, ey], fill=(255, 190, 120), width=max(1, int(S * 0.8)))
    x0, y0 = cx - r * 1.25, cy - r * 1.25
    x1, y1 = cx - r * 0.12, gy - r * 0.05
    d.line([x0, y0, x1, y1], fill=(255, 196, 140), width=max(2, int(r * 0.09)))
    blob(img, x1, y1, r * 0.15, r * 0.15, (255, 232, 195), blur=r * 0.09, alpha=255)


def icon_human(img, cx, cy, r):
    blob(img, cx, cy, r * 1.25, r * 1.25, ACC, blur=r * 0.55, alpha=55)
    d = ImageDraw.Draw(img)
    head_r = r * 0.22
    head_cy = cy - r * 0.52
    d.ellipse([cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r], fill=FG)
    top_y = head_cy + head_r * 0.95
    bot_y = cy + r * 0.55
    top_w, bot_w = r * 0.26, r * 0.48
    d.polygon([(cx - top_w, top_y), (cx + top_w, top_y), (cx + bot_w, bot_y), (cx - bot_w, bot_y)], fill=FG)


ICONS = [icon_galaxy, icon_sun_earth, icon_impact, icon_human]


# ---------------------------------------------------------------- Hintergrund / Rahmen

def starfield(img, seed, n=170):
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        r = rnd.uniform(0.6, 1.8) * S
        op = rnd.randint(70, 200)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(op, op, min(255, op + 20)))
    for _ in range(n // 12):
        x, y = rnd.uniform(0, W), rnd.uniform(0, H)
        r = rnd.uniform(2.0, 3.4) * S
        gl = Image.new("L", img.size, 0)
        ImageDraw.Draw(gl).ellipse([x - r * 3, y - r * 3, x + r * 3, y + r * 3], fill=90)
        gl = gl.filter(ImageFilter.GaussianBlur(r * 1.4))
        img.paste(Image.new("RGB", img.size, FG), (0, 0), gl)
        d.ellipse([x - r, y - r, x + r, y + r], fill=FG)


def header(d, label):
    tracked(d, (M, TOP_SAFE), label, fmono(26 * S), ACC, 5 * S)


def footer_handle(d):
    text = "@theorbitlog"
    tw = d.textlength(text, font=fmono(22 * S))
    d.text((W / 2 - tw / 2, H - BOT_SAFE + 6 * S), text, font=fmono(22 * S), fill=SEC)


def ruler(d, step, total=4):
    y = H - BOT_SAFE - 70 * S
    x0 = W / 2 - (total - 1) * 26 * S / 2
    for i in range(total):
        x = x0 + i * 26 * S
        r = 6 * S if i != step else 9 * S
        col = ACC if i == step else HAIR
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)


# ---------------------------------------------------------------- Content

FACTS = [
    ("The Milky Way doesn't exist until May 1",
     "Our own galaxy takes almost four months of the cosmic year to take shape."),
    ("The Sun and Earth form on September 9",
     "Over eight months in - the solar system is a relative latecomer to the universe."),
    ("The dinosaurs go extinct on December 30",
     "Just a day and a half before the year runs out."),
    ("Modern humans arrive at 23:52 on December 31",
     "With only 8 minutes left in the entire cosmic year."),
]


def frame_title():
    img, d = canvas(W, H)
    starfield(img, seed=1)
    d = ImageDraw.Draw(img)
    header(d, "COSMIC SCALE")
    y = TOP_SAFE + int(H * 0.16)
    fo = f(78 * S, bold=True)
    for ln in ["Squeeze 13.8", "billion years", "into one year"]:
        d.text((M, y), ln, font=fo, fill=FG)
        y += 90 * S
    d.text((M, y + 16 * S), "humans show up with 8 minutes left →", font=f(30 * S), fill=SEC)
    footer_handle(d)
    return img


def frame_fact(i):
    head, sub = FACTS[i]
    img, d = canvas(W, H)
    starfield(img, seed=10 + i)
    d = ImageDraw.Draw(img)
    header(d, f"COSMIC CALENDAR · {i + 1}/4")

    icon_cy = TOP_SAFE + int((H - TOP_SAFE - BOT_SAFE) * 0.20)
    ICONS[i](img, W // 2, icon_cy, 120 * S)
    d = ImageDraw.Draw(img)

    ty = icon_cy + int(160 * S)
    fo, fs = f(56 * S, bold=True), f(32 * S)
    for ln in wrap(d, head, fo, W - 2 * M):
        d.text((M, ty), ln, font=fo, fill=FG)
        ty += 68 * S
    ty += 16 * S
    for ln in wrap(d, sub, fs, W - 2 * M):
        d.text((M, ty), ln, font=fs, fill=SEC)
        ty += 44 * S

    ruler(d, i)
    footer_handle(d)
    return img


def frame_scale():
    """Payoff: Jahresbalken, fast vollstaendig gefuellt, mit markiertem Splitter am Ende."""
    img, d = canvas(W, H)
    starfield(img, seed=77)
    d = ImageDraw.Draw(img)
    header(d, "JAN 1 -> DEC 31, ONE FULL YEAR")

    bar_y = TOP_SAFE + int(H * 0.16)
    bar_h = 30 * S
    x0, x1 = M, W - M
    d.rounded_rectangle([x0, bar_y, x1, bar_y + bar_h], radius=bar_h // 2, fill=HAIR)

    milky = 121 / 365
    sun = 252 / 365
    dino_end = 363 / 365
    humans = 364.99 / 365

    for frac in (milky, sun, dino_end):
        x = x0 + (x1 - x0) * frac
        d.ellipse([x - 9 * S, bar_y + bar_h / 2 - 9 * S, x + 9 * S, bar_y + bar_h / 2 + 9 * S], fill=SEC)
    xh = x0 + (x1 - x0) * humans
    d.ellipse([xh - 12 * S, bar_y + bar_h / 2 - 12 * S, xh + 12 * S, bar_y + bar_h / 2 + 12 * S], fill=ACC)

    ly = bar_y + bar_h + 30 * S
    labels = [(milky, "Milky Way\nMay 1"), (sun, "Sun & Earth\nSep 9"), (dino_end, "Dinosaurs\nDec 30")]
    fl = f(22 * S)
    for frac, text in labels:
        x = x0 + (x1 - x0) * frac
        for j, ln in enumerate(text.split("\n")):
            tw = d.textlength(ln, font=fl)
            xx = min(max(x - tw / 2, x0), x1 - tw)
            d.text((xx, ly + j * 28 * S), ln, font=fl, fill=SEC)

    y2 = bar_y + int(H * 0.20)
    fo = f(46 * S, bold=True)
    for ln in wrap(d, "All of recorded human history fits into", fo, W - 2 * M):
        d.text((M, y2), ln, font=fo, fill=FG)
        y2 += 58 * S
    for ln in wrap(d, "the last 14 seconds of December 31.", fo, W - 2 * M):
        d.text((M, y2), ln, font=fo, fill=ACC)
        y2 += 58 * S
    y2 += 20 * S
    fs = f(28 * S)
    for ln in wrap(d, "Agriculture, writing, every empire, every war - all inside one blink of the cosmic year.",
                   fs, W - 2 * M):
        d.text((M, y2), ln, font=fs, fill=SEC)
        y2 += 40 * S

    footer_handle(d)
    return img


def frame_cta():
    img, d = canvas(W, H)
    starfield(img, seed=99)
    d = ImageDraw.Draw(img)
    ring_mark(img, W // 2, TOP_SAFE + int(H * 0.20), 46 * S)
    fo = f(58 * S, bold=True)
    y = TOP_SAFE + int(H * 0.32)
    for ln in ["Follow for one", "every day"]:
        tw = d.textlength(ln, font=fo)
        d.text((W / 2 - tw / 2, y), ln, font=fo, fill=FG)
        y += 72 * S
    handle = "@theorbitlog"
    fa = fmono(34 * S)
    tw = d.textlength(handle, font=fa)
    d.text((W / 2 - tw / 2, y + 20 * S), handle, font=fa, fill=ACC)
    return img


def main():
    frames = [frame_title()] + [frame_fact(i) for i in range(4)] + [frame_scale(), frame_cta()]
    for n, im in enumerate(frames, 1):
        downscale(im, 1080, 1920).save(OUT / f"w3-cosmic-calendar-{n:02d}.png")
    th_w, th_h = 240, 427
    mont = Image.new("RGB", (th_w * 4, th_h * 2), (0, 0, 0))
    for i, im in enumerate(frames):
        mont.paste(downscale(im, 1080, 1920).resize((th_w, th_h)), ((i % 4) * th_w, (i // 4) * th_h))
    mont.save(OUT / "w3-cosmic-calendar_montage.png")
    print("saved", len(frames), "frames + montage")


if __name__ == "__main__":
    main()
