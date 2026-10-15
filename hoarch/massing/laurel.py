"""Massing 113: a water-powered gristmill with the miller's house (after Mabry Mill, Blue
Ridge Parkway, Virginia, about 1910, and the mountain mills like it).

New: water and machinery. The base is a stream bank with the creek cut down into it; the mill
stands on the bank with its end wall over the creek, an overshot wheel turning in a stone
wheel pit, fed over the top by a wooden flume carried on trestles from upstream; a plank
footbridge crosses the creek; the miller's cabin with its porch and stone chimney sits back on
the bank. Front faces -y.
"""
import math
import sys
sys.path.insert(0, sys.argv[1])
from mk import (Model, bx, block, gable_x, gable_y, posts, stack, rail_x, rail_y, win_xz, win_yz, skin_roof, roof,
                rect_fp, boulder)
from manifold3d import Manifold as M
import numpy as np

OUT = sys.argv[2]
m = Model()
ZB, ZW, ZBED = 16.0, 7.0, 3.0                    # bank top, water surface, creek bed
CX0, CX1 = 168.0, 214.0                          # the creek

# the ground: the bank on both sides of the creek, stone walls lining the wheel pit
m.add("base", bx(0.0, 10.0, 0.0, CX0, 200.0, ZB) + bx(CX1, 10.0, 0.0, 240.0, 200.0, ZB))
m.add("base", bx(CX0, 10.0, 0.0, CX1, 200.0, ZBED))
m.add("glass", bx(CX0, 10.0, ZBED, CX1, 200.0, ZW))                             # the water
m.add("chimney", bx(CX0, 72.0, ZBED, CX0 + 4.0, 128.0, ZB + 2.0) + bx(CX0 + 22.0, 72.0, ZBED, CX0 + 26.0, 128.0, ZB + 2.0))
for i, (c, r) in enumerate((((CX1 + 4, 40.0), 6.0), ((CX0 + 6, 160.0), 5.0), ((CX1 - 3, 176.0), 7.0), ((CX0 + 3, 30.0), 4.0))):
    m.add("base", boulder(c, r, squash=0.7, seed=20 + i).translate([0, 0, ZBED]))

# the mill: two storeys of boards on the bank, its gable to the creek
MX0, MX1, MY0, MY1 = 92.0, CX0, 70.0, 130.0
block(m, MX0, MY0, MX1, MY1, ZB, gable_x(MY0, MY1, ZB + 62.0, 0.75), over=4.0, rake=5.0)
m.add("base", bx(MX0 - 1, MY0 - 1, ZB - 2, MX1, MY1 + 1, ZB + 2))
m.add("upper", bx(MX0 + 14, MY0 - 12, ZB, MX0 + 40, MY0, ZB + 30))               # a loading shed on the front
m.add("roof", skin_roof([(MX0 + 12, MY0 - 14), (MX0 + 42, MY0 - 14), (MX0 + 42, MY0 + 1), (MX0 + 12, MY0 + 1)],
                        [[((0.0, MY0 - 14), (0, 1), ZB + 30.0, 0.4)]], th=1.6))
for x in (MX0 + 8, MX1 - 22):
    m.add("glass", win_xz(x, x + 9, ZB + 10, ZB + 24, MY0))
    m.add("glass", win_xz(x, x + 9, ZB + 40, ZB + 54, MY0))
m.add("glass", win_xz(MX0 + 20, MX0 + 34, ZB, ZB + 24, MY0 - 12))
m.add("glass", win_yz(94.0, 104.0, ZB + 44, ZB + 56, MX1, out=1))
m.add("glass", win_yz(94.0, 106.0, ZB + 72, ZB + 82, MX1, out=1))

# the overshot wheel in the pit, its axle into the mill
WC, WR, WX0, WX1 = (100.0, ZBED + 30.0), 28.0, CX0 + 6.0, CX0 + 18.0


def xaxis_cyl(h, r0, r1, seg=64):
    return M.cylinder(h, r0, r1, seg).rotate([0, 90, 0])


wheel = xaxis_cyl(WX1 - WX0, WR, WR) - xaxis_cyl(WX1 - WX0 + 2, WR - 5, WR - 5).translate([-1, 0, 0])
for k in range(8):
    wheel = wheel + M.cube([WX1 - WX0, 2.4, 2 * WR - 4]).translate([0, -1.2, -WR + 2]).rotate([22.5 * k, 0, 0])
wheel = wheel + xaxis_cyl(WX1 - WX0 + 10, 4.0, 4.0).translate([-8, 0, 0])
m.add("trim", wheel.translate([WX0, WC[0], WC[1]]))
# the flume on trestles, from upstream (the back) to just over the wheel's top
FZ = WC[1] + WR + 4.0
m.add("deck", bx(WX0 - 1, WC[0] - 2, FZ, WX1 + 1, 200.0, FZ + 2.0) +
      bx(WX0 - 1, WC[0] - 2, FZ, WX0 + 0.5, 200.0, FZ + 6.0) + bx(WX1 - 0.5, WC[0] - 2, FZ, WX1 + 1, 200.0, FZ + 6.0))
for y in np.arange(WC[0] + 34, 200.0, 22.0):
    for x in (WX0 + 0.5, WX1 - 0.5):
        m.add("deck", bx(x - 1.0, y - 1.0, ZBED, x + 1.0, y + 1.0, FZ))
    m.add("deck", bx(WX0 - 1, y - 0.8, FZ - 8, WX1 + 1, y + 0.8, FZ - 6))

# the footbridge across the creek in front
m.add("deck", bx(CX0 - 6, 34.0, ZB - 1.0, CX1 + 6, 48.0, ZB + 0.4))
rail_x(m, CX0 - 6, CX1 + 6, 34.6, ZB + 0.4, h=6.0)
rail_x(m, CX0 - 6, CX1 + 6, 47.4, ZB + 0.4, h=6.0)
posts(m, [(x, y) for x in (CX0 + 12, CX1 - 12) for y in (36.0, 46.0)], ZBED, ZB - 1.0, r=1.4, mat="deck")

# the miller's cabin back on the bank: a storey and a half, porch, stone end chimney
HX0, HX1, HY0, HY1 = 18.0, 78.0, 118.0, 166.0
block(m, HX0, HY0, HX1, HY1, ZB, gable_x(HY0, HY1, ZB + 30.0, 0.9), over=3.5, rake=3.0)
m.add("deck", bx(HX0, HY0 - 14, ZB - 1.0, HX1, HY0, ZB + 0.4))
posts(m, [(x, HY0 - 12.5) for x in np.linspace(HX0 + 2, HX1 - 2, 4)], ZB, ZB + 26.0, r=1.3)
m.add("roof", skin_roof([(HX0 - 2, HY0 - 16), (HX1 + 2, HY0 - 16), (HX1 + 2, HY0 + 1), (HX0 - 2, HY0 + 1)],
                        [[((0.0, HY0 - 16), (0, 1), ZB + 25.0, 0.35)]], th=1.6))
m.add("chimney", bx(HX0 - 9, 134.0, ZB, HX0 + 1, 150.0, ZB + 28) + bx(HX0 - 7, 137.0, ZB + 28, HX0 + 1, 147.0, ZB + 62))
m.add("glass", win_xz(HX0 + 24, HX0 + 34, ZB, ZB + 22, HY0))
for x in (HX0 + 8, HX1 - 16):
    m.add("glass", win_xz(x, x + 9, ZB + 6, ZB + 20, HY0))
m.add("glass", win_yz(130.0, 140.0, ZB + 34, ZB + 44, HX1, out=1))
# a millstone leaning by the door, a path from the cabin to the mill
m.add("base", xaxis_cyl(3.0, 9.0, 9.0).rotate([0, 0, 90]).rotate([0, 0, 0]).translate([MX0 + 50, MY0 - 8, ZB + 9.0]))
m.add("deck", bx(HX1 - 10, 60.0, ZB, MX0 + 20, 70.0, ZB + 0.6) + bx(HX1 - 10, 60.0, ZB, HX1, HY0 - 14, ZB + 0.6))
lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
