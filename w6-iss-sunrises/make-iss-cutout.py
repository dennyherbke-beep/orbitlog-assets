"""Stellt die ISS aus dem NASA-Foto iss056e201248 frei (images.nasa.gov, ~medium.jpg) -> textures/iss-nasa-iss056e201248.png.

    python make-iss-cutout.py iss056e201248~medium.jpg ../textures/iss-nasa-iss056e201248.png
"""
import sys

import numpy as np
from PIL import Image, ImageFilter

src, dst = sys.argv[1], sys.argv[2]
im = Image.open(src).convert("RGB").crop((120, 50, 1170, 615))      # Station ohne Erdhorizont
a = np.asarray(im, np.float32)
lum = a.max(axis=2)
row_sky = np.percentile(lum, 20, axis=1, keepdims=True)              # Himmelshelligkeit je Zeile (Horizontaufhellung)
alpha = np.clip((lum - row_sky - 22) / 26, 0, 1)                    # dunkles All -> transparent
solid = Image.fromarray(((lum - row_sky > 20) * 255).astype(np.uint8))   # alles, was nicht Himmel ist
solid = solid.filter(ImageFilter.MedianFilter(5)).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.MinFilter(9))   # Paneel-Innenflaechen schliessen
alpha = np.maximum(alpha, np.asarray(solid, np.float32) / 255)
mask = Image.fromarray((alpha * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(3)).filter(ImageFilter.GaussianBlur(0.8))
out = im.convert("RGBA")
out.putalpha(mask)
out = out.crop(out.getbbox())
out.save(dst)
print(dst, out.size)
