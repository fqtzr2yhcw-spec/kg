"""Massing 114: an estate gate lodge with the road passing through it (after the Lodge Gate of
the Biltmore Estate, Asheville, North Carolina, 1895, by Richard Morris Hunt).

New: a house that is also a gateway: a long, low lodge with a great arch through its middle
for the drive, rooms on either side and over the arch; brick and stone below, the upper storey
jettied and half-timbered; a steep hipped roof with a cross gable over the arch on both faces;
two tall chimneys; gate piers and low walls stepping out on either side of the drive. Front
faces -y.
"""
import sys
sys.path.insert(0, sys.argv[1])
from mk import (Model, bx, block, gable_x, gable_y, hip, posts, stack, win_xz, win_yz, skin_roof, roof, rect_fp, sunk,
                xz_panel, round_head)
from manifold3d import Manifold as M
import numpy as np

OUT = sys.argv[2]
m = Model()
ZF, S1, ZE = 6.0, 42.0, 72.0
X0, X1, Y0, Y1 = 26.0, 226.0, 84.0, 128.0          # 200 x 44
AX0, AX1, AS = 106.0, 146.0, 26.0                   # the arch: 40 wide, springing at 26 (top at 46)
XC = (AX0 + AX1) / 2
J = 3.0                                              # the upper storey's jetty

arch = xz_panel(round_head(AX0, AX1, -1.0, AS), Y0 - 12, Y1 + 12)
low = bx(X0, Y0, ZF, X1, Y1, S1) - arch
m.add("base", bx(X0 - 1, Y0 - 1, 0.0, X1 + 1, Y1 + 1, ZF) - arch)
m.add("wall", low)
H = hip(X0 - J, Y0 - J, X1 + J, Y1 + J, ZE, 1.3)
m.add("upper", roof(rect_fp(X0 - J, Y0 - J, X1 + J, Y1 + J), S1, sunk(H, 1.3)) - arch)
m.add("roof", skin_roof(rect_fp(X0 - J - 4, Y0 - J - 4, X1 + J + 4, Y1 + J + 4),
                        hip(X0 - J - 4, Y0 - J - 4, X1 + J + 4, Y1 + J + 4, ZE - 1.3 * 4, 1.3), th=2.6))
m.add("trim", bx(X0 - J, Y0 - J, S1 - 1.6, X1 + J, Y1 + J, S1) - arch)               # the jetty's bressumer
# the cross gable over the arch on both faces
for yf, s in ((Y0 - J, -1), (Y1 + J, 1)):
    ya, yb = sorted((yf, (Y0 + Y1) / 2))
    g = gable_y(XC - 26, XC + 26, ZE, 1.3)
    m.add("upper", roof(rect_fp(XC - 26, ya, XC + 26, yb), S1, sunk(g, 1.3)) - arch)
    yao, ybo = sorted((yf + s * 4, (Y0 + Y1) / 2))
    m.add("roof", skin_roof(rect_fp(XC - 30, yao, XC + 30, ybo), gable_y(XC - 30, XC + 30, ZE - 1.3 * 4, 1.3), th=2.6))
    m.add("glass", win_xz(XC - 10, XC + 10, S1 + 6, S1 + 22, yf, out=s))
    m.add("glass", win_xz(XC - 4, XC + 4, ZE + 8, ZE + 18, yf, out=s))
m.add("shadow", xz_panel(round_head(AX0 + 0.3, AX1 - 0.3, ZF, AS), (Y0 + Y1) / 2 - 0.2, (Y0 + Y1) / 2 + 0.2) -
      xz_panel(round_head(AX0 + 4, AX1 - 4, ZF - 1, AS), (Y0 + Y1) / 2 - 1, (Y0 + Y1) / 2 + 1))   # the gates inside
m.add("trim", xz_panel(round_head(AX0 - 3, AX1 + 3, ZF, AS), Y0 - 1.0, Y0) - xz_panel(round_head(AX0, AX1, ZF - 1, AS), Y0 - 2, Y0 + 1))
# chimneys
for x in (X0 + 30, X1 - 30):
    stack(m, x, (Y0 + Y1) / 2 + 6, 12, 8, 90.0, 132.0)
# windows: the ground floor's paired lights, the upper storey's, the end walls'
for xa in (X0 + 12, X0 + 44, X1 - 64, X1 - 32):
    for yf, s in ((Y0, -1), (Y1, 1)):
        m.add("glass", win_xz(xa, xa + 8, 14.0, 34.0, yf, out=s))
        m.add("glass", win_xz(xa + 10, xa + 18, 14.0, 34.0, yf, out=s))
        m.add("glass", win_xz(xa + 2, xa + 16, S1 + 8, S1 + 22, yf + s * J, out=s))
m.add("glass", win_xz(AX0 - 16, AX0 - 6, ZF, 34.0, Y0))                              # the lodge-keeper's door
for x, s in ((X0, -1), (X1, 1)):
    m.add("glass", win_yz(98.0, 114.0, 14.0, 34.0, x, out=s))
    m.add("glass", win_yz(100.0, 112.0, S1 + 8, S1 + 22, x + s * J, out=s))
# the drive through the arch; gate piers and low walls stepping out either side
m.add("deck", bx(AX0 + 2, 0.0, 0.0, AX1 - 2, 200.0, 0.6))
for x in (AX0 - 4, AX1 + 4):
    m.add("chimney", bx(x - 4, 40.0, 0.0, x + 4, 48.0, 30.0) + bx(x - 5, 39.0, 30.0, x + 5, 49.0, 33.0))
    m.add("trim", M.sphere(3.5, 24).translate([x, 44.0, 36.0]))
for xa, xb in ((10.0, AX0 - 8), (AX1 + 8, 242.0)):
    m.add("wall", bx(xa, 42.0, 0.0, xb, 46.0, 14.0))
    m.add("trim", bx(xa, 41.4, 14.0, xb, 46.6, 15.6))
lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
