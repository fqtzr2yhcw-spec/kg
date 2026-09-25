"""The Larkspur -- an original HO-scale (1:87.1) Queen Anne, after the user's photo of a
turquoise house with a round tower and a loggia. Rev B: the house-size plan (196 x 136 mm,
storeys of 42 and 38 mm), framed windows spaced along the walls, built-up cornices at every
level, a gabled dormer in place of the little turret, and the wing's attic window clear of its
pediment.

Turquoise chamfered lap siding below and chisel-pointed shingles above an astragal
belt, on a rock-faced base of drafted stone, with reveal corner boards. A gabled wing steps
forward on the west with a closed Free Classic pediment, a sunburst fan over an arched attic
light in its gable. A round tower
stands out of the east front corner, rising a storey above the eaves to a bracketed eave and
a bell-cast slate cone with a lance finial. Between them, over the porch, a loggia is sunk
into the upper storey behind an arcade of columns with a railing. A gabled dormer with a
framed round-headed window sits on the hip roof of plain square slate; a tall clustered brick
chimney. Built-up cornices: between the storeys a navy running-wave frieze, a cream scalloped
course and a cream cyma-reversa crown; at the eave a navy frieze of rosettes, a cream dentil
course, a cream soffit on cove brackets and a navy cavetto crown; round the tower a navy frieze
of scrolls, a cream soffit on cove brackets and a cream stepped crown. A porch wraps the front and curves round the tower on paired columns, with
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
from hoarch import cornice as CO, features as FT, gables as G, openings as O, roof as R, skins as SK, storefront as SF, \
    trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext, stroke
from hoarch.shell import _stepped
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Larkspur"
COLORS = {"Aqua": "#3FAAB4", "Cream": "#EFE7D2", "Navy": "#23345A", "Slate": "#4A4F57", "Stone": "#8C8378",
          "Brick": "#8A4232", "PorchDeck": "#8C8378", "Windows_Doors": "#EFE7D2"}
RENDER_MAT = {"Aqua": "siding", "Cream": "trim", "Navy": "navy", "Slate": "roof", "Stone": "stone", "Brick": "brick",
              "PorchDeck": "stone", "Planks": "planks", "Windows_Doors": "trim", "Sash": "sash", "Door": "door",
              "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Larkspur)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.2, b=1.2, orn="wave", role="Navy"),
    dict(kind="course", h=1.8, b=1.4, orn="scallop", role="Cream"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="reverse", role="Cream")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.6, b=1.2, orn="rosettes", role="Navy"),
    dict(kind="course", h=1.4, b=1.4, orn="dentil", role="Cream", tooth=0.7, gap=0.5),
    dict(kind="bed", h=2.0, b=1.4, P=6.2, role="Cream", brackets=dict(style="cove", t=0.9, reach=0.55)),
    dict(kind="crown", h=2.8, b=1.4, P=7.0, orn="cavetto", role="Navy")])
TOWER_C = dict(pitch=8.0, margin=2.6, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="scrolls", role="Navy"),
    dict(kind="bed", h=1.8, b=1.4, P=5.0, role="Cream", brackets=dict(style="cove", t=0.8, reach=0.7)),
    dict(kind="crown", h=2.2, b=1.4, P=5.8, orn="stepped", role="Cream")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 14.0
S1 = ZF + 42.0                  # first-storey shell top = the joint ring's foot
RH = RJ
ZE = S1 + RJ + 38.0             # the eave ledge's top
ZW = ZE + HE                    # the wall top behind the eave cornice; the roof sits here
ZT = ZW + 38.0                  # the tower's cornice ledge
ZTW = ZT + CO.band_height(TOWER_C)
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 7.4, 4.2, 1.8
S_MAIN, S_WING = 1.0, 1.4
V1 = 8.0
V2 = S1 + RJ + 5.0 - ZF

# ------------------------------------------------------------------ plan
W, D = 196.0, 136.0
WX, WD = 76.0, 28.0             # the west wing: its width and how far it steps forward
LX0, LX1, LD = 92.0, 146.0, 14.0  # the loggia: its span and depth into the upper storey
GY = 56.0                       # how far the wing's gable roof runs back into the hip
TC, TR = (186.0, -8.0), 28.0    # the round tower's centre and radius (a 16-sided drum)
MAIN_LO = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, S1)
MAIN_HI = Block("upper", [(0, 0), (LX0, 0), (LX0, LD), (LX1, LD), (LX1, 0), (W, 0), (W, D), (0, D)], S1, ZW)
WING = Block("wing", [(0, -WD), (WX, -WD), (WX, 3.0), (0, 3.0)], ZF, ZW)
TOWER = Block("tower", ngon(TC, TR, n=16), ZF, ZTW)
BLOCKS = [MAIN_LO, MAIN_HI, WING, TOWER]
DOOR_X = 114.0
DOOR_W, DOOR_H = 13.0, 30.0
GWIN = (9.6, 16.0)              # the wing's arched attic light (w, h)


def _siding(f, b, reg):
    """Chamfered lap siding on the first storey, chisel-pointed shingles above the joint;
    nothing behind the cornices."""
    cut = S1 - b.z0
    top = (ZT if b is TOWER else ZE) - b.z0
    reg = reg - rect(-1, top, f.L + 1, (ZTW if b is TOWER else ZW) - b.z0)
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

    def win(w, h, head="pent", rise=0):
        return SF.window_commercial(w, h, rise=rise, lites=(1, 3), rows=(1, 3), sill=1.2, head=head, casing=1.3,
                                    band=True)

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    v2 = V2 - (S1 - ZF)
    # the wing: a pair below and above, an arched light in the gable under the pediment's fan
    for x in (WX / 2 - 14.0, WX / 2 + 14.0):
        add(WING, x, -WD, V1, win(8.4, 24.0), f"wing{x:.0f}-1")
        add(WING, x, -WD, V2, win(8.4, 21.0), f"wing{x:.0f}-2")
    add(WING, WX / 2, -WD, ZW - ZF + 6.0, win(GWIN[0], GWIN[1], head=None, rise=GWIN[0] / 2), "wing-gable")
    # the main front: the door, a window beside it, and inside the loggia a door and a window
    add(MAIN_LO, DOOR_X, 0.0, 0.0, SF.door_commercial(DOOR_W, DOOR_H, transom=5.0, leaf="cameo", tstyle="wave",
                                                     head=None, leaves=2), "door", "door")
    add(MAIN_LO, 138.0, 0.0, V1, win(8.4, 24.0), "F138-1")
    add(MAIN_HI, 106.0, LD, RH, SF.door_commercial(10.0, 29.0, transom=4.2, leaf="cameo", tstyle="wave",
                                                                  head=None), "loggia-door", "door")
    add(MAIN_HI, 132.0, LD, v2, win(8.4, 21.0, head=None), "loggia-win")
    # the west side, the east side behind the tower, the back
    for y in (26.0, 66.0, 106.0):
        add(MAIN_LO, 0.0, y, V1, win(8.4, 24.0), f"W{y:.0f}-1")
        add(MAIN_HI, 0.0, y, v2, win(8.4, 21.0), f"W{y:.0f}-2")
    for y in (72.0, 110.0):
        add(MAIN_LO, W, y, V1, win(8.4, 24.0), f"E{y:.0f}-1")
        add(MAIN_HI, W, y, v2, win(8.4, 21.0), f"E{y:.0f}-2")
    add(MAIN_LO, 38.0, D, 0.0, SF.door_commercial(10.0, 29.0, transom=4.2, leaf="cameo", tstyle="wave", head=None),
        "back-door", "door")
    for x in (78.0, 118.0, 158.0):
        add(MAIN_LO, x, D, V1, win(8.4, 24.0), f"B{x:.0f}-1")
    for x in (38.0, 78.0, 118.0, 158.0):
        add(MAIN_HI, x, D, v2, win(8.4, 21.0), f"B{x:.0f}-2")
    # the tower: framed tall lights on the faces clear of the house, three storeys
    tw = win(7.2, 22.0, head=None)
    tw3 = win(7.2, 18.0, head=None)
    for k, f in enumerate(TOWER.facades()):
        m = (f.p0 + f.p1) / 2
        clear = (MAIN_LO.cs ^ rect(m[0] + f.n[0] * 3 - 3, m[1] + f.n[1] * 3 - 3, m[0] + f.n[0] * 3 + 3,
                                   m[1] + f.n[1] * 3 + 3)).is_empty()
        if not clear or k % 2:
            continue
        add(TOWER, m[0], m[1], V1, tw, f"tower{k}-1")
        add(TOWER, m[0], m[1], V2, tw, f"tower{k}-2")
        if f.n[1] < 0.3:
            add(TOWER, m[0], m[1], ZT - ZF - 25.0, tw3, f"tower{k}-3")
    return L


OPENINGS = _openings()


def loggia_screen():
    """The loggia's front: an arcade of three round arches on two columns and two end
    pilasters, a low railing of flat balusters between the column bases, and the spandrel
    wall over the arches up to the wall top, with the eave cornice's ledge on its face and a
    plain band above it. Built lying on its back in (u along the loggia, v up from the loggia
    floor, w out of the recess from its back at w = 0 to the front at w = 3); prints on its
    back: the columns are round to the front and flat behind, and the railing lies flush with
    the back."""
    L = LX1 - LX0
    Hs = ZW - (S1 + RH)
    vE = ZE - (S1 + RH)                       # the eave ledge's top on the screen
    t = 3.0
    ucol = [L / 3, 2 * L / 3]
    spring = vE - 16.0
    # the spandrel wall with the three arches cut out of it
    wall = rect(0.0, spring - 1.0, L, Hs)
    holes = []
    edges = [0.0] + ucol + [L]
    for a, b in zip(edges[:-1], edges[1:]):
        a2, b2 = a + (2.2 if a == 0.0 else 1.8), b - (2.2 if b == L else 1.8)
        holes.append(arch_cs(a2, b2, -5.0, spring, rise=(b2 - a2) / 2, seg=32))
    body = ext(wall - cs_union(holes), 0.0, t)
    # archivolts: a raised ring round each arch
    for hcs in holes:
        body = body + ext((hcs.offset(1.0) - hcs) ^ rect(-1, spring, L + 1, vE - LEDGE - 0.6), t - 0.01, t + 0.6)
    # the eave cornice's ledge across the screen (face-up here: a chamfered strip)
    body = body + ext(rect(0.0, vE - LEDGE - 0.4, L, vE), t - 0.01, t + LEDGE)
    # the end pilasters and the columns (half round, flat-backed, on square plinths)
    for u0, u1 in ((0.0, 2.2), (L - 2.2, L)):
        body = body + box([u0, 0.0, 0.0], [u1, spring, t])
    for u in ucol:
        body = body + box([u - 2.2, 0.0, 0.0], [u + 2.2, 2.4, t]) + box([u - 2.2, spring - 2.4, 0.0], [u + 2.2, spring, t])
        # the shaft: flat-backed on the bed, round to the front (a D in section), so it prints on its back
        dcs = cs_union([rect(-1.6, 0.0, 1.6, 1.6), circle((0.0, 1.6), 1.6, 28) ^ rect(-2, 1.6, 2, 3.6)])
        shaft = M.extrude(dcs, spring - 4.8).transform(np.array([[1.0, 0, 0, u], [0, 0, 1.0, 2.4], [0, 1.0, 0, 0.0]]))
        body = body + shaft
    # the railing between the column bases: a rail, a bottom rail and flat balusters with a bead
    rh = 10.0
    for a, b in zip(edges[:-1], edges[1:]):
        a2, b2 = a + 2.2, b - 2.2
        cells = [rect(a2, 0.6, b2, 1.6), rect(a2, rh - 1.2, b2, rh)]
        n = max(2, int((b2 - a2) / 1.8))
        for k in range(n):
            u = a2 + (b2 - a2) * (k + 0.5) / n
            cells.append(cs_union([rect(u - 0.35, 1.5, u + 0.35, rh - 1.1), circle((u, rh / 2), 0.6, 16)]))
        body = body + ext(cs_union(cells), 0.0, 1.8)                  # flush with the back: it prints on the bed
    return body


def dormer_gabled(w=26.0, dep=34.0, hwall=16.0, slope=1.2):
    """A gabled dormer's body: a box with a flat bottom (it drops into a pocket in the roof and
    sits on a seat), its front wall 1.2 thick rising into a gable, carrying one round-headed
    light in a raised stepped frame with a sill, a meeting rail and a fan of bars in the head,
    over a dark core. Local: u across (centred), v up from its foot, w out (the face at w = 0).
    Returns (body, core, apex_v)."""
    from hoarch.core import arch_cs
    apex = hwall + slope * w / 2
    front = poly([(-w / 2, 0.0), (w / 2, 0.0), (w / 2, hwall), (0.0, apex), (-w / 2, hwall)])
    body = box([-w / 2, 0.0, -dep], [w / 2, hwall, 0.0]) - box([-w / 2 + 1.2, 1.2, -dep - 1], [w / 2 - 1.2, hwall + 1, -1.2])
    body = body + ext(front, -1.2, 0.0)
    lw, lh = 10.0, hwall + 2.0
    light = arch_cs(-lw / 2, lw / 2, 2.4, lh - lw / 2, seg=28)
    body = body - ext(light, -1.3, 1.0)
    frame = light.offset(1.0, JoinType.Round) - light
    body = body + _stepped(frame ^ rect(-w / 2, 1.8, w / 2, apex - 2.0), -0.01, 0.6)
    mr = 2.4 + (lh - lw / 2 - 2.4) * 0.5
    body = body + ext(rect(-lw / 2, mr - 0.35, lw / 2, mr + 0.35), -1.2, -0.4)               # the meeting rail
    for a_ in np.linspace(math.radians(35), math.radians(145), 3):                           # a fan in the head
        body = body + ext(stroke([(0.0, lh - lw / 2), (8.0 * math.cos(a_), lh - lw / 2 + 8.0 * math.sin(a_))], 0.5,
                                 caps=False) ^ light, -1.2, -0.4)
    body = body + ext(rect(-lw / 2 - 1.4, 1.4, lw / 2 + 1.4, 2.4), -0.01, 1.2)               # the sill
    core = box([-w / 2 + 1.2, 1.2, -dep + 1.2], [w / 2 - 1.2, hwall - 0.4, -1.2])
    return body, core, apex


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
    eave_cs = cs_union([MAIN_LO.cs, WING.cs])
    eave_path = max(eave_cs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(eave_cs, 8.0) - offset(TOWER.cs, 1.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="reveal", siding=_siding, gables=gables,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    # the loggia floor over the porch: a slab filling the recess at the upper floor's level,
    # carried on a 45 degree web off the front wall so the belt prints clean
    lfloor = slab(rect(LX0, -0.01, LX1, LD), S1, S1 + RH) - \
        ext(poly([(3.0, S1 - 0.01), (LD + 0.01, S1 - 0.01), (LD + 0.01, S1 + min(LD - 3.0, RH - 1.6)),
                  (3.0 + min(LD - 3.0, RH - 1.6), S1 + min(LD - 3.0, RH - 1.6))]), LX0 - 1, LX1 + 1).transform(
            np.array([[0, 0, 1.0, 0], [1.0, 0, 0, 0], [0, 1.0, 0, 0]]))
    # the joint cornice's ledge across the loggia's front, on the loggia floor
    lledge = ext(poly([(0.0, S1), (-LEDGE, S1 + LEDGE), (-LEDGE, S1 + LEDGE + 0.4), (0.0, S1 + LEDGE + 0.4)]), LX0, LX1)
    lledge = lledge.transform(np.array([[0, 0, 1.0, 0], [1.0, 0, 0, 0], [0, 1.0, 0, 0]]))
    kit.add("WALLS-1", "Aqua", st["shells"][0], group="walls")
    kit.add("JOINT", "Aqua", st["rings"][0] + ((lfloor + lledge) - st["shells"][0] - st["shells"][1]), group="walls")
    tkeep = TOWER.solid(grow=0.2, dz0=-1, dz1=1)
    no_lip = union([box([-D_EAVE - 0.6 - 1, -WD - 1, ZW - 1], [WX + D_EAVE + 0.6, -WD + 5.0, ZW + 5]),
                    tkeep, slab(offset(TOWER.cs, 1.0), ZW - 1, ZW + 5)])
    top_cs = cs_union([MAIN_HI.cs, WING.cs])
    lip = (_corbel(top_cs, 3.0, ZW) + lip_ring(top_cs, 3.0, ZW)) - no_lip
    base = cs_union([b.cs for b in BLOCKS])
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN_LO.cs, -3.05), S1 + RH, ZW + 1.2)
    tring = tring - lip_keep(base, 3.0, S1 + RH)
    loggia_front = box([LX0 - 0.01, -8.0, ZE - 10.0], [LX1 + 0.01, LD, ZW + 1.0])     # the screen carries its own ledge
    ledges = (CO.ledge(eave_path, ZE, LEDGE) - tkeep - loggia_front) + CO.ledge(TOWER.pts, ZT, LEDGE)
    kit.add("WALLS-2", "Aqua", st["shells"][1] + lip + tring + ledges, group="walls")
    jpath = max(cs_union([MAIN_LO.cs, WING.cs, TOWER.cs]).to_polygons(), key=lambda L_: abs(poly(L_).area()))
    for tag, path, z0, spec, cut in (("J", jpath, S1 + LEDGE + 0.4, JOINT, st["rings"][0]),
                                     ("E", eave_path, ZE, EAVE, TOWER.solid(grow=1.1, dz0=-2, dz1=2)),
                                     ("T", TOWER.pts, ZT, TOWER_C, None)):
        rings, _ = CO.level(path, z0, spec, cut=cut)
        CO.add_level(kit, rings, f"CORNICE-{tag}", "tower" if tag == "T" else "cornice")
    fnd = foundation([MAIN_LO, WING, TOWER], 0.0, ZF, style="drafted")
    kit.add("FOUNDATION", "Stone", fnd, group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
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
    caps = [G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZW)]
    walls_env = wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
    zc = Z_EAVE + S_WING * (WX / 2 + D_EAVE)
    y_meet = (zc - Z_EAVE) / S_MAIN - D_EAVE + 1.0
    caps.append(G.ridge_cap((WX / 2, -WD - RAKE), (WX / 2, y_meet), zc, S_WING, ZW))
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.6, up=0.9, drop=2.2)
                  for c, e in zip(corners, ends)])
    roof = roof + ((union(caps) + hips) - walls_env)
    roof = roof - lip_keep(top_cs, 3.0, ZW)
    roof = roof.trim_by_plane([0, 0, 1.0], ZW)                # nothing below the wall top (the hip caps' drops)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    # the chimney, and the gabled dormer's pocket and seat on the front slope
    CW, CD = 16.0, 8.0
    cx, cy = 158.0, 88.0
    zroof = Z_EAVE + S_MAIN * min(cy - CD / 2 + D_EAVE, D + D_EAVE - cy - CD / 2, W + D_EAVE - cx - CW / 2)
    z0 = round((zroof - 3.0) / 0.2) * 0.2
    roof = roof + G.chimney_seat(solid_env, cx, cy, CW / 2, zr + 1.0)
    pocket = box([cx - CW / 2 - 0.4, cy - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CD / 2 + 0.4, zr + 40])
    DW, DDEP, DHW, DS = 26.0, 34.0, 16.0, 1.2
    dx, dyf = (LX0 + LX1) / 2, 18.0
    zdf = ZW + round((Z_EAVE - ZW + S_MAIN * (dyf + D_EAVE) - 1.0) / 0.2) * 0.2
    Ad = np.array([[1.0, 0, 0, dx], [0, 0, -1.0, dyf], [0, 1.0, 0, zdf]])
    dbody, dcore, dapex = dormer_gabled(DW, DDEP, DHW, DS)
    dface = poly([(-DW / 2, 0.0), (DW / 2, 0.0), (DW / 2, DHW), (0.0, dapex), (-DW / 2, DHW)])
    dkeep = ext(dface.offset(0.3, JoinType.Miter, 4.0), -DDEP - 0.3, 0.3).transform(Ad)     # the pocket follows the dormer
    dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
    dseat = box([dx - DW / 2 - 1.3, dyf - 1.6, ZW], [dx + DW / 2 + 1.3, dyf + DDEP + 1.3, zdf]) ^ solid_env
    roof = roof - pocket - dpocket - slab(offset(TOWER.cs, 1.4), ZW - 1, ZTW + 90) + (dseat - dpocket - lip_keep(top_cs, 3.0, ZW))
    kit.add("ROOF", "Slate", roof, group="roof")
    ch = TW.chimney("clustered", w=CW, d=CD, h=round((zr + 16.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    # the pediment: its fan rises over the arched attic light and keeps clear of it
    gw_, gh_ = GWIN
    v_win = ZW + 6.0 - Z_EAVE                                  # the light's foot in the ornament's frame
    spring_ = v_win + gh_ - gw_ / 2
    clear = arch_cs(wl["L"] / 2 - gw_ / 2 - 2.2, wl["L"] / 2 + gw_ / 2 + 2.2, v_win - 3.0, spring_, rise=gw_ / 2 + 2.2, seg=32)
    orn = G.gable_pediment(wl["L"], wl["slope"], D_EAVE, skin=SKIN, fan_v=spring_, clear=clear, fan_r=gw_ / 2 + 7.0)
    f = wl["facade"]
    A = f.A.copy()
    A[:, 3] = f.world(0.0, 0.0, RAKE)
    ow = orn.transform(A) - roof
    kit.add("GABLE", "Cream", max(ow.decompose(), key=lambda m_: m_.volume()), P=inv34(A), group="roof")
    kit.add("DORMER", "Cream", dbody.transform(Ad), group="roof")
    kit.add("DORMER-core", "Slate", dcore.transform(Ad), group="roof")
    # its gabled roof: boxed eaves (a flat soffit down to the body's wall top each side), so it
    # prints upright standing on its two soffits
    ez = DHW - 1.2 * DS
    droof_cs = poly([(-DW / 2 - 1.6, ez), (-DW / 2, ez), (-DW / 2, DHW), (0.0, dapex + 0.2), (DW / 2, DHW),
                     (DW / 2, ez), (DW / 2 + 1.6, ez), (DW / 2 + 1.6, ez + 1.6), (0.0, dapex + 2.2),
                     (-DW / 2 - 1.6, ez + 1.6)])
    droof = ext(droof_cs, -DDEP - 8.0, 1.6).transform(Ad) - solid_env - dbody.transform(Ad) - roof
    kit.add("DORMER-roof", "Slate", max(droof.decompose(), key=lambda m_: m_.volume()), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the tower's bell-cast cone on its cornice
    zc0 = ZTW
    dfl = TOWER_C["layers"][-1]["P"] + 1.4 + 0.4
    flare, ftex = R.hip_roof([(ngon(TC, TR - 1.4, n=16), list(range(16)))], zc0, 0.8, dfl, texture="square",
                             tex_kw=dict(pitch=1.5, wtab=2.0, d=0.42), zlo=zc0)
    zf = zc0 + round(0.8 * dfl / 0.2) * 0.2
    flare = (flare + ftex).trim_by_plane([0, 0, -1.0], -zf)
    cone, ctex = R.hip_roof([(ngon(TC, TR - 1.4, n=16), list(range(16)))], zf, 2.6, 0.0, texture="square",
                            tex_kw=dict(pitch=1.5, wtab=2.0, d=0.42), zlo=zf - 0.01)
    zs = round((zf + 2.6 * (TR - 1.4) - 2.0) / 0.2) * 0.2
    tcone = (flare + cone + ctex).trim_by_plane([0, 0, -1.0], -zs)
    kit.add("TOWER-roof", "Slate", tcone, group="tower")
    kit.add("TOWER-finial", "Cream", TW.finial("lance", 1.8, 18.0).translate([TC[0], TC[1], zs]), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- the porch: across the front from the wing, round the tower, down the east side
    RP = TR + 16.0
    FY = -WD
    x_meet = TC[0] - math.sqrt(RP ** 2 - (FY - TC[1]) ** 2)
    a0 = math.atan2(FY - TC[1], x_meet - TC[0])
    nf = 5
    sweep = -a0                                   # from the front line round to due east
    arc = [(TC[0] + RP * math.cos(a0 + sweep * k / nf), TC[1] + RP * math.sin(a0 + sweep * k / nf)) for k in range(nf + 1)]
    EX_ = arc[-1][0]
    YB = 60.0
    ppts = [(WX, 0.0), (WX, FY)] + arc + [(EX_, YB), (W, YB), (W, 0.0)]
    turn = sweep / nf
    ca = 1.6 * math.tan(turn / 2)
    Lf = x_meet - WX
    runs = [dict(a=(WX, FY), b=arc[0], posts=[2.8, DOOR_X - WX - 12.0, DOOR_X - WX + 12.0, Lf - ca])]
    Ls = float(np.linalg.norm(np.array(arc[1]) - np.array(arc[0])))
    for k in range(nf):
        runs.append(dict(a=arc[k], b=arc[k + 1], posts=[ca, Ls - ca]))
    runs.append(dict(a=arc[-1], b=(EX_, YB), posts=[ca, (YB - arc[-1][1]) / 2, YB - arc[-1][1] - 1.6]))
    runs.append(dict(a=(EX_, YB), b=(W, YB), posts=[1.6, EX_ - W - 3.6]))
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    PP = FT.porch_turned(ppts, runs, H_floor, post_h, steps_at=[(0, DOOR_X - WX, 18.0)],
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
    ped = G.gable_pediment(20.0, 0.8, 0.6, skin=0.8, width=1.2, finial=3.0)
    Ap = np.array([[1.0, 0, 0, DOOR_X - 10.0], [0, 0, -1.0, FY - 1.4 + 0.5], [0, 1.0, 0, ptop + 0.02]])
    back = ext(poly([(-0.6, 0.0), (20.6, 0.0), (10.0, 0.8 * 10.6)]), -3.0, 0.0)
    kit.add("PORCH-pediment", "Cream", (ped + back).transform(Ap), P=inv34(Ap), group="porch")
    e, u = MAIN_LO.locate(38.0, D)
    fb = MAIN_LO.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Stone", FT.steps(14.0, ZF - 0.6, 6).transform(A) - fnd, group="porch")
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
