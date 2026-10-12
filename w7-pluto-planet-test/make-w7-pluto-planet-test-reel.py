"""Woche 7 - Reel "Why PLUTO isn't a planet - the 3-rule test" (Typ f Physik-Konzept / Kommentar-
Thema aus w6-sun-from-planets: 5 von 7 Kommentaren "Pluto is not a planet"). Feste Kopfzeile, eine
durchgehende Tabellen-Animation: 5 Himmelskoerper, 3 Regeln, Haken/Kreuze erscheinen Regel fuer Regel,
Urteil am Ende. 14 s.

Fakten (IAU-Resolution B5, 24.08.2006; NASA Science "Pluto", "Ceres", "Eris"):
  Planet = (1) umkreist die Sonne, (2) genug Masse fuer annaehernd runde Form (hydrostatisches
  Gleichgewicht), (3) hat die Umgebung seiner Bahn freigeraeumt. Erfuellt nur (1)+(2) -> Zwergplanet.
  Pluto, Eris, Ceres: (1) ja (2) ja (3) nein (Kuiper-Guertel bzw. Asteroidenguertel). Mond: umkreist
  die Erde, nicht direkt die Sonne -> (1) nein; rund ja; Regel (3) nicht anwendbar (Strich). Erde: alle drei ja.
  Ausloeser: Entdeckung von Eris 2005 (etwa so gross wie Pluto, ~27 % massereicher).

Hook-Varianten:
  1 "Why PLUTO isn't a planet - the 3-rule test" (gewaehlt)   2 "Pluto passed 2 of 3 tests"
  3 "Would Earth still be a planet under the new rules?"   4 "The rule that kicked Pluto out"
  5 "Is Pluto a planet? Vote before the answer"

    python make-w7-pluto-planet-test-reel.py  ->  w7-pluto-planet-test.mp4, -cover.png
"""

import math
import os
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brandkit import S, FG, SEC, ACC, HAIR, f, downscale
from bodies import planet
from reelkit import W as WS, new_frame, header_band, cinematic

OUT = Path(__file__).resolve().parent
W, H, FPS, DUR = 1080, 1920, 30, 14.0
YES, NO = (110, 210, 130), (255, 96, 86)
RULES = ["Orbits\nthe Sun", "Round\nshape", "Cleared\nits orbit"]
# Name, Textur, Regeln (1/0), Urteil
ROWS = [("Earth", "earth", (1, 1, 1), "PLANET"), ("Moon", "moon", (0, 1, None), "MOON"),
        ("Ceres", "mercury", (1, 1, 0), "DWARF"), ("Eris", "moon", (1, 1, 0), "DWARF"),
        ("Pluto", "pluto", (1, 1, 0), "DWARF")]
TOP, ROW_H = 770, 124
COLS = [430, 600, 770, 940]                       # Mitte Regel 1..3, Urteil
T_RULE = [2.0, 4.2, 6.4]                          # Start je Regel-Spalte
T_VERDICT = 9.6


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def background():
    img, _ = new_frame(47)
    header_band(img, ["Why PLUTO isn't a planet", "- the 3-rule test"], "PLUTO")
    d = ImageDraw.Draw(img)
    for i, (name, kind, _, _) in enumerate(ROWS):
        cy = TOP + i * ROW_H + ROW_H // 2
        planet(img, 110 * S, cy * S, 76 if name != "Earth" else 84, kind, light=(-0.6, -0.4, 0.7))
        d = ImageDraw.Draw(img)
        d.text((165 * S, (cy - 20) * S), name, font=f(38 * S, bold=True), fill=ACC if name == "Pluto" else FG)
        if i:
            d.line([60 * S, (TOP + i * ROW_H) * S, 1020 * S, (TOP + i * ROW_H) * S], fill=HAIR, width=2 * S)
    y = TOP + len(ROWS) * ROW_H + 40
    note = "IAU rules, 2006 · triggered by the discovery of Eris"
    d.text(((WS - d.textlength(note, font=f(26 * S))) / 2, y * S), note, font=f(26 * S), fill=SEC)
    cta = "Planet or not? Vote in the comments"
    d.text(((WS - d.textlength(cta, font=f(36 * S, bold=True))) / 2, (y + 50) * S), cta,
           font=f(36 * S, bold=True), fill=FG)
    return downscale(img, W, H)


def mark(d, cx, cy, ok, k, r=26):
    """Haken oder Kreuz, k = 0..1 Einblendung (waechst)."""
    if k <= 0:
        return
    if ok is None:                                                         # Regel nicht anwendbar
        d.line([cx - r * 0.5, cy, cx + r * 0.5, cy], fill=SEC + (int(255 * k),), width=7)
        return
    col = YES if ok else NO
    s = r * (0.6 + 0.4 * k)
    a = int(255 * k)
    d.ellipse([cx - s - 8, cy - s - 8, cx + s + 8, cy + s + 8], outline=col + (a,), width=4)
    if ok:
        d.line([cx - s * 0.55, cy, cx - s * 0.1, cy + s * 0.45, cx + s * 0.6, cy - s * 0.5], fill=col + (a,), width=7,
               joint="curve")
    else:
        d.line([cx - s * 0.45, cy - s * 0.45, cx + s * 0.45, cy + s * 0.45], fill=col + (a,), width=7)
        d.line([cx - s * 0.45, cy + s * 0.45, cx + s * 0.45, cy - s * 0.45], fill=col + (a,), width=7)


def frame(bg, t):
    im = bg.copy().convert("RGBA")
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    for c, txt in enumerate(RULES + ["Verdict"]):                          # Spaltenkoepfe
        start = T_RULE[c] - 0.4 if c < 3 else T_VERDICT - 0.4
        a = ease((t - start) / 0.4) if c < 3 else ease((t - start) / 0.4)
        a = max(a, 0.35)
        fo = f(28, bold=True)
        col = (ACC if c < 3 and T_RULE[c] <= t < T_RULE[c] + 2.2 else FG) if c < 3 else ACC
        for n, ln in enumerate(txt.split("\n")):
            tw = d.textlength(ln, font=fo)
            d.text((COLS[c] - tw / 2, TOP - 92 + n * 34), ln, font=fo, fill=col + (int(255 * a),))
    for c in range(3):                                                     # Haken je Regel, zeilenweise
        if T_RULE[c] <= t < T_RULE[c] + 2.2:
            d.rectangle([COLS[c] - 78, TOP - 100, COLS[c] + 78, TOP + len(ROWS) * ROW_H], outline=(255, 180, 84, 90),
                        width=3)
        for i, (_, _, rules, _) in enumerate(ROWS):
            k = ease((t - T_RULE[c] - 0.3 * i) / 0.35)
            mark(d, COLS[c], TOP + i * ROW_H + ROW_H // 2, rules[c], k)
    for i, (name, _, rules, verdict) in enumerate(ROWS):                   # Urteil
        k = ease((t - T_VERDICT - 0.35 * i) / 0.4)
        if k > 0:
            col = YES if verdict == "PLANET" else ACC if verdict == "DWARF" else SEC
            fo = f(30, bold=True)
            txt = verdict
            tw = d.textlength(txt, font=fo)
            d.text((COLS[3] - tw / 2, TOP + i * ROW_H + ROW_H // 2 - 18), txt, font=fo, fill=col + (int(255 * k),))
    if t > 7.6:                                                            # Erklaerung Regel 3
        k = ease((t - 7.6) / 0.5) * (1 - ease((t - T_VERDICT + 0.2) / 0.4))
        if k > 0:
            fo = f(30, bold=True)
            for n, ln in enumerate(["Pluto shares its orbit with thousands", "of icy Kuiper Belt objects"]):
                tw = d.textlength(ln, font=fo)
                d.text(((W - tw) / 2, TOP - 205 + n * 40), ln, font=fo, fill=(255, 180, 84, int(255 * k)),
                       stroke_width=3, stroke_fill=(8, 10, 14, int(255 * k)))
    if t > T_VERDICT + 2.0:                                                # Schlusszeile
        k = ease((t - T_VERDICT - 2.0) / 0.5)
        fo = f(34, bold=True)
        txt = "Pluto passed 2 of 3 - so it's a dwarf planet"
        tw = d.textlength(txt, font=fo)
        d.text(((W - tw) / 2, TOP - 190), txt, font=fo, fill=(242, 244, 248, int(255 * k)),
               stroke_width=3, stroke_fill=(8, 10, 14, int(255 * k)))
    im.alpha_composite(ov)
    return im.convert("RGB")


def main():
    bg = background()
    ff = imageio_ffmpeg.get_ffmpeg_exe()
    out = OUT / "w7-pluto-planet-test.mp4"
    n = int(DUR * FPS)
    proc = subprocess.Popen([
        ff, "-y", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
        "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-maxrate", "12M", "-bufsize", "24M", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-t", f"{DUR:.2f}", "-movflags", "+faststart", str(out)],
        stdin=subprocess.PIPE)
    for i in range(n):
        proc.stdin.write(cinematic(frame(bg, i / FPS), i).tobytes())
    proc.stdin.close()
    proc.wait()
    cinematic(frame(bg, 8.4), 0).save(OUT / "w7-pluto-planet-test-cover.png")
    cinematic(frame(bg, DUR - 0.1), 0).save(Path(os.environ.get("CHECK_DIR", OUT)) / "_check-pluto-end.png")
    print(f"saved {out.name} ({DUR:.1f} s, {n} frames) + cover")


if __name__ == "__main__":
    main()
