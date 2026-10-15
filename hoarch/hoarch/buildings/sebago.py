"""The Sebago: an original HO-scale (1:87.1) New England connected farm; house 111, of the
new-layouts batch (hoarch.novel2), after the "big house, little house, back house, barn"
farmsteads of Maine and New Hampshire (1840s-80s).

Four buildings joined end to end, each lower and set further back than the last: the big
house, two storeys of Greek Revival with its pedimented gable to the road and a side-hall
entrance; the kitchen ell (the little house), a storey and a half with lights in its knee
walls and a porch on Doric columns onto the dooryard; the back house, a woodshed open in two
arched bays (cordwood stacked inside) with a workshop door; and the English barn, its long
side to the road, the great sliding doors in a gabled centre bay with the hay door over
them, a ventilator cupola on the ridge.

- Walls: narrow feather-edged clapboards; panelled corner pilasters with plinths and
  capitals on the big house, plain corner boards on the ell; the pediment's tympanum in
  flush boards; the barn in boards and battens. All on split granite with drill marks.
- Cornices: the big house's eave a full entablature (a two-fascia architrave, a frieze of
  laurel wreaths, Doric mutules with their drops, a cyma), carried across the gable as the
  pediment's floor, raking cornices up both gables; a bead-and-reel belt between its
  storeys; the ell's, the back house's and the barn's each their own (a sawn eave board on
  the barn).
- Windows and doors: six over six in eared architraves with cornice caps below, under
  pedimented lintels above, louvred shutters; the entrance with sidelights and a transom
  between panelled pilasters under an entablature; the ell's palmette-grilled knee-wall
  lights; the barn's crossbuck sliding doors on their track.

usage: python3 -m hoarch.buildings.sebago [check] [export]
"""
import json
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import box, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, gables as G, novel2 as N, openings as O, roof as R
from hoarch.colonial import shutters_pair
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells, wall_shell

NAME = "The Sebago"
COLORS = {"Clapboard": "#EDE7D8", "White": "#FAF9F4", "Green": "#2D4234", "Red": "#8B2C22", "Granite": "#9E9C96",
          "Shingles": "#5E5A55", "Brick": "#8C4636", "Planks": "#8D918C", "Wood": "#A87B4C", "Windows_Doors": "#FAF9F4"}
RENDER_MAT = {"Clapboard": "clap", "White": "trim", "Green": "green", "Red": "red", "Granite": "granite", "Shingles": "roof",
              "Brick": "brick", "Planks": "planks", "Wood": "wood", "Windows_Doors": "trim", "Sash": "sash", "Door": "door",
              "Glass": "glass"}
PALETTE = {"clap": ["#EDE7D8", 0.7, 0.0], "trim": ["#FAF9F4", 0.6, 0.0], "green": ["#2D4234", 0.6, 0.0],
           "red": ["#8B2C22", 0.75, 0.0], "granite": ["#9E9C96", 0.9, 0.0], "roof": ["#5E5A55", 0.85, 0.0],
           "brick": ["#8C4636", 0.85, 0.0], "planks": ["#8D918C", 0.7, 0.0], "wood": ["#A87B4C", 0.85, 0.0],
           "sash": ["#FAF9F4", 0.5, 0.0], "door": ["#2D4234", 0.5, 0.0]}
VIEWS = {"hero": [-30, 16, 70, 0.92, [0, 0, -10]], "hero_right": [32, 16, 70, 0.92, [0, 0, -10]],
         "front": [0, 6, 85, 0.95, [0, 0, 0]], "rear": [160, 20, 70, 0.92, [0, 0, -10]],
         "entrance": [-16, 8, 85, None, [36, 30, 40], 150], "dooryard": [6, 10, 85, None, [130, 60, 30], 170]}

LEDGE = 1.4
JOINT_B = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="course", h=1.6, b=1.2, orn="sbreel", role="White"),
    dict(kind="crown", h=1.6, b=1.2, P=2.4, orn="ovolo", role="Clapboard")])
EAVE_B = dict(pitch=8.0, margin=3.0, layers=[
    dict(kind="course", h=2.0, b=1.2, orn="sbfascia", role="White"),
    dict(kind="frieze", h=4.6, b=1.2, orn="sbwreath", role="Clapboard"),
    dict(kind="bed", h=1.8, b=1.4, P=3.6, role="White", brackets=dict(style="sbmutule", t=1.6, h=1.8)),
    dict(kind="crown", h=1.8, b=1.4, P=4.4, orn="cyma", role="White")])
EAVE_L = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="course", h=1.8, b=1.2, orn="sbfascia", role="White"),
    dict(kind="crown", h=1.6, b=1.2, P=2.6, orn="cavetto", role="Clapboard")])
EAVE_K = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="course", h=1.4, b=1.2, orn="sbreel", role="Clapboard"),
    dict(kind="crown", h=1.4, b=1.2, P=2.2, orn="bevel", role="White")])
EAVE_R = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="course", h=2.0, b=1.2, orn="sbsaw", role="White"),
    dict(kind="crown", h=1.8, b=1.2, P=3.0, orn="ovolo", role="Red")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT_B)) / 0.2) * 0.2

T = 3.0
ZF = 8.0
# the big house: gable to the road
BX0, BX1, BY0, BY1 = 10.0, 86.0, 36.0, 124.0
BXC = (BX0 + BX1) / 2
S1 = ZF + 34.0
ZU = S1 + RJ
ZE = ZU + 30.0
ZW = round((ZE + CO.band_height(EAVE_B)) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
SL_B, D_EAVE, RAKE = 0.62, 3.0, 3.2
BIG = Block("big", [(BX0, BY0), (BX1, BY0), (BX1, BY1), (BX0, BY1)], ZF, ZW)
# the ell (the little house): a storey and a half, ridge along the chain
LX0, LX1, LY0, LY1 = BX1, 132.0, 72.0, 124.0
ZEL = ZF + 36.0
ZWL = round((ZEL + CO.band_height(EAVE_L)) / 0.2) * 0.2
ZL_EAVE = ZWL + 1.2
SL_L, DL_EAVE = 0.65, 2.6
ELL = Block("ell", [(LX0, LY0), (LX1, LY0), (LX1, LY1), (LX0, LY1)], ZF, ZWL)
# the back house (the woodshed), one storey
KX0, KX1, KY0, KY1 = LX1, 172.0, 82.0, 124.0
ZEK = ZF + 26.0
ZWK = round((ZEK + CO.band_height(EAVE_K)) / 0.2) * 0.2
ZK_EAVE = ZWK + 1.2
SL_K, DK_EAVE = 0.75, 2.4
SHED = Block("shed", [(KX0, KY0), (KX1, KY0), (KX1, KY1), (KX0, KY1)], ZF, ZWK)
BAYS = (140.0, 154.0)                              # its open arched bays
# the English barn: long side to the road, a gabled centre bay
RX0, RX1, RY0, RY1 = KX1, 244.0, 60.0, 132.0
XD0, XD1, PJ = 192.0, 224.0, 2.0
XDC = (XD0 + XD1) / 2
ZER = ZF + 44.0
ZWR = round((ZER + CO.band_height(EAVE_R)) / 0.2) * 0.2
ZR_EAVE = ZWR + 1.4
SL_R, DR_EAVE, RAKE_R = 0.95, 3.4, 3.4
BARN = Block("barn", [(RX0, RY0), (XD0, RY0), (XD0, RY0 - PJ), (XD1, RY0 - PJ), (XD1, RY0), (RX1, RY0), (RX1, RY1), (RX0, RY1)], ZF, ZWR)
BLOCKS = [BIG, ELL, SHED, BARN]
V1, V2 = 6.0, ZU - ZF + 5.0
SHUTTERED = set()


def _openings():
    LB1, LB2, LL, LK, LR = [], [], [], [], []
    fams = {}

    def add(L, blk, x, y, v0, sp, name, kind="window", sh=False):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        L[-1].fam = fams.setdefault(id(sp), name)
        if sh:
            SHUTTERED.add(name)

    lo, up = N.window_sblower(w=8.0), N.window_sbupper(w=7.4)
    # the big house: the side-hall entrance and two windows, three over (room for the
    # shutters between), the pediment's light
    add(LB1, BIG, 28.0, BY0, 0.0, N.door_sbhall(), "entrance", "door")
    for x in (49.0, 70.0):
        add(LB1, BIG, x, BY0, V1, lo, f"S{x:.0f}-1", sh=True)
    for x in (28.0, 49.0, 70.0):
        add(LB2, BIG, x, BY0, V2, up, f"S{x:.0f}-2", sh=True)
    add(LB2, BIG, BXC, BY0, ZW + 6.0 - ZF, N.window_sbattic(), "pediment")
    # the west side, the back, the east side clear of the ell
    for y in (54.0, 80.0, 106.0):
        add(LB1, BIG, BX0, y, V1, lo, f"W{y:.0f}-1", sh=True)
        add(LB2, BIG, BX0, y, V2, up, f"W{y:.0f}-2", sh=True)
    for x in (BX0 + 20.0, BX1 - 20.0):
        add(LB1, BIG, x, BY1, V1, lo, f"N{x:.0f}-1")
        add(LB2, BIG, x, BY1, V2, up, f"N{x:.0f}-2")
    add(LB2, BIG, BXC, BY1, ZW + 6.0 - ZF, N.window_sbattic(), "N-gable")
    add(LB1, BIG, BX1, 48.0, V1, lo, "E48-1", sh=True)
    add(LB2, BIG, BX1, 52.0, V2, up, "E52-2", sh=True)
    # the ell: its door and a window onto the porch (whose roof runs up to the eave); at the
    # back the kitchen door and a window with a knee-wall light over it
    fz = ZEL - LEDGE - 0.6 - 6.4 - ZF
    lo_l = N.window_sblower(w=8.0, h=16.0)
    add(LL, ELL, LX0 + 13.0, LY0, 0.0, N.door_sbell(), "ell-door", "door")
    add(LL, ELL, LX0 + 33.0, LY0, V1, lo_l, "ell-S")
    add(LL, ELL, LX0 + 30.0, LY1, fz, N.window_sbfrieze(), "ell-knee-N")
    add(LL, ELL, LX0 + 30.0, LY1, V1, lo_l, "ell-N")
    add(LL, ELL, LX0 + 9.0, LY1, 0.0, N.door_sbell(), "kitchen-door", "door")
    # the back house: its workshop door beside the arched bays, a light at the back
    add(LK, SHED, KX1 - 5.4, KY0, 0.0, N.door_sbshop(), "shop-door", "door")
    add(LK, SHED, (KX0 + KX1) / 2, KY1, 12.0, N.window_sbbarn(), "shed-N")
    # the barn: lights along the front, at the back and the east end, the man door there, a
    # light high in the east gable
    bl = N.window_sbbarn()
    for x in (RX0 + 10.0, RX1 - 10.0):
        add(LR, BARN, x, RY0, 18.0, bl, f"barn-S{x:.0f}")
    for x in (RX0 + 18.0, RX1 - 18.0):
        add(LR, BARN, x, RY1, 18.0, bl, f"barn-N{x:.0f}")
    add(LR, BARN, RX0, 70.0, 18.0, bl, "barn-W70")
    add(LR, BARN, RX1, 78.0, 0.0, N.door_sbbarn(), "barn-door", "door")
    for y in (102.0, 120.0):
        add(LR, BARN, RX1, y, 18.0, bl, f"barn-E{y:.0f}")
    add(LR, BARN, RX1, (RY0 + RY1) / 2, ZWR + 6.0 - ZF, bl, "barn-E-gable")
    return LB1, LB2, LL, LK, LR


OPEN_B1, OPEN_B2, OPEN_L, OPEN_K, OPEN_R = _openings()
OPENINGS = OPEN_B1 + OPEN_B2 + OPEN_L + OPEN_K + OPEN_R


def _free(pt, b):
    """Is this plan corner of block b clear of the other blocks?"""
    return all(not _inside(pt, o) for o in BLOCKS if o is not b)


def _inside(pt, o):
    xs = [p[0] for p in o.pts]
    ys = [p[1] for p in o.pts]
    return min(xs) - 0.3 <= pt[0] <= max(xs) + 0.3 and min(ys) - 0.3 <= pt[1] <= max(ys) + 0.3


def _skin(f, b, reg):
    """Clapboards (the barn's boards and battens), kept clear of the cornices' bands; the
    big house's pediment in flush boards; pilasters and corner boards at free corners."""
    ze, zw = {BIG: (ZE, ZW), ELL: (ZEL, ZWL), SHED: (ZEK, ZWK), BARN: (ZER, ZWR)}[b]
    reg = reg - rect(-1, ze - LEDGE - 0.6 - b.z0, f.L + 1, zw - b.z0 + 0.2)
    if b is BIG:
        reg = reg - rect(-1, S1 - b.z0, f.L + 1, ZU - b.z0)
    if reg.is_empty():
        return M()
    ends = (_free(f.p0, b), _free(f.p1, b))
    cut = rect(-50.0, -50.0, f.L + 50.0, zw - b.z0)
    lo, hi = reg ^ cut, reg - cut
    out = []
    if b is BARN:
        if not lo.is_empty():
            out.append(N.batten_sebago(lo, datum=0.0, L=f.L if f.L > 8.0 else None, ends=ends))
        if not hi.is_empty():
            out.append(N.batten_sebago(hi, datum=0.0))
        return union(out)
    if not lo.is_empty():
        if b is BIG:
            lob = lo.bounds()
            out.append(N.clap_sebago(lo, datum=0.0, L=f.L, ends=ends, pw=4.4, panel=True, base=lob[1] < 1.0,
                                     cap=lob[3] > ZE - LEDGE - 1.0 - b.z0))
        else:
            out.append(N.clap_sebago(lo, datum=0.0, L=f.L if f.L > 8.0 else None, ends=ends, pw=2.4, panel=False))
    if not hi.is_empty():
        if b is BIG and abs(f.u[0]) > 0.5:
            out.append(N.flush_sebago(hi, datum=zw - b.z0 + 0.2))
        else:
            out.append(N.clap_sebago(hi, datum=0.0))
    return union(out)


def _shutter_room():
    """Where the shutters hang: the clapboards are kept off the wall there, so each glues flat
    on its whole back."""
    out = []
    for o in OPENINGS:
        if o.name not in SHUTTERED:
            continue
        b = o.spec["cut"].bounds()
        w_, h_ = b[2] - b[0], b[3] - b[1]
        for sg in (-1, 1):
            a, c_ = sorted((sg * (w_ / 2 + 1.1 + 1.0 - 0.3), sg * (w_ / 2 + 1.1 + 1.0 + w_ / 2 + 0.3)))
            out.append(o.facade.place(box([o.u + a, o.v0 - 0.3, -0.5], [o.u + c_, o.v0 + h_ + 0.3, 1.5])))
    return union(out)


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
            left, right = shutters_pair(w_op, h_op, casing=1.1, gap=1.0, make=N.shutter_sebago)
            for side, m in (("L", left), ("R", right)):
                kit.add(f"SHUTTER-{o.name}-{side}", "Green", m.transform(A), P=inv34(A),
                        key=f"SHUTTER-sebago-{h_op:.0f}", group="shutters")


def _m44(A):
    return np.vstack([A, [0, 0, 0, 1.0]])


def _zones(solid, z, below, above):
    lo = box([-1e4, -1e4, -10.0], [1e4, 1e4, z + 0.05])
    return [(below, solid ^ lo), (above, solid - lo)]


def _gable_cs(wl, fascia):
    return wl["cs"] + rect(0.0, -fascia - 0.4, wl["L"], -fascia + 0.01)


def _sheared(x0, x1, y0, y1, ztop, below, above):
    return M.hull_points([(x, y, ztop(y) + dz) for x in (x0, x1) for y in (y0, y1) for dz in (-below, above)])


def _pocket(roof, env, cx, cy, hx, hy, zl, ztop, rise=7.0):
    z0c = round((zl - 2.4) / 0.2) * 0.2
    roof = roof + G.pocket_seat(env, cx, cy, hx + 0.35, hy + 0.35, z0c) - box([cx - hx - 0.35, cy - hy - 0.35, z0c], [cx + hx + 0.35, cy + hy + 0.35, z0c + 200])
    ch = N.chimney_sebago(w=2 * hx, d=2 * hy, h=round((ztop + rise - z0c) / 0.2) * 0.2).translate([cx, cy, z0c])
    return roof, ch


def _rakes(kit, name, rf, roof, cut=None, d_eave=D_EAVE, rake=RAKE, w_out=0.45):
    for j, wl in enumerate(rf["walls"]):
        rk = N.raking_sebago(wl["L"], wl["slope"], d_eave, skin=1.6, depth=2.6, rake=rake - w_out - 0.05)
        A = wl["facade"].A.copy()
        A[:, 3] = wl["facade"].world(0.0, 0.0, w_out)                # (in front of the siding)
        r_ = rk.transform(A) - roof
        if cut is not None:
            r_ = r_ - cut
        r_ = max(r_.decompose(), key=lambda m_: m_.volume())
        kit.add(f"{name}-{j}", "White", r_, P=inv34(A), group="roof")


def _steps(xa, xb, y0, dy, n=3, carry=False):
    """Granite steps from a sill at ZF at y0 out along dy, standing on z = 0; with ``carry`` a
    block behind them under a deck's rim and planks (their glue face)."""
    out = []
    if carry:
        ya, yb = sorted((y0, y0 - dy * 1.0))
        yc, yd = sorted((y0 - dy * 1.0, y0 - dy * 1.8))
        out += [box([xa, ya, 0.0], [xb, yb, ZF - 2.6]), box([xa, yc, 0.0], [xb, yd, ZF - 1.4])]
    rise = ZF / (n + 1)
    for j in range(n):
        z = ZF - rise * (j + 1)
        ya, yb = sorted((y0 + dy * 2.8 * j, y0 + dy * 2.8 * (j + 1)))
        out.append(M.hull_points([(x, y, 0.0) for x in (xa, xb) for y in (ya, yb)] +
                                 [(x, y, z - 0.3) for x in (xa, xb) for y in (ya, yb)] +
                                 [(x, y, z) for x in (xa + 0.3, xb - 0.3) for y in (ya + 0.3, yb - 0.3)]))
    return union(out)


def _porch(kit, A, L, D, posts, steps, z_hi, os_l=0.0, os_r=1.6, s=0.3, OV=2.2, PT=1.4):
    """The ell's porch in its own frame (x 0..L along the wall, the wall at y = 0, the porch
    out to y = -D) placed by A. The top is one piece: a shingled roof (its courses grooved
    into its face) over a boxed soffit with a beaded ceiling, an entablature on Doric columns
    (pegs under them); it prints tilted onto its roof face, the shingles its first 0.6 mm.
    The deck: grey-painted boards out from the wall on granite piers, printed upside down."""
    zt = lambda y: z_hi + s * y
    y_out = -(D + OV)
    zc = round((zt(y_out) - PT) / 0.2) * 0.2
    xa, xb = -os_l, L + os_r
    parts = [M.hull_points([(x, y, z) for x in (xa, xb) for y in (y_out, 0.0) for z in (zc, zt(y))])]
    grooves = []
    rng = np.random.default_rng(11)
    for y in np.arange(-1.6, y_out, -2.2):
        grooves.append(_sheared(xa - 1, xb + 1, y - 0.15, y + 0.15, zt, 0.3, 1.0))
        x = xa + rng.uniform(0.3, 1.6)
        while x < xb - 0.4:
            grooves.append(_sheared(x - 0.12, x + 0.12, max(y - 2.2, y_out - 1.0), y, zt, 0.3, 1.0))
            x += rng.uniform(1.6, 2.6)
    for y in np.arange(-1.0, y_out + 0.6, -1.0):                         # the beaded ceiling
        grooves.append(box([xa + 0.6, y - 0.12, zc - 1.0], [xb - 0.6, y + 0.12, zc + 0.2]))
    yp = -D + 1.5
    zb = zc - 3.0
    parts.append(box([xa + 0.2, yp - 1.5, zb], [xb - 0.2, yp + 1.5, zc + 0.01]))         # the entablature
    parts.append(box([xa + 0.2, yp - 1.75, zc - 1.0], [xb - 0.2, yp + 1.5, zc + 0.01]))
    parts.append(box([xa + 0.2, yp - 1.7, zb], [xb - 0.2, yp + 1.5, zb + 0.5]))
    for u in posts:
        parts.append(N.post_sbdoric(zb - ZF + 0.3).translate([u, yp, ZF]))
        parts.append(box([u - 0.8, yp - 0.8, ZF - 1.2], [u + 0.8, yp + 0.8, ZF + 0.3]))
    top = union(parts) - union(grooves)
    face = _sheared(xa - 1, xb + 1, y_out - 1, 1.0, zt, 0.6, 2.0)
    ph_ = math.pi - math.atan(s)
    Rx = np.array([[1.0, 0, 0, 0], [0, math.cos(ph_), -math.sin(ph_), 0], [0, math.sin(ph_), math.cos(ph_), 0]])
    P = (_m44(Rx) @ np.linalg.inv(_m44(A)))[:3]
    topw, facew = top.transform(A), face.transform(A)
    kit.add("PORCH-top", "Shingles", topw, P=P, group="porch", change=(0.6, "White"),
            render=[("Shingles", topw ^ facew), ("White", topw - facew)])
    deck = box([0.0, -D, ZF - 1.4], [L - 0.2, -1.6, ZF])
    deck = deck + box([0.0, -D, ZF - 2.6], [L - 0.2, -D + 1.0, ZF - 1.3]) + box([L - 1.2, -D, ZF - 2.6], [L - 0.2, -1.6, ZF - 1.3])
    gaps = [box([x - 0.15, -D - 1, ZF - 0.3], [x + 0.15, 0.0, ZF + 1]) for x in np.arange(1.5, L - 0.4, 1.5)]
    piers = []
    for u in posts:
        for y in (yp, -4.0):
            piers.append(M.hull_points([(u + dx, y + dy, z) for dx in (-1.6, 1.6) for dy in (-1.6, 1.6) for z in (0.0, ZF - 2.0)] +
                                       [(u + dx, y + dy, ZF - 1.3) for dx in (-1.3, 1.3) for dy in (-1.3, 1.3)]))
    socks = [box([u - 0.95, yp - 0.95, ZF - 2.4], [u + 0.95, yp + 0.95, ZF + 1]) for u in posts]
    d_ = (deck - union(gaps) + union(piers)) - union(socks)
    dw = d_.transform(A)
    kit.add("PORCH-deck", "Planks", dw, P=(_m44(print_flip()) @ np.linalg.inv(_m44(A)))[:3], group="porch",
            change=(2.6, "Granite"), render=_zones(dw, ZF - 2.6, "Granite", "Planks"))
    return topw


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    keep = []
    core = {b.name: b.solid(grow=0.05, dz0=-20, dz1=300) for b in BLOCKS}
    und = {b.name: b.solid(grow=0.6, dz0=-20, dz1=0.0) for b in BLOCKS}
    und2 = {b.name: b.solid(grow=1.6, dz0=-20, dz1=0.0) for b in BLOCKS}         # (with their ledges)

    # --- the roofs first: each lower one stops at the wall it meets
    rb = G.gabled_roof([([(BX0, BY0 - (RAKE - D_EAVE)), (BX1, BY0 - (RAKE - D_EAVE)), (BX1, BY1 + (RAKE - D_EAVE)), (BX0, BY1 + (RAKE - D_EAVE))],
                         [1, 3], SL_B)], Z_EAVE, D_EAVE,
                       [dict(p0=(BX0, BY0), p1=(BX1, BY0), slope=SL_B), dict(p0=(BX1, BY1), p1=(BX0, BY1), slope=SL_B)],
                       texture="sbshingle", tex_kw=dict(pitch=1.5, d=0.3), skin=1.6, rake=RAKE,
                       inner_cs=offset(BIG.cs, -3.0), fascia=FASCIA, hollow=2.4)
    lpath = [(LX0 - 3.0, LY0), (LX1 - 0.8, LY0), (LX1 - 0.8, LY1), (LX0 - 3.0, LY1)]
    rl = G.gabled_roof([(lpath, [0, 2], SL_L)], ZL_EAVE, DL_EAVE,
                       [dict(p0=(LX1, LY0), p1=(LX1, LY1), slope=SL_L)], texture="sbshingle", tex_kw=dict(pitch=1.5, d=0.3), skin=1.5,
                       rake=1.8, inner_cs=offset(ELL.cs, -3.0), fascia=1.2, hollow=2.2)
    rk = G.gabled_roof([([(KX0 - 3.0, KY0), (KX1 + 3.0, KY0), (KX1 + 3.0, KY1), (KX0 - 3.0, KY1)], [0, 2], SL_K)], ZK_EAVE, DK_EAVE, [],
                       texture="sbshingle", tex_kw=dict(pitch=1.5, d=0.3), skin=1.4, inner_cs=offset(SHED.cs, -3.0), fascia=1.2, hollow=2.0)
    RYC = (RY0 + RY1) / 2
    rr = G.gabled_roof([([(RX0, RY0), (RX1, RY0), (RX1, RY1), (RX0, RY1)], [0, 2], SL_R),
                        ([(XD0, RY0 - PJ), (XD1, RY0 - PJ), (XD1, RYC), (XD0, RYC)], [1, 3], SL_R)], ZR_EAVE, DR_EAVE,
                       [dict(p0=(RX1, RY0), p1=(RX1, RY1), slope=SL_R), dict(p0=(RX0, RY1), p1=(RX0, RY0), slope=SL_R),
                        dict(p0=(XD0, RY0 - PJ), p1=(XD1, RY0 - PJ), slope=SL_R, e=DR_EAVE)],
                       texture="sbshingle", tex_kw=dict(pitch=1.6, d=0.32), skin=1.6, rake=RAKE_R,
                       inner_cs=offset(BARN.cs, -3.0), fascia=1.4, hollow=2.4)
    zrl = ZL_EAVE + SL_L * ((LY1 - LY0) / 2 + DL_EAVE)
    lwenv = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), 1.8 + 4.2).translate([0, 0, -3.15])) for wl in rl["walls"]])
    lroof = rl["body"] + rl["tex"] + rl["skins"] + rl["skin_tex"]
    lroof = (lroof + (G.ridge_cap((LX0 - 3.0, (LY0 + LY1) / 2), (LX1 + 1.8, (LY0 + LY1) / 2), zrl, SL_L, ZWL, half=0.9, up=0.5) - lwenv)) - core["big"]
    kroof = (rk["body"] + rk["tex"]) - core["ell"] - core["barn"] - box([0.0, 0.0, -1.0], [KX0 + 0.05, 300.0, 300.0])
    lr_env, kr_env = M.hull(lroof), M.hull(kroof)
    # the lower blocks' cornices (their neighbours' walls keep clear of them)
    lrings, _ = CO.level(ELL.pts, ZEL, EAVE_L, t=T, cut=core["big"] + kr_env)
    krings, _ = CO.level(SHED.pts, ZEK, EAVE_K, t=T, cut=core["ell"] + core["barn"])
    rrings, _ = CO.level(BARN.pts, ZER, EAVE_R, t=T, cut=kr_env + core["shed"])
    lr_ring = union([M.hull(r["solid"]) for r in lrings])
    kr_ring = union([M.hull(r["solid"]) for r in krings])
    print("roofs", round(time.time() - t0, 1))

    # --- the big house: two storey shells, the belt, the eave entablature, the pediments
    gb = [(BIG, 0, _gable_cs(rb["walls"][0], FASCIA).translate((0.0, Z_EAVE - ZF))),
          (BIG, 2, _gable_cs(rb["walls"][1], FASCIA).translate((0.0, Z_EAVE - ZF)))]
    band = slab(offset(BIG.cs, 10.0), ZE - LEDGE - 0.6, ZW + 0.01)
    st = stacked_shells([BIG], OPEN_B1 + OPEN_B2, [S1], t=T, corners="none", siding=_skin, clear=[lip_keep(BIG.cs, T, ZF, 1.2)],
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=[band, und["ell"], lr_env, lr_ring, _shutter_room()], gables=gb)
    kit.add("WALLS-1", "Clapboard", st["shells"][0], group="walls")
    kit.add("BELT", "Clapboard", st["rings"][0] - und2["ell"] - lr_ring, group="walls")
    lip = _corbel(BIG.cs, T, ZW) + lip_ring(BIG.cs, T, ZW)
    kit.add("WALLS-2", "Clapboard", st["shells"][1] + lip + CO.ledge(BIG.pts, ZE, LEDGE, t=T), group="walls")
    jr, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT_B, cut=und2["ell"] + lr_ring)
    CO.add_level(kit, jr, "CORNICE-J", "cornice")
    er, _ = CO.level(BIG.pts, ZE, EAVE_B, t=T)
    CO.add_level(kit, er, "CORNICE-E", "cornice")
    eenv = union([r["solid"] for r in er])
    _place_inserts(kit, OPEN_B1 + OPEN_B2, keep)
    roof = rb["body"] + rb["tex"] + rb["skins"] + rb["skin_tex"]
    zr = Z_EAVE + SL_B * ((BX1 - BX0) / 2 + D_EAVE)
    wenv = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rb["walls"]])
    roof = roof + (G.ridge_cap((BXC, BY0 - RAKE), (BXC, BY1 + RAKE), zr, SL_B, ZW, half=1.0, up=0.5) - wenv)
    roof = roof - lip_keep(BIG.cs, T, ZW)
    env, _ = R.hip_roof([([(BX0, BY0 - 0.2), (BX1, BY0 - 0.2), (BX1, BY1 + 0.2), (BX0, BY1 + 0.2)], [1, 3], SL_B)], Z_EAVE, SL_B, D_EAVE,
                        texture=None, zlo=ZW)
    hx, hy = 3.6, 4.4
    roof, chb = _pocket(roof, env, BXC, 88.0, hx, hy, Z_EAVE + SL_B * ((BX1 - BX0) / 2 + D_EAVE - hx), zr)
    roof = max(roof.decompose(), key=lambda m_: m_.volume())
    kit.add("ROOF", "Shingles", roof, group="roof")
    kit.add("CHIMNEY", "Brick", chb, group="roof")
    _rakes(kit, "RAKING", rb, roof, cut=eenv)
    print("big house", round(time.time() - t0, 1))

    # --- the ell: one shell to its knee walls, its east gable over the woodshed's roof
    gl = [(ELL, 1, _gable_cs(rl["walls"][0], 1.2).translate((0.0, ZL_EAVE - ZF)))]
    z_hi = ZEL - LEDGE - 1.0
    porch_und = box([LX0 - 1.0, LY0 - 2.0, z_hi - 7.0], [LX1 + 2.0, LY0 + 0.1, z_hi + 0.6])
    lband = slab(offset(ELL.cs, 8.0), ZEL - LEDGE - 0.6, ZWL + 0.01)
    lsh = wall_shell([ELL], OPEN_L, t=T, belt=None, corners="none", water_table=False, siding=_skin, gables=gl,
                     undress=[lband, und2["shed"], kr_env, kr_ring, porch_und])
    lw = (lsh - lip_keep(ELL.cs, T, ZF, 1.2)) + _corbel(ELL.cs, T, ZWL) + lip_ring(ELL.cs, T, ZWL) + \
        (CO.ledge(ELL.pts, ZEL, LEDGE, t=T) - kr_env)
    lw = lw - core["big"]
    kit.add("ELL-WALLS", "Clapboard", max(lw.decompose(), key=lambda m_: m_.volume()), group="walls")
    CO.add_level(kit, lrings, "CORNICE-L", "cornice")
    _place_inserts(kit, OPEN_L, keep)
    lenv, _ = R.hip_roof([(lpath, [0, 2], SL_L)], ZL_EAVE, SL_L, DL_EAVE, texture=None, zlo=ZWL)
    lroof = lroof - lip_keep(ELL.cs, T, ZWL)
    hx, hy = 3.4, 3.0
    lroof, chl = _pocket(lroof, lenv, LX1 - 11.0, (LY0 + LY1) / 2, hx, hy, ZL_EAVE + SL_L * ((LY1 - LY0) / 2 + DL_EAVE - hy), zrl, rise=6.0)
    kit.add("ELL-ROOF", "Shingles", max(lroof.decompose(), key=lambda m_: m_.volume()), group="roof")
    kit.add("ELL-CHIMNEY", "Brick", chl, group="roof")
    _rakes(kit, "ELL-RAKING", rl, lroof, cut=union([r["solid"] for r in lrings]) + kr_env, d_eave=DL_EAVE, rake=1.8)
    _porch(kit, np.array([[1.0, 0, 0, LX0 + 1.6], [0, 1.0, 0, LY0], [0, 0, 1.0, 0]]), LX1 - LX0 - 1.6, 13.0,
           [2.0, 21.4, 31.0, LX1 - LX0 - 3.8], [(2.0, 21.4)], z_hi)
    print("ell", round(time.time() - t0, 1))

    # --- the back house: its two bays open under arches, the cordwood stacked inside
    arches = []
    for k, x in enumerate(BAYS):
        op, casing = N.arch_sebago(w=10.0, h=19.0)
        Aa = np.array([[1.0, 0, 0, x], [0, 0, -1.0, KY0], [0, 1.0, 0, ZF]])
        arches.append((op, casing, Aa))
    arch_cut = union([M.extrude(op, 3.0 + 2.0).translate([0, 0, -1.0 - 3.0]).transform(Aa) for op, _, Aa in arches])
    arch_und = union([M.extrude(op.offset(1.9, JoinType.Miter, 4.0), 2.0).translate([0, 0, -0.5]).transform(Aa) for op, _, Aa in arches])
    kband = slab(offset(SHED.cs, 8.0), ZEK - LEDGE - 0.6, ZWK + 0.01)
    ksh = wall_shell([SHED], OPEN_K, t=T, belt=None, corners="none", water_table=False, siding=_skin,
                     undress=[kband, arch_und])
    kw = (ksh - lip_keep(SHED.cs, T, ZF, 1.2)) + _corbel(SHED.cs, T, ZWK) + lip_ring(SHED.cs, T, ZWK) + CO.ledge(SHED.pts, ZEK, LEDGE, t=T)
    kw = kw - core["ell"] - core["barn"] - arch_cut
    kit.add("SHED-WALLS", "Clapboard", max(kw.decompose(), key=lambda m_: m_.volume()), group="walls")
    CO.add_level(kit, krings, "CORNICE-K", "cornice")
    _place_inserts(kit, OPEN_K, keep)
    for k, (op, casing, Aa) in enumerate(arches):
        kit.add(f"ARCH-{k}", "White", casing.transform(Aa), P=inv34(Aa), key="ARCH-sebago", group="inserts")
        kit.add(f"WOODPILE-{k}", "Wood", N.woodpile_sebago(L=8.8, d=9.0, h=16.0, seed=k).translate([BAYS[k] - 3.4, KY0 + T + 1.3 + 0.2, 0.0]),
                group="stoop")
    kroof = kroof - lip_keep(SHED.cs, T, ZWK)
    kit.add("SHED-ROOF", "Shingles", max(kroof.decompose(), key=lambda m_: m_.volume()), group="roof")
    print("back house", round(time.time() - t0, 1))

    # --- the barn: boards and battens, the gabled bay with the great doors and the hay door,
    # the cupola on the ridge
    where = [(5, 0.0), (7, 0.0), (2, 0.0)]
    gr = [(BARN, e, _gable_cs(wl, 1.4).translate((u0, ZR_EAVE - ZF))) for (e, u0), wl in zip(where, rr["walls"])]
    Ad = np.array([[1.0, 0, 0, XDC], [0, 0, -1.0, RY0 - PJ], [0, 1.0, 0, ZF]])
    doors = N.barn_doors_sebago(W=22.0, H=34.0, run=3.0)
    Ah = np.array([[1.0, 0, 0, XDC], [0, 0, -1.0, RY0 - PJ], [0, 1.0, 0, ZWR + 0.8]])
    hay = N.hay_door_sebago(w=8.0, h=7.0)
    db, hb = doors.bounding_box(), hay.bounding_box()
    door_und = box([db[0] - 0.3, db[1] - 0.3, -0.5], [db[3] + 0.3, db[4] + 0.3, 2.0]).transform(Ad) + \
        box([hb[0] - 0.3, hb[1] - 0.3, -0.5], [hb[3] + 0.3, hb[4] + 0.3, 2.0]).transform(Ah)
    rband = slab(offset(BARN.cs, 8.0), ZER - LEDGE - 0.6, ZWR + 0.01)
    rsh = wall_shell([BARN], OPEN_R, t=T, belt=None, corners="none", water_table=False, siding=_skin, gables=gr,
                     undress=[rband, und2["shed"], kr_env, kr_ring, door_und])
    rw = (rsh - lip_keep(BARN.cs, T, ZF, 1.2)) + _corbel(BARN.cs, T, ZWR) + lip_ring(BARN.cs, T, ZWR) + \
        (CO.ledge(BARN.pts, ZER, LEDGE, t=T) - kr_env)
    kit.add("BARN-WALLS", "Red", rw, group="walls")
    CO.add_level(kit, rrings, "CORNICE-R", "cornice")
    _place_inserts(kit, OPEN_R, keep)
    dw, hw = doors.transform(Ad), hay.transform(Ah)
    kit.add("BARN-DOORS", "Red", dw, P=inv34(Ad), group="inserts", change=(0.8, "White"),
            render=[("Red", dw ^ ext_slab(Ad, 0.82)), ("White", dw - ext_slab(Ad, 0.82))])
    kit.add("HAY-DOOR", "Red", hw, P=inv34(Ah), group="inserts", change=(0.8, "White"),
            render=[("Red", hw ^ ext_slab(Ah, 0.82)), ("White", hw - ext_slab(Ah, 0.82))])
    rroof = rr["body"] + rr["tex"] + rr["skins"] + rr["skin_tex"]
    zrr = ZR_EAVE + SL_R * ((RY1 - RY0) / 2 + DR_EAVE)
    rwenv = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE_R + 4.2).translate([0, 0, -3.15])) for wl in rr["walls"]])
    rroof = rroof + (G.ridge_cap((RX0 - RAKE_R, RYC), (RX1 + RAKE_R, RYC), zrr, SL_R, ZWR, half=1.1, up=0.5) - rwenv)
    rroof = rroof - lip_keep(BARN.cs, T, ZWR)
    rroof = max(rroof.decompose(), key=lambda m_: m_.volume())
    kit.add("BARN-ROOF", "Shingles", rroof, group="roof")
    _rakes(kit, "BARN-RAKING", rr, rroof, cut=union([r["solid"] for r in rrings]) + kr_env + hw, d_eave=DR_EAVE, rake=RAKE_R, w_out=0.8)
    cup = N.cupola_sebago(SL_R).translate([XDC, RYC, zrr + 1.2]) - rroof
    cup = max(cup.decompose(), key=lambda m_: m_.volume())
    zcb = zrr + 1.2 + 8.0
    kit.add("CUPOLA", "White", cup, group="roof", change=(round((zcb - cup.bounding_box()[2]) / 0.2) * 0.2, "Shingles"),
            render=_zones(cup, zcb, "White", "Shingles"))
    print("barn", round(time.time() - t0, 1))

    # --- the footings, the steps and the ramp
    house_keep = union(keep)
    bases = {b.name: foundation([b], 0.0, ZF, style="sbgranite", seed=k * 5) for k, b in enumerate(BLOCKS)}
    flat = box([28.0 - 8.0, BY0 - 4.0, -1.0], [28.0 + 8.0, BY0 - 0.8, ZF + 1.0])          # (the steps glue to a dressed face)
    kit.add("BASE", "Granite", bases["big"] - house_keep - flat, group="foundation")
    kit.add("ELL-BASE", "Granite", bases["ell"] - bases["big"] - core["big"] - house_keep, group="foundation")
    kit.add("SHED-BASE", "Granite", bases["shed"] - bases["ell"] - bases["barn"] - core["ell"] - core["barn"] - house_keep, group="foundation")
    kit.add("BARN-BASE", "Granite", bases["barn"] - house_keep, group="foundation")
    kit.add("STEPS", "Granite", _steps(28.0 - 8.0, 28.0 + 8.0, BY0 - 0.8, -1.0) - house_keep, group="stoop")
    kit.add("PORCH-STEPS", "Granite", _steps(LX0 + 5.2, LX0 + 21.4, LY0 - 13.0, -1.0, carry=True), group="stoop")
    ramp = M.hull_points([(x, y, z) for x in (XD0 + 3.0, XD1 - 3.0) for (y, z) in
                          ((RY0 - PJ - 1.6, 0.0), (RY0 - PJ - 1.6, ZF), (RY0 - PJ - 16.0, 0.0), (RY0 - PJ - 16.0, 0.6))])
    ramp = ramp - union([box([XD0, y - 0.15, ZF - 3.0], [XD1, y + 0.15, ZF + 2.0]) for y in np.arange(RY0 - PJ - 4.0, RY0 - PJ - 15.0, -3.2)])
    kit.add("RAMP", "Granite", ramp - house_keep, group="stoop")
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


def ext_slab(A, w):
    """The world slab of a part placed by A from its back (w = 0) to w (its first layers)."""
    return box([-500, -500, -1.0], [500, 500, w]).transform(A)


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "sebago")
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
    kit.render_npz(os.path.join(OUT, "sebago.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
