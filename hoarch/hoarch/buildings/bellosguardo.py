"""The Bellosguardo -- an original HO-scale (1:87.1) Italian villa, 1866: the third of the grand batch
(houses 91 to 100, hoarch.grand).

The pattern books' "Tuscan villa" in an L: a ground storey of brownstone drafted ashlar on a
battered talus with barred vents, and an upper storey of orange Siena brick in monk bond with a
diaper of raised headers, pillowed quoins, cream stone dressings and olive accents. A flat roof
behind a stone balustrade set with urns, over a deep cornice of rosette coffers between paired
pendant scrolls. In the angle of the L a campanile rises two stages over the roof: a stage of
bifora windows under a guilloche band, then an open belvedere loggia of paired arches, under a
cornice of laurel wreaths and a pyramid of clay tiles crowned by a pine cone. A loggia of
Corinthian columns and archivolted arches wraps the front and the west side on a paved floor,
its flat roof a terrace behind the same balustrade. The wing's upper storey holds a Serliana over
a balconet; the door stands in a Gibbs surround of rusticated blocks under a cornice.

- Ground storey: round-headed two-over-two sashes under Florentine voussoirs on impost blocks,
  sills over panelled aprons. Upper storey: tabernacle windows (eared architraves, festooned
  friezes, cornice hoods on scroll consoles).
- Storey joint: a cream guilloche, an olive frieze of olive branches, a cream bevelled crown.
- Eave: cream egg and dart, olive coffers with rosettes, paired pendant scrolls, a cream cyma.
- Campanile: a guilloche band between its stages; wreaths under the same consoles at its eave.

usage: python3 -m hoarch.buildings.bellosguardo [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import Facade, arch_cs, box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, grand as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, stacked_shells

NAME = "The Bellosguardo"
COLORS = {"Stone": "#E2D6BC", "Brownstone": "#7A5643", "Brick": "#B4633E", "Olive": "#5D6B3A", "Tile": "#A2502F",
          "Iron": "#232528", "Roof": "#6A6560", "Windows_Doors": "#E2D6BC"}
RENDER_MAT = {"Stone": "stone", "Brownstone": "brownstone", "Brick": "brick", "Olive": "accent", "Tile": "tile",
              "Iron": "iron", "Roof": "roof", "Windows_Doors": "stone", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"stone": ["#E2D6BC", 0.75, 0.0], "brownstone": ["#7A5643", 0.9, 0.0], "brick": ["#B4633E", 0.85, 0.0],
           "accent": ["#5D6B3A", 0.6, 0.0], "tile": ["#A2502F", 0.8, 0.0], "iron": ["#232528", 0.45, 0.3],
           "roof": ["#6A6560", 0.7, 0.0], "sash": ["#2F3A26", 0.45, 0.0], "door": ["#4A3020", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Bellosguardo)
LEDGE = 1.4
JOINT = dict(pitch=14.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="guillocheroses", role="Stone"),
    dict(kind="frieze", h=5.0, b=1.2, orn="olivebranch", role="Olive"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="bevel", role="Stone")])
EAVE = dict(pitch=16.0, margin=5.0, pair=3.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="eggdartfine", role="Stone"),
    dict(kind="frieze", h=7.2, b=1.2, orn="rosettecoffers", role="Olive"),
    dict(kind="bed", h=3.0, b=1.4, P=8.6, role="Stone", brackets=dict(style="pendantscroll", t=1.6, reach=0.6)),
    dict(kind="crown", h=3.0, b=1.4, P=9.4, orn="cyma", role="Stone")])
TOWER_J = dict(pitch=12.0, margin=3.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="guillocheroses", role="Stone"),
    dict(kind="crown", h=1.8, b=1.2, P=3.0, orn="bevel", role="Stone")])
TOWER_C = dict(pitch=11.0, margin=3.5, pair=2.6, layers=[
    dict(kind="frieze", h=5.4, b=1.2, orn="wreathribbons", role="Olive"),
    dict(kind="bed", h=2.6, b=1.4, P=6.8, role="Stone", brackets=dict(style="pendantscroll", t=1.4, reach=0.5)),
    dict(kind="crown", h=2.6, b=1.4, P=7.4, orn="cyma", role="Stone")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 8.0
S1 = ZF + 34.0
ZE = S1 + RJ + 36.0
ZW = ZE + HE
DK = EAVE["layers"][-1]["P"] + 0.2
ZTA = ZW + 24.0                                  # the campanile's bifora stage, deck to band
ZTB0 = ZTA + CO.band_height(TOWER_J)
ZTB = ZTB0 + 20.0                                # the open loggia stage
ZTW = ZTB + CO.band_height(TOWER_C)
DT = TOWER_C["layers"][-1]["P"] + 0.2
G.BS_LEVELS.update(hi=S1 + RJ - ZF)
V1, V2 = 7.0, S1 + RJ - ZF + 4.0

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 132.0, 96.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
WX0, WY0 = 84.0, -22.0
WING = Block("wing", [(WX0, WY0), (X1, WY0), (X1, 0.0), (WX0, 0.0)], ZF, ZW)
TX0, TX1, TY0, TY1 = 58.0, 84.0, -16.0, 10.0
TOWER = Block("tower", [(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)], ZF, ZTW)
TC = ((TX0 + TX1) / 2, (TY0 + TY1) / 2)
BLOCKS = [MAIN, WING, TOWER]
DOOR_X = 30.6
LD = 16.0                                        # the loggia's depth
LN = 56.0                                        # how far it runs down the west side
CHIMS = [(28.0, 74.0), (108.0, 74.0)]


def _walls(f, b, reg):
    """Drafted ashlar below the joint, monk-bond brick above; nothing in the cornice bands."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    if b is TOWER:
        reg = reg - rect(-1, ZTA - b.z0 - LEDGE - 0.6, f.L + 1, ZTB0 - b.z0)
        reg = reg - rect(-1, ZTB - b.z0 - LEDGE - 0.6, f.L + 1, 999)
    lo = reg ^ rect(-1, -100, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, S1 + RJ - b.z0, f.L + 1, 999)
    out = []
    if not lo.is_empty():
        out.append(G.stone_drafted(lo, datum=0.0))
    if not hi.is_empty():
        out.append(G.brick_monk(hi, datum=S1 + RJ - b.z0 + 0.2))
    return union(out) if out else M()


def _openings():
    L = []

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    lo, up = G.window_bello_ground(), G.window_bello_upper()
    front, back = G.door_bello(), G.door_bello_back()
    add(MAIN, DOOR_X, 0.0, 1.2, front, "front-door", "door")
    for x in (12.0, 47.0):
        add(MAIN, x, 0.0, V1, lo, f"S{x:.0f}-1")
    for x in (12.0, DOOR_X, 47.0):
        add(MAIN, x, 0.0, V2, up, f"S{x:.0f}-2")
    for x in (96.0, 120.0):
        add(WING, x, WY0, V1, lo, f"WS{x:.0f}-1")
    add(WING, 108.0, WY0, V2 + 2.6, G.window_bello_serliana(), "WS-serliana")
    add(WING, X1, WY0 / 2, V1, lo, "WE-1")
    add(WING, X1, WY0 / 2, V2, up, "WE-2")
    add(TOWER, TC[0], TY0, V1, lo, "TS-1")
    add(TOWER, TC[0], TY0, V2, up, "TS-2")
    add(TOWER, TX0, TY0 / 2 - 0.5, V2, up, "TW-2")
    bif = G.window_bello_bifora(h=16.0)
    for k, (x, y) in enumerate(((TC[0], TY0), (TX1, TC[1]), (TC[0], TY1), (TX0, TC[1]))):
        add(TOWER, x, y, ZW - ZF + 2.6, bif, f"T{k}-bifora")
    for y in (14.0, 40.0, 76.0):
        add(MAIN, 0.0, y, V1, lo, f"W{y:.0f}-1")
        add(MAIN, 0.0, y, V2, up, f"W{y:.0f}-2")
    for y in (20.0, 50.0, 80.0):
        add(MAIN, X1, y, V1, lo, f"E{y:.0f}-1")
        add(MAIN, X1, y, V2, up, f"E{y:.0f}-2")
    for x in (20.0, 46.0, 86.0, 112.0):
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
    for x in (20.0, 46.0, 66.0, 86.0, 112.0):
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, 66.0, Y1, 1.2, back, "back-door", "door")
    return L


OPENINGS = _openings()


def _loggia_arches():
    """The campanile's open belvedere: two round arches through every face (a world solid to
    cut), and the archivolts, imposts and blind-baluster parapets dressing them."""
    cuts, dress = [], []
    v0 = ZTB0 - ZF
    for f in TOWER.facades():
        for du in (-5.6, 5.6):
            u = f.L / 2 + du
            hole = arch_cs(u - 3.5, u + 3.5, v0 + 3.0, v0 + 12.6, rise=3.5, seg=24)
            cuts.append(f.place(ext(hole, -4.0, 1.0)))
            ring = arch_cs(u - 4.3, u + 4.3, v0 + 12.6, v0 + 12.6, rise=4.3, seg=24) - arch_cs(u - 3.5, u + 3.5, v0 + 12.0, v0 + 12.6, rise=3.5, seg=24)
            dress.append(f.place(ext(ring ^ rect(-1e3, v0 + 12.59, 1e3, 1e3), -0.01, 0.6)))
            for x in (u - 3.5, u + 3.5):
                dress.append(f.place(G.chamfer_box(x - 0.9, v0 + 11.4, x + 0.9, v0 + 12.6, -0.01, 0.6, c=0.2, bottom=0.6)))
            bals = cs_union([cs_union([rect(x - 0.3, v0 + 0.6, x + 0.3, v0 + 2.6), G.oval((x, v0 + 1.4), 0.5, 0.6, 12)])
                             for x in np.linspace(u - 2.8, u + 2.8, 5)])
            dress.append(f.place(ext(rect(u - 3.5, v0 + 0.4, u + 3.5, v0 + 3.0), -0.01, 0.15) - ext(bals, -0.3, 0.2) +
                                 ext(rect(u - 3.9, v0 + 2.6, u + 3.9, v0 + 3.2), -0.01, 0.5)))
    return union(cuts), union(dress)


LOGGIA_CUT, LOGGIA_DRESS = _loggia_arches()


def _inset_chain(pts, d):
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
        s = ((b0[0] - a0[0]) * db[1] - (b0[1] - a0[1]) * db[0]) / den
        out.append(a0 + da * s)
    out.append(P[-1] + d * nrm[-1])
    return [tuple(p) for p in out]


def _parapet(kit, tag, chain, z, keep, group, h=7.0):
    """The stone balustrade along an open chain, as flat strips standing at z."""
    for i in range(len(chain) - 1):
        f = Facade(np.array(chain[i]), np.array(chain[i + 1]), 0.0)
        if f.L < 6.0:
            continue
        cs = G.fence_bello_parapet(f.L - 1.4, h).translate([0.7, 0.0])
        strip = M.extrude(cs, 1.0).translate([0, 0, -0.5])
        A = f.A.copy()
        A[:, 3] = f.world(0, 0, 0) + np.array([0, 0, z - 0.01])
        seg = strip.transform(A) - keep
        for j, piece in enumerate(seg.decompose()):
            if piece.volume() > 3.0:
                kit.add(f"{tag}-{i}{chr(97 + j)}", "Stone", piece, P=inv34(A), group=group)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    allcs = cs_union([b.cs for b in BLOCKS])
    eave_path = max(allcs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(allcs, 10.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 8.0), ZTA - LEDGE - 0.6, ZTB0 + 0.01),
               slab(offset(TOWER.cs, 8.0), ZTB - LEDGE - 0.6, ZTW + 0.01),
               slab(offset(TOWER.cs, 8.0), ZTB0 - 0.01, ZTB + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="bellosguardo", clear=[lip_keep(allcs, 3.0, ZF, 1.2)],
                        siding=_walls, prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=undress, extra_cut=LOGGIA_CUT)
    kit.add("WALLS-1", "Brownstone", st["shells"][0], group="walls")
    kit.add("JOINT", "Brick", st["rings"][0], group="walls")
    ledges = CO.ledge(eave_path, ZE, LEDGE) + CO.ledge(TOWER.pts, ZTA, LEDGE) + CO.ledge(TOWER.pts, ZTB, LEDGE)
    shelf = _corbel(TOWER.cs, 3.0, ZTB0 - 1.2)
    # inside the house the campanile's walls rise from the joint, so its stages over the roof
    # bear all round
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(allcs, 3.0, S1 + RJ)
    walls2 = st["shells"][1] + tring + ledges + shelf + (LOGGIA_DRESS - LOGGIA_CUT)
    kit.add("WALLS-2", "Brick", walls2, group="walls")
    kit.add("TOWER-floor", "Roof", slab(offset(TOWER.cs, -3.15), ZTB0 - 1.2, ZTB0), group="tower")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(TOWER.pts, ZTA, TOWER_J)
    CO.add_level(kit, rings, "CORNICE-TJ", "tower")
    rings, _ = CO.level(TOWER.pts, ZTB, TOWER_C)
    CO.add_level(kit, rings, "CORNICE-T", "tower")
    kit.add("FOUNDATION", "Brownstone", foundation(BLOCKS, 0.0, ZF, style="talusvent"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Stone", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the flat roof: a tin deck over the walls and the crown, a balustrade round it, stacks
    tower_hug = TOWER.solid(grow=0.3, dz0=-1, dz1=400)
    dcs = offset(allcs, DK - 1.4)
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + 2.6, x1, 5.2)]) ^ offset(dcs, -2.6)
    pads = union([box([x - 6.0, y - 5.0, ZW + 0.5], [x + 6.0, y + 5.0, ZW + 2]) for x, y in CHIMS])
    deck = slab(dcs, ZW, ZW + 1.0) + slab(seams, ZW + 0.99, ZW + 1.4)
    kit.add("ROOF-deck", "Roof", deck - tower_hug - pads - walls2, group="roof")
    for k, (x, y) in enumerate(CHIMS):
        kit.add(f"CHIMNEY-{k}", "Brick", G.chimney_bellosguardo(10.0, 8.0, 26.0).translate([x, y, ZW + 1.0]), key="CHIMNEY", group="roof")
    ring = max(offset(allcs, DK - 2.6).to_polygons(), key=lambda L_: abs(poly(L_).area()))
    P_ = [tuple(p) for p in ring]
    # the balustrade runs round the roof from the tower's east face to its west face
    pts = [np.asarray(p) for p in P_]
    k0 = int(np.argmin([abs(p[0] - TX1) + abs(p[1] - (TY0 + 2)) for p in pts]))
    _parapet(kit, "ROOF-rail", [P_[(k0 + i) % len(P_)] for i in range(len(P_) + 1)], ZW + 1.0,
             TOWER.solid(grow=0.5, dz0=-1, dz1=400), "roof")
    print("roof", round(time.time() - t0, 1))

    # --- the campanile's tile pyramid and pine cone
    zr1 = ZTW + 20.0
    cap, ctex, _ = R.mansard(TOWER.pts, [(DT, ZTW), (DT - 1.0, ZTW + 0.8), (-10.8, zr1)], t=2.4,
                             tex=dict(pitch=1.4, wtab=1.3, d=0.35, shape="square"))
    top = slab(offset(TOWER.cs, -10.8), zr1 - 0.6, zr1 + 0.8)
    kit.add("TOWER-roof", "Tile", cap + ctex + top - lip_keep(TOWER.cs, 3.0, ZTW), group="tower")
    kit.add("TOWER-finial", "Stone", G.finial_pigna(8.0).translate([TC[0], TC[1], zr1 + 0.79]), group="tower")
    FT.crown(kit, "TOWER-finial", "TOWER-roof")
    print("tower", round(time.time() - t0, 1))

    # --- the loggia: across the front from the campanile and down the west side, Corinthian
    # columns and archivolted arches, a paved floor, a balustraded terrace on its flat roof
    pts_l = [(0.0, LN), (-LD, LN), (-LD, -LD), (TX0, -LD), (TX0, -1.4), (-1.4, -1.4), (-1.4, LN)]
    Lw, Lf = LN + LD, TX0 + LD
    ud = DOOR_X + LD
    runs = [dict(a=(0.0, LN), b=(-LD, LN), posts=[1.7, LD - 1.6]),
            dict(a=(-LD, LN), b=(-LD, -LD), posts=[1.6, Lw * 0.25, Lw * 0.5, Lw * 0.75, Lw - 1.6]),
            dict(a=(-LD, -LD), b=(TX0, -LD), posts=[1.6, ud - 9.0, ud + 9.0, Lf - 1.6])]
    H_floor = ZF - 1.0
    post_h = S1 - 2.4 - H_floor - 5.0
    P = FT.porch_turned(pts_l, runs, H_floor, post_h, steps_at=[(2, ud, 14.0)], planks=dict(pitch=2.8, crack=0.3, border=2.0),
                        joined=True, post="corinthian", rail="squarebellied", arcade="archivoltarcade", skirt="medallion",
                        pier_tex="stone", roof_edge="eggedge", drop=8.0, top=True)
    # the roof's seat only meets the beams' tops on a plane: a hidden key over every post ties
    # them into one piece
    where = []
    for r in runs:
        f = Facade(r["a"], r["b"], 0.0)
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
    kit.add("LOGGIA-deck", "Brownstone", deck_, P=print_flip(), group="loggia",
            render=FT.plank_zones(deck_, H_floor, "Stone", "Brownstone"))
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=300) for b in BLOCKS])
    ptop = FT.add_porch_top(kit, "LOGGIA", P, bld_keep + ins_keep, "Stone", "Stone", tin_col="Roof", tin="flat",
                            group="loggia")["ptop"]
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"LOGGIA-steps-{k}", "Brownstone", sm.transform(A) - fkeep, group="loggia")
    chain = _inset_chain([(0.0, LN), (-LD, LN), (-LD, -LD), (TX0, -LD)], 2.4)
    parts = {p_.name: p_ for p_ in kit.parts}
    parts["LOGGIA-top"].solid = parts["LOGGIA-top"].solid - parts["FOUNDATION"].solid
    _parapet(kit, "LOGGIA-rail", chain, ptop, bld_keep + slab(offset(allcs, 4.8), S1 - 0.2, 999), "loggia", h=6.4)
    e, u = MAIN.locate(66.0, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Brownstone", FT.steps(14.0, ZF - 0.6, 3).transform(A), group="loggia")
    print("loggia", round(time.time() - t0, 1))

    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("ROOF-rail")]:
        FT.key_into(kit, p_.name, ["ROOF-deck"], (0, 0, -1), depth=0.6)
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("LOGGIA-rail")]:
        FT.key_into(kit, p_.name, ["LOGGIA-top"], (0, 0, -1), depth=0.6)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "bellosguardo")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:60]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "bellosguardo.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
