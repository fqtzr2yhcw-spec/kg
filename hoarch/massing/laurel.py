"""Massing 113: a water-powered gristmill with the miller's house (after Mabry Mill, Blue
Ridge Parkway, Virginia, about 1910, and the mountain mills like it).

New: water and machinery. The creek runs across the front of the base, cut down below the
bank; the mill stands on the bank at the front corner with its front wall at the water, an
overshot wheel turning in the creek against it, fed over the top by a wooden flume carried on
trestles along the creek from upstream; a plank footbridge crosses to the miller's cabin, which
sits back on the bank with its porch and stone chimney. Front faces -y (revised: the wheel and
flume to the front corner, the owner's choice).
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
ZB, ZW, ZBED, ZFAR = 16.0, 7.0, 3.0, 10.0          # bank top, water, creek bed, the far (front) bank
CY0, CY1 = 12.0, 52.0                              # the creek, across the front

# the ground: the bank behind the creek, the low far bank in front, stone walls at the wheel
m.add("base", bx(0.0, CY1, 0.0, 240.0, 200.0, ZB) + bx(0.0, 0.0, 0.0, 240.0, CY0, ZFAR))
m.add("base", bx(0.0, CY0, 0.0, 240.0, CY1, ZBED))
m.add("glass", bx(0.0, CY0, ZBED, 240.0, CY1, ZW))                               # the water
for i, (c, r) in enumerate((((30.0, 20.0), 6.0), ((110.0, 46.0), 5.0), ((226.0, 30.0), 7.0), ((92.0, 16.0), 4.0))):
    m.add("base", boulder(c, r, squash=0.7, seed=20 + i).translate([0, 0, ZBED]))

# the mill on the bank at the front corner, its front wall at the creek, gable ends east and west
MX0, MX1, MY0, MY1 = 146.0, 218.0, CY1, 116.0
block(m, MX0, MY0, MX1, MY1, ZB, gable_x(MY0, MY1, ZB + 62.0, 0.75), over=4.0, rake=5.0)
m.add("chimney", bx(MX0, CY1 - 4.0, ZBED, MX1, CY1, ZB + 2.0))                    # the stone wall at the water
m.add("upper", bx(MX0 - 12, MY0 + 18, ZB, MX0, MY0 + 46, ZB + 30))              # a loading shed on the west end
m.add("roof", skin_roof([(MX0 - 14, MY0 + 16), (MX0 + 1, MY0 + 16), (MX0 + 1, MY0 + 48), (MX0 - 14, MY0 + 48)],
                        [[((MX0 - 14, 0.0), (1, 0), ZB + 30.0, 0.4)]], th=1.6))
for x in (MX0 + 8, MX1 - 18):
    m.add("glass", win_xz(x, x + 9, ZB + 10, ZB + 24, MY0))
    m.add("glass", win_xz(x, x + 9, ZB + 40, ZB + 54, MY0))
m.add("glass", win_yz(MY0 + 22, MY0 + 42, ZB, ZB + 24, MX0 - 12, out=-1))
m.add("glass", win_yz(MY0 + 26, MY0 + 36, ZB + 40, ZB + 52, MX0, out=-1))

# the overshot wheel in the creek against the mill's front, its axle into the wall
WX, WR = 196.0, 26.0
WZ, WY0, WY1 = ZBED + 28.0, CY1 - 16.0, CY1 - 4.0


def yaxis_cyl(h, r0, r1, seg=64):
    return M.cylinder(h, r0, r1, seg).rotate([-90, 0, 0])


wheel = yaxis_cyl(WY1 - WY0, WR, WR) - yaxis_cyl(WY1 - WY0 + 2, WR - 5, WR - 5).translate([0, -1, 0])
for k in range(8):
    wheel = wheel + M.cube([2.4, WY1 - WY0, 2 * WR - 4]).translate([-1.2, 0, -WR + 2]).rotate([0, 22.5 * k, 0])
wheel = wheel + yaxis_cyl(WY1 - WY0 + 8, 4.0, 4.0)
m.add("trim", wheel.translate([WX, WY0, WZ]))
# the flume along the creek from upstream (the west) on trestles to just over the wheel's top
FZ = WZ + WR + 4.0
m.add("deck", bx(0.0, WY0 - 1, FZ, WX + 2, WY1 + 1, FZ + 2.0) + bx(0.0, WY0 - 1, FZ, WX + 2, WY0 + 0.5, FZ + 6.0) +
      bx(0.0, WY1 - 0.5, FZ, WX + 2, WY1 + 1, FZ + 6.0))
for x in np.arange(12.0, WX - 30, 24.0):
    for y in (WY0 + 0.5, WY1 - 0.5):
        m.add("deck", bx(x - 1.0, y - 1.0, ZBED, x + 1.0, y + 1.0, FZ))
    m.add("deck", bx(x - 0.8, WY0 - 1, FZ - 8, x + 0.8, WY1 + 1, FZ - 6))

# the footbridge across the creek to the cabin
m.add("deck", bx(56.0, 0.0, ZFAR - 1.0, 70.0, CY1 + 4, ZB + 0.4).warp(lambda v: v) if False else
      M.hull_points([(x, y, z) for x in (56.0, 70.0) for y, z in ((2.0, ZFAR), (CY1 + 4, ZB), (2.0, ZFAR + 1.4), (CY1 + 4, ZB + 1.4))]))
for x in (56.6, 69.4):
    m.add("trim", M.hull_points([(x + dx, y, z) for dx in (-0.4, 0.4) for y, z in ((2.0, ZFAR + 6.4), (CY1 + 4, ZB + 6.4), (2.0, ZFAR + 7.2), (CY1 + 4, ZB + 7.2))]))
posts(m, [(x, y) for x in (57.0, 69.0) for y in (20.0, 40.0)], ZBED, ZFAR + 3.0, r=1.4, mat="deck")

# the miller's cabin back on the bank: a storey and a half, porch, stone end chimney
HX0, HX1, HY0, HY1 = 26.0, 90.0, 120.0, 168.0
block(m, HX0, HY0, HX1, HY1, ZB, gable_x(HY0, HY1, ZB + 30.0, 0.9), over=3.5, rake=3.0)
m.add("deck", bx(HX0, HY0 - 14, ZB - 1.0, HX1, HY0, ZB + 0.4))
posts(m, [(x, HY0 - 12.5) for x in np.linspace(HX0 + 2, HX1 - 2, 4)], ZB, ZB + 26.0, r=1.3)
m.add("roof", skin_roof([(HX0 - 2, HY0 - 16), (HX1 + 2, HY0 - 16), (HX1 + 2, HY0 + 1), (HX0 - 2, HY0 + 1)],
                        [[((0.0, HY0 - 16), (0, 1), ZB + 25.0, 0.35)]], th=1.6))
m.add("chimney", bx(HX0 - 9, 136.0, ZB, HX0 + 1, 152.0, ZB + 28) + bx(HX0 - 7, 139.0, ZB + 28, HX0 + 1, 149.0, ZB + 62))
m.add("glass", win_xz(HX0 + 26, HX0 + 36, ZB, ZB + 22, HY0))
for x in (HX0 + 8, HX1 - 16):
    m.add("glass", win_xz(x, x + 9, ZB + 6, ZB + 20, HY0))
m.add("glass", win_yz(132.0, 142.0, ZB + 34, ZB + 44, HX1, out=1))
# paths: footbridge to the cabin and along the bank to the mill; a millstone by the mill door
m.add("deck", bx(57.0, CY1 + 4, ZB, 69.0, HY0 - 14, ZB + 0.6) + bx(69.0, 76.0, ZB, MX0 - 12, 86.0, ZB + 0.6))
m.add("base", yaxis_cyl(3.0, 9.0, 9.0).rotate([0, 0, 90]).translate([MX0 - 16, MY0 + 10, ZB + 9.0]))
lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
