"""Woche 6, Donnerstag - Space-Tech-Reel "Your Moon photos look like a white blob. Here's the fix."
8 Frames, 1080x1920, eigene Vektorgrafik (generisches Handy, keine Marke), langsamer Zoom je Frame.

Fakten/Praxis (allgemeine Smartphone-Fotografie; NASA Science "Tips for photographing the Moon"):
  Automatik belichtet auf den dunklen Himmel -> der sonnenbeschienene Mond brennt aus.
  Fix: auf den Mond tippen/halten (Fokus + Belichtung sperren, iOS "AE/AF-Sperre", Android
  aehnlich), Belichtungsregler nach unten, optische Zoomstufe (2x/3x/5x je nach Modell)
  statt Pinch-Digitalzoom ueber die Linse hinaus, Handy abstuetzen + 3-s-Selbstausloeser.
  Halbmond zeigt mehr Krater-Relief als Vollmond (Schatten am Terminator).
  Termine 2026 (UTC): Erstes Viertel 18.10. 16:13, Vollmond ("Hunter's Moon") 26.10. 04:12.

Hook-Varianten (Formatvorlage Woche 6):
  1 "Your Moon photos look like a white blob. Here's the fix." (gewaehlt)
  2 "Stop pinching to zoom on the Moon"   3 "4 taps for a sharp Moon photo"
  4 "Why the Moon looks like a streetlight in your photos"   5 "Your phone can do this"

    python make-w6-moon-phone-reel.py  ->  w6-moon-phone-01..08.png, -cover.png, .mp4
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono
from bodies import planet
from reelkit import (W, H, M, TOP_SAFE, new_frame, header, footer_handle, ruler, ctext,
                     ctext_block, frame_save, blob, finish)

OUT = Path(__file__).resolve().parent
GY = TOP_SAFE + 400 * S
TY = TOP_SAFE + 800 * S
PW, PH = 420 * S, 760 * S          # Handy-Groesse


def stat(d, label, big, sub, big_col=ACC):
    ctext(d, label, f(46 * S, bold=True), FG, TY)
    ctext(d, big, f(92 * S, bold=True), big_col, TY + 66 * S)
    ctext_block(d, sub, f(34 * S), SEC, TY + 196 * S, 46 * S, W - 2 * M - 40 * S)


def sun_icon(d, x, y, r):
    """Belichtungs-Symbol (Sonne mit Strahlen), da der Font kein Sonnen-Glyph hat."""
    import math
    d.ellipse([x - r, y - r, x + r, y + r], fill=ACC)
    for i in range(8):
        a = i * math.pi / 4
        d.line([x + math.cos(a) * r * 1.5, y + math.sin(a) * r * 1.5,
                x + math.cos(a) * r * 2.2, y + math.sin(a) * r * 2.2], fill=ACC, width=max(2, int(r * 0.3)))


def mark(d, cx, cy, ok):
    """Gezeichnetes Haken-/Kreuz-Symbol."""
    r = 28 * S
    if ok:
        d.line([(cx - r, cy), (cx - r * 0.3, cy + r * 0.7), (cx + r, cy - r * 0.7)], fill=(110, 210, 140),
               width=9 * S, joint="curve")
    else:
        d.line([cx - r, cy - r, cx + r, cy + r], fill=(230, 90, 80), width=9 * S)
        d.line([cx - r, cy + r, cx + r, cy - r], fill=(230, 90, 80), width=9 * S)


def phone(img, cx, cy, moon="blob", moon_d=120, lit=(0.0, 0.0, 1.0), ui=()):
    """Generisches Handy mit Kamera-Sucher. moon: 'blob' (ausgebrannt) oder 'sharp'.
    ui: Teilmenge von {'focus', 'slider', 'lens', 'timer'} - hervorgehobene Bedienelemente."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = cx - PW // 2, cy - PH // 2, cx + PW // 2, cy + PH // 2
    d.rounded_rectangle([x0 - 10 * S, y0 - 10 * S, x1 + 10 * S, y1 + 10 * S], 64 * S, fill=(40, 44, 52))
    d.rounded_rectangle([x0, y0, x1, y1], 56 * S, fill=(4, 6, 10))
    sx, sy = cx, cy - 60 * S
    if moon == "blob":
        blob(img, sx, sy, int(110 * S), int(110 * S), (255, 255, 240), blur=int(40 * S), alpha=200)
        blob(img, sx, sy, int(44 * S), int(44 * S), (255, 255, 255), blur=int(6 * S))
    else:
        planet(img, sx, sy, moon_d, "moon", light=lit, glow=False)
    d = ImageDraw.Draw(img)
    hi = lambda k: ACC if k in ui else (120, 126, 136)
    if "focus" in ui:                                                  # Fokus-/Belichtungsrahmen
        r = 92 * S
        d.rectangle([sx - r, sy - r, sx + r, sy + r], outline=ACC, width=4 * S)
        d.text((sx - r, sy - r - 44 * S), "AE/AF LOCK", font=fmono(24 * S), fill=ACC)
    if "slider" in ui:                                                 # Belichtungsregler
        x = sx + 140 * S
        d.line([x, sy - 110 * S, x, sy + 110 * S], fill=ACC, width=4 * S)
        d.ellipse([x - 18 * S, sy + 40 * S, x + 18 * S, sy + 76 * S], fill=ACC)
        sun_icon(d, x, sy - 150 * S, 14 * S)
    by = y1 - 150 * S                                                  # Zoomstufen-Leiste
    for i, t in enumerate(["0.5", "1x", "3x"]):
        bx = cx + (i - 1) * 90 * S
        on = "lens" in ui and t == "3x"
        d.ellipse([bx - 34 * S, by - 34 * S, bx + 34 * S, by + 34 * S],
                  fill=(70, 56, 30) if on else (30, 34, 40), outline=hi("lens") if on else None, width=3 * S)
        tw = d.textlength(t, font=f(24 * S, bold=True))
        d.text((bx - tw / 2, by - 14 * S), t, font=f(24 * S, bold=True), fill=ACC if on else FG)
    d.ellipse([cx - 46 * S, y1 - 78 * S - 40 * S, cx + 46 * S, y1 - 78 * S + 52 * S], outline=FG, width=5 * S)
    if "timer" in ui:
        tx, ty = x0 + 60 * S, y0 + 62 * S
        d.ellipse([tx - 20 * S, ty - 20 * S, tx + 20 * S, ty + 20 * S], outline=ACC, width=4 * S)
        d.line([tx, ty, tx, ty - 12 * S], fill=ACC, width=4 * S)
        d.line([tx, ty, tx + 9 * S, ty], fill=ACC, width=4 * S)
        d.text((tx + 32 * S, ty - 22 * S), "3s", font=f(34 * S, bold=True), fill=ACC)


def frame_hook():
    img, d = new_frame(1)
    header(d, "PHONE + MOON")
    cy = TOP_SAFE + 450 * S
    phone(img, W // 2 - 230 * S, cy, "blob")
    phone(img, W // 2 + 230 * S, cy, "sharp", moon_d=200, lit=(-0.75, -0.2, 0.55))
    d = ImageDraw.Draw(img)
    mark(d, W // 2 - 230 * S, cy + 440 * S, False)
    mark(d, W // 2 + 230 * S, cy + 440 * S, True)
    y = TOP_SAFE + 960 * S
    ctext(d, "Your Moon photos look", f(70 * S, bold=True), FG, y)
    ctext(d, "like a white blob?", f(70 * S, bold=True), FG, y + 84 * S)
    ctext(d, "4 fixes. No extra gear.", f(52 * S, bold=True), ACC, y + 200 * S)
    footer_handle(d)
    return img


def frame_why():
    img, d = new_frame(2)
    header(d, "WHY IT HAPPENS")
    phone(img, W // 2, GY, "blob")
    d = ImageDraw.Draw(img)
    stat(d, "Your phone exposes for", "the dark sky",
         "But the Moon is lit by full, direct sunlight - so it burns out to white.")
    ruler(d, 1)
    footer_handle(d)
    return img


def frame_step(n, ui, moon, label, big, sub, seed, lit=(-0.75, -0.2, 0.55), moon_d=170):
    img, d = new_frame(seed)
    header(d, f"FIX {n} OF 4")
    phone(img, W // 2, GY, moon, moon_d=moon_d, lit=lit, ui=ui)
    d = ImageDraw.Draw(img)
    stat(d, label, big, sub)
    ruler(d, n + 1)
    footer_handle(d)
    return img


def frame_bonus():
    img, d = new_frame(7)
    header(d, "BONUS · SKIP THE FULL MOON")
    planet(img, W // 2 - 210 * S, GY, 300, "moon", light=(0.0, 0.0, 1.0), glow=False)
    planet(img, W // 2 + 210 * S, GY, 300, "moon", light=(-1.0, 0.0, 0.05), glow=False)
    d = ImageDraw.Draw(img)
    ctext(d, "full: flat", f(32 * S, bold=True), SEC, GY + 190 * S, cx=W // 2 - 210 * S)
    ctext(d, "half: craters pop", f(32 * S, bold=True), ACC, GY + 190 * S, cx=W // 2 + 210 * S)
    stat(d, "Best detail:", "a half Moon",
         "Shadows along the edge make craters stand out. Try a few nights before or after full Moon.")
    ruler(d, 6)
    footer_handle(d)
    return img


def main():
    frames = [
        frame_hook(),
        frame_why(),
        frame_step(1, {"focus"}, "blob", "Tap and hold the Moon", "lock focus",
                   "Your phone stops readjusting to the dark sky around it.", 3),
        frame_step(2, {"focus", "slider"}, "sharp", "Then drag brightness", "way down",
                   "Keep going until the dark patches and craters appear.", 4),
        frame_step(3, {"lens"}, "sharp", "Tap the zoom button,", "don't pinch",
                   "2x, 3x or 5x - whatever lens your phone has. Pinching past it only enlarges blur.", 5,
                   moon_d=250),
        frame_step(4, {"timer"}, "sharp", "Lean it on something +", "3-second timer",
                   "A wall, a car roof, a fence post. No shaky thumb on the shutter.", 6,
                   moon_d=250),
        frame_bonus(),
        frame_save(("Save this", "for the Hunter's Moon", "Oct 26"),
                   sub="Send it to the friend with the blurry Moon pics"),
    ]
    finish(frames, OUT, "w6-moon-phone", cover_idx=0, motion=True)


if __name__ == "__main__":
    main()
