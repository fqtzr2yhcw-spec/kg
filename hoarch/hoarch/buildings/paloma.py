"""The Paloma: an original HO-scale (1:87.1) Monterey Colonial adobe; house 108, of the
new-layouts batch (hoarch.novel2), after the Larkin House, Monterey, California (1835), the
first of its kind, and the adobes round it.

A two-storey adobe at the back of a courtyard that opens to the street, its low hipped roof of
redwood shingles running out over a two-tier gallery on three sides of it: a tiled corredor
below and a balcony above, each tier on its own slender posts with carved zapatas, the balcony
railed in turned balusters. Two one-storey adobe wings come forward from it round the court,
each with a corredor facing the court under a shingled shed and a window caged in a turned
reja to the street; a lime-washed garden wall with a tile coping and an arched gate closes the
court; a well stands in it. The walls are lime-washed adobe, a painted dado at their foot,
patches fallen away here and there to the adobe bricks.

- Cornices: the balcony joint, a running Vitruvian scroll over a dogtooth course under a bevel;
  the eave (under the gallery roof), chip-carved rosettes in square panels under a cavetto; the
  wings, a dogtooth course under a bevel.
- Windows: nine over six deep in the adobe with a corniced head and a sill on corbels below;
  six over six under little pediments above; the doors onto the balcony are glazed pairs under
  pediments; the court door a pair of six-panel leaves with nail heads under a carved lintel.

usage: python3 -m hoarch.buildings.paloma [check] [export]
"""
import json
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, gables as G, novel2 as N, openings as O, roof as R
from hoarch.colonial import shutters_pair
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells, wall_shell

NAME = "The Paloma"
COLORS = {"Limewash": "#EFE9DC", "Redwood": "#7A3B2A", "Green": "#3C5B3A", "Shingle": "#6B5E50", "Terracotta": "#B4623E",
          "Sandstone": "#C4B08E", "Planks": "#8A6A4A", "Windows_Doors": "#3C5B3A"}
RENDER_MAT = {"Limewash": "walls", "Redwood": "wood", "Green": "green", "Shingle": "roof", "Terracotta": "tile",
              "Sandstone": "stone", "Planks": "planks", "Windows_Doors": "green", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"walls": ["#EFE9DC", 0.9, 0.0], "wood": ["#7A3B2A", 0.7, 0.0], "green": ["#3C5B3A", 0.6, 0.0],
           "roof": ["#6B5E50", 0.85, 0.0], "tile": ["#B4623E", 0.85, 0.0], "stone": ["#C4B08E", 0.9, 0.0],
           "planks": ["#8A6A4A", 0.75, 0.0], "sash": ["#EFE9DC", 0.5, 0.0], "door": ["#7A3B2A", 0.5, 0.0]}
VIEWS = {"hero": [-32, 18, 70, 0.9, [0, 0, -10]], "hero_right": [34, 18, 70, 0.9, [0, 0, -10]],
         "front": [0, 10, 85, 0.92, [0, 0, 0]], "rear": [160, 20, 70, 0.92, [0, 0, -10]],
         "court": [-6, 24, 85, None, [116, 80, 30], 190], "gallery": [-40, 10, 85, None, [40, 140, 45], 170]}

LEDGE = 1.4
JOINT = dict(pitch=10.0, margin=3.0, layers=[
    dict(kind="frieze", h=3.6, b=1.2, orn="plwave", role="Redwood"),
    dict(kind="course", h=1.4, b=1.2, orn="pltooth", role="Limewash"),
    dict(kind="crown", h=1.8, b=1.2, P=3.2, orn="bevel", role="Redwood")])
EAVE = dict(pitch=10.0, margin=3.0, layers=[
    dict(kind="frieze", h=3.6, b=1.2, orn="plrosette", role="Green"),
    dict(kind="crown", h=2.0, b=1.2, P=3.4, orn="cavetto", role="Redwood")])
KEAVE = dict(pitch=10.0, margin=3.0, layers=[
    dict(kind="course", h=1.6, b=1.2, orn="pltooth", role="Redwood"),
    dict(kind="crown", h=1.8, b=1.2, P=2.8, orn="bevel", role="Limewash")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)
HEK = CO.band_height(KEAVE)
P_J = 3.2                                         # how far the joint's crown stands out

T = 3.0
X0, X1, Y0, Y1 = 46.0, 186.0, 120.0, 184.0         # the house at the back of the court, 140 x 64
XC = (X0 + X1) / 2
WL, WR = (X0, X0 + 40.0), (X1 - 40.0, X1)          # the wings, coming forward to y = YF
YF = 34.0
GD = 16.0                                          # the gallery's depth
ZF = 6.0
S1 = ZF + 32.0
ZU = S1 + RJ                                      # the upper floor and the balcony
ZE = ZU + 29.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
SL, DE = 0.42, 3.0
MAIN = Block("main", [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)], ZF, ZW)
RPATH = [(X0 - GD, Y0 - GD), (X1 + GD, Y0 - GD), (X1 + GD, Y1), (X0 - GD, Y1)]   # the roof's wall line: the galleries' outer posts
ZEK = ZF + 27.0
ZWK = round((ZEK + HEK) / 0.2) * 0.2
ZK_EAVE = ZWK + 1.2
SLK, DK = 0.42, 2.6
WINGL = Block("wing-W", [(WL[0], YF), (WL[1], YF), (WL[1], Y0), (WL[0], Y0)], ZF, ZWK)
WINGR = Block("wing-E", [(WR[0], YF), (WR[1], YF), (WR[1], Y0), (WR[0], Y0)], ZF, ZWK)
DC = 12.0                                         # the wings' corredors' depth
YCO0, YCO1 = YF + 6.0, Y0 - GD                     # and their run along the wings
PY = Y0 - GD + 1.4                                 # the galleries' outer posts
PXW, PXE = X0 - GD + 1.4, X1 + GD - 1.4


def _openings():
    L1, L2, LW = [], [], []
    fams = {}
    shut = set()

    def add(L, blk, x, y, v0, sp, name, kind="window", sh=False):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        L[-1].fam = fams.setdefault(id(sp), name)
        if sh:
            shut.add(name)

    win, upw, fr = N.window_plmain(), N.window_plupper(), N.door_plfrench()
    plank, court = N.door_plplank(), N.window_plcourt()
    # the court front: the great door between two shuttered windows, three doors onto the balcony
    add(L1, MAIN, XC, Y0, 0.0, N.door_plmain(), "court-door", "door")
    for x in (XC - 18.0, XC + 18.0):
        add(L1, MAIN, x, Y0, 7.0, win, f"S{x:.0f}-1")
    for x in (XC - 18.0, XC, XC + 18.0):
        add(L2, MAIN, x, Y0, ZU - ZF + 0.4, fr, f"S{x:.0f}-2", "door")
    for x in (WL[0] + 20.0, WR[0] + 20.0):                         # over the wings' roofs
        add(L2, MAIN, x, Y0, ZU - ZF + 6.0, upw, f"S{x:.0f}-2")
    # the ends: windows below, doors onto the end balconies above, a door to the corredor
    for x, tag in ((X0, "W"), (X1, "E")):
        for y in (132.0, 172.0):
            add(L1, MAIN, x, y, 7.0, win, f"{tag}{y:.0f}-1", sh=True)
            add(L2, MAIN, x, y, ZU - ZF + 0.4, fr, f"{tag}{y:.0f}-2", "door")
        add(L1, MAIN, x, 152.0, 0.0, plank, f"{tag}-door", "door")
    # the back
    for x in (X0 + 14.0, X0 + 46.0, X1 - 46.0, X1 - 14.0):
        add(L1, MAIN, x, Y1, 7.0, win, f"N{x:.0f}-1", sh=True)
    add(L1, MAIN, XC, Y1, 0.0, plank, "back-door", "door")
    for x in (X0 + 14.0, X0 + 46.0, XC, X1 - 46.0, X1 - 14.0):
        add(L2, MAIN, x, Y1, ZU - ZF + 6.0, upw, f"N{x:.0f}-2")
    # the wings: a reja to the street, windows out, a door and windows to the court
    reja = N.window_plreja()
    for blk, xo, xi in ((WINGL, WL[0], WL[1]), (WINGR, WR[1], WR[0])):
        add(LW, blk, (WL[0] + WL[1]) / 2 if blk is WINGL else (WR[0] + WR[1]) / 2, YF, 8.0, reja, f"reja-{blk.name}")
        for y in (62.0, 94.0):
            add(LW, blk, xo, y, 8.0, court, f"{blk.name}-out{y:.0f}")
        add(LW, blk, xi, 76.0, 0.0, plank, f"{blk.name}-door", "door")
        for y in (56.0, 96.0):
            add(LW, blk, xi, y, 8.0, court, f"{blk.name}-in{y:.0f}")
    return L1, L2, LW, shut


OPEN1, OPEN2, OPEN_W, SHUTTERED = _openings()
OPENINGS = OPEN1 + OPEN2 + OPEN_W
BLOCKS = [MAIN, WINGL, WINGR]


def _skin(f, b, reg):
    """Lime-washed adobe, kept clear of the cornices' bands."""
    if b is MAIN:
        reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
        reg = reg - rect(-1, S1 - b.z0, f.L + 1, ZU - b.z0)
    else:
        reg = reg - rect(-1, ZEK - LEDGE - 0.6 - b.z0, f.L + 1, ZWK - b.z0 + 0.2)
    if reg.is_empty():
        return M()
    seed = int(abs(f.p0[0]) * 3 + abs(f.p0[1]) * 7) % 97
    return N.adobe_paloma(reg, datum=0.0, seed=seed, dado=5.0 if b.z0 == ZF else -10.0)


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
            left, right = shutters_pair(w_op, h_op, casing=1.1, gap=0.5, make=N.shutter_paloma)
            for side, m in (("L", left), ("R", right)):
                kit.add(f"SHUTTER-{o.name}-{side}", "Green", m.translate([0, 0, 0.35]).transform(A), P=inv34(A),
                        key="SHUTTER-paloma", group="shutters")


def _m44(A):
    return np.vstack([A, [0, 0, 0, 1.0]])


def _beam(a, b_, z0, z1, wd=2.2):
    """A beam from post a to post b (plan points), z0 to z1, wd wide."""
    a, b_ = np.array(a), np.array(b_)
    d = (b_ - a) / np.linalg.norm(b_ - a)
    n = np.array([-d[1], d[0]]) * wd / 2
    pts = [a - d * 1.0 + n, b_ + d * 1.0 + n, b_ + d * 1.0 - n, a - d * 1.0 - n]
    return M.extrude(poly([tuple(p) for p in pts]), z1 - z0).translate([0, 0, z0])


def _zapata(p, d, z_top):
    """A zapata on a post at p under a beam running along d, its top at z_top."""
    d = np.array(d, float) / np.linalg.norm(d)
    A = np.array([[d[0], -d[1], 0.0, p[0]], [d[1], d[0], 0.0, p[1]], [0.0, 0.0, 1.0, z_top - 1.6]])
    return N.zapata_paloma().transform(A)


def _rail(a, b_, z, h=7.6):
    """A balcony railing between two posts (plan points), standing on z: rails top and bottom,
    turned balusters between."""
    a, b_ = np.array(a), np.array(b_)
    L = float(np.linalg.norm(b_ - a))
    d = (b_ - a) / L
    a2, b2 = a + d * 1.3, b_ - d * 1.3
    out = [_beam(a2 + d, b2 - d, z + 0.3, z + 1.1, 1.0), _beam(a2 + d, b2 - d, z + h - 1.0, z + h, 1.2)]
    n = max(1, int((L - 2.6) / 1.8))
    for k in range(n):
        p = a2 + (b2 - a2) * (k + 0.5) / n
        out.append(N.baluster_paloma(h - 2.0).translate([p[0], p[1], z + 1.05]))
    return union(out)


def _galleries(kit, jenv, keep, fnd):
    """The two-tier galleries: the corredor's tiled floor, the lower posts with zapatas and the
    beam the balcony rests on (one piece, upright on pegs), the balcony deck (planked, upside
    down, rebated over the joint's crown), the upper posts with zapatas, railing and the plate
    under the roof (one piece, upright on pegs into the deck)."""
    zbt = ZU - 1.2                                   # the deck's foot: the lower beam's top
    zpl = ZW                                         # the roof's soffit: the upper plate's top
    sides = {
        "front": dict(posts=[(x, PY) for x in np.linspace(WL[1] + DC - 1.2, WR[0] - DC + 1.2, 4)],
                      chains=[[0, 1, 2, 3]], ends=[((WL[1] + DC - 1.2, PY), (WL[1] + DC - 1.2, Y0 - P_J - 0.6)),
                                                   ((WR[0] - DC + 1.2, PY), (WR[0] - DC + 1.2, Y0 - P_J - 0.6))],
                      deck=rect(WL[1] + DC - 2.4, Y0 - GD, WR[0] - DC + 2.4, Y0), floor=rect(WL[1], Y0 - GD, WR[0], Y0)),
        "west": dict(posts=[(PXW, y) for y in np.linspace(PY, Y1 - 1.4, 5)] + [(X0 - 4.6, PY)],
                     chains=[[0, 1, 2, 3, 4], [0, 5]], ends=[((PXW, Y1 - 1.4), (X0 - P_J - 0.6, Y1 - 1.4))],
                     deck=rect(X0 - GD, Y0 - GD, X0, Y1), floor=rect(X0 - GD, Y0 - GD, X0, Y1)),
        "east": dict(posts=[(PXE, y) for y in np.linspace(PY, Y1 - 1.4, 5)] + [(X1 + 4.6, PY)],
                     chains=[[0, 1, 2, 3, 4], [0, 5]], ends=[((PXE, Y1 - 1.4), (X1 + P_J + 0.6, Y1 - 1.4))],
                     deck=rect(X1, Y0 - GD, X1 + GD, Y1), floor=rect(X1, Y0 - GD, X1 + GD, Y1)),
    }
    house = MAIN.solid(grow=0.15, dz0=-10, dz1=200)
    for name, sd in sides.items():
        posts = sd["posts"]
        # the corredor's floor: square terracotta tiles on a low plinth, sockets for the posts
        fl = M.extrude(sd["floor"], ZF - 0.01) - house - fnd
        tiles = [box([x - 0.15, -1e3, ZF - 0.3], [x + 0.15, 1e3, ZF + 1]) for x in np.arange(0.0, 260.0, 3.0)] + \
                [box([-1e3, y - 0.15, ZF - 0.3], [1e3, y + 0.15, ZF + 1]) for y in np.arange(0.0, 260.0, 3.0)]
        fl = fl - union(tiles) - union([box([p[0] - 0.85, p[1] - 0.85, ZF - 1.4], [p[0] + 0.85, p[1] + 0.85, ZF + 1]) for p in posts])
        kit.add(f"CORREDOR-{name}", "Terracotta", fl, group="foundation")
        # the lower tier
        zb0 = round((zbt - 2.4) / 0.2) * 0.2
        lo = []
        for p in posts:
            lo.append(N.post_paloma(zb0 - 1.6 - ZF).translate([p[0], p[1], ZF]))
            lo.append(box([p[0] - 0.7, p[1] - 0.7, ZF - 1.2], [p[0] + 0.7, p[1] + 0.7, ZF + 0.3]))
        for chain in sd["chains"]:
            seq = [posts[k] for k in chain]
            for a, b_ in zip(seq[:-1], seq[1:]):
                lo.append(_beam(a, b_, zb0, zbt))
                for p in (a, b_):
                    lo.append(_zapata(p, np.array(b_) - np.array(a), zb0 + 0.01))
        lower = union(lo) - house - jenv
        kit.add(f"GALLERY-{name}-lower", "Redwood", lower, group="porch")
        # the balcony deck
        deck = M.extrude(sd["deck"], 1.6).translate([0, 0, zbt]) - house - jenv
        deck = deck - union([box([x - 0.15, -1e3, ZU + 0.1], [x + 0.15, 1e3, ZU + 1]) for x in np.arange(0.0, 260.0, 1.6)]
                            if name == "front" else
                            [box([-1e3, y - 0.15, ZU + 0.1], [1e3, y + 0.15, ZU + 1]) for y in np.arange(0.0, 260.0, 1.6)])
        deck = deck - union([box([p[0] - 0.85, p[1] - 0.85, zbt - 1], [p[0] + 0.85, p[1] + 0.85, ZU + 1]) for p in posts])
        kit.add(f"BALCONY-{name}", "Planks", deck, P=print_flip(), group="porch")
        # the upper tier
        zt = ZU + 0.4
        up = []
        for p in posts:
            up.append(N.post_paloma(zpl - 2.4 - 1.6 - zt).translate([p[0], p[1], zt]))
            up.append(box([p[0] - 0.7, p[1] - 0.7, zt - 1.2], [p[0] + 0.7, p[1] + 0.7, zt + 0.3]))
        for chain in sd["chains"]:
            seq = [posts[k] for k in chain]
            for a, b_ in zip(seq[:-1], seq[1:]):
                up.append(_beam(a, b_, zpl - 2.4, zpl))
                up.append(_rail(a, b_, zt))
                for p in (a, b_):
                    up.append(_zapata(p, np.array(b_) - np.array(a), zpl - 2.39))
        for a, b_ in sd["ends"]:
            up.append(_rail(a, b_, zt))
        upper = union(up) - house - jenv - union(keep)
        kit.add(f"GALLERY-{name}-upper", "Redwood", max(upper.decompose(), key=lambda m_: m_.volume()), group="porch")


def _corredor(kit, name, A, L, posts, z_hi, keep_env, fnd, s=0.25, D=DC, OS=1.4, OV=2.2, PT=1.4):
    """A wing's corredor, built in its own frame (x 0..L along the wall, the wall at y = 0, out to
    y = -D) placed by A: the shingled shed roof from under the wing's eave, rafters, ledger, the
    beam on zapatas over round posts with pegs, all one piece printed upside down tilted onto its
    shingled face (the shingles are cut in, courses and joints); the tiled floor on its plinth."""
    zt = lambda y: z_hi + s * y
    y_out = -(D + OV)
    sh = lambda x0, x1, y0, y1, below, above: M.hull_points([(x, y, zt(y) + dz) for x in (x0, x1) for y in (y0, y1) for dz in (-below, above)])
    parts = [sh(-OS, L + OS, y_out, 0.0, PT, 0.0), box([0.0, -1.2, z_hi - PT - 2.0], [L, 0.0, z_hi - PT + 0.3])]
    cuts = []
    for k, y in enumerate(np.arange(-1.6, y_out, -1.6)):                  # the courses
        cuts.append(sh(-OS - 1, L + OS + 1, y - 0.15, y + 0.15, 0.25, 1.0))
        off = (k % 2) * 0.9
        for x in np.arange(-OS + off, L + OS, 1.8):
            cuts.append(sh(x - 0.12, x + 0.12, y, y + 1.6, 0.25, 1.0))
    for x in np.arange(1.0, L - 0.5, 4.0):
        parts.append(sh(x - 0.45, x + 0.45, y_out + 0.3, -1.2, PT + 0.9, -PT + 0.2))
    zb = round((zt(-D) - PT - 2.2) / 0.2) * 0.2
    parts.append(box([-0.4, -D, zb], [L + 0.4, -D + 2.4, zt(-D + 2.4) - PT + 0.2]))
    yp = -D + 1.2
    for u in posts:
        parts.append(N.post_paloma(zb - 1.6 - (ZF - 0.6) + 0.1).translate([u, yp, ZF - 0.6]))
        parts.append(box([u - 0.7, yp - 0.7, ZF - 1.8], [u + 0.7, yp + 0.7, ZF - 0.3]))
        parts.append(_zapata((u, yp), (1.0, 0.0), zb + 0.01))
    top = union(parts) - union(cuts)
    face = sh(-OS - 1, L + OS + 1, y_out - 1, 1.0, 0.6, 2.0)
    ph_ = math.pi - math.atan(s)
    Rm = np.array([[1.0, 0, 0, 0], [0, math.cos(ph_), -math.sin(ph_), 0], [0, math.sin(ph_), math.cos(ph_), 0]])
    P = (_m44(Rm) @ np.linalg.inv(_m44(A)))[:3]
    topw = top.transform(A) - keep_env
    facew = face.transform(A)
    kit.add(f"{name}-top", "Shingle", topw, P=P, group="porch", change=(0.6, "Redwood"),
            render=[("Shingle", topw ^ facew), ("Redwood", topw - facew)])
    fl = box([0.0, -D - 0.6, 0.0], [L, -0.4, ZF - 0.6])
    tiles = [box([x - 0.15, -D - 2, ZF - 0.9], [x + 0.15, 1.0, ZF]) for x in np.arange(1.5, L, 3.0)] + \
            [box([-1.0, y - 0.15, ZF - 0.9], [L + 1, y + 0.15, ZF]) for y in np.arange(-1.9, -D - 0.6, -3.0)]
    fl = fl - union(tiles) - union([box([u - 0.85, yp - 0.85, ZF - 2.0], [u + 0.85, yp + 0.85, ZF]) for u in posts])
    kit.add(f"{name}-floor", "Terracotta", fl.transform(A) - fnd, group="foundation")


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()

    # --- the wings' roofs first (the house's walls and joint keep clear of them)
    wroofs = {}
    for blk in (WINGL, WINGR):
        xa, xb = blk.pts[0][0], blk.pts[1][0]
        rw = G.gabled_roof([(blk.pts, [1, 3], SLK)], ZK_EAVE, DK, [dict(p0=(xa, YF), p1=(xb, YF), slope=SLK)],
                           texture="monterey", tex_kw=dict(pitch=1.3, d=0.3), skin=1.4, rake=2.4,
                           inner_cs=offset(blk.cs, -3.0), fascia=1.2, hollow=2.2)
        wroofs[blk.name] = rw
    house_env = MAIN.solid(grow=0.15, dz0=-10, dz1=300)
    wenv = union([(rw["body"] + rw["tex"]) for rw in wroofs.values()])
    wings_env = union([b.solid(grow=0.15, dz0=-10, dz1=0.0) for b in (WINGL, WINGR)])
    wings_und = union([b.solid(grow=0.6, dz0=-10, dz1=0.0) for b in (WINGL, WINGR)])

    # --- the house: two storeys, the joint at the balcony's floor, the eave under the gallery roof
    band = slab(offset(MAIN.cs, 9.0), ZE - LEDGE - 0.6, ZW + 0.01)
    st = stacked_shells([MAIN], OPEN1 + OPEN2, [S1], t=T, corners="none", siding=_skin, clear=[lip_keep(MAIN.cs, T, ZF, 1.2)],
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=[band, wenv, wings_und])
    kit.add("WALLS-1", "Limewash", st["shells"][0] - wenv, group="walls")
    kit.add("JOINT", "Limewash", st["rings"][0] - wenv, group="walls")
    lip = _corbel(MAIN.cs, T, ZW) + lip_ring(MAIN.cs, T, ZW)
    kit.add("WALLS-2", "Limewash", st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE, t=T), group="walls")
    jr, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=wenv + wings_env)
    CO.add_level(kit, jr, "CORNICE-J", "cornice")
    jenv = union([r["solid"] for r in jr])
    er, _ = CO.level(MAIN.pts, ZE, EAVE, t=T)
    CO.add_level(kit, er, "CORNICE-E", "cornice")
    keep = []
    _place_inserts(kit, OPEN1 + OPEN2, keep)
    print("house", round(time.time() - t0, 1))

    # --- the great roof: redwood shingles, out over the galleries, a chimney at the back
    rf = G.gabled_roof([(RPATH, [0, 1, 2, 3], SL)], Z_EAVE, DE, [], texture="monterey", tex_kw=dict(pitch=1.4, d=0.32),
                       skin=1.6, inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA, hollow=2.4)
    roof = rf["body"] + rf["tex"]
    yr = (Y0 - GD + Y1) / 2
    hl = (Y1 - (Y0 - GD)) / 2
    zr = Z_EAVE + SL * (hl + DE)
    roof = roof + G.ridge_cap((X0 - GD + hl, yr), (X1 + GD - hl, yr), zr, SL, ZW, half=1.0, up=0.5)
    roof = roof - lip_keep(MAIN.cs, T, ZW)
    env, _ = R.hip_roof([(RPATH, [0, 1, 2, 3], SL)], Z_EAVE, SL, DE, texture=None, zlo=ZW)
    chim = []
    for (cx, cy, hx, hy) in ((X1 - 22.0, Y1 - 12.0, 4.0, 3.5),):
        zl = Z_EAVE + SL * ((Y1 + DE) - (cy + hy))
        z0c = round((zl - 2.4) / 0.2) * 0.2
        roof = roof + G.pocket_seat(env, cx, cy, hx + 0.3, hy + 0.3, z0c) - box([cx - hx - 0.3, cy - hy - 0.3, z0c], [cx + hx + 0.3, cy + hy + 0.3, z0c + 200])
        chim.append(N.chimney_paloma(w=2 * hx, d=2 * hy, h=round((zr + 7.0 - z0c) / 0.2) * 0.2).translate([cx, cy, z0c]))
    kit.add("ROOF", "Shingle", max(roof.decompose(), key=lambda m_: m_.volume()), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the base: a sandstone footing under the house and the wings
    fnd = foundation([MAIN, WINGL, WINGR], 0.0, ZF, style="plstone")
    kit.add("FOUNDATION", "Sandstone", fnd, group="foundation")

    # --- the galleries
    _galleries(kit, jenv, keep, fnd)
    print("galleries", round(time.time() - t0, 1))

    # --- the wings: walls with the street gable, eave cornice (cut where the corredor's roof
    # comes in and against the house), the roof against the house's wall, corredors to the court
    wing_walls = []
    for blk, sgn in ((WINGL, 1), (WINGR, -1)):
        rw = wroofs[blk.name]
        xa, xb = blk.pts[0][0], blk.pts[1][0]
        xin = xb if sgn > 0 else xa
        g = [(blk, 0, (rw["walls"][0]["cs"] + rect(0.0, -1.2 - 0.4, rw["walls"][0]["L"], -1.19)).translate((0.0, ZK_EAVE - ZF)))]
        kband = slab(offset(blk.cs, 8.0), ZEK - LEDGE - 0.6, ZWK + 0.01)
        sw = wall_shell([blk], [o for o in OPEN_W if o.block is blk], t=T, belt=None, corners="none", water_table=False,
                        siding=_skin, gables=g, undress=[kband])
        sw = (sw - lip_keep(blk.cs, T, ZF, 1.2)) + _corbel(blk.cs, T, ZWK) + lip_ring(blk.cs, T, ZWK) + CO.ledge(blk.pts, ZEK, LEDGE, t=T)
        sw = sw - house_env
        # the corredor's frame: along the court side, out from the wall
        if sgn > 0:
            A = np.array([[0.0, -1.0, 0.0, xin], [1.0, 0.0, 0.0, YCO0], [0.0, 0.0, 1.0, 0.0]])
        else:
            A = np.array([[0.0, 1.0, 0.0, xin], [-1.0, 0.0, 0.0, YCO1], [0.0, 0.0, 1.0, 0.0]])
        Lc = YCO1 - YCO0
        cor_env = box([min(xin, xin + sgn * (DC + 3)), YCO0 - 2, ZEK - LEDGE - 3.0], [max(xin, xin + sgn * (DC + 3)), YCO1 + 2, ZWK + 0.5])
        kit.add(f"WALLS-{blk.name}", "Limewash", sw, group="walls")
        kr, _ = CO.level(blk.pts, ZEK, KEAVE, t=T, cut=house_env + cor_env)
        CO.add_level(kit, kr, f"CORNICE-{blk.name}", "cornice")
        kenv = union([r["solid"] for r in kr])
        wk = []
        _place_inserts(kit, [o for o in OPEN_W if o.block is blk], wk)
        keep += wk
        wr = rw["body"] + rw["tex"] + rw["skins"] + rw["skin_tex"]
        wr = wr - lip_keep(blk.cs, T, ZWK) - house_env
        if blk is WINGL:                                    # the wing's chimney on its outer slope
            cx, cy, hx, hy = xa + 10.0, 60.0, 3.5, 3.0
            wenv_, _ = R.hip_roof([(blk.pts, [1, 3], SLK)], ZK_EAVE, SLK, DK, texture=None, zlo=ZWK)
            zl = ZK_EAVE + SLK * (cx - hx - (xa - DK))
            z0c = round((zl - 2.4) / 0.2) * 0.2
            wr = wr + G.pocket_seat(wenv_, cx, cy, hx + 0.3, hy + 0.3, z0c) - box([cx - hx - 0.3, cy - hy - 0.3, z0c], [cx + hx + 0.3, cy + hy + 0.3, z0c + 200])
            zrw = ZK_EAVE + SLK * ((xb - xa) / 2 + DK)
            chim.append(N.chimney_paloma(w=2 * hx, d=2 * hy, h=round((zrw + 6.0 - z0c) / 0.2) * 0.2).translate([cx, cy, z0c]))
        kit.add(f"ROOF-{blk.name}", "Shingle", max(wr.decompose(), key=lambda m_: m_.volume()), group="roof")
        posts = list(np.linspace(1.6, Lc - 1.6, 5))
        lowers = union([p_.solid for p_ in kit.parts if p_.name.startswith("GALLERY-") and p_.name.endswith("-lower")])
        _corredor(kit, f"CORREDOR-{blk.name}", A, Lc, posts, ZWK, union(wk) + kenv + lowers, fnd)
        wing_walls.append(sw)
    for k, c in enumerate(chim):
        kit.add(f"CHIMNEY-{k}", "Limewash", c, key=f"CHIMNEY-paloma-{k}", group="roof")
    print("wings", round(time.time() - t0, 1))

    # --- the court: the garden wall and gate, the paving, the well
    gw = box([WL[1], YF + 2.0, 0.0], [WR[0], YF + 6.0, 26.0])
    gate = M.extrude(poly([(XC - 8.0, -1.0), (XC + 8.0, -1.0)] + [(XC + 8.0 * math.cos(a), 15.0 + 8.0 * math.sin(a)) for a in np.linspace(0, math.pi, 25)]), 10.0)
    gate = gate.transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, YF - 2.0], [0, 1.0, 0, 0]]))
    face = N.adobe_paloma(rect(0.0, 0.0, WR[0] - WL[1], 26.0) - poly([(XC - WL[1] - 8.6, -1), (XC - WL[1] + 8.6, -1)] +
                                                                     [(XC - WL[1] + 8.6 * math.cos(a), 15.0 + 8.6 * math.sin(a)) for a in np.linspace(0, math.pi, 25)]),
                          seed=13, dado=4.0)
    gw = gw + face.transform(np.array([[1.0, 0, 0, WL[1]], [0, 0, -1.0, YF + 2.0], [0, 1.0, 0, 0]]))
    arch = M.extrude(poly([(XC + 9.6 * math.cos(a), 15.0 + 9.6 * math.sin(a)) for a in np.linspace(0, math.pi, 25)] +
                          [(XC - 8.0 * math.cos(a), 15.0 + 8.0 * math.sin(a)) for a in np.linspace(0, math.pi, 25)]), 0.8)
    gw = gw + arch.transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, YF + 1.2], [0, 1.0, 0, 0]]))
    gw = gw - gate
    tiles = [M.cylinder(WR[0] - WL[1], 1.0, 1.0, 16).rotate([0, 90, 0]).translate([WL[1], y, 26.0]) for y in (YF + 3.0, YF + 5.0)]
    tiles.append(M.cylinder(WR[0] - WL[1], 0.9, 0.9, 16).rotate([0, 90, 0]).translate([WL[1], YF + 4.0, 26.9]))
    cop = union(tiles) ^ box([WL[1], YF + 1.5, 25.99], [WR[0], YF + 6.5, 28.0])
    gwall = gw + cop - wings_env - union(wing_walls) - fnd
    kit.add("GARDEN-WALL", "Limewash", gwall, group="stoop", change=(26.0, "Terracotta"),
            render=[("Limewash", gwall ^ box([-1e4, -1e4, -1], [1e4, 1e4, 26.05])), ("Terracotta", gwall - box([-1e4, -1e4, -1], [1e4, 1e4, 26.05]))])
    pave = box([WL[1] + DC + 0.6, YF + 6.0, 0.0], [WR[0] - DC - 0.6, Y0 - GD, 0.6])
    rng = np.random.default_rng(4)
    joints = []
    y = YF + 6.0
    while y < Y0 - GD:
        h = rng.uniform(3.0, 5.0)
        joints.append(box([0, y - 0.15, 0.3], [400, y + 0.15, 1.0]))
        x = WL[1] + DC + rng.uniform(0, 4)
        while x < WR[0] - DC:
            joints.append(box([x - 0.15, y, 0.3], [x + 0.15, y + h, 1.0]))
            x += rng.uniform(3.0, 6.0)
        y += h
    pave = pave - union(joints)
    wc = (XC, 76.0)
    pave = pave - M.cylinder(2.0, 5.2, 5.2, 40).translate([wc[0], wc[1], -0.5])
    kit.add("COURT", "Sandstone", pave, group="foundation")
    well = M.cylinder(5.0, 5.0, 5.0, 40) - M.cylinder(6.0, 3.6, 3.6, 40).translate([0, 0, 1.0])
    for k, a in enumerate(np.linspace(0, 2 * math.pi, 14, endpoint=False)):
        well = well - box([-0.15, 3.0, 1.2 + (k % 2) * 1.6], [0.15, 6.0, 5.5]).rotate([0, 0, math.degrees(a)])
    well = well + M.cylinder(0.8, 5.3, 5.0, 40).translate([0, 0, 4.99]) - M.cylinder(2.0, 3.6, 3.6, 40).translate([0, 0, 4.5])
    for sg in (-1, 1):
        well = well + box([sg * 4.3 - 0.7, -0.7, 5.6], [sg * 4.3 + 0.7, 0.7, 16.0])
    well = well + box([-5.4, -0.7, 15.99], [5.4, 0.7, 17.2]) + M.cylinder(6.0, 0.7, 0.7, 16).rotate([0, 90, 0]).translate([-3.0, 0, 13.0])
    well = well + (M.cylinder(2.0, 1.1, 1.2, 16) - M.cylinder(2.0, 0.8, 0.9, 16).translate([0, 0, 0.4])).translate([3.6, 3.0, 5.79])
    kit.add("WELL", "Sandstone", well.translate([wc[0], wc[1], 0.0]), group="stoop")
    print("court", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "paloma")
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
    kit.render_npz(os.path.join(OUT, "paloma.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
