"""Pack the concept model into a compact gzip'd binary for the web viewer.

Layout (little endian), after gunzip:
  u32 header_len, header JSON (utf-8), then per material in header order:
  int16[n_vert*3] quantised positions, uint32[n_tri*3] indices.
Positions are quantised to the global bounding box (z-up, millimetres).
"""
import base64
import gzip
import json
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from palette import PALETTE  # noqa: E402


def weld(v, f, tol=1e-3):
    q = np.round(v / tol).astype(np.int64)
    _, idx, inv = np.unique(q, axis=0, return_index=True, return_inverse=True)
    return v[idx], inv.reshape(-1)[f]


def main(src, dst):
    d = np.load(src)
    names = sorted({k.split("__")[0] for k in d.files if k.split("__")[0] != "shadow"})
    allv = np.concatenate([d[n + "__v"] for n in names])
    lo, hi = allv.min(0), allv.max(0)
    scale = (hi - lo).max() / 65000.0
    blobs = []
    mats = []
    for n in names:
        v, f = weld(d[n + "__v"].astype(np.float64), d[n + "__f"])
        q = np.round((v - lo) / scale - 32500).astype(np.int16)
        blobs.append(q.tobytes())
        blobs.append(f.astype(np.uint32).tobytes())
        hexcol, rough, metal = PALETTE.get(n, ("#ff00ff", 0.5, 0.0))
        mats.append(dict(name=n, nv=int(len(v)), nt=int(len(f)), color=hexcol, rough=rough, metal=metal))
    header = json.dumps(dict(lo=lo.tolist(), scale=float(scale), offset=-32500, materials=mats)).encode()
    pad = (-(4 + len(header))) % 4
    header += b" " * pad
    raw = struct.pack("<I", len(header)) + header + b"".join(blobs)
    with gzip.open(dst, "wb", compresslevel=9) as fh:
        fh.write(raw)
    with open(os.path.splitext(dst)[0] + ".txt", "w") as fh:   # served form for the review page
        fh.write(base64.b64encode(open(dst, "rb").read()).decode())
    print("materials", len(mats), "tris", sum(m["nt"] for m in mats), "raw MB", round(len(raw) / 1e6, 2),
          "gz MB", round(os.path.getsize(dst) / 1e6, 2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "out", "house_parts.npz"),
         sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "out", "house.bin.gz"))
