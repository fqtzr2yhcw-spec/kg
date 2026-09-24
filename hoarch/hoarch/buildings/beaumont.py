"""The Beaumont, Rev C: the HO (1:87.1) Queen Anne rebuilt on the hoarch method.

The Rev A design (octagonal corner tower with a tall spire, a front gable wing with a
canted bay, a dormer, a wraparound porch with a chamfered corner) built the way the Ashby
villa is built:

- one upright shell per storey with belt rings between; the tower's third storey is its
  own shell on its own ring;
- clapboard below and fish-scale shingles on the upright second-floor shell, where the
  scallops are drawn by the layers;
- banded slate roofs and a fish-scale spire, all printed upright;
- a turned porch (round posts and railings printed upright, sawn-work arcade on edge);
- Queen Anne sashes (a big light ringed by small ones) and separate finials;
- every detail at nozzle-safe sizes, with flat faces on the 0.2 mm layer grid.

usage: python3 -m hoarch.buildings.beaumont [check] [export] [views]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch import features as FT, openings as O, roof as R
from hoarch.core import (Facade, box, clapboard, compose, cs_union, frame, inv34, offset, poly, rect, scallop_rows,
                         slab, union)
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext, finial
from hoarch.shell import Block, Opening, foundation, lip_keep, stacked_shells

NAME = "Beaumont Queen Anne Rev C"
COLORS = {"Sage": "#7F8F6A", "Gold": "#C79A45", "Cream": "#EFE7D2", "Oxblood": "#5A1A24", "Slate": "#43474D",
          "Walnut": "#4A2616", "Brick": "#8A3B2B", "Fieldstone": "#8D877C", "PorchGray": "#6B706F"}
RENDER_MAT = {"Sage": "siding", "Gold": "shingle", "Cream": "trim", "Oxblood": "sash", "Slate": "roof",
              "Walnut": "door", "Brick": "brick", "Fieldstone": "stone", "PorchGray": "porchfloor"}
PALETTE = {"siding": ["#7f8f6a", 0.62, 0.0], "shingle": ["#c79a45", 0.6, 0.0], "trim": ["#efe7d2", 0.55, 0.0],
           "sash": ["#5a1a24", 0.45, 0.0], "roof": ["#43474d", 0.8, 0.0], "door": ["#4a2616", 0.45, 0.0],
           "brick": ["#8a3b2b", 0.85, 0.0], "stone": ["#8d877c", 0.9, 0.0], "porchfloor": ["#6b706f", 0.7, 0.0]}

# ------------------------------------------------------------------ levels (all on the 0.2 mm grid)
ZF = 10.4                 # first floor / foundation top
S1 = ZF + 38.4            # first-floor shell top = belt ring bottom
RH = 4.4                  # belt ring height
ZE = S1 + RH + 34.0       # main eave (second-floor shell top)
TT = ZF + 115.6           # tower wall top
V1, V2, V3 = 8.0, 46.2, 85.2          # sill heights above ZF: first, second, tower third storey

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 105.0, 133.0
WX0, WY0 = 59.6, -21.0                 # front gable wing
MAIN = Block("main", [(0, 0), (WX0, 0), (WX0, WY0), (X1, WY0), (X1, Y1), (0, Y1)], ZF, ZE)
TC, TA = (12.2, 3.5), 19.2             # tower centre and apothem


def oct_pts(c, a):
    R_ = a / math.cos(math.radians(22.5))
    return [(c[0] + R_ * math.cos(math.radians(-112.5 + 45 * k)), c[1] + R_ * math.sin(math.radians(-112.5 + 45 * k)))
            for k in range(8)]


TOWER = Block("tower", oct_pts(TC, TA), ZF, TT)
BAY = Block("bay", [(64.8, WY0), (73.6, WY0 - 8.8), (91.0, WY0 - 8.8), (99.8, WY0), (99.8, WY0 + 3.0),
                    (64.8, WY0 + 3.0)], ZF, ZF + 28.4)
BLOCKS = [MAIN, TOWER, BAY]
TOWER_FACES = (7, 0, 1, 6)             # the tower faces that stand clear of the house

# eave: a frieze with paired brackets, a boxed soffit and a fascia (heights on the grid from the top)
CORNICE_QA = [(-4.4, 0), (0.9, 0), (0.9, 3.6), (1.3, 3.8), (5.0, 3.8), (5.0, 5.0), (5.4, 5.2), (5.4, 6.0), (-4.4, 6.0)]
EAVE_H, EAVE_D = 6.0, 5.4
S_MAIN, S_WING, S_SPIRE = 1.15, 1.0, 3.0
SLATE = ("square", "square", "square", "fish", "fish")        # banded courses
SPIRE_SLATE = ("fish", "fish", "diamond", "diamond")


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    # first floor: segmental pediments with sunbursts over shaped aprons; second floor:
    # scroll hoods with volutes over bracketed sills; ornate Queen Anne entrances
    lo = O.window_insert(9.8, 20.2, rise=0, style="pediment", apron=True)
    lo_qa = O.window_insert(9.8, 20.2, rise=0, style="pediment", apron=True, qa=True)
    up = O.window_insert(9.1, 18.2, rise=0, style="scroll")
    up_qa = O.window_insert(8.4, 18.2, rise=0, style="scroll", qa=True)
    small = O.window_insert(8.4, 15.4, rise=0, style="scroll")
    tk = dict(casing=0.8, ends=0.2, sill_ext=0.3, clip=True)
    tw1 = O.window_insert(8.4, 20.2, rise=0, style="pediment", apron=True, qa=True, **tk)
    tw2 = O.window_insert(8.4, 18.2, rise=0, style="scroll", **tk)
    tw3 = O.window_insert(7.6, 14.0, rise=None, style="scroll", **tk)
    bay_s = O.window_insert(7.6, 18.2, rise=0, style="blocks", apron=True, **tk)
    bay_f = O.window_insert(11.2, 18.2, rise=0, style="blocks", apron=True, qa=True, **tk)
    front = O.door_ornate(15.4, 25.2, leaves=2, transom=4.2, head="swan")
    back = O.door_ornate(11.2, 24.4, leaves=1, transom=4.2, head="pediment")

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    add(MAIN, 45.5, 0, 0.4, front, "front-door", "door")                     # front of the main block
    add(MAIN, 45.5, 0, V2, up, "S45-2")
    add(MAIN, WX0, -10.5, V2, up, "wingW-2")                                 # wing, west side
    for x in (73.3, 91.3):                                                   # wing front, above the bay
        add(MAIN, x, WY0, V2, up_qa, f"wingS{x:.0f}-2")
    for y in (-10.5, 28.0, 115.5):                                           # east side
        add(MAIN, X1, y, V1, lo, f"E{y:.0f}-1")
        add(MAIN, X1, y, V2, up, f"E{y:.0f}-2")
    for x in (87.5, 21.0):                                                   # rear
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, 52.5, Y1, V2 + 1.4, small, "N52-2")
    add(MAIN, 52.5, Y1, 0.4, back, "back-door", "door")
    for y, sp in ((105.0, lo), (59.5, lo_qa), (29.8, lo)):                   # west side
        add(MAIN, 0, y, V1, sp, f"W{y:.0f}-1")
        add(MAIN, 0, y, V2, up, f"W{y:.0f}-2")
    P = TOWER.pts
    for k in TOWER_FACES:                                                    # tower, three storeys
        m = ((P[k][0] + P[(k + 1) % 8][0]) / 2, (P[k][1] + P[(k + 1) % 8][1]) / 2)
        add(TOWER, m[0], m[1], V1, tw1, f"T{k}-1")
        add(TOWER, m[0], m[1], V2, tw2, f"T{k}-2")
        add(TOWER, m[0], m[1], V3, tw3, f"T{k}-3")
    Q = BAY.pts
    for i, sp in ((0, bay_s), (1, bay_f), (2, bay_s)):                        # bay
        m = ((Q[i][0] + Q[i + 1][0]) / 2, (Q[i][1] + Q[i + 1][1]) / 2)
        add(BAY, m[0], m[1], V1 - 0.4, sp, f"bay{i}-1")
    return L


OPENINGS = _openings()


def _siding(f, b, reg):
    """Clapboard on the first floor; shingles above, upright so the layers draw them:
    fish-scale on the second floor, the tower's third storey banded fish-scale and diamond."""
    out = []
    lo = reg ^ rect(-1, -1, f.L + 1, S1 - ZF)
    mid = reg ^ rect(-1, S1 - ZF, f.L + 1, ZE - ZF)
    top = reg ^ rect(-1, ZE - ZF, f.L + 1, 999)
    if not lo.is_empty():
        out.append(clapboard(lo, pitch=1.2, d=0.3, dmin=0.05, datum=1.8))
    if not mid.is_empty():
        out.append(scallop_rows(mid, 1.6, 1.9, d=0.4, datum=S1 + RH - ZF, shape="fish"))
    if not top.is_empty():
        out.append(scallop_rows(top, 1.6, 1.9, d=0.4, datum=ZE + RH - ZF, shape=SPIRE_SLATE))
    return union(out) if out else M()


DORMER_Y, DORMER_W, DORMER_X = 59.5, 15.0, 6.0      # centre (over the W59 stack), width, face line
DORMER_HW, DORMER_S = 10.4, 0.9                       # face wall height above the roof, dormer roof slope


def _dormer(ze):
    """Gable dormer on the main roof's west slope (the plane through x = -EAVE_D at ze)."""
    W, xf, yc = DORMER_W, DORMER_X, DORMER_Y
    zr = round((ze + S_MAIN * (xf + EAVE_D)) / 0.2) * 0.2      # roof surface at the face line (on the grid)
    hw, gh = DORMER_HW, DORMER_S * W / 2
    t_face, t_roof, over = 1.6, 1.0, 0.8
    xb = xf + (hw + gh) / S_MAIN + 1.0               # the dormer ridge dies into the main roof
    # body (slate cheeks) behind the face piece
    pent = poly([(yc - W / 2, zr - 0.6), (yc + W / 2, zr - 0.6), (yc + W / 2, zr + hw), (yc, zr + hw + gh),
                 (yc - W / 2, zr + hw)])
    yz_to_x = frame([0, 0, 0], [0, 1.0, 0], [0, 0, 1.0], [1.0, 0, 0])          # (y, z, x) -> world
    body = M.extrude(pent, xb - xf - t_face).transform(yz_to_x).translate([xf + t_face, 0, 0])
    # dormer roof: two slabs over the rakes, running out past the face and the cheeks
    ln = math.hypot(W / 2 + over, (W / 2 + over) * DORMER_S)
    ang = math.atan(DORMER_S)
    slabs, tex = [], []
    for sg in (-1, 1):
        # plane-local (u along x, v up the slope from the eave, n out of the roof)
        e_v = np.array([0.0, -sg * math.cos(ang), math.sin(ang)])
        e_n = np.array([0.0, sg * math.sin(ang), math.cos(ang)])
        eave = np.array([xf - over, yc + sg * (W / 2 + over), zr + hw - over * DORMER_S])
        A = frame(eave, [1.0, 0, 0], e_v, e_n)
        L = xb - xf + over
        slabs.append(box([0, 0, 0], [L, ln + 0.6, t_roof]).transform(A))
        tex.append(scallop_rows(rect(0.3, 0.0, L, ln - 0.4), 1.6, 2.2, d=0.4, shape=SLATE, datum=0.0)
                   .translate([0, 0, t_roof]).transform(A))
    top_z = zr + hw + gh + t_roof / math.cos(ang)
    roofs = (union(slabs) + union(tex)).trim_by_plane([0, 0, -1.0], -top_z)
    ridge_roll = M.cylinder(xb - xf + over, 0.6, 0.6, 16).transform(frame([xf - over, yc, top_z - 0.3], [0, 1.0, 0],
                                                                             [0, 0, 1.0], [1.0, 0, 0]))
    body = body + roofs + ridge_roll
    # the face: fish-scale pentagon with an arched attic window
    f = Facade((xf, yc + W / 2), (xf, yc - W / 2), zr)
    win = O.window_insert(6.4, 8.2, rise=None, style="scroll", casing=0.8, ends=0.2, sill_ext=0.3, clip=True)
    wu, wv = W / 2, 3.2
    fcs = poly([(0, 0), (W, 0), (W, hw), (W / 2, hw + gh), (0, hw)])
    face = M.extrude(fcs - win["cut"].translate((wu, wv)), t_face).translate([0, 0, -t_face])
    reg = (fcs.offset(-0.5) - win["landing"].translate((wu, wv))) ^ rect(0, 0.6, W, hw + gh)
    face = face + scallop_rows(reg, 1.6, 1.9, d=0.4, datum=0.6, shape="fish")
    face = f.place(face)
    notch = box([xf - 0.01, yc - W / 2 - 0.01, zr], [xf + t_face + 0.01, yc + W / 2 + 0.01, zr + hw + gh + 5])
    Aw = f.A.copy()
    Aw[:, 3] = f.world(wu, wv, 0.0)
    return dict(body=body, notch=notch, face=face, sash=win["sash"].transform(Aw),
                surround=win["surround"].transform(Aw), P=inv34(Aw))


def _ridge_crest(a, b, z0, h=2.6):
    """Iron cresting for the hip ridge as its own strip: a base bar that drops into a slot
    in the ridge, the pierced fence, and a turned finial at each end. Prints upright."""
    f = Facade(a, b, z0)
    L = f.L
    parts = [box([-0.6, -0.6, 0.0], [L + 0.6, 0.6, 1.4])]                    # base bar in the slot
    cr = R.crest_fence(L, h=h, pitch=1.6).transform(frame([0, 0, 1.2], [1.0, 0, 0], [0, 0, 1.0], [0, -1.0, 0]))
    parts.append(cr)
    for u in (0.0, L):
        parts.append(finial(1.0, 6.0).translate([u, 0, 1.2]))
    m = union(parts)
    A = np.eye(3, 4)
    A[:, 0] = [f.u[0], f.u[1], 0.0]
    A[:, 1] = [-f.u[1], f.u[0], 0.0]
    A[:, 2] = [0, 0, 1.0]
    A[:, 3] = [a[0], a[1], z0]
    return m.transform(A)


# ------------------------------------------------------------------ build
def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    clear = [lip_keep(cs_union([b.cs for b in BLOCKS]), 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1, ZE], t=3.0, corners="board", clear=clear, siding=_siding)
    kit.add("WALLS-1", "Sage", st["shells"][0], group="walls")
    kit.add("BELT-1", "Cream", st["rings"][0], group="walls")
    # inside the house the tower's walls rise from the second floor so its belt ring (and
    # the lip under it) bear all round, not just on the faces that stand clear
    tw_in = slab((TOWER.cs - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -1.0), S1 + RH, ZE)
    tw_in = tw_in - lip_keep(cs_union([MAIN.cs, TOWER.cs]), 3.0, S1 + RH)
    kit.add("WALLS-2", "Gold", st["shells"][1] + tw_in, group="walls")
    kit.add("TOWER-BELT", "Cream", st["rings"][1], group="tower")
    kit.add("TOWER-3", "Gold", st["shells"][2], group="tower")
    kit.add("FOUNDATION", "Fieldstone", foundation(BLOCKS, 0.0, ZF), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        inserts.append(kit.add(f"{key}-{o.name}-sash", "Walnut" if o.kind == "door" else "Oxblood",
                               sp["sash"].transform(A), P=inv34(A), key=f"{key}-{tag}-sash-{o.name[:1]}", group="inserts"))
        if sp["surround"] is not None:
            inserts.append(kit.add(f"{key}-{o.name}-surround", "Cream", sp["surround"].transform(A), P=inv34(A),
                                   key=f"{key}-{tag}-surround-{o.v0 > 20}", group="inserts"))
    print("walls + inserts", round(time.time() - t0, 1))

    tower_keep = TOWER.solid(grow=2.1, dz0=-1, dz1=200)
    # --- main eave ring (upside down), cut round the tower
    eave = R.bracketed_cornice(MAIN.pts, ZE, CORNICE_QA,
                               brackets=dict(z_top=3.8, h=3.4, d0=0.9, d=3.6, t=0.7, pitch=10.4, pair=1.5, margin=3.6),
                               dents=dict(z=3.0, h=0.8, d0=0.9, d=0.6), panels=dict(z=0.6, h=2.0, d=0.35))
    kit.add("EAVE-main", "Cream", eave - tower_keep, P=print_flip(), group="roof")
    # --- main roof: banded slate hip over the house, a gable roof over the front wing
    ze = ZE + EAVE_H
    main_p = [(0, 0), (X1, 0), (X1, Y1), (0, Y1)]
    wing_front = WY0 + 3.0 + EAVE_D           # after the eave offset the wing roof's body stops at the gable's back face
    wing_p = [(WX0, wing_front), (X1, wing_front), (X1, 35.0), (WX0, 35.0)]
    roof, tex = R.hip_roof([(main_p, [0, 1, 2, 3], S_MAIN), (wing_p, [1, 3], S_WING)], ze, S_MAIN, EAVE_D,
                           texture=SLATE, tex_kw=dict(pitch=1.6, wtab=2.2, d=0.4))
    # rake: the wing roof's skin runs 3.6 mm past the gable face
    rk_p = [(WX0, WY0 - 3.6 + EAVE_D), (X1, WY0 - 3.6 + EAVE_D), (X1, wing_front + 0.5), (WX0, wing_front + 0.5)]
    rk_top, rk_pl = R.hip_solid(rk_p, ze, S_WING, ze - 20, d_eave=EAVE_D, exposed=[1, 3])
    rk_low, _ = R.hip_solid(rk_p, ze - 1.8, S_WING, ze - 20, d_eave=EAVE_D, exposed=[1, 3])
    rake = (rk_top - rk_low) ^ box([-50, -60, ze], [200, WY0 + 3.0 + 0.1, 400])
    rake_tex = R.hip_texture(rk_p, rk_pl, ze, d_eave=EAVE_D, shape=SLATE, pitch=1.6, wtab=2.2, d=0.4) ^ \
        box([-50, -60, ze], [200, WY0 + 3.0, 400])
    ridge = ze + S_MAIN * (X1 / 2 + EAVE_D)
    chims = [(28.0, 108.0), (86.0, 96.0)]

    def chim_z0(x, y):     # 3 mm below the lowest roof point under the chimney
        d = min(x + EAVE_D, X1 + EAVE_D - x, y + EAVE_D, Y1 + EAVE_D - y) - 5.65
        return ze + S_MAIN * d - 3.0
    pockets = union([box([x - 5.65, y - 5.65, chim_z0(x, y)], [x + 5.65, y + 5.65, ridge + 30]) for x, y in chims])
    roof_all = (roof + tex + rake + rake_tex) - tower_keep - pockets
    # gabled dormer on the west slope over the Queen Anne window stack: slate cheeks and
    # roof are part of the main roof; the shingled face is its own piece in a notch
    dm = _dormer(ze)
    roof_all = roof_all - dm["notch"] + dm["body"]
    # ridge: a slot for the separate cresting strip
    ry0, ry1 = 57.9 - EAVE_D, Y1 - 57.9 + EAVE_D
    rz = round((ridge - 0.8) / 0.2) * 0.2
    roof_all = roof_all - box([X1 / 2 - 0.65, ry0 - 1, rz], [X1 / 2 + 0.65, ry1 + 1, ridge + 10])
    kit.add("ROOF-main", "Slate", roof_all, group="roof")
    kit.add("DORMER", "Gold", dm["face"], group="roof")
    kit.add("WIN-dormer-sash", "Oxblood", dm["sash"], P=dm["P"], group="inserts")
    kit.add("WIN-dormer-surround", "Cream", dm["surround"], P=dm["P"], group="inserts")
    kit.add("ROOF-crest", "Slate", _ridge_crest((X1 / 2, ry0), (X1 / 2, ry1), rz), group="roof")
    for k, (x, y) in enumerate(chims):
        z0 = chim_z0(x, y)
        ch = FT.chimney(w=10.5, dpt=10.5, h=ridge - 4.0 - z0, peg=None).translate([x, y, z0])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY" if k == 0 else f"CHIMNEY-{k}", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- wing gable: shingled pentagon on the eave ring, with an attic window and trim
    gz = ze                                   # gable base (top of the eave ring)
    GL = X1 - WX0
    shoulder = EAVE_D * S_WING - 1.8          # where the rake skin meets the wall face
    apex = shoulder + GL / 2 * S_WING
    gcs = poly([(0, 0), (GL, 0), (GL, shoulder), (GL / 2, apex), (0, shoulder)])
    gf = Facade((WX0, WY0), (X1, WY0), gz)
    attic = O.window_insert(7.0, 9.2, rise=None, style="scroll", casing=0.8, ends=0.2, sill_ext=0.3, clip=True)
    a_u, a_v = GL / 2, 3.0
    # gable trim: bargeboards under the rake, a sunburst in the peak, a collar tie
    trim = []
    for sgn in (-1, 1):
        x0, x1 = (0.0, GL / 2) if sgn < 0 else (GL, GL / 2)
        a = np.array([x0, shoulder])
        b = np.array([x1, apex])
        d = (b - a) / np.linalg.norm(b - a)
        n = np.array([d[1], -d[0]]) * (1 if sgn < 0 else -1)
        trim.append(poly([tuple(a), tuple(b), tuple(b + n * 1.3), tuple(a + n * 1.3)]))
    sun_c = (GL / 2, apex - 6.0)
    rays = []
    for k in range(7):
        ang = math.radians(20 + 140 * k / 6)
        c_, s_ = math.cos(ang), math.sin(ang)
        rays.append(poly([(sun_c[0] - 0.25 * s_, sun_c[1] + 0.25 * c_), (sun_c[0] + 0.25 * s_, sun_c[1] - 0.25 * c_),
                          (sun_c[0] + 4.2 * c_ + 0.3 * s_, sun_c[1] + 4.2 * s_ - 0.3 * c_),
                          (sun_c[0] + 4.2 * c_ - 0.3 * s_, sun_c[1] + 4.2 * s_ + 0.3 * c_)]))
    trim.append(cs_union(rays) ^ rect(0, sun_c[1], GL, apex))
    trim.append(rect(GL / 2 - 5.2, sun_c[1] - 0.6, GL / 2 + 5.2, sun_c[1]))       # collar tie
    tr = cs_union(trim) ^ gcs
    gwall = M.extrude(gcs - attic["cut"].translate((a_u, a_v)), 3.0).translate([0, 0, -3.0])
    reg = (gcs.offset(-0.6) - attic["landing"].translate((a_u, a_v)) - tr.offset(0.3)) ^ rect(0, 2.2, GL, apex)
    gtex = scallop_rows(reg, 1.6, 1.9, d=0.4, datum=2.2, shape=SPIRE_SLATE)
    kit.add("GABLE", "Gold", gf.place(gwall + gtex), group="roof")
    Ag = gf.A.copy()
    Ag[:, 3] = gf.world(a_u, a_v, 0.0)
    kit.add("WIN-attic-sash", "Oxblood", attic["sash"].transform(Ag), P=inv34(Ag), group="inserts")
    kit.add("WIN-attic-surround", "Cream", attic["surround"].transform(Ag), P=inv34(Ag), group="inserts")
    kit.add("GABLE-trim", "Cream", gf.place(ext(tr, 0.0, 0.8)), P=inv34(gf.A), group="roof")     # flat on its back

    # --- tower: eave ring, fish-scale spire, separate finial
    teave = R.bracketed_cornice(TOWER.pts, TT, R.CORNICE_SMALL,
                                brackets=dict(z_top=4.6, h=4.2, d0=0.8, d=2.4, t=0.7, pitch=7.0, pair=1.5, margin=3.0),
                                dents=dict(z=3.8, h=0.8, d0=0.8, d=0.7), panels=dict(z=0.6, h=2.4, d=0.35))
    kit.add("TOWER-EAVE", "Cream", teave, P=print_flip(), group="tower")
    tz = TT + 8.0
    spire, stex = R.hip_roof([(TOWER.pts, list(range(8)))], tz, S_SPIRE, 4.8, texture=SPIRE_SLATE,
                             tex_kw=dict(pitch=1.6, wtab=1.9, d=0.4))
    tip = tz + S_SPIRE * (TA + 4.8)
    zseat = tip - 2.4
    seat = M.cylinder(1.0, 1.35, 1.35, 32).translate([TC[0], TC[1], zseat - 0.4])
    kit.add("TOWER-SPIRE", "Slate", (spire + stex).trim_by_plane([0, 0, -1.0], -zseat) - seat, group="tower")
    kit.add("TOWER-FINIAL", "Slate", finial(1.2, 9.0).translate([TC[0], TC[1], zseat - 0.4]), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- bay: small bracketed cornice and a slate hip roof
    bay_path = BAY.pts
    # clear of the wing's siding, and stopping short of its corner boards
    bay_keep = MAIN.solid(grow=0.45, dz0=-1, dz1=300) + box([-50, -60, 0], [62.2, 0, 300]) + box([102.4, -60, 0], [200, 0, 300])
    beave = R.bracketed_cornice(bay_path, BAY.z1, CORNICE_QA,
                                brackets=dict(z_top=3.8, h=3.4, d0=0.9, d=3.6, t=0.7, pitch=6.0, pair=1.5, margin=2.4),
                                dents=dict(z=3.0, h=0.8, d0=0.9, d=0.6), panels=dict(z=0.6, h=2.0, d=0.35))
    kit.add("BAY-EAVE", "Cream", beave - bay_keep, P=print_flip(), group="bay")
    deck_z = S1 - 0.4
    broof, btex = R.hip_roof([(bay_path, [0, 1, 2])], BAY.z1 + EAVE_H, 0.8, EAVE_D, texture=SLATE,
                             flat_top=deck_z, tex_kw=dict(pitch=1.6, wtab=2.2, d=0.4))
    run = (deck_z - BAY.z1 - EAVE_H) / 0.8
    crest = R.cresting(bay_path, deck_z - 0.2, h=2.4, pitch=1.6, d_off=EAVE_D - run - 0.8)
    crest = crest ^ box([0, -60, 0], [200, WY0 - 2.6, 400])
    kit.add("BAY-ROOF", "Slate", (broof + btex + crest) - bay_keep, group="bay")

    # --- wraparound porch: turned posts, railings, sawn-work arcades, gray board floor
    H_floor = ZF - 2.0
    post_h = 41.6 - H_floor
    ppoly = [(-14.0, -28.0), (WX0, -28.0), (WX0, WY0), (WX0, 0.0), (0.0, 0.0), (0.0, 84.0), (-28.0, 84.0),
             (-28.0, -14.0)]
    runs = [dict(a=(0.0, 84.0), b=(-28.0, 84.0), posts=[3.2, 26.4]),
            dict(a=(-28.0, 84.0), b=(-28.0, -14.0), posts=[1.6, 25.6, 49.6, 73.6, 98.0 - 0.663]),
            dict(a=(-28.0, -14.0), b=(-14.0, -28.0), posts=[0.663, 19.799 - 0.663]),
            dict(a=(-14.0, -28.0), b=(WX0, -28.0), posts=[0.663, 25.0, 50.5, 72.0]),
            dict(a=(WX0, -28.0), b=(WX0, WY0), posts=[1.6])]
    P = FT.porch_turned(ppoly, runs, H_floor, post_h, steps_at=[(3, 59.5, 16.0)], boards=dict(pitch=1.8),
                        joined=True, ledger_off=1.5)          # the ledger clears the foundation's stones
    fkeep = slab(offset(cs_union([b.cs for b in BLOCKS]), 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    kit.add("PORCH-deck", "Cream", P["deck"] - fkeep, P=print_flip(), group="porch")
    kit.add("PORCH-floor", "PorchGray", P["floor"] - fkeep, P=print_flip(), group="porch")
    # posts and railings as one piece (printed upright on plinths and railing feet)
    for k, fr in enumerate(sorted(P["frames"], key=lambda m: -m.volume())):
        kit.add(f"PORCH-frame-{k}", "Cream", fr, group="porch")
    for k, (arc, A) in enumerate(P["arcades"]):
        kit.add(f"PORCH-arcade-{k}", "Cream", arc, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=0) for b in BLOCKS]) + TOWER.solid(grow=1.45, dz0=-20, dz1=300)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    proof = P["roof"] - bld_keep - ins_keep - box([62.0, -60, 0], [200, WY0 + 0.5, 300])    # stops at the bay
    ptop = proof.bounding_box()[5]
    below = proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8))
    cap = proof.trim_by_plane([0, 0, 1.0], ptop - 0.8)                # standing-seam tin, square to each wall
    inner = M.extrude(cap.slice(ptop - 0.4).offset(-0.5), 5).translate([0, 0, ptop - 1])
    ribs = union([box([x - 0.25, -60, ptop - 0.01], [x + 0.25, 0.0, ptop + 0.4]) for x in np.arange(-26.4, 61, 5.2)])
    ribs = ribs + union([box([-60, y - 0.25, ptop - 0.01], [0.0, y + 0.25, ptop + 0.4]) for y in np.arange(2.6, 86, 5.2)])
    ribs = ribs ^ inner
    kit.add("PORCH-roof", "Cream", below, P=print_flip(), group="porch")
    kit.add("PORCH-roof-cap", "Slate", cap + ribs, group="porch")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "PorchGray", sm.transform(A) - fkeep, group="porch")
    # back stoop under the rear door
    e, u = MAIN.locate(52.5, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "PorchGray", FT.steps(16.0, ZF - 0.6, 4).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "beaumont")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "beaumont.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2)
