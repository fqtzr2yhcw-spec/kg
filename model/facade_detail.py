#!/usr/bin/env python3
"""
Empire State Building - EXTREME-detail facade panel (parametric).

A section of the tower elevation modelled at large scale, where the real
detail becomes printable geometry:
  * individual windows - recessed opening, jambs, projecting sill, lintel/head,
    raised frame, central mullion and divided lights (muntins)
  * Art Deco spandrel panels below each window, with vertical flutes
  * coursed limestone - horizontal mortar reveals + staggered vertical joints
    (running bond) on the piers

Prints flat (back face down, detail up) - all relief faces up, no supports.
Tile the panel to cover a full elevation, or raise N_BAYS/N_FLOORS.

Scale here is the PANEL scale (default ~1:80), independent of the whole-building
model in empire_state_building.py.
"""
import os
import numpy as np
import trimesh

MM_PER_FT = 3.2                       # panel scale (~1:95).  1ft -> 3.2mm
N_BAYS    = 3
N_FLOORS  = 4
OUT       = os.path.dirname(os.path.abspath(__file__))

# facade dimensions (feet)
BAY   = 16.0
FLOOR = 12.25
PIER  = 6.0                            # limestone pier between bays
T     = 9.0                            # panel thickness
WO    = BAY - PIER                     # window opening width (10)
HO    = 8.0                            # window opening height
REC   = 3.0                            # window recess depth
SPAND = 3.0                            # spandrel zone height (below window)
HEAD  = FLOOR - HO - SPAND             # head zone (above window) = 1.25
COURSE = 2.5                           # masonry course height
GJD, GJW = 0.22, 0.35                  # mortar joint depth / width (ft)

W = N_BAYS * BAY
H = N_FLOORS * FLOOR

def blk(x0, x1, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=(x1-x0, y1-y0, z1-z0))
    b.apply_translation(((x0+x1)/2, (y0+y1)/2, (z0+z1)/2)); return b

def union(ms): return ms[0] if len(ms) == 1 else trimesh.boolean.union(ms)
def diff(a, cs): return a if not cs else trimesh.boolean.difference([a, union(cs)])

def build():
    subs, adds = [], []

    # ---- masonry coursing on the whole stone face -------------------------
    y = COURSE
    while y < H - 0.1:                                   # horizontal mortar reveals
        subs.append(blk(0, W, y-GJW/2, y+GJW/2, T-GJD, T+1)); y += COURSE
    # staggered vertical joints (running bond) on the solid pier columns
    for pc in [i*BAY for i in range(N_BAYS+1)]:          # pier centre lines
        row = 0; yy = 0.0
        while yy < H - 0.1:
            off = (PIER*0.5) if row % 2 else -(PIER*0.5)
            for vx in (pc, pc+off):
                subs.append(blk(vx-GJW/2, vx+GJW/2, yy, min(yy+COURSE, H), T-GJD, T+1))
            yy += COURSE; row += 1

    # ---- per bay / per floor ---------------------------------------------
    for bx in range(N_BAYS):
        x0 = bx*BAY
        xw0 = x0 + (BAY-WO)/2; xw1 = xw0 + WO           # window x-span
        for fy in range(N_FLOORS):
            y0 = fy*FLOOR
            wy0 = y0 + SPAND; wy1 = wy0 + HO            # window y-span
            glass = T - REC

            # window opening (recess)
            subs.append(blk(xw0, xw1, wy0, wy1, glass, T+1))
            # raised window frame (perimeter) at the glass plane
            f = 0.5
            for (a, b, c, d) in [(xw0, xw1, wy0, wy0+f), (xw0, xw1, wy1-f, wy1),
                                 (xw0, xw0+f, wy0, wy1), (xw1-f, xw1, wy0, wy1)]:
                adds.append(blk(a, b, c, d, glass, glass+1.4))
            # central mullion + two horizontal muntins (divided lights)
            adds.append(blk((xw0+xw1)/2-0.3, (xw0+xw1)/2+0.3, wy0, wy1, glass, glass+1.2))
            for t in (1/3, 2/3):
                ym = wy0 + t*HO
                adds.append(blk(xw0, xw1, ym-0.3, ym+0.3, glass, glass+1.2))
            # projecting sill + lintel/head
            adds.append(blk(xw0-0.6, xw1+0.6, wy0-0.7, wy0, T, T+1.1))
            adds.append(blk(xw0-0.8, xw1+0.8, wy1, wy1+0.9, T, T+0.7))
            # Art Deco spandrel panel below the window, with vertical flutes
            sy0, sy1 = y0+0.6, wy0-0.9
            subs.append(blk(xw0, xw1, sy0, sy1, T-1.1, T+1))          # recessed panel
            for k in range(4):
                fx = xw0 + (k+0.5)*WO/4
                subs.append(blk(fx-0.25, fx+0.25, sy0+0.4, sy1-0.4, T-1.6, T+1))  # flutes

    slab = blk(0, W, 0, H, 0, T)
    mesh = diff(slab, subs)
    mesh = union([mesh] + adds)
    return mesh

def main():
    os.makedirs(os.path.join(OUT, "stl"), exist_ok=True)
    m = build()
    m.apply_scale(MM_PER_FT); m.merge_vertices(); m.fix_normals()
    path = os.path.join(OUT, "stl", "facade_panel.stl")
    m.export(path)
    e = m.extents
    print(f"facade panel: watertight={m.is_watertight}  triangles={len(m.faces)}")
    print(f"  {N_BAYS} bays x {N_FLOORS} floors  ->  {e[0]:.0f} x {e[1]:.0f} x {e[2]:.1f} mm  "
          f"(scale {MM_PER_FT} mm/ft ~1:{304.8/MM_PER_FT:.0f})")
    print("  ->", path)
    preview(m)

def preview(m):
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    except Exception as e:
        print("preview skipped:", e); return
    L = np.array([0.1, -0.4, 0.9]); L /= np.linalg.norm(L)
    sh = 0.35 + 0.65*np.clip(m.face_normals @ L, 0, 1)
    fc = np.clip(np.array([0.80, 0.77, 0.70])[None, :]*sh[:, None], 0, 1)
    fc = np.hstack([fc, np.ones((len(fc), 1))])
    fig = plt.figure(figsize=(7, 9)); ax = fig.add_subplot(111, projection="3d")
    ax.add_collection3d(Poly3DCollection(m.vertices[m.faces], facecolors=fc, edgecolors="none"))
    b = m.bounds; ctr = (b[0]+b[1])/2; span = (b[1]-b[0]).max()/2
    for L_, U, s in [(ax.set_xlim, None, 0)]: pass
    ax.set_xlim(ctr[0]-span, ctr[0]+span); ax.set_ylim(ctr[1]-span, ctr[1]+span); ax.set_zlim(ctr[2]-span, ctr[2]+span)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=68, azim=-90); ax.set_axis_off()
    out = os.path.join(OUT, "preview_facade.png")
    plt.savefig(out, dpi=140, bbox_inches="tight"); plt.close(); print("  preview ->", out)

if __name__ == "__main__":
    main()
