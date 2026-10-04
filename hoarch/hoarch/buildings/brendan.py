"""St. Brendan's Church: an original HO-scale (1:87.1) Gothic Revival parish church, building 62
(the railroad and town batch).

A High Victorian Gothic church of about 1878 in red brick banded with buff (polychromy) on a
snecked rubble plinth: a steep nave between stepped buttresses, a tower at the west corner
rising through a stage of lancets and clocks and a louvred belfry to an octagonal spire of slates pointed
in zigzag bands, with a gabled pinnacle at each corner and a stone cross at the tip. The west
front has a rose window of eight cusped petals over a door of three receding orders under a
gablet with a trefoil; lancets of diamond quarries under hood moulds light the nave, three
stepped lancets the east end. Cornices of blind tracery over four-leaf flowers (the eave and the
tower's string) and leafy crockets under the tower top.

usage: python3 -m hoarch.buildings.brendan [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, slab, union
from hoarch import cornice as CO, features as FT, gables as G, openings as O, town as TN
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "St. Brendan's Church"
COLORS = {"Brick": "#8E3B2A", "Buff": "#D6C298", "Stone": "#C4BDAD", "Slate": "#4A5058", "Rubble": "#8F8778",
          "Windows_Doors": "#C4BDAD"}
RENDER_MAT = {"Brick": "brick", "Buff": "buff", "Stone": "stone", "Slate": "roof", "Rubble": "rubble",
              "Windows_Doors": "stone", "Door": "door", "Glass": "glass", "Dial": "dial", "Hands": "hands"}
PALETTE = {"brick": ("#8E3B2A", 0.9), "buff": ("#D6C298", 0.8), "stone": ("#C4BDAD", 0.85), "roof": ("#4A5058", 0.8),
           "rubble": ("#8F8778", 0.9), "door": ("#6B4A2E", 0.6), "dial": ("#EFEADC", 0.6), "hands": ("#1E1E1E", 0.5)}
VIEWS = {"hero": [-36, 14, 70, 0.95, [0, 0, 0]], "front": [0, 6, 80, 0.92, [0, 0, 0]], "rear": [150, 16, 70, 0.95, [0, 0, 0]],
         "right": [60, 12, 70, 0.95, [0, 0, 0]]}

# ------------------------------------------------------------------ cornices (unique to St. Brendan's)
LEDGE = 1.4
EAVE = dict(pitch=10.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.6, b=1.2, orn="tracery", role="Buff"),
    dict(kind="course", h=1.8, b=1.4, orn="fourleaf", role="Stone"),
    dict(kind="crown", h=2.4, b=1.4, P=4.6, orn="torus", role="Buff")])
JOINT = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="tracery", role="Buff"),
    dict(kind="course", h=1.6, b=1.4, orn="fourleaf", role="Stone"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="reverse", role="Buff")])
TOWER_C = dict(pitch=6.0, margin=2.4, layers=[
    dict(kind="frieze", h=5.0, b=1.2, orn="crockets", role="Stone"),
    dict(kind="course", h=1.6, b=1.4, orn="fourleaf", role="Buff"),
    dict(kind="crown", h=2.4, b=1.4, P=4.2, orn="ovolo", role="Stone")])
HE = CO.band_height(EAVE)
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2

# ------------------------------------------------------------------ levels and plan
ZF = 10.0
ZE = ZF + 52.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 5.0, 4.0, 1.8
S_NAVE = 1.05
W_N, D_N = 96.0, 150.0
XC = W_N / 2
ZR = Z_EAVE + S_NAVE * (W_N / 2 + D_EAVE)          # the nave ridge
S1 = round((ZR + 6.0) / 0.2) * 0.2                 # the tower's string course, clear over the ridge
ZT = S1 + RJ + 34.0                                # the tower's cornice
ZTW = round((ZT + CO.band_height(TOWER_C)) / 0.2) * 0.2
TX0, TX1, TY0, TY1 = -32.0, 3.0, -10.0, 25.0        # the tower, overlapping the nave's west wall
TCX, TCY = (TX0 + TX1) / 2, (TY0 + TY1) / 2
NAVE = Block("nave", [(0, 0), (W_N, 0), (W_N, D_N), (0, D_N)], ZF, ZW)
TOWER = Block("tower", [(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)], ZF, ZTW)
BLOCKS = [NAVE, TOWER]
SP_H = 62.0


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    side = TN.window_lancet(8.0, 32.0)
    add(NAVE, XC, 0.0, 0.4, TN.door_west(14.0, 30.0), "west-door", "door")
    for x in (26.0, 74.0):
        add(NAVE, x, 0.0, 12.0, TN.window_lancet(7.0, 26.0), f"S{x:.0f}")
    add(NAVE, XC, 0.0, Z_EAVE - ZF + 6.0, TN.window_rose(24.0), "rose")
    for y in (45.0, 75.0, 105.0, 135.0):
        add(NAVE, 0.0, y, 10.0, side, f"W{y:.0f}")
    for y in (15.0, 45.0, 75.0, 105.0, 135.0):
        add(NAVE, W_N, y, 10.0, side, f"E{y:.0f}")
    add(NAVE, XC, D_N, 8.0, TN.window_lancet(10.0, 38.0), "east-C")
    for x in (XC - 15.0, XC + 15.0):
        add(NAVE, x, D_N, 11.0, TN.window_lancet(7.0, 30.0), f"east-{x:.0f}")
    # the tower: a door and a lancet on the front, lancets on the free sides, a louvred belfry
    add(TOWER, TCX, TY0, 0.4, TN.door_tower(10.0, 26.0), "tower-door", "door")
    add(TOWER, TCX, TY0, 42.0, TN.window_lancet(7.0, 24.0), "T-S")
    add(TOWER, TX0, TCY, 30.0, TN.window_lancet(7.0, 24.0), "T-W")
    add(TOWER, TCX, TY1, 42.0, TN.window_lancet(7.0, 24.0), "T-N")
    vb = S1 + RJ - ZF + 5.0
    bel = TN.window_belfry(10.0, 20.0)
    for (x, y, nm) in ((TCX, TY0, "S"), (TX1, TCY, "E"), (TCX, TY1, "N"), (TX0, TCY, "W")):
        add(TOWER, x, y, vb, bel, f"belfry-{nm}")
    return L


OPENINGS = _openings()


CLOCK_V, CLOCK_D = 92.0, 16.0                     # the tower clocks (front and west faces), v from ZF
CLOCKS = (0, 3)                                    # TOWER facade edges


def _skin(f, b, reg):
    if b is NAVE:
        reg = reg - TN.rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    else:
        reg = reg - TN.rect(-1, ZT - LEDGE - 0.6 - b.z0, f.L + 1, 999)
        if any(np.allclose(TOWER.facades()[e].n, f.n) for e in CLOCKS):          # the clock's plain field
            reg = reg - TN.circle((f.L / 2, CLOCK_V), CLOCK_D / 2 + 2.0, 64)
    return TN.brick_polychrome(reg, datum=0.0)


def _buttresses():
    """Stepped buttresses between the nave's bays and at its free corners, (facade, u) pairs."""
    fs = NAVE.facades()
    out = [(fs[1], y) for y in (30.0, 60.0, 90.0, 120.0)]                    # east side: u = y
    out += [(fs[3], D_N - y) for y in (30.0, 60.0, 90.0, 120.0)]             # west side: u runs north to south
    out += [(fs[0], W_N - 2.5), (fs[2], 2.5), (fs[2], W_N - 2.5)]           # the free corners, front and back
    return out


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = NAVE.cs
    pieces = [(NAVE.pts, [1, 3], S_NAVE)]
    gdefs = [dict(p0=(0.0, 0.0), p1=(W_N, 0.0), slope=S_NAVE, e=0.3), dict(p0=(W_N, D_N), p1=(0.0, D_N), slope=S_NAVE, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="zigband", tex_kw=dict(pitch=1.8, wtab=2.4, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    ws, wn = rf["walls"]
    gables = [(NAVE, 0, ws["cs"].translate((0.0, Z_EAVE - ZF))), (NAVE, 2, wn["cs"].translate((0.0, Z_EAVE - ZF)))]
    tw = TOWER.solid(grow=0.6, dz0=-5, dz1=500)          # clear of the brick relief
    undress = [slab(offset(base, 9.0) - offset(TOWER.cs, 3.5), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 9.0), ZT - LEDGE - 0.6, ZTW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=gables,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    no_lip = union([box([-10, -10, ZW - 1], [W_N + 10, 5.0, ZW + 5]), box([-10, D_N - 5.0, ZW - 1], [W_N + 10, D_N + 10, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip - tw
    ledge = CO.ledge(NAVE.pts, ZE, LEDGE) - TOWER.solid(grow=0.2, dz0=-1, dz1=1)
    btr = union([f.place(TN.buttress(ZE - ZF - 2.0).translate([u, 0.0, 0.0])) for f, u in _buttresses()])
    w1 = st["shells"][0] + lip + ledge + btr
    w1 = w1 - lip_keep(base, 3.0, ZF, 1.2) - lip_keep(TOWER.cs, 3.0, ZF, 1.2)
    bands = union([box([-100, -100, z0], [300, 300, z1]) for z0, z1 in TN.band_rows(ZF, ZTW, ZF)])
    kit.add("WALLS-1", "Brick", w1, group="walls", render=[("Brick", w1 - bands), ("Buff", w1 ^ bands)])
    kit.add("JOINT", "Stone", st["rings"][0], group="walls")
    w2 = st["shells"][1] + _corbel(TOWER.cs, 3.0, ZTW) + lip_ring(TOWER.cs, 3.0, ZTW) + CO.ledge(TOWER.pts, ZT, LEDGE)
    kit.add("WALLS-2", "Brick", w2, group="walls", render=[("Brick", w2 - bands), ("Buff", w2 ^ bands)])
    rings, _ = CO.level(NAVE.pts, ZE, EAVE, cut=TOWER.solid(grow=1.1, dz0=-2, dz1=2))
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(TOWER.pts, ZT, TOWER_C)
    CO.add_level(kit, rings, "CORNICE-T", "tower")
    fnd = foundation(BLOCKS, 0.0, ZF, style="snecked")
    plinths = union([f.place(box([u - 2.9, -ZF, -0.01], [u + 2.9, 0.0, 5.8])) for f, u in _buttresses()])
    fnd = fnd + (plinths - NAVE.solid(grow=-0.01, dz0=-50, dz1=50))
    kit.add("FOUNDATION", "Rubble", fnd, group="foundation")
    ins_keep = []
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        b = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if op.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P,
                       key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{op.name[:5]}", group="inserts", render=zones)
        ins_keep.append(part.solid)
    # the tower clocks, each glued by its whole back into the plain field left in the brick
    for e in CLOCKS:
        f = TOWER.facades()[e]
        A = f.A.copy()
        A[:, 3] = f.world(f.L / 2, CLOCK_V, 0.0)
        whole, dial, marks = TN.clock_face(CLOCK_D)
        Pp = np.column_stack([np.vstack([A[:, 0], A[:, 1], A[:, 2]]), np.zeros(3)])
        ring = whole - dial - marks
        kit.add(f"CLOCK-{'S' if e == 0 else 'W'}", "Stone", whole.transform(A), P=Pp, key="CLOCK", group="tower",
                render=[("Stone", ring.transform(A)), ("Dial", dial.transform(A)), ("Hands", marks.transform(A))])
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the nave roof: pointed-band slates, a ridge cap, cut round the tower
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((XC, -RAKE), (XC, D_N + RAKE), ZR, S_NAVE, ZW) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW) - tw
    kit.add("ROOF", "Slate", max(roof.decompose(), key=lambda m_: m_.volume()), group="roof")
    # --- the spire, its deck and pinnacles in one piece on the tower top, a cross at the tip
    sp = TN.spire(17.5, 13.6, SP_H).translate([TCX, TCY, ZTW])
    sp = sp - lip_keep(TOWER.cs, 3.0, ZTW)
    kit.add("SPIRE", "Slate", sp, group="roof")
    kit.add("CROSS", "Stone", TN.cross_finial().translate([TCX, TCY, ZTW + 1.6 + SP_H - 0.8]), group="roof")
    FT.crown(kit, "CROSS", "SPIRE")
    # --- steps up to the two doors
    for blk, x, y, wd, nm in ((NAVE, XC, 0.0, 22.0, "STEPS-west"), (TOWER, TCX, TY0, 15.0, "STEPS-tower")):
        e, u = blk.locate(x, y)
        fb = blk.facades()[e]
        A = fb.A.copy()
        A[:, 3] = fb.world(u, -ZF, 1.4)
        kit.add(nm, "Stone", FT.steps(wd, ZF - 0.6, 4).transform(A) - fnd, group="steps")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "brendan")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "brendan.npz"))
    import json
    json.dump({"materials": {k: [h, r, 0.0] for k, (h, r) in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
