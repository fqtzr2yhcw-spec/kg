"""Massing 103: a lighthouse keeper's house with the light tower rising out of the middle of
its roof (after Point Fermin, San Pedro CA, 1874, and its Stick Style sisters by Paul Pelz).

New: the tower is not on a corner or a front: it rises from the crossing of the roofs, square,
through two stages to a railed gallery on brackets and a glazed lantern under a domed cap.
A cross-gabled two-storey house below, a veranda round the front and the sea side, a kitchen
wing behind, all on a low bluff edge with a rock face at the back. Front faces -y.
"""
import sys
sys.path.insert(0, sys.argv[1])
from mk import *                                   # noqa: F401,F403
from mk import Model, bx, block, gable_x, gable_y, hip, posts, stack, rail_x, rail_y, steps_y, win_xz, win_yz, \
    skin_roof, roof, rect_fp, boulder, shed
from manifold3d import Manifold as M
from hoarch.core import union
import numpy as np

OUT = sys.argv[2]
m = Model()
ZF, S1, ZE = 8.0, 44.0, 76.0
X0, X1, Y0, Y1 = 40.0, 170.0, 40.0, 140.0          # the house, 130 x 100
XC, YC = (X0 + X1) / 2, (Y0 + Y1) / 2
SL = 0.62

# the hipped core and the four cross gables (front, back, both sides), stick-style
block(m, X0, Y0, X1, Y1, ZF, hip(X0, Y0, X1, Y1, ZE, SL), over=6.0)
for (gx0, gx1) in ((XC - 24, XC + 24),):
    block(m, gx0, Y0 - 6, gx1, YC, ZF, gable_y(gx0, gx1, ZE, 1.15), over=6.0, rake=5.0)       # front gable, forward 6
    block(m, gx0, YC, gx1, Y1, ZF, gable_y(gx0, gx1, ZE, 1.15), over=6.0, rake=5.0)           # back gable
block(m, XC, YC - 22, X1 + 4, YC + 22, ZF, gable_x(YC - 22, YC + 22, ZE, 1.15), over=6.0, rake=5.0)  # east gable
block(m, X0 - 4, YC - 22, XC, YC + 22, ZF, gable_x(YC - 22, YC + 22, ZE, 1.15), over=6.0, rake=5.0)  # west gable

# the tower out of the crossing: two stages, a bracketed gallery, the lantern and its dome
T, ZG = 17.0, 150.0
m.add("upper", bx(XC - T, YC - T, ZE, XC + T, YC + T, ZG))
m.add("trim", bx(XC - T - 1.2, YC - T - 1.2, ZG - 28, XC + T + 1.2, YC + T + 1.2, ZG - 25))      # a band between the stages
m.add("deck", bx(XC - T - 7, YC - T - 7, ZG, XC + T + 7, YC + T + 7, ZG + 3))                     # the gallery
for k in range(-2, 3):                                                                             # brackets under it
    for s in (-1, 1):
        m.add("trim", bx(XC + k * 8 - 0.8, YC + s * T - (3.5 if s < 0 else 0.0), ZG - 5, XC + k * 8 + 0.8,
                         YC + s * T + (0.0 if s < 0 else 3.5), ZG))
        m.add("trim", bx(XC + s * T - (3.5 if s < 0 else 0.0), YC + k * 8 - 0.8, ZG - 5,
                         XC + s * T + (0.0 if s < 0 else 3.5), YC + k * 8 + 0.8, ZG))
for s in (-1, 1):
    rail_x(m, XC - T - 7, XC + T + 7, YC + s * (T + 6.6), ZG + 3, h=7.0)
    rail_y(m, YC - T - 7, YC + T + 7, XC + s * (T + 6.6), ZG + 3, h=7.0)
m.add("trim", M.cylinder(4.0, 15.0, 15.0, 8).rotate([0, 0, 22.5]).translate([XC, YC, ZG + 3]))          # lantern base
m.add("glass", M.cylinder(18.0, 13.0, 13.0, 8).rotate([0, 0, 22.5]).translate([XC, YC, ZG + 7]))       # the glazed lantern
for k in range(8):                                                                                 # its mullions
    a = np.radians(22.5 + 45 * k)
    m.add("trim", M.cylinder(18.0, 0.9, 0.9, 8).translate([XC + 13.2 * np.cos(a), YC + 13.2 * np.sin(a), ZG + 7]))
m.add("roof", M.cylinder(2.0, 15.0, 15.0, 8).rotate([0, 0, 22.5]).translate([XC, YC, ZG + 25]))
m.add("roof", M.sphere(13.0, 32).scale([1, 1, 0.75]).translate([XC, YC, ZG + 27]) - bx(XC - 20, YC - 20, ZG, XC + 20, YC + 20, ZG + 27))
m.add("roof", M.cylinder(5.0, 2.0, 0.8, 12).translate([XC, YC, ZG + 35]) + M.sphere(2.2, 16).translate([XC, YC, ZG + 41]))
for a, b in ((-1, 0), (1, 0), (0, -1), (0, 1)):                                                    # one light per face, each stage
    for z0, z1 in ((ZG - 50, ZG - 36), (ZG - 20, ZG - 8)):
        if b == 0:
            m.add("glass", win_yz(YC - 5, YC + 5, z0, z1, XC + a * T, out=a))
        else:
            m.add("glass", win_xz(XC - 5, XC + 5, z0, z1, YC + b * T, out=b))

# the veranda: round the front and down the sea (east) side, hipped
VY, VX = Y0 - 20.0, X1 + 20.0
m.add("deck", bx(X0 - 6, VY, ZF - 1.0, VX, Y0, ZF) + bx(X1, Y0, ZF - 1.0, VX, Y1 - 20, ZF))
vroof = skin_roof([(X0 - 8, VY - 3), (VX + 3, VY - 3), (VX + 3, Y1 - 17), (X1, Y1 - 17), (X1, Y0), (X0 - 8, Y0)],
                  [[((0.0, VY - 3), (0, 1), 38.0, 0.45), ((VX + 3, 0.0), (-1, 0), 38.0, 0.45)]], th=1.8)
m.add("roof", vroof - bx(X0 - 1, Y0 - 7, 0, X1 + 1, Y1, 300) - bx(X1 - 30, Y0 - 1, 0, X1 + 0.5, Y1, 300))
pp = [(x, VY + 1.5) for x in np.linspace(X0 - 4, VX - 1.5, 7)] + [(VX - 1.5, y) for y in np.linspace(VY + 1.5, Y1 - 21.5, 5)[1:]]
posts(m, pp, ZF, 38.5)
rail_x(m, X0 - 4, XC - 8, VY + 1.5, ZF, h=5.0)
rail_x(m, XC + 8, VX - 1.5, VY + 1.5, ZF, h=5.0)
rail_y(m, VY + 1.5, Y1 - 21.5, VX - 1.5, ZF, h=5.0)
steps_y(m, XC - 8, XC + 8, VY, ZF, 3)

# kitchen wing behind (one storey) with its own chimney; the house's two stacks
block(m, X0 + 10, Y1, X0 + 60, Y1 + 34, ZF, gable_y(X0 + 10, X0 + 60, 40.0, 0.8), over=4.0)
stack(m, X0 + 35, Y1 + 26, 8, 6, 40, 70)
stack(m, X0 + 14, YC + 30, 9, 7, 70, 110)
stack(m, X1 - 14, YC - 30, 9, 7, 70, 110)

# windows (two storeys), doors
for x in (X0 + 12, X1 - 24):
    m.add("glass", win_xz(x, x + 11, 16.0, 36.0, Y0))
    m.add("glass", win_xz(x, x + 11, 52.0, 68.0, Y0))
m.add("glass", win_xz(XC - 7, XC + 7, ZF, 34.0, Y0 - 6))                 # front door in the gable
m.add("glass", win_xz(XC - 12, XC - 2, 52.0, 68.0, Y0 - 6))
m.add("glass", win_xz(XC + 2, XC + 12, 52.0, 68.0, Y0 - 6))
m.add("glass", win_xz(XC - 5, XC + 5, 82.0, 92.0, Y0 - 6))
for y in (Y0 + 12, Y1 - 24):
    m.add("glass", win_yz(y, y + 11, 16.0, 36.0, X1, out=1))
    m.add("glass", win_yz(y, y + 11, 52.0, 68.0, X1, out=1))
    m.add("glass", win_yz(y, y + 11, 16.0, 36.0, X0, out=-1))
    m.add("glass", win_yz(y, y + 11, 52.0, 68.0, X0, out=-1))
for x in (X1 - 40, X1 - 22):
    m.add("glass", win_xz(x, x + 11, 16.0, 36.0, Y1, out=1))
    m.add("glass", win_xz(x, x + 11, 52.0, 68.0, Y1, out=1))

# the ground: a low bluff, rock face and boulders behind and to the sea side
m.add("base", bx(X0 - 2, Y0 - 2, 0.0, X1 + 2, Y1 + 2, ZF) + bx(X0 + 8, Y1, 0, X0 + 62, Y1 + 36, ZF))
for i, (c, r) in enumerate((((206.0, 150.0), 16.0), ((222.0, 126.0), 12.0), ((196.0, 178.0), 14.0),
                            ((174.0, 194.0), 11.0), ((218.0, 172.0), 10.0), ((224.0, 100.0), 9.0))):
    m.add("base", boulder(c, r, squash=0.9, seed=i))                       # the rocky point on the sea side
lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
