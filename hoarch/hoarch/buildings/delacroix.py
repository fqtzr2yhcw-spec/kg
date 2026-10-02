"""The Delacroix -- an original HO-scale (1:87.1) Second Empire house of the mansard batch
(houses 81 to 90), on the batch's roof system (hoarch.secondempire).

Deep red brick in rat-trap bond with buff sandstone dressings and bottle-green accents, on
pick-dressed sandstone. A tall square tower at the front-east corner rises a storey above the
eave to a concave cap; the main roof is a straight mansard of square slate with a diaper of
hexagon-cut slates, both roofs carrying pedimented add-ins (the tower's on its two street faces
only), crests with their own cornices, trefoil cresting and a crowned ball finial on the tower.
Two stacks with open gabled caps. A veranda along the front to the tower on beaded-collar posts,
bobbin balusters, a frieze of ogee arches and acorn drops.

- Ground-floor windows round-headed in beaded architraves under segmental pediments broken by a
  scrolled keystone; upper windows flat-headed in eared architraves with a cushion frieze and a
  tablet; a double door with oval lights under a shell fanlight between rusticated pilasters.
- Storey joint: a green frieze of thistles, a sandstone knurled course and a green cyma crown.
- Eave (and the tower's top): a sandstone plait, a green frieze of ferns, a sandstone knurled
  course, a soffit on swan-neck brackets and a green ovolo crown.
- Crests: a sandstone plait under a green cyma crown on block modillions.

usage: python3 -m hoarch.buildings.delacroix [check] [export]
"""
import math
import os
import sys
import time

import numpy as np

from hoarch.core import box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, openings as O, roof as R, secondempire as SE
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Delacroix"
COLORS = {"PorchDeck": "#CDB78F", "Planks": "#6F5034",       # the planked veranda floor: two colours, one change
          "Brick": "#8A3A2A", "Sandstone": "#CDB78F", "Green": "#2F4A3A", "Slate": "#4B4F57", "Iron": "#232528",
          "Windows_Doors": "#CDB78F", "Addins": "#4B4F57"}
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks", "Brick": "brick", "Sandstone": "trim", "Green": "accent",
              "Slate": "roof", "Iron": "iron", "Windows_Doors": "trim", "Addins": "roof", "Sash": "sash", "Door": "door",
              "Glass": "glass"}
PALETTE = {"brick": ["#8A3A2A", 0.85, 0.0], "trim": ["#CDB78F", 0.65, 0.0], "accent": ["#2F4A3A", 0.5, 0.0],
           "roof": ["#4B4F57", 0.75, 0.0], "iron": ["#232528", 0.45, 0.3], "planks": ["#6F5034", 0.75, 0.0],
           "sash": ["#1F2A22", 0.45, 0.0], "door": ["#3B2418", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Delacroix)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.6, b=1.2, orn="thistles", role="Green"),
    dict(kind="course", h=1.6, b=1.4, orn="knurl", role="Sandstone"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="cyma", role="Green")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="plait", role="Sandstone"),
    dict(kind="frieze", h=6.4, b=1.2, orn="ferns", role="Green"),
    dict(kind="course", h=1.4, b=1.4, orn="knurl", role="Sandstone"),
    dict(kind="bed", h=2.2, b=1.4, P=6.8, role="Sandstone", brackets=dict(style="swanneck", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.8, b=1.4, P=7.6, orn="ovolo", role="Green")])
TOWER_C = dict(pitch=11.0, margin=3.5, layers=[
    dict(kind="frieze", h=5.6, b=1.2, orn="ferns", role="Green"),
    dict(kind="bed", h=2.0, b=1.4, P=5.8, role="Sandstone", brackets=dict(style="swanneck", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.4, b=1.4, P=6.6, orn="ovolo", role="Green")])
CREST_COURSE = dict(h=2.0, b=0.6, orn=SE.plait, role="Sandstone")
CREST_CROWN = dict(h=2.6, P=3.4, kind="cyma", role="Green", blocks=(0.9, 5.0))
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (all on the 0.2 mm grid)
ZF = 13.0
S1 = ZF + 42.0
ZE = S1 + RJ + 38.0
ZW = ZE + HE
MZ0 = ZW
MH = 30.0
MZ1 = MZ0 + MH
DK = EAVE["layers"][-1]["P"] + 0.2
D_TOP = -2.0
MANSARD = [(DK, MZ0), (DK - 1.4, MZ0 + 1.4), (D_TOP, MZ1)]
ZT = ZW + 38.0            # the tower's ledge: its top storey stands over the eave
ZTW = ZT + CO.band_height(TOWER_C)
TCAP_H = 28.0
V1, V2 = 6.4, S1 + RJ + 5.0 - ZF
V3 = ZW + 7.0 - ZF
Z_ADD = MZ0 + 3.2

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 186.0, 140.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
TX0, TX1, TY0, TY1 = 148.0, 196.0, -24.0, 24.0
TOWER = Block("tower", [(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)], ZF, ZTW)
BLOCKS = [MAIN, TOWER]
SLATE = SE.slate_diaper


def _brick(f, b, reg):
    """Rat-trap bond; nothing in the cornice bands."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    if b is TOWER:
        reg = reg - rect(-1, ZT - b.z0, f.L + 1, 999)
    return SE.brick_rattrap(reg, datum=1.8)


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    lo = SE.window_delacroix_lower()
    up = SE.window_delacroix_upper()
    front = SE.door_delacroix()
    back = SE.door_delacroix_back()

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    for x in (26.0, 122.0):
        add(MAIN, x, 0, V1, lo, f"S{x:.0f}-1")
    for x in (26.0, 74.0, 122.0):
        add(MAIN, x, 0, V2, up, f"S{x:.0f}-2")
    add(MAIN, 74.0, 0, 0.4, front, "front-door", "door")
    tx = (TX0 + TX1) / 2
    for v0, sp, k in ((V1, lo, 1), (V2, up, 2), (V3, up, 3)):           # the tower's two street faces
        add(TOWER, tx, TY0, v0, sp, f"T-S{k}")
        add(TOWER, TX1, 0.0, v0, sp, f"T-E{k}")
    for y in (60.0, 106.0):
        add(MAIN, X1, y, V1, lo, f"E{y:.0f}-1")
        add(MAIN, X1, y, V2, up, f"E{y:.0f}-2")
    for y in (30.0, 75.0, 120.0):
        add(MAIN, 0, y, V1, lo, f"W{y:.0f}-1")
        add(MAIN, 0, y, V2, up, f"W{y:.0f}-2")
    for x in (30.0, 156.0):
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
    for x in (30.0, 93.0, 156.0):
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, 93.0, Y1, 0.4, back, "back-door", "door")
    return L


OPENINGS = _openings()
ADDINS = [(26.0, 0.0), (74.0, 0.0), (122.0, 0.0), (X1, 60.0), (X1, 106.0), (156.0, Y1), (93.0, Y1), (30.0, Y1),
          (0.0, 120.0), (0.0, 75.0), (0.0, 30.0)]
TOWER_ADDINS = [((TX0 + TX1) / 2, TY0), (TX1, 0.0)]


def _frame_on(block, x, y, z, w0):
    e, u = block.locate(x, y)
    f = block.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, z - ZF, w0)
    return A


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
                 ("Sandstone", a["frame"].transform(A))]
        kit.add(f"{tag}-{k}", "Addins", a["solid"].transform(A), P=inv34(A), change=(round(depth, 1), "Sandstone"),
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
    undress = [slab(offset(allcs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", clear=[lip_keep(allcs, 3.0, ZF, 1.2)],
                        siding=_brick, prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=undress)
    kit.add("WALLS-1", "Brick", st["shells"][0], group="walls")
    kit.add("JOINT", "Brick", st["rings"][0], group="walls")
    # inside the house the tower's walls rise from the joint so its top storey bears all round
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(allcs, 3.0, S1 + RJ)
    ledges = CO.ledge(eave_path, ZE, LEDGE) + CO.ledge(TOWER.pts, ZT, LEDGE)
    tlip = _corbel(TOWER.cs, 3.0, ZTW) + lip_ring(TOWER.cs, 3.0, ZTW)
    kit.add("WALLS-2", "Brick", st["shells"][1] + tring + ledges + tlip, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    tcen = ((TX0 + TX1) / 2, (TY0 + TY1) / 2)
    cut = CO.blades(CO.tower_cuts(eave_path, tcen, 34.0, tower=TOWER.pts, house=MAIN.pts), ZE, ZW)
    rings, _ = CO.level(eave_path, ZE, EAVE, cut=cut)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(TOWER.pts, ZT, TOWER_C)
    CO.add_level(kit, rings, "CORNICE-T", "tower")
    kit.add("FOUNDATION", "Sandstone", foundation(BLOCKS, 0.0, ZF, style="pickdressed"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Sandstone", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    tower_keep = TOWER.solid(grow=2.1, dz0=-1, dz1=400)
    tower_hug = TOWER.solid(grow=0.5, dz0=-1, dz1=400)          # the roof's notch hugs the tower
    # --- the main mansard (upside down), notched round the tower, its add-ins
    mans, mtex, inner = R.mansard(MAIN.pts, MANSARD, t=2.6, tex=dict(pitch=1.8, wtab=2.4, d=0.4, shape=SLATE))
    sp = SE.addin_delacroix()
    mk, mf = _addins(kit, MAIN, ADDINS, MANSARD, Z_ADD, sp, "ADDIN")
    kit.add("MANSARD", "Slate", (mans + (mtex - mf)) - mk - tower_hug, P=print_flip(), group="roof")
    C = SE.crest_ring(MAIN.pts, D_TOP, MZ1, D_TOP - inner(MZ1), CREST_COURSE, CREST_CROWN)
    kit.add("CREST", "Green", C["solid"] - tower_hug, P=print_flip(), change=C["change"], group="roof",
            render=[(r, z - tower_hug) for r, z in C["zones"]])
    zdeck = C["z_top"]
    chims = [(30.0, 104.0), (118.0, 112.0)]
    pads = union([box([x - 5.6, y - 5.6, zdeck - 0.6], [x + 5.6, y + 5.6, zdeck + 1]) for x, y in chims])
    dcs = poly(R.offset_path(C["path"], -1.6))
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + 2.6, x1, 5.2)]) ^ dcs
    kit.add("ROOF-deck", "Slate", C["deck"] + slab(seams, zdeck - 0.01, zdeck + 0.4) - pads - tower_hug, group="roof")
    for i, seg, A, L in SE.cresting_strips(C["path"], zdeck, C["P"] - 1.4, SE.fence_delacroix, 3.4):
        for j, piece in enumerate((seg - tower_keep).decompose()):
            if piece.volume() > 3.0:
                kit.add(f"CREST-iron-{i}{'abc'[j]}", "Iron", piece, P=inv34(A), group="roof")
    for k, (x, y) in enumerate(chims):
        ch = SE.chimney_delacroix(w=10.0, d=10.0, h=26.0).translate([x, y, zdeck - 0.6])
        zc = zdeck - 0.6 + 20.0                     # the band of stone, the piers, the gabled cap: one change
        cap = ch ^ box([-1e3, -1e3, zc], [1e3, 1e3, 1e3])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof", change=(20.0, "Sandstone"),
                render=[("Brick", ch - cap), ("Sandstone", cap)])
    print("roof", round(time.time() - t0, 1))

    # --- the tower: its cornice (above), a concave cap with add-ins on the street faces, crest, finial
    cprof = FT.tower_cap(None, ZTW, TCAP_H, d_flare=TOWER_C["layers"][-1]["P"] + 0.2, d_top=-6.0, bands=6)
    cap, ctex, cin = R.mansard(TOWER.pts, cprof, t=2.4, tex=dict(pitch=1.6, wtab=2.0, d=0.35, shape=SLATE))
    tk, tf = _addins(kit, TOWER, TOWER_ADDINS, cprof, ZTW + 7.0, sp, "ADDIN-T")     # up where the cap is steep
    kit.add("TOWER-CAP", "Slate", (cap + (ctex - tf)) - tk - lip_keep(TOWER.cs, 3.0, ZTW), P=print_flip(), group="tower")
    TC = SE.crest_ring(TOWER.pts, cprof[-1][0], ZTW + TCAP_H, cprof[-1][0] - cin(ZTW + TCAP_H), CREST_COURSE, CREST_CROWN)
    kit.add("TOWER-CREST", "Green", TC["solid"], P=print_flip(), change=TC["change"], group="tower", render=TC["zones"])
    tz = TC["z_top"]
    kit.add("TOWER-deck", "Slate", TC["deck"], group="tower")
    for i, seg, A, L in SE.cresting_strips(TC["path"], tz, TC["P"] - 1.4, SE.fence_delacroix, 3.6):
        kit.add(f"TOWER-iron-{i}", "Iron", seg, P=inv34(A), key=f"TOWER-iron-{round(L, 1)}", group="tower")
    tc = ((TX0 + TX1) / 2, (TY0 + TY1) / 2)
    kit.add("TOWER-finial", "Iron", SE.finial_crownball(10.0).translate([tc[0], tc[1], tz - 0.01]), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- veranda along the front to the tower
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    y0, y1 = -1.4, TY0
    px0, xt = -3.0, TX0 - 1.4
    Lf = xt - px0
    door_u = 74.0 - px0
    runs = [dict(a=(px0, y0), b=(px0, y1), posts=[1.7, (y0 - y1) - 1.6]),
            dict(a=(px0, y1), b=(xt, y1), posts=[1.6, 36.0, door_u - 11.0, door_u + 11.0, 116.0, Lf - 1.6])]
    P = FT.porch_turned([(px0, y0), (px0, y1), (xt, y1), (xt, y0)], runs, H_floor, post_h,
                        steps_at=[(1, door_u, 18.0)], planks=dict(pitch=1.4, border=1.6), joined=True,
                        post="beadcollar", rail="beadstack", arcade="ogeearcade", skirt="archslats", pier_tex="limestone",
                        roof_edge="acorndrops", top=True)
    fkeep = slab(offset(allcs, 1.7), -1, ZF + 1.3)
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    deck_ = P["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck_, P=print_flip(), group="porch",
            render=FT.plank_zones(deck_, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=300) for b in BLOCKS])
    FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_keep, "Sandstone", "Sandstone", tin_col="Slate", tin="flat")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Sandstone", sm.transform(A) - fkeep, group="porch")
    e, u = MAIN.locate(93.0, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Sandstone", FT.steps(15.0, ZF - 0.6, 5).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("CREST-iron")]:
        FT.key_into(kit, p_.name, ["CREST"], (0, 0, -1), depth=0.6)
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("TOWER-iron")]:
        FT.key_into(kit, p_.name, ["TOWER-CREST"], (0, 0, -1), depth=0.6)
    FT.crown(kit, "TOWER-finial", "TOWER-deck")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "delacroix")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "delacroix.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Addins"))
