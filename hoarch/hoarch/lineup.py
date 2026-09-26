"""Group photos: every building of a batch in one scene, two rows on one lawn, each labelled
with its name.

    python3 -m hoarch.lineup <batch>... [--samples 40] [--res 2600x1500]
    python3 -m hoarch.lineup --all

Batches: houses1 (1-10), shops (11-20), houses2 (21-30), colonial (31-40). Uses each
building's out/<b>/<b>.npz and palette (the last check/export), so run those first. Writes
out/lineups/<Batch>.png (and the scene files beside it).
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "out"))

# (title, back row, front row, gap between buildings, depth between the rows)
BATCHES = {
    "houses1": ("Houses 1-10", ["harcourt", "ardmore", "carrow", "beaumont", "merritt"],
                ["villa", "fowler", "whitby", "hollis", "delancey"], 45.0, 290.0),
    "shops": ("Main Street, shops 11-20", ["hotel", "bank", "pemberton", "drugstore", "hardware"],
              ["barber", "general", "bakery", "millinery", "jeweler"], 55.0, 230.0),
    "houses2": ("Houses 21-30", ["rosecroft", "larkspur", "camellia", "juniper", "hawthorn"],
                ["marigold", "wisteria", "twins", "primrose", "magnolia"], 45.0, 290.0),
    "colonial": ("The Colonial batch, houses 31-40", ["ellsworth", "oakhurst", "fairhaven", "westbrook", "winthrop"],
                 ["chatham", "vantassel", "whitmore", "pennock", "hathaway"], 45.0, 310.0),
}
VIEW = {"shops": [-10, 27, 50, 0.98, [0, 0, -14]]}       # the shops are small: frame them wider
FILE = {"houses1": "Houses_01-10", "shops": "Shops_11-20", "houses2": "Houses_21-30", "colonial": "Colonial_31-40"}


def names():
    from .guide import BUILDINGS
    return dict(BUILDINGS)


def scene(batch):
    """Merge the batch's render meshes into one npz, with a palette and label points."""
    title, back, front, gap, depth = BATCHES[batch]
    d_out = os.path.join(OUT, "lineups", batch)
    os.makedirs(d_out, exist_ok=True)
    data, pal, labels = {}, {}, {}
    for row, keys in ((0, front), (1, back)):
        if not keys:
            continue
        items = []
        for n in keys:
            d = np.load(os.path.join(OUT, n, f"{n}.npz"))
            p = json.load(open(os.path.join(OUT, n, "palette.json")))["materials"]
            lo, hi = np.array([1e9] * 3), np.array([-1e9] * 3)
            for k in d.files:
                if k.endswith("__v"):
                    v = d[k]
                    lo, hi = np.minimum(lo, v.min(0)), np.maximum(hi, v.max(0))
            items.append((n, d, p, lo, hi))
        total = sum(it[4][0] - it[3][0] for it in items) + gap * (len(items) - 1)
        x = -total / 2 + (total / len(items) / 2 if row == 1 else 0.0)     # the back row staggered into the gaps
        for n, d, p, lo, hi in items:
            off = np.array([x - lo[0], row * depth - (lo[1] + hi[1]) / 2, -lo[2]])
            for k in d.files:
                mat = k.split("__")[0]
                key = mat if mat == "glass" else f"{n}_{mat}"
                data.setdefault(key + "__v" if k.endswith("__v") else key + "__f", []).append(
                    d[k] + off if k.endswith("__v") else d[k])
                if mat != "glass":
                    pal[key] = p.get(mat, ["#ff00ff", 0.5, 0.0])
            cx = x + (hi[0] - lo[0]) / 2
            if row == 0:        # the front row's names on the lawn before them
                labels[n] = [cx, lo[1] + off[1] - 22.0, 0.0]
            else:               # the back row's over their roofs
                labels[n] = [cx, (lo[1] + hi[1]) / 2 + off[1], hi[2] - lo[2] + 14.0]
            x += (hi[0] - lo[0]) + gap
    merged = {}
    for key in sorted({k.rsplit("__", 1)[0] for k in data}):
        vs, fs, o = [], [], 0
        for v, f in zip(data[key + "__v"], data[key + "__f"]):
            vs.append(v)
            fs.append(f + o)
            o += len(v)
        merged[key + "__v"] = np.concatenate(vs).astype(np.float32)
        merged[key + "__f"] = np.concatenate(fs).astype(np.int32)
    np.savez_compressed(os.path.join(d_out, "scene.npz"), **merged)
    json.dump({"materials": pal, "views": {"group": VIEW.get(batch, [-12, 31, 50, 0.72, [0, 0, -20]])}},
              open(os.path.join(d_out, "palette.json"), "w"), indent=1)
    json.dump(labels, open(os.path.join(d_out, "labels.json"), "w"), indent=1)
    return d_out


def label(batch, d_out):
    """Draw each building's name at its projected label point, and the batch's title."""
    from PIL import Image, ImageDraw, ImageFont
    title = BATCHES[batch][0]
    nm = names()
    img = Image.open(os.path.join(d_out, "group.png")).convert("RGBA")
    pix = json.load(open(os.path.join(d_out, "group_labels.json")))
    W, H = img.size
    fs = max(18, W // 72)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", fs)
    tfont = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", int(fs * 1.5))
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dr = ImageDraw.Draw(over)
    placed = []
    front = set(BATCHES[batch][2])
    for k, (x, y, _) in sorted(pix.items(), key=lambda it: it[1][0]):
        text = nm.get(k, k)
        if len(text) > 20:          # a long name on two lines, broken at the space nearest its middle
            sp = [i for i, ch in enumerate(text) if ch == " "]
            i = min(sp, key=lambda j: abs(j - len(text) / 2))
            text = text[:i] + "\n" + text[i + 1:]
        b = dr.multiline_textbbox((0, 0), text, font=font, align="center")
        w, h = b[2] - b[0], b[3] - b[1]
        x0, y0 = int(x - w / 2), int(y - h / 2)
        x0 = max(8, min(W - w - 8, x0))
        pad = fs // 3
        # a tag that would cover one already placed moves away (down in front, up behind) till it is clear
        step = (h + 3 * pad) * (1 if k in front else -1)
        while any(not (x0 + w + pad < a - 4 or x0 - pad > c + 4 or y0 + h + pad * 1.4 < b_ - 4 or y0 - pad > d_ + 4)
                  for a, b_, c, d_ in placed):
            y0 += step
        placed.append((x0 - pad, y0 - pad, x0 + w + pad, y0 + h + pad * 1.4))
        dr.rounded_rectangle([x0 - pad, y0 - pad, x0 + w + pad, y0 + h + pad * 1.4], radius=pad,
                             fill=(255, 255, 255, 215), outline=(60, 60, 60, 255), width=2)
        dr.multiline_text((x0 - b[0], y0 - b[1]), text, font=font, fill=(30, 30, 30, 255), align="center")
    b = dr.textbbox((0, 0), title, font=tfont)
    dr.text(((W - (b[2] - b[0])) // 2, fs // 2), title, font=tfont, fill=(40, 40, 40, 255))
    out = Image.alpha_composite(img, over).convert("RGB")
    path = os.path.join(OUT, "lineups", f"{FILE[batch]}.png")
    out.save(path, optimize=True)
    return path


def run(batch, samples=40, res="2600x1500"):
    d_out = scene(batch)
    cmd = [sys.executable, "-m", "hoarch.render", "--npz", os.path.join(d_out, "scene.npz"), "--palette",
           os.path.join(d_out, "palette.json"), "--views", "group", "--samples", str(samples), "--res", res,
           "--out", d_out, "--labels", os.path.join(d_out, "labels.json")]
    subprocess.run(cmd, check=True, cwd=os.path.join(HERE, ".."), stdout=subprocess.DEVNULL)
    return label(batch, d_out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batches", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--samples", type=int, default=40)
    ap.add_argument("--res", default="2600x1500")
    a = ap.parse_args()
    for b in (list(BATCHES) if a.all else a.batches):
        print(run(b, a.samples, a.res))


if __name__ == "__main__":
    main()
