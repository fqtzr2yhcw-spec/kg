"""The Hathaway: an original HO-scale (1:87.1) New England saltbox, house 35 of the third batch.

Two storeys in front and one behind under a long catslide roof: Spanish-brown clapboard,
graduated (narrow courses at the foot of each storey, widening as they rise) with a bead on
every butt, on split granite that still shows its drill holes. Small-paned windows, nine over
nine, under drip boards below and tight under the eave above; a six-panel door under a
four-light transom between fluted pilasters, crowned by a broken scroll (swan-neck) pediment
with an urn finial. Between the storeys a mustard frieze of chain links, a putty reed course
and a putty ovolo, running on round the lean-to's eave; at the front eave a mustard frieze of
trees of life, putty dentils and a putty cyma, running across the gable feet. A massive
centre chimney with corner piers and four pots, and a roof of shakes banded bevel and square.

The roof is one part: its section run the length of the house, printed standing on its end.

usage: python3 -m hoarch.buildings.hathaway [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import Facade, box, cs_union, frame, inv34, offset, poly, rect, scallop_rows, slab, union
from hoarch import colonial as C, cornice as CO, openings as O
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Hathaway"
COLORS = {"Spanish": "#6E3B2B", "Putty": "#D8CCAE", "Mustard": "#C29838", "Cedar": "#66625C", "Brick": "#8B4A38",
          "Granite": "#8E8E88", "Windows_Doors": "#D8CCAE"}
RENDER_MAT = {"Spanish": "siding", "Putty": "trim", "Mustard": "accent", "Cedar": "roof", "Brick": "brick2",
              "Granite": "stone2", "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Hathaway)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="chain", role="Mustard"),
    dict(kind="course", h=1.4, b=1.4, orn="reeds", role="Putty"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="ovolo", role="Putty")])
EAVE = dict(pitch=11.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.2, b=1.2, orn="trees", role="Mustard"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Putty", tooth=0.8, gap=0.6),
    dict(kind="crown", h=3.0, b=1.4, P=6.2, orn="cyma", role="Putty")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)
SHAKES = ("bevel", "square")

# ------------------------------------------------------------------ levels and the saltbox section
ZF = 12.0
S1 = ZF + 42.0
ZE = S1 + RJ + 36.0
ZW = round((ZE + HE) / 0.2) * 0.2               # the front block's wall top
ZW1 = S1 - 2.0                                  # the lean-to's wall top
ZE1 = round((ZW1 - CO.band_height(JOINT)) / 0.2) * 0.2
W, DM, D = 168.0, 64.0, 132.0                   # width, the two-storey block's depth, the whole depth
YR = DM / 2                                     # the ridge
DE, BO, RG, T = 7.0, 7.0, 7.0, 2.4              # front eave, back eave, rake, the roof's shell
Z_FE, Z_BE = ZW + 2.0, ZW1 + 2.0                # the eave edges' tops
S = (Z_FE - Z_BE) / (D + BO - 2 * YR - DE)      # one pitch front and back
ZR = Z_FE + S * (YR + DE)
TOP = [(-DE, Z_FE), (YR, ZR), (D + BO, Z_BE)]

MAIN = Block("main", [(0, 0), (W, 0), (W, DM), (0, DM)], ZF, ZW)
LEAN = Block("lean", [(0, DM - 3.0), (W, DM - 3.0), (W, D), (0, D)], ZF, ZW1)
BLOCKS = [MAIN, LEAN]
V1 = 6.0
V2 = S1 + RJ + 4.0 - ZF
XC = W / 2


def _under_top():
    return poly([(-DE, ZW1 - 20.0), TOP[0], TOP[1], TOP[2], (D + BO, ZW1 - 20.0)])


def _hollow():
    inner = _under_top().offset(-T, JoinType.Miter, 4.0)
    return inner ^ cs_union([rect(3.0, ZW, DM - 3.0, 999), rect(DM, ZW1, D - 3.0, 999)])


def _section():
    clip = cs_union([rect(-DE - 1.0, ZW, DM, 999), rect(DM, ZW1, D + BO + 1.0, 999)])
    return (_under_top() ^ clip) - _hollow()


def _gable_cs(y0, y1, z0):
    return _under_top().offset(-T - 0.15, JoinType.Miter, 4.0) ^ rect(y0, z0, y1, 999)


def _gables():
    g = _gable_cs(3.15, DM - 3.15, ZW)
    east = g.translate((0.0, -ZF))                                        # u = y
    west = g.transform(np.array([[-1.0, 0, DM], [0, 1.0, -ZF]]))          # u = DM - y
    return [(MAIN, 1, east), (MAIN, 3, west)]


def _siding(f, b, reg):
    """Graduated clapboard, each storey starting narrow at its foot; nothing in the cornice bands."""
    if b is LEAN:
        reg = reg - rect(-1, ZE1 - LEDGE - 0.6 - ZF, f.L + 1, 999)
        return C.clapboard_graduated(reg, datum=0.0, span=30.0)
    lo = reg ^ rect(-1, -1, f.L + 1, S1 - ZF)
    hi = reg ^ rect(-1, S1 + RJ - ZF, f.L + 1, ZE - LEDGE - 0.6 - ZF)
    gab = reg ^ rect(-1, ZW - ZF + 0.2, f.L + 1, 999)
    return (C.clapboard_graduated(lo, datum=0.0) + C.clapboard_graduated(hi, datum=S1 + RJ - ZF, span=30.0) +
            C.clapboard_graduated(gab, datum=ZW - ZF + 0.2, p0=1.6, p1=1.6))


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    lo = C.window_smallpane(9.6, 20.0)
    up = C.window_smallpane(9.6, 18.0, head="flush")
    att = C.window_smallpane(6.4, 7.6, lites=(2, 2), rows=(1, 1), head="flush")
    for x in (22.0, 52.0, W - 52.0, W - 22.0):
        add(MAIN, x, 0.0, V1, lo, f"S{x:.0f}-1")
    add(MAIN, XC, 0.0, 0.4, C.door_swanneck(11.0, 30.0), "front-door", "door")
    for x in (22.0, 52.0, XC, W - 52.0, W - 22.0):
        add(MAIN, x, 0.0, V2, up, f"S{x:.0f}-2")
    for x_, tag in ((0.0, "W"), (W, "E")):
        for y in (18.0, 46.0):
            add(MAIN, x_, y, V1, lo, f"{tag}{y:.0f}-1")
            add(MAIN, x_, y, V2, up, f"{tag}{y:.0f}-2")
        add(MAIN, x_, YR, ZW - ZF + 3.0, att, f"{tag}-attic")
        add(LEAN, x_, 100.0, V1, lo, f"lean{tag}-1")
    for x in (26.0, 62.0, W - 26.0):
        add(LEAN, x, D, V1, lo, f"N{x:.0f}-1")
    add(LEAN, 100.0, D, 0.4, C.door_swanneck(10.0, 25.0, pediment=False), "back-door", "door")
    return L


OPENINGS = _openings()


def _face_tex(A, B, x0, x1, pitch=1.6, wtab=2.3, d=0.42):
    """Shakes on the roof face from A (lower) to B (upper) in (y, z), from x0 to x1."""
    A, B = np.asarray(A, float), np.asarray(B, float)
    v = B - A
    L = float(np.linalg.norm(v))
    v /= L
    ex = np.array([1.0, 0, 0])
    n = np.cross(ex, [0.0, v[0], v[1]])
    if n[2] < 0:
        ex, n = -ex, -n
    ua, ub = (x0, x1) if ex[0] > 0 else (-x1, -x0)
    tex = scallop_rows(rect(ua + 0.3, 0.0, ub - 0.3, L - 0.2), pitch, wtab, d=d, shape=SHAKES, datum=0.0)
    return tex.translate([0, 0, -0.03]).transform(frame([0.0, A[0], A[1]], list(ex), [0.0, v[0], v[1]], list(n)))


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    lean_only = rect(-500, DM + 0.5, 500, 500)
    undress = [slab(offset(base, 9.0), ZE - LEDGE - 0.6, ZW + 0.2),
               slab(offset(LEAN.cs, 9.0) ^ lean_only, ZE1 - LEDGE - 0.6, ZW1 + 0.2),
               box([-10.0, DM - 0.5, ZW1 - 1.0], [W + 10.0, DM + 2.0, 999.0])]            # inside the lean-to's roof
    allcs = cs_union([b_.cs for b_ in BLOCKS])
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_siding, gables=_gables(),
                        clear=[lip_keep(allcs, 3.0, ZF, 1.2)], prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None,
                        water_table=False, undress=undress, partitions=[((XC - 14.0, 3.0), (XC - 14.0, DM - 3.0), 2.0, ZF, ZW)])
    main_keep = MAIN.solid(grow=0.8, dz0=-2, dz1=400)
    lean_ledge = CO.ledge(LEAN.pts, ZE1, LEDGE) - main_keep
    lean_lip = (_corbel(LEAN.cs, 3.0, ZW1) + lip_ring(LEAN.cs, 3.0, ZW1)) - MAIN.solid(grow=0.3, dz0=-2, dz1=400) - \
        box([-1, -1, ZW1 - 1], [5.0, D + 1, ZW1 + 5]) - box([W - 5.0, -1, ZW1 - 1], [W + 1, D + 1, ZW1 + 5])
    kit.add("WALLS-1", "Spanish", st["shells"][0] + lean_ledge + lean_lip, group="walls")
    kit.add("JOINT", "Spanish", st["rings"][0] - box([-10, DM + 0.02, S1 - 1], [W + 10, DM + 10, S1 + RJ + 1]), group="walls")
    eave_path = max(base.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    no_lip = union([box([W - 5.0, -1, ZW - 1], [W + 1, DM + 1, ZW + 5]), box([-1, -1, ZW - 1], [5.0, DM + 1, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    back_cut = box([-10, DM - 0.5, -10], [W + 10, DM + 20, 400])
    kit.add("WALLS-2", "Spanish", st["shells"][1] + lip + (CO.ledge(eave_path, ZE, LEDGE) - back_cut), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=back_cut)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZE, EAVE, cut=back_cut)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(LEAN.pts, ZE1, JOINT, cut=MAIN.solid(grow=0.7, dz0=-2, dz1=2))
    CO.add_level(kit, rings, "CORNICE-L", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="splitgranite")
    kit.add("FOUNDATION", "Granite", fnd, group="foundation")
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                group="inserts", render=zones)
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the saltbox roof: its section run the length of the house, shakes on both faces
    Ar = np.array([[0, 0, 1.0, -RG], [1.0, 0, 0, 0], [0, 1.0, 0, 0]])
    Lr = W + 2 * RG
    roof = M.extrude(_section(), Lr).transform(Ar)
    env = M.extrude(_under_top() ^ cs_union([rect(-DE - 1.0, ZW, DM, 999), rect(DM, ZW1, D + BO + 1.0, 999)]), Lr).transform(Ar)
    roof = roof + _face_tex(TOP[0], TOP[1], -RG, W + RG) + _face_tex(TOP[2], TOP[1], -RG, W + RG)
    cap = poly([(YR - 1.8, ZR - 1.8 * S + 0.3), (YR, ZR + 0.9), (YR + 1.8, ZR - 1.8 * S + 0.3), (YR, ZR - 0.6)])
    roof = roof + M.extrude(cap, Lr).transform(Ar)
    roof = roof - lip_keep(base, 3.0, ZW) - lip_keep(LEAN.cs, 3.0, ZW1)
    CW, CD = 18.0, 12.0
    z_at = ZR - S * CD / 2
    cz0 = round((z_at - 3.2) / 0.2) * 0.2
    seat = box([XC - CW / 2 - 1.2, YR - CD / 2 - 1.2, ZW], [XC + CW / 2 + 1.2, YR + CD / 2 + 1.2, cz0]) ^ env
    pocket = box([XC - CW / 2 - 0.5, YR - CD / 2 - 0.5, cz0], [XC + CW / 2 + 0.5, YR + CD / 2 + 0.5, ZR + 40])
    roof = roof + seat - pocket
    kit.add("ROOF", "Cedar", roof, P=inv34(Ar), group="roof")
    kit.add("CHIMNEY", "Brick", C.chimney_massive(CW, CD, ZR + 11.0 - cz0).translate([XC, YR, cz0]), group="roof")
    # the lean-to's gable ends: clapboarded walls under the catslide, on the lean-to's end walls
    gcs = _gable_cs(DM + 0.15, D - 3.15, ZW1)
    for tag, x0, f in (("W", 0.0, Facade((0.0, D), (0.0, DM), 0.0)), ("E", W - 3.0, Facade((W, DM), (W, D), 0.0))):
        wall = M.extrude(gcs, 3.0).transform(np.array([[0, 0, 1.0, x0], [1.0, 0, 0, 0], [0, 1.0, 0, 0]]))
        reg = gcs.transform(np.array([[-1.0, 0, D], [0, 1.0, 0]])) if tag == "W" else gcs.transform(np.array([[1.0, 0, -DM], [0, 1.0, 0]]))
        tex = f.place(C.clapboard_graduated(reg.offset(-0.3, JoinType.Miter, 4.0), datum=ZW1 + 0.2, p0=1.6, p1=1.6)
                      .translate([0, 0, -0.02]))
        kit.add(f"LEAN-gable-{tag}", "Spanish", wall + tex - roof, group="walls")
    print("roof", round(time.time() - t0, 1))

    # --- granite steps at the doors
    for name, blk, x, y, wd in (("STOOP-front", MAIN, XC, 0.0, 24.0), ("STOOP-back", LEAN, 100.0, D, 16.0)):
        e, u = blk.locate(x, y)
        f = blk.facades()[e]
        A = f.A.copy()
        A[:, 3] = f.world(u, -ZF, 0.0)
        steps = union([box([-wd / 2, 0.0, 0.4], [wd / 2, ZF - 0.4, 5.2]),
                       box([-wd / 2 - 2.0, 0.0, 5.0], [wd / 2 + 2.0, round(ZF / 2 / 0.2) * 0.2, 9.6])])
        kit.add(name, "Granite", steps.transform(A) - fnd, group="stoop")
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "hathaway")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "hathaway.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
