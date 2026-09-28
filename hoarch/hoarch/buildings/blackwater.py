"""The Blackwater Coaling Tower: an original HO-scale (1:87.1) timber coaling tower, building 71
(the engine terminal batch).

A timber coaling tower of about 1895. The bin house stands high on a trestle of twelve posts
with girts and X braces, over a planked walkway on knee braces along the track side; its walls
are heavy horizontal bin planks held by plumb bin posts and two rows of wales with a tie-rod
washer at every post, painted Tuscan red. Two steel apron chutes hang over the track from their
gate boxes, each on a pair of hanger bars. At the east end the elevator shaft, in board and
batten, climbs from its footing past the eave to a head house with segmental windows, joined to
the bin by an inclined distributing spout. A hoist house at the shaft's foot holds the engine,
its iron stack through a corrugated roof. Roofs of corrugated iron; BLACKWATER on a long board
under the eave. Cornices: a strapped timber sill over a chain (the bin's foot); elevator buckets
over a chain on bin struts (the eave); head pulleys over sprockets (under the head house); a
chain (the head house eave); crossed pick and shovel (the hoist house).

usage: python3 -m hoarch.buildings.blackwater [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, rect, slab, union
from hoarch import cornice as CO, gables as G, openings as O, yard as YD
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Blackwater Coaling Tower"
COLORS = {"Tuscan": "#6E2E24", "Bone": "#D8CCAE", "Iron": "#2B2B2B", "Timber": "#5B4734", "Galv": "#8B9096",
          "Concrete": "#A6A297", "Windows_Doors": "#D8CCAE"}
RENDER_MAT = {"Tuscan": "siding", "Bone": "trim", "Iron": "iron", "Timber": "timber", "Galv": "roof", "Concrete": "stone",
              "Windows_Doors": "trim", "Door": "door", "Glass": "glass", "Letters": "iron", "Planks": "planks"}
PALETTE = {"siding": ("#6E2E24", 0.85, 0.0), "trim": ("#D8CCAE", 0.55, 0.0), "iron": ("#2B2B2B", 0.45, 0.3),
           "timber": ("#5B4734", 0.9, 0.0), "roof": ("#8B9096", 0.45, 0.35), "stone": ("#A6A297", 0.9, 0.0),
           "door": ("#5B2620", 0.7, 0.0), "planks": ("#6B563F", 0.85, 0.0)}
VIEWS = {"hero": [-34, 14, 60, 0.95, [0, 0, 0]], "front": [0, 6, 70, 0.92, [0, 0, 0]], "rear": [150, 16, 60, 0.95, [0, 0, 0]],
         "right": [60, 12, 60, 0.95, [0, 0, 0]]}

# ------------------------------------------------------------------ cornices (unique to the Blackwater)
LEDGE = 1.4
BASE = dict(pitch=14.0, margin=0.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="binstraps", role="Timber"),
    dict(kind="course", h=1.6, b=1.4, orn="chainlinks", role="Iron")])
EAVE = dict(pitch=14.0, margin=14.0, layers=[
    dict(kind="frieze", h=5.2, b=1.2, orn="buckets", role="Bone"),
    dict(kind="course", h=1.6, b=1.4, orn="chainlinks", role="Iron"),
    dict(kind="bed", h=2.4, b=1.4, P=7.0, role="Bone", brackets=dict(style="binstrut", t=1.6, reach=0.5)),
    dict(kind="crown", h=2.0, b=1.4, P=7.4, orn="stepped", role="Tuscan")])
HEADC = dict(pitch=10.0, margin=3.0, layers=[
    dict(kind="frieze", h=5.0, b=1.2, orn="headwheels", role="Bone"),
    dict(kind="course", h=1.6, b=1.4, orn="sprockets", role="Iron"),
    dict(kind="bed", h=2.2, b=1.4, P=3.8, role="Bone", brackets=dict(style="binstrut", t=1.6, reach=0.5)),
    dict(kind="crown", h=1.8, b=1.4, P=4.2, orn="cavetto", role="Tuscan")])
HHE = dict(pitch=7.0, margin=2.5, layers=[
    dict(kind="course", h=1.6, b=1.2, orn="chainlinks", role="Iron"),
    dict(kind="crown", h=1.8, b=1.4, P=3.0, orn="ogee_fillet", role="Bone")])
HOE = dict(pitch=8.0, margin=3.0, layers=[
    dict(kind="frieze", h=4.2, b=1.2, orn="pickshovel", role="Bone"),
    dict(kind="crown", h=1.8, b=1.4, P=3.4, orn="bevel", role="Tuscan")])
HB = CO.band_height(BASE)
HE = CO.band_height(EAVE)
HS = CO.band_height(HEADC)

# ------------------------------------------------------------------ levels and plan
Z_FOOT = 4.0                                      # the footings' tops
H_TR = 76.0                                       # the trestle, feet to deck top
Z_DECK = Z_FOOT + H_TR
ZE = Z_DECK + 64.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 7.0, 4.0, 1.6
S_MAIN = 0.7
W, D = 84.0, 56.0
YC = D / 2
ZR = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)           # the main ridge
MAIN = Block("bin", [(0, 0), (W, 0), (W, D), (0, D)], Z_DECK, ZW)

XS = (3.0, 29.0, 55.0, 81.0)                      # trestle posts
YS = (3.0, YC, D - 3.0)
WALK = -9.0                                       # the walkway's outer edge
DECK = (-3.0, WALK, W + 3.0, D + 3.0)
PAD_T = 1.8

SX0, SX1, SY0, SY1 = W, W + 16.0, YC - 8.0, YC + 8.0     # the elevator shaft
ZS_E = round((ZR + 2.4) / 0.2) * 0.2              # its cornice's foot, clear of the main ridge
ZS_W = round((ZS_E + HS) / 0.2) * 0.2
SHAFT = Block("shaft", [(SX0, SY0), (SX1, SY0), (SX1, SY1), (SX0, SY1)], Z_FOOT, ZS_W)
SHAFT_CUT = box([SX0 - 0.05, SY0 - 0.9, -10.0], [SX1 + 2.0, SY1 + 0.9, 400.0])

HX0, HX1, HY0, HY1 = SX0 - 3.0, SX1 + 3.0, SY0 - 3.0, SY1 + 3.0   # the head house, on the shaft's cornice
ZH_E = ZS_W + 15.0
HHB = CO.band_height(HHE)
ZH_W = round((ZH_E + HHB) / 0.2) * 0.2
S_HH = 0.9
HEAD = Block("head", [(HX0, HY0), (HX1, HY0), (HX1, HY1), (HX0, HY1)], ZS_W, ZH_W)

KX0, KX1, KY0, KY1 = SX1 + 3.0, SX1 + 31.0, YC - 12.0, YC + 12.0  # the hoist house
ZK_F = 4.0
ZK_E = ZK_F + 24.0
ZK_W = round((ZK_E + CO.band_height(HOE)) / 0.2) * 0.2
S_K = 0.6
HOIST = Block("hoist", [(KX0, KY0), (KX1, KY0), (KX1, KY1), (KX0, KY1)], ZK_F, ZK_W)
STACK = (KX0 + 19.0, YC + 5.5)

GATE_V, CHUTES = 17.0, (21.0, 63.0)               # the chute gates (v above the deck)
SIGN_V, SIGN_L, SIGN_H = 55.6, 40.0, 6.0
DOOR_X = 35.0
SPOUT_V = 7.0                                     # the spout's axis on the head house (v)


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    wb = YD.window_bin(8.0, 12.0)
    for x in (7.0, 77.0):
        add(MAIN, x, 0.0, 40.0, wb, f"S{x:.0f}")
    for x in (21.0, 63.0):
        add(MAIN, x, D, 40.0, wb, f"N{x:.0f}")
    for y in (21.0, 35.0):
        add(MAIN, 0.0, y, 40.0, wb, f"W{y:.0f}")
    add(MAIN, 0.0, YC, 77.6, YD.window_bin(7.0, 10.0), "W-gable")
    for y in (7.0, 49.0):
        add(MAIN, W, y, 40.0, wb, f"E{y:.0f}")
    add(MAIN, DOOR_X, 0.0, HB + 0.2, YD.door_bin(9.0, 20.0), "walk", "door")
    ws = YD.window_slit(5.0, 9.0)
    add(SHAFT, SX0 + 8.0, SY0, 50.0, ws, "shaft-S50")
    add(SHAFT, SX0 + 8.0, SY0, 112.0, ws, "shaft-S112")
    add(SHAFT, SX1, YC, 80.0, ws, "shaft-E80")
    add(SHAFT, SX0 + 8.0, SY1, 130.0, ws, "shaft-N130")
    wh = YD.window_headhouse(6.0, 9.0)
    add(HEAD, (HX0 + HX1) / 2, HY0, 2.0, wh, "head-S")
    add(HEAD, HX1, YC, 2.0, wh, "head-E")
    add(HEAD, (HX0 + HX1) / 2, HY1, 2.0, wh, "head-N")
    add(HOIST, KX0 + 8.0, KY0, 0.4, YD.door_hoist(12.0, 16.0), "hoist", "door")
    wk = YD.window_hoist(7.0, 8.0)
    add(HOIST, KX0 + 22.0, KY0, 8.0, wk, "hoist-S")
    add(HOIST, KX1, YC, 8.0, wk, "hoist-E")
    add(HOIST, KX0 + 12.0, KY1, 8.0, wk, "hoist-N")
    return L


OPENINGS = _openings()


def _fields(f, blk):
    out = []
    if blk is MAIN and np.allclose(MAIN.facades()[0].n, f.n):
        for x in CHUTES:
            out.append(rect(x - 5.4, GATE_V - 0.4, x + 5.4, GATE_V + 12.4))
        out.append(rect(W / 2 - SIGN_L / 2 - 0.3, SIGN_V - 0.3, W / 2 + SIGN_L / 2 + 0.3, SIGN_V + SIGN_H + 0.3))
    if blk is MAIN and np.allclose(MAIN.facades()[1].n, f.n):
        out.append(rect(SY0 - 1.0, -50.0, SY1 + 1.0, 999.0))
    if blk is HEAD and np.allclose(HEAD.facades()[3].n, f.n):       # where the spout meets the head house
        out.append(rect(HY1 - YC - 3.4, SPOUT_V - 3.4, HY1 - YC + 3.4, SPOUT_V + 3.4))
    return out


def _skin(f, b, reg):
    if b is MAIN:
        reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2) - rect(-1, -50.0, f.L + 1, HB + 0.2)
        for fl in _fields(f, b):
            reg = reg - fl
        return YD.bin_planks(reg, datum=0.0, pitch=2.0, stud=14.0, u0=0.0, wales=(22.0, 47.0),
                             post_top=ZE - LEDGE - 0.6 - b.z0)
    if b is SHAFT:
        reg = reg - rect(-1, ZS_E - LEDGE - 0.6 - b.z0, f.L + 1, 999.0)
        if np.allclose(SHAFT.facades()[3].n, f.n):          # against the bin: plain where it glues
            reg = reg - rect(-1, -50.0, f.L + 1, ZR + 2.0 - b.z0)
        return YD.battens_vertical(reg, board=2.6)
    if b is HEAD:
        reg = reg - rect(-1, ZH_E - LEDGE - 0.6 - b.z0, f.L + 1, ZH_W - b.z0 + 0.2)
        for fl in _fields(f, b):
            reg = reg - fl
        return YD.bin_planks(reg, datum=0.0, pitch=1.6, stud=7.0, u0=0.0, wales=(), post_top=ZH_E - LEDGE - 0.6 - b.z0)
    if b is HOIST:
        reg = reg - rect(-1, ZK_E - LEDGE - 0.6 - b.z0, f.L + 1, ZK_W - b.z0 + 0.2)
        return YD.battens_vertical(reg, board=2.2)
    return M()


def _add_inserts(kit, ops):
    keep = []
    for op in ops:
        A = op.local_frame()
        sp = op.spec
        bb = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if op.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P,
                       key=f"{key}-{bb[2] - bb[0]:.1f}x{bb[3] - bb[1]:.1f}-{op.block.name}", group="inserts", render=zones)
        keep.append(part.solid)
    return keep


def _face_P(A):
    return np.column_stack([np.vstack([A[:, 0], A[:, 1], A[:, 2]]), np.zeros(3)])


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs

    # --- the footings and the trestle
    notch = box([SX0 - 0.3, SY0 - 1.0, -50.0], [SX1 + 5.0, SY1 + 1.0, 200.0])
    pad = YD.footings_coal(XS, YS, (-6.0, -2.0, SX1 + 1.4, D + 3.0), shaft=(SX0, SY0, SX1, SY1), zt=Z_FOOT, pad_t=PAD_T)
    pad = pad + box([-6.0, -10.5, 0.0], [0.0, -1.9, PAD_T])                    # under the ladder's feet
    pad = pad + lip_ring(SHAFT.cs, 2.4, Z_FOOT)
    kit.add("FOOTINGS", "Concrete", pad, group="base")
    tr = YD.trestle_coal(XS, YS, H_TR, DECK, WALK, notch=notch.translate([0, 0, -Z_FOOT])).translate([0, 0, Z_FOOT])
    kit.add("TRESTLE", "Timber", tr, P=print_flip(), group="trestle",
            render=[("Timber", tr - box([-10, -20, Z_DECK - 0.35], [SX1, D + 10, Z_DECK + 1])),
                    ("Planks", tr ^ box([-10, -20, Z_DECK - 0.35], [SX1, D + 10, Z_DECK + 1]))])
    print("trestle", round(time.time() - t0, 1))

    # --- the bin house: walls with their gables, the base band, the eave cornice
    pieces = [(MAIN.pts, [0, 2], S_MAIN)]
    gdefs = [dict(p0=(W, 0.0), p1=(W, D), slope=S_MAIN, e=0.3), dict(p0=(0.0, D), p1=(0.0, 0.0), slope=S_MAIN, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="corrugated", tex_kw=dict(pitch=16.0, wtab=7.2, d=0.32),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    we, ww = rf["walls"]
    gables = [(MAIN, 1, we["cs"].translate((0.0, Z_EAVE - Z_DECK))), (MAIN, 3, ww["cs"].translate((0.0, Z_EAVE - Z_DECK)))]
    undress = [slab(offset(base, 12.0), ZE - LEDGE - 0.6, ZW + 0.01), slab(offset(base, 12.0), Z_DECK - 1.0, Z_DECK + HB + 0.01)]
    bin_ops = [op for op in OPENINGS if op.block is MAIN]
    walls = wall_shell([MAIN], bin_ops, t=3.0, belt=None, corners="none", water_table=False, siding=_skin,
                       gables=gables, undress=undress)
    no_lip = union([box([-1, -20, ZW - 1], [5.0, D + 20, ZW + 5]), box([W - 5.0, -20, ZW - 1], [W + 1, D + 20, ZW + 5])])
    walls = walls + ((_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip) + (CO.ledge(MAIN.pts, ZE, LEDGE) - SHAFT_CUT)
    kit.add("WALLS", "Tuscan", walls, group="walls")
    rings, _ = CO.level(MAIN.pts, Z_DECK, BASE, cut=SHAFT_CUT)
    CO.add_level(kit, rings, "CORNICE-B", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE, cut=SHAFT_CUT)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    f = MAIN.facades()[0]
    A = f.A.copy()
    A[:, 3] = f.world(W / 2, SIGN_V, 0.0)
    sb, letters = YD.sign_bin("BLACKWATER", SIGN_L, SIGN_H, cap=4.2)
    kit.add("SIGN", "Bone", sb.transform(A), P=_face_P(A), group="walls",
            render=[("Bone", (sb - letters).transform(A)), ("Letters", letters.transform(A))])
    ins = _add_inserts(kit, bin_ops)
    print("bin house", round(time.time() - t0, 1))

    # --- the main roof: corrugated iron, a ridge roll, the distributing spout up to the head house
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((-RAKE, YC), (W + RAKE, YC), ZR, S_MAIN, ZW, half=1.2, up=0.7) - walls_env)
    zc = ZS_W + SPOUT_V                                  # the spout's axis where it meets the head house
    zlow = ZR + 1.4
    xlow = HX0 - (zc - zlow)
    spout = M.hull_points([(HX0, YC + s * 2.2, zc + t) for s in (-1, 1) for t in (-2.2, 2.2)] +
                          [(xlow, YC + s * 2.2, zlow + t) for s in (-1, 1) for t in (-2.2 - 1.6, 2.2)])
    spout = spout + M.hull_points([(HX0 - 0.01, YC + s * 2.9, zc + t) for s in (-1, 1) for t in (-2.9, 2.9)] +
                                  [(HX0 - 1.2, YC + s * 2.9, zc + t - 1.2) for s in (-1, 1) for t in (-2.9, 2.9)])
    roof = (roof + spout - lip_keep(base, 3.0, ZW) - SHAFT_CUT).trim_by_plane([0, 0, 1.0], ZW)
    ch = round((ZR + 1.2 - ZW) / 0.2) * 0.2
    kit.add("ROOF", "Galv", roof, group="roof", change=(ch, "Iron"),
            render=[("Galv", roof - box([-50, -50, ZW + ch], [300, 300, 400])), ("Iron", roof ^ box([-50, -50, ZW + ch], [300, 300, 400]))])
    print("roof", round(time.time() - t0, 1))

    # --- the elevator shaft, its cornice, the head house on it
    sh_ops = [op for op in OPENINGS if op.block is SHAFT]
    sh = wall_shell([SHAFT], sh_ops, t=2.4, belt=None, corners="none", water_table=False, siding=_skin,
                    undress=[slab(offset(SHAFT.cs, 8.0), ZS_E - LEDGE - 0.6, ZS_W + 0.01)])
    sh = sh + CO.ledge(SHAFT.pts, ZS_E, LEDGE, t=2.4)
    kit.add("SHAFT", "Tuscan", sh, group="shaft")
    rings, _ = CO.level(SHAFT.pts, ZS_E, HEADC, t=2.4)
    CO.add_level(kit, rings, "CORNICE-S", "cornice")
    ins += _add_inserts(kit, sh_ops)
    hh_ops = [op for op in OPENINGS if op.block is HEAD]
    hb_ = HEAD.cs
    hpieces = [(HEAD.pts, [1, 3], S_HH)]
    hg = [dict(p0=(HX0, HY0), p1=(HX1, HY0), slope=S_HH, e=0.3), dict(p0=(HX1, HY1), p1=(HX0, HY1), slope=S_HH, e=0.3)]
    ZH_EAVE = ZH_W + 1.2
    hrf = G.gabled_roof(hpieces, ZH_EAVE, 3.2, hg, texture="corrugated", tex_kw=dict(pitch=12.0, wtab=6.0, d=0.3),
                        skin=1.4, rake=2.6, inner_cs=offset(hb_, -2.4), fascia=1.2, hollow=2.2)
    hs, hn = hrf["walls"]
    hgab = [(HEAD, 0, hs["cs"].translate((0.0, ZH_EAVE - ZS_W))), (HEAD, 2, hn["cs"].translate((0.0, ZH_EAVE - ZS_W)))]
    hw = wall_shell([HEAD], hh_ops, t=2.4, belt=None, corners="none", water_table=False, siding=_skin, gables=hgab,
                    undress=[slab(offset(hb_, 8.0), ZH_E - LEDGE - 0.6, ZH_W + 0.01)])
    hw = hw + CO.ledge(HEAD.pts, ZH_E, LEDGE, t=2.4)
    kit.add("HEAD-WALLS", "Tuscan", hw, group="head")
    rings, _ = CO.level(HEAD.pts, ZH_E, HHE, t=2.4)
    CO.add_level(kit, rings, "CORNICE-H", "cornice")
    hroof = hrf["body"] + hrf["tex"] + hrf["skins"] + hrf["skin_tex"]
    hzr = ZH_EAVE + S_HH * ((HX1 - HX0) / 2 + 3.2)
    xc = (HX0 + HX1) / 2
    hroof = hroof + G.ridge_cap((xc, HY0 - 2.6), (xc, HY1 + 2.6), hzr, S_HH, ZH_W, half=1.0, up=0.6)
    for y in (HY0 - 1.6, HY1 + 1.6):
        hroof = hroof + M.cylinder(3.0, 0.5, 0.45, 12).translate([xc, y, hzr - 0.2]) + M.sphere(1.0, 14).translate([xc, y, hzr + 3.3])
    hroof = hroof.trim_by_plane([0, 0, 1.0], ZH_W)
    kit.add("HEAD-ROOF", "Galv", hroof, group="head")
    ins += _add_inserts(kit, hh_ops)
    print("shaft + head house", round(time.time() - t0, 1))

    # --- the chutes, the walkway railing, the ladder
    f = MAIN.facades()[0]
    for k, x in enumerate(CHUTES):
        A = f.A.copy()
        A[:, 3] = f.world(x, GATE_V, 0.0)
        c = YD.chute_apron().transform(A)
        kit.add(f"CHUTE-{k + 1}", "Iron", c, P=_face_P(A), key="CHUTE", group="chutes")
    L_r = DECK[2] - DECK[0]
    rl = YD.rail_walkway(L_r, h=11.0, ret=6.0).transform(np.array([[1.0, 0, 0, DECK[0]], [0, 1.0, 0, WALK], [0, 0, 1.0, Z_DECK]]))
    kit.add("RAILING", "Timber", rl, group="walkway")
    lad = YD.ladder_coal(Z_DECK - PAD_T, w=5.6)
    Aw = np.array([[0.0, 0.0, -1.0, DECK[0]], [1.0, 0.0, 0.0, -7.6], [0.0, 1.0, 0.0, PAD_T]])
    Pw = np.array([[0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], [1.0, 0.0, 0.0, 0.0]])
    kit.add("LADDER", "Timber", lad.transform(Aw), P=Pw, group="walkway")

    # --- the hoist house: formboard footing, board and batten, pick-and-shovel cornice, the stack
    ho_ops = [op for op in OPENINGS if op.block is HOIST]
    kb = HOIST.cs
    kpieces = [(HOIST.pts, [0, 2], S_K)]
    kg = [dict(p0=(KX1, KY0), p1=(KX1, KY1), slope=S_K, e=0.3), dict(p0=(KX0, KY1), p1=(KX0, KY0), slope=S_K, e=0.3)]
    ZK_EAVE = ZK_W + 1.2
    krf = G.gabled_roof(kpieces, ZK_EAVE, 4.0, kg, texture="corrugated", tex_kw=dict(pitch=14.0, wtab=6.0, d=0.3),
                        skin=1.4, rake=3.0, inner_cs=offset(kb, -2.4), fascia=1.2, hollow=2.2)
    ke, kw_ = krf["walls"]
    kgab = [(HOIST, 1, ke["cs"].translate((0.0, ZK_EAVE - ZK_F))), (HOIST, 3, kw_["cs"].translate((0.0, ZK_EAVE - ZK_F)))]
    kwall = wall_shell([HOIST], ho_ops, t=2.4, belt=None, corners="none", water_table=False, siding=_skin, gables=kgab,
                       undress=[slab(offset(kb, 8.0), ZK_E - LEDGE - 0.6, ZK_W + 0.01)])
    kwall = kwall + CO.ledge(HOIST.pts, ZK_E, LEDGE, t=2.4) - lip_keep(kb, 2.4, ZK_F, 1.2)
    kit.add("HOIST-WALLS", "Tuscan", kwall, group="hoist")
    kf = foundation([HOIST], 0.0, ZK_F, t=2.4, style="formboard", openings=[])
    kit.add("HOIST-FOUNDATION", "Concrete", kf, group="hoist")
    rings, _ = CO.level(HOIST.pts, ZK_E, HOE, t=2.4, cut=box([SX0 - 5, SY0 - 1.0, -10], [SX1 + 0.9, SY1 + 1.0, 400]))
    CO.add_level(kit, rings, "CORNICE-K", "cornice")
    kroof = krf["body"] + krf["tex"] + krf["skins"] + krf["skin_tex"]
    kzr = ZK_EAVE + S_K * ((KY1 - KY0) / 2 + 4.0)
    kroof = kroof + G.ridge_cap((KX0 - 3.0, YC), (KX1 + 3.0, YC), kzr, S_K, ZK_W, half=1.0, up=0.6)
    px, py = STACK
    zp = ZK_EAVE + S_K * (KY1 - py + 4.0) - 4.0
    stack = YD.stack_hoist(kzr + 38.0 - zp).translate([px, py, zp])
    kroof = (kroof - box([SX0 - 5, SY0 - 1.0, -10], [SX1 + 0.9, SY1 + 1.0, 400]) - M.cylinder(80.0, 1.75, 1.75, 28).translate([px, py, ZK_W])
             - stack).trim_by_plane([0, 0, 1.0], ZK_W)
    kit.add("HOIST-ROOF", "Galv", max(kroof.decompose(), key=lambda m_: m_.volume()), group="hoist")
    kit.add("STACK", "Iron", stack - M.cylinder(3.0, 5.0, 5.0, 12).translate([px, py, zp - 3.0]), group="hoist")
    ins += _add_inserts(kit, ho_ops)
    print("hoist house", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "blackwater")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "blackwater.npz"))
    import json
    json.dump({"materials": {k: list(v) for k, v in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
