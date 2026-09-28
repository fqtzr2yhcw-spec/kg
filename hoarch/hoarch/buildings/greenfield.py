"""The Greenfield Bandstand: an original HO-scale (1:87.1) octagonal park bandstand, building 70 (the
railroad and town batch).

An octagonal bandstand of about 1892 on a raised planked floor over a square-grid lattice skirt,
with steps on the front face. Eight columns (vase-turned bases, ringed shafts, bell capitals),
the railings of lyre-waisted balusters, the shallow arches with sunbursts in their spandrels and
the roof slab over them are one piece, pegged into the floor; a valance of little bells hangs
from the fascia. Above it a tall ogee roof of slates long and short in turn, drawn up to a turned
urn finial.

usage: python3 -m hoarch.buildings.greenfield [check] [export]
"""
import math
import os
import sys

from manifold3d import Manifold as M

from hoarch import features as FT, roof as R, town as TN
from hoarch.kit import Kit, print_flip

NAME = "The Greenfield Bandstand"
COLORS = {"White": "#F2EFE6", "Copper": "#4E7C6E", "PorchDeck": "#7C6853", "Stone": "#A8A396"}
RENDER_MAT = {"White": "trim", "Copper": "roof", "PorchDeck": "deck", "Planks": "planks", "Stone": "stone"}
PALETTE = {"trim": ("#F2EFE6", 0.5), "roof": ("#4E7C6E", 0.6), "deck": ("#6E5B48", 0.85), "planks": ("#8C7456", 0.85),
           "stone": ("#A8A396", 0.9)}
VIEWS = {"hero": [-34, 14, 60, 0.95, [0, 0, 0]], "front": [0, 6, 70, 0.92, [0, 0, 0]], "rear": [150, 16, 60, 0.95, [0, 0, 0]]}

R_OCT = 34.0                                       # the octagon's circumradius
H_FLOOR = 14.0
POST_H = 30.0
INSET = 2.2
PTS = [(R_OCT * math.cos(math.radians(22.5 + 45 * k)), R_OCT * math.sin(math.radians(22.5 + 45 * k))) for k in range(8)]
EDGE = 2 * R_OCT * math.sin(math.radians(22.5))
FRONT = 5                                          # the run facing -y (its corners at 247.5 and 292.5 degrees)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t = INSET * math.tan(math.radians(22.5))      # a corner post stands on the bisector, INSET in from both faces
    runs = [dict(a=PTS[i], b=PTS[(i + 1) % 8], posts=[t, EDGE - t]) for i in range(8)]
    o = 2.4
    PP = FT.porch_turned(PTS, runs, H_FLOOR, POST_H, steps_at=[(FRONT, EDGE / 2, 12.0)], over=o, inset=INSET, rail_h=8.0,
                         planks=dict(pitch=1.6, border=1.2), post="bandstand", rail="bandstand", arcade="bandarch",
                         skirt="gridlattice", pier_tex="plain", roof_edge="bellvalance", top=True)
    deck = PP["deck"]
    kit.add("DECK", "PorchDeck", deck, P=print_flip(), group="floor", render=FT.plank_zones(deck, H_FLOOR, "Planks", "PorchDeck"))
    res = FT.add_porch_top(kit, "TOP", PP, M(), "White", "White", tin="custom", group="top")
    zs = res["ptop"] - 0.8
    ap = R_OCT * math.cos(math.radians(22.5)) + o + 0.4
    bands = [(1.4, 0.35), (3.0, 0.6), (5.0, 0.9), (7.0, 1.3), (9.0, 1.9), (10.0, 2.8), (6.0, 1.9)]
    sol, tex, ap_top, ztop = R.bell_roof((0.0, 0.0), ap, zs, bands, n=8, texture="longshort", tex_kw=dict(pitch=1.5, wtab=2.0, d=0.4))
    kit.add("ROOF", "Copper", sol + tex, group="roof")
    kit.add("FINIAL", "White", TN.finial_bandstand().translate([0, 0, ztop - 0.6]), group="roof")
    FT.crown(kit, "FINIAL", "ROOF")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"STEPS-{k}", "Stone", sm.transform(A) - deck, group="floor")
        FT.key_into(kit, f"STEPS-{k}", ["DECK"], (0, 1, 0), depth=0.8, conform=True)
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "greenfield")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "greenfield.npz"))
    import json
    json.dump({"materials": {k: [h, r, 0.0] for k, (h, r) in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2)
