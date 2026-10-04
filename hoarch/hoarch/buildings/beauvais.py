"""The Beauvais -- an original HO-scale (1:87.1) Second Empire cottage of the mansard batch
(houses 81 to 90), on the batch's roof system (hoarch.secondempire).

A storey and a half: one storey of peach channel-and-bead siding with bobbin corner boards, on a
pebble-dashed base, and over it the bedroom storey in a tall bell-cast mansard chequered in
square and diamond-pointed slates, lit by fourteen big add-ins and a twin one over the door, under a
crest with its own cornice and crook-and-daisy cresting. A veranda wraps the front and both
sides on twin-vase posts, with railings of stacked rings, a frieze of scroll arches and an
icicle fascia. Cream trim, forest accents.

- Windows tall, flat-headed, in casings under a frieze with a sunflower and a shed hood on sawn
  brackets; the front door a leaf between sidelights under a diamond-barred transom, a frieze
  with a sunburst and a cornice crested with sunflowers.
- Eave: a cream course of ovals and bars, a forest frieze of sunflowers, a cream interlaced
  arcade, a soffit on lyre consoles and a forest crown.
- Crest: a cream course of ovals and bars under a forest cyma crown on block modillions.

usage: python3 -m hoarch.buildings.beauvais [check] [export]
"""
import math
import os
import sys
import time

import numpy as np

from hoarch.core import box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, openings as O, roof as R, secondempire as SE
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, foundation, lip_keep, wall_shell

NAME = "Beauvais"
COLORS = {"PorchDeck": "#F1E8D2", "Planks": "#7A5A3C",       # the planked veranda floor: two colours, one change
          "Peach": "#E2A887", "Cream": "#F1E8D2", "Forest": "#3B5233", "Slate": "#5A6458", "Iron": "#232528",
          "Stone": "#8A8070", "Windows_Doors": "#F1E8D2", "Addins": "#5A6458"}
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks", "Peach": "walls", "Cream": "trim", "Forest": "accent",
              "Slate": "roof", "Iron": "iron", "Stone": "stone", "Windows_Doors": "trim", "Addins": "roof", "Sash": "sash",
              "Door": "door", "Glass": "glass"}
PALETTE = {"walls": ["#E2A887", 0.8, 0.0], "trim": ["#F1E8D2", 0.65, 0.0], "accent": ["#3B5233", 0.5, 0.0],
           "roof": ["#5A6458", 0.75, 0.0], "iron": ["#232528", 0.45, 0.3], "stone": ["#8A8070", 0.9, 0.0],
           "planks": ["#7A5A3C", 0.75, 0.0], "sash": ["#24302A", 0.45, 0.0], "door": ["#3B5233", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Beauvais)
LEDGE = 1.4
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="ovalbar", role="Cream"),
    dict(kind="frieze", h=6.6, b=1.2, orn="sunflowers", role="Forest"),
    dict(kind="course", h=1.8, b=1.4, orn="interarcade", role="Cream"),
    dict(kind="bed", h=2.2, b=1.4, P=7.2, role="Cream", brackets=dict(style="lyreconsole", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.8, b=1.4, P=8.0, orn="cavetto", role="Forest")])
CREST_COURSE = dict(h=2.0, b=0.6, orn=SE.ovalbar, role="Cream")
CREST_CROWN = dict(h=2.6, P=3.4, kind="cyma", role="Forest", blocks=(0.9, 5.0))
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (all on the 0.2 mm grid)
ZF = 13.0
ZE = ZF + 46.0
ZW = ZE + HE
MZ0 = ZW
MH = 40.0                   # the bedroom storey
MZ1 = MZ0 + MH
DK = EAVE["layers"][-1]["P"] + 0.2
D_TOP = -6.0
MANSARD = SE.bell_profile(DK, MZ0, D_TOP, MZ1, kick=(1.6, 1.6), power=2.0, step=8.0)
SLATE = dict(pitch=1.8, wtab=2.4, d=0.4, shape=SE.slate_chequer)
V1 = 6.4
Z_ADD = MZ0 + 6.0

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 190.0, 136.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
BLOCKS = [MAIN]
DOOR_X = X1 / 2
FRONT = (30.0, 62.0, X1 - 62.0, X1 - 30.0)
SIDES = (30.0, 68.0, 106.0)
REAR = (32.0, 64.0, X1 - 64.0, X1 - 32.0)


def _siding(f, b, reg):
    """Channel-and-bead siding; nothing in the eave band."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    return SE.channelbead(reg, datum=1.8)


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    win = SE.window_beauvais()
    front = SE.door_beauvais()
    back = SE.door_beauvais_back()

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    add(DOOR_X, 0, 0.4, front, "front-door", "door")
    for x in FRONT:
        add(x, 0, V1, win, f"S{x:.0f}")
    for y in SIDES:
        add(0, y, V1, win, f"W{y:.0f}")
        add(X1, y, V1, win, f"E{y:.0f}")
    for x in REAR:
        add(x, Y1, V1, win, f"N{x:.0f}")
    add(DOOR_X, Y1, 0.4, back, "back-door", "door")
    return L


OPENINGS = _openings()
ADDINS = ([(x, 0.0, "one") for x in FRONT] + [(DOOR_X, 0.0, "twin")] + [(X1, y, "one") for y in SIDES]
          + [(x, Y1, "one") for x in REAR] + [(0.0, y, "one") for y in SIDES])


def _frame_on(x, y, z, w0):
    e, u = MAIN.locate(x, y)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, z - ZF, w0)
    return A


# ------------------------------------------------------------------ build
def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    allcs = MAIN.cs
    undress = [slab(offset(allcs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    walls = wall_shell(BLOCKS, OPENINGS, t=3.0, belt=None, corners="bobbinboard", siding=_siding, water_table=True,
                       undress=undress) - lip_keep(allcs, 3.0, ZF, 1.2)
    kit.add("WALLS", "Peach", walls + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    kit.add("FOUNDATION", "Stone", foundation(BLOCKS, 0.0, ZF, style="pebbledash"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Cream", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{tag}", group="inserts",
                               render=zones))
    print("walls + cornice + inserts", round(time.time() - t0, 1))

    # --- the bell-cast mansard (upside down): the bedroom storey, its add-ins, crest, deck, cresting
    mans, mtex, inner = R.mansard(MAIN.pts, MANSARD, t=2.6, tex=SLATE)
    one, twin = SE.addin_beauvais(), SE.addin_beauvais(twin=True)
    specs = [one if k == "one" else twin for _, _, k in ADDINS]
    pl = [SE.addin_place(sp, MANSARD, Z_ADD) for sp in specs]
    depth = max(d for _, d in pl)
    keeps, flashes = [], []
    for k, ((x, y, kind), sp, (w0, _)) in enumerate(zip(ADDINS, specs, pl)):
        A = _frame_on(x, y, Z_ADD, w0)
        a = SE.addin(sp, depth)
        keeps.append(a["keep"].transform(A))
        flashes.append(a["flash"].transform(A))
        zones = [("Glass", a["glass"].transform(A)), ("Slate", (a["plug"] - a["glass"]).transform(A)),
                 ("Cream", a["frame"].transform(A))]
        kit.add(f"ADDIN-{k}", "Addins", a["solid"].transform(A), P=inv34(A), change=(round(depth, 1), "Cream"),
                key=f"ADDIN-{kind}", group="addins", render=zones)
    C = SE.crest_ring(MAIN.pts, D_TOP, MZ1, D_TOP - inner(MZ1), CREST_COURSE, CREST_CROWN)
    kit.add("MANSARD", "Slate", mans + (mtex - union(flashes)) - union(keeps) - C["groove"], P=print_flip(), group="roof")
    kit.add("CREST", "Forest", C["solid"], P=print_flip(), change=C["change"], group="roof", render=C["zones"])
    zdeck = C["z_top"]
    chims = [(44.0, 70.0), (X1 - 44.0, 70.0)]
    pads = union([box([x - 5.6, y - 4.8, zdeck - 0.6], [x + 5.6, y + 4.8, zdeck + 1]) for x, y in chims])
    dcs = poly(R.offset_path(C["path"], -1.6))
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + 2.6, x1, 5.2)]) ^ dcs
    kit.add("ROOF-deck", "Slate", C["deck"] + slab(seams, zdeck - 0.01, zdeck + 0.4) - pads, group="roof")
    for i, seg, A, L in SE.cresting_strips(C["path"], zdeck, C["P"] - 1.4, SE.printable(SE.fence_beauvais), 7.2):
        kit.add(f"CREST-iron-{i}", "Iron", seg, P=inv34(A), key=f"CREST-iron-{round(L, 1)}", group="roof")
    for k, (x, y) in enumerate(chims):
        ch = SE.chimney_beauvais(w=10.0, d=8.4, h=24.0).translate([x, y, zdeck - 0.6])
        kit.add(f"CHIMNEY-{k}", "Peach", ch, key="CHIMNEY", group="roof")
    print("roof", round(time.time() - t0, 1), "plug", depth)

    # --- the veranda: across the front and down both sides
    H_floor = ZF - 1.4
    post_h = ZE - LEDGE - 0.4 - 2.0 - 5.6 - H_floor
    D, YB, w_ = 20.0, 100.0, -1.4
    xw, xe, yf = -D, X1 + D, -D
    pts = [(w_, YB), (xw, YB), (xw, yf), (xe, yf), (xe, YB), (X1 - w_, YB), (X1 - w_, w_), (w_, w_)]
    Ls, Lf, Le = YB - yf, xe - xw, w_ - xw
    door_u = DOOR_X - xw
    side = [1.6, 30.0, 60.0, 90.0, Ls - 1.6]
    runs = [dict(a=(w_, YB), b=(xw, YB), posts=[1.7, Le - 1.6]),
            dict(a=(xw, YB), b=(xw, yf), posts=side),
            dict(a=(xw, yf), b=(xe, yf), posts=[1.6, 34.0, 66.0, door_u - 13.0, door_u + 13.0, Lf - 66.0, Lf - 34.0, Lf - 1.6]),
            dict(a=(xe, yf), b=(xe, YB), posts=side),
            dict(a=(xe, YB), b=(X1 - w_, YB), posts=[1.6, Le - 1.7])]
    P = FT.porch_turned(pts, runs, H_floor, post_h, steps_at=[(2, door_u, 20.0)], planks=dict(pitch=1.4, border=1.6),
                        joined=True, post="twinvase", rail="ringstack", arcade="scrollarch", skirt="basketweave",
                        pier_tex="stone", roof_edge="icicles", top=True)
    P["top"] = P["top"] + P["roof"].translate([0.0, 0.0, -0.1])      # the roof only touches the beams: fuse them
    fkeep = slab(offset(allcs, 1.7), -1, ZF + 1.3)
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    deck_ = P["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck_, P=print_flip(), group="porch",
            render=FT.plank_zones(deck_, H_floor, "Planks", "PorchDeck"))
    bld_keep = MAIN.solid(grow=1.45, dz0=-20, dz1=300)
    FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_keep, "Cream", "Cream", tin_col="Slate", tin="flat")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Stone", sm.transform(A) - fkeep, group="porch")
    e, u = MAIN.locate(DOOR_X, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Stone", FT.steps(15.0, ZF - 0.6, 5).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("CREST-iron")]:
        FT.key_into(kit, p_.name, ["CREST"], (0, 0, -1), depth=0.6)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "beauvais")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "beauvais.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Addins"))
