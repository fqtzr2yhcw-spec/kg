#!/usr/bin/env python3
"""
Empire State Building - parametric, sectioned, 3D-printable model (detailed).

Driven by the real building's massing and Art Deco facade grammar rather than a
generative guess:
  * full-block limestone BASE (floors 1-5) with a street-level arcade + upper
    window register
  * slab TOWER shaft carved with the signature vertical limestone piers AND
    shallow per-floor spandrel reveals (Art Deco "vertical emphasis")
  * stepped upper SETBACKS forming the crown base + 86th-floor deck
  * the stepped mooring-mast CROWN with vertical ribs and the 102nd-floor lantern
  * tapering SPIRE / broadcast antenna

Each section exports as its own watertight STL and carries a central alignment
tenon (peg on top) / mortise (socket on bottom) so the parts stack and register.

Reference: Shreve, Lamb & Harmon, 1931. Roof (102nd fl) 1250 ft, tip 1454 ft,
footprint ~2 acres (~425 x 197 ft), Indiana limestone over a granite base.
"""

import os
import numpy as np
import trimesh

# --------------------------------------------------------------------------
# PARAMETERS
# --------------------------------------------------------------------------
MM_PER_FT   = 0.40           # roof 1250ft -> 500mm, tip 1454ft -> ~582mm
OUT         = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stl")

PIER_PITCH  = 16.0           # ft between window-band centres (tower)
WIN_FRAC    = 0.58           # window width / pitch
WIN_DEPTH   = 3.0            # ft the vertical window bands recess
FLOOR_FT    = 12.25          # storey height
SPANDREL_DEPTH = 1.1         # ft the shallow per-floor reveals recess
SPANDREL_H  = 1.3            # ft height of each floor reveal

TEN_H       = 6.0            # tenon height (ft)
TEN_CLR     = 1.6            # mortise clearance (ft)

os.makedirs(OUT, exist_ok=True)

# --------------------------------------------------------------------------
# GEOMETRY HELPERS (feet; scaled to mm at export)
# --------------------------------------------------------------------------
def box_ft(xs, ys, z0, z1):
    b = trimesh.creation.box(extents=(xs, ys, z1 - z0))
    b.apply_translation((0, 0, (z0 + z1) / 2.0))
    return b

def poly_frustum(n, r0, r1, z0, z1, rot=0.0):
    ang = rot + np.linspace(0, 2 * np.pi, n, endpoint=False)
    bottom = np.column_stack([r0*np.cos(ang), r0*np.sin(ang), np.full(n, z0)])
    top    = np.column_stack([r1*np.cos(ang), r1*np.sin(ang), np.full(n, z1)])
    V = np.vstack([bottom, top, [0, 0, z0], [0, 0, z1]])
    cbi, cti = 2*n, 2*n+1
    F = []
    for i in range(n):
        j = (i+1) % n
        F += [[i, j, n+j], [i, n+j, n+i], [cbi, j, i], [cti, n+i, n+j]]
    m = trimesh.Trimesh(vertices=V, faces=np.array(F), process=True)
    m.fix_normals()
    return m

def union(meshes):
    return meshes[0].copy() if len(meshes) == 1 else trimesh.boolean.union(meshes)

def difference(a, cutters):
    if not cutters:
        return a
    tool = union(cutters) if len(cutters) > 1 else cutters[0]
    return trimesh.boolean.difference([a, tool])

def centered(width, pitch, corner):
    usable = width - 2*corner
    n = max(1, int(usable // pitch))
    span = (n-1)*pitch
    return [-span/2 + i*pitch for i in range(n)], n

def add_tenon(mesh, z_top, size):
    t = box_ft(size, size, z_top, z_top + TEN_H)
    return union([mesh, t])

def add_mortise(mesh, z_bottom, size):
    d = TEN_H + 1.0
    return difference(mesh, [box_ft(size + TEN_CLR, size + TEN_CLR, z_bottom, z_bottom + d)])

# --------------------------------------------------------------------------
# FACADE RELIEF
# --------------------------------------------------------------------------
def facade_cutters(xs, ys, z0, z1, pitch, win_depth, corner,
                   floor_reveals=True):
    """Vertical window bands + shallow per-floor reveals on all four faces."""
    win  = pitch * WIN_FRAC
    cutters = []
    vmarg = 1.0
    zc, zh = (z0+z1)/2.0, (z1-z0) - 2*vmarg
    ypos, ny = centered(ys, pitch, corner)          # broad faces (normal X)
    for sx in (1, -1):
        for yc in ypos:
            c = trimesh.creation.box(extents=(2*win_depth, win, zh))
            c.apply_translation((sx*xs/2.0, yc, zc)); cutters.append(c)
    xpos, nx = centered(xs, pitch, corner)           # narrow faces (normal Y)
    for sy in (1, -1):
        for xc in xpos:
            c = trimesh.creation.box(extents=(win, 2*win_depth, zh))
            c.apply_translation((xc, sy*ys/2.0, zc)); cutters.append(c)
    if floor_reveals:
        bw_y = ys - 2*corner
        bw_x = xs - 2*corner
        z = z0 + FLOOR_FT
        while z < z1 - 2.0:
            for sx in (1, -1):
                c = trimesh.creation.box(extents=(2*SPANDREL_DEPTH, bw_y, SPANDREL_H))
                c.apply_translation((sx*xs/2.0, 0, z)); cutters.append(c)
            for sy in (1, -1):
                c = trimesh.creation.box(extents=(bw_x, 2*SPANDREL_DEPTH, SPANDREL_H))
                c.apply_translation((0, sy*ys/2.0, z)); cutters.append(c)
            z += FLOOR_FT
    return cutters, nx, ny

def base_cutters(xs, ys):
    """Street-level arcade (tall bays) + an upper-floor window register."""
    cutters = []
    corner = 14.0
    # tall ground-floor arcade, z 4..28
    apitch, afrac, adepth = 26.0, 0.6, 2.5
    for (w, sgn, axis) in [(ys, 1, 'x'), (ys, -1, 'x'), (xs, 1, 'y'), (xs, -1, 'y')]:
        pos, _ = centered(w, apitch, corner)
        for p in pos:
            bay = apitch*afrac
            if axis == 'x':
                c = trimesh.creation.box(extents=(2*adepth, bay, 24)); c.apply_translation((sgn*xs/2.0, p, 16))
            else:
                c = trimesh.creation.box(extents=(bay, 2*adepth, 24)); c.apply_translation((p, sgn*ys/2.0, 16))
            cutters.append(c)
    return cutters

def crown_rib_cutters(n, r, z0, z1):
    ribs = []
    for i in range(n):
        c = trimesh.creation.box(extents=(6, 2.2, (z1-z0)-4))
        c.apply_translation((r, 0, (z0+z1)/2.0))
        c.apply_transform(trimesh.transformations.rotation_matrix(2*np.pi*i/n, (0, 0, 1)))
        ribs.append(c)
    return ribs

def safe_diff(solid, cutters, label):
    try:
        return difference(solid, cutters)
    except Exception as e:
        print(f"  ({label} relief skipped: {e})")
        return solid

# --------------------------------------------------------------------------
# BUILD SECTIONS
# --------------------------------------------------------------------------
def build():
    sections, meta = {}, {}

    # 01 BASE : full-lot podium (1-5) + lower massing, with street-level detail
    b1 = box_ft(197, 425, 0, 60)
    b1 = safe_diff(b1, base_cutters(197, 425), "base")
    # upper-base window register (floors 2-5) as vertical bands
    bc, _, _ = facade_cutters(197, 425, 32, 58, 22.0, 2.2, 16.0, floor_reveals=False)
    b1 = safe_diff(b1, bc, "base-windows")
    base = union([b1, box_ft(165, 340, 60, 120)])
    base = add_tenon(base, 120, 22)
    sections["01_base"] = base

    # 02/03 TOWER SHAFT : slab split into two printable bands, full Art Deco relief
    for name, z0, z1 in [("02_shaft_lower", 120, 560),
                         ("03_shaft_upper", 560, 1000)]:
        s = box_ft(132, 210, z0, z1)
        cutters, nx, ny = facade_cutters(132, 210, z0, z1, PIER_PITCH, WIN_DEPTH, 24.0)
        s = safe_diff(s, cutters, name)
        s = add_mortise(s, z0, 22)
        s = add_tenon(s, z1, 22)
        sections[name] = s
        meta[name] = f"{ny}x{nx} window bands + {int((z1-z0)/FLOOR_FT)} floor reveals"

    # 04 SETBACKS : stepped tiers + 86th-floor observation deck
    setb = union([box_ft(118, 180, 1000, 1022),
                  box_ft(104, 150, 1022, 1040),
                  box_ft( 92, 124, 1040, 1052)])
    setb = add_mortise(setb, 1000, 22)
    setb = add_tenon(setb, 1052, 18)
    sections["04_setbacks"] = setb

    # 05 CROWN : ribbed mooring mast + 102nd-floor lantern
    N = 24
    crown = union([
        poly_frustum(N, 46, 44, 1052, 1110),
        poly_frustum(N, 40, 38, 1110, 1152),
        poly_frustum(N, 36, 35, 1152, 1200),   # lantern
        poly_frustum(N, 33, 18, 1200, 1238),   # dome cap
        poly_frustum(N, 15, 11, 1238, 1252),
    ])
    crown = safe_diff(crown, crown_rib_cutters(24, 45, 1052, 1150), "crown-ribs")
    try:
        slots = []
        for i in range(12):
            c = trimesh.creation.box(extents=(10, 4, 40)); c.apply_translation((33, 0, 1176))
            c.apply_transform(trimesh.transformations.rotation_matrix(2*np.pi*i/12, (0, 0, 1)))
            slots.append(c)
        crown = difference(crown, slots)
    except Exception as e:
        print("  (lantern slots skipped:", e, ")")
    crown = add_mortise(crown, 1052, 18)
    crown = add_tenon(crown, 1252, 6)
    sections["05_crown"] = crown

    # 06 SPIRE : tapering mast + antenna needle
    spire = union([poly_frustum(16, 9, 5, 1252, 1335),
                   poly_frustum(16, 5, 2.5, 1335, 1454)])
    spire = add_mortise(spire, 1252, 6)
    sections["06_spire"] = spire
    return sections, meta

# --------------------------------------------------------------------------
# EXPORT + REPORT + PREVIEW
# --------------------------------------------------------------------------
def main():
    sections, meta = build()
    print(f"\nScale {MM_PER_FT} mm/ft  (roof {1250*MM_PER_FT:.0f}mm, tip {1454*MM_PER_FT:.0f}mm)\n")
    print(f"{'section':16}{'watertight':11}{'W x D x H mm':24}notes")
    print("-"*82)
    scaled = {}
    for name, m in sections.items():
        m = m.copy(); m.apply_scale(MM_PER_FT); m.merge_vertices(); m.fix_normals()
        m.export(os.path.join(OUT, name + ".stl"))
        scaled[name] = m
        e = m.extents
        print(f"{name:16}{str(m.is_watertight):11}"
              f"{e[0]:6.1f} x{e[1]:6.1f} x{e[2]:7.1f}    {meta.get(name,'')}")
    trimesh.util.concatenate(list(scaled.values())).export(
        os.path.join(OUT, "00_full_assembly_preview.stl"))
    print(f"\nWrote {len(scaled)} sections + preview to {OUT}")
    render_matplotlib(scaled)

def render_matplotlib(scaled):
    try:
        import matplotlib; matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    except Exception as e:
        print("preview skipped:", e); return
    pal = {"01_base":"#6f6f6f","02_shaft_lower":"#8c8c8c","03_shaft_upper":"#9c9c9c",
           "04_setbacks":"#7f7f7f","05_crown":"#c9a24a","06_spire":"#b3b3b3"}
    L = np.array([-0.3,-0.5,0.8]); L/=np.linalg.norm(L)
    lo = np.min([m.bounds[0] for m in scaled.values()],axis=0)
    hi = np.max([m.bounds[1] for m in scaled.values()],axis=0)
    ctr,span=(lo+hi)/2,(hi-lo).max()/2
    fig=plt.figure(figsize=(12,7))
    for k,(t,el,az) in enumerate([("Isometric",16,-55),("Broad face",3,-90),("Narrow face",3,0)]):
        ax=fig.add_subplot(1,3,k+1,projection="3d")
        for name,m in scaled.items():
            base=np.array(matplotlib.colors.to_rgb(pal[name]))
            sh=0.4+0.6*np.clip(m.face_normals@L,0,1)
            fc=np.clip(base[None,:]*sh[:,None],0,1); fc=np.hstack([fc,np.ones((len(fc),1))])
            ax.add_collection3d(Poly3DCollection(m.vertices[m.faces],facecolors=fc,edgecolors="none"))
        ax.set_xlim(ctr[0]-span,ctr[0]+span);ax.set_ylim(ctr[1]-span,ctr[1]+span);ax.set_zlim(ctr[2]-span,ctr[2]+span)
        ax.set_box_aspect((1,1,1));ax.view_init(elev=el,azim=az);ax.set_axis_off();ax.set_title(t,fontsize=11)
    fig.suptitle("Empire State Building - detailed sectioned print model",fontsize=13)
    plt.tight_layout();out=os.path.join(os.path.dirname(OUT),"preview_matplotlib.png")
    plt.savefig(out,dpi=130,bbox_inches="tight");plt.close();print("matplotlib preview ->",out)

if __name__ == "__main__":
    main()
