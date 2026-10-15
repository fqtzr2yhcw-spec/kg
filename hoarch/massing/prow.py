"""Massing 112: a flatiron block on a wedge-shaped lot (after the Gooderham Building, Toronto,
1892, by David Roberts Jr.).

New: the plan is a wedge, two long fronts meeting at a sharp angle where two streets fork,
the point rounded into a turret that rises through the cornice under a tall conical roof; a
steep slate roof with dormers follows the wedge; shops along the ground floor of both fronts
with the main entrance at the point; a plain brick back wall where the next lot would be.
Built for the odd corners of a layout. The point faces -y.
"""
import math
import sys
sys.path.insert(0, sys.argv[1])
from mk import (Model, bx, hip_poly, roof, skin_roof, sunk, stack, win_xz, rect_fp, cone)
from manifold3d import Manifold as M
from hoarch.core import slab, poly, offset
import numpy as np

OUT = sys.argv[2]
m = Model()
ZF, Z1, ZC = 4.0, 42.0, 128.0                       # sidewalk, shop storey's top, the main cornice
XC, YN, YB, HALF = 128.0, 46.0, 228.0, 17.0         # point centre, back wall, half-angle (deg)
RN = 15.0


def hull2(pts):
    P = sorted(set(map(tuple, np.round(pts, 4))))
    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and (h[-1][0] - h[-2][0]) * (p[1] - h[-2][1]) - (h[-1][1] - h[-2][1]) * (p[0] - h[-2][0]) <= 0:
                h.pop()
            h.append(p)
        return h
    lo, up = half(P), half(P[::-1])
    return lo[:-1] + up[:-1]


wb = (YB - YN) * math.tan(math.radians(HALF)) + RN / math.cos(math.radians(HALF))
circ = [(XC + RN * math.cos(a), YN + RN * math.sin(a)) for a in np.linspace(0, 2 * math.pi, 48, endpoint=False)]
PL = hull2(circ + [(XC - wb, YB), (XC + wb, YB)])                                   # counter-clockwise
fp = poly(PL)
# the block: shop storey, three upper storeys, a cornice, a steep roof with a flat top
m.add("wall", slab(fp, ZF, ZC))
m.add("trim", slab(offset(fp, 2.0), ZC - 5.0, ZC) + slab(offset(fp, 1.0), Z1 - 2.0, Z1 + 1.0))
Hr = hip_poly(PL, ZC, 1.6)
m.add("roof", roof(PL, ZC, Hr, zhi=ZC + 26.0))
m.add("deck", slab(offset(fp, -16.5), ZC + 25.0, ZC + 26.6))
m.add("base", slab(offset(fp, 6.0), 0.0, ZF))                                         # the sidewalks round it
# the turret at the point: rises a stage over the cornice, conical roof, finial
m.add("upper", M.cylinder(ZC + 30.0 - ZF, RN + 1.5, RN + 1.5, 48).translate([XC, YN, ZF]))
m.add("trim", M.cylinder(4.0, RN + 3.2, RN + 3.2, 48).translate([XC, YN, ZC + 26.0]))
m.add("roof", M.cylinder(36.0, RN + 4.0, 0.0, 48).translate([XC, YN, ZC + 30.0]))
m.add("trim", M.cylinder(8.0, 1.2, 0.2, 8).translate([XC, YN, ZC + 66.0]))
# dormers along both slopes, a chimney stack on each side near the back
side = [(XC - wb, YB), (XC + wb, YB)]
edges = [(np.array(PL[i]), np.array(PL[(i + 1) % len(PL)])) for i in range(len(PL))]
longs = sorted(edges, key=lambda e: -np.linalg.norm(e[1] - e[0]))[:3]                # the two fronts and the back
for sgn in (-1, 1):
    e = [e for e in longs if abs(e[1][1] - e[0][1]) > 60 and (e[0][0] - XC) * sgn > 0][0]
    a0, a1 = (e[0], e[1]) if e[0][1] < e[1][1] else (e[1], e[0])                    # from the point to the back
    d = (a1 - a0) / np.linalg.norm(a1 - a0)
    n = np.array([d[1], -d[0]])
    n = n if n[0] * sgn > 0 else -n                                                   # outward
    for k in range(4):
        c = a0 + d * (36.0 + k * 34.0)
        dm = M.cube([12.0, 14.0, 16.0]).translate([-6.0, -6.0, 0.0])
        ang = math.degrees(math.atan2(n[1], n[0])) - 90.0
        dm = dm.rotate([0, 0, ang]).translate([c[0], c[1], ZC - 1.0])
        m.add("upper", dm)
        cap = M.hull_points([(x, y, z) for x, y, z in [(-7, -7, 15), (7, -7, 15), (-7, 9, 15), (7, 9, 15), (0, -7, 22), (0, 9, 22)]])
        m.add("roof", cap.rotate([0, 0, ang]).translate([c[0], c[1], ZC - 1.0]))
        w = M.cube([7.0, 1.0, 9.0]).translate([-3.5, -7.4, 3.0]).rotate([0, 0, ang]).translate([c[0], c[1], ZC - 1.0])
        m.add("glass", w)
        # windows on three storeys, and the shopfront glass, along this front
        for z0, z1 in ((48.0, 66.0), (78.0, 96.0), (106.0, 122.0)):
            for j in range(5):
                cc = a0 + d * (18.0 + j * 30.0)
                ww = M.cube([9.0, 1.0, z1 - z0]).translate([-4.5, -0.6, z0]).rotate([0, 0, ang]).translate([cc[0], cc[1], 0])
                m.add("glass", ww)
        for j in range(4):
            cc = a0 + d * (24.0 + j * 38.0)
            ww = M.cube([30.0, 1.0, 30.0]).translate([-15.0, -0.6, ZF + 4.0]).rotate([0, 0, ang]).translate([cc[0], cc[1], 0])
            m.add("glass", ww)
    stack(m, XC + sgn * (wb - 14.0), YB - 12.0, 8, 8, ZC + 10, ZC + 40)
# the turret's windows, and the entrance at the point
for z0, z1 in ((48.0, 66.0), (78.0, 96.0), (106.0, 122.0), (ZC + 6.0, ZC + 22.0)):
    for a in (-90.0, -45.0, -135.0):
        from mk import win_round
        m.add("glass", win_round((XC, YN), RN + 1.5, a, 8.0, z0, z1))
m.add("glass", win_round((XC, YN), RN + 1.5, -90.0, 12.0, ZF, 36.0))
lo, hi = m.save(OUT + ".npz", OUT + "_palette.json")
print("bbox", np.round(lo, 1), np.round(hi, 1), "size", np.round(hi - lo, 1))
