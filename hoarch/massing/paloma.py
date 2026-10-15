"""Massing 108: a Monterey Colonial adobe (after the Larkin House, Monterey, California, 1835,
and the adobes round it).

New: a two-storey adobe whose low hipped roof runs right out over a balcony on three sides,
carried on slender posts from the ground, so the house wears a two-tier gallery like a skirt;
behind it two one-storey adobe wings run back to make a U round a courtyard, closed at the back
by a garden wall with an arched gate, the wings' corridors (open arcades) facing the court.
Front faces -y.
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
X0, X1, Y0, Y1 = 46.0, 186.0, 62.0, 126.0         # the house, 140 x 64
G = 16.0                                          # the gallery's depth
ZR, SL = 70.0, 0.42                               # roof edge height over the gallery posts

# the roof: a low hip from the gallery's outer edge on three sides, short at the back
H = [[((X0 - G, 0.0), (1, 0), ZR, SL), ((X1 + G, 0.0), (-1, 0), ZR, SL), ((0.0, Y0 - G), (0, 1), ZR, SL),
      ((0.0, Y1 + 4), (0, -1), ZR + SL * 4, SL)]]
m.add("roof", skin_roof(rect_fp(X0 - G - 2, Y0 - G - 2, X1 + G + 2, Y1 + 5), H, th=2.4))
m.add("wall", roof(rect_fp(X0, Y0, X1, Y1), ZF, sunk(H, 1.2)))
m.add("base", bx(X0 - G, Y0 - G, 0.0, X1 + G, Y1, ZF))                         # the gallery's floor, stone-flagged
# the balcony on three sides at the second floor, its railing; posts from the ground to the roof
m.add("deck", bx(X0 - G, Y0 - G, ZB - 1.6, X1 + G, Y0, ZB) + bx(X0 - G, Y0, ZB - 1.6, X0, Y1, ZB) +
      bx(X1, Y0, ZB - 1.6, X1 + G, Y1, ZB))
rail_x(m, X0 - G + 1, X1 + G - 1, Y0 - G + 1, ZB, h=7.0)
rail_y(m, Y0 - G + 1, Y1, X0 - G + 1, ZB, h=7.0)
rail_y(m, Y0 - G + 1, Y1, X1 + G - 1, ZB, h=7.0)
pp = [(x, Y0 - G + 1.4) for x in np.linspace(X0 - G + 1.4, X1 + G - 1.4, 9)]
pp += [(X0 - G + 1.4, y) for y in np.linspace(Y0 - G + 1.4, Y1 - 1.4, 5)[1:]]
pp += [(X1 + G - 1.4, y) for y in np.linspace(Y0 - G + 1.4, Y1 - 1.4, 5)[1:]]
posts(m, pp, ZF, ZR - 1.5, r=1.2)

# the two wings running back, one storey, tile roofs falling to the court; their corridors
for xa, xb, s in ((X0, X0 + 40.0, 1), (X1 - 40.0, X1, -1)):
    block(m, xa, Y1, xb, 206.0, ZF, gable_y(xa, xb, 36.0, 0.4), over=3.0)
    m.add("base", bx(xa, Y1, 0, xb, 206.0, ZF))
    xin = xb if s > 0 else xa                                                   # the court side
    m.add("deck", bx(min(xin, xin + s * 12), Y1, 0, max(xin, xin + s * 12), 206.0, ZF - 0.5))
    m.add("roof", skin_roof(rect_fp(min(xin, xin + s * 14), Y1, max(xin, xin + s * 14), 206.0),
                            [[((xin + s * 14, 0.0), (-s, 0), 30.0, 0.3)]], th=1.8))
    posts(m, [(xin + s * 12, y) for y in np.linspace(Y1 + 8, 200.0, 6)], ZF - 0.5, 30.5, r=1.3)
    for y in (140.0, 176.0):
        m.add("glass", win_yz(y, y + 10, 12.0, 30.0, xin, out=s))
        m.add("glass", win_yz(y, y + 9, 14.0, 28.0, xb if s < 0 else xa, out=-s))
# the garden wall closing the court at the back, its arched gate
wall = bx(X0 + 40.0, 202.0, 0.0, X1 - 40.0, 206.0, 26.0) - xz_panel(round_head(108.0, 124.0, -1.0, 16.0), 201.0, 207.0)
m.add("wall", wall)
m.add("trim", bx(X0 + 40.0, 201.4, 26.0, X1 - 40.0, 206.6, 27.6))
m.add("shadow", xz_panel(round_head(108.0, 124.0, 0.0, 16.0), 203.8, 204.2))

# the house's openings: tall shuttered windows both floors, a central door each floor
for x in np.linspace(X0 + 14, X1 - 24, 5):
    if abs(x + 5 - (X0 + X1) / 2) < 6:
        m.add("glass", win_xz(x, x + 10, ZF, 32.0, Y0))
        m.add("glass", win_xz(x, x + 10, ZB, ZB + 24.0, Y0))
    else:
        m.add("glass", win_xz(x, x + 10, 12.0, 32.0, Y0))
        m.add("glass", win_xz(x, x + 10, ZB + 2, ZB + 22.0, Y0))
    m.add("shadow", bx(x - 4.5, Y0 - 0.6, 12.0, x - 0.5, Y0, 32.0) + bx(x + 10.5, Y0 - 0.6, 12.0, x + 14.5, Y0, 32.0))
for y in (78.0, 104.0):
    for x, s in ((X0, -1), (X1, 1)):
        m.add("glass", win_yz(y, y + 10, 12.0, 32.0, x, out=s))
        m.add("glass", win_yz(y, y + 10, ZB + 2, ZB + 22.0, x, out=s))
for x in (96.0, 126.0):
    m.add("glass", win_xz(x, x + 10, 12.0, 32.0, Y1, out=1))
    m.add("glass", win_xz(x, x + 10, ZB + 2, ZB + 22.0, Y1, out=1))
stack(m, X1 - 22.0, Y1 - 12.0, 9, 7, 70.0, 92.0)
stack(m, X0 + 16.0, 190.0, 8, 6, 30.0, 48.0)
lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
