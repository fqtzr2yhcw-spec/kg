"""Massing 106: a Southern dogtrot house (after Sam Houston's Woodland, Huntsville, Texas, 1847,
and the dogtrot farmhouses of the Gulf states).

New: a house you can see straight through. Two log pens under one long side-gabled roof with an
open breezeway (the dogtrot) between them, floored and roofed, open front and back; the roof
breaks to a shallower pitch over a full-width front porch on cedar posts; fat stone chimneys
stand outside both gable ends; the whole thing sits up on stone piers. Behind, a detached
kitchen cabin reached by a covered walk from the breezeway. Front faces -y.
"""
import sys
sys.path.insert(0, sys.argv[1])
from mk import sunk, Model, bx, block, gable_x, gable_y, posts, stack, rail_x, win_xz, win_yz, skin_roof, roof, rect_fp, steps_y
from manifold3d import Manifold as M
import numpy as np

OUT = sys.argv[2]
m = Model()
ZF, ZE, SL = 9.0, 42.0, 0.8
X0, XA, XB, X1 = 26.0, 92.0, 132.0, 198.0         # west pen, breezeway, east pen
Y0, Y1 = 66.0, 130.0
YP = 40.0                                         # the porch's front

# the long roof over both pens and the breezeway; its gable walls stand only over the pens
G = gable_x(Y0, Y1, ZE, SL)
m.add("roof", skin_roof([(X0 - 2, Y0 - 3), (X1 + 2, Y0 - 3), (X1 + 2, Y1 + 5), (X0 - 2, Y1 + 5)], G, th=2.4))
for xa, xb in ((X0, XA), (XB, X1)):
    m.add("wall", roof(rect_fp(xa, Y0, xb, Y1), ZF, sunk(G, 1.2)))
m.add("upper", bx(XA, Y0 + 2, ZE - 2.0, XB, Y1 - 2, ZE))                                          # the loft floor over the trot
m.add("shadow", bx(XA + 0.5, Y0 + 1, ZF, XB - 0.5, Y0 + 1.4, ZE - 0.5) - bx(XA + 2, Y0, ZF, XB - 2, Y0 + 3, ZE - 2))
m.add("deck", bx(X0, Y0, ZF - 1.2, X1, Y1, ZF))                                                     # floor through
# stone piers under everything
for x in np.linspace(X0 + 2, X1 - 2, 9):
    for y in (Y0 + 2, Y1 - 2, YP + 2):
        m.add("base", bx(x - 2.5, y - 2.5, 0.0, x + 2.5, y + 2.5, ZF - 1.2))
# the porch: the roof breaks to a shallow pitch over it, posts, floor, steps at the trot
m.add("roof", skin_roof([(X0 - 2, YP - 3), (X1 + 2, YP - 3), (X1 + 2, Y0 + 0.5), (X0 - 2, Y0 + 0.5)],
                        [[((0.0, YP - 3), (0, 1), 33.0, 0.32)]], th=2.0))
m.add("deck", bx(X0, YP, ZF - 1.2, X1, Y0, ZF))
posts(m, [(x, YP + 1.6) for x in np.linspace(X0 + 1.6, X1 - 1.6, 7)], ZF, 34.0, r=1.5)
steps_y(m, XA + 6, XB - 6, YP, ZF, 3)
# back porch along the east pen
m.add("roof", skin_roof([(XA, Y1 - 0.5), (X1 + 2, Y1 - 0.5), (X1 + 2, Y1 + 20), (XA, Y1 + 20)],
                        [[((0.0, Y1 + 20), (0, -1), 30.0, 0.3)]], th=2.0))
m.add("deck", bx(XA, Y1, ZF - 1.2, X1, Y1 + 18, ZF))
posts(m, [(x, Y1 + 16.5) for x in np.linspace(XA + 1.6, X1 - 1.6, 5)], ZF, 31.0, r=1.5)

# stone end chimneys outside both gables, tapering
for x, s in ((X0, -1), (X1, 1)):
    yc = (Y0 + Y1) / 2
    m.add("chimney", bx(min(x, x + s * 12), yc - 10, 0.0, max(x, x + s * 12), yc + 10, 34.0))
    m.add("chimney", M.hull_points([(xx, yy, z) for xx, yy, z in
                                    [(x, yc - 10, 34), (x + s * 12, yc - 10, 34), (x, yc + 10, 34), (x + s * 12, yc + 10, 34),
                                     (x, yc - 5, 46), (x + s * 8, yc - 5, 46), (x, yc + 5, 46), (x + s * 8, yc + 5, 46)]]))
    m.add("chimney", bx(min(x, x + s * 8), yc - 5, 46, max(x, x + s * 8), yc + 5, 84))

# the kitchen cabin behind, and the covered walk to it from the breezeway
KX0, KX1, KY0, KY1 = 36.0, 80.0, 164.0, 204.0
block(m, KX0, KY0, KX1, KY1, ZF, gable_y(KX0, KX1, 36.0, 0.8), over=3.5)
m.add("base", bx(KX0, KY0, 0, KX1, KY1, ZF))
stack(m, KX1 - 8, KY1 - 8, 10, 8, 30, 70)
m.add("deck", bx(XA + 8, Y1 + 18, ZF - 1.2, XA + 22, KY0 + 18, ZF))
m.add("deck", bx(KX1, KY0 + 10, ZF - 1.2, XA + 22, KY0 + 24, ZF))
m.add("roof", skin_roof([(XA + 6, Y1 + 17), (XA + 24, Y1 + 17), (XA + 24, KY0 + 26), (XA + 6, KY0 + 26)],
                        gable_y(XA + 6, XA + 24, 30.0, 0.6), th=1.6))
posts(m, [(XA + 8, y) for y in (Y1 + 22, Y1 + 34, KY0 + 4, KY0 + 16)] + [(XA + 22, y) for y in (Y1 + 22, Y1 + 34, KY0 + 4)], ZF, 30.0, r=1.0)

# windows and doors: a door from each pen into the trot, windows front and back, loft lights
for xa, xb in ((X0, XA), (XB, X1)):
    xc = (xa + xb) / 2
    m.add("glass", win_xz(xc - 6, xc + 6, 16.0, 34.0, Y0))
    m.add("glass", win_xz(xc - 6, xc + 6, 16.0, 34.0, Y1, out=1))
m.add("glass", win_yz(Y0 + 22, Y0 + 36, ZF, 34.0, XA, out=1))
m.add("glass", win_yz(Y0 + 22, Y0 + 36, ZF, 34.0, XB, out=-1))
for x, s in ((X0, -1), (X1, 1)):
    for y in (Y0 + 6, Y1 - 16):
        m.add("glass", win_yz(y, y + 9, 46.0, 56.0, x, out=s))
m.add("glass", win_xz(52.0, 62.0, 14.0, 30.0, KY0))
lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
