#!/usr/bin/env python3
"""
Empire State Building - 4-wall-plate variant.

For each tower band, emit the FOUR outer walls (east / west = broad faces,
north / south = narrow faces) as separate flat-backed printable plates that
carry the Art Deco facade relief on the outer face and interlock at the vertical
corners (tab-and-slot spline joints), assembling into a hollow ring per band.

Print each plate flat (inner face down, relief up) or standing; glue the corner
splines. This is the hollow-shell alternative to the solid banded sections in
empire_state_building.py.
"""
import os
import numpy as np
import trimesh

MM_PER_FT   = 0.40
OUT         = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl_panels")

WALL_T      = 7.0            # wall thickness (ft) ~2.8mm
PIER_PITCH  = 16.0
WIN_FRAC    = 0.58
WIN_DEPTH   = 3.0
FLOOR_FT    = 12.25
SPANDREL_DEPTH = 1.1
SPANDREL_H  = 1.3
TAB_LEN     = 4.5            # corner spline depth (ft)
TAB_W       = 6.0            # corner spline width (ft)
CLR         = 0.8            # corner slot clearance (ft)

os.makedirs(OUT, exist_ok=True)

def box(xs, ys, zs, c):
    b = trimesh.creation.box(extents=(xs, ys, zs)); b.apply_translation(c); return b

def union(ms):  return ms[0].copy() if len(ms) == 1 else trimesh.boolean.union(ms)
def diff(a, cs): return a if not cs else trimesh.boolean.difference([a, union(cs) if len(cs) > 1 else cs[0]])

def centered(width, pitch, corner):
    n = max(1, int((width - 2*corner) // pitch)); span = (n-1)*pitch
    return [-span/2 + i*pitch for i in range(n)]

def relief_cutters_face(axis, sign, plate_w, z0, z1, corner):
    """Vertical window bands + floor reveals on ONE outer face."""
    win = PIER_PITCH*WIN_FRAC
    zc, zh = (z0+z1)/2.0, (z1-z0)-2.0
    face = sign*plate_w_outer[axis]/2.0  # set per call below
    cutters = []
    for p in centered(plate_w, PIER_PITCH, corner):
        if axis == 'x':
            cutters.append(box(2*WIN_DEPTH, win, zh, (face, p, zc)))
        else:
            cutters.append(box(win, 2*WIN_DEPTH, zh, (p, face, zc)))
    z = z0 + FLOOR_FT
    while z < z1 - 2.0:
        if axis == 'x':
            cutters.append(box(2*SPANDREL_DEPTH, plate_w-2*corner, SPANDREL_H, (face, 0, z)))
        else:
            cutters.append(box(plate_w-2*corner, 2*SPANDREL_DEPTH, SPANDREL_H, (0, face, z)))
        z += FLOOR_FT
    return cutters

def build_band(X, Y, z0, z1):
    """Return {east,west,north,south: mesh} for one tower band."""
    global plate_w_outer
    plate_w_outer = {'x': X, 'y': Y}
    T, H, zc = WALL_T, z1-z0, (z0+z1)/2.0
    Xn = X - 2*T
    walls = {}

    # broad walls (normal X): east=+x, west=-x, full Y length; carry 2 corner slots
    for sx, tag in [(1, 'east'), (-1, 'west')]:
        w = box(T, Y, H, (sx*(X/2 - T/2), 0, zc))
        w = diff(w, relief_cutters_face('x', sx, Y, z0, z1, 18.0))
        slots = []
        for sy in (1, -1):
            slots.append(box(TAB_LEN+CLR, TAB_W+CLR, H*0.94,
                             (sx*(X/2 - T + (TAB_LEN+CLR)/2), sy*(Y/2 - T/2), zc)))
        w = diff(w, slots)
        walls[tag] = w

    # narrow walls (normal Y): north=+y, south=-y, inset in X; carry 2 corner tabs
    for sy, tag in [(1, 'north'), (-1, 'south')]:
        w = box(Xn, T, H, (0, sy*(Y/2 - T/2), zc))
        w = diff(w, relief_cutters_face('y', sy, Xn, z0, z1, 16.0))
        tabs = [w]
        for sx in (1, -1):
            tabs.append(box(TAB_LEN, TAB_W, H*0.9,
                            (sx*(X/2 - T + TAB_LEN/2), sy*(Y/2 - T/2), zc)))
        w = union(tabs)
        walls[tag] = w
    return walls

def main():
    bands = [("lower", 132, 210, 120, 560), ("upper", 132, 210, 560, 1000)]
    print(f"\n4-wall-plate variant  (scale {MM_PER_FT} mm/ft, wall {WALL_T*MM_PER_FT:.1f}mm)\n")
    print(f"{'plate':22}{'watertight':11}{'W x D x H mm'}")
    print("-"*55)
    allw = {}
    for name, X, Y, z0, z1 in bands:
        walls = build_band(X, Y, z0, z1)
        for face, m in walls.items():
            m = m.copy(); m.apply_scale(MM_PER_FT); m.merge_vertices(); m.fix_normals()
            fn = f"{name}_{face}"
            m.export(os.path.join(OUT, fn + ".stl")); allw[fn] = m
            e = m.extents
            print(f"{fn:22}{str(m.is_watertight):11}{e[0]:6.1f} x{e[1]:6.1f} x{e[2]:7.1f}")
    print(f"\nWrote {len(allw)} wall plates to {OUT}")
    preview(bands)

def preview(bands):
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    except Exception as e:
        print("preview skipped:", e); return
    # exploded view of the lower band's 4 plates
    walls = build_band(132, 210, 120, 560)
    off = 90
    shift = {'east': (off, 0, 0), 'west': (-off, 0, 0), 'north': (0, off, 0), 'south': (0, -off, 0)}
    col = {'east': "#8c8c8c", 'west': "#9a9a9a", 'north': "#7f7f7f", 'south': "#adadad"}
    L = np.array([-0.3, -0.5, 0.8]); L /= np.linalg.norm(L)
    fig = plt.figure(figsize=(8, 8)); ax = fig.add_subplot(111, projection="3d")
    for face, m in walls.items():
        m = m.copy(); m.apply_translation(shift[face])
        base = np.array(matplotlib.colors.to_rgb(col[face]))
        sh = 0.4 + 0.6*np.clip(m.face_normals @ L, 0, 1)
        fc = np.clip(base[None, :]*sh[:, None], 0, 1); fc = np.hstack([fc, np.ones((len(fc), 1))])
        ax.add_collection3d(Poly3DCollection(m.vertices[m.faces], facecolors=fc, edgecolors="none"))
    ax.set_xlim(-200, 200); ax.set_ylim(-200, 200); ax.set_zlim(40, 240)
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=28, azim=-52); ax.set_axis_off()
    ax.set_title("4 wall plates - exploded (one tower band)")
    out = os.path.join(os.path.dirname(OUT), "preview_panels.png")
    plt.savefig(out, dpi=130, bbox_inches="tight"); plt.close(); print("panels preview ->", out)

if __name__ == "__main__":
    main()
