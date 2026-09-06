"""Woche 1, Donnerstag - Space-Tech & Tools:
"See Saturn's rings for under $200 - what to actually buy". Karussell, 6 Slides, 1080x1080.
Affiliate-Kennzeichnung: Slide 6 + Caption (docs/canva-vorlagen-woche1.md, Post 3).

    python make-w1-saturn-gear.py   ->  w1-saturn-gear-01.png ... -06.png (+ _montage.png)
"""

import sys
from pathlib import Path

from PIL import ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import (S, FG, SEC, ACC, HAIR, f, fmono, tracked, wrap, canvas, glow,
                      furniture, ring_mark, downscale)

OUT = Path(__file__).resolve().parent
W = 1080 * S
M = 96 * S
TOTAL = 6

FACTS = [
    ("You need about 25-30x magnification",
     "That's the point where the rings separate from the planet and become obvious."),
    ("A 70-90 mm refractor, or a 114-130 mm tabletop reflector",
     "Both sit in the $120-$200 range and show the rings, Jupiter's moons and lunar craters."),
    ("Skip the cheap \"500x\" department-store scopes",
     "Wobbly mounts, empty magnification. A steady mount matters far more than big numbers."),
    ("Steady air beats big aperture",
     "Wait until Saturn is high, let the scope cool for 20 minutes, don't look over rooftops."),
]


def deck(d, i):
    furniture(d, W, M, f"{i:02d} / {TOTAL:02d}")


def slide_hook():
    img, _ = canvas(W, W)
    img = glow(img, [W * 0.45, -W * 0.30, W * 1.15, W * 0.42], strength=0.16, blur_frac=0.12)
    d = ImageDraw.Draw(img)
    deck(d, 1)
    y = int(W * 0.30)
    tracked(d, (M, y), "SPACE-TECH", fmono(27 * S), ACC, 6 * S)
    y += 58 * S
    fo = f(74 * S, bold=True)
    for ln in wrap(d, "See Saturn's rings for under $200", fo, W - 2 * M):
        d.text((M, y), ln, font=fo, fill=FG)
        y += 88 * S
    d.line([M, int(W * 0.80), M + 60 * S, int(W * 0.80)], fill=HAIR, width=3 * S)
    d.text((M, int(W * 0.80) + 20 * S), "what to actually buy →", font=f(30 * S), fill=SEC)
    return img


def slide_fact(i):
    img, _ = canvas(W, W)
    d = ImageDraw.Draw(img)
    deck(d, i + 2)
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


def slide_cta():
    img, _ = canvas(W, W)
    d = ImageDraw.Draw(img)
    deck(d, 6)
    ring_mark(img, W // 2, int(W * 0.33), 44 * S)
    fo = f(58 * S, bold=True)
    y = int(W * 0.45)
    for ln in ["Steady scope,", "steady sky"]:
        tw = d.textlength(ln, font=fo)
        d.text((W / 2 - tw / 2, y), ln, font=fo, fill=FG)
        y += 72 * S
    sub = "Follow @theorbitlog · new gear guide every Thursday"
    fs = f(30 * S)
    tw = d.textlength(sub, font=fs)
    d.text((W / 2 - tw / 2, y + 12 * S), sub, font=fs, fill=SEC)
    return img


def main():
    slides = [slide_hook()] + [slide_fact(i) for i in range(4)] + [slide_cta()]
    for n, s in enumerate(slides, 1):
        downscale(s, 1080, 1080).save(OUT / f"w1-saturn-gear-{n:02d}.png")
    th = 360
    from PIL import Image
    mont = Image.new("RGB", (th * 3, th * 2), (0, 0, 0))
    for i, s in enumerate(slides):
        mont.paste(downscale(s, 1080, 1080).resize((th, th)), ((i % 3) * th, (i // 3) * th))
    mont.save(OUT / "w1-saturn-gear_montage.png")
    print("saved 6 slides + montage")


if __name__ == "__main__":
    main()
