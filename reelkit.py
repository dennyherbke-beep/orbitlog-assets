"""Gemeinsame Bausteine fuer 1080x1920-Reels (ab Woche 4): Rahmen, Kugel-Schattierung,
Frame-Export, Montage und ffmpeg-Zusammenbau. Baut auf brandkit.py auf.

Reel-Skripte importieren per sys.path-Zeile (Elternordner) und rufen am Ende
`finish(frames, OUT, "w4-...", cover_idx)` auf.
Benoetigt: Pillow, imageio-ffmpeg (liefert die ffmpeg-Binary).
"""

import random
import subprocess
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from brandkit import S, FG, SEC, ACC, HAIR, f, fmono, tracked, wrap, canvas, ring_mark, downscale

W = 1080 * S
H = 1920 * S
M = 96 * S
TOP_SAFE = 250 * S
BOT_SAFE = 300 * S
SEC_PER_FRAME = 2.5


# ---------------------------------------------------------------- Rahmen

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


def new_frame(seed):
    img, _ = canvas(W, H)
    starfield(img, seed)
    return img, ImageDraw.Draw(img)


def header(d, label):
    tracked(d, (M, TOP_SAFE), label, fmono(26 * S), ACC, 5 * S)


def footer_handle(d):
    text = "@theorbitlog"
    tw = d.textlength(text, font=fmono(22 * S))
    d.text((W / 2 - tw / 2, H - BOT_SAFE + 6 * S), text, font=fmono(22 * S), fill=SEC)


def ruler(d, step, total=8):
    """Kleine Fortschrittsanzeige unten (symbolisch)."""
    y = H - BOT_SAFE - 70 * S
    x0 = W / 2 - (total - 1) * 26 * S / 2
    for i in range(total):
        x = x0 + i * 26 * S
        r = 6 * S if i != step else 9 * S
        col = ACC if i == step else HAIR
        d.ellipse([x - r, y - r, x + r, y + r], fill=col)


def ctext(d, s, font, fill, y, cx=None):
    cx = W / 2 if cx is None else cx
    d.text((cx - d.textlength(s, font=font) / 2, y), s, font=font, fill=fill)


def ctext_block(d, s, font, fill, y, line_h, maxw=None):
    """Zentrierter Umbruchtext, gibt die naechste freie y-Position zurueck."""
    for ln in wrap(d, s, font, maxw or (W - 2 * M)):
        ctext(d, ln, font, fill, y)
        y += line_h
    return y


def frame_cta(lines=("Follow for one", "every day"), seed=99):
    img, _ = new_frame(seed)
    d = ImageDraw.Draw(img)
    ring_mark(img, W // 2, TOP_SAFE + int(H * 0.20), 46 * S)
    fo = f(58 * S, bold=True)
    y = TOP_SAFE + int(H * 0.32)
    for ln in lines:
        ctext(d, ln, fo, FG, y)
        y += 72 * S
    ctext(d, "@theorbitlog", fmono(34 * S), ACC, y + 20 * S)
    return img


def bookmark(d, cx, cy, h, fill=ACC, width=None):
    """Lesezeichen-Umriss wie das Instagram-Speichern-Symbol (Hoehe h, Mittelpunkt cx/cy)."""
    w = h * 0.72
    x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    pts = [(x0, y0), (x1, y0), (x1, y1), (cx, y1 - h * 0.28), (x0, y1), (x0, y0)]
    d.line(pts, fill=fill, width=width or max(2, int(h * 0.08)), joint="curve")


def frame_save(lines, sub="Follow @theorbitlog for more", seed=98):
    """Endframe mit Speicheranreiz (ab 27.09.2026 Standard statt reinem Follow-CTA):
    Lesezeichen-Symbol, 2-3 Zeilen mit konkretem Grund zum Speichern, Follow als Zusatz."""
    img, _ = new_frame(seed)
    d = ImageDraw.Draw(img)
    bookmark(d, W // 2, TOP_SAFE + int(H * 0.17), 150 * S)
    fo = f(62 * S, bold=True)
    y = TOP_SAFE + int(H * 0.30)
    for n, ln in enumerate(lines):
        ctext(d, ln, fo, ACC if n == 0 else FG, y)
        y += 78 * S
    ctext(d, sub, f(34 * S), SEC, y + 40 * S)
    footer_handle(d)
    return img


# ---------------------------------------------------------------- Kugeln

def blob(img, cx, cy, rx, ry, color, blur=10, alpha=255):
    layer = Image.new("RGB", img.size, color)
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=alpha)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    img.paste(layer, (0, 0), m)


def band(img, y0, y1, color, alpha=255, blur=10):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rectangle([0, y0, img.width, y1], fill=alpha)
    if blur:
        m = m.filter(ImageFilter.GaussianBlur(blur))
    img.paste(Image.new("RGB", img.size, color), (0, 0), m)


def grain(img, amount=14, seed=0):
    """Feines Rauschen ueber eine Textur (bricht flache Farbflaechen auf)."""
    noise = Image.effect_noise(img.size, 60).convert("RGB")
    return Image.blend(img, ImageChops.overlay(img, noise), amount / 100)


TEX = 512
_SHADE = {}


def _shade_map(light):
    if light in _SHADE:
        return _SHADE[light]
    n = sum(c * c for c in light) ** 0.5
    lx, ly, lz = (c / n for c in light)
    img = Image.new("L", (TEX, TEX), 0)
    px = img.load()
    r = TEX / 2
    for j in range(TEX):
        ny = (j - r + 0.5) / r
        for i in range(TEX):
            nx = (i - r + 0.5) / r
            d2 = nx * nx + ny * ny
            if d2 <= 1.0:
                nz = (1.0 - d2) ** 0.5
                inten = max(0.0, nx * lx + ny * ly + nz * lz)
                px[i, j] = int(min(255, 40 + inten * 215))
    mask = Image.new("L", (TEX, TEX), 0)
    ImageDraw.Draw(mask).ellipse([2, 2, TEX - 3, TEX - 3], fill=255)
    _SHADE[light] = (img, mask.filter(ImageFilter.GaussianBlur(1.2)))
    return _SHADE[light]


def sphere(img, cx, cy, d_px, tex, glow_color, ring=False, light=(-0.55, -0.65, 0.62)):
    """Schattierte Kugel mit Textur `tex` (TEX x TEX RGB) und Glow; optional Ring (Saturn)."""
    shade, mask = _shade_map(light)
    d = max(2, int(d_px * S))
    r = d // 2
    blob(img, cx, cy, int(r * 1.5), int(r * 1.5), glow_color, blur=int(r * 0.55), alpha=110)
    rx, ry = int(r * 1.9), int(r * 0.55)
    if ring:
        ImageDraw.Draw(img).arc([cx - rx, cy - ry, cx + rx, cy + ry], 20, 160,
                                fill=(214, 196, 158), width=max(2, int(r * 0.05)))
    shaded = ImageChops.multiply(tex, Image.merge("RGB", (shade, shade, shade)))
    img.paste(shaded.resize((d, d), Image.LANCZOS), (cx - r, cy - r), mask.resize((d, d), Image.LANCZOS))
    if ring:
        ImageDraw.Draw(img).arc([cx - rx, cy - ry, cx + rx, cy + ry], 200, 340,
                                fill=(236, 220, 182), width=max(2, int(r * 0.05)))


def tex_saturn():
    img = Image.new("RGB", (TEX, TEX), (222, 198, 150))
    for i in range(0, 7, 2):
        band(img, int(TEX * i / 7), int(TEX * (i + 1) / 7), (196, 168, 118), alpha=150, blur=10)
    return grain(img, 10, 1)


def tex_moon():
    img = Image.new("RGB", (TEX, TEX), (172, 170, 166))
    rnd = random.Random(7)
    for cx, cy, rx, ry in [(190, 170, 78, 56), (300, 150, 52, 46), (250, 250, 70, 52),
                           (165, 290, 45, 40), (340, 250, 40, 34)]:
        blob(img, cx, cy, rx, ry, (112, 112, 116), blur=14, alpha=200)
    for _ in range(46):
        cx, cy = rnd.randint(30, TEX - 30), rnd.randint(30, TEX - 30)
        r = rnd.randint(5, 20)
        blob(img, cx, cy, r, r, (132, 130, 128), blur=r * 0.35, alpha=200)
        blob(img, cx - r * 0.25, cy - r * 0.25, r * 0.8, r * 0.8, (196, 194, 190), blur=r * 0.3, alpha=150)
    return grain(img, 22, 2)


# ---------------------------------------------------------------- Export

def finish(frames, out, prefix, cover_idx, motion=False):
    """Speichert frames (1080x1920) als <prefix>-NN.png, Montage, Cover (frames[cover_idx])
    und baut <prefix>.mp4 (30 fps, 2,5 s/Frame, stille AAC-Spur - keine lizenzierte Musik).
    motion=True (ab Woche 6): langsamer Zoom auf jedem Frame statt Standbild (Watch-Time)."""
    import imageio_ffmpeg

    out = Path(out)
    small = [downscale(im, 1080, 1920) for im in frames]
    for n, im in enumerate(small, 1):
        im.save(out / f"{prefix}-{n:02d}.png")
    small[cover_idx].save(out / f"{prefix}-cover.png")

    tw, th = 240, 427
    cols = 4
    rows = (len(small) + cols - 1) // cols
    mont = Image.new("RGB", (tw * cols, th * rows), (0, 0, 0))
    for i, im in enumerate(small):
        mont.paste(im.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    mont.save(out / f"{prefix}_montage.png")

    total = len(small) * SEC_PER_FRAME
    vf = "fps=30,format=yuv420p"
    if motion:   # 2x hochskalieren gegen Zoom-Ruckeln, Zoom 1.00 -> ~1.06 je Frame, zentriert
        n = int(SEC_PER_FRAME * 30)
        vf = (f"scale=2160:3840,zoompan=z='min(zoom+0.0008,1.06)':d={n}:s=1080x1920:fps=30"
              ":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)',format=yuv420p")
    subprocess.run([
        imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error",
        "-framerate", f"1/{SEC_PER_FRAME}", "-i", str(out / f"{prefix}-%02d.png"),
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "aac", "-b:a", "128k", "-t", str(total), "-movflags", "+faststart",
        str(out / f"{prefix}.mp4"),
    ], check=True)
    print(f"saved {len(small)} frames + cover + montage + {prefix}.mp4 ({total:.0f} s)")
