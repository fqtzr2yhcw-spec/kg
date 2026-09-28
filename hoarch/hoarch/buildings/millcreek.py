"""The Mill Creek Bridge: an original HO-scale (1:87.1) two-span railroad bridge kit, building 79
(the engine terminal batch): two concrete abutments, a concrete pier and two ballasted deck
plate-girder spans for a single track.

The abutments (1908) are poured concrete: a breast wall to the bridge seat with three recessed
chamfered panels, a coping under the seat and bearing pads for the girders, the backwall behind
with the date cast in a plate, splayed wing walls with panels sloping down under copings to capped
ends, all on a projecting footing. The pier is battered with a pointed cutwater at each end,
panelled faces and a coping cap carrying both spans' bearings. Each span is two riveted plate
girders, 120 mm long and 16 mm deep, with flange angles, stiffener angles and knee-braced
diaphragms, under a steel deck with ballast curbs carried on outrigger brackets; lay the track in its ballast on the deck. The rail's height over the
creek bed is about 67 mm.

The water and track in the renders are scenery for the pictures, not parts.

usage: python3 -m hoarch.buildings.millcreek [check] [export]
"""
import os
import sys

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, union
from hoarch import yard as YD
from hoarch.kit import Kit

NAME = "The Mill Creek Bridge"
COLORS = {"Concrete": "#AFAAA0", "Steel": "#3A3D40"}
RENDER_MAT = {"Concrete": "stone", "Steel": "iron"}
PALETTE = {"stone": ("#AFAAA0", 0.9, 0.0), "iron": ("#3A3D40", 0.5, 0.3), "water": ("#48656F", 0.08, 0.0), "earth": ("#6B6A40", 0.97, 0.0),
           "ballast": ("#8C877E", 0.97, 0.0), "ties": ("#3F3328", 0.9, 0.0), "rail": ("#77716A", 0.35, 0.8)}
VIEWS = {"hero": [-62, 16, 60, 0.95, [0, 0, 0]], "front": [-90, 6, 70, 0.92, [0, 0, 0]], "rear": [140, 18, 60, 0.95, [0, 0, 0]]}

Z_SEAT, Z_TOP = 40.0, 60.0
SPAN_L = 120.0
Y_PIER = 113.0
Y_B = 226.0                                        # the north abutment's breast


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    ab = YD.abutment_concrete(48.0, Z_SEAT, Z_TOP)
    kit.add("ABUTMENT-S", "Concrete", ab.rotate([0, 0, 180]), key="ABUTMENT", group="abutments")
    kit.add("ABUTMENT-N", "Concrete", ab.translate([0, Y_B, 0]), key="ABUTMENT", group="abutments")
    kit.add("PIER", "Concrete", YD.pier_concrete(h=Z_SEAT - 4.0).translate([0, Y_PIER, 0]), group="pier")
    sp = YD.span_girder(SPAN_L)
    for k, yc in enumerate((-7.5 + SPAN_L / 2, Y_PIER + 0.5 + SPAN_L / 2)):
        kit.add(f"SPAN-{k + 1}", "Steel", sp.translate([0, yc, Z_SEAT + 2.0]), key="SPAN", group="spans")
    print("specks dropped:", kit.drop_specks())
    return kit


def scenery():
    """Render-only: the creek under the bridge and the track across its deck."""
    water = box([-130.0, 4.0, 0.0], [130.0, Y_B - 4.0, 0.7])
    z0 = Z_SEAT + 2.0 + 16.0 + 2.0
    bal = M.hull_points([(x, y, z) for y in (-7.0, Y_B + 7.5) for (x, z) in ((-15.8, z0), (15.8, z0), (-13.0, z0 + 2.4), (13.0, z0 + 2.4))])
    ties = union([box([-13.5, y - 1.3, z0 + 2.4], [13.5, y + 1.3, z0 + 4.2]) for y in np.arange(-68.0, Y_B + 68.0, 6.4)])
    rails = union([box([s - 0.45, -70.0, z0 + 4.2], [s + 0.45, Y_B + 70.0, z0 + 6.3]) for s in (-8.7, 8.7)])
    fills = []
    for sg, y0 in ((-1, 0.0), (1, Y_B)):
        pts = [(x, y0 + sg * 14.0, Z_TOP) for x in (-20.0, 20.0)] + [(x, y0 + sg * 70.0, Z_TOP) for x in (-20.0, 20.0)] + \
              [(x, y0 + sg * 37.0, 22.0) for x in (-43.0, 43.0)] + [(x, y0 + sg * 70.0, 0.0) for x in (-78.0, 78.0)] + \
              [(x, y0 + sg * 40.0, 0.0) for x in (-62.0, 62.0)]
        fills.append(M.hull_points(pts))
    trk = []
    for sg, y0 in ((-1, 0.0), (1, Y_B)):
        ya, yb = sorted((y0 + sg * 7.0, y0 + sg * 70.0))
        trk.append(M.hull_points([(x, y, z) for y in (ya, yb) for (x, z) in ((-15.8, Z_TOP), (15.8, Z_TOP), (-13.0, Z_TOP + 2.4), (13.0, Z_TOP + 2.4))]))
    return {"water": water, "ballast": bal + union(trk), "ties": ties, "rail": rails, "earth": union(fills)}


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "millcreek")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    npz = os.path.join(OUT, "millcreek.npz")
    kit.render_npz(npz)
    from hoarch.kit import mesh_arrays
    data = dict(np.load(npz))
    for name, m in scenery().items():
        v, f = mesh_arrays(m)
        data[name + "__v"], data[name + "__f"] = v.astype(np.float32), f.astype(np.int32)
    np.savez_compressed(npz, **data)
    import json
    json.dump({"materials": {k: list(v) for k, v in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2)
