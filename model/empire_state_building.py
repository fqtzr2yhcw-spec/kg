#!/usr/bin/env python3
"""
Empire State Building - parametric, sectioned, 3D-printable model (high detail).

Driven by the real building's massing and Art Deco facade grammar:
  * full-block limestone BASE (floors 1-5): street-level arcade, upper window
    register, projecting cornice at the 5th-floor setback
  * slab TOWER shaft carved with a true punched-window GRID - paired windows per
    bay separated by aluminum mullions, continuous limestone piers, and
    per-floor spandrel reveals (the signature "vertical emphasis")
  * stepped upper SETBACKS with cornices + the 86th-floor observation deck
  * the tiered Art Deco CROWN: ribbed mooring mast, cornice rings, the windowed
    102nd-floor lantern, and the stepped cap
  * tapering SPIRE / broadcast antenna

Every section exports as its own watertight STL with a central alignment tenon
(peg on top) / mortise (socket on bottom). The tower is auto-split into as many
stacked bands as your printer bed height needs (MAX_PART_H_MM).

Reference: Shreve, Lamb & Harmon, 1931.  Roof 1250 ft, tip 1454 ft,
footprint ~425 x 197 ft, Indiana limestone over a granite base.
"""
import math
import os
import numpy as np
import trimesh

# --------------------------------------------------------------------------
# PARAMETERS
# --------------------------------------------------------------------------
MM_PER_FT      = 304.8 / 350.0 # 1:350 scale  (0.8709 mm/ft; tip ~1266mm / 4'2")
MAX_PART_H_MM  = 250.0         # printer bed height budget (Bambu P1S/P2S: 256mm)
OUT            = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl")

PIER_PITCH     = 16.0          # ft between bay centres
WINDOWS_PER_BAY = 2            # paired windows per bay (Art Deco grouping)
WIN_W          = 4.6          # each window width (ft)
WIN_DEPTH      = 3.2          # window recess depth (ft)
FLOOR_FT       = 12.25
SPANDREL_DEPTH = 1.6          # per-floor reveal depth (ft)
SPANDREL_H     = 1.4
CORNER_PIER    = 22.0         # solid corner pier width (ft)

TEN_H, TEN_CLR = 6.0, 1.6

os.makedirs(OUT, exist_ok=True)

# --------------------------------------------------------------------------
# HELPERS (feet; scaled to mm at export)
# --------------------------------------------------------------------------
def box_ft(xs, ys, z0, z1):
    b = trimesh.creation.box(extents=(xs, ys, z1 - z0))
    b.apply_translation((0, 0, (z0 + z1) / 2.0)); return b

def slab(xs, ys, z0, z1):                       # a thin projecting cornice lip
    return box_ft(xs, ys, z0, z1)

def poly_frustum(n, r0, r1, z0, z1, rot=0.0):
    ang = rot + np.linspace(0, 2*np.pi, n, endpoint=False)
    bot = np.column_stack([r0*np.cos(ang), r0*np.sin(ang), np.full(n, z0)])
    top = np.column_stack([r1*np.cos(ang), r1*np.sin(ang), np.full(n, z1)])
    V = np.vstack([bot, top, [0, 0, z0], [0, 0, z1]])
    cbi, cti = 2*n, 2*n+1; F = []
    for i in range(n):
        j = (i+1) % n
        F += [[i, j, n+j], [i, n+j, n+i], [cbi, j, i], [cti, n+i, n+j]]
    m = trimesh.Trimesh(vertices=V, faces=np.array(F), process=True); m.fix_normals(); return m

def union(ms):  return ms[0].copy() if len(ms) == 1 else trimesh.boolean.union(ms)
def diff(a, cs):
    if not cs: return a
    return trimesh.boolean.difference([a, union(cs) if len(cs) > 1 else cs[0]])

def safe_diff(a, cs, label):
    try: return diff(a, cs)
    except Exception as e:
        print(f"  ({label} skipped: {e})"); return a

def bay_positions(width):
    n = max(1, int((width - 2*CORNER_PIER) // PIER_PITCH)); span = (n-1)*PIER_PITCH
    return [-span/2 + i*PIER_PITCH for i in range(n)], n

def window_offsets():
    if WINDOWS_PER_BAY == 1: return [0.0]
    gap = (WIN_W + 2.2)                          # window + mullion
    return [(-(WINDOWS_PER_BAY-1)/2 + k)*gap for k in range(WINDOWS_PER_BAY)]

def facade_cutters(xs, ys, z0, z1):
    """Punched window grid: paired window recesses + per-floor spandrel reveals."""
    cutters = []
    zc, zh = (z0+z1)/2.0, (z1-z0) - 2.0
    ypos, ny = bay_positions(ys)
    xpos, nx = bay_positions(xs)
    for sx in (1, -1):                           # broad faces (normal X)
        for yb in ypos:
            for wo in window_offsets():
                cutters.append(_cut(2*WIN_DEPTH, WIN_W, zh, (sx*xs/2.0, yb+wo, zc)))
    for sy in (1, -1):                           # narrow faces (normal Y)
        for xb in xpos:
            for wo in window_offsets():
                cutters.append(_cut(WIN_W, 2*WIN_DEPTH, zh, (xb+wo, sy*ys/2.0, zc)))
    z = z0 + FLOOR_FT                             # spandrel reveals (floor lines)
    while z < z1 - 2.0:
        for sx in (1, -1):
            cutters.append(_cut(2*SPANDREL_DEPTH, ys-2*CORNER_PIER, SPANDREL_H, (sx*xs/2.0, 0, z)))
        for sy in (1, -1):
            cutters.append(_cut(xs-2*CORNER_PIER, 2*SPANDREL_DEPTH, SPANDREL_H, (0, sy*ys/2.0, z)))
        z += FLOOR_FT
    return cutters, nx, ny

def _cut(xs, ys, zs, c):
    b = trimesh.creation.box(extents=(xs, ys, zs)); b.apply_translation(c); return b

def add_tenon(m, z_top, size):  return union([m, box_ft(size, size, z_top, z_top + TEN_H)])
def add_mortise(m, z_bot, size):
    d = TEN_H + 1.0; return diff(m, [box_ft(size+TEN_CLR, size+TEN_CLR, z_bot, z_bot+d)])

def block(x0, x1, y0, y1, z0, z1):
    b = trimesh.creation.box(extents=(x1-x0, y1-y0, z1-z0))
    b.apply_translation(((x0+x1)/2, (y0+y1)/2, (z0+z1)/2)); return b

def _dowel_y(r, ylen, x, z):                 # dowel hole along Y for a seam
    c = trimesh.creation.cylinder(radius=r, height=ylen, sections=20)
    c.apply_transform(trimesh.transformations.rotation_matrix(np.pi/2, (1, 0, 0)))
    c.apply_translation((x, 0, z)); return c

def split_y_halves(mesh):                    # split an over-wide section into 2 print halves
    m = diff(mesh, [_dowel_y(3.0, 44, x, z) for x in (-70, 70) for z in (35, 95)])
    B = 1e5
    return diff(m, [block(-B, B, -B, 0, -B, B)]), diff(m, [block(-B, B, 0, B, -B, B)])

# --------------------------------------------------------------------------
# BUILD
# --------------------------------------------------------------------------
def build():
    sections, meta = {}, {}

    # 01 BASE ---------------------------------------------------------------
    b1 = box_ft(197, 425, 0, 60)
    # street-level arcade (tall bays)
    arc = []
    for w, sgn, ax in [(425, 1, 'x'), (425, -1, 'x'), (197, 1, 'y'), (197, -1, 'y')]:
        pos, _ = bay_positions_generic(w, 26.0, 16.0)
        for p in pos:
            if ax == 'x': arc.append(_cut(5.0, 15.5, 24, (sgn*197/2.0, p, 16)))
            else:         arc.append(_cut(15.5, 5.0, 24, (p, sgn*425/2.0, 16)))
    b1 = safe_diff(b1, arc, "base-arcade")
    # upper-base window register (floors 2-5)
    bc, _, _ = facade_cutters_custom(197, 425, 32, 58, pitch=21.0, wdepth=2.2)
    b1 = safe_diff(b1, bc, "base-windows")
    base = union([b1,
                  slab(207, 435, 0, 4),          # projecting granite water-table course
                  slab(205, 433, 58, 62),        # 5th-floor projecting cornice
                  box_ft(165, 340, 62, 120)])
    base = add_tenon(base, 120, 24)
    sections["01_base"] = base

    # 02.. TOWER SHAFT (auto-split to bed height) ---------------------------
    shaft_z0, shaft_z1 = 120, 1000
    band_h_ft = MAX_PART_H_MM / MM_PER_FT
    nbands = max(1, math.ceil((shaft_z1 - shaft_z0) / band_h_ft))
    edges = np.linspace(shaft_z0, shaft_z1, nbands + 1)
    for i in range(nbands):
        z0, z1 = float(edges[i]), float(edges[i+1])
        name = f"{i+2:02d}_shaft_{i+1}of{nbands}"
        s = box_ft(132, 210, z0, z1)
        cutters, nx, ny = facade_cutters(132, 210, z0, z1)
        s = safe_diff(s, cutters, name)
        if i > 0:            s = add_mortise(s, z0, 22)
        else:                s = add_mortise(s, z0, 24)
        s = add_tenon(s, z1, 22)
        sections[name] = s
        meta[name] = f"{ny}x{nx} bays x{WINDOWS_PER_BAY} windows, {int((z1-z0)/FLOOR_FT)} floors"
    nxt = nbands + 2

    # 04 SETBACKS + cornices + 86th deck ------------------------------------
    setb = union([
        slab(140, 218, 1000, 1004),              # cornice over shaft
        box_ft(118, 180, 1004, 1024),
        slab(124, 186, 1024, 1028),
        box_ft(104, 150, 1028, 1046),
        slab(110, 156, 1046, 1050),
        box_ft(92, 124, 1050, 1062),             # 86th-floor deck parapet
    ])
    setb = add_mortise(setb, 1000, 22)
    setb = add_tenon(setb, 1062, 18)
    sections[f"{nxt:02d}_setbacks"] = setb

    # 05 CROWN : ribbed mast + cornice rings + lantern + stepped cap ---------
    N = 32
    drums = [(46, 44, 1062, 1110), (41, 39, 1110, 1152),
             (37, 35, 1152, 1200), (33, 31, 1200, 1228),
             (30, 18, 1228, 1246), (16, 10, 1246, 1258)]   # last two = stepped cap
    parts = [poly_frustum(N, r0, r1, a, b) for (r0, r1, a, b) in drums]
    for r, z in [(49, 1110), (44, 1152), (40, 1200)]:      # projecting cornice rings
        parts.append(poly_frustum(N, r, r, z-2.5, z+2.5))
    crown = union(parts)
    ribs = [_radial(3.5, 3.4, 1062, 1150, ang, 44)         # mast mullion grooves (chunkier ribs)
            for ang in np.linspace(0, 2*np.pi, 24, endpoint=False)]
    crown = safe_diff(crown, ribs, "crown-ribs")
    # 102nd-floor lantern windows
    try:
        slots = [_radial(11, 4.5, 1160, 1196, ang, 35)
                 for ang in np.linspace(0, 2*np.pi, 16, endpoint=False)]
        crown = diff(crown, slots)
    except Exception as e:
        print("  (lantern slots skipped:", e, ")")
    crown = add_mortise(crown, 1062, 18)
    crown = add_tenon(crown, 1258, 6)
    sections[f"{nxt+1:02d}_crown"] = crown

    # 06 SPIRE : stepped mast base + antenna needle -------------------------
    # sturdier taper for a 170mm-tall needle: base 19mm -> tip ~5.6mm, still slender
    spire = union([poly_frustum(24, 11, 8.0, 1258, 1300),
                   poly_frustum(20, 8.0, 5.5, 1300, 1370),
                   poly_frustum(16, 5.5, 3.2, 1370, 1454)])
    spire = add_mortise(spire, 1258, 6)
    sections[f"{nxt+2:02d}_spire"] = spire
    return sections, meta

def _radial(depth, width, z0, z1, ang, r):
    b = trimesh.creation.box(extents=(depth, width, (z1-z0)))
    b.apply_translation((r, 0, (z0+z1)/2.0))
    b.apply_transform(trimesh.transformations.rotation_matrix(ang, (0, 0, 1))); return b

def bay_positions_generic(width, pitch, corner):
    n = max(1, int((width - 2*corner) // pitch)); span = (n-1)*pitch
    return [-span/2 + i*pitch for i in range(n)], n

def facade_cutters_custom(xs, ys, z0, z1, pitch, wdepth):
    cutters = []; zc, zh = (z0+z1)/2.0, (z1-z0)-2.0
    for sx in (1, -1):
        for p, in [(v,) for v in bay_positions_generic(ys, pitch, 16.0)[0]]:
            cutters.append(_cut(2*wdepth, pitch*0.5, zh, (sx*xs/2.0, p, zc)))
    for sy in (1, -1):
        for p in bay_positions_generic(xs, pitch, 16.0)[0]:
            cutters.append(_cut(pitch*0.5, 2*wdepth, zh, (p, sy*ys/2.0, zc)))
    return cutters, 0, 0

# --------------------------------------------------------------------------
# EXPORT + REPORT + PREVIEW
# --------------------------------------------------------------------------
def main():
    sections, meta = build()
    # base long axis exceeds the bed at this scale -> split into 2 dowel-pinned halves
    if "01_base" in sections and 433*MM_PER_FT > 250:
        n, s = split_y_halves(sections.pop("01_base"))
        sections = {"01_base_N": n, "01_base_S": s, **sections}
        meta["01_base_N"] = meta["01_base_S"] = "base half (dowel-pin seam at centre)"
    print(f"\nScale {MM_PER_FT} mm/ft  bed budget {MAX_PART_H_MM:.0f}mm  "
          f"(roof {1250*MM_PER_FT:.0f}mm, tip {1454*MM_PER_FT:.0f}mm)\n")
    print(f"{'section':22}{'watertight':11}{'W x D x H mm':24}notes")
    print("-"*90)
    scaled = {}
    for name, m in sections.items():
        m = m.copy(); m.apply_scale(MM_PER_FT); m.merge_vertices(); m.fix_normals()
        m.export(os.path.join(OUT, name + ".stl")); scaled[name] = m
        e = m.extents
        flag = "" if e[0] <= MAX_PART_H_MM and e[1] <= MAX_PART_H_MM else "  <-check bed XY"
        print(f"{name:22}{str(m.is_watertight):11}{e[0]:6.1f} x{e[1]:6.1f} x{e[2]:7.1f}    {meta.get(name,'')}{flag}")
    trimesh.util.concatenate(list(scaled.values())).export(os.path.join(OUT, "00_full_assembly_preview.stl"))
    print(f"\nWrote {len(scaled)} sections + preview to {OUT}")
    preview(scaled)

def preview(scaled):
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    except Exception as e:
        print("preview skipped:", e); return
    keys = list(scaled)
    cmap = plt.get_cmap("gray")
    L = np.array([-0.3, -0.5, 0.8]); L /= np.linalg.norm(L)
    lo = np.min([m.bounds[0] for m in scaled.values()], axis=0)
    hi = np.max([m.bounds[1] for m in scaled.values()], axis=0)
    ctr, span = (lo+hi)/2, (hi-lo).max()/2
    fig = plt.figure(figsize=(12, 7))
    for k, (t, el, az) in enumerate([("Isometric", 16, -55), ("Broad face", 3, -90), ("Narrow face", 3, 0)]):
        ax = fig.add_subplot(1, 3, k+1, projection="3d")
        for i, (name, m) in enumerate(scaled.items()):
            base = np.array(cmap(0.45 + 0.1*np.sin(i))[:3])
            if "crown" in name: base = np.array([0.79, 0.63, 0.30])
            sh = 0.4 + 0.6*np.clip(m.face_normals @ L, 0, 1)
            fc = np.clip(base[None, :]*sh[:, None], 0, 1); fc = np.hstack([fc, np.ones((len(fc), 1))])
            ax.add_collection3d(Poly3DCollection(m.vertices[m.faces], facecolors=fc, edgecolors="none"))
        ax.set_xlim(ctr[0]-span, ctr[0]+span); ax.set_ylim(ctr[1]-span, ctr[1]+span); ax.set_zlim(ctr[2]-span, ctr[2]+span)
        ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=el, azim=az); ax.set_axis_off(); ax.set_title(t, fontsize=11)
    fig.suptitle("Empire State Building - high-detail sectioned model", fontsize=13)
    plt.tight_layout(); out = os.path.join(os.path.dirname(OUT), "preview_matplotlib.png")
    plt.savefig(out, dpi=130, bbox_inches="tight"); plt.close(); print("matplotlib preview ->", out)

if __name__ == "__main__":
    main()
