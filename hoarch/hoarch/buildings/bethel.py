"""The Bethel Grove cottages: three original HO-scale (1:87.1) camp-meeting cottages round a
little green; house 105, of the new-layouts batch (hoarch.novel2), after the cottages of the
Wesleyan Grove camp ground at Oak Bluffs, Martha's Vineyard (1860s-70s).

The camp meetings' tents turned into cottages: tall, narrow and close together, each a steep
front gable a storey and a half high, Gothic double doors under a pointed arch on the ground
floor, a pointed door above opening onto a balcony over the porch, a trefoil light in the
peak, the gable edged in deep jigsaw lace, and each painted in its own bright colours. These
three stand on an arc facing a shared green, a planked boardwalk following the arc in front of
them, and each has its own siding, lace, railing and side:

- A (lavender): board and batten; a lace bargeboard pierced with roundels and hung with drops;
  railings of sawn balusters with hearts; a one-storey ell on its outer side.
- B (teal): narrow clapboards; a bargeboard of pierced hearts with a pointed edge; railings of
  crossed sticks with rings; a two-tier porch whose upper tier has its own little gable.
- C (coral): clapboards banded with diamond shingles; a fringe of teardrops for a bargeboard;
  railings of pierced tulip panels; a canted bay on its outer side.
- Storey joint (each in its own colours): a frieze of hanging pennants, a course of spools, a
  torus. Eave: spools and a cavetto.

usage: python3 -m hoarch.buildings.bethel [check] [export]
"""
import json
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, circle, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, gables as G, novel2 as N, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells, wall_shell

NAME = "The Bethel Grove Cottages"
COLORS = {"Lavender": "#B39BC8", "Teal": "#3E8C89", "Coral": "#E07A5F", "White": "#F4F1EA", "Cream": "#F1E3BC",
          "Rose": "#C96F8E", "Lime": "#B3C46A", "Gold": "#D9A93E", "Shingle": "#5E6367", "Brick": "#8A4434",
          "Planks": "#7A5C40", "Windows_Doors": "#F4F1EA"}
RENDER_MAT = {"Lavender": "lav", "Teal": "teal", "Coral": "coral", "White": "trim", "Cream": "cream", "Rose": "rose",
              "Lime": "lime", "Gold": "gold", "Shingle": "roof", "Brick": "brick", "Planks": "planks",
              "Windows_Doors": "trim", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"lav": ["#B39BC8", 0.75, 0.0], "teal": ["#3E8C89", 0.75, 0.0], "coral": ["#E07A5F", 0.75, 0.0],
           "trim": ["#F4F1EA", 0.6, 0.0], "cream": ["#F1E3BC", 0.6, 0.0], "rose": ["#C96F8E", 0.6, 0.0],
           "lime": ["#B3C46A", 0.6, 0.0], "gold": ["#D9A93E", 0.55, 0.0], "roof": ["#5E6367", 0.75, 0.0],
           "brick": ["#8A4434", 0.85, 0.0], "planks": ["#7A5C40", 0.75, 0.0], "sash": ["#F4F1EA", 0.5, 0.0],
           "door": ["#C96F8E", 0.45, 0.0]}
VIEWS = {"hero": [-30, 14, 70, 0.9, [0, 0, -10]], "hero_right": [32, 14, 70, 0.9, [0, 0, -10]],
         "front": [0, 6, 85, 0.92, [0, 0, 0]], "rear": [160, 18, 70, 0.92, [0, 0, -10]],
         "gables": [-6, 10, 85, None, [124, 40, 70], 230], "green": [-10, 38, 60, 1.0, [0, 0, 0]]}

LEDGE = 1.4
# each cottage's colours: walls, trim, accent (its doors and lace take the accent)
SCHEMES = {"A": dict(wall="Lavender", trim="White", acc="Rose", skin="bb", barge="a", rail="a", side="ell"),
           "B": dict(wall="Teal", trim="Cream", acc="Coral", skin="clap", barge="b", rail="b", side="tiers"),
           "C": dict(wall="Coral", trim="White", acc="Lime", skin="bands", barge="c", rail="c", side="bay")}


def _joint(sc):
    return dict(pitch=10.0, margin=3.0, layers=[
        dict(kind="frieze", h=3.6, b=1.2, orn="btpennant", role=sc["acc"]),
        dict(kind="course", h=1.4, b=1.2, orn="btspool", role=sc["trim"]),
        dict(kind="crown", h=1.8, b=1.2, P=3.0, orn="torus", role=sc["trim"])])


def _eave(sc):
    return dict(pitch=10.0, margin=3.0, layers=[
        dict(kind="course", h=1.4, b=1.2, orn="btspool", role=sc["acc"]),
        dict(kind="crown", h=2.2, b=1.2, P=4.2, orn="cavetto", role=sc["trim"])])


JOINTS = {k: _joint(v) for k, v in SCHEMES.items()}
EAVES = {k: _eave(v) for k, v in SCHEMES.items()}
RJ = round((LEDGE + 0.4 + CO.band_height(JOINTS["A"])) / 0.2) * 0.2
HE = CO.band_height(EAVES["A"])

# ------------------------------------------------------------------ one cottage, in its own frame
W, D = 46.0, 84.0
X0, X1 = -W / 2, W / 2
ZF = 6.0
S1 = ZF + 34.0
ZU = S1 + RJ
ZE = ZU + 6.0                                  # a knee wall under the eave: the upper floor is in the roof
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.2
Z_EAVE = ZW + FASCIA
S_R, D_EAVE, RAKE = 1.7, 3.0, 3.6                 # steep, as the camp ground's are
PD = 14.0                                      # the porch's depth
V1 = 6.0
# the arc: centre of the green, radius, and each cottage's angle (degrees from +x)
GC, GR = (124.0, -44.0), 134.0
ANG = {"A": 118.0, "B": 90.0, "C": 62.0}


def _frame(k):
    """World transform (3x4) of cottage k's frame: its front (-y) faces the green."""
    th = math.radians(ANG[k])
    ph = th - math.pi / 2
    px, py = GC[0] + GR * math.cos(th), GC[1] + GR * math.sin(th)
    return np.array([[math.cos(ph), -math.sin(ph), 0, px], [math.sin(ph), math.cos(ph), 0, py], [0, 0, 1.0, 0]])


def _m44(A):
    return np.vstack([A, [0, 0, 0, 1.0]])


def _skinfn(kind, blk):
    def fn(f, b, reg):
        reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
        if b.name.startswith("ell") or b.name.startswith("bay"):
            reg = reg - rect(-1, b.z1 - b.z0 - 6.0, f.L + 1, 999)
        lo = reg ^ rect(-1, -100, f.L + 1, S1 - b.z0)
        hi = reg ^ rect(-1, ZU - b.z0, f.L + 1, 999)
        out = []
        sk = {"bb": N.bb_bethel, "clap": N.clap_bethel, "bands": N.bands_bethel}[kind]
        for r_, dt in ((lo, 0.0), (hi, ZU - b.z0)):
            if not r_.is_empty():
                out.append(sk(r_, datum=dt))
        return union(out) if out else M()
    return fn


def _plan(k):
    """Cottage k's blocks and openings, in its own frame."""
    sc = SCHEMES[k]
    MAIN = Block(f"main{k}", [(X0, 0.0), (X1, 0.0), (X1, D), (X0, D)], ZF, ZW)
    side = None
    if sc["side"] == "ell":
        side = Block(f"ell{k}", [(X0 - 22.0, 28.0), (X0, 28.0), (X0, 70.0), (X0 - 22.0, 70.0)], ZF, ZF + 28.0)
    elif sc["side"] == "bay":
        side = Block(f"bay{k}", [(X1, 30.0), (X1 + 6.0, 34.0), (X1 + 6.0, 50.0), (X1, 54.0)], ZF, ZF + 26.0)
    L1, L2, LS = [], [], []
    fams = {}

    def add(L, blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        L[-1].fam = fams.setdefault(id(sp), name)

    pw = N.window_btpointed(w=6.0, h=16.0)
    add(L1, MAIN, 0.0, 0.0, 0.4, N.door_btdouble(w=12.0, h=24.0), "door", "door")
    for x in (-15.0, 15.0):
        add(L1, MAIN, x, 0.0, V1, pw, f"S{x:+.0f}")
    add(L2, MAIN, 0.0, 0.0, ZU - ZF + 0.4, N.door_btdouble(w=8.4, h=19.0, A=0.8), "balcony-door", "door")
    for y in (14.0, 62.0):
        if not (sc["side"] == "ell" and 26.0 < y < 72.0):
            add(L1, MAIN, X0, y, V1, pw, f"W{y:.0f}")
        if not (sc["side"] == "bay" and 28.0 < y < 56.0):
            add(L1, MAIN, X1, y, V1, pw, f"E{y:.0f}")
    add(L1, MAIN, 10.0, D, 0.4, N.door_btdouble(w=7.6, h=21.0, A=0.8), "back-door", "door")
    add(L1, MAIN, -12.0, D, V1, pw, "N-12")
    add(L2, MAIN, 0.0, D, ZW - ZF + 6.0, N.window_btpointed(w=5.0, h=13.0, label=False), "back-gable")
    # the peak light: kept clear of the bargeboard's lace and the balcony door's head; on B it
    # is in the gable run forward over the upper porch
    if sc["side"] == "tiers":
        tb = Block(f"tier{k}", [(X0, -PD), (X1, -PD), (X1, 0.0), (X0, 0.0)], ZF, ZW)
        add(LS, tb, 0.0, -PD, ZW - ZF + 16.5, N.window_bttrefoil(r=3.0), "peak")
    else:
        add(L2, MAIN, 0.0, 0.0, ZW - ZF + 16.5, N.window_bttrefoil(r=3.0), "peak")
    if sc["side"] == "ell":
        add(LS, side, X0 - 22.0, 49.0, V1, pw, "ell-W")
        add(LS, side, X0 - 11.0, 28.0, V1, pw, "ell-S")
    if sc["side"] == "bay":
        add(LS, side, X1 + 6.0, 42.0, V1, N.window_btpointed(w=6.0, h=14.0, label=False), "bay-E")
    return MAIN, side, L1, L2, LS


PLANS = {k: _plan(k) for k in SCHEMES}


def _door_env(o, grow=0.4, out=8.0):
    """The room an opening's casing takes, as a solid (for cutting bands back from it)."""
    cs = o.cs_on_facade(o.spec["landing"]).offset(grow)
    return o.facade.place(M.extrude(cs, out + 4.0).translate([0.0, 0.0, -4.0]))


def _ring_env(rings):
    return union([r["solid"] for r in rings])


def _cottage(kit, k):
    """Add cottage k's parts to ``kit`` in its own frame (the caller moves them onto the arc)."""
    sc = SCHEMES[k]
    MAIN, side, L1, L2, LS = PLANS[k]
    tiers = sc["side"] == "tiers"
    ops_main = L1 + L2
    bdoor = next(o for o in L2 if o.name == "balcony-door")
    benv = _door_env(bdoor)

    # the roof, its gable walls (front and back); B's runs forward over the upper porch
    rpts = [(X0, -PD), (X1, -PD), (X1, D), (X0, D)] if tiers else MAIN.pts
    y_f = rpts[0][1]
    gdefs = [dict(p0=(X0, y_f), p1=(X1, y_f), slope=S_R, e=0.3), dict(p0=(X1, D), p1=(X0, D), slope=S_R, e=0.3)]
    rf = G.gabled_roof([(rpts, [1, 3], S_R)], Z_EAVE, D_EAVE, gdefs, texture="square", tex_kw=dict(pitch=1.4, wtab=2.0, d=0.35),
                       skin=1.6, rake=RAKE, inner_cs=offset(poly(rpts), -3.0), fascia=FASCIA, hollow=2.4)
    gables = [(MAIN, 0, rf["walls"][0]["cs"].translate((0.0, Z_EAVE - MAIN.z0))),
              (MAIN, 2, rf["walls"][1]["cs"].translate((0.0, Z_EAVE - MAIN.z0)))]
    side_env = side.solid(grow=0.15, dz0=-10, dz1=40) if side is not None else None
    undress = [slab(offset(MAIN.cs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)] + ([side.solid(grow=6.0, dz0=-10, dz1=8)] if side is not None else [])
    st = stacked_shells([MAIN], ops_main, [S1], t=2.6, corners="none", siding=_skinfn(sc["skin"], MAIN), clear=[lip_keep(MAIN.cs, 2.6, ZF, 1.2)],
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress, gables=gables)
    kit.add(f"{k}-WALLS-1", sc["wall"], st["shells"][0], group="walls")
    kit.add(f"{k}-JOINT", sc["wall"], st["rings"][0], group="walls")
    # the balcony door rises through the eave line into the gable: the ledge, the lip and the
    # eave cornice stop at its casing
    lip = _corbel(MAIN.cs, 2.6, ZW) + lip_ring(MAIN.cs, 2.6, ZW)
    w2 = st["shells"][1] + ((lip + CO.ledge(MAIN.pts, ZE, LEDGE, t=2.6)) - benv)
    if tiers:                                          # the front gable is inside the roof run forward: trim it to the roof's underside
        w2 = w2 - (rf["body"] + rf["skins"])
    kit.add(f"{k}-WALLS-2", sc["wall"], w2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINTS[k], cut=(side_env or M()))
    CO.add_level(kit, rings, f"{k}-CORNICE-J", "cornice")
    jenv = _ring_env(rings)
    y_j = jenv.bounding_box()[1]                       # how far the joint cornice stands out in front
    erings, _ = CO.level(MAIN.pts, ZE, EAVES[k], t=2.6, cut=benv)
    CO.add_level(kit, erings, f"{k}-CORNICE-E", "cornice")
    eenv = _ring_env(erings)
    keep = []
    for o in ops_main + LS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        part = kit.add(f"{k}-{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{o.fam}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                       group="inserts", render=zones)
        keep.append(part.solid)
    # the roof, its ridge roll, the lace on both gables, the chimney
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_R * (W / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((0.0, y_f - RAKE), (0.0, D + RAKE), zr, S_R, ZW, half=1.1, up=0.6) - walls_env)
    senv, _ = R.hip_roof([(MAIN.pts, [1, 3], S_R)], Z_EAVE, S_R, D_EAVE, texture=None, zlo=ZW)
    cx, cy = 0.0, D - 16.0
    z0c = round((Z_EAVE + S_R * (W / 2 - 3.4 + D_EAVE) - 2.4) / 0.2) * 0.2
    roof = roof + G.pocket_seat(senv, cx, cy, 3.4, 2.8, z0c)
    roof = roof - box([cx - 3.4, cy - 2.8, z0c], [cx + 3.4, cy + 2.8, z0c + 100]) - lip_keep(MAIN.cs, 2.6, ZW)
    kit.add(f"{k}-ROOF", "Shingle", roof, group="roof")
    ch = box([-3.0, -2.4, 0.0], [3.0, 2.4, zr + 8.0 - z0c]) + box([-3.8, -3.2, zr + 6.0 - z0c], [3.8, 3.2, zr + 8.0 - z0c]) - \
        box([-1.8, -1.2, zr + 6.8 - z0c], [1.8, 1.2, zr + 9.0 - z0c])
    kit.add(f"{k}-CHIMNEY", "Brick", ch.translate([cx, cy, z0c]), group="roof")
    for j, wl in enumerate(rf["walls"]):
        bg = N.barge_bethel(wl["L"], wl["slope"], D_EAVE, kind=sc["barge"], skin=1.6, tab=RAKE - 0.6)
        fw = wl["facade"]
        A = fw.A.copy()
        A[:, 3] = fw.world(0.0, 0.0, RAKE)
        bw = bg.transform(A) - roof - eenv
        bw = max(bw.decompose(), key=lambda m_: m_.volume())
        kit.add(f"{k}-BARGE-{j}", sc["acc"], bw, P=inv34(A), key=f"{k}-BARGE", group="roof")
    # the base: brick piers with lattice between
    fnd = foundation([MAIN] + ([side] if side is not None else []), 0.0, ZF, style="brick")
    kit.add(f"{k}-FOUNDATION", "Brick", fnd, group="foundation")
    house_env = MAIN.solid(grow=0.15, dz0=-10, dz1=200)

    # the side: the ell (walls, eave, little gable roof facing front) or the bay (walls, a hip cap)
    if sc["side"] == "ell":
        sz = side.z1
        rf2 = G.gabled_roof([(side.pts, [1, 3], 1.1)], sz + 1.2, 2.6, [dict(p0=side.pts[0], p1=side.pts[1], slope=1.1, e=0.3),
                                                                       dict(p0=side.pts[2], p1=side.pts[3], slope=1.1, e=0.3)],
                            texture="square", tex_kw=dict(pitch=1.4, wtab=2.0, d=0.35), skin=1.4, rake=2.6,
                            inner_cs=offset(side.cs, -2.6), fascia=1.2, hollow=2.2)
        g2 = [(side, 0, rf2["walls"][0]["cs"].translate((0.0, sz + 1.2 - side.z0)))]
        sw = wall_shell([side], LS, t=2.6, belt=None, corners="none", water_table=False, siding=_skinfn(sc["skin"], side), gables=g2)
        sw = (sw - lip_keep(side.cs, 2.6, ZF, 1.2)) + (_corbel(side.cs, 2.6, sz) + lip_ring(side.cs, 2.6, sz))
        kit.add(f"{k}-ELL-WALLS", sc["wall"], max((sw - house_env).decompose(), key=lambda m_: m_.volume()), group="walls")
        r2 = rf2["body"] + rf2["tex"] + rf2["skins"] + rf2["skin_tex"] - house_env - lip_keep(side.cs, 2.6, sz)
        kit.add(f"{k}-ELL-ROOF", "Shingle", max(r2.decompose(), key=lambda m_: m_.volume()), group="roof")
        wl = rf2["walls"][0]
        bg = N.barge_bethel(wl["L"], wl["slope"], 2.6, kind=sc["barge"], skin=1.4, width=2.6, finial=4.0, tab=2.0)
        fw = wl["facade"]
        A = fw.A.copy()
        A[:, 3] = fw.world(0.0, 0.0, 2.6)
        bw = max((bg.transform(A) - r2 - house_env).decompose(), key=lambda m_: m_.volume())
        kit.add(f"{k}-ELL-BARGE", sc["acc"], bw, P=inv34(A), group="roof")
    if sc["side"] == "bay":
        sz = side.z1
        sw = wall_shell([side], LS, t=2.2, belt=None, corners="none", water_table=False, siding=_skinfn(sc["skin"], side))
        sw = sw - lip_keep(side.cs, 2.2, ZF, 1.2)
        kit.add(f"{k}-BAY-WALLS", sc["wall"], max((sw - house_env).decompose(), key=lambda m_: m_.volume()), group="walls")
        cap, _ = R.hip_roof([(side.pts, [1, 2, 3], 0.9)], sz + 1.0, 0.9, 2.0, texture="square", tex_kw=dict(pitch=1.3, wtab=1.8, d=0.3), zlo=sz)
        cap = cap - house_env
        kit.add(f"{k}-BAY-ROOF", "Shingle", max(cap.decompose(), key=lambda m_: m_.volume()), group="roof")

    # the porch: planked deck, a one-piece top whose roof is the balcony floor
    pts = [(X0, -PD), (X1, -PD), (X1, 0.0), (X0, 0.0)]
    runs = [dict(a=(X0, 0.0), b=(X0, -PD), posts=[PD - 1.6]),
            dict(a=(X0, -PD), b=(X1, -PD), posts=[1.6, W / 2 - 7.0, W / 2 + 7.0, W - 1.6]),
            dict(a=(X1, -PD), b=(X1, 0.0), posts=[1.6])]
    post_h = round((S1 - 1.0 - 2.4 - ZF) / 0.2) * 0.2
    P = FT.porch_turned(pts, runs, ZF, post_h, steps_at=[(1, W / 2, 12.0)], inset=1.6, rail="btsawn", beam=2.4, post="bethel",
                        arcade="btlace", skirt="btlattice", pier_tex="brick", roof_edge="btscallop", planks=dict(pitch=1.4, border=1.6),
                        drop=4.0, top=True)
    fkeep = slab(offset(MAIN.cs, 1.7), -1, ZF + 1.3)
    steps = []
    for sm, A in P["steps"]:                         # the steps run 1.2 into the deck, which is cut to fit them
        A2 = A.copy()
        A2[:, 3] = A[:, 3] + A[:, 2] * (-1.2)
        steps.append(sm.transform(A2))
    deck = P["deck"] - fkeep - fnd - union(steps)
    kit.add(f"{k}-PORCH-deck", sc["trim"], deck, P=print_flip(), group="porch", render=FT.plank_zones(deck, ZF, "Planks", sc["trim"]))
    ins_box = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2], [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                     for b in (s_.bounding_box() for s_ in keep)])
    bld = MAIN.solid(grow=1.45, dz0=-20, dz1=300)
    FT.add_porch_top(kit, f"{k}-PORCH", P, bld + ins_box, sc["trim"], sc["trim"], tin_col="Shingle", tin="flat", group="porch")
    parts = {p_.name: p_ for p_ in kit.parts}
    ptop = parts[f"{k}-PORCH-top"]
    zb = ptop.solid.bounding_box()[5]                     # the balcony floor
    for stp in steps:
        stp = stp - fkeep - fnd - ptop.solid
        STEP_Y[k] = min(STEP_Y.get(k, 0.0), stp.bounding_box()[1])
        kit.add(f"{k}-PORCH-steps", "Brick", stp, group="porch")
    # the balcony railings, in slots in the porch roof: the front and both sides, the sides
    # stopping short of the joint cornice (B's front runs between its upper posts)
    y_w = y_j - 0.4
    xr0, xr1 = (X0 + 1.6, X1 - 1.6) if tiers else (X0 + 0.6, X1 - 0.6)
    yf = -PD + (1.6 if tiers else 0.6)
    lines = [("W", ((xr0, y_w), (xr0, yf + (1.6 if tiers else 1.1))), (1, 0)),
             ("E", ((xr1, yf + (1.6 if tiers else 1.1)), (xr1, y_w)), (-1, 0))]
    lines.append(("front", ((X0 + 3.0, yf), (X1 - 3.0, yf)) if tiers else ((X0 + 0.6, yf), (X1 - 0.6, yf)), (0, 1)))
    rails = []
    for name, (a, b_), wdir in lines:
        a, b_ = np.array(a), np.array(b_)
        L = float(np.linalg.norm(b_ - a))
        uv = (b_ - a) / L
        A = np.array([[uv[0], 0.0, wdir[0], a[0]], [uv[1], 0.0, wdir[1], a[1]], [0.0, 1.0, 0.0, zb]])
        rs = N.rail_bethel(L, h=7.0, kind=sc["rail"], t=1.0).transform(A)
        rails.append(rs)
        kit.add(f"{k}-RAIL-{name}", sc["acc"], rs, P=inv34(A), group="porch")
    ptop.solid = ptop.solid - union(rails)
    if tiers:
        _upper_tier(kit, k, sc, zb, keep, rf, eenv + jenv, union(rails))
    return MAIN, side


def _upper_tier(kit, k, sc, zb, keep, rf, cornices, rails):
    """Cottage B's upper porch, under its gable run forward: two round posts on the balcony
    carry the beams the projecting gable stands on, lace under the front beam; the gable's
    face (its own part, in the wall colour and siding) is pierced by a cusped pointed arch
    with the trefoil over it."""
    from hoarch.grand import _lancet
    from hoarch.porchwork import POSTS
    zt = ZW
    ph = round((zt - 2.4 - zb) / 0.2) * 0.2 + 0.4               # into the beam
    post = POSTS["bethel"](ph, slot=None)
    yp = -PD + 1.6
    parts = [post.translate([x, yp, zb]) for x in (X0 + 1.6, X1 - 1.6)]
    parts.append(box([X0, -PD + 0.2, zt - 2.4], [X1, -PD + 2.4, zt]))                  # the front beam
    lace = N.spandrel_btlace(X0 + 3.0, X1 - 3.0, zt - 6.0, zt - 2.4 + 0.01)
    parts.append(M.extrude(lace, 1.2).transform([[1, 0, 0, 0], [0, 0, 1, -PD + 0.6], [0, 1, 0, 0]]))
    for x in (X0, X1 - 1.2):                                    # the side beams back to the wall
        parts.append(box([x, -PD + 0.2, zt - 2.4], [x + 1.2, -0.2, zt]))
    top = union(parts) - cornices - union(keep) - rails
    kit.add(f"{k}-TIER-top", sc["trim"], max(top.decompose(), key=lambda m_: m_.volume()), P=print_flip(), group="porch")
    # the projecting gable's face: the gable wall's outline, a cusped pointed arch over the
    # porch, the trefoil's opening; siding like the walls
    tb = PLANS[k][4][0]                                        # the peak light, on the tier's block
    f = tb.facade
    wl = rf["walls"][0]
    pcs = wl["cs"].translate((0.0, Z_EAVE - ZF))
    span, rise = 24.0, 14.0
    r = (rise * rise + span * span / 4) / span                  # an arch struck from the springings, apex rise over them
    arch = _lancet(W / 2 - span / 2, W / 2 + span / 2, ZW - ZF, v0=ZW - ZF - 1.0, r=r)
    cusp = []
    for t in np.linspace(0.08, 0.92, 9):
        th = math.pi * t
        cusp.append(circle((W / 2 - (span / 2) * math.cos(th), ZW - ZF + rise * math.sin(th) ** 0.8), 0.9, 14))
    arch = arch - cs_union(cusp)
    op = tb.cs_on_facade(tb.spec["cut"])
    face = pcs - arch - op
    fr = tb.cs_on_facade(tb.spec["landing"]).offset(0.3)
    sk = {"bb": N.bb_bethel, "clap": N.clap_bethel, "bands": N.bands_bethel}[sc["skin"]]
    reg = face - fr - rect(-1, -10, W + 1, ZW - ZF + 0.8)
    panel = M.extrude(face, 2.6).translate([0, 0, -2.6]) + sk(reg, datum=ZU - ZF).translate([0, 0, -0.02])
    A = f.A.copy()
    A[:, 3] = f.world(0.0, 0.0, 0.0)
    kit.add(f"{k}-GABLE", sc["wall"], panel.transform(A) - union(keep), P=inv34(A), group="roof")


STEP_Y = {}
MAIN_ENV = {}


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    for k in ("A", "B", "C"):
        MAIN_ENV[k] = box([X0 - 0.15, -0.15, -10], [X1 + 0.15, D + 0.15, 300])
        n0 = len(kit.parts)
        _cottage(kit, k)
        T = _frame(k)
        T44 = _m44(T)
        Ti = np.linalg.inv(T44)
        for p_ in kit.parts[n0:]:
            p_.solid = p_.solid.transform(T)
            p_.P = (_m44(p_.P) @ Ti)[:3]
            if p_.render:
                p_.render = [(c, s_.transform(T)) for c, s_ in p_.render]
        print("cottage", k, round(time.time() - t0, 1))
    # the boardwalk round the green, in three planked arcs (one in front of each cottage)
    rout = GR + min(STEP_Y.values()) - 0.5
    rin = rout - 14.0
    for j, (a0, a1) in enumerate(((104.1, 132.0), (76.1, 103.9), (48.0, 75.9))):
        pts_o = [(GC[0] + rout * math.cos(math.radians(a)), GC[1] + rout * math.sin(math.radians(a))) for a in np.linspace(a0, a1, 24)]
        pts_i = [(GC[0] + rin * math.cos(math.radians(a)), GC[1] + rin * math.sin(math.radians(a))) for a in np.linspace(a1, a0, 24)]
        cs = poly(pts_o + pts_i)
        slab_ = M.extrude(cs, 1.2)
        gaps = []
        for a in np.arange(a0 + 0.7, a1, 0.8):
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            gaps.append(M.hull_points([(GC[0] + r * ca + dx, GC[1] + r * sa + dy, z) for r in (rin - 1, rout + 1) for z in (0.8, 2.0)
                                       for dx, dy in ((-0.25 * sa, 0.25 * ca), (0.25 * sa, -0.25 * ca))]))
        kit.add(f"BOARDWALK-{j}", "Planks", slab_ - union(gaps), group="foundation")
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


def _world():
    """The three cottages' blocks and openings on the arc (for the audit)."""
    blocks, ops = [], []
    for k, (MAIN, side, L1, L2, LS) in PLANS.items():
        T = _frame(k)
        wb = {}
        for b in [MAIN] + ([side] if side is not None else []) + [o.block for o in LS]:
            if id(b) not in wb:
                wb[id(b)] = Block(b.name, [tuple((T @ [x, y, 0.0, 1.0])[:2]) for x, y in b.pts], b.z0, b.z1)
                blocks.append(wb[id(b)])
        ops += [Opening(wb[id(o.block)], o.edge, o.u, o.v0, o.spec, o.name, o.kind) for o in L1 + L2 + LS]
    return blocks, ops


BLOCKS, OPENINGS = _world()


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "bethel")
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
    kit.render_npz(os.path.join(OUT, "bethel.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
