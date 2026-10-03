"""Woche 6, Freitag - Reel "You can see another galaxy this weekend. No telescope."
8 Frames, 1080x1920, eigene Vektorgrafik (Sternbilder schematisch), langsamer Zoom je Frame.

Fakten (NASA Science "Andromeda Galaxy", Sky & Telescope "Find the Andromeda Galaxy",
Mondphasen 2026 timeanddate/LPL):
  Neumond 10.10.2026, 15:50 UTC -> Wochenende 9.-11.10. ohne stoerendes Mondlicht.
  M31: ~2,5 Mio. Lichtjahre, Helligkeit ~3,4 mag, unter dunklem Himmel mit blossem Auge als
  schwacher, laenglicher Nebelfleck sichtbar (kein Spiralbild wie auf Fotos), indirektes Sehen
  hilft. Oktober abends Nordhalbkugel: ~2 h nach Sonnenuntergang hoch im Osten/Nordosten.
  Aufsuchen: Cassiopeias "W" - die tiefere V-Haelfte zeigt grob in Richtung M31 (gaengige
  Aufsuchhilfe); Alternative ueber Pegasus-Quadrat/Mirach (first_comment).
  Fernglas zeigt das helle Zentrum + laengliche Form. Suedhalbkugel: steht tief im Norden,
  von weit suedlich kaum sichtbar (Caption).

Hook-Varianten (Formatvorlage Woche 6):
  1 "You can see another galaxy this weekend. No telescope." (gewaehlt)
  2 "The oldest light you'll ever see with your own eyes"   3 "This weekend is the darkest of October"
  4 "2.5 million years old - and visible from your backyard"
  5 "Most people have never seen another galaxy"

    python make-w6-andromeda-weekend-reel.py  ->  w6-andromeda-weekend-01..08.png, -cover.png, .mp4
"""

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono
from bodies import planet
from reelkit import (W, H, M, TOP_SAFE, new_frame, header, footer_handle, ruler, ctext,
                     ctext_block, frame_save, blob, finish)

OUT = Path(__file__).resolve().parent
GY = TOP_SAFE + 400 * S
TY = TOP_SAFE + 800 * S

# Cassiopeia (schematisch, W-Form) und M31-Position relativ dazu (Leinwand-Ausgabepx)
CAS = [(-210, -60), (-110, 30), (-20, -40), (80, 40), (190, -50)]
M31 = (40, 300)


def stat(d, label, big, sub, big_col=ACC):
    ctext(d, label, f(46 * S, bold=True), FG, TY)
    ctext(d, big, f(92 * S, bold=True), big_col, TY + 66 * S)
    ctext_block(d, sub, f(34 * S), SEC, TY + 196 * S, 46 * S, W - 2 * M - 40 * S)


def galaxy(img, cx, cy, size, strength=1.0, angle=-35):
    """Andromeda als laenglicher Nebelfleck (so wie mit blossem Auge/Fernglas): heller Kern,
    weicher Halo, angedeutete Staubbahn - bewusst kein Foto-Spiralbild."""
    layer = Image.new("L", (int(size * 3), int(size * 3)), 0)
    ld = ImageDraw.Draw(layer)
    c = size * 1.5
    for k, a in [(1.0, 60), (0.7, 90), (0.45, 140), (0.22, 220)]:
        ld.ellipse([c - size * k, c - size * k * 0.32, c + size * k, c + size * k * 0.32], fill=a)
    layer = layer.filter(ImageFilter.GaussianBlur(size * 0.12))
    ld = ImageDraw.Draw(layer)
    ld.arc([c - size * 0.8, c - size * 0.22, c + size * 0.8, c + size * 0.3], 200, 340, fill=20,
           width=max(1, int(size * 0.04)))
    layer = layer.filter(ImageFilter.GaussianBlur(size * 0.03)).rotate(angle, resample=Image.BICUBIC)
    layer = layer.point(lambda p: int(p * strength))
    img.paste((236, 228, 214), (int(cx - c), int(cy - c)), layer)


def star_dot(img, x, y, r, col=(250, 250, 255)):
    blob(img, int(x), int(y), int(r * 3), int(r * 3), col, blur=int(r * 1.5), alpha=120)
    ImageDraw.Draw(img).ellipse([x - r, y - r, x + r, y + r], fill=col)


def sky(img, cx, cy, w_lines=False, arrow=False, gal=0.0, label=True):
    """Himmelsausschnitt: Cassiopeia-W, optional Linien, Pfeil und Galaxie."""
    pts = [(cx + x * S, cy + y * S) for x, y in CAS]
    d = ImageDraw.Draw(img)
    if w_lines:
        d.line(pts, fill=(90, 110, 150), width=3 * S)
    for x, y in pts:
        star_dot(img, x, y, 7 * S)
    gx, gy = cx + M31[0] * S, cy + M31[1] * S
    if gal:
        galaxy(img, gx, gy, 90 * S, gal)
    d = ImageDraw.Draw(img)
    if arrow:                                                          # tiefere V-Haelfte -> M31
        ax, ay = pts[3]
        bx, by = gx + 10 * S, gy - 60 * S
        d.line([ax, ay + 20 * S, bx, by], fill=ACC, width=5 * S)
        ang = math.atan2(by - ay, bx - ax)
        for s_ in (-1, 1):
            d.line([bx, by, bx - math.cos(ang + s_ * 0.5) * 30 * S, by - math.sin(ang + s_ * 0.5) * 30 * S],
                   fill=ACC, width=5 * S)
    if label:
        ctext(d, "Cassiopeia", f(30 * S, bold=True), SEC, cy - 140 * S, cx=cx)
        if gal:
            ctext(d, "Andromeda", f(30 * S, bold=True), ACC, gy + 70 * S, cx=gx)


def horizon(img):
    """Baum-/Huegel-Silhouette am unteren Rand."""
    d = ImageDraw.Draw(img)
    rnd = random.Random(5)
    y0 = H - 150 * S
    pts = [(0, H)]
    for i in range(0, 41):
        x = W * i / 40
        pts.append((x, y0 + math.sin(i * 0.35) * 30 * S + rnd.uniform(-10, 10) * S))
    pts.append((W, H))
    d.polygon(pts, fill=(3, 4, 6))
    for x in (W * 0.12, W * 0.86):
        for k in range(4):
            w = (54 - k * 11) * S
            d.polygon([(x - w, y0 - k * 38 * S + 10 * S), (x + w, y0 - k * 38 * S + 10 * S),
                       (x, y0 - (k + 1) * 38 * S - 14 * S)], fill=(3, 4, 6))


def frame_hook():
    img, d = new_frame(1)
    galaxy(img, W // 2, TOP_SAFE + 420 * S, 230 * S, 1.0)
    horizon(img)
    d = ImageDraw.Draw(img)
    header(d, "THIS WEEKEND · OCT 9-11")
    y = TOP_SAFE + 760 * S
    ctext(d, "You can see", f(78 * S, bold=True), FG, y)
    ctext(d, "another galaxy", f(78 * S, bold=True), ACC, y + 92 * S)
    ctext(d, "this weekend.", f(78 * S, bold=True), FG, y + 184 * S)
    ctext(d, "No telescope.", f(52 * S, bold=True), SEC, y + 300 * S)
    footer_handle(d)
    return img


def moon_phase_row(img, y, highlight):
    xs = [W // 2 - 300 * S, W // 2 - 150 * S, W // 2, W // 2 + 150 * S, W // 2 + 300 * S]
    lights = [(-1.0, 0, 0.0), (-1.0, 0, -0.7), None, (1.0, 0, -0.7), (1.0, 0, 0.0)]   # abnehmend -> Neumond -> zunehmend (Nordhalbkugel)
    for i, (x, l) in enumerate(zip(xs, lights)):
        if i == 2:
            ImageDraw.Draw(img).ellipse([x - 55 * S, y - 55 * S, x + 55 * S, y + 55 * S],
                                        outline=ACC if highlight else HAIR, width=4 * S)
        else:
            planet(img, x, y, 100, "moon", light=l, glow=False)
    return xs


def frame_why():
    img, d = new_frame(2)
    header(d, "WHY THIS WEEKEND")
    xs = moon_phase_row(img, GY, True)
    d = ImageDraw.Draw(img)
    ctext(d, "Oct 10", f(34 * S, bold=True), ACC, GY + 80 * S, cx=xs[2])
    stat(d, "New Moon on Saturday:", "no moonlight",
         "The darkest nights of October - perfect for faint things.")
    ruler(d, 1)
    footer_handle(d)
    return img


def frame_when():
    img, d = new_frame(3)
    header(d, "WHEN + WHERE")
    horizon(img)
    d = ImageDraw.Draw(img)
    cx, cy = W // 2, GY + 120 * S
    d.arc([cx - 360 * S, cy - 360 * S, cx + 360 * S, cy + 360 * S], 200, 340, fill=HAIR, width=3 * S)
    star_dot(img, cx + 200 * S, cy - 290 * S, 9 * S, ACC)
    d = ImageDraw.Draw(img)
    ctext(d, "high in the east", f(34 * S, bold=True), ACC, cy - 250 * S, cx=cx + 200 * S)
    stat(d, "About 2 hours", "after sunset",
         "Look east, about halfway up the sky. Northern Hemisphere, away from city lights.")
    ruler(d, 2)
    footer_handle(d)
    return img


def frame_cas():
    img, d = new_frame(4)
    header(d, "STEP 1 · FIND THE 'W'")
    sky(img, W // 2, GY - 60 * S, w_lines=True)
    d = ImageDraw.Draw(img)
    stat(d, "Five bright stars", "shaped like a W",
         "That's Cassiopeia - easy to spot, high in the northeast.")
    ruler(d, 3)
    footer_handle(d)
    return img


def frame_arrow():
    img, d = new_frame(5)
    header(d, "STEP 2 · FOLLOW THE ARROW")
    sky(img, W // 2, GY - 60 * S, w_lines=True, arrow=True, gal=0.75)
    d = ImageDraw.Draw(img)
    stat(d, "The deeper 'V' of the W", "points to it",
         "Follow it down and look for a faint, fuzzy smudge. (Map not to scale.)")
    ruler(d, 4)
    footer_handle(d)
    return img


def frame_see():
    img, d = new_frame(6)
    header(d, "WHAT YOU'LL ACTUALLY SEE")
    galaxy(img, W // 2 - 220 * S, GY, 110 * S, 0.55)
    galaxy(img, W // 2 + 220 * S, GY, 170 * S, 1.0)
    d = ImageDraw.Draw(img)
    ctext(d, "naked eye", f(32 * S, bold=True), SEC, GY + 170 * S, cx=W // 2 - 220 * S)
    ctext(d, "binoculars", f(32 * S, bold=True), ACC, GY + 170 * S, cx=W // 2 + 220 * S)
    stat(d, "A soft, oval glow -", "not a photo",
         "Tip: look slightly beside it. The edge of your vision is more sensitive to faint light.")
    ruler(d, 5)
    footer_handle(d)
    return img


def frame_light():
    img, d = new_frame(7)
    header(d, "THE PAYOFF")
    galaxy(img, W // 2, GY, 220 * S, 1.0)
    d = ImageDraw.Draw(img)
    stat(d, "That light left Andromeda", "2.5 million years ago",
         "The most distant thing most people can ever see with their own eyes.")
    ruler(d, 6)
    footer_handle(d)
    return img


def main():
    frames = [
        frame_hook(),
        frame_why(),
        frame_when(),
        frame_cas(),
        frame_arrow(),
        frame_see(),
        frame_light(),
        frame_save(("Save this", "for Saturday night", "New Moon · Oct 10"),
                   sub="Send it to your stargazing buddy"),
    ]
    finish(frames, OUT, "w6-andromeda-weekend", cover_idx=0, motion=True)


if __name__ == "__main__":
    main()
