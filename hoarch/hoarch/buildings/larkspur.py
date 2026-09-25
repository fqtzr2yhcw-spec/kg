"""The Larkspur -- an original HO-scale (1:87.1) Queen Anne, after the user's photo of a
turquoise house with a round tower and a loggia.

Turquoise chamfered lap siding below and chisel-pointed shingles above an astragal
belt, on a rock-faced base of drafted stone, with reveal corner boards. A gabled wing steps
forward on the west with a closed Free Classic pediment and a fan in its gable. A round tower
stands out of the east front corner, rising a storey above the eaves to a bracketed eave and
a bell-cast slate cone with a lance finial. Between them, over the porch, a loggia is sunk
into the upper storey behind an arcade of columns with a railing. A round dormer turret with
three lights and a cone sits on the steep hip roof of plain square slate; a tall clustered
brick chimney. A porch wraps the front and curves round the tower on paired columns, with
twisted balusters, a ball-and-spindle frieze, a lozenge fascia, a planked floor over a skirt
of drafted stone, and a pediment over the steps. Queen Anne windows (9-over-1 under little
shingled pent roofs on brackets); double doors with round-headed lights and oval cameos under
a wave transom.

Colour comes from the part split: turquoise walls, cream trim, navy accents, slate roofs,
grey stone.

usage: python3 -m hoarch.buildings.larkspur [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import arch_cs, box, circle, compose, cs_union, inv34, ngon, offset, poly, rect, scallop_rows, slab, union
from hoarch import features as FT, gables as G, openings as O, roof as R, skins as SK, storefront as SF, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext, stroke
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Larkspur"
COLORS = {"Aqua": "#3FAAB4", "Cream": "#EFE7D2", "Navy": "#23345A", "Slate": "#4A4F57", "Stone": "#8C8378",
          "Brick": "#8A4232", "PorchDeck": "#8C8378", "Windows_Doors": "#EFE7D2"}
RENDER_MAT = {"Aqua": "siding", "Cream": "trim", "Navy": "navy", "Slate": "roof", "Stone": "stone", "Brick": "brick",
              "PorchDeck": "stone", "Planks": "planks", "Windows_Doors": "trim", "Sash": "sash", "Door": "door",
              "Glass": "glass"}

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 12.0
S1 = ZF + 38.0
RH = 4.4
ZE = S1 + RH + 36.0
ZT = ZE + 30.0                  # the tower's eave
FASCIA = 1.8
Z_EAVE = ZE + FASCIA
D_EAVE, RAKE, SKIN = 3.0, 3.2, 1.8
S_MAIN, S_WING = 1.3, 1.5
V1 = 7.0
V2 = S1 + RH + 4.0 - ZF

# ------------------------------------------------------------------ plan
W, D = 104.0, 70.0
WX, WD = 40.0, 14.0             # the west wing: its width and how far it steps forward
LX0, LX1, LD = 48.0, 76.0, 7.0  # the loggia: its span and depth into the upper storey
GY = 26.0                       # how far the wing's gable roof runs back into the hip
TC, TR = (98.0, -4.0), 16.0     # the round tower's centre and radius (a 16-sided drum)
MAIN_LO = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, S1)
MAIN_HI = Block("upper", [(0, 0), (LX0, 0), (LX0, LD), (LX1, LD), (LX1, 0), (W, 0), (W, D), (0, D)], S1, ZE)
WING = Block("wing", [(0, -WD), (WX, -WD), (WX, 3.0), (0, 3.0)], ZF, ZE)
TOWER = Block("tower", ngon(TC, TR, n=16), ZF, ZT)
BLOCKS = [MAIN_LO, MAIN_HI, WING, TOWER]
DOOR_X = 58.0
DOOR_W, DOOR_H = 10.0, 26.0


def _siding(f, b, reg):
    """Chamfered lap siding on the first storey, chisel-pointed shingles above the belt."""
    cut = S1 - b.z0
    out = []
    lo = reg ^ rect(-1, -100, f.L + 1, cut)
    hi = reg ^ rect(-1, cut, f.L + 1, 999)
    if not lo.is_empty():
        out.append(SK.chamfer_lap(lo, datum=0.0))
    if not hi.is_empty():
        out.append(scallop_rows(hi, 1.6, 2.2, d=0.42, datum=S1 + RH - b.z0, shape="chisel", lap=2.0))
    return union(out) if out else M()


def _openings():
    L = []

    def win(w, h, head="pent"):
        return SF.window_commercial(w, h, rise=0, lites=(1, 3), rows=(1, 3), sill=1.0, head=head)

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    # the wing: a triple window below, a pair above, one in the gable
    for x in (8.6, 20.0, 31.4):
        add(WING, x, -WD, V1, win(7.2, 22.0), f"wing{x:.0f}-1")
    for x in (13.0, 27.0):
        add(WING, x, -WD, V2, win(7.2, 20.0), f"wing{x:.0f}-2")
    add(WING, WX / 2, -WD, ZE - ZF + 4.0, win(6.4, 12.0, head=None), "wing-gable")
    # the main front: the door, a window beside it, and inside the loggia a door and a window
    add(MAIN_LO, DOOR_X, 0.0, 0.0, SF.door_commercial(DOOR_W, DOOR_H, transom=4.6, leaf="cameo", tstyle="wave",
                                                     head=None, leaves=2), "door", "door")
    add(MAIN_LO, 71.0, 0.0, V1, win(7.2, 22.0), "F71-1")
    add(MAIN_HI, 55.0, LD, RH, SF.door_commercial(8.0, 24.0, transom=3.6, leaf="cameo", tstyle="wave",
                                                                 head=None), "loggia-door", "door")
    add(MAIN_HI, 69.0, LD, V2 - (S1 - ZF), win(7.2, 20.0, head=None), "loggia-win")
    # the west side, the east side behind the tower, the back
    for y in (14.0, 34.0, 54.0):
        add(MAIN_LO, 0.0, y, V1, win(7.2, 22.0), f"W{y:.0f}-1")
        add(MAIN_HI, 0.0, y, V2 - (S1 - ZF), win(7.2, 20.0), f"W{y:.0f}-2")
    for y in (42.0, 60.0):
        add(MAIN_LO, W, y, V1, win(7.2, 22.0), f"E{y:.0f}-1")
        add(MAIN_HI, W, y, V2 - (S1 - ZF), win(7.2, 20.0), f"E{y:.0f}-2")
    add(MAIN_LO, 20.0, D, 0.0, SF.door_commercial(8.0, 24.0, transom=3.6, leaf="cameo", tstyle="wave", head=None),
        "back-door", "door")
    for x in (40.0, 62.0, 84.0):
        add(MAIN_LO, x, D, V1, win(7.2, 22.0), f"B{x:.0f}-1")
    for x in (20.0, 40.0, 62.0, 84.0):
        add(MAIN_HI, x, D, V2 - (S1 - ZF), win(7.2, 20.0), f"B{x:.0f}-2")
    # the tower: plain tall lights on the faces clear of the house, three storeys
    tw = SF.window_commercial(4.4, 18.0, rise=0, lites=(1, 3), rows=(1, 3), sill=0.8, head=None)
    tw3 = SF.window_commercial(4.4, 16.0, rise=0, lites=(1, 3), rows=(1, 3), sill=0.8, head=None)
    for k, f in enumerate(TOWER.facades()):
        m = (f.p0 + f.p1) / 2
        clear = (MAIN_LO.cs ^ rect(m[0] + f.n[0] * 3 - 3, m[1] + f.n[1] * 3 - 3, m[0] + f.n[0] * 3 + 3,
                                   m[1] + f.n[1] * 3 + 3)).is_empty()
        if not clear or k % 2:
            continue
        add(TOWER, m[0], m[1], V1, tw, f"tower{k}-1")
        add(TOWER, m[0], m[1], V2, tw, f"tower{k}-2")
        if f.n[1] < 0.3:
            add(TOWER, m[0], m[1], ZE - ZF + 6.0, tw3, f"tower{k}-3")
    return L


OPENINGS = _openings()


def loggia_screen():
    """The loggia's front: an arcade of three round arches on two columns and two end
    pilasters, a low railing of flat balusters between the column bases, and the spandrel
    wall over the arches up to the eave. Built lying on its back in (u along the loggia,
    v up from the loggia floor, w out of the recess from its back at w = 0 to the front at
    w = 3); prints on its back: the columns are round to the front and flat behind, and the
    railing lies flush with the back."""
    L = LX1 - LX0
    Hs = ZE - (S1 + RH)
    t = 3.0
    ucol = [L / 3, 2 * L / 3]
    spring = Hs - 12.0
    # the spandrel wall with the three arches cut out of it
    wall = rect(0.0, spring - 1.0, L, Hs)
    holes = []
    edges = [0.0] + ucol + [L]
    for a, b in zip(edges[:-1], edges[1:]):
        a2, b2 = a + (1.4 if a == 0.0 else 1.2), b - (1.4 if b == L else 1.2)
        holes.append(arch_cs(a2, b2, -5.0, spring, rise=(b2 - a2) / 2, seg=32))
    body = ext(wall - cs_union(holes), 0.0, t)
    # archivolts: a raised ring round each arch
    for hcs in holes:
        body = body + ext((hcs.offset(0.8) - hcs) ^ rect(-1, spring, L + 1, Hs), t - 0.01, t + 0.4)
    # the end pilasters and the columns (half round, flat-backed, on square plinths)
    for u0, u1 in ((0.0, 1.4), (L - 1.4, L)):
        body = body + box([u0, 0.0, 0.0], [u1, spring, t])
    for u in ucol:
        body = body + box([u - 1.4, 0.0, 0.0], [u + 1.4, 1.6, t]) + box([u - 1.4, spring - 1.6, 0.0], [u + 1.4, spring, t])
        # the shaft: flat-backed on the bed, round to the front (a D in section), so it prints on its back
        dcs = cs_union([rect(-1.0, 0.0, 1.0, 1.6), circle((0.0, 1.6), 1.0, 24) ^ rect(-2, 1.6, 2, 3)])
        shaft = M.extrude(dcs, spring - 3.2).transform(np.array([[1.0, 0, 0, u], [0, 0, 1.0, 1.6], [0, 1.0, 0, 0.0]]))
        body = body + shaft
    # the railing between the column bases: a rail, a bottom rail and twisted-looking flat balusters
    rh = 8.0
    for a, b in zip(edges[:-1], edges[1:]):
        a2, b2 = a + (1.4 if a == 0.0 else 1.4), b - (1.4 if b == L else 1.4)
        cells = [rect(a2, 0.6, b2, 1.4), rect(a2, rh - 1.0, b2, rh)]
        n = max(2, int((b2 - a2) / 1.4))
        for k in range(n):
            u = a2 + (b2 - a2) * (k + 0.5) / n
            cells.append(cs_union([rect(u - 0.3, 1.3, u + 0.3, rh - 0.9), circle((u, rh / 2), 0.5, 16)]))
        body = body + ext(cs_union(cells), 0.0, 1.8)                  # flush with the back: it prints on the bed
    return body


def dormer_turret(r=6.4, h=20.4):
    """The round dormer turret: a 12-sided drum with three pointed lights facing forward (a
    navy sleeve over a dark core, so the lights read as glass) under a slate cone. Returns
    (sleeve, core, cone) in a local frame at the drum's foot, the lights facing -y."""
    pts = ngon((0.0, 0.0), r, n=12)
    lt = 1.0
    sleeve = slab(poly(pts) - poly(ngon((0.0, 0.0), r - lt, n=12)), 0.0, h)
    light = poly([(-1.4, 4.2), (1.4, 4.2), (1.4, h - 6.8), (0.0, h - 5.4), (-1.4, h - 6.8)])
    for k in range(12):
        a, b = np.array(pts[k]), np.array(pts[(k + 1) % 12])
        mm = (a + b) / 2
        if mm[1] > -r * 0.4:
            continue
        t_ = (b - a) / np.linalg.norm(b - a)
        n = np.array([t_[1], -t_[0]])
        Al = np.array([[t_[0], 0.0, n[0], mm[0]], [t_[1], 0.0, n[1], mm[1]], [0.0, 1.0, 0.0, 0.0]])
        sleeve = sleeve - ext(light, -lt - 0.5, 1.0).transform(Al)
    sleeve = sleeve + ((slab(poly(pts), h - 0.01, h) + slab(poly(ngon((0.0, 0.0), r + 0.8, n=12)), h + 0.79, h + 0.8)).hull()
                       - slab(poly(ngon((0.0, 0.0), r - lt, n=12)), -1, h + 2))
    core = slab(poly(ngon((0.0, 0.0), r - lt, n=12)), 0.0, h + 0.8)
    cone, ctex = R.hip_roof([(ngon((0.0, 0.0), r + 0.8, n=12), list(range(12)))], h + 0.8, 2.2, 0.0, texture=None)
    return sleeve, core, cone


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    r = RAKE - D_EAVE
    pieces = [(MAIN_LO.pts, [0, 1, 2, 3], S_MAIN), ([(0.0, -WD - r), (WX, -WD - r), (WX, GY), (0.0, GY)], [1, 3], S_WING)]
    specs = [dict(p0=(0.0, -WD), p1=(WX, -WD), slope=S_WING, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture="square", tex_kw=dict(pitch=1.5, wtab=2.2, d=0.42),
                       skin=SKIN, rake=RAKE, inner_cs=offset(MAIN_LO.cs, -3.0), fascia=FASCIA, hollow=2.6)
    wl = rf["walls"][0]
    gables = [(WING, 0, wl["cs"].translate((0.0, Z_EAVE - ZF)))]
    bprof, _ = TW.BELTS["astragal"]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="reveal", siding=_siding, gables=gables, prof=bprof,
                        belt_blocks=None, water_table=False)
    # the loggia floor over the porch: a slab filling the recess at the upper floor's level,
    # carried on a 45 degree web off the front wall so the belt prints clean
    lfloor = slab(rect(LX0, -0.01, LX1, LD), S1, S1 + RH) - \
        ext(poly([(3.0, S1 - 0.01), (LD + 0.01, S1 - 0.01), (LD + 0.01, S1 + LD - 3.0)]), LX0 - 1, LX1 + 1).transform(
            np.array([[0, 0, 1.0, 0], [1.0, 0, 0, 0], [0, 1.0, 0, 0]]))
    kit.add("WALLS-1", "Aqua", st["shells"][0], group="walls")
    kit.add("BELT", "Cream", st["rings"][0] + (lfloor - st["shells"][0] - st["shells"][1]), group="walls")
    no_lip = union([box([-D_EAVE - 0.6 - 1, -WD - 1, ZE - 1], [WX + D_EAVE + 0.6, -WD + 5.0, ZE + 5]),
                    TOWER.solid(grow=0.2, dz0=-1, dz1=1), slab(offset(TOWER.cs, 1.0), ZE - 1, ZE + 5)])
    top_cs = cs_union([MAIN_HI.cs, WING.cs])
    lip = (_corbel(top_cs, 3.0, ZE) + lip_ring(top_cs, 3.0, ZE)) - no_lip
    base = cs_union([b.cs for b in BLOCKS])
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN_LO.cs, -3.05), S1 + RH, ZE + 1.2)
    tring = tring - lip_keep(base, 3.0, S1 + RH)
    kit.add("WALLS-2", "Aqua", st["shells"][1] + lip + tring, group="walls")
    fnd = foundation([MAIN_LO, WING, TOWER], 0.0, ZF, style="drafted")
    kit.add("FOUNDATION", "Stone", fnd, group="foundation")
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

    # --- the loggia's arcade screen in the front plane of the upper storey
    Al = np.array([[1.0, 0, 0, LX0], [0, 0, -1.0, 3.0], [0, 1.0, 0, S1 + RH]])
    scr = loggia_screen()
    kit.add("LOGGIA", "Cream", scr.transform(Al) - st["shells"][1], P=inv34(Al), group="walls")

    # --- the main roof: a hollow hip with the wing's gable, cut round the tower
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    caps = [G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZE)]
    walls_env = wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
    zc = Z_EAVE + S_WING * (WX / 2 + D_EAVE)
    y_meet = (zc - Z_EAVE) / S_MAIN - D_EAVE + 1.0
    caps.append(G.ridge_cap((WX / 2, -WD - RAKE), (WX / 2, y_meet), zc, S_WING, ZE))
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.3, up=0.7, drop=1.8)
                  for c, e in zip(corners, ends)])
    roof = roof + ((union(caps) + hips) - walls_env)
    roof = roof - lip_keep(top_cs, 3.0, ZE)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZE)
    # the chimney, and the dormer turret's seat on the front slope
    CW, CD = 11.0, 5.0
    cx, cy = 82.0, 44.0
    zroof = Z_EAVE + S_MAIN * min(cy - CD / 2 + D_EAVE, D + D_EAVE - cy - CD / 2, W + D_EAVE - cx - CW / 2)
    z0 = round((zroof - 3.0) / 0.2) * 0.2
    roof = roof + G.chimney_seat(solid_env, cx, cy, CW / 2, zr + 1.0)
    pocket = box([cx - CW / 2 - 0.4, cy - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CD / 2 + 0.4, zr + 40])
    DR = 6.4
    dx, dy = (LX0 + LX1) / 2, 14.0
    zd = round((Z_EAVE + S_MAIN * (dy - DR + D_EAVE) - 1.6) / 0.2) * 0.2
    roof = roof + G.chimney_seat(solid_env, dx, dy, DR, zd + 20.0)
    dpocket = slab(poly(ngon((dx, dy), DR + 0.3, n=12)), zd - 0.4, zr + 40)
    # (the drum is tall enough that its cap and cone clear the slope behind it)
    roof = roof - pocket - dpocket - slab(offset(TOWER.cs, 1.4), ZE - 1, ZT + 60)
    kit.add("ROOF", "Slate", roof, group="roof")
    ch = TW.chimney("clustered", w=CW, d=CD, h=round((zr + 16.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    orn = G.gable_pediment(wl["L"], wl["slope"], D_EAVE, skin=SKIN)
    f = wl["facade"]
    A = f.A.copy()
    A[:, 3] = f.world(0.0, 0.0, RAKE)
    kit.add("GABLE", "Cream", orn.transform(A), P=inv34(A), group="roof")
    sleeve, core, cone = dormer_turret(DR)
    Td = np.array([[1.0, 0, 0, dx], [0, 1.0, 0, dy], [0, 0, 1.0, zd - 0.4]])
    kit.add("DORMER", "Navy", sleeve.transform(Td), group="roof")
    kit.add("DORMER-core", "Slate", core.transform(Td) - (roof ^ box([dx - 20, dy - 20, 0], [dx + 20, dy + 20, zd - 0.4])),
            group="roof")
    kit.add("DORMER-roof", "Slate", cone.transform(Td), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the tower's eave and bell-cast cone
    teave = R.bracketed_cornice(TOWER.pts, ZT, R.CORNICE_SMALL,
                                brackets=dict(z_top=4.6, h=4.2, d0=0.8, d=2.6, t=0.8, pitch=6.0, margin=1.2, style="cove"),
                                lip_t=3.0, deck=(6.0, 8.0))
    kit.add("TOWER-eave", "Cream", teave, P=print_flip(), group="tower")
    zc0 = ZT + 8.0
    flare, ftex = R.hip_roof([(ngon(TC, TR - 1.4, n=16), list(range(16)))], zc0, 0.8, 4.4, texture="square",
                             tex_kw=dict(pitch=1.5, wtab=2.0, d=0.42), zlo=zc0)
    zf = zc0 + round(0.8 * 4.4 / 0.2) * 0.2
    flare = (flare + ftex).trim_by_plane([0, 0, -1.0], -zf)
    cone, ctex = R.hip_roof([(ngon(TC, TR - 1.4, n=16), list(range(16)))], zf, 2.6, 0.0, texture="square",
                            tex_kw=dict(pitch=1.5, wtab=2.0, d=0.42), zlo=zf - 0.01)
    zs = round((zf + 2.6 * (TR - 1.4) - 2.0) / 0.2) * 0.2
    tcone = (flare + cone + ctex).trim_by_plane([0, 0, -1.0], -zs)
    kit.add("TOWER-roof", "Slate", tcone, group="tower")
    kit.add("TOWER-finial", "Cream", TW.finial("lance", 1.4, 12.0).translate([TC[0], TC[1], zs]), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- the porch: across the front from the wing, round the tower, down the east side
    RP = TR + 12.0
    FY = -WD
    x_meet = TC[0] - math.sqrt(RP ** 2 - (FY - TC[1]) ** 2)
    a0 = math.atan2(FY - TC[1], x_meet - TC[0])
    nf = 7
    sweep = -a0                                   # from the front line round to due east
    arc = [(TC[0] + RP * math.cos(a0 + sweep * k / nf), TC[1] + RP * math.sin(a0 + sweep * k / nf)) for k in range(nf + 1)]
    EX_ = arc[-1][0]
    YB = 30.0
    ppts = [(WX, 0.0), (WX, FY)] + arc + [(EX_, YB), (W, YB), (W, 0.0)]
    turn = sweep / nf
    ca = 1.6 * math.tan(turn / 2)
    Lf = x_meet - WX
    runs = [dict(a=(WX, FY), b=arc[0], posts=[2.8, DOOR_X - WX - 7.4, DOOR_X - WX + 7.4, Lf - ca])]
    Ls = float(np.linalg.norm(np.array(arc[1]) - np.array(arc[0])))
    for k in range(nf):
        runs.append(dict(a=arc[k], b=arc[k + 1], posts=[ca, Ls - ca]))
    runs.append(dict(a=arc[-1], b=(EX_, YB), posts=[ca, (YB - arc[-1][1]) / 2, YB - arc[-1][1] - 1.6]))
    runs.append(dict(a=(EX_, YB), b=(W, YB), posts=[1.6, EX_ - W - 3.6]))
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    PP = FT.porch_turned(ppts, runs, H_floor, post_h, steps_at=[(0, DOOR_X - WX, 12.0)],
                         planks=dict(pitch=1.4, border=2.0), joined=True, ledger_off=1.5, post="paired",
                         rail="twist", arcade="beads", skirt="stone", pier_tex="drafted", roof_edge="lozenge")
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    deck = PP["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    tabs = union([arc_ for arc_, _ in PP["arcades"]])
    for k, fr in enumerate(sorted(PP["frames"], key=lambda m_: -m_.volume())):
        kit.add(f"PORCH-frame-{k}", "Cream", fr - tabs - fnd, group="porch")
    for k, (arc_, A) in enumerate(PP["arcades"]):
        kit.add(f"PORCH-frieze-{k}", "Navy", arc_, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = union([b.solid(grow=1.8, dz0=-20, dz1=0) for b in (MAIN_LO, WING, TOWER)])
    proof = PP["roof"] - bld_keep - ins_keep
    ptop = proof.bounding_box()[5]
    kit.add("PORCH-roof", "Cream", proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8)), P=print_flip(), group="porch")
    kit.add("PORCH-roof-top", "Slate", proof.trim_by_plane([0, 0, 1.0], ptop - 0.8), group="porch")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PORCH-steps-{k}", "Stone", sm.transform(A) - fkeep - deck, group="porch")
    ped = G.gable_pediment(14.0, 0.8, 0.6, skin=0.8, width=1.0, finial=2.4)
    Ap = np.array([[1.0, 0, 0, DOOR_X - 7.0], [0, 0, -1.0, FY - 1.4 + 0.4], [0, 1.0, 0, ptop]])
    back = ext(poly([(-0.6, 0.0), (14.6, 0.0), (7.0, 0.8 * 7.6)]), -3.0, 0.0)
    kit.add("PORCH-pediment", "Cream", (ped + back).transform(Ap), P=inv34(Ap), group="porch")
    e, u = MAIN_LO.locate(20.0, D)
    fb = MAIN_LO.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Stone", FT.steps(12.0, ZF - 0.6, 5).transform(A) - fnd, group="porch")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "larkspur")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "larkspur.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
