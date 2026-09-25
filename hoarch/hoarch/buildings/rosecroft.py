"""The Rosecroft -- an original HO-scale (1:87.1) Stick-style tower house, after the user's photo of a
coral house with a crowned octagonal tower.

Two storeys and an attic of coral rabbeted-bevel siding on a banded stone base, with notched
Stick-style corner boards and a double-fascia belt between the floors. A broad octagonal tower
stands forward at the middle of the front, rising a storey above the eaves to a bracketed eave
and a crown: a ring of eight pointed gablets with lancet lights and spikes, a steep octagonal
roof of round-cornered shingles behind them, a teal lantern of eight tall pointed lights, and
a spire with a weathervane. A porch wraps round the foot of the tower on notched posts, with
ladder railings, a frieze of drops, a notched fascia, a planked floor over a sawtooth skirt
and banded piers, and a gablet with a sunflower over its steps; under it the tower door, a
pair of leaves with keyhole lights under a chevron transom. On either side a steep front
gable with a spoked-wheel ornament over a collar of drops; under the west gable a two-storey
canted bay with a bracketed eave and a low hip. Tall windows under peaked heads. A dogtooth
brick chimney.

Colour comes from the part split: coral walls, teal trim, cream windows, doors and porch
posts, slate-grey roofs. The porch floor prints planks first (one filament change).

usage: python3 -m hoarch.buildings.rosecroft [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, circle, compose, cs_union, inv34, ngon, offset, poly, rect, slab, union
from hoarch import features as FT, gables as G, openings as O, roof as R, skins as SK, \
    storefront as SF, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext, stroke
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Rosecroft"
COLORS = {"Coral": "#E07C68", "Teal": "#2E7C74", "Cream": "#EFE6D2", "Slate": "#5E605F", "Stone": "#8F8A82",
          "Brick": "#8E4632", "PorchDeck": "#2E7C74", "Windows_Doors": "#EFE6D2"}
RENDER_MAT = {"Coral": "siding", "Teal": "teal", "Cream": "trim", "Slate": "roof", "Stone": "stone", "Brick": "brick",
              "PorchDeck": "teal", "Planks": "planks", "Windows_Doors": "trim", "Sash": "sash", "Door": "door",
              "Glass": "glass"}

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 9.0
S1 = ZF + 36.0
RH = 4.4
ZE = S1 + RH + 34.0
ZT = ZE + 36.0                  # tower top
FASCIA = 1.8
Z_EAVE = ZE + FASCIA
D_EAVE, RAKE, SKIN = 2.8, 3.2, 1.8
S_MAIN, S_CROSS = 0.9, 1.3
V1 = 7.0
V2 = S1 + RH + 4.0 - ZF

# ------------------------------------------------------------------ plan
W, D = 150.0, 80.0
GABLES = [(8.0, 52.0), (98.0, 142.0)]
GY = 36.0                       # how far the front gables' roofs run back into the hip
TC, TA = (75.0, 3.0), 17.0      # tower centre and apothem
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZE)
TOWER = Block("tower", ngon(TC, TA, n=8), ZF, ZT)
BX0, BX1, BD = 16.0, 44.0, 6.0  # the canted bay under the west front gable
BAY = Block("bay", [(BX0, 3.0), (BX0, 0.0), (BX0 + BD, -BD), (BX1 - BD, -BD), (BX1, 0.0), (BX1, 3.0)], ZF, ZE)
BLOCKS = [MAIN, BAY, TOWER]
# the bay's eave ring: frieze, bed moulding, soffit and fascia (heights on the grid from the top)
BAY_CORNICE = [(-4.4, 0), (0.8, 0), (0.8, 2.0), (1.2, 2.2), (3.0, 2.2), (3.0, 3.4), (3.4, 3.6), (3.4, 4.0), (-4.4, 4.0)]
S_BAY = 0.7
DOOR_W, DOOR_H = 9.0, 25.0
PORCH_D = 10.0                  # the porch's depth round the tower


def _siding(f, b, reg):
    return SK.rabbet_bevel(reg, datum=0.0)


def _outside(p, blk, margin):
    return (blk.cs ^ rect(p[0] - margin, p[1] - margin, p[0] + margin, p[1] + margin)).is_empty()


def _openings():
    L = []
    lo = SF.window_commercial(7.2, 20.0, rise=0, lites=(1, 1), rows=(2, 1), sill=1.0, head="peak")
    up = SF.window_commercial(7.2, 18.0, rise=0, lites=(1, 1), rows=(2, 1), sill=1.0, head="peak")
    gw = SF.window_commercial(6.0, 13.0, rise=0, lites=(1, 1), rows=(2, 1), sill=0.8, head=None)
    tw1 = SF.window_commercial(7.2, 18.0, rise=0, lites=(1, 1), rows=(2, 1), sill=1.0, head=None)     # under the porch

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    g0, g1 = GABLES[1]
    gm = (g0 + g1) / 2
    for x in (gm - 10.4, gm + 10.4):
        add(MAIN, x, 0.0, V1, lo, f"F{x:.0f}-1")
        add(MAIN, x, 0.0, V2, up, f"F{x:.0f}-2")
    add(MAIN, (g0 + g1) / 2, 0.0, ZE - ZF + 3.0, gw, f"G{(g0 + g1) / 2:.0f}")
    # the bay: a wide light on its front, narrow ones on the cants
    Q = [np.array(p) for p in BAY.pts]
    for k, (w1, tag) in ((1, (4.8, "L")), (2, (7.2, "F")), (3, (4.8, "R"))):
        m = (Q[k] + Q[k + 1]) / 2
        add(BAY, m[0], m[1], V1, SF.window_commercial(w1, 20.0, rise=0, lites=(1, 1), rows=(2, 1), sill=1.0, head=None),
            f"bay{tag}-1")
        add(BAY, m[0], m[1], V2, SF.window_commercial(w1, 18.0, rise=0, lites=(1, 1), rows=(2, 1), sill=1.0, head=None),
            f"bay{tag}-2")
    for y in (16.0, 40.0, 64.0):
        for x, tag in ((0.0, "W"), (W, "E")):
            add(MAIN, x, y, V1, lo, f"{tag}{y:.0f}-1")
            add(MAIN, x, y, V2, up, f"{tag}{y:.0f}-2")
    add(MAIN, W - 24.0, D, 0.0, SF.door_commercial(8.0, 25.0, transom=4.0, leaf="keyhole", tstyle="chevron", head=None),
        "back-door", "door")
    for x in (18.0, 46.0, 75.0, 104.0):
        add(MAIN, x, D, V1, lo, f"B{x:.0f}-1")
    for x in (18.0, 46.0, 75.0, 104.0, 132.0):
        add(MAIN, x, D, V2, up, f"B{x:.0f}-2")
    # the tower: the door on its front face, windows on the faces clear of the house
    front = SF.door_commercial(DOOR_W, DOOR_H, transom=4.4, leaf="keyhole", tstyle="chevron", head=None, leaves=2)
    for k, f in enumerate(TOWER.facades()):
        m = (f.p0 + f.p1) / 2
        clear = _outside(m + f.n * 3.0, MAIN, 4.0)
        if k == 0:
            add(TOWER, m[0], m[1], 0.0, front, "tower-door", "door")
            add(TOWER, m[0], m[1], V2, up, f"tower-{k}-2")
        elif clear:
            add(TOWER, m[0], m[1], V1, tw1, f"tower-{k}-1")
            add(TOWER, m[0], m[1], V2, up, f"tower-{k}-2")
        if f.n[1] < -0.3:                       # the faces clear of the main roof
            add(TOWER, m[0], m[1], ZE - ZF + 8.0, up, f"tower-{k}-3")
    return L


OPENINGS = _openings()


def porch_gable():
    """The gablet over the porch steps: a pentagonal gable prism with a raised rim and a
    sunflower (petals round a boss) in its face, standing on the porch roof. Local: u across
    (centred), v up from the porch roof's top, w out (its back at w = 0, its face at w = 3).
    Prints on its back."""
    hw, dep, rise = 8.0, 3.0, 6.0
    face = poly([(-hw, 0.0), (hw, 0.0), (hw, 1.2), (0.0, 1.2 + rise), (-hw, 1.2)])
    body = ext(face, 0.0, dep)
    rim = face - face.offset(-0.8)
    c = (0.0, 1.2 + rise * 0.36)
    petals = cs_union([(circle_(c, 0.4) + circle_((c[0] + 1.3 * math.cos(a), c[1] + 1.3 * math.sin(a)), 0.55)).hull()
                       for a in np.linspace(0, 2 * math.pi, 8, endpoint=False)])
    return body + ext(rim, dep - 0.01, dep + 0.6) + ext(petals + circle_(c, 0.7), dep - 0.01, dep + 0.6)


def circle_(c, r):
    return circle(c, r, 16)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    r = RAKE - D_EAVE
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN)] + \
             [([(g0, -r), (g1, -r), (g1, GY), (g0, GY)], [1, 3], S_CROSS) for g0, g1 in GABLES]
    specs = [dict(p0=(g0, 0.0), p1=(g1, 0.0), slope=S_CROSS, e=0.3) for g0, g1 in GABLES]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture="rounded", tex_kw=dict(pitch=1.5, wtab=2.0, d=0.42),
                       skin=SKIN, rake=RAKE, inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA, hollow=2.6)
    gables = [(MAIN, 0, wl["cs"].translate((g0, Z_EAVE - ZF))) for (g0, g1), wl in zip(GABLES, rf["walls"])]
    bprof, _ = TW.BELTS["fillet"]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="notched", siding=_siding, gables=gables, prof=bprof,
                        belt_blocks=None, water_table=False)
    kit.add("WALLS-1", "Coral", st["shells"][0], group="walls")
    kit.add("BELT", "Teal", st["rings"][0], group="walls")
    tkeep = TOWER.solid(grow=0.2, dz0=-1, dz1=1)
    no_lip = union([box([g0 - D_EAVE - 0.6, -1, ZE - 1], [g1 + D_EAVE + 0.6, 5.0, ZE + 5]) for g0, g1 in GABLES] +
                   [tkeep, slab(offset(TOWER.cs, 1.0), ZE - 1, ZE + 5)])
    lip = (_corbel(MAIN.cs, 3.0, ZE) + lip_ring(MAIN.cs, 3.0, ZE)) - no_lip
    base = cs_union([b.cs for b in BLOCKS])
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RH, ZE + 1.2)
    tring = tring - lip_keep(base, 3.0, S1 + RH)
    # the gable wall stands over the open back of the bay: a 45 degree web under its foot carries it
    web = ext(poly([(3.0, ZE - 5.0), (3.0, ZE), (-2.0, ZE)]), BX0, BX1)
    web = web.transform(np.array([[0, 0, 1.0, 0], [1.0, 0, 0, 0], [0, 1.0, 0, 0]])) ^ slab(offset(BAY.cs, -0.5), ZE - 6, ZE)
    kit.add("WALLS-2", "Coral", st["shells"][1] + lip + tring + web, group="walls")
    fnd = foundation(BLOCKS, 0.0, ZF, style="banded")
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

    # --- the main roof: a hollow hip with the two front gables, cut round the tower
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    caps = [G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZE)]
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
                       for wl in rf["walls"]])
    for g0, g1 in GABLES:
        zc = Z_EAVE + S_CROSS * ((g1 - g0) / 2 + D_EAVE)
        y_meet = (zc - Z_EAVE) / S_MAIN - D_EAVE + 1.0
        caps.append(G.ridge_cap(((g0 + g1) / 2, -RAKE), ((g0 + g1) / 2, y_meet), zc, S_CROSS, ZE))
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.3, up=0.7, drop=1.8)
                  for c, e in zip(corners, ends)])
    roof = roof + ((union(caps) + hips) - walls_env)
    roof = roof - lip_keep(MAIN.cs, 3.0, ZE)
    CH = 9.0
    cx, cy = W - 30.0, D / 2 + 8.0
    zroof = Z_EAVE + S_MAIN * min(cx - CH / 2 + D_EAVE, W + D_EAVE - cx - CH / 2, cy - CH / 2 + D_EAVE, D + D_EAVE - cy - CH / 2)
    z0 = round((zroof - 3.0) / 0.2) * 0.2
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZE)
    roof = roof + G.chimney_seat(solid_env, cx, cy, CH / 2, zr + 1.0)
    pocket = box([cx - CH / 2 - 0.4, cy - CH / 2 - 0.4, z0], [cx + CH / 2 + 0.4, cy + CH / 2 + 0.4, zr + 40])
    roof = roof - pocket - slab(offset(TOWER.cs, 1.4), ZE - 1, ZT + 60)
    kit.add("ROOF", "Slate", roof, group="roof")
    ch = TW.chimney("dogtooth", w=CH, d=CH * 0.75, h=round((zr + 12.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    for k, wl in enumerate(rf["walls"]):
        orn = G.gable_wheel(wl["L"], wl["slope"], D_EAVE, skin=SKIN)
        f = wl["facade"]
        A = f.A.copy()
        A[:, 3] = f.world(0.0, 0.0, RAKE)
        kit.add(f"GABLE-{k}", "Teal", orn.transform(A) - TOWER.solid(grow=0.6, dz0=-1, dz1=1), P=inv34(A), group="roof")
    # the bay: a bracketed eave ring and a low hip of the same shingles, stopped at the wall
    bay_keep = MAIN.solid(grow=0.45, dz0=-1, dz1=300) + box([-50, -60, 0], [BX0, 0, 300]) + box([BX1, -60, 0], [200, 0, 300])
    beave = R.bracketed_cornice(BAY.pts, ZE, BAY_CORNICE,
                                brackets=dict(z_top=2.2, h=3.2, d0=0.8, d=2.0, t=0.7, pitch=4.6, margin=1.4, style="fret"))
    kit.add("BAY-eave", "Teal", beave - bay_keep - web, P=print_flip(), group="bay")
    broof, btex = R.hip_roof([(BAY.pts, [1, 2, 3])], ZE + 4.0, S_BAY, 3.6, texture="rounded",
                             tex_kw=dict(pitch=1.5, wtab=2.0, d=0.42))
    kit.add("BAY-roof", "Slate", (broof + btex) - bay_keep, group="bay")
    print("roof", round(time.time() - t0, 1))

    # --- the tower's crown: a bracketed eave; a ring of pointed gablets, each with a lancet light
    # and a spike; a steep octagonal roof rising behind them; an eight-light lantern; a spire and the vane
    tpts = TOWER.pts
    teave = R.bracketed_cornice(tpts, ZT, R.CORNICE_SMALL,
                                brackets=dict(z_top=4.6, h=4.0, d0=0.8, d=2.4, t=0.7, pitch=4.0, margin=1.6, style="fret"),
                                lip_t=3.0, deck=(6.0, 8.0))
    kit.add("TOWER-eave", "Teal", teave, P=print_flip(), group="tower")
    zc0 = ZT + 8.0
    RO, RB, HB = TA + 0.6, TA - 1.4, 2.4          # gablet faces, the roof's foot, the band's height
    GW, GS, GP = 9.0, 7.0, 1.84                   # gablet width, side-wall height, gable pitch
    ST = 3.2
    ridge = GS + GW / 2 * GP
    r_in = RB - (ridge + 0.4 - HB) / ST           # the gablets run back until the roof covers their ridges
    ring = [slab(poly(ngon(TC, RO, n=8)) - poly(ngon(TC, RB, n=8)), zc0, zc0 + HB)]
    pent = poly([(-GW / 2, 0.0), (GW / 2, 0.0), (GW / 2, GS), (0.0, ridge), (-GW / 2, GS)])
    rim = cs_union([stroke([(-GW / 2 - 1, GS - GP), (0.0, ridge)], 1.6), stroke([(0.0, ridge), (GW / 2 + 1, GS - GP)], 1.6)]) ^ pent
    lancet = cs_union([rect(-1.7, 2.4, 1.7, 9.0), poly([(-1.7, 9.0), (1.7, 9.0), (0.0, 10.8)])])
    for f in TOWER.facades():
        n, t_ = f.n, f.u
        o = np.array(TC) + n * RO
        Ag = np.array([[t_[0], 0.0, n[0], o[0]], [t_[1], 0.0, n[1], o[1]], [0.0, 1.0, 0.0, zc0]])
        g = ext(pent, -(RO - r_in), 0.0) + ext(rim, -0.01, 0.4) - ext(lancet, -0.8, 1.0)
        g = g + M.cylinder(3.4, 0.8, 0.2, 12).transform(
            np.array([[1.0, 0, 0, 0], [0, 0, 1.0, ridge - 0.8], [0, -1.0, 0, -0.9]]))
        ring.append(g.transform(Ag))
    gring = union(ring)
    kit.add("TOWER-gablets", "Teal", gring, group="tower")
    # the lantern: as wide as the crown allows once the roof has climbed over the gablets, its
    # eight tall pointed lights; a teal part of its own, the slate spire another
    LA, HL, SS = 10.8, 15.0, 2.0                  # the lantern's apothem and height, the spire's slope
    zl = zc0 + round((HB + ST * (RB - LA - 0.6)) / 0.2) * 0.2
    assert zl - zc0 >= ridge + 0.2, "the lantern would stand on the gablets"
    croof, ctex = R.hip_roof([(ngon(TC, RB, n=8), list(range(8)))], zc0 + HB, ST, 0.0, texture="rounded",
                             tex_kw=dict(pitch=1.5, wtab=2.0, d=0.42), zlo=zc0)
    crown = (croof + ctex).trim_by_plane([0, 0, -1.0], -zl) - gring
    kit.add("TOWER-crown", "Slate", crown, group="tower")
    lpts = ngon(TC, LA, n=8)
    LT = 1.2                                      # the sleeve's wall: its lights open onto a dark core
    lantern = slab(poly(lpts) - poly(ngon(TC, LA - LT, n=8)), zl, zl + HL)
    lw = 2.4                                      # half the width of a light
    light = poly([(-lw, 2.0), (lw, 2.0), (lw, HL - 4.6), (0.0, HL - 4.6 + lw), (-lw, HL - 4.6)])
    for k in range(8):
        a, b = np.array(lpts[k]), np.array(lpts[(k + 1) % 8])
        t_ = (b - a) / np.linalg.norm(b - a)
        n = np.array([t_[1], -t_[0]])
        mm = (a + b) / 2
        Al = np.array([[t_[0], 0.0, n[0], mm[0]], [t_[1], 0.0, n[1], mm[1]], [0.0, 1.0, 0.0, zl]])
        lantern = lantern - ext(light, -LT - 0.5, 1.0).transform(Al)
    inner = slab(poly(ngon(TC, LA - LT, n=8)), zl - 1, zl + HL + 2)
    lantern = lantern + slab(poly(ngon(TC, LA + 0.4, n=8)), zl, zl + 1.0) - inner + \
        ((slab(poly(lpts), zl + HL - 0.01, zl + HL) + slab(poly(ngon(TC, LA + 0.8, n=8)), zl + HL + 0.79, zl + HL + 0.8)).hull() - inner)
    kit.add("TOWER-lantern", "Teal", lantern, group="tower")
    kit.add("TOWER-lantern-core", "Slate", slab(poly(ngon(TC, LA - LT, n=8)), zl, zl + HL + 0.8), group="tower")
    spire, _ = R.hip_roof([(ngon(TC, LA + 0.8, n=8), list(range(8)))], zl + HL + 0.8, SS, 0.0, texture=None)
    # (the spire sits on the sleeve's cap and the core's top)
    zs = round((zl + HL + 0.8 + SS * (LA + 0.8) - 1.4) / 0.2) * 0.2      # the spire stops flat for the finial's seat
    spire = spire.trim_by_plane([0, 0, -1.0], -zs)
    kit.add("TOWER-spire", "Slate", spire, group="tower")
    HV = 10.2                                     # the rod's top, where the arrow's hub stands
    fin = TW.finial("vane", 1.3, HV).translate([TC[0], TC[1], zs])
    kit.add("TOWER-finial", "Teal", fin, group="tower")
    arrow = cs_union([stroke([(-4.0, 0.0), (3.2, 0.0)], 0.6), poly([(3.0, -1.0), (4.6, 0.0), (3.0, 1.0)]),
                      poly([(-4.0, -0.3), (-3.0, -0.3), (-3.6, -1.4), (-4.6, -1.4)]),
                      poly([(-4.0, 0.3), (-3.0, 0.3), (-3.6, 1.4), (-4.6, 1.4)]), rect(-0.5, -1.2, 0.5, 2.4),
                      circle((0.0, 2.6), 0.6, 16)])
    Av = np.array([[1.0, 0, 0, TC[0]], [0, 0, -1.0, TC[1] + 0.3], [0, 1.0, 0, zs + HV + 1.2]])
    kit.add("TOWER-vane", "Teal", ext(arrow, 0.0, 0.6).transform(Av), P=inv34(Av), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- the porch round the tower: its outline is the tower's octagon grown by PORCH_D, cut at
    # the house front; notched posts and ladder railings in one piece per run of runs
    grown = poly(ngon(TC, TA + PORCH_D, n=8)) ^ rect(-100, -100, 400, 0.0)
    ppts = [tuple(round(c, 4) for c in p) for p in max(grown.to_polygons(), key=len)]
    if poly(ppts).area() < 0:
        ppts = ppts[::-1]
    k0 = next(i for i in range(len(ppts)) if abs(ppts[i][1]) < 1e-6 and abs(ppts[(i + 1) % len(ppts)][1]) > 1e-6)
    ppts = ppts[k0:] + ppts[:k0]                      # start at the west end on the wall line
    c45 = 1.6 * math.tan(math.radians(22.5))
    runs = []
    for i in range(len(ppts) - 1):
        a, b = np.array(ppts[i]), np.array(ppts[i + 1])
        L_ = float(np.linalg.norm(b - a))
        first, last = i == 0, i == len(ppts) - 2
        if first:
            posts = [2.0, L_ - c45]
        elif last:
            posts = [c45, L_ - 2.0]
        elif abs(a[1] - b[1]) < 1e-6:                 # the front: open between its corner posts for the steps
            posts = [c45, L_ - c45]
            steps_run = i
        else:
            posts = [c45, L_ / 2, L_ - c45]
        runs.append(dict(a=tuple(a), b=tuple(b), posts=posts))
    front_L = float(np.linalg.norm(np.array(runs[steps_run]["b"]) - np.array(runs[steps_run]["a"])))
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor              # the porch roof stays under the belt
    PP = FT.porch_turned(ppts, runs, H_floor, post_h, steps_at=[(steps_run, front_L / 2, 18.0)],
                         planks=dict(pitch=2.0, border=1.8), joined=True, ledger_off=1.5, post="notched",
                         rail="ladder", arcade="drops", skirt="sawtooth", pier_tex="banded", roof_edge="notched")
    base = cs_union([b.cs for b in BLOCKS])
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
        kit.add(f"PORCH-frieze-{k}", "Teal", arc_, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = union([b.solid(grow=1.8, dz0=-20, dz1=0) for b in (MAIN, TOWER)])
    proof = PP["roof"] - bld_keep - ins_keep
    ptop = proof.bounding_box()[5]
    kit.add("PORCH-roof", "Teal", proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8)), P=print_flip(), group="porch")
    kit.add("PORCH-roof-top", "Slate", proof.trim_by_plane([0, 0, 1.0], ptop - 0.8), group="porch")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PORCH-steps-{k}", "Stone", sm.transform(A) - fkeep - deck, group="porch")
    fa, fb_ = np.array(runs[steps_run]["a"]), np.array(runs[steps_run]["b"])
    mid = (fa + fb_) / 2
    Ag = np.array([[1.0, 0, 0, mid[0]], [0, 0, -1.0, mid[1] - 1.4 + 0.4 + 3.0], [0, 1.0, 0, ptop]])
    kit.add("PORCH-gable", "Teal", porch_gable().transform(Ag), P=inv34(Ag), group="porch")
    e, u = MAIN.locate(W - 24.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Stone", FT.steps(12.0, ZF - 0.6, 4).transform(A), group="porch")

    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "rosecroft")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "rosecroft.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
