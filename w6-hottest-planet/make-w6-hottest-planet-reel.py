"""Woche 6, Sonntag - Reel "Mercury is closest to the Sun. It's NOT the hottest planet." (Rate-Format)
8 Frames, 1080x1920, eigene Vektorgrafik, langsamer Zoom je Frame.

Fakten (NASA Science Venus/Mercury/Uranus Facts, NASA Planetary Fact Sheet):
  Merkur: mittl. Sonnenabstand 0,39 AU, Tag bis ~430 C, Nacht bis ~-180 C, praktisch keine
  Atmosphaere. Venus: 0,72 AU (~1,85x weiter), Oberflaeche ~465 C (NASA: 475 C / 900 F),
  Tag und Nacht, Pol und Aequator fast gleich; CO2-Atmosphaere, Bodendruck ~92 bar
  (~90x Erde) -> galoppierender Treibhauseffekt. Blei schmilzt bei 327 C.
  Kaelteste gemessene Atmosphaerentemperatur: Uranus ~-224 C (NASA), obwohl Neptun weiter
  draussen liegt (Uranus gibt kaum innere Waerme ab).

Hook-Varianten (Formatvorlage Woche 6):
  1 "Mercury is closest to the Sun. It's NOT the hottest planet." (gewaehlt)
  2 "Guess the hottest planet. Hint: not Mercury."   3 "Hot enough to melt lead - and it's not Mercury"
  4 "Which planet would cook you fastest?"   5 "The hottest planet isn't the closest one"

    python make-w6-hottest-planet-reel.py  ->  w6-hottest-planet-01..08.png, -cover.png, .mp4
"""

import sys
from pathlib import Path

from PIL import ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, fmono
from bodies import planet, star
from reelkit import (W, H, M, TOP_SAFE, new_frame, header, footer_handle, ruler, ctext,
                     ctext_block, frame_save, blob, finish)

OUT = Path(__file__).resolve().parent
GY = TOP_SAFE + 400 * S
TY = TOP_SAFE + 800 * S
HOT = (255, 120, 70)
COLD = (130, 180, 255)


def stat(d, label, big, sub, big_col=ACC):
    ctext(d, label, f(46 * S, bold=True), FG, TY)
    ctext(d, big, f(92 * S, bold=True), big_col, TY + 66 * S)
    ctext_block(d, sub, f(34 * S), SEC, TY + 196 * S, 46 * S, W - 2 * M - 40 * S)


def lineup(img, y, highlight=None):
    """Sonne links angeschnitten, Merkur + Venus (+ Erde) in Abstandsreihenfolge."""
    star(img, -260 * S, y, 900, spots=False, corona=0.8)
    pos = {"mercury": (W // 2 - 120 * S, 120), "venus": (W // 2 + 140 * S, 220), "earth": (W - M - 40 * S, 230)}
    for k, (x, dp) in pos.items():
        planet(img, x, y, dp, k, light=(-1.0, 0.0, 0.35))
    d = ImageDraw.Draw(img)
    for k, (x, dp) in pos.items():
        col = ACC if k == highlight else SEC
        ctext(d, k.capitalize(), f(32 * S, bold=True), col, y + dp * S // 2 + 26 * S, cx=x)
    return pos


def frame_hook():
    img, d = new_frame(1)
    header(d, "GUESS FIRST")
    lineup(img, TOP_SAFE + 420 * S)
    d = ImageDraw.Draw(img)
    y = TOP_SAFE + 790 * S
    ctext(d, "Mercury is closest", f(76 * S, bold=True), FG, y)
    ctext(d, "to the Sun.", f(76 * S, bold=True), FG, y + 90 * S)
    ctext(d, "It's NOT the hottest planet.", f(54 * S, bold=True), ACC, y + 206 * S)
    ctext(d, "which one is? comment ↓", f(34 * S), SEC, y + 310 * S)
    footer_handle(d)
    return img


def frame_merc_day():
    img, d = new_frame(2)
    header(d, "MERCURY · DAYTIME")
    planet(img, W // 2, GY, 380, "mercury", light=(-0.8, -0.2, 0.55))
    blob(img, W // 2 - 260 * S, GY, 120 * S, 300 * S, (255, 200, 120), blur=90 * S, alpha=60)
    d = ImageDraw.Draw(img)
    stat(d, "In sunlight it hits", "430 °C",
         "Hot enough to melt tin and lead.", big_col=HOT)
    ruler(d, 1)
    footer_handle(d)
    return img


def frame_merc_night():
    img, d = new_frame(3)
    header(d, "MERCURY · NIGHTTIME")
    planet(img, W // 2, GY, 380, "mercury", light=(1.0, 0.0, -0.75))
    d = ImageDraw.Draw(img)
    stat(d, "Same planet, at night:", "-180 °C",
         "No real atmosphere - the heat escapes straight into space.", big_col=COLD)
    ruler(d, 2)
    footer_handle(d)
    return img


def frame_choice():
    img, d = new_frame(4)
    header(d, "LAST CHANCE TO GUESS")
    y = TOP_SAFE + 170 * S
    for letter, val in [("A", "Jupiter"), ("B", "Venus"), ("C", "Mars")]:
        d.rounded_rectangle([M + 40 * S, y, W - M - 40 * S, y + 150 * S], 30 * S, outline=HAIR, width=4 * S)
        d.text((M + 90 * S, y + 36 * S), letter, font=f(70 * S, bold=True), fill=ACC)
        d.text((M + 220 * S, y + 40 * S), val, font=f(64 * S, bold=True), fill=FG)
        y += 180 * S
    stat(d, "So which is hottest?", "A, B or C",
         "Comment your pick before the answer.")
    ruler(d, 3)
    footer_handle(d)
    return img


def frame_reveal():
    img, d = new_frame(5)
    header(d, "ANSWER")
    planet(img, W // 2, GY, 440, "venus", light=(-0.7, -0.25, 0.6))
    blob(img, W // 2, GY, 300 * S, 300 * S, HOT, blur=90 * S, alpha=50)
    d = ImageDraw.Draw(img)
    stat(d, "It's B, Venus:", "465 °C",
         "Day and night, pole to equator. Almost twice as far from the Sun as Mercury - and hotter.",
         big_col=HOT)
    ruler(d, 4)
    footer_handle(d)
    return img


def frame_why():
    img, d = new_frame(6)
    header(d, "WHY")
    cx, cy = W // 2, GY
    planet(img, cx, cy, 360, "venus", light=(-0.7, -0.25, 0.6))
    d = ImageDraw.Draw(img)
    for i in range(5):                                                 # Waerme kommt rein, nicht raus
        x = cx - 160 * S + i * 80 * S
        d.line([x, cy - 360 * S, x, cy - 220 * S], fill=(255, 214, 140), width=5 * S)
        d.line([x - 14 * S, cy - 236 * S, x, cy - 216 * S, x + 14 * S, cy - 236 * S], fill=(255, 214, 140),
               width=5 * S)
    d.arc([cx - 230 * S, cy - 230 * S, cx + 230 * S, cy + 230 * S], 200, 340, fill=HOT, width=8 * S)
    stat(d, "A thick CO2 blanket", "traps the heat",
         "Its air is 90x denser than Earth's. Sunlight gets in - the heat can't get out.")
    ruler(d, 5)
    footer_handle(d)
    return img


def frame_twist():
    img, d = new_frame(7)
    header(d, "BONUS TWIST")
    planet(img, W // 2 - 200 * S, GY, 300, "uranus", light=(-0.7, -0.2, 0.6))
    planet(img, W // 2 + 210 * S, GY, 290, "neptune", light=(-0.7, -0.2, 0.6))
    d = ImageDraw.Draw(img)
    ctext(d, "Uranus", f(32 * S, bold=True), COLD, GY + 190 * S, cx=W // 2 - 200 * S)
    ctext(d, "Neptune (farther out)", f(32 * S, bold=True), SEC, GY + 190 * S, cx=W // 2 + 210 * S)
    stat(d, "The coldest isn't the farthest:", "Uranus, -224 °C",
         "It gives off almost no inner heat - so it's colder than Neptune.", big_col=COLD)
    ruler(d, 6)
    footer_handle(d)
    return img


def main():
    frames = [
        frame_hook(),
        frame_merc_day(),
        frame_merc_night(),
        frame_choice(),
        frame_reveal(),
        frame_why(),
        frame_twist(),
        frame_save(("Send this", "to whoever", "says 'Mercury'"), sub="Save it for your next quiz night"),
    ]
    finish(frames, OUT, "w6-hottest-planet", cover_idx=0, motion=True)


if __name__ == "__main__":
    main()
