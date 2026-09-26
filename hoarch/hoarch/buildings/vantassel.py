"""The Van Tassel: an original HO-scale (1:87.1) Dutch Colonial, house 34 of the third batch.

A storey and a half of red Jersey sandstone, coursed ashlar with every block's face tooled in
furrows, on a base of field boulders under a sandstone sill. A gambrel roof of chisel-cut
cedar shakes (every fourth course swallowtailed) whose front slope sweeps out in a Dutch kick
over a porch the width of the house, carried on six round posts; the gable ends are
double-coursed white shingles with a pair of quarter-round lights either side of the flue. A
Dutch door (a panelled lower leaf, an upper leaf glazed with bull's-eyes, a bull's-eye
transom) and six-over-six windows under ogee 'bell' head boards, with Delft-blue
board-and-batten shutters cut with crescent moons. At the eave a frieze of Delft tiles, a
cream pellet course and a cream cove, running across the gable feet. A long shed dormer on the
back slope, and a stack at each end: sandstone to the roof, brick above it under a corbelled
cap.

The roof is one part: its cross-section run the length of the house, printed standing on its
end so the kick, the eaves and the knuckles need no support.

usage: python3 -m hoarch.buildings.vantassel [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import Facade, box, compose, frame, inv34, poly, rect, scallop_rows, slab, union
from hoarch import colonial as C, cornice as CO, features as FT, openings as O
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Van Tassel"
COLORS = {"Sandstone": "#9A5B45", "Shingle": "#E6DFCC", "Cream": "#EFE6D0", "Cedar": "#4F4640", "Delft": "#3C5D93",
          "Boulder": "#7C766C", "PorchDeck": "#EFE6D0", "Windows_Doors": "#EFE6D0"}
RENDER_MAT = {"Sandstone": "stone", "Shingle": "siding", "Cream": "trim", "Cedar": "roof", "Delft": "shutter",
              "Boulder": "stone2", "PorchDeck": "trim", "Planks": "planks", "Windows_Doors": "trim", "Door": "door",
              "Glass": "glass"}

# ------------------------------------------------------------------ the cornice (unique to the Van Tassel)
LEDGE = 1.4
EAVE = dict(pitch=11.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="delft", role="Delft"),
    dict(kind="course", h=1.4, b=1.4, orn="pellets", role="Cream"),
    dict(kind="crown", h=2.6, b=1.4, P=6.4, orn="cavetto", role="Cream")])
HE = CO.band_height(EAVE)
SHAKES = ("chisel", "chisel", "chisel", "swallow")

# ------------------------------------------------------------------ levels and the roof's section (y, z)
ZF = 10.0
ZE = ZF + 40.0
ZW = round((ZE + HE) / 0.2) * 0.2
W, D = 190.0, 96.0
XC = W / 2
T = 2.4                                        # the roof's shell
FL, BO, RG = 24.0, 8.5, 8.0                    # the kick over the porch, the back eave, the rake
S_U, S_K, S_LO, S_UP, KY = 0.38, 0.42, 1.75, 0.55, 22.0
Y_SOFF = -7.5                                  # the soffit runs level out to here, over the cornice
Z_KB = ZW - (FL + Y_SOFF) * S_U                # the kick's underside at the porch edge
Z_KT = Z_KB + 2.2                              # ... and its top
ZEF = Z_KT + FL * S_K                          # the roof's top at the wall line
ZK = ZEF + S_LO * KY                             # the knuckles
ZR = ZK + S_UP * (D / 2 - KY)                    # the ridge
Z_BK = ZEF - BO * S_K                          # the back eave's top
TOP = [(-FL, Z_KT), (0.0, ZEF), (KY, ZK), (D / 2, ZR), (D - KY, ZK), (D, ZEF), (D + BO, Z_BK)]

MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
V1 = 8.0
DOOR_W, DOOR_H = 12.0, 30.0
POST_Y = -FL + 3.2
BEAM_Z0 = round((Z_KB + 0.2) / 0.2) * 0.2 - 3.4


def _roof_frame():
    """Section (a = y, b = z) run along c -> world (x = c - RG, y = a, z = b)."""
    return np.array([[0, 0, 1.0, -RG], [1.0, 0, 0, 0], [0, 1.0, 0, 0]])


def _outer_cs():
    return poly([(-FL, Z_KB)] + TOP + [(D + BO, ZW), (Y_SOFF, ZW)])


def _hollow_cs():
    top = poly([(0.0, ZW - 5.0)] + TOP[1:6] + [(D, ZW - 5.0)])
    return top.offset(-T, JoinType.Miter, 4.0) ^ rect(3.0, ZW - 1.0, D - 3.0, 999)


def _gable_cs():
    """The gable wall under the roof, in (y, z): from the wall top up to the roof's underside."""
    top = poly([(0.0, ZW - 5.0)] + TOP[1:6] + [(D, ZW - 5.0)])
    return top.offset(-T - 0.15, JoinType.Miter, 4.0) ^ rect(3.15, ZW, D - 3.15, 999)


def _gables():
    g = _gable_cs()
    east = g.translate((0.0, -ZF))                                        # u = y
    west = g.transform(np.array([[-1.0, 0, D], [0, 1.0, -ZF]]))           # u = D - y
    return [(MAIN, 1, east), (MAIN, 3, west)]


def _siding(f, b, reg):
    """Tooled sandstone to the eave band, double-coursed shingles in the gables above it."""
    lo = reg ^ rect(-1, -1, f.L + 1, ZE - LEDGE - 0.6 - ZF)
    hi = reg ^ rect(-1, ZW - ZF + 0.2, f.L + 1, 999)
    out = C.tooled_ashlar(lo, datum=0.0, seed=int(f.p0[0] * 3 + f.p0[1] * 7) % 97)
    if not hi.is_empty():
        out = out + C.shingles_doubled(hi, datum=ZW - ZF + 0.2)
    return out


def _openings():
    L, SH = [], []

    def add(x, y, v0, sp, name, kind="window", shutters=False):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))
        if shutters:
            SH.append(name)

    lo = C.window_dutch(10.4, 22.0)
    door = C.door_dutch(DOOR_W, DOOR_H)
    for x in (22.0, 58.0, W - 58.0, W - 22.0):
        add(x, 0.0, V1, lo, f"S{x:.0f}", shutters=True)
        add(x, D, V1, lo, f"N{x:.0f}", shutters=True)
    add(XC, 0.0, 0.4, door, "front-door", "door")
    add(XC, D, 0.4, C.door_dutch(11.0, 28.0), "back-door", "door")
    for x_, tag in ((0.0, "W"), (W, "E")):
        for y in (28.0, D - 28.0):
            add(x_, y, V1, lo, f"{tag}{y:.0f}", shutters=True)
    vq = ZW - ZF + 9.0
    for x_, tag in ((0.0, "W"), (W, "E")):
        for dy, left in ((-10.0, True), (10.0, False)):
            y = D / 2 + dy
            # on the west face u runs from north to south, so the lights swap sides
            lft = left if tag == "E" else not left
            add(x_, y, vq, C.window_quadrant(8.0, lft), f"{tag}{y:.0f}-quad")
    return L, SH


OPENINGS, SHUTTERED = _openings()


def _face_tex(A, B, x0, x1, shape=SHAKES, pitch=1.6, wtab=2.3, d=0.42):
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
    tex = scallop_rows(rect(ua + 0.3, 0.0, ub - 0.3, L - 0.2), pitch, wtab, d=d, shape=shape, datum=0.0)
    return tex.translate([0, 0, -0.03]).transform(frame([0.0, A[0], A[1]], list(ex), [0.0, v[0], v[1]], list(n)))


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    undress = [slab(base.offset(9.0, JoinType.Miter, 4.0), ZE - LEDGE - 0.6, ZW + 0.2)]
    walls = wall_shell(BLOCKS, OPENINGS, t=3.0, belt=None, corners="none", water_table=False, siding=_siding,
                       gables=_gables(), undress=undress, partitions=[((XC - 22.0, 3.0), (XC - 22.0, D - 3.0), 2.0, ZF, ZW)])
    walls = walls - lip_keep(base, 3.0, ZF, 1.2)
    no_lip = union([box([W - 5.0, -1, ZW - 1], [W + 1, D + 1, ZW + 5]), box([-1, -1, ZW - 1], [5.0, D + 1, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    eave_path = max(base.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    walls = walls + lip + CO.ledge(eave_path, ZE, LEDGE)
    below = box([-50, -50, -1], [W + 50, D + 50, ZW])
    kit.add("WALLS", "Sandstone", walls, group="walls", change=(round((ZW - ZF) / 0.2) * 0.2, "Shingle"),
            render=[("Sandstone", walls ^ below), ("Shingle", walls - below)])
    rings, _ = CO.level(eave_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="boulder")
    kit.add("FOUNDATION", "Boulder", fnd, group="foundation")
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}" + (f"-{o.name}" if "quad" in o.name else ""),
                group="inserts", render=zones)
        if o.name in SHUTTERED:
            w_op, h_op = b[2] - b[0], b[3] - b[1]
            left, right = C.shutters_pair(w_op, h_op, casing=1.2, gap=0.9, make=C.shutter_crescent)
            for side, m in (("L", left), ("R", right)):
                kit.add(f"SHUTTER-{o.name}-{side}", "Delft", m.translate([0, 0, 0.42]).transform(A), P=inv34(A),
                        key=f"SHUTTER-{h_op:.1f}", group="shutters")
    print("walls + cornice + inserts", round(time.time() - t0, 1))

    # --- the roof: the section run the length of the house, shakes on every face
    Ar = _roof_frame()
    Lr = W + 2 * RG
    section = _outer_cs() - _hollow_cs()
    roof = M.extrude(section, Lr).transform(Ar)
    collar = rect(3.0, ZK - T - 3.0, D - 3.0, ZK - T - 1.6) ^ _hollow_cs().offset(0.05, JoinType.Miter, 4.0)
    roof = roof + M.extrude(collar, W - 6.4).transform(Ar).translate([RG + 3.2, 0, 0])
    env = M.extrude(_outer_cs(), Lr).transform(Ar)
    faces = [(TOP[0], TOP[1]), (TOP[1], TOP[2]), (TOP[2], TOP[3]), (TOP[4], TOP[3]), (TOP[5], TOP[4]), (TOP[6], TOP[5])]
    tex = union([_face_tex(a, b_, -RG, W + RG) for a, b_ in faces])
    cap = poly([(D / 2 - 1.8, ZR - 1.8 * S_UP + 0.3), (D / 2, ZR + 0.9), (D / 2 + 1.8, ZR - 1.8 * S_UP + 0.3), (D / 2, ZR - 0.6)])
    roof = roof + tex + M.extrude(cap, Lr).transform(Ar)
    fascia = rect(-FL - 0.6, Z_KB - 0.6, -FL + 0.2, Z_KT + 0.3)
    roof = roof + M.extrude(fascia, Lr).transform(Ar)
    roof = roof - lip_keep(base, 3.0, ZW)
    # the two stacks, each in a pocket through the upper slopes, on a seat on the collar
    CW, CD = 9.0, 13.0
    z_at = ZR - S_UP * (CD / 2)
    cz0 = round((z_at - 3.0) / 0.2) * 0.2
    stacks = []
    for cx in (11.0, W - 11.0):
        seat = box([cx - CW / 2 - 1.2, D / 2 - CD / 2 - 1.2, ZK - T - 1.61], [cx + CW / 2 + 1.2, D / 2 + CD / 2 + 1.2, cz0]) ^ env
        pocket = box([cx - CW / 2 - 0.4, D / 2 - CD / 2 - 0.4, cz0], [cx + CW / 2 + 0.4, D / 2 + CD / 2 + 0.4, ZR + 40])
        roof = roof + seat - pocket
        stacks.append(C.chimney_stonebrick(CW, CD, ZR + 10.0 - cz0, stone_h=ZR + 1.4 - cz0, seed=int(cx)).translate([cx, D / 2, cz0]))
    # the shed dormer on the back slope
    DL, DH = 84.0, 18.0
    y_face = D - 5.0
    zfeet = round((ZEF + S_LO * (D - y_face) - 1.0) / 0.2) * 0.2
    ddep = y_face - (D - KY)
    dslope = (ZK - T - (zfeet + DH) - 0.6) / ddep
    dbody, dcore, dside = C.dormer_shed(DL, DH, ddep, dslope, n_win=4, lw=7.0, lh=8.0)
    Ad = np.array([[-1.0, 0, 0, XC], [0, 0, 1.0, y_face], [0, 1.0, 0, zfeet]])
    dkeep = M.extrude(dside.offset(0.3, JoinType.Miter, 4.0), DL + 0.6).transform(
        np.array([[0, 0, 1.0, -DL / 2 - 0.3], [0, 1.0, 0, 0], [1.0, 0, 0, 0]])).transform(Ad)
    dpocket = dkeep ^ box([-500, -500, zfeet], [500, 500, 999])
    plates = union([box([XC - DL / 2 - 0.3, y_face - 1.6, ZW], [XC + DL / 2 + 0.3, y_face - 0.3, zfeet]),
                    box([XC - DL / 2 - 1.2, D - KY, ZW], [XC - DL / 2 + 0.3, y_face, zfeet + 0.01]),
                    box([XC + DL / 2 - 0.3, D - KY, ZW], [XC + DL / 2 + 1.2, y_face, zfeet + 0.01])]) ^ env
    roof = roof - dpocket + (plates - dpocket - lip_keep(base, 3.0, ZW))
    kit.add("ROOF", "Cedar", roof, P=inv34(Ar), group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Sandstone", s_, key="CHIMNEY", group="roof")
    kit.add("DORMER", "Cream", dbody.transform(Ad), group="roof")
    kit.add("DORMER-core", "Cedar", dcore.transform(Ad), group="roof")
    # its shed roof: a slab over the dormer's sloping top, shakes on it, printed lying on its underside
    th = 1.4
    slab_cs = poly([(1.0, DH), (-ddep - 4.0, DH + (ddep + 4.0) * dslope), (-ddep - 4.0, DH + (ddep + 4.0) * dslope + th),
                    (1.0, DH + th)])                                           # (w, v)
    droof = M.extrude(slab_cs, DL + 2.4).transform(np.array([[0, 0, 1.0, -DL / 2 - 1.2], [0, 1.0, 0, 0], [1.0, 0, 0, 0]]))
    nn = math.hypot(1.0, dslope)
    Rl = np.array([[1.0, 0, 0, 0], [0, dslope / nn, -1.0 / nn, 0], [0, 1.0 / nn, dslope / nn, 0]])   # the slab's normal -> up
    # shakes on its top face: from the front edge (w = 1, v = DH + th) up the slope
    a_ = np.array([DH + th, 1.0])
    ttex = scallop_rows(rect(-DL / 2 - 0.9, 0.0, DL / 2 + 0.9, (ddep + 5.0) * nn - 0.3), 1.6, 2.3, d=0.42, shape=SHAKES)
    tdir = np.array([0.0, dslope, -1.0]) / nn                                   # (u, v, w): up the slab, backward
    tnorm = np.array([0.0, 1.0, dslope]) / nn
    droof = droof + ttex.translate([0, 0, -0.03]).transform(frame([0.0, a_[0], a_[1]], [1.0, 0, 0], list(tdir), list(tnorm)))
    droof = droof.transform(Ad) - env.translate([0, 0, 0.0]) - dbody.transform(Ad) - roof
    droof = max(droof.decompose(), key=lambda m_: m_.volume())
    kit.add("DORMER-roof", "Cedar", droof, P=compose(Rl, inv34(Ad)), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the porch under the kick: a boulder-faced base, a planked deck, six posts, a beam
    pb = box([-0.5, -FL + 1.0, 0.0], [W + 0.5, 0.02, ZF - 2.2])
    for p0, p1 in (((-0.5, -FL + 1.0), (W + 0.5, -FL + 1.0)), ((W + 0.5, -FL + 1.0), (W + 0.5, 0.0)), ((-0.5, 0.0), (-0.5, -FL + 1.0))):
        f = Facade(p0, p1, 0.0)
        pb = pb + f.place(C.foundation_boulder(rect(0.0, 0.0, f.L, ZF - 2.2), seed=int(p0[0])).translate([0, 0, -0.02]))
    kit.add("PORCH-base", "Boulder", pb - fnd, group="porch")
    ppts = [(-0.5, -1.7), (-0.5, -FL + 1.0), (W + 0.5, -FL + 1.0), (W + 0.5, -1.7)]
    planks = FT.porch_planks(ppts, [0, 1, 2], H=ZF, pitch=1.6, crack=0.25, border=1.4, along=(0.0, -1.0))
    xs = [4.0 + (W - 8.0) * k / 5 for k in range(6)]
    # each post's plinth drops 1.2 mm into a recess in the deck and a square peg on its cap
    # 1.2 mm up into a pocket in the beam: both ends glued round their sides
    seats = [FT.column_seats(x, POST_Y, ZF, BEAM_Z0, ("square", 1.9), head=("square", 0.8), dhead=1.2) for x in xs]
    deck = (slab(poly(ppts), ZF - 2.2, ZF - 1.19) + planks) - fnd - union([f_ for _, f_, _ in seats])
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch", render=FT.plank_zones(deck, ZF, "Planks", "PorchDeck"))
    for k, x in enumerate(xs):
        kit.add(f"PORCH-post-{k}", "Cream", C.post_dutch(BEAM_Z0 - ZF).translate([x, POST_Y, ZF]) + seats[k][0],
                key="PORCH-post", group="porch")
    beam = box([-RG + 1.0, POST_Y - 1.6, BEAM_Z0], [W + RG - 1.0, POST_Y + 1.6, Z_KB + 1.9]) - env
    beam = beam + box([-RG + 1.0, POST_Y - 1.9, BEAM_Z0], [W + RG - 1.0, POST_Y + 1.9, BEAM_Z0 + 0.8])
    kit.add("PORCH-beam", "Cream", beam - union([t_ for _, _, t_ in seats]), group="porch")
    fr = MAIN.facades()[0]
    A = fr.A.copy()
    A[:, 3] = fr.world(XC, -ZF, FL - 1.0 + 0.9)
    kit.add("STEPS-front", "Boulder", FT.steps(20.0, ZF - 0.6, 3, cheek=1.8).transform(A), group="porch")
    e, u = MAIN.locate(XC, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Boulder", FT.steps(15.0, ZF - 0.6, 3).transform(A) - fnd, group="stoop")
    # glue joints: nothing small is left butted on a dab of glue (see NOTES.md)
    FT.key_into(kit, "STEPS-front", ["PORCH-base"], (0, 1, 0), depth=0.8, conform=True)
    print("specks dropped:", kit.drop_specks())
    print("porch", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "vantassel")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "vantassel.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
