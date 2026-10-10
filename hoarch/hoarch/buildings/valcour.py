"""The Valcour -- an original HO-scale (1:87.1) Second Empire house of the mansard batch (houses
81 to 90), on the batch's roof system (hoarch.secondempire).

Dove-grey rusticated boarding (wood cut to look like stone) with rusticated corner piers, white
trim and navy accents, on a brick foundation of sunk panels. Its roofs swell: a convex mansard
of striped slate (every fourth column of slates cut to a diamond point) and, over a centre
pavilion, a taller convex roof; oculus add-ins in wreathed frames under little hoods, a larger
round-headed add-in under a broken scroll pediment on the pavilion; crests with their own
cornices, lozenge cresting, an urn-and-spike finial. Two brick stacks with three pots each. A
veranda down the east side on spiral-fluted posts with lozenge splats, a scalloped valance, a
crossbuck skirt and bells on its fascia; a stoop to the pavilion's door under a deep hood on long
scroll brackets.

- Ground-floor windows segmental with keystones under a triglyph frieze and a crested cap;
  upper windows round-headed under ogee-pointed hoods with knobs.
- Storey joint: a navy frieze of crossed palms, a white course of triple beads, a navy crown.
- Eave: a white course of triple beads, a navy frieze of caducei between sunk panels, a white
  cusped course, a soffit on trefoil consoles and a navy crown.
- Crests: white triple beads under a navy ovolo crown on block modillions.

usage: python3 -m hoarch.buildings.valcour [check] [export]
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

NAME = "Valcour"
COLORS = {"PorchDeck": "#F2EFE6", "Planks": "#6F5034",
          "Grey": "#9AA3A6", "White": "#F2EFE6", "Navy": "#2D3A55", "Slate": "#3F4642", "Iron": "#232528",
          "Brick": "#8E4A36", "Windows_Doors": "#F2EFE6", "Addins": "#3F4642"}
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks", "Grey": "walls", "White": "trim", "Navy": "accent", "Slate": "roof",
              "Iron": "iron", "Brick": "brick", "Windows_Doors": "trim", "Addins": "roof", "Sash": "sash", "Door": "door",
              "Glass": "glass"}
PALETTE = {"walls": ["#9AA3A6", 0.8, 0.0], "trim": ["#F2EFE6", 0.6, 0.0], "accent": ["#2D3A55", 0.5, 0.0],
           "roof": ["#3F4642", 0.75, 0.0], "iron": ["#232528", 0.45, 0.3], "brick": ["#8E4A36", 0.85, 0.0],
           "planks": ["#6F5034", 0.75, 0.0], "sash": ["#22262E", 0.45, 0.0], "door": ["#2D3A55", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Valcour)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.4, b=1.2, orn="crossedpalms", role="Navy"),
    dict(kind="course", h=1.6, b=1.4, orn="tribead", role="White"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="cyma", role="Navy")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.6, b=1.0, orn="tribead", role="White"),
    dict(kind="frieze", h=6.4, b=1.2, orn="caducei", role="Navy"),
    dict(kind="course", h=1.4, b=1.4, orn="cusps", role="White"),
    dict(kind="bed", h=2.2, b=1.4, P=6.6, role="White", brackets=dict(style="trefoilconsole", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.8, b=1.4, P=7.4, orn="cyma", role="Navy")])
CREST_COURSE = dict(h=2.0, b=0.6, orn=SE.tribeads, role="White")
CREST_CROWN = dict(h=2.6, P=3.4, kind="ovolo", role="Navy", blocks=(0.9, 5.0))
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (all on the 0.2 mm grid)
ZF = 13.0
S1 = ZF + 42.0
ZE = S1 + RJ + 38.0
ZW = ZE + HE
MZ0 = ZW
MH, PMH = 30.0, 44.0
MZ1, PZ1 = MZ0 + MH, MZ0 + PMH
DK = EAVE["layers"][-1]["P"] + 0.2
D_TOP, PD_TOP = -5.0, -7.0
MANSARD = SE.bell_profile(DK, MZ0, D_TOP, MZ1, power=1.8, step=7.2, convex=True)
PAV_MANSARD = SE.bell_profile(DK, MZ0, PD_TOP, PZ1, power=1.8, step=7.2, convex=True)
SLATE = dict(pitch=1.8, wtab=2.4, d=0.4, shape=SE.slate_stripes)
V1, V2 = 6.4, S1 + RJ + 5.0 - ZF
Z_ADD = MZ0 + 3.2

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 190.0, 132.0
PX0, PX1, PY0, PY1 = 70.0, 120.0, -10.0, 24.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
PAV = Block("pavilion", [(PX0, PY0), (PX1, PY0), (PX1, PY1), (PX0, PY1)], ZF, ZW)
BLOCKS = [MAIN, PAV]
PCX = (PX0 + PX1) / 2


def _siding(f, b, reg):
    """Rusticated boarding; nothing in the eave band."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    return SE.rusticboard(reg, datum=1.8)


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    lo = SE.window_valcour_lower()
    up = SE.window_valcour_upper()
    front = SE.door_valcour()
    side = SE.door_valcour_side()

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    add(PAV, PCX, PY0, 0.4, front, "front-door", "door")
    add(PAV, PCX, PY0, V2, up, "P-2")
    for x in (22.0, 48.0, 142.0, 168.0):
        add(MAIN, x, 0, V1, lo, f"S{x:.0f}-1")
        add(MAIN, x, 0, V2, up, f"S{x:.0f}-2")
    for y in (26.0, 66.0, 106.0):
        add(MAIN, 0, y, V1, lo, f"W{y:.0f}-1")
        add(MAIN, 0, y, V2, up, f"W{y:.0f}-2")
        add(MAIN, X1, y, V2, up, f"E{y:.0f}-2")
    for y in (26.0, 106.0):
        add(MAIN, X1, y, V1, lo, f"E{y:.0f}-1")
    add(MAIN, X1, 66.0, 0.4, side, "side-door", "door")
    for x in (26.0, 70.0, 164.0):
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
    for x in (26.0, 70.0, 120.0, 164.0):
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, 120.0, Y1, 0.4, side, "back-door", "door")
    return L


OPENINGS = _openings()
ADDINS = [(22.0, 0.0), (48.0, 0.0), (142.0, 0.0), (168.0, 0.0), (X1, 26.0), (X1, 66.0), (X1, 106.0),
          (164.0, Y1), (120.0, Y1), (70.0, Y1), (26.0, Y1), (0.0, 106.0), (0.0, 66.0), (0.0, 26.0)]
PAV_ADDINS = [(PCX, PY0)]


def _frame_on(block, x, y, z, w0):
    e, u = block.locate(x, y)
    f = block.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, z - ZF, w0)
    return A


def _volume(path, prof, top=0.0):
    """The solid inside a mansard's outer face, carried up ``top`` past its last point."""
    P, Mi = R._edges(path)

    def ring(d, z):
        return np.c_[P + d * Mi, np.full(len(P), z)]
    segs = list(zip(prof[:-1], prof[1:])) + ([(prof[-1], (prof[-1][0], prof[-1][1] + top))] if top else [])
    return union([M.hull_points(np.vstack([ring(d0, z0), ring(d1, z1)]).tolist()) for (d0, z0), (d1, z1) in segs])


def _addins(kit, block, places, prof, z_sill, sp, tag):
    pl = [SE.addin_place(sp, prof, z_sill) for _ in places]
    depth = max(d for _, d in pl)
    keeps, flashes = [], []
    for k, ((x, y), (w0, _)) in enumerate(zip(places, pl)):
        A = _frame_on(block, x, y, z_sill, w0)
        a = SE.addin(sp, depth)
        keeps.append(a["keep"].transform(A))
        flashes.append(a["flash"].transform(A))
        zones = [("Glass", a["glass"].transform(A)), ("Slate", (a["plug"] - a["glass"]).transform(A)),
                 ("White", a["frame"].transform(A))]
        kit.add(f"{tag}-{k}", "Addins", a["solid"].transform(A), P=inv34(A), change=(round(depth, 1), "White"),
                key=tag, group="addins", render=zones)
    print(tag, "plug", depth)
    return union(keeps), union(flashes)


# ------------------------------------------------------------------ build
def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    allcs = cs_union([b.cs for b in BLOCKS])
    eave_path = max(allcs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(allcs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="rusticpier", siding=_siding,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        clear=[lip_keep(allcs, 3.0, ZF, 1.2)])
    kit.add("WALLS-1", "Grey", st["shells"][0], group="walls")
    kit.add("JOINT", "Grey", st["rings"][0], group="walls")
    kit.add("WALLS-2", "Grey", st["shells"][1] + CO.ledge(eave_path, ZE, LEDGE), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    kit.add("FOUNDATION", "Brick", foundation(BLOCKS, 0.0, ZF, style="brickpanel"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "White", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the two convex mansards (upside down); the pavilion's rises through the main one
    pav_vol = _volume(PAV.pts, [(d + 0.5, z) for d, z in PAV_MANSARD], top=20.0)
    main_vol = _volume(MAIN.pts, [(d + 0.5, z) for d, z in MANSARD])
    mans, mtex, inner = R.mansard(MAIN.pts, MANSARD, t=2.6, tex=SLATE)
    pmans, ptex, pinner = R.mansard(PAV.pts, PAV_MANSARD, t=2.6, tex=SLATE)
    mk, mf = _addins(kit, MAIN, ADDINS, MANSARD, Z_ADD, SE.addin_valcour_oculus(), "ADDIN")
    pk, pf = _addins(kit, PAV, PAV_ADDINS, PAV_MANSARD, Z_ADD, SE.addin_valcour_big(), "ADDIN-P")
    C = SE.crest_ring(MAIN.pts, D_TOP, MZ1, D_TOP - inner(MZ1), CREST_COURSE, CREST_CROWN)
    PC = SE.crest_ring(PAV.pts, PD_TOP, PZ1, PD_TOP - pinner(PZ1), CREST_COURSE, CREST_CROWN)
    kit.add("MANSARD", "Slate", (mans + (mtex - mf)) - mk - pav_vol - C["groove"], P=print_flip(), group="roof")
    kit.add("MANSARD-P", "Slate", (pmans + (ptex - pf)) - pk - main_vol - PC["groove"], P=print_flip(), group="pavilion")
    print("mansards + add-ins", round(time.time() - t0, 1))

    # --- crests, decks, cresting, the pavilion's finial, chimneys
    kit.add("CREST", "Navy", C["solid"] - pav_vol, P=print_flip(), change=C["change"], group="roof",
            render=[(r, z - pav_vol) for r, z in C["zones"]])
    zdeck = C["z_top"]
    chims = [(24.0, 100.0), (166.0, 100.0)]
    pads = union([box([x - 5.4, y - 6.6, zdeck - 0.6], [x + 5.4, y + 6.6, zdeck + 1]) for x, y in chims])
    dcs = poly(R.offset_path(C["path"], -1.6))
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + 2.6, x1, 5.2)]) ^ dcs
    kit.add("ROOF-deck", "Slate", C["deck"] + slab(seams, zdeck - 0.01, zdeck + 0.4) - pads - pav_vol, group="roof")
    for i, seg_, A, L in SE.cresting_strips(C["path"], zdeck, C["P"] - 1.4, SE.printable(SE.fence_valcour), 6.8):
        for j, piece in enumerate((seg_ - pav_vol).decompose()):
            if piece.volume() > 3.0:
                kit.add(f"CREST-iron-{i}{'abc'[j]}", "Iron", piece, P=inv34(A), group="roof")
    for k, (x, y) in enumerate(chims):
        ch = SE.chimney_valcour(w=9.6, d=12.0, h=24.0).translate([x, y, zdeck - 0.6])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof")
    kit.add("PAV-CREST", "Navy", PC["solid"], P=print_flip(), change=PC["change"], group="pavilion", render=PC["zones"])
    pz = PC["z_top"]
    pcs = poly(R.offset_path(PC["path"], -1.6))
    px0_, py0_, px1_, py1_ = pcs.bounds()
    pseams = cs_union([rect(x - 0.25, py0_, x + 0.25, py1_) for x in np.arange(px0_ + 2.6, px1_, 5.2)]) ^ pcs
    kit.add("PAV-deck", "Slate", PC["deck"] + slab(pseams, pz - 0.01, pz + 0.4), group="pavilion")
    for i, seg_, A, L in SE.cresting_strips(PC["path"], pz, PC["P"] - 1.4, SE.printable(SE.fence_valcour), 7.2):
        kit.add(f"PAV-iron-{i}", "Iron", seg_, P=inv34(A), key=f"PAV-iron-{round(L, 1)}", group="pavilion")
    tc = (PCX, (PY0 + PY1) / 2)
    kit.add("PAV-finial", "Iron", SE.finial_urnspike(10.0).translate([tc[0], tc[1], pz + 0.39]), group="pavilion")
    print("roofs", round(time.time() - t0, 1))

    # --- veranda down the east side, the stoop to the pavilion door
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    xa, xb, ya, yb = X1 + 1.4, X1 + 24.0, 6.0, 126.0
    pts = [(xa, ya), (xb, ya), (xb, yb), (xa, yb)]
    Le = yb - ya
    runs = [dict(a=(xa, ya), b=(xb, ya), posts=[1.7, (xb - xa) - 1.6]),
            dict(a=(xb, ya), b=(xb, yb), posts=[1.6, 30.0, 60.0 - 11.0, 60.0 + 11.0, Le - 30.0, Le - 1.6]),
            dict(a=(xb, yb), b=(xa, yb), posts=[1.6, (xb - xa) - 1.7])]
    P = FT.porch_turned(pts, runs, H_floor, post_h, steps_at=[(1, 60.0, 18.0)], planks=dict(pitch=1.4, border=1.6),
                        joined=True, post="spiralflute", rail="lozengesplats", arcade="scallopvalance", skirt="crossbuck",
                        pier_tex="brick", roof_edge="bellcourse", top=True)
    fkeep = slab(offset(allcs, 1.7), -1, ZF + 1.3)
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    deck_ = P["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck_, P=print_flip(), group="porch",
            render=FT.plank_zones(deck_, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=300) for b in BLOCKS])
    FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_keep, "White", "White", tin_col="Slate", tin="flat")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Brick", sm.transform(A) - fkeep, group="porch")
    for blk, x, y, w_, nm in ((PAV, PCX, PY0, 22.0, "STOOP-front"), (MAIN, 120.0, Y1, 15.0, "STOOP-back")):
        e, u = blk.locate(x, y)
        f = blk.facades()[e]
        A = f.A.copy()
        A[:, 3] = f.world(u, -ZF, 1.6)
        kit.add(nm, "Brick", FT.steps(w_, ZF - 0.6, 6 if w_ > 20 else 5).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("CREST-iron")]:
        FT.key_into(kit, p_.name, ["CREST"], (0, 0, -1), depth=0.6)
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("PAV-iron")]:
        FT.key_into(kit, p_.name, ["PAV-CREST"], (0, 0, -1), depth=0.6)
    FT.crown(kit, "PAV-finial", "PAV-deck")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "valcour")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "valcour.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Addins"))
