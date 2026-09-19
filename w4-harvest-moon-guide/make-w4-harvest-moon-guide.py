"""Woche 4, Donnerstag - Space-Tech & Tools: "How to spot Saturn and Neptune by the Harvest Moon".
Karussell, 6 Slides, 1080x1080, gleiches Muster wie w3-binoculars-vs-telescope. Kein Affiliate-Link,
keine Produktnennung ausser der kostenlosen App Stellarium (schon in w2-stargazing-apps genannt).

Fakten: NASA Skywatching Sept. 2026 - am 26.09. geht der Harvest Moon kurz nach Sonnenuntergang im
Osten auf, Saturn steht nahebei, der schwache Neptun (Helligkeit ~8) bildet ein weites Dreieck und
braucht Fernglas/Teleskop. Neptun-Opposition um den 25./26.09. (Quellen weichen um einen Tag ab ->
im Text nur "around Sept 25-26"). Heller Vollmond stoert lichtschwache Objekte.

    python make-w4-harvest-moon-guide.py   ->  w4-harvest-moon-guide-01..06.png (+ montage)
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
    y = int(W * 0.28)
    tracked(d, (M, y), "SPACE-TECH", fmono(27 * S), ACC, 6 * S)
    y += 58 * S
    fo = f(62 * S, bold=True)
    for ln in wrap(d, "Spot Saturn and Neptune next to the Harvest Moon", fo, W - 2 * M):
        d.text((M, y), ln, font=fo, fill=FG)
        y += 76 * S
    d.line([M, int(W * 0.82), M + 60 * S, int(W * 0.82)], fill=HAIR, width=3 * S)
    d.text((M, int(W * 0.82) + 20 * S), "your Sept 26 observing plan, 4 steps →", font=f(28 * S), fill=SEC)
    return img


STEPS = [
    ("1 · Use the Moon as your pointer",
     "On Sept 26 the full Moon rises in the east shortly after sunset - with Saturn nearby. "
     "Saturn is the bright, steady, pale-gold 'star' close to it. No equipment needed."),
    ("2 · Neptune needs optics",
     "Neptune shines at only about magnitude 8 - too faint for the naked eye. "
     "Binoculars (10x50) or a small telescope show it as a faint, star-like dot."),
    ("3 · Beat the Moon's glare",
     "A full Moon washes out faint objects. Block it behind a roof or tree edge. Neptune is at its "
     "brightest of the year around Sept 25-26 and stays close to that for weeks - retry on the "
     "nights after full Moon, when it rises later."),
    ("4 · Bring a star chart",
     "A free app like Stellarium shows exactly where Neptune sits among nearby stars. Match the "
     "star pattern in your binoculars - the 'star' that isn't on the chart is Neptune. "
     "Give your eyes 20 minutes to adapt and use a red light."),
]


def slide_step(i):
    img, _ = canvas(W, W)
    d = ImageDraw.Draw(img)
    deck(d, i + 2)
    head, sub = STEPS[i]
    fo, fs = f(48 * S, bold=True), f(31 * S)
    hl = wrap(d, head, fo, W - 2 * M)
    sl = wrap(d, sub, fs, W - 2 * M)
    rule_h, gap = 4 * S, 34 * S
    total = rule_h + gap + len(hl) * 58 * S + 20 * S + len(sl) * 43 * S
    y = (W - total) // 2
    d.rectangle([M, y, M + 64 * S, y + rule_h], fill=ACC)
    y += rule_h + gap
    for ln in hl:
        d.text((M, y), ln, font=fo, fill=FG)
        y += 58 * S
    y += 20 * S
    for ln in sl:
        d.text((M, y), ln, font=fs, fill=SEC)
        y += 43 * S
    return img


def slide_cta():
    img, _ = canvas(W, W)
    d = ImageDraw.Draw(img)
    deck(d, 6)
    ring_mark(img, W // 2, int(W * 0.33), 44 * S)
    fo = f(58 * S, bold=True)
    y = int(W * 0.45)
    for ln in ["Look east", "after sunset"]:
        tw = d.textlength(ln, font=fo)
        d.text((W / 2 - tw / 2, y), ln, font=fo, fill=FG)
        y += 72 * S
    sub = "Follow @theorbitlog · new gear guide every Thursday"
    fs = f(30 * S)
    tw = d.textlength(sub, font=fs)
    d.text((W / 2 - tw / 2, y + 12 * S), sub, font=fs, fill=SEC)
    return img


def main():
    slides = [slide_hook()] + [slide_step(i) for i in range(4)] + [slide_cta()]
    for n, s in enumerate(slides, 1):
        downscale(s, 1080, 1080).save(OUT / f"w4-harvest-moon-guide-{n:02d}.png")
    th = 360
    mont = Image.new("RGB", (th * 3, th * 2), (0, 0, 0))
    for i, s in enumerate(slides):
        mont.paste(downscale(s, 1080, 1080).resize((th, th)), ((i % 3) * th, (i // 3) * th))
    mont.save(OUT / "w4-harvest-moon-guide_montage.png")
    print("saved 6 slides + montage")


if __name__ == "__main__":
    main()
