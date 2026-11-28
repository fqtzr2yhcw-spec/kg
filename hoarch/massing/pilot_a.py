"""Massing pilot A: the whole house under one great gable (after the W. G. Low House, Bristol RI,
1887, and Kragsyde, Manchester-by-the-Sea, 1883).

The new ideas: a single enormous gable whose face is the front, its eaves brought down to the
first storey on both sides, so the second storey and attic live inside the roof; the gable's
upper storey jetties out over a loggia of three broad arches; a carriage arch running right
through the west end of the house under the sweep; a round bay at the east corner rising from
the ground and bursting through the roof edge under a flared cap; eyebrow dormers rolling out
of both slopes; a stone terrace with boulders. Front faces -y.
"""
import math
import sys

import numpy as np

sys.path.insert(0, sys.argv[1])
from mk import (Model, bx, below, roof, skin_roof, bellcone, cone, ring, win_xz, win_yz, win_round, xz_panel,
                yz_panel, round_head, eyebrow, boulder)
from hoarch.core import poly, slab, union, circle, offset, cs_union

OUT = sys.argv[2]
m = Model()
ZF, S1 = 8.0, 42.0
X0, X1, YF, YJ, YB = 16.0, 196.0, 30.0, 24.0, 130.0      # walls; YJ = the jettied gable face
SL = 0.78
W_PL = (X0, 0.0), (1, 0), S1, SL
E_PL = (X1, 0.0), (-1, 0), S1, SL
G = [[W_PL, E_PL]]
APEX = S1 + SL * (X1 - X0) / 2

# ---------------------------------------------------------------- the great gable
m.add("roof", skin_roof([(X0 - 6, YJ - 6), (X1 + 6, YJ - 6), (X1 + 6, YB + 6), (X0 - 6, YB + 6)], G, th=2.8))
upper = roof([(X0, YJ), (X1, YJ), (X1, YB), (X0, YB)], S1, G)
upper = upper - xz_panel(round_head(92.0, 120.0, 74.0, 80.0), YJ - 1.0, YJ + 8.0)          # balcony sunk in the gable
m.add("deck", bx(92.0, YJ, 73.2, 120.0, YJ + 8.0, 74.0))
m.add("trim", bx(92.0, YJ, 74.0, 120.0, YJ + 1.0, 77.6))
lower = bx(X0, YF, ZF, X1, YB, S1)
# loggia: three broad arches in the ground storey, recessed to y = 46
ARCH = [(62.0, 90.0), (92.0, 120.0), (122.0, 150.0)]
loggia = bx(60.0, YF - 1, ZF, 152.0, 46.0, 38.0)
arcade = union([xz_panel(round_head(a, b, ZF, 24.0), YF - 1.0, YF + 4.0) for a, b in ARCH])
lower = lower - arcade - bx(60.0, YF + 3.9, ZF, 152.0, 46.0, 38.0)
# carriage arch right through the west end, front to back
CARR = round_head(24.0, 50.0, 0.0, 23.0)
passage = xz_panel(CARR, YJ - 8.0, YB + 8.0)
lower = lower - passage
upper = upper - passage
m.add("wall", lower)
m.add("upper", upper)
m.add("upper", yz_panel([(YJ, S1), (YF, S1), (YF, S1 - 4.0)], X0, X1) - passage)    # flared skirt under the jetty
m.add("shadow", bx(60.0, 45.6, ZF, 152.0, 46.0, 38.0))
m.add("deck", bx(60.0, YF, ZF - 0.6, 152.0, 46.0, ZF))

# ---------------------------------------------------------------- round bay through the roof edge
BC, BR = (174.0, 26.0), 14.0
m.add("wall", ring(BC, BR, ZF, 74.0))
m.add("trim", ring(BC, BR + 1.0, 71.0, 74.0))
m.add("roof", bellcone(BC, BR + 3.0, 74.0, 20.0))

# ---------------------------------------------------------------- eyebrows on both slopes
hw, ww = eyebrow(W_PL, (X0 + 24.0, 84.0), (0, 1), 15.0, 6.5, 34.0)
m.add("roof", hw); m.add("glass", ww)
he, we = eyebrow(E_PL, (X1 - 24.0, 64.0), (0, 1), 15.0, 6.5, 34.0)
m.add("roof", he); m.add("glass", we)

# ---------------------------------------------------------------- kitchen lean-to behind
LT = (0.0, 150.0), (0, -1), 30.0, 0.5
m.add("wall", below(bx(64, YB - 2, ZF, 148, 150, 60), *LT))
m.add("roof", below(bx(61, YB - 1, 20, 151, 154, 70), (0.0, 154.0), (0, -1), 29.0, 0.5)
      - below(bx(60, YB - 2, 10, 152, 156, 70), (0.0, 154.0), (0, -1), 26.2, 0.5))

# ---------------------------------------------------------------- chimneys (rubble stone)
for (cx, cy, z1) in ((70.0, 100.0, 126.0), (146.0, 64.0, 122.0)):
    m.add("chimney", bx(cx - 6, cy - 5, 60, cx + 6, cy + 5, z1) + bx(cx - 7.2, cy - 6.2, z1 - 3, cx + 7.2, cy + 6.2, z1))

# ---------------------------------------------------------------- stone base, terrace, boulders
fp = cs_union([poly([(X0, YF), (X1, YF), (X1, YB), (X0, YB)]), circle(BC, BR, 48), poly([(64, YB), (148, YB), (148, 150), (64, 150)])])
base = slab(offset(fp, 1.0), 0.0, ZF) - xz_panel(CARR, YJ - 9, YB + 9)
m.add("base", base)
m.add("base", bx(56, 8, 0, 156, YF + 0.5, ZF - 0.6) - bx(94, 7, 3.0, 118, 14, 9))
m.add("deck", bx(94, 1, 0, 118, 8, 2.4) + bx(94, 4, 0, 118, 14, 5.0))
for i, (c, r) in enumerate((((8.0, 22.0), 8.0), ((14.0, 138.0), 10.0), ((200.0, 112.0), 9.0),
                            ((160.0, 10.0), 6.5), ((50.0, 10.0), 7.0), ((196.0, 140.0), 6.0))):
    m.add("base", boulder(c, r, seed=i))
m.add("deck", bx(22, YJ - 10, 0, 52, YB + 10, 0.8))                                     # the drive through the arch

# ---------------------------------------------------------------- openings
A = m.add
for k in range(5):                                        # ribbon of second-storey windows in the gable
    x0 = 66.0 + k * 16.4
    A("glass", win_xz(x0, x0 + 14.4, 50.0, 64.0, YJ))
A("shadow", xz_panel(round_head(92.0, 120.0, 74.0, 80.0), YJ + 7.6, YJ + 8.0))
A("glass", win_xz(30.0, 44.0, 50.0, 60.0, YJ))
A("glass", win_xz(98.0, 114.0, ZF, 34.0, 46.0))           # door at the back of the loggia
for x0 in (70.0, 130.0):
    A("glass", win_xz(x0, x0 + 12.0, 14.0, 32.0, 46.0))
for a in (-135.0, -90.0, -45.0):
    A("glass", win_round(BC, BR, a, 7.5, 14.0, 34.0))
for a in (-120.0, -60.0):
    A("glass", win_round(BC, BR, a, 7.5, 46.0, 62.0))
for y0 in (64.0, 100.0):
    A("glass", win_yz(y0, y0 + 14.0, 14.0, 34.0, X0, out=-1))
    A("glass", win_yz(y0, y0 + 14.0, 14.0, 34.0, X1, out=1))
for x0 in (28.0, 166.0):
    A("glass", win_xz(x0, x0 + 14.0, 14.0, 34.0, YB, out=1))
for k in range(4):
    x0 = 76.0 + k * 15.4
    A("glass", win_xz(x0, x0 + 13.4, 50.0, 62.0, YB, out=1))
A("glass", win_xz(98.0, 114.0, 76.0, 88.0, YB, out=1))
for x0 in (74.0, 126.0):
    A("glass", win_xz(x0, x0 + 12.0, 14.0, 26.0, 150.0, out=1))
A("glass", win_xz(100.0, 112.0, ZF, 26.0, 150.0, out=1))

lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("apex", round(APEX, 1), "bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
