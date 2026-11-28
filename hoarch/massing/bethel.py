"""Massing 105: three camp-meeting cottages round a little green (after the cottages of the
Wesleyan Grove camp ground, Oak Bluffs, Martha's Vineyard, 1860s-70s).

New: a group, not a house: three tall, narrow cottages on one base, set on an arc so they face
a shared green, a boardwalk path following the arc in front of them. Each is a steep front
gable a storey and a half high, with Gothic double doors below and a door onto a balcony above
the porch; each has a different side: one plain, one with a one-storey side ell, one with a
two-tier porch under its own little gable. Front of the group faces -y.
"""
import math
import sys
sys.path.insert(0, sys.argv[1])
from mk import Model, bx, block, gable_y, gable_x, posts, stack, rail_x, rail_y, win_xz, win_yz, skin_roof, roof, rect_fp
from manifold3d import Manifold as M, CrossSection as CS
from hoarch.core import union, slab, poly
import numpy as np

OUT = sys.argv[2]
m = Model()
ZF = 6.0
W, D = 46.0, 84.0                     # each cottage: 46 wide (13 ft), 84 deep
ZE, SL = 44.0, 1.55                   # a storey and a half: the eave low, the gable steep


def cottage(kind):
    c = Model()
    x0, x1 = -W / 2, W / 2
    block(c, x0, 0.0, x1, D, ZF, gable_y(x0, x1, ZE, SL), over=3.5, rake=4.0)
    c.add("base", bx(x0 - 1, -1, 0.0, x1 + 1, D + 1, ZF))
    # porch across the front, its roof the balcony floor; railing on the balcony
    zb = 34.0
    c.add("deck", bx(x0 - 1, -14.0, ZF - 1.0, x1 + 1, 0.0, ZF))
    posts(c, [(x0 + 0.5, -13.0), (-8.0, -13.0), (8.0, -13.0), (x1 - 0.5, -13.0)], ZF, zb)
    c.add("deck", bx(x0 - 1.5, -15.0, zb, x1 + 1.5, 0.0, zb + 1.6))
    rail_x(c, x0 - 1, x1 + 1, -14.2, zb + 1.6, h=5.0)
    rail_y(c, -14.2, 0.0, x0 - 1, zb + 1.6, h=5.0)
    rail_y(c, -14.2, 0.0, x1 + 1, zb + 1.6, h=5.0)
    # Gothic double doors below, a pointed door onto the balcony above, a pointed light in the peak
    c.add("glass", win_xz(-8.0, 8.0, ZF, 30.0, 0.0, head="pointed"))
    c.add("glass", win_xz(-6.0, 6.0, zb + 1.6, zb + 24.0, 0.0, head="pointed"))
    c.add("glass", win_xz(-3.0, 3.0, ZE + 22.0, ZE + 32.0, 0.0, head="pointed"))
    for y in (22.0, 56.0):
        c.add("glass", win_yz(y, y + 9.0, 14.0, 30.0, x0, out=-1, head="pointed"))
        c.add("glass", win_yz(y, y + 9.0, 14.0, 30.0, x1, out=1, head="pointed"))
    c.add("trim", M.cylinder(8.0, 0.9, 0.3, 8).translate([0.0, -3.0, ZE + SL * W / 2 + 1.0]))           # finial
    stack(c, x1 - 9.0, D - 16.0, 6.0, 5.0, ZE, ZE + SL * 14.0 + 8.0)
    if kind == "ell":                     # a one-storey side ell with its own gable to the front
        block(c, x0 - 20.0, 30.0, x0, 74.0, ZF, gable_y(x0 - 20.0, x0, 30.0, 1.1), over=3.0)
        c.add("base", bx(x0 - 21.0, 29.0, 0.0, x0, 75.0, ZF))
        c.add("glass", win_xz(x0 - 15.0, x0 - 5.0, 12.0, 26.0, 30.0, head="pointed"))
    if kind == "tiers":                   # a two-tier porch under its own little gable
        c.parts["deck"] = [s for s in c.parts["deck"] if s.bounding_box()[2] < zb - 1]
        c.parts["trim"] = [s for s in c.parts["trim"] if s.bounding_box()[2] < zb]
        c.add("deck", bx(x0 - 1.5, -15.0, zb, x1 + 1.5, 0.0, zb + 1.6))
        posts(c, [(x0 + 0.5, -13.0), (x1 - 0.5, -13.0)], zb + 1.6, 58.0)
        rail_x(c, x0 - 1, x1 + 1, -14.2, zb + 1.6, h=5.0)
        c.add("roof", skin_roof([(x0 - 3, -17.0), (x1 + 3, -17.0), (x1 + 3, 1.0), (x0 - 3, 1.0)],
                                gable_y(x0 - 3, x1 + 3, 58.0, 1.2), th=1.8))
        c.add("trim", M.cylinder(8.0, 0.9, 0.3, 8).translate([0.0, -15.0, 58.0 + 1.2 * 26 + 1.0]))
        c.add("upper", roof([(x0 - 1, -15.5), (x1 + 1, -15.5), (x1 + 1, -14.5), (x0 - 1, -14.5)], 58.0,
                            gable_y(x0 - 1, x1 + 1, 58.0, 1.2)))                       # its gable face (open below)
        c.add("glass", win_xz(-4.0, 4.0, 62.0, 74.0, -15.6, head="round"))
    if kind == "plain":                   # a side bay window
        c.add("wall", bx(x1, 34.0, ZF, x1 + 6.0, 52.0, 30.0))
        c.add("roof", bx(x1, 33.0, 30.0, x1 + 7.0, 53.0, 32.0))
        c.add("glass", win_yz(37.0, 49.0, 12.0, 27.0, x1 + 6.0, out=1))
    return c


C = (124.0, -40.0)
R = 130.0
for kind, th in (("ell", 115.0), ("tiers", 90.0), ("plain", 65.0)):
    c = cottage(kind)
    ph = math.radians(th - 90.0)
    px, py = C[0] + R * math.cos(math.radians(th)), C[1] + R * math.sin(math.radians(th))
    A = [[math.cos(ph), -math.sin(ph), 0, px], [math.sin(ph), math.cos(ph), 0, py], [0, 0, 1, 0]]
    for mat, ss in c.parts.items():
        for s_ in ss:
            m.add(mat, s_.transform(A))

# the boardwalk following the arc in front of the cottages, and the green inside it
ring = M.cylinder(1.2, R - 16.0, R - 16.0, 160).translate([C[0], C[1], 0]) - \
    M.cylinder(4.0, R - 28.0, R - 28.0, 160).translate([C[0], C[1], -1])
sector = slab(poly([C, (C[0] + 400 * math.cos(math.radians(20)), C[1] + 400 * math.sin(math.radians(20))),
                    (C[0], C[1] + 400), (C[0] + 400 * math.cos(math.radians(160)), C[1] + 400 * math.sin(math.radians(160)))]), -2, 10)
m.add("deck", ring ^ sector)
lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
