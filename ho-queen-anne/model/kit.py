"""Printable kit for the Beaumont (HO 1:87.1).

Splits the Rev A design into single-colour parts. Every part carries:
  * its solid in assembly coordinates (for renders and fit checks),
  * a colour name (from the Rev A render palette),
  * a print transform that lays it on the bed in its intended orientation,
  * a type key so identical parts can share one STL.

Joinery conventions (see KIT_PROGRESS.md):
  * cream trim sits in PK-deep pockets / on texture-free landings, so it
    self-aligns; pockets are made by subtracting a clearance "keep-out" of
    the trim from the parts it touches;
  * 1st-floor (Sage) and 2nd-floor (Gold) panels meet at Z2 under the cream
    belt loop, which is also the splice;
  * foundation ring, water-table ring and cornice ring square up the shell.
"""
import math
import os
import sys
import time
from collections import defaultdict

import numpy as np
from manifold3d import Manifold as M, CrossSection as CS, JoinType

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from geom import (ft, inch, box, union, cs_union, rect, poly, prism, revolve, frame_matrix,
                  Wall, clapboard, shingle_rows, stonework, brickwork, Plane, roof_slab,
                  roof_solid, plane_faces, roof_texture, roof_caps, segment_bar)
import components as C
import kit_parts as KP
from house import (ZF, Z2, ZE, ZP, OV, S_MAIN, S_WING, X0, X1, Y0, Y1, WX0, WY0,
                   TOWER_C, TOWER_A, TOWER_TOP, S_TOWER, tower_vertices)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out")

# ------------------------------------------------------------------ kit constants
T = 2.0                     # wall core thickness
PK = KP.PK                  # trim pocket depth
CLR = KP.CLR                # fit clearance per side
ZW = ZE - 2.2               # top of walls = underside of the cornice ring
RING_T = 0.8                # soffit thickness
DROP = ft(1.4)              # frieze depth below soffit
WT_H = 1.4                  # water-table ring height
BELT = [(0.8, -0.87, 3.15), (1.15, 3.15, 3.55), (0.95, -1.22, -0.87)]   # (w_out, v0, v1) about the floor line
BELT_LO, BELT_HI = 1.22, 3.55
CB = 2.6                    # corner board leg width
CB_T = 0.75                 # corner board thickness
TT = TOWER_TOP
TOWER_OV = ft(1.3)
RK = ft(1.0)                # rake overhang at the wing gable

COLORS = {
    "Sage": "#7f8f6a", "Harvest-Gold": "#c79a45", "Cream": "#efe7d2", "Oxblood": "#6a1f2b",
    "Walnut": "#4a2616", "Slate": "#43474d", "Fieldstone": "#8d877c", "Brick": "#8a3b2b",
    "Porch-Gray": "#6b706f", "Black-Iron": "#2b2b2d",
}
RENDER_MAT = {"Sage": "siding", "Harvest-Gold": "shingle", "Cream": "trim", "Oxblood": "sash",
              "Walnut": "door", "Slate": "roof", "Fieldstone": "stone", "Brick": "brick",
              "Porch-Gray": "porchfloor", "Black-Iron": "metal"}

# ------------------------------------------------------------------ print transforms
I34 = np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0]])
FLIP = np.array([[1.0, 0, 0, 0], [0, -1.0, 0, 0], [0, 0, -1.0, 0]])


def m4(A):
    B = np.eye(4)
    B[:3, :] = A
    return B


def compose(B, A):
    return (m4(B) @ m4(A))[:3, :]


def inv34(A):
    R = A[:, :3]
    t = A[:, 3]
    out = np.zeros((3, 4))
    out[:, :3] = R.T
    out[:, 3] = -R.T @ t
    return out


def wall_print(w, off):
    """World -> print for a part lying flat in wall w's frame, bed at w = -off."""
    L = np.array([[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, off]])
    return compose(L, inv34(w.A))


def rows_print(xr, yr, zr):
    """Print transform from three world direction rows (made right-handed)."""
    xr, yr, zr = (np.asarray(v, float) for v in (xr, yr, zr))
    R = np.array([xr, yr, zr])
    if np.linalg.det(R) < 0:
        R[1] = -R[1]
    out = np.zeros((3, 4))
    out[:, :3] = R
    return out


# ------------------------------------------------------------------ registry
class Part:
    def __init__(self, name, color, solid, P, key, group, note=""):
        self.name, self.color, self.solid, self.P = name, color, solid, P
        self.key, self.group, self.note = key, group, note

    def printed(self):
        s = self.solid.transform(self.P)
        b = s.bounding_box()
        return s.translate([-(b[0] + b[3]) / 2, -(b[1] + b[4]) / 2, -b[2]])


PARTS = []


def add(name, color, solid, P=None, key=None, group="", note=""):
    if solid is None or solid.is_empty():
        print("  (empty part skipped)", name)
        return None
    p = Part(name, color, solid, I34 if P is None else P, key or name, group, note)
    PARTS.append(p)
    return p


# ------------------------------------------------------------------ 2D footprints
def off(cs, d):
    return cs.offset(d, JoinType.Miter, 4.0)


def slab(cs, z0, z1):
    return M.extrude(cs, z1 - z0).translate([0, 0, z0])


MAIN_PTS = [(X0, Y0), (WX0, Y0), (WX0, WY0), (X1, WY0), (X1, Y1), (X0, Y1)]
MAIN = poly(MAIN_PTS)
OCT = poly([tuple(p) for p in tower_vertices(TOWER_A)])
BAY_CX = (WX0 + X1) / 2
BAY_PTS = [(BAY_CX - ft(5.0), WY0), (BAY_CX - ft(2.5), WY0 - ft(2.5)),
           (BAY_CX + ft(2.5), WY0 - ft(2.5)), (BAY_CX + ft(5.0), WY0)]
BAY = poly(BAY_PTS + [(BAY_CX + ft(5.0), WY0 + 3), (BAY_CX - ft(5.0), WY0 + 3)])
ALL = cs_union([MAIN, OCT, BAY])

# exterior chimney on the right wall
CH_Y0, CH_Y1 = ft(22.0), ft(27.0)
CH_D = ft(2.3)
CH_ZSH = Z2 + ft(3)
RIDGE_Z = ZE + ((X1 - X0) / 2 + OV) * S_MAIN
CH_TOP = RIDGE_Z + ft(1.0)
STACK = (X1 + CLR, CH_Y0 + ft(1), X1 + CH_D - ft(0.6), CH_Y1 - ft(1))   # x0, y0, x1, y1


def ch_notch(pad=0.2, full=False):
    """Plan-view slot cleared around the chimney in rings/foundation/roof."""
    if full:
        return rect(X1 - 0.05, CH_Y0 - pad, X1 + 30, CH_Y1 + pad)
    return rect(X1 - 0.05, STACK[1] - pad, X1 + 30, STACK[3] + pad)


# ------------------------------------------------------------------ keep-outs
KEEP_MAIN = []      # subtracted from main wall panels
KEEP_TOWER = []     # subtracted from tower tubes
KEEP_BAY = []       # subtracted from bay walls


def textures_for(w, region, kind, datum_v):
    if region.is_empty():
        return M()
    if kind == "clap":
        return clapboard(region, datum=datum_v)
    if kind == "fish":
        return shingle_rows(region, inch(5.5), inch(6.5), d=0.4, shape="fish", datum=datum_v)
    if kind == "hex":
        return shingle_rows(region, inch(5.5), inch(6), d=0.4, shape="hex", datum=datum_v)
    if kind == "stone":
        return stonework(region, seed=int(w.L * 10) % 97)
    if kind == "brick":
        return brickwork(region, datum=datum_v)
    raise ValueError(kind)


WIN_COUNT = defaultdict(int)


def window_set(host, w, spec, sash_T=T):
    """Adds casing + sash parts for one window. Returns (opening, pocket) CS in w-local."""
    uc, vb, ww, hh = spec["uc"], spec["vb"], spec["w"], spec["h"]
    head = spec.get("head", "cornice")
    lites = spec.get("lites", "2/2")
    opening, pocket, cas = KP.casing(uc, vb, ww, hh, head=head)
    sa = KP.sash(uc, vb, ww, hh, sash_T, lites=lites)
    WIN_COUNT[host] += 1
    n = WIN_COUNT[host]
    tkey = f"{ww / ft(1):.1f}x{hh / ft(1):.1f}"
    add(f"Cream__WIN-{host}-{n}-casing", "Cream", w.place(cas), wall_print(w, PK),
        key=f"Cream__casing-{tkey}-{head}", group="windows")
    add(f"Oxblood__WIN-{host}-{n}-sash", "Oxblood", w.place(sa), wall_print(w, sash_T + 2 * KP.LAYER),
        key=f"Oxblood__sash-{tkey}-{lites}", group="windows")
    return opening, pocket


def win(u, zsill, zb, wft, hft, lites="2/2", head="cornice"):
    return dict(uc=u, vb=zsill - zb, w=ft(wft), h=ft(hft), lites=lites, head=head)


def wall_panel(name, color, p0, p1, zb, outline, zones, tex_u, windows=(), doors=(),
               end_plane=None, datum=None, keep=None):
    """Flat-printed textured wall panel (exterior up)."""
    w = Wall(p0, p1, zb)
    holes, pockets = [], []
    for spec in windows:
        op, pk = window_set(name, w, spec)
        holes.append(op)
        pockets.append(pk)
    for spec in doors:
        op, pk = door_set(name, w, spec)
        holes.append(op)
        pockets.append(pk)
    hole = cs_union(holes)
    pocket = cs_union(pockets)
    core = M.extrude(outline - hole, T).translate([0, 0, -T])
    if not pocket.is_empty():
        core = core - M.extrude(pocket, PK + 0.05).translate([0, 0, -PK])
    texreg = outline ^ rect(tex_u[0], -50, tex_u[1], 500)
    texreg = texreg - hole.offset(0.2, JoinType.Miter) - pocket.offset(0.1, JoinType.Miter)
    tex = []
    for (a, b, kind) in zones:
        band = texreg ^ rect(-500, a, 1000, b)
        tex.append(textures_for(w, band, kind, (ZF - zb) if datum is None else datum))
    solid = union([core] + tex)
    if end_plane is not None:
        solid = solid.trim_by_plane(*end_plane)
    solid = w.place(solid)
    for k in (keep if keep is not None else KEEP_MAIN):
        solid = solid - k
    add(f"{color}__WALL-{name}", color, solid, wall_print(w, T), group="walls")
    return w


def door_set(host, w, spec):
    uc, vb, ww, hh = spec["uc"], spec["vb"], spec["w"], spec["h"]
    tr = spec.get("transom", ft(1.2))
    leaves = spec.get("leaves", 2)
    opening, pocket, cas = KP.door_casing(uc, vb, ww, hh + tr, pediment=spec.get("pediment", True),
                                          head_h=spec.get("head_h", ft(1.1)), ped_slope=spec.get("ped_slope", 0.45))
    ins = KP.door_insert(uc, vb, ww, hh, T, transom=tr, leaves=leaves)
    add(f"Cream__DOOR-{host}-casing", "Cream", w.place(cas), wall_print(w, PK), group="doors")
    add(f"Walnut__DOOR-{host}-door", "Walnut", w.place(ins), wall_print(w, T + 2 * KP.LAYER), group="doors")
    return opening, pocket


# ================================================================== build steps
def build_foundation():
    outer = off(ALL, 1.0)
    inner = off(ALL, -(T + 1.5))
    ring = slab(outer - inner, 0, ZF)
    lip_reg = off(ALL, -(T + CLR)) - inner
    lip_reg = lip_reg - (off(OCT, 0.5) - off(OCT, -T - CLR)) - rect(WX0 - 1, WY0 - 0.5, X1 + 1, WY0 + T + CLR)
    for (x0_, x1_, y0_, y1_) in DOOR_LIP_CUTS:
        lip_reg = lip_reg - rect(x0_, y0_, x1_, y1_)
    lip = slab(lip_reg, ZF - 0.01, ZF + 1.0)
    tex = []
    for loop in outer.to_polygons():
        pts = [tuple(p) for p in loop]
        # outer contour is counter-clockwise
        area = 0.5 * sum(pts[i][0] * pts[(i + 1) % len(pts)][1] - pts[(i + 1) % len(pts)][0] * pts[i][1]
                         for i in range(len(pts)))
        if area < 0:
            continue
        for i in range(len(pts)):
            a, b = np.array(pts[i]), np.array(pts[(i + 1) % len(pts)])
            if np.linalg.norm(b - a) < 1.0:
                continue
            fw = Wall(a, b, 0)
            tex.append(fw.place(stonework(rect(0.2, 0.15, fw.L - 0.2, ZF - 0.2), seed=int(fw.L * 7) % 91)))
    solid = union([ring, lip] + tex)
    # chimney base notch (outside the wall line)
    solid = solid - slab(ch_notch(0.2, full=True), -1, ZF + 2)
    # basement windows: recessed sash
    bw = []
    for (p0, p1, us) in (((X1, WY0), (X1, Y1), (ft(9.0), ft(38.0))),
                         ((X1, Y1), (X0, Y1), (ft(6.0), ft(24.0))),
                         ((X0, Y1), (X0, Y0), (ft(4.0), ft(12.0)))):
        w = Wall(p0, p1, 0)
        for u in us:
            cut = w.place(box([u - ft(1.3), ZF * 0.28, 0.35], [u + ft(1.3), ZF * 0.8, 3.0]))
            solid = solid - cut
            bw.append(w.place(box([u - 0.15, ZF * 0.28, 0.2], [u + 0.15, ZF * 0.8, 0.5])))
            bw.append(w.place(box([u - ft(1.3), ZF * 0.28 - 0.4, 0.2], [u + ft(1.3), ZF * 0.28, 1.4])))
    solid = union([solid] + bw)
    add("Fieldstone__FOUNDATION-ring", "Fieldstone", solid, group="foundation")
    # base plate (glued inside the bottom of the ring for stiffness)
    plate = slab(off(ALL, -(T + 1.5 + CLR)), 0, 1.2)
    add("Fieldstone__FOUNDATION-base-plate", "Fieldstone", plate, group="foundation")


DOOR_LIP_CUTS = [(ft(13.0) - ft(2.2) - 1.1, ft(13.0) + ft(2.2) + 1.1, T - 0.5, T + 2.0),
                 (X1 - ft(15.0) - ft(1.6) - 1.1, X1 - ft(15.0) + ft(1.6) + 1.1, Y1 - T - 2.0, Y1 - T + 0.5)]
DOOR_WT_CUTS = [(ft(13.0) - ft(2.2) - inch(6) - 0.8, ft(13.0) + ft(2.2) + inch(6) + 0.8, -3.0, 0.5),
                (X1 - ft(15.0) - ft(1.6) - inch(6) - 0.8, X1 - ft(15.0) + ft(1.6) + inch(6) + 0.8, Y1 - 0.5, Y1 + 3.0)]


def build_water_table():
    lo = off(ALL, 1.6) - ALL
    hi = off(ALL, 1.2) - ALL
    ring = union([slab(lo, ZF, ZF + 0.8), slab(hi, ZF + 0.8, ZF + WT_H)])
    ring = ring - slab(ch_notch(0.2, full=True), ZF - 1, ZF + 3)
    for (x0_, x1_, y0_, y1_) in DOOR_WT_CUTS:
        ring = ring - slab(rect(x0_, y0_, x1_, y1_), ZF - 1, ZF + 3)
    add("Cream__TRIM-water-table-ring", "Cream", ring, group="trim")
    k = slab(off(ALL, 3.0) - off(ALL, -0.01), ZF - 1, ZF + WT_H + CLR)
    KEEP_MAIN.append(k)
    KEEP_TOWER.append(k)
    KEEP_BAY.append(k)


def build_chimney():
    x0 = X1 + CLR
    parts = []

    def brick_box(xa, ya, xb, yb, za, zb, faces=(0, 1, 2)):
        parts.append(box([xa, ya, za], [xb, yb, zb]))
        sides = [((xa, ya), (xb, ya)), ((xb, ya), (xb, yb)), ((xb, yb), (xa, yb))]
        for i in faces:
            p, q = sides[i]
            wv = Wall(p, q, za)
            parts.append(wv.place(brickwork(rect(0.15, 0, wv.L - 0.15, zb - za), datum=-za)))

    brick_box(x0, CH_Y0, X1 + CH_D, CH_Y1, 0, CH_ZSH)
    sx0, sy0, sx1, sy1 = STACK
    parts.append(M.hull_points(np.array([
        [x0, CH_Y0, CH_ZSH - 0.01], [X1 + CH_D, CH_Y0, CH_ZSH - 0.01], [X1 + CH_D, CH_Y1, CH_ZSH - 0.01],
        [x0, CH_Y1, CH_ZSH - 0.01], [x0, sy0, CH_ZSH + ft(2)], [sx1, sy0, CH_ZSH + ft(2)],
        [sx1, sy1, CH_ZSH + ft(2)], [x0, sy1, CH_ZSH + ft(2)]])))
    brick_box(sx0, sy0, sx1, sy1, CH_ZSH + ft(2) - 0.05, CH_TOP)
    for k, e in enumerate((0.4, 0.8, 1.2)):
        parts.append(box([sx0, sy0 - e, CH_TOP - ft(1.6) + k * 0.9], [sx1 + e, sy1 + e, CH_TOP - ft(1.6) + (k + 1) * 0.9]))
    parts.append(box([sx0, sy0 - 0.9, CH_TOP], [sx1 + 0.9, sy1 + 0.9, CH_TOP + 0.6]))
    for yy in ((sy0 + sy1) / 2 - ft(0.8), (sy0 + sy1) / 2 + ft(0.8)):
        parts.append(revolve([(0, 0), (1.2, 0), (1.25, 1.0), (0.9, 2.5), (1.0, 3.2), (0.7, 3.2), (0.7, 0.5), (0, 0.5)], 16)
                     .translate([(sx0 + sx1) / 2, yy, CH_TOP + 0.6]))
    add("Brick__CHIMNEY-exterior", "Brick", union(parts), group="chimneys")
    k = union([box([X1 - 0.2, CH_Y0 - 0.35, -1], [X1 + CH_D + 2, CH_Y1 + 0.35, CH_ZSH + ft(2)]),
               box([X1 - 0.2, sy0 - 0.35, CH_ZSH], [sx1 + 2, sy1 + 0.35, CH_TOP])])
    KEEP_MAIN.append(k)


def belt_loop():
    parts = []
    for (wo, v0, v1) in BELT:
        reg = off(MAIN, wo) - off(MAIN, -PK)
        parts.append(slab(reg, Z2 + v0, Z2 + v1))
    loop = union(parts)
    loop = loop - slab(off(OCT, 1.2), 0, 200)
    loop = loop - slab(rect(X1 - 1.0, CH_Y0 - 0.35, X1 + 30, CH_Y1 + 0.35), 0, 200)
    pieces = loop.decompose()
    for i, pc in enumerate(sorted(pieces, key=lambda m: m.volume(), reverse=True)):
        add(f"Cream__TRIM-belt-loop-{i + 1}", "Cream", pc, group="trim")
    KEEP_MAIN.append(slab(off(MAIN, 3.0) - off(MAIN, -PK - CLR / 2), Z2 - BELT_LO - CLR, Z2 + BELT_HI + CLR))


def corner_boards():
    corners = [((WX0, Y0), (WX0, WY0), (X1, WY0)), ((WX0, WY0), (X1, WY0), (X1, Y1)),
               ((X1, WY0), (X1, Y1), (X0, Y1)), ((X1, Y1), (X0, Y1), (X0, Y0))]
    band = off(MAIN, CB_T) - MAIN
    kband = off(MAIN, 3.0) - off(MAIN, -0.01)
    for i, (pa, c, pb) in enumerate(corners):
        c = np.array(c)
        sq = rect(c[0] - CB, c[1] - CB, c[0] + CB, c[1] + CB)
        reg = band ^ sq
        d_in = (c - np.array(pa)) / np.linalg.norm(c - np.array(pa))
        n_in = np.array([d_in[1], -d_in[0]])
        for (lvl, z0, z1) in (("lower", ZF + WT_H + CLR, Z2 - BELT_LO - CLR),
                              ("upper", Z2 + BELT_HI + CLR, ZW - DROP - 0.45 - CLR)):
            s = slab(reg, z0, z1)
            P = rows_print([0, 0, 1], [d_in[0], d_in[1], 0], [-n_in[0], -n_in[1], 0])
            add(f"Cream__TRIM-corner-board-{i + 1}-{lvl}", "Cream", s, P, key="Cream__corner-board-" + lvl, group="trim")
        KEEP_MAIN.append(slab(kband ^ rect(c[0] - CB - CLR, c[1] - CB - CLR, c[0] + CB + CLR, c[1] + CB + CLR),
                              ZF, ZW))


def cornice_main():
    """Soffit ring + frieze skirt + brackets, printed upside down."""
    fp_main = rect(X0 - OV, Y0 - OV, X1 + OV, Y1 + OV)
    fp_wing = rect(WX0 - OV, WY0 - RK, X1 + OV, Y0)
    fp = fp_main + fp_wing
    soff = fp - off(MAIN, -T) - rect(WX0 - 0.01, WY0 - RK - 5, X1 + 0.01, WY0 + T + CLR)
    soff = soff - off(OCT, CLR) - ch_notch(0.2)
    parts = [slab(soff, ZW, ZW + RING_T)]
    skirt_cut = cs_union([rect(WX0 - 0.01, WY0 - 20, X1 + 0.01, WY0 + 0.01), off(OCT, 0.9), ch_notch(0.2)])
    parts.append(slab(off(MAIN, 0.7) - MAIN - skirt_cut, ZW - DROP, ZW + 0.01))
    parts.append(slab(off(MAIN, 1.0) - MAIN - skirt_cut, ZW - DROP - 0.45, ZW - DROP))
    # paired brackets along each eave wall
    walls = [((X0, Y0), (WX0, Y0), ft(9.6), None), ((WX0, Y0), (WX0, WY0), 0, None),
             ((X1, WY0), (X1, Y1), 0, (CH_Y0 - WY0 - 3, CH_Y1 - WY0 + 3)),
             ((X1, Y1), (X0, Y1), 0, None), ((X0, Y1), (X0, Y0), 0, (Y1 - ft(6.5), 1e9))]
    for (p0, p1, u0, skip) in walls:
        w = Wall(p0, p1, 0)
        u1 = w.L
        n = max(1, int(round((u1 - u0 - ft(2)) / ft(4.0))))
        for k in range(n + 1):
            uu = u0 + ft(1.0) + (u1 - u0 - ft(2.0)) * k / n
            if skip and skip[0] <= uu <= skip[1]:
                continue
            for du in (-0.55, 0.55):
                b = C.eave_bracket(ft(1.2), DROP * 1.05, thick=0.7).transform(
                    frame_matrix([uu + du, ZW + 0.01, 0.69], [0, 0, 1], [1, 0, 0], [0, 1, 0]))
                parts.append(w.place(b))
    ring = union(parts)
    add("Cream__CORNICE-main-ring", "Cream", ring, FLIP, group="cornice")
    KEEP_MAIN.append(slab(off(MAIN, 6.0) - off(MAIN, -0.01) - rect(WX0 + 0.01, WY0 - 20, X1 - 0.01, WY0 - 0.01),
                          ZW - DROP - 0.45 - CLR, ZW + 0.01))
    return soff


def main_walls():
    H1_ = Z2 - ZF
    H2_ = ZW - Z2
    lower = [(0, H1_ + 1, "clap")]
    upper = [(-1, 200, "fish")]
    s1 = ZF + ft(2.4)
    s2 = Z2 + ft(2.0)
    L = lambda a, b: float(np.linalg.norm(np.array(b) - np.array(a)))
    tr = TOWER_C[0] + TOWER_A            # tower right face (x)
    # W6 end against tower back-left face: y = x + (tower line offset)
    ang = math.radians(135)
    nrm = np.array([math.cos(ang), math.sin(ang)])
    fc = TOWER_C + nrm * TOWER_A           # face centre; face line is y - x = const
    k6 = fc[1] - fc[0]
    u6_ext = Y1 - k6
    u6_int = Y1 - (k6 + T)
    # the end plane in W6-local coords passes through (u6_ext, w=0) and (u6_int, w=-T); keep u smaller side
    nplane = np.array([-(T), 0.0, (u6_ext - u6_int)])
    nplane = nplane / np.linalg.norm(nplane)
    end6 = (list(nplane), float(nplane @ np.array([u6_ext, 0, 0])))

    specs = {
        "W1": ((X0, Y0), (WX0, Y0), (tr, L((X0, Y0), (WX0, Y0)) + T), (tr + 0.5, L((X0, Y0), (WX0, Y0)))),
        "W2": ((WX0, Y0), (WX0, WY0), (0, -WY0 - T), (0.5, -WY0 - CB - 0.05)),
        "W3": ((WX0, WY0), (X1, WY0), (0, X1 - WX0 - T), (CB + 0.05, X1 - WX0 - CB - 0.05)),
        "W4": ((X1, WY0), (X1, Y1), (0, Y1 - WY0 - T), (CB + 0.05, Y1 - WY0 - CB - 0.05)),
        "W5": ((X1, Y1), (X0, Y1), (0, X1 - X0 - T), (CB + 0.05, X1 - X0 - CB - 0.05)),
        "W6": ((X0, Y1), (X0, Y0), (0, u6_ext + 1), (CB + 0.05, u6_ext - 0.6)),
    }
    wins_lower = {
        "W4": [(3.0, "2/2"), (14.0, "2/2"), (39.0, "2/2")],
        "W5": [(5.0, "2/2"), (24.0, "2/2")],
        "W6": [(8.0, "2/2"), (21.0, "qa"), (29.5, "2/2")],
    }
    wins_upper = {
        "W1": [(13.0, 2.6, 5.2, "2/2")],
        "W2": [(3.0, 2.4, 5.2, "2/2")],
        "W4": [(3.0, 2.6, 5.2, "2/2"), (14.0, 2.6, 5.2, "2/2"), (39.0, 2.6, 5.2, "2/2")],
        "W5": [(5.0, 2.6, 5.2, "2/2"), (15.0, 2.4, 4.4, "2/2"), (24.0, 2.6, 5.2, "2/2")],
        "W6": [(8.0, 2.6, 5.2, "2/2"), (21.0, 2.6, 5.2, "2/2"), (29.5, 2.6, 5.2, "2/2")],
    }
    _tower_abutments(tr, k6)
    for name, (p0, p1, (ua, ub), tex_u) in specs.items():
        # ---------------- lower (Sage)
        wl = [win(ft(u), s1, ZF, 2.8, 6.2, lites) for (u, lites) in wins_lower.get(name, [])]
        doors = []
        if name == "W1":
            doors = [dict(uc=ft(13.0), vb=0.0, w=ft(4.4), h=ft(7.0), transom=ft(1.2), leaves=2, pediment=True,
                          head_h=0.0, ped_slope=0.3)]
        if name == "W5":
            doors = [dict(uc=ft(15.0), vb=0.0, w=ft(3.2), h=ft(7.0), transom=ft(1.0), leaves=1, pediment=False,
                          head_h=ft(0.8))]
        wall_panel(name + "-lower", "Sage", p0, p1, ZF, rect(ua, 0, ub, H1_), lower, tex_u, windows=wl,
                   doors=doors, end_plane=end6 if name == "W6" else None)
        # ---------------- upper (Gold)
        wu = [win(ft(u), s2, Z2, wf, hf, lites) for (u, wf, hf, lites) in wins_upper.get(name, [])]
        outline = rect(ua, 0, ub, H2_)
        zones = upper
        if name == "W3":
            L3 = X1 - WX0
            v_e = ZE + OV * S_WING - 1.4 - Z2 - 0.1
            outline = poly([(ua, 0), (ub, 0), (ub, v_e + (L3 - ub) * S_WING if ub > L3 / 2 else v_e),
                            (L3 / 2, v_e + L3 / 2 * S_WING), (ua, v_e)])
            gz = ZE + OV * S_WING - 1.0 - Z2
            zones = [(-1, gz - 0.4, "fish"), (gz + 1.2, 200, "hex")]
            wu = [win(L3 / 2 - ft(2.0), s2, Z2, 2.4, 5.2, "qa"), win(L3 / 2 + ft(2.0), s2, Z2, 2.4, 5.2, "qa"),
                  win(L3 / 2, ZE + OV * S_WING + ft(0.7), Z2, 2.0, 2.6, "2/2", "plain")]
        w = wall_panel(name + "-upper", "Harvest-Gold", p0, p1, Z2, outline, zones, tex_u, windows=wu,
                       end_plane=end6 if name == "W6" else None, datum=0.0)
        if name == "W3":
            gz = ZE + OV * S_WING - 1.0 - Z2
            band = union([box([ua, gz - 0.4, -PK], [ub, gz + 1.2, 0.85]),
                          box([ua - 0.2, gz + 1.2, -PK], [ub + 0.2, gz + 1.6, 1.2])])
            band = band ^ M.extrude(outline.offset(-0.05, JoinType.Miter), 10).translate([0, 0, -5])
            add("Cream__TRIM-gable-band", "Cream", w.place(band), wall_print(w, PK), group="trim")
            # pocket for the gable band
            gp = w.place(box([ua - 1, gz - 0.4 - CLR, -PK - 0.05], [ub + 1, gz + 1.6 + CLR, 3]))
            for p in PARTS:
                if p.name == "Harvest-Gold__WALL-W3-upper":
                    p.solid = p.solid - gp


def _tower_abutments(tr, k6):
    KEEP_TOWER.append(slab(rect(tr - 0.5, -CLR, tr + 3.0, T + CLR), ZF - 1, ZW + 1))
    KEEP_TOWER.append(slab(poly([(-CLR, k6 - CLR - 0.05), (T + CLR, k6 + T + CLR - 0.05),
                                 (T + CLR, k6 + 15), (-CLR, k6 + 15)]), ZF - 1, ZW + 1))


def tower_faces():
    tv = tower_vertices(TOWER_A)
    return [Wall(tv[k], tv[(k + 1) % 8], 0) for k in range(8)]


def tower_rings():
    for (zc, nm) in ((Z2, "z2"), (ZE, "ze")):
        parts = [slab(off(OCT, wo) - OCT, zc + v0, zc + v1) for (wo, v0, v1) in BELT]
        ring = union(parts)
        if nm == "z2":
            ring = ring - slab(MAIN, 0, 300)
        add(f"Cream__TOWER-belt-ring-{nm}", "Cream", ring, group="tower")
        KEEP_TOWER.append(slab(off(OCT, 3.0) - off(OCT, -0.01), zc - BELT_LO - CLR, zc + BELT_HI + CLR))
    # cornice ring (upside down)
    zr = TT - 1.3 - RING_T
    drop = ft(1.6)
    parts = [slab(off(OCT, TOWER_OV) - off(OCT, -T), zr, zr + RING_T),
             slab(off(OCT, 0.7) - OCT, zr - drop, zr + 0.01),
             slab(off(OCT, 1.0) - OCT, zr - drop - 0.45, zr - drop)]
    for k, w in enumerate(tower_faces()):
        if k in (2, 3, 4):
            continue
        for uu in (ft(1.0), w.L - ft(1.0)):
            for du in (-0.55, 0.55):
                b = C.eave_bracket(ft(1.0), drop * 1.05, thick=0.7).transform(
                    frame_matrix([uu + du, zr + 0.01, 0.69], [0, 0, 1], [1, 0, 0], [0, 1, 0]))
                parts.append(w.place(b))
    add("Cream__TOWER-cornice-ring", "Cream", union(parts), FLIP, group="tower")
    KEEP_TOWER.append(slab(off(OCT, 3.0) - off(OCT, -0.01), zr - drop - 0.45 - CLR, zr + 0.01))
    # main cornice soffit + main roof passing the tower
    KEEP_TOWER.append(slab(off(OCT, 3.0) - off(OCT, -0.01), ZW - 0.6, ZE + BELT_HI + CLR))


def tower_tube(name, color, z0, z1, zones, windows_by_face, datum):
    tube = slab(OCT - off(OCT, -T), z0, z1)
    faces = tower_faces()
    tv = tower_vertices(TOWER_A)
    holes = []
    tex = []
    for k, w0 in enumerate(faces):
        w = Wall(tv[k], tv[(k + 1) % 8], z0)
        hs, pks = [], []
        for spec in windows_by_face.get(k, []):
            op, pk = window_set(f"tower-{name}-f{k}", w, spec)
            hs.append(op)
            pks.append(pk)
        hole = cs_union(hs)
        pocket = cs_union(pks)
        if not hole.is_empty():
            holes.append(w.place(M.extrude(hole, T + 2).translate([0, 0, -T - 1])))
        if not pocket.is_empty():
            holes.append(w.place(M.extrude(pocket, PK + 0.05).translate([0, 0, -PK])))
        reg = rect(0.15, 0, w.L - 0.15, z1 - z0) - hole.offset(0.2, JoinType.Miter) - pocket.offset(0.1, JoinType.Miter)
        for (a, b, kind) in zones:
            band = reg ^ rect(-5, a - z0, w.L + 5, b - z0)
            tex.append(w.place(textures_for(w, band, kind, datum - z0)))
    solid = union([tube] + tex)
    for h in holes:
        solid = solid - h
    for k in KEEP_TOWER:
        solid = solid - k
    add(f"{color}__TOWER-{name}", color, solid, group="tower")


def build_tower():
    tower_rings()
    s1 = ZF + ft(2.4)
    lower_w = {k: [win(0, ZF + ft(2.2), ZF, 2.5, 6.0, "qa" if k == 0 else "2/2")] for k in (0, 1, 6, 7)}
    faces = tower_faces()
    for k in lower_w:
        lower_w[k][0]["uc"] = faces[k].L / 2
    tower_tube("lower", "Sage", ZF, Z2, [(ZF, Z2 + 1, "clap")], lower_w, ZF)
    upper_w = {}
    for k in (0, 1, 6, 7):
        upper_w.setdefault(k, []).append(win(faces[k].L / 2, Z2 + ft(2.0), Z2, 2.4, 5.2))
    for k in (0, 1, 6, 7):
        upper_w.setdefault(k, []).append(win(faces[k].L / 2, ZE + ft(2.4), Z2, 2.2, 4.0))
    tower_tube("upper", "Harvest-Gold", Z2, TT - 1.3 - RING_T,
               [(Z2 - 1, ZE, "fish"), (ZE, TT + 5, "hex")], upper_w, Z2 + 1.0)
    # spire
    ov = TOWER_OV
    planes = []
    for k in range(8):
        ang = math.radians(-90 + 45 * k)
        nrm = np.array([math.cos(ang), math.sin(ang)])
        planes.append(Plane(TOWER_C + nrm * (TOWER_A + ov), -nrm, TT, S_TOWER))
    fp = [tuple(p) for p in tower_vertices(TOWER_A + ov)]
    faces_ = plane_faces(fp, planes)
    sp = [roof_slab(fp, planes, 1.3, TT - 1.3),
          roof_texture(fp, planes, kind="fish", e=inch(7), wtab=inch(7.5), d=0.4, faces=faces_),
          roof_caps(fp, planes, width=1.0, height=0.8, faces=faces_)]
    outer = roof_solid(fp, planes, TT - 1.3)
    fl = slab(poly(fp) - off(poly(fp), -1.8), TT - 1.3, TT - 0.6) ^ outer
    sp.append(fl)
    apex = TT + (TOWER_A + ov) * S_TOWER
    sp.append(revolve([(0, 0), (1.4, 0), (1.4, 0.6), (0.7, 1.2), (1.0, 2.0), (0.6, 2.8),
                       (0.6, 4.5), (1.2, 5.3), (0.6, 6.1), (0.45, 9.5), (1.0, 10.3), (0.4, 11.2),
                       (0.3, 14.0), (0, 14.0)], 16).translate([TOWER_C[0], TOWER_C[1], apex - 2.5]))
    add("Slate__ROOF-tower-spire", "Slate", union(sp), group="roofs")


def roof_main():
    ov = OV
    fp = [(X0 - ov, Y0 - ov), (X1 + ov, Y0 - ov), (X1 + ov, Y1 + ov), (X0 - ov, Y1 + ov)]
    planes = [Plane((0, Y0 - ov), (0, 1), ZE, S_MAIN), Plane((X1 + ov, 0), (-1, 0), ZE, S_MAIN),
              Plane((0, Y1 + ov), (0, -1), ZE, S_MAIN), Plane((X0 - ov, 0), (1, 0), ZE, S_MAIN)]
    faces = plane_faces(fp, planes)
    parts = [roof_slab(fp, planes, 1.4, ZE - 1.4),
             roof_texture(fp, planes, kind="random", e=inch(6.5), wtab=inch(10), d=0.36, faces=faces),
             roof_caps(fp, planes, faces=faces)]
    outer = roof_solid(fp, planes, ZE - 1.4)
    wfp = [(WX0 - OV, WY0 - RK), (X1 + OV, WY0 - RK), (X1 + OV, ft(10)), (WX0, ft(10)), (WX0, Y0), (WX0 - OV, Y0 - OV)]
    wpl = [Plane((WX0 - OV, 0), (1, 0), ZE, S_WING), Plane((X1 + OV, 0), (-1, 0), ZE, S_WING)]
    wfaces = plane_faces(wfp, wpl)
    parts += [roof_slab(wfp, wpl, 1.4, ZE - 1.4),
              roof_texture(wfp, wpl, kind="random", e=inch(6.5), wtab=inch(10), d=0.36, seed=11, faces=wfaces)]
    xm = (WX0 + X1) / 2
    zr = ZE + ((X1 - WX0) / 2 + OV) * S_WING
    parts.append(segment_bar([xm, WY0 - RK, zr + 0.3], [xm, ft(5.5), zr + 0.3], 1.2, 0.9))
    outer = outer + roof_solid(wfp, wpl, ZE - 1.4)
    # eave flange (sits on the cornice ring)
    soff = cornice_soffit_region()
    allfp = poly(fp) + poly(wfp)
    fl = slab(soff ^ (allfp - off(allfp, -2.2)), ZE - 1.4, ZE - 0.8) ^ outer
    parts.append(fl)
    roof = union(parts)
    # cut-outs: tower, tower eave, chimneys
    roof = roof - slab(off(OCT, 1.25), 0, 400)
    roof = roof - slab(ch_notch(0.2), 0, 400)
    roof = roof - slab(ICH_RECT.offset(CLR + 0.3, JoinType.Miter), 0, 400)
    add("Slate__ROOF-main", "Slate", roof, group="roofs")
    ROOF_PLANES["main"] = (fp, planes)
    # the tower's spire eave and cornice ring die into the main roof at the back
    below = roof_solid(fp, [p.shifted(0.45) for p in planes], 0)
    for p in PARTS:
        if p.name in ("Slate__ROOF-tower-spire", "Cream__TOWER-cornice-ring"):
            p.solid = p.solid - below


ROOF_PLANES = {}
ICH = (ft(9.0), ft(29.0), ft(3.2), ft(2.2))
ICH_RECT = rect(ICH[0] - ICH[2] / 2, ICH[1] - ICH[3] / 2, ICH[0] + ICH[2] / 2, ICH[1] + ICH[3] / 2)


def cornice_soffit_region():
    fp_main = rect(X0 - OV, Y0 - OV, X1 + OV, Y1 + OV)
    fp_wing = rect(WX0 - OV, WY0 - RK, X1 + OV, Y0)
    soff = (fp_main + fp_wing) - off(MAIN, -T) - rect(WX0 - 0.01, WY0 - RK - 5, X1 + 0.01, WY0 + T + CLR)
    return soff - off(OCT, CLR) - ch_notch(0.2)


def interior_chimney():
    fp, planes = ROOF_PLANES["main"]
    cx, cy, w_, d_ = ICH
    corners = [(cx + sx * w_ / 2, cy + sy * d_ / 2) for sx in (-1, 1) for sy in (-1, 1)]
    zmin = min(min(p.z(*c) for p in planes) for c in corners)
    zt = CH_TOP - ft(0.5)
    parts = [box([cx - w_ / 2, cy - d_ / 2, zmin - 3.0], [cx + w_ / 2, cy + d_ / 2, zt])]
    for (p, q) in (((cx - w_ / 2, cy - d_ / 2), (cx + w_ / 2, cy - d_ / 2)), ((cx + w_ / 2, cy - d_ / 2), (cx + w_ / 2, cy + d_ / 2)),
                   ((cx + w_ / 2, cy + d_ / 2), (cx - w_ / 2, cy + d_ / 2)), ((cx - w_ / 2, cy + d_ / 2), (cx - w_ / 2, cy - d_ / 2))):
        wv = Wall(p, q, zmin - 3.0)
        parts.append(wv.place(brickwork(rect(0.1, 0, wv.L - 0.1, zt - zmin + 3.0), datum=-(zmin - 3.0))))
    for k, e in enumerate((0.4, 0.8)):
        parts.append(box([cx - w_ / 2 - e, cy - d_ / 2 - e, zt - ft(1.2) + k * 0.9], [cx + w_ / 2 + e, cy + d_ / 2 + e, zt - ft(1.2) + (k + 1) * 0.9]))
    parts.append(box([cx - w_ / 2 - 0.9, cy - d_ / 2 - 0.9, zt], [cx + w_ / 2 + 0.9, cy + d_ / 2 + 0.9, zt + 0.6]))
    for xx in (cx - ft(0.8), cx + ft(0.8)):
        parts.append(revolve([(0, 0), (1.1, 0), (1.15, 1.0), (0.85, 2.3), (0.95, 3.0), (0.65, 3.0), (0.65, 0.5), (0, 0.5)], 16)
                     .translate([xx, cy, zt + 0.6]))
    add("Brick__CHIMNEY-interior-stack", "Brick", union(parts), group="chimneys")


def gable_trim():
    """Bargeboards + sunburst ornament, one flat cream part in front of the roof edge."""
    xm = (WX0 + X1) / 2
    zr = ZE + ((X1 - WX0) / 2 + OV) * S_WING
    y1 = WY0 - RK - CLR
    y0 = y1 - 0.8
    # rake boards: in (x, z) plane
    parts2d = []
    for sgn in (-1, 1):
        xe = xm + sgn * ((X1 - WX0) / 2 + OV)
        a = np.array([xe, ZE - 0.2])
        b = np.array([xm, zr - 0.2])
        d = (b - a) / np.linalg.norm(b - a)
        nrm = np.array([-d[1], d[0]])
        if nrm[1] > 0:
            nrm = -nrm
        pts = [a + nrm * 0.0 + d * 0.0, b, b + nrm * 2.4, a + nrm * 2.4]
        parts2d.append(poly([tuple(p) for p in pts]))
    zbase = ZE + OV * S_WING - 1.0
    zc = zbase + (zr - zbase) * 0.52
    half = (zr - zc) / S_WING
    parts2d.append(rect(xm - half, zc - 0.6, xm + half, zc + 0.3))
    parts2d.append(rect(xm - 0.55, zc - 1.6, xm + 0.55, zr - 0.8))
    parts2d.append(poly([(xm - 0.7, zc - 1.6), (xm + 0.7, zc - 1.6), (xm, zc - 3.6)]))
    for k in range(9):
        ang = math.radians(15 + 150 * k / 8)
        Lr = (zr - zc) * 1.4
        a = np.array([xm, zc + 0.3])
        b = a + Lr * np.array([math.cos(ang), math.sin(ang)])
        d = (b - a) / np.linalg.norm(b - a)
        nr = np.array([-d[1], d[0]]) * 0.3
        parts2d.append(poly([tuple(a - nr), tuple(b - nr), tuple(b + nr), tuple(a + nr)]))
    # keep ornament below the rake boards' upper edge
    clip = poly([(xm - (X1 - WX0) / 2 - OV - 1, ZE - 3), (xm + (X1 - WX0) / 2 + OV + 1, ZE - 3),
                 (xm, zr + 2.0)])
    inner = poly([(xm - (X1 - WX0) / 2, zbase - 5), (xm + (X1 - WX0) / 2, zbase - 5), (xm, zr - 1.2)])
    orn = cs_union(parts2d[2:]) ^ inner ^ rect(xm - 100, zc - 4, xm + 100, 400)
    shape = cs_union(parts2d[:2] + [orn]) ^ clip
    solid = M.extrude(shape, 0.8).transform(frame_matrix([0, y1, 0], [1, 0, 0], [0, 0, 1], [0, -1, 0]))
    P = rows_print([1, 0, 0], [0, 0, 1], [0, -1, 0])
    add("Cream__GABLE-bargeboards-and-sunburst", "Cream", solid, P, group="trim")


def cresting():
    xc = (X0 + X1) / 2
    ry0, ry1 = Y0 + (X1 - X0) / 2, Y1 - (X1 - X0) / 2
    z0 = RIDGE_Z + 1.0
    sh = [rect(ry0, z0, ry1, z0 + 0.5), rect(ry0, z0 + 2.4, ry1, z0 + 2.8)]
    n = int((ry1 - ry0) / 1.4)
    for k in range(n + 1):
        yy = ry0 + (ry1 - ry0) * k / n
        sh.append(rect(yy - 0.25, z0, yy + 0.25, z0 + 3.4))
        sh.append(poly([(yy - 0.45, z0 + 3.4), (yy + 0.45, z0 + 3.4), (yy, z0 + 4.2)]))
    for yy in (ry0, ry1):
        sh.append(rect(yy - 0.5, z0, yy + 0.5, z0 + 5.5))
        sh.append(CS.circle(0.9, 12).translate((yy, z0 + 6.2)))
        sh.append(poly([(yy - 0.3, z0 + 6.8), (yy + 0.3, z0 + 6.8), (yy, z0 + 8.6)]))
    shape = cs_union(sh)
    solid = M.extrude(shape, 0.7).transform(frame_matrix([xc - 0.35, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0]))
    P = rows_print([0, 1, 0], [0, 0, 1], [1, 0, 0])
    add("Black-Iron__ROOF-ridge-cresting", "Black-Iron", solid, P, group="roofs")


def build_bay():
    zt = ZF + ft(10.0)
    parts = []
    tex = []
    holes = []
    walls = []
    for i in range(3):
        a, b = np.array(BAY_PTS[i]), np.array(BAY_PTS[i + 1])
        w = Wall(a, b, ZF)
        walls.append(w)
        parts.append(w.place(box([0, 0, -T], [w.L, zt - ZF, 0])))
        wide = 3.2 if i == 1 else 2.0
        spec = win(w.L / 2, ZF + ft(2.2), ZF, wide, 5.6, "qa" if i == 1 else "2/2", "plain")
        op, pk = window_set(f"bay-{i + 1}", w, spec)
        holes.append(w.place(M.extrude(op, T + 2).translate([0, 0, -T - 1])))
        holes.append(w.place(M.extrude(pk, PK + 0.05).translate([0, 0, -PK])))
        reg = rect(0.3, 0, w.L - 0.3, zt - ZF) - op.offset(0.2, JoinType.Miter) - pk.offset(0.1, JoinType.Miter)
        tex.append(w.place(clapboard(reg, datum=0.0)))
    solid = union(parts + tex)
    for h in holes:
        solid = solid - h
    solid = solid - slab(rect(-1000, WY0 - 0.45, 1000, 1000), 0, 400)
    # cornice ring (upside down)
    ov = ft(0.8)
    drop = ft(1.4)
    back = rect(-1000, WY0 - 1.2, 1000, 1000)
    soff = off(BAY, ov) - off(BAY, -T) - back
    ring = [slab(soff, zt, zt + RING_T), slab(off(BAY, 0.7) - BAY - back, zt - drop, zt + 0.01),
            slab(off(BAY, 1.0) - BAY - back, zt - drop - 0.45, zt - drop)]
    for w in walls:
        n = max(1, int(round((w.L - ft(1.5)) / ft(3.0))))
        for k in range(n + 1):
            uu = ft(0.75) + (w.L - ft(1.5)) * k / n
            bb = C.eave_bracket(ft(0.8), drop * 1.05, thick=0.6).transform(
                frame_matrix([uu, zt - ZF + 0.01, 0.69], [0, 0, 1], [1, 0, 0], [0, 1, 0]))
            ring.append(w.place(bb))
    add("Cream__BAY-cornice-ring", "Cream", union(ring), FLIP, group="bay")
    clipb = slab(rect(-1000, WY0 - 0.45, 1000, 1000), -10, 400)
    for p in PARTS:
        if p.name.startswith(("Cream__WIN-bay", "Oxblood__WIN-bay")):
            p.solid = p.solid - clipb
    kb = slab(off(BAY, 3.0) - off(BAY, -0.01), zt - drop - 0.45 - CLR, zt + 0.01)
    for k in KEEP_BAY + [kb]:
        solid = solid - k
    add("Sage__BAY-walls", "Sage", solid, group="bay")
    # roof
    zr0 = zt + RING_T
    planes = []
    for w in walls:
        edge = w.p0 + w.n * ov
        planes.append(Plane(edge, -w.n, zr0 + 1.0, 0.6))
    fpcs = off(BAY, ov) - back
    fp = [tuple(p) for p in fpcs.to_polygons()[0]]
    faces = plane_faces(fp, planes)
    rp = [roof_slab(fp, planes, 1.0, zr0),
          roof_texture(fp, planes, kind="random", e=inch(6), wtab=inch(9), d=0.3, faces=faces),
          roof_caps(fp, planes, width=0.9, height=0.7, faces=faces)]
    outer = roof_solid(fp, planes, zr0)
    rp.append(slab(fpcs - off(fpcs, -1.5) - off(poly([(-1000, WY0 - 3.5), (1000, WY0 - 3.5), (1000, 1000), (-1000, 1000)]), 0),
                   zr0, zr0 + 0.55) ^ outer)
    add("Slate__ROOF-bay", "Slate", union(rp), group="roofs")


def build_dormer():
    yc = ft(20.0)
    hw = ft(3.0)
    ovd = ft(0.7)
    sd = 1.25
    x_face = X0 + ft(2.0)
    main_left = Plane((X0 - OV, 0), (1, 0), ZE, S_MAIN)
    z_m = main_left.z(x_face, yc)
    z_base = z_m + 0.65
    hwall = ft(5.6)
    z_eave = z_base + hwall
    zr = z_eave + (hw + ovd) * sd
    depth = ft(13)
    planes = [Plane((0, yc - hw - ovd), (0, 1), z_eave, sd), Plane((0, yc + hw + ovd), (0, -1), z_eave, sd)]
    fp = [(x_face - ovd, yc - hw - ovd), (x_face + depth, yc - hw - ovd),
          (x_face + depth, yc + hw + ovd), (x_face - ovd, yc + hw + ovd)]
    under = roof_solid(fp, [p.shifted(-1.2 - CLR) for p in planes], z_base - 30)
    above_roof = roof_solid([(x_face - 5, yc - 30), (x_face + 60, yc - 30), (x_face + 60, yc + 30), (x_face - 5, yc + 30)],
                            [main_left.shifted(0.65)], -100)
    # box: front wall + two cheeks (Gold, printed upright)
    box_ = box([x_face, yc - hw, z_base], [x_face + depth, yc + hw, zr + 5])
    hollow = box([x_face + T, yc - hw + T, z_base - 1], [x_face + depth + 1, yc + hw - T, zr + 6])
    body = ((box_ - hollow) ^ under) - above_roof
    w = Wall((x_face, yc + hw), (x_face, yc - hw), z_base)
    spec = dict(uc=w.L / 2, vb=4.0, w=ft(2.6), h=ft(3.6), lites="qa", head="plain")
    op, pk = window_set("dormer", w, spec)
    body = body - w.place(M.extrude(op, T + 2).translate([0, 0, -T - 1]))
    body = body - w.place(M.extrude(pk, PK + 0.05).translate([0, 0, -PK]))
    face_reg = rect(0.2, 0, w.L - 0.2, 60) - op.offset(0.2, JoinType.Miter) - pk.offset(0.1, JoinType.Miter)
    tex = w.place(shingle_rows(face_reg, inch(5.5), inch(6.5), d=0.4, shape="fish", datum=0.0)) ^ under
    add("Harvest-Gold__DORMER-box", "Harvest-Gold", body + tex, group="dormer")
    # roof (Slate, upright), trimmed by the main roof surface
    faces = plane_faces(fp, planes)
    rp = [roof_slab(fp, planes, 1.2, z_eave - 1.2),
          roof_texture(fp, planes, kind="random", e=inch(6.5), wtab=inch(10), d=0.34, seed=21, faces=faces),
          segment_bar([x_face - ovd, yc, zr + 0.2], [x_face + depth, yc, zr + 0.2], 1.1, 0.8),
          revolve([(0, 0), (0.7, 0), (0.7, 0.4), (0.35, 0.9), (0.5, 1.6), (0.25, 4.0), (0, 4.0)], 10)
          .translate([x_face - ovd + 0.3, yc, zr + 0.4])]
    droof = union(rp)
    droof = droof - roof_solid([(x_face - 20, yc - 40), (x_face + 80, yc - 40), (x_face + 80, yc + 40), (x_face - 20, yc + 40)],
                               [main_left.shifted(0.65)], -100)
    add("Slate__ROOF-dormer", "Slate", droof, group="roofs")
    # bargeboards (one inverted-V part, flat)
    xb = x_face - ovd - CLR
    pts = []
    sh = []
    for sgn in (-1, 1):
        a = np.array([yc + sgn * (hw + ovd), z_eave - 1.2])
        b = np.array([yc, zr - 0.3])
        d = (b - a) / np.linalg.norm(b - a)
        nrm = np.array([-d[1], d[0]])
        if nrm[1] > 0:
            nrm = -nrm
        sh.append(poly([tuple(a), tuple(b), tuple(b + nrm * 1.8), tuple(a + nrm * 1.8)]))
    shape = cs_union(sh)
    solid = M.extrude(shape, 0.8).transform(frame_matrix([xb, 0, 0], [0, 1, 0], [0, 0, 1], [-1, 0, 0]))
    add("Cream__DORMER-bargeboards", "Cream", solid, rows_print([0, 1, 0], [0, 0, 1], [-1, 0, 0]), group="dormer")


# ------------------------------------------------------------------ porch
PORCH_DEPTH = ft(8.0)
PXL, PYF = X0 - PORCH_DEPTH, Y0 - PORCH_DEPTH
PXR, PYB = WX0, ft(24.0)
PCH = ft(4.0)
POST_H = ft(8.4)
POST_S = inch(7) / 2
S_PORCH = 0.36
PORCH_OUT = [(PXL + PCH, PYF), (PXR, PYF), (PXR, Y0), (X0, Y0), (X0, PYB), (PXL, PYB), (PXL, PYF + PCH)]
STEP_X = ft(13.0)


def post_2d(h, s):
    """Silhouette of a turned post (for flat-backed printing)."""
    r = s * 0.8
    prof = [(r * 0.95, h * 0.2 - 0.01), (r * 1.05, h * 0.23), (r * 0.72, h * 0.26), (r * 0.66, h * 0.30),
            (r * 0.92, h * 0.34), (r * 0.66, h * 0.38), (r * 0.6, h * 0.55), (r * 0.66, h * 0.70),
            (r * 0.92, h * 0.74), (r * 0.66, h * 0.78), (r * 0.72, h * 0.82), (r * 1.05, h * 0.845),
            (r * 0.95, h * 0.861)]
    right = [(x, z) for (x, z) in prof]
    left = [(-x, z) for (x, z) in reversed(prof)]
    return prof, poly(right + left)


def flat_post(u, h, s, wb):
    """Turned post at u, back face at wb (w), full round front, flat back."""
    prof, sil = post_2d(h, s)
    base = box([u - s, 0, wb], [u + s, h * 0.2, wb + 2 * s])
    cap = box([u - s, h * 0.86, wb], [u + s, h, wb + 2 * s])
    shaft = revolve([(0, h * 0.2 - 0.01)] + prof + [(0, h * 0.861)], 16)
    # revolve is about z; map (x, y, z) -> (u, v, w): axis along v at (u, wb + s)
    shaft = shaft.transform(frame_matrix([u, 0, wb + s], [1, 0, 0], [0, 0, -1], [0, 1, 0]))
    front = shaft.trim_by_plane([0, 0, 1], wb + s)
    back = M.extrude(sil.translate((u, 0)), s).translate([0, 0, wb])
    return union([base, cap, front, back])


def baluster_2d(u, v0, v1, wmax=0.95, wmin=0.62):
    h = v1 - v0
    prof = [(wmax / 2, 0), (wmax / 2, h * 0.12), (wmin / 2, h * 0.22), (wmin / 2 * 0.9, h * 0.5),
            (wmin / 2, h * 0.78), (wmax / 2, h * 0.88), (wmax / 2, h)]
    right = [(u + x, v0 + z) for (x, z) in prof]
    left = [(u - x, v0 + z) for (x, z) in reversed(prof)]
    return poly(right + left)


def scroll_2d(corner, a, b, sgn):
    """Gingerbread bracket silhouette; corner at post/beam junction, reaches sgn*a along u, b down."""
    pts = [(0, 0), (a, 0), (a, -0.6)]
    seg = 10
    for k in range(seg + 1):
        t = k / seg
        ang = t * math.pi / 2
        pts.append((0.6 + (a - 0.6) * (1 - math.sin(ang)), -0.6 - (b - 0.6) * (1 - math.cos(ang))))
    pts.append((0, -b))
    sh = poly([(corner[0] + sgn * x, corner[1] + z) for (x, z) in pts])
    hole = CS.circle(min(a, b) * 0.17, 10).translate((corner[0] + sgn * a * 0.3, corner[1] - b * 0.3))
    return sh - hole


def porch_front(name, p0, p1, posts, ua, ub, gaps=(), beam_ext=(0.0, 0.0)):
    w = Wall(p0, p1, ZP)
    s = POST_S
    wb = -0.9 - s
    h = POST_H
    parts = []
    for u in posts:
        parts.append(flat_post(u, h, s, wb))
    beam = box([ua - beam_ext[0], h - 0.3, wb], [ub + beam_ext[1], h + ft(1.1), 0.3])
    beam = beam - box([ua + 0.8, h + 0.6, 0.18], [ub - 0.8, h + ft(1.1) - 0.6, 0.31])
    parts.append(beam)
    # spans between posts / ends
    stops = sorted(set([ua] + list(posts) + [ub]))
    rail_h = ft(2.6)
    fr0 = h - ft(1.3)
    sh = []
    for a, b in zip(stops[:-1], stops[1:]):
        a0 = a + (s if a in posts else 0.0)
        b0 = b - (s if b in posts else 0.0)
        if b0 - a0 < 1.0:
            continue
        # spindle frieze
        sh.append(rect(a0, fr0 - 0.5, b0, fr0))
        n = max(1, int((b0 - a0) / 1.35))
        for k in range(1, n):
            uu = a0 + (b0 - a0) * k / n
            sh.append(baluster_2d(uu, fr0, h - 0.3, 0.9, 0.62))
        # balustrade unless in a gap
        if any(g0 <= (a0 + b0) / 2 <= g1 for (g0, g1) in gaps):
            continue
        sh.append(rect(a0, 0.9, b0, 1.5))
        sh.append(rect(a0, rail_h - 0.6, b0, rail_h))
        n = max(1, int((b0 - a0) / 1.3))
        for k in range(1, n):
            uu = a0 + (b0 - a0) * k / n
            sh.append(baluster_2d(uu, 1.5, rail_h - 0.6))
    for u in posts:
        for sgn in (-1, 1):
            c = (u + sgn * s, h - 0.3)
            if not (ua + 1 < c[0] + sgn * 4 < ub - 1):
                continue
            sh.append(scroll_2d(c, ft(1.3), ft(1.3), sgn))
    parts.append(M.extrude(cs_union(sh), 0.8).translate([0, 0, wb]))
    solid = w.place(union(parts))
    add(f"Cream__PORCH-{name}", "Cream", solid, wall_print(w, -wb), group="porch")
    return w


def _miter_plane(d_in, d_out, V):
    m = np.array([d_in[0] + d_out[0], d_in[1] + d_out[1], 0.0])
    m /= np.linalg.norm(m)
    return m, float(m @ np.array([V[0], V[1], 0.0]))


def miter_porch(EL, EC, EF):
    dirs = []
    for (a, b) in (EL, EC, EF):
        d = np.array(b) - np.array(a)
        dirs.append(d / np.linalg.norm(d))
    m1, o1 = _miter_plane(dirs[0], dirs[1], EL[1])
    m2, o2 = _miter_plane(dirs[1], dirs[2], EC[1])
    for p in PARTS:
        if p.name == "Cream__PORCH-front-left-leg":
            p.solid = p.solid.trim_by_plane(list(-m1), -o1 - 0.03)
        elif p.name == "Cream__PORCH-front-corner":
            p.solid = p.solid.trim_by_plane(list(m1), o1 + 0.03).trim_by_plane(list(-m2), -o2 - 0.03)
        elif p.name == "Cream__PORCH-front-main":
            p.solid = p.solid.trim_by_plane(list(m2), o2 + 0.03)


def build_porch():
    outline = poly(PORCH_OUT)
    base_fp = outline - off(ALL, 1.55)
    top = ZP - 1.2
    base = slab(base_fp, 0, top)
    # lattice relief on the outer faces
    edges = [((PXL, PYB), (PXL, PYF + PCH)), ((PXL, PYF + PCH), (PXL + PCH, PYF)), ((PXL + PCH, PYF), (PXR, PYF)),
             ((X0, PYB), (PXL, PYB))]
    lat_parts, cuts = [], []
    for (a, b) in edges:
        w = Wall(a, b, 0)
        L = w.L
        field = rect(0.8, 0.8, L - 0.8, top - 1.3)
        cuts.append(w.place(M.extrude(field, 0.8).translate([0, 0, -0.8])))
        lat = []
        for k in range(-20, int(L / 1.8) + 20):
            u = k * 1.8
            hh = top
            lat.append(poly([(u, 0), (u + 0.6, 0), (u + 0.6 + hh, hh), (u + hh, hh)]))
            lat.append(poly([(u + hh, 0), (u + hh + 0.6, 0), (u + 0.6, hh), (u, hh)]))
        lcs = cs_union(lat) ^ field
        lat_parts.append(w.place(M.extrude(lcs, 0.6).translate([0, 0, -0.8])))
    base = union([base - union(cuts)] + [lp ^ slab(base_fp, -1, top + 1) for lp in lat_parts])
    add("Cream__PORCH-base-lattice", "Cream", base, group="porch")
    # deck (Porch Gray, flat)
    deck_fp = off(base_fp, 0.4) ^ off(outline, 0.4) - off(ALL, 1.5)
    deck = slab(deck_fp, top, ZP - 0.2)
    boards = []
    x = PXL - 1
    while x < PXR + 1:
        boards.append(rect(x + 0.08, PYF - 2, x + inch(3.5) - 0.08, PYB + 2))
        x += inch(3.5)
    deck = deck + slab(cs_union(boards) ^ deck_fp, ZP - 0.2, ZP)
    add("Porch-Gray__PORCH-deck", "Porch-Gray", deck, group="porch")
    # fronts
    s = POST_S
    EL = ((PXL, PYB), (PXL, PYF + PCH))
    EC = ((PXL, PYF + PCH), (PXL + PCH, PYF))
    EF = ((PXL + PCH, PYF), (PXR, PYF))
    lenL = PYB - (PYF + PCH)
    lenC = math.hypot(PCH, PCH)
    lenF = PXR - (PXL + PCH)
    postsL = [s + 0.9, lenL * 0.25, lenL * 0.5, lenL * 0.75]
    ustep = STEP_X - (PXL + PCH)
    gap = (ustep - ft(3.1), ustep + ft(3.1))
    postsF = [ft(6.3), gap[0] - s, gap[1] + s]
    porch_front("front-left-leg", *EL, postsL, 0.0, lenL + 3.0, beam_ext=(0.0, 0.0))
    porch_front("front-corner", *EC, [s + 0.9, lenC - s - 0.9], 0.0, lenC)
    porch_front("front-main", *EF, postsF, -3.0, lenF, gaps=[gap])
    miter_porch(EL, EC, EF)
    # end frame at the back of the left leg, from the corner post to the house wall
    Lr = (X0 - 1.75) - (PXL + 0.9 + s)
    porch_front("end-return", (X0 - 1.75, PYB), (PXL + 0.9 + s, PYB), [], 0.0, Lr - 0.05)
    # piers (stone) glued over the lattice at posts
    for i, (a, b, posts) in enumerate(((EL[0], EL[1], postsL), (EF[0], EF[1], postsF))):
        w = Wall(a, b, 0)
        for j, u in enumerate(posts):
            pr = box([u - 1.6, 0.4, 0.0], [u + 1.6, top - 1.0, 0.6])
            add(f"Fieldstone__PORCH-pier-{i + 1}-{j + 1}", "Fieldstone", w.place(pr), wall_print(w, 0.0),
                key="Fieldstone__porch-pier", group="porch")
    # steps
    nst = 3
    rise = ZP / (nst + 1)
    sp = []
    for k in range(nst + 1):
        z1 = ZP - rise * k - 0.15
        y0 = PYF - ft(1.0) * k
        sp.append(box([STEP_X - ft(3.0) + 0.7, y0 - ft(1.0), 0], [STEP_X + ft(3.0) - 0.7, y0 - 0.9 if k == 0 else y0 + 0.01, z1]))
    add("Porch-Gray__PORCH-front-steps", "Porch-Gray", union(sp), group="porch")
    for sgn in (-1, 1):
        xw = STEP_X + sgn * ft(3.0)
        yb, yf = PYF - 0.9, PYF - ft(1.0) * (nst + 1)
        # cheek wall with a flat-backed newel at the front, printed on its side
        prof = poly([(yf, 0), (yb, 0), (yb, ZP + 0.2), (yf + 2.5, rise * 1.2 + 1.0), (yf, rise * 1.2 + 1.0)])
        wall_ = M.extrude(prof, 1.2)
        newel = box([yf, rise * 1.2 + 1.0 - 0.01, 0], [yf + 2.4, rise * 1.2 + 1.0 + 8.0, 2.4])
        newel = newel + box([yf - 0.3, rise * 1.2 + 9.0, 0], [yf + 2.7, rise * 1.2 + 9.8, 2.4])
        solid = (wall_ + newel)
        # local (y, z, t) -> world: x = xw - sgn*0.6 + sgn * t ... inner face on the steps side
        if sgn < 0:
            A = frame_matrix([xw + 0.6, 0, 0], [0, 1, 0], [0, 0, 1], [-1, 0, 0])
        else:
            A = frame_matrix([xw - 0.6, 0, 0], [0, 1, 0], [0, 0, 1], [1, 0, 0])
        solid = solid.transform(A)
        P = compose(np.eye(4)[:3], inv34(A))
        add(f"Cream__PORCH-step-cheek-{'L' if sgn < 0 else 'R'}", "Cream", solid, P, group="porch")
    # porch roof
    ov = ft(0.8)
    beam_top = ZP + POST_H + ft(1.1)
    zr_edge = beam_top + 1.1 + S_PORCH * 0.3
    nch = np.array([-1.0, -1.0]) / math.sqrt(2)
    planes = [Plane((0, PYF), (0, 1), zr_edge, S_PORCH), Plane((PXL, 0), (1, 0), zr_edge, S_PORCH),
              Plane((PXL + PCH / 2, PYF + PCH / 2), -nch, zr_edge, S_PORCH),
              Plane((0, PYB), (0, -1), zr_edge, S_PORCH)]
    fpcs = off(outline, ov) - off(ALL, 1.2) - rect(WX0 - 1.2, -1000, 1000, 1000)
    fpcs = fpcs - off(OCT, 1.25)
    fp_ = [tuple(p) for p in max(fpcs.to_polygons(), key=lambda l: poly(l).area())]
    faces = plane_faces(fp_, planes)
    z_lo = zr_edge - S_PORCH * ov - 1.1
    rp = [roof_slab(fp_, planes, 1.1, z_lo),
          roof_texture(fp_, planes, kind="random", e=inch(6), wtab=inch(9), d=0.3, seed=5, faces=faces),
          roof_caps(fp_, planes, width=1.0, height=0.7, faces=faces)]
    outer = roof_solid(fp_, planes, z_lo)
    rp.append(slab(off(outline, ov) - off(outline, ov - 1.5) - off(ALL, 3.0), z_lo, z_lo + 0.55) ^ outer)
    roof = union(rp) - slab(off(OCT, 1.25), 0, 400)
    add("Slate__ROOF-porch", "Slate", roof, group="roofs")


def build_back():
    bx = ft(15.0)
    y0 = Y1 + 1.5
    sp = [box([bx - ft(3.2), y0, 0], [bx + ft(3.2), Y1 + ft(4.0), ZF - 0.3])]
    for k in range(3):
        z1 = (ZF - 0.3) * (3 - k) / 4
        sp.append(box([bx - ft(2.2), Y1 + ft(4.0) - 0.01, 0], [bx + ft(2.2), Y1 + ft(4.0) + (k + 1) * ft(0.95), z1]))
    add("Porch-Gray__BACK-stoop-and-steps", "Porch-Gray", union(sp), group="back")
    zh = ZF + ft(9.6)
    fp = [(bx - ft(3.3), Y1 + 1.2), (bx + ft(3.3), Y1 + 1.2), (bx + ft(3.3), Y1 + ft(3.2)), (bx - ft(3.3), Y1 + ft(3.2))]
    pl = [Plane((0, Y1 + ft(3.2)), (0, -1), zh, 0.55)]
    faces = plane_faces(fp, pl)
    hood = union([roof_slab(fp, pl, 1.0, zh - 1.0),
                  roof_texture(fp, pl, kind="random", e=inch(6), wtab=inch(9), d=0.3, seed=31, faces=faces),
                  box([bx - ft(3.3), Y1 + ft(3.2) - 0.8, zh - 1.6], [bx + ft(3.3), Y1 + ft(3.2), zh - 0.9])])
    add("Slate__ROOF-back-door-hood", "Slate", hood, group="back")
    z_under = zh + 0.55 * (ft(3.2) - 1.3) - 1.0 - 0.05
    for sx in (-1, 1):
        sh = scroll_2d((0, 0), ft(2.4), ft(2.4), 1).transform(np.array([[1.0, 0, 0], [-0.55, 1.0, 0]]))
        A = frame_matrix([bx + sx * ft(2.9) - 0.4, Y1 + 1.2 + CLR, z_under], [0, 1, 0], [0, 0, 1], [1, 0, 0])
        b = M.extrude(sh, 0.8).transform(A)
        add(f"Cream__BACK-hood-bracket-{'L' if sx < 0 else 'R'}", "Cream", b, compose(np.eye(4)[:3], inv34(A)),
            key="Cream__back-hood-bracket", group="back")


def downspouts():
    spots = [((X1, Y1), (1, 1)), ((X0, Y1), (-1, 1)), ((X1, WY0), (1, -1))]
    for i, (c, (sx, sy)) in enumerate(spots):
        px, py = c[0] + sx * 2.25, c[1] + sy * 2.25
        parts = [box([px - 0.55, py - 0.55, 0.3], [px + 0.55, py + 0.55, ZW - 0.05]),
                 box([px - 0.8, py - 0.8, 0.0], [px + 0.8, py + 0.8, 1.2])]
        for zz in (ZF + ft(4), Z2 + ft(6)):
            parts.append(box([min(px, c[0] + sx * 0.8), py - 0.55, zz], [max(px, c[0] + sx * 0.8), py + 0.55, zz + 0.5]))
        solid = union(parts)
        P = rows_print([0, 0, 1], [1, 0, 0], [0, 1, 0])
        add(f"Black-Iron__DOWNSPOUT-{i + 1}", "Black-Iron", solid, P, key="Black-Iron__downspout", group="small")


# ================================================================== driver
def build():
    t0 = time.time()
    steps = [build_foundation, build_water_table, build_chimney, belt_loop, corner_boards, cornice_main,
             main_walls, build_tower, build_bay, roof_main, interior_chimney,
             gable_trim, cresting, build_dormer, build_porch, build_back, downspouts]
    for fn in steps:
        fn()
        print(f"{fn.__name__:22s} {time.time() - t0:6.1f}s  parts={len(PARTS)}")


def export_assembly(path):
    groups = defaultdict(list)
    for p in PARTS:
        groups[RENDER_MAT[p.color]].append(p.solid)
    data = {}
    for mat, ms in groups.items():
        vs, fs, off_ = [], [], 0
        for m in ms:
            mesh = m.to_mesh()
            v = np.asarray(mesh.vert_properties)[:, :3]
            f = np.asarray(mesh.tri_verts)
            vs.append(v)
            fs.append(f + off_)
            off_ += len(v)
        data[mat + "__v"] = np.concatenate(vs).astype(np.float32)
        data[mat + "__f"] = np.concatenate(fs).astype(np.int32)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    np.savez_compressed(path, **data)


if __name__ == "__main__":
    build()
    export_assembly(os.path.join(OUT, "kit_assembly.npz"))
    print("parts:", len(PARTS))
