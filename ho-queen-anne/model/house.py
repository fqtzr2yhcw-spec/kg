"""HO-scale Queen Anne Victorian house - concept model.

Builds the full house as a set of material groups (for rendering) and writes
them to ``out/house_parts.npz``. Dimensions are in prototype feet via ft().
"""
import math
import os
import sys
import time
from collections import defaultdict

import numpy as np
from manifold3d import Manifold as M, CrossSection as CS, JoinType

sys.path.insert(0, os.path.dirname(__file__))
from geom import (ft, inch, box, union, cs_union, rect, poly, prism, cyl, revolve,
                  frame_matrix, Wall, clapboard, shingle_rows, stonework, brickwork,
                  Plane, roof_slab, roof_solid, plane_faces, roof_texture, roof_caps,
                  segment_bar)
import components as C

OUT = os.path.join(os.path.dirname(__file__), "..", "out")
PARTS = defaultdict(list)


def add(mat, m):
    if m is None or m.is_empty():
        return
    PARTS[mat].append(m)


def add_parts(parts, wall=None):
    for k, m in parts.items():
        add(k, wall.place(m) if wall is not None else m)


# ------------------------------------------------------------------ levels
ZF = ft(3.0)                 # first floor / top of foundation
H1 = ft(11.0)                # first storey
H2 = ft(11.0)                # second storey
Z2 = ZF + H1                 # second floor line
ZE = ZF + H1 + H2            # main eave (wall line height of roof planes)
ZP = ZF - ft(0.6)            # porch floor
T = 2.4                      # wall core thickness
CB = inch(5.5)               # corner board width

S_MAIN = 1.15                # main roof pitch (rise/run)
S_WING = 1.0
OV = ft(1.5)                 # main eave overhang
WALL_BASE = ft(1.0)          # walls start below foundation top (hidden)

# plan (feet -> mm)
X0, X1 = 0.0, ft(30)
Y0, Y1 = 0.0, ft(38)
WX0, WY0 = ft(17), -ft(6)    # front gable wing x range [WX0, X1], y [WY0, 0]

TOWER_C = np.array([ft(3.5), ft(1.0)])
TOWER_A = ft(5.5)            # apothem
TOWER_TOP = ZF + ft(33)
S_TOWER = 3.0


def wall_texture(w, outline, zones, holes):
    """Apply texture zones to wall w. zones: (v0, v1, kind)."""
    for (a, b, kind) in zones:
        band = outline ^ rect(-5, a, w.L + 5, b)
        band = band - holes
        if band.is_empty():
            continue
        if kind == "clap":
            add("siding", w.place(clapboard(band, datum=ZF - w.zb)))
        elif kind == "fish":
            add("shingle", w.place(shingle_rows(band, inch(5.5), inch(6.5), d=0.4,
                                                shape="fish", datum=Z2 - w.zb + 1.0)))
        elif kind == "sawtooth":
            add("shingle", w.place(shingle_rows(band, inch(5.5), inch(6), d=0.4,
                                                shape="hex", datum=Z2 - w.zb + 1.0)))
        elif kind == "stone":
            add("stone", w.place(stonework(band, seed=int(w.L * 10) % 97)))
        elif kind == "brick":
            add("brick", w.place(brickwork(band)))


def build_wall(p0, p1, top, zones, windows=(), doors=(), outline=None,
               corners=(True, True), belt=True, core_mat="siding", zb=WALL_BASE,
               tex_top=None):
    """Generic textured wall with openings. ``top`` = wall-top z (world)."""
    w = Wall(p0, p1, zb)
    H = top - zb
    if outline is None:
        outline = rect(0, 0, w.L, H)
    holes = []
    for spec in windows:
        op, parts = C.window(**spec)
        holes.append(op)
        add_parts(parts, w)
    for spec in doors:
        op, parts = C.double_door(**spec)
        holes.append(op)
        add_parts(parts, w)
    hole = cs_union(holes)
    add(core_mat, w.place(M.extrude(outline - hole, T).translate([0, 0, -T])))
    wall_texture(w, outline, zones, cs_union([h.offset(0.25) for h in holes]) if holes else CS())
    # corner boards
    ext = 0.75
    if corners[0]:
        add("trim", w.place(box([-ext, 0, -0.3], [CB, H, 0.75])))
    if corners[1]:
        add("trim", w.place(box([w.L - CB, 0, -0.3], [w.L + ext, H, 0.75])))
    # water table at the base (just above foundation)
    wt = ZF - zb
    add("trim", w.place(box([-ext, wt - 0.2, -0.3], [w.L + ext, wt + inch(7), 0.8])))
    add("trim", w.place(box([-ext, wt + inch(7), -0.3], [w.L + ext, wt + inch(7) + 0.35, 1.05])))
    if belt:
        bv = Z2 - zb
        add("trim", w.place(box([-ext, bv - inch(3), -0.3], [w.L + ext, bv + ft(0.9), 0.8])))
        add("trim", w.place(box([-ext - 0.2, bv + ft(0.9), -0.3], [w.L + ext + 0.2, bv + ft(0.9) + 0.4, 1.15])))
        add("trim", w.place(box([-ext - 0.1, bv - inch(3) - 0.35, -0.3], [w.L + ext + 0.1, bv - inch(3), 0.95])))
    return w


def win(u, zsill, wft=2.8, hft=6.0, lites="2/2", head="cornice", zb=WALL_BASE, tex=0.42):
    return dict(uc=u, vb=zsill - zb, w=ft(wft), h=ft(hft), lites=lites, head=head, tex=tex)


def frieze(w, zt, brackets=True, spacing=ft(4.0), u0=0.0, u1=None, drop=ft(1.4)):
    """Frieze band + cornice brackets along the top of wall w (world z top)."""
    u1 = w.L if u1 is None else u1
    v = zt - w.zb
    add("trim", w.place(box([u0, v - drop, -0.3], [u1, v, 0.7])))
    add("accent", w.place(box([u0 + 0.5, v - drop + 0.5, 0.7], [u1 - 0.5, v - 0.9, 0.82])))
    add("trim", w.place(box([u0, v - drop - 0.45, -0.3], [u1, v - drop, 1.0])))
    if brackets:
        n = max(1, int(round((u1 - u0 - ft(2)) / spacing)))
        for k in range(n + 1):
            uu = u0 + ft(1.0) + (u1 - u0 - ft(2.0)) * k / n
            for du in (-0.55, 0.55):
                # bracket built in (x=reach, z=down, y=thickness): map x->w, y->u, z->v
                bb = C.eave_bracket(ft(1.2), drop * 1.05, thick=0.7).transform(
                    frame_matrix([uu + du, v, 0.7], [0, 0, 1], [1, 0, 0], [0, 1, 0]))
                add("trim", w.place(bb))


# ================================================================== build
def build():
    t0 = time.time()
    # ---------------------------------------------------------- foundation
    fp_main = [(X0, Y0), (WX0, Y0), (WX0, WY0), (X1, WY0), (X1, Y1), (X0, Y1)]
    FO = 1.0  # foundation proud of sheathing
    n = len(fp_main)
    for i in range(n):
        a = np.array(fp_main[i])
        b = np.array(fp_main[(i + 1) % n])
        w = Wall(a, b, 0)
        # offset outward
        ao = a + w.n * FO - w.u * FO
        bo = b + w.n * FO + w.u * FO
        fw = Wall(ao, bo, 0)
        add("stone", fw.place(M.extrude(rect(0, 0, fw.L, ZF), 3.0).translate([0, 0, -3.0])))
        wall_texture(fw, rect(0, 0, fw.L, ZF - 0.2), [(0, ZF, "stone")], CS())
    # tower foundation
    tv = tower_vertices(TOWER_A + FO)
    for k in range(8):
        fw = Wall(tv[k], tv[(k + 1) % 8], 0)
        add("stone", fw.place(M.extrude(rect(0, 0, fw.L, ZF), 3.0).translate([0, 0, -3.0])))
        wall_texture(fw, rect(0, 0, fw.L, ZF - 0.2), [(0, ZF, "stone")], CS())
    print("foundation", round(time.time() - t0, 1))

    # ---------------------------------------------------------- walls
    zones = [(0, Z2 - WALL_BASE, "clap"), (Z2 - WALL_BASE + ft(0.9), 999, "fish")]
    s1 = ZF + ft(2.4)          # first floor sill height
    s2 = Z2 + ft(2.2)          # second floor sill
    FZ = ZE - 1.9              # frieze top (just inside soffit)
    top = ZE - 0.6

    # W1 front of main, left part (0,0)->(17,0): door + window above
    w1 = build_wall((X0, Y0), (WX0, Y0), top, zones,
                    windows=[win(ft(13.0), s2, 2.6, 5.2, "2/2", "cornice")],
                    doors=[dict(uc=ft(13.0), vb=ZF - WALL_BASE, w=ft(4.4), h=ft(7.2), tex=0.42)],
                    corners=(False, True))
    frieze(w1, FZ, u0=ft(8.5))
    # W2 wing left side (17,0)->(17,-6)
    w2 = build_wall((WX0, Y0), (WX0, WY0), top, zones,
                    windows=[win(ft(3.0), s2, 2.4, 5.0, "2/2", "cornice")],
                    corners=(True, True))
    frieze(w2, FZ)
    # W3 wing front with gable (17,-6)->(30,-6)
    L3 = X1 - WX0
    ridge_h = (L3 / 2) * S_WING
    gtop = ZE + OV * S_WING - 1.4 - WALL_BASE - 0.3
    outline3 = poly([(0, 0), (L3, 0), (L3, gtop), (L3 / 2, gtop + ridge_h), (0, gtop)])
    gz = ZE + OV * S_WING - 1.0 - WALL_BASE      # gable base (wall-local v)
    w3 = build_wall((WX0, WY0), (X1, WY0), top,
                    [zones[0], (zones[1][0], gz - 0.4, "fish"), (gz + 1.2, 999, "sawtooth")],
                    windows=[win(L3 / 2 - ft(2.0), s2, 2.4, 5.2, "qa", "cornice"),
                             win(L3 / 2 + ft(2.0), s2, 2.4, 5.2, "qa", "cornice"),
                             win(L3 / 2, ZE + OV * S_WING + ft(0.7), 2.0, 2.6, "2/2", "plain")],
                    outline=outline3)
    add("trim", w3.place(box([-0.75, gz - 0.4, -0.3], [L3 + 0.75, gz + 1.2, 0.85])))
    add("trim", w3.place(box([-0.95, gz + 1.2, -0.3], [L3 + 0.95, gz + 1.6, 1.2])))
    # W4 right side (30,-6)->(30,38)
    L4 = Y1 - WY0
    w4 = build_wall((X1, WY0), (X1, Y1), top, zones,
                    windows=[win(ft(3.0), s1, 2.8, 6.2), win(ft(3.0), s2, 2.6, 5.2),
                             win(ft(14.0), s1, 2.8, 6.2), win(ft(14.0), s2, 2.6, 5.2),
                             win(ft(39.0), s1, 2.8, 6.2), win(ft(39.0), s2, 2.6, 5.2)])
    frieze(w4, FZ)
    # W5 back (30,38)->(0,38)
    w5 = build_wall((X1, Y1), (X0, Y1), top, zones,
                    windows=[win(ft(5.0), s1, 2.8, 6.2), win(ft(5.0), s2, 2.6, 5.2),
                             win(ft(15.0), s2, 2.4, 4.4),
                             win(ft(24.0), s1, 2.8, 6.2), win(ft(24.0), s2, 2.6, 5.2)],
                    doors=[dict(uc=ft(15.0), vb=ZF - WALL_BASE, w=ft(3.2), h=ft(7.0), tex=0.42, transom=ft(1.2))])
    frieze(w5, FZ)
    # W6 left side (0,38)->(0,0)
    w6 = build_wall((X0, Y1), (X0, Y0), top, zones,
                    windows=[win(ft(8.0), s1, 2.8, 6.2), win(ft(8.0), s2, 2.6, 5.2),
                             win(ft(21.0), s1, 2.8, 6.2, "qa"), win(ft(21.0), s2, 2.6, 5.2),
                             win(ft(29.5), s1, 2.8, 6.2), win(ft(29.5), s2, 2.6, 5.2)],
                    corners=(True, False))
    frieze(w6, FZ, u1=ft(31.5))
    print("walls", round(time.time() - t0, 1))

    # ---------------------------------------------------------- tower
    build_tower()
    print("tower", round(time.time() - t0, 1))
    # ---------------------------------------------------------- bay window
    build_bay()
    print("bay", round(time.time() - t0, 1))
    # ---------------------------------------------------------- roofs
    build_roofs()
    print("roofs", round(time.time() - t0, 1))
    # ---------------------------------------------------------- porch
    build_porch()
    print("porch", round(time.time() - t0, 1))
    build_chimneys()
    print("chimneys", round(time.time() - t0, 1))
    build_extras()
    print("extras", round(time.time() - t0, 1))


def tower_vertices(a):
    R = a / math.cos(math.radians(22.5))
    pts = []
    for k in range(8):
        ang = math.radians(-90 - 22.5 + 45 * k)
        pts.append(TOWER_C + R * np.array([math.cos(ang), math.sin(ang)]))
    return pts


def build_tower():
    tv = tower_vertices(TOWER_A)
    top = TOWER_TOP - 0.4
    zones = [(0, Z2 - WALL_BASE, "clap"), (Z2 - WALL_BASE + ft(0.9), ZE - WALL_BASE, "fish"),
             (ZE - WALL_BASE + ft(0.9), 999, "sawtooth")]
    for k in range(8):
        facing = -90 + 45 * k      # outward normal angle
        wins = []
        L = np.linalg.norm(tv[(k + 1) % 8] - tv[k])
        visible_low = k in (0, 1, 6, 7)   # front, front-right, left, front-left
        if visible_low:
            wins.append(win(L / 2, ZF + ft(2.4), 2.5, 6.2, "qa" if k == 0 else "2/2", "cornice"))
            wins.append(win(L / 2, Z2 + ft(2.2), 2.4, 5.2, "2/2", "cornice"))
        wins.append(win(L / 2, ZE + ft(2.4), 2.2, 4.0, "2/2", "cornice"))
        w = build_wall(tv[k], tv[(k + 1) % 8], top, zones, windows=wins, corners=(True, True))
        # extra belt at third floor
        bv = ZE - WALL_BASE
        add("trim", w.place(box([-0.5, bv - inch(3), -0.3], [w.L + 0.5, bv + ft(0.9), 0.8])))
        add("trim", w.place(box([-0.7, bv + ft(0.9), -0.3], [w.L + 0.7, bv + ft(0.9) + 0.4, 1.15])))
        frieze(w, TOWER_TOP - 1.9, spacing=ft(10), drop=ft(1.6))

    # tower roof: octagonal spire
    ov = ft(1.3)
    planes = []
    for k in range(8):
        ang = math.radians(-90 + 45 * k)
        nrm = np.array([math.cos(ang), math.sin(ang)])
        planes.append(Plane(TOWER_C + nrm * (TOWER_A + ov), -nrm, TOWER_TOP, S_TOWER))
    fpv = tower_vertices(TOWER_A + ov)
    fp = [tuple(p) for p in fpv]
    faces = plane_faces(fp, planes)
    add("roof", roof_slab(fp, planes, 1.3, TOWER_TOP - 3))
    add("roof", roof_texture(fp, planes, kind="fish", e=inch(7), wtab=inch(7.5), d=0.4, faces=faces))
    add("roof", roof_caps(fp, planes, width=1.0, height=0.8, faces=faces))
    # boxed soffit
    zs = TOWER_TOP - 1.3
    soff = prism(fp, zs - 0.8, zs + 0.2) - prism([tuple(p) for p in tower_vertices(TOWER_A - 1)], zs - 5, zs + 5)
    add("trim", soff)
    # apex finial (metal)
    apex = TOWER_TOP + (TOWER_A + ov) * S_TOWER
    fin = revolve([(0, 0), (1.3, 0), (1.3, 0.6), (0.6, 1.2), (0.9, 2.0), (0.45, 2.8),
                   (0.45, 4.5), (1.1, 5.3), (0.45, 6.1), (0.3, 9.5), (0.9, 10.3), (0.25, 11.2),
                   (0.12, 15.0), (0, 15.0)], 16)
    add("metal", fin.translate([TOWER_C[0], TOWER_C[1], apex - 2.5]))


def build_bay():
    """Canted bay window on the wing front, first floor."""
    cx = (WX0 + X1) / 2
    y0 = WY0
    proj = ft(2.5)
    halfw = ft(5.0)       # half width at wall
    halff = ft(2.5)       # half width of front face
    pts = [(cx - halfw, y0), (cx - halff, y0 - proj), (cx + halff, y0 - proj), (cx + halfw, y0)]
    zt = ZF + ft(10.3)
    zones = [(0, 999, "clap")]
    for i in range(3):
        a, b = np.array(pts[i]), np.array(pts[i + 1])
        L = np.linalg.norm(b - a)
        wfs = [win(L / 2, ZF + ft(2.2), 2.2 if i != 1 else 3.2, 6.0, "qa" if i == 1 else "2/2", "plain")]
        w = build_wall(a, b, zt, zones, windows=wfs, belt=False)
        frieze(w, zt, spacing=ft(3.0), drop=ft(1.4))
    # bay foundation
    FO = 1.0
    for i in range(3):
        a, b = np.array(pts[i]), np.array(pts[i + 1])
        w = Wall(a, b, 0)
        fw = Wall(a + w.n * FO - w.u * 0.4, b + w.n * FO + w.u * 0.4, 0)
        add("stone", fw.place(M.extrude(rect(0, 0, fw.L, ZF), 3.0).translate([0, 0, -3.0])))
        wall_texture(fw, rect(0, 0, fw.L, ZF - 0.2), [(0, ZF, "stone")], CS())
    # bay roof (3 planes)
    ov = ft(0.8)
    planes = []
    fpts = []
    for i in range(3):
        a, b = np.array(pts[i]), np.array(pts[i + 1])
        w = Wall(a, b, 0)
        planes.append(Plane(a, -w.n, zt + 0.4, 0.8))
    # footprint: offset polygon of bay plus region into wall
    bay = poly(pts + [(cx + halfw, y0 + 3), (cx - halfw, y0 + 3)])
    fpcs = bay.offset(ov, JoinType.Miter)
    fpcs = fpcs ^ rect(-1e3, -1e3, 1e3, y0 + 0.5)
    fp = [tuple(p) for p in fpcs.to_polygons()[0]]
    faces = plane_faces(fp, planes)
    add("roof", roof_slab(fp, planes, 1.0, zt - 5))
    add("roof", roof_texture(fp, planes, kind="random", e=inch(6), wtab=inch(9), d=0.34, faces=faces))
    add("roof", roof_caps(fp, planes, width=0.9, height=0.7, faces=faces))
    soff = prism(fp, zt + 0.4 - ov * 0.8 - 1.0 - 0.7, zt + 0.4 - ov * 0.8 - 0.9) - poly_prism_inset(pts, y0)
    add("trim", soff)


def poly_prism_inset(pts, y0):
    return prism(pts + [(pts[-1][0], y0 + 5), (pts[0][0], y0 + 5)], -10, 400)


def build_roofs():
    # main hip roof
    ov = OV
    fp = [(X0 - ov, Y0 - ov), (X1 + ov, Y0 - ov), (X1 + ov, Y1 + ov), (X0 - ov, Y1 + ov)]
    planes = [Plane((0, Y0 - ov), (0, 1), ZE, S_MAIN), Plane((X1 + ov, 0), (-1, 0), ZE, S_MAIN),
              Plane((0, Y1 + ov), (0, -1), ZE, S_MAIN), Plane((X0 - ov, 0), (1, 0), ZE, S_MAIN)]
    faces = plane_faces(fp, planes)
    add("roof", roof_slab(fp, planes, 1.4, ZE - 4))
    add("roof", roof_texture(fp, planes, kind="random", e=inch(6.5), wtab=inch(10), d=0.36, faces=faces))
    add("roof", roof_caps(fp, planes, faces=faces))
    # boxed eave soffit
    zs = ZE - 1.4
    bld = prism([(X0 - 0.5, Y0 - 0.5), (X1 + 0.5, Y0 - 0.5), (X1 + 0.5, Y1 + 0.5), (X0 - 0.5, Y1 + 0.5)], zs - 5, zs + 5)
    add("trim", prism(fp, zs - 0.8, zs + 0.3) - bld)
    # ridge cresting + finials
    ridge_z = ZE + ((X1 - X0) / 2 + ov) * S_MAIN
    ry0, ry1 = Y0 + (X1 - X0) / 2, Y1 - (X1 - X0) / 2
    xc = (X0 + X1) / 2
    cres = []
    cres.append(box([xc - 0.2, ry0, ridge_z + 1.2], [xc + 0.2, ry1, ridge_z + 1.5]))
    cres.append(box([xc - 0.2, ry0, ridge_z + 3.3], [xc + 0.2, ry1, ridge_z + 3.55]))
    nsp = int((ry1 - ry0) / 1.3)
    for k in range(nsp + 1):
        yy = ry0 + (ry1 - ry0) * k / nsp
        cres.append(box([xc - 0.15, yy - 0.15, ridge_z + 1.2], [xc + 0.15, yy + 0.15, ridge_z + 4.2]))
        cres.append(M.cylinder(0.9, 0.35, 0.0, 6).translate([xc, yy, ridge_z + 4.0]))
    for yy in (ry0, ry1):
        cres.append(revolve([(0, 0), (0.8, 0), (0.8, 0.5), (0.35, 1.0), (0.6, 2.0), (0.25, 3.0),
                             (0.5, 3.8), (0.1, 6.5), (0, 6.5)], 12).translate([xc, yy, ridge_z + 0.8]))
    add("metal", union(cres))

    # wing gable roof
    rk = ft(1.0)
    wfp = [(WX0 - OV, WY0 - rk), (X1 + OV, WY0 - rk), (X1 + OV, ft(10)), (WX0, ft(10)),
           (WX0, Y0), (WX0 - OV, Y0 - OV)]
    wpl = [Plane((WX0 - OV, 0), (1, 0), ZE, S_WING), Plane((X1 + OV, 0), (-1, 0), ZE, S_WING)]
    wfaces = plane_faces(wfp, wpl)
    add("roof", roof_slab(wfp, wpl, 1.4, ZE - 4))
    add("roof", roof_texture(wfp, wpl, kind="random", e=inch(6.5), wtab=inch(10), d=0.36, seed=11, faces=wfaces))
    # ridge cap for wing
    xm = (WX0 + X1) / 2
    zr = ZE + ((X1 - WX0) / 2 + OV) * S_WING
    add("roof", segment_bar([xm, WY0 - rk, zr + 0.3], [xm, ft(5.5), zr + 0.3], 1.2, 0.9))
    # rake boards (bargeboards) with scallops
    for sgn in (-1, 1):
        x_e = WX0 - OV if sgn < 0 else X1 + OV
        z_e = ZE
        p0 = np.array([x_e, WY0 - rk - 0.2, z_e - 0.4])
        p1 = np.array([xm, WY0 - rk - 0.2, zr - 0.2])
        add("trim", segment_bar(p0 - [0, 0.6, 0], p1 - [0, 0.6, 0], 1.2, 2.4, up=(0, -1, 0)).translate([0, 0, 0]))
    # soffit along wing sides
    zs = ZE - 1.4
    add("trim", box([WX0 - OV, WY0 - rk, zs - 0.8], [WX0, Y0 - OV, zs + 0.3]))
    add("trim", box([X1, WY0 - rk, zs - 0.8], [X1 + OV, Y0, zs + 0.3]))
    gable_ornament(xm, WY0 - rk, ZE + OV * S_WING - 1.0, zr)

    # left-side dormer on main roof (faces -x)
    build_dormer()


def gable_ornament(xm, yf, zbase, zr):
    """King-post truss with sunburst in the front gable peak."""
    ys = yf - 0.4
    parts = []
    # collar tie
    zc = zbase + (zr - zbase) * 0.52
    half = (zr - zc) / S_WING
    parts.append(box([xm - half, ys - 0.6, zc - 0.5], [xm + half, ys, zc + 0.3]))
    # king post with pendant
    parts.append(box([xm - 0.5, ys - 0.6, zc - 1.6], [xm + 0.5, ys, zr - 0.8]))
    parts.append(revolve([(0, 0), (0.55, 0), (0.7, 0.6), (0.3, 1.1), (0.45, 1.6), (0, 2.2)], 10)
                 .rotate([180, 0, 0]).translate([xm, ys - 0.3, zc - 1.6]))
    # sunburst spindles radiating from the collar tie centre
    for k in range(9):
        ang = math.radians(15 + 150 * k / 8)
        L = (zr - zc) * 0.9 / max(0.35, math.sin(ang) + 0.3 * abs(math.cos(ang)))
        dx, dz = math.cos(ang), math.sin(ang)
        pe = np.array([xm + dx * L, ys - 0.3, zc + dz * L])
        # stop at rake line
        parts.append(segment_bar([xm, ys - 0.3, zc + 0.3], pe, 0.5, 0.45, up=(0, -1, 0)))
    orn = union(parts)
    # clip to below the roof rake (polygon in x, z; extruded along y)
    clip = M.extrude(poly([(xm - (zr - zc) / S_WING - 2, zc - 12), (xm + (zr - zc) / S_WING + 2, zc - 12),
                           (xm + (zr - zc) / S_WING + 2, zc - 0.2 + 0), (xm, zr - 1.2), (xm - (zr - zc) / S_WING - 2, zc)]),
                     3).transform(frame_matrix([0, ys + 1.5, 0], [1, 0, 0], [0, 0, 1], [0, -1, 0]))
    add("trim", orn ^ clip)


def build_dormer():
    """Gabled dormer on the left (-x) plane of the main roof."""
    yc = ft(20.0)
    hw = ft(3.0)
    ovd = ft(0.7)
    sd = 1.25
    x_face = X0 + ft(2.0)
    z_m = ZE + S_MAIN * (x_face - (X0 - OV))       # main roof surface at the face
    z_base = z_m + 0.4
    hwall = ft(5.6)
    z_eave = z_base + hwall
    zr = z_eave + (hw + ovd) * sd
    depth = ft(13)
    planes = [Plane((0, yc - hw - ovd), (0, 1), z_eave, sd), Plane((0, yc + hw + ovd), (0, -1), z_eave, sd)]
    fp = [(x_face - ovd, yc - hw - ovd), (x_face + depth, yc - hw - ovd),
          (x_face + depth, yc + hw + ovd), (x_face - ovd, yc + hw + ovd)]
    # body (cheek walls), clipped under the dormer roof
    body = box([x_face + T + 0.2, yc - hw, z_base - 10], [x_face + depth, yc + hw, zr + 5])
    under = roof_solid(fp, [p.shifted(-1.0) for p in planes], z_base - 12)
    add("siding", body ^ under)
    # cheek shingles
    for (y0, y1) in ((yc - hw - 0.4, yc - hw), (yc + hw, yc + hw + 0.4)):
        add("shingle", box([x_face + 0.5, y0, z_base - 10], [x_face + depth, y1, zr + 5]) ^ under)
    # gable front wall
    zb = z_base - 4
    w = Wall((x_face, yc + hw), (x_face, yc - hw), zb)
    L = w.L
    v_e = z_eave + ovd * sd - 1.2 - zb - 0.2
    outline = poly([(0, 0), (L, 0), (L, v_e), (L / 2, v_e + hw * sd), (0, v_e)])
    op, parts = C.window(uc=L / 2, vb=4 + 1.0, w=ft(2.6), h=ft(4.0), lites="qa", head="plain", tex=0.42)
    add_parts(parts, w)
    add("siding", w.place(M.extrude(outline - op, T).translate([0, 0, -T])))
    add("shingle", w.place(shingle_rows(outline - op.offset(0.25) - rect(-1, -1, L + 1, 4.4),
                                        inch(5.5), inch(6.5), d=0.4, shape="fish", datum=4.4)))
    add("trim", w.place(box([-0.6, 0, -0.3], [CB, v_e, 0.75])))
    add("trim", w.place(box([L - CB, 0, -0.3], [L + 0.6, v_e, 0.75])))
    add("trim", w.place(box([-0.6, 3.6, -0.3], [L + 0.6, 4.4, 0.9])))
    # dormer roof
    faces = plane_faces(fp, planes)
    add("roof", roof_slab(fp, planes, 1.2, z_base - 5))
    add("roof", roof_texture(fp, planes, kind="random", e=inch(6.5), wtab=inch(10), d=0.34, seed=21, faces=faces))
    add("roof", segment_bar([x_face - ovd, yc, zr + 0.2], [x_face + depth, yc, zr + 0.2], 1.1, 0.8))
    for sgn in (-1, 1):
        p0 = np.array([x_face - ovd - 0.3, yc + sgn * (hw + ovd), z_eave - 0.5])
        p1 = np.array([x_face - ovd - 0.3, yc, zr - 0.4])
        add("trim", segment_bar(p0, p1, 0.8, 1.8, up=(-1, 0, 0)))
    add("metal", revolve([(0, 0), (0.6, 0), (0.6, 0.4), (0.3, 0.9), (0.45, 1.6), (0.1, 4.0), (0, 4.0)], 10)
        .translate([x_face - ovd, yc, zr + 0.4]))


def build_porch():
    depth = ft(8.0)
    xL = X0 - depth          # outer x of left leg
    yF = Y0 - depth          # outer y of front leg
    xR = WX0                 # front leg ends at wing
    yB = ft(24.0)            # left leg ends
    ch = ft(4.0)             # corner chamfer
    outline = [(xL + ch, yF), (xR, yF), (xR, Y0), (X0, Y0), (X0, yB), (xL, yB), (xL, yF + ch)]
    # deck
    add("porchfloor", prism(outline, ZP - 1.2, ZP - 0.12))
    boards = []
    x = xL
    while x < xR:
        boards.append(rect(x + 0.08, yF - 0.3, x + inch(3.5) - 0.08, yB + 1))
        x += inch(3.5)
    bcs = cs_union(boards) ^ poly(outline)
    add("porchfloor", M.extrude(bcs, 0.2).translate([0, 0, ZP - 0.2]))
    # skirt with lattice + piers along outer edges
    edges = [((xL, yB), (xL, yF + ch)), ((xL, yF + ch), (xL + ch, yF)), ((xL + ch, yF), (xR, yF))]
    post_pts = []
    for (a, b) in edges:
        a, b = np.array(a), np.array(b)
        w = Wall(a, b, 0)
        L = w.L
        # fascia / skirt board
        add("trim", w.place(box([0, ZP - 1.9, -0.2], [L, ZP - 0.1, 0.5])))
        add("trim", w.place(box([0, ZP - 0.4, 0.5], [L, ZP + 0.1, 1.1])))
        # lattice
        lat = []
        hgt = ZP - 1.9
        for k in range(-40, int(L / 1.6) + 40):
            u = k * 1.6
            lat.append(poly([(u, 0), (u + 0.45, 0), (u + 0.45 + hgt, hgt), (u + hgt, hgt)]))
            lat.append(poly([(u + hgt, 0), (u + hgt + 0.45, 0), (u + 0.45, hgt), (u, hgt)]))
        lcs = cs_union(lat) ^ rect(0, 0, L, hgt)
        add("trim", w.place(M.extrude(lcs, 0.5).translate([0, 0, -0.9])))
        add("shadow", w.place(box([0, 0, -2.5], [L, hgt, -2.2])))
        nposts = max(1, int(round(L / ft(7.5))))
        for k in range(nposts + 1):
            u = min(max(k * L / nposts, 0.9), L - 0.9)
            post_pts.append(tuple(np.round(w.world(u, 0, -0.9)[:2], 3)))
            # pier
            add("stone", w.place(box([u - 1.5, 0, -2.8], [u + 1.5, ZP - 1.9, 0.3])))
    # dedupe posts
    uniq = []
    for p in post_pts:
        if all(np.hypot(p[0] - q[0], p[1] - q[1]) > 2.5 for q in uniq):
            uniq.append(p)
    # add posts near wing and step openings
    ph = ft(8.4)
    for (x, y) in uniq:
        add("trim", C.turned_post(ph).translate([x, y, ZP]))
    # beam
    zb0 = ZP + ph
    for (a, b) in edges:
        a, b = np.array(a), np.array(b)
        w = Wall(a, b, 0)
        add("trim", w.place(box([-0.6, zb0 - 0.3, -2.2], [w.L + 0.6, zb0 + ft(1.1), 0.3])))
        add("accent", w.place(box([0.8, zb0 + 0.3, 0.3], [w.L - 0.8, zb0 + ft(1.1) - 0.5, 0.42])))
        # spindle frieze
        fr0 = zb0 - ft(1.3)
        add("trim", w.place(box([0, fr0 - 0.45, -1.3], [w.L, fr0, -0.5])))
        n = int(w.L / 1.25)
        for k in range(1, n):
            u = k * w.L / n
            sp = C.spindle(ft(1.3) - 0.3, 0.3)
            add("trim", w.place(sp.translate([0, 0, 0]).transform(
                frame_matrix([u, fr0, -0.9], [1, 0, 0], [0, 0, 1], [0, 1, 0]))))
        # balustrade
        rail_h = ft(2.6)
        z0 = ZP
        segs = [(0.9, w.L - 0.9)]
        if abs(a[1] - yF) < 1e-6 and abs(b[1] - yF) < 1e-6:
            # front leg: leave opening for steps at door
            sx = ft(13.0)
            u_c = (sx - a[0])
            segs = [(0.9, u_c - ft(3.1)), (u_c + ft(3.1), w.L - 0.9)]
        for (s0, s1) in segs:
            if s1 - s0 < 2:
                continue
            add("trim", w.place(box([s0, rail_h - 0.5, -1.3], [s1, rail_h, -0.3]).translate([0, ZP, 0])))
            add("trim", w.place(box([s0, 0.9, -1.2], [s1, 1.4, -0.4]).translate([0, ZP, 0])))
            nb = int((s1 - s0) / 1.22)
            for k in range(1, nb):
                u = s0 + (s1 - s0) * k / nb
                bal = C.spindle(rail_h - 1.9, 0.32)
                add("trim", w.place(bal.transform(frame_matrix([u, ZP + 1.4, -0.8], [1, 0, 0], [0, 0, 1], [0, 1, 0]))))
    # gingerbread brackets at posts, only where they run along the beam line
    band = poly(outline) - poly(outline).offset(-2.0, JoinType.Miter)
    for (x, y) in uniq:
        for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            bx = C.scroll_bracket(ft(1.4), ft(1.4), thick=0.5)
            ang = math.degrees(math.atan2(d[1], d[0]))
            bx = bx.rotate([0, 0, ang]).translate([x + d[0] * 0.9, y + d[1] * 0.9, zb0 - 0.3])
            cx, cy = x + d[0] * 3, y + d[1] * 3
            probe = rect(cx - 0.2, cy - 0.2, cx + 0.2, cy + 0.2)
            if (band ^ probe).area() > 0.1:
                add("trim", bx)
    # steps to front door
    sx = ft(13.0)
    nst = 3
    rise = ZP / (nst + 1)
    for k in range(nst + 1):
        z1 = ZP - rise * (k) - 0.1
        y0 = yF - ft(1.0) * k
        add("stone" if k == nst else "porchfloor",
            box([sx - ft(3.0), y0 - ft(1.0), 0], [sx + ft(3.0), y0 + 0.5, z1]))
    # step cheek walls
    for sgn in (-1, 1):
        add("trim", box([sx + sgn * ft(3.0) - 0.6, yF - ft(1.0) * (nst + 1), 0], [sx + sgn * ft(3.0) + 0.6, yF, ZP + 0.2]))
        add("trim", C.turned_post(ft(3.2), inch(8)).translate([sx + sgn * ft(3.0), yF - ft(1.0) * (nst + 1) + 1.2, ZP * 0.25 + 0.2]))

    # porch roof
    ov = ft(0.8)
    s = 0.36
    zeave = zb0 + ft(1.1)
    fpcs = poly(outline).offset(ov, JoinType.Miter) ^ rect(-1e3, -1e3, WX0, yB + ov)
    fpcs = fpcs - rect(X0 + 0.01, Y0 + 0.01, 1e3, 1e3)
    fp = [tuple(p) for p in fpcs.to_polygons()[0]]
    # planes pass through the outer edges at zeave
    nch = np.array([-1.0, -1.0]) / math.sqrt(2)
    planes = [Plane((0, yF), (0, 1), zeave, s), Plane((xL, 0), (1, 0), zeave, s),
              Plane(((xL + ch / 2), (yF + ch / 2)), -nch, zeave, s),
              Plane((0, yB), (0, -1), zeave, s)]
    faces = plane_faces(fp, planes)
    add("roof", roof_slab(fp, planes, 1.1, zeave - 5))
    add("roof", roof_texture(fp, planes, kind="random", e=inch(6), wtab=inch(9), d=0.3, seed=5, faces=faces))
    add("roof", roof_caps(fp, planes, width=1.0, height=0.7, faces=faces))
    # ceiling
    add("ceiling", prism([tuple(p) for p in poly(outline).to_polygons()[0]], zeave - 0.4, zeave - 0.1))


def build_chimneys():
    # exterior chimney on right wall
    y0, y1 = ft(22.0), ft(27.0)
    x0 = X1
    depth = ft(2.3)
    ridge = ZE + ((X1 - X0) / 2 + OV) * S_MAIN
    ztop = ridge + ft(1.0)
    # base (wide) up to shoulder, then stack
    zsh = Z2 + ft(3)
    def brick_box(xa, ya, xb, yb, za, zb):
        add("brick", box([xa, ya, za], [xb, yb, zb]))
        faces = [((xa, ya), (xb, ya)), ((xb, ya), (xb, yb)), ((xb, yb), (xa, yb)), ((xa, yb), (xa, ya))]
        for (p, q) in faces:
            w = Wall(p, q, za)
            add("brick", w.place(brickwork(rect(0, 0, w.L, zb - za), datum=-za)))
    brick_box(x0 - 1, y0, x0 + depth, y1, 0, zsh)
    # sloped shoulder
    sh = M.hull_points(np.array([[x0 - 1, y0, zsh], [x0 + depth, y0, zsh], [x0 + depth, y1, zsh], [x0 - 1, y1, zsh],
                                 [x0 - 1, y0 + ft(1), zsh + ft(2)], [x0 + depth - ft(0.6), y0 + ft(1), zsh + ft(2)],
                                 [x0 + depth - ft(0.6), y1 - ft(1), zsh + ft(2)], [x0 - 1, y1 - ft(1), zsh + ft(2)]]))
    add("stone", sh)
    brick_box(x0 - 1, y0 + ft(1), x0 + depth - ft(0.6), y1 - ft(1), zsh + ft(2) - 0.1, ztop)
    # corbelled cap
    cx0, cy0, cx1, cy1 = x0 - 1, y0 + ft(1), x0 + depth - ft(0.6), y1 - ft(1)
    for k, e in enumerate((0.4, 0.8, 1.2)):
        add("brick", box([cx0 - e, cy0 - e, ztop - ft(1.6) + k * 0.9], [cx1 + e, cy1 + e, ztop - ft(1.6) + (k + 1) * 0.9]))
    add("stone", box([cx0 - 0.9, cy0 - 0.9, ztop], [cx1 + 0.9, cy1 + 0.9, ztop + 0.6]))
    for yy in ((cy0 + cy1) / 2 - ft(0.8), (cy0 + cy1) / 2 + ft(0.8)):
        add("terracotta", revolve([(0, 0), (1.2, 0), (1.25, 1.0), (0.9, 2.5), (1.0, 3.2), (0.7, 3.2), (0.7, 0.5), (0, 0.5)], 16)
            .translate([(cx0 + cx1) / 2, yy, ztop + 0.6]))
    # interior chimney through back of main roof
    ix, iy = ft(9.0), ft(29.0)
    w_, d_ = ft(3.2), ft(2.2)
    brick_box(ix - w_ / 2, iy - d_ / 2, ix + w_ / 2, iy + d_ / 2, ZE, ztop - ft(0.5))
    zt = ztop - ft(0.5)
    for k, e in enumerate((0.4, 0.8)):
        add("brick", box([ix - w_ / 2 - e, iy - d_ / 2 - e, zt - ft(1.2) + k * 0.9], [ix + w_ / 2 + e, iy + d_ / 2 + e, zt - ft(1.2) + (k + 1) * 0.9]))
    add("stone", box([ix - w_ / 2 - 0.9, iy - d_ / 2 - 0.9, zt], [ix + w_ / 2 + 0.9, iy + d_ / 2 + 0.9, zt + 0.6]))
    for xx in (ix - ft(0.8), ix + ft(0.8)):
        add("terracotta", revolve([(0, 0), (1.1, 0), (1.15, 1.0), (0.85, 2.3), (0.95, 3.0), (0.65, 3.0), (0.65, 0.5), (0, 0.5)], 16)
            .translate([xx, iy, zt + 0.6]))


def build_extras():
    """Back stoop + door hood, downspouts, basement windows."""
    # ---- back stoop at W5 door (x = 15 ft)
    bx = ft(15.0)
    add("stone", box([bx - ft(3.2), Y1 + 1.0, 0], [bx + ft(3.2), Y1 + ft(4.0), ZF - 0.3]))
    add("porchfloor", box([bx - ft(3.0), Y1 + 1.0, ZF - 0.5], [bx + ft(3.0), Y1 + ft(3.8), ZF - 0.1]))
    for k in range(3):
        z1 = (ZF - 0.3) * (3 - k) / 4
        add("porchfloor", box([bx - ft(2.2), Y1 + ft(4.0) + k * ft(0.95), 0],
                              [bx + ft(2.2), Y1 + ft(4.0) + (k + 1) * ft(0.95), z1]))
    # door hood (shed roof on brackets)
    zh = ZF + ft(9.6)
    fp = [(bx - ft(3.3), Y1), (bx + ft(3.3), Y1), (bx + ft(3.3), Y1 + ft(3.2)), (bx - ft(3.3), Y1 + ft(3.2))]
    pl = [Plane((0, Y1 + ft(3.2)), (0, -1), zh, 0.55)]
    faces = plane_faces(fp, pl)
    add("roof", roof_slab(fp, pl, 1.0, zh - 4))
    add("roof", roof_texture(fp, pl, kind="random", e=inch(6), wtab=inch(9), d=0.3, seed=31, faces=faces))
    add("trim", box([bx - ft(3.3), Y1 + ft(3.2) - 0.1, zh - 1.6], [bx + ft(3.3), Y1 + ft(3.2) + 0.5, zh + 0.1]))
    for sx in (-1, 1):
        b = C.scroll_bracket(ft(2.6), ft(2.4), thick=0.8).rotate([0, 0, 90]).translate([bx + sx * ft(2.9), Y1, zh - 0.9])
        add("trim", b)
    # ---- downspouts at outside corners
    for (x, y, nx, ny) in ((X1, Y1, 1, 1), (X0, Y1, -1, 1), (X1, WY0, 1, -1)):
        px, py = x + nx * 1.6, y + ny * 1.6
        add("metal", cyl([px, py, 1.0], 0.5, ZE - 2.4 - 1.0, 10))
        add("metal", box([px - 0.8, py - 0.8, 0.2], [px + 0.8, py + 0.8, 1.2]))
        for zz in (ZF + ft(4), Z2 + ft(4)):
            add("metal", box([px - 0.25 - (0.9 if nx < 0 else 0), py - 0.25, zz], [px + 0.25 + (0.9 if nx > 0 else 0), py + 0.25, zz + 0.4]))
    # ---- basement windows (hopper) on right and back foundation
    def bwin(p0, p1, u):
        w = Wall(p0, p1, 0)
        wp = Wall(w.p0 + w.n * 1.0, w.p0 + w.n * 1.0 + w.u * w.L, 0)
        add("trim", wp.place(box([u - ft(1.3), ZF * 0.28, -0.6], [u + ft(1.3), ZF * 0.82, 0.55])))
        add("glass", wp.place(box([u - ft(1.3) + 0.5, ZF * 0.28 + 0.5, -0.6], [u + ft(1.3) - 0.5, ZF * 0.82 - 0.5, 0.62])))
        add("trim", wp.place(box([u - 0.12, ZF * 0.28 + 0.4, -0.6], [u + 0.12, ZF * 0.82 - 0.4, 0.7])))
    for u in (ft(9.0), ft(25.0), ft(36.0)):
        bwin((X1, WY0), (X1, Y1), u)
    for u in (ft(6.0), ft(24.0)):
        bwin((X1, Y1), (X0, Y1), u)
    for u in (ft(4.0), ft(12.0)):
        bwin((X0, Y1), (X0, Y0), u)


def export(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = {}
    stats = {}
    for mat, ms in PARTS.items():
        vs, fs = [], []
        off = 0
        for m in ms:
            mesh = m.to_mesh()
            v = np.asarray(mesh.vert_properties)[:, :3]
            f = np.asarray(mesh.tri_verts)
            if len(f) == 0:
                continue
            vs.append(v)
            fs.append(f + off)
            off += len(v)
        if not vs:
            continue
        data[mat + "__v"] = np.concatenate(vs).astype(np.float32)
        data[mat + "__f"] = np.concatenate(fs).astype(np.int32)
        stats[mat] = len(data[mat + "__f"])
    np.savez_compressed(path, **data)
    return stats


if __name__ == "__main__":
    t = time.time()
    build()
    st = export(os.path.join(OUT, "house_parts.npz"))
    print("tris per material:", st, "total", sum(st.values()))
    print("done in", round(time.time() - t, 1), "s")
