"""The Piney: an original HO-scale (1:87.1) dogtrot house; house 106, of the new-layouts batch
(hoarch.novel2), after Woodland, Sam Houston's house at Huntsville, Texas (1847), and the
dogtrot farmhouses of the Gulf states.

You can see straight through it: two pens of hewn logs under one long side-gabled roof of
riven shakes, the open breezeway (the dogtrot) between them floored and ceiled, open front
and back, a door from each pen into it (a bench along one wall, the water shelf on the
other). A full-width porch on cedar posts under a shallow tin roof, a door from each pen onto
it beside a shuttered window; fat fieldstone chimneys outside both gable ends with the loft's
little lights beside them; a back porch behind the east pen; the whole house up on dry-laid
fieldstone piers over a swept clay yard. Behind, the kitchen in its own log cabin with a
Dutch door and a stick-and-clay chimney, reached from the breezeway by a covered walk; a cord
of stovewood by it.

- Walls: hewn logs with chinking, the two walls of each corner half a log apart, the
  crossing logs' dovetailed ends showing at the corners. One part for both pens and the
  breezeway floor (the sills and floor in the plank colour, one change).
- Eave cornice: the loft joists' squared ends under a plate board, a beaded board, an ovolo.
  The kitchen's: a board sawn into points under a bevel.
- Windows: six over six in wide beaded casings with a frieze, a drip and a low peaked head,
  sills on sawn brackets; the loft's casement pairs. Doors: Greek Revival four-panel doors in
  eared architraves onto the porch; board doors on strap hinges with transoms and rosette
  corner blocks into the breezeway; the kitchen's Dutch door with its shelf.
- Porches: cedar posts with growth rings and bolsters, knee braces, a pole railing, rafters
  under a tin roof. Each porch top (roof, rafters, beam, braces, posts, railing) is one piece
  printed upside down tilted onto its tin face, the tin in its one colour change.

usage: python3 -m hoarch.buildings.piney [check] [export]
"""
import json
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import box, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, gables as G, novel2 as N, openings as O
from hoarch.colonial import shutters_pair
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, lip_keep, lip_ring, wall_shell

NAME = "The Piney"
COLORS = {"Logs": "#8A7560", "Whitewash": "#EEE9DC", "Cedar": "#9A5B3A", "Haint": "#8FC3C9", "Shakes": "#6F6A62",
          "Tin": "#A7ABAE", "Stone": "#8E8578", "Clay": "#A4583A", "Planks": "#B28B5E", "Windows_Doors": "#EEE9DC"}
RENDER_MAT = {"Logs": "logs", "Whitewash": "trim", "Cedar": "cedar", "Haint": "haint", "Shakes": "roof", "Tin": "tin",
              "Stone": "stone", "Clay": "clay", "Planks": "planks", "Windows_Doors": "trim", "Sash": "sash", "Door": "door",
              "Glass": "glass"}
PALETTE = {"logs": ["#8A7560", 0.85, 0.0], "trim": ["#EEE9DC", 0.6, 0.0], "cedar": ["#9A5B3A", 0.7, 0.0],
           "haint": ["#8FC3C9", 0.55, 0.0], "roof": ["#6F6A62", 0.85, 0.0], "tin": ["#A7ABAE", 0.45, 0.35],
           "stone": ["#8E8578", 0.9, 0.0], "clay": ["#A4583A", 0.95, 0.0], "planks": ["#B28B5E", 0.75, 0.0],
           "sash": ["#EEE9DC", 0.5, 0.0], "door": ["#8FC3C9", 0.5, 0.0]}
VIEWS = {"hero": [-30, 16, 70, 0.9, [0, 0, -10]], "hero_right": [32, 16, 70, 0.9, [0, 0, -10]],
         "front": [0, 6, 85, 0.92, [0, 0, 0]], "rear": [160, 20, 70, 0.92, [0, 0, -10]],
         "trot": [-4, 4, 85, None, [112, 70, 22], 150], "kitchen": [150, 14, 85, None, [95, 175, 25], 150]}

LEDGE = 1.4
EAVE = dict(pitch=10.0, margin=3.0, layers=[
    dict(kind="frieze", h=3.4, b=1.2, orn="pnjoists", role="Whitewash"),
    dict(kind="course", h=1.2, b=1.2, orn="pnbead", role="Cedar"),
    dict(kind="crown", h=1.8, b=1.2, P=3.2, orn="ovolo", role="Whitewash")])
KEAVE = dict(pitch=10.0, margin=3.0, layers=[
    dict(kind="course", h=1.6, b=1.2, orn="pnnotch", role="Cedar"),
    dict(kind="crown", h=1.6, b=1.2, P=2.6, orn="bevel", role="Whitewash")])
HE = CO.band_height(EAVE)
HEK = CO.band_height(KEAVE)

# ------------------------------------------------------------------ the house
T = 3.0                                          # the log walls
ZG = 1.6                                         # the yard's top (it prints flat, 1.6 thick)
ZF = ZG + 9.0                                    # the floors' top
ZS = ZF - 1.2                                    # the sills' foot (on the piers)
ZE = ZG + 44.4                                   # the eave cornice's foot
ZW = round((ZE + HE) / 0.2) * 0.2                # the walls' top
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
SL, D_EAVE, RAKE = 0.8, 3.6, 2.6
X0, XA, XB, X1 = 26.0, 92.0, 132.0, 198.0        # the west pen, the breezeway, the east pen
Y0, Y1 = 66.0, 130.0
YC = (Y0 + Y1) / 2
PENW = Block("pen-W", [(X0, Y0), (XA, Y0), (XA, Y1), (X0, Y1)], ZS, ZW)
PENE = Block("pen-E", [(XB, Y0), (X1, Y0), (X1, Y1), (XB, Y1)], ZS, ZW)
RPTS = [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)]
# the porches: the front one full width, the back one behind the east pen
YP = 40.0
SP = 0.25                                        # their tin roofs' slope
ZP = ZE - 1.6                                    # where the porch roofs meet the walls, under the cornice
# the kitchen and the covered walk to it
KX0, KX1, KY0, KY1 = 56.0, 100.0, 164.0, 204.0
ZEK = ZF + 28.0
ZWK = round((ZEK + HEK) / 0.2) * 0.2
ZK_EAVE = ZWK + 1.2
SLK, DK_EAVE = 0.85, 2.6
KITB = Block("kitchen", [(KX0, KY0), (KX1, KY0), (KX1, KY1), (KX0, KY1)], ZS, ZWK)
WX0, WX1, WY1 = 104.0, 118.0, KY0 + 30.0         # the walk: x from, x to, its far end
ZWP = ZF + 21.6                                  # the walk's plates
V1 = ZF + 7.0 - ZS                               # the windows' sills over the blocks' foot
VD = ZF - ZS                                     # the doors' sills (the floor)
# the chimneys' frames (local y out from the gable wall) and the kitchen's
CH_W = np.array([[0.0, -1.0, 0.0, X0], [1.0, 0.0, 0.0, YC], [0.0, 0.0, 1.0, ZG]])
CH_E = np.array([[0.0, 1.0, 0.0, X1], [-1.0, 0.0, 0.0, YC], [0.0, 0.0, 1.0, ZG]])
CH_K = np.array([[1.0, 0.0, 0.0, (KX0 + KX1) / 2], [0.0, 1.0, 0.0, KY1], [0.0, 0.0, 1.0, ZG]])


def _openings():
    LP, LK = [], []
    fams = {}
    shut = set()

    def add(L, blk, x, y, v0, sp, name, kind="window", sh=False):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        L[-1].fam = fams.setdefault(id(sp), name)
        if sh:
            shut.add(name)

    win, loft = N.window_pnsash(), N.window_pnloft()
    front, trot = N.door_pnfront(), N.door_pnbatten()
    # the front: a shuttered window and a door onto the porch in each pen
    add(LP, PENW, X0 + 20.0, Y0, V1, win, "S46", sh=True)
    add(LP, PENW, XA - 18.0, Y0, VD, front, "door-W", "door")
    add(LP, PENE, XB + 18.0, Y0, VD, front, "door-E", "door")
    add(LP, PENE, X1 - 20.0, Y0, V1, win, "S178", sh=True)
    # the back: a window in the west pen, a door and a window onto the back porch in the east
    add(LP, PENW, (X0 + XA) / 2, Y1, V1, win, "N59", sh=True)
    add(LP, PENE, XB + 18.0, Y1, VD, trot, "back-door", "door")
    add(LP, PENE, X1 - 20.0, Y1, V1, win, "N178", sh=True)
    # the breezeway: a door from each pen
    add(LP, PENW, XA, YC, VD, trot, "trot-W", "door")
    add(LP, PENE, XB, YC, VD, trot, "trot-E", "door")
    # the gable ends: a window each side of the chimney, the loft's lights over them
    for blk, x, tag in ((PENW, X0, "W"), (PENE, X1, "E")):
        for y in (Y0 + 11.0, Y1 - 11.0):
            add(LP, blk, x, y, V1, win, f"{tag}{y:.0f}")
        for y in (YC - 14.0, YC + 14.0):
            add(LP, blk, x, y, ZW + 2.6 - ZS, loft, f"loft-{tag}{y:.0f}")
    # the kitchen: its Dutch door onto the walk, a window each side
    add(LK, KITB, KX1, KY0 + 18.0, VD, N.door_pndutch(), "kitchen-door", "door")
    kwin = N.window_pnsash(w=10.0, h=13.0)
    add(LK, KITB, KX0, KY0 + 20.0, V1, kwin, "K-W")
    add(LK, KITB, (KX0 + KX1) / 2, KY0, V1, kwin, "K-S")
    return LP, LK, shut


OPEN_P, OPEN_K, SHUTTERED = _openings()
OPENINGS = OPEN_P + OPEN_K
BLOCKS = [PENW, PENE, KITB]


def _skinfn(f, b, reg):
    """Hewn logs, kept clear of the eave cornice's band."""
    ze, zw = (ZEK, ZWK) if b is KITB else (ZE, ZW)
    reg = reg - rect(-1, ze - LEDGE - 0.6 - b.z0, f.L + 1, zw - b.z0 + 0.2)
    if reg.is_empty():
        return M()
    shift = 0.0 if abs(f.u[0]) > 0.5 else 0.5
    return N.log_piney(reg, datum=0.0, L=f.L, shift=shift)


def _place_inserts(kit, ops, keep, group="inserts"):
    for o in ops:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        part = kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{o.fam}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                       group=group, render=zones)
        keep.append(part.solid)
        if o.name in SHUTTERED:
            w_op, h_op = b[2] - b[0], b[3] - b[1]
            left, right = shutters_pair(w_op, h_op, casing=1.4, gap=0.5, make=N.shutter_piney)
            for side, m in (("L", left), ("R", right)):
                kit.add(f"SHUTTER-{o.name}-{side}", "Haint", m.translate([0, 0, 0.55]).transform(A), P=inv34(A),
                        key="SHUTTER-piney", group="shutters")


def _env(c, step=2.0):
    """A chimney's room: the hulls of its slices, each a little grown (the roof, the cornice
    and the logs keep clear of it)."""
    b = c.bounding_box()
    out = []
    for z in np.arange(b[2], b[5], step):
        sl = c ^ box([b[0] - 1, b[1] - 1, z - 0.01], [b[3] + 1, b[4] + 1, z + step + 0.01])
        if not sl.is_empty():
            h = M.hull(sl)
            hb = h.bounding_box()
            cx, cy = (hb[0] + hb[3]) / 2, (hb[1] + hb[4]) / 2
            sx = (hb[3] - hb[0] + 0.4) / max(1e-6, hb[3] - hb[0])
            sy = (hb[4] - hb[1] + 0.4) / max(1e-6, hb[4] - hb[1])
            out.append(h.translate([-cx, -cy, 0]).scale([sx, sy, 1.0]).translate([cx, cy, 0]))
    return union(out)


def _gable_cs(wl, fascia):
    """A gable wall's outline, run 0.4 down into the wall under it (so the two are one solid)."""
    return wl["cs"] + rect(0.0, -fascia - 0.4, wl["L"], -fascia + 0.01)


def _zones(solid, z, below, above):
    """Render zones of a part with one colour change at height z (split a hair above it, so
    no face lying in that plane leaves a film in the upper zone)."""
    lo = box([-1e4, -1e4, -10.0], [1e4, 1e4, z + 0.05])
    return [(below, solid ^ lo), (above, solid - lo)]


def _m44(A):
    return np.vstack([A, [0, 0, 0, 1.0]])


def _sheared(x0, x1, y0, y1, ztop, below, above):
    """A slab under (and over) a plane sloping along y: z from ztop(y) - below to ztop(y) + above."""
    return M.hull_points([(x, y, ztop(y) + dz) for x in (x0, x1) for y in (y0, y1) for dz in (-below, above)])


def _shed_porch(kit, name, A, L, D, posts, steps, z_hi, s=SP, OS=1.6, OV=2.4, PT=1.4):
    """A porch against a wall, built in its own frame (x 0..L along the wall, the wall at y = 0,
    the porch out to y = -D, z as the world) and placed by A. Returns the deck's keep-out.

    The top is one piece: a tin roof sloping ``s`` from z_hi at the wall, rafters under it, a
    ledger on the wall, the beam over the posts with knee braces, cedar posts with pegs, the
    pole railing between them (not across ``steps`` = [(u0, u1)]). It prints upside down,
    tilted so its tin face lies on the bed: the tin is its first 0.6 mm, then one change.
    The deck: planks across, a rim board, a socket under every post; it prints upside down."""
    zt = lambda y: z_hi + s * y
    y_out = -(D + OV)
    parts = [_sheared(-OS, L + OS, y_out, 0.0, zt, PT, 0.0)]
    seams = [_sheared(x - 0.2, x + 0.2, y_out - 1.0, 1.0, zt, 0.3, 1.0) for x in np.arange(-OS + 1.3, L + OS - 0.6, 2.4)]
    parts.append(box([0.0, -1.2, z_hi - PT - 2.2], [L, 0.0, z_hi - PT + 0.3]))            # the ledger
    for x in np.arange(1.2, L - 0.6, 4.4):                                                # the rafters
        parts.append(_sheared(x - 0.45, x + 0.45, y_out + 0.3, -1.2, zt, PT + 1.0, -PT + 0.2))
    zb = round((zt(-D) - PT - 2.4) / 0.2) * 0.2                                          # the beam's foot
    parts.append(box([-0.4, -D, zb], [L + 0.4, -D + 2.6, zt(-D + 2.6) - PT + 0.2]))
    yp = -D + 1.3
    ph = zb - ZF + 0.4
    for u in posts:
        parts.append(N.post_piney(ph).translate([u, yp, ZF]))
        parts.append(box([u - 0.8, yp - 0.8, ZF - 1.2], [u + 0.8, yp + 0.8, ZF + 0.3]))       # the peg
        for sg in (-1, 1):                                                               # knee braces
            if not (0.5 < u + sg * 4.6 < L - 0.5):
                continue
            a = (u + sg * 1.2, zb - 4.0)
            b_ = (u + sg * 4.6, zb + 0.2)
            parts.append(M.hull_points([(x, y, z) for (x, z) in (a, b_) for y in (yp - 0.45, yp + 0.45)] +
                                       [(x + sg * 0.6, y, z) for (x, z) in (a,) for y in (yp - 0.45, yp + 0.45)] +
                                       [(x - sg * 0.9, y, z) for (x, z) in (b_,) for y in (yp - 0.45, yp + 0.45)]))
    for ua, ub in zip(posts[:-1], posts[1:]):                                            # the railing
        if any(u0 <= (ua + ub) / 2 <= u1 for u0, u1 in steps):
            continue
        a, b_ = ua + 1.3, ub - 1.3
        parts.append(box([a, yp - 0.5, ZF + 7.0], [b_, yp + 0.5, ZF + 8.0]))
        parts.append(box([a, yp - 0.45, ZF + 1.4], [b_, yp + 0.45, ZF + 2.2]))
        n = max(1, int((b_ - a) / 2.0))
        for k in range(n):
            x = a + (b_ - a) * (k + 0.5) / n
            parts.append(M.cylinder(5.0, 0.45, 0.45, 12).translate([x, yp, ZF + 2.1]))
    top = union(parts) - union(seams)
    tin = _sheared(-OS - 1, L + OS + 1, y_out - 1, 1.0, zt, 0.6, 2.0)
    ph_ = math.pi - math.atan(s)
    R = np.array([[1.0, 0, 0, 0], [0, math.cos(ph_), -math.sin(ph_), 0], [0, math.sin(ph_), math.cos(ph_), 0]])
    P = (_m44(R) @ np.linalg.inv(_m44(A)))[:3]
    topw = top.transform(A)
    tinw = tin.transform(A)
    kit.add(f"{name}-top", "Tin", topw, P=P, group="porch", change=(0.6, "Cedar"),
            render=[("Tin", topw ^ tinw), ("Cedar", topw - tinw)])
    # the deck
    deck = box([0.0, -D, ZF - 1.4], [L, -0.8, ZF])
    deck = deck + box([0.0, -D, ZF - 2.6], [L, -D + 1.0, ZF - 1.3]) + box([0.0, -D, ZF - 2.6], [1.0, -0.8, ZF - 1.3]) \
        + box([L - 1.0, -D, ZF - 2.6], [L, -0.8, ZF - 1.3])
    for u in posts:                                     # a joist under every post, back to the house
        deck = deck + box([min(max(u, 0.6), L - 0.6) - 0.6, -D, ZF - 2.6], [min(max(u, 0.6), L - 0.6) + 0.6, -3.6, ZF - 1.3])
    gaps = [box([x - 0.15, -D - 1, ZF - 0.3], [x + 0.15, 0.0, ZF + 1]) for x in np.arange(1.6, L - 0.4, 1.6)]
    socks = [box([u - 0.95, yp - 0.95, ZF - 1.6], [u + 0.95, yp + 0.95, ZF + 1]) for u in posts]
    deck = deck - union(gaps) - union(socks)
    kit.add(f"{name}-deck", "Planks", deck.transform(A), P=(_m44(print_flip()) @ np.linalg.inv(_m44(A)))[:3], group="porch")
    return [(u, yp) for u in posts], topw


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()

    # --- the chimneys first (everything else keeps clear of them)
    chw, che = N.chimney_piney(seed=3), N.chimney_piney(seed=8)
    chk, zck = N.chimney_pnstick(top=round((ZK_EAVE + SLK * 24.6 + 6.0 - ZG) / 0.2) * 0.2)
    ch_env = union([_env(c.transform(A)) for c, A in ((chw, CH_W), (che, CH_E))])
    chk_env = _env(chk.transform(CH_K))

    # --- the pens: one shell with the breezeway's floor; the gables over the end walls
    rf = G.gabled_roof([(RPTS, [0, 2], SL)], Z_EAVE, D_EAVE,
                       [dict(p0=(X1, Y0), p1=(X1, Y1), slope=SL), dict(p0=(X0, Y1), p1=(X0, Y0), slope=SL)],
                       texture="cypress", tex_kw=dict(pitch=2.4, d=0.35), skin=1.6, rake=RAKE,
                       inner_cs=offset(poly(RPTS), -3.0), fascia=FASCIA, hollow=2.4)
    gables = [(PENE, 1, _gable_cs(rf["walls"][0], FASCIA).translate((0.0, Z_EAVE - ZS))),
              (PENW, 3, _gable_cs(rf["walls"][1], FASCIA).translate((0.0, Z_EAVE - ZS)))]
    band = slab(offset(poly(RPTS), 8.0), ZE - LEDGE - 0.6, ZW + 0.01)
    ledger_f = box([X0 - 1, Y0 - 1.6, ZP - 4.0], [X1 + 1, Y0 + 0.1, ZP + 0.2])
    ledger_b = box([XB - 1, Y1 - 0.1, ZP - 4.0], [X1 + 1, Y1 + 1.6, ZP + 0.2])
    undress = [band, ledger_f, ledger_b, ch_env]
    sh = wall_shell([PENW, PENE], OPEN_P, t=T, belt=None, corners="none", water_table=False, siding=_skinfn, gables=gables,
                    undress=undress)
    lip = union([_corbel(b.cs, T, ZW) + lip_ring(b.cs, T, ZW) for b in (PENW, PENE)])
    led = CO.ledge(RPTS, ZE, LEDGE, t=T) - ch_env
    trot = box([XA - 0.01, Y0 - 5, -1], [XB + 0.01, Y1 + 5, 200])
    floor = box([XA - 1.0, Y0, ZS], [XB + 1.0, Y1, ZF])
    floor = floor - union([box([x - 0.15, Y0 - 1, ZF - 0.3], [x + 0.15, Y1 + 1, ZF + 1]) for x in np.arange(XA + 1.6, XB - 0.4, 1.6)])
    # the loft over the breezeway: its floor (the trot's ceiling) and the plates front and back,
    # the floor's ends in notches in the pens' inner walls
    loft = box([XA - 1.5, Y0, ZW - 1.6], [XB + 1.5, Y1, ZW]) + box([XA, Y0, ZE - LEDGE - 0.4], [XB, Y0 + 2.8, ZW]) \
        + box([XA, Y1 - 2.8, ZE - LEDGE - 0.4], [XB, Y1, ZW]) + (led ^ trot)
    notch = box([XA - 1.65, Y0 - 1, ZW - 1.75], [XB + 1.65, Y1 + 1, ZW + 1])
    walls = (sh + lip + (led - trot)) - notch + floor
    # the breezeway's furniture: a bench along the west pen, the water shelf on the east
    bench = box([XA + 1.0, Y0 + 7.0, ZF + 3.4], [XA + 4.2, Y0 + 23.0, ZF + 4.2])
    for y in (Y0 + 7.6, Y0 + 15.0, Y0 + 22.4):
        bench = bench + box([XA + 1.4, y - 0.5, ZF - 0.01], [XA + 3.8, y + 0.5, ZF + 3.41])
    shelf = box([XB - 3.8, Y1 - 24.0, ZF + 8.6], [XB - 0.4, Y1 - 8.0, ZF + 9.4])
    for y in (Y1 - 22.5, Y1 - 9.5):
        shelf = shelf + M.hull_points([(XB - 0.4, y + dy, ZF + 5.4) for dy in (-0.45, 0.45)] +
                                      [(x, y + dy, ZF + 8.61) for x in (XB - 0.4, XB - 3.4) for dy in (-0.45, 0.45)])
    bucket = M.cylinder(2.4, 1.3, 1.45, 24).translate([XB - 2.1, Y1 - 19.0, ZF + 9.39]) - \
        M.cylinder(2.0, 1.0, 1.15, 24).translate([XB - 2.1, Y1 - 19.0, ZF + 10.2])
    basin = M.cylinder(0.9, 1.0, 1.7, 24).translate([XB - 2.1, Y1 - 13.0, ZF + 9.39]) - \
        M.cylinder(0.6, 0.7, 1.4, 24).translate([XB - 2.1, Y1 - 13.0, ZF + 9.7])
    walls = walls + bench + shelf + bucket + basin - loft
    kit.add("WALLS", "Planks", walls, group="walls", change=(1.2, "Logs"), render=_zones(walls, ZF, "Planks", "Logs"))
    kit.add("LOFT", "Logs", loft, P=print_flip(), group="walls")
    rings, _ = CO.level(RPTS, ZE, EAVE, t=T, cut=ch_env)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    keep = []
    _place_inserts(kit, OPEN_P, keep)
    print("pens", round(time.time() - t0, 1))

    # --- the roof: riven shakes, a comb of shakes along the ridge, cut round the chimneys
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + SL * ((Y1 - Y0) / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    rng = np.random.default_rng(5)
    comb, x = [], X0 - RAKE + 0.3
    while x < X1 + RAKE - 0.6:
        wd = rng.uniform(1.4, 2.6)
        hh = rng.uniform(1.0, 1.6)
        comb.append(M.hull_points([(xx, YC + dy, zr - 1.6) for xx in (x + 0.1, min(x + wd, X1 + RAKE - 0.3) - 0.1) for dy in (-0.5, 0.5)] +
                                  [(xx, YC + dy, zr + hh) for xx in (x + 0.3, min(x + wd, X1 + RAKE - 0.3) - 0.3) for dy in (-0.4, 0.4)]))
        x += wd
    roof = roof + (union(comb) - walls_env)
    for b in (PENW, PENE):
        roof = roof - lip_keep(b.cs, T, ZW)
    roof = roof - ch_env
    kit.add("ROOF", "Shakes", max(roof.decompose(), key=lambda m_: m_.volume()), group="roof")
    for nm, c, A in (("CHIMNEY-W", chw, CH_W), ("CHIMNEY-E", che, CH_E)):
        kit.add(nm, "Stone", c.transform(A), P=inv34(A), key="CHIMNEY-piney", group="chimney")
    print("roof", round(time.time() - t0, 1))

    # --- the porches
    house_keep = union(keep)
    fposts = [1.6, 23.0, 44.5, XA - X0, XB - X0, 127.5, 149.0, X1 - X0 - 1.6]
    sock_f, ftop = _shed_porch(kit, "PORCH", np.array([[1.0, 0, 0, X0], [0, 1.0, 0, Y0], [0, 0, 1.0, 0]]), X1 - X0, Y0 - YP, fposts,
                               [(XA - X0, XB - X0)], ZP)
    bposts = [1.6, 22.5, 43.5, X1 - XB - 1.6]
    sock_b, btop = _shed_porch(kit, "BACK-PORCH", np.array([[-1.0, 0, 0, X1], [0, -1.0, 0, Y1], [0, 0, 1.0, 0]]), X1 - XB, 18.0, bposts,
                               [(22.5, 43.5)], ZP)
    print("porches", round(time.time() - t0, 1))

    # --- the kitchen
    rk = G.gabled_roof([(KITB.pts, [1, 3], SLK)], ZK_EAVE, DK_EAVE,
                       [dict(p0=(KX0, KY0), p1=(KX1, KY0), slope=SLK), dict(p0=(KX1, KY1), p1=(KX0, KY1), slope=SLK)],
                       texture="cypress", tex_kw=dict(pitch=2.4, d=0.35), skin=1.6, rake=2.2,
                       inner_cs=offset(KITB.cs, -3.0), fascia=1.2, hollow=2.2)
    kg = [(KITB, 0, _gable_cs(rk["walls"][0], 1.2).translate((0.0, ZK_EAVE - ZS))), (KITB, 2, _gable_cs(rk["walls"][1], 1.2).translate((0.0, ZK_EAVE - ZS)))]
    kband = slab(offset(KITB.cs, 8.0), ZEK - LEDGE - 0.6, ZWK + 0.01)
    ksh = wall_shell([KITB], OPEN_K, t=T, belt=None, corners="none", water_table=False, siding=_skinfn, gables=kg,
                     undress=[kband, chk_env])
    kwalls = ksh + _corbel(KITB.cs, T, ZWK) + lip_ring(KITB.cs, T, ZWK) + (CO.ledge(KITB.pts, ZEK, LEDGE, t=T) - chk_env)
    kfloor = box([KX0 + 0.5, KY0 + 0.5, ZS], [KX1 - 0.5, KY1 - 0.5, ZS + 1.2])            # a floor: it prints on it
    kw = kwalls + kfloor
    kit.add("KITCHEN-WALLS", "Planks", kw, group="walls", change=(1.2, "Logs"), render=_zones(kw, ZF, "Planks", "Logs"))
    krings, _ = CO.level(KITB.pts, ZEK, KEAVE, t=T, cut=chk_env)
    CO.add_level(kit, krings, "CORNICE-K", "cornice")
    _place_inserts(kit, OPEN_K, keep, group="inserts")
    kroof = rk["body"] + rk["tex"] + rk["skins"] + rk["skin_tex"]
    kzr = ZK_EAVE + SLK * ((KX1 - KX0) / 2 + DK_EAVE)
    kwenv = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), 2.2 + 4.2).translate([0, 0, -3.15])) for wl in rk["walls"]])
    kroof = kroof + (G.ridge_cap(((KX0 + KX1) / 2, KY0 - 2.2), ((KX0 + KX1) / 2, KY1 + 2.2), kzr, SLK, ZWK, half=1.0, up=0.5) - kwenv)
    kroof = kroof - lip_keep(KITB.cs, T, ZWK) - chk_env
    kit.add("KITCHEN-ROOF", "Shakes", max(kroof.decompose(), key=lambda m_: m_.volume()), group="roof")
    kc = chk.transform(CH_K)
    kit.add("KITCHEN-CHIMNEY", "Stone", kc, P=inv34(CH_K), group="chimney", change=(zck, "Clay"), render=_zones(kc, ZG + zck, "Stone", "Clay"))
    print("kitchen", round(time.time() - t0, 1))

    # --- the covered walk: a planked deck from the breezeway to the kitchen door, a frame of
    # round posts, plates, ties and braces (printed upright on its pegs), a little gabled roof
    # with board ends (printed upright like the others)
    wdeck = box([WX0, Y1 + 0.2, ZS], [WX1, WY1, ZF]) + box([KX1 + 0.7, KY0 + 10.0, ZS], [WX0 + 0.01, KY0 + 26.0, ZF])
    wdeck = wdeck - union([box([WX0 - 5, y - 0.15, ZF - 0.3], [WX1 + 1, y + 0.15, ZF + 1]) for y in np.arange(Y1 + 1.8, WY1 - 0.4, 1.6)])
    wys = [Y1 + 6.0, Y1 + 20.0, Y1 + 34.0, Y1 + 48.0, WY1 - 2.0]
    wxs = [WX0 + 1.2, WX1 - 1.2]
    wdeck = wdeck - union([box([x - 0.75, y - 0.75, ZF - 1.0], [x + 0.75, y + 0.75, ZF + 1]) for x in wxs for y in wys])
    kit.add("WALK-deck", "Planks", wdeck, group="porch")
    fr = []
    for x in wxs:
        for y in wys:
            fr.append(M.cylinder(ZWP - 1.4 - ZF + 0.2, 1.0, 0.9, 16).translate([x, y, ZF]))
            fr.append(box([x - 0.6, y - 0.6, ZF - 0.8], [x + 0.6, y + 0.6, ZF + 0.3]))
            for sg in (-1, 1):
                if Y1 + 1.0 < y + sg * 4.0 < WY1 - 0.5:
                    fr.append(M.hull_points([(x + dx, y + sg * 0.9, ZWP - 5.0) for dx in (-0.4, 0.4)] + [(x + dx, y + sg * 0.5, ZWP - 4.2) for dx in (-0.4, 0.4)] +
                                            [(x + dx, y + sg * 4.0, ZWP - 1.39) for dx in (-0.4, 0.4)] + [(x + dx, y + sg * 3.0, ZWP - 1.39) for dx in (-0.4, 0.4)]))
        fr.append(box([x - 0.8, Y1 + 0.4, ZWP - 1.4], [x + 0.8, WY1, ZWP]))
    for y in wys:
        fr.append(box([WX0 + 0.4, y - 0.7, ZWP - 1.4], [WX1 - 0.4, y + 0.7, ZWP]))
    kit.add("WALK-frame", "Cedar", union(fr), group="porch")
    wpts = [(WX0, Y1 + 0.4), (WX1, Y1 + 0.4), (WX1, WY1), (WX0, WY1)]
    rw = G.gabled_roof([(wpts, [1, 3], 0.6)], ZWP + 1.0, 1.4, [dict(p0=(WX0, Y1 + 0.4), p1=(WX1, Y1 + 0.4), slope=0.6),
                                                           dict(p0=(WX1, WY1), p1=(WX0, WY1), slope=0.6)],
                       texture="cypress", tex_kw=dict(pitch=2.2, d=0.3), skin=1.2, rake=1.6, inner_cs=offset(poly(wpts), -1.6),
                       fascia=1.0, hollow=1.6)
    wroof = rw["body"] + rw["tex"] + rw["skins"] + rw["skin_tex"]
    for wl in rw["walls"]:                                       # board-and-batten gable ends
        wroof = wroof + wl["facade"].place(M.extrude(wl["cs"] ^ rect(-5, 0.0, 100, 100), 1.0).translate([0, 0, -1.0]))
    kit.add("WALK-ROOF", "Shakes", max(wroof.decompose(), key=lambda m_: m_.volume()), group="roof")
    print("walk", round(time.time() - t0, 1))

    # --- the yard: swept clay, the fieldstone piers on it, the stone steps (one part, the
    # stone above its one colour change), the stovewood
    yard_cs = rect(9.0, 26.0, 215.0, 224.0).offset(-6.0, JoinType.Round).offset(6.0, JoinType.Round)
    base = M.extrude(yard_cs, ZG)
    covered = [rect(X0 - 12, YP - 9, X1 + 12, Y1 + 20), rect(KX0 - 4, KY0 - 4, KX1 + 20, KY1 + 14), rect(WX0 - 3, Y1, WX1 + 3, WY1 + 2)]
    from hoarch.core import cs_union
    free = yard_cs.offset(-2.0) - cs_union(covered)
    base = base - N.yard_piney(free, seed=9).translate([0, 0, ZG])
    piers = []
    pid = 0

    def pier(x, y, top):
        nonlocal pid
        pid += 1
        piers.append(N.pier_piney(4.4, top - ZG, seed=pid).translate([x, y, ZG - 0.01]))
    for blk in (PENW, PENE):
        xa, ya = blk.pts[0]
        xb, yb = blk.pts[2]
        for x in np.linspace(xa + 2.0, xb - 2.0, 4):
            for y in (ya + 2.2, yb - 2.2):                 # (clear of the porch decks)
                pier(x, y, ZS)
        pier(XA - 1.5 if blk is PENW else XB + 1.5, YC, ZS)          # (the chimney carries the gable end)
    for x in (XA + 12.0, XB - 12.0):
        for y in (Y0 + 12.0, Y1 - 12.0):
            pier(x, y, ZS)
    for (u, yp) in sock_f:
        ux = min(max(u, 0.6), X1 - X0 - 0.6)
        pier(X0 + ux, Y0 + yp, ZF - 2.6)
        pier(X0 + ux, (YP + Y0) / 2, ZF - 2.6)
    for (u, yp) in sock_b:
        ux = min(max(u, 0.6), X1 - XB - 0.6)
        pier(X1 - ux, Y1 - yp, ZF - 2.6)
        pier(X1 - ux, Y1 + 8.0, ZF - 2.6)
    for x in wxs:
        for y in wys[1:]:
            pier(x, y + 3.0, ZS)
    for x in (KX0 + 2.0, (KX0 + KX1) / 2, KX1 - 2.0):
        pier(x, KY0 + 1.5, ZS)
    for x in (KX0 + 2.0, KX1 - 2.0):                       # (the chimney stands in the middle at the back)
        pier(x, KY1 - 2.5, ZS)
    steps = []
    for k, (xa, xb, y0, dy) in enumerate(((XA + 6.0, XB - 6.0, YP, -1.0), (X1 - 43.5 + 2.6, X1 - 22.5 - 2.6, Y1 + 18.0, 1.0))):
        xa, xb = sorted((xa, xb))
        for j in range(3):
            z = round((ZF - 2.25 * (j + 1)) / 0.2) * 0.2
            ya, yb = sorted((y0 + dy * 2.8 * j, y0 + dy * 2.8 * (j + 1)))
            steps.append(M.hull_points([(x, y, ZG - 0.01) for x in (xa, xb) for y in (ya, yb)] +
                                       [(x, y, z) for x in (xa + 0.3, xb - 0.3) for y in (ya + 0.3, yb - 0.3)] +
                                       [(x, y, z - 0.4) for x in (xa, xb) for y in (ya, yb)]))
    stones = []
    rng = np.random.default_rng(21)
    for (x, y) in ((112.0, 29.5), (166.0, 154.0), (172.0, 160.0), (40.0, 160.0)):
        r = rng.uniform(1.8, 2.4)
        stones.append(M.extrude(poly([(x + r * rng.uniform(0.8, 1.1) * math.cos(a), y + r * rng.uniform(0.8, 1.1) * math.sin(a))
                                      for a in np.linspace(0, 2 * math.pi, 9, endpoint=False)]), 0.4).translate([0, 0, ZG - 0.01]))
    ground = base + union(piers) + union(steps) + union(stones)
    kit.add("YARD", "Clay", ground, group="foundation", change=(ZG, "Stone"), render=_zones(ground, ZG, "Clay", "Stone"))
    kit.add("WOODPILE", "Logs", N.woodpile_piney().translate([36.0, 176.0, ZG]), group="stoop")
    print("yard", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "piney")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    json.dump({"materials": PALETTE, "views": VIEWS}, open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "piney.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
