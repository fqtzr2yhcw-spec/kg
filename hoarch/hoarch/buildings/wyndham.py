"""The Wyndham -- an original HO-scale (1:87.1) Gilded Age mansion, 1889: the flagship of the grand
batch (houses 91 to 100), which blends the collection's Victorian, Colonial and mansard families
(hoarch.grand), on the mansard batch's roof system (hoarch.secondempire).

Pressed brick in Sussex bond below with moulded-brick quoins, beaded narrow-and-wide lap above
with fluted corner pilasters, cream trim and gold accents, on a brownstone plinth of raised
panels. Queen Anne massing: a great octagonal tower on the front-east corner rising a storey over
the eave to a tall bell cap with oval add-ins, a crest, sunflower cresting and a spire threaded
with three orbs; a two-storey bow on the west under a balustraded deck. A Second Empire roof: a
straight mansard slated in a trellis of diamond slates with pagoda-hooded add-ins, and over the
front pavilion a taller bell-cast mansard rising through it with a Palladian add-in. A Colonial
Revival heart: the pavilion's tripartite window, a fanlit entrance between fluted pilasters, and
a porch of Scamozzi Ionic columns across the front, round the tower and up the east side, a
pediment over its steps and a balustrade round its roof.

- Ground-floor windows: Queen Anne sashes (a big light ringed by small border lights) in
  architraves eared at the head, a pulvinated frieze, a cornice and a segmental pediment holding
  a half chrysanthemum, a sill over a panelled apron. Upper windows: one-over-one under a bamboo
  bar and a pagoda hood on two consoles. The tower's top storey: round-headed lights under
  archivolts with keystones between ringed colonnettes.
- Storey joint: a cream bamboo stalk, a gold frieze of chrysanthemum roundels between bamboo
  canes, a cream torus crown.
- Eave: a cream ribbon-and-pearl course, a gold frieze of peacock feathers, a bamboo course, a
  soffit on fiddlehead consoles and a gold ogee crown. The tower's eave: gold lilies under the
  same consoles and crown.
- Crests: a cream Japanese fret under a gold cavetto crown on block modillions.

usage: python3 -m hoarch.buildings.wyndham [check] [export]
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
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Wyndham"
COLORS = {"PorchDeck": "#E6D7B4", "Planks": "#6E4E33",       # the planked porch floor: two colours, one change
          "Brick": "#8E3B2E", "Siding": "#3E5A47", "Cream": "#E6D7B4", "Gold": "#B8862E", "Slate": "#4B4752",
          "Iron": "#232528", "Brownstone": "#6A4A3B", "Windows_Doors": "#E6D7B4", "Addins": "#4B4752"}
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks", "Brick": "brick", "Siding": "siding", "Cream": "trim",
              "Gold": "accent", "Slate": "roof", "Iron": "iron", "Brownstone": "stone", "Windows_Doors": "trim",
              "Addins": "roof", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"brick": ["#8E3B2E", 0.85, 0.0], "siding": ["#3E5A47", 0.75, 0.0], "trim": ["#E6D7B4", 0.6, 0.0],
           "accent": ["#B8862E", 0.45, 0.15], "roof": ["#4B4752", 0.75, 0.0], "iron": ["#232528", 0.45, 0.3],
           "stone": ["#6A4A3B", 0.9, 0.0], "planks": ["#6E4E33", 0.75, 0.0], "sash": ["#2B2A26", 0.45, 0.0],
           "door": ["#5B2A22", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Wyndham)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="bamboo", role="Cream"),
    dict(kind="frieze", h=5.6, b=1.2, orn="chrysanthemums", role="Gold"),
    dict(kind="crown", h=2.2, b=1.4, P=3.8, orn="torus", role="Cream")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="pearlribbon", role="Cream"),
    dict(kind="frieze", h=6.6, b=1.2, orn="peacocks", role="Gold"),
    dict(kind="course", h=1.6, b=1.4, orn="bamboo", role="Cream"),
    dict(kind="bed", h=2.4, b=1.4, P=7.2, role="Cream", brackets=dict(style="fiddlehead", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.8, b=1.4, P=8.0, orn="ogee_fillet", role="Gold")])
TOWER_C = dict(pitch=11.0, margin=3.5, layers=[
    dict(kind="frieze", h=6.0, b=1.2, orn="lilies", role="Gold"),
    dict(kind="bed", h=2.2, b=1.4, P=6.4, role="Cream", brackets=dict(style="fiddlehead", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.4, b=1.4, P=7.0, orn="ogee_fillet", role="Gold")])
CREST_COURSE = dict(h=2.6, b=0.6, orn=G.japanfret, role="Cream")
CREST_CROWN = dict(h=2.6, P=3.6, kind="cavetto", role="Gold", blocks=(0.9, 5.0))
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (all on the 0.2 mm grid)
ZF = 14.0
S1 = ZF + 42.0
ZE = S1 + RJ + 38.0
ZW = ZE + HE
MZ0 = ZW
MH, PMH = 32.0, 46.0        # the main mansard, the pavilion's
MZ1, PZ1 = MZ0 + MH, MZ0 + PMH
DK = EAVE["layers"][-1]["P"] + 0.2
D_TOP, PD_TOP = -2.0, -5.6
MANSARD = [(DK, MZ0), (DK - 1.4, MZ0 + 1.4), (D_TOP, MZ1)]
PAV_MANSARD = SE.bell_profile(DK, MZ0, PD_TOP, PZ1, power=1.8, step=7.2)
SLATE = dict(pitch=1.8, wtab=2.4, d=0.4, shape=G.slate_trellis)
ZT = ZW + 38.0             # the tower's ledge: its top storey stands over the eave
ZTW = ZT + CO.band_height(TOWER_C)
TCAP_H = 34.0
V1, V2 = 6.6, S1 + RJ + 5.0 - ZF
V3 = ZW + 7.0 - ZF
Z_ADD = MZ0 + 3.4
Z_ADDP = MZ0 + 6.0
G.WY_LEVELS.update(lo=S1 - ZF, hi=S1 + RJ - ZF)

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 178.0, 128.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
PX0, PX1, PY0, PY1 = 26.0, 82.0, -16.0, 40.0          # the front pavilion breaks forward 16
PAV = Block("pavilion", [(PX0, PY0), (PX1, PY0), (PX1, PY1), (PX0, PY1)], ZF, ZW)
TA = 26.0                  # the tower's apothem; it stands on the front-east corner
TC = (X1, 0.0)
TOWER = Block("tower", ngon(TC, TA, n=8), ZF, ZTW)
# the bow: five facets on an arc of radius 30 bulging 16 out of the west wall
BR, BC = 30.0, (14.0, 76.0)
_ba = math.acos(BC[0] / BR)
BOW_ARC = [(BC[0] - BR * math.cos(a), BC[1] + BR * math.sin(a)) for a in np.linspace(_ba, -_ba, 6)]
BOW = Block("bow", [(3.0, BOW_ARC[0][1]), (0.0, BOW_ARC[0][1])] + BOW_ARC[1:-1] + [(0.0, BOW_ARC[-1][1]), (3.0, BOW_ARC[-1][1])],
            ZF, ZW)
BLOCKS = [MAIN, PAV, TOWER, BOW]
DOOR_X = 118.0
TFACES = {"S": (X1, -TA), "SE": (X1 + TA / math.sqrt(2), -TA / math.sqrt(2)), "E": (X1 + TA, 0.0)}


def _walls(f, b, reg):
    """Sussex-bond brick below the joint, narrow-and-wide lap above; nothing in the eave band."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    if b is TOWER:
        reg = reg - rect(-1, ZT - b.z0, f.L + 1, 999)
    lo = reg ^ rect(-1, -100, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, S1 + RJ - b.z0, f.L + 1, 999)
    out = []
    if not lo.is_empty():
        out.append(G.brick_sussex(lo, datum=1.8))
    if not hi.is_empty():
        out.append(G.lap_beadnarrow(hi, datum=S1 + RJ - b.z0 + 0.4))
    return union(out) if out else M()


# ------------------------------------------------------------------ openings
def _bow_mids():
    """The bow's three middle facets: their midpoints on the wall line."""
    return [((BOW_ARC[i][0] + BOW_ARC[i + 1][0]) / 2, (BOW_ARC[i][1] + BOW_ARC[i + 1][1]) / 2) for i in (1, 2, 3)]


def _openings():
    L = []
    lo, up = G.window_wyndham_lower(), G.window_wyndham_upper()
    lo_n, up_n = G.window_wyndham_lower(w=7.2, h=22.0, A=0.9), G.window_wyndham_upper(w=7.2, h=20.0, A=0.8)
    lo_t, up_t = G.window_wyndham_lower(w=8.2, h=22.0, A=0.9), G.window_wyndham_upper(w=8.0, h=20.0, A=0.85)
    tw = G.window_wyndham_tower()
    tri = G.window_wyndham_tripartite()
    front, back = G.door_wyndham(), G.door_wyndham_back()

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    add(MAIN, DOOR_X, 0, 0.4, front, "front-door", "door")
    for x in (13.0, 96.0, 140.0):
        add(MAIN, x, 0, V1, lo, f"S{x:.0f}-1")
    for x in (13.0, 96.0, DOOR_X, 140.0):
        add(MAIN, x, 0, V2, up, f"S{x:.0f}-2")
    pc = (PX0 + PX1) / 2
    add(PAV, pc, PY0, V1, tri, "P-1")
    for x in (pc - 13.0, pc + 13.0):
        add(PAV, x, PY0, V2, up, f"P{x:.0f}-2")
    for k, (x, y) in TFACES.items():                    # the tower's three street faces
        add(TOWER, x, y, V1, lo_t, f"T{k}-1")
        add(TOWER, x, y, V2, up_t, f"T{k}-2")
        add(TOWER, x, y, V3, tw, f"T{k}-3")
    for y in (60.0, 100.0):
        add(MAIN, X1, y, V1, lo, f"E{y:.0f}-1")
        add(MAIN, X1, y, V2, up, f"E{y:.0f}-2")
    for y in (20.0, 116.0):
        add(MAIN, 0, y, V1, lo, f"W{y:.0f}-1")
        add(MAIN, 0, y, V2, up, f"W{y:.0f}-2")
    for i, (x, y) in enumerate(_bow_mids()):
        add(BOW, x, y, V1, lo_n, f"B{i}-1")
        add(BOW, x, y, V2, up_n, f"B{i}-2")
    for x in (30.0, 118.0, 160.0):
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
    for x in (30.0, 74.0, 118.0, 160.0):
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, 74.0, Y1, 0.4, back, "back-door", "door")
    return L


OPENINGS = _openings()
ADDINS = [(96.0, 0.0), (140.0, 0.0), (X1, 60.0), (X1, 100.0), (160.0, Y1), (118.0, Y1), (74.0, Y1), (30.0, Y1),
          (0.0, 114.0), (0.0, 76.0), (0.0, 20.0)]


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


def _addins(kit, block, places, prof, z_sill, sp, tag, key=None):
    pl = [SE.addin_place(sp, prof, z_sill) for _ in places]
    depth = max(d for _, d in pl)
    keeps, flashes = [], []
    for k, ((x, y), (w0, _)) in enumerate(zip(places, pl)):
        A = _frame_on(block, x, y, z_sill, w0)
        a = SE.addin(sp, depth)
        keeps.append(a["keep"].transform(A))
        flashes.append(a["flash"].transform(A))
        zones = [("Glass", a["glass"].transform(A)), ("Slate", (a["plug"] - a["glass"]).transform(A)),
                 ("Cream", a["frame"].transform(A))]
        kit.add(f"{tag}-{k}", "Addins", a["solid"].transform(A), P=inv34(A), change=(round(depth, 1), "Cream"),
                key=key or tag, group="addins", render=zones)
    print(tag, "plug", depth)
    return union(keeps), union(flashes)


def _deck(C, z, seams_along_x=True):
    dcs = poly(R.offset_path(C["path"], -1.6))
    x0, y0, x1, y1 = dcs.bounds()
    if seams_along_x:
        seams = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + 2.6, x1, 5.2)]) ^ dcs
    else:
        seams = cs_union([rect(x0, y - 0.25, x1, y + 0.25) for y in np.arange(y0 + 2.6, y1, 5.2)]) ^ dcs
    return C["deck"] + slab(seams, z - 0.01, z + 0.4)


def _inset_chain(pts, d):
    """An open chain of points moved ``d`` to its left (inward for a CCW yard edge): each
    corner where the two offset lines meet, the ends moved square to their edge."""
    P = [np.asarray(p, float) for p in pts]
    n = len(P)
    nrm = []
    for i in range(n - 1):
        t = (P[i + 1] - P[i]) / np.linalg.norm(P[i + 1] - P[i])
        nrm.append(np.array([-t[1], t[0]]))
    out = [P[0] + d * nrm[0]]
    for i in range(1, n - 1):
        a0, a1 = P[i - 1] + d * nrm[i - 1], P[i] + d * nrm[i - 1]
        b0, b1 = P[i] + d * nrm[i], P[i + 1] + d * nrm[i]
        da, db = a1 - a0, b1 - b0
        den = da[0] * db[1] - da[1] * db[0]
        if abs(den) < 1e-9:
            out.append(a1)
        else:
            s = ((b0[0] - a0[0]) * db[1] - (b0[1] - a0[1]) * db[0]) / den
            out.append(a0 + da * s)
    out.append(P[-1] + d * nrm[-1])
    return [tuple(p) for p in out]


def _add_split(kit, name, color, solid, render=None, **kw):
    """Add a part that falls into separate pieces as one part per piece: the biggest keeps the
    name, the next is ``-front``; each piece takes its share of the colour zones."""
    pcs = sorted([c for c in solid.decompose() if c.volume() > 1.0], key=lambda c: -c.volume())
    for i, c in enumerate(pcs):
        nm = name if i == 0 else (f"{name}-front" if i == 1 else f"{name}-{i}")
        kit.add(nm, color, c, render=None if render is None else [(r, z ^ c) for r, z in render], **kw)


# ------------------------------------------------------------------ build
def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    allcs = cs_union([b.cs for b in BLOCKS])
    eave_path = max(allcs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(allcs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="wyndham", clear=[lip_keep(allcs, 3.0, ZF, 1.2)],
                        siding=_walls, prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=undress)
    kit.add("WALLS-1", "Brick", st["shells"][0], group="walls")
    kit.add("JOINT", "Siding", st["rings"][0], group="walls")
    # inside the house the tower's walls rise from the joint so its top storey bears all round
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(allcs, 3.0, S1 + RJ)
    ledges = CO.ledge(eave_path, ZE, LEDGE) + CO.ledge(TOWER.pts, ZT, LEDGE)
    tlip = _corbel(TOWER.cs, 3.0, ZTW) + lip_ring(TOWER.cs, 3.0, ZTW)
    walls2 = st["shells"][1] + tring + ledges + tlip
    kit.add("WALLS-2", "Siding", walls2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    cut = CO.blades(CO.tower_cuts(eave_path, TC, 36.0, wall=TA, away=(1.0, -1.0)), ZE, ZW)
    rings, _ = CO.level(eave_path, ZE, EAVE, cut=cut)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(TOWER.pts, ZT, TOWER_C)
    CO.add_level(kit, rings, "CORNICE-T", "tower")
    kit.add("FOUNDATION", "Brownstone", foundation(BLOCKS, 0.0, ZF, style="panelplinth"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Cream", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    tower_keep = TOWER.solid(grow=2.1, dz0=-1, dz1=400)
    tower_hug = TOWER.solid(grow=0.5, dz0=-1, dz1=400)          # the roofs' notches hug the tower
    # --- the two mansards (upside down); the pavilion's rises through the main one, each cut back
    # to the other's slates
    pav_vol = _volume(PAV.pts, [(d + 0.5, z) for d, z in PAV_MANSARD], top=20.0)
    main_vol = _volume(MAIN.pts, [(d + 0.5, z) for d, z in MANSARD])
    mans, mtex, inner = R.mansard(MAIN.pts, MANSARD, t=2.6, tex=SLATE)
    pmans, ptex, pinner = R.mansard(PAV.pts, PAV_MANSARD, t=2.6, tex=SLATE)
    mk, mf = _addins(kit, MAIN, ADDINS, MANSARD, Z_ADD, G.addin_wyndham(), "ADDIN")
    pk, pf = _addins(kit, PAV, [((PX0 + PX1) / 2, PY0)], PAV_MANSARD, Z_ADDP, G.addin_wyndham_palladian(), "ADDIN-P")
    C = SE.crest_ring(MAIN.pts, D_TOP, MZ1, D_TOP - inner(MZ1), CREST_COURSE, CREST_CROWN)
    PC = SE.crest_ring(PAV.pts, PD_TOP, PZ1, PD_TOP - pinner(PZ1), CREST_COURSE, CREST_CROWN)
    # the pavilion and the tower box in the front slope between them: it and its crest print as
    # parts of their own
    _add_split(kit, "MANSARD", "Slate", (mans + (mtex - mf)) - mk - pav_vol - tower_hug - C["groove"], P=print_flip(),
               group="roof")
    kit.add("MANSARD-P", "Slate", (pmans + (ptex - pf)) - pk - main_vol - PC["groove"], P=print_flip(), group="pavilion")
    _add_split(kit, "CREST", "Gold", C["solid"] - pav_vol - tower_hug, P=print_flip(), change=C["change"], group="roof",
               render=[(r, z - pav_vol - tower_hug) for r, z in C["zones"]])
    zdeck = C["z_top"]
    chims = [(44.0, 100.0), (150.0, 96.0)]
    pads = union([box([x - 6.0, y - 5.0, zdeck - 0.6], [x + 6.0, y + 5.0, zdeck + 1]) for x, y in chims])
    # (the deck hugs the tower's corner boards too)
    kit.add("ROOF-deck", "Slate", _deck(C, zdeck) - pads - pav_vol - tower_hug - walls2, group="roof")
    for i, seg, A, L in SE.cresting_strips(C["path"], zdeck, C["rail"], SE.printable(G.fence_wyndham), 7.2):
        for j, piece in enumerate((seg - pav_vol - tower_keep).decompose()):
            if piece.volume() > 3.0:
                kit.add(f"CREST-iron-{i}{chr(97 + j)}", "Iron", piece, P=inv34(A), group="roof")
    for k, (x, y) in enumerate(chims):
        ch = G.chimney_wyndham(w=11.0, d=9.0, h=27.0).translate([x, y, zdeck - 0.6])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof")
    kit.add("PAV-CREST", "Gold", PC["solid"], P=print_flip(), change=PC["change"], group="pavilion", render=PC["zones"])
    pz = PC["z_top"]
    kit.add("PAV-deck", "Slate", _deck(PC, pz), group="pavilion")
    for i, seg, A, L in SE.cresting_strips(PC["path"], pz, PC["rail"], SE.printable(G.fence_wyndham), 7.2):
        kit.add(f"PAV-iron-{i}", "Iron", seg, P=inv34(A), key=f"PAV-iron-{round(L, 1)}", group="pavilion")
    print("roofs", round(time.time() - t0, 1))

    # --- the bow's deck at the eave, from its crown back to the mansard's foot, a balustrade round it
    Pc = EAVE["layers"][-1]["P"]
    mfoot = M.hull_points([(x, y, z) for x, y in R.offset_path(MAIN.pts, DK + 0.1) for z in (ZW - 1, ZW + 40)])
    bd = slab(offset(BOW.cs, Pc + 0.2), ZW, ZW + 1.2) - mfoot
    bd = max(bd.decompose(), key=lambda m_: m_.volume())
    kit.add("BOW-deck", "Slate", bd, group="bow")
    for i, seg, A, L in SE.cresting_strips(BOW.pts, ZW + 1.2, Pc - 1.2, G.fence_wyndham_balustrade, 5.2):
        seg = seg - mfoot
        if not seg.is_empty() and seg.volume() > 2.0:
            kit.add(f"BOW-rail-{i}", "Cream", seg, P=inv34(A), group="bow")
    print("bow", round(time.time() - t0, 1))

    # --- the tower: its cornice (above), a tall bell cap with oval add-ins on the street faces,
    # crest, cresting, finial
    cprof = SE.bell_cap(ZTW, TCAP_H, TOWER_C["layers"][-1]["P"] + 0.2, -11.6, a=0.45, bands=10)
    cap, ctex, cin = R.mansard(TOWER.pts, cprof, t=2.4, tex=dict(pitch=1.6, wtab=2.0, d=0.35, shape=G.slate_trellis))
    tk, tf = _addins(kit, TOWER, list(TFACES.values()), cprof, ZTW + 5.0, G.addin_wyndham_tower(), "ADDIN-T")
    TCR = SE.crest_ring(TOWER.pts, cprof[-1][0], ZTW + TCAP_H, cprof[-1][0] - cin(ZTW + TCAP_H), CREST_COURSE, CREST_CROWN)
    tcap = (cap + (ctex - tf)) - tk - lip_keep(TOWER.cs, 3.0, ZTW) - TCR["groove"]
    tcap = union([c for c in tcap.decompose() if c.volume() > 50.0])
    kit.add("TOWER-CAP", "Slate", tcap, P=print_flip(), group="tower")
    kit.add("TOWER-CREST", "Gold", TCR["solid"], P=print_flip(), change=TCR["change"], group="tower", render=TCR["zones"])
    tz = TCR["z_top"]
    kit.add("TOWER-deck", "Slate", TCR["deck"], group="tower")
    for i, seg, A, L in SE.cresting_strips(TCR["path"], tz, TCR["rail"], SE.printable(G.fence_wyndham), 6.8):
        kit.add(f"TOWER-iron-{i}", "Iron", seg, P=inv34(A), key=f"TOWER-iron-{round(L, 1)}", group="tower")
    kit.add("TOWER-finial", "Iron", G.finial_wyndham(16.0).translate([TC[0], TC[1], tz - 0.01]), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- the porch: across the front from the pavilion, round the tower's foot, up the east side
    PD, FY, EX, YN = 14.0, -18.0, X1 + 18.0, 76.0
    Q = [np.array(q) for q in ngon(TC, TA + PD, n=8)]

    def cross(a, b, c, d):                       # where line a-b meets line c-d
        t = np.cross(c - a, d - c) / np.cross(b - a, d - c)
        return a + (b - a) * t

    P1 = tuple(cross(Q[7], Q[0], np.array([0.0, FY]), np.array([1.0, FY])))
    P2 = tuple(cross(Q[3], Q[4], np.array([EX, 0.0]), np.array([EX, 1.0])))
    w_ = -1.4                                    # the porch's wall line, clear of the foundation's face
    XA = PX1 + 1.4
    pts = [(XA, w_), (XA, FY), P1, tuple(Q[0]), tuple(Q[1]), tuple(Q[2]), tuple(Q[3]), P2, (EX, YN), (X1 + 1.4, YN),
           (X1 + 1.4, w_)]
    ca = 1.6 * math.tan(math.radians(22.5))      # at the octagon's corners (a 45 degree turn)

    def L_(a, b):
        return float(np.linalg.norm(np.array(b) - np.array(a)))

    Lf, Lo = L_((XA, FY), P1), L_(Q[0], Q[1])
    ud = DOOR_X - XA
    runs = [dict(a=(XA, w_), b=(XA, FY), posts=[1.7, w_ - FY - 1.6]),
            dict(a=(XA, FY), b=P1, posts=[1.6, ud - 11.0, ud + 11.0, Lf + ca], piers=[1.6, ud - 11.0, ud + 11.0, Lf - ca]),
            dict(a=P1, b=tuple(Q[0]), posts=[-ca, L_(P1, Q[0]) - ca], piers=[ca, L_(P1, Q[0]) - ca]),
            dict(a=tuple(Q[0]), b=tuple(Q[1]), posts=[ca, Lo / 2, Lo - ca]),
            dict(a=tuple(Q[1]), b=tuple(Q[2]), posts=[ca, Lo / 2, Lo - ca]),
            dict(a=tuple(Q[2]), b=tuple(Q[3]), posts=[ca, Lo / 2, Lo - ca]),
            dict(a=tuple(Q[3]), b=P2, posts=[ca, L_(Q[3], P2) + ca], piers=[ca, L_(Q[3], P2) - ca]),
            dict(a=P2, b=(EX, YN), posts=[-ca, (YN - P2[1]) / 2, YN - P2[1] - 1.6], piers=[ca, (YN - P2[1]) / 2, YN - P2[1] - 1.6]),
            dict(a=(EX, YN), b=(X1 + 1.4, YN), posts=[1.6, EX - X1 - 1.4 - 1.7])]
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    P = FT.porch_turned(pts, runs, H_floor, post_h, steps_at=[(1, ud, 18.0)], planks=dict(pitch=1.4, border=1.6),
                        joined=True, post="scamozzi", rail="bottleblock", arcade="ballspindle", skirt="sunpanels",
                        pier_tex="stone", roof_edge="ballfringe", top=True)
    fkeep = slab(offset(allcs, 1.7), -1, ZF + 1.3)
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    deck_ = P["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck_, P=print_flip(), group="porch",
            render=FT.plank_zones(deck_, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=300) for b in BLOCKS])
    ptop = FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_keep, "Cream", "Cream", tin_col="Slate", tin="flat")["ptop"]
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Brownstone", sm.transform(A) - fkeep, group="porch")
    # a pediment over the steps, standing on the porch roof
    edep = 5.0
    Ag = np.array([[-1.0, 0, 0, DOOR_X], [0, -1.0, 0, FY - 1.0 + edep], [0, 0, 1.0, ptop]])
    kit.add("PORCH-pediment", "Cream", G.entry_wyndham(22.0, edep, 7.0).transform(Ag), P=inv34(Ag), group="porch")
    # a balustrade round the porch roof, over the beams, stopping clear of the pediment
    chain = _inset_chain([(XA, w_), (XA, FY), P1] + [tuple(q) for q in Q[0:4]] + [P2, (EX, YN), (X1 + 1.4, YN)], 2.2)
    ped_keep = box([DOOR_X - 12.5, FY - 3.0, ptop - 1], [DOOR_X + 12.5, FY + 8.0, ptop + 12])
    for i in range(len(chain) - 1):
        a, b = np.array(chain[i]), np.array(chain[i + 1])
        f = Facade(a, b, 0.0)
        if f.L < 4.0:
            continue
        cs = G.fence_wyndham_balustrade(f.L - 0.8, 5.0).translate([0.4, 0.0])
        strip = M.extrude(cs, 0.9).translate([0, 0, -0.45])
        A = f.A.copy()
        A[:, 3] = f.world(0, 0, 0) + np.array([0, 0, ptop - 0.01])
        seg = strip.transform(A) - ped_keep - bld_keep
        for j, piece in enumerate(seg.decompose()):
            if piece.volume() > 3.0:
                kit.add(f"PORCH-rail-{i}{chr(97 + j)}", "Cream", piece, P=inv34(A), group="porch")
    e, u = MAIN.locate(74.0, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Brownstone", FT.steps(15.0, ZF - 0.6, 5).transform(A), group="porch")
    parts = {p_.name: p_ for p_ in kit.parts}
    parts["PORCH-top"].solid = parts["PORCH-top"].solid - parts["FOUNDATION"].solid
    print("porch", round(time.time() - t0, 1))
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("CREST-iron")]:
        FT.key_into(kit, p_.name, ["CREST", "CREST-front"], (0, 0, -1), depth=0.6)
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("PAV-iron")]:
        FT.key_into(kit, p_.name, ["PAV-CREST"], (0, 0, -1), depth=0.6)
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("TOWER-iron")]:
        FT.key_into(kit, p_.name, ["TOWER-CREST"], (0, 0, -1), depth=0.6)
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("BOW-rail")]:
        FT.key_into(kit, p_.name, ["BOW-deck"], (0, 0, -1), depth=0.6)
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("PORCH-rail")]:
        FT.key_into(kit, p_.name, ["PORCH-top"], (0, 0, -1), depth=0.6)
    FT.crown(kit, "TOWER-finial", "TOWER-deck")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "wyndham")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "wyndham.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Addins"))
