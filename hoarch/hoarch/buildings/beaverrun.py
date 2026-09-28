"""The Beaver Run Trestle: an original HO-scale (1:87.1) timber trestle bridge kit, building 80
(the engine terminal batch).

Five four-post bents graded to cross a valley (35, 60, 75, 60 and 35 mm), each with two plumb
posts under the stringers and two battered outer posts, a cap and a sill running past them with
bolt heads, X sway braces in every story and a sash girt between stories on the tall ones; six
open-deck spans of six stringers in two chords on spacer blocks under ties every 4 mm with guard timbers; two
plank bulkheads retaining the banks at the ends. Lay rail on the ties (or flex track on the
stringers). About 300 mm long; the rail is about 82 mm over the creek.

The valley, creek and approach track in the renders are scenery for the pictures, not parts.

usage: python3 -m hoarch.buildings.beaverrun [check] [export]
"""
import os
import sys

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, union
from hoarch import yard as YD
from hoarch.kit import Kit

NAME = "The Beaver Run Trestle"
COLORS = {"Timber": "#4B3C2F"}
RENDER_MAT = {"Timber": "timber"}
PALETTE = {"timber": ("#4B3C2F", 0.9, 0.0), "earth": ("#6B6A40", 0.97, 0.0), "water": ("#48656F", 0.08, 0.0),
           "ballast": ("#8C877E", 0.97, 0.0), "ties": ("#3F3328", 0.9, 0.0), "rail": ("#77716A", 0.35, 0.8)}
VIEWS = {"hero": [-62, 12, 60, 0.95, [0, 0, 0]], "front": [-90, 4, 70, 0.92, [0, 0, 0]], "rear": [120, 16, 60, 0.95, [0, 0, 0]]}

DECK = 75.0                                        # the caps' top, where the stringers rest
SPACING = 50.0
BENTS = [35.0, 60.0, 75.0, 60.0, 35.0]
BULK_H = 14.0
TIE_TOP = DECK + 3.2 + 1.8


def _face_up(A):
    """Print pose for a part lying on its back: its local y (out of the face) up."""
    return np.column_stack([np.vstack([A[:, 0], -A[:, 2], A[:, 1]]), np.zeros(3)])


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    for k, h in enumerate(BENTS):
        y = SPACING * (k + 1)
        A = np.array([[1.0, 0, 0, 0.0], [0, 1.0, 0, y - 1.1], [0, 0, 1.0, DECK - h]])
        kit.add(f"BENT-{k + 1}", "Timber", YD.bent_timber(h).transform(A), P=_face_up(A), key=f"BENT-{h:.0f}", group="bents")
    deck = YD.deck_trestle(SPACING - 0.2)
    for k in range(len(BENTS) + 1):
        kit.add(f"SPAN-{k + 1}", "Timber", deck.translate([0, SPACING * k + SPACING / 2, DECK]), key="SPAN", group="spans")
    bh = YD.bulkhead_timber(32.0, BULK_H)
    L_end = SPACING * (len(BENTS) + 1)
    for tag, A in (("S", np.array([[1.0, 0, 0, 0.0], [0, 1.0, 0, -2.1], [0, 0, 1.0, DECK - BULK_H]])),
                   ("N", np.array([[-1.0, 0, 0, 0.0], [0, -1.0, 0, L_end + 2.1], [0, 0, 1.0, DECK - BULK_H]]))):
        kit.add(f"BULKHEAD-{tag}", "Timber", bh.transform(A), P=_face_up(A), key="BULKHEAD", group="bulkheads")
    print("specks dropped:", kit.drop_specks())
    return kit


def scenery():
    """Render-only: the valley the bents stand in, the creek, the banks and the approach track."""
    L_end = SPACING * (len(BENTS) + 1)
    prof = [(-70.0, DECK), (-2.1, DECK), (0.5, DECK - BULK_H)] + [(SPACING * (k + 1), DECK - h) for k, h in enumerate(BENTS)] + \
           [(L_end - 0.5, DECK - BULK_H), (L_end + 2.1, DECK), (L_end + 70.0, DECK)]
    slabs = []
    for (y0, z0), (y1, z1) in zip(prof[:-1], prof[1:]):
        slabs.append(M.hull_points([(x, y, z) for x in (-95.0, 95.0) for (y, z) in ((y0, -1.0), (y0, z0), (y1, -1.0), (y1, z1))]))
    ground = union(slabs)
    water = box([-95.0, L_end / 2 - 18.0, 0.0], [95.0, L_end / 2 + 18.0, 0.7])
    trk = []
    for (ya, yb) in ((-70.0, -2.5), (L_end + 2.5, L_end + 70.0)):
        trk.append(M.hull_points([(x, y, z) for y in (ya, yb) for (x, z) in ((-15.8, DECK), (15.8, DECK), (-13.0, TIE_TOP - 1.8), (13.0, TIE_TOP - 1.8))]))
    ties = union([box([-13.5, y - 1.3, TIE_TOP - 1.8], [13.5, y + 1.3, TIE_TOP]) for yr in ((-68.0, -4.0), (L_end + 4.0, L_end + 68.0))
                  for y in np.arange(yr[0], yr[1], 6.4)])
    rails = union([box([s - 0.45, -70.0, TIE_TOP], [s + 0.45, L_end + 70.0, TIE_TOP + 2.1]) for s in (-8.4, 8.4)])
    return {"earth": ground, "water": water, "ballast": union(trk), "ties": ties, "rail": rails}


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "beaverrun")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    npz = os.path.join(OUT, "beaverrun.npz")
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
