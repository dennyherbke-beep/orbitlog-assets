"""Layout A - "Explained image of the day": Foto + Marken-Overlay, 1080 x 1350.
Wiederverwendbar fuer alle Explained-Posts - Block "pro Post anpassen" aendern
(POST_DIR = Unterordner in content/assets/, dort muss SRC bereits liegen).

    python make-explained-image.py   ->  <POST_DIR>/<OUTNAME>
"""

from pathlib import Path

from PIL import Image, ImageDraw

from brandkit import S, BG, FG, SEC, ACC, HANDLE, f, fmono, tracked, wrap

# --- pro Post anpassen -------------------------------------------------------
POST_DIR = "first-pillars"        # Unterordner in content/assets/ fuer diesen Post
SRC = "w1-pillars-src.jpg"
OUTNAME = "w1-pillars.png"
KICKER = "EXPLAINED"
HEADLINE = "The Pillars of Creation"
SUBLINE = ("Columns of gas and dust about 4-5 light-years tall, where new stars are "
           "being born. 6,500 light-years away.")
CREDIT = "NASA, ESA, CSA, STScI"
CROP_Y = 0.40          # 0 = oberer Bildrand, 1 = unterer
# ---------------------------------------------------------------------------

OUT = Path(__file__).resolve().parent / POST_DIR
W, H = 1080 * S, 1350 * S
M = 96 * S


def cover(im, w, h, cy):
    sr = im.width / im.height
    if sr > w / h:
        nh, nw = h, round(h * sr)
    else:
        nw, nh = w, round(w / sr)
    im = im.resize((nw, nh), Image.LANCZOS)
    x, y = (nw - w) // 2, round((nh - h) * cy)
    return im.crop((x, y, x + w, y + h))


def vgrad(w, h, y0, y1, p0, p1, power=1.0):
    m = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(m)
    for yy in range(h):
        t = min(1.0, max(0.0, (yy - y0) / (y1 - y0)))
        d.line([(0, yy), (w, yy)], fill=int(p0 + (p1 - p0) * (t ** power)))
    return m


def build():
    img = cover(Image.open(OUT / SRC).convert("RGB"), W, H, CROP_Y)

    img = Image.composite(Image.new("RGB", (W, H), BG), img,
                          vgrad(W, H, int(H * 0.42), H, 0, 255, 1.4))
    img = Image.composite(Image.new("RGB", (W, H), BG), img,
                          vgrad(W, H, 0, int(H * 0.16), 150, 0, 1.0))

    d = ImageDraw.Draw(img)
    fo, fs = f(72 * S, bold=True), f(32 * S)
    hl = wrap(d, HEADLINE, fo, W - 2 * M)
    sl = wrap(d, SUBLINE, fs, W - 2 * M)
    block_h = 46 * S + len(hl) * 84 * S + 18 * S + len(sl) * 44 * S
    y = H - M - block_h
    tracked(d, (M, y), KICKER, fmono(27 * S), ACC, 6 * S)
    y += 46 * S
    for ln in hl:
        d.text((M, y), ln, font=fo, fill=FG)
        y += 84 * S
    y += 18 * S
    for ln in sl:
        d.text((M, y), ln, font=fs, fill=SEC)
        y += 44 * S

    cr = fmono(20 * S)
    d.text((M, M), f"Image: {CREDIT}", font=cr, fill=SEC)
    tw = d.textlength(HANDLE, font=cr)
    d.text((W - M - tw, M), HANDLE, font=cr, fill=SEC)

    return img.resize((1080, 1350), Image.LANCZOS)


if __name__ == "__main__":
    build().save(OUT / OUTNAME)
    print("saved", OUTNAME)
