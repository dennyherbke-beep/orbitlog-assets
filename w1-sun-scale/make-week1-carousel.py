"""Rendert den ersten Post: Signature-Karussell "How big is the Sun compared to Earth?"
als 7 postfertige PNGs (1080x1080) im Markensystem.

    python make-week1-carousel.py

Benoetigt: Pillow. Schriften: Segoe UI + Bahnschrift (Windows-Standard).
Ausgabe: w1-sun-scale-01.png ... -07.png  (+ _montage.png zur Kontrolle)
Text der Fakten-Slides: Liste FACTS unten. Layout-Parameter: Konstanten oben.
Design-System: docs/strategie.md / docs/canva-vorlagen-woche1.md
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).resolve().parent
FDIR = Path("C:/Windows/Fonts")

S = 2                      # Supersampling -> 1080
W = 1080 * S
M = 96 * S                 # Rand

BG = (11, 14, 20)
FG = (242, 244, 248)
SEC = (169, 178, 195)
ACC = (255, 180, 84)
HAIR = (35, 42, 56)

HANDLE = "@theorbitlog"
TOTAL = 7


def f(px, bold=False):
    return ImageFont.truetype(str(FDIR / ("segoeuib.ttf" if bold else "segoeui.ttf")), int(px))


def fmono(px):
    return ImageFont.truetype(str(FDIR / "bahnschrift.ttf"), int(px))


def tracked(d, xy, s, font, fill, track):
    x, y = xy
    for ch in s:
        d.text((x, y), ch, font=font, fill=fill)
        x += d.textlength(ch, font=font) + track


def wrap(d, s, font, maxw):
    words, lines, cur = s.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def base(sun_glow=False):
    img = Image.new("RGB", (W, W), BG)
    d = ImageDraw.Draw(img)
    # dezente Vignette
    vig = Image.new("L", (W, W), 0)
    ImageDraw.Draw(vig).ellipse([-W * 0.3, -W * 0.3, W * 1.3, W * 1.3], fill=40)
    vig = vig.filter(ImageFilter.GaussianBlur(W * 0.25))
    img = Image.composite(Image.new("RGB", (W, W), (6, 8, 12)), img, Image.eval(vig, lambda p: 60 - p if p < 60 else 0))
    d = ImageDraw.Draw(img)
    if sun_glow:
        g = Image.new("L", (W, W), 0)
        ImageDraw.Draw(g).ellipse([W * 0.12, -W * 0.34, W * 0.98, W * 0.40], fill=255)
        g = g.filter(ImageFilter.GaussianBlur(W * 0.13))
        glow = Image.new("RGB", (W, W), ACC)
        img = Image.composite(glow, img, Image.eval(g, lambda p: int(p * 0.22)))
        d = ImageDraw.Draw(img)
    return img, d


def furniture(d, idx):
    tracked(d, (M, M), f"{idx:02d} / {TOTAL:02d}", fmono(24 * S), SEC, 2 * S)
    w = d.textlength(HANDLE, font=fmono(24 * S))
    d.text((W - M - w, M), HANDLE, font=fmono(24 * S), fill=SEC)


def slide_hook():
    img, d = base(sun_glow=True)
    furniture(d, 1)
    y = int(W * 0.30)
    tracked(d, (M, y), "COSMIC SCALE", fmono(27 * S), ACC, 6 * S)
    y += 58 * S
    fo = f(82 * S, bold=True)
    for ln in ["How big is the Sun", "compared to Earth?"]:
        d.text((M, y), ln, font=fo, fill=FG)
        y += 96 * S
    d.line([M, int(W * 0.80), M + 60 * S, int(W * 0.80)], fill=HAIR, width=3 * S)
    d.text((M, int(W * 0.80) + 20 * S), "swipe \u2192", font=f(30 * S), fill=SEC)
    return img


FACTS = [
    ("The Sun is about 109 Earths wide",
     "1,391,000 km across, next to Earth's 12,742 km."),
    ("About 1.3 million Earths would fit inside it",
     "By volume \u2014 it could swallow every planet several times."),
    ("It holds 99.86% of the Solar System's mass",
     "Everything else \u2014 all 8 planets, every moon and asteroid \u2014 is the leftover 0.14%."),
    ("The Sun weighs about 333,000 Earths",
     "That mass is what holds the whole system in orbit."),
]


def slide_fact(i):
    img, d = base()
    furniture(d, i + 2)          # Deck-Position: Hook=1, Fakten=2..5
    head, sub = FACTS[i]
    fo, fs = f(56 * S, bold=True), f(32 * S)
    hl = wrap(d, head, fo, W - 2 * M)
    sl = wrap(d, sub, fs, W - 2 * M)
    rule_h, gap = 4 * S, 34 * S
    total = rule_h + gap + len(hl) * 66 * S + 20 * S + len(sl) * 44 * S
    y = (W - total) // 2
    d.rectangle([M, y, M + 64 * S, y + rule_h], fill=ACC)
    y += rule_h + gap
    for ln in hl:
        d.text((M, y), ln, font=fo, fill=FG)
        y += 66 * S
    y += 20 * S
    for ln in sl:
        d.text((M, y), ln, font=fs, fill=SEC)
        y += 44 * S
    return img


def slide_scale():
    img, d = base()
    furniture(d, 6)
    tracked(d, (M, M + 44 * S), "BOTH TO SCALE", fmono(27 * S), SEC, 5 * S)
    sun_r = int(W * 0.235)
    sx, sy = int(W * 0.33), int(W * 0.54)
    g = Image.new("L", (W, W), 0)
    ImageDraw.Draw(g).ellipse([sx - sun_r, sy - sun_r, sx + sun_r, sy + sun_r], fill=255)
    g = g.filter(ImageFilter.GaussianBlur(sun_r * 0.30))
    img = Image.composite(Image.new("RGB", (W, W), ACC), img, Image.eval(g, lambda p: int(p * 0.30)))
    d = ImageDraw.Draw(img)
    d.ellipse([sx - sun_r, sy - sun_r, sx + sun_r, sy + sun_r], fill=ACC)
    er = max(2 * S, round(sun_r / 109))          # exakt 1/109
    ex = sx + sun_r + 60 * S
    d.ellipse([ex - er, sy - er, ex + er, sy + er], fill=FG)
    lx = ex + er + 10 * S
    d.line([lx, sy, lx + 34 * S, sy], fill=HAIR, width=2 * S)
    tx = lx + 48 * S
    d.text((tx, sy - 40 * S), "Earth", font=f(30 * S, bold=True), fill=FG)
    d.text((tx, sy - 2 * S), "1/109 the width", font=f(23 * S), fill=SEC)
    d.text((M, int(W * 0.82)), "The Sun really is that much bigger.",
           font=f(24 * S), fill=SEC)
    return img


def ring_mark(d, cx, cy, s):
    d.ellipse([cx - s, cy - s, cx + s, cy + s], fill=FG)
    d.arc([cx - int(s * 1.9), cy - int(s * 0.62), cx + int(s * 1.9), cy + int(s * 0.62)],
          200, 360 + 160, fill=ACC, width=max(2, int(s * 0.16)))


def slide_cta():
    img, d = base()
    furniture(d, 7)
    ring_mark(d, W // 2, int(W * 0.34), 46 * S)
    fo = f(60 * S, bold=True)
    lines = ["Follow @theorbitlog", "for one every day"]
    y = int(W * 0.46)
    for ln in lines:
        tw = d.textlength(ln, font=fo)
        d.text((W / 2 - tw / 2, y), ln, font=fo, fill=FG)
        y += 74 * S
    sub = "New space fact daily \u00b7 gear guides on Thursdays"
    fs = f(30 * S)
    tw = d.textlength(sub, font=fs)
    d.text((W / 2 - tw / 2, y + 14 * S), sub, font=fs, fill=SEC)
    return img


def finish(img):
    return img.resize((1080, 1080), Image.LANCZOS)


def main():
    slides = [slide_hook()] + [slide_fact(i) for i in range(4)] + [slide_scale(), slide_cta()]
    paths = []
    for n, s in enumerate(slides, 1):
        p = OUT / f"w1-sun-scale-{n:02d}.png"
        finish(s).save(p)
        paths.append(p)
    # Kontroll-Montage
    th = 360
    mont = Image.new("RGB", (th * 4, th * 2), (0, 0, 0))
    for i, s in enumerate(slides):
        mont.paste(finish(s).resize((th, th)), ((i % 4) * th, (i // 4) * th))
    mont.save(OUT / "w1-sun-scale_montage.png")
    print("saved", len(paths), "slides + montage")


if __name__ == "__main__":
    main()
