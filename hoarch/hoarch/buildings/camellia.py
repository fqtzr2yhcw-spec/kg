"""The Camellia -- an original HO-scale (1:87.1) Queen Anne, after the user's photo of a pink
house with a bell-roofed tower. Rev B: the house-size plan (200 x 132 mm, storeys of 42 and
38 mm), framed windows spaced along the walls, and built-up cornices at every level.

Pink banded lap siding below (bevel courses tied by a flat band every sixth course) and
key-cut shingles above, lozenge corner boards, a base of red-brown diamond-point rustication.
Between the storeys a three-part cornice: a raspberry frieze hung with swags between rosettes,
a white course of pellets and a white cyma crown. At the eave a four-part cornice: a raspberry
frieze with ovals between the brackets, a white dentil course, a white soffit on pierced ring
brackets, and a raspberry cavetto crown. A round tower stands on the west front corner, its
upper storeys in bands of key-cut and diamond shingles, a ring of framed lights at the top under
its own fluted frieze, bracketed soffit and crown, then a tall black bell roof (flaring at the
foot, swelling and drawing in to a point) with an iron spike finial. A two-storey pavilion
steps forward on the east with a steep front gable and a one-storey canted bay (studded frieze,
bracketed eave, hip roof); a steep east side gable; both gables carry deep white gingerbread
bargeboards cut into cusps with balls and pierced with keyholes, a collar tie with a lattice
panel and a teardrop pendant, all clear of the attic lights. Black wave-butt slates; a brick
chimney with a Greek cross in a sunk panel on each face and two pots. Between the tower and
the pavilion an entry porch on barley-twist columns with hourglass balusters, a lambrequin
frieze, a cable-moulded fascia, a honeycomb brick skirt on diamond-point piers and a pediment
over the steps. Windows under half-round hoods with keystones (8-over-1; plain lights in the
tower) in stepped casings; the ground-floor front window round-arched; doors with
trefoil-headed lights under a fret transom. In front, a brick forecourt in basket-weave with
two cast-iron street lamps.

usage: python3 -m hoarch.buildings.camellia [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import box, compose, cs_union, inv34, ngon, offset, poly, rect, scallop_rows, slab, union
from hoarch import cornice as CO, features as FT, gables as G, openings as O, roof as R, skins as SK, \
    storefront as SF, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Camellia"
COLORS = {"Pink": "#E59AB0", "White": "#F3EFE7", "Raspberry": "#A8436A", "Black": "#2A2A2E", "Brownstone": "#7B4A3C",
          "Brick": "#9A4535", "PorchDeck": "#7B4A3C", "Lamp": "#F2DE9A", "Windows_Doors": "#F3EFE7"}
RENDER_MAT = {"Pink": "siding", "White": "trim", "Raspberry": "accent", "Black": "roof", "Brownstone": "stone",
              "Brick": "brick", "PorchDeck": "stone", "Planks": "planks", "Lamp": "lampglass", "Windows_Doors": "trim",
              "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Camellia)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="swags", role="Raspberry"),
    dict(kind="course", h=1.4, b=1.4, orn="pellets", role="White"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="cyma", role="White")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=6.0, b=1.2, orn="ovals", role="Raspberry"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="White", tooth=0.9, gap=0.6),
    dict(kind="bed", h=2.0, b=1.4, P=6.2, role="White", brackets=dict(style="ring", t=0.9, reach=0.55)),
    dict(kind="crown", h=3.0, b=1.4, P=7.2, orn="cavetto", role="Raspberry")])
TOWER_C = dict(pitch=7.0, margin=2.2, layers=[
    dict(kind="frieze", h=4.0, b=1.2, orn="flutes", role="Raspberry"),
    dict(kind="bed", h=1.8, b=1.4, P=5.0, role="White", brackets=dict(style="ring", t=0.8, reach=0.7)),
    dict(kind="crown", h=2.2, b=1.4, P=5.8, orn="ovolo", role="White")])
BAY_C = dict(pitch=8.0, margin=2.4, layers=[
    dict(kind="frieze", h=3.4, b=1.2, orn="studs", role="Raspberry"),
    dict(kind="bed", h=1.6, b=1.4, P=4.4, role="White", brackets=dict(style="ring", t=0.8, reach=0.7)),
    dict(kind="crown", h=1.8, b=1.4, P=5.0, orn="bevel", role="White")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2      # the joint (belt ring) height
HE = CO.band_height(EAVE)                                          # the eave band over the ledge

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 14.0
S1 = ZF + 42.0                  # first-storey shell top = the joint ring's foot
ZE = S1 + RJ + 38.0             # the eave ledge's top: the wall face ends here
ZW = ZE + HE                    # the wall top (the band behind the eave cornice); the roof sits here
ZT = ZW + 46.0                  # the tower's ledge
ZTW = ZT + CO.band_height(TOWER_C)
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 7.4, 4.2, 1.8
S_MAIN, S_FRONT, S_SIDE = 0.9, 1.35, 1.25
V1 = 8.0
V2 = S1 + RJ + 5.0 - ZF

# ------------------------------------------------------------------ plan
W, D = 200.0, 132.0
PX0, PX1, PY = 116.0, 188.0, -24.0        # the pavilion stepping forward on the east
SG = (44.0, 100.0)                        # the east side gable's span on the east wall
TC, TR = (16.0, -4.0), 26.0               # the round tower (a 16-sided drum, TR its apothem)
BAY_LEDGE = ZF + 30.0
BAY_TOP = BAY_LEDGE + CO.band_height(BAY_C)
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
PAV = Block("pavilion", [(PX0, PY), (PX1, PY), (PX1, 3.0), (PX0, 3.0)], ZF, ZW)
BAY = Block("bay", [(124.0, PY), (136.0, PY - 12.0), (168.0, PY - 12.0), (180.0, PY), (180.0, PY + 3.0), (124.0, PY + 3.0)],
            ZF, BAY_TOP)
TOWER = Block("tower", ngon(TC, TR, n=16), ZF, ZTW)
BLOCKS = [MAIN, PAV, BAY, TOWER]
DOOR_X = 90.0
DOOR_W, DOOR_H = 13.0, 30.0
SASH = dict(lites=(1, 4), rows=(1, 2))    # 8-over-1


def _siding(f, b, reg):
    """Banded lap siding on the first storey; key-cut shingles above the joint, the tower's in
    bands of three courses of key-cut and two of diamond. Nothing in the cornice bands."""
    cut = S1 - b.z0
    top = (BAY_LEDGE if b is BAY else ZT if b is TOWER else ZE) - b.z0
    reg = reg - rect(-1, top, f.L + 1, (ZW if b in (MAIN, PAV) else 999) - b.z0)   # gables keep theirs
    out = []
    lo = reg ^ rect(-1, -100, f.L + 1, cut)
    hi = reg ^ rect(-1, cut, f.L + 1, 999)
    if not lo.is_empty():
        out.append(SK.banded_lap(lo, datum=0.0))
    if not hi.is_empty():
        shape = ["key", "key", "key", "diamond", "diamond"] if b is TOWER else "key"
        out.append(scallop_rows(hi, 1.6, 2.2, d=0.42, datum=S1 + RJ - b.z0, shape=shape, lap=2.0))
    return union(out) if out else M()


def win(w, h, rise=0, head="keyarch", **kw):
    s = dict(SASH)
    s.update(kw)
    return SF.window_commercial(w, h, rise=rise, sill=1.2, head=head, casing=1.3, band=True, **s)


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    add(MAIN, DOOR_X, 0.0, 0.0, SF.door_commercial(DOOR_W, DOOR_H, transom=5.4, leaf="trefoil", tstyle="fret",
                                                  head=None, leaves=2), "door", "door")
    add(MAIN, 64.0, 0.0, V1, win(8.4, 26.0, rise=4.2), "F64-1")       # the round-arched window on the porch
    for x in (64.0, 96.0):
        add(MAIN, x, 0.0, V2, win(8.4, 21.0), f"F{x:.0f}-2")
    # the pavilion: the canted bay below, a pair above, an attic light in the gable
    bq = BAY.pts
    for i, (wd, sp) in enumerate(((6.4, dict(lites=(1, 1), rows=(1, 1))), (10.4, {}), (6.4, dict(lites=(1, 1), rows=(1, 1))))):
        m = ((bq[i][0] + bq[i + 1][0]) / 2, (bq[i][1] + bq[i + 1][1]) / 2)
        add(BAY, m[0], m[1], 4.4, win(wd, 14.4, **sp), f"bay{i}")
    pm = (PX0 + PX1) / 2
    for x in (pm - 15.0, pm + 15.0):
        add(PAV, x, PY, V2, win(8.4, 21.0), f"P{x:.0f}-2")
    add(PAV, pm, PY, ZW - ZF + 3.0, win(8.0, 14.0, rise=4.0), "front-gable")
    sm = (SG[0] + SG[1]) / 2
    for y in (22.0, sm, 114.0):
        add(MAIN, W, y, V1, win(8.4, 24.0), f"E{y:.0f}-1")
    for y in (22.0, sm - 13.0, sm + 13.0, 114.0):
        add(MAIN, W, y, V2, win(8.4, 21.0), f"E{y:.0f}-2")
    add(MAIN, W, sm, ZW - ZF + 3.0, win(7.2, 12.0, rise=3.6), "side-gable")
    for y in (54.0, 86.0, 116.0):
        add(MAIN, 0.0, y, V1, win(8.4, 24.0), f"W{y:.0f}-1")
        add(MAIN, 0.0, y, V2, win(8.4, 21.0), f"W{y:.0f}-2")
    add(MAIN, 150.0, D, 0.0, SF.door_commercial(10.0, 28.0, transom=4.4, leaf="trefoil", tstyle="fret", head=None),
        "back-door", "door")
    for x in (30.0, 70.0, 110.0, 180.0):
        add(MAIN, x, D, V1, win(8.4, 24.0), f"B{x:.0f}-1")
    for x in (30.0, 70.0, 110.0, 150.0, 180.0):
        add(MAIN, x, D, V2, win(8.4, 21.0), f"B{x:.0f}-2")
    # the tower: framed single lights on every other facet facing out, a ring of five at the top
    tw1 = win(6.4, 21.0, lites=(1, 1), rows=(1, 1), head="keyarch")
    tw2 = win(6.4, 19.0, lites=(1, 1), rows=(1, 1), head="keyarch")
    tw3 = win(6.4, 17.0, lites=(1, 1), rows=(1, 1), head=None)
    for k, f in enumerate(TOWER.facades()):
        m = (f.p0 + f.p1) / 2
        probe = rect(m[0] + f.n[0] * 3 - 5.5, m[1] + f.n[1] * 3 - 5.5, m[0] + f.n[0] * 3 + 5.5, m[1] + f.n[1] * 3 + 5.5)
        if not (MAIN.cs ^ probe).is_empty() or k % 2:
            continue
        if f.n[0] < 0.3 and f.n[1] < 0.3:          # facing west or south, away from the roof
            add(TOWER, m[0], m[1], V1, tw1, f"tower{k}-1")
            add(TOWER, m[0], m[1], V2, tw2, f"tower{k}-2")
        add(TOWER, m[0], m[1], ZT - ZF - 23.0, tw3, f"tower{k}-3")
    return L


OPENINGS = _openings()


def street_lamp(h=38.0):
    """A cast-iron street lamp in three parts, all printed upright: the standard (a square
    plinth, a fluted pedestal, a slim tapering shaft with rings, a cup and the four corner
    posts of a lantern wider at the top), the glass (a tapered block notched for the posts,
    dropped into the cage from above) and the cap (a square rim socketed over the post tops
    under a pyramid roof and a ball). Local z up from the ground. Returns (standard, glass,
    cap)."""
    from hoarch.porchwork import _revolve
    zl0, zl1 = h - 8.0, h - 3.4                 # the lantern cage
    std = box([-2.8, -2.8, 0.0], [2.8, 2.8, 1.2])
    ped = _revolve([(0.0, 1.19), (2.2, 1.19), (2.2, 1.6), (1.8, 2.0), (1.7, 6.4), (1.2, 6.9), (1.2, 7.3), (1.4, 7.5),
                    (1.4, 7.9), (1.0, 8.4)], 32)
    flutes = union([box([-0.25, -2.0, 2.4], [0.25, -1.45, 6.0]).rotate([0, 0, 360.0 * k / 8]) for k in range(8)])
    shaft = _revolve([(0.0, 8.2), (1.0, 8.2), (0.8, zl0 - 3.0), (1.15, zl0 - 2.6), (1.15, zl0 - 2.2), (0.8, zl0 - 1.8),
                      (0.8, zl0 - 1.2), (1.6, zl0 - 0.4), (1.6, zl0)], 28)
    std = std + (ped - flutes) + shaft + box([-1.6, -1.6, zl0 - 0.01], [1.6, 1.6, zl0 + 0.6])
    b0, b1 = 1.5, 2.1                           # the cage's half width at its foot and head
    posts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            posts.append(M.hull_points([(sx * (b0 - q), sy * (b0 - q), zl0 + 0.5) for q in (0.0, 0.6)] +
                                       [(sx * (b0 - 0.6), sy * b0, zl0 + 0.5), (sx * b0, sy * (b0 - 0.6), zl0 + 0.5)] +
                                       [(sx * (b1 - q), sy * (b1 - q), zl1) for q in (0.0, 0.6)] +
                                       [(sx * (b1 - 0.6), sy * b1, zl1), (sx * b1, sy * (b1 - 0.6), zl1)]))
    std = std + union(posts)
    core = M.hull_points([(sx * (b0 - 0.15), sy * (b0 - 0.15), zl0 + 0.6) for sx in (-1, 1) for sy in (-1, 1)] +
                         [(sx * (b1 - 0.15), sy * (b1 - 0.15), zl1) for sx in (-1, 1) for sy in (-1, 1)])
    glass = core - union(posts) - union(
        [M.hull_points([(sx * (b0 - 0.75), sy * (b0 - 0.75), zl0) , (sx * 9, sy * 9, zl0), (sx * (b0 - 0.75), sy * 9, zl0),
                        (sx * 9, sy * (b0 - 0.75), zl0), (sx * (b1 - 0.75), sy * (b1 - 0.75), zl1 + 0.01),
                        (sx * 9, sy * 9, zl1 + 0.01), (sx * (b1 - 0.75), sy * 9, zl1 + 0.01), (sx * 9, sy * (b1 - 0.75), zl1 + 0.01)])
         for sx in (-1, 1) for sy in (-1, 1)])
    rim = box([-b1 - 0.3, -b1 - 0.3, zl1], [b1 + 0.3, b1 + 0.3, zl1 + 0.8])
    roof = M.hull_points([(sx * (b1 + 0.5), sy * (b1 + 0.5), zl1 + 0.8) for sx in (-1, 1) for sy in (-1, 1)] +
                         [(0.0, 0.0, zl1 + 3.2)])
    ball = M.sphere(0.55, 16).translate([0, 0, zl1 + 3.5]) + M.cylinder(0.6, 0.3, 0.3, 12).translate([0, 0, zl1 + 2.9])
    cap = rim + roof + ball
    cap = cap - union([box([sx * b1 - 0.7, sy * b1 - 0.7, zl1 - 0.01], [sx * b1 + 0.7, sy * b1 + 0.7, zl1 + 0.6])
                       for sx in (-1, 1) for sy in (-1, 1)])
    return std, glass, cap


def forecourt(w, d, t=1.2, sockets=()):
    """A brick forecourt laid in basket-weave: 4 mm squares of two bricks each, turned
    alternately, inside a border of bricks on edge. Local u across (centred), v out from the
    house (0 at the steps), prints face-up. ``sockets``: (u, v) of 5.8 mm square recesses for
    the lamp plinths."""
    slab_ = box([-w / 2, 0.0, 0.0], [w / 2, d, t])
    bricks = []
    for (u0, v0, u1, v1) in ((-w / 2, 0.0, w / 2, 1.4), (-w / 2, d - 1.4, w / 2, d), (-w / 2, 1.4, -w / 2 + 1.4, d - 1.4),
                             (w / 2 - 1.4, 1.4, w / 2, d - 1.4)):
        n = max(1, int(round(max(u1 - u0, v1 - v0) / 1.4)))
        for k in range(n):
            if u1 - u0 > v1 - v0:
                a = u0 + (u1 - u0) * k / n
                bricks.append(rect(a + 0.25, v0 + 0.25, a + (u1 - u0) / n - 0.25, v1 - 0.25))
            else:
                a = v0 + (v1 - v0) * k / n
                bricks.append(rect(u0 + 0.25, a + 0.25, u1 - 0.25, a + (v1 - v0) / n - 0.25))
    field = (w - 2.8, d - 2.8)
    nu, nv = int(field[0] / 4.0), int(field[1] / 4.0)
    cu, cv = -nu * 2.0, 1.4 + (field[1] - nv * 4.0) / 2
    for i in range(nu):
        for j in range(nv):
            x0, y0 = cu + 4.0 * i, cv + 4.0 * j
            if (i + j) % 2 == 0:
                bricks += [rect(x0 + 0.25, y0 + 0.25, x0 + 3.75, y0 + 1.75), rect(x0 + 0.25, y0 + 2.25, x0 + 3.75, y0 + 3.75)]
            else:
                bricks += [rect(x0 + 0.25, y0 + 0.25, x0 + 1.75, y0 + 3.75), rect(x0 + 2.25, y0 + 0.25, x0 + 3.75, y0 + 3.75)]
    top = M.extrude(cs_union(bricks), 0.4).translate([0, 0, t - 0.02])
    out = slab_ + top
    for (su, sv) in sockets:
        out = out - box([su - 2.9, sv - 2.9, t - 0.6], [su + 2.9, sv + 2.9, t + 1.0])
    return out


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    r = RAKE - D_EAVE
    zcf = Z_EAVE + S_FRONT * ((PX1 - PX0) / 2 + D_EAVE)
    gy = 88.0                                             # the pavilion roof's back end (a hip, buried)
    gx = (S_SIDE * ((SG[1] - SG[0]) / 2 + D_EAVE)) / S_MAIN + 6.0
    base = cs_union([MAIN.cs, PAV.cs])
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN),
              ([(PX0, PY - r), (PX1, PY - r), (PX1, gy), (PX0, gy)], [1, 2, 3], S_FRONT),
              ([(W - gx, SG[0]), (W + r, SG[0]), (W + r, SG[1]), (W - gx, SG[1])], [0, 2], S_SIDE)]
    specs = [dict(p0=(PX0, PY), p1=(PX1, PY), slope=S_FRONT, e=0.3),
             dict(p0=(W, SG[0]), p1=(W, SG[1]), slope=S_SIDE, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture="wave", tex_kw=dict(pitch=1.5, wtab=2.2, d=0.42),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    wf, ws = rf["walls"]
    gables = [(PAV, 0, wf["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 1, ws["cs"].translate((SG[0], Z_EAVE - ZF)))]
    # no siding or corner boards where the cornices wrap the walls
    base0 = cs_union([MAIN.cs, PAV.cs])
    undress = [slab(offset(base0, 8.0) - offset(TOWER.cs, 1.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01),
               slab(offset(BAY.cs, 8.0) ^ rect(0.0, -200.0, 400.0, PY - 0.6), BAY_LEDGE - LEDGE - 0.6, BAY_TOP + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="lozenge", siding=_siding, gables=gables,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    ledge_b = CO.ledge(BAY.pts, BAY_LEDGE, LEDGE) - PAV.solid(grow=0.2, dz0=-1, dz1=1)
    kit.add("WALLS-1", "Pink", st["shells"][0] + ledge_b, group="walls")
    kit.add("JOINT", "Pink", st["rings"][0], group="walls")
    tower_keep = TOWER.solid(grow=0.2, dz0=-1, dz1=1)
    # the ledges the cornices stand on: the eave's (main + pavilion), the bay's, the tower's
    eave_path = max(base.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    ledge_e = CO.ledge(eave_path, ZE, LEDGE) - tower_keep
    no_lip = union([box([PX0 - D_EAVE - 0.6, PY - 1, ZW - 1], [PX1 + D_EAVE + 0.6, PY + 5.0, ZW + 5]),
                    box([W - 5.0, SG[0] - D_EAVE - 0.6, ZW - 1], [W + 1, SG[1] + D_EAVE + 0.6, ZW + 5]),
                    tower_keep, slab(offset(TOWER.cs, 1.0), ZW - 1, ZW + 5)])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    allcs = cs_union([b.cs for b in BLOCKS])
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(allcs, 3.0, S1 + RJ)
    ledge_t = CO.ledge(TOWER.pts, ZT, LEDGE)
    kit.add("WALLS-2", "Pink", st["shells"][1] + lip + tring + ledge_e + ledge_t, group="walls")
    # the cornices: at the joint (round everything that rises through it), at the eave (cut back
    # to the tower), round the tower's top and the bay's
    jpath = st["outlines"][0]
    rings, _ = CO.level(jpath, S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, zt_ = CO.level(eave_path, ZE, EAVE, cut=TOWER.solid(grow=1.1, dz0=-2, dz1=2))
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(TOWER.pts, ZT, TOWER_C)
    CO.add_level(kit, rings, "CORNICE-T", "tower")
    rings, _ = CO.level(BAY.pts, BAY_LEDGE, BAY_C, cut=PAV.solid(grow=0.7, dz0=-2, dz1=2))
    CO.add_level(kit, rings, "CORNICE-B", "bay")
    fnd = foundation(BLOCKS, 0.0, ZF, style="diamond")
    kit.add("FOUNDATION", "Brownstone", fnd, group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the main roof: a hollow hip with the pavilion's front gable and the east side gable
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    caps = [G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZW)]
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
                       for wl in rf["walls"]])
    fx = (PX0 + PX1) / 2
    fy = gy + D_EAVE - (zcf - Z_EAVE) / S_FRONT
    caps.append(G.ridge_cap((fx, PY - RAKE), (fx, fy + 0.4), zcf, S_FRONT, ZW))
    for xc in (PX0 - D_EAVE, PX1 + D_EAVE):
        caps.append(G.hip_cap((xc, gy + D_EAVE, Z_EAVE), (fx, fy, zcf), half=1.6, up=0.9, drop=2.2))
    zc2 = Z_EAVE + S_SIDE * ((SG[1] - SG[0]) / 2 + D_EAVE)
    caps.append(G.ridge_cap((W + RAKE, (SG[0] + SG[1]) / 2), (W - ((zc2 - Z_EAVE) / S_MAIN - D_EAVE + 1.0), (SG[0] + SG[1]) / 2),
                            zc2, S_SIDE, ZW))
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.6, up=0.9, drop=2.2)
                  for c, e in zip(corners, ends)])
    roof = roof + ((union(caps) + hips) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 12.0, 10.4
    cx, cy = 92.0, 100.0
    zroof = Z_EAVE + S_MAIN * min(cx - CW / 2 + D_EAVE, D + D_EAVE - cy - CD / 2)
    z0 = round((zroof - 3.0) / 0.2) * 0.2
    roof = roof + G.chimney_seat(solid_env, cx, cy, CW / 2, zr + 1.0)
    pocket = box([cx - CW / 2 - 0.4, cy - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CD / 2 + 0.4, zr + 40])
    roof = roof - pocket - slab(offset(TOWER.cs, 1.4), ZW - 1, ZTW + 90)
    kit.add("ROOF", "Black", roof, group="roof")
    ch = TW.chimney("cross", w=CW, d=CD, h=round((zr + 22.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    for k, wl in enumerate(rf["walls"]):
        orn = G.gable_keyhole(wl["L"], wl["slope"], D_EAVE, skin=SKIN, collar=0.6)
        f = wl["facade"]
        A = f.A.copy()
        A[:, 3] = f.world(0.0, 0.0, RAKE)
        ow = orn.transform(A) - (roof + ch)                   # the side gable's feet stop on the main roof
        ow = max(ow.decompose(), key=lambda m_: m_.volume())
        kit.add(f"GABLE-{k}", "White", ow, P=inv34(A), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the bay: its cornice (above) and a low hip roof of the same slates under the joint
    bay_path = BAY.pts
    bay_keep = union([MAIN.solid(grow=0.45, dz0=-1, dz1=300), PAV.solid(grow=1.0, dz0=-1, dz1=300)])
    zb_top = S1 - 0.4
    broof, btex = R.hip_roof([(bay_path, [0, 1, 2])], BAY_TOP, 0.9, BAY_C["layers"][-1]["P"] + 0.2, texture="wave",
                             flat_top=zb_top, tex_kw=dict(pitch=1.5, wtab=2.0, d=0.4), zlo=BAY_TOP)
    kit.add("BAY-ROOF", "Black", (broof + btex) - bay_keep, group="bay")

    # --- the tower's bell roof on its cornice
    zc0 = ZTW
    # a bell: a flared lip, a steep waist, rounded shoulders, then drawn in to the point
    bands = [(1.6, 0.8), (3.0, 1.6), (6.4, 3.6), (13.0, 8.0), (9.0, 4.2), (6.4, 1.9), (4.4, 1.4), (5.2, 2.8),
             (9.0, 7.2)]
    bsol, btx, ap_top, zs = R.bell_roof(TC, TR + TOWER_C["layers"][-1]["P"] + 0.4, zc0, bands, texture="wave",
                                        tex_kw=dict(pitch=1.5, wtab=2.2, d=0.42))
    kit.add("TOWER-roof", "Black", bsol + btx, group="tower")
    kit.add("TOWER-finial", "Black", TW.finial("spike", 1.6, 18.0).translate([TC[0], TC[1], zs]), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- the entry porch between the tower and the pavilion, flush with the pavilion's front
    XW, XE, FY = 46.0, PX0, PY
    ppts = [(XW, 0.0), (XW, FY), (XE, FY), (XE, 0.0)]
    Lf = XE - XW
    ud = DOOR_X - XW
    runs = [dict(a=(XW, 0.0), b=(XW, FY), posts=[3.4, -FY - 1.6]),
            dict(a=(XW, FY), b=(XE, FY), posts=[1.6, ud - 14.0, ud + 14.0, Lf - 2.6])]
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    PP = FT.porch_turned(ppts, runs, H_floor, post_h, steps_at=[(1, ud, 20.0)],
                         planks=dict(pitch=1.6, border=1.6), joined=True, ledger_off=1.5, post="barley",
                         rail="hourglass", arcade="lambrequin", skirt="honeycomb", pier_tex="diamond", roof_edge="cable")
    fkeep = slab(offset(allcs, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    deck = PP["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    tabs = union([arc_ for arc_, _ in PP["arcades"]])
    for k, fr in enumerate(sorted(PP["frames"], key=lambda m_: -m_.volume())):
        kit.add(f"PORCH-frame-{k}", "White", fr - tabs - fnd, group="porch")
    for k, (arc_, A) in enumerate(PP["arcades"]):
        kit.add(f"PORCH-frieze-{k}", "White", arc_, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = union([b.solid(grow=1.8, dz0=-20, dz1=0) for b in (MAIN, PAV, TOWER)])
    proof = PP["roof"] - bld_keep - ins_keep
    ptop = proof.bounding_box()[5]
    kit.add("PORCH-roof", "White", proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8)), P=print_flip(), group="porch")
    kit.add("PORCH-roof-top", "Black", proof.trim_by_plane([0, 0, 1.0], ptop - 0.8), group="porch")
    steps_front = FY
    for k, (sm, A) in enumerate(PP["steps"]):
        s_ = sm.transform(A) - fkeep - deck
        kit.add(f"PORCH-steps-{k}", "Brownstone", s_, group="porch")
        steps_front = min(steps_front, s_.bounding_box()[1])
    # the pediment over the steps: a raking cornice round a tympanum with a raised oval and dentils
    gw_, gr_ = 11.6, 8.0
    tri = poly([(-gw_, 0.0), (gw_, 0.0), (0.0, gr_)])
    rim = tri - tri.offset(-1.0, JoinType.Miter, 4.0)
    ped = ext(tri, 0.0, 2.4) + ext(rim, 2.39, 3.2)
    ped = ped + ext(poly([(2.0 * math.cos(t_), 2.8 + 1.3 * math.sin(t_)) for t_ in np.linspace(0, 2 * math.pi, 32, endpoint=False)]),
                    2.39, 3.0)
    ped = ped + ext(cs_union([rect(u - 0.3, 1.0, u + 0.3, 1.6) for u in np.arange(-gw_ + 2.2, gw_ - 2.0, 1.2)]), 2.39, 2.8)
    Ag = np.array([[1.0, 0, 0, DOOR_X], [0, 0, -1.0, FY - 1.4 + 0.4 + 3.2], [0, 1.0, 0, ptop]])
    kit.add("PORCH-pediment", "White", ped.transform(Ag), P=inv34(Ag), group="porch")
    e, u = MAIN.locate(150.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Brownstone", FT.steps(15.0, ZF - 0.6, 5).transform(A) - fnd, group="porch")

    # --- the forecourt and its two street lamps
    FW, FD = 56.0, 30.0
    lamps_at = [(-FW / 2 + 4.4, FD - 4.4), (FW / 2 - 4.4, FD - 4.4)]
    fc = forecourt(FW, FD, sockets=lamps_at)
    fcw = fc.mirror([0, 1, 0]).translate([DOOR_X, steps_front - 0.2, 0.0])
    kit.add("FORECOURT", "Brick", fcw, group="extras")
    std, glass, cap = street_lamp(44.0)
    for k, (su, sv) in enumerate(lamps_at):
        p = [DOOR_X + su, steps_front - 0.2 - sv, 0.6]
        kit.add(f"LAMP-{k}", "Black", std.translate(p), group="extras")
        kit.add(f"LAMP-glass-{k}", "Lamp", glass.translate(p), group="extras")
        kit.add(f"LAMP-cap-{k}", "Black", cap.translate(p), group="extras")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "camellia")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "camellia.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
