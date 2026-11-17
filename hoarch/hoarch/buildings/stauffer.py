"""The Stauffer: an original HO-scale (1:87.1) Pennsylvania German farmhouse, house 45 of the
fourth batch (all Colonial).

A whitewashed limestone ground storey in random ashlar on a sandstone plinth, and over it a
storey of hewn logs chinked with lime, their ends dovetailed at the corners. Across the front
the log storey stands out 14 mm in a forebay, carried on the upper floor's joists, whose ends
show under it, and sheltering the front door: a Dutch door of boards on tulip-ended strap
hinges under a transom board carved with a heart between two tulips. The gables are boarded,
the boards' feet cut to points, a hex sign in each. Stone-storey windows in pegged plank
frames under sandstone lintels keyed with a heart, with board shutters sawn with tulips; the
log storey has pairs of casements under wave-cut head boards carved with tulips. The side
door has a bonnet hood. A steep roof of beaver-tail tiles cut to a point (Spitzschnitt), a
central stack with a dogtooth band, and a bake oven with its own little roof against the
east gable. Between the storeys (the forebay's girt) a barn-red frieze of tulip pots and
hearts over a course of saltires and a stepped crown; at the eave a barn-red frieze of
distelfinks over dentils, a soffit on heart-nosed brackets and a bevelled crown.

usage: python3 -m hoarch.buildings.stauffer [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, circle, offset, poly, rect, slab, union
from hoarch import colonial4 as C4, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.colonial import shutters_pair
from hoarch.kit import Kit, inv34, print_flip
from hoarch.shell import Block, Opening, _corbel, belt_ring, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Stauffer"
COLORS = {"Limestone": "#D8D0BF", "Logs": "#7A5A3E", "Cream": "#EEE6D2", "BarnRed": "#8E2F25", "Terracotta": "#A5543A",
          "Sandstone": "#9C6B4E", "Brick": "#8A4632", "Windows_Doors": "#EEE6D2"}
RENDER_MAT = {"Limestone": "stone", "Logs": "siding", "Cream": "trim", "BarnRed": "accent", "Terracotta": "roof",
              "Sandstone": "stone2", "Brick": "brick", "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Stauffer)
LEDGE = 1.4
JOINT = dict(pitch=15.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="tulippots", role="BarnRed"),
    dict(kind="course", h=1.4, b=1.4, orn="saltires", role="Cream"),
    dict(kind="crown", h=2.2, b=1.4, P=3.2, orn="stepped", role="Cream")])
EAVE = dict(pitch=14.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.2, b=1.2, orn="distelfinks", role="BarnRed"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Cream", tooth=0.8, gap=0.6),
    dict(kind="bed", h=2.2, b=1.4, P=5.6, role="Cream", brackets=dict(style="heart", t=1.4, reach=0.3)),
    dict(kind="crown", h=2.6, b=1.4, P=6.2, orn="bevel", role="Cream")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 6.0
S1 = ZF + 40.0
ZU = S1 + RJ
ZE = ZU + 36.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 6.0, 6.2, 1.8
S_MAIN = 1.05
W, D, FB = 184.0, 100.0, 14.0                   # the log storey stands FB out over the front (the forebay)
LOW = Block("lower", [(0, 0), (W, 0), (W, D), (0, D)], ZF, S1)
UP = Block("upper", [(0, -FB), (W, -FB), (W, D), (0, D)], ZU, ZW)
BLOCKS = [LOW, UP]
YR = (D - FB) / 2                               # the ridge line
V1, V2 = 7.0, 6.0
XCH = 84.0                                      # the central stack (off centre, Continental plan)


def _stone(f, b, reg):
    return C4.limestone_random(reg, seed=int(abs(f.n[0]) * 3 + abs(f.n[1]) * 7 + f.p0[0]) % 97)


def _logs(f, b, reg):
    out = []
    lo = reg ^ rect(-1, -10, f.L + 1, ZE - LEDGE - 0.6 - b.z0)
    hi = reg ^ rect(-1, ZW - b.z0 + 0.2, f.L + 1, 999)
    if not lo.is_empty():
        out.append(C4.logs_dovetail(lo, f.L, datum=0.0))
    if not hi.is_empty():
        out.append(C4.boards_pointed(hi, datum=ZW - b.z0 + 0.2))
    return union(out) if out else M()


def _openings():
    L1, L2, SH = [], [], []

    def add(L, blk, x, y, v0, sp, name, kind="window", shut=False):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        if shut:
            SH.append(name)

    lo = C4.window_pegframe(9.6, 18.0)
    up = C4.window_casement_tulip(10.0, 14.0)
    for x in (26.0, 124.0, 158.0):
        add(L1, LOW, x, 0.0, V1, lo, f"S{x:.0f}-1", shut=True)
    add(L1, LOW, 70.0, 0.0, 0.4, C4.door_forebay(11.0, 22.0), "front-door", "door")
    for x in (40.0, 144.0):
        add(L1, LOW, x, D, V1, lo, f"N{x:.0f}-1", shut=True)
    add(L1, LOW, 92.0, D, 0.4, C4.door_forebay(10.0, 20.0, transom=2.6), "back-door", "door")
    for y in (20.0, 80.0):
        add(L1, LOW, 0.0, y, V1, lo, f"W{y:.0f}-1", shut=True)
    add(L1, LOW, 0.0, 50.0, 0.4, C4.door_bonnet(10.0, 22.0), "side-door", "door")
    for y in (18.0, 82.0):
        add(L1, LOW, W, y, V1, lo, f"E{y:.0f}-1", shut=True)
    for x in (24.0, 60.0, 96.0, 132.0, 164.0):
        add(L2, UP, x, -FB, V2, up, f"S{x:.0f}-2")
    for x in (40.0, 92.0, 144.0):
        add(L2, UP, x, D, V2, up, f"N{x:.0f}-2")
    for x_, tag in ((0.0, "W"), (W, "E")):
        for y in (14.0, 72.0):
            add(L2, UP, x_, y, V2, up, f"{tag}{y:.0f}-2")
    return L1, L2, SH


OPEN1, OPEN2, SHUTTERED = _openings()
OPENINGS = OPEN1 + OPEN2


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    rf = G.gabled_roof([(UP.pts, [0, 2], S_MAIN)], Z_EAVE, D_EAVE,
                       [dict(p0=(W, -FB), p1=(W, D), slope=S_MAIN, e=0.3), dict(p0=(0.0, D), p1=(0.0, -FB), slope=S_MAIN, e=0.3)],
                       texture="gothic", tex_kw=dict(pitch=1.6, wtab=2.4, d=0.4), skin=SKIN, rake=RAKE,
                       inner_cs=offset(UP.cs, -3.0), fascia=FASCIA, hollow=2.8)
    we, ww = rf["walls"]
    gables = [(UP, 1, we["cs"].translate((0.0, Z_EAVE - ZU))), (UP, 3, ww["cs"].translate((0.0, Z_EAVE - ZU)))]
    zr = Z_EAVE + S_MAIN * ((D + FB) / 2 + D_EAVE)
    # --- the stone storey; the girt (the joint ring on the log storey's outline); the log storey
    w1 = wall_shell([LOW], OPEN1, t=3.0, belt=None, corners="none", water_table=False, siding=_stone,
                    partitions=[((XCH - 10.0, 3.0), (XCH - 10.0, D - 3.0), 2.0, ZF, S1)])
    w1 = w1 - lip_keep(LOW.cs, 3.0, ZF, 1.2)
    w1 = w1 + _corbel(LOW.cs, 3.0, S1) + lip_ring(LOW.cs, 3.0, S1)
    kit.add("WALLS-1", "Limestone", w1, group="walls")
    up_path = max(UP.cs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    ring = belt_ring(up_path, S1, t=3.0, prof=CO.joint_profile(RJ, LEDGE), blocks=None) - lip_keep(LOW.cs, 3.0, S1)
    kit.add("JOINT", "Logs", ring, group="walls")
    undress = [slab(offset(UP.cs, 9.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    w2 = wall_shell([UP], OPEN2, t=3.0, belt=None, corners="none", water_table=False, siding=_logs, gables=gables,
                    undress=undress, partitions=[((XCH - 10.0, 3.0 - FB), (XCH - 10.0, D - 3.0), 2.0, ZU, ZW)])
    w2 = w2 - lip_keep(UP.cs, 3.0, ZU)
    no_lip = union([box([W - 5.0, -FB - 1, ZW - 1], [W + 1, D + 1, ZW + 5]), box([-1, -FB - 1, ZW - 1], [5.0, D + 1, ZW + 5])])
    w2 = w2 + ((_corbel(UP.cs, 3.0, ZW) + lip_ring(UP.cs, 3.0, ZW)) - no_lip) + CO.ledge(up_path, ZE, LEDGE)
    # a hex sign in each gable, seated in a shallow pocket in the boards
    hexes = []
    zc = Z_EAVE + 15.0
    for A in (np.array([[0, 0, 1.0, W + 0.1], [1.0, 0, 0, YR], [0, 1.0, 0, zc]]),
              np.array([[0, 0, -1.0, -0.1], [-1.0, 0, 0, YR], [0, 1.0, 0, zc]])):
        hexes.append(A)
        w2 = w2 - C4.ext(circle((0, 0), 5.15, 64), -0.2, 3.0).transform(A)
    walls2 = kit.add("WALLS-2", "Logs", w2, group="walls")
    rings, _ = CO.level(up_path, S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(up_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation([LOW], 0.0, ZF, style="stoneplinth")
    kit.add("FOUNDATION", "Sandstone", fnd, group="foundation")
    for k, A in enumerate(hexes):
        kit.add(f"HEXSIGN-{k}", "BarnRed", C4.hex_sign(5.0).transform(A), P=inv34(A), key="HEXSIGN", group="walls")
    # the forebay's floor under the girt, the joists' ends showing under it
    fb = box([0.0, -FB, S1 - 1.6], [W, 0.0, S1])
    joists = union([box([x - 0.7, -FB - 0.8, S1 - 3.4], [x + 0.7, 0.0, S1 - 1.59]) for x in np.arange(6.0, W - 3.0, 11.5)])
    kit.add("FOREBAY", "Logs", (fb + joists) - w1 - fnd, P=print_flip(), group="walls")
    ins_keep = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                       group="inserts", render=zones)
        ins_keep.append(part.solid)
        if o.name in SHUTTERED:
            w_op, h_op = b[2] - b[0], b[3] - b[1]
            left, right = shutters_pair(w_op, h_op, casing=1.7, gap=0.4, make=C4.shutter_tulip)
            for s_, m in (("L", left), ("R", right)):
                kit.add(f"SHUTTER-{o.name}-{s_}", "BarnRed", m.translate([0, 0, 0.45]).transform(A),
                        P=inv34(A), key=f"SHUTTER-{h_op:.1f}", group="shutters")
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the roof: pointed beaver-tail tiles, a ridge cap, the central stack
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((-RAKE, YR), (W + RAKE, YR), zr, S_MAIN, ZW) - walls_env)
    roof = roof - lip_keep(UP.cs, 3.0, ZW)
    solid_env, _ = R.hip_roof([(UP.pts, [0, 2], S_MAIN)], Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 12.0, 10.0
    z0 = round((zr - 8.0) / 0.2) * 0.2
    roof = roof + (box([XCH - CW / 2 - 1.2, YR - CD / 2 - 1.2, ZW + 0.01], [XCH + CW / 2 + 1.2, YR + CD / 2 + 1.2, z0 + 0.01]) ^ solid_env)
    roof = roof - box([XCH - CW / 2 - 0.4, YR - CD / 2 - 0.4, z0], [XCH + CW / 2 + 0.4, YR + CD / 2 + 0.4, zr + 40])
    kit.add("ROOF", "Terracotta", roof, group="roof")
    kit.add("CHIMNEY", "Brick", C4.chimney_dogtooth(CW, CD, zr + 13.0 - z0).translate([XCH, YR, z0]), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the bake oven against the east gable
    Ao = np.array([[0, 1.0, 0, W], [-1.0, 0, 0, 50.0], [0, 0, 1.0, 0.0]])
    ob, orf, ofl = C4.bakeoven(30.0, 16.0, 13.0, 8.0)
    oven = (ob + ofl).transform(Ao) - fnd - w1
    kit.add("BAKEOVEN", "Limestone", max(oven.decompose(), key=lambda m_: m_.volume()), group="oven")
    kit.add("BAKEOVEN-roof", "Terracotta", orf.transform(Ao) - w1 - walls2.solid, group="oven")

    # --- steps at the three doors
    for (x, y), wd in (((70.0, 0.0), 16.0), ((92.0, D), 15.0), ((0.0, 50.0), 15.0)):
        e, u = LOW.locate(x, y)
        f = LOW.facades()[e]
        A = f.A.copy()
        A[:, 3] = f.world(u, -ZF, 1.4)
        kit.add(f"STOOP-{e}", "Sandstone", FT.steps(wd, ZF - 0.6, 2).transform(A) - fnd, group="steps")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "stauffer")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "stauffer.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
