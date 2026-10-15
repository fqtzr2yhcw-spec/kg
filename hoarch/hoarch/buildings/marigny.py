"""The Marigny: an original HO-scale (1:87.1) New Orleans camelback shotgun double; house 107, of
the new-layouts batch (hoarch.novel2), after the camelback doubles of the Faubourg Marigny and
Bywater (1880s-90s).

Its section is the new thing: one storey at the street and two at the back. The front house,
two dwellings side by side each one room wide and five deep, sits under a hipped roof of 5V
crimped tin; behind, the "camelback" rises a full second storey under its own higher hip (built
so, the house was taxed as one storey). The double front: a door, two floor-length windows and
a door, every one under an Italianate hood on scroll consoles, the windows with louvered
shutters, behind a deep gallery on four Eastlake turned columns with a spindle frieze and fan
brackets, turned balusters and two flights of steps; the street front's boards channelled like
dressed stone with wooden quoins, the sides in bevelled weatherboard. A heavy bracketed
cornice (paired scroll consoles, rosette panels, a guilloche) runs round the whole ground
storey: the front house's eave and the camel's belt. Up on brick piers with diagonal-slat
skirts between; a back gallery under the camel.

usage: python3 -m hoarch.buildings.marigny [check] [export]
"""
import json
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, gables as G, novel2 as N, openings as O, roof as R
from hoarch.colonial import shutters_pair
from hoarch.kit import Kit, print_flip
from hoarch.ornament import chamfer_box
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Marigny"
COLORS = {"Peach": "#E9B68C", "Cream": "#F4ECD8", "Oxblood": "#6E2C2A", "Bayou": "#2F5B4D", "Slate": "#4E555C",
          "Tin": "#A3A9AD", "Brick": "#8E4632", "Deck": "#7E8581", "Windows_Doors": "#F4ECD8"}
RENDER_MAT = {"Peach": "siding", "Cream": "trim", "Oxblood": "accent", "Bayou": "shutter", "Slate": "roof", "Tin": "tin",
              "Brick": "brick", "Deck": "deck", "Windows_Doors": "trim", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"siding": ["#E9B68C", 0.8, 0.0], "trim": ["#F4ECD8", 0.6, 0.0], "accent": ["#6E2C2A", 0.6, 0.0],
           "shutter": ["#2F5B4D", 0.6, 0.0], "roof": ["#4E555C", 0.55, 0.3], "tin": ["#A3A9AD", 0.45, 0.35],
           "brick": ["#8E4632", 0.85, 0.0], "deck": ["#7E8581", 0.75, 0.0], "sash": ["#F4ECD8", 0.5, 0.0],
           "door": ["#2F5B4D", 0.45, 0.0]}
VIEWS = {"hero": [-32, 16, 70, 0.9, [0, 0, -10]], "hero_right": [34, 16, 70, 0.9, [0, 0, -10]],
         "front": [0, 6, 85, 0.92, [0, 0, 0]], "rear": [158, 20, 70, 0.92, [0, 0, -10]],
         "gallery": [-14, 8, 85, None, [114, 30, 30], 170], "camel": [70, 14, 75, None, [174, 190, 60], 260]}

LEDGE = 1.4
JOINT = dict(pitch=15.0, margin=5.0, pair=2.6, layers=[
    dict(kind="frieze", h=4.2, b=1.2, orn="mgpanels", role="Oxblood", half=1.1),
    dict(kind="course", h=1.4, b=1.2, orn="mgguilloche", role="Cream"),
    dict(kind="bed", h=2.4, b=1.4, P=4.6, role="Cream", brackets=dict(style="mgscroll", t=1.6)),
    dict(kind="crown", h=2.2, b=1.4, P=5.2, orn="cyma", role="Cream")])
EAVE = dict(pitch=11.0, margin=4.0, layers=[
    dict(kind="frieze", h=3.4, b=1.2, orn="mgsunburst", role="Bayou", half=1.1),
    dict(kind="bed", h=2.0, b=1.4, P=3.8, role="Cream", brackets=dict(style="mgscroll", t=1.6)),
    dict(kind="crown", h=2.0, b=1.4, P=4.4, orn="cyma", role="Cream")])
HJ = CO.band_height(JOINT)
HE = CO.band_height(EAVE)

T = 3.0
X0, X1 = 54.0, 174.0                              # 120 wide: two dwellings of 17 ft
XC = (X0 + X1) / 2
YG, Y0, YC, Y1 = 22.0, 42.0, 150.0, 228.0         # the gallery's front, the front wall, the camel's front, the back
ZF = 12.0                                         # up on piers
ZE1 = ZF + 37.0                                   # the great cornice's foot
ZW1 = round((ZE1 + HJ) / 0.2) * 0.2               # the ground storey's top
S1 = ZW1                                          # (the storey joint, for the audit)
RJ = 0.0
FASCIA = 1.4
Z_EAVE1 = ZW1 + FASCIA
ZE2 = ZW1 + 33.0                                  # the camel's eave cornice
ZW2 = round((ZE2 + HE) / 0.2) * 0.2
ZE = ZE2
Z_EAVE2 = ZW2 + FASCIA
S1R, S2R = 0.45, 0.6
D_EAVE1, D_EAVE2 = 5.6, 4.8
LOW = Block("main", [(X0, Y0), (X1, Y0), (X1, Y1), (X0, Y1)], ZF, ZW1)
CAMEL = Block("camel", [(X0, YC), (X1, YC), (X1, Y1), (X0, Y1)], ZW1, ZW2)
FPTS = [(X0, Y0), (X1, Y0), (X1, YC), (X0, YC)]
V_SIDE = 6.0


def _roof_z(x):
    """The front roof's top over the camel's front wall at x (its side planes)."""
    d = min(x - (X0 - D_EAVE1), (X1 + D_EAVE1) - x)
    return Z_EAVE1 + S1R * d


def _openings():
    L1, L2 = [], []
    fams = {}
    shut = set()

    def add(L, blk, x, y, v0, sp, name, kind="window", sh=False):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        L[-1].fam = fams.setdefault(id(sp), name)
        if sh:
            shut.add(name)

    door, floor_w = N.door_mgfront(w=10.0), N.window_mgfloor(w=10.0)
    side, up, back = N.window_mgside(), N.window_mgupper(h=13.0), N.door_mgback()
    # the double front: door, floor-length window, window, door
    add(L1, LOW, X0 + 12.0, Y0, 0.0, door, "door-W", "door")
    add(L1, LOW, X0 + 37.0, Y0, 0.4, floor_w, "S-W", sh=True)
    add(L1, LOW, X1 - 37.0, Y0, 0.4, floor_w, "S-E", sh=True)
    add(L1, LOW, X1 - 12.0, Y0, 0.0, door, "door-E", "door")
    # the long sides: a window to each room
    for y in (64.0, 96.0, 128.0, 172.0, 206.0):
        add(L1, LOW, X0, y, V_SIDE, side, f"W{y:.0f}")
        add(L1, LOW, X1, y, V_SIDE, side, f"E{y:.0f}")
    # the back: a door and a window for each dwelling, onto the back gallery
    for x, nm in ((X0 + 16.0, "W"), (X1 - 16.0, "E")):
        add(L1, LOW, x, Y1, 0.0, back, f"back-door-{nm}", "door")
    for x in (X0 + 40.0, X1 - 40.0):
        add(L1, LOW, x, Y1, V_SIDE, side, f"N{x:.0f}-1")
    # the camel: two lights over the front roof, two each side, two at the back
    for x in (X0 + 15.0, X1 - 15.0):
        v0 = round((max(_roof_z(x - 6.5), _roof_z(x + 6.5)) + 2.6 - ZW1) / 0.2) * 0.2     # its sill clear of the roof
        add(L2, CAMEL, x, YC, v0, up, f"camel-S{x:.0f}")
    for y in (YC + 20.0, YC + 56.0):
        add(L2, CAMEL, X0, y, 8.0, up, f"camel-W{y:.0f}")
        add(L2, CAMEL, X1, y, 8.0, up, f"camel-E{y:.0f}")
    for x in (X0 + 28.0, X1 - 28.0):
        add(L2, CAMEL, x, Y1, 8.0, up, f"camel-N{x:.0f}")
    return L1, L2, shut


OPEN1, OPEN2, SHUTTERED = _openings()
OPENINGS = OPEN1 + OPEN2
BLOCKS = [LOW, CAMEL]


def _skin(f, b, reg):
    """The street front channelled like stone with wooden quoins; elsewhere weatherboard; all
    kept clear of the cornices' bands."""
    ze, zw = (ZE1, ZW1) if b is LOW else (ZE2, ZW2)
    reg = reg - rect(-1, ze - LEDGE - 0.6 - b.z0, f.L + 1, zw - b.z0 + 0.2)
    if reg.is_empty():
        return M()
    if b is LOW and f.n[1] < -0.5:
        body = reg - rect(-1, -1, 3.2, 999) - rect(f.L - 3.2, -1, f.L + 1, 999)
        out = N.rustic_marigny(body, datum=0.0)
        k, v = 0, 0.0
        H = reg.bounds()[3]
        while v < H - 1.0:                                       # quoins: long and short in turn
            top = min(v + 2.6 - 0.45, H)
            for a, c_ in ((0.0, 3.0 if k % 2 == 0 else 2.0), (f.L - (3.0 if k % 2 == 0 else 2.0), f.L)):
                q = rect(a, v, c_, top) ^ reg
                if not q.is_empty():
                    out = out + chamfer_box(*q.bounds(), 0.0, 0.55, c=0.2, bottom=0.55)
            v += 2.6
            k += 1
        return out
    return N.lap_marigny(reg, datum=0.0)


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
            left, right = shutters_pair(w_op, h_op, casing=1.2, gap=0.5, h=round((h_op - 3.2) / 0.2) * 0.2,
                                        make=N.shutter_marigny)              # (under the hood's consoles)
            for side, m in (("L", left), ("R", right)):
                kit.add(f"SHUTTER-{o.name}-{side}", "Bayou", m.translate([0, 0, 0.45]).transform(A), P=inv34(A),
                        key="SHUTTER-marigny", group="shutters")


def _gallery(kit, name, pts, runs, steps_at, post_h, drop, fnd, keep, bld):
    """A gallery the pink-house way: planked deck on piers with slatted skirts, a one-piece top
    (flat tin roof, beam, spindle frieze, columns, balusters) printed upside down."""
    P = FT.porch_turned(pts, runs, ZF, post_h, steps_at=steps_at, inset=1.6, rail="marigny", beam=2.6, post="marigny",
                        arcade="mgspindle", skirt="mgslats", pier_tex="brick", roof_edge="mgmodillion",
                        planks=dict(pitch=1.4, border=1.6), drop=drop, top=True)
    fkeep = slab(offset(LOW.cs, 1.7), -1, ZF + 1.3)
    steps = []
    for sm, A in P["steps"]:                         # the steps run 1.2 into the deck, which is cut to fit them
        A2 = A.copy()
        A2[:, 3] = A[:, 3] + A[:, 2] * (-1.2)
        steps.append(sm.transform(A2))
    deck = P["deck"] - fkeep - fnd - union(steps)
    kit.add(f"{name}-deck", "Cream", deck, P=print_flip(), group="porch", render=FT.plank_zones(deck, ZF, "Deck", "Cream"))
    ins_box = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2], [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                     for b in (s_.bounding_box() for s_ in keep)])
    FT.add_porch_top(kit, name, P, bld + ins_box, "Cream", "Cream", tin_col="Tin", tin="flat", group="porch")
    top = [p_ for p_ in kit.parts if p_.name == f"{name}-top"][0]
    for k, sw in enumerate(steps):
        kit.add(f"{name}-steps-{k}", "Brick", sw - fkeep - fnd - top.solid, key=f"{name}-steps", group="porch")


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()

    # --- the roofs first (the camel's siding keeps clear of the front one)
    rf = G.gabled_roof([(FPTS, [0, 1, 3], S1R)], Z_EAVE1, D_EAVE1, [], texture="crimp", tex_kw=dict(seam_pitch=3.4, d=0.3),
                       skin=1.6, inner_cs=offset(poly(FPTS), -3.0), fascia=FASCIA, hollow=2.4)
    froof = rf["body"] + rf["tex"]
    rc = G.gabled_roof([(CAMEL.pts, [0, 1, 2, 3], S2R)], Z_EAVE2, D_EAVE2, [], texture="crimp", tex_kw=dict(seam_pitch=3.4, d=0.3),
                       skin=1.6, inner_cs=offset(CAMEL.cs, -3.0), fascia=FASCIA, hollow=2.4)
    croof = rc["body"] + rc["tex"]
    camel_env = CAMEL.solid(grow=0.15, dz0=-0.2, dz1=0.0)

    # --- the ground storey: one shell, a cross wall under the camel's front, the great cornice
    band1 = slab(offset(LOW.cs, 9.0), ZE1 - LEDGE - 0.6, ZW1 + 0.01)
    w1 = wall_shell([LOW], OPEN1, t=T, belt=None, corners="none", water_table=False, siding=_skin, undress=[band1],
                    partitions=[((X0, YC + 1.5), (X1, YC + 1.5), 2.0, ZF, ZW1)])
    w1 = w1 + CO.ledge(LOW.pts, ZE1, LEDGE, t=T) + _corbel(LOW.cs, T, ZW1) + lip_ring(LOW.cs, T, ZW1)
    kit.add("WALLS-1", "Peach", w1, group="walls")
    jr, _ = CO.level(LOW.pts, ZE1, JOINT, t=T)
    CO.add_level(kit, jr, "CORNICE-J", "cornice")
    # --- the camel: its own shell on the ground storey's top, the eave cornice
    band2 = slab(offset(CAMEL.cs, 9.0), ZE2 - LEDGE - 0.6, ZW2 + 0.01)
    w2 = wall_shell([CAMEL], OPEN2, t=T, belt=None, corners="none", water_table=False, siding=_skin, undress=[band2, froof])
    w2 = w2 + CO.ledge(CAMEL.pts, ZE2, LEDGE, t=T) + _corbel(CAMEL.cs, T, ZW2) + lip_ring(CAMEL.cs, T, ZW2)
    kit.add("WALLS-2", "Peach", w2 - froof, group="walls")
    er, _ = CO.level(CAMEL.pts, ZE2, EAVE, t=T)
    CO.add_level(kit, er, "CORNICE-E", "cornice")
    keep = []
    _place_inserts(kit, OPENINGS, keep)
    print("walls", round(time.time() - t0, 1))

    # --- the roofs: hip ridges capped, chimneys in pockets (two on the front house, one on the camel)
    zr1 = Z_EAVE1 + S1R * ((X1 - X0) / 2 + D_EAVE1)
    froof = froof + G.ridge_cap((XC, Y0 + (X1 - X0) / 2), (XC, YC - 0.2), zr1, S1R, ZW1, half=1.0, up=0.5)
    froof = froof - lip_keep(LOW.cs, T, ZW1) - camel_env
    zr2 = Z_EAVE2 + S2R * ((Y1 - YC) / 2 + D_EAVE2)
    yr = (YC + Y1) / 2
    croof = croof + G.ridge_cap((X0 + (Y1 - YC) / 2, yr), (X1 - (Y1 - YC) / 2, yr), zr2, S2R, ZW2, half=1.0, up=0.5)
    croof = croof - lip_keep(CAMEL.cs, T, ZW2)
    fenv, _ = R.hip_roof([(FPTS, [0, 1, 3], S1R)], Z_EAVE1, S1R, D_EAVE1, texture=None, zlo=ZW1)
    cenv, _ = R.hip_roof([(CAMEL.pts, [0, 1, 2, 3], S2R)], Z_EAVE2, S2R, D_EAVE2, texture=None, zlo=ZW2)
    chim = []
    for (roof_name, env, cx, cy, hx, hy, zs, ztop) in (("ROOF-1", fenv, X0 + 30.0, 96.0, 3.5, 6.0, S1R, zr1),
                                                       ("ROOF-1", fenv, X1 - 30.0, 96.0, 3.5, 6.0, S1R, zr1),
                                                       ("ROOF-2", cenv, XC, YC + 30.0, 3.5, 6.0, S2R, zr2)):
        # the pocket's floor a little under the roof's lowest point round the stack
        zl = min(Z_EAVE1 + S1R * min(cx - hx - (X0 - D_EAVE1), (X1 + D_EAVE1) - cx - hx, cy - hy - (Y0 - D_EAVE1))
                 if roof_name == "ROOF-1" else
                 Z_EAVE2 + S2R * min(cx - hx - (X0 - D_EAVE2), (X1 + D_EAVE2) - cx - hx, cy - hy - (YC - D_EAVE2), (Y1 + D_EAVE2) - cy - hy), ztop)
        z0c = round((zl - 2.4) / 0.2) * 0.2
        seat = G.pocket_seat(env, cx, cy, hx + 0.35, hy + 0.35, z0c)            # room for the brick's relief
        hole = box([cx - hx - 0.35, cy - hy - 0.35, z0c], [cx + hx + 0.35, cy + hy + 0.35, z0c + 200])
        if roof_name == "ROOF-1":
            froof = froof + seat - hole
        else:
            croof = croof + seat - hole
        h = round((ztop + 8.0 - z0c) / 0.2) * 0.2
        chim.append(N.chimney_marigny(w=2 * hx, d=2 * hy, h=h).translate([cx, cy, z0c]))
    kit.add("ROOF-1", "Slate", max(froof.decompose(), key=lambda m_: m_.volume()), group="roof")
    kit.add("ROOF-2", "Slate", max(croof.decompose(), key=lambda m_: m_.volume()), group="roof")
    for k, c in enumerate(chim):
        kit.add(f"CHIMNEY-{k}", "Brick", c, key="CHIMNEY-marigny", group="roof")
    print("roofs", round(time.time() - t0, 1))

    # --- the raised foundation: brick piers and slatted skirts
    fnd = foundation([LOW], 0.0, ZF, style="mgpiers") - box([X0, YC + 0.3, ZF - 0.01], [X1, YC + 2.7, ZF + 3.0])   # (the cross wall)
    kit.add("FOUNDATION", "Brick", fnd, group="foundation")

    # --- the front gallery and the back one
    bld = LOW.solid(grow=1.45, dz0=-20, dz1=300)
    L = (X1 + 2.0) - (X0 - 2.0)
    post_h = round((ZE1 - LEDGE - 0.6 - 1.4 - 2.6 - ZF) / 0.2) * 0.2
    _gallery(kit, "GALLERY", [(X0 - 2.0, YG), (X1 + 2.0, YG), (X1 + 2.0, Y0), (X0 - 2.0, Y0)],
             [dict(a=(X0 - 2.0, Y0), b=(X0 - 2.0, YG), posts=[Y0 - YG - 1.6]),
              dict(a=(X0 - 2.0, YG), b=(X1 + 2.0, YG), posts=[1.6, L / 3, 2 * L / 3, L - 1.6]),
              dict(a=(X1 + 2.0, YG), b=(X1 + 2.0, Y0), posts=[1.6])],
             [(1, 14.0, 12.0), (1, L - 14.0, 12.0)], post_h, 6.4, fnd, keep, bld)
    YB = Y1 + 14.0
    Lb = X1 - X0
    _gallery(kit, "BACK-GALLERY", [(X0, Y1), (X1, Y1), (X1, YB), (X0, YB)],
             [dict(a=(X1, Y1), b=(X1, YB), posts=[YB - Y1 - 1.6]),
              dict(a=(X1, YB), b=(X0, YB), posts=[1.6, Lb / 3, 2 * Lb / 3, Lb - 1.6]),
              dict(a=(X0, YB), b=(X0, Y1), posts=[1.6])],
             [(1, Lb / 2, 12.0)], post_h, 4.4, fnd, keep, bld)
    print("galleries", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "marigny")
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
    kit.render_npz(os.path.join(OUT, "marigny.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
