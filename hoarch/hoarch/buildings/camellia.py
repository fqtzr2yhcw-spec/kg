"""The Camellia -- an original HO-scale (1:87.1) Queen Anne, after the user's photo of a pink
house with a bell-roofed tower.

Pink banded lap siding below (bevel courses tied by a flat band every sixth course) and
key-cut shingles above a white belt hung with swags between rosettes, lozenge corner boards,
a base of red-brown diamond-point rustication. A round tower stands on the west front corner,
its upper storeys in bands of key-cut and diamond shingles, ringed with tall lights at the top
under a bracketed eave, then a tall black bell roof (flaring at the foot, swelling and drawing
in to a point) with an iron spike finial. A two-storey pavilion steps forward on the east
with a steep front gable and a one-storey canted bay under a little hip roof; a steep east
side gable; both gables carry deep white gingerbread bargeboards cut into cusps with balls
and pierced with keyholes, a collar tie with a lattice panel and a teardrop pendant. Black
wave-butt slates; a brick chimney with a Greek cross in a sunk panel on each face and two
pots. Between the tower and the pavilion an entry porch on barley-twist columns with
hourglass balusters, a lambrequin frieze, a cable-moulded fascia, a honeycomb brick skirt on
diamond-point piers and a pediment over the steps. Windows under half-round hoods with
keystones (8-over-1; plain lights in the tower); the ground-floor front windows round-arched;
doors with trefoil-headed lights under a fret transom. In front, a brick forecourt in
basket-weave with two cast-iron street lamps.

usage: python3 -m hoarch.buildings.camellia [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import box, circle, compose, cs_union, inv34, ngon, offset, poly, rect, scallop_rows, slab, union
from hoarch import features as FT, gables as G, openings as O, roof as R, skins as SK, storefront as SF, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Camellia"
COLORS = {"Pink": "#E59AB0", "White": "#F3EFE7", "Black": "#2A2A2E", "Brownstone": "#7B4A3C", "Brick": "#9A4535",
          "PorchDeck": "#7B4A3C", "Lamp": "#F2DE9A", "Windows_Doors": "#F3EFE7"}
RENDER_MAT = {"Pink": "siding", "White": "trim", "Black": "roof", "Brownstone": "stone", "Brick": "brick",
              "PorchDeck": "stone", "Planks": "planks", "Lamp": "lampglass", "Windows_Doors": "trim", "Sash": "sash",
              "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 12.0
S1 = ZF + 36.0
RH = 4.4
ZE = S1 + RH + 34.0
ZT = ZE + 22.0                  # the tower's eave
FASCIA = 1.8
Z_EAVE = ZE + FASCIA
D_EAVE, RAKE, SKIN = 3.0, 3.2, 1.8
S_MAIN, S_FRONT, S_SIDE = 1.2, 1.7, 1.5
V1 = 7.0
V2 = S1 + RH + 4.0 - ZF

# ------------------------------------------------------------------ plan
W, D = 100.0, 72.0
PX0, PX1, PY = 56.0, 92.0, -12.0          # the pavilion stepping forward on the east
SG = (24.0, 52.0)                         # the east side gable's span on the east wall
TC, TR = (8.0, -2.0), 14.0                # the round tower (a 16-sided drum, TR its apothem)
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZE)
PAV = Block("pavilion", [(PX0, PY), (PX1, PY), (PX1, 3.0), (PX0, 3.0)], ZF, ZE)
BAY = Block("bay", [(60.0, PY), (66.0, PY - 6.0), (82.0, PY - 6.0), (88.0, PY), (88.0, PY + 3.0), (60.0, PY + 3.0)],
            ZF, ZF + 27.2)
TOWER = Block("tower", ngon(TC, TR, n=16), ZF, ZT)
BLOCKS = [MAIN, PAV, BAY, TOWER]
DOOR_X = 44.0
DOOR_W, DOOR_H = 10.0, 26.0
SASH = dict(lites=(1, 4), rows=(1, 2))    # 8-over-1


def _siding(f, b, reg):
    """Banded lap siding on the first storey; key-cut shingles above the belt, the tower's in
    bands of three courses of key-cut and two of diamond."""
    cut = S1 - b.z0
    out = []
    lo = reg ^ rect(-1, -100, f.L + 1, cut)
    hi = reg ^ rect(-1, cut, f.L + 1, 999)
    if not lo.is_empty():
        out.append(SK.banded_lap(lo, datum=0.0))
    if not hi.is_empty():
        shape = ["key", "key", "key", "diamond", "diamond"] if b is TOWER else "key"
        out.append(scallop_rows(hi, 1.6, 2.2, d=0.42, datum=S1 + RH - b.z0, shape=shape, lap=2.0))
    return union(out) if out else M()


def _openings():
    L = []

    def win(w, h, rise=0, head="keyarch", **kw):
        s = dict(SASH)
        s.update(kw)
        return SF.window_commercial(w, h, rise=rise, sill=1.0, head=head, **s)

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    add(MAIN, DOOR_X, 0.0, 0.0, SF.door_commercial(DOOR_W, DOOR_H, transom=4.6, leaf="trefoil", tstyle="fret",
                                                  head=None, leaves=2), "door", "door")
    add(MAIN, 30.0, 0.0, V1, win(7.2, 22.0, rise=3.6), "F30-1")       # the round-arched window on the porch
    for x in (30.0, DOOR_X):
        add(MAIN, x, 0.0, V2, win(7.2, 17.0), f"F{x:.0f}-2")
    # the pavilion: the canted bay below, a pair above, an attic light in the gable
    bq = BAY.pts
    for i, (wd, sp) in enumerate(((5.2, dict(lites=(1, 1), rows=(1, 1))), (8.4, {}), (5.2, dict(lites=(1, 1), rows=(1, 1))))):
        m = ((bq[i][0] + bq[i + 1][0]) / 2, (bq[i][1] + bq[i + 1][1]) / 2)
        add(BAY, m[0], m[1], 4.0, win(wd, 15.0, **sp), f"bay{i}")
    pm = (PX0 + PX1) / 2
    for x in (pm - 8.0, pm + 8.0):
        add(PAV, x, PY, V2, win(7.2, 17.0), f"P{x:.0f}-2")
    add(PAV, pm, PY, ZE - ZF + 5.0, win(7.2, 13.0, rise=3.6), "front-gable")
    sm = (SG[0] + SG[1]) / 2
    for y in (10.0, sm - 7.0, sm + 7.0, 62.0):
        add(MAIN, W, y, V1, win(7.2, 20.0), f"E{y:.0f}-1")
        add(MAIN, W, y, V2, win(7.2, 17.0), f"E{y:.0f}-2")
    add(MAIN, W, sm, ZE - ZF + 4.0, win(6.4, 11.0, rise=3.2), "side-gable")
    for y in (26.0, 46.0, 62.0):
        add(MAIN, 0.0, y, V1, win(7.2, 20.0), f"W{y:.0f}-1")
        add(MAIN, 0.0, y, V2, win(7.2, 17.0), f"W{y:.0f}-2")
    add(MAIN, 76.0, D, 0.0, SF.door_commercial(8.0, 24.0, transom=3.6, leaf="trefoil", tstyle="fret", head=None),
        "back-door", "door")
    for x in (14.0, 34.0, 54.0):
        add(MAIN, x, D, V1, win(7.2, 20.0), f"B{x:.0f}-1")
    for x in (14.0, 34.0, 54.0, 76.0):
        add(MAIN, x, D, V2, win(7.2, 17.0), f"B{x:.0f}-2")
    # the tower: plain tall lights (too narrow for muntins), a ring of them in the top storey
    tw = SF.window_commercial(3.8, 17.0, rise=0, lites=(1, 1), rows=(1, 1), sill=0.8, head=None)
    tw3 = SF.window_commercial(3.6, 14.0, rise=0, lites=(1, 1), rows=(1, 1), sill=0, head=None)
    for k, f in enumerate(TOWER.facades()):
        m = (f.p0 + f.p1) / 2
        probe = rect(m[0] + f.n[0] * 3 - 4.5, m[1] + f.n[1] * 3 - 4.5, m[0] + f.n[0] * 3 + 4.5, m[1] + f.n[1] * 3 + 4.5)
        if not (MAIN.cs ^ probe).is_empty():
            continue
        if k % 2 == 0 and m[0] < 21.0:
            add(TOWER, m[0], m[1], V1, tw, f"tower{k}-1")
            add(TOWER, m[0], m[1], V2, tw, f"tower{k}-2")
        add(TOWER, m[0], m[1], ZE - ZF + 4.0, tw3, f"tower{k}-3")
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
    gy = 44.0                                             # the pavilion roof's back end (a hip, buried)
    gx = (S_SIDE * ((SG[1] - SG[0]) / 2 + D_EAVE)) / S_MAIN + 4.0
    base = cs_union([MAIN.cs, PAV.cs])
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN),
              ([(PX0, PY - r), (PX1, PY - r), (PX1, gy), (PX0, gy)], [1, 2, 3], S_FRONT),
              ([(W - gx, SG[0]), (W + r, SG[0]), (W + r, SG[1]), (W - gx, SG[1])], [0, 2], S_SIDE)]
    specs = [dict(p0=(PX0, PY), p1=(PX1, PY), slope=S_FRONT, e=0.3),
             dict(p0=(W, SG[0]), p1=(W, SG[1]), slope=S_SIDE, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture="wave", tex_kw=dict(pitch=1.5, wtab=2.2, d=0.42),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.6)
    wf, ws = rf["walls"]
    gables = [(PAV, 0, wf["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 1, ws["cs"].translate((SG[0], Z_EAVE - ZF)))]
    bprof, bsw = TW.BELTS["swag"]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="lozenge", siding=_siding, gables=gables, prof=bprof,
                        belt_blocks=bsw, water_table=False)
    kit.add("WALLS-1", "Pink", st["shells"][0], group="walls")
    kit.add("BELT", "White", st["rings"][0], group="walls")
    no_lip = union([box([PX0 - D_EAVE - 0.6, PY - 1, ZE - 1], [PX1 + D_EAVE + 0.6, PY + 5.0, ZE + 5]),
                    box([W - 5.0, SG[0] - D_EAVE - 0.6, ZE - 1], [W + 1, SG[1] + D_EAVE + 0.6, ZE + 5]),
                    TOWER.solid(grow=0.2, dz0=-1, dz1=1), slab(offset(TOWER.cs, 1.0), ZE - 1, ZE + 5)])
    lip = (_corbel(base, 3.0, ZE) + lip_ring(base, 3.0, ZE)) - no_lip
    allcs = cs_union([b.cs for b in BLOCKS])
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RH, ZE + 1.2)
    tring = tring - lip_keep(allcs, 3.0, S1 + RH)
    kit.add("WALLS-2", "Pink", st["shells"][1] + lip + tring, group="walls")
    fnd = foundation(BLOCKS, 0.0, ZF, style="diamond")
    kit.add("FOUNDATION", "Brownstone", fnd, group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}", group="inserts", render=zones))
    print("walls + inserts", round(time.time() - t0, 1))

    # --- the main roof: a hollow hip with the pavilion's front gable and the east side gable
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    caps = [G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZE)]
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
                       for wl in rf["walls"]])
    fx = (PX0 + PX1) / 2
    fy = gy + D_EAVE - (zcf - Z_EAVE) / S_FRONT
    caps.append(G.ridge_cap((fx, PY - RAKE), (fx, fy + 0.4), zcf, S_FRONT, ZE))
    for xc in (PX0 - D_EAVE, PX1 + D_EAVE):
        caps.append(G.hip_cap((xc, gy + D_EAVE, Z_EAVE), (fx, fy, zcf), half=1.3, up=0.7, drop=1.8))
    zc2 = Z_EAVE + S_SIDE * ((SG[1] - SG[0]) / 2 + D_EAVE)
    caps.append(G.ridge_cap((W + RAKE, (SG[0] + SG[1]) / 2), (W - ((zc2 - Z_EAVE) / S_MAIN - D_EAVE + 1.0), (SG[0] + SG[1]) / 2),
                            zc2, S_SIDE, ZE))
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.3, up=0.7, drop=1.8)
                  for c, e in zip(corners, ends)])
    roof = roof + ((union(caps) + hips) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZE)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZE)
    CW, CD = 8.4, 7.2
    cx, cy = 46.0, 52.0
    zroof = Z_EAVE + S_MAIN * min(cx - CW / 2 + D_EAVE, D + D_EAVE - cy - CD / 2)
    z0 = round((zroof - 3.0) / 0.2) * 0.2
    roof = roof + G.chimney_seat(solid_env, cx, cy, CW / 2, zr + 1.0)
    pocket = box([cx - CW / 2 - 0.4, cy - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CD / 2 + 0.4, zr + 40])
    roof = roof - pocket - slab(offset(TOWER.cs, 1.4), ZE - 1, ZT + 60)
    kit.add("ROOF", "Black", roof, group="roof")
    ch = TW.chimney("cross", w=CW, d=CD, h=round((zr + 11.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    for k, wl in enumerate(rf["walls"]):
        orn = G.gable_keyhole(wl["L"], wl["slope"], D_EAVE, skin=SKIN)
        f = wl["facade"]
        A = f.A.copy()
        A[:, 3] = f.world(0.0, 0.0, RAKE)
        kit.add(f"GABLE-{k}", "White", orn.transform(A), P=inv34(A), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the bay: a bracketed eave and a little hip roof of the same slates under the belt
    bay_path = BAY.pts
    bay_keep = union([MAIN.solid(grow=0.45, dz0=-1, dz1=300), PAV.solid(grow=1.0, dz0=-1, dz1=300)])
    bay_cornice = [(-4.4, 0), (0.8, 0), (0.8, 2.2), (1.2, 2.4), (1.3, 2.8), (2.4, 2.8), (2.4, 3.4), (2.8, 3.8),
                   (2.8, 4.4), (-4.4, 4.4)]
    beave = R.bracketed_cornice(bay_path, BAY.z1, bay_cornice,
                                brackets=dict(z_top=2.8, h=2.6, d0=0.8, d=1.6, t=0.7, pitch=4.4, margin=1.2, style="ring"),
                                lip_t=3.0, deck=None)
    kit.add("BAY-EAVE", "White", beave - bay_keep, P=print_flip(), group="bay")
    eh = beave.bounding_box()[5] - BAY.z1
    zb_top = S1 - 0.4
    broof, btex = R.hip_roof([(bay_path, [0, 1, 2])], BAY.z1 + eh, 0.9, 1.8, texture="wave",
                             flat_top=zb_top, tex_kw=dict(pitch=1.5, wtab=2.0, d=0.4), zlo=BAY.z1 + eh)
    kit.add("BAY-ROOF", "Black", (broof + btex) - bay_keep, group="bay")

    # --- the tower's bracketed eave and its bell roof
    teave = R.bracketed_cornice(TOWER.pts, ZT, R.CORNICE_SMALL,
                                brackets=dict(z_top=4.6, h=4.6, d0=0.8, d=2.6, t=0.8, pitch=5.6, margin=1.2, style="ring"),
                                lip_t=3.0, deck=(6.0, 8.0))
    kit.add("TOWER-eave", "White", teave, P=print_flip(), group="tower")
    zc0 = ZT + 8.0
    # a bell: a flared lip, a steep waist, rounded shoulders, then drawn in to the point
    bands = [(1.0, 0.45), (1.6, 0.9), (3.0, 2.0), (6.0, 4.5), (4.0, 2.4), (3.0, 1.1), (2.0, 0.8), (2.4, 1.6),
             (3.6, 4.0)]
    bsol, btx, ap_top, zs = R.bell_roof(TC, TR + 3.4, zc0, bands, texture="wave", tex_kw=dict(pitch=1.4, wtab=2.0, d=0.42))
    kit.add("TOWER-roof", "Black", bsol + btx, group="tower")
    kit.add("TOWER-finial", "Black", TW.finial("spike", 1.3, 12.0).translate([TC[0], TC[1], zs]), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- the entry porch between the tower and the pavilion, flush with the pavilion's front
    XW, XE, FY = 23.0, PX0, PY
    ppts = [(XW, 0.0), (XW, FY), (XE, FY), (XE, 0.0)]
    Lf = XE - XW
    ud = DOOR_X - XW
    runs = [dict(a=(XW, 0.0), b=(XW, FY), posts=[3.4, -FY - 1.6]),
            dict(a=(XW, FY), b=(XE, FY), posts=[1.6, ud - 8.6, Lf - 2.6])]
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    PP = FT.porch_turned(ppts, runs, H_floor, post_h, steps_at=[(1, ud, 16.0)],
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
    gw_, gr_ = 9.4, 6.6
    tri = poly([(-gw_, 0.0), (gw_, 0.0), (0.0, gr_)])
    rim = tri - tri.offset(-1.0, JoinType.Miter, 4.0)
    ped = ext(tri, 0.0, 2.4) + ext(rim, 2.39, 3.2)
    ped = ped + ext(poly([(1.6 * math.cos(t_), 2.3 + 1.1 * math.sin(t_)) for t_ in np.linspace(0, 2 * math.pi, 32, endpoint=False)]),
                    2.39, 3.0)
    ped = ped + ext(cs_union([rect(u - 0.3, 1.0, u + 0.3, 1.6) for u in np.arange(-gw_ + 2.2, gw_ - 2.0, 1.2)]), 2.39, 2.8)
    Ag = np.array([[1.0, 0, 0, DOOR_X], [0, 0, -1.0, FY - 1.4 + 0.4 + 3.2], [0, 1.0, 0, ptop]])
    kit.add("PORCH-pediment", "White", ped.transform(Ag), P=inv34(Ag), group="porch")
    e, u = MAIN.locate(76.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Brownstone", FT.steps(12.0, ZF - 0.6, 4).transform(A) - fnd, group="porch")

    # --- the forecourt and its two street lamps
    FW, FD = 44.0, 24.0
    lamps_at = [(-FW / 2 + 3.6, FD - 3.6), (FW / 2 - 3.6, FD - 3.6)]
    fc = forecourt(FW, FD, sockets=lamps_at)
    fcw = fc.mirror([0, 1, 0]).translate([DOOR_X, steps_front - 0.2, 0.0])
    kit.add("FORECOURT", "Brick", fcw, group="extras")
    std, glass, cap = street_lamp()
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
