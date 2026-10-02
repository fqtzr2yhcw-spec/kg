"""The Lafayette -- an original HO-scale (1:87.1) Second Empire house: the second pilot of the
mansard batch (houses 81 to 90), on the batch's roof system (hoarch.secondempire).

Sage clapboard laid in board lengths, wooden quoins, ivory trim and plum accents, on a
chequered stone foundation. A pavilion at the front-west corner breaks forward and carries a
taller bell-cast mansard that rises through the main roof; both roofs are trefoil-cut purple
slate. The main mansard holds segmental add-ins under pediments with shells, alternating with
oval add-ins keyed at their points; the pavilion has a larger add-in on each street face. Crests
with their own cornices, palmette cresting, a torch finial on the pavilion, two rusticated
stucco stacks. A veranda along the front and down the east side on reeded vase posts, with
fleur-de-lis splats, rope festoons, a scalloped skirt and pendants on its fascia.

- Ground-floor windows under cornice hoods on long consoles, with a garland frieze and a sawn
  crest; upper windows round-headed under hood moulds curling into volutes; a double door with
  octagon-headed lights under a star transom and a segmental hood on long consoles.
- Storey joint: a plum frieze of cockades with bow knots, an ivory course of lamb's tongues and
  a plum ogee crown.
- Eave: an ivory ribbon-and-stick course, a plum frieze of candelabra between sunk panels, an
  ivory course of beaded dentils, an ivory soffit on leaf modillions and a plum cyma-reversa
  crown.
- Crests (both roofs): ivory ribbon bands under a plum cavetto crown on block modillions.

usage: python3 -m hoarch.buildings.lafayette [check] [export]
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

NAME = "Lafayette"
COLORS = {"PorchDeck": "#E6DFCB", "Planks": "#6F5034",       # the planked veranda floor: two colours, one change
          "Siding": "#8C9C84", "Ivory": "#E6DFCB", "Plum": "#5E3A4E", "Slate": "#57505C", "Iron": "#232528",
          "Stone": "#8B8378", "Windows_Doors": "#E6DFCB", "Addins": "#57505C"}
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks", "Siding": "siding", "Ivory": "trim", "Plum": "accent",
              "Slate": "roof", "Iron": "iron", "Stone": "stone", "Windows_Doors": "trim", "Addins": "roof", "Sash": "sash",
              "Door": "door", "Glass": "glass"}
PALETTE = {"siding": ["#8C9C84", 0.8, 0.0], "trim": ["#E6DFCB", 0.6, 0.0], "accent": ["#5E3A4E", 0.55, 0.0],
           "roof": ["#57505C", 0.75, 0.0], "iron": ["#232528", 0.45, 0.3], "stone": ["#8B8378", 0.9, 0.0],
           "planks": ["#6F5034", 0.75, 0.0], "sash": ["#2E3A2C", 0.45, 0.0], "door": ["#4A2A33", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Lafayette)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.0, b=1.2, orn="cockades", role="Plum"),
    dict(kind="course", h=1.8, b=1.4, orn="lambstongue", role="Ivory"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="ogee_fillet", role="Plum")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="ribbonstick", role="Ivory"),
    dict(kind="frieze", h=6.4, b=1.2, orn="candelabra", role="Plum"),
    dict(kind="course", h=1.6, b=1.4, orn="beaddentil", role="Ivory"),
    dict(kind="bed", h=2.4, b=1.4, P=6.6, role="Ivory", brackets=dict(style="leafmod", t=1.6, h=2.8)),
    dict(kind="crown", h=2.8, b=1.4, P=7.4, orn="reverse", role="Plum")])
CREST_COURSE = dict(h=2.0, b=0.6, orn=SE.ribbonbands, role="Ivory")
CREST_CROWN = dict(h=2.6, P=3.6, kind="cavetto", role="Plum", blocks=(0.9, 4.8))
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (all on the 0.2 mm grid)
ZF = 14.0
S1 = ZF + 42.0
ZE = S1 + RJ + 38.0
ZW = ZE + HE
MZ0 = ZW
MH, PMH = 30.0, 46.0       # the main mansard, the pavilion's
MZ1, PZ1 = MZ0 + MH, MZ0 + PMH
DK = EAVE["layers"][-1]["P"] + 0.2
D_TOP, PD_TOP = -2.4, -6.0
MANSARD = SE.bell_profile(DK, MZ0, D_TOP, MZ1, power=1.5, step=8.0)
PAV_MANSARD = SE.bell_profile(DK, MZ0, PD_TOP, PZ1, power=1.9, step=8.0)
SLATE = dict(pitch=2.0, wtab=2.8, d=0.4, shape="trefoil")
V1, V2 = 7.0, S1 + RJ + 5.0 - ZF
Z_ADD = MZ0 + 3.2          # the main add-ins' sill line
Z_ADDP = MZ0 + 7.0         # the pavilion's

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 186.0, 134.0
PX0, PX1, PY0, PY1 = -8.0, 60.0, -22.0, 44.0       # the pavilion breaks forward 22 and out 8 on the west
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
PAV = Block("pavilion", [(PX0, PY0), (PX1, PY0), (PX1, PY1), (PX0, PY1)], ZF, ZW)
BLOCKS = [MAIN, PAV]


def _siding(f, b, reg):
    """Jointed clapboard; nothing in the eave band."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    return SE.jointed_clapboard(reg, datum=1.8)


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    lo = SE.window_lafayette_lower()
    up = SE.window_lafayette_upper()
    front = SE.door_lafayette()
    back = SE.door_lafayette_back()

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    for x in (12.0, 40.0):                                   # the pavilion's front
        add(PAV, x, PY0, V1, lo, f"P{x:.0f}-1")
        add(PAV, x, PY0, V2, up, f"P{x:.0f}-2")
    add(PAV, PX0, 11.0, V1, lo, "W11-1")                   # west: the pavilion's side, then the house
    add(PAV, PX0, 11.0, V2, up, "W11-2")
    for y in (70.0, 108.0):
        add(MAIN, 0, y, V1, lo, f"W{y:.0f}-1")
        add(MAIN, 0, y, V2, up, f"W{y:.0f}-2")
    for x in (88.0, 160.0):                                 # the front, the door between
        add(MAIN, x, 0, V1, lo, f"S{x:.0f}-1")
    for x in (88.0, 124.0, 160.0):
        add(MAIN, x, 0, V2, up, f"S{x:.0f}-2")
    add(MAIN, 124.0, 0, 0.4, front, "front-door", "door")
    for y in (26.0, 67.0, 108.0):                          # east
        add(MAIN, X1, y, V1, lo, f"E{y:.0f}-1")
        add(MAIN, X1, y, V2, up, f"E{y:.0f}-2")
    for x in (30.0, 156.0):                                 # rear
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
    for x in (30.0, 93.0, 156.0):
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, 93.0, Y1, 0.4, back, "back-door", "door")
    return L


OPENINGS = _openings()
# add-ins on the main mansard: (x, y, kind) on the wall line, segmental and oval in turn
ADDINS = [(88.0, 0.0, "seg"), (124.0, 0.0, "oval"), (160.0, 0.0, "seg"),
          (X1, 26.0, "seg"), (X1, 67.0, "oval"), (X1, 108.0, "seg"),
          (156.0, Y1, "seg"), (93.0, Y1, "oval"), (30.0, Y1, "seg"),
          (0.0, 108.0, "seg"), (0.0, 72.0, "oval")]
PAV_ADDINS = [(26.0, PY0), (PX0, 11.0)]


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


def _addins(kit, block, places, prof, z_sill, tag):
    """Add one roof's add-ins (one plug length each roof, so they share one colour change).
    Returns (pocket cutters, slate clearances) in world."""
    specs = [p[2] for p in places]
    pl = [SE.addin_place(sp, prof, z_sill) for sp in specs]
    depth = max(d for _, d in pl)
    keeps, flashes = [], []
    for k, ((x, y, sp, key), (w0, _)) in enumerate(zip([(p[0], p[1], p[2], p[3]) for p in places], pl)):
        A = _frame_on(block, x, y, z_sill, w0)
        a = SE.addin(sp, depth)
        keeps.append(a["keep"].transform(A))
        flashes.append(a["flash"].transform(A))
        zones = [("Glass", a["glass"].transform(A)), ("Slate", (a["plug"] - a["glass"]).transform(A)),
                 ("Ivory", a["frame"].transform(A))]
        kit.add(f"{tag}-{k}", "Addins", a["solid"].transform(A), P=inv34(A), change=(round(depth, 1), "Ivory"),
                key=f"{tag}-{key}", group="addins", render=zones)
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
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="woodquoin", siding=_siding,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=True, undress=undress,
                        clear=[lip_keep(allcs, 3.0, ZF, 1.2)])
    kit.add("WALLS-1", "Siding", st["shells"][0], group="walls")
    kit.add("JOINT", "Siding", st["rings"][0], group="walls")
    kit.add("WALLS-2", "Siding", st["shells"][1] + CO.ledge(eave_path, ZE, LEDGE), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    kit.add("FOUNDATION", "Stone", foundation(BLOCKS, 0.0, ZF, style="chequerstone"), group="foundation")
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

    # --- the two mansards (upside down); the pavilion's rises through the main one
    # each roof is cut back to the other's slates (0.5 proud of its face)
    pav_vol = _volume(PAV.pts, [(d + 0.5, z) for d, z in PAV_MANSARD], top=20.0)
    main_vol = _volume(MAIN.pts, [(d + 0.5, z) for d, z in MANSARD])
    mans, mtex, inner = R.mansard(MAIN.pts, MANSARD, t=2.6, tex=SLATE)
    pmans, ptex, pinner = R.mansard(PAV.pts, PAV_MANSARD, t=2.6, tex=SLATE)
    seg, ova, big = SE.addin_lafayette_seg(), SE.addin_lafayette_oval(), SE.addin_lafayette_seg(w=6.4, h=12.4, rise=1.6)
    mk, mf = _addins(kit, MAIN, [(x, y, seg if k == "seg" else ova, k) for x, y, k in ADDINS], MANSARD, Z_ADD, "ADDIN")
    pk, pf = _addins(kit, PAV, [(x, y, big, "big") for x, y in PAV_ADDINS], PAV_MANSARD, Z_ADDP, "ADDIN-P")
    C = SE.crest_ring(MAIN.pts, D_TOP, MZ1, D_TOP - inner(MZ1), CREST_COURSE, CREST_CROWN)
    PC = SE.crest_ring(PAV.pts, PD_TOP, PZ1, PD_TOP - pinner(PZ1), CREST_COURSE, CREST_CROWN)
    kit.add("MANSARD", "Slate", (mans + (mtex - mf)) - mk - pav_vol - C["groove"], P=print_flip(), group="roof")
    kit.add("MANSARD-P", "Slate", (pmans + (ptex - pf)) - pk - main_vol - PC["groove"], P=print_flip(), group="pavilion")
    print("mansards + add-ins", round(time.time() - t0, 1))

    # --- crests, decks, cresting, the pavilion's finial, chimneys
    kit.add("CREST", "Plum", C["solid"] - pav_vol, P=print_flip(), change=C["change"], group="roof", render=C["zones"])
    zdeck = C["z_top"]
    chims = [(30.0, 104.0), (164.0, 67.0)]
    pads = union([box([x - 5.6, y - 5.6, zdeck - 0.6], [x + 5.6, y + 5.6, zdeck + 1]) for x, y in chims])
    dcs = poly(R.offset_path(C["path"], -1.6))
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x0, y - 0.25, x1, y + 0.25) for y in np.arange(y0 + 2.6, y1, 5.2)]) ^ dcs
    sky = box([110.0, 60.0, zdeck - 0.01], [126.0, 74.0, zdeck + 1.2]) + \
        M.hull_points([(x, y, zdeck + 1.19) for x in (110.0, 126.0) for y in (60.0, 74.0)] + [(x, 67.0, zdeck + 3.4) for x in (110.6, 125.4)])
    deck = C["deck"] + slab(seams - rect(108.0, 58.0, 128.0, 76.0), zdeck - 0.01, zdeck + 0.4) + sky
    kit.add("ROOF-deck", "Slate", deck - pads - pav_vol, group="roof")
    for i, seg_, A, L in SE.cresting_strips(C["path"], zdeck, C["rail"], SE.fence_lafayette, 3.6):
        for j, piece in enumerate((seg_ - pav_vol).decompose()):
            if piece.volume() > 3.0:
                kit.add(f"CREST-iron-{i}{'abc'[j]}", "Iron", piece, P=inv34(A), group="roof")
    for k, (x, y) in enumerate(chims):
        ch = SE.chimney_lafayette(w=10.0, d=10.0, h=24.0).translate([x, y, zdeck - 0.6])
        zc = zdeck - 0.6 + 20.4
        cap = ch ^ box([-1e3, -1e3, zc], [1e3, 1e3, 1e3])
        kit.add(f"CHIMNEY-{k}", "Stone", ch, key="CHIMNEY", group="roof", change=(20.4, "Ivory"),
                render=[("Stone", ch - cap), ("Ivory", cap)])
    kit.add("PAV-CREST", "Plum", PC["solid"], P=print_flip(), change=PC["change"], group="pavilion", render=PC["zones"])
    pz = PC["z_top"]
    pcs = poly(R.offset_path(PC["path"], -1.6))
    px0, py0, px1, py1 = pcs.bounds()
    pseams = cs_union([rect(x - 0.25, py0, x + 0.25, py1) for x in np.arange(px0 + 2.6, px1, 5.2)]) ^ pcs
    kit.add("PAV-deck", "Slate", PC["deck"] + slab(pseams, pz - 0.01, pz + 0.4), group="pavilion")
    for i, seg_, A, L in SE.cresting_strips(PC["path"], pz, PC["rail"], SE.fence_lafayette, 4.2):
        kit.add(f"PAV-iron-{i}", "Iron", seg_, P=inv34(A), key=f"PAV-iron-{round(L, 1)}", group="pavilion")
    tc = ((PX0 + PX1) / 2, (PY0 + PY1) / 2)
    kit.add("PAV-finial", "Iron", SE.finial_torch(10.0).translate([tc[0], tc[1], pz + 0.39]), group="pavilion")
    print("roofs", round(time.time() - t0, 1))

    # --- veranda along the front and down the east side
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    y0, y1 = -1.4, PY0
    xa, xb = PX1 + 1.4, X1 + 22.0
    ye = 70.0
    pts = [(xa, y0), (xa, y1), (xb, y1), (xb, ye), (X1 + 1.4, ye), (X1 + 1.4, y0)]
    Lf, Le, Ln = xb - xa, ye - y1, xb - X1 - 1.4
    door_u = 124.0 - xa
    runs = [dict(a=(xa, y1), b=(xb, y1), posts=[1.6, 28.0, door_u - 11.0, door_u + 11.0, Lf - 44.0, Lf - 1.6]),
            dict(a=(xb, y1), b=(xb, ye), posts=[1.6, Le / 2, Le - 1.6]),
            dict(a=(xb, ye), b=(X1 + 1.4, ye), posts=[1.6, Ln - 1.7])]
    P = FT.porch_turned(pts, runs, H_floor, post_h, steps_at=[(0, door_u, 18.0)], planks=dict(pitch=1.4, border=1.6),
                        joined=True, post="reededvase", rail="fleursplats", arcade="festoons", skirt="scallopboards",
                        pier_tex="stone", roof_edge="pendants", top=True)
    fkeep = slab(offset(allcs, 1.7), -1, ZF + 1.3)          # clear of the rock-faced blocks
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    deck_ = P["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck_, P=print_flip(), group="porch",
            render=FT.plank_zones(deck_, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=300) for b in BLOCKS])
    FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_keep, "Ivory", "Ivory", tin_col="Slate", tin="flat")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Stone", sm.transform(A) - fkeep, group="porch")
    e, u = MAIN.locate(93.0, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Stone", FT.steps(15.0, ZF - 0.6, 5).transform(A), group="porch")
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
    OUT = os.path.join(HERE, "..", "..", "out", "lafayette")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "lafayette.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Addins"))
