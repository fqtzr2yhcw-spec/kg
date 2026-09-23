"""Detail test plate: a 34 x 30 mm corner of the Ashby villa built exactly like the full kit.

Print it before the full villa (one plate, one colour, about 2 h) and check what matters:
clapboards and corner boards on an upright shell, the belt ring joint between the storey
shells, the locating lips, window/door inserts and their fit in the openings, louvered
shutters, quoins, the belt ring's blocks, the bracketed eave with frieze panels printed
upside down, the standing-seam hip roof, a panelled brick chimney and a separate turned
finial, plus a short run of porch posts with brackets and railing and a piece of floor.

usage: python3 -m hoarch.buildings.sampler [check] [export] [colour]
       (``colour`` exports in the villa's colours instead of one test colour)
"""
import os
import sys

import numpy as np
from manifold3d import Manifold as M

from hoarch import features as FT, openings as O, roof as R
from hoarch.buildings import villa as V
from hoarch.core import box, inv34, poly
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
    add(SX, S / 2, 0.3, door, "E-door", "door")
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
             lip_keep(poly(BLOCK.pts), 3.0, ZW - 1.5, 1.5, inner=0.15, reach=1.2)]
    st = storey_shells([BLOCK], ops, ZF + BELT[0], t=3.0, corners="quoin", clear=clear)
    kit.add("WALLS-1", C("Sand"), st["lower"])
    kit.add("BELT", C("White"), st["ring"])
    kit.add("WALLS-2", C("Sand"), st["upper"])
    kit.add("FOUNDATION", C("Stone"), foundation([BLOCK], 0.0, ZF))
    for o, sh in OPENINGS_S:
        A = o.local_frame()
        sp = o.spec
        key = "DOOR" if o.kind == "door" else "WIN"
        kit.add(f"{key}-{o.name}-sash", C("Forest" if o.kind == "door" else "White"), sp["sash"].transform(A), P=inv34(A))
        kit.add(f"{key}-{o.name}-surround", C("White"), sp["surround"].transform(A), P=inv34(A))
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
    # a short run of the villa's porch posts (front face down), set in front of the house
    H_floor = ZF - 1.0
    post_h = (ZF + BELT[0] - 0.2) - (H_floor + 5.2)
    panel = FT.porch_posts(SX, post_h, [1.3, SX / 2, SX - 1.3], style="bracket", rail=dict(h=8.6))
    f = BLOCK.facades()[0]
    A = f.A.copy()
    A[:, 3] = f.world(0.0, 0.0, 30.0) + np.array([0, 0, H_floor])
    back_down = np.array([[1.0, 0, 0, 0], [0, -1.0, 0, 0], [0, 0, -1.0, 0]])
    from hoarch.core import compose
    kit.add("PORCH-posts", C("White"), panel.transform(A), P=compose(back_down, inv34(A)))
    # a piece of the slotted porch floor (boards, border board, nosing), printed top down
    fl = FT.porch_floor([(0, -46), (SX, -46), (SX, -34), (0, -34)], [0, 1, 3], H=H_floor)
    kit.add("PORCH-floor", C("Stone"), fl, P=print_flip())
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
