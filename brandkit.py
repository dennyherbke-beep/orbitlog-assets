"""Gemeinsame Bausteine fuer die Content-Grafiken (Markensystem).

Farben/Schrift: docs/strategie.md. Wird von den make-*.py Skripten importiert.
Benoetigt: Pillow. Schriften: Segoe UI + Bahnschrift (Windows-Standard).
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FDIR = Path("C:/Windows/Fonts")

S = 2                     # Supersampling
BG = (11, 14, 20)
FG = (242, 244, 248)
SEC = (169, 178, 195)
ACC = (255, 180, 84)
HAIR = (35, 42, 56)
HANDLE = "@theorbitlog"


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


def canvas(w, h):
    """Hintergrund mit dezenter Rand-Abdunklung. Gibt (img, draw) zurueck."""
    img = Image.new("RGB", (w, h), BG)
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse([-w * 0.28, -h * 0.28, w * 1.28, h * 1.28], fill=255)
    m = m.filter(ImageFilter.GaussianBlur(min(w, h) * 0.26))
    img = Image.composite(img, Image.new("RGB", (w, h), (6, 8, 12)), m)
    return img, ImageDraw.Draw(img)


def glow(img, box, color=ACC, strength=0.22, blur_frac=0.12):
    w, h = img.size
    g = Image.new("L", (w, h), 0)
    ImageDraw.Draw(g).ellipse(box, fill=255)
    g = g.filter(ImageFilter.GaussianBlur(min(w, h) * blur_frac))
    return Image.composite(Image.new("RGB", (w, h), color), img,
                           Image.eval(g, lambda p: int(p * strength)))


def furniture(d, w, m, left, right=HANDLE, size=24):
    tracked(d, (m, m), left, fmono(size * S), SEC, 2 * S)
    tw = d.textlength(right, font=fmono(size * S))
    d.text((w - m - tw, m), right, font=fmono(size * S), fill=SEC)


_MARK_CACHE = {}


def brand_mark():
    """Laedt das freigestellte Marken-Icon (Ringplanet, identisch zum Profilbild).
    Erzeugt/aktualisiert mit make-brand-mark.py."""
    if "img" not in _MARK_CACHE:
        _MARK_CACHE["img"] = Image.open(Path(__file__).resolve().parent / "brand-mark.png").convert("RGBA")
    return _MARK_CACHE["img"]


def ring_mark(img, cx, cy, s):
    """Marken-Icon auf CTA-/Cover-Slides. img = Ziel-Bild, cx/cy = Mittelpunkt, s = Groesse."""
    sz = max(1, int(s * 3.8))
    mark = brand_mark().resize((sz, sz), Image.LANCZOS)
    img.paste(mark, (int(cx - sz / 2), int(cy - sz / 2)), mark)


def downscale(img, w, h):
    return img.resize((w, h), Image.LANCZOS)
