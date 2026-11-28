"""Massing 107: a New Orleans camelback shotgun double (after the camelback doubles of the
Faubourg Marigny and Bywater, 1880s-90s).

New: the section. One storey across the street front, a full second storey only at the back
(the "camelback", built so the house was taxed as one storey), rising behind the front hip
roof. Two houses in one: a double front of door, two tall floor-length windows and door,
under a deep gallery on turned columns with a bracketed frieze; the whole raised on brick piers
with steps to each door. Long and narrow, the way the lots are. Front faces -y.
"""
import sys
sys.path.insert(0, sys.argv[1])
from mk import Model, bx, block, hip, gable_x, posts, stack, rail_x, rail_y, win_xz, win_yz, skin_roof, steps_y
from manifold3d import Manifold as M
import numpy as np

OUT = sys.argv[2]
m = Model()
ZF = 12.0                                         # raised on piers
X0, X1 = 60.0, 168.0                              # 108 wide (31 ft)
YG, Y0, YC, Y1 = 22.0, 42.0, 150.0, 228.0         # gallery front, front wall, the camel's front, back wall
Z1, Z2, SL = 52.0, 86.0, 0.72

# the one-storey front house, hipped; the two-storey camelback behind, hipped higher
block(m, X0, Y0, X1, YC + 2, ZF, hip(X0, Y0, X1, YC + 2, Z1, SL), over=4.0)
block(m, X0 + 4, YC, X1 - 4, Y1, ZF, hip(X0 + 4, YC, X1 - 4, Y1, Z2, SL), over=4.0)
m.add("wall", bx(X0, YC, ZF, X1, Y1, Z1))                                         # its lower storey, full width
m.add("trim", bx(X0 + 4, YC - 0.6, Z1 + 2, X1 - 4, YC, Z1 + 4))
# brick piers and the lattice skirt between them (dark)
for x in np.linspace(X0 + 3, X1 - 3, 6):
    for y in np.linspace(Y0 + 3, Y1 - 3, 9):
        m.add("base", bx(x - 3, y - 3, 0, x + 3, y + 3, ZF))
m.add("shadow", bx(X0 + 0.5, Y0 + 0.5, 0, X1 - 0.5, Y1 - 0.5, ZF - 1))

# the gallery across the front: floor on piers, four turned columns, a deep bracketed frieze,
# its own low hip roof under the main eave
m.add("deck", bx(X0 - 2, YG, ZF - 1.2, X1 + 2, Y0, ZF))
for x in np.linspace(X0, X1, 4):
    m.add("base", bx(x - 3, YG, 0, x + 3, YG + 6, ZF - 1.2))
posts(m, [(x, YG + 2.5) for x in np.linspace(X0 + 1, X1 - 1, 4)], ZF, 46.0, r=1.8)
m.add("trim", bx(X0 - 2, YG, 42.0, X1 + 2, YG + 3, 47.0))                         # the frieze
m.add("roof", skin_roof([(X0 - 3, YG - 3), (X1 + 3, YG - 3), (X1 + 3, Y0 + 1), (X0 - 3, Y0 + 1)],
                        [[((0.0, YG - 3), (0, 1), 46.0, 0.35), ((X0 - 3, 0.0), (1, 0), 46.0, 0.35), ((X1 + 3, 0.0), (-1, 0), 46.0, 0.35)]], th=1.8))
rail_x(m, X0 + 14, X1 - 14, YG + 2.5, ZF, h=6.0)
for xd in (X0 + 8.0, X1 - 8.0):                                                   # steps to each door
    steps_y(m, xd - 7, xd + 7, YG, ZF, 4)

# the double front: door, two floor-length windows, door; side windows; the camel's windows
for x, kind in ((X0 + 8, "door"), (X0 + 38, "win"), (X1 - 38, "win"), (X1 - 8, "door")):
    m.add("glass", win_xz(x - 6, x + 6, ZF + (0 if kind == "door" else 1), 44.0, Y0))
    m.add("shadow", bx(x - 11.5, Y0 - 0.6, ZF + 2, x - 6.5, Y0, 44.0) + bx(x + 6.5, Y0 - 0.6, ZF + 2, x + 11.5, Y0, 44.0))  # shutters
for y in np.linspace(Y0 + 16, Y1 - 24, 6):
    m.add("glass", win_yz(y, y + 10, ZF + 4, 44.0, X0, out=-1))
    m.add("glass", win_yz(y, y + 10, ZF + 4, 44.0, X1, out=1))
for x in (X0 + 22, X1 - 32):
    m.add("glass", win_xz(x, x + 10, 60.0, 78.0, YC))
for y in (YC + 16, YC + 48):
    m.add("glass", win_yz(y, y + 10, 60.0, 78.0, X0 + 4, out=-1))
    m.add("glass", win_yz(y, y + 10, 60.0, 78.0, X1 - 4, out=1))
for x in (X0 + 22, X1 - 32):
    m.add("glass", win_xz(x, x + 10, 60.0, 78.0, Y1, out=1))
    m.add("glass", win_xz(x, x + 10, ZF + 4, 44.0, Y1, out=1))
# chimneys: two on the front house (one per side), one on the camel
for x in (X0 + 30, X1 - 30):
    stack(m, x, 96.0, 7, 12, 60, 86)
stack(m, (X0 + X1) / 2, YC + 30, 7, 12, 96, 118)
# a back gallery under the camel's upper storey, with its stair
m.add("deck", bx(X0, Y1, ZF - 1.2, X1, Y1 + 14, ZF))
posts(m, [(x, Y1 + 12.5) for x in np.linspace(X0 + 1, X1 - 1, 4)], ZF, Z1, r=1.4)
m.add("roof", bx(X0 - 1, Y1, Z1, X1 + 1, Y1 + 15, Z1 + 1.6))
lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
