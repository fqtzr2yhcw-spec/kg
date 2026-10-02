"""The Marchand -- an original HO-scale (1:87.1) Second Empire house of the mansard batch (houses
81 to 90), on the batch's roof system (hoarch.secondempire).

Rose-red brick stepped a third of a brick each course, with chequered bands of headers; cream
limestone dressings and indigo accents, on chamfered rustication. An octagonal turret engaged at
the front-west corner rises a storey over the eave to a bell cap of arrow-pointed slates with
three add-ins, its own cornice, a crest and an artichoke finial. The main roof is a straight
mansard banded with arrow-pointed slates, eleven swan-neck add-ins, a crest with its own cornice and
anthemion cresting. Two stacks with sunk arched panels, dogtooth and pots. A veranda runs across
the front, round the foot of the turret and up the west side on cushion-waisted posts, urn-necked
balusters, a frieze of basket arches and a fascia of darts and beads.

- Ground-floor windows round-headed on imposts under a hood with curled stops and a shell
  keystone, over a shaped apron; upper windows flat-headed with a garlanded frieze and a cornice
  crested with an anthemion between scrolls; a double door with arched lights under a web
  fanlight between engaged columns, an entablature with a cartouche and a scrolled crest.
- Storey joint: a limestone guilloche, an indigo frieze of rinceau scrolls, a limestone crown.
- Eave (and the turret's top): a limestone egg-and-dart, an indigo frieze of garlanded
  cartouches, a guilloche, a soffit on drop consoles and an indigo cove crown.
- Crests: a limestone guilloche under an indigo ovolo crown on block modillions.

usage: python3 -m hoarch.buildings.marchand [check] [export]
"""
import math
import os
import sys
import time

import numpy as np

from hoarch.core import box, cs_union, inv34, ngon, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, openings as O, roof as R, secondempire as SE
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Marchand"
COLORS = {"PorchDeck": "#D9CDB0", "Planks": "#7A5A3C",       # the planked veranda floor: two colours, one change
          "Brick": "#A85B42", "Limestone": "#D9CDB0", "Indigo": "#34405E", "Slate": "#50555C", "Iron": "#232528",
          "Granite": "#7E7A74", "Windows_Doors": "#D9CDB0", "Addins": "#50555C"}
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks", "Brick": "brick", "Limestone": "trim", "Indigo": "accent",
              "Slate": "roof", "Iron": "iron", "Granite": "stone", "Windows_Doors": "trim", "Addins": "roof", "Sash": "sash",
              "Door": "door", "Glass": "glass"}
PALETTE = {"brick": ["#A85B42", 0.85, 0.0], "trim": ["#D9CDB0", 0.65, 0.0], "accent": ["#34405E", 0.5, 0.0],
           "roof": ["#50555C", 0.75, 0.0], "iron": ["#232528", 0.45, 0.3], "stone": ["#7E7A74", 0.9, 0.0],
           "planks": ["#7A5A3C", 0.75, 0.0], "sash": ["#2A2622", 0.45, 0.0], "door": ["#34405E", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Marchand)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="guilloche", role="Limestone"),
    dict(kind="frieze", h=5.4, b=1.2, orn="rinceau", role="Indigo"),
    dict(kind="crown", h=2.2, b=1.4, P=3.8, orn="reverse", role="Limestone")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.6, b=1.0, orn="eggdart", role="Limestone"),
    dict(kind="frieze", h=6.4, b=1.2, orn="cartouches", role="Indigo"),
    dict(kind="course", h=1.6, b=1.4, orn="guilloche", role="Limestone"),
    dict(kind="bed", h=2.2, b=1.4, P=7.0, role="Limestone", brackets=dict(style="dropconsole", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.8, b=1.4, P=7.8, orn="cavetto", role="Indigo")])
TOWER_C = dict(pitch=11.0, margin=3.0, layers=[
    dict(kind="course", h=1.6, b=1.0, orn="eggdart", role="Limestone"),
    dict(kind="frieze", h=6.0, b=1.2, orn="cartouches", role="Indigo"),
    dict(kind="bed", h=2.0, b=1.4, P=6.0, role="Limestone", brackets=dict(style="dropconsole", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.4, b=1.4, P=6.8, orn="cavetto", role="Indigo")])
CREST_COURSE = dict(h=2.0, b=0.6, orn=SE.guilloche, role="Limestone")
CREST_CROWN = dict(h=2.6, P=3.4, kind="ovolo", role="Indigo", blocks=(0.9, 5.0))
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
SLATE = dict(pitch=1.8, wtab=2.4, d=0.4, shape=SE.slate_arrowbands)
ZT = ZW + 36.0            # the turret's ledge: its top storey stands over the eave
ZTW = ZT + CO.band_height(TOWER_C)
TCAP_H = 26.0
V1, V2 = 6.4, S1 + RJ + 5.0 - ZF
V3 = ZW + 6.0 - ZF
Z_ADD = MZ0 + 3.2

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 190.0, 136.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
TA = 24.0                 # the turret's apothem; it stands on the front-west corner
TOWER = Block("turret", ngon((0.0, 0.0), TA, n=8), ZF, ZTW)
BLOCKS = [MAIN, TOWER]
DOOR_X = 107.0
TFACES = {"S": (0.0, -TA), "SW": (-TA / math.sqrt(2), -TA / math.sqrt(2)), "W": (-TA, 0.0)}


def _brick(f, b, reg):
    """Third bond with chequered bands; nothing in the cornice bands."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    if b is TOWER:
        reg = reg - rect(-1, ZT - b.z0, f.L + 1, 999)
    return SE.brick_thirdcheck(reg, datum=1.8)


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    lo = SE.window_marchand_lower()
    up = SE.window_marchand_upper()
    lo_t = SE.window_marchand_lower(w=8.4, h=21.0, A=0.9)
    up_t = SE.window_marchand_upper(w=8.0, h=19.0, A=0.8)
    front = SE.door_marchand()
    back = SE.door_marchand_back()

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    add(MAIN, DOOR_X, 0, 0.4, front, "front-door", "door")
    for x in (63.0, 151.0):
        add(MAIN, x, 0, V1, lo, f"S{x:.0f}-1")
    for x in (63.0, DOOR_X, 151.0):
        add(MAIN, x, 0, V2, up, f"S{x:.0f}-2")
    for k, (x, y) in TFACES.items():                    # the turret's three street faces
        add(TOWER, x, y, V1, lo_t, f"T{k}-1")
        add(TOWER, x, y, V2, up_t, f"T{k}-2")
        add(TOWER, x, y, V3, up_t, f"T{k}-3")
    for y in (30.0, 70.0, 110.0):
        add(MAIN, X1, y, V1, lo, f"E{y:.0f}-1")
        add(MAIN, X1, y, V2, up, f"E{y:.0f}-2")
    for y in (62.0, 106.0):
        add(MAIN, 0, y, V1, lo, f"W{y:.0f}-1")
        add(MAIN, 0, y, V2, up, f"W{y:.0f}-2")
    for x in (34.0, 156.0):
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
    for x in (34.0, 95.0, 156.0):
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, 95.0, Y1, 0.4, back, "back-door", "door")
    return L


OPENINGS = _openings()
ADDINS = [(63.0, 0.0), (DOOR_X, 0.0), (151.0, 0.0), (X1, 30.0), (X1, 70.0), (X1, 110.0), (156.0, Y1), (95.0, Y1), (34.0, Y1),
          (0.0, 106.0), (0.0, 62.0)]


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
                 ("Limestone", a["frame"].transform(A))]
        kit.add(f"{tag}-{k}", "Addins", a["solid"].transform(A), P=inv34(A), change=(round(depth, 1), "Limestone"),
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
    # inside the house the turret's walls rise from the joint so its top storey bears all round
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(allcs, 3.0, S1 + RJ)
    ledges = CO.ledge(eave_path, ZE, LEDGE) + CO.ledge(TOWER.pts, ZT, LEDGE)
    tlip = _corbel(TOWER.cs, 3.0, ZTW) + lip_ring(TOWER.cs, 3.0, ZTW)
    kit.add("WALLS-2", "Brick", st["shells"][1] + tring + ledges + tlip, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    cut = CO.blades(CO.tower_cuts(eave_path, (0.0, 0.0), 34.0, wall=TA, away=(-1.0, -1.0)), ZE, ZW)
    rings, _ = CO.level(eave_path, ZE, EAVE, cut=cut)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(TOWER.pts, ZT, TOWER_C)
    CO.add_level(kit, rings, "CORNICE-T", "tower")
    kit.add("FOUNDATION", "Granite", foundation(BLOCKS, 0.0, ZF, style="chamferrustic"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Limestone", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    tower_keep = TOWER.solid(grow=2.1, dz0=-1, dz1=400)
    tower_hug = TOWER.solid(grow=0.5, dz0=-1, dz1=400)          # the roof's notch hugs the turret
    # --- the main mansard (upside down), notched round the turret, its add-ins
    mans, mtex, inner = R.mansard(MAIN.pts, MANSARD, t=2.6, tex=SLATE)
    sp = SE.addin_marchand()
    mk, mf = _addins(kit, MAIN, ADDINS, MANSARD, Z_ADD, sp, "ADDIN")
    C = SE.crest_ring(MAIN.pts, D_TOP, MZ1, D_TOP - inner(MZ1), CREST_COURSE, CREST_CROWN)
    kit.add("MANSARD", "Slate", (mans + (mtex - mf)) - mk - tower_hug - C["groove"], P=print_flip(), group="roof")
    kit.add("CREST", "Indigo", C["solid"] - tower_hug, P=print_flip(), change=C["change"], group="roof",
            render=[(r, z - tower_hug) for r, z in C["zones"]])
    zdeck = C["z_top"]
    chims = [(62.0, 104.0), (148.0, 96.0)]
    pads = union([box([x - 5.6, y - 4.8, zdeck - 0.6], [x + 5.6, y + 4.8, zdeck + 1]) for x, y in chims])
    dcs = poly(R.offset_path(C["path"], -1.6))
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + 2.6, x1, 5.2)]) ^ dcs
    kit.add("ROOF-deck", "Slate", C["deck"] + slab(seams, zdeck - 0.01, zdeck + 0.4) - pads - tower_hug, group="roof")
    for i, seg, A, L in SE.cresting_strips(C["path"], zdeck, C["P"] - 1.4, SE.fence_marchand, 3.6):
        for j, piece in enumerate((seg - tower_keep).decompose()):
            if piece.volume() > 3.0:
                kit.add(f"CREST-iron-{i}{'abc'[j]}", "Iron", piece, P=inv34(A), group="roof")
    for k, (x, y) in enumerate(chims):
        ch = SE.chimney_marchand(w=10.4, d=8.8, h=25.0).translate([x, y, zdeck - 0.6])
        zc = zdeck - 0.6 + 20.0                     # the stone cap and the pots: one change
        cap = ch ^ box([-1e3, -1e3, zc], [1e3, 1e3, 1e3])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof", change=(20.0, "Limestone"),
                render=[("Brick", ch - cap), ("Limestone", cap)])
    print("roof", round(time.time() - t0, 1))

    # --- the turret: its cornice (above), a bell cap with add-ins on the street faces, crest, finial
    cprof = SE.bell_cap(ZTW, TCAP_H, TOWER_C["layers"][-1]["P"] + 0.2, -8.6)
    cap, ctex, cin = R.mansard(TOWER.pts, cprof, t=2.4, tex=dict(pitch=1.6, wtab=2.0, d=0.35, shape="arrow"))
    spt = SE.addin_marchand(w=4.6, h=9.0, A=0.8)
    tk, tf = _addins(kit, TOWER, list(TFACES.values()), cprof, ZTW + 6.0, spt, "ADDIN-T")
    TC = SE.crest_ring(TOWER.pts, cprof[-1][0], ZTW + TCAP_H, cprof[-1][0] - cin(ZTW + TCAP_H), CREST_COURSE, CREST_CROWN)
    kit.add("TOWER-CAP", "Slate", (cap + (ctex - tf)) - tk - lip_keep(TOWER.cs, 3.0, ZTW) - TC["groove"], P=print_flip(),
            group="tower")
    kit.add("TOWER-CREST", "Indigo", TC["solid"], P=print_flip(), change=TC["change"], group="tower", render=TC["zones"])
    tz = TC["z_top"]
    kit.add("TOWER-deck", "Slate", TC["deck"], group="tower")
    for i, seg, A, L in SE.cresting_strips(TC["path"], tz, TC["P"] - 1.4, SE.fence_marchand, 3.4):
        kit.add(f"TOWER-iron-{i}", "Iron", seg, P=inv34(A), key=f"TOWER-iron-{round(L, 1)}", group="tower")
    kit.add("TOWER-finial", "Iron", SE.finial_artichoke(11.0).translate([0.0, 0.0, tz - 0.01]), group="tower")
    print("turret", round(time.time() - t0, 1))

    # --- the veranda: across the front, round the foot of the turret, up the west side
    PD, FY, XW, XE, YW = 15.0, -18.0, -18.0, 130.0, 80.0
    Q = [np.array(q) for q in ngon((0.0, 0.0), TA + PD, n=8)]

    def cross(a, b, c, d):                       # where line a-b meets line c-d
        t = np.cross(c - a, d - c) / np.cross(b - a, d - c)
        return a + (b - a) * t

    P1 = tuple(cross(Q[1], Q[2], np.array([0.0, FY]), np.array([1.0, FY])))
    P2 = tuple(cross(Q[5], Q[6], np.array([XW, 0.0]), np.array([XW, 1.0])))
    w_ = -1.4                                    # the veranda's wall line, clear of the foundation's face
    pts = [(w_, YW), (XW, YW), P2, tuple(Q[6]), tuple(Q[7]), tuple(Q[0]), tuple(Q[1]), P1, (XE, FY), (XE, w_), (w_, w_)]
    inset = 1.6
    ca = inset * math.tan(math.radians(22.5))          # at the octagon's corners (a 45 degree turn)
    cm = inset * math.tan(math.radians(22.5))          # at the two inside corners (also 45 degrees)

    def L_(a, b):
        return float(np.linalg.norm(np.array(b) - np.array(a)))

    Lw, Lf, Lh = L_((XW, YW), P2), L_(P1, (XE, FY)), L_(Q[0], Q[1])
    ud = DOOR_X - P1[0]
    runs = [dict(a=(w_, YW), b=(XW, YW), posts=[1.7, w_ - XW - 1.6]),
            dict(a=(XW, YW), b=P2, posts=[1.6, Lw / 2, Lw + cm], piers=[1.6, Lw / 2, Lw - ca]),
            dict(a=P2, b=tuple(Q[6]), posts=[-cm, L_(P2, Q[6]) - ca], piers=[ca, L_(P2, Q[6]) - ca]),
            dict(a=tuple(Q[6]), b=tuple(Q[7]), posts=[ca, Lh / 2, Lh - ca]),
            dict(a=tuple(Q[7]), b=tuple(Q[0]), posts=[ca, Lh / 2, Lh - ca]),
            dict(a=tuple(Q[0]), b=tuple(Q[1]), posts=[ca, Lh / 2, Lh - ca]),
            dict(a=tuple(Q[1]), b=P1, posts=[ca, L_(Q[1], P1) + cm], piers=[ca, L_(Q[1], P1) - ca]),
            dict(a=P1, b=(XE, FY), posts=[-cm, 0.5 * (ud - 11.0), ud - 11.0, ud + 11.0, Lf - 1.6],
                 piers=[ca, 0.5 * (ud - 11.0), ud - 11.0, ud + 11.0, Lf - 1.6]),
            dict(a=(XE, FY), b=(XE, w_), posts=[1.6, w_ - FY - 1.7])]
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    P = FT.porch_turned(pts, runs, H_floor, post_h, steps_at=[(7, ud, 18.0)], planks=dict(pitch=1.4, border=1.6),
                        joined=True, post="cushionwaist", rail="urnneck", arcade="basketarch", skirt="herringboards",
                        pier_tex="stone", roof_edge="dartbeads", top=True)
    fkeep = slab(offset(allcs, 1.7), -1, ZF + 1.3)
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    deck_ = P["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck_, P=print_flip(), group="porch",
            render=FT.plank_zones(deck_, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=300) for b in BLOCKS])
    FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_keep, "Limestone", "Limestone", tin_col="Slate", tin="flat")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Granite", sm.transform(A) - fkeep, group="porch")
    e, u = MAIN.locate(95.0, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Granite", FT.steps(15.0, ZF - 0.6, 5).transform(A), group="porch")
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
    OUT = os.path.join(HERE, "..", "..", "out", "marchand")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "marchand.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Addins"))
