"""The Rochambeau -- an original HO-scale (1:87.1) Second Empire house of the mansard batch
(houses 81 to 90), on the batch's roof system (hoarch.secondempire).

A formal villa of sage stucco scored as ashlar, chamfered quoins at every corner, ivory dressings
and burgundy accents, on a bluestone base with a blind arcade. A straight mansard of purple slate
laid with diamond-cut crosses; two-storey bays on the east and west under mansard hoods of their
own that run into the main roof, each with its crest, deck and cresting; fourteen add-ins with
scrolled cheeks. A portico on banded columns before the door, an iron balustrade on its roof; a
veranda down the east side.

- Ground-floor windows segmental in Gibbs surrounds with voussoirs and a tall keystone; upper
  windows round-headed under archivolts on consoles, over balconettes; a double door under a
  radiating transom in a Gibbs surround, a scrolled keystone and a cornice on consoles.
- Storey joint: an ivory running dog, a burgundy frieze of ribboned medallions, an ivory crown.
- Eave: ivory triple dentils, a burgundy frieze of acanthus, a running dog, a soffit on cushion
  consoles and a burgundy crown.
- Crests: an ivory running dog under a burgundy cyma reversa crown on block modillions.

usage: python3 -m hoarch.buildings.rochambeau [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, openings as O, roof as R, secondempire as SE
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, foundation, lip_keep, stacked_shells

NAME = "Rochambeau"
COLORS = {"PorchDeck": "#EEE7D3", "Planks": "#7A5A3C",       # the planked porch floors: two colours, one change
          "Stucco": "#9DAA88", "Ivory": "#EEE7D3", "Burgundy": "#6B2633", "Slate": "#54495E", "Iron": "#232528",
          "Bluestone": "#5E6670", "Windows_Doors": "#EEE7D3", "Addins": "#54495E"}
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks", "Stucco": "walls", "Ivory": "trim", "Burgundy": "accent",
              "Slate": "roof", "Iron": "iron", "Bluestone": "stone", "Windows_Doors": "trim", "Addins": "roof", "Sash": "sash",
              "Door": "door", "Glass": "glass"}
PALETTE = {"walls": ["#9DAA88", 0.85, 0.0], "trim": ["#EEE7D3", 0.65, 0.0], "accent": ["#6B2633", 0.5, 0.0],
           "roof": ["#54495E", 0.75, 0.0], "iron": ["#232528", 0.45, 0.3], "stone": ["#5E6670", 0.9, 0.0],
           "planks": ["#7A5A3C", 0.75, 0.0], "sash": ["#2A2428", 0.45, 0.0], "door": ["#6B2633", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Rochambeau)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="runningdog", role="Ivory"),
    dict(kind="frieze", h=5.4, b=1.2, orn="ribbonmedallions", role="Burgundy"),
    dict(kind="crown", h=2.2, b=1.4, P=3.8, orn="stepped", role="Ivory")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.6, b=1.0, orn="tripledentil", role="Ivory"),
    dict(kind="frieze", h=6.4, b=1.2, orn="acanthusfan", role="Burgundy"),
    dict(kind="course", h=1.6, b=1.4, orn="runningdog", role="Ivory"),
    dict(kind="bed", h=2.2, b=1.4, P=7.0, role="Ivory", brackets=dict(style="cushionconsole", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.8, b=1.4, P=7.8, orn="ogee_fillet", role="Burgundy")])
CREST_COURSE = dict(h=2.0, b=0.6, orn=SE.runningdog, role="Ivory")
CREST_CROWN = dict(h=2.6, P=3.4, kind="reverse", role="Burgundy", blocks=(0.9, 5.0))
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (all on the 0.2 mm grid)
ZF = 13.0
S1 = ZF + 42.0
ZE = S1 + RJ + 38.0
ZW = ZE + HE
MZ0 = ZW
MH, BMH = 32.0, 18.0       # the main mansard, the bays' hoods
MZ1, BZ1 = MZ0 + MH, MZ0 + BMH
DK = EAVE["layers"][-1]["P"] + 0.2
D_TOP, BD_TOP = -1.6, -3.0
MANSARD = [(DK, MZ0), (DK - 1.4, MZ0 + 1.4), (D_TOP, MZ1)]
HOOD = [(DK, MZ0), (DK - 1.4, MZ0 + 1.4), (BD_TOP, BZ1)]
SLATE = dict(pitch=1.8, wtab=2.4, d=0.4, shape=SE.slate_crosses)
V1, V2 = 6.4, S1 + RJ + 5.0 - ZF
Z_ADD = MZ0 + 3.2
Z_ADDB = MZ0 + 2.4

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 176.0, 128.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
BY0, BY1, BP, BO = 36.0, 80.0, 20.0, 8.0          # the side bays: from y, to y, projection, overlap into the house
BAYW = Block("bay-west", [(-BP, BY0), (BO, BY0), (BO, BY1), (-BP, BY1)], ZF, ZW)
BAYE = Block("bay-east", [(X1 - BO, BY0), (X1 + BP, BY0), (X1 + BP, BY1), (X1 - BO, BY1)], ZF, ZW)
BLOCKS = [MAIN, BAYW, BAYE]
BAYS = [(BAYW, "BAYW", (-BP, (BY0 + BY1) / 2)), (BAYE, "BAYE", (X1 + BP, (BY0 + BY1) / 2))]
DOOR_X = X1 / 2


def _stucco(f, b, reg):
    """Scored stucco; nothing in the cornice band."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    return SE.scoredstucco(reg, datum=1.8)


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    lo = SE.window_rochambeau_lower()
    up = SE.window_rochambeau_upper()
    front = SE.door_rochambeau()
    back = SE.door_rochambeau_back()

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    add(MAIN, DOOR_X, 0, 0.4, front, "front-door", "door")
    for x in (26.0, 54.0, X1 - 54.0, X1 - 26.0):
        add(MAIN, x, 0, V1, lo, f"S{x:.0f}-1")
    for x in (26.0, 54.0, DOOR_X, X1 - 54.0, X1 - 26.0):
        add(MAIN, x, 0, V2, up, f"S{x:.0f}-2")
    for bay, tag, (x, _) in BAYS:                                      # the bays' outer faces: two lights each floor
        for y in (BY0 + 12.0, BY1 - 12.0):
            add(bay, x, y, V1, lo, f"{tag}{y:.0f}-1")
            add(bay, x, y, V2, up, f"{tag}{y:.0f}-2")
    for xw, tag in ((0.0, "W"), (X1, "E")):
        for y in (18.0, 104.0):
            if not (tag == "E" and y == 104.0):
                add(MAIN, xw, y, V1, lo, f"{tag}{y:.0f}-1")
            add(MAIN, xw, y, V2, up, f"{tag}{y:.0f}-2")
    add(MAIN, X1, 104.0, 0.4, back, "side-door", "door")
    for x in (30.0, 58.0, X1 - 58.0, X1 - 30.0):
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
    for x in (30.0, 58.0, DOOR_X, X1 - 58.0, X1 - 30.0):
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, DOOR_X, Y1, 0.4, back, "back-door", "door")
    return L


OPENINGS = _openings()
ADDINS = [(26.0, 0.0), (54.0, 0.0), (DOOR_X, 0.0), (X1 - 54.0, 0.0), (X1 - 26.0, 0.0), (X1, 18.0), (X1, 104.0),
          (X1 - 30.0, Y1), (DOOR_X, Y1), (30.0, Y1), (0.0, 104.0), (0.0, 18.0)]


def _frame_on(block, x, y, z, w0):
    e, u = block.locate(x, y)
    f = block.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, z - ZF, w0)
    return A


def _volume(path, prof, top=0.0):
    """The solid inside a mansard's outer face (to cut the other roof back to it), carried up
    ``top`` past its last point."""
    P, Mi = R._edges(path)

    def ring(d, z):
        return np.c_[P + d * Mi, np.full(len(P), z)]
    segs = list(zip(prof[:-1], prof[1:])) + ([(prof[-1], (prof[-1][0], prof[-1][1] + top))] if top else [])
    return union([M.hull_points(np.vstack([ring(d0, z0), ring(d1, z1)]).tolist()) for (d0, z0), (d1, z1) in segs])


def _addins(kit, places, prof, z_sill, sp, tag):
    """One roof's add-ins (one plug length each roof, so they share one colour change); places
    are (block, x, y). Returns (pocket cutters, slate clearances) in world."""
    pl = [SE.addin_place(sp, prof, z_sill) for _ in places]
    depth = max(d for _, d in pl)
    keeps, flashes = [], []
    for k, ((block, x, y), (w0, _)) in enumerate(zip(places, pl)):
        A = _frame_on(block, x, y, z_sill, w0)
        a = SE.addin(sp, depth)
        keeps.append(a["keep"].transform(A))
        flashes.append(a["flash"].transform(A))
        zones = [("Glass", a["glass"].transform(A)), ("Slate", (a["plug"] - a["glass"]).transform(A)),
                 ("Ivory", a["frame"].transform(A))]
        kit.add(f"{tag}-{k}", "Addins", a["solid"].transform(A), P=inv34(A), change=(round(depth, 1), "Ivory"),
                key=tag, group="addins", render=zones)
    print(tag, "plug", depth)
    return union(keeps), union(flashes)


def _deck(C, z, pads=None):
    dcs = poly(R.offset_path(C["path"], -1.6))
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + 2.6, x1, 5.2)]) ^ dcs
    d = C["deck"] + slab(seams, z - 0.01, z + 0.4)
    return d - pads if pads is not None else d


# ------------------------------------------------------------------ build
def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    allcs = cs_union([b.cs for b in BLOCKS])
    eave_path = max(allcs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(allcs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="chamferquoin", siding=_stucco,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        clear=[lip_keep(allcs, 3.0, ZF, 1.2)])
    kit.add("WALLS-1", "Stucco", st["shells"][0], group="walls")
    kit.add("JOINT", "Stucco", st["rings"][0], group="walls")
    kit.add("WALLS-2", "Stucco", st["shells"][1] + CO.ledge(eave_path, ZE, LEDGE), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    kit.add("FOUNDATION", "Bluestone", foundation(BLOCKS, 0.0, ZF, style="blindarcade"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Ivory", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the main mansard and the bays' hoods (upside down); each is cut back to the other's slates
    main_vol = _volume(MAIN.pts, [(d + 0.5, z) for d, z in MANSARD])
    mans, mtex, inner = R.mansard(MAIN.pts, MANSARD, t=2.6, tex=SLATE)
    sp = SE.addin_rochambeau()
    spb = SE.addin_rochambeau(w=4.4, h=8.4, A=0.8)
    mk, mf = _addins(kit, [(MAIN, x, y) for x, y in ADDINS], MANSARD, Z_ADD, sp, "ADDIN")
    bk, bf = _addins(kit, [(bay, x, y) for bay, _, (x, y) in BAYS], HOOD, Z_ADDB, spb, "ADDIN-B")
    bay_vols = union([_volume(bay.pts, [(d + 0.5, z) for d, z in HOOD]) for bay, _, _ in BAYS])
    C = SE.crest_ring(MAIN.pts, D_TOP, MZ1, D_TOP - inner(MZ1), CREST_COURSE, CREST_CROWN)
    kit.add("MANSARD", "Slate", (mans + (mtex - mf)) - mk - bay_vols - C["groove"], P=print_flip(), group="roof")
    kit.add("CREST", "Burgundy", C["solid"], P=print_flip(), change=C["change"], group="roof", render=C["zones"])
    zdeck = C["z_top"]
    chims = [(40.0, 96.0), (X1 - 40.0, 96.0)]
    pads = union([box([x - 5.8, y - 5.8, zdeck - 0.6], [x + 5.8, y + 5.8, zdeck + 1]) for x, y in chims])
    kit.add("ROOF-deck", "Slate", _deck(C, zdeck, pads), group="roof")
    for i, seg, A, L in SE.cresting_strips(C["path"], zdeck, C["P"] - 1.4, SE.printable(SE.fence_rochambeau), 7.2):
        kit.add(f"CREST-iron-{i}", "Iron", seg, P=inv34(A), key=f"CREST-iron-{round(L, 1)}", group="roof")
    for k, (x, y) in enumerate(chims):
        ch = SE.chimney_rochambeau(w=10.4, d=10.4, h=25.0).translate([x, y, zdeck - 0.6])
        kit.add(f"CHIMNEY-{k}", "Stucco", ch, key="CHIMNEY", group="roof")
    for bay, tag, _ in BAYS:
        hood, htex, hin = R.mansard(bay.pts, HOOD, t=2.4, tex=SLATE)
        HC = SE.crest_ring(bay.pts, BD_TOP, BZ1, BD_TOP - hin(BZ1), CREST_COURSE, CREST_CROWN)
        kit.add(f"{tag}-HOOD", "Slate", (hood + (htex - bf)) - bk - main_vol - HC["groove"], P=print_flip(), group="bays")
        kit.add(f"{tag}-CREST", "Burgundy", HC["solid"] - main_vol, P=print_flip(), change=HC["change"], group="bays",
                render=[(r, z - main_vol) for r, z in HC["zones"]])
        bz = HC["z_top"]
        kit.add(f"{tag}-deck", "Slate", _deck(HC, bz) - main_vol, group="bays")
        for i, seg, A, L in SE.cresting_strips(HC["path"], bz, HC["P"] - 1.4, SE.printable(SE.fence_rochambeau), 6.4):
            seg = seg - main_vol
            if not seg.is_empty() and seg.volume() > 3.0:
                kit.add(f"{tag}-iron-{i}", "Iron", seg, P=inv34(A), key=f"{tag[:3]}-iron-{round(L, 1)}", group="bays")
    print("roofs", round(time.time() - t0, 1))

    # --- the portico before the door (a balustrade on its roof), the veranda down the east side
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    fkeep = slab(offset(allcs, 1.7), -1, ZF + 1.3)
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=300) for b in BLOCKS])
    xa, xb, yf, w_ = DOOR_X - 20.0, DOOR_X + 20.0, -18.0, -1.4
    Lp, Ls = xb - xa, w_ - yf
    runs = [dict(a=(xa, w_), b=(xa, yf), posts=[1.7, Ls - 1.6]),
            dict(a=(xa, yf), b=(xb, yf), posts=[1.6, 5.0, Lp - 5.0, Lp - 1.6]),
            dict(a=(xb, yf), b=(xb, w_), posts=[1.6, Ls - 1.7])]
    ys0, ys1, xv = BY1 + 1.4, Y1 - 4.0, X1 + BP - 2.0
    Le, Ln = ys1 - ys0, xv - X1 - 1.4
    vruns = [dict(a=(xv, ys0), b=(xv, ys1), posts=[1.7, 12.0, Le - 12.0, Le - 1.6]),
             dict(a=(xv, ys1), b=(X1 + 1.4, ys1), posts=[1.6, Ln - 1.7])]
    for tag, pts, rr, steps in (("PORCH", [(xa, w_), (xa, yf), (xb, yf), (xb, w_)], runs, [(1, Lp / 2, 18.0)]),
                                ("VERANDA", [(X1 + 1.4, ys0), (xv, ys0), (xv, ys1), (X1 + 1.4, ys1)], vruns,
                                 [(0, 104.0 - ys0, 14.0)])):
        P = FT.porch_turned(pts, rr, H_floor, post_h, steps_at=steps, planks=dict(pitch=1.4, border=1.6),
                            joined=True, post="bandedcolumn", rail="bellbase", arcade="wreathpierced", skirt="roundels",
                            pier_tex="stone", roof_edge="crescents", top=True)
        deck_ = P["deck"] - fkeep - bld_keep
        kit.add(f"{tag}-deck", "PorchDeck", deck_, P=print_flip(), group="porch",
                render=FT.plank_zones(deck_, H_floor, "Planks", "PorchDeck"))
        res = FT.add_porch_top(kit, tag, P, bld_keep + ins_keep, "Ivory", "Ivory", tin_col="Slate", tin="flat")
        for k, (sm, A) in enumerate(P["steps"]):
            kit.add(f"{tag}-steps-{k}", "Bluestone", sm.transform(A) - fkeep, group="porch")
        if tag == "PORCH":                     # the iron balustrade round the portico's roof
            ptop = res["ptop"]
            path = [(xa - 1.4, yf - 1.4), (xb + 1.4, yf - 1.4), (xb + 1.4, w_), (xa - 1.4, w_)]
            for i, seg, A, L in SE.cresting_strips(path, ptop, -1.0, SE.printable(SE.fence_rochambeau_balcony), 6.4):
                bb = seg.bounding_box()
                if (bb[1] + bb[4]) / 2 > w_ - 2.5:             # not along the wall
                    continue
                kit.add(f"PORCH-rail-{i}", "Iron", seg - bld_keep, P=inv34(A), group="porch")
    e, u = MAIN.locate(DOOR_X, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Bluestone", FT.steps(15.0, ZF - 0.6, 5).transform(A), group="porch")
    print("porches", round(time.time() - t0, 1))
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("CREST-iron")]:
        FT.key_into(kit, p_.name, ["CREST"], (0, 0, -1), depth=0.6)
    for p_ in [p_ for p_ in kit.parts if "-iron-" in p_.name and p_.name.startswith("BAY")]:
        FT.key_into(kit, p_.name, [p_.name.split("-iron-")[0] + "-CREST"], (0, 0, -1), depth=0.6)
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("PORCH-rail")]:
        FT.key_into(kit, p_.name, ["PORCH-top"], (0, 0, -1), depth=0.6)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "rochambeau")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "rochambeau.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Addins"))
