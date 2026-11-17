"""The Marisol: an original HO-scale (1:87.1) lighthouse keeper's house with the light tower
rising out of the middle of its roof; house 103, of the new-layouts batch (hoarch.novel2), after
Point Fermin Light (San Pedro, California, 1874) and its Stick Style sisters drawn by Paul J.
Pelz for the U.S. Lighthouse Board.

A two-storey keeper's house of buff drop siding over the frame boards of the Stick Style
(corner posts, studs between the windows, sill and plate bands), under a hipped roof crossed
by four steep gables, one to each side, each with an open stick truss. Out of the crossing of
the roofs rises the light's square tower: two stages with one tall window to each face of
each (a keeper's watch room has them all round), a frieze of lozenges and a bracketed cornice
under an iron gallery with its railing, and on the gallery the octagonal iron lantern, glazed
all round in two tiers of panes, under a domed roof with a ventilator ball and a lightning
rod. A veranda on turned posts with stick braces and crossed railings wraps the front and the
sea (east) side; a one-storey kitchen wing stands behind; the house sits on a low base of
rough basalt with the rocks of the point heaped against its seaward corner.

- Storey joint: a red frieze of stick framing with crossed braces, an ivory rope, an ivory
  reverse ogee.
- Eave: a spruce frieze of round ports with bolt heads, an ivory soffit on stick braces, an
  ivory cyma.
- Tower: a red frieze of linked lozenges, a soffit on stick braces, a bevelled crown.
- Kitchen wing: a spruce rope and an ivory cavetto.

usage: python3 -m hoarch.buildings.marisol [check] [export]
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
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells, wall_shell

NAME = "The Marisol"
COLORS = {"Buff": "#E3D5B5", "Ivory": "#F3EEE1", "Redwood": "#7B3A29", "Pewter": "#575D63", "Spruce": "#2F4F4A",
          "Iron": "#2A2D30", "Basalt": "#5F5A54", "Brick": "#8A4434", "Planks": "#7A5C40", "Glass": "#1E2226",
          "Windows_Doors": "#F3EEE1"}
RENDER_MAT = {"Buff": "siding", "Ivory": "trim", "Redwood": "accent", "Pewter": "roof", "Spruce": "accent2",
              "Iron": "iron", "Basalt": "stone", "Brick": "brick", "Planks": "planks", "Glass": "glass",
              "Windows_Doors": "trim", "Sash": "sash", "Door": "door"}
PALETTE = {"siding": ["#E3D5B5", 0.8, 0.0], "trim": ["#F3EEE1", 0.6, 0.0], "accent": ["#7B3A29", 0.6, 0.0],
           "roof": ["#575D63", 0.75, 0.0], "accent2": ["#2F4F4A", 0.6, 0.0], "iron": ["#2A2D30", 0.45, 0.3],
           "stone": ["#5F5A54", 0.95, 0.0], "brick": ["#8A4434", 0.85, 0.0], "planks": ["#7A5C40", 0.75, 0.0],
           "sash": ["#F3EEE1", 0.5, 0.0], "door": ["#7B3A29", 0.45, 0.0]}
VIEWS = {"hero": [-34, 14, 70, 0.9, [0, 0, -14]], "hero_right": [36, 14, 70, 0.9, [0, 0, -14]],
         "front": [0, 6, 85, 0.92, [0, 0, 0]], "rear": [155, 16, 70, 0.92, [0, 0, -14]],
         "light": [-24, 8, 85, None, [76, 52, 200], 240], "porch": [-14, 8, 85, None, [74, -20, 26], 200]}

# ------------------------------------------------------------------ cornices (unique to the Marisol)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="mrsticks", role="Redwood"),
    dict(kind="course", h=1.6, b=1.4, orn="mrrope", role="Ivory"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="reverse", role="Ivory")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="mrportholes", role="Spruce"),
    dict(kind="bed", h=2.4, b=1.4, P=6.4, role="Ivory", brackets=dict(style="mrbrace", t=1.6)),
    dict(kind="crown", h=2.4, b=1.4, P=7.2, orn="cyma", role="Ivory")])
TOWER_C = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="frieze", h=3.8, b=1.2, orn="mrlozenge", role="Redwood"),
    dict(kind="bed", h=2.2, b=1.4, P=5.4, role="Ivory", brackets=dict(style="mrbrace", t=1.6)),
    dict(kind="crown", h=2.0, b=1.4, P=6.0, orn="bevel", role="Ivory")])
SMALL = dict(pitch=10.0, margin=3.0, layers=[
    dict(kind="course", h=1.6, b=1.4, orn="mrrope", role="Spruce"),
    dict(kind="crown", h=2.2, b=1.4, P=4.6, orn="cavetto", role="Ivory")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)
HT = CO.band_height(TOWER_C)
HS = CO.band_height(SMALL)

# ------------------------------------------------------------------ levels and plan (front = -y)
ZF = 8.0
S1 = ZF + 36.0
ZU = S1 + RJ
ZE = ZU + 32.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, S_H, S_G = 6.0, 5.0, 0.62, 1.05
W, D = 152.0, 104.0
XC, YC = W / 2, 52.0
PV0, PV1, PJ = XC - 24.0, XC + 24.0, 6.0                        # the front gable's pavilion, 6 forward
MAIN = Block("main", [(0, 0), (PV0, 0), (PV0, -PJ), (PV1, -PJ), (PV1, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
GH = 24.0                                             # the cross gables' half width
V1, V2 = 6.0, ZU - ZF + 5.0
VG = ZW - ZF + 3.0                                    # gable windows' sill
# the tower: out of the crossing, two stages, its cornice and the gallery on top
TW = 32.0
Z_T0 = round((Z_EAVE + 22.0) / 0.2) * 0.2             # its foot, in the roof's pocket
ZTW = round((Z_EAVE + 88.0) / 0.2) * 0.2              # its walls' top (under the gallery deck)
TOWER = Block("tower", [(XC - TW / 2, YC - TW / 2), (XC + TW / 2, YC - TW / 2), (XC + TW / 2, YC + TW / 2), (XC - TW / 2, YC + TW / 2)],
              Z_T0, ZTW)
T_T = 2.4
Z_ST = Z_EAVE + 56.0                                  # the band between the stages
GAL = 25.0                                            # the gallery deck's half width
# the kitchen wing behind
LZE = ZF + 28.0
LZW = round((LZE + HS) / 0.2) * 0.2
WING = Block("wing", [(12.0, D), (58.0, D), (58.0, D + 34.0), (12.0, D + 34.0)], ZF, LZW)
LZ_EAVE, S_W, D_W = LZW + 1.2, 0.55, 4.0
# the veranda: round the front and down the east (sea) side
VY, VX, VEND = -26.0, W + 20.0, 70.0


def _sticks(f, b):
    """The Stick Style boards on a facade: posts at its ends and halfway between its openings."""
    us = [0.8, f.L - 0.8]
    mine = sorted(o.u for o in OPENINGS + OPEN_W if o.block is b and o.facade.L == f.L and np.allclose(o.facade.p0, f.p0))
    for a, c in zip(mine[:-1], mine[1:]):
        if c - a > 20.0:
            us.append((a + c) / 2)
    return us


def _skin(f, b, reg):
    if b is MAIN:
        reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
        lo = reg ^ rect(-1, -100, f.L + 1, S1 - b.z0)
        hi = reg ^ rect(-1, ZU - b.z0, f.L + 1, 999)
        su = _sticks(f, b)
        out = []
        if not lo.is_empty():
            out.append(N.drop_marisol(lo, datum=0.0, sticks_u=su, bands_v=(1.4, V1 - 1.9, S1 - b.z0 - 1.6)))
        if not hi.is_empty():
            out.append(N.drop_marisol(hi, datum=ZU - b.z0, sticks_u=su,
                                      bands_v=(ZU - b.z0 + 1.0, V2 - 1.9, ZE - b.z0 - LEDGE - 1.4, ZW - b.z0 + 1.4)))
        return union(out) if out else M()
    if b is TOWER:
        reg = reg - rect(-1, ZTW - HT - LEDGE - 0.6 - b.z0, f.L + 1, 999)
        return N.drop_marisol(reg, datum=0.0, sticks_u=(0.8, f.L - 0.8), bands_v=(Z_ST - b.z0, Z_ST - b.z0 + 1.6))
    reg = reg - rect(-1, LZE - LEDGE - 0.6 - b.z0, f.L + 1, LZW - b.z0 + 0.2)
    return N.drop_marisol(reg, datum=0.0, sticks_u=(0.8, f.L - 0.8), bands_v=(1.4, V1 - 1.9))


def _openings():
    L1, L2, LT, LW = [], [], [], []
    fams = {}

    def add(L, blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        L[-1].fam = fams.setdefault(id(sp), name)

    lo, up, gw, tw = N.window_mrlower(), N.window_mrupper(), N.window_mrgable(), N.window_mrtower(h=13.0)
    back = N.door_mrback()
    # the front: a window each side of the pavilion, the door in it; two windows over it
    for x in (23.0, W - 23.0):
        add(L1, MAIN, x, 0.0, V1, lo, f"S{x:.0f}-1")
        add(L2, MAIN, x, 0.0, V2, up, f"S{x:.0f}-2")
    add(L1, MAIN, XC, -PJ, 0.4, N.door_mrfront(), "front-door", "door")
    add(L2, MAIN, XC, -PJ, V2, up, "S-centre-2")
    # the sides: three bays each; a door onto the veranda on the sea side
    for y in (16.0, 84.0):
        add(L1, MAIN, W, y, V1, lo, f"E{y:.0f}-1")
        add(L2, MAIN, W, y, V2, up, f"E{y:.0f}-2")
        add(L1, MAIN, 0.0, y, V1, lo, f"W{y:.0f}-1")
        add(L2, MAIN, 0.0, y, V2, up, f"W{y:.0f}-2")
    add(L1, MAIN, W, YC, 0.4, back, "side-door", "door")
    add(L2, MAIN, W, YC, V2, up, "E50-2")
    add(L1, MAIN, 0.0, YC, V1, lo, "W50-1")
    add(L2, MAIN, 0.0, YC, V2, up, "W50-2")
    # the back (the wing covers its west end)
    for x in (XC + 14.0, W - 22.0):
        add(L1, MAIN, x, D, V1, lo, f"N{x:.0f}-1")
        add(L2, MAIN, x, D, V2, up, f"N{x:.0f}-2")
    # a pair of lights in each of the four gables
    add(L2, MAIN, XC, -PJ, VG, gw, "gable-S")
    add(L2, MAIN, XC, D, VG, gw, "gable-N")
    add(L2, MAIN, W, YC, VG, gw, "gable-E")
    add(L2, MAIN, 0.0, YC, VG, gw, "gable-W")
    # the tower: one tall light to each face of each stage
    for (x, y, tag) in ((XC, YC - TW / 2, "S"), (XC + TW / 2, YC, "E"), (XC, YC + TW / 2, "N"), (XC - TW / 2, YC, "W")):
        add(LT, TOWER, x, y, Z_EAVE + 38.2 - Z_T0, tw, f"T{tag}-1")
        add(LT, TOWER, x, y, Z_ST + 4.0 - Z_T0, tw, f"T{tag}-2")
    # the kitchen wing
    add(LW, WING, 35.0, D + 34.0, 0.4, back, "kitchen-door", "door")
    klo = N.window_mrlower(h=15.0)
    add(LW, WING, 12.0, D + 17.0, V1, klo, "K-W")
    add(LW, WING, 58.0, D + 17.0, V1, klo, "K-E")
    return L1, L2, LT, LW


OPEN1, OPEN2, OPEN_T, OPEN_W = _openings()
OPENINGS = OPEN1 + OPEN2 + OPEN_T
BLOCKS = [MAIN, TOWER, WING]


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


def _roof_pieces():
    hip = ([(0, 0), (W, 0), (W, D), (0, D)], [0, 1, 2, 3], S_H)
    front = ([(PV0, -PJ), (PV1, -PJ), (PV1, YC), (PV0, YC)], [1, 3], S_G)
    backp = ([(PV0, YC), (PV1, YC), (PV1, D), (PV0, D)], [1, 3], S_G)
    east = ([(XC, YC - GH), (W, YC - GH), (W, YC + GH), (XC, YC + GH)], [0, 2], S_G)
    west = ([(0, YC - GH), (XC, YC - GH), (XC, YC + GH), (0, YC + GH)], [0, 2], S_G)
    gdefs = [dict(p0=(PV0, -PJ), p1=(PV1, -PJ), slope=S_G, e=D_EAVE), dict(p0=(PV1, D), p1=(PV0, D), slope=S_G, e=D_EAVE),
             dict(p0=(W, YC - GH), p1=(W, YC + GH), slope=S_G, e=D_EAVE), dict(p0=(0, YC + GH), p1=(0, YC - GH), slope=S_G, e=D_EAVE)]
    # (block edge, u of the gable's left end along it) for each gable, as in gdefs
    where = [(2, 0.0), (6, W - PV1), (5, YC - GH), (7, D - (YC + GH))]
    return [hip, front, backp, east, west], gdefs, where


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    path = MAIN.pts
    house_env = MAIN.solid(grow=0.15, dz0=-20, dz1=400)
    tower_env = TOWER.solid(grow=0.15, dz0=-60, dz1=200)
    # the wing's whole envelope (walls, cornice, roof) where it meets the back wall: kept clear of
    # the house's dressing, and cut from the storey joint and its cornice
    wing_env = box([WING.pts[0][0] - 7.0, D - 1.0, -1.0], [WING.pts[1][0] + 7.0, D + 40.0, LZ_EAVE + S_W * 30.0 + 2.0])

    # --- the roof first (its gable walls go into the upper shell)
    pieces, gdefs, where = _roof_pieces()
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture=("diamond", "square"), tex_kw=dict(pitch=1.5, wtab=2.1, d=0.35),
                       skin=1.8, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    gables = [(MAIN, e, wl["cs"].translate((u0, Z_EAVE - MAIN.z0))) for (e, u0), wl in zip(where, rf["walls"])]

    # --- the house: two storeys, the joint, the ledge for the eave; the gable walls with them
    undress = [slab(offset(base, 10.0), ZE - LEDGE - 0.6, ZW + 0.01), wing_env]
    st = stacked_shells([MAIN], OPEN1 + OPEN2, [S1], t=3.0, corners="none", siding=_skin, clear=[lip_keep(base, 3.0, ZF, 1.2)],
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress, gables=gables,
                        partitions=[((XC - TW / 2 - 1.2, 3.0), (XC - TW / 2 - 1.2, D - 3.0), 2.0, ZF, ZE)])
    kit.add("WALLS-1", "Buff", st["shells"][0], group="walls")
    kit.add("JOINT", "Buff", st["rings"][0] - wing_env, group="walls")
    lip = _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)
    kit.add("WALLS-2", "Buff", st["shells"][1] + lip + CO.ledge(path, ZE, LEDGE), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=wing_env)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    erings, _ = CO.level(path, ZE, EAVE)
    CO.add_level(kit, erings, "CORNICE-E", "cornice")
    ins_keep = []
    _place_inserts(kit, OPEN1 + OPEN2, ins_keep)
    print("house walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the roof: slates, ridge caps on the four gables, the trusses, two stacks, the tower's pocket
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zrg = Z_EAVE + S_G * (GH + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    caps = [G.ridge_cap((XC, -PJ - RAKE), (XC, YC), zrg, S_G, ZW, half=1.2, up=0.6),
            G.ridge_cap((XC, YC), (XC, D + RAKE), zrg, S_G, ZW, half=1.2, up=0.6),
            G.ridge_cap((XC, YC), (W + RAKE, YC), zrg, S_G, ZW, half=1.2, up=0.6),
            G.ridge_cap((-RAKE, YC), (XC, YC), zrg, S_G, ZW, half=1.2, up=0.6)]
    roof = roof + (union(caps) - walls_env - tower_env)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_H, D_EAVE, texture=None, zlo=ZW)
    hx = TW / 2 + 0.95                               # clear of the tower's siding and corner boards
    roof = roof + G.pocket_seat(solid_env, XC, YC, hx, hx, Z_T0)
    roof = roof - box([XC - hx, YC - hx, Z_T0], [XC + hx, YC + hx, Z_T0 + 200])
    stacks = []
    CW, CD = 10.0, 7.0
    for k, (cx, cy) in enumerate(((22.0, D - 14.0), (W - 22.0, 14.0))):
        dmin = min(cx - CW / 2, W - cx - CW / 2, cy - CD / 2, D - cy - CD / 2) + D_EAVE
        z_low = Z_EAVE + S_H * dmin
        z0 = round((z_low - 2.4) / 0.2) * 0.2
        roof = roof + G.pocket_seat(solid_env, cx, cy, CW / 2 + 0.4, CD / 2 + 0.4, z0)
        roof = roof - box([cx - CW / 2 - 0.4, cy - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CD / 2 + 0.4, z0 + 200])
        h = round((Z_EAVE + S_H * (D / 2 + D_EAVE) + 8.0 - z0) / 0.2) * 0.2
        stacks.append(N.chimney_marisol(CW, CD, h).translate([cx, cy, z0]))
    roof = roof - lip_keep(base, 3.0, ZW)
    kit.add("ROOF", "Pewter", roof, group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Brick", s_, key="CHIMNEY", group="roof")
    for k, wl in enumerate(rf["walls"]):
        tr = N.gable_marisol(wl["L"], wl["slope"], D_EAVE, skin=1.8)
        fw = wl["facade"]
        A = fw.A.copy()
        A[:, 3] = fw.world(0.0, 0.0, RAKE)
        tw = tr.transform(A) - roof
        tw = max(tw.decompose(), key=lambda m_: m_.volume())
        kit.add(f"TRUSS-{k}", "Ivory", tw, P=inv34(A), key="TRUSS", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the light tower: two stages in one shell, its cornice, the gallery, railing, lantern
    tpath = TOWER.pts
    tws = wall_shell([TOWER], OPEN_T, t=T_T, belt=None, corners="none", water_table=False, siding=_skin,
                     undress=[slab(offset(TOWER.cs, 8.0), ZTW - HT - LEDGE - 0.6, ZTW + 0.01)])
    tws = tws + CO.ledge(tpath, ZTW - HT, LEDGE, t=T_T)
    kit.add("TOWER", "Buff", tws, group="tower")
    trings, _ = CO.level(tpath, ZTW - HT, TOWER_C, t=T_T)
    CO.add_level(kit, trings, "CORNICE-T", "cornice")
    _place_inserts(kit, OPEN_T, ins_keep, group="tower")
    lip_in = TW / 2 - T_T - 0.15
    gal = N.gallery_marisol(GAL, t=1.6, lip=(lip_in, 1.2)).translate([XC, YC, ZTW])
    kit.add("GALLERY", "Iron", gal, P=print_flip(), group="tower")
    zg = ZTW + 1.6
    e = GAL - 1.4                                    # the slots' centre lines
    Lf, Ls = 2 * e + 1.0, 2 * e - 2.4                 # front and back strips run past the sides' ends
    for k, (Lr, ang, off) in enumerate(((Lf, 0, (-Lf / 2, -e - 0.5)), (Ls, 90, (e + 0.5, -Ls / 2)),
                                        (Lf, 180, (Lf / 2, e + 0.5)), (Ls, 270, (-e - 0.5, Ls / 2)))):
        rs = N.gallery_rail_marisol(Lr)
        a = math.radians(ang)
        ux, uy = math.cos(a), math.sin(a)
        # local u along the side, v up, w inward (toward the lantern)
        A = np.array([[ux, 0.0, -uy, XC + off[0]], [uy, 0.0, ux, YC + off[1]], [0.0, 1.0, 0.0, zg]])
        kit.add(f"RAIL-{k}", "Iron", rs.transform(A), P=inv34(A), key=f"RAIL-{Lr:.1f}", group="tower")
    cage, glass = N.lantern_marisol()
    kit.add("LANTERN", "Iron", cage.translate([XC, YC, zg]), group="lantern")
    kit.add("LANTERN-glass", "Glass", glass.translate([XC, YC, zg]), group="lantern")
    print("tower", round(time.time() - t0, 1))

    # --- the base: basalt under the house and the wing, the rocks of the point heaped at the
    # seaward back corner (fused to it)
    fnd = foundation([MAIN, WING], 0.0, ZF, style="mrbasalt")
    rocks = N.rocks_marisol([(W + 4.0, D - 12.0, 9.0), (W + 15.0, D - 22.0, 10.0), (W + 13.0, D - 4.0, 8.5), (W + 26.0, D - 12.0, 9.0),
                             (W + 5.0, D + 4.0, 7.0), (W + 24.0, D - 30.0, 6.5), (W + 30.0, D + 2.0, 6.0)])
    rocks = rocks - house_env
    fnd = fnd + rocks
    kit.add("FOUNDATION", "Basalt", fnd, group="foundation")

    # --- the veranda: planked deck, one-piece top (posts, braces, railings, roof) printed upside
    # down on its flat top, a tin top in its one colour change; steps to the front door
    pts = [(0.0, VY), (VX, VY), (VX, VEND), (W, VEND), (W, 0.0), (PV1, 0.0), (PV1, -PJ), (PV0, -PJ), (PV0, 0.0), (0.0, 0.0)]
    runs = [dict(a=(0.0, 0.0), b=(0.0, VY), posts=[-VY - 1.6]),
            dict(a=(0.0, VY), b=(VX, VY), posts=[1.6, 32.0, XC - 12.0, XC + 12.0, W - 32.0, W - 2.0, VX - 1.6]),
            dict(a=(VX, VY), b=(VX, VEND), posts=[1.6, 34.0, 66.0, VEND - VY - 1.6]),
            dict(a=(VX, VEND), b=(W, VEND), posts=[1.6])]
    post_h = round((S1 - 1.4 - 2.4 - ZF) / 0.2) * 0.2
    P = FT.porch_turned(pts, runs, ZF, post_h, steps_at=[(1, XC, 18.0)], inset=1.6, rail="mrcross", beam=2.6,
                        post="marisol", arcade="mrbraces", skirt="mrboards", pier_tex="rubble", roof_edge="mrdrip",
                        planks=dict(pitch=1.5, border=1.8), drop=4.4, top=True)
    fkeep = slab(offset(base, 1.7), -1, ZF + 1.3)
    steps = []
    for sm, A in P["steps"]:                         # the steps run 1.2 into the deck, which is cut to fit them
        A2 = A.copy()
        A2[:, 3] = A[:, 3] + A[:, 2] * (-1.2)
        steps.append(sm.transform(A2))
    deck = P["deck"] - fkeep - fnd - union(steps)
    kit.add("PORCH-deck", "Redwood", deck, P=print_flip(), group="porch", render=FT.plank_zones(deck, ZF, "Planks", "Redwood"))
    ins_box = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2], [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                     for b in (s_.bounding_box() for s_ in ins_keep)])
    bld_keep = MAIN.solid(grow=1.45, dz0=-20, dz1=300)
    FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_box, "Ivory", "Ivory", tin_col="Pewter", tin="flat", group="porch")
    parts = {p_.name: p_ for p_ in kit.parts}
    for k, sw in enumerate(steps):
        kit.add(f"PORCH-steps-{k}", "Basalt", sw - fkeep - fnd - parts["PORCH-top"].solid, group="porch")
    print("veranda", round(time.time() - t0, 1))

    # --- the kitchen wing: walls with its back gable, cornice, roof, stack, the stoop
    wins = []
    _place_inserts(kit, OPEN_W, wins, group="wing")
    wrf = G.gabled_roof([(WING.pts, [1, 3], S_W)], LZ_EAVE, D_W, [dict(p0=(58.0, D + 34.0), p1=(12.0, D + 34.0), slope=S_W, e=0.3)],
                        texture=("diamond", "square"), tex_kw=dict(pitch=1.5, wtab=2.1, d=0.35), skin=1.6, rake=3.4,
                        inner_cs=offset(WING.cs, -3.0), fascia=1.2, hollow=2.4)
    wg = [(WING, 2, wrf["walls"][0]["cs"].translate((0.0, LZ_EAVE - WING.z0)))]
    ww = wall_shell([WING], OPEN_W, t=3.0, belt=None, corners="none", water_table=False, siding=_skin, gables=wg,
                    undress=[slab(offset(WING.cs, 8.0), LZE - LEDGE - 0.6, LZW + 0.01)])
    ww = ww - lip_keep(WING.cs, 3.0, ZF, 1.2)
    ww = ww + CO.ledge(WING.pts, LZE, LEDGE) + (_corbel(WING.cs, 3.0, LZW) + lip_ring(WING.cs, 3.0, LZW))
    ww = ww - house_env
    kit.add("WING-WALLS", "Buff", max(ww.decompose(), key=lambda m_: m_.volume()), group="wing")
    lrings, _ = CO.level(WING.pts, LZE, SMALL, cut=house_env)
    CO.add_level(kit, lrings, "CORNICE-W", "cornice")
    wroof = wrf["body"] + wrf["tex"] + wrf["skins"] + wrf["skin_tex"]
    zrw = LZ_EAVE + S_W * (23.0 + D_W)
    wroof = wroof + G.ridge_cap((35.0, D), (35.0, D + 34.0 + 3.4), zrw, S_W, LZW, half=1.1, up=0.6)
    wenv, _ = R.hip_roof([(WING.pts, [1, 3], S_W)], LZ_EAVE, S_W, D_W, texture=None, zlo=LZW)
    cx, cy = 35.0, D + 24.0
    z0 = round((LZ_EAVE + S_W * (23.0 - 4.0 + D_W) - 2.4) / 0.2) * 0.2
    wroof = wroof + G.pocket_seat(wenv, cx, cy, 4.4, 3.4, z0)
    wroof = wroof - box([cx - 4.4, cy - 3.4, z0], [cx + 4.4, cy + 3.4, z0 + 100]) - house_env - lip_keep(WING.cs, 3.0, LZW)
    kit.add("WING-ROOF", "Pewter", max(wroof.decompose(), key=lambda m_: m_.volume()), group="wing")
    kit.add("CHIMNEY-wing", "Brick", N.chimney_marisol(8.0, 6.0, round((zrw + 9.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0]), group="wing")
    e_, u_ = WING.locate(35.0, D + 34.0)
    fb = WING.facades()[e_]
    A = fb.A.copy()
    A[:, 3] = fb.world(u_, -ZF, 0.82)                # its back against the base's face (the base is 0.8 proud)
    kit.add("STOOP-back", "Basalt", FT.steps(14.0, ZF - 0.6, 3).transform(A) - fnd, group="stoop")
    print("wing", round(time.time() - t0, 1))

    # --- glue joints: the rails into the gallery deck's slots
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "marisol")
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
    kit.render_npz(os.path.join(OUT, "marisol.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
