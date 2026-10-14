"""The Kenmore: an original HO-scale (1:87.1) Federal house in a Gothic skeleton, with a carriage-
arch link to a matching barn; house 101, the first of the new-layouts batch (hoarch.novel), after
the Wedding Cake House of Kennebunk, Maine (built 1826, dressed in Gothic woodwork in 1852-55).

A plain five-bay Federal house of painted butter-yellow brick in English garden-wall bond, on a
quarry-faced granite base, under a low hipped roof of slate banded square and hexagonal, with a
tall stack at each end of both hip slopes. Round it stands a Gothic skeleton in white, built as
its own layer: stepped buttresses between the bays and two at every corner, rising from the
ground on chamfered plinths, each stage carved with a blind lancet, a trefoil or a quatrefoil;
from the eave hangs an openwork screen of cusped pointed arches on little drops, a long pendant
over every buttress; and over every buttress a crocketed pinnacle stands on the roof's edge. A
Gothic porch of clustered shafts and pointed arches under a steep crocketed gable shelters the
door, whose pointed transom of intersecting tracery spans the door and its lancet sidelights.
Ground-floor windows wear ogee labels with crocket finials; upstairs, steep gablets with sunk
trefoils; over the porch a pointed light with Y-tracery between two side lights.

East of the house a one-storey link runs back to the barn, a pointed carriage arch right through
it under two chamfered orders. The barn is gable-fronted, clapboarded in the house's yellow,
with a great pointed hay door hung on fleured straps, a loft door in the gable, lancet windows,
angle buttresses at its corners, bargeboards hung with cusped arches on both gables and a
louvred cupola with a pinnacle on the ridge.

- Storey joint: a white blind arcade of cusped lancets, a green course of ball flowers, a white
  torus crown.
- Eave: a white course of ball flowers, a yellow frieze of fleurettes in diamonds, a white soffit
  and a white cavetto crown; the screen hangs in front.
- The barn's eave and the link's: ball flowers, fleurettes, a cavetto.

usage: python3 -m hoarch.buildings.kenmore [check] [export]
"""
import json
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import Facade, box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, gables as G, novel as N, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells, wall_shell

NAME = "The Kenmore"
COLORS = {"Butter": "#E4CB82", "Lace": "#F3F0E8", "Slate": "#4B525C", "Granite": "#9C9A92", "Forest": "#2F4A3A",
          "Brick": "#8A3D2E", "Planks": "#7A5C40", "Windows_Doors": "#F3F0E8"}
RENDER_MAT = {"Butter": "siding", "Lace": "trim", "Slate": "roof", "Granite": "stone", "Forest": "accent", "Brick": "brick",
              "Planks": "planks", "Windows_Doors": "trim", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"siding": ["#E4CB82", 0.8, 0.0], "trim": ["#F3F0E8", 0.6, 0.0], "roof": ["#4B525C", 0.75, 0.0],
           "stone": ["#9C9A92", 0.9, 0.0], "accent": ["#2F4A3A", 0.6, 0.0], "brick": ["#8A3D2E", 0.85, 0.0],
           "planks": ["#7A5C40", 0.75, 0.0], "sash": ["#F3F0E8", 0.5, 0.0], "door": ["#2F4A3A", 0.45, 0.0]}
VIEWS = {"hero": [-34, 14, 70, 0.9, [0, 0, -10]], "hero_right": [36, 14, 70, 0.9, [0, 0, -10]],
         "front": [0, 6, 85, 0.92, [0, 0, 0]], "rear": [155, 16, 70, 0.92, [0, 0, -10]],
         "porch": [-14, 8, 85, None, [60, -14, 30], 190], "roof": [-25, 40, 60, 1.0, [0, 0, 0]]}

# ------------------------------------------------------------------ cornices (unique to the Kenmore)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.2, b=1.2, orn="kmcuspedarcade", role="Lace"),
    dict(kind="course", h=1.4, b=1.4, orn="kmballflower", role="Forest"),
    dict(kind="crown", h=2.0, b=1.4, P=3.2, orn="torus", role="Lace")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.6, b=1.4, orn="kmballflower", role="Lace"),
    dict(kind="frieze", h=4.2, b=1.2, orn="kmfleurettes", role="Butter"),
    dict(kind="bed", h=2.6, b=1.4, P=7.0, role="Lace"),
    dict(kind="crown", h=2.4, b=1.4, P=7.6, orn="cavetto", role="Lace")])
SMALL = dict(pitch=10.0, margin=3.0, layers=[
    dict(kind="course", h=1.4, b=1.4, orn="kmballflower", role="Lace"),
    dict(kind="frieze", h=3.6, b=1.2, orn="kmfleurettes", role="Butter"),
    dict(kind="crown", h=2.2, b=1.4, P=5.0, orn="cavetto", role="Lace")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)
HS = CO.band_height(SMALL)

# ------------------------------------------------------------------ levels and plan (front = -y)
ZF = 8.0
S1 = ZF + 36.0
ZU = S1 + RJ
ZE = ZU + 32.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
S_MAIN, D_EAVE = 0.62, 8.4
W, D = 120.0, 90.0
XC, YC = W / 2, D / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
V1, V2 = 6.0, ZU - ZF + 4.0
# the link: one storey, its ends run into the house and barn walls (cut back to them)
LX0, LX1, LY0, LY1 = 120.0, 150.0, 16.0, 76.0
LZE = ZF + 30.0
LZW = round((LZE + HS) / 0.2) * 0.2
LZ_EAVE, S_L, D_L = LZW + 1.2, 0.55, 4.6
LINK = Block("link", [(LX0 - 3.0, LY0), (LX1 + 3.0, LY0), (LX1 + 3.0, LY1), (LX0 - 3.0, LY1)], ZF, LZW)
ARCH_X, ARCH_W, ARCH_S = (LX0 + LX1) / 2, 20.0, 18.0
# the barn
BX0, BX1, BY0, BY1 = 150.0, 220.0, -4.0, 92.0
BZF, BZE = 4.0, 66.0
BZW = round((BZE + HS) / 0.2) * 0.2
B_FASCIA = 1.4
BZ_EAVE = BZW + B_FASCIA
S_B, D_B, RAKE_B, SKIN_B = 1.25, 6.0, 6.0, 1.8
BARN = Block("barn", [(BX0, BY0), (BX1, BY0), (BX1, BY1), (BX0, BY1)], BZF, BZW)
BXC = (BX0 + BX1) / 2
# the porch
PX0, PX1, PY = 50.6, 69.4, -11.6
Z_CAP = ZF + 28.0

# the skeleton: buttress stations (block, edge, u) and their screens
FRONT_U = [3.2, 24.0, 48.0, 72.0, 96.0, W - 3.2]
SIDE_U = [3.2, 30.0, 60.0, D - 3.2]           # along y from the front corner
BUT_TOP = ZE - LEDGE - 0.6
STAGES = ((0.0, 5.6, 5.0), (S1 - 8.0, 4.4, 4.4), (ZU + 10.0, 3.2, 3.8))
SCREEN_W = 3.4                                # the screen's back, off the wall face


def _stations():
    """(x, y, outward normal, tag) for every buttress on the house."""
    out = []
    for u in FRONT_U:
        out.append((u, 0.0, (0.0, -1.0), f"S{u:.0f}"))
    for u in SIDE_U:
        out.append((0.0, u, (-1.0, 0.0), f"W{u:.0f}"))
    for u in (SIDE_U[0], SIDE_U[-1]):
        out.append((W, u, (1.0, 0.0), f"E{u:.0f}"))
    return out


STATIONS = _stations()


def _frame_at(x, y, nrm, z=0.0, w=0.0):
    """A facade frame (u along the wall with the house on the left, v up, w out) at (x, y, z),
    shifted w outward."""
    n = np.array([nrm[0], nrm[1], 0.0])
    uu = np.array([-nrm[1], nrm[0], 0.0])          # u: along the wall, as the shell's facades run (n = (u_y, -u_x))
    A = np.zeros((3, 4))
    A[:, 0], A[:, 1], A[:, 2] = uu, (0, 0, 1.0), n
    A[:, 3] = (x + n[0] * w, y + n[1] * w, z)
    return A


def _brick(f, b, reg):
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    lo = reg ^ rect(-1, -100, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, ZU - b.z0, f.L + 1, 999)
    out = []
    if not lo.is_empty():
        out.append(N.brick_kmgarden(lo, datum=0.0))
    if not hi.is_empty():
        out.append(N.brick_kmgarden(hi, datum=ZU - b.z0 + 0.2))
    return union(out) if out else M()


def _link_skin(f, b, reg):
    reg = reg - rect(-1, LZE - LEDGE - 0.6 - b.z0, f.L + 1, 999)
    return N.brick_kmgarden(reg, datum=0.0)


def _barn_skin(f, b, reg):
    reg = reg - rect(-1, BZE - LEDGE - 0.6 - b.z0, f.L + 1, BZW - b.z0 + 0.2)
    return N.clap_kmbarn(reg, datum=0.0, seed=int(abs(f.p0[0]) + abs(f.p0[1])) % 97)


def _openings():
    L1, L2, LL, LB = [], [], [], []

    fams = {}

    def add(L, blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        L[-1].fam = fams.setdefault(id(sp), name)

    lo, up = N.window_kmlower(), N.window_kmupper()
    mids = [(a + b) / 2 for a, b in zip(FRONT_U[:-1], FRONT_U[1:])]
    for x in mids:
        if abs(x - XC) < 1.0:
            add(L1, MAIN, x, 0.0, 0.4, N.door_kenmore(w=7.6, h=24.0, side=1.5, A=0.8), "front-door", "door")
            add(L2, MAIN, x, 0.0, V2, N.window_kmcentre(), "centre")
            add(L1, MAIN, x, D, 0.4, N.door_kenmore(w=8.4, h=22.0, A=0.8, back=True), "back-door", "door")
            add(L2, MAIN, x, D, V2, up, f"N{x:.0f}-2")
        else:
            add(L1, MAIN, x, 0.0, V1, lo, f"S{x:.0f}-1")
            add(L2, MAIN, x, 0.0, V2, up, f"S{x:.0f}-2")
            add(L1, MAIN, x, D, V1, lo, f"N{x:.0f}-1")
            add(L2, MAIN, x, D, V2, up, f"N{x:.0f}-2")
    smids = [(a + b) / 2 for a, b in zip(SIDE_U[:-1], SIDE_U[1:])]
    for y in smids:
        add(L1, MAIN, 0.0, y, V1, lo, f"W{y:.0f}-1")
        add(L2, MAIN, 0.0, y, V2, up, f"W{y:.0f}-2")
    for y in (smids[0], smids[-1]):
        add(L2, MAIN, W, y, V2, up, f"E{y:.0f}-2")
    # the link's carriage arch, front and back
    car = N.arch_kmcarriage(w=ARCH_W, spring=ARCH_S, depth=3.0)
    add(LL, LINK, ARCH_X, LY0, -ZF, car, "arch-S", "door")
    add(LL, LINK, ARCH_X, LY1, -ZF, car, "arch-N", "door")
    # the barn
    add(LB, BARN, BXC, BY0, 0.4, N.door_kmhay(), "hay", "door")
    add(LB, BARN, BXC, BY0, BZW - BZF + 4.0, N.door_kmsmall(12.0, 18.0), "loft", "door")
    add(LB, BARN, BXC, BY1, 0.4, N.door_kmsmall(12.0, 24.0), "barn-back", "door")
    lan = N.window_kmlancet()
    for y in (12.0, 44.0, 76.0):
        add(LB, BARN, BX1, y, 16.0, lan, f"BE{y:.0f}")
    add(LB, BARN, BX0, 84.0, 16.0, lan, "BW84")
    add(LB, BARN, BXC, BY1, BZW - BZF + 6.0, N.window_kmlancet(6.0, 20.0), "BN-gable")
    return L1, L2, LL, LB


OPEN1, OPEN2, OPEN_L, OPEN_B = _openings()
OPENINGS = OPEN1 + OPEN2


def _place_inserts(kit, ops, ins_keep):
    for o in ops:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        part = kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{o.fam}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                       group="inserts", render=zones)
        ins_keep.append(part.solid)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    path = MAIN.pts

    # --- envelopes: the buttresses (cleared from the brick, the base and the cornices), the
    # porch, the link and the barn
    but = N.buttress_kenmore(BUT_TOP, stages=STAGES)
    bb = but.bounding_box()
    but_env = box([bb[0] - 0.15, -1.0, -1.0], [bb[3] + 0.15, BUT_TOP + 0.6, bb[5] + 0.15])
    skel = []
    skel_keep = []
    for x, y, nrm, tag in STATIONS:
        A = _frame_at(x, y, nrm)
        skel.append((tag, A))
        skel_keep.append(but_env.transform(A))
    skel_keep = union(skel_keep)
    skel_solid = union([but.transform(A) for _, A in skel])
    # between the two angle buttresses at each corner the string course is left out (it would be
    # a sliver too small to glue)
    corner_cut = union([box([cx - 7.2, cy - 7.2, S1 - 1.0], [cx + 7.2, cy + 7.2, ZU + 1.0]) for cx in (0.0, W) for cy in (0.0, D)])
    # on the east side the link covers all but two short ends, which would be slivers as well
    corner_cut = corner_cut + box([W - 1.0, -1.0, S1 - 1.0], [W + 9.0, D + 1.0, ZU + 1.0])
    house_env = MAIN.solid(grow=0.15, dz0=-20, dz1=300)
    barn_env = BARN.solid(grow=0.15, dz0=-20, dz1=300)
    link_env = box([LX0 - 1.0, LY0 - D_L - 1.0, -1.0], [LX1 + 1.0, LY1 + D_L + 1.0, LZ_EAVE + S_L * ((LY1 - LY0) / 2 + D_L) + 2.0])
    porch_env = box([PX0 - 1.6, PY - 1.6, -1.0], [PX1 + 1.6, 0.2, Z_CAP + 22.0])
    porch_contact = union([box([PX0 - 0.2, -1.0, -1.0], [PX0 + 1.4, 0.2, Z_CAP + 22.0]),
                           box([PX1 - 1.4, -1.0, -1.0], [PX1 + 0.2, 0.2, Z_CAP + 22.0]),
                           box([PX0 - 1.6, -1.0, Z_CAP], [PX1 + 1.6, 0.2, Z_CAP + 22.0])])

    # --- the house: two storeys of brick, the joint, the ledge for the eave
    undress = [slab(offset(base, 10.0), ZE - LEDGE - 0.6, ZW + 0.01), skel_keep, link_env, porch_contact]
    st = stacked_shells([MAIN], OPENINGS, [S1], t=3.0, corners="none", siding=_brick, clear=[lip_keep(base, 3.0, ZF, 1.2)],
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((XC - 18.0, 3.0), (XC - 18.0, D - 3.0), 2.0, ZF, ZW)])
    kit.add("WALLS-1", "Butter", st["shells"][0] - skel_solid, group="walls")
    kit.add("JOINT", "Butter", st["rings"][0] - skel_keep - link_env - porch_env, group="walls")
    lip = _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)
    kit.add("WALLS-2", "Butter", st["shells"][1] + lip + (CO.ledge(path, ZE, LEDGE) - skel_keep) - skel_solid, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=skel_keep + link_env + porch_env + corner_cut)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    erings, _ = CO.level(path, ZE, EAVE)
    CO.add_level(kit, erings, "CORNICE-E", "cornice")
    bed = [r for r in erings if r["name"] == "bed"][0]
    Z_SOFFIT = bed["z1"] - 0.8
    ins_keep = []
    _place_inserts(kit, OPENINGS, ins_keep)
    print("house walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the hipped roof, its caps, the four stacks in buckets
    pieces = [(path, [0, 1, 2, 3], S_MAIN)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, [], texture=("square", "square", "hex"), tex_kw=dict(pitch=1.7, wtab=2.3, d=0.35),
                       inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    roof = rf["body"] + rf["tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, YC), (W - D / 2, YC), (W - D / 2, YC), (D / 2, YC)]
    roof = roof + G.ridge_cap((D / 2, YC), (W - D / 2, YC), zr, S_MAIN, ZW, half=1.3, up=0.7)
    roof = roof + union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.3, up=0.7, drop=1.8) for c, e in zip(corners, ends)])
    roof = roof.trim_by_plane([0, 0, 1.0], Z_EAVE - FASCIA)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 11.0, 6.4
    stacks = []
    for k, (cx, cy) in enumerate(((11.0, 22.0), (11.0, D - 22.0), (W - 11.0, 22.0), (W - 11.0, D - 22.0))):
        dmin = min(cx - CW / 2, W - cx - CW / 2, cy - CD / 2, D - cy - CD / 2) + D_EAVE
        z_low = Z_EAVE + S_MAIN * dmin
        z0 = round((z_low - 2.4) / 0.2) * 0.2
        roof = roof + G.pocket_seat(solid_env, cx, cy, CW / 2 + 0.4, CD / 2 + 0.4, z0)
        roof = roof - box([cx - CW / 2 - 0.4, cy - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CD / 2 + 0.4, zr + 60])
        h = round((zr + 10.0 - z0) / 0.2) * 0.2
        stacks.append(N.chimney_kenmore(CW, CD, h).translate([cx, cy, z0]))
    # pockets for the pinnacles over the buttresses, on the roof's edge
    pins = []
    PIN = N.pinnacle_kenmore()
    for tag, A in skel:
        p = A @ np.array([0.0, 0.0, 1.9, 1.0])
        z_seat = round((Z_EAVE + 1.6) / 0.2) * 0.2
        roof = roof - box([p[0] - 2.4, p[1] - 2.4, z_seat], [p[0] + 2.4, p[1] + 2.4, zr + 40])
        roof = roof + box([p[0] - 0.8, p[1] - 0.8, z_seat - 0.01], [p[0] + 0.8, p[1] + 0.8, z_seat + 1.2])
        pins.append((tag, p, z_seat))
    kit.add("ROOF", "Slate", roof - lip_keep(base, 3.0, ZW), group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Brick", s_, key="CHIMNEY", group="roof")
    for tag, p, z_seat in pins:
        T = np.array([[1.0, 0, 0, p[0]], [0, 1.0, 0, p[1]], [0, 0, 1.0, z_seat]])
        kit.add(f"PINNACLE-{tag}", "Lace", PIN.transform(T), P=inv34(T), key="PINNACLE", group="skeleton")
    print("roof", round(time.time() - t0, 1))

    # --- the skeleton: the buttresses (each printed on its back) and the screens
    fnd = foundation([MAIN, LINK], 0.0, ZF, style="kmquarry",
                     openings=[(o.block.facades()[o.edge], o.u, -ZF - 1.0, ARCH_W + 8.4, ZF + 2.0) for o in OPEN_L])
    fnd = fnd - skel_keep - barn_env - porch_env
    kit.add("FOUNDATION", "Granite", fnd, group="foundation")
    for tag, A in skel:
        kit.add(f"BUTTRESS-{tag}", "Lace", but.transform(A), P=inv34(A), key="BUTTRESS", group="skeleton")
    screens = []
    Hs = Z_SOFFIT - (ZE - 1.0)
    for name, (x0, y0), nrm, L, stations in (
            ("S", (-SCREEN_W - 1.2, 0.0), (0.0, -1.0), W + 2 * (SCREEN_W + 1.2), [u + SCREEN_W + 1.2 for u in FRONT_U]),
            ("W", (0.0, D), (-1.0, 0.0), D, [D - u for u in SIDE_U])):
        sc = N.screen_kenmore(L, Hs, stations)
        A = _frame_at(x0, y0, nrm, z=Z_SOFFIT, w=SCREEN_W)
        kit.add(f"SCREEN-{name}", "Lace", sc.transform(A), P=inv34(A), group="skeleton")
        screens.append(f"SCREEN-{name}")
    print("skeleton", round(time.time() - t0, 1))

    # --- the Gothic porch: a granite landing and steps; the top in one piece (shafts, arches,
    # crocketed gable, roof), printed upright, pegs under the shafts
    zd = ZF - 0.2
    deck = box([PX0 - 1.2, PY - 1.8, 0.0], [PX1 + 1.2, -0.85, zd])
    fr = MAIN.facades()[0]
    Ast = fr.A.copy()
    Ast[:, 3] = fr.world(XC, -ZF, -PY + 1.8)
    steps = FT.steps(16.0, zd - 0.6, 3).transform(Ast)
    ptop = N.porch_kenmore(PX0, PX1, PY, zd, Z_CAP, slope=1.6)
    ptop = ptop - house_env - union(ins_keep) - skel_keep
    bosses = union([box([x - 0.8, PY + 0.8 - 0.8, zd - 0.01], [x + 0.8, PY + 0.8 + 0.8, zd + 1.2]) for x in (PX0 + 1.6, PX1 - 1.6)])
    deck = deck - fnd - skel_keep
    grooves = union([box([x - 0.25, PY - 1.2, zd - 0.4], [x + 0.25, -1.0, zd + 1.0]) for x in np.arange(PX0 + 0.4, PX1, 1.6)])
    border = box([PX0 - 1.2, PY - 1.8, zd - 0.4], [PX1 + 1.2, PY - 1.2, zd + 1.0])
    deck = deck - grooves - border + box([PX0 - 1.2, PY - 1.8, zd - 0.41], [PX1 + 1.2, PY - 1.2, zd]) + bosses
    kit.add("PORCH-deck", "Planks", deck, group="porch", render=[("Planks", deck)])
    kit.add("PORCH-steps", "Granite", steps - deck - fnd, group="porch")
    kit.add("PORCH-top", "Lace", max(ptop.decompose(), key=lambda m_: m_.volume()), group="porch",
            change=None)
    e, u = MAIN.locate(XC, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Granite", FT.steps(14.0, ZF - 0.6, 3).transform(A) - fnd, group="porch")
    print("porch", round(time.time() - t0, 1))

    # --- the link: brick walls front and back, the passage walls, its cornice and roof
    lins = []
    _place_inserts(kit, OPEN_L, lins)
    lwalls = wall_shell([LINK], OPEN_L, t=3.0, belt=None, corners="none", water_table=False, siding=_link_skin,
                        undress=[slab(offset(LINK.cs, 10.0), LZE - LEDGE - 0.6, LZW + 0.01)],
                        partitions=[((ARCH_X - ARCH_W / 2 - 1.0, LY0 + 3.0), (ARCH_X - ARCH_W / 2 - 1.0, LY1 - 3.0), 2.0, ZF, LZW),
                                    ((ARCH_X + ARCH_W / 2 + 1.0, LY0 + 3.0), (ARCH_X + ARCH_W / 2 + 1.0, LY1 - 3.0), 2.0, ZF, LZW)])
    lwalls = lwalls - lip_keep(LINK.cs, 3.0, ZF, 1.2)
    lwalls = lwalls + CO.ledge(LINK.pts, LZE, LEDGE)
    lwalls = lwalls - house_env - barn_env
    kit.add("LINK-WALLS", "Butter", max(lwalls.decompose(), key=lambda m_: m_.volume()), group="link")
    lrings, _ = CO.level(LINK.pts, LZE, SMALL, cut=house_env + barn_env)
    CO.add_level(kit, lrings, "CORNICE-L", "cornice")
    lrf = G.gabled_roof([(LINK.pts, [0, 2], S_L)], LZ_EAVE, D_L, [], texture="square", tex_kw=dict(pitch=1.6, wtab=2.2, d=0.35),
                        inner_cs=None, fascia=1.2, hollow=0)
    lroof = (lrf["body"] + lrf["tex"]) - house_env - barn_env
    zrl = LZ_EAVE + S_L * ((LY1 - LY0) / 2 + D_L)
    lroof = lroof + (G.ridge_cap((LX0, (LY0 + LY1) / 2), (LX1, (LY0 + LY1) / 2), zrl, S_L, LZW, half=1.2, up=0.6) - house_env - barn_env)
    lroof = lroof.trim_by_plane([0, 0, 1.0], LZ_EAVE - 1.2)
    kit.add("LINK-ROOF", "Slate", max(lroof.decompose(), key=lambda m_: m_.volume()), group="link")
    print("link", round(time.time() - t0, 1))

    # --- the barn: one storey of clapboard with both gables, its cornice, roof, bargeboards,
    # cupola, angle buttresses, base
    brf = G.gabled_roof([(BARN.pts, [1, 3], S_B)], BZ_EAVE, D_B,
                        [dict(p0=(BX0, BY0), p1=(BX1, BY0), slope=S_B, e=0.3), dict(p0=(BX1, BY1), p1=(BX0, BY1), slope=S_B, e=0.3)],
                        texture="square", tex_kw=dict(pitch=1.7, wtab=2.4, d=0.35), skin=SKIN_B, rake=RAKE_B,
                        inner_cs=offset(BARN.cs, -3.0), fascia=B_FASCIA, hollow=2.8)
    wf, wb = brf["walls"]
    gables = [(BARN, 0, wf["cs"].translate((0.0, BZ_EAVE - BZF))), (BARN, 2, wb["cs"].translate((0.0, BZ_EAVE - BZF)))]
    bstat = [(BARN, 0, 3.2), (BARN, 0, BX1 - BX0 - 3.2), (BARN, 2, 3.2), (BARN, 2, BX1 - BX0 - 3.2)]
    bbut = N.buttress_kenmore(BZE - LEDGE - 0.6, stages=((0.0, 5.6, 5.0), (24.0, 4.4, 4.4), (46.0, 3.2, 3.8)))
    bbb = bbut.bounding_box()
    bbut_env = box([bbb[0] - 0.15, -1.0, -1.0], [bbb[3] + 0.15, BZE, bbb[5] + 0.15])
    bskel, bkeep = [], []
    for blk, e, u in bstat:
        f = blk.facades()[e]
        A = f.A.copy()
        A[:, 3] = f.world(u, -blk.z0, 0.0)
        bskel.append((f"B{e}-{u:.0f}", A))
        bkeep.append(bbut_env.transform(A))
    bkeep = union(bkeep)
    bwalls = wall_shell([BARN], OPEN_B, t=3.0, belt=None, corners="none", water_table=False, siding=_barn_skin, gables=gables,
                        undress=[slab(offset(BARN.cs, 10.0), BZE - LEDGE - 0.6, BZW + 0.01), link_env, bkeep])
    bwalls = bwalls - lip_keep(BARN.cs, 3.0, BZF, 1.2)
    no_lip = union([box([BX0 - 1, BY0 - 1, BZW - 1], [BX1 + 1, BY0 + 5.0, BZW + 5]), box([BX0 - 1, BY1 - 5.0, BZW - 1], [BX1 + 1, BY1 + 1, BZW + 5])])
    blip = (_corbel(BARN.cs, 3.0, BZW) + lip_ring(BARN.cs, 3.0, BZW)) - no_lip
    bwalls = bwalls + blip + (CO.ledge(BARN.pts, BZE, LEDGE) - bkeep - link_env)
    kit.add("BARN-WALLS", "Butter", bwalls, group="barn")
    brings, _ = CO.level(BARN.pts, BZE, SMALL, cut=bkeep)
    CO.add_level(kit, brings, "CORNICE-B", "cornice")
    bins = []
    _place_inserts(kit, OPEN_B, bins)
    broof = brf["body"] + brf["tex"] + brf["skins"] + brf["skin_tex"]
    zrb = BZ_EAVE + S_B * ((BX1 - BX0) / 2 + D_B)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE_B + 4.2).translate([0, 0, -3.15])) for wl in brf["walls"]])
    broof = broof + (G.ridge_cap((BXC, BY0 - RAKE_B), (BXC, BY1 + RAKE_B), zrb, S_B, BZW) - walls_env)
    broof = broof - lip_keep(BARN.cs, 3.0, BZW)
    bsolid_env, _ = R.hip_roof([(BARN.pts, [1, 3], S_B)], BZ_EAVE, S_B, D_B, texture=None, zlo=BZW)
    CU = 14.0
    cy = (BY0 + BY1) / 2
    z_cu = round((zrb - S_B * (CU / 2) - 3.0) / 0.2) * 0.2
    broof = broof + G.pocket_seat(bsolid_env, BXC, cy, CU / 2 + 1.0, CU / 2 + 1.0, z_cu)
    broof = broof - box([BXC - CU / 2 - 1.0, cy - CU / 2 - 1.0, z_cu], [BXC + CU / 2 + 1.0, cy + CU / 2 + 1.0, zrb + 40])
    broof = broof - lip_keep(BARN.cs, 3.0, BZW)
    kit.add("BARN-ROOF", "Slate", broof, group="barn")
    cup = N.cupola_kenmore(CU, round((zrb + 12.0 - z_cu) / 0.2) * 0.2)
    cub = cup.bounding_box()
    kit.add("CUPOLA", "Lace", cup.translate([BXC, cy, z_cu]), group="barn")
    ztop = z_cu + cub[5]
    cuproof, _ = R.hip_roof([([(BXC - CU / 2 - 1.6, cy - CU / 2 - 1.6), (BXC + CU / 2 + 1.6, cy - CU / 2 - 1.6),
                               (BXC + CU / 2 + 1.6, cy + CU / 2 + 1.6), (BXC - CU / 2 - 1.6, cy + CU / 2 + 1.6)], [0, 1, 2, 3])],
                            ztop, 1.5, 0.0, texture=None, zlo=ztop)
    cuproof = cuproof.trim_by_plane([0, 0, -1.0], -(ztop + 9.0))
    cuproof = cuproof + box([BXC - 0.8, cy - 0.8, ztop + 8.99], [BXC + 0.8, cy + 0.8, ztop + 10.2])
    kit.add("CUPOLA-roof", "Slate", cuproof, group="barn")
    T = np.array([[1.0, 0, 0, BXC], [0, 1.0, 0, cy], [0, 0, 1.0, ztop + 9.0]])
    kit.add("PINNACLE-cupola", "Lace", N.pinnacle_kenmore(base=4.6, h_ped=2.4, h_shaft=3.0, h_spire=9.0).transform(T), P=inv34(T),
            group="barn")
    for k, wl in enumerate(brf["walls"]):
        bgb = N.barge_kenmore(wl["L"], wl["slope"], D_B, skin=SKIN_B)
        fw = wl["facade"]
        A = fw.A.copy()
        A[:, 3] = fw.world(0.0, 0.0, RAKE_B)
        bw = bgb.transform(A) - broof
        bw = max(bw.decompose(), key=lambda m_: m_.volume())
        kit.add(f"BARGE-{k}", "Lace", bw, P=inv34(A), key="BARGE", group="barn")
    bfnd = foundation([BARN], 0.0, BZF, style="kmquarry",
                      openings=[(o.block.facades()[o.edge], o.u, -BZF - 1.0, 27.0, BZF + 2.0) for o in OPEN_B if o.name == "hay"])
    bfnd = bfnd - bkeep - box([LX0 - 4.0, LY0 - 1, -1], [BX0 + 0.2, LY1 + 1, BZF + 2]) - fnd
    kit.add("BARN-FOUNDATION", "Granite", bfnd, group="barn")
    for tag, A in bskel:
        kit.add(f"BUTTRESS-{tag}", "Lace", bbut.transform(A), P=inv34(A), key="BUTTRESS-barn", group="barn")
    ramp = M.hull_points([(x, y, z) for x in (BXC - 15.0, BXC + 15.0) for y, z in ((BY0 - 0.85, 0.0), (BY0 - 0.85, BZF + 0.3), (BY0 - 10.0, 0.0))])
    kit.add("BARN-ramp", "Granite", ramp - bfnd, group="barn")
    print("barn", round(time.time() - t0, 1))

    # --- glue joints
    for n in screens:
        FT.key_into(kit, n, ["CORNICE-E-upper"], (0, 0, 1), depth=0.6)
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "kenmore")
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
    kit.render_npz(os.path.join(OUT, "kenmore.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
