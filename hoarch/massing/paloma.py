"""Massing 108: a Monterey Colonial adobe (after the Larkin House, Monterey, California, 1835,
and the adobes round it).

New: a two-storey adobe whose low hipped roof runs right out over a balcony, carried on slender
posts from the ground, so the house wears a two-tier gallery like a skirt; two one-storey adobe
wings come forward from it to make a U round a courtyard that opens to the street, closed by a
garden wall with an arched gate, the wings' corridors (open arcades) facing the court. Front
faces -y (revised: the courtyard to the front, the owner's choice).
"""
import sys
sys.path.insert(0, sys.argv[1])
from mk import (Model, bx, block, gable_y, gable_x, posts, stack, rail_x, rail_y, win_xz, win_yz, skin_roof, roof,
                rect_fp, sunk, xz_panel, round_head)
from manifold3d import Manifold as M
import numpy as np

OUT = sys.argv[2]
m = Model()
ZF, S1, ZB = 6.0, 40.0, 41.6
X0, X1, Y0, Y1 = 46.0, 186.0, 120.0, 184.0        # the house at the back of the court, 140 x 64
WL, WR = (X0, X0 + 40.0), (X1 - 40.0, X1)          # the wings, coming forward to y = YF
YF = 40.0
G = 16.0                                          # the gallery's depth
ZR, SL = 70.0, 0.42

# the house's roof: a low hip out over the gallery (front between the wings, both ends, short back)
H = [[((X0 - G, 0.0), (1, 0), ZR, SL), ((X1 + G, 0.0), (-1, 0), ZR, SL), ((0.0, Y0 - G), (0, 1), ZR, SL),
      ((0.0, Y1 + 4), (0, -1), ZR + SL * 4, SL)]]
m.add("roof", skin_roof(rect_fp(X0 - G - 2, Y0 - G - 2, X1 + G + 2, Y1 + 5), H, th=2.4))
m.add("wall", roof(rect_fp(X0, Y0, X1, Y1), ZF, sunk(H, 1.2)))
m.add("base", bx(X0 - G, Y0, 0.0, X0, Y1, ZF) + bx(X1, Y0, 0.0, X1 + G, Y1, ZF) + bx(WL[1], Y0 - G, 0.0, WR[0], Y0, ZF))
# the balcony: across the court front and down both ends; posts from the ground to the roof
m.add("deck", bx(WL[1], Y0 - G, ZB - 1.6, WR[0], Y0, ZB) + bx(X0 - G, Y0 - G, ZB - 1.6, X0, Y1, ZB) +
      bx(X1, Y0 - G, ZB - 1.6, X1 + G, Y1, ZB))
rail_x(m, WL[1], WR[0], Y0 - G + 1, ZB, h=7.0)
rail_y(m, Y0 - G + 1, Y1, X0 - G + 1, ZB, h=7.0)
rail_y(m, Y0 - G + 1, Y1, X1 + G - 1, ZB, h=7.0)
rail_x(m, X0 - G + 1, X0, Y0 - G + 1, ZB, h=7.0)
rail_x(m, X1, X1 + G - 1, Y0 - G + 1, ZB, h=7.0)
pp = [(x, Y0 - G + 1.4) for x in np.linspace(WL[1] + 1.4, WR[0] - 1.4, 5)]
pp += [(X0 - G + 1.4, y) for y in np.linspace(Y0 - G + 1.4, Y1 - 1.4, 5)]
pp += [(X1 + G - 1.4, y) for y in np.linspace(Y0 - G + 1.4, Y1 - 1.4, 5)]
posts(m, pp, ZF, ZR - 1.5, r=1.2)

# the two wings coming forward, one storey, gable ends to the street; corridors facing the court
for (xa, xb), s in ((WL, 1), (WR, -1)):
    block(m, xa, YF, xb, Y0 - G - 0.5, ZF, gable_y(xa, xb, 36.0, 0.42), over=3.0)
    m.add("wall", bx(xa, Y0 - G - 1, ZF, xb, Y0 + 1, 36.0))                      # under the house's gallery roof
    m.add("base", bx(xa, YF, 0, xb, Y0, ZF))
    xin = xb if s > 0 else xa                                                   # the court side
    m.add("deck", bx(min(xin, xin + s * 12), YF + 6, 0, max(xin, xin + s * 12), Y0 - G, ZF - 0.5))
    m.add("roof", skin_roof(rect_fp(min(xin, xin + s * 14), YF + 4, max(xin, xin + s * 14), Y0 - G),
                            [[((xin + s * 14, 0.0), (-s, 0), 30.0, 0.3)]], th=1.8))
    posts(m, [(xin + s * 12, y) for y in np.linspace(YF + 10, Y0 - G - 3, 5)], ZF - 0.5, 30.5, r=1.3)
    for y in (60.0, 84.0):
        m.add("glass", win_yz(y, y + 10, 12.0, 30.0, xin, out=s))
        m.add("glass", win_yz(y, y + 9, 14.0, 28.0, xb if s < 0 else xa, out=-s))
    xc = (xa + xb) / 2
    m.add("glass", win_xz(xc - 5, xc + 5, 14.0, 30.0, YF))                      # a grilled window to the street
    m.add("trim", bx(xc - 7, YF - 1.2, 12.0, xc + 7, YF, 13.0))
# the garden wall across the front of the court, its arched gate; the court's well
m.add("wall", bx(WL[1], YF + 2, 0.0, WR[0], YF + 6, 26.0) - xz_panel(round_head(108.0, 124.0, -1.0, 16.0), YF + 1, YF + 7))
m.add("trim", bx(WL[1], YF + 1.4, 26.0, WR[0], YF + 6.6, 27.6))
m.add("trim", xz_panel(round_head(105.0, 127.0, 0.0, 16.0), YF + 1.0, YF + 2.0) - xz_panel(round_head(108.0, 124.0, -1.0, 16.0), YF, YF + 3))
m.add("shadow", xz_panel(round_head(108.0, 124.0, 0.0, 16.0), YF + 3.8, YF + 4.2))
m.add("base", M.cylinder(5.0, 6.0, 6.0, 32).translate([116.0, 76.0, 0.0]) - M.cylinder(6.0, 4.6, 4.6, 32).translate([116.0, 76.0, 1.0]))
m.add("deck", bx(WL[1], YF + 6, 0.0, WR[0], Y0 - G, 0.6))                         # the court's paving

# the house's openings: tall shuttered windows both floors facing the court, a door each floor
for x in np.linspace(WL[1] + 8, WR[0] - 18, 3):
    if abs(x + 5 - (X0 + X1) / 2) < 6:
        m.add("glass", win_xz(x, x + 10, ZF, 32.0, Y0))
        m.add("glass", win_xz(x, x + 10, ZB, ZB + 24.0, Y0))
    else:
        m.add("glass", win_xz(x, x + 10, 12.0, 32.0, Y0))
        m.add("glass", win_xz(x, x + 10, ZB + 2, ZB + 22.0, Y0))
for y in (136.0, 162.0):
    for x, s in ((X0, -1), (X1, 1)):
        m.add("glass", win_yz(y, y + 10, 12.0, 32.0, x, out=s))
        m.add("glass", win_yz(y, y + 10, ZB + 2, ZB + 22.0, x, out=s))
for x in np.linspace(X0 + 14, X1 - 24, 5):
    m.add("glass", win_xz(x, x + 10, 12.0, 32.0, Y1, out=1))
    m.add("glass", win_xz(x, x + 10, ZB + 2, ZB + 22.0, Y1, out=1))
stack(m, X1 - 22.0, Y1 - 12.0, 9, 7, 70.0, 92.0)
stack(m, WL[0] + 10.0, 60.0, 8, 6, 30.0, 48.0)
lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
