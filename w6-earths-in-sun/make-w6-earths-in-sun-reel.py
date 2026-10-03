"""Woche 6, Dienstag - Reel "How many Earths fit inside the Sun?" (Rate-Format, ab Woche 6).
8 Frames, 1080x1920, eigene Vektorgrafik, langsamer Zoom je Frame (finish(..., motion=True)).

Fakten (NASA Sun Facts / Planetary Fact Sheet):
  Sonnendurchmesser 1.391.000 km, Erde 12.742 km -> ~109x. Volumenverhaeltnis = 109^3
  = ~1,3 Mio. (NASA: "about 1.3 million Earths"). Dicht gepackte Kugeln fuellen nur ~74 %
  -> ~960.000 ganze Erden (first_comment). Sonne = 99,86 % der Masse des Sonnensystems.
  Beteigeuze: Radius grob 700-1.000 Sonnenradien (~3-4,5 AU), an Stelle der Sonne reichte
  sie ueber die Mars- (1,52 AU) bis in Richtung Jupiterbahn - im Reel nur "past Mars".

Hook-Varianten (Formatvorlage Woche 6, Punkt 1):
  1 "Guess how many Earths fit inside the Sun"   2 "Most people guess 100. It's not even close." (gewaehlt)
  3 "The Sun isn't 100x bigger than Earth"       4 "Fill the Sun with Earths. How many?"
  5 "1.3 million of these fit in there"

    python make-w6-earths-in-sun-reel.py  ->  w6-earths-in-sun-01..08.png, -cover.png, .mp4
"""

import sys
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono
from bodies import planet, star
from reelkit import (W, H, M, TOP_SAFE, new_frame, header, footer_handle, ruler, ctext,
                     ctext_block, frame_save, finish)

OUT = Path(__file__).resolve().parent
GY = TOP_SAFE + 400 * S
TY = TOP_SAFE + 800 * S


def stat(d, label, big, sub, big_col=ACC):
    ctext(d, label, f(46 * S, bold=True), FG, TY)
    ctext(d, big, f(92 * S, bold=True), big_col, TY + 66 * S)
    ctext_block(d, sub, f(34 * S), SEC, TY + 196 * S, 46 * S, W - 2 * M - 40 * S)


def frame_hook():
    img, d = new_frame(1)
    header(d, "GUESS FIRST")
    star(img, W // 2, TOP_SAFE + 430 * S, 560)
    planet(img, W // 2 + 330 * S, TOP_SAFE + 120 * S, 26, "earth")
    d = ImageDraw.Draw(img)
    d.text((W // 2 + 360 * S, TOP_SAFE + 100 * S), "Earth", font=f(28 * S, bold=True), fill=SEC)
    y = TOP_SAFE + 820 * S
    ctext(d, "How many Earths fit", f(74 * S, bold=True), FG, y)
    ctext(d, "inside the Sun?", f(74 * S, bold=True), FG, y + 88 * S)
    ctext(d, "Most people guess 100.", f(52 * S, bold=True), ACC, y + 220 * S)
    ctext(d, "It's not even close.", f(52 * S, bold=True), ACC, y + 286 * S)
    ctext(d, "comment your guess ↓", f(34 * S), SEC, y + 400 * S)
    footer_handle(d)
    return img


def frame_across():
    img, d = new_frame(2)
    header(d, "STEP 1 · LINE THEM UP")
    star(img, W // 2, GY, 640, spots=False, corona=0.6)
    n, x0, x1 = 22, W // 2 - 300 * S, W // 2 + 300 * S          # symbolisch 22 statt 109 Kugeln
    for i in range(n):
        planet(img, int(x0 + (x1 - x0) * i / (n - 1)), GY, 24, "earth", glow=False)
    d = ImageDraw.Draw(img)
    stat(d, "Across the Sun:", "109 Earths",
         "Line Earths up edge to edge - it takes 109 to cross the Sun once.")
    ruler(d, 1)
    footer_handle(d)
    return img


def frame_cube():
    img, d = new_frame(3)
    header(d, "STEP 2 · IT'S A BALL, NOT A LINE")
    cx, cy = W // 2, GY
    for dx in (-270, 0, 270):
        ctext(d, "109", f(110 * S, bold=True), ACC, cy - 70 * S, cx=cx + dx * S)
    for dx in (-135, 135):
        ctext(d, "×", f(80 * S, bold=True), SEC, cy - 50 * S, cx=cx + dx * S)
    ctext(d, "wide · tall · deep", fmono(30 * S), SEC, cy + 80 * S)
    stat(d, "Volume grows with size", "cubed",
         "Something 109 times wider holds 109 × 109 × 109 times more.")
    ruler(d, 2)
    footer_handle(d)
    return img


def frame_choice():
    img, d = new_frame(4)
    header(d, "LAST CHANCE TO GUESS")
    y = TOP_SAFE + 170 * S
    for letter, val in [("A", "13,000"), ("B", "130,000"), ("C", "1.3 million")]:
        d.rounded_rectangle([M + 40 * S, y, W - M - 40 * S, y + 150 * S], 30 * S, outline=HAIR, width=4 * S)
        d.text((M + 90 * S, y + 36 * S), letter, font=f(70 * S, bold=True), fill=ACC)
        d.text((M + 220 * S, y + 40 * S), val, font=f(64 * S, bold=True), fill=FG)
        y += 180 * S
    stat(d, "A, B or C?", "comment it",
         "Answer in 2 seconds.")
    ruler(d, 3)
    footer_handle(d)
    return img


def frame_reveal():
    img, d = new_frame(5)
    header(d, "ANSWER")
    star(img, W // 2, GY, 600)
    d = ImageDraw.Draw(img)
    stat(d, "It's C:", "1.3 million",
         "About 1.3 million Earths would fit inside the Sun. (Squished together - the fine print is in the comments.)")
    ruler(d, 4)
    footer_handle(d)
    return img


def frame_mass():
    img, d = new_frame(6)
    header(d, "AND THE WEIGHT")
    star(img, W // 2 - 140 * S, GY, 420, spots=False)
    xs = [W // 2 + 140 * S, W // 2 + 210 * S, W // 2 + 300 * S, W // 2 + 385 * S]
    for x, kind, dp in zip(xs, ["earth", "neptune", "jupiter", "saturn"], [16, 26, 50, 42]):
        planet(img, x, GY, dp, kind, glow=False)
    d = ImageDraw.Draw(img)
    stat(d, "The Sun holds", "99.8 %",
         "of all the mass in the solar system. Every planet, moon and asteroid together: the rest.")
    ruler(d, 5)
    footer_handle(d)
    return img


def frame_twist():
    img, d = new_frame(7)
    bg = img.copy()
    star(img, W // 2, GY + 1150 * S, 2400, kind="red_dwarf", spots=False, corona=0.5)
    cut, fade = TY - 260 * S, 200 * S                   # Riesenstern weich vor dem Textblock ausblenden
    m = Image.linear_gradient("L").resize((W, fade))
    mask = Image.new("L", (W, H), 0)
    mask.paste(m, (0, cut))
    mask.paste(255, (0, cut + fade, W, H))
    img.paste(bg, (0, 0), mask)
    d = ImageDraw.Draw(img)
    header(d, "PLOT TWIST")
    star(img, W // 2, GY - 200 * S, 14, spots=False, corona=0.8)
    d = ImageDraw.Draw(img)
    ctext(d, "the Sun", f(30 * S, bold=True), SEC, GY - 160 * S)
    ctext(d, "Betelgeuse (just its edge)", f(30 * S, bold=True), FG, GY + 130 * S)
    stat(d, "And the Sun is just", "a medium star",
         "Put the red giant Betelgeuse in its place and it would swallow Earth - and reach past Mars.")
    ruler(d, 6)
    footer_handle(d)
    return img


def main():
    frames = [
        frame_hook(),
        frame_across(),
        frame_cube(),
        frame_choice(),
        frame_reveal(),
        frame_mass(),
        frame_twist(),
        frame_save(("Send this", "to someone", "who guessed 100"), sub="Save it for your next quiz night"),
    ]
    finish(frames, OUT, "w6-earths-in-sun", cover_idx=0, motion=True)


if __name__ == "__main__":
    main()
