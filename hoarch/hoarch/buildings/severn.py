"""The Severn: an original HO-scale (1:87.1) five-part Palladian house; house 109, of the
new-layouts batch (hoarch.novel2), after the Hammond-Harwood House, Annapolis, Maryland (1774,
William Buckland).

Five buildings in a row, symmetrical and wide and low: a two-storey brick centre block with a
pedimented centre pavilion, two one-storey hyphens set back from it, and two wings at the ends
whose fronts are canted bays (half-octagons) under hipped roofs.

- Walls: Flemish bond with glazed headers, rubbed-brick corners; a stone water table on a
  brick base in English bond.
- Cornices: a stone belt between the storeys (a Greek key fret under a bevel); the eave, a
  Doric frieze of triglyphs and rosettes, egg and dart, modillions and a cyma, carried across
  the pavilion as its pediment's base, with a raking cornice of modillions up both rakes and
  the end gables; the hyphens and wings have their own (egg and dart, fret, modillions).
- Openings: nine over nine below and nine over six above under rubbed-brick flat arches with
  stone keystones; the doorway (a fanlight in a round arch between Ionic columns, a garland
  frieze, a dentilled cornice and a pediment) and the round-headed window over it between fluted
  pilasters; an oculus in the pediment; round-headed windows in the hyphens; twelve over twelve
  under lunettes in the wings' bays.

usage: python3 -m hoarch.buildings.severn [check] [export]
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
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells, wall_shell

NAME = "The Severn"
COLORS = {"Brick": "#9C4A35", "Stone": "#D8D0BE", "White": "#F2F0EA", "Slate": "#565B63", "Windows_Doors": "#F2F0EA"}
RENDER_MAT = {"Brick": "brick", "Stone": "stone", "White": "trim", "Slate": "roof", "Windows_Doors": "trim",
              "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"brick": ["#9C4A35", 0.85, 0.0], "stone": ["#D8D0BE", 0.8, 0.0], "trim": ["#F2F0EA", 0.6, 0.0],
           "roof": ["#565B63", 0.7, 0.0], "sash": ["#F2F0EA", 0.5, 0.0], "door": ["#2E3B33", 0.45, 0.0]}
VIEWS = {"hero": [-28, 16, 70, 0.92, [0, 0, -12]], "hero_right": [30, 16, 70, 0.92, [0, 0, -12]],
         "front": [0, 6, 85, 0.95, [0, 0, 0]], "rear": [160, 20, 70, 0.92, [0, 0, -10]],
         "door": [-8, 6, 85, None, [126, 50, 40], 140], "wing": [-40, 14, 80, None, [24, 70, 40], 190]}

LEDGE = 1.4
JOINT = dict(pitch=10.0, margin=3.0, layers=[
    dict(kind="course", h=2.0, b=1.2, orn="svfret", role="Stone"),
    dict(kind="crown", h=1.6, b=1.2, P=2.6, orn="bevel", role="Stone")])
EAVE = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="frieze", h=3.8, b=1.2, orn="svtriglyph", role="White", half=1.2),
    dict(kind="course", h=1.2, b=1.2, orn="svegg", role="Stone"),
    dict(kind="bed", h=2.0, b=1.4, P=4.4, role="White", brackets=dict(style="svmodillion", t=1.6, h=2.2)),
    dict(kind="crown", h=2.0, b=1.4, P=5.0, orn="cyma", role="White")])
HEAVE = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="course", h=1.2, b=1.2, orn="svegg", role="White"),
    dict(kind="crown", h=1.8, b=1.2, P=3.0, orn="cavetto", role="White")])
WEAVE = dict(pitch=8.0, margin=2.5, layers=[
    dict(kind="course", h=1.8, b=1.2, orn="svfret", role="Stone"),
    dict(kind="bed", h=1.8, b=1.4, P=3.6, role="White", brackets=dict(style="svmodillion", t=1.6, h=2.0)),
    dict(kind="crown", h=1.8, b=1.4, P=4.2, orn="cyma", role="White")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

T = 3.0
ZF = 8.0
CX0, CX1, CY0, CY1 = 74.0, 178.0, 60.0, 128.0      # the centre block, 104 x 68
XC = (CX0 + CX1) / 2
PX0, PX1, PJ = XC - 20.0, XC + 20.0, 4.0           # the centre pavilion, 4 forward
S1 = ZF + 40.0
ZU = S1 + RJ
ZE = ZU + 30.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
S_M, S_P, D_EAVE, RAKE = 0.55, 0.42, 3.0, 3.0
MAIN = Block("main", [(CX0, CY0), (PX0, CY0), (PX0, CY0 - PJ), (PX1, CY0 - PJ), (PX1, CY0), (CX1, CY0), (CX1, CY1), (CX0, CY1)], ZF, ZW)
# the hyphens, set back
HY0, HY1 = 80.0, 120.0
ZEH = ZF + 30.0
ZWH = round((ZEH + CO.band_height(HEAVE)) / 0.2) * 0.2
ZH_EAVE = ZWH + 1.2
S_H = 0.5
HYW = Block("hyphen-W", [(44.0, HY0), (CX0, HY0), (CX0, HY1), (44.0, HY1)], ZF, ZWH)
HYE = Block("hyphen-E", [(CX1, HY0), (208.0, HY0), (208.0, HY1), (CX1, HY1)], ZF, ZWH)
# the wings, their fronts canted bays
WY0, WY1 = 52.0, 128.0
ZEW = ZF + 46.0
ZWW = round((ZEW + CO.band_height(WEAVE)) / 0.2) * 0.2
ZW_EAVE = ZWW + 1.4
S_W = 0.75


def _wing_pts(xa, xb):
    return [(xa + 12.0, WY0), (xb - 12.0, WY0), (xb, WY0 + 12.0), (xb, WY1), (xa, WY1), (xa, WY0 + 12.0)]


WGW = Block("wing-W", _wing_pts(4.0, 44.0), ZF, ZWW)
WGE = Block("wing-E", _wing_pts(208.0, 248.0), ZF, ZWW)
V1, V2 = 6.0, ZU - ZF + 5.0


def _openings():
    L1, L2, LH, LW = [], [], [], []
    fams = {}

    def add(L, blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        L[-1].fam = fams.setdefault(id(sp), name)

    lo, up = N.window_svmain(w=9.0), N.window_svupper(w=9.0)
    # the front: a bay each side of the pavilion (no wall more than half window), the doorway
    # and the window over it
    for x in ((CX0 + PX0) / 2, (PX1 + CX1) / 2):
        add(L1, MAIN, x, CY0, V1, lo, f"S{x:.0f}-1")
        add(L2, MAIN, x, CY0, V2, up, f"S{x:.0f}-2")
    add(L1, MAIN, XC, CY0 - PJ, 0.0, N.door_svmain(), "doorway", "door")
    add(L2, MAIN, XC, CY0 - PJ, V2 + 0.6, N.window_svcentre(h=19.0), "S-centre-2")
    # the garden front
    for x in ((CX0 + PX0) / 2, (PX1 + CX1) / 2):
        add(L1, MAIN, x, CY1, V1, lo, f"N{x:.0f}-1")
    add(L1, MAIN, XC, CY1, 0.0, N.door_svback(), "garden-door", "door")
    for x in ((CX0 + PX0) / 2, XC, (PX1 + CX1) / 2):
        add(L2, MAIN, x, CY1, V2, up, f"N{x:.0f}-2")
    # the ends, clear of the hyphens
    for x, tag in ((CX0, "W"), (CX1, "E")):
        add(L1, MAIN, x, 70.0, V1, lo, f"{tag}70-1")
        for y in (70.0, 118.0):
            add(L2, MAIN, x, y, V2, up, f"{tag}{y:.0f}-2")
    # the hyphens: a round-headed window each side
    arch = N.window_svarch()
    for blk in (HYW, HYE):
        xm = (blk.pts[0][0] + blk.pts[1][0]) / 2
        add(LH, blk, xm, HY0, V1, arch, f"{blk.name}-S")
        add(LH, blk, xm, HY1, V1, arch, f"{blk.name}-N")
    # the wings: the bay's tall window under its lunette, two windows out, one at the back
    tall, lun = N.window_svwing(), N.window_svlunette()
    for blk, xo in ((WGW, 4.0), (WGE, 248.0)):
        xm = (blk.pts[0][0] + blk.pts[1][0]) / 2
        add(LW, blk, xm, WY0, V1, tall, f"{blk.name}-bay")
        add(LW, blk, xm, WY0, V1 + 24.0 + 6.0, lun, f"{blk.name}-lunette")
        for y in (86.0, 108.0):
            add(LW, blk, xo, y, V1, lo, f"{blk.name}-out{y:.0f}")
        add(LW, blk, xm, WY1, V1, lo, f"{blk.name}-back")
    return L1, L2, LH, LW


OPEN1, OPEN2, OPEN_H, OPEN_W = _openings()
OPENINGS = OPEN1 + OPEN2 + OPEN_H + OPEN_W
BLOCKS = [MAIN, HYW, HYE, WGW, WGE]


def _skin(f, b, reg):
    """Flemish bond, kept clear of the belt's and the cornices' bands."""
    if b is MAIN:
        reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2) - rect(-1, S1 - b.z0, f.L + 1, ZU - b.z0)
    else:
        ze, zw = (ZEH, ZWH) if b in (HYW, HYE) else (ZEW, ZWW)
        reg = reg - rect(-1, ze - LEDGE - 0.6 - b.z0, f.L + 1, zw - b.z0 + 0.2)
    if reg.is_empty():
        return M()
    return N.brick_severn(reg, datum=0.0, L=f.L if f.L > 8.0 else None)


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


def _rakes(kit, name, rf, roof, cut=None):
    """A raking cornice under every rake of a roof's gables."""
    for j, wl in enumerate(rf["walls"]):
        rk = N.raking_severn(wl["L"], wl["slope"], D_EAVE, skin=1.6, depth=2.2, rake=RAKE - 0.65)
        fw = wl["facade"]
        A = fw.A.copy()
        A[:, 3] = fw.world(0.0, 0.0, 0.45)                     # (in front of the brick's relief)
        r_ = rk.transform(A) - roof
        if cut is not None:
            r_ = r_ - cut
        r_ = max(r_.decompose(), key=lambda m_: m_.volume())
        kit.add(f"{name}-{j}", "White", r_, P=inv34(A), key=f"{name}-{round(wl['L'])}", group="roof")


def _pocket(roof, env, cx, cy, hx, hy, zl, ztop):
    z0c = round((zl - 2.4) / 0.2) * 0.2
    roof = roof + G.pocket_seat(env, cx, cy, hx + 0.35, hy + 0.35, z0c) - box([cx - hx - 0.35, cy - hy - 0.35, z0c], [cx + hx + 0.35, cy + hy + 0.35, z0c + 200])
    ch = N.chimney_severn(w=2 * hx, d=2 * hy, h=round((ztop + 9.0 - z0c) / 0.2) * 0.2).translate([cx, cy, z0c])
    return roof, ch


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()

    # --- the low roofs first: the hyphens' (against the centre block and the wings) and the wings'
    hroofs = {}
    for blk in (HYW, HYE):
        hroofs[blk.name] = G.gabled_roof([(blk.pts, [0, 2], S_H)], ZH_EAVE, 2.4, [], texture="svslate", tex_kw=dict(pitch=1.4, d=0.3),
                                         skin=1.4, inner_cs=offset(blk.cs, -3.0), fascia=1.2, hollow=2.2)
    wroofs = {}
    for blk in (WGW, WGE):
        wroofs[blk.name] = G.gabled_roof([(blk.pts, list(range(6)), S_W)], ZW_EAVE, 2.8, [], texture="svslate", tex_kw=dict(pitch=1.4, d=0.3),
                                         skin=1.6, inner_cs=offset(blk.cs, -3.0), fascia=1.4, hollow=2.4)
    henv = union([r["body"] + r["tex"] for r in hroofs.values()])
    hwalls_env = union([b.solid(grow=0.6, dz0=-10, dz1=0.0) for b in (HYW, HYE)])
    main_env = MAIN.solid(grow=0.6, dz0=-10, dz1=300)                     # (with the brick's relief)
    wing_env = union([b.solid(grow=0.6, dz0=-10, dz1=300) for b in (WGW, WGE)])
    bases = {b.name: foundation([b], 0.0, ZF, style="svwater") for b in (MAIN, HYW, HYE, WGW, WGE)}

    # --- the centre block: the main roof with the pavilion's pediment, its gable walls
    pieces = [([(CX0, CY0), (CX1, CY0), (CX1, CY1), (CX0, CY1)], [0, 2], S_M),
              ([(PX0, CY0 - PJ), (PX1, CY0 - PJ), (PX1, (CY0 + CY1) / 2), (PX0, (CY0 + CY1) / 2)], [1, 3], S_P)]
    gdefs = [dict(p0=(CX1, CY0), p1=(CX1, CY1), slope=S_M), dict(p0=(CX0, CY1), p1=(CX0, CY0), slope=S_M),
             dict(p0=(PX0, CY0 - PJ), p1=(PX1, CY0 - PJ), slope=S_P, e=D_EAVE)]
    where = [(5, 0.0), (7, 0.0), (2, 0.0)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="svslate", tex_kw=dict(pitch=1.5, d=0.32), skin=1.6, rake=RAKE,
                       inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA, hollow=2.6)
    gables = [(MAIN, e, (wl["cs"] + rect(0.0, -FASCIA - 0.4, wl["L"], -FASCIA + 0.01)).translate((u0, Z_EAVE - MAIN.z0)))
              for (e, u0), wl in zip(where, rf["walls"])]
    undress = [slab(offset(MAIN.cs, 10.0), ZE - LEDGE - 0.6, ZW + 0.01), henv, hwalls_env]
    st = stacked_shells([MAIN], OPEN1 + OPEN2, [S1], t=T, corners="none", siding=_skin, clear=[lip_keep(MAIN.cs, T, ZF, 1.2)],
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress, gables=gables)
    kit.add("WALLS-1", "Brick", st["shells"][0], group="walls")
    kit.add("BELT", "Brick", st["rings"][0] - henv, group="walls")
    lip = _corbel(MAIN.cs, T, ZW) + lip_ring(MAIN.cs, T, ZW)
    kit.add("WALLS-2", "Brick", st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE, t=T), group="walls")
    jr, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=henv + hwalls_env)
    CO.add_level(kit, jr, "CORNICE-J", "cornice")
    er, _ = CO.level(MAIN.pts, ZE, EAVE, t=T)
    CO.add_level(kit, er, "CORNICE-E", "cornice")
    eenv = union([r["solid"] for r in er])
    keep = []
    _place_inserts(kit, OPEN1 + OPEN2, keep)
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_M * ((CY1 - CY0) / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((CX0 - RAKE, (CY0 + CY1) / 2), (CX1 + RAKE, (CY0 + CY1) / 2), zr, S_M, ZW, half=1.0, up=0.5) - walls_env)
    roof = roof - lip_keep(MAIN.cs, T, ZW)
    env, _ = R.hip_roof([(pieces[0][0], [0, 2], S_M)], Z_EAVE, S_M, D_EAVE, texture=None, zlo=ZW)
    chim = []
    for cx in (CX0 + 10.5, CX1 - 10.5):                      # (their pockets clear of the end walls and lips)
        for cy in (CY0 + 20.0, CY1 - 20.0):
            hy = 3.2
            zl = Z_EAVE + S_M * (min(cy - hy - (CY0 - D_EAVE), (CY1 + D_EAVE) - (cy + hy)))
            roof, ch = _pocket(roof, env, cx, cy, 4.0, hy, zl, zr)
            chim.append(ch)
    kit.add("ROOF", "Slate", max(roof.decompose(), key=lambda m_: m_.volume()), group="roof")
    _rakes(kit, "RAKING", rf, roof, cut=eenv)
    fnd = bases["main"]
    kit.add("BASE", "Brick", fnd, group="foundation", change=(round((ZF - 1.8) / 0.2) * 0.2, "Stone"),
            render=[("Brick", fnd ^ box([-1e4, -1e4, -1], [1e4, 1e4, ZF - 1.75])), ("Stone", fnd - box([-1e4, -1e4, -1], [1e4, 1e4, ZF - 1.75]))])
    print("centre", round(time.time() - t0, 1))

    # --- the hyphens and the wings
    for blk, rr, spec, ze, zw in ((HYW, hroofs, HEAVE, ZEH, ZWH), (HYE, hroofs, HEAVE, ZEH, ZWH),
                                  (WGW, wroofs, WEAVE, ZEW, ZWW), (WGE, wroofs, WEAVE, ZEW, ZWW)):
        ops = [o for o in OPEN_H + OPEN_W if o.block is blk]
        nbr = main_env + wing_env if blk in (HYW, HYE) else M()
        sw = wall_shell([blk], ops, t=T, belt=None, corners="none", water_table=False, siding=_skin,
                        undress=[slab(offset(blk.cs, 8.0), ze - LEDGE - 0.6, zw + 0.01)] + ([hwalls_env, henv] if blk in (WGW, WGE) else []))
        sw = (sw - lip_keep(blk.cs, T, ZF, 1.2)) + _corbel(blk.cs, T, zw) + lip_ring(blk.cs, T, zw) + CO.ledge(blk.pts, ze, LEDGE, t=T)
        sw = sw - nbr
        kit.add(f"WALLS-{blk.name}", "Brick", max(sw.decompose(), key=lambda m_: m_.volume()), group="walls")
        kr, _ = CO.level(blk.pts, ze, spec, t=T, cut=nbr if blk in (HYW, HYE) else hwalls_env)
        CO.add_level(kit, kr, f"CORNICE-{blk.name}", "cornice")
        _place_inserts(kit, ops, keep)
        r = rr[blk.name]
        rs = r["body"] + r["tex"] - lip_keep(blk.cs, T, zw) - nbr
        if blk in (WGW, WGE):
            xa, xb = blk.pts[4][0], blk.pts[3][0]
            cx, cy = (xa + xb) / 2, 112.0
            wenv, _ = R.hip_roof([(blk.pts, list(range(6)), S_W)], ZW_EAVE, S_W, 2.8, texture=None, zlo=zw)
            zrw = ZW_EAVE + S_W * ((xb - xa) / 2 + 2.8)
            zl = ZW_EAVE + S_W * min((WY1 + 2.8) - (cy + 3.0), cx - 4.0 - (xa - 2.8), (xb + 2.8) - (cx + 4.0))
            rs, ch = _pocket(rs, wenv, cx, cy, 4.0, 3.0, zl, zrw)
            chim.append(ch)
        kit.add(f"ROOF-{blk.name}", "Slate", max(rs.decompose(), key=lambda m_: m_.volume()), group="roof")
        f_ = bases[blk.name] - fnd if blk in (WGW, WGE) else bases[blk.name] - fnd - bases["wing-W"] - bases["wing-E"]
        kit.add(f"BASE-{blk.name}", "Brick", f_, group="foundation", change=(round((ZF - 1.8) / 0.2) * 0.2, "Stone"),
                render=[("Brick", f_ ^ box([-1e4, -1e4, -1], [1e4, 1e4, ZF - 1.75])), ("Stone", f_ - box([-1e4, -1e4, -1], [1e4, 1e4, ZF - 1.75]))])
    for k, c in enumerate(chim):
        kit.add(f"CHIMNEY-{k}", "Brick", c, key="CHIMNEY-severn", group="roof")
    print("hyphens and wings", round(time.time() - t0, 1))

    # --- the steps: stone, to the doorway and the garden door
    steps = []
    for (xa, xb, y0, dy) in ((XC - 11.0, XC + 11.0, CY0 - PJ, -1.0), (XC - 7.0, XC + 7.0, CY1, 1.0)):
        for j in range(3):                                   # three treads, four risers of 2 mm down to the ground
            z = ZF - 2.0 * (j + 1)
            ya, yb = sorted((y0 + dy * 2.8 * j, y0 + dy * 2.8 * (j + 1)))
            steps.append(M.hull_points([(x, y, 0.0) for x in (xa, xb) for y in (ya, yb)] +
                                       [(x, y, z - 0.4) for x in (xa, xb) for y in (ya, yb)] +
                                       [(x, y, z) for x in (xa + 0.3, xb - 0.3) for y in (ya + 0.3, yb - 0.3)]))
    stp = union(steps) - fnd - main_env
    kit.add("STEPS", "Stone", stp, group="stoop")
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "severn")
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
    kit.render_npz(os.path.join(OUT, "severn.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
