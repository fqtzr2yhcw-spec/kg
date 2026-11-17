"""Massing 110: an Adirondack great camp lodge (after Sagamore, Raquette Lake, New York, 1897,
by William West Durant).

New: a Swiss-chalet log lodge three storeys high under a steep front gable whose eaves reach
far out on great log brackets, stacked balconies across the gable front (a porch, a balcony,
and a smaller one tucked under the peak); a one-storey dining cabin at right angles, reached by
a covered walk; a huge boulder chimney climbing the lodge's side; a rocky site. Front faces -y.
"""
import sys
sys.path.insert(0, sys.argv[1])
from mk import (Model, bx, block, gable_y, gable_x, posts, stack, rail_x, rail_y, win_xz, win_yz, skin_roof, roof,
                rect_fp, sunk, boulder, steps_y)
from manifold3d import Manifold as M
import numpy as np

OUT = sys.argv[2]
m = Model()
ZF, S1, S2, ZE = 10.0, 44.0, 74.0, 74.0
X0, X1, Y0, Y1 = 40.0, 136.0, 76.0, 156.0          # the lodge, 96 x 80
SL = 1.05
XC = (X0 + X1) / 2

# the lodge: walls to a steep front-and-back gable; the roof runs 16 out over the front gable
G = gable_y(X0, X1, ZE, SL)
m.add("wall", roof(rect_fp(X0, Y0, X1, Y1), ZF, sunk(G, 1.3)))
m.add("roof", skin_roof([(X0 - 5, Y0 - 16), (X1 + 5, Y0 - 16), (X1 + 5, Y1 + 6), (X0 - 5, Y1 + 6)], G, th=2.6))
m.add("base", bx(X0 - 2, Y0 - 2, 0.0, X1 + 2, Y1 + 2, ZF))
# log brackets under the overhang, from the gable face out to the roof's edge
for x in (X0 + 2, XC - 18, XC + 18, X1 - 2):
    zr = ZE + SL * min(x - X0, X1 - x)
    m.add("trim", M.hull_points([(x + dx, y, z) for dx in (-1.2, 1.2) for y, z in
                                 ((Y0, zr - 22.0), (Y0, zr - 2.0), (Y0 - 15.0, zr - 2.5))]))
# stacked balconies: a porch on posts, a balcony at the second floor, a small one under the peak
m.add("deck", bx(X0 - 4, Y0 - 18, ZF - 1.2, X1 + 4, Y0, ZF))
posts(m, [(x, Y0 - 16.5) for x in np.linspace(X0 - 2.5, X1 + 2.5, 5)], ZF, S1 + 6.0, r=1.8)
m.add("deck", bx(X0 - 4, Y0 - 18, S1 + 4.4, X1 + 4, Y0, S1 + 6.0))
rail_x(m, X0 - 4, X1 + 4, Y0 - 17.4, S1 + 6.0, h=7.0)
posts(m, [(x, Y0 - 16.5) for x in np.linspace(X0 - 2.5, X1 + 2.5, 5)], S1 + 6.0, S2 + 6.0, r=1.5)
m.add("deck", bx(X0 + 6, Y0 - 12, S2 + 4.6, X1 - 6, Y0, S2 + 6.0))
rail_x(m, X0 + 6, X1 - 6, Y0 - 11.4, S2 + 6.0, h=7.0)
steps_y(m, XC - 10, XC + 10, Y0 - 18, ZF, 3)
m.add("roof", bx(X0 - 6, Y0 - 20, S2 + 6.0, X0 + 6, Y0, S2 + 7.6) + bx(X1 - 6, Y0 - 20, S2 + 6.0, X1 + 6, Y0, S2 + 7.6))
# the boulder chimney up the west side, tapering, boulders at its foot
CY = (Y0 + Y1) / 2 + 8
m.add("chimney", M.hull_points([(x, y, z) for z, hw, d in ((0.0, 15.0, 16.0), (40.0, 11.0, 13.0), (ZE + SL * 18 + 12, 8.0, 11.0))
                                for x in (X0 - d, X0 + 1.0) for y in (CY - hw, CY + hw)]))
for i, (c, r) in enumerate((((X0 - 18, CY - 14), 7.0), ((X0 - 20, CY + 10), 6.0), ((X0 - 10, CY + 18), 5.0))):
    m.add("chimney", boulder(c, r, squash=0.8, seed=10 + i))

# the dining cabin at right angles, its gable to the east; the covered walk to it
DX0, DX1, DY0, DY1 = 158.0, 230.0, 100.0, 156.0
block(m, DX0, DY0, DX1, DY1, ZF, gable_x(DY0, DY1, 42.0, 0.85), over=5.0, rake=7.0)
m.add("base", bx(DX0 - 1, DY0 - 1, 0.0, DX1 + 1, DY1 + 1, ZF))
m.add("chimney", M.hull_points([(x, y, z) for z, hw, d in ((0.0, 12.0, 12.0), (30.0, 9.0, 10.0), (82.0, 6.0, 7.0))
                                for x in (DX1 - 1.0, DX1 + d) for y in (128.0 - hw, 128.0 + hw)]))
m.add("deck", bx(X1, 116.0, ZF - 1.2, DX0, 136.0, ZF))
m.add("roof", skin_roof([(X1, 114.0), (DX0, 114.0), (DX0, 138.0), (X1, 138.0)], gable_x(114.0, 138.0, 34.0, 0.7), th=1.8))
posts(m, [(x, y) for x in (X1 + 6, DX0 - 6) for y in (117.0, 135.0)], ZF, 34.0, r=1.3)
# a porch along the cabin's front
m.add("deck", bx(DX0, DY0 - 14, ZF - 1.2, DX1, DY0, ZF))
posts(m, [(x, DY0 - 12.5) for x in np.linspace(DX0 + 2, DX1 - 2, 5)], ZF, 38.0, r=1.4)
m.add("roof", skin_roof([(DX0 - 2, DY0 - 16), (DX1 + 2, DY0 - 16), (DX1 + 2, DY0 + 1), (DX0 - 2, DY0 + 1)],
                        [[((0.0, DY0 - 16), (0, 1), 37.0, 0.35)]], th=1.8))

# windows: the gable front's three floors, sides; the cabin
for x in (X0 + 12, X1 - 24):
    m.add("glass", win_xz(x, x + 12, 16.0, 38.0, Y0))
    m.add("glass", win_xz(x, x + 12, S1 + 8, S1 + 26, Y0))
m.add("glass", win_xz(XC - 7, XC + 7, ZF, 38.0, Y0))
m.add("glass", win_xz(XC - 6, XC + 6, S1 + 6, S1 + 28, Y0))
m.add("glass", win_xz(XC - 6, XC + 6, S2 + 6, S2 + 24, Y0))
for y in (Y0 + 14, Y0 + 50):
    m.add("glass", win_yz(y, y + 12, 16.0, 38.0, X1, out=1))
    m.add("glass", win_yz(y, y + 12, S1 + 8, S1 + 26, X1, out=1))
for x in np.linspace(DX0 + 8, DX1 - 18, 4):
    m.add("glass", win_xz(x, x + 10, 16.0, 34.0, DY0))
for i, (c, r) in enumerate((((24.0, 60.0), 9.0), ((150.0, 70.0), 7.0), ((236.0, 84.0), 8.0), ((30.0, 170.0), 10.0),
                            ((140.0, 176.0), 8.0), ((244.0, 166.0), 9.0))):
    m.add("base", boulder(c, r, squash=0.75, seed=i))
lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
