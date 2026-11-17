"""Massing 104: a hillside house in a river town (after the brick houses on the bluffs of
Galena, Illinois, 1840s-50s).

New: the ground. The house is set into a slope: three storeys at the street (a stone walk-out
storey under two of brick) and two at the back, where the hill has climbed a storey. A stone
retaining wall along the street with a flight of steps up to a front terrace; a stone stair
climbing along the front wall to the door on the main floor; stepped garden terraces down the
east side; parapeted gable ends with paired chimneys, Federal style. Front faces -y.
"""
import sys
sys.path.insert(0, sys.argv[1])
from mk import Model, bx, block, gable_x, posts, stack, rail_x, rail_y, steps_y, win_xz, win_yz, roof, rect_fp, below
from manifold3d import Manifold as M
from hoarch.core import union
import numpy as np

OUT = sys.argv[2]
m = Model()
X0, X1, Y0, Y1 = 40.0, 180.0, 60.0, 140.0        # the house, 140 x 80
ZT, ZM, S2, ZE = 18.0, 50.0, 82.0, 112.0           # terrace, main floor, second floor, eave
YW = 30.0                                          # the street's retaining wall
SL = 0.7

# the ground: street wall and terrace, the hill behind, the slope down the west side, terraces east
g = []
g.append(bx(0.0, YW, 0.0, 230.0, Y0 + 1, ZT))                                   # the front terrace
g.append(bx(0.0, Y1 - 1, 0.0, 230.0, 200.0, ZM))                                # the back garden, a storey up
g.append(roof(rect_fp(0.0, Y0, X0, Y1), 0.0, [[((0.0, Y0), (0, 1), ZT, (ZM - ZT) / (Y1 - Y0))]]))   # west bank
for (ya, yb, z) in ((Y0, 87.0, ZT + 8), (87.0, 114.0, ZT + 19), (114.0, Y1, ZM - 2)):              # east terraces
    g.append(bx(X1, ya, 0.0, 230.0, yb + 0.01, z))
g.append(bx(X0, Y0, 0.0, X1, Y1, ZT))
m.add("base", union(g))
for (yb, z) in ((87.0, ZT + 8), (114.0, ZT + 19)):                                                # their wall copings
    m.add("trim", bx(X1, yb - 1.2, z, 230.0, yb, z + 1.2))
m.add("trim", bx(0.0, YW, ZT, 230.0, YW + 1.6, ZT + 1.6))                                         # street wall coping
steps_y(m, 100.0, 120.0, YW, ZT, 7, toward=-1)                                                    # steps up from the street
for x in (99.0, 121.0):
    m.add("trim", bx(x - 1.5, YW - 1.5, ZT, x + 1.5, YW + 1.5, ZT + 6.0))                          # gate piers

# the house: a stone walk-out storey toward the street, two of brick, a side-gabled roof between
# parapeted ends with paired chimneys
m.add("base", bx(X0, Y0, ZT, X1, Y1, ZM))                                                         # the stone storey
m.add("trim", bx(X0 - 0.8, Y0 - 0.8, ZM - 1.6, X1 + 0.8, Y1 + 0.8, ZM))                           # water table
block(m, X0, Y0, X1, Y1, ZM, gable_x(Y0, Y1, ZE, SL), over=3.0, rake=-1.0)
for x in (X0, X1 - 4.0):                                                                          # parapet gable ends
    m.add("wall", roof(rect_fp(x, Y0 - 0.5, x + 4.0, Y1 + 0.5), ZM, gable_x(Y0 - 0.5, Y1 + 0.5, ZE + 3.0, SL)))
    for y in (Y0 + 18.0, Y1 - 18.0):
        stack(m, x + 2.0, y, 4.0, 10.0, ZE + 10, ZE + 3.0 + SL * 40 + 4.0)
m.add("trim", bx(X0, Y0 - 1.2, ZE - 4.0, X1, Y0, ZE) + bx(X0, Y1, ZE - 4.0, X1, Y1 + 1.2, ZE))      # plain cornices

# the stone stair along the front wall to the main-floor door, its landing and rail
XS0, XD = 66.0, 108.0
n = 11
for k in range(n):
    z = ZT + (k + 1) * (ZM - ZT) / n
    x = XS0 + k * (XD - XS0 - 14.0) / n
    m.add("base", bx(x, Y0 - 13.0, ZT, XD - 14.0 + 0.01, Y0, z))
m.add("base", bx(XD - 14.0, Y0 - 13.0, ZT, XD + 14.0, Y0, ZM))                                    # the landing
xa, xb = XS0, XD - 14.0                                                                             # the sloped handrail
m.add("trim", M.hull_points([(x, y, z + dz) for x, z in ((xa, ZT + 8.0), (xb, ZM + 8.0)) for y in (Y0 - 13.4, Y0 - 12.6) for dz in (0.0, 0.8)]))
for k in range(0, n + 1, 2):
    x = XS0 + k * (XD - XS0 - 14.0) / n
    z = ZT + k * (ZM - ZT) / n
    m.add("trim", bx(x - 0.5, Y0 - 13.4, z, x + 0.5, Y0 - 12.6, z + 8.0))
rail_x(m, XD - 14.0, XD + 14.0, Y0 - 13.0, ZM, h=8.0)
m.add("glass", win_xz(XD - 6.0, XD + 6.0, ZM, ZM + 24.0, Y0))                                     # the front door

# windows: three storeys at the front, two at the back; the walk-out door to the terrace
for x in (52.0, 76.0, 130.0, 154.0):
    if x != 76.0:
        m.add("glass", win_xz(x, x + 11.0, ZT + 8.0, ZT + 26.0, Y0))
    m.add("glass", win_xz(x, x + 11.0, ZM + 6.0, ZM + 26.0, Y0))
    m.add("glass", win_xz(x, x + 11.0, S2 + 6.0, S2 + 24.0, Y0))
    m.add("glass", win_xz(x, x + 11.0, ZM + 6.0, ZM + 26.0, Y1, out=1))
    m.add("glass", win_xz(x, x + 11.0, S2 + 6.0, S2 + 24.0, Y1, out=1))
m.add("glass", win_xz(102.0, 114.0, ZT, ZT + 24.0, Y0 - 13.0 if False else Y0))                     # under the landing
m.add("shadow", bx(100.0, Y0 - 12.6, ZT, 116.0, Y0 - 0.2, ZT + 26.0))                             # the arch under the landing
for y in (80.0, 112.0):
    m.add("glass", win_yz(y, y + 11.0, ZM + 6.0, ZM + 26.0, X0, out=-1))
    m.add("glass", win_yz(y, y + 11.0, S2 + 6.0, S2 + 24.0, X1, out=1))
m.add("glass", win_xz(102.0, 114.0, ZM, ZM + 24.0, Y1, out=1))                                     # back door to the garden

# a small rear porch onto the garden
m.add("deck", bx(96.0, Y1, ZM, 120.0, Y1 + 12.0, ZM + 1.0))
posts(m, [(97.5, Y1 + 10.5), (118.5, Y1 + 10.5)], ZM + 1.0, ZM + 30.0)
m.add("roof", bx(94.0, Y1, ZM + 30.0, 122.0, Y1 + 14.0, ZM + 32.0))
lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
