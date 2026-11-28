"""Massing 109: a five-part Palladian house (after the Hammond-Harwood House, Annapolis,
Maryland, 1774, by William Buckland).

New: the plan is five buildings in a row, symmetrical: a two-storey centre block with a
pedimented centre pavilion, two one-storey hyphens set back from it, and two wings at the ends
whose fronts are canted bays (half-octagons) under hipped roofs. Wide and low, the opposite of
our towered houses. Front faces -y.
"""
import sys
sys.path.insert(0, sys.argv[1])
from mk import (Model, bx, block, gable_x, gable_y, hip_poly, posts, stack, win_xz, win_yz, skin_roof, roof, rect_fp,
                sunk, steps_y)
from manifold3d import Manifold as M
from hoarch.core import slab, offset, poly
import numpy as np

OUT = sys.argv[2]
m = Model()
ZF, S1, ZE = 8.0, 44.0, 78.0
CX0, CX1, CY0, CY1 = 74.0, 178.0, 60.0, 128.0      # the centre block, 104 x 68
XC = (CX0 + CX1) / 2

# the centre block: a gable roof along the front, the pavilion's pediment, two pairs of stacks
block(m, CX0, CY0, CX1, CY1, ZF, gable_x(CY0, CY1, ZE, 0.55), over=3.0, rake=2.0)
PX0, PX1 = XC - 20.0, XC + 20.0
block(m, PX0, CY0 - 4.0, PX1, CY0 + 10.0, ZF, gable_y(PX0, PX1, ZE, 0.42), over=2.0, rake=3.0)
m.add("trim", bx(CX0 - 1.2, CY0 - 1.2, ZE - 5, CX1 + 1.2, CY0, ZE) + bx(CX0 - 1.2, CY1, ZE - 5, CX1 + 1.2, CY1 + 1.2, ZE))
m.add("trim", bx(CX0 - 0.8, CY0 - 0.8, S1 - 1.6, CX1 + 0.8, CY1 + 0.8, S1))                  # the belt course
for x in (CX0 + 6.0, CX1 - 6.0):
    for y in (CY0 + 22.0, CY1 - 22.0):
        stack(m, x, y, 8, 6, ZE + 10, ZE + 0.55 * 34 + 12)

# the hyphens: one storey, set back
for xa, xb in ((44.0, CX0), (CX1, 208.0)):
    block(m, xa, 80.0, xb, 120.0, ZF, gable_x(80.0, 120.0, 40.0, 0.5), over=2.0, rake=0.0)
# the wings: canted bays to the front under hipped roofs
for xa, xb in ((4.0, 44.0), (208.0, 248.0)):
    pts = [(xa + 12.0, 52.0), (xb - 12.0, 52.0), (xb, 66.0), (xb, 128.0), (xa, 128.0), (xa, 66.0)]
    Hw = hip_poly(pts, 64.0, 0.75)
    m.add("wall", roof(pts, ZF, sunk(Hw, 1.2)))
    big = [(x + (3.0 if x > (xa + xb) / 2 else -3.0), y + (3.0 if y > 90 else -3.0)) for x, y in pts]
    m.add("roof", skin_roof(big, hip_poly(big, 64.0 - 0.75 * 3.0, 0.75), th=2.4))
    xc = (xa + xb) / 2
    stack(m, xc, 112.0, 8, 6, 70.0, 94.0)
    m.add("glass", win_xz(xc - 6, xc + 6, 16.0, 40.0, 52.0))
    m.add("glass", win_xz(xc - 4, xc + 4, 48.0, 58.0, 52.0))
    for y in (86.0, 106.0):
        m.add("glass", win_yz(y, y + 9, 16.0, 38.0, xa if xa < 100 else xb, out=-1 if xa < 100 else 1))
    m.add("trim", slab(offset(poly(pts[::-1] if False else pts), 0.8), ZF - 0.8, ZF))

# the base, the centre door's steps; windows: five bays both storeys, the hyphens' arched lights
m.add("base", bx(2.0, 50.0, 0.0, 250.0, 130.0, ZF) - bx(44.0, 50.0, -1, 74.0, 79.0, 20) - bx(178.0, 50.0, -1, 208.0, 79.0, 20)
      - bx(74.0, 50.0, -1, 178.0, 55.0, 20) + bx(PX0 - 2, CY0 - 6.0, 0, PX1 + 2, CY0, ZF))
steps_y(m, XC - 10, XC + 10, CY0 - 6.0, ZF, 3)
for x in (CX0 + 10.0, CX0 + 28.0, CX1 - 38.0, CX1 - 20.0):
    m.add("glass", win_xz(x, x + 10, 14.0, 38.0, CY0))
    m.add("glass", win_xz(x, x + 10, 50.0, 70.0, CY0))
    m.add("glass", win_xz(x, x + 10, 14.0, 38.0, CY1, out=1))
    m.add("glass", win_xz(x, x + 10, 50.0, 70.0, CY1, out=1))
m.add("glass", win_xz(XC - 7, XC + 7, ZF, 38.0, CY0 - 4.0, head="round"))
m.add("glass", win_xz(XC - 6, XC + 6, 50.0, 72.0, CY0 - 4.0, head="round"))
m.add("glass", win_xz(XC - 3, XC + 3, 82.0, 88.0, CY0 - 4.0 - 0.01))
for xa in (44.0, CX1):
    m.add("glass", win_xz(xa + 10, xa + 20, 14.0, 34.0, 80.0, head="round"))
lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
