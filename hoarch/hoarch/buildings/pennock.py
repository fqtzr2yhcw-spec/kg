"""The Pennock: an original HO-scale (1:87.1) Pennsylvania fieldstone Colonial, house 32 of the
third batch (after the user's photo 2).

A five-bay farmhouse of roughly coursed fieldstone with dressed quoins (each with a chiselled
drafted margin) on a ledgestone foundation. Every window sits under a flat-bottomed segmental
arch of thin stones set on edge; nine-over-six sash below under drip caps, six-over-six above
in eared frames, lugged sills, and oxblood shutters of two raised panels hung on iron strap
hinges. Between the storeys a pent roof of riven shakes runs across the front on a cornice of
an ochre frieze of compass stars, a white course of wolf's teeth and a white torus; at the
eave an ochre frieze of gadroons, white dentils and a deep white cove. The entrance is a pair
of strap-hinged leaves under a four-light transom, beneath a pedimented hood on scrolled
consoles with a compass star in its tympanum, up a stone stoop with a settle either side. A
steep side-gabled roof of riven shakes with two arched dormers roofed in tin; fieldstone end
stacks under stone hoods; a datestone (J P 1768) in the west gable over two attic lights. At
the back a kitchen ell of one storey under its own gable and hooded stack, with an ochre
frieze of whirling rosettes.

usage: python3 -m hoarch.buildings.pennock [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import box, compose, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import colonial as C, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.ornament import chamfer_box, ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Pennock"
COLORS = {"Fieldstone": "#A1917B", "Ledge": "#6B6258", "White": "#EDE8DC", "Ochre": "#B98B3E", "Oxblood": "#6A2B24",
          "Shake": "#5C4F45", "Tin": "#8A9096", "Windows_Doors": "#EDE8DC"}
RENDER_MAT = {"Fieldstone": "stone", "Ledge": "stone2", "White": "trim", "Ochre": "accent", "Oxblood": "shutter",
              "Shake": "roof", "Tin": "metal", "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Pennock)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="compass", role="Ochre"),
    dict(kind="course", h=1.6, b=1.4, orn="wedges", role="White", tooth=1.8, gap=0.6),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="torus", role="White")])
EAVE = dict(pitch=11.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.2, b=1.2, orn="gadroons", role="Ochre"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="White", tooth=0.8, gap=0.6),
    dict(kind="crown", h=3.4, b=1.4, P=6.6, orn="cavetto", role="White")])
ELL_C = dict(pitch=10.0, margin=3.4, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="whirls", role="Ochre"),
    dict(kind="crown", h=2.2, b=1.4, P=4.0, orn="ovolo", role="White")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 12.0
S1 = ZF + 44.0
ZE = S1 + RJ + 38.0
ZW = ZE + HE
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 6.2, 6.4, 1.8
S_MAIN = 0.85
V1 = 8.0
V2 = S1 + RJ + 8.0 - ZF
ZP = S1 + RJ                                   # the pent's soffit, on the joint cornice's crown
P_PENT, S_PENT, F_PENT = 8.0, 0.55, 1.2
P_GABLE = 6.0
ZP_TOP = ZP + F_PENT + S_PENT * P_PENT
ELL_ZE = ZF + 38.0
ELL_ZW = ELL_ZE + CO.band_height(ELL_C)
ELL_FASCIA = 1.4
ELL_Z_EAVE = ELL_ZW + ELL_FASCIA
S_ELL, D_EAVE_E, RAKE_E = 0.8, 5.4, 5.6

# ------------------------------------------------------------------ plan (x east, y north; the front faces south)
W, D = 196.0, 100.0
XC = W / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
EX0, EX1, EY1 = 118.0, 170.0, 144.0
ELL = Block("ell", [(EX0, D - 3.0), (EX1, D - 3.0), (EX1, EY1), (EX0, EY1)], ZF, ELL_ZW)
BLOCKS = [MAIN, ELL]
ELL_RIDGE = ELL_Z_EAVE + S_ELL * ((EX1 - EX0) / 2 + D_EAVE_E)
DOOR_W, DOOR_H = 13.0, 30.0
SW, SD = 42.0, 12.0                          # the stoop
BENCH_L = 9.0
SHUT_GAP, SHUT_CAS = 1.0, 1.4


def _openings():
    L, SH = [], []

    def add(blk, x, y, v0, sp, name, kind="window", shutters=False):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        if shutters:
            SH.append(name)

    lo = C.window_pennsylvania(10.4, 25.0, lites=(3, 3), rows=(3, 2), head="drip")
    up = C.window_pennsylvania(10.4, 22.0, lites=(3, 3), rows=(2, 2), head="ears")
    att = C.window_attic(6.4, 7.2)
    ell = C.window_pennsylvania(9.6, 22.0, lites=(3, 3), rows=(3, 2), head="drip")
    back_door = C.door_hooded(11.0, 28.0, hood=False)
    for x in (30.0, 64.0, W - 64.0, W - 30.0):
        add(MAIN, x, 0.0, V1, lo, f"S{x:.0f}-1", shutters=True)
    add(MAIN, XC, 0.0, 0.4, C.door_hooded(DOOR_W, DOOR_H), "front-door", "door")
    for x in (30.0, 64.0, XC, W - 64.0, W - 30.0):
        add(MAIN, x, 0.0, V2, up, f"S{x:.0f}-2", shutters=True)
    for x_, tag in ((0.0, "W"), (W, "E")):
        for y in (30.0, 70.0):
            add(MAIN, x_, y, V1, lo, f"{tag}{y:.0f}-1", shutters=True)
            add(MAIN, x_, y, V2, up, f"{tag}{y:.0f}-2", shutters=True)
            add(MAIN, x_, y, ZW + F_PENT + S_PENT * P_GABLE + 1.8 - ZF, att, f"{tag}{y:.0f}-attic")
    for x in (30.0, 64.0):
        add(MAIN, x, D, V1, lo, f"N{x:.0f}-1", shutters=True)
    add(MAIN, 94.0, D, 0.4, back_door, "back-door", "door")
    for x in (30.0, 64.0, 94.0):
        add(MAIN, x, D, V2, up, f"N{x:.0f}-2", shutters=True)
    # the kitchen ell: one opening to a wall, no shutters (its walls are too short for them)
    add(ELL, EX1, 122.0, 0.4, back_door, "ell-door", "door")
    add(ELL, EX0, 122.0, 7.0, ell, "ellW-1")
    add(ELL, (EX0 + EX1) / 2, EY1, 7.0, ell, "ellN-1")
    return L, SH


OPENINGS, SHUTTERED = _openings()


def _open_on(b, f):
    return [o for o in OPENINGS if o.block is b and np.allclose(o.facade.p0, f.p0) and np.allclose(o.facade.p1, f.p1)]


def _corners(b):
    """Per corner of block b: a building corner (convex, not against the other block)."""
    conv = b.convex_corners(min_turn=70.0)
    others = [offset(o.cs, 0.2) for o in BLOCKS if o is not b]
    touch = [any(not (o ^ rect(p[0] - 0.01, p[1] - 0.01, p[0] + 0.01, p[1] + 0.01)).is_empty() for o in others)
             for p in b.pts]
    return [c and not t for c, t in zip(conv, touch)]


def _stone(f, b, reg):
    """Fieldstone with drafted quoins at the building's corners, a rubble arch over every
    window, bare wall behind the shutters, and the datestone in the west gable."""
    parts = []
    i = next(k for k, f_ in enumerate(b.facades()) if np.allclose(f_.p0, f.p0) and np.allclose(f_.p1, f.p1))
    cor = _corners(b)
    ends = (cor[i], cor[(i + 1) % len(cor)])
    zones = ([(0.0, S1 - ZF - 0.2), (S1 + RJ - ZF, ZE - LEDGE - 0.6 - ZF)] if b is MAIN else
             [(0.0, ELL_ZE - LEDGE - 0.6 - ZF)])
    keep = []
    for za, zb in zones:
        q, qz = C.quoins_drafted(f.L, zb - za, ends=ends, datum=0.0)
        if not q.is_empty():
            parts.append(q.translate([0, za, 0]))
            keep.append(qz.translate((0.0, za)))
    seed = int(abs(f.p0[0]) * 7 + abs(f.p0[1]) * 3 + f.zb) % 997
    for k, o in enumerate(_open_on(b, f)):
        sp = o.spec
        lb = sp["landing"].bounds()
        w_op = sp["cut"].bounds()[2] - sp["cut"].bounds()[0]
        h_op = sp["cut"].bounds()[3] - sp["cut"].bounds()[1]
        if o.kind == "window" and "attic" not in o.name:
            a, az = C.rubble_arch(o.u, o.v0 + lb[3], lb[2] - lb[0] + 0.6, seed=seed + k)
            parts.append(a)
            keep.append(az)
        if o.name in SHUTTERED:
            x0 = w_op / 2 + SHUT_CAS + SHUT_GAP
            for sg in (-1, 1):
                u0, u1 = sorted((o.u + sg * (x0 - 0.3), o.u + sg * (x0 + w_op / 2 + 0.3)))
                keep.append(rect(u0, o.v0 - 0.3, u1, o.v0 + h_op + 0.3))
    if b is MAIN and i == 3:                  # the datestone, high in the west gable
        from hoarch.storefront import text_cs
        uc, v0 = D / 2, ZW - ZF + 17.0
        tab = chamfer_box(uc - 8.0, v0, uc + 8.0, v0 + 8.4, 0.0, 0.6, c=0.25, bottom=0.6)
        letters = cs_union([text_cs("J P", cap=2.2).translate((uc, v0 + 5.0)), text_cs("1768", cap=2.4).translate((uc, v0 + 1.3))])
        parts.append(tab + ext(letters, 0.59, 0.95))
        keep.append(rect(uc - 8.4, v0 - 0.4, uc + 8.4, v0 + 8.8))
    fs_reg = reg - cs_union(keep) if keep else reg
    parts.append(C.fieldstone(fs_reg, datum=0.0, seed=seed))
    return union(parts) ^ ext(reg.offset(0.6, JoinType.Miter, 4.0) + cs_union(keep), -0.5, 2.0)


def _stoop():
    """The front stoop: a platform faced in ledgestone on three sides under a cap slab."""
    from hoarch.core import Facade
    x0, x1, y0 = XC - SW / 2, XC + SW / 2, -SD
    zt = ZF - 0.8
    body = box([x0 + 0.4, y0 + 0.4, 0.0], [x1 - 0.4, 0.02, zt + 0.01])
    for p0, p1 in (((x0 + 0.4, y0 + 0.4), (x1 - 0.4, y0 + 0.4)), ((x1 - 0.4, y0 + 0.4), (x1 - 0.4, 0.0)),
                   ((x0 + 0.4, 0.0), (x0 + 0.4, y0 + 0.4))):
        f = Facade(p0, p1, 0.0)
        body = body + f.place(C.foundation_ledgestone(rect(0.0, 0.0, f.L, zt), seed=int(p0[0])).translate([0, 0, -0.02]))
    cap = box([x0, y0, zt], [x1, 0.02, ZF - 0.3]) + box([x0 + 0.3, y0 + 0.3, ZF - 0.31], [x1 - 0.3, 0.02, ZF])
    return body + cap


def _steps(n=4, width=20.0, tread=2.6):
    """Solid stone steps down from the stoop, each tread a slab with a little nosing."""
    r = ZF / n
    out = []
    for k in range(1, n):
        top = round((ZF - k * r) / 0.2) * 0.2
        ya, yb = -SD - k * tread - 0.55, (-SD - 0.55 if k == 1 else -SD - (k - 1) * tread - 0.55 + 0.02)
        out.append(box([XC - width / 2, ya, 0.0], [XC + width / 2, yb, top - 0.6]))
        out.append(box([XC - width / 2 - 0.3, ya - 0.3, top - 0.61], [XC + width / 2 + 0.3, yb, top]))
    return union(out)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    # --- the main roof first: its gable walls go into the top shell
    pieces = [(MAIN.pts, [0, 2], S_MAIN)]
    specs = [dict(p0=(W, 0.0), p1=(W, D), slope=S_MAIN, e=0.3), dict(p0=(0.0, D), p1=(0.0, 0.0), slope=S_MAIN, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture="riven", tex_kw=dict(pitch=1.6, wtab=2.4, d=0.42),
                       skin=SKIN, rake=RAKE, inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA, hollow=2.8)
    we, ww = rf["walls"]
    gables = [(MAIN, 1, we["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 3, ww["cs"].translate((0.0, Z_EAVE - ZF)))]
    base = MAIN.cs
    epath = [(EX0, D + 0.2), (EX1, D + 0.2), (EX1, EY1), (EX0, EY1)]
    ell_env, _ = R.hip_roof([(epath, [1, 3], S_ELL)], ELL_Z_EAVE + 1.4, S_ELL, D_EAVE_E + 1.0, texture=None, zlo=ELL_ZW - 1.0)
    ell_zone = ell_env ^ box([-500, D - 1.0, -10], [500, D + 2.0, 500])
    gp_top = ZW + F_PENT + S_PENT * P_GABLE
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(ELL.cs, 8.0) ^ rect(-500.0, D + 0.5, 500.0, 500.0), ELL_ZE - LEDGE - 0.6, ELL_ZW + 0.01),
               ell_zone,
               box([-1.0, -2.0, ZP - 0.2], [W + 1.0, 1.0, ZP_TOP + 0.6]),                # behind the pent
               box([-2.0, -1.0, ZW - 0.2], [1.0, D + 1.0, gp_top + 0.6]),               # behind the gable pents
               box([W - 1.0, -1.0, ZW - 0.2], [W + 2.0, D + 1.0, gp_top + 0.6]),
               box([XC - SW / 2, -2.0, ZF - 0.5], [XC + SW / 2, 1.0, ZF + 10.4])]      # behind the settles
    allcs = cs_union([b_.cs for b_ in BLOCKS])
    clear = [lip_keep(allcs, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_stone, gables=gables, clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((XC - 22.0, 3.0), (XC - 22.0, D - 3.0), 2.0, ZF, ZW)])
    ell_ledge = CO.ledge(ELL.pts, ELL_ZE, LEDGE) - MAIN.solid(grow=0.2, dz0=-1, dz1=1)
    ell_lip = (_corbel(ELL.cs, 3.0, ELL_ZW) + lip_ring(ELL.cs, 3.0, ELL_ZW)) - MAIN.solid(grow=0.3, dz0=-5, dz1=5) - \
        box([EX0 - 1, EY1 - 5.0, ELL_ZW - 1], [EX1 + 1, EY1 + 1, ELL_ZW + 5])
    # the ell's walls run on above the storey joint, behind its cornice, up to its roof
    ell_band = (slab(ELL.cs, S1 - 0.01, ELL_ZW) - slab(offset(ELL.cs, -3.0), S1 - 1.0, ELL_ZW + 1.0)) - \
        MAIN.solid(grow=0.0, dz0=-2, dz1=400) - st["rings"][0]
    kit.add("WALLS-1", "Fieldstone", st["shells"][0] + ell_band + ell_ledge + ell_lip, group="walls")
    ell_cut = box([EX0 - D_EAVE_E - 0.8, D + 0.02, S1 - 1.0], [EX1 + D_EAVE_E + 0.8, D + 8.0, S1 + RJ + 1.0])
    kit.add("JOINT", "Fieldstone", st["rings"][0] - ell_cut, group="walls")
    eave_path = max(base.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    no_lip = union([box([W - 5.0, -1, ZW - 1], [W + 1, D + 1, ZW + 5]), box([-1, -1, ZW - 1], [5.0, D + 1, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    kit.add("WALLS-2", "Fieldstone", st["shells"][1] + lip + CO.ledge(eave_path, ZE, LEDGE), group="walls")

    # --- cornices: the joint (cut round the ell's roof), the eave, the ell's three sides
    ell_keep = box([EX0 - D_EAVE_E - 0.8, D - 8.0, ZF], [EX1 + D_EAVE_E + 0.8, D + 60.0, ELL_RIDGE + 2.0])
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=ell_keep)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(ELL.pts, ELL_ZE, ELL_C, cut=MAIN.solid(grow=0.7, dz0=-2, dz1=2))
    CO.add_level(kit, rings, "CORNICE-ELL", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="ledgestone")
    kit.add("FOUNDATION", "Ledge", fnd, group="foundation")

    # --- windows, doors and shutters
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{o.v0 > 20}", group="inserts", render=zones)
        if o.name in SHUTTERED:
            w_op, h_op = b[2] - b[0], b[3] - b[1]
            sw = w_op / 2
            x0 = w_op / 2 + SHUT_CAS + SHUT_GAP
            left = C.shutter_strap(sw, h_op, hinge_left=True).translate([-(x0 + sw), 0, 0.02])
            right = C.shutter_strap(sw, h_op, hinge_left=False).translate([x0, 0, 0.02])
            for side, m in (("L", left), ("R", right)):
                kit.add(f"SHUTTER-{o.name}-{side}", "Oxblood", m.transform(A), P=inv34(A),
                        key=f"SHUTTER-{h_op:.1f}-{side}", group="shutters")
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the pent roof across the front, on the joint cornice
    pent_path = [(0.0, -P_PENT), (W, -P_PENT), (W, -0.02), (0.0, -0.02)]
    psol, ptex = R.hip_roof([(pent_path, [0], S_PENT)], ZP + F_PENT, S_PENT, 0.0, texture="riven",
                            tex_kw=dict(pitch=1.6, wtab=2.4, d=0.42), zlo=ZP)
    kit.add("PENT-S", "Shake", psol + ptex, group="walls")

    # --- the main roof: riven shakes, gabled at both ends
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
                       for wl in rf["walls"]])
    caps = [G.ridge_cap((-RAKE, D / 2), (W + RAKE, D / 2), zr, S_MAIN, ZW)]
    roof = roof + (union(caps) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 8.0, 16.0
    pockets, stacks = [], []
    for cx in (10.0, W - 10.0):
        zroof = Z_EAVE + S_MAIN * (D / 2 - CD / 2 + D_EAVE)
        z0 = round((zroof - 3.0) / 0.2) * 0.2
        roof = roof + G.chimney_seat(solid_env, cx, D / 2, CD / 2, zr + 1.0)
        pockets.append(box([cx - CW / 2 - 0.4, D / 2 - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, D / 2 + CD / 2 + 0.4, zr + 40]))
        stacks.append(C.chimney_stonehood(CW, CD, zr + 10.0 - z0, seed=int(cx)).translate([cx, D / 2, z0]))
    roof = roof - union(pockets)
    # two arched dormers on the front slope
    DW, DDEP, DHW, DRISE = 15.0, 18.0, 11.0, 3.6
    dyf = 16.0
    zdf = round((Z_EAVE + S_MAIN * (dyf + D_EAVE) - 1.0) / 0.2) * 0.2
    dbody, dcore, dface, (DR, dcy) = C.dormer_arched(DW, DDEP, DHW, DRISE)
    dparts = []
    for dxc in (64.0, W - 64.0):
        Ad = np.array([[1.0, 0, 0, dxc], [0, 0, -1.0, dyf], [0, 1.0, 0, zdf]])
        dkeep = ext(dface.offset(0.3, JoinType.Miter, 4.0), -DDEP - 0.3, 0.3).transform(Ad)
        dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
        dseat = box([dxc - DW / 2 - 1.3, dyf - 1.6, ZW], [dxc + DW / 2 + 1.3, dyf + DDEP + 1.3, zdf]) ^ solid_env
        roof = roof - dpocket + (dseat - dpocket - lip_keep(base, 3.0, ZW))
        dparts.append(Ad)
    kit.add("ROOF", "Shake", roof, group="roof")
    # pent eaves across both gables, on the eave cornice where it crosses the gable feet
    for tag, gpath, ex_ in (("E", [(W + 0.02, 0.0), (W + P_GABLE, 0.0), (W + P_GABLE, D), (W + 0.02, D)], [1]),
                            ("W", [(-P_GABLE, 0.0), (-0.02, 0.0), (-0.02, D), (-P_GABLE, D)], [3])):
        gsol, gtex = R.hip_roof([(gpath, ex_, S_PENT)], ZW + F_PENT, S_PENT, 0.0, texture="riven",
                                tex_kw=dict(pitch=1.6, wtab=2.4, d=0.42), zlo=ZW)
        gp = (gsol + gtex) - roof.translate([0, 0, -0.3]) - roof
        kit.add(f"PENT-{tag}", "Shake", max(gp.decompose(), key=lambda m_: m_.volume()), key="PENT-gable", group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Fieldstone", s_, key="CHIMNEY", group="roof")
    rcs = C.arched_roof_cs(DW, DR, dcy, t=1.0, eave=1.2)
    for k, Ad in enumerate(dparts):
        kit.add(f"DORMER-{k}", "White", dbody.transform(Ad), key="DORMER", group="roof")
        kit.add(f"DORMER-core-{k}", "Shake", dcore.transform(Ad), key="DORMER-core", group="roof")
        droof = ext(rcs, -DDEP - 8.0, 1.2).transform(Ad) - solid_env - dbody.transform(Ad) - roof
        droof = max(droof.decompose(), key=lambda m_: m_.volume())
        kit.add(f"DORMER-roof-{k}", "Tin", droof, P=compose(print_flip(), inv34(Ad)), key="DORMER-roof", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the kitchen ell's roof, its gable and its stack
    erf = G.gabled_roof([(epath, [1, 3], S_ELL)], ELL_Z_EAVE, D_EAVE_E, [dict(p0=(EX1, EY1), p1=(EX0, EY1), slope=S_ELL, e=0.3)],
                        texture="riven", tex_kw=dict(pitch=1.5, wtab=2.2, d=0.4), skin=SKIN, rake=RAKE_E,
                        inner_cs=offset(ELL.cs, -3.0), fascia=ELL_FASCIA, hollow=2.4)
    eroof = erf["body"] + erf["tex"] + erf["skins"] + erf["skin_tex"]
    ezr = ELL_RIDGE
    ex = (EX0 + EX1) / 2
    ewl = erf["walls"][0]
    ewall_env = ewl["facade"].place(M.extrude(ewl["cs"].offset(0.15), RAKE_E + 4.2).translate([0, 0, -3.15]))
    eroof = eroof + (G.ridge_cap((ex, D + 0.2), (ex, EY1 + RAKE_E), ezr, S_ELL, ELL_ZW) - ewall_env)
    eroof = (eroof ^ box([-500, D + 0.2, -10], [500, 500, 500])) - lip_keep(ELL.cs, 3.0, ELL_ZW)
    esolid, _ = R.hip_roof([(epath, [1, 3], S_ELL)], ELL_Z_EAVE, S_ELL, D_EAVE_E, texture=None, zlo=ELL_ZW)
    ECW, ECD = 14.0, 8.0
    ecy = EY1 - 8.0
    ez0 = round((ELL_Z_EAVE + S_ELL * ((EX1 - EX0) / 2 - ECW / 2 + D_EAVE_E) - 3.0) / 0.2) * 0.2
    eroof = eroof + G.chimney_seat(esolid, ex, ecy, ECW / 2, ezr + 1.0)
    eroof = eroof - box([ex - ECW / 2 - 0.4, ecy - ECD / 2 - 0.4, ez0], [ex + ECW / 2 + 0.4, ecy + ECD / 2 + 0.4, ezr + 40])
    kit.add("ELL-roof", "Shake", eroof, group="roof")
    estack = C.chimney_stonehood(ECD, ECW, ezr + 12.0 - ez0, seed=31).rotate([0, 0, 90]).translate([ex, ecy, ez0])
    kit.add("ELL-chimney", "Fieldstone", estack, group="roof")
    f = ewl["facade"]
    gcs = ewl["cs"]
    gwall = f.place(M.extrude(gcs, 3.0).translate([0, 0, -3.0]))
    gtex = f.place(C.fieldstone(gcs.offset(-0.3, JoinType.Miter, 4.0), datum=0.0, seed=77).translate([0, 0, -0.02]))
    kit.add("ELL-gable", "Fieldstone", gwall + gtex - eroof, group="walls")
    print("ell", round(time.time() - t0, 1))

    # --- the stoop: a stone platform, steps, a settle either side of the door
    kit.add("STOOP", "Ledge", _stoop() - fnd, group="stoop")
    kit.add("STEPS-front", "Ledge", _steps(), group="stoop")
    bench = C.settle_bench(BENCH_L)
    hood_half = DOOR_W / 2 + 1.3 + 0.79 + 1.5 + 0.3
    for k, u0 in enumerate((XC - hood_half - 1.0 - BENCH_L, XC + hood_half + 1.0)):
        Ab = np.array([[-1.0, 0, 0, u0 + BENCH_L], [0, -1.0, 0, -0.05], [0, 0, 1.0, ZF]])
        kit.add(f"SETTLE-{k}", "Oxblood", bench.transform(Ab), P=inv34(Ab), key="SETTLE", group="stoop")
    e, u = ELL.locate(EX1, 122.0)
    fe = ELL.facades()[e]
    A = fe.A.copy()
    A[:, 3] = fe.world(u, -ZF, 1.4)
    kit.add("STOOP-ell", "Ledge", FT.steps(14.0, ZF - 0.6, 4).transform(A) - fnd, group="stoop")
    e, u = MAIN.locate(94.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Ledge", FT.steps(14.0, ZF - 0.6, 4).transform(A) - fnd, group="stoop")
    print("specks dropped:", kit.drop_specks())
    print("stoop", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "pennock")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "pennock.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
