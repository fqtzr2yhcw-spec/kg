"""The Whitmore: an original HO-scale (1:87.1) Georgian Colonial, house 31 and the first of the
third batch (after the user's photo 4).

A red-brick house of five bays in English garden-wall bond (three stretcher courses to a header
course) on a brick foundation under a moulded water table. The centre pavilion steps forward
under a pediment with an oculus; in front of it a portico of two Tuscan columns carries a
balcony railed in Chinese Chippendale fretwork, onto which a round-headed French window opens.
Six-over-six windows sit under splayed stone jack arches (keyed below, plain above) with dark
green louvered-and-panelled shutters; a copper-roofed box bay stands either side of the
entrance. A six-panel door under a five-light transom. Between the storeys a cornice of a cream
frieze hung with Adam husks, a white Wall-of-Troy course and a white ovolo crown; at the eave a
cream frieze of bay-leaf garland, white dentils, a soffit on white block modillions and a white
cyma crown; on each bay a white frieze of reeded tablets and oval paterae under a copper cavetto.
A graduated slate hip roof with two pedimented dormers and two tall end stacks.

usage: python3 -m hoarch.buildings.whitmore [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import colonial as C, cornice as CO, features as FT, gables as G, openings as O, roof as R, skins as SK
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Whitmore"
COLORS = {"Brick": "#8E3B2E", "White": "#EFEDE6", "Cream": "#D9CDB0", "Slate": "#4B5058", "Copper": "#5E9C8A",
          "Green": "#2E4A3C", "Clinker": "#6A2C23", "Windows_Doors": "#EFEDE6"}
RENDER_MAT = {"Brick": "brick", "White": "trim", "Cream": "stone", "Slate": "roof", "Copper": "accent",
              "Green": "shutter", "Clinker": "brick2", "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Whitmore)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="husks", role="Cream"),
    dict(kind="course", h=1.6, b=1.4, orn="troy", role="White"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="ovolo", role="White")])
EAVE = dict(pitch=11.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.6, b=1.2, orn="laurel", role="Cream"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="White", tooth=0.9, gap=0.6),
    dict(kind="bed", h=2.2, b=1.4, P=6.6, role="White", brackets=dict(style="mutule", t=1.3, reach=0.3)),
    dict(kind="crown", h=3.0, b=1.4, P=7.4, orn="cyma", role="White")])
BAY_C = dict(pitch=8.0, margin=2.6, layers=[
    dict(kind="frieze", h=4.0, b=1.2, orn="tablets", role="White"),
    dict(kind="crown", h=2.0, b=1.4, P=3.8, orn="cavetto", role="Copper")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 14.0
S1 = ZF + 42.0
ZE = S1 + RJ + 38.0
ZW = ZE + HE
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 7.8, 3.6, 1.8
S_MAIN, S_PED = 0.8, 0.5
V1 = 8.0
V2 = S1 + RJ + 5.0 - ZF
BAY_LEDGE = ZF + 30.0
BAY_TOP = BAY_LEDGE + CO.band_height(BAY_C)

# ------------------------------------------------------------------ plan (x east, y north; the front faces south)
W, D = 204.0, 112.0
XC = W / 2
PX0, PX1, PY = 78.0, 126.0, -5.0         # the centre pavilion
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
PAV = Block("pavilion", [(PX0, PY), (PX1, PY), (PX1, 3.0), (PX0, 3.0)], ZF, ZW)
BAYS = [Block(f"bay{k}", [(x0, -9.0), (x0 + 32.0, -9.0), (x0 + 32.0, 3.0), (x0, 3.0)], ZF, BAY_TOP)
        for k, x0 in enumerate((10.0, W - 42.0))]
BLOCKS = [MAIN, PAV] + BAYS
# the portico in front of the pavilion: its floor at ZF, its entablature topping out level with the joint
PW, PD = 30.0, 14.0
ENT_H = 5.0
ZPT = S1 + RJ                            # the balcony floor, level with the second floor
COL_R = 2.0
COL_X = (XC - PW / 2 + 2.6, XC + PW / 2 - 2.6)
COL_Y = PY - PD + 2.6
DOOR_W, DOOR_H = 12.0, 32.0


def _brick(f, b, reg):
    """English garden-wall bond: three stretcher courses to every header course. Nothing in
    the cornice bands (the joint's is the belt ring; the eave's and the bays' are cut here)."""
    top = (BAY_LEDGE if b in BAYS else ZE) - b.z0
    reg = reg - rect(-1, top, f.L + 1, (ZW if b in (MAIN, PAV) else 999) - b.z0)
    return SK.brick_bond(reg, "common", header_every=4, datum=1.8)


def _openings():
    L, SH = [], []

    def add(blk, x, y, v0, sp, name, kind="window", shutters=False):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        if shutters:
            SH.append(name)

    lo = C.window_georgian(9.6, 24.0, "keyed", apron=True)
    up = C.window_georgian(9.6, 21.0, "plain")
    bay = C.window_georgian(9.0, 18.0, "plain", lites=(3, 3), rows=(2, 2), A=0.8)
    # front: the bays, a window each side of the pavilion, the door; five across upstairs
    for bk in BAYS:
        x0 = bk.pts[0][0]
        for x in (x0 + 8.4, x0 + 23.6):
            add(bk, x, -9.0, 4.4, bay, f"bay{bk.name[-1]}-{x:.0f}")
    for x in (60.0, W - 60.0):
        add(MAIN, x, 0.0, V1, lo, f"S{x:.0f}-1", shutters=True)
    add(PAV, XC, PY, 0.4, C.door_georgian(DOOR_W, DOOR_H), "front-door", "door")
    for x in (26.0, 60.0, W - 60.0, W - 26.0):
        add(MAIN, x, 0.0, V2, up, f"S{x:.0f}-2", shutters=True)
    add(PAV, XC, PY, ZPT - ZF + 0.4, C.door_venetian(13.0, 30.0), "balcony-door", "door")
    add(PAV, XC, PY, Z_EAVE - ZF + 2.2, C.window_oculus(5.4), "oculus")
    # the ends
    for x_ in (0.0, W):
        for y in (32.0, 80.0):
            add(MAIN, x_, y, V1, lo, f"{'W' if x_ == 0 else 'E'}{y:.0f}-1", shutters=True)
            add(MAIN, x_, y, V2, up, f"{'W' if x_ == 0 else 'E'}{y:.0f}-2", shutters=True)
    # the back
    for x in (26.0, 60.0, W - 60.0, W - 26.0):
        add(MAIN, x, D, V1, lo, f"N{x:.0f}-1", shutters=True)
        add(MAIN, x, D, V2, up, f"N{x:.0f}-2", shutters=True)
    add(MAIN, XC, D, 0.4, C.door_georgian(11.0, 28.0, transom=4.0), "back-door", "door")
    add(MAIN, XC, D, V2, up, f"N{XC:.0f}-2", shutters=True)
    return L, SH


OPENINGS, SHUTTERED = _openings()


def portico():
    """The entrance portico: a stone floor with steps, two Tuscan columns (printed upright),
    two pilasters against the pavilion, an entablature with a flat deck (printed upside down)
    and a Chippendale railing round the balcony on the deck (three runs, printed on their backs).
    Returns dict of world solids."""
    from hoarch.porchwork import _revolve
    x0, x1 = XC - PW / 2, XC + PW / 2
    y0, y1 = PY - PD, PY
    zc0 = ZF
    zcol = ZPT - ENT_H                    # the columns' top, under the architrave
    hcol = zcol - zc0
    prof = [(0.0, 0.0), (COL_R + 0.6, 0.0), (COL_R + 0.6, 0.8), (COL_R + 0.2, 1.2), (COL_R + 0.2, 1.6), (COL_R, 1.8),
            (COL_R * 0.86, hcol - 2.4), (COL_R * 0.86 + 0.2, hcol - 2.0), (COL_R * 0.86, hcol - 1.8),
            (COL_R + 0.3, hcol - 1.2), (COL_R + 0.6, hcol - 0.8), (COL_R + 0.6, hcol), (0.0, hcol)]
    col = _revolve(prof, 36)
    cols = [col.translate([x, COL_Y, zc0]) for x in COL_X]
    pil = [box([x - 1.6, y1 - 0.8, zc0], [x + 1.6, y1, zcol]) + box([x - 2.0, y1 - 1.0, zc0], [x + 2.0, y1, zc0 + 1.6])
           + box([x - 2.0, y1 - 1.0, zcol - 1.2], [x + 2.0, y1, zcol]) for x in COL_X]
    # the entablature: an architrave band, a plain frieze, a cornice with dentils; a flat deck
    ent = box([x0, y0, zcol], [x1, y1, zcol + 1.6]) + box([x0 - 0.4, y0 - 0.4, zcol + 1.6], [x1 + 0.4, y1, zcol + 3.4])
    cor = M.hull_points([(x, y, zcol + 3.4) for x in (x0 - 0.4, x1 + 0.4) for y in (y0 - 0.4, y1)] +
                        [(x, y, ZPT) for x in (x0 - 2.0, x1 + 2.0) for y in (y0 - 2.0, y1)])
    ent = ent + cor
    teeth = union([box([x - 0.35, y0 - 1.0, zcol + 3.0], [x + 0.35, y0 - 0.39, zcol + 3.6])
                   for x in np.arange(x0 + 0.8, x1 - 0.5, 1.4)])
    ent = ent + teeth
    floor = box([x0 - 1.0, y0 - 1.0, 0.0], [x1 + 1.0, y1 + 0.02, ZF])
    # the Chippendale railing round the balcony: a front run and two returns to the wall
    hr = 7.0
    rails = []
    front = C.chippendale_panel(PW + 3.6, hr, t=1.2)
    A = np.array([[1.0, 0, 0, x0 - 1.8], [0, 0, -1.0, y0 - 1.8 + 1.2], [0, 1.0, 0, ZPT]])
    rails.append((front.transform(A), A))
    for sg, xs in ((-1, x0 - 1.8), (1, x1 + 1.8 - 1.2)):
        side = C.chippendale_panel(PD - 0.6 + 0.2, hr, t=1.2, n=1)
        As = np.array([[0, 0, 1.0, xs], [1.0, 0, 0, y0 - 1.8 + 1.2 + 0.02], [0, 1.0, 0, ZPT]])
        rails.append((side.transform(As), As))
    return dict(cols=cols, pilasters=pil, ent=ent, floor=floor, rails=rails)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    r = RAKE - D_EAVE
    zcf = Z_EAVE + S_PED * ((PX1 - PX0) / 2 + D_EAVE)
    gy = (zcf - Z_EAVE) / S_MAIN - D_EAVE + 4.0
    base = cs_union([MAIN.cs, PAV.cs])
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN),
              ([(PX0, PY - r), (PX1, PY - r), (PX1, gy), (PX0, gy)], [1, 2, 3], S_PED)]
    specs = [dict(p0=(PX0, PY), p1=(PX1, PY), slope=S_PED, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture="graduated", tex_kw=dict(pitch=1.7, wtab=2.2, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    wf = rf["walls"][0]
    gables = [(PAV, 0, wf["cs"].translate((0.0, Z_EAVE - ZF)))]
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)] + \
        [slab(offset(bk.cs, 8.0) ^ rect(0.0, -200.0, 400.0, -0.6), BAY_LEDGE - LEDGE - 0.6, BAY_TOP + 0.01) for bk in BAYS] + \
        [box([PX0 - 1.0, PY - 3.0, ZW - 0.2], [PX1 + 1.0, PY + 1.0, Z_EAVE + 40.0])] + \
        [box([x - 2.3, PY - 3.0, ZF - 1.0], [x + 2.3, PY + 1.0, ZPT + 0.2]) for x in COL_X]
    allcs = cs_union([b_.cs for b_ in BLOCKS])
    clear = [lip_keep(allcs, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_brick, gables=gables, clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((XC - 20.0, 3.0), (XC - 20.0, D - 3.0), 2.0, ZF, ZW)])
    ledges_b = union([CO.ledge(bk.pts, BAY_LEDGE, LEDGE) - MAIN.solid(grow=0.2, dz0=-1, dz1=1) for bk in BAYS])
    kit.add("WALLS-1", "Brick", st["shells"][0] + ledges_b, group="walls")
    ledge_cut = box([XC - PW / 2 - 2.6, PY - 6.0, S1 - 1.0], [XC + PW / 2 + 2.6, PY - 0.02, S1 + RJ + 1.0])
    kit.add("JOINT", "Brick", st["rings"][0] - ledge_cut, group="walls")
    eave_path = max(base.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    no_lip = box([PX0 - D_EAVE - 0.6, PY - 1, ZW - 1], [PX1 + D_EAVE + 0.6, PY + 5.0, ZW + 5])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    kit.add("WALLS-2", "Brick", st["shells"][1] + lip + CO.ledge(eave_path, ZE, LEDGE), group="walls")

    # the portico (its box cuts the joint cornice where it meets the pavilion)
    PO = portico()
    port_keep = box([XC - PW / 2 - 2.6, PY - PD - 2.6, ZF], [XC + PW / 2 + 2.6, PY + 0.02, ZPT + 0.4])
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=port_keep)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    for k, bk in enumerate(BAYS):
        rings, _ = CO.level(bk.pts, BAY_LEDGE, BAY_C, cut=MAIN.solid(grow=0.7, dz0=-2, dz1=2))
        CO.add_level(kit, rings, f"CORNICE-B{k}", "bay")
    fnd = foundation(BLOCKS, 0.0, ZF, style="watertable")
    kit.add("FOUNDATION", "Clinker", fnd, group="foundation")

    # windows, doors and shutters
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{o.v0 > 20}", group="inserts", render=zones))
        if o.name in SHUTTERED:
            w_op, h_op = b[2] - b[0], b[3] - b[1]
            left, right = C.shutters_pair(w_op, h_op, casing=1.0, gap=0.7)
            for side, m in (("L", left), ("R", right)):
                kit.add(f"SHUTTER-{o.name}-{side}", "Green", m.translate([0, 0, 0.32]).transform(A), P=inv34(A),
                        key=f"SHUTTER-{h_op:.1f}", group="shutters")
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the roof: graduated slate on a hip, with the pediment's gable over the pavilion
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    caps = [G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZW, half=1.2, up=0.6)]
    walls_env = wf["facade"].place(M.extrude(wf["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
    fy = gy + D_EAVE - (zcf - Z_EAVE) / S_PED
    caps.append(G.ridge_cap((XC, PY - RAKE), (XC, fy + 0.4), zcf, S_PED, ZW, half=1.0, up=0.5))
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.2, up=0.6, drop=1.8)
                  for c, e in zip(corners, ends)])
    roof = roof + ((union(caps) + hips) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW)
    # the gable wall's apex stands into the shallow pediment roof: the roof is cut round it
    apex_box = box([PX0, PY - 1.0, Z_EAVE], [PX1, PY + 4.0, Z_EAVE + 30.0])
    roof = roof - (st["shells"][1] ^ apex_box)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    # two tall end stacks
    CW, CD = 7.0, 15.0
    chims = [(10.0, D / 2), (W - 10.0, D / 2)]
    pockets, stacks = [], []
    for (cx, cy) in chims:
        zroof = Z_EAVE + S_MAIN * (min(cx, W - cx) - CW / 2 + D_EAVE)
        z0 = round((zroof - 3.0) / 0.2) * 0.2
        roof = roof + G.chimney_seat(solid_env, cx, cy, max(CW, CD) / 2, zr + 1.0)
        pockets.append(box([cx - CW / 2 - 0.4, cy - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CD / 2 + 0.4, zr + 40]))
        stacks.append(C.chimney_georgian(CW, CD, zr + 8.0 - z0).translate([cx, cy, z0]))
    roof = roof - union(pockets)
    # two pedimented dormers on the front slope
    DW, DDEP, DHW = 17.0, 18.0, 14.4
    dyf = 18.0
    zdf = round((Z_EAVE + S_MAIN * (dyf + D_EAVE) - 1.0) / 0.2) * 0.2
    dbody, dcore, dface = C.dormer_pedimented(DW, DDEP, DHW)
    drise = DW / 2 * 0.62
    dkeeps, dparts = [], []
    for dxc in (50.0, W - 50.0):
        Ad = np.array([[1.0, 0, 0, dxc], [0, 0, -1.0, dyf], [0, 1.0, 0, zdf]])
        dkeep = ext(dface.offset(0.3, JoinType.Miter, 4.0), -DDEP - 0.3, 0.3).transform(Ad)
        dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
        dseat = box([dxc - DW / 2 - 1.3, dyf - 1.6, ZW], [dxc + DW / 2 + 1.3, dyf + DDEP + 1.3, zdf]) ^ solid_env
        dkeeps.append((dpocket, dseat))
        dparts.append(Ad)
    for dpocket, dseat in dkeeps:
        roof = roof - dpocket
    for dpocket, dseat in dkeeps:
        roof = roof + (dseat - dpocket - lip_keep(base, 3.0, ZW))
    kit.add("ROOF", "Slate", roof, group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Brick", s_, key="CHIMNEY", group="roof")
    ez = DHW - 1.6 * 0.62
    droof_cs = poly([(-DW / 2 - 1.6, ez), (-DW / 2, ez), (-DW / 2, DHW), (0.0, DHW + drise + 0.2), (DW / 2, DHW),
                     (DW / 2, ez), (DW / 2 + 1.6, ez), (DW / 2 + 1.6, ez + 1.6), (0.0, DHW + drise + 2.2),
                     (-DW / 2 - 1.6, ez + 1.6)])
    for k, Ad in enumerate(dparts):
        kit.add(f"DORMER-{k}", "White", dbody.transform(Ad), key="DORMER", group="roof")
        kit.add(f"DORMER-core-{k}", "Slate", dcore.transform(Ad), key="DORMER-core", group="roof")
        droof = ext(droof_cs, -DDEP - 6.0, 1.2).transform(Ad) - solid_env - dbody.transform(Ad) - roof
        kit.add(f"DORMER-roof-{k}", "Slate", droof, key="DORMER-roof", group="roof")
    # the pediment's tympanum: a white panel on the gable wall round the oculus (0.8 thick,
    # printed on its back), stopping under the roof's rakes
    ocul = next(p for p in inserts if p is not None and p.name == "WIN-oculus")
    apex = Z_EAVE + S_PED * (XC - PX0)
    tri = poly([(PX0 + 0.6, ZW + 0.2), (PX1 - 0.6, ZW + 0.2), (XC + (PX1 - 0.6 - XC) * 0.0, apex)]) + \
        poly([(PX0 + 0.6, ZW + 0.2), (PX1 - 0.6, ZW + 0.2), (PX1 - 0.6, Z_EAVE + 0.2), (XC, apex), (PX0 + 0.6, Z_EAVE + 0.2)])
    At = np.array([[1.0, 0, 0, 0], [0, 0, -1.0, PY], [0, 1.0, 0, 0]])      # (x, z, out) -> world
    ty = M.extrude(tri, 0.8).transform(At)
    # the raking cornices: a moulded band under each rake, out to the roof's edge, dentils under it
    rk = []
    for sg in (-1, 1):
        xe = XC + sg * (XC - PX0 + RAKE)
        ze = Z_EAVE - S_PED * RAKE
        top = [(xe, ze + 1.4), (XC, apex + 1.4)]
        band = poly([top[0], top[1], (XC, apex - 2.4), (xe, ze - 2.4)])
        rk.append(M.extrude(band, RAKE - 0.3).transform(At))
        rk.append(M.extrude(band.offset(-0.6, JoinType.Miter, 4.0), RAKE + 0.3).transform(At))
        n = int(abs(XC - xe) / 1.5)
        for k in range(1, n):
            x = xe + (XC - xe) * k / n
            z = ze + (apex - ze) * k / n - 2.4
            rk.append(M.extrude(rect(x - 0.35, z - 0.7, x + 0.35, z + 0.1), 1.6).translate([0, 0, 0.8]).transform(At))
    ty = (ty + union(rk)) ^ box([-500, -500, ZW + 0.2], [500, 500, 999])
    ty = ty - union([p.solid for p in kit.parts if p.name.startswith("CORNICE-E")])
    ty = ty - union([ocul.solid.translate(v) for v in ((0.25, 0, 0), (-0.25, 0, 0), (0, 0, 0.25), (0, 0, -0.25))]) - roof
    kit.add("PEDIMENT", "White", max(ty.decompose(), key=lambda m_: m_.volume()), P=inv34(At), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the bays' copper roofs
    for k, bk in enumerate(BAYS):
        keep = MAIN.solid(grow=0.45, dz0=-1, dz1=300)
        broof, btex = R.hip_roof([(bk.pts, [0, 1, 3])], BAY_TOP, 0.9, BAY_C["layers"][-1]["P"] + 0.2, texture="seam",
                                 flat_top=S1 - 0.4, tex_kw=dict(seam_pitch=2.6), zlo=BAY_TOP)
        kit.add(f"BAY-roof-{k}", "Copper", (broof + btex) - keep, key="BAY-roof", group="bay")

    # --- the portico
    for k, p_ in enumerate(PO["pilasters"]):
        kit.add(f"PORTICO-pilaster-{k}", "White", p_ - st["rings"][0], P=inv34(np.array([[1.0, 0, 0, 0], [0, 0, -1.0, PY], [0, 1.0, 0, 0]])),
                key="PORTICO-pilaster", group="portico")
    # the entablature and both columns in one piece, printed upside down on the flat deck: each
    # column's foot drops into a snug recess in the floor, so no column is glued on its own
    zcol = ZPT - ENT_H
    seats = [FT.column_seats(x, COL_Y, ZF, zcol, ("round", COL_R + 0.6)) for x in COL_X]
    tie = union([M.cylinder(0.21, COL_R + 0.6, COL_R + 0.6, 36).translate([x, COL_Y, zcol - 0.01]) for x in COL_X])
    ent = (PO["ent"] + union(PO["cols"]) + tie + union([a_ for a_, _, _ in seats])) - PAV.solid(grow=0.0, dz0=-1, dz1=1)
    kit.add("PORTICO-top", "White", ent, P=print_flip(), group="portico")
    kit.add("PORTICO-floor", "Cream", PO["floor"] - fnd - union([f_ for _, f_, _ in seats]), group="portico")
    for k, (rl, A) in enumerate(PO["rails"]):
        kit.add(f"BALCONY-rail-{k}", "White", rl, P=inv34(A), group="portico")
    fr = PAV.facades()[0]
    A = fr.A.copy()
    A[:, 3] = fr.world(XC - PX0, -ZF, PD + 1.0)
    kit.add("STEPS-front", "Cream", FT.steps(22.0, ZF - 0.6, 5, cheek=1.8).transform(A) - fnd, group="portico")
    e, u = MAIN.locate(XC, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Cream", FT.steps(15.0, ZF - 0.6, 5).transform(A) - fnd, group="portico")
    print("specks dropped:", kit.drop_specks())
    print("portico", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "whitmore")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "whitmore.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
