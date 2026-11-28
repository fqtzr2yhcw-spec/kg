"""Glue audit: how much of each part's surface lies against another part (or on the layout), so
no small piece hangs on a tiny glue spot (the owner's rule: super glue leaves a crust).

Each part's surface is sampled; a sample within TOL of another part counts as glue face, one at
the layout's level (z = 0) as standing on the layout. A part is SMALL when its glue face plus
layout face is under max(MIN_AREA, FRAC * volume^(2/3)): a crumb needs a few mm2, a big part
proportionally more.

usage: python3 tools/glue_audit.py <building> [...]
"""
import sys

import numpy as np
import trimesh

from _common import building

TOL = 0.2             # mm: a gap CA glue fills (the inserts' plugs sit with a little clearance)
MIN_AREA = 4.0        # mm2
FRAC = 0.1
DENSITY = 3.0         # samples per mm2 (capped)
MAX_SAMPLES = 30000   # a big part's glue face is never the problem; this keeps the roofs quick
CHUNK = 1500          # points per distance query (a big roof mesh runs out of memory on more)


def _mesh(m):
    mm = m.to_mesh()
    v = np.asarray(mm.vert_properties)[:, :3]
    return trimesh.Trimesh(vertices=v, faces=np.asarray(mm.tri_verts), process=False)


def audit(key):
    kit = building(key).build()
    parts = [p for p in kit.parts if not p.solid.is_empty()]
    meshes = [_mesh(p.solid) for p in parts]
    boxes = [np.array(p.solid.bounding_box()).reshape(2, 3) for p in parts]
    rng = np.random.default_rng(7)
    rows = []
    for i, (p, ma) in enumerate(zip(parts, meshes)):
        area = float(ma.area)
        n = int(np.clip(area * DENSITY, 1500, MAX_SAMPLES))
        pts, _ = trimesh.sample.sample_surface(ma, n, seed=int(rng.integers(1 << 30)))
        hit = np.zeros(len(pts), bool)
        per = []
        lo, hi = boxes[i][0] - TOL, boxes[i][1] + TOL
        for j, mb in enumerate(meshes):
            if j == i:
                continue
            bl, bh = boxes[j][0] - TOL, boxes[j][1] + TOL
            if np.any(bl > hi) or np.any(bh < lo):
                continue
            near = np.all((pts >= bl) & (pts <= bh), axis=1)
            if not near.any():
                continue
            q = pts[near]
            d = np.concatenate([trimesh.proximity.closest_point(mb, q[k:k + CHUNK])[1] for k in range(0, len(q), CHUNK)])
            c = np.zeros(len(pts), bool)
            c[np.flatnonzero(near)[d < TOL]] = True
            if c.any():
                per.append((parts[j].name, round(c.sum() / n * area, 1)))
                hit |= c
        on_layout = pts[:, 2] <= 0.05
        glue = hit.sum() / n * area
        layout = (on_layout & ~hit).sum() / n * area
        vol = p.solid.volume()
        need = max(MIN_AREA, FRAC * vol ** (2.0 / 3.0))
        small = glue + layout < need
        per.sort(key=lambda t: -t[1])
        rows.append((p.name, vol, glue, layout, per, small))
        flag = "  <-- SMALL" if small else ""
        print(f"{p.name:30s} vol {vol:9.1f}  glue {glue:8.1f} mm2  layout {layout:7.1f} mm2  {per[:4]}{flag}", flush=True)
    bad = [r for r in rows if r[5]]
    print(f"== {key}: {len(rows)} parts, {len(bad)} small glue faces")
    return rows


if __name__ == "__main__":
    for key in sys.argv[1:]:
        audit(key)
