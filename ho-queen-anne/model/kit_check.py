"""Fit checks for the kit: part-to-part interference, bed size, part stats."""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kit

BED = 250.0          # usable P1S/P2S bed (256 mm minus margin)
MAX_H = 250.0


def bbox(m):
    b = m.bounding_box()
    return np.array(b[:3]), np.array(b[3:])


def interference(parts, tol=0.05):
    boxes = [bbox(p.solid) for p in parts]
    hits = []
    n = len(parts)
    for i in range(n):
        for j in range(i + 1, n):
            lo = np.maximum(boxes[i][0], boxes[j][0])
            hi = np.minimum(boxes[i][1], boxes[j][1])
            if np.any(hi - lo <= 0.01):
                continue
            v = (parts[i].solid ^ parts[j].solid).volume()
            if v > tol:
                hits.append((v, parts[i].name, parts[j].name))
    return sorted(hits, reverse=True)


def bed_check(parts):
    bad = []
    for p in parts:
        lo, hi = bbox(p.printed())
        ext = hi - lo
        if max(ext[0], ext[1]) > BED or ext[2] > MAX_H:
            bad.append((p.name, np.round(ext, 1)))
    return bad


if __name__ == "__main__":
    t = time.time()
    kit.build()
    print("built", round(time.time() - t, 1), "s")
    t = time.time()
    hits = interference(kit.PARTS)
    print("interference check", round(time.time() - t, 1), "s")
    for v, a, b in hits:
        print(f"  {v:8.2f} mm3  {a}  x  {b}")
    print("interfering pairs:", len(hits))
    for name, ext in bed_check(kit.PARTS):
        print("  TOO BIG:", name, ext)
