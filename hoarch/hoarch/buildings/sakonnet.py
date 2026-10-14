"""The Sakonnet: an original HO-scale (1:87.1) Shingle Style house under one great gable; house
102, the second of the new-layouts batch (hoarch.novel), after the W. G. Low House (Bristol,
Rhode Island, 1887) and Kragsyde (Manchester-by-the-Sea, 1883).

The whole house lives under a single enormous gable that faces the front: its eaves come down
to the top of the ground storey on both sides, so the upper floors are inside the roof. The
ground storey is squared rubble on a battered plinth of boulder-faced stones; across the front
it opens in a loggia of three broad round arches of rock-faced voussoirs, and at its west end a
carriage arch runs right through the house, front to back, with the drive passing under the
upper floor. The great gable is shingled, square butts with a band of diamond points every
ninth course; it jetties out over the loggia on a moulded girt, carries a ribbon of five
casements across its second floor, and high up a balcony sunk into the gable under a round arch,
with glazed doors at its back. At the east corner a round bay of ten facets rises out of the
ground, stone below and shingle above, and bursts up through the roof's edge under a flared
bell cap. Eyebrow dormers roll out of both slopes; two rubble chimneys with clay pots rise
through them. A kitchen lean-to runs along the back; a stone terrace with steps lies in front of
the loggia, boulders at its ends.

- Storey joint (the jetty's girt): an oxblood frieze of daisies on a wavy vine, a cream course
  of chevrons and beads, a cream ovolo.
- Eave (on the girt, under both eaves and across the gable feet: a double cornice): an oxblood
  course of chevrons and beads, a cream cavetto.
- The bay's cornice under its cap, and the lean-to's: the same daisies and chevrons.

usage: python3 -m hoarch.buildings.sakonnet [check] [export]
"""
import json
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import arch_cs, box, cs_union, inv34, ngon, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, gables as G, novel as N, openings as O, roof as R
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, belt_ring, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Sakonnet"
COLORS = {"Cedar": "#946746", "Fieldstone": "#8B857A", "Cream": "#EEE6CF", "Moss": "#4D5940", "Oxblood": "#6E2A22",
          "Boulder": "#77726A", "Planks": "#7A5C40", "Windows_Doors": "#EEE6CF"}
RENDER_MAT = {"Cedar": "shingle", "Fieldstone": "stone", "Cream": "trim", "Moss": "roof", "Oxblood": "accent",
              "Boulder": "stone2", "Planks": "planks", "Windows_Doors": "trim", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"shingle": ["#946746", 0.85, 0.0], "stone": ["#8B857A", 0.9, 0.0], "trim": ["#EEE6CF", 0.6, 0.0],
           "roof": ["#4D5940", 0.8, 0.0], "accent": ["#6E2A22", 0.6, 0.0], "stone2": ["#77726A", 0.95, 0.0],
           "planks": ["#7A5C40", 0.75, 0.0], "sash": ["#6E2A22", 0.5, 0.0], "door": ["#6E2A22", 0.45, 0.0]}
VIEWS = {"hero": [-34, 14, 70, 0.9, [0, 0, -10]], "hero_right": [36, 14, 70, 0.9, [0, 0, -10]],
         "front": [0, 6, 85, 0.92, [0, 0, 0]], "rear": [155, 16, 70, 0.92, [0, 0, -10]],
         "loggia": [-10, 8, 85, None, [90, -16, 26], 200], "roof": [-25, 40, 60, 1.0, [0, 0, 0]]}

# ------------------------------------------------------------------ cornices (unique to the Sakonnet)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="skdaisies", role="Oxblood"),
    dict(kind="course", h=1.4, b=1.4, orn="skchevronbead", role="Cream"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="ovolo", role="Cream")])
SMALL = dict(pitch=9.0, margin=2.5, layers=[
    dict(kind="frieze", h=3.6, b=1.2, orn="skdaisies", role="Oxblood"),
    dict(kind="course", h=1.2, b=1.2, orn="skchevronbead", role="Cream"),
    dict(kind="crown", h=2.0, b=1.2, P=3.4, orn="ovolo", role="Cream")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.4, b=1.4, orn="skchevronbead", role="Oxblood"),
    dict(kind="crown", h=2.2, b=1.4, P=4.6, orn="cavetto", role="Cream")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HS = CO.band_height(SMALL)
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan (front = -y)
ZF = 8.0
S1 = ZF + 36.0
ZU = S1 + RJ                                   # the upper storey's foot (on the girt)
ZK = ZU + HE                                   # the knee under the eaves, wrapped by the eave cornice (the girt's lip
                                               # below, the roof's corbel above)
FASCIA = 1.6
Z_EAVE = ZK + FASCIA
S_ROOF, D_EAVE, RAKE, SKIN = 0.8, 7.0, 6.0, 1.8
W, D, JET = 176.0, 100.0, 6.0
XC = W / 2
LG0, LG1, LGY = 44.0, 136.0, 16.0              # the loggia: its arcade on the front line, its back wall at y = LGY
LOW = Block("lower", [(0, 0), (LG0, 0), (LG0, LGY), (LG1, LGY), (LG1, 0), (W, 0), (W, D), (0, D)], ZF, S1)
UP = Block("upper", [(0, -JET), (W, -JET), (W, D), (0, D)], ZU, ZK)
BC, BR, BN = (W - 18.0, -4.0), 14.0, 10        # the round bay: centre, apothem, facets
BZE = ZU + 26.0                                # its walls' top
BZW = round((BZE + HS) / 0.2) * 0.2
BAYL = Block("bay-lo", ngon(BC, BR, n=BN), ZF, S1)
BAYU = Block("bay-up", ngon(BC, BR, n=BN), ZU, BZW)
CX0, CX1 = 8.0, 34.0                           # the carriage passage
CAR_SPRING = 12.0                              # its arch springs this far over ZF
LN = Block("lean", [(48.0, D), (132.0, D), (132.0, D + 20.0), (48.0, D + 20.0)], ZF, ZF + 22.0)
LZE = ZF + 22.0
LZW = round((LZE + HS) / 0.2) * 0.2
V1 = 6.0
CHIMS = [(54.0, 70.0), (130.0, 34.0)]


def _rubble(f, b, reg):
    reg = reg - rect(-1, S1 - LEDGE - 0.6 - b.z0, f.L + 1, 999)
    return N.rubble_sakonnet(reg, datum=0.0, seed=int(abs(f.p0[0]) * 3 + abs(f.p0[1])) % 89)


def _shingles(f, b, reg):
    if b is BAYU:
        reg = reg - rect(-1, BZE - LEDGE - 0.6 - b.z0, f.L + 1, 999)
    return N.shingles_sakonnet(reg, datum=0.0)


def _lean_skin(f, b, reg):
    reg = reg - rect(-1, LZE - LEDGE - 0.6 - b.z0, f.L + 1, 999)
    return N.shingles_sakonnet(reg, datum=0.0)


def _openings():
    L1, L2, LB, LL = [], [], [], []
    fams = {}

    def add(L, blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        L[-1].fam = fams.setdefault(id(sp), name)

    lo = N.window_sklower()
    # the loggia's back wall: the door between two windows
    add(L1, LOW, XC + 2.0, LGY, 0.4, N.door_skloggia(), "front-door", "door")
    for x in (LG0 + 16.0, LG1 - 16.0):
        add(L1, LOW, x, LGY, V1, lo, f"L{x:.0f}")
    # the carriage arch, front and back
    car = N.arch_skrock(w=CX1 - CX0, spring=ZF + CAR_SPRING, depth=3.0)
    add(L1, LOW, (CX0 + CX1) / 2, 0.0, -ZF, car, "carriage-S", "door")
    add(L1, LOW, (CX0 + CX1) / 2, D, -ZF, car, "carriage-N", "door")
    for x_, tag in ((0.0, "W"), (W, "E")):
        for y in (34.0, 70.0):
            add(L1, LOW, x_, y, V1, lo, f"{tag}{y:.0f}")
    for x in (146.0, 164.0):
        add(L1, LOW, x, D, V1, lo, f"N{x:.0f}")
    # the bay: three facets towards the street, both storeys
    bw = N.window_skbay()
    pts = ngon(BC, BR, n=BN)
    for k in (BN - 1, 0, 1):
        a, b = np.array(pts[k]), np.array(pts[(k + 1) % BN])
        m = (a + b) / 2
        add(LB, BAYL, m[0], m[1], V1, bw, f"bay{k}-1")
        add(LB, BAYU, m[0], m[1], 5.0, bw, f"bay{k}-2")
    # the great gable: the ribbon, the balcony; the back gable: four casements and an attic light
    add(L2, UP, XC, -JET, ZK - ZU + 3.0, N.window_skribbon(), "ribbon")
    add(L2, UP, XC, -JET, ZK - ZU + 30.0, N.balcony_sakonnet(), "balcony")
    bk = N.window_skback()
    for x in (52.0, 74.0, 102.0, 124.0):
        add(L2, UP, x, D, ZK - ZU + 5.0, bk, f"N{x:.0f}-2")
    add(L2, UP, XC, D, ZK - ZU + 32.0, N.window_skback(10.0, 12.0), "N-attic")
    # the lean-to
    add(LL, LN, 90.0, D + 20.0, 0.4, N.door_skback(8.0, 16.0), "kitchen-door", "door")
    for x in (64.0, 116.0):
        add(LL, LN, x, D + 20.0, V1, N.window_skbay(7.0, 12.0), f"K{x:.0f}")
    return L1, L2, LB, LL


OPEN1, OPEN2, OPEN_B, OPEN_L = _openings()
OPEN_BL = [o for o in OPEN_B if o.block is BAYL]
OPEN_BU = [o for o in OPEN_B if o.block is BAYU]
OPENINGS = OPEN1 + OPEN2 + OPEN_B + OPEN_L
BLOCKS = [LOW, UP, BAYL, BAYU, LN]


def _place_inserts(kit, ops, keep):
    for o in ops:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        part = kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{o.fam}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                       group="inserts", render=zones)
        keep.append(part.solid)


def _arcade(ins_keep, kit):
    """The loggia's front: a rubble wall on the front line from LG0 to LG1, three round arches of
    rock-faced voussoirs through it (their surrounds placed as inserts)."""
    t = 3.0
    wall = box([LG0 - 0.01, 0.0, ZF], [LG1 + 0.01, t, S1])
    skin = N.rubble_sakonnet(rect(0.0, 0.0, LG1 - LG0, S1 - LEDGE - 0.6 - ZF), seed=31)
    A = np.array([[1.0, 0, 0, LG0], [0, 0, -1.0, 0.03], [0, 1.0, 0, ZF]])
    wall = wall + skin.transform(A)
    aw, pier = 24.0, (LG1 - LG0 - 3 * 24.0) / 4
    sp = N.arch_skrock(w=aw, spring=16.0, depth=t, ring=1.8, n=13)
    for k in range(3):
        xc = LG0 + pier + aw / 2 + k * (aw + pier)
        Af = np.array([[1.0, 0, 0, xc], [0, 0, -1.0, 0.0], [0, 1.0, 0, ZF]])
        cut = M.extrude(sp["cut"], t + 2.0).translate([0, 0, -t - 1.0]).transform(Af)
        land = M.extrude(sp["landing"], 1.2).translate([0, 0, -0.05]).transform(Af)
        wall = wall - cut - land
        world, P, zones = O.place(sp, Af, "Windows_Doors", "Door", "Glass")
        part = kit.add(f"ARCH-loggia-{k}", "Windows_Doors", world, P=P, key="ARCH-loggia", group="inserts", render=zones)
        ins_keep.append(part.solid)
    return wall


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    bay_cs = BAYL.cs
    low_cs = cs_union([LOW.cs, bay_cs])
    up_cs = cs_union([UP.cs, bay_cs])
    up_path = max(up_cs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    lean_env = LN.solid(grow=0.15, dz0=-20, dz1=40) + box([LN.pts[0][0] - 5.0, D - 1.0, -1.0], [LN.pts[1][0] + 5.0, D + 6.0, S1])

    # --- the great gable roof (its gable walls go into the upper shell)
    gdefs = [dict(p0=(0.0, -JET), p1=(W, -JET), slope=S_ROOF, e=0.3), dict(p0=(W, D), p1=(0.0, D), slope=S_ROOF, e=0.3)]
    rf = G.gabled_roof([(UP.pts, [1, 3], S_ROOF)], Z_EAVE, D_EAVE, gdefs, texture="square", tex_kw=dict(pitch=1.5, wtab=2.0, d=0.38),
                       skin=SKIN, rake=RAKE, inner_cs=offset(UP.cs, -3.0), fascia=FASCIA, hollow=2.8)
    wf, wb = rf["walls"]
    gables = [(UP, 0, wf["cs"].translate((0.0, Z_EAVE - ZU))), (UP, 2, wb["cs"].translate((0.0, Z_EAVE - ZU)))]
    zr = Z_EAVE + S_ROOF * (W / 2 + D_EAVE)
    solid_env, _ = R.hip_roof([(UP.pts, [1, 3], S_ROOF)], Z_EAVE, S_ROOF, D_EAVE, texture=None, zlo=ZK)
    bay_env = slab(offset(bay_cs, 0.7), ZU - 1.0, BZW + 0.01)

    # --- the ground storey: rubble, the passage walls, the loggia's arcade
    ins_keep = []
    w1 = wall_shell([LOW, BAYL], OPEN1 + OPEN_BL, t=3.0, belt=None, corners="none", water_table=False, siding=_rubble,
                    undress=[lean_env],
                    partitions=[((CX0 - 1.0, 3.0), (CX0 - 1.0, D - 3.0), 2.0, ZF, S1), ((CX1 + 1.0, 3.0), (CX1 + 1.0, D - 3.0), 2.0, ZF, S1)])
    w1 = w1 + _arcade(ins_keep, kit)
    w1 = w1 - lip_keep(low_cs, 3.0, ZF, 1.2)
    w1 = w1 + _corbel(low_cs, 3.0, S1) + lip_ring(low_cs, 3.0, S1)
    kit.add("WALLS-1", "Fieldstone", w1, group="walls")
    # the girt: the joint ring jettied out over the front, its soffit under the overhang
    ring = belt_ring(up_path, S1, t=3.0, prof=CO.joint_profile(RJ, LEDGE), blocks=None)
    soffit = box([0.0, -JET, S1], [W, 3.0, S1 + 1.6]) - slab(offset(bay_cs, -0.01), S1 - 1, S1 + 3)
    ring = (ring + soffit) - lip_keep(low_cs, 3.0, S1)
    kit.add("JOINT", "Fieldstone", ring, group="walls")
    rings, _ = CO.level(up_path, S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    _place_inserts(kit, OPEN1 + OPEN_BL, ins_keep)
    print("ground storey", round(time.time() - t0, 1))

    # --- the upper shell: the two gables, the knee under the eaves, the bay's upper storey
    undress = [slab(offset(bay_cs, 8.0), BZE - LEDGE - 0.6, BZW + 0.01) - slab(offset(UP.cs, -0.2), 0, 999),
               slab(offset(up_cs, 8.0), ZU - 0.1, ZK + 0.01)]
    w2 = wall_shell([UP], OPEN2, t=3.0, belt=None, corners="none", water_table=False, siding=_shingles,
                    gables=gables, undress=undress)
    # the bay's upper storey: its own full ring, so it closes behind where it rises through the roof
    wb2 = wall_shell([BAYU], OPEN_BU, t=3.0, belt=None, corners="none", water_table=False, siding=_shingles, undress=undress)
    w2 = w2 + wb2
    w2 = w2 - lip_keep(up_cs, 3.0, ZU)
    no_lip = union([box([-1, -JET - 1, ZK - 1], [W + 1, -JET + 5.0, ZK + 5]), box([-1, D - 5.0, ZK - 1], [W + 1, D + 1, ZK + 5])])
    w2 = w2 + ((_corbel(UP.cs, 3.0, ZK) + lip_ring(UP.cs, 3.0, ZK)) - no_lip - bay_env)
    w2 = w2 + (CO.ledge(BAYU.pts, BZE, LEDGE) - solid_env)
    kit.add("WALLS-2", "Cedar", w2, group="walls")
    erings, _ = CO.level(up_path, ZU, EAVE)
    CO.add_level(kit, erings, "CORNICE-E", "cornice")
    _place_inserts(kit, OPEN2 + OPEN_BU, ins_keep)
    print("upper shell", round(time.time() - t0, 1))

    # --- the roof: shingles, a ridge cap, eyebrows, the two stacks in buckets, cut round the bay
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((XC, -JET - RAKE), (XC, D + RAKE), zr, S_ROOF, ZK) - walls_env)
    eyes = []
    for name, pl, c, e in (("W", ((0.0, 0.0), (1, 0), Z_EAVE + S_ROOF * D_EAVE, S_ROOF), (24.0, 62.0), (0.0, -1.0)),
                           ("E", ((W, 0.0), (-1, 0), Z_EAVE + S_ROOF * D_EAVE, S_ROOF), (W - 24.0, 52.0), (0.0, 1.0))):
        hump, Ae = N.eyebrow_hump(pl, c, e, 19.0, 9.0, 42.0)
        roof = roof + hump
        sp = N.window_skeyebrow(22.0, 6.4)
        Af = Ae.copy()
        Af[:, 3] = Ae[:, 3] + np.array([0.0, 0.0, 0.9])
        land = M.extrude(sp["landing"], 3.0).translate([0, 0, -2.0]).transform(Af)
        plug = M.extrude(sp["cut"], 3.0).translate([0, 0, -2.6]).transform(Af)
        roof = roof - land - plug
        eyes.append((name, sp, Af))
    for cx, cy in CHIMS:
        CW, CD = 12.0, 9.0
        d_low = min(cx - CW / 2, W - cx - CW / 2) + D_EAVE
        z_low = Z_EAVE + S_ROOF * d_low
        z0 = round((z_low - 2.6) / 0.2) * 0.2
        roof = roof + G.pocket_seat(solid_env, cx, cy, CW / 2 + 0.6, CD / 2 + 0.6, z0)
        roof = roof - box([cx - CW / 2 - 0.6, cy - CD / 2 - 0.6, z0], [cx + CW / 2 + 0.6, cy + CD / 2 + 0.6, zr + 60])
        h = round((zr + 8.0 - z0) / 0.2) * 0.2
        kit.add(f"CHIMNEY-{len([p for p in kit.parts if p.name.startswith('CHIMNEY')])}", "Fieldstone",
                N.chimney_sakonnet(CW, CD, h).translate([cx, cy, z0]), key=f"CHIMNEY-{h:.0f}", group="roof")
    roof = roof - bay_env - lip_keep(UP.cs, 3.0, ZK)
    kit.add("ROOF", "Moss", roof, group="roof")
    for name, sp, Af in eyes:
        world, P, zones = O.place(sp, Af, "Windows_Doors", "Sash", "Glass")
        kit.add(f"WIN-eyebrow-{name}", "Windows_Doors", world, P=P, key="WIN-eyebrow", group="roof", render=zones)
    print("roof", round(time.time() - t0, 1))

    # --- the bay's cornice and its bell cap, both cut where they run into the roof
    brings, _ = CO.level(BAYU.pts, BZE, SMALL, cut=solid_env + walls_env + roof + [p_ for p_ in kit.parts if p_.name == "WALLS-2"][0].solid.offset(0.0) if False else solid_env + walls_env + roof)
    w2s = [p_ for p_ in kit.parts if p_.name == "WALLS-2"][0].solid
    brings = [dict(r, solid=r["solid"] - w2s) for r in brings]
    CO.add_level(kit, brings, "CORNICE-BAY", "cornice")
    cap, ztop = N.bay_cap_sakonnet(BC, BR + 3.0, BZW, n=BN)
    cap = cap - solid_env - roof
    kit.add("BAY-cap", "Moss", max(cap.decompose(), key=lambda m_: m_.volume()), group="roof")
    print("bay", round(time.time() - t0, 1))

    # --- base, passage curbs, loggia floor, terrace with its boulders and steps
    fnd = foundation([Block("f", [(0, 0), (W, 0), (W, D), (0, D)], ZF, S1), BAYL], 0.0, ZF, style="skboulders",
                     openings=[(o.block.facades()[o.edge], o.u, -ZF - 1.0, CX1 - CX0 + 9.0, ZF + 2.0) for o in OPEN1 if o.name.startswith("carriage")])
    curbs = union([box([x - 1.0, 3.0, 0.0], [x + 1.0, D - 3.0, ZF]) for x in (CX0 - 1.0, CX1 + 1.0)])
    fnd = fnd + curbs - union([box([x - 1.05, 2.0, ZF], [x + 1.05, D - 2.0, ZF + 3.0]) for x in (CX0 - 1.0, CX1 + 1.0)])
    fnd = fnd - [p_ for p_ in kit.parts if p_.name == "WALLS-1"][0].solid
    kit.add("FOUNDATION", "Boulder", fnd, group="foundation")
    zd = ZF - 0.2
    deck = box([LG0 + 3.0, 3.15, 0.0], [LG1 - 3.0, LGY - 0.15, zd])
    grooves = union([box([x - 0.25, 3.5, zd - 0.4], [x + 0.25, LGY - 0.5, zd + 1.0]) for x in np.arange(LG0 + 4.2, LG1 - 3.0, 1.6)])
    deck = deck - grooves - fnd
    kit.add("LOGGIA-deck", "Planks", deck, group="loggia")
    zt = ZF - 2.4
    terr = box([LG0 - 6.0, -18.0, 0.0], [LG1 + 6.0, -0.9, zt])
    tskin = N.rubble_sakonnet(rect(0.0, 0.4, LG1 - LG0 + 12.0, zt - 0.4), seed=5)
    terr = terr + tskin.transform(np.array([[1.0, 0, 0, LG0 - 6.0], [0, 0, -1.0, -18.0 + 0.03], [0, 1.0, 0, 0.0]]))
    rng = np.random.default_rng(7)
    boulders = []
    for (bx, by, r) in ((LG0 - 7.0, -10.0, 6.0), (LG1 + 7.5, -12.0, 5.2), (LG0 - 4.0, -19.0, 3.6), (W + 3.0, 90.0, 5.0), (-4.0, 104.0, 5.6)):
        b = M.sphere(r, 24).scale([1.0 + 0.25 * rng.random(), 0.85 + 0.25 * rng.random(), 0.62])
        b = b.translate([bx, by, 0.0]).trim_by_plane([0, 0, 1.0], 0.0)
        boulders.append(b)
    terr = terr + union(boulders[:3])
    fnd_b = union(boulders[3:])
    fr = LOW.facades()[0]
    Ast = fr.A.copy()
    Ast[:, 3] = fr.world(XC + 2.0, -ZF, 18.0)
    steps = FT.steps(18.0, zt - 0.4, 3).transform(Ast)
    kit.add("TERRACE", "Boulder", terr - fnd, group="terrace")
    kit.add("TERRACE-steps", "Boulder", steps - terr - fnd, group="stoop")
    parts_ = {p_.name: p_ for p_ in kit.parts}
    parts_["FOUNDATION"].solid = parts_["FOUNDATION"].solid + (fnd_b - parts_["WALLS-1"].solid)
    print("base + terrace", round(time.time() - t0, 1))

    # --- the kitchen lean-to: shingled walls, its cornice, a shed roof against the house
    house_env = union([Block("h", [(0, 0), (W, 0), (W, D), (0, D)], ZF, S1).solid(grow=0.15, dz0=-20, dz1=300)])
    lw = wall_shell([LN], OPEN_L, t=3.0, belt=None, corners="none", water_table=False, siding=_lean_skin,
                    undress=[slab(offset(LN.cs, 8.0), LZE - LEDGE - 0.6, LZW + 0.01)])
    lw = (lw - lip_keep(LN.cs, 3.0, ZF, 1.2) + CO.ledge(LN.pts, LZE, LEDGE)) - house_env
    lfnd = foundation([LN], 0.0, ZF, style="skboulders") - house_env - [p_ for p_ in kit.parts if p_.name == "FOUNDATION"][0].solid
    kit.add("LEAN-FOUNDATION", "Boulder", max(lfnd.decompose(), key=lambda m_: m_.volume()), group="lean")
    kit.add("LEAN-WALLS", "Cedar", max(lw.decompose(), key=lambda m_: m_.volume()), group="lean")
    lrings, _ = CO.level(LN.pts, LZE, SMALL, cut=house_env)
    CO.add_level(kit, lrings, "CORNICE-LEAN", "cornice")
    _place_inserts(kit, OPEN_L, ins_keep)
    LZ_EAVE = LZW + 1.2
    s_l = round((S1 - 2.4 - LZ_EAVE) / 24.6, 3)
    lr, ltex = R.hip_roof([(LN.pts, [2], s_l)], LZ_EAVE, s_l, 4.0, texture="square", tex_kw=dict(pitch=1.5, wtab=2.0, d=0.38), zlo=LZW)
    lroof = (lr + ltex) - house_env
    kit.add("LEAN-ROOF", "Moss", max(lroof.decompose(), key=lambda m_: m_.volume()), group="lean")
    e, u = LN.locate(90.0, D + 20.0)
    fb = LN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 0.0)
    stoop = FT.steps(14.0, ZF - 0.6, 3).transform(A)
    # the base is cut back flat behind the step, so the step's back glues over its whole face
    sb = stoop.bounding_box()
    pp = {p_.name: p_ for p_ in kit.parts}
    pp["LEAN-FOUNDATION"].solid = pp["LEAN-FOUNDATION"].solid - box([sb[0] - 0.1, D + 20.0, -1.0], [sb[3] + 0.1, sb[4] + 1.0, ZF - 0.5])
    pp["LEAN-FOUNDATION"].solid = pp["LEAN-FOUNDATION"].solid - stoop
    pp["LEAN-WALLS"].solid = pp["LEAN-WALLS"].solid - stoop
    kit.add("STOOP-back", "Boulder", stoop, group="stoop")
    print("lean-to", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "sakonnet")
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
    kit.render_npz(os.path.join(OUT, "sakonnet.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
