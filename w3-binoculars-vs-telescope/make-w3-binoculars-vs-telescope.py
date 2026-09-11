"""Woche 3, Donnerstag - Space-Tech & Tools:
"Binoculars vs. your first telescope - what beginners should get". Karussell, 6 Slides,
1080x1080, gleiches Muster wie w2-stargazing-apps. Kein Affiliate-Link, keine Markennennung
(docs/monetarisierung.md: erst ab ~1.000-5.000 Followern; reine, produktneutrale Kaufberatung).

    python make-w3-binoculars-vs-telescope.py   ->  w3-binoculars-vs-telescope-01..06.png (+ montage)
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import (S, FG, SEC, ACC, HAIR, f, fmono, tracked, wrap, canvas, glow,
                      furniture, ring_mark, downscale)

OUT = Path(__file__).resolve().parent
W = 1080 * S
M = 96 * S
TOTAL = 6


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
    fo = f(64 * S, bold=True)
    for ln in wrap(d, "Buy binoculars before your first telescope", fo, W - 2 * M):
        d.text((M, y), ln, font=fo, fill=FG)
        y += 78 * S
    d.line([M, int(W * 0.80), M + 60 * S, int(W * 0.80)], fill=HAIR, width=3 * S)
    d.text((M, int(W * 0.80) + 20 * S), "what beginners should actually get →",
           font=f(28 * S), fill=SEC)
    return img


FACTS = [
    ("A pair of 10x50 binoculars beats a cheap telescope",
     "Wide field of view, easy to point by hand, and enough light-gathering to show Jupiter's four largest moons and craters on the Moon."),
    ("Department-store telescopes often disappoint",
     "Shaky mounts and tiny fields of view make cheap telescopes hard to aim - a big reason first-time buyers give up within weeks."),
    ("Aperture matters more than magnification",
     "A telescope's light-gathering power (its aperture, in mm) decides how much detail and how many faint objects you can see - not the '450x zoom!' printed on the box."),
    ("Ready to upgrade? Look at a Dobsonian",
     "A simple mirror-and-tube design on a rocking base - it gives the most aperture per dollar of any beginner telescope type."),
]


def slide_fact(i):
    img, _ = canvas(W, W)
    d = ImageDraw.Draw(img)
    deck(d, i + 2)
    head, sub = FACTS[i]
    fo, fs = f(50 * S, bold=True), f(32 * S)
    hl = wrap(d, head, fo, W - 2 * M)
    sl = wrap(d, sub, fs, W - 2 * M)
    rule_h, gap = 4 * S, 34 * S
    total = rule_h + gap + len(hl) * 60 * S + 20 * S + len(sl) * 44 * S
    y = (W - total) // 2
    d.rectangle([M, y, M + 64 * S, y + rule_h], fill=ACC)
    y += rule_h + gap
    for ln in hl:
        d.text((M, y), ln, font=fo, fill=FG)
        y += 60 * S
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
    for ln in ["Start simple,", "look up tonight"]:
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
        downscale(s, 1080, 1080).save(OUT / f"w3-binoculars-vs-telescope-{n:02d}.png")
    th = 360
    mont = Image.new("RGB", (th * 3, th * 2), (0, 0, 0))
    for i, s in enumerate(slides):
        mont.paste(downscale(s, 1080, 1080).resize((th, th)), ((i % 3) * th, (i // 3) * th))
    mont.save(OUT / "w3-binoculars-vs-telescope_montage.png")
    print("saved 6 slides + montage")


if __name__ == "__main__":
    main()
