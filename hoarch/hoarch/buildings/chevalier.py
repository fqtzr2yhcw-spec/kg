"""The Chevalier -- an original HO-scale (1:87.1) Second Empire house of the mansard batch (houses
81 to 90), on the batch's roof system (hoarch.secondempire).

Fawn siding of two kinds in every storey (a wainscot of vertical boards under a capped rail,
rebated lap above), chocolate trim and teal accents, on herringbone stone. A straight mansard of
red slate with a chevron band of diamond-cut slates, ogee-capped add-ins, a crest with its own
cornice and heart cresting, twin-shafted stacks joined by an arch. Two canted bays rise the full
two storeys (one on the front, one on the west) under crested decks. A porch turns the
front-east corner on bulb-and-ring posts with tulip splats, a keyhole arcade, diamond-cut
skirting and teardrops on its fascia.

- Ground-floor windows flat-headed in casings with roundel corner blocks under capped cornices
  with a sawn lozenge crest; upper windows segmental under hood moulds ending in teardrops over
  scalloped aprons; a double door with oval lights under a scrolled transom and a hood on big
  sawn brackets.
- Storey joint: a teal frieze of swallows, a chocolate hexagon chain, a teal crown.
- Eave: a chocolate hexagon chain, a teal frieze of peltae, a soffit on fan-tail brackets and
  a teal torus crown.
- Crest: a chocolate hexagon chain under a teal cyma crown on block modillions.

usage: python3 -m hoarch.buildings.chevalier [check] [export]
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

NAME = "Chevalier"
COLORS = {"PorchDeck": "#4A3328", "Planks": "#6F5034",
          "Fawn": "#C9AE86", "Chocolate": "#4A3328", "Teal": "#2F6F6A", "Slate": "#7A4A44", "Iron": "#232528",
          "Stone": "#8D857A", "Windows_Doors": "#4A3328", "Addins": "#7A4A44"}
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks", "Fawn": "walls", "Chocolate": "trim", "Teal": "accent",
              "Slate": "roof", "Iron": "iron", "Stone": "stone", "Windows_Doors": "trim", "Addins": "roof", "Sash": "sash",
              "Door": "door", "Glass": "glass"}
PALETTE = {"walls": ["#C9AE86", 0.8, 0.0], "trim": ["#4A3328", 0.6, 0.0], "accent": ["#2F6F6A", 0.5, 0.0],
           "roof": ["#7A4A44", 0.75, 0.0], "iron": ["#232528", 0.45, 0.3], "stone": ["#8D857A", 0.9, 0.0],
           "planks": ["#6F5034", 0.75, 0.0], "sash": ["#2A2420", 0.45, 0.0], "door": ["#2F6F6A", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Chevalier)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.2, b=1.2, orn="swallows", role="Teal"),
    dict(kind="course", h=1.8, b=1.4, orn="hexchain", role="Chocolate"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="ogee_fillet", role="Teal")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="hexchain", role="Chocolate"),
    dict(kind="frieze", h=6.2, b=1.2, orn="peltae", role="Teal"),
    dict(kind="bed", h=2.2, b=1.4, P=6.8, role="Chocolate", brackets=dict(style="fantail", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.8, b=1.4, P=7.6, orn="torus", role="Teal")])
CREST_COURSE = dict(h=2.0, b=0.6, orn=SE.hexlinks, role="Chocolate")
CREST_CROWN = dict(h=2.6, P=3.4, kind="cyma", role="Teal", blocks=(0.9, 5.0))
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
D_TOP = -2.4
MANSARD = [(DK, MZ0), (DK - 1.4, MZ0 + 1.4), (D_TOP, MZ1)]
SLATE = dict(pitch=1.8, wtab=2.4, d=0.4, shape=SE.slate_chevron)
V1, V2 = 6.4, S1 + RJ + 5.0 - ZF
Z_ADD = MZ0 + 3.2

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 184.0, 134.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
BAYF = Block("bay-front", [(22.0, 3.0), (22.0, 0.0), (30.0, -12.0), (52.0, -12.0), (60.0, 0.0), (60.0, 3.0)], ZF, ZW)
BAYW = Block("bay-west", [(3.0, 102.0), (0.0, 102.0), (-12.0, 94.0), (-12.0, 78.0), (0.0, 70.0), (3.0, 70.0)], ZF, ZW)
BLOCKS = [MAIN, BAYF, BAYW]
BAYS = [BAYF, BAYW]


def _siding(f, b, reg):
    """The wainscot and lap of each storey; nothing in the joint or the eave band."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    lo = reg ^ rect(-1, -1, f.L + 1, S1 - b.z0)
    up = reg ^ rect(-1, S1 + RJ - b.z0, f.L + 1, 999)
    return SE.wainscotlap(lo, datum=1.8) + SE.wainscotlap(up, datum=S1 + RJ - b.z0 + 0.4)


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    lo = SE.window_chevalier_lower()
    up = SE.window_chevalier_upper()
    lo_n = SE.window_chevalier_lower(w=5.0, h=19.0, A=0.9)
    up_n = SE.window_chevalier_upper(w=5.0, h=17.0, rise=1.2, A=0.8)
    front = SE.door_chevalier()
    back = SE.door_chevalier_back()

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    add(MAIN, 128.0, 0, 0.4, front, "front-door", "door")
    for x in (82.0, 164.0):
        add(MAIN, x, 0, V1, lo, f"S{x:.0f}-1")
    for x in (82.0, 128.0, 164.0):
        add(MAIN, x, 0, V2, up, f"S{x:.0f}-2")
    for bay, tag in ((BAYF, "BF"), (BAYW, "BW")):
        Q = ccw_pts(bay)
        for i in range(len(Q)):
            a, b = np.array(Q[i]), np.array(Q[(i + 1) % len(Q)])
            Lf = float(np.linalg.norm(b - a))
            if Lf < 10.0:
                continue
            m = (a + b) / 2
            wide = Lf > 18.0
            add(bay, m[0], m[1], V1, lo if wide else lo_n, f"{tag}{i}-1")
            add(bay, m[0], m[1], V2, up if wide else up_n, f"{tag}{i}-2")
    for y in (30.0, 122.0):
        add(MAIN, 0, y, V1, lo, f"W{y:.0f}-1")
        add(MAIN, 0, y, V2, up, f"W{y:.0f}-2")
    for y in (26.0, 70.0, 110.0):
        add(MAIN, X1, y, V1, lo, f"E{y:.0f}-1")
        add(MAIN, X1, y, V2, up, f"E{y:.0f}-2")
    for x in (30.0, 154.0):
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
    for x in (30.0, 92.0, 154.0):
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, 92.0, Y1, 0.4, back, "back-door", "door")
    return L


def ccw_pts(block):
    from hoarch.core import ccw
    return ccw(block.pts)


OPENINGS = _openings()
ADDINS = [(82.0, 0.0), (128.0, 0.0), (164.0, 0.0), (X1, 26.0), (X1, 70.0), (X1, 110.0), (154.0, Y1), (92.0, Y1), (30.0, Y1),
          (0.0, 122.0), (0.0, 30.0)]


def _frame_on(block, x, y, z, w0):
    e, u = block.locate(x, y)
    f = block.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, z - ZF, w0)
    return A


# ------------------------------------------------------------------ build
def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    allcs = cs_union([b.cs for b in BLOCKS])
    eave_path = max(allcs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(allcs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_siding,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=True, undress=undress,
                        clear=[lip_keep(allcs, 3.0, ZF, 1.2)])
    kit.add("WALLS-1", "Fawn", st["shells"][0], group="walls")
    kit.add("JOINT", "Fawn", st["rings"][0], group="walls")
    kit.add("WALLS-2", "Fawn", st["shells"][1] + CO.ledge(eave_path, ZE, LEDGE), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    kit.add("FOUNDATION", "Stone", foundation(BLOCKS, 0.0, ZF, style="herringstone"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Chocolate", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the mansard (upside down) over the main block, its add-ins, crest, deck, cresting
    mans, mtex, inner = R.mansard(MAIN.pts, MANSARD, t=2.6, tex=SLATE)
    sp = SE.addin_chevalier()
    pl = [SE.addin_place(sp, MANSARD, Z_ADD) for _ in ADDINS]
    depth = max(d for _, d in pl)
    keeps, flashes = [], []
    for k, ((x, y), (w0, _)) in enumerate(zip(ADDINS, pl)):
        A = _frame_on(MAIN, x, y, Z_ADD, w0)
        a = SE.addin(sp, depth)
        keeps.append(a["keep"].transform(A))
        flashes.append(a["flash"].transform(A))
        zones = [("Glass", a["glass"].transform(A)), ("Slate", (a["plug"] - a["glass"]).transform(A)),
                 ("Chocolate", a["frame"].transform(A))]
        kit.add(f"ADDIN-{k}", "Addins", a["solid"].transform(A), P=inv34(A), change=(round(depth, 1), "Chocolate"),
                key="ADDIN", group="addins", render=zones)
    C = SE.crest_ring(MAIN.pts, D_TOP, MZ1, D_TOP - inner(MZ1), CREST_COURSE, CREST_CROWN)
    kit.add("MANSARD", "Slate", mans + (mtex - union(flashes)) - union(keeps) - C["groove"], P=print_flip(), group="roof")
    kit.add("CREST", "Teal", C["solid"], P=print_flip(), change=C["change"], group="roof", render=C["zones"])
    zdeck = C["z_top"]
    chims = [(40.0, 108.0), (150.0, 100.0)]
    pads = union([box([x - 6.4, y - 2.4, zdeck - 0.6], [x + 6.4, y + 2.4, zdeck + 1]) for x, y in chims] +
                 [box([x - 6.4, y - 4.4, zdeck - 0.6], [x + 6.4, y + 4.4, zdeck + 1]) for x, y in chims])
    dcs = poly(R.offset_path(C["path"], -1.6))
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + 2.6, x1, 5.2)]) ^ dcs
    kit.add("ROOF-deck", "Slate", C["deck"] + slab(seams, zdeck - 0.01, zdeck + 0.4) - pads, group="roof")
    for i, seg, A, L in SE.cresting_strips(C["path"], zdeck, C["P"] - 1.4, SE.printable(SE.fence_chevalier), 7.2):
        kit.add(f"CREST-iron-{i}", "Iron", seg, P=inv34(A), key=f"CREST-iron-{round(L, 1)}", group="roof")
    for k, (x, y) in enumerate(chims):
        ch = SE.chimney_chevalier(w=12.0, d=8.0, h=24.0).translate([x, y, zdeck - 0.6])
        kit.add(f"CHIMNEY-{k}", "Slate", ch, key="CHIMNEY", group="roof")
    print("roof", round(time.time() - t0, 1), "plug", depth)

    # --- the bays' crested decks, from their crowns back to the mansard's foot
    main_vol = M.hull_points([(x, y, z) for x, y in R.offset_path(MAIN.pts, DK + 0.1) for z in (ZW - 1, ZW + 40)])
    Pc = EAVE["layers"][-1]["P"]
    for bay, tag in ((BAYF, "BAYF"), (BAYW, "BAYW")):
        bd = slab(offset(bay.cs, Pc + 0.2), ZW, ZW + 1.2) - main_vol
        bd = max(bd.decompose(), key=lambda m_: m_.volume())
        kit.add(f"{tag}-roof", "Slate", bd, group="bays")
        for i, seg, A, L in SE.cresting_strips(bay.pts, ZW + 1.2, Pc - 1.0, SE.printable(SE.fence_chevalier), 5.6):
            seg = seg - main_vol
            if not seg.is_empty() and seg.volume() > 1.0:
                kit.add(f"{tag}-crest-{i}", "Iron", seg, P=inv34(A), group="bays")
    print("bays", round(time.time() - t0, 1))

    # --- a porch round the front-east corner
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    xa, xb, ya, yb, xe = 96.0, X1 + 22.0, -22.0, 52.0, X1 + 1.4
    pts = [(xa, -1.4), (xa, ya), (xb, ya), (xb, yb), (xe, yb), (xe, -1.4)]
    Lf, Le = xb - xa, yb - ya
    door_u = 128.0 - xa
    runs = [dict(a=(xa, -1.4), b=(xa, ya), posts=[1.7, (-1.4 - ya) - 1.6]),
            dict(a=(xa, ya), b=(xb, ya), posts=[1.6, door_u - 11.0, door_u + 11.0, 76.0, Lf - 1.6]),
            dict(a=(xb, ya), b=(xb, yb), posts=[1.6, Le / 2, Le - 1.6]),
            dict(a=(xb, yb), b=(xe, yb), posts=[1.6, (xb - xe) - 1.7])]
    P = FT.porch_turned(pts, runs, H_floor, post_h, steps_at=[(1, door_u, 18.0)], planks=dict(pitch=1.4, border=1.6),
                        joined=True, post="bulbring", rail="tulipsplats", arcade="keyholearcade", skirt="diamondboards",
                        pier_tex="stone", roof_edge="teardrops", top=True)
    fkeep = slab(offset(allcs, 1.7), -1, ZF + 1.3)
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    deck_ = P["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck_, P=print_flip(), group="porch",
            render=FT.plank_zones(deck_, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=300) for b in BLOCKS])
    FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_keep, "Chocolate", "Chocolate", tin_col="Slate", tin="flat")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Stone", sm.transform(A) - fkeep, group="porch")
    e, u = MAIN.locate(92.0, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Stone", FT.steps(15.0, ZF - 0.6, 5).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("CREST-iron")]:
        FT.key_into(kit, p_.name, ["CREST"], (0, 0, -1), depth=0.6)
    for p_ in [p_ for p_ in kit.parts if "-crest-" in p_.name]:
        FT.key_into(kit, p_.name, [p_.name.split("-crest-")[0] + "-roof"], (0, 0, -1), depth=0.6)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "chevalier")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "chevalier.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Addins"))
