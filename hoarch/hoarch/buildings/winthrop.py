"""The Winthrop: an original HO-scale (1:87.1) Garrison Colonial, house 37 of the third batch.

A ground storey of red brick laid in rat-trap bond (bricks on edge) on galleted rubble, under
an upper storey of oyster clapboard (its lengths joined in long diagonal scarfs) that jetties
out over the front on a moulded girt, with turned acorn drops hanging under the overhang.
Twelve-over-twelve windows: in segmental-headed openings below, under caps broken by a key
block above. A seventeenth-century doorway: a pair of chevron-boarded leaves studded with
nails in a four-centred (Tudor) arch under a label moulding. Between the storeys (the jetty's
girt) a sage frieze of linenfold panels, an ivory cable course and an ivory ovolo; at the eave
a sage frieze of acorns and oak leaves, ivory dentils and an ivory cyma, across the gable
feet. A side-gabled roof of slates banded notched and square, and at each end an exterior
chimney of English-bond brick that steps in on two sloping shoulders.

usage: python3 -m hoarch.buildings.winthrop [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, cs_union, offset, poly, rect, slab, union
from hoarch import colonial as C, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, belt_ring, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Winthrop"
COLORS = {"Brick": "#7E3526", "Oyster": "#CFC7B5", "Ivory": "#EEE8D8", "Slate": "#535B66", "Sage": "#7D8B6A",
          "Rubble": "#857F74", "Windows_Doors": "#EEE8D8"}
RENDER_MAT = {"Brick": "brick", "Oyster": "siding", "Ivory": "trim", "Slate": "roof", "Sage": "accent", "Rubble": "stone2",
              "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Winthrop)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="linenfold", role="Sage"),
    dict(kind="course", h=1.4, b=1.4, orn="cable", role="Ivory"),
    dict(kind="crown", h=2.2, b=1.4, P=3.0, orn="ovolo", role="Ivory")])
EAVE = dict(pitch=11.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.0, b=1.2, orn="acorns", role="Sage"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Ivory", tooth=0.8, gap=0.6),
    dict(kind="crown", h=2.8, b=1.4, P=6.0, orn="cyma", role="Ivory")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)
SLATES = ("notch", "square")

# ------------------------------------------------------------------ levels and plan
ZF = 10.0
S1 = ZF + 40.0
ZU = S1 + RJ                                    # the upper storey's foot
ZE = ZU + 36.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 7.0, 7.2, 1.8
S_MAIN = 0.9
W, D, JET = 172.0, 88.0, 5.0                    # the upper storey jetties JET out over the front
XC = W / 2
LOW = Block("lower", [(0, 0), (W, 0), (W, D), (0, D)], ZF, S1)
UP = Block("upper", [(0, -JET), (W, -JET), (W, D), (0, D)], ZU, ZW)
BLOCKS = [LOW, UP]
V1, V2 = 7.0, 5.0
YC = (D - JET) / 2                              # the end chimneys' centre line
CHW, CHD = 22.0, 9.0


def _chimneys(z_ridge):
    """The two end chimneys, placed against each gable (the raw solids), and their clearances: a
    slightly larger copy reaching 0.05 into the wall, cut from the siding, trim and roof."""
    hch = z_ridge + 8.0
    sh = ((round((S1 - 4.0) / hch, 3), 0.72), (round((ZE - 6.0) / hch, 3), 0.5))
    ch = C.chimney_shouldered(CHW, CHD, hch, shoulders=sh)
    cl = C.chimney_shouldered(CHW + 0.8, CHD + 0.45, hch, shoulders=sh).translate([0.0, -0.05, 0.0])
    raw, clr = [], []
    for x0, sgn in ((0.0, -1.0), (W, 1.0)):
        A = np.array([[0, sgn, 0, x0], [-sgn, 0, 0, YC], [0, 0, 1.0, 0.0]])
        raw.append(ch.transform(A))
        clr.append(cl.transform(A))
    return raw, clr


def _brick(f, b, reg):
    return C.brick_rattrap(reg, datum=0.0)


def _clap(f, b, reg):
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    return C.clapboard_scarfed(reg, datum=0.0, seed=int(abs(f.p0[0]) + abs(f.p0[1])) % 91)


def _openings():
    L1, L2 = [], []

    def add(L, blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    lo = C.window_segmental(10.0, 20.0)
    up = C.window_keycap(10.0, 18.0)
    att = C.window_keycap(6.4, 8.0, lites=(2, 2), rows=(2, 2))
    for x in (20.0, 50.0, W - 50.0, W - 20.0):
        add(L1, LOW, x, 0.0, V1, lo, f"S{x:.0f}-1")
        add(L1, LOW, x, D, V1, lo, f"N{x:.0f}-1")
    add(L1, LOW, XC, 0.0, 0.4, C.door_tudor(12.0, 28.0), "front-door", "door")
    add(L1, LOW, XC, D, 0.4, C.door_tudor(11.0, 26.0), "back-door", "door")
    for x_, tag in ((0.0, "W"), (W, "E")):
        for y in (12.0, D - 12.0):
            add(L1, LOW, x_, y, V1, lo, f"{tag}{y:.0f}-1")
            add(L2, UP, x_, y, V2, up, f"{tag}{y:.0f}-2")
        for y in (YC - 22.0, YC + 22.0):
            add(L2, UP, x_, y, ZW - ZU + 3.0, att, f"{tag}{y:.0f}-attic")
    for x in (20.0, 50.0, XC, W - 50.0, W - 20.0):
        add(L2, UP, x, -JET, V2, up, f"S{x:.0f}-2")
        add(L2, UP, x, D, V2, up, f"N{x:.0f}-2")
    return L1, L2


OPEN1, OPEN2 = _openings()
OPENINGS = OPEN1 + OPEN2


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    rf = G.gabled_roof([(UP.pts, [0, 2], S_MAIN)], Z_EAVE, D_EAVE,
                       [dict(p0=(W, -JET), p1=(W, D), slope=S_MAIN, e=0.3), dict(p0=(0.0, D), p1=(0.0, -JET), slope=S_MAIN, e=0.3)],
                       texture=SLATES, tex_kw=dict(pitch=1.6, wtab=2.2, d=0.4), skin=SKIN, rake=RAKE,
                       inner_cs=offset(UP.cs, -3.0), fascia=FASCIA, hollow=2.8)
    we, ww = rf["walls"]
    gables = [(UP, 1, we["cs"].translate((0.0, Z_EAVE - ZU))), (UP, 3, ww["cs"].translate((0.0, Z_EAVE - ZU)))]
    zr = Z_EAVE + S_MAIN * ((D + JET) / 2 + D_EAVE)
    chims, chim_keep = _chimneys(zr)
    chim_cut = union(chim_keep)
    # --- the brick storey; the girt (joint ring) jettied out over the front; the clapboard storey
    w1 = wall_shell([LOW], OPEN1, t=3.0, belt=None, corners="none", water_table=False, siding=_brick, undress=chim_keep,
                    partitions=[((XC - 20.0, 3.0), (XC - 20.0, D - 3.0), 2.0, ZF, S1)])
    w1 = w1 - lip_keep(LOW.cs, 3.0, ZF, 1.2)
    w1 = w1 + _corbel(LOW.cs, 3.0, S1) + lip_ring(LOW.cs, 3.0, S1) - chim_cut
    kit.add("WALLS-1", "Brick", w1, group="walls")
    up_path = max(UP.cs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    ring = belt_ring(up_path, S1, t=3.0, prof=CO.joint_profile(RJ, LEDGE), blocks=None)
    soffit = box([0.0, -JET, S1], [W, 3.0, S1 + 1.6])
    ring = (ring + soffit) - lip_keep(LOW.cs, 3.0, S1) - chim_cut
    kit.add("JOINT", "Brick", ring, group="walls")
    undress = [slab(offset(UP.cs, 9.0), ZE - LEDGE - 0.6, ZW + 0.01)] + chim_keep
    w2 = wall_shell([UP], OPEN2, t=3.0, belt=None, corners="none", water_table=False, siding=_clap, gables=gables,
                    undress=undress, partitions=[((XC - 20.0, 3.0 - JET), (XC - 20.0, D - 3.0), 2.0, ZU, ZW)])
    w2 = w2 - lip_keep(UP.cs, 3.0, ZU)
    no_lip = union([box([W - 5.0, -JET - 1, ZW - 1], [W + 1, D + 1, ZW + 5]), box([-1, -JET - 1, ZW - 1], [5.0, D + 1, ZW + 5])])
    w2 = w2 + ((_corbel(UP.cs, 3.0, ZW) + lip_ring(UP.cs, 3.0, ZW)) - no_lip) + CO.ledge(up_path, ZE, LEDGE) - chim_cut
    kit.add("WALLS-2", "Oyster", w2, group="walls")
    rings, _ = CO.level(up_path, S1 + LEDGE + 0.4, JOINT, cut=chim_cut)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(up_path, ZE, EAVE, cut=chim_cut)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation([LOW], 0.0, ZF, style="galleted")
    kit.add("FOUNDATION", "Rubble", fnd, group="foundation")
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                group="inserts", render=zones)
    # acorn drops under the jetty, at the corners and between the bays
    drop = C.drop_acorn(6.0, 1.2)
    for k, x in enumerate((2.0, 35.0, 68.0, W - 68.0, W - 35.0, W - 2.0)):
        kit.add(f"DROP-{k}", "Ivory", drop.translate([x, -JET + 1.6, S1]), P=print_flip(), key="DROP", group="walls")
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the roof, the rakes cut round the end chimneys
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    yr = (D - JET) / 2
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((-RAKE, yr), (W + RAKE, yr), zr, S_MAIN, ZW) - walls_env)
    roof = roof - lip_keep(UP.cs, 3.0, ZW) - chim_cut
    kit.add("ROOF", "Slate", roof, group="roof")
    # --- the end chimneys: standing on the ground against each gable, stepping in on two shoulders
    for k, c in enumerate(chims):
        c = c - fnd - w1 - w2
        kit.add(f"CHIMNEY-{k}", "Brick", max(c.decompose(), key=lambda m_: m_.volume()), key="CHIMNEY", group="roof")
    print("roof + chimneys", round(time.time() - t0, 1))

    # --- stone steps at the doors
    fr = LOW.facades()[0]
    A = fr.A.copy()
    A[:, 3] = fr.world(XC, -ZF, 1.8)
    kit.add("STOOP-front", "Rubble", FT.steps(18.0, ZF - 0.6, 3).transform(A) - fnd, group="stoop")
    e, u = LOW.locate(XC, D)
    fb = LOW.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.8)
    kit.add("STOOP-back", "Rubble", FT.steps(15.0, ZF - 0.6, 3).transform(A) - fnd, group="stoop")
    # glue joints: nothing small is left butted on a dab of glue (see NOTES.md)
    for k_ in range(6):
        FT.key_into(kit, f"DROP-{k_}", ["JOINT"], (0, 0, 1))
    FT.key_into(kit, "STOOP-front", ["FOUNDATION"], (0, 1, 0), depth=0.8, conform=True)
    FT.key_into(kit, "STOOP-back", ["FOUNDATION"], (0, -1, 0), depth=0.8, conform=True)
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "winthrop")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "winthrop.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
