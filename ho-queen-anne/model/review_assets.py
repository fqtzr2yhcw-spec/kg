"""Copy renders into the review page as web-sized JPEGs plus thumbnails."""
import glob
import os

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "renders")
DST = os.path.join(HERE, "..", "review", "img")

os.makedirs(DST, exist_ok=True)
for path in sorted(glob.glob(os.path.join(SRC, "*.png"))):
    name = os.path.splitext(os.path.basename(path))[0]
    im = Image.open(path).convert("RGB")
    im.save(os.path.join(DST, name + ".jpg"), quality=86, optimize=True, progressive=True)
    th = im.copy()
    th.thumbnail((320, 220))
    th.save(os.path.join(DST, name + "_t.jpg"), quality=80, optimize=True)
    print(name, os.path.getsize(os.path.join(DST, name + ".jpg")) // 1024, "KB")
