"""The Oakhurst: an original HO-scale (1:87.1) Southern Colonial, house 33 of the third batch
(after the user's photo 3).

A five-bay house of buttermilk-painted brick in American bond with Flemish header courses, on
a raised basement of red brick with arched vents under a stone water table. Across the middle
of the front a giant portico: four fluted Greek Doric columns on a planked floor up a broad
flight of steps, an architrave of two fasciae, and a pediment with a fanned lunette in its
tympanum; its ceiling coffered and painted haint blue. Under it a Greek Revival entrance (a
pair of panelled leaves between sidelights, the lights leaded in lozenges, pilasters and a
lintel with a tablet) and, above it, a French door onto a balcony railed in wrought-iron
scrolls. Six-over-nine windows below under pedimented lintels, six-over-six above under
tabled lintels, charleston-green plantation shutters. Between the storeys a haint-blue frieze
of pineapples, a white billet course and a white ovolo; at the eave and round the portico a
frieze of magnolia blossoms, white dentils and a white cyma. A pewter slate hip roof banded
with keyed courses, a dormer with a segmental pediment on each end, two Flemish-bond stacks
with acroterion caps, and a square cupola with arched louvers under a ribbed copper dome. To
the east a one-storey wing (a frieze of lotus and bud) carries a roof terrace behind a
balustrade of flat-sawn vase balusters, reached by a French door from the upper floor.

usage: python3 -m hoarch.buildings.oakhurst [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import Facade, box, circle, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import colonial as C, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext, stroke
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Oakhurst"
COLORS = {"Buttermilk": "#E4D6B8", "White": "#F2F0EA", "Charleston": "#26332D", "Pewter": "#5B636B",
          "Verdigris": "#6FA38F", "Haint": "#A8CCCB", "Brick": "#8A4032", "PorchDeck": "#F2F0EA",
          "Windows_Doors": "#F2F0EA"}
RENDER_MAT = {"Buttermilk": "brick", "White": "trim", "Charleston": "shutter", "Pewter": "roof", "Verdigris": "accent",
              "Haint": "haint", "Brick": "brick2", "PorchDeck": "trim", "Planks": "planks", "Windows_Doors": "trim",
              "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Oakhurst)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.8, b=1.2, orn="pineapples", role="Haint"),
    dict(kind="course", h=1.4, b=1.4, orn="billet", role="White"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="ovolo", role="White")])
EAVE = dict(pitch=11.0, margin=4.0, layers=[
    dict(kind="frieze", h=6.0, b=1.2, orn="magnolias", role="Haint"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="White", tooth=0.9, gap=0.6),
    dict(kind="crown", h=3.2, b=1.4, P=7.0, orn="cyma", role="White")])
WING_C = dict(pitch=10.0, margin=3.4, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="lotus", role="Haint"),
    dict(kind="crown", h=2.2, b=1.4, P=4.0, orn="stepped", role="White")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)
SLATE = ("square", "square", "key")

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 16.0                                     # a raised basement
S1 = ZF + 46.0
ZE = S1 + RJ + 42.0
ZW = ZE + HE
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 8.0, 3.6, 1.8
S_MAIN, S_PED = 0.7, 0.42
V1 = 3.0
V2 = S1 + RJ + 5.0 - ZF
WING_ZE = ZF + 48.0
WING_ZW = WING_ZE + CO.band_height(WING_C)
DECK_T = 1.4

# ------------------------------------------------------------------ plan (x east, y north; the front faces south)
W, D = 180.0, 104.0
XC = W / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
WX1, WY0, WY1 = 232.0, 20.0, 84.0
WING = Block("wing", [(W - 3.0, WY0), (WX1, WY0), (WX1, WY1), (W - 3.0, WY1)], ZF, WING_ZW)
BLOCKS = [MAIN, WING]
# the giant portico: its beam (an architrave from ZA up, the eave cornice round it) on four columns
PX0, PX1, PD, PB = 40.0, 140.0, 26.0, 6.0
ZA = ZE - 5.0
COL_R = 3.6
COL_Y = -PD + PB / 2
COL_X = [PX0 + PB / 2 + (PX1 - PX0 - PB) * k / 3 for k in range(4)]
PORT_PTS = [(PX0, -PD), (PX1, -PD), (PX1, 0.0), (PX0, 0.0)]
BAL_W, BAL_D = 26.0, 7.0
SHUT_CAS, SHUT_GAP = 1.2, 0.9


def _brick(f, b, reg):
    """American bond with Flemish header courses; nothing in the cornice bands."""
    top = (WING_ZE if b is WING else ZE) - b.z0
    reg = reg - rect(-1, top - LEDGE - 0.6, f.L + 1, 999)
    return C.brick_american(reg, datum=0.0)


def _openings():
    L, SH = [], []

    def add(blk, x, y, v0, sp, name, kind="window", shutters=False):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        if shutters:
            SH.append(name)

    lo = C.window_greek(10.8, 32.0, "pediment", rows=(3, 2))
    up = C.window_greek(10.8, 25.0, "tablet")
    french = C.door_greek(11.0, 28.0, side=0.0, glazed=True)
    for x in (20.0, 58.0, W - 58.0, W - 20.0):
        add(MAIN, x, 0.0, V1, lo, f"S{x:.0f}-1", shutters=True)
    add(MAIN, XC, 0.0, 0.4, C.door_greek(12.0, 34.0), "front-door", "door")
    for x in (20.0, 58.0, W - 58.0, W - 20.0):
        add(MAIN, x, 0.0, V2, up, f"S{x:.0f}-2", shutters=True)
    add(MAIN, XC, 0.0, S1 + RJ + 1.2 + 0.2 - ZF, french, "balcony-door", "door")
    for y in (30.0, 74.0):
        add(MAIN, 0.0, y, V1, lo, f"W{y:.0f}-1", shutters=True)
        add(MAIN, 0.0, y, V2, up, f"W{y:.0f}-2", shutters=True)
        add(MAIN, W, y, V2, up, f"E{y:.0f}-2", shutters=True)
    add(MAIN, W, 52.0, WING_ZW + DECK_T + 0.2 - ZF, french, "terrace-door", "door")
    for x in (20.0, 58.0, W - 58.0, W - 20.0):
        add(MAIN, x, D, V1, lo, f"N{x:.0f}-1", shutters=True)
    add(MAIN, XC, D, 0.4, C.door_greek(11.0, 30.0, side=0.0), "back-door", "door")
    for x in (20.0, 58.0, XC, W - 58.0, W - 20.0):
        add(MAIN, x, D, V2, up, f"N{x:.0f}-2", shutters=True)
    # the wing
    wx = (W + WX1) / 2
    add(WING, wx, WY0, V1, lo, "wingS-1", shutters=True)
    add(WING, wx, WY1, V1, lo, "wingN-1", shutters=True)
    for y in (36.0, 68.0):
        add(WING, WX1, y, V1, lo, f"wingE{y:.0f}-1", shutters=True)
    return L, SH


OPENINGS, SHUTTERED = _openings()


def _faced_block(x0, x1, y0, y1, z1, faces, seed=0):
    """A block with the arcaded brick facing on the named faces ("S", "E", "W")."""
    body = box([x0, y0, 0.0], [x1, y1, z1])
    fs = {"S": ((x0, y0), (x1, y0)), "E": ((x1, y0), (x1, y1)), "W": ((x0, y1), (x0, y0))}
    for k in faces:
        f = Facade(*fs[k], 0.0)
        body = body + f.place(C.foundation_arcaded(rect(0.0, 0.0, f.L, z1), seed=seed).translate([0, 0, -0.02]))
    return body


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    wing_zone = box([W - 1.0, WY0 - 6.0, ZF], [WX1 + 8.0, WY1 + 6.0, S1 + RJ + 12.0])
    undress = [slab(offset(base, 9.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(WING.cs, 8.0) - offset(base, 0.5), WING_ZE - LEDGE - 0.6, WING_ZW + 0.01),
               box([W - 1.0, WY0 - 1.0, WING_ZW - 0.5], [W + 2.0, WY1 + 1.0, S1 + RJ + 9.0]),     # behind the terrace
               box([XC - BAL_W / 2 - 1.0, -2.0, S1 + RJ - 0.2], [XC + BAL_W / 2 + 1.0, 1.0, S1 + RJ + 9.0]),
               box([PX0 - 0.5, -2.0, ZA - 0.5], [PX0 + PB + 0.5, 1.0, ZW + 1.0]),                   # the beam's ends
               box([PX1 - PB - 0.5, -2.0, ZA - 0.5], [PX1 + 0.5, 1.0, ZW + 1.0])]
    allcs = cs_union([b_.cs for b_ in BLOCKS])
    clear = [lip_keep(allcs, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_brick, clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((XC - 24.0, 3.0), (XC - 24.0, D - 3.0), 2.0, ZF, ZW)])
    main_keep = MAIN.solid(grow=0.8, dz0=-2, dz1=400)
    wing_ledge = CO.ledge(WING.pts, WING_ZE, LEDGE) - main_keep
    wing_lip = (_corbel(WING.cs, 3.0, WING_ZW) + lip_ring(WING.cs, 3.0, WING_ZW)) - MAIN.solid(grow=0.2, dz0=-2, dz1=400)
    # the wing's walls run on above the storey joint, behind its cornice, up to the terrace deck
    wing_band = (slab(WING.cs, S1 - 0.01, WING_ZW) - slab(offset(WING.cs, -3.0), S1 - 1.0, WING_ZW + 1.0)) - \
        MAIN.solid(grow=0.0, dz0=-2, dz1=400) - st["rings"][0]
    kit.add("WALLS-1", "Buttermilk", st["shells"][0] + wing_band + wing_ledge + wing_lip, group="walls")
    kit.add("JOINT", "Buttermilk", st["rings"][0] - box([W + 0.02, WY0 - 6.0, S1 - 1.0], [W + 10.0, WY1 + 6.0, S1 + RJ + 1.0]),
            group="walls")
    eave_path = max(base.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    lip = _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)
    eave_ledge = CO.ledge(eave_path, ZE, LEDGE) - box([PX0 - 0.6, -5.0, ZE - 5.0], [PX1 + 0.6, -0.02, ZE + 5.0])
    kit.add("WALLS-2", "Buttermilk", st["shells"][1] + lip + eave_ledge, group="walls")

    # --- cornices: the joint (stopped either side of the wing's terrace), the eave (stopped
    # under the portico, whose own cornice takes over), round the portico, round the wing
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=wing_zone)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    port_in = box([PX0 - 0.2, -PD - 1.0, ZE - 3.0], [PX1 + 0.2, 1.0, ZW + 3.0])
    rings, _ = CO.level(eave_path, ZE, EAVE, cut=port_in)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(PORT_PTS, ZE, EAVE, cut=MAIN.solid(grow=7.4, dz0=-5, dz1=5))
    CO.add_level(kit, rings, "CORNICE-P", "portico")
    rings, _ = CO.level(WING.pts, WING_ZE, WING_C, cut=MAIN.solid(grow=0.7, dz0=-2, dz1=2))
    CO.add_level(kit, rings, "CORNICE-W", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="arcaded")
    kit.add("FOUNDATION", "Brick", fnd, group="foundation")

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
            left, right = C.shutters_pair(w_op, h_op, casing=SHUT_CAS, gap=SHUT_GAP, make=C.shutter_louver2)
            for side, m in (("L", left), ("R", right)):
                kit.add(f"SHUTTER-{o.name}-{side}", "Charleston", m.translate([0, 0, 0.27]).transform(A), P=inv34(A),
                        key=f"SHUTTER-{h_op:.1f}", group="shutters")
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the roof: keyed slate on a hip, with the portico's pediment roof
    r = RAKE - D_EAVE
    zcf = Z_EAVE + S_PED * ((PX1 - PX0) / 2 + D_EAVE)
    gy = (zcf - Z_EAVE) / S_MAIN - D_EAVE + 4.0
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN),
              ([(PX0, -PD - r), (PX1, -PD - r), (PX1, gy), (PX0, gy)], [1, 3], S_PED)]
    specs = [dict(p0=(PX0, -PD), p1=(PX1, -PD), slope=S_PED, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture=SLATE, tex_kw=dict(pitch=1.6, wtab=2.2, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    wf = rf["walls"][0]
    walls_env = wf["facade"].place(M.extrude(wf["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
    caps = [G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZW, half=1.2, up=0.6)]
    fy = gy + D_EAVE - (zcf - Z_EAVE) / S_PED
    caps.append(G.ridge_cap((XC, -PD - RAKE), (XC, fy + 0.4), zcf, S_PED, ZW, half=1.0, up=0.5))
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.2, up=0.6, drop=1.8) for c, e in zip(corners, ends)])
    roof = roof + ((union(caps) + hips) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    # the cupola on the ridge, two stacks on the hips
    CS_ = 16.0
    zcu = round((zr - S_MAIN * CS_ / 2 - 2.0) / 0.2) * 0.2
    roof = roof + G.chimney_seat(solid_env, XC, D / 2, CS_ / 2, zr + 1.0)
    roof = roof - box([XC - CS_ / 2 - 1.0, D / 2 - CS_ / 2 - 1.0, zcu], [XC + CS_ / 2 + 1.0, D / 2 + CS_ / 2 + 1.0, zr + 40])
    CW, CD = 10.0, 12.0
    stacks = []
    for cx in (58.0, W - 58.0):
        zroof = Z_EAVE + S_MAIN * (min(cx, W - cx) - CW / 2 + D_EAVE)
        z0 = round((zroof - 3.0) / 0.2) * 0.2
        roof = roof + G.chimney_seat(solid_env, cx, D / 2, CD / 2, zr + 1.0)
        roof = roof - box([cx - CW / 2 - 0.7, D / 2 - CD / 2 - 0.7, z0], [cx + CW / 2 + 0.7, D / 2 + CD / 2 + 0.7, zr + 40])
        stacks.append(C.chimney_acroteria(CW, CD, zr + 9.0 - z0).translate([cx, D / 2, z0]))
    # a dormer on each end slope
    DW, DDEP, DHW = 15.0, 16.0, 12.0
    dgr = DW / 2 * 0.7
    dxf = 17.0
    zdf = round((Z_EAVE + S_MAIN * (dxf + D_EAVE) - 1.0) / 0.2) * 0.2
    dbody, dcore, dface = C.dormer_segmental(DW, DDEP, DHW)
    dAs = [np.array([[0, 0, -1.0, dxf], [-1.0, 0, 0, D / 2], [0, 1.0, 0, zdf]]),
           np.array([[0, 0, 1.0, W - dxf], [1.0, 0, 0, D / 2], [0, 1.0, 0, zdf]])]
    for Ad in dAs:
        dkeep = ext(dface.offset(0.3, JoinType.Miter, 4.0), -DDEP - 0.3, 0.3).transform(Ad)
        dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
        seat = ext(rect(-DW / 2 - 1.3, ZW - zdf, DW / 2 + 1.3, 0.0), -DDEP - 1.3, 1.6).transform(Ad) ^ solid_env
        roof = roof - dpocket + (seat - dpocket - lip_keep(base, 3.0, ZW))
    kit.add("ROOF", "Pewter", roof, group="roof")
    ez = DHW - 1.6 * 0.7
    droof_cs = poly([(-DW / 2 - 1.6, ez), (-DW / 2, ez), (-DW / 2, DHW), (0.0, DHW + dgr + 0.2), (DW / 2, DHW),
                     (DW / 2, ez), (DW / 2 + 1.6, ez), (DW / 2 + 1.6, ez + 1.6), (0.0, DHW + dgr + 2.2), (-DW / 2 - 1.6, ez + 1.6)])
    for k, Ad in enumerate(dAs):
        kit.add(f"DORMER-{k}", "White", dbody.transform(Ad), key="DORMER", group="roof")
        kit.add(f"DORMER-core-{k}", "Pewter", dcore.transform(Ad), key="DORMER-core", group="roof")
        droof = ext(droof_cs, -DDEP - 12.0, 1.2).transform(Ad) - solid_env - dbody.transform(Ad) - roof
        kit.add(f"DORMER-roof-{k}", "Pewter", max(droof.decompose(), key=lambda m_: m_.volume()), key="DORMER-roof", group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Brick", s_, key="CHIMNEY", group="roof")
    cb, cdome, cfin = C.cupola_domed(CS_, 15.0)
    kit.add("CUPOLA", "White", cb.translate([XC, D / 2, zcu]), group="cupola")
    kit.add("CUPOLA-dome", "Verdigris", cdome.translate([XC, D / 2, zcu]), group="cupola")
    kit.add("CUPOLA-finial", "Verdigris", cfin.translate([XC, D / 2, zcu]), group="cupola")
    print("roof", round(time.time() - t0, 1))

    # --- the portico
    beam_cs = (poly(PORT_PTS) - rect(PX0 + PB, -PD + PB, PX1 - PB, 5.0)) ^ rect(-500, -500, 500, -0.5)
    beam = slab(beam_cs, ZA, ZW)
    beam = beam + slab(beam_cs.offset(0.4, JoinType.Miter, 4.0) ^ rect(-500, -500, 500, -0.5), ZA + 2.4, ZE - 0.2)
    beam = beam + (CO.ledge(PORT_PTS, ZE, LEDGE) - MAIN.solid(grow=7.4, dz0=-5, dz1=5))
    # each giant column's foot drops 1.2 mm into a recess in the floor and a square peg on its
    # abacus 1.6 mm up into a pocket in the beam: both ends glued round their sides
    seats = [FT.column_seats(x, COL_Y, ZF, ZA, ("round", COL_R), head=("square", 2.0), dhead=1.6) for x in COL_X]
    kit.add("PORTICO-beam", "White", beam - roof - union([t_ for _, _, t_ in seats]), group="portico")
    for k, x in enumerate(COL_X):
        kit.add(f"PORTICO-column-{k}", "White", C.column_doric(ZA - ZF, COL_R).translate([x, COL_Y, ZF]) + seats[k][0],
                key="PORTICO-column", group="portico")
    ceil_cs = rect(PX0 + PB + 0.2, -PD + PB + 0.2, PX1 - PB - 0.2, -0.3)
    ceil = C.coffered_ceiling(ceil_cs, t=0.8, pitch=6.0).mirror([0, 0, 1.0]).translate([0, 0, ZW])
    kit.add("PORTICO-ceiling", "Haint", ceil - roof, P=print_flip(), group="portico")
    # the pediment's tympanum: a wall on the beam with a fanned lunette, its raking cornice
    f = wf["facade"]
    At = f.A
    apex_v = wf["apex"]
    tcs = wf["cs"] ^ rect(-1, -FASCIA + 0.02, 500, 500)
    rl = min(11.0, apex_v * 0.9)
    lun = cs_union([(circle((wf["L"] / 2, -FASCIA), rl, 48) - circle((wf["L"] / 2, -FASCIA), rl - 0.9, 48)),
                    circle((wf["L"] / 2, -FASCIA), 1.6, 20)]) ^ rect(0, -FASCIA + 0.4, 500, 500)
    rays = cs_union([stroke([(wf["L"] / 2 + 1.6 * np.cos(a), -FASCIA + 1.6 * np.sin(a)),
                               (wf["L"] / 2 + (rl - 0.5) * np.cos(a), -FASCIA + (rl - 0.5) * np.sin(a))], 0.5)
                     for a in np.linspace(0.35, np.pi - 0.35, 7)])
    tym = M.extrude(tcs, 2.4).translate([0, 0, -2.4]) + M.extrude(lun, 0.6) + M.extrude(rays ^ tcs, 0.4)
    tym = tym - M.extrude(circle((wf["L"] / 2, -FASCIA), rl - 0.9, 48) ^ tcs, 0.6).translate([0, 0, -0.4])
    kit.add("PEDIMENT", "White", f.place(tym) - roof, P=inv34(At), group="portico")
    # the floor: a brick base with the arcaded facing, a planked deck on it, broad steps
    pbase = _faced_block(PX0 - 1.0, PX1 + 1.0, -PD - 1.0, 0.02, ZF - 2.0, "SEW", seed=5) - fnd
    kit.add("PORTICO-base", "Brick", pbase, group="portico")
    ppts = [(PX0 - 1.0, 0.0), (PX0 - 1.0, -PD - 1.0), (PX1 + 1.0, -PD - 1.0), (PX1 + 1.0, 0.0)]
    pcs = poly(ppts) ^ rect(-500, -500, 500, -0.02)
    planks = FT.porch_planks(ppts, [0, 1, 2], H=ZF, pitch=1.6, crack=0.25, border=1.4, along=(0.0, -1.0))
    pfloor = (slab(pcs, ZF - 2.0, ZF - 1.19) + planks) - fnd - union([f_ for _, f_, _ in seats])
    kit.add("PORTICO-floor", "PorchDeck", pfloor, P=print_flip(), group="portico",
            render=FT.plank_zones(pfloor, ZF, "Planks", "PorchDeck"))
    fr = MAIN.facades()[0]
    A = fr.A.copy()
    A[:, 3] = fr.world(XC, -ZF, PD + 1.9)
    kit.add("STEPS-front", "Brick", FT.steps(44.0, ZF - 0.6, 6, cheek=2.4).transform(A), group="portico")
    # the balcony over the door: a deck on the joint cornice, an iron railing round it
    zb = S1 + RJ
    bal = box([XC - BAL_W / 2, -BAL_D, zb], [XC + BAL_W / 2, -0.3, zb + 1.2])
    kit.add("BALCONY", "White", bal, group="portico")
    hr = 7.0
    runs = [(np.array([[1.0, 0, 0, XC - BAL_W / 2 + 0.2], [0, 0, -1.0, -BAL_D + 1.1], [0, 1.0, 0, zb + 1.2]]), BAL_W - 0.4)]
    for xs in (XC - BAL_W / 2 + 0.2, XC + BAL_W / 2 - 1.1):
        runs.append((np.array([[0, 0, 1.0, xs], [1.0, 0, 0, -BAL_D + 1.12], [0, 1.0, 0, zb + 1.2]]), BAL_D - 1.12 - 0.35))
    for k, (Ar, Lr) in enumerate(runs):
        kit.add(f"BALCONY-rail-{k}", "Charleston", C.iron_rail(Lr, hr).transform(Ar), P=inv34(Ar), group="portico")
    print("portico", round(time.time() - t0, 1))

    # --- the wing's roof terrace: a planked deck on its walls and cornice, a sawn balustrade
    dcs = (offset(WING.cs, 4.0) ^ rect(W + 0.3, -500, 500, 500))
    dpts = [(W + 0.3, WY0 - 4.0), (WX1 + 4.0, WY0 - 4.0), (WX1 + 4.0, WY1 + 4.0), (W + 0.3, WY1 + 4.0)]
    dplanks = FT.porch_planks(dpts, [0, 1, 2], H=WING_ZW + DECK_T, pitch=1.6, crack=0.25, border=1.2, along=(1.0, 0.0))
    deck = slab(dcs, WING_ZW, WING_ZW + DECK_T - 1.19) + dplanks
    deck = deck - lip_keep(WING.cs, 3.0, WING_ZW)
    kit.add("TERRACE-deck", "PorchDeck", deck, P=print_flip(), group="balcony",
            render=FT.plank_zones(deck, WING_ZW + DECK_T, "Planks", "PorchDeck"))
    zt = WING_ZW + DECK_T
    t = 1.2
    ys, yn, xe = WY0 - 2.6, WY1 + 2.6, WX1 + 2.6
    x0r = W + 1.5                             # clear of the upper shutters on the east wall
    bruns = [(np.array([[1.0, 0, 0, x0r], [0, 0, 1.0, ys], [0, 1.0, 0, zt]]), xe - x0r),
             (np.array([[1.0, 0, 0, x0r], [0, 0, -1.0, yn], [0, 1.0, 0, zt]]), xe - x0r),
             (np.array([[0, 0, -1.0, xe], [1.0, 0, 0, ys + t + 0.65], [0, 1.0, 0, zt]]), yn - ys - 2 * t - 1.3)]
    for k, (Ar, Lr) in enumerate(bruns):
        kit.add(f"TERRACE-rail-{k}", "White", C.sawn_balustrade(Lr, 7.4, t=t).transform(Ar), P=inv34(Ar), group="balcony")
    e, u = MAIN.locate(XC, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Brick", FT.steps(16.0, ZF - 0.6, 6).transform(A) - fnd, group="stoop")
    # glue joints: nothing small is left butted on a dab of glue (see NOTES.md)
    FT.crown(kit, "CUPOLA-finial", "CUPOLA-dome")
    for k_ in range(3):
        FT.key_into(kit, f"BALCONY-rail-{k_}", ["BALCONY"], (0, 0, -1), depth=0.6)
    print("specks dropped:", kit.drop_specks())
    print("wing", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "oakhurst")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "oakhurst.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
