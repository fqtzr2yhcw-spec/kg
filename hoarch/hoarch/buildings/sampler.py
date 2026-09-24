"""Detail test plate: a 34 x 30 mm corner of the Ashby villa built exactly like the full kit.

Print it before the full villa (one plate, one colour, about 2 h) and check what matters:
clapboards and corner boards on an upright shell, the belt ring joint between the storey
shells, the locating lips, window/door inserts and their fit in the openings, louvered
shutters, quoins, the belt ring's blocks, the bracketed eave with frieze panels printed
upside down, the standing-seam hip roof, a panelled brick chimney and a separate turned
finial, plus a run of the porch: turned posts and railings in one upright piece, the sawn-work
arcade printed on edge, and a piece of the board floor with post sockets.

usage: python3 -m hoarch.buildings.sampler [check] [export] [colour]
       (``colour`` exports in the villa's colours instead of one test colour)
"""
import os
import sys

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch import features as FT, openings as O, roof as R
from hoarch.buildings import villa as V
from hoarch.core import Facade, box, compose, inv34, poly, slab, union
from hoarch.kit import Kit, print_flip
from hoarch.ornament import finial
from hoarch.shell import Block, Opening, foundation, lip_keep, storey_shells

NAME = "Ashby detail test plate"
SX, S = 34.0, 30.0                 # front wide enough for a shuttered window between quoins
ZF, BELT, ZW = V.ZF, V.BELT, V.ZW
BLOCK = Block("sample", [(0, 0), (SX, 0), (SX, S), (0, S)], ZF, ZW)


def _openings():
    lo = O.window_insert(10.0, 24.0, rise=0, style="flat", apron=True)
    up = O.window_insert(10.0, 21.0, rise=None, style="key")
    door = O.door_insert(11.0, 26.0, leaves=1, glass_top=True)
    L = []

    def add(x, y, v0, sp, name, kind="window", shutters=False):
        e, u = BLOCK.locate(x, y)
        L.append((Opening(BLOCK, e, u, v0, sp, name, kind), shutters))

    add(SX / 2, 0, V.V1, lo, "S-1", shutters=True)
    add(SX / 2, 0, V.V2, up, "S-2", shutters=True)
    add(SX, S / 2, 0.4, door, "E-door", "door")
    add(SX, S / 2, V.V2, up, "E-2")
    return L


OPENINGS_S = _openings()


def build(single=True):
    colors = {"Test": "#B8B8B8"} if single else V.COLORS
    mat = {"Test": "trim"} if single else V.RENDER_MAT
    kit = Kit(NAME, colors, mat)

    def C(c):
        return "Test" if single else c

    ops = [o for o, _ in OPENINGS_S]
    clear = [lip_keep(poly(BLOCK.pts), 3.0, ZF, 1.2),
             lip_keep(poly(BLOCK.pts), 3.0, ZW - 1.6, 1.6, inner=0.15, reach=1.2)]
    st = storey_shells([BLOCK], ops, ZF + BELT[0], t=3.0, corners="quoin", clear=clear)
    kit.add("WALLS-1", C("Sand"), st["lower"])
    kit.add("BELT", C("White"), st["ring"])
    kit.add("WALLS-2", C("Sand"), st["upper"])
    kit.add("FOUNDATION", C("Stone"), foundation([BLOCK], 0.0, ZF))
    for o, sh in OPENINGS_S:
        A = o.local_frame()
        sp = o.spec
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, C("White"), C("Forest" if o.kind == "door" else "White"))
        kit.add(f"{key}-{o.name}", C("Doors" if o.kind == "door" else "Windows"), world, P=P, render=zones)
        if sh:
            b = sp["cut"].bounds()
            w_op, h_op = b[2] - b[0], b[3] - b[1]
            arched = abs(sp["top"] - h_op) > 3.0 and o.v0 > 20
            hh = (h_op - w_op / 2 - 1.8) if arched else h_op
            for side, m in zip("LR", FT.shutters_for(w_op, h_op, casing=1.1, h=hh)):
                kit.add(f"SHUTTER-{o.name}-{side}", C("Forest"), m.translate([0, 0, 0.32]).transform(A), P=inv34(A))
    # eave (upside down) and a pyramid hip roof with a chimney and a separate finial
    eave = R.bracketed_cornice(BLOCK.pts, ZW, R.EAVE_DEEP,
                               brackets=dict(z_top=5.2, h=5.0, d0=0.9, d=5.6, t=0.8, pitch=12.0, pair=1.9, margin=4.5),
                               dents=dict(z=4.4, h=0.8, d0=0.9, d=0.7), panels=dict(z=0.6, h=3.0, d=0.4))
    kit.add("EAVE", C("White"), eave, P=print_flip())
    z_eave = V.Z_EAVE_TOP
    roof, tex = R.hip_roof([(BLOCK.pts, [0, 1, 2, 3])], z_eave, V.ROOF_SLOPE, V.D_EAVE, texture="seam")
    ztip = z_eave + V.ROOF_SLOPE * (S / 2 + V.D_EAVE)
    zseat = ztip - 0.8
    cx, cy = SX / 2, S / 2
    chx, chy = 7.5, 15.0
    chim_z0 = z_eave + V.ROOF_SLOPE * (chx - 5.65 + V.D_EAVE) - 3.0
    pocket = box([chx - 5.65, chy - 5.65, chim_z0], [chx + 5.65, chy + 5.65, ztip + 20])
    seat = M.cylinder(1.0, 1.35, 1.35, 32).translate([cx, cy, zseat - 0.4])
    kit.add("ROOF", C("Charcoal"), (roof + tex).trim_by_plane([0, 0, -1.0], -zseat) - pocket - seat)
    kit.add("FINIAL", C("Charcoal"), finial(1.2, 7.4).translate([cx, cy, zseat - 0.4]))
    ch = FT.chimney(w=10.5, dpt=10.5, h=ztip + 6.0 - chim_z0, peg=None).translate([chx, chy, chim_z0])
    kit.add("CHIMNEY", C("Brick"), ch)
    # a free-standing run of the villa's porch in front of the house: floor piece with post
    # sockets, three turned posts and two railings in one upright piece, and the arcade (on edge)
    H_floor = ZF - 1.0
    post_h = (ZF + BELT[0] - 0.2) - (H_floor + 5.2)
    y_run = -40.0
    us = [1.6, SX / 2, SX - 1.6]
    f = Facade((0.0, y_run), (SX, y_run), 0.0)
    A = f.A.copy()
    A[:, 3] = np.r_[f.p0, H_floor]
    post = FT.turned_post(post_h - 2.2 + 0.4, collar=8.6 + 0.4)
    # posts and railings as one piece, printed upright (as on the villa)
    frame = [post.translate([p[0], p[1], H_floor - 0.4]) for p in (f.p0 + f.u * u for u in us)]
    for a, b in zip(us[:-1], us[1:]):
        rail = FT.railing_section((b - a) - 1.6, sink=0.4, foot_margin=1.6, stiles=False).translate([a + 0.8, 0, 0])
        frame.append(rail.transform(FT.Z_UP_TO_FACADE).transform(A))
    frame = union(frame)
    kit.add("PORCH-frame", C("White"), frame)
    socks = slab(frame.slice(H_floor - 0.2).offset(0.15, JoinType.Miter, 4.0), H_floor - 0.41, H_floor + 1)
    arc = FT.porch_arcade(us[0] - 1.5, us[-1] + 1.5, us, post_h)
    kit.add("PORCH-arcade", C("White"), arc.transform(A), P=compose(FT.ARCADE_PRINT, inv34(A)))
    fl = FT.porch_floor([(0.0, y_run - 1.6), (SX, y_run - 1.6), (SX, y_run + 8.0), (0.0, y_run + 8.0)], [0, 1, 3],
                        H=H_floor)
    kit.add("PORCH-floor", C("Stone"), fl - socks, P=print_flip())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    single = "colour" not in sys.argv
    OUT = os.path.join(HERE, "..", "..", "out", "sampler" + ("" if single else "_colour"))
    os.makedirs(OUT, exist_ok=True)
    kit = build(single=single)
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:20]:
            print("  ", b)
        from hoarch.lint import lint_kit
        lint_kit(kit, layer=0.2, limit=0.5)
    kit.render_npz(os.path.join(OUT, "sampler.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2)
