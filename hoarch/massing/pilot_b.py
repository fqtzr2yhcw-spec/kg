"""Massing pilot B: a plain Federal brick house wrapped in a standing Gothic skeleton, joined
through a carriage-arch link to a matching barn (after the Wedding Cake House, Kennebunk ME,
built 1826 and dressed in Gothic in 1852-55).

The new ideas: the ornament is a separate outer frame, not a skin: stepped buttresses rising
from the ground between every bay to pinnacles above the eave, with pointed-arch screens hung
between them in front of the cornice; a Gothic entrance porch; a one-storey link with a
pointed carriage arch running front to back; a gable-front barn dressed the same way, with a
pointed hay door and a cupola. Front faces -y.
"""
import math
import sys

import numpy as np

sys.path.insert(0, sys.argv[1])
from mk import (Model, bx, below, roof, skin_roof, cone, ring, win_xz, win_yz, xz_panel, yz_panel, pointed,
                round_head)
from hoarch.core import poly, slab, union, offset, cs_union
from manifold3d import Manifold as M

OUT = sys.argv[2]
m = Model()
ZF, S1, ZE = 8.0, 42.0, 76.0
HX0, HX1, HY0, HY1 = 12.0, 132.0, 18.0, 108.0
HS = 0.5

# ---------------------------------------------------------------- the Federal block, low hip roof
hip = [[((HX0, 0.0), (1, 0), ZE, HS), ((HX1, 0.0), (-1, 0), ZE, HS),
        ((0.0, HY0), (0, 1), ZE, HS), ((0.0, HY1), (0, -1), ZE, HS)]]
m.add("roof", skin_roof([(HX0 - 3, HY0 - 3), (HX1 + 3, HY0 - 3), (HX1 + 3, HY1 + 3), (HX0 - 3, HY1 + 3)], hip, th=2.4))
house = bx(HX0, HY0, ZF, HX1, HY1, ZE)
m.add("wall", house)
m.add("trim", bx(HX0 - 1.2, HY0 - 1.2, ZE - 5.0, HX1 + 1.2, HY1 + 1.2, ZE))           # the plain cornice behind
for cx, cy in ((22.0, 32.0), (22.0, 94.0), (122.0, 32.0), (122.0, 94.0)):
    m.add("chimney", bx(cx - 5, cy - 3, 70, cx + 5, cy + 3, 112) + bx(cx - 6, cy - 4, 109, cx + 6, cy + 4, 112))


# ---------------------------------------------------------------- the Gothic skeleton
def pinnacle_x(x, y_face, out=-1, z_top=88.0, spire=14.0, w=4.4):
    """A stepped buttress standing off a wall at y_face (out = -1: in front, toward -y), rising
    to a pinnacle shaft and spire above the eave."""
    d = out
    parts = []
    steps = [(0.0, 22.0, 6.0, w + 1.6), (22.0, 50.0, 4.8, w + 0.8), (50.0, z_top, 3.6, w)]
    for z0, z1, depth, ww in steps:
        ya, yb = sorted((y_face, y_face + d * depth))
        parts.append(bx(x - ww / 2, ya, z0, x + ww / 2, yb, z1))
        # weathering: a sloped cap on each step
        if z1 < z_top:
            parts.append(below(bx(x - ww / 2, ya, z1, x + ww / 2, yb, z1 + 3.0),
                               (x, y_face + d * depth), (0, -d), z1, 3.0 / depth * 0.9))
    yc = y_face + d * 1.8
    parts.append(bx(x - 1.9, yc - 1.9, z_top, x + 1.9, yc + 1.9, z_top + 6.0))
    parts.append(M.cylinder(spire, 2.6, 0.0, 4).rotate([0, 0, 45]).translate([x, yc, z_top + 6.0]))
    return union(parts)


def pinnacle_y(y, x_face, out=1, **kw):
    """The same on a side wall at x_face (out = +1: toward +x)."""
    p = pinnacle_x(0.0, 0.0, out=-1, **kw)
    # rotate the local frame: local -y (outward) -> world out*x
    ang = 90.0 if out > 0 else -90.0
    return p.rotate([0, 0, ang]).translate([x_face, y, 0])


def screen_xz(x0, x1, y_face, out=-1, z0=62.0, z1=90.0, gap=3.0, t=1.4):
    """A pointed-arch screen hung between two pinnacles in front of a wall (no tracery yet)."""
    yA = y_face + out * gap
    ya, yb = sorted((yA, yA + out * t))
    panel = xz_panel([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], ya, yb)
    hole = xz_panel(pointed(x0 + 2.0, x1 - 2.0, z0 - 1.0, z1 - 6.0 - (x1 - x0 - 4.0) * 0.86), ya - 1, yb + 1)
    return panel - hole


def screen_yz(y0, y1, x_face, out=1, z0=62.0, z1=90.0, gap=3.0, t=1.4):
    xA = x_face + out * gap
    xa, xb = sorted((xA, xA + out * t))
    panel = yz_panel([(y0, z0), (y1, z0), (y1, z1), (y0, z1)], xa, xb)
    hole = yz_panel(pointed(y0 + 2.0, y1 - 2.0, z0 - 1.0, z1 - 6.0 - (y1 - y0 - 4.0) * 0.86), xa - 1, xb + 1)
    return panel - hole


FX = [HX0 + 1.0, 36.0, 60.0, 84.0, 108.0, HX1 - 1.0]
for x in FX:
    m.add("trim", pinnacle_x(x, HY0, out=-1))
for a, b in zip(FX[:-1], FX[1:]):
    m.add("trim", screen_xz(a, b, HY0, out=-1))
SY = [HY0 + 1.0, 48.0, 78.0, HY1 - 1.0]
for y in SY[1:-1]:
    m.add("trim", pinnacle_y(y, HX0, out=-1))
    m.add("trim", pinnacle_y(y, HX1, out=1))
for a, b in zip(SY[:-1], SY[1:]):
    m.add("trim", screen_yz(a, b, HX0, out=-1))
    m.add("trim", screen_yz(a, b, HX1, out=1))
for x in (HX0 + 1.0, HX1 - 1.0):
    m.add("trim", pinnacle_x(x, HY1, out=1))

# ---------------------------------------------------------------- Gothic entrance porch
m.add("trim", xz_panel([(60.0, ZF), (84.0, ZF), (84.0, 50.0), (60.0, 50.0)], 6.0, 8.0)
      - xz_panel(pointed(64.0, 80.0, ZF - 1, 34.0), 5.0, 9.0))
for x in (61.5, 82.5):
    m.add("trim", bx(x - 1.8, 6.0, ZF, x + 1.8, 18.0, 52.0) + M.cylinder(12.0, 2.0, 0.0, 4).rotate([0, 0, 45]).translate([x, 7.6, 52.0]))
PR = [[((60.0, 0.0), (1, 0), 49.0, 1.5), ((84.0, 0.0), (-1, 0), 49.0, 1.5)]]
m.add("roof", skin_roof([(59.0, 5.0), (85.0, 5.0), (85.0, 19.0), (59.0, 19.0)], PR, th=1.8))
m.add("deck", bx(62, 0, 0, 82, 8, 4.0) + bx(64, 0, 0, 80, 3, 2.0) - bx(0, 0, 0, 1, 1, 1))

# ---------------------------------------------------------------- link with a carriage arch
LX0, LX1, LY0, LY1, LZ = HX1, 162.0, 34.0, 96.0, 44.0
link_roof = [[((0.0, LY0), (0, 1), LZ, 0.9), ((0.0, LY1), (0, -1), LZ, 0.9)]]
m.add("roof", skin_roof([(LX0 - 2, LY0 - 3), (LX1 + 2, LY0 - 3), (LX1 + 2, LY1 + 3), (LX0 - 2, LY1 + 3)], link_roof, th=2.2))
CAR = pointed(137.0, 157.0, -1.0, 22.0)
link = roof([(LX0, LY0), (LX1, LY0), (LX1, LY1), (LX0, LY1)], ZF, link_roof) - xz_panel(CAR, LY0 - 4, LY1 + 4)
m.add("wall", link)
m.add("trim", screen_xz(LX0 + 2.0, LX1 - 2.0, LY0, out=-1, z0=34.0, z1=52.0))
m.add("trim", pinnacle_x(LX1 - 2.0, LY0, out=-1, z_top=56.0, spire=10.0, w=3.6))
m.add("deck", bx(134, 0, 0, 160, 110, 0.6))                                    # the drive through the arch

# ---------------------------------------------------------------- the barn
BX0, BX1, BY0, BY1, BZ = 162.0, 232.0, 14.0, 110.0, 58.0
BS = 1.25
barn_roof = [[((BX0, 0.0), (1, 0), BZ, BS), ((BX1, 0.0), (-1, 0), BZ, BS)]]
m.add("roof", skin_roof([(BX0 - 4, BY0 - 4), (BX1 + 4, BY0 - 4), (BX1 + 4, BY1 + 4), (BX0 - 4, BY1 + 4)], barn_roof, th=2.4))
barn = roof([(BX0, BY0), (BX1, BY0), (BX1, BY1), (BX0, BY1)], 3.0, barn_roof)
HAY = pointed(182.0, 212.0, 2.0, 30.0)
barn = barn - xz_panel(HAY, BY0 - 1, BY0 + 3)
m.add("upper", barn)
m.add("shadow", xz_panel(HAY, BY0 + 2.6, BY0 + 3.0))
m.add("glass", win_xz(190.0, 204.0, 66.0, 84.0, BY0, head="pointed"))
CX, CY = (BX0 + BX1) / 2, 62.0
zr = BZ + BS * (BX1 - BX0) / 2
m.add("upper", bx(CX - 7, CY - 7, zr - 12, CX + 7, CY + 7, zr + 14))
m.add("roof", M.cylinder(14.0, 11.5, 0.0, 4).rotate([0, 0, 45]).translate([CX, CY, zr + 14]))
m.add("trim", cone((CX, CY), 1.2, zr + 26.0, 8.0, 12, 0.2))
for x in (BX0 + 2.0, BX1 - 2.0):
    m.add("trim", pinnacle_x(x, BY0, out=-1, z_top=70.0, spire=12.0, w=4.0))
    m.add("trim", pinnacle_x(x, BY1, out=1, z_top=70.0, spire=12.0, w=4.0))
m.add("trim", bx(CX - 2.2, BY0 - 5.0, zr - 4, CX + 2.2, BY0 - 0.6, zr + 8) +
      M.cylinder(12.0, 3.0, 0.0, 4).rotate([0, 0, 45]).translate([CX, BY0 - 2.8, zr + 8]))
# a band under each front rake (where the pierced bargeboard screen will go)
for sgn in (1, -1):
    xa, xb = (BX0 - 2.0, CX) if sgn > 0 else (CX, BX1 + 2.0)
    za = BZ - 1.0 + BS * (xa - BX0 + 2.0 if sgn > 0 else BX1 + 2.0 - xb) * 0 + 0
    pts = []
    for x in np.linspace(xa, xb, 12):
        zt = BZ + BS * (min(x - BX0, BX1 - x)) - 1.5
        pts.append((x, zt))
    band = [(x, z - 7.0) for x, z in pts][::-1]
    m.add("trim", xz_panel(pts + band, BY0 - 3.0, BY0 - 1.4))

# ---------------------------------------------------------------- base and openings
m.add("base", slab(offset(poly([(HX0, HY0), (HX1, HY0), (HX1, HY1), (HX0, HY1)]), 1.0), 0.0, ZF))
m.add("base", (slab(offset(poly([(LX0, LY0), (LX1, LY0), (LX1, LY1), (LX0, LY1)]), 1.0), 0.0, ZF)
               - xz_panel(CAR, LY0 - 5, LY1 + 5)))
m.add("base", slab(offset(poly([(BX0, BY0), (BX1, BY0), (BX1, BY1), (BX0, BY1)]), 1.0), 0.0, 3.0)
      - xz_panel(HAY, BY0 - 3, BY0 + 3))
A = m.add
for xc in (24.0, 48.0, 96.0, 120.0):
    A("glass", win_xz(xc - 6, xc + 6, 16.0, 36.0, HY0))
for xc in (24.0, 48.0, 96.0, 120.0):
    A("glass", win_xz(xc - 6, xc + 6, 50.0, 68.0, HY0))
A("glass", win_xz(66.0, 78.0, ZF, 34.0, HY0))
A("glass", win_xz(64.0, 80.0, 50.0, 68.0, HY0, head="round"))
for yc in (33.0, 63.0, 93.0):
    for x, o in ((HX0, -1), (HX1, 1)):
        A("glass", win_yz(yc - 6, yc + 6, 16.0, 36.0, x, out=o))
        A("glass", win_yz(yc - 6, yc + 6, 50.0, 68.0, x, out=o))
for xc in (36.0, 60.0, 84.0, 108.0):
    A("glass", win_xz(xc - 6, xc + 6, 16.0, 36.0, HY1, out=1))
    A("glass", win_xz(xc - 6, xc + 6, 50.0, 68.0, HY1, out=1))
for yc in (36.0, 62.0, 88.0):
    A("glass", win_yz(yc - 5, yc + 5, 20.0, 38.0, BX1, out=1, head="pointed"))
A("glass", win_xz(186.0, 208.0, 20.0, 40.0, BY1, out=1, head="pointed"))

lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
