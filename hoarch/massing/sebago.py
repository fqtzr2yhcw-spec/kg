"""Massing 111: a New England connected farm (after the "big house, little house, back house,
barn" farmsteads of Maine and New Hampshire, 1840s-80s).

New: four buildings joined end to end, each lower and set further back than the last, their
ridges turning as they go: a two-storey Greek Revival big house with its gable to the road; a
storey-and-a-half kitchen ell (the little house) with a porch onto the dooryard; a one-storey
woodshed and workshop (the back house) open in two arched bays; and an English barn with its
long side to the road and great doors in the middle of it, a lean-to on its far end. Front
faces -y.
"""
import sys
sys.path.insert(0, sys.argv[1])
from mk import (Model, bx, block, gable_y, gable_x, posts, stack, rail_x, win_xz, win_yz, skin_roof, roof, rect_fp,
                sunk, xz_panel, round_head, steps_y)
from manifold3d import Manifold as M
import numpy as np

OUT = sys.argv[2]
m = Model()
ZF = 8.0

# the big house: gable to the road, Greek Revival (corner pilasters, a full entablature, a
# pedimented gable with its return), side-hall door
BX0, BX1, BY0, BY1 = 10.0, 76.0, 36.0, 124.0
block(m, BX0, BY0, BX1, BY1, ZF, gable_y(BX0, BX1, 76.0, 0.72), over=3.0, rake=3.0)
m.add("base", bx(BX0 - 1, BY0 - 1, 0.0, BX1 + 1, BY1 + 1, ZF))
for x in (BX0, BX1 - 4.0):
    m.add("trim", bx(x - 0.6, BY0 - 0.6, ZF, x + 4.6, BY0 + 4.0, 76.0))                     # pilasters
m.add("trim", bx(BX0 - 0.8, BY0 - 0.8, 70.0, BX1 + 0.8, BY0 + 1.0, 76.0))                   # the entablature across the gable
stack(m, (BX0 + BX1) / 2, BY0 + 50.0, 8, 8, 90.0, 118.0)
m.add("glass", win_xz(BX0 + 8, BX0 + 20, ZF, 38.0, BY0))                                    # side-hall door, sidelights
m.add("trim", bx(BX0 + 5, BY0 - 3, ZF, BX0 + 23, BY0, 42.0) - bx(BX0 + 7.5, BY0 - 4, ZF, BX0 + 20.5, BY0 - 0.5, 39.0))
steps_y(m, BX0 + 6, BX0 + 22, BY0 - 3, ZF, 3)
for x in (BX0 + 32, BX0 + 48):
    m.add("glass", win_xz(x, x + 10, 16.0, 38.0, BY0))
for x in (BX0 + 10, BX0 + 30, BX0 + 48):
    m.add("glass", win_xz(x, x + 10, 50.0, 68.0, BY0))
m.add("glass", win_xz(39.0, 47.0, 84.0, 94.0, BY0))
for y in (52.0, 76.0, 100.0):
    m.add("glass", win_yz(y, y + 10, 16.0, 38.0, BX0, out=-1))
    m.add("glass", win_yz(y, y + 10, 50.0, 68.0, BX0, out=-1))

# the little house: a storey and a half, ridge along the chain, porch onto the dooryard
LX0, LX1, LY0, LY1 = BX1, 124.0, 70.0, 124.0
block(m, LX0 - 2, LY0, LX1, LY1, ZF, gable_x(LY0, LY1, 50.0, 0.8), over=3.0, rake=0.0)
m.add("base", bx(LX0, LY0 - 1, 0, LX1, LY1 + 1, ZF))
m.add("deck", bx(LX0, LY0 - 14, ZF - 1.2, LX1, LY0, ZF))
posts(m, [(x, LY0 - 12.5) for x in np.linspace(LX0 + 3, LX1 - 2, 4)], ZF, 40.0, r=1.4)
m.add("roof", skin_roof([(LX0, LY0 - 16), (LX1 + 2, LY0 - 16), (LX1 + 2, LY0 + 1), (LX0, LY0 + 1)],
                        [[((0.0, LY0 - 16), (0, 1), 39.0, 0.4)]], th=1.8))
stack(m, LX1 - 12, 97.0, 8, 7, 60.0, 84.0)
m.add("glass", win_xz(LX0 + 8, LX0 + 18, ZF, 34.0, LY0))
m.add("glass", win_xz(LX0 + 26, LX0 + 36, 16.0, 34.0, LY0))
for x in (LX0 + 8, LX0 + 30):                                                             # knee-wall lights
    m.add("glass", win_xz(x, x + 9, 42.0, 48.0, LY0))

# the back house: one storey, two arched open bays (the woodshed) and a workshop door
KX0, KX1, KY0, KY1 = LX1, 166.0, 80.0, 124.0
block(m, KX0 - 2, KY0, KX1, KY1, ZF, gable_x(KY0, KY1, 38.0, 0.75), over=3.0, rake=0.0)
m.add("base", bx(KX0, KY0 - 1, 0, KX1, KY1 + 1, ZF))
for x0 in (KX0 + 4.0, KX0 + 20.0):
    m.add("shadow", xz_panel(round_head(x0, x0 + 13.0, ZF, 30.0), KY0 - 0.4, KY0 + 0.2))
m.add("glass", win_xz(KX1 - 9, KX1 - 3, 14.0, 30.0, KY0))

# the English barn: long side to the road, great doors in its middle, a lean-to at the far end
RX0, RX1, RY0, RY1 = KX1, 238.0, 62.0, 134.0
block(m, RX0 - 2, RY0, RX1, RY1, ZF, gable_x(RY0, RY1, 54.0, 0.95), over=4.0, rake=4.0)
m.add("base", bx(RX0, RY0 - 1, 0, RX1, RY1 + 1, ZF))
DX = (RX0 + RX1) / 2
m.add("shadow", bx(DX - 14, RY0 - 0.4, ZF, DX + 14, RY0 + 0.2, 46.0))                    # the great doors
m.add("trim", bx(DX - 32, RY0 - 2.0, 48.0, DX + 32, RY0 - 1.0, 49.0))                    # their track
m.add("deck", bx(DX - 16, RY0 - 12, 0.0, DX + 16, RY0, ZF))                             # the ramp
m.add("upper", roof(rect_fp(DX - 10, RY0 - 9, DX + 10, RY0 + 1), 60.0, gable_y(DX - 10, DX + 10, 60.0, 1.0)))   # hay hood
m.add("roof", skin_roof(rect_fp(DX - 11, RY0 - 10, DX + 11, RY0 + 1), gable_y(DX - 11, DX + 11, 60.0, 1.0), th=1.6))
block(m, RX1, RY0 + 16, RX1 + 16, RY1, ZF, [[((RX1 + 16, 0.0), (-1, 0), 34.0, 0.6)]], over=2.0, rake=2.0)
m.add("base", bx(RX1, RY0 + 15, 0, RX1 + 16, RY1 + 1, ZF))
for x in (RX0 + 8, RX1 - 16):
    m.add("glass", win_xz(x, x + 8, 30.0, 40.0, RY0))
# the dooryard between the ell and the road
m.add("deck", bx(LX0, 30.0, 0.0, RX0, LY0 - 14, 0.6))
lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
