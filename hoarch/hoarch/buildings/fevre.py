"""The Fevre: an original HO-scale (1:87.1) hillside house of a Mississippi river town; house
104, of the new-layouts batch (hoarch.novel2), after the brick houses on the bluffs of
Galena, Illinois (the lead-mining town on the Fever River), 1840s-50s.

The house is set into a slope, and the slope is part of the model. To the street it shows three
storeys: a walk-out storey of tooled Galena limestone under two of red brick in common bond;
behind, the hill has climbed a storey, and the garden is level with the main floor. A
limestone wall runs along the street with steps up between gate piers to a front terrace; a
stone stair with an iron railing climbs along the front wall to a landing at the door on the
main floor, the landing carried on an arch over the walk-out storey's door. The house is
Federal with Greek Revival touches: six-over-six windows under tooled stone lintels with
louvered shutters, a door with an elliptical fanlight and leaded sidelights, a cornice of
swags and dentils, and parapeted gable ends carrying paired chimneys, coped in limestone, a
half-round lunette in each. Down the east side the garden steps in three terraces behind
limestone walls; down the west the lawn slopes away; at the back a small porch on Doric posts
opens onto the upper garden.

- Joint over the stone storey: a brick corbel table, a tooled limestone band.
- Storey joint: a diaper of raised brick, a limestone bead and reel, an ovolo.
- Eave: a sage frieze of swags and tassels, cream dentils, a cream soffit on modillions and a
  cyma.

usage: python3 -m hoarch.buildings.fevre [check] [export]
"""
import json
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, gables as G, novel2 as N, openings as O, roof as R
from hoarch.colonial import shutters_pair
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, lip_keep, lip_ring, stacked_shells

NAME = "The Fevre"
COLORS = {"Brick": "#8E3B2A", "Limestone": "#CFC6AE", "Cream": "#EFE6D2", "Sage": "#7E8C6E", "Green": "#2E4636",
          "Slate": "#4F555B", "Iron": "#2A2D30", "Turf": "#6B7F45", "Planks": "#7A5C40", "Windows_Doors": "#EFE6D2"}
RENDER_MAT = {"Brick": "brick", "Limestone": "stone", "Cream": "trim", "Sage": "accent", "Green": "shutter",
              "Slate": "roof", "Iron": "iron", "Turf": "turf", "Planks": "planks", "Windows_Doors": "trim",
              "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"brick": ["#8E3B2A", 0.85, 0.0], "stone": ["#CFC6AE", 0.9, 0.0], "trim": ["#EFE6D2", 0.6, 0.0],
           "accent": ["#7E8C6E", 0.6, 0.0], "shutter": ["#2E4636", 0.55, 0.0], "roof": ["#4F555B", 0.75, 0.0],
           "iron": ["#2A2D30", 0.45, 0.3], "turf": ["#6B7F45", 0.95, 0.0], "planks": ["#7A5C40", 0.75, 0.0],
           "sash": ["#EFE6D2", 0.5, 0.0], "door": ["#2E4636", 0.45, 0.0]}
VIEWS = {"hero": [-34, 16, 70, 0.9, [0, 0, -12]], "hero_right": [36, 16, 70, 0.9, [0, 0, -12]],
         "front": [0, 8, 85, 0.92, [0, 0, 0]], "rear": [155, 18, 70, 0.92, [0, 0, -12]],
         "stair": [-20, 10, 85, None, [86, 40, 34], 210], "terraces": [62, 18, 70, None, [196, 96, 30], 220]}

# ------------------------------------------------------------------ cornices (unique to the Fevre)
LEDGE = 1.4
JOINT0 = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.0, b=1.2, orn="fvcorbel", role="Brick"),
    dict(kind="course", h=2.2, b=1.6, orn="fvtooled", role="Limestone"),
    dict(kind="crown", h=1.4, b=1.6, P=2.8, orn="bevel", role="Limestone")])
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.0, b=1.2, orn="fvdiaper", role="Brick"),
    dict(kind="course", h=1.6, b=1.4, orn="fvbead", role="Limestone"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="ovolo", role="Limestone")])
EAVE = dict(pitch=10.0, margin=3.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="fvswags", role="Sage"),
    dict(kind="course", h=1.6, b=1.4, orn="fvdentil", role="Cream"),
    dict(kind="bed", h=2.2, b=1.4, P=5.6, role="Cream", brackets=dict(style="fvmodillion", t=1.6)),
    dict(kind="crown", h=2.4, b=1.4, P=6.4, orn="cyma", role="Cream")])
RJ = round((LEDGE + 0.4 + max(CO.band_height(JOINT), CO.band_height(JOINT0))) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels, plan and ground (front = -y)
ZT = 12.0                                       # the front terrace (the walk-out storey's floor)
ZJ0 = ZT + 30.0                                 # the stone storey's top (its joint ring above)
ZM = ZJ0 + RJ                                   # the main floor (the landing, the doors)
ZF = ZM                                         # (the audit reads the main floor as the first storey)
ZB = ZT                                         # (and the stone storey under it as a basement)
ZG = ZJ0 - 2.0                                  # the garden behind, just under the joint's ledge
S1 = ZM + 32.0                                  # the storey joint
ZU = S1 + RJ
ZE = ZU + 30.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
D_EAVE, S_ROOF = 3.0, 0.72
X0, X1, Y0, Y1 = 30.0, 182.0, 54.0, 134.0       # the house, 152 x 80
XC = (X0 + X1) / 2
MAIN = Block("main", [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)], ZT, ZW)
GX0, GX1, GY0, GY1 = 0.0, 220.0, 27.0, 160.0    # the ground behind the street wall
YW = 24.0                                       # the street wall's face
PAR = 3.0                                       # the parapets stand this far over the slates
# the stair along the front: flight from XS0 up to the landing XL0..XL1, the door over its middle
XS0, XL0, XL1 = 58.0, 92.0, 120.0
XD = (XL0 + XL1) / 2
YS = Y0 - 13.0                                  # the stair's outer face
# the east terraces (y from, y to, top z) and the back porch
TERR = [(Y0, 80.0, ZT + 8.0), (80.0, 106.0, ZT + 16.0), (106.0, Y1, ZG)]
BPX0, BPX1, BPD = XD - 20.0, XD + 20.0, 16.0
V1 = ZM - ZT + 6.0
V2 = ZU - ZT + 5.0
VB = 6.0


def _skin(f, b, reg):
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    lo = reg ^ rect(-1, -100, f.L + 1, ZJ0 - b.z0)
    mid = reg ^ rect(-1, ZM - b.z0, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, ZU - b.z0, f.L + 1, 999)
    out = []
    if not lo.is_empty():
        out.append(N.stone_fevre(lo, datum=0.0, seed=int(f.p0[0] + f.p0[1]) % 31))
    if not mid.is_empty():
        out.append(N.brick_fevre(mid, datum=ZM - b.z0 + 0.2))
    if not hi.is_empty():
        out.append(N.brick_fevre(hi, datum=ZU - b.z0 + 0.2))
    return union(out) if out else M()


def _openings():
    L0, L1, L2, LG = [], [], [], []
    fams = {}
    shut = set()

    def add(L, blk, x, y, v0, sp, name, kind="window", sh=False):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        L[-1].fam = fams.setdefault(id(sp), name)
        if sh:
            shut.add(name)

    base, main, upper = N.window_fvbase(), N.window_fvmain(), N.window_fvupper()
    plain, low = N.door_fvplain(), N.door_fvplain(h=16.0)
    # the walk-out storey: a window clear of the stair at each end, the door under the landing
    for x in (44.0, 138.0, 168.0):
        add(L0, MAIN, x, Y0, VB, base, f"S{x:.0f}-0")
    add(L0, MAIN, XD, Y0, 0.4, low, "base-door", "door")
    # the main floor: four windows and the door on the landing; five windows above
    for x in (46.0, 76.0, 136.0, 166.0):
        add(L1, MAIN, x, Y0, V1, main, f"S{x:.0f}-1", sh=True)
    add(L1, MAIN, XD, Y0, ZM - ZT + 0.4, N.door_fvfront(), "front-door", "door")
    for x in (46.0, 76.0, XD, 136.0, 166.0):
        add(L2, MAIN, x, Y0, V2, upper, f"S{x:.0f}-2", sh=True)
    # the ends: two bays each floor; the lunette in each gable
    for y in (76.0, 112.0):
        for x, tag in ((X0, "W"), (X1, "E")):
            add(L1, MAIN, x, y, V1, main, f"{tag}{y:.0f}-1", sh=True)
            add(L2, MAIN, x, y, V2, upper, f"{tag}{y:.0f}-2", sh=True)
    lun = N.window_fvlunette()
    for x, tag in ((X0, "W"), (X1, "E")):
        add(LG, MAIN, x, (Y0 + Y1) / 2, ZW - ZT + 4.0, lun, f"lunette-{tag}")
    # the back: the garden door and four windows; five above
    add(L1, MAIN, XD, Y1, ZM - ZT + 0.4, plain, "garden-door", "door")
    for x in (46.0, 76.0, 136.0, 166.0):
        add(L1, MAIN, x, Y1, V1, main, f"N{x:.0f}-1")
    for x in (46.0, 76.0, XD, 136.0, 166.0):
        add(L2, MAIN, x, Y1, V2, upper, f"N{x:.0f}-2")
    return L0, L1, L2, LG, shut


OPEN0, OPEN1, OPEN2, OPEN_G, SHUTTERED = _openings()
OPENINGS = OPEN0 + OPEN1 + OPEN2 + OPEN_G
BLOCKS = [MAIN]


def _place_inserts(kit, ops, keep, group="inserts"):
    for o in ops:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        part = kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{o.fam}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                       group=group, render=zones)
        keep.append(part.solid)
        if o.name in SHUTTERED:
            w_op, h_op = b[2] - b[0], b[3] - b[1]
            left, right = shutters_pair(w_op, h_op, casing=0.6, gap=0.5, make=N.shutter_fevre)
            for side, m in (("L", left), ("R", right)):
                kit.add(f"SHUTTER-{o.name}-{side}", "Green", m.translate([0, 0, 0.32]).transform(A), P=inv34(A),
                        key=f"SHUTTER-{h_op:.1f}", group="shutters")


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    path = MAIN.pts
    house_env = MAIN.solid(grow=0.15, dz0=-40, dz1=400)
    # what stands against the walls keeps them bare (no stone or brick dressing) and cuts the
    # joint ring and its cornice: the stair and its landing, the back porch
    rs_ = (ZM - ZT) / 12.0                         # one riser: the flight's keep-out runs a riser over its nosings
    stair_env = M.hull_points([(x, y, z) for y in (YS - 1.0, Y0 + 5.0) for x, z in
                               ((XS0 - 0.6, ZT - 1.0), (XL0, ZT - 1.0), (XS0 - 0.6, ZT + 2 * rs_), (XL0, ZM + rs_))]) + \
        box([XL0 - 0.6, YS - 1.0, ZT - 1.0], [XL1 + 0.6, Y0 + 5.0, ZM + 1.0])
    porch_env = box([BPX0 - 1.8, Y1 - 1.0, ZG - 1.0], [BPX1 + 1.8, Y1 + BPD + 2.0, S1 - 0.2])

    # --- the roof (between the parapets) and the parapeted gable walls
    pieces = [(path, [0, 2], S_ROOF)]
    gdefs = [dict(p0=(X1, Y0), p1=(X1, Y1), slope=S_ROOF, e=D_EAVE + 1.0), dict(p0=(X0, Y1), p1=(X0, Y0), slope=S_ROOF, e=D_EAVE + 1.0)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="square", tex_kw=dict(pitch=1.5, wtab=2.4, d=0.35), skin=1.8,
                       rake=-3.0, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    L_end = Y1 - Y0
    gables = []
    par_cs = []
    for e, wl in ((1, rf["walls"][0]), (3, rf["walls"][1])):
        s = wl["slope"]
        top = [(0.0, s * D_EAVE + PAR), (L_end / 2, s * (L_end / 2 + D_EAVE) + PAR), (L_end, s * D_EAVE + PAR)]
        cs = poly([(0.0, -FASCIA), (L_end, -FASCIA), top[2], top[1], top[0]])
        par_cs.append((wl, top))
        gables.append((MAIN, e, cs.translate((0.0, Z_EAVE - MAIN.z0))))

    # --- the house: a stone storey, two of brick, two joints, the ledge for the eave
    undress = [slab(offset(base, 10.0), ZE - LEDGE - 0.6, ZW + 0.01), stair_env, porch_env]
    st = stacked_shells([MAIN], OPENINGS, [ZJ0, S1], t=3.0, corners="none", siding=_skin, clear=[],
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress, gables=gables)
    # the stairs' landing and the flight stand against the stone storey: a plain face there
    kit.add("WALLS-0", "Limestone", st["shells"][0], group="walls")
    kit.add("JOINT-0", "Limestone", st["rings"][0] - stair_env - porch_env, group="walls")
    kit.add("WALLS-1", "Brick", st["shells"][1], group="walls")
    kit.add("JOINT", "Brick", st["rings"][1], group="walls")
    lip = _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)
    walls2 = st["shells"][2] + lip + CO.ledge(path, ZE, LEDGE)
    # the paired chimneys on each parapet, part of the wall (one brick part), each corbelled out
    # at the top under a stone-coloured band moulded in the brick
    stacks, stack_env = [], []
    for wl, top in par_cs:
        f = wl["facade"]
        s = wl["slope"]
        for uc in (13.0, L_end - 13.0):
            zr = Z_EAVE + s * (min(uc, L_end - uc) + D_EAVE)
            z1 = Z_EAVE + s * (L_end / 2 + D_EAVE) + 10.0
            ch = box([uc - 5.0, ZW - Z_EAVE, -4.6], [uc + 5.0, z1 - Z_EAVE, 1.6])
            cap = box([uc - 5.8, z1 - Z_EAVE - 3.0, -5.4], [uc + 5.8, z1 - Z_EAVE - 1.6, 2.4]) + \
                M.hull_points([(uc + dx, v, w) for dx in (-5.0, 5.0) for v, w in ((z1 - Z_EAVE - 3.8, -4.6), (z1 - Z_EAVE - 3.8, 1.6))] +
                              [(uc + dx, z1 - Z_EAVE - 3.0, w) for dx in (-5.8, 5.8) for w in (-5.4, 2.4)])
            flue = box([uc - 3.6, z1 - Z_EAVE - 1.6, -3.4], [uc + 3.6, z1 - Z_EAVE + 1.0, 0.4]) - box([uc - 0.5, z1 - Z_EAVE - 2.0, -4], [uc + 0.5, z1 - Z_EAVE + 2, 1])
            stacks.append(f.place((ch + cap - flue)))
            stack_env.append(f.place(box([uc - 6.0, ZW - Z_EAVE - 0.01, -5.6], [uc + 6.0, z1 - Z_EAVE + 3.0, 2.6])))
    stacks = union(stacks)
    stack_env = union(stack_env)
    walls2 = walls2 + stacks
    kit.add("WALLS-2", "Brick", walls2, group="walls")
    r0, _ = CO.level(st["outlines"][0], ZJ0 + LEDGE + 0.4, JOINT0, cut=stair_env + porch_env)
    CO.add_level(kit, r0, "CORNICE-J0", "cornice")
    r1, _ = CO.level(st["outlines"][1], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, r1, "CORNICE-J", "cornice")
    erings, _ = CO.level(path, ZE, EAVE)
    CO.add_level(kit, erings, "CORNICE-E", "cornice")
    ins_keep = []
    _place_inserts(kit, OPENINGS, ins_keep)
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the roof between the parapets, a ridge roll; the limestone copings on the parapets
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_ROOF * (L_end / 2 + D_EAVE)
    roof = roof + G.ridge_cap((X0 + 3.2, (Y0 + Y1) / 2), (X1 - 3.2, (Y0 + Y1) / 2), zr, S_ROOF, ZW, half=1.2, up=0.6)
    roof = roof - lip_keep(base, 3.0, ZW) - stack_env
    roof = roof - union([box([X0 - 10, Y0 - 10, ZW - 1], [X0 + 3.15, Y1 + 10, zr + 30]), box([X1 - 3.15, Y0 - 10, ZW - 1], [X1 + 10, Y1 + 10, zr + 30])])
    kit.add("ROOF", "Slate", max(roof.decompose(), key=lambda m_: m_.volume()), group="roof")
    for k, (wl, top) in enumerate(par_cs):
        cp = N.coping_fevre(L_end, wl["slope"], D_EAVE, w=4.4, th=1.6).translate([0.0, PAR, 0.0])
        f = wl["facade"]
        A = f.A.copy()
        A[:, 3] = f.world(0.0, 0.0, -1.5)
        cw = cp.transform(A) - stack_env
        for j, piece in enumerate(sorted(cw.decompose(), key=lambda m_: -m_.volume())[:3]):
            if piece.volume() > 5.0:
                kit.add(f"COPING-{k}-{j}", "Limestone", piece, P=inv34(A), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the stone stair along the front, its railings
    stair = N.stair_fevre(XS0, XL1, YS, Y0, ZT, ZM, n=12, landing=(14.0, XL1 - XL0))
    stair = stair - house_env
    st_ = st
    run, rise = XL0 - XS0, ZM - ZT
    rail = N.stair_rail_fevre(run, rise, h=9.0)
    A_r = np.array([[1.0, 0, 0, XS0], [0, 0, 1.0, YS + 0.3], [0, 1.0, 0, ZT + rise / 12.0 * 0.5]])
    railw = rail.transform(A_r)
    lrail = N.stair_rail_fevre(XL1 - XL0 - 0.6, 0.0, h=9.0)
    A_l = np.array([[1.0, 0, 0, XL0 + 0.3], [0, 0, 1.0, YS + 0.3], [0, 1.0, 0, ZM]])
    lrailw = lrail.transform(A_l)
    stair = stair - union([railw, lrailw])                  # the railings' newels and tabs sit in slots
    kit.add("STAIR", "Limestone", stair, group="stoop")
    kit.add("STAIR-rail", "Iron", railw - house_env, P=inv34(A_r), group="stoop")
    kit.add("LANDING-rail", "Iron", lrailw - house_env, P=inv34(A_l), group="stoop")
    print("stair", round(time.time() - t0, 1))

    # --- the ground: a lawn base (the front terrace, the west bank, the east terraces' fill and
    # the back garden), the street wall with its steps and gate piers, the terrace walls
    g = [box([GX0, GY0, 0.0], [GX1, GY1, ZT])]
    bank = M.hull_points([(x, y, z) for x in (GX0, X0) for y, z in ((Y0, 0.0), (Y0, ZT), (Y1, 0.0), (Y1, ZG))])
    g.append(bank)
    g.append(box([GX0, Y1, 0.0], [GX1, GY1, ZG]))
    for (ya, yb, z) in TERR:
        g.append(box([X1, ya, 0.0], [GX1, yb + 0.01, z]))
    ground = union(g)
    ground = ground - slab(offset(base, -4.0), -1.0, ZG + 10)          # hollow under the house
    ground = ground - MAIN.solid(grow=1.0, dz0=0.0, dz1=300)
    ground = ground - slab(offset(base, 6.0), ZJ0 - 2.0, 400)                # clear of the joint's ledge and cornice
    walls_t = [(Y0, ZT, TERR[0][2]), (TERR[0][1], TERR[0][2], TERR[1][2]), (TERR[1][1], TERR[1][2], TERR[2][2])]
    for (yb, zl, zu) in walls_t:                                        # notches for the terrace walls
        ground = ground - box([X1 + 1.0 - 0.15, yb - 0.2, zl - 0.01], [GX1 + 1, yb + 3.15, zu + 20])
    # the lot's outer faces (west, back, east) are dry limestone walls holding the ground up:
    # the ground is cut back 3 mm there, and each wall is its own part, its top following the
    # ground's edge under a coping
    LT = 3.0
    zt = lambda y: ZT if y <= Y0 else (ZG if y >= Y1 else ZT + (ZG - ZT) * (y - Y0) / (Y1 - Y0))
    G0 = GY0 + 0.65                                  # clear of the street wall's coping
    west = [(G0, 0.0), (GY1, 0.0), (GY1, ZG), (Y1, ZG), (Y0, ZT), (G0, ZT)]                  # (y, z), outer face at x = 0
    east = [(G0, 0.0), (GY1, 0.0), (GY1, ZG)] + [pt for (ya, yb, z) in TERR[::-1] for pt in ((yb, z), (ya, z))] + [(Y0, ZT), (G0, ZT)]
    back = [(GX0 + 3.4, 0.0), (GX1 - 3.4, 0.0), (GX1 - 3.4, ZG), (GX0 + 3.4, ZG)]           # (x, z), outer face at y = GY1
    lot = [("LOT-wall-W", west, np.array([[0, 0, -1.0, GX0], [-1.0, 0, 0, 0.0], [0, 1.0, 0, 0.0]]), True),
           ("LOT-wall-E", east, np.array([[0, 0, 1.0, GX1], [1.0, 0, 0, 0.0], [0, 1.0, 0, 0.0]]), False),
           ("LOT-wall-N", back, np.array([[1.0, 0, 0, 0.0], [0, 0, 1.0, GY1], [0, 1.0, 0, 0.0]]), False)]
    lot_parts = []
    for name, face_pts, A, flip_u in lot:
        pts_ = [(-u, v) for u, v in face_pts] if flip_u else face_pts
        face = poly(pts_)
        if face.area() < 0:
            face = poly(pts_[::-1])
        body = M.extrude(face, LT).translate([0, 0, -LT])
        cop = face - face.translate((0.0, -1.2))
        tex = N.stone_fevre(face - cop, seed=len(name))
        wall = body + tex + M.extrude(cop, LT + 1.0).translate([0, 0, -LT])            # flush inside: it prints on that face
        lot_parts.append((name, wall.transform(A), A))
    lot_env = union([w_ for _, w_, _ in lot_parts])
    ground = ground - box([GX0 - 1, GY0 - 1, -1], [GX0 + LT + 0.15, GY1 + 1, 200]) - box([GX1 - LT - 0.15, GY0 - 1, -1], [GX1 + 1, GY1 + 1, 200]) \
        - box([GX0 - 1, GY1 - LT - 0.15, -1], [GX1 + 1, GY1 + 1, 200])
    ground = ground - lot_env
    kit.add("GROUND", "Turf", ground, group="foundation")
    for name, w_, A in lot_parts:
        kit.add(name, "Limestone", w_, P=inv34(A), group="foundation")
    # a flagstone path from the gate to the stair's foot
    path_ = []
    rng = np.random.default_rng(11)
    y = GY0 + 0.6
    while y < YS - 0.6:
        L_ = rng.uniform(2.6, 3.6)
        path_.append(box([XS0 - 9.4, y, ZT], [XS0 + 4.4, min(y + L_ - 0.5, YS - 0.4), ZT + 0.6]))
        y += L_
    kit.add("PATH", "Limestone", union(path_), group="stoop")
    sw = box([GX0, YW, 0.0], [GX1, GY0 + 0.01, ZT])
    face = N.stone_fevre(rect(0.0, 0.0, GX1 - GX0, ZT - 1.2), seed=3)
    sw = sw + face.transform(np.array([[1.0, 0, 0, GX0], [0, 0, -1.0, YW + 0.03], [0, 1.0, 0, 0.0]]))
    sw = sw + M.hull(box([GX0, YW, ZT - 1.2], [GX1, GY0 + 0.01, ZT - 1.19]) + box([GX0 - 0.6, YW - 0.6, ZT - 0.6], [GX1 + 0.6, GY0 + 0.6, ZT + 0.4]))
    gate0, gate1 = XS0 - 10.0, XS0 + 6.0
    sw = sw - box([gate0, YW - 2, -1], [gate1, GY0 + 2, ZT + 5])
    for x in (gate0 - 2.4, gate1 + 2.4):
        sw = sw + box([x - 2.4, YW - 1.0, 0.0], [x + 2.4, GY0 + 0.4, ZT + 8.0]) + box([x - 3.0, YW - 1.6, ZT + 8.0], [x + 3.0, GY0 + 1.0, ZT + 9.2])
        sw = sw + M.sphere(2.2, 24).translate([x, (YW + GY0) / 2, ZT + 11.0])
    nst = 5
    for k in range(nst):
        z = ZT * (k + 1) / nst
        sw = sw + box([gate0, YW - 2.6 * (nst - 1 - k) - 2.6, 0.0], [gate1, GY0 + 0.01, round(z / 0.2) * 0.2])
    kit.add("STREET-WALL", "Limestone", sw, group="foundation")
    parts_ = {p_.name: p_ for p_ in kit.parts}
    parts_["GROUND"].solid = parts_["GROUND"].solid - sw
    for k, (yb, zl, zu) in enumerate(walls_t):
        L_ = GX1 - X1 - 1.6 - 3.0 - 1.0
        rw = N.retaining_fevre(L_, zu - zl + 1.2, t=3.0, seed=k)
        A = np.array([[1.0, 0, 0, X1 + 1.6], [0, 0, -1.0, yb], [0, 1.0, 0, zl]])
        rwm = rw.transform(A) - ground
        kit.add(f"TERRACE-wall-{k}", "Limestone", max(rwm.decompose(), key=lambda m_: m_.volume()), key=f"TERRACE-wall-{k}", group="foundation")
    print("ground", round(time.time() - t0, 1))

    # --- the back porch onto the garden: planked deck, a one-piece top on Doric posts
    pts = [(BPX0, Y1), (BPX1, Y1), (BPX1, Y1 + BPD), (BPX0, Y1 + BPD)]
    runs = [dict(a=(BPX1, Y1), b=(BPX1, Y1 + BPD), posts=[BPD - 1.6]),
            dict(a=(BPX1, Y1 + BPD), b=(BPX0, Y1 + BPD), posts=[1.6, (BPX1 - BPX0) / 2, BPX1 - BPX0 - 1.6]),
            dict(a=(BPX0, Y1 + BPD), b=(BPX0, Y1), posts=[1.6])]
    hf = ZM - ZG - 0.2
    post_h = round((S1 - 1.4 - 2.4 - ZM) / 0.2) * 0.2
    P = FT.porch_turned(pts, runs, hf, post_h, steps_at=[(1, (BPX1 - BPX0) / 2, 14.0)], inset=1.6, rail="fevre", beam=2.6,
                        post="fevre", arcade="fvplain", skirt="fvstone", pier_tex="coursed", roof_edge="fvdentilcap",
                        planks=dict(pitch=1.5, border=1.8), drop=2.0, top=True)
    T = [0, 0, ZG]
    deck = P["deck"].translate(T) - house_env - ground
    kit.add("PORCH-deck", "Limestone", deck, P=print_flip(), group="porch", render=FT.plank_zones(deck, ZG + hf, "Planks", "Limestone"))
    ins_box = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2], [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                     for b in (s_.bounding_box() for s_ in ins_keep)])
    P2 = dict(P)
    P2["top"] = P["top"].translate(T)
    P2["roof"] = P["roof"].translate(T)
    P2["applied"] = []
    bld_keep = MAIN.solid(grow=1.45, dz0=-20, dz1=300)
    FT.add_porch_top(kit, "PORCH", P2, bld_keep + ins_box, "Cream", "Cream", tin_col="Slate", tin="flat", group="porch")
    parts = {p_.name: p_ for p_ in kit.parts}
    for k, (sm, A) in enumerate(P["steps"]):
        A2 = A.copy()
        A2[:, 3] = A[:, 3] + np.array([0, 0, ZG])
        kit.add(f"PORCH-steps-{k}", "Limestone", sm.transform(A2) - deck - parts["PORCH-top"].solid - ground, group="porch")
    print("porch", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "fevre")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    json.dump({"materials": PALETTE, "views": VIEWS}, open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "fevre.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
