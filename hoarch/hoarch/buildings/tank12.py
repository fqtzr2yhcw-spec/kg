"""Water Tank No. 12: an original HO-scale (1:87.1) railroad water tank, building 69 (the railroad
and town batch).

A wooden water tank of about 1890: a drum of vertical staves bound by four iron hoops with lugs,
on a chime and under a rim, its spout raised at 45 degrees on a pivot box; a conical roof of
boards running up to a ball vent; the whole on a timber trestle of nine posts with girts, X
braces in every outer bay, joists and a planked deck, standing on concrete footings on a pad.

usage: python3 -m hoarch.buildings.tank12 [check] [export]
"""
import os
import sys

from manifold3d import Manifold as M

from hoarch.core import box, union
from hoarch import town as TN
from hoarch.kit import Kit, print_flip

NAME = "Water Tank No. 12"
COLORS = {"Tank": "#7A5A3C", "Iron": "#2E2E2E", "Timber": "#5E4A36", "Tar": "#4A4A4A", "Concrete": "#A7A39A"}
RENDER_MAT = {"Tank": "tank", "Iron": "iron", "Timber": "timber", "Tar": "roof", "Concrete": "stone"}
PALETTE = {"tank": ("#7A5A3C", 0.85), "iron": ("#2E2E2E", 0.5), "timber": ("#5E4A36", 0.9), "roof": ("#4A4A4A", 0.9),
           "stone": ("#A7A39A", 0.9)}
VIEWS = {"hero": [-34, 14, 60, 0.95, [0, 0, 0]], "front": [0, 6, 70, 0.92, [0, 0, 0]], "rear": [150, 16, 60, 0.95, [0, 0, 0]]}

R_T, H_T, H_TR = 34.0, 40.0, 44.0                  # the tank's radius and height, the trestle's height
Z_FOOT = 4.0                                       # the footings' tops


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    kit.add("FOOTINGS", "Concrete", TN.footings(R_T), group="base")
    kit.add("TRESTLE", "Timber", TN.trestle(R_T, H_TR).translate([0, 0, Z_FOOT]), P=print_flip(), group="trestle")
    z_deck = Z_FOOT + H_TR
    tank = TN.tank_body(R_T, H_T).translate([0, 0, z_deck])
    bands = union([box([-R_T - 5, -R_T - 5, z_deck + z - 0.05], [R_T + 5, R_T + 5, z_deck + z + 1.3])
                   for z in [4.0 + k * (H_T - 9.0) / 3 for k in range(4)]])
    iron = (tank ^ bands) - M.cylinder(400.0, R_T + 0.05, R_T + 0.05, 96).translate([0, 0, -10])
    kit.add("TANK", "Tank", tank, group="tank", render=[("Tank", tank - iron), ("Iron", iron)])
    kit.add("ROOF", "Tar", TN.tank_roof(R_T).translate([0, 0, z_deck + H_T]), group="tank")
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "tank12")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "tank12.npz"))
    import json
    json.dump({"materials": {k: [h, r, 0.0] for k, (h, r) in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2)
