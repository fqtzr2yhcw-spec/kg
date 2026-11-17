"""The Thornbury -- an original HO-scale (1:87.1) Richardsonian Romanesque house, 1887: the seventh of
the grand batch (houses 91 to 100, hoarch.grand), on the mansard batch's roof system
(hoarch.secondempire).

A banker's house in the manner of H. H. Richardson: heavy, low-browed and round-arched. A ground
storey of rock-faced pink granite in random courses on a chamfered plinth, an upper storey of
long thin Roman brick with rock-faced quoins, and over a cornice of deeply cut Byzantine leaves
on roll corbels a steep hipped roof of green slate banded in key-butted slates, with copper
eyebrow dormers rolling out of the slope, stopping at a crested top with terracotta crocket
cresting. A great round tower stands on the front-west corner, rising a stage over the eave to
a steep bellcast cone and a copper finial, and a porch of squat cushion-capital columns and
broad Syrian arches wraps round the tower's foot and along the front, a rock-faced gable over
its steps. The front door is a pair of strapped plank leaves under a fanlight, sunk in a round
arch of three orders on nook shafts.

- Ground storey: deep round-headed sashes under rings of long voussoirs, sills on corbels.
  Upper storey: ribbon windows of three lights on colonnettes under a carved stone lintel.
  Tower: round-headed lights in voussoir rings.
- Storey joint: a brownstone nailhead course, a sandstone interlace frieze, a brownstone torus.
- Eave: nailheads, a sandstone frieze of Byzantine leaves, roll corbels, a brownstone bevel.
  Tower: an interlace frieze on the same corbels.
- Crest: a brownstone pellet chain under a copper torus.

usage: python3 -m hoarch.buildings.thornbury [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import Facade, box, cs_union, inv34, ngon, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, grand as G, openings as O, roof as R, secondempire as SE
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, foundation, lip_keep, lip_ring, _corbel, stacked_shells

NAME = "The Thornbury"
COLORS = {"Granite": "#9C7D6E", "Brick": "#8A3826", "Brownstone": "#5C392B", "Sandstone": "#CDB48A",
          "Slate": "#3D4842", "Copper": "#5B8B76", "Planks": "#6B4A33", "Windows_Doors": "#CDB48A", "Addins": "#3D4842"}
RENDER_MAT = {"Granite": "granite", "Brick": "brick", "Brownstone": "stone", "Sandstone": "trim", "Slate": "roof",
              "Copper": "copper", "Planks": "planks", "Windows_Doors": "trim", "Addins": "roof", "Sash": "sash",
              "Door": "door", "Glass": "glass"}
PALETTE = {"granite": ["#9C7D6E", 0.9, 0.0], "brick": ["#8A3826", 0.85, 0.0], "stone": ["#5C392B", 0.85, 0.0],
           "trim": ["#CDB48A", 0.7, 0.0], "roof": ["#3D4842", 0.75, 0.0], "copper": ["#5B8B76", 0.55, 0.2],
           "planks": ["#6B4A33", 0.75, 0.0], "sash": ["#2A2622", 0.45, 0.0], "door": ["#4A2A1C", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Thornbury)
LEDGE = 1.4
JOINT = dict(pitch=14.0, margin=4.0, layers=[
    dict(kind="course", h=1.6, b=1.0, orn="nailheadstud", role="Brownstone"),
    dict(kind="frieze", h=5.2, b=1.2, orn="byzantineknot", role="Sandstone"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="torus", role="Brownstone")])
EAVE = dict(pitch=6.4, margin=3.0, layers=[
    dict(kind="course", h=1.6, b=1.0, orn="nailheadstud", role="Brownstone"),
    dict(kind="frieze", h=6.4, b=1.2, orn="byzantineleaf", role="Sandstone"),
    dict(kind="bed", h=3.4, b=1.4, P=7.2, role="Brownstone", brackets=dict(style="rollcorbel", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.6, b=1.4, P=8.0, orn="bevel", role="Brownstone")])
TOWER_C = dict(pitch=5.6, margin=1.6, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="byzantineknot", role="Sandstone"),
    dict(kind="bed", h=2.6, b=1.4, P=5.8, role="Brownstone", brackets=dict(style="rollcorbel", t=1.6, reach=0.5)),
    dict(kind="crown", h=2.4, b=1.4, P=6.4, orn="bevel", role="Brownstone")])
CREST_COURSE = dict(h=2.6, b=0.6, orn=G.pelletchain, role="Brownstone")
CREST_CROWN = dict(h=2.4, P=3.4, kind="torus", role="Copper", blocks=None)
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 8.0
S1 = ZF + 38.0
ZE = S1 + RJ + 32.0
ZW = ZE + HE
DK = EAVE["layers"][-1]["P"] + 0.2
RH = 40.0
ZR1 = ZW + RH
D_TOP = round(DK - 2.6 - (RH - 2.2) / math.tan(math.radians(62.0)), 1)
ROOF = [(DK, ZW), (DK - 2.6, ZW + 2.2), (D_TOP, ZR1)]           # a kick at the foot, then steep
SLATE = dict(pitch=1.7, wtab=2.0, d=0.4, shape=G.slate_keybands)
Z_ADD = ZW + 3.0
ZT = ZW + 22.0                                   # the tower's top stage over the eave
ZTW = ZT + CO.band_height(TOWER_C)
DT = TOWER_C["layers"][-1]["P"] + 0.2
CONE_H = 52.0
G.TB_LEVELS.update(hi=S1 + RJ - ZF)
V1, V2 = 6.0, S1 + RJ - ZF + 3.0

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 144.0, 96.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
TA, TC = 23.0, (10.0, 0.0)                       # the round tower (a 12-gon) on the front-west corner
TOWER = Block("tower", ngon(TC, TA, n=12), ZF, ZTW)
# the apse: five facets on an arc of radius 28 bulging 18 out of the back wall (the library)
AR, AC = 28.0, (72.0, Y1 - 10.0)
_aa = math.asin((Y1 - AC[1]) / AR)
APSE_ARC = [(AC[0] + AR * math.cos(a), AC[1] + AR * math.sin(a)) for a in np.linspace(_aa, math.pi - _aa, 6)]
APSE = Block("apse", [(APSE_ARC[0][0], Y1 - 3.0), (APSE_ARC[0][0], Y1)] + APSE_ARC[1:-1] +
             [(APSE_ARC[-1][0], Y1), (APSE_ARC[-1][0], Y1 - 3.0)], ZF, ZW)
BLOCKS = [MAIN, TOWER, APSE]
DOOR_X = 72.0
CHIMS = [(44.0, 62.0), (110.0, 48.0)]


def _walls(f, b, reg):
    """Rock-faced granite below the joint, Roman brick above; nothing in the cornice bands."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    if b is TOWER:                               # (the skins stop short of the facets' ends: a brick
        reg = reg - rect(-1, ZT - b.z0 - LEDGE - 0.6, f.L + 1, 999)      # end would jut past a turn)
        reg = reg ^ rect(0.35, -100, f.L - 0.35, 999)
    lo = reg ^ rect(-1, -100, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, S1 + RJ - b.z0, f.L + 1, 999)
    out = []
    if not lo.is_empty():
        out.append(G.rockfaced(lo, datum=0.0, seed=11 + int(f.L * 7) % 89))
    if not hi.is_empty():
        out.append(G.brick_roman(hi, datum=S1 + RJ - b.z0 + 0.2))
    return union(out) if out else M()


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    def add_face(e, v0, sp, name):
        f = TOWER.facades()[e]
        L.append(Opening(TOWER, e, f.L / 2, v0, sp, name, "window"))

    lo, up = G.window_thornbury_ground(), G.window_thornbury_ribbon()
    add(DOOR_X, 0.0, 1.2, G.door_thornbury(), "front-door", "door")
    for x in (46.0, 96.0, 112.0, 131.0):
        add(x, 0.0, V1, lo, f"S{x:.0f}-1")
    for x in (52.0, 92.0, 126.0):
        add(x, 0.0, V2, up, f"S{x:.0f}-2")
    for y in (44.0, 74.0):
        add(0.0, y, V1, lo, f"W{y:.0f}-1")
    for y in (48.0, 78.0):
        add(0.0, y, V2, up, f"W{y:.0f}-2")
    for y in (22.0, 48.0, 74.0):
        add(X1, y, V1, lo, f"E{y:.0f}-1")
    for y in (30.0, 68.0):
        add(X1, y, V2, up, f"E{y:.0f}-2")
    for x in (22.0, 134.0):
        add(x, Y1, V1, lo, f"N{x:.0f}-1")
    for x in (24.0, 122.0):
        add(x, Y1, V2, up, f"N{x:.0f}-2")
    add(114.0, Y1, 1.2, G.door_thornbury(w=10.0, h=21.0, orders=2), "back-door", "door")
    for i in (1, 2, 3):
        x, y = (APSE_ARC[i][0] + APSE_ARC[i + 1][0]) / 2, (APSE_ARC[i][1] + APSE_ARC[i + 1][1]) / 2
        e, u = APSE.locate(x, y)
        L.append(Opening(APSE, e, u, V1 + 2.0, G.window_thornbury_tower(w=6.4, h=17.0), f"A{i}-1", "window"))
        L.append(Opening(APSE, e, u, V2 + 1.0, G.window_thornbury_tower(w=6.4, h=15.0), f"A{i}-2", "window"))
    for e in (10, 0, 2):
        add_face(e, V1 + 2.0, G.window_thornbury_tower(h=16.0), f"T{e}-1")
        add_face(e, V2 + 1.0, G.window_thornbury_tower(h=15.0), f"T{e}-2")
        add_face(e, ZW - ZF + 2.4, G.window_thornbury_tower(h=12.0), f"T{e}-3")
    return L


OPENINGS = _openings()
ADDINS = [(58.0, 0.0), (108.0, 0.0), (28.0, Y1), (72.0, Y1), (116.0, Y1), (X1, 32.0), (X1, 66.0), (0.0, 66.0)]


def _frame_on(block, x, y, z, w0):
    e, u = block.locate(x, y)
    f = block.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, z - block.z0, w0)
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
                 ("Copper", a["frame"].transform(A))]
        kit.add(f"{tag}-{k}", "Addins", a["solid"].transform(A), P=inv34(A), change=(round(depth, 1), "Copper"),
                key=tag, group="addins", render=zones)
    print(tag, "plug", depth)
    return union(keeps), union(flashes)


def _deck_plate(C, z):
    """The roof's flat top: standing-seam lead in the long direction."""
    dcs = poly(R.offset_path(C["path"], -1.6))
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x0, y - 0.25, x1, y + 0.25) for y in np.arange(y0 + 2.8, y1, 5.6)]) ^ dcs
    return C["deck"] + slab(seams, z - 0.01, z + 0.4)


def _porch(kit, allcs, inserts, t0):
    """The porch: along the west side, round the tower's foot on an octagon, along the front to
    past the door; squat cushion columns, Syrian arches, a corbel table, a rock-faced base."""
    PD, FY, WX, YN, XE = 13.0, -16.0, -14.4, 64.0, 100.0
    Q = [np.array(q) for q in ngon(TC, TA + PD, n=8)]

    def cross(a, b, c, d):                       # where line a-b meets line c-d
        t = np.cross(c - a, d - c) / np.cross(b - a, d - c)
        return a + (b - a) * t

    P1 = tuple(cross(Q[1], Q[2], np.array([0.0, FY]), np.array([1.0, FY])))
    P2 = tuple(cross(Q[5], Q[6], np.array([WX, 0.0]), np.array([WX, 1.0])))
    w_ = -1.4                                    # the porch's wall line, clear of the plinth's face
    pts = [(w_, YN), (WX, YN), P2, tuple(Q[6]), tuple(Q[7]), tuple(Q[0]), tuple(Q[1]), P1, (XE, FY), (XE, w_), (w_, w_)]
    ca = 1.6 * math.tan(math.radians(22.5))      # at the octagon's corners (a 45 degree turn)

    def L_(a, b):
        return float(np.linalg.norm(np.array(b) - np.array(a)))

    Lw, L2, Lo, L6, Lf, Le = YN - P2[1], L_(P2, Q[6]), L_(Q[6], Q[7]), L_(Q[1], P1), XE - P1[0], -w_ - FY
    ud = DOOR_X - P1[0]
    runs = [dict(a=(w_, YN), b=(WX, YN), posts=[1.7, w_ - WX - 1.6]),
            dict(a=(WX, YN), b=P2, posts=[1.6, Lw / 2, Lw + ca], piers=[1.6, Lw / 2, Lw - ca]),
            dict(a=P2, b=tuple(Q[6]), posts=[-ca, L2 - ca], piers=[ca, L2 - ca]),
            dict(a=tuple(Q[6]), b=tuple(Q[7]), posts=[ca, Lo / 2, Lo - ca]),
            dict(a=tuple(Q[7]), b=tuple(Q[0]), posts=[ca, Lo / 2, Lo - ca]),
            dict(a=tuple(Q[0]), b=tuple(Q[1]), posts=[ca, Lo / 2, Lo - ca]),
            dict(a=tuple(Q[1]), b=P1, posts=[ca, L6 + ca], piers=[ca, L6 - ca]),
            dict(a=P1, b=(XE, FY), posts=[-ca, ud - 12.0, ud + 12.0, Lf - 1.6], piers=[ca, ud - 12.0, ud + 12.0, Lf - 1.6]),
            dict(a=(XE, FY), b=(XE, w_), posts=[1.6, Le - 1.7])]
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    P = FT.porch_turned(pts, runs, H_floor, post_h, steps_at=[(7, ud, 18.0)], planks=dict(pitch=1.5, border=1.8),
                        post="cushion", rail="spindleknop", arcade="syrianarch", skirt="rockwall", pier_tex="granite",
                        roof_edge="corbeltable", drop=9.0, beam=2.4, top=True)
    where = []                                   # hidden keys tie each post's beams into the roof seat
    for r in runs:
        f = Facade(np.array(r["a"]), np.array(r["b"]), 0.0)
        for u in r["posts"]:
            p = f.p0 + f.u * u - f.n * 1.6
            if not any(np.allclose(p, q, atol=0.05) for q in where):
                where.append(p)
    z0r = H_floor + post_h
    P["top"] = P["top"] + union([box([p[0] - 0.5, p[1] - 0.5, z0r - 0.6], [p[0] + 0.5, p[1] + 0.5, z0r + 0.6]) for p in where])
    fkeep = slab(offset(allcs, 1.7), -1, ZF + 1.3)
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    deck_ = P["deck"] - fkeep
    kit.add("PORCH-deck", "Granite", deck_, P=print_flip(), group="porch",
            render=FT.plank_zones(deck_, H_floor, "Planks", "Granite"))
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=300) for b in BLOCKS])
    ptop = FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_keep, "Sandstone", "Sandstone", tin_col="Copper", tin="flat")["ptop"]
    parts = {p_.name: p_ for p_ in kit.parts}
    parts["PORCH-top"].solid = parts["PORCH-top"].solid - parts["FOUNDATION"].solid
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Granite", sm.transform(A) - fkeep - parts["PORCH-top"].solid, group="porch")
    edep = 4.0                                   # the rock-faced gable over the steps
    Ag = np.array([[-1.0, 0, 0, DOOR_X], [0, -1.0, 0, FY - 1.0 + edep], [0, 0, 1.0, ptop]])
    kit.add("PORCH-gable", "Granite", G.entry_thornbury(24.0, edep, 13.0).transform(Ag), P=inv34(Ag), group="porch")
    e, u = MAIN.locate(114.0, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Granite", FT.steps(14.0, ZF - 0.6, 4).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    allcs = cs_union([b.cs for b in BLOCKS])
    eave_path = max(allcs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(allcs, 10.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="thornbury", clear=[lip_keep(allcs, 3.0, ZF, 1.2)],
                        siding=_walls, prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=undress)
    kit.add("WALLS-1", "Granite", st["shells"][0], group="walls")
    kit.add("JOINT", "Brick", st["rings"][0], group="walls")
    ledges = CO.ledge(eave_path, ZE, LEDGE) + CO.ledge(TOWER.pts, ZT, LEDGE)
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(allcs, 3.0, S1 + RJ)
    tlip = _corbel(TOWER.cs, 3.0, ZTW) + lip_ring(TOWER.cs, 3.0, ZTW)
    walls2 = st["shells"][1] + ledges + tring + tlip
    kit.add("WALLS-2", "Brick", walls2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(TOWER.pts, ZT, TOWER_C)
    CO.add_level(kit, rings, "CORNICE-T", "tower")
    kit.add("FOUNDATION", "Granite", foundation(BLOCKS, 0.0, ZF, style="chamfercourse"), group="foundation")
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

    # --- the steep roof (upside down) with its eyebrows, the crest, the deck, stacks, cresting
    tower_hug = TOWER.solid(grow=0.5, dz0=-1, dz1=400)
    mans, mtex, inner = R.mansard(MAIN.pts, ROOF, t=2.6, tex=SLATE)
    mk, mf = _addins(kit, MAIN, ADDINS, ROOF, Z_ADD, G.addin_eyebrow(w=12.0, h=5.4, A=0.8), "ADDIN")
    C = SE.crest_ring(MAIN.pts, D_TOP, ZR1, D_TOP - inner(ZR1), CREST_COURSE, CREST_CROWN)
    # the tower rises through the roof's corner: the roof, its crest, deck and cresting stop clear
    # of its cornice and cone
    tcut = slab(offset(TOWER.cs, DT + 0.4), ZT - LEDGE - 0.8, 999)
    roof = (mans + (mtex - mf)) - mk - C["groove"] - tower_hug - walls2 - tcut
    for k, c in enumerate(sorted([c for c in roof.decompose() if c.volume() > 20.0], key=lambda c: -c.volume())):
        kit.add("ROOF" if k == 0 else f"ROOF-{k}", "Slate", c, P=print_flip(), group="roof")
    crest = C["solid"] - tcut
    for k, c in enumerate(sorted([c for c in crest.decompose() if c.volume() > 2.0], key=lambda c: -c.volume())):
        kit.add("CREST" if k == 0 else f"CREST-{k}", "Brownstone", c, P=print_flip(), change=C["change"], group="roof",
                render=[(r, z ^ c) for r, z in C["zones"]])
    zdeck = C["z_top"]
    pads = union([box([x - 7.6, y - 6.2, zdeck - 0.6], [x + 7.6, y + 6.2, zdeck + 1]) for x, y in CHIMS])
    kit.add("ROOF-deck", "Slate", _deck_plate(C, zdeck) - pads - tcut, group="roof")
    for k, (x, y) in enumerate(CHIMS):
        kit.add(f"CHIMNEY-{k}", "Granite", G.chimney_thornbury(12.0, 9.0, 26.0).translate([x, y, zdeck - 0.6]), key="CHIMNEY", group="roof")
    for i, seg, A, L in SE.cresting_strips(C["path"], zdeck, C["rail"], SE.printable(G.fence_thornbury), 6.4):
        for j, piece in enumerate((seg - tcut).decompose()):
            if piece.volume() > 3.0:
                kit.add(f"CREST-iron-{i}{chr(97 + j)}", "Copper", piece, P=inv34(A), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the tower's bellcast cone and finial
    cprof = [(DT, ZTW), (DT - 2.4, ZTW + 2.0), (-TA + 3.4, ZTW + CONE_H)]
    cone, ctex, _ = R.mansard(TOWER.pts, cprof, t=2.4, tex=dict(pitch=1.5, wtab=1.6, d=0.35, shape=G.slate_keybands))
    ztop = ZTW + CONE_H
    top = slab(offset(TOWER.cs, -TA + 3.4), ztop - 0.6, ztop + 0.8)
    kit.add("TOWER-cone", "Slate", cone + ctex + top - lip_keep(TOWER.cs, 3.0, ZTW), group="tower")
    kit.add("TOWER-finial", "Copper", G.finial_thornbury(12.0).translate([TC[0], TC[1], ztop + 0.79]), group="tower")
    FT.crown(kit, "TOWER-finial", "TOWER-cone")
    print("tower", round(time.time() - t0, 1))

    # --- the apse's flat top at the eave, from the cornice's crown back to the roof's foot, a
    # dwarf-gallery parapet round it
    Pc = EAVE["layers"][-1]["P"]
    mfoot = M.hull_points([(x, y, z) for x, y in R.offset_path(MAIN.pts, DK + 0.7) for z in (ZW - 1, ZW + 40)])
    ad = slab(offset(APSE.cs, Pc + 0.2), ZW, ZW + 1.2) - mfoot
    ad = max(ad.decompose(), key=lambda m_: m_.volume())
    kit.add("APSE-deck", "Slate", ad, group="apse")
    for i, seg, A, L in SE.cresting_strips(APSE.pts, ZW + 1.2, Pc - 1.2, G.fence_thornbury_parapet, 5.6):
        seg = seg - mfoot
        if not seg.is_empty() and seg.volume() > 2.0:
            kit.add(f"APSE-rail-{i}", "Brownstone", seg, P=inv34(A), group="apse")
    print("apse", round(time.time() - t0, 1))

    _porch(kit, allcs, inserts, t0)
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("APSE-rail")]:
        FT.key_into(kit, p_.name, ["APSE-deck"], (0, 0, -1), depth=0.6)
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("CREST-iron")]:
        FT.key_into(kit, p_.name, [q.name for q in kit.parts if q.name.startswith("CREST") and "iron" not in q.name], (0, 0, -1), depth=0.6)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "thornbury")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:60]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "thornbury.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Addins"))
