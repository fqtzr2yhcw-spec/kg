"""The Juniper -- an original HO-scale (1:87.1) Queen Anne, after the user's photo of a green
house with a round corner tower. Rev B: the house-size plan (196 x 140 mm, storeys of 42 and
38 mm), framed windows spaced along the walls, built-up cornices at every level, and fewer
lights round the tower's top.

Olive wide clapboard below and sage hexagon-cut shingles above, on a base of red brick with
raised white pointing, with Eastlake rosette-block corners. Between the storeys a three-part
cornice (a lavender frieze of fans, a cream pellet course and a lavender ovolo crown); at the
eave a four-part one (a lavender lattice frieze, a cream dentil course, a cream soffit on tongue
brackets and a lavender cyma crown). A round tower stands out of the west front corner, its top
storey with framed lights on every other face under a lavender frieze of stars, a cream soffit
on tongue brackets and a cream crown, then a tall cone of swallowtail shingles with a
fleur-de-lis finial. The
steep hip roof of swallowtail shingles carries a front gable and an east side gable, each
with a round-headed attic window and a lavender king-pendant ornament, and a gabled dormer
with a framed triple window; a brick chimney with sunk lozenges. An oval window with a lavender
surround sits beside the door. A porch sweeps round the foot of the tower and across the
front on vasiform turned posts, with ringed balusters, a frieze of pierced fans, a billet
fascia, a planked floor over a skirt of swallowtail shingles pierced by square vent grilles,
and a gablet with a round-arched panel over the steps. Windows with a raised oval tablet in
their head boards (six over one: the upper sash two lights across and three high); doors with elliptical lights
under a star transom.

usage: python3 -m hoarch.buildings.juniper [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import arch_cs, box, circle, compose, cs_union, inv34, ngon, offset, poly, rect, scallop_rows, slab, union
from hoarch import cornice as CO, features as FT, gables as G, openings as O, roof as R, skins as SK, storefront as SF, \
    trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext, stroke
from hoarch.shell import _stepped
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Juniper"
COLORS = {"Olive": "#6E7D3C", "Sage": "#9DB07C", "Lavender": "#A690C2", "Cream": "#EFE8D6", "Brown": "#6A4A34",
          "Brick": "#8A3B2B", "PorchDeck": "#9DB07C", "Windows_Doors": "#EFE8D6"}
RENDER_MAT = {"Olive": "siding", "Sage": "sage", "Lavender": "lavender", "Cream": "trim", "Brown": "roof",
              "Brick": "brick", "PorchDeck": "sage", "Planks": "planks", "Windows_Doors": "trim", "Sash": "sash",
              "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Juniper)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="fans", role="Lavender"),
    dict(kind="course", h=1.6, b=1.4, orn="pellets", role="Cream"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="ovolo", role="Lavender")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.6, b=1.2, orn="lattice", role="Lavender"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Cream", tooth=0.8, gap=0.5),
    dict(kind="bed", h=2.0, b=1.4, P=6.2, role="Cream", brackets=dict(style="tongue", t=0.9, reach=0.55)),
    dict(kind="crown", h=2.8, b=1.4, P=7.0, orn="cyma", role="Lavender")])
TOWER_C = dict(pitch=7.0, margin=2.4, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="stars", role="Lavender"),
    dict(kind="bed", h=1.8, b=1.4, P=5.0, role="Cream", brackets=dict(style="tongue", t=0.8, reach=0.7)),
    dict(kind="crown", h=2.2, b=1.4, P=5.8, orn="bevel", role="Cream")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 12.0
S1 = ZF + 42.0                  # first-storey shell top = the joint ring's foot
RH = RJ
ZE = S1 + RJ + 38.0             # the eave ledge's top
ZW = ZE + HE                    # the wall top behind the eave cornice; the roof sits here
ZT = ZW + 34.0                  # the tower's cornice ledge
ZTW = ZT + CO.band_height(TOWER_C)
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 7.4, 4.2, 1.8
S_MAIN, S_GABLE = 0.95, 1.3
V1 = 8.0
V2 = S1 + RJ + 5.0 - ZF

# ------------------------------------------------------------------ plan
W, D = 196.0, 140.0
FG = (112.0, 192.0)             # the front gable's span on the front wall
SG = (44.0, 108.0)              # the east side gable's span on the east wall
TC, TR = (8.0, -8.0), 28.0      # the round tower's centre and radius (a 16-sided drum)
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
TOWER = Block("tower", ngon(TC, TR, n=16), ZF, ZTW)
BLOCKS = [MAIN, TOWER]
DOOR_X = 88.0
DOOR_W, DOOR_H = 13.0, 30.0
OVAL_X, OVAL_V, OVAL_R = 60.0, 16.0, (4.6, 7.0)


def _siding(f, b, reg):
    """Wide clapboard on the first storey, hexagon-cut shingles above the joint; nothing
    behind the cornices."""
    cut = S1 - b.z0
    top = (ZT if b is TOWER else ZE) - b.z0
    reg = reg - rect(-1, top, f.L + 1, (ZTW if b is TOWER else ZW) - b.z0)
    out = []
    lo = reg ^ rect(-1, -100, f.L + 1, cut)
    hi = reg ^ rect(-1, cut, f.L + 1, 999)
    if not lo.is_empty():
        out.append(SK.wide_lap(lo, datum=0.0))
    if not hi.is_empty():
        out.append(scallop_rows(hi, 1.6, 2.2, d=0.42, datum=S1 + RH - b.z0, shape="hex", lap=2.0))
    return union(out) if out else M()


def _openings():
    L = []

    def win(w, h, head="tablet", rise=0):
        return SF.window_commercial(w, h, rise=rise, lites=(1, 2), rows=(1, 3), sill=1.2, head=head, casing=1.3,
                                    band=True)

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    add(MAIN, DOOR_X, 0.0, 0.0, SF.door_commercial(DOOR_W, DOOR_H, transom=4.6, leaf="ellipse", tstyle="star",
                                                  head=None, leaves=2), "door", "door")
    gm = (FG[0] + FG[1]) / 2
    for x in (gm - 16.0, gm + 16.0):
        add(MAIN, x, 0.0, V1, win(8.4, 24.0), f"F{x:.0f}-1")
        add(MAIN, x, 0.0, V2, win(8.4, 21.0), f"F{x:.0f}-2")
    add(MAIN, gm, 0.0, ZW - ZF + 5.0, win(8.8, 17.0, head=None, rise=4.4), "front-gable")
    for x in (62.0, 92.0):
        add(MAIN, x, 0.0, V2, win(8.4, 21.0), f"F{x:.0f}-2")
    sm = (SG[0] + SG[1]) / 2
    for y in (20.0, sm, 126.0):
        add(MAIN, W, y, V1, win(8.4, 24.0), f"E{y:.0f}-1")
    for y in (20.0, sm - 13.0, sm + 13.0, 126.0):
        add(MAIN, W, y, V2, win(8.4, 21.0), f"E{y:.0f}-2")
    add(MAIN, W, sm, ZW - ZF + 5.0, win(8.0, 15.0, head=None, rise=4.0), "side-gable")
    for y in (60.0, 100.0):
        add(MAIN, 0.0, y, V1, win(8.4, 24.0), f"W{y:.0f}-1")
        add(MAIN, 0.0, y, V2, win(8.4, 21.0), f"W{y:.0f}-2")
    add(MAIN, 148.0, D, 0.0, SF.door_commercial(10.0, 29.0, transom=4.2, leaf="ellipse", tstyle="star", head=None),
        "back-door", "door")
    for x in (32.0, 72.0, 112.0):
        add(MAIN, x, D, V1, win(8.4, 24.0), f"B{x:.0f}-1")
    for x in (32.0, 72.0, 112.0, 148.0, 180.0):
        add(MAIN, x, D, V2, win(8.4, 21.0), f"B{x:.0f}-2")
    # the tower: framed tall lights; the top storey's on every other face clear of the roof
    tw = win(6.4, 22.0, head=None)
    tw3 = win(6.4, 18.0, head=None)
    for k, f in enumerate(TOWER.facades()):
        m = (f.p0 + f.p1) / 2
        clear = (MAIN.cs ^ rect(m[0] + f.n[0] * 3 - 3, m[1] + f.n[1] * 3 - 3, m[0] + f.n[0] * 3 + 3,
                                m[1] + f.n[1] * 3 + 3)).is_empty()
        if not clear:
            continue
        if k % 2 == 0:
            add(TOWER, m[0], m[1], V1, tw, f"tower{k}-1")
            add(TOWER, m[0], m[1], V2, tw, f"tower{k}-2")
            add(TOWER, m[0], m[1], ZT - ZF - 24.0, tw3, f"tower{k}-3")
    return L


OPENINGS = _openings()


def oval_window():
    """The oval window beside the door: a lavender surround (a moulded ring with four key
    blocks) round a sash ring and dark glass, one piece printed face-up, pushed into its oval
    opening from outside. Local: u across, v up (centred), w out. Returns (solid, zones, cut)."""
    rx, ry = OVAL_R
    ov = lambda a, b: poly([(a * math.cos(t), b * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 48, endpoint=False)])
    cut = ov(rx, ry)
    plug = ext(ov(rx - 0.15, ry - 0.15), -1.6, 0.0)
    glass = ext(ov(rx - 0.8, ry - 0.8), -1.6, -1.2)
    sash = plug - ext(ov(rx - 0.8, ry - 0.8), -1.21, 1.0)
    ring = ext(ov(rx + 1.8, ry + 1.8) - ov(rx - 0.2, ry - 0.2), 0.0, 0.6) + ext(ov(rx + 1.1, ry + 1.1) - ov(rx + 0.3, ry + 0.3), 0.59, 1.0)
    keys = M()
    for (x, y, rot) in ((0.0, ry + 0.2, 0.0), (0.0, -ry - 0.2, 180.0), (rx + 0.2, 0.0, -90.0), (-rx - 0.2, 0.0, 90.0)):
        k = poly([(-0.6, 0.0), (0.6, 0.0), (0.8, 1.6), (-0.8, 1.6)]).rotate(rot).translate((x, y))
        keys = keys + ext(k, 0.0, 1.2)
    frame = ring + keys
    solid = sash + glass + frame
    return solid, [("Lavender", frame), ("Lavender", sash), ("Glass", glass)], cut


def dormer(w=16.0, dep=14.0, hwall=8.0, pitch=1.2):
    """A gabled dormer with a triple window: a pentagonal body (the front wall 1.2 thick with
    three lights opening onto a dark core behind), a raised rim and a small pendant in the
    gable. Local: u across (centred), v up from the dormer's foot, w out (the face at w = 0,
    the body running back to w = -dep). Returns (body, core)."""
    rise = w / 2 * pitch
    face = poly([(-w / 2, 0.0), (w / 2, 0.0), (w / 2, hwall), (0.0, hwall + rise), (-w / 2, hwall)])
    body = ext(face, -dep, 0.0) - ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, 99), -dep - 1, -1.2)
    us = (-w * 0.28, 0.0, w * 0.28)
    lw = w * 0.085
    lights = cs_union([rect(u - lw, 2.4, u + lw, hwall - 1.6) for u in us])
    body = body - ext(lights, -1.3, 1.0)
    body = body + _stepped((lights.offset(0.8, JoinType.Miter, 4.0) - lights) ^ rect(-w / 2 + 0.6, 1.6, w / 2 - 0.6, hwall),
                           -0.01, 0.6)                                                              # framed lights
    mr = 2.4 + (hwall - 4.0) * 0.5
    body = body + ext(cs_union([rect(u - lw, mr - 0.3, u + lw, mr + 0.3) for u in us]), -1.2, -0.4)   # meeting rails
    body = body + ext((face - face.offset(-0.8, JoinType.Miter, 4.0)) ^ rect(-50, hwall, 50, 99), -0.01, 0.4)
    body = body + ext(cs_union([rect(u - lw - 1.0, 1.2, u + lw + 1.0, 2.0) for u in us]), -0.01, 1.0)   # sills
    core = ext(face.offset(-1.2, JoinType.Miter, 4.0) ^ rect(-50, 1.2, 50, hwall), -dep + 1.2, -1.2)
    return body, core


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    r = RAKE - D_EAVE
    gy = (S_GABLE * ((FG[1] - FG[0]) / 2 + D_EAVE)) / S_MAIN + 4.0
    gx = (S_GABLE * ((SG[1] - SG[0]) / 2 + D_EAVE)) / S_MAIN + 4.0
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN),
              ([(FG[0], -r), (FG[1], -r), (FG[1], gy), (FG[0], gy)], [1, 2, 3], S_GABLE),
              ([(W - gx, SG[0]), (W + r, SG[0]), (W + r, SG[1]), (W - gx, SG[1])], [0, 2], S_GABLE)]
    specs = [dict(p0=(FG[0], 0.0), p1=(FG[1], 0.0), slope=S_GABLE, e=0.3),
             dict(p0=(W, SG[0]), p1=(W, SG[1]), slope=S_GABLE, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture="swallow", tex_kw=dict(pitch=1.5, wtab=2.2, d=0.42),
                       skin=SKIN, rake=RAKE, inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA, hollow=2.6)
    wf, ws = rf["walls"]
    gables = [(MAIN, 0, wf["cs"].translate((FG[0], Z_EAVE - ZF))), (MAIN, 1, ws["cs"].translate((SG[0], Z_EAVE - ZF)))]
    tkeep = TOWER.solid(grow=0.2, dz0=-1, dz1=1)
    undress = [slab(offset(MAIN.cs, 8.0) - offset(TOWER.cs, 1.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="rosette", siding=_siding, gables=gables,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    # the oval window's opening beside the door
    ov_solid, ov_zones, ov_cut = oval_window()
    f0 = MAIN.facades()[0]
    Ao = f0.A.copy()
    Ao[:, 3] = f0.world(OVAL_X, OVAL_V, 0.0)
    walls1 = st["shells"][0] - ext(ov_cut, -4.0, 2.0).transform(Ao) - \
        ext(cs_union([poly([((OVAL_R[0] + 2.0) * math.cos(t), (OVAL_R[1] + 2.0) * math.sin(t))
                            for t in np.linspace(0, 2 * math.pi, 48, endpoint=False)])]), -0.05, 1.0).transform(Ao)
    kit.add("WALLS-1", "Olive", walls1, group="walls")
    kit.add("JOINT", "Olive", st["rings"][0], group="walls")
    no_lip = union([box([FG[0] - D_EAVE - 0.6, -1, ZW - 1], [FG[1] + D_EAVE + 0.6, 5.0, ZW + 5]),
                    box([W - 5.0, SG[0] - D_EAVE - 0.6, ZW - 1], [W + 1, SG[1] + D_EAVE + 0.6, ZW + 5]),
                    tkeep, slab(offset(TOWER.cs, 1.0), ZW - 1, ZW + 5)])
    lip = (_corbel(MAIN.cs, 3.0, ZW) + lip_ring(MAIN.cs, 3.0, ZW)) - no_lip
    base = cs_union([b.cs for b in BLOCKS])
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RH, ZW + 1.2)
    tring = tring - lip_keep(base, 3.0, S1 + RH)
    ledges = (CO.ledge(MAIN.pts, ZE, LEDGE) - tkeep) + CO.ledge(TOWER.pts, ZT, LEDGE)
    kit.add("WALLS-2", "Sage", st["shells"][1] + lip + tring + ledges, group="walls")
    for tag, path, z0, spec, cut in (("J", st["outlines"][0], S1 + LEDGE + 0.4, JOINT, None),
                                     ("E", MAIN.pts, ZE, EAVE, TOWER.solid(grow=1.1, dz0=-2, dz1=2)),
                                     ("T", TOWER.pts, ZT, TOWER_C, None)):
        rings, _ = CO.level(path, z0, spec, cut=cut)
        CO.add_level(kit, rings, f"CORNICE-{tag}", "tower" if tag == "T" else "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="tuckpoint")
    kit.add("FOUNDATION", "Brick", fnd, group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}", group="inserts", render=zones))
    inserts.append(kit.add("WIN-oval", "Lavender", ov_solid.transform(Ao), P=inv34(Ao), group="inserts",
                           render=[(c, s.transform(Ao)) for c, s in ov_zones]))
    print("walls + inserts", round(time.time() - t0, 1))

    # --- the main roof: a hollow hip with the front and side gables, cut round the tower
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    caps = [G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZW)]
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
                       for wl in rf["walls"]])
    zc = Z_EAVE + S_GABLE * ((FG[1] - FG[0]) / 2 + D_EAVE)
    # the front gable's ridge stands above the main hip's east slope, so it ends in a hip of
    # its own at the back, with caps on the two hip lines
    fx = (FG[0] + FG[1]) / 2
    fy = gy + D_EAVE - (zc - Z_EAVE) / S_GABLE
    caps.append(G.ridge_cap((fx, -RAKE), (fx, fy + 0.4), zc, S_GABLE, ZW))
    for xc in (FG[0] - D_EAVE, FG[1] + D_EAVE):
        caps.append(G.hip_cap((xc, gy + D_EAVE, Z_EAVE), (fx, fy, zc), half=1.6, up=0.9, drop=2.2))
    zc2 = Z_EAVE + S_GABLE * ((SG[1] - SG[0]) / 2 + D_EAVE)
    caps.append(G.ridge_cap((W + RAKE, (SG[0] + SG[1]) / 2), (W - ((zc2 - Z_EAVE) / S_MAIN - D_EAVE + 1.0), (SG[0] + SG[1]) / 2),
                            zc2, S_GABLE, ZW))
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.6, up=0.9, drop=2.2)
                  for c, e in zip(corners, ends)])
    roof = roof + ((union(caps) + hips) - walls_env)
    roof = roof - lip_keep(MAIN.cs, 3.0, ZW)
    roof = roof.trim_by_plane([0, 0, 1.0], ZW)                # nothing below the wall top (the hip caps' drops)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 13.0, 10.0
    cx, cy = 60.0, 88.0
    zroof = Z_EAVE + S_MAIN * min(cx - CW / 2 + D_EAVE, cy - CD / 2 + D_EAVE, D + D_EAVE - cy - CD / 2)
    z0 = round((zroof - 3.0) / 0.2) * 0.2
    roof = roof + G.chimney_seat(solid_env, cx, cy, CW / 2, zr + 1.0)
    pocket = box([cx - CW / 2 - 0.4, cy - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CD / 2 + 0.4, zr + 40])
    # the dormer on the front slope between the tower and the front gable
    DW, DDEP, DHW = 30.0, 28.0, 15.0
    dxc = 70.0
    dyf = 14.0                                   # its face line
    zdf = round((Z_EAVE + S_MAIN * (dyf + D_EAVE) - 1.0) / 0.2) * 0.2
    dbody, dcore = dormer(DW, DDEP, DHW)
    Ad = np.array([[1.0, 0, 0, dxc], [0, 0, -1.0, dyf], [0, 1.0, 0, zdf]])
    # its pocket in the roof follows the dormer's own outline, 0.3 clear all round
    dface = poly([(-DW / 2, 0.0), (DW / 2, 0.0), (DW / 2, DHW), (0.0, DHW + DW / 2 * 1.2), (-DW / 2, DHW)])
    dkeep = ext(dface.offset(0.3, JoinType.Miter, 4.0), -DDEP - 0.3, 0.3).transform(Ad)
    roof = roof - pocket - (dkeep ^ box([-500, -500, zdf], [500, 500, 999])) - slab(offset(TOWER.cs, 1.4), ZW - 1, ZTW + 90)
    dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
    # the dormer's seat: a block standing on the bed inside the hollow roof (a seat pyramid's
    # tip would start in mid-air this far down), its top the pocket's floor
    dseat = box([dxc - DW / 2 - 1.3, dyf - 1.6, ZW], [dxc + DW / 2 + 1.3, dyf + DDEP + 1.3, zdf]) ^ solid_env
    roof = roof + (dseat - dpocket - lip_keep(MAIN.cs, 3.0, ZW))
    kit.add("ROOF", "Brown", roof, group="roof")
    ch = TW.chimney("lozenge", w=CW, d=CD, h=round((zr + 18.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    for k, wl in enumerate(rf["walls"]):
        orn = G.gable_pendant(wl["L"], wl["slope"], D_EAVE, skin=SKIN)
        f = wl["facade"]
        A = f.A.copy()
        A[:, 3] = f.world(0.0, 0.0, RAKE)
        ow = orn.transform(A) - roof                          # the ornaments' feet stop on the main roof
        kit.add(f"GABLE-{k}", "Lavender", max(ow.decompose(), key=lambda m_: m_.volume()), P=inv34(A), group="roof")
    # the dormer: a flat-bottomed body dropped into its pocket on the seat (so it prints
    # upright on the 0.2 grid), its own little gabled roof of the same shingles
    envd = solid_env.translate([0, 0, 0])
    dsolid = dbody.transform(Ad)
    kit.add("DORMER", "Sage", dsolid, group="roof")
    kit.add("DORMER-core", "Brown", dcore.transform(Ad), group="roof")
    rise = DW / 2 * 1.2
    # boxed eaves: a flat soffit at each side down to the body's wall top, so the roof prints
    # upright standing on its two soffits
    ez = DHW - 1.6 * 1.2
    droof_cs = poly([(-DW / 2 - 1.6, ez), (-DW / 2, ez), (-DW / 2, DHW), (0.0, DHW + rise + 0.2), (DW / 2, DHW),
                     (DW / 2, ez), (DW / 2 + 1.6, ez), (DW / 2 + 1.6, ez + 1.6), (0.0, DHW + rise + 2.2),
                     (-DW / 2 - 1.6, ez + 1.6)])
    droof = ext(droof_cs, -DDEP - 6.0, 1.2).transform(Ad) - envd - dbody.transform(Ad) - roof
    kit.add("DORMER-roof", "Brown", droof, group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the tower's tall cone on its cornice
    zc0 = ZTW
    dct = TOWER_C["layers"][-1]["P"] + 0.4
    cone, ctex = R.hip_roof([(ngon(TC, TR, n=16), list(range(16)))], zc0, 2.4, dct, texture="swallow",
                            tex_kw=dict(pitch=1.5, wtab=2.2, d=0.42), zlo=zc0)
    zs = round((zc0 + 2.4 * (TR + dct) - 2.6) / 0.2) * 0.2
    tcone = (cone + ctex).trim_by_plane([0, 0, -1.0], -zs)
    kit.add("TOWER-roof", "Brown", tcone, group="tower")
    kit.add("TOWER-finial", "Lavender", TW.finial("fleur", 1.9, 16.0).translate([TC[0], TC[1], zs]), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- the porch: down the west side, round the foot of the tower, across the front
    RP = TR + 18.0
    FY = -28.0
    x_meet = TC[0] + math.sqrt(RP ** 2 - (FY - TC[1]) ** 2)
    a0, a1 = math.pi, 2 * math.pi + math.atan2(FY - TC[1], x_meet - TC[0])
    nf = 5
    arc = [(TC[0] + RP * math.cos(a0 + (a1 - a0) * k / nf), TC[1] + RP * math.sin(a0 + (a1 - a0) * k / nf))
           for k in range(nf + 1)]
    XW = arc[0][0]
    YN = 52.0
    XE = 124.0
    ppts = [(0.0, YN), (XW, YN)] + arc + [(XE, FY), (XE, 0.0), (0.0, 0.0)]
    turn = (a1 - a0) / nf
    ca = 1.6 * math.tan(turn / 2)
    Ls = float(np.linalg.norm(np.array(arc[1]) - np.array(arc[0])))
    runs = [dict(a=(0.0, YN), b=(XW, YN), posts=[3.0, -XW - 1.6]),
            dict(a=(XW, YN), b=arc[0], posts=[1.6, (YN - arc[0][1]) / 2, YN - arc[0][1] - ca])]
    # the arc meets the front run at an inside corner: one post serves both, standing past
    # the ends of the two runs where their inset lines cross
    d1 = np.array(arc[-1]) - np.array(arc[-2])
    cm = 1.6 * math.tan(abs(math.atan2(d1[1], d1[0])) / 2)
    for k in range(nf):
        last = k == nf - 1
        runs.append(dict(a=arc[k], b=arc[k + 1], posts=[ca, Ls + cm if last else Ls - ca],
                         piers=[ca, Ls - ca]))
    Lf = XE - arc[-1][0]
    ud = DOOR_X - arc[-1][0]
    runs.append(dict(a=arc[-1], b=(XE, FY), posts=[-cm, ud - 12.0, ud + 12.0, Lf - 1.6],
                     piers=[ca, ud - 12.0, ud + 12.0, Lf - 1.6]))
    runs.append(dict(a=(XE, FY), b=(XE, 0.0), posts=[1.6, -FY - 2.8]))
    steps_run = nf + 2
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    PP = FT.porch_turned(ppts, runs, H_floor, post_h, steps_at=[(steps_run, ud, 18.0)],
                         planks=dict(pitch=1.8, border=1.2), joined=True, ledger_off=1.5, post="vase",
                         rail="ringed", arcade="fans", skirt="vents", pier_tex="tuckpoint", roof_edge="billet")
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
        kit.add(f"PORCH-frieze-{k}", "Lavender", arc_, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = union([b.solid(grow=1.8, dz0=-20, dz1=0) for b in (MAIN, TOWER)])
    proof = PP["roof"] - bld_keep - ins_keep
    ptop = proof.bounding_box()[5]
    kit.add("PORCH-roof", "Cream", proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8)), P=print_flip(), group="porch")
    kit.add("PORCH-roof-top", "Brown", proof.trim_by_plane([0, 0, 1.0], ptop - 0.8), group="porch")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PORCH-steps-{k}", "Brick", sm.transform(A) - fkeep - deck, group="porch")
    # the gablet over the steps: a triangle with a raised rim and a sunk round-arched panel
    gw_, gr_ = 11.0, 8.4
    tri = poly([(-gw_, 0.0), (gw_, 0.0), (0.0, gr_)])
    gab = ext(tri, 0.0, 3.0) + ext(tri - tri.offset(-0.8, JoinType.Miter, 4.0), 2.99, 3.6) - \
        ext(arch_cs(-3.0, 3.0, 1.2, 3.6, rise=3.0, seg=24), 2.4, 4.0)
    Ag = np.array([[1.0, 0, 0, DOOR_X], [0, 0, -1.0, FY - 1.4 + 0.4 + 3.0], [0, 1.0, 0, ptop]])
    kit.add("PORCH-gable", "Cream", gab.transform(Ag), P=inv34(Ag), group="porch")
    e, u = MAIN.locate(148.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Brick", FT.steps(14.0, ZF - 0.6, 5).transform(A) - fnd, group="porch")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "juniper")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "juniper.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
