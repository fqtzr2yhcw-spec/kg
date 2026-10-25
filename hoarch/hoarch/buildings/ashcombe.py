"""The Ashcombe: an original HO-scale (1:87.1) Tudor Revival house, house 54 of the fifth batch
(the Craftsman era, 1900-1930).

Two storeys under a steep side-gabled roof of Cotswold stone slates, with a two-storey front
gable standing forward on the left. The ground storey is Tudor brick with a diaper of darker
over-burnt headers; the upper storey and the gables are half-timbered over smooth render,
close-studded below the rail, lozenges and curved braces above, king posts, struts and
quatrefoils in the gables, under cusped bargeboards with pendants. Downstairs the windows are
stone-mullioned with transoms, leaded in diamond quarries under square labels with carved
stops; upstairs oak frames with arched head beams and bracketed sills; small arched lights in
the gables. The front door is oak under a four-centred stone arch, with fleur strap hinges and
a speaking grille. Beside it a great diapered chimney steps in twice and ends in two twisted
star-shaped shafts. The storeys are divided by a jetty cornice of portcullis badges and
trailing vines over flushwork chequer and curved jetty braces; at the eaves Tudor flowers over
ballflowers.

usage: python3 -m hoarch.buildings.ashcombe [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, cs_union, inv34, offset, rect, slab, union
from hoarch import craftsman2 as CR2, cornice as CO, features as FT, gables as G
from hoarch import openings as O, roof as R
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Ashcombe"
COLORS = {"Brick": "#8E3B2E", "Stucco": "#E9E0CC", "Oak": "#3B2A1E", "Stone": "#C9BFA8", "Slate": "#5A5E57",
          "Clinker": "#4F2620", "Windows_Doors": "#3B2A1E"}
RENDER_MAT = {"Brick": "brick", "Stucco": "siding", "Oak": "wood", "Stone": "stone", "Slate": "roof", "Clinker": "accent",
              "Windows_Doors": "wood", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Ashcombe)
LEDGE = 1.4
JOINT = dict(pitch=15.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="portcullis", role="Oak"),
    dict(kind="course", h=1.6, b=1.4, orn="chequer", role="Stone"),
    dict(kind="bed", h=2.2, b=1.4, P=4.6, role="Oak", brackets=dict(style="jettybrace", t=1.2, reach=0.5)),
    dict(kind="crown", h=2.2, b=1.4, P=5.0, orn="cyma", role="Oak")])
EAVE = dict(pitch=13.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.0, b=1.2, orn="tudorflower", role="Oak"),
    dict(kind="course", h=1.6, b=1.4, orn="ballflower", role="Stone"),
    dict(kind="crown", h=2.6, b=1.4, P=5.2, orn="ovolo", role="Oak")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 9.0
S1 = ZF + 38.0
ZU = S1 + RJ
ZE = ZU + 30.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 5.0, 5.4, 1.8
S = 1.0
W, D = 156.0, 92.0
XC, YC = W / 2, D / 2
FX0, FX1, FY0 = 14.0, 66.0, -16.0               # the front gable
FXC = (FX0 + FX1) / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
FG = Block("gable", [(FX0, FY0), (FX1, FY0), (FX1, 3.0), (FX0, 3.0)], ZF, ZW)
BLOCKS = [MAIN, FG]
OUT_PTS = [(0.0, 0.0), (FX0, 0.0), (FX0, FY0), (FX1, FY0), (FX1, 0.0), (W, 0.0), (W, D), (0.0, D)]
V1 = 7.0
V2 = ZU - ZF + 4.0
CHX = 104.0                                     # the front chimney
ZC1 = S1 - 3.0                                  # its first weathering (22 -> 19 wide)
ZC2 = ZE - LEDGE - 3.4                          # its second (19 -> 14 wide)
ZONES = dict(diaper=[], timber=[])


def _chim_keep(y1=0.2):
    """The front chimney's room, level by level (for cutting the walls' dressing, the
    cornices, the foundation and the roof round it)."""
    return union([box([CHX - 12.2, -12.0, -1.0], [CHX + 12.2, y1, 7.6]),
                  box([CHX - 11.9, -12.0, 7.5], [CHX + 11.9, y1, ZC1 + 2.6]),
                  box([CHX - 10.4, -12.0, ZC1 + 2.5], [CHX + 10.4, y1, ZC2 + 2.2]),
                  box([CHX - 7.9, -12.0, ZC2 + 2.1], [CHX + 7.9, y1, 400.0])])


def _skin(f, b, reg):
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    if b is MAIN and f.n[1] < -0.5:
        z0 = b.z0
        reg = reg - cs_union([rect(CHX - 12.4, -ZF - 1, CHX + 12.4, ZC1 + 2.6 - z0), rect(CHX - 10.6, ZC1 + 2.5 - z0, CHX + 10.6, ZC2 + 2.2 - z0),
                              rect(CHX - 8.1, ZC2 + 2.1 - z0, CHX + 8.1, 999)])
    lo = reg ^ rect(-1, -50, f.L + 1, S1 - b.z0)
    hi = reg - rect(-1, -50, f.L + 1, ZU - b.z0)
    out = M()
    if not lo.is_empty():
        sk, dz = CR2.brick_diaper(lo, parts=True)
        out = out + sk
        ZONES["diaper"].append(f.place(dz.translate([0, 0, -0.02])))
    if not hi.is_empty():
        apex = hi.bounds()[3]
        vg = ZW - b.z0 if apex > ZW - b.z0 + 6.0 else None
        sk, tz = CR2.halftimber_tudor(hi, f.L, ZU - b.z0, ZE - LEDGE - 0.6 - b.z0, vg, apex, parts=True)
        out = out + sk
        ZONES["timber"].append(f.place(tz.translate([0, 0, -0.02])))
    return out


def _gable_specs():
    return [dict(p0=(0.0, D), p1=(0.0, 0.0), slope=S, blk=MAIN, edge=3),
            dict(p0=(W, 0.0), p1=(W, D), slope=S, blk=MAIN, edge=1),
            dict(p0=(FX0, FY0), p1=(FX1, FY0), slope=S, blk=FG, edge=0)]


def _roof_pieces():
    r = RAKE - D_EAVE
    return [([(-r, 0.0), (W + r, 0.0), (W + r, D), (-r, D)], [0, 2], S),
            ([(FX0, FY0 - r), (FX1, FY0 - r), (FX1, YC), (FX0, YC)], [1, 3], S)]


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    g4 = CR2.window_stonemullion(34.0, 20.0, n=4)
    g3 = CR2.window_stonemullion(26.0, 20.0, n=3)
    g2 = CR2.window_stonemullion(17.0, 20.0, n=2)
    u3 = CR2.window_oakframe(26.0, 17.0, n=3)
    u2 = CR2.window_oakframe(17.0, 17.0, n=2)
    at = CR2.window_tudorlights(12.0, 10.0, n=2)
    atf = CR2.window_tudorlights(10.0, 9.0, n=2)
    add(FG, FXC, FY0, V1, g4, "FG-1")
    add(FG, FXC, FY0, V2, u3, "FG-2")
    add(FG, FXC, FY0, Z_EAVE + 3.0 - ZF, atf, "FG-attic")
    add(MAIN, 80.0, 0.0, 0.4, CR2.door_tudor(11.0, 24.0), "front-door", "door")
    add(MAIN, 80.0, 0.0, V2, u2, "S80-2")
    add(MAIN, 136.0, 0.0, V1, g3, "S136-1")
    add(MAIN, 136.0, 0.0, V2, u3, "S136-2")
    for x_, tag in ((0.0, "W"), (W, "E")):
        add(MAIN, x_, YC, V1, g3, f"{tag}-1")
        add(MAIN, x_, YC, V2, u2 if tag == "W" else u3, f"{tag}-2")
        add(MAIN, x_, YC, Z_EAVE + 7.0 - ZF, at, f"{tag}-attic")
    add(MAIN, 40.0, D, V1, g3, "N40-1")
    add(MAIN, 40.0, D, V2, u3, "N40-2")
    add(MAIN, 84.0, D, V1, g2, "N84-1")
    add(MAIN, 84.0, D, V2, u2, "N84-2")
    add(MAIN, 122.0, D, 0.4, CR2.door_ledged(9.0, 21.0), "back-door", "door")
    add(MAIN, 122.0, D, V2, u2, "N122-2")
    return L


OPENINGS = _openings()
STONE_FRAMED = ("DOOR-front-door",) + tuple(f"WIN-{n}" for n in ("FG-1", "S136-1", "W-1", "E-1", "N40-1", "N84-1"))


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    ZONES["diaper"].clear()
    ZONES["timber"].clear()
    t0 = time.time()
    base = MAIN.cs + FG.cs
    specs = _gable_specs()
    rf = G.gabled_roof(_roof_pieces(), Z_EAVE, D_EAVE, specs, texture="stoneslate", tex_kw=dict(pitch=2.2, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    gables = [(g["blk"], g["edge"], wl["cs"].translate((0.0, Z_EAVE - ZF))) for g, wl in zip(specs, rf["walls"])]
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    clear = [lip_keep(base, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=gables, clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((XC + 10.0, 3.0), (XC + 10.0, D - 3.0), 2.0, ZF, ZW)])
    ck = _chim_keep()
    ck_out = _chim_keep(0.0)
    w1 = st["shells"][0] - ck_out
    dz = union(ZONES["diaper"])
    kit.add("WALLS-1", "Brick", w1, group="walls", render=[("Brick", w1 - dz), ("Clinker", w1 ^ dz)])
    kit.add("JOINT", "Oak", st["rings"][0] - ck_out, group="walls")
    no_lip = union([box([-1, -1, ZW - 1], [5.0, D + 1, ZW + 5]), box([W - 5.0, -1, ZW - 1], [W + 1, D + 1, ZW + 5]),
                    box([FX0 - 1, FY0 - 1, ZW - 1], [FX1 + 1, FY0 + 5.0, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    w2 = st["shells"][1] + lip + CO.ledge(OUT_PTS, ZE, LEDGE) - ck_out
    tz = union(ZONES["timber"])
    kit.add("WALLS-2", "Stucco", w2, group="walls", render=[("Stucco", w2 - tz), ("Oak", w2 ^ tz)])
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=ck)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(OUT_PTS, ZE, EAVE, cut=ck)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="tudorstone") - ck
    kit.add("FOUNDATION", "Stone", fnd, group="foundation")
    ins_keep = []
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        b = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        name = f"{key}-{op.name}"
        stone = name in STONE_FRAMED
        world, P, zones = O.place(sp, A, "Stone" if stone else "Oak", "Door" if op.kind == "door" else "Oak", "Glass")
        part = kit.add(name, "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{op.v0 > 20}-{stone}",
                       group="inserts", render=zones, change=(O.PLUG, "Stone") if stone else None)
        ins_keep.append(part.solid)
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the roof: stone slates, ridge caps on both ridges, the chimney's notch in the eave
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S * (D / 2 + D_EAVE)
    zrf = Z_EAVE + S * ((FX1 - FX0) / 2 + D_EAVE)
    yj = (zrf - Z_EAVE) / S - D_EAVE
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((-RAKE, YC), (W + RAKE, YC), zr, S, ZW) - walls_env)
    roof = roof + (G.ridge_cap((FXC, FY0 - RAKE), (FXC, yj + 1.0), zrf, S, ZW) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW) - ck
    kit.add("ROOF", "Slate", roof, group="roof")
    chim = CR2.chimney_tudor(zr + 2.0, ZC1, ZC2).transform(np.array([[-1.0, 0, 0, CHX], [0, -1.0, 0, 0], [0, 0, 1.0, 0]]))
    kit.add("CHIMNEY", "Stone", chim, group="roof", change=(7.0, "Brick"),
            render=[("Stone", chim ^ box([-1e3, -1e3, -1], [1e3, 1e3, 7.0])), ("Brick", chim - box([-1e3, -1e3, -1], [1e3, 1e3, 7.0]))])
    for k, (g, wl) in enumerate(zip(specs, rf["walls"])):
        bb = CR2.barge_cusped(wl["L"], wl["slope"], D_EAVE, skin=SKIN, width=3.4 if wl["L"] < 60 else 4.0)
        fw = wl["facade"]
        A = fw.A.copy()
        A[:, 3] = fw.world(0.0, 0.0, RAKE)
        bw = bb.transform(A) - roof
        bw = max(bw.decompose(), key=lambda m_: m_.volume())
        kit.add(f"BARGE-{k}", "Oak", bw, P=inv34(A), key=f"BARGE-{wl['L']:.0f}", group="gable")
    print("roof", round(time.time() - t0, 1))

    # --- steps at the doors
    for (x, y, wd, tag) in ((80.0, 0.0, 18.0, "front"), (122.0, D, 14.0, "back")):
        e, u = MAIN.locate(x, y)
        f = MAIN.facades()[e]
        A = f.A.copy()
        A[:, 3] = f.world(u, -ZF, 1.4)
        kit.add(f"STOOP-{tag}", "Stone", FT.steps(wd, ZF - 0.6, 3).transform(A) - fnd, group="steps")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "ashcombe")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "ashcombe.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
