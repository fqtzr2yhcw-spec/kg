"""The Westbrook: an original HO-scale (1:87.1) Colonial Revival house with a Victorian flair,
house 38 of the third batch (after the user's photo 1).

A white five-bay house of Colonial clapboard (short bevelled boards with staggered butt
joints) on a rubble foundation under a dressed cap, beaded corner boards and black shutters
with tilt rods. Across the middle of the front a bowed portico on six slender Ionic columns
carries a curved entablature (a frieze of roundels, dentils) and a balustrade of turned
balusters round the balcony on its roof; the fanlit entrance (a six-panel door between
sidelights under an elliptical fanlight) and two pairs of French doors open under it, and a
pair of French doors opens onto the balcony. Six-over-six windows: under a dentilled cornice
cap below, a plain cap above. Between the storeys a dove-grey frieze of ribbon and stick, a
white bead course and a white crown; at the eave a dove-grey frieze of Federal gouge-work,
white dentils, a soffit on white leaf modillions and a white cyma; on the west wing a
dove-grey frieze of urns and bead drapery. A slate hip roof banded with sawtooth courses and
three gabled dormers with cornice returns and fanned round-headed windows; a bridged chimney
at each end of the ridge; a storey-and-a-half wing to the west under its own hip and dormer.

usage: python3 -m hoarch.buildings.westbrook [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType

from hoarch.core import box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import colonial as C, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Westbrook"
COLORS = {"White": "#F1F0EB", "Dove": "#B7BCB8", "Black": "#26282B", "Slate": "#565C63", "Brick": "#8E4A3A",
          "Stone": "#9B968C", "PorchDeck": "#F1F0EB", "Planks": "#6E7479", "Windows_Doors": "#F1F0EB"}
RENDER_MAT = {"White": "siding", "Dove": "accent", "Black": "shutter", "Slate": "roof", "Brick": "brick", "Stone": "stone",
              "PorchDeck": "trim", "Planks": "planks", "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Westbrook)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="ribbon", role="Dove"),
    dict(kind="course", h=1.4, b=1.4, orn="beadreel", role="White"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="reverse", role="White")])
EAVE = dict(pitch=11.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.4, b=1.2, orn="gougework", role="Dove"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="White", tooth=0.8, gap=0.7),
    dict(kind="bed", h=2.2, b=1.4, P=6.4, role="White", brackets=dict(style="leafy", t=1.2, reach=0.35)),
    dict(kind="crown", h=2.8, b=1.4, P=7.2, orn="cyma", role="White")])
WING_C = dict(pitch=10.0, margin=3.4, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="urns", role="Dove"),
    dict(kind="crown", h=2.2, b=1.4, P=4.2, orn="ovolo", role="White")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 14.0
S1 = ZF + 42.0
ZE = S1 + RJ + 38.0
ZW = ZE + HE
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
D_EAVE = 7.6
S_MAIN = 0.75
V1 = 8.0
V2 = S1 + RJ + 5.0 - ZF
WING_ZE = ZF + 34.0
WING_ZW = WING_ZE + CO.band_height(WING_C)
S_WING = 0.8

# ------------------------------------------------------------------ plan (x east, y north; the front faces south)
W, D = 172.0, 100.0
XC = W / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
WY0, WY1, WX0 = 16.0, 84.0, -54.0
WING = Block("wing", [(WX0, WY0), (0.0, WY0), (0.0, WY1), (WX0, WY1)], ZF, WING_ZW)
BLOCKS = [MAIN, WING]
# the bowed portico: an arc bulging DEPTH out from the chord XC +- HALF on the front wall
HALF, DEPTH = 32.0, 22.0
PR = (HALF ** 2 + DEPTH ** 2) / (2 * DEPTH)
PC = (XC, -DEPTH + PR)
A0, A1 = math.atan2(-PC[1], -HALF), math.atan2(-PC[1], HALF)
H_FLOOR = ZF - 1.4
ENT_H = 5.0
ZPT = S1 + RJ                       # the balcony floor, level with the second floor


def _siding(f, b, reg):
    """Colonial clapboard; nothing in the cornice bands."""
    top = (WING_ZE if b is WING else ZE) - b.z0
    reg = reg - rect(-1, top, f.L + 1, 999)
    return C.clapboard_butt(reg, datum=0.6, seed=int(f.p0[0] * 7 + f.p0[1] * 3) % 97)


def _openings():
    L, SH = [], []

    def add(blk, x, y, v0, sp, name, kind="window", shutters=False):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        if shutters:
            SH.append(name)

    lo = C.window_capped(9.6, 24.0, "cornice")
    up = C.window_capped(9.6, 21.0, "cap")
    wlo = C.window_capped(8.8, 21.0, "cap")
    # the front: windows outside the portico, the entrance and French doors under it
    for x in (18.0, W - 18.0):
        add(MAIN, x, 0.0, V1, lo, f"S{x:.0f}-1", shutters=True)
    add(MAIN, XC, 0.0, 0.4, C.door_fanlight(11.0, 32.0), "front-door", "door")
    for x in (XC - 23.0, XC + 23.0):
        add(MAIN, x, 0.0, 0.4, C.door_french(11.0, 28.0), f"S{x:.0f}-french", "door")
    for x in (18.0, 46.0, W - 46.0, W - 18.0):
        add(MAIN, x, 0.0, V2, up, f"S{x:.0f}-2", shutters=True)
    add(MAIN, XC, 0.0, ZPT - ZF + 0.4, C.door_french(12.0, 29.0, transom=4.4), "balcony-door", "door")
    # the east end
    for y in (26.0, 74.0):
        add(MAIN, W, y, V1, lo, f"E{y:.0f}-1", shutters=True)
        add(MAIN, W, y, V2, up, f"E{y:.0f}-2", shutters=True)
    # the back
    for x in (18.0, 50.0, W - 50.0, W - 18.0):
        add(MAIN, x, D, V1, lo, f"N{x:.0f}-1", shutters=True)
        add(MAIN, x, D, V2, up, f"N{x:.0f}-2", shutters=True)
    add(MAIN, XC, D, 0.4, C.door_french(11.0, 28.0), "back-door", "door")
    add(MAIN, XC, D, V2, up, f"N{XC:.0f}-2", shutters=True)
    # the wing
    for x in (WX0 + 14.0, -14.0):
        add(WING, x, WY0, 7.0, wlo, f"wS{-x:.0f}", shutters=True)
    for y in (WY0 + 20.0, WY1 - 20.0):
        add(WING, WX0, y, 7.0, wlo, f"wW{y:.0f}", shutters=True)
    add(WING, WX0 / 2, WY1, 7.0, wlo, "wN", shutters=True)
    return L, SH


OPENINGS, SHUTTERED = _openings()


def portico_floor():
    """The bowed portico's floor: a painted plinth under a planked floor (one part, printed
    upside down: the planks first, one filament change), and its steps."""
    n = 24
    arc = [(PC[0] + PR * math.cos(a), PC[1] + PR * math.sin(a)) for a in np.linspace(A0, A1, n + 1)]
    pts = [(XC + HALF, 0.0), (XC - HALF, 0.0)] + arc[:-1]
    pts = [(XC - HALF, 0.0)] + arc[1:-1] + [(XC + HALF, 0.0)]
    cs = poly(pts)
    base = slab(cs, 0.0, H_FLOOR - 1.2)
    cap = slab(cs.offset(0.4, JoinType.Miter, 4.0) ^ rect(-500, -500, 500, -0.02), H_FLOOR - 2.0, H_FLOOR - 1.2)
    outer = list(range(len(pts) - 1))
    planks = FT.porch_planks(pts, outer, H=H_FLOOR, pitch=1.6, crack=0.25, border=1.4, along=(0.0, -1.0))
    return base + cap + planks


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    allcs = cs_union([b.cs for b in BLOCKS])
    undress = [slab(offset(MAIN.cs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(WING.cs, 8.0) - offset(MAIN.cs, 2.0), WING_ZE - LEDGE - 0.6, WING_ZW + 0.01)]
    clear = [lip_keep(allcs, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="beaded", siding=_siding, clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    main_keep = MAIN.solid(grow=0.8, dz0=-2, dz1=400)
    wing_ledge = CO.ledge(WING.pts, WING_ZE, LEDGE) - main_keep
    wing_lip = (_corbel(WING.cs, 3.0, WING_ZW) + lip_ring(WING.cs, 3.0, WING_ZW)) - MAIN.solid(grow=0.2, dz0=-2, dz1=400)
    kit.add("WALLS-1", "White", st["shells"][0] + wing_ledge + wing_lip, group="walls")
    # the wing's hip roof (under the joint cornice, which is cut back to it)
    wd = WING_C["layers"][-1]["P"] + 0.6
    wze = WING_ZW + 1.4
    wroof, wtex = R.hip_roof([(WING.pts, [0, 2, 3])], wze, S_WING, wd, texture=["square", "square", "square", "saw", "saw"],
                             tex_kw=dict(pitch=1.5, wtab=2.0, d=0.38), zlo=WING_ZW)
    wing_env, _ = R.hip_roof([(WING.pts, [0, 2, 3])], wze + 0.5, S_WING, wd + 0.5, texture=None, zlo=WING_ZW - 1.0)
    joint_keep = slab(offset(MAIN.cs, 2.0), S1 - 2.2, S1 + RJ + 0.2)
    kit.add("JOINT", "White", st["rings"][0], group="walls")
    lip = _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)
    kit.add("WALLS-2", "White", st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")

    # the portico (its box cuts the joint cornice where it meets the front)
    zcol = ZPT - ENT_H
    PO = C.bowed_portico(PC, PR, A0, A1, H_FLOOR, zcol, ent_h=ENT_H, n_cols=6, col_r=1.6, rail_h=7.0, col_trim=0.27,
                         wall_y=-0.44)
    front_keep = box([-500, -500, -50], [500, -0.02, 500])
    arc_cs = poly([(PC[0] + (PR + 2.6) * math.cos(a), PC[1] + (PR + 2.6) * math.sin(a)) for a in np.linspace(A0 - 0.1, A1 + 0.1, 40)])
    port_env = slab(arc_cs.offset(1.0, JoinType.Round), zcol - 0.4, ZPT + 8.0)
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=union([wing_env, port_env]))
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(WING.pts, WING_ZE, WING_C, cut=main_keep)
    CO.add_level(kit, rings, "CORNICE-W", "cornice")
    kit.add("ROOF-wing", "Slate", (wroof + wtex) - main_keep - joint_keep - lip_keep(WING.cs, 3.0, WING_ZW), group="roof")
    fnd = foundation(BLOCKS, 0.0, ZF, style="capstone")
    kit.add("FOUNDATION", "Stone", fnd, group="foundation")

    # windows, doors and shutters
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{o.v0 > 20}", group="inserts", render=zones))
        if o.name in SHUTTERED:
            w_op, h_op = b[2] - b[0], b[3] - b[1]
            left, right = C.shutters_pair(w_op, h_op, casing=1.1, gap=0.7, make=C.shutter_rod)
            for side, m in (("L", left), ("R", right)):
                kit.add(f"SHUTTER-{o.name}-{side}", "Black", m.translate([0, 0, 0.44]).transform(A), P=inv34(A),
                        key=f"SHUTTER-{h_op:.1f}", group="shutters")
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the main roof: a banded slate hip with three dormers and two bridged chimneys
    roof, rtex = R.hip_roof([(MAIN.pts, [0, 1, 2, 3])], Z_EAVE, S_MAIN, D_EAVE,
                            texture=["square", "square", "square", "saw", "saw"], tex_kw=dict(pitch=1.5, wtab=2.0, d=0.38),
                            zlo=ZW)
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    inner, _ = R.hip_roof([(MAIN.pts, [0, 1, 2, 3])], Z_EAVE - 2.8 * math.sqrt(1 + S_MAIN ** 2), S_MAIN, D_EAVE, texture=None)
    roof = (roof - (inner ^ slab(offset(MAIN.cs, -3.0), ZW - 1, zr + 50))) + rtex
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    roof = roof + union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.2, up=0.6, drop=1.8)
                         for c, e in zip(corners, ends)])
    roof = roof + G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZW, half=1.2, up=0.6)
    roof = roof - lip_keep(base, 3.0, ZW)
    solid_env, _ = R.hip_roof([(MAIN.pts, [0, 1, 2, 3])], Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 20.0, 8.0
    chims = [(D / 2 + 2.0, D / 2), (W - D / 2 - 2.0, D / 2)]
    pockets, stacks = [], []
    for (cx, cy) in chims:
        zroof = Z_EAVE + S_MAIN * (min(cx, W - cx, cy, D - cy) - CW / 2 + D_EAVE)
        z0 = round((min(zroof, zr - S_MAIN * CD / 2) - 3.0) / 0.2) * 0.2
        roof = roof + G.chimney_seat(solid_env, cx, cy, CW / 2, zr + 1.0)
        pockets.append(box([cx - CW / 2 - 0.4, cy - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CD / 2 + 0.4, zr + 40]))
        stacks.append(C.chimney_bridged(CW, CD, zr + 20.0 - z0).translate([cx, cy, z0]))
    roof = roof - union(pockets)
    # three dormers on the front slope, the middle one wider; one on the wing's front slope
    dyf = 16.0
    zdf = round((Z_EAVE + S_MAIN * (dyf + D_EAVE) - 1.0) / 0.2) * 0.2
    dorms = []
    for dxc, dw in ((XC - 46.0, 15.0), (XC, 18.0), (XC + 46.0, 15.0)):
        dbody, dcore, dface = C.dormer_returns(dw, 18.0, 13.0)
        Ad = np.array([[1.0, 0, 0, dxc], [0, 0, -1.0, dyf], [0, 1.0, 0, zdf]])
        dkeep = ext(dface.offset(0.3, JoinType.Miter, 4.0), -18.3, 0.3).transform(Ad)
        dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
        dseat = box([dxc - dw / 2 - 1.3, dyf - 1.6, ZW], [dxc + dw / 2 + 1.3, dyf + 18.0 + 1.3, zdf]) ^ solid_env
        dorms.append((dw, dbody, dcore, Ad, dpocket, dseat))
    for d_ in dorms:
        roof = roof - d_[4]
    for d_ in dorms:
        roof = roof + (d_[5] - d_[4] - lip_keep(base, 3.0, ZW))
    kit.add("ROOF", "Slate", roof, group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Brick", s_, key="CHIMNEY", group="roof")
    for k, (dw, dbody, dcore, Ad, dpocket, dseat) in enumerate(dorms):
        rise = dw / 2
        ez = 13.0 - 1.6
        droof_cs = poly([(-dw / 2 - 1.6, ez), (-dw / 2, ez), (-dw / 2, 13.0), (0.0, 13.0 + rise + 0.2), (dw / 2, 13.0),
                         (dw / 2, ez), (dw / 2 + 1.6, ez), (dw / 2 + 1.6, ez + 1.6), (0.0, 13.0 + rise + 2.2),
                         (-dw / 2 - 1.6, ez + 1.6)])
        kit.add(f"DORMER-{k}", "White", dbody.transform(Ad), key=f"DORMER-{dw:.0f}", group="roof")
        kit.add(f"DORMER-core-{k}", "Slate", dcore.transform(Ad), key=f"DORMER-core-{dw:.0f}", group="roof")
        droof = ext(droof_cs, -24.0, 1.2).transform(Ad) - solid_env - dbody.transform(Ad) - roof
        kit.add(f"DORMER-roof-{k}", "Slate", droof, key=f"DORMER-roof-{dw:.0f}", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the bowed portico
    ent = (PO["ent"] ^ front_keep)
    # the balcony floor inside the entablature's ring, flush with its top
    arc_in = [(PC[0] + (PO["Rc"] - 1.0) * math.cos(a), PC[1] + (PO["Rc"] - 1.0) * math.sin(a)) for a in np.linspace(A0, A1, 40)]
    deck_cs = poly([(XC - HALF, 0.0)] + arc_in[1:-1] + [(XC + HALF, 0.0)]) ^ rect(-500, -500, 500, -0.02)
    ent = ent + slab(deck_cs, zcol + 1.6, ZPT)
    # the columns in one piece with it (printed upside down on the flat deck), each foot
    # dropping into a snug recess in the floor: no column is glued on its own
    Rc = PR - 2.6
    cxy = [(PC[0] + Rc * math.cos(a), PC[1] + Rc * math.sin(a)) for a in np.linspace(A0 + 0.27, A1 - 0.27, 6)]
    seats = [FT.column_seats(x, y, H_FLOOR, zcol, ("round", 1.6 + 0.6), dfoot=1.6) for x, y in cxy]
    ent = ent + union(PO["cols"]) + union([a_ for a_, _, _ in seats])
    ent = ent - MAIN.solid(grow=0.0, dz0=-1, dz1=1) - st["rings"][0]
    kit.add("PORTICO-top", "White", ent, P=print_flip(), group="portico")
    rail = (PO["rail"] ^ front_keep) - MAIN.solid(grow=0.0, dz0=-1, dz1=1)
    kit.add("BALCONY-rail", "White", rail, group="portico")
    pf = portico_floor() - fnd - union([f_ for _, f_, _ in seats])
    kit.add("PORTICO-floor", "PorchDeck", pf, P=print_flip(), group="portico",
            render=FT.plank_zones(pf, H_FLOOR, "Planks", "PorchDeck"))
    f0 = MAIN.facades()[0]
    A = f0.A.copy()
    A[:, 3] = f0.world(XC, -ZF, DEPTH)
    kit.add("STEPS-front", "Stone", FT.steps(24.0, H_FLOOR - 0.6, 5, cheek=1.8).transform(A) - pf, group="portico")
    e, u = MAIN.locate(XC, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Stone", FT.steps(15.0, ZF - 0.6, 5).transform(A) - fnd, group="portico")
    print("specks dropped:", kit.drop_specks())
    print("portico", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "westbrook")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "westbrook.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
