"""The Beaumont, Rev D: the HO (1:87.1) Queen Anne on the house-size plan (150 x 180 mm, storeys
of 42 and 38 mm) with framed windows spaced along the walls and built-up cornices at every level.

An octagonal corner tower rising a storey over the eave to a hexagon-slate spire, a front gable
wing with a one-storey canted bay, a gabled dormer on the west slope, and a wraparound porch
with a chamfered corner. Sage beaded lap siding below and gold staggered-butt shingles above
(and on the tower's top storey and in the gable), cream trim, oxblood sashes.

- Between the storeys a three-part cornice: an oxblood frieze of turned pendants (long and short
  in turn), a cream bead-and-reel course and a cream ogee crown.
- At the eave, carried round the tower: an oxblood frieze of ribbed scallop shells, a cream
  dentil course, a cream soffit on paired curved brackets and an oxblood cyma-reversa crown.
- Round the tower's top: an oxblood frieze of hearts, a cream soffit on curved brackets and a
  stepped crown; round the bay: a gold frieze of pendants, a bracketed soffit and a bevel crown.
- Banded hexagon-and-square slate roofs, a ridge cap with iron cresting and urn finials, and a
  shingled gable with a sunburst over a collar tie round the attic window.

usage: python3 -m hoarch.buildings.beaumont [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch import cornice as CO, features as FT, gables as G, openings as O, roof as R, skins as SK, trimwork as TW
from hoarch.core import Facade, box, compose, cs_union, frame, inv34, offset, poly, rect, slab, union
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Beaumont Queen Anne"
COLORS = {"PorchDeck": "#EFE7D2", "Planks": "#6F5034",       # the planked porch deck: two colours, one change
          "Sage": "#7F8F6A", "Gold": "#C79A45", "Cream": "#EFE7D2", "Oxblood": "#5A1A24", "Slate": "#43474D",
          "Walnut": "#4A2616", "Brick": "#8A3B2B", "Fieldstone": "#8D877C", "PorchGray": "#6B706F",
          "Windows_Doors": "#EFE7D2"}
# windows and doors are one part each (plug with glass and sash, and the surround), all on
# their own plate: it is the one plate printed with supports (under the surrounds)
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks",
              "Sage": "siding", "Gold": "shingle", "Cream": "trim", "Oxblood": "sash", "Slate": "roof",
              "Walnut": "door", "Brick": "brick", "Fieldstone": "stone", "PorchGray": "porchfloor",
              "Windows_Doors": "trim", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"siding": ["#7f8f6a", 0.62, 0.0], "shingle": ["#c79a45", 0.6, 0.0], "trim": ["#efe7d2", 0.55, 0.0],
           "sash": ["#5a1a24", 0.45, 0.0], "roof": ["#43474d", 0.8, 0.0], "door": ["#4a2616", 0.45, 0.0],
           "brick": ["#8a3b2b", 0.85, 0.0], "stone": ["#8d877c", 0.9, 0.0], "porchfloor": ["#6b706f", 0.7, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Beaumont)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="pendants", role="Oxblood"),
    dict(kind="course", h=1.6, b=1.4, orn="beadreel", role="Cream"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="ogee_fillet", role="Cream")])
EAVE = dict(pitch=12.0, margin=4.0, pair=1.8, layers=[
    dict(kind="frieze", h=5.8, b=1.2, orn="shells", role="Oxblood"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Cream", tooth=0.9, gap=0.6),
    dict(kind="bed", h=2.0, b=1.4, P=6.2, role="Cream", brackets=dict(style="curve", t=0.8, reach=0.6)),
    dict(kind="crown", h=2.8, b=1.4, P=7.0, orn="reverse", role="Oxblood")])
TOWER_C = dict(pitch=8.0, margin=2.6, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="hearts", role="Oxblood"),
    dict(kind="bed", h=1.8, b=1.4, P=5.0, role="Cream", brackets=dict(style="curve", t=0.8, reach=0.7)),
    dict(kind="crown", h=2.2, b=1.4, P=5.8, orn="stepped", role="Cream")])
BAY_C = dict(pitch=8.0, margin=2.4, layers=[
    dict(kind="frieze", h=3.6, b=1.2, orn="pendants", role="Gold"),
    dict(kind="bed", h=1.6, b=1.4, P=4.4, role="Cream", brackets=dict(style="curve", t=0.8, reach=0.7)),
    dict(kind="crown", h=1.8, b=1.4, P=5.0, orn="bevel", role="Cream")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (all on the 0.2 mm grid)
ZF = 14.0                 # first floor / foundation top
S1 = ZF + 42.0            # first-storey shell top = the joint ring's foot
ZE = S1 + RJ + 38.0       # the eave ledge's top
ZW = ZE + HE              # the wall top; the roof sits here
ZT = ZW + 40.0            # the tower's ledge (its top storey stands over the eave)
ZTW = ZT + CO.band_height(TOWER_C)
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 7.4, 7.6, 1.8
S_MAIN, S_WING, S_SPIRE = 1.1, 1.1, 3.0
V1 = 8.0
V2 = S1 + RJ + 5.0 - ZF
V3 = ZW + 8.0 - ZF        # the tower's top storey
SLATE = ("hex", "hex", "square")        # banded courses
SPIRE_SLATE = ("hex", "hex", "hex", "square")

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 150.0, 180.0
WX0, WY0 = 84.0, -30.0                  # front gable wing
MAIN = Block("main", [(0, 0), (WX0, 0), (WX0, WY0), (X1, WY0), (X1, Y1), (0, Y1)], ZF, ZW)
TC, TA = (16.0, 4.0), 26.0              # tower centre and apothem


def oct_pts(c, a):
    R_ = a / math.cos(math.radians(22.5))
    return [(c[0] + R_ * math.cos(math.radians(-112.5 + 45 * k)), c[1] + R_ * math.sin(math.radians(-112.5 + 45 * k)))
            for k in range(8)]


TOWER = Block("tower", oct_pts(TC, TA), ZF, ZTW)
BAY_LEDGE = ZF + 32.0
BAY_TOP = BAY_LEDGE + CO.band_height(BAY_C)
BAY = Block("bay", [(93.0, WY0), (105.0, WY0 - 12.0), (129.0, WY0 - 12.0), (141.0, WY0), (141.0, WY0 + 3.0),
                    (93.0, WY0 + 3.0)], ZF, BAY_TOP)
BLOCKS = [MAIN, TOWER, BAY]
TOWER_FACES = (7, 0, 1, 6)             # the tower faces that stand clear of the house
DOOR_X = 64.0
GL = X1 - WX0                          # the wing gable's width
GWIN = (8.4, 14.0)                     # the attic window


def _gable_trim():
    """The wing gable's trim, in its facade frame (u from the wing's west corner, v up from ZF):
    a sunburst of seven rays over a collar tie, above the attic window."""
    apex = Z_EAVE - ZF + S_WING * (GL / 2 + D_EAVE) - SKIN - 0.15
    sc = (GL / 2, apex - 11.0)
    rays = []
    for k in range(7):
        a = math.radians(20 + 140 * k / 6)
        c_, s_ = math.cos(a), math.sin(a)
        rays.append(poly([(sc[0] - 0.3 * s_, sc[1] + 0.3 * c_), (sc[0] + 0.3 * s_, sc[1] - 0.3 * c_),
                          (sc[0] + 7.0 * c_ + 0.4 * s_, sc[1] + 7.0 * s_ - 0.4 * c_),
                          (sc[0] + 7.0 * c_ - 0.4 * s_, sc[1] + 7.0 * s_ + 0.4 * c_)]))
    half = cs_union(rays) ^ rect(0, sc[1], GL, apex)
    hub = poly([(sc[0] + 2.0 * math.cos(a), sc[1] + 2.0 * math.sin(a)) for a in np.linspace(0, math.pi, 13)])
    collar = rect(GL / 2 - 9.0, sc[1] - 0.8, GL / 2 + 9.0, sc[1])
    return cs_union([half, hub, collar])


GABLE_TRIM = _gable_trim()


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    # first floor: segmental pediments with sunbursts over shaped aprons; second floor:
    # scroll hoods with volutes over bracketed sills; ornate Queen Anne entrances
    c = dict(casing=1.3)
    lo = O.window_insert(9.8, 24.0, rise=0, style="pediment", apron=True, **c)
    lo_qa = O.window_insert(9.8, 24.0, rise=0, style="pediment", apron=True, qa=True, **c)
    up = O.window_insert(9.1, 21.0, rise=0, style="scroll", **c)
    up_qa = O.window_insert(8.4, 21.0, rise=0, style="scroll", qa=True, **c)
    small = O.window_insert(8.4, 17.0, rise=0, style="scroll", **c)
    tk = dict(casing=0.8, ends=0.2, sill_ext=0.3, clip=True)
    tw1 = O.window_insert(8.4, 23.0, rise=0, style="pediment", apron=True, qa=True, **tk)
    tw2 = O.window_insert(8.4, 20.0, rise=0, style="scroll", **tk)
    tw3 = O.window_insert(7.6, 17.0, rise=None, style="scroll", **tk)
    bay_s = O.window_insert(8.4, 20.0, rise=0, style="blocks", apron=True, **tk)
    bay_f = O.window_insert(12.4, 20.0, rise=0, style="blocks", apron=True, qa=True, **tk)
    attic = O.window_insert(GWIN[0], GWIN[1], rise=None, style="scroll", casing=0.9, ends=0.2, sill_ext=0.3, clip=True)
    front = O.door_ornate(17.0, 30.0, leaves=2, transom=4.6, head="swan")
    back = O.door_ornate(11.6, 27.0, leaves=1, transom=4.2, head="pediment")

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    add(MAIN, DOOR_X, 0, 0.4, front, "front-door", "door")                  # front of the main block
    add(MAIN, DOOR_X, 0, V2, up, "S64-2")
    add(MAIN, WX0, -15.0, V2, up, "wingW-2")                                # wing, west side
    for x in (105.0, 129.0):                                                # wing front, above the bay
        add(MAIN, x, WY0, V2, up_qa, f"wingS{x:.0f}-2")
    add(MAIN, (WX0 + X1) / 2, WY0, ZW - ZF + 6.0, attic, "attic")
    for y in (-15.0, 45.0, 105.0, 158.0):                                   # east side
        add(MAIN, X1, y, V1, lo, f"E{y:.0f}-1")
        add(MAIN, X1, y, V2, up, f"E{y:.0f}-2")
    for x in (125.0, 30.0):                                                 # rear
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, 78.0, Y1, V2 + 2.0, small, "N78-2")
    add(MAIN, 78.0, Y1, 0.4, back, "back-door", "door")
    for y, sp in ((150.0, lo), (105.0, lo_qa), (60.0, lo)):                 # west side
        add(MAIN, 0, y, V1, sp, f"W{y:.0f}-1")
        add(MAIN, 0, y, V2, up, f"W{y:.0f}-2")
    P = TOWER.pts
    for k in TOWER_FACES:                                                   # tower, three storeys
        m = ((P[k][0] + P[(k + 1) % 8][0]) / 2, (P[k][1] + P[(k + 1) % 8][1]) / 2)
        add(TOWER, m[0], m[1], V1, tw1, f"T{k}-1")
        add(TOWER, m[0], m[1], V2, tw2, f"T{k}-2")
        add(TOWER, m[0], m[1], V3, tw3, f"T{k}-3")
    Q = BAY.pts
    for i, sp in ((0, bay_s), (1, bay_f), (2, bay_s)):                       # bay
        m = ((Q[i][0] + Q[i + 1][0]) / 2, (Q[i][1] + Q[i + 1][1]) / 2)
        add(BAY, m[0], m[1], V1 - 0.4, sp, f"bay{i}-1")
    return L


OPENINGS = _openings()


def _siding(f, b, reg):
    """Beaded lap siding on the first storey; staggered-butt shingles above, upright so the
    layers draw them (the tower's top storey and the gable each a different random run).
    Nothing in the cornice bands; the gable's shingles stop round its trim."""
    if b is BAY:
        reg = reg - rect(-1, BAY_LEDGE - b.z0, f.L + 1, 999)
    else:
        reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
        if b is TOWER:
            reg = reg - rect(-1, ZT - b.z0, f.L + 1, 999)
    out = []
    lo = reg ^ rect(-1, -100, f.L + 1, S1 - ZF)
    mid = reg ^ rect(-1, S1 - ZF, f.L + 1, ZE - ZF)
    top = reg ^ rect(-1, ZW - ZF, f.L + 1, 999)
    if not lo.is_empty():
        out.append(SK.beaded_lap(lo, datum=1.8))
    if not mid.is_empty():
        out.append(SK.stagger_shingles(mid, datum=S1 + RJ - ZF, seed=3))
    if not top.is_empty():
        gable = b is MAIN and abs(f.p0[1] - WY0) < 0.01 and abs(f.p1[1] - WY0) < 0.01
        if gable:
            top = top - GABLE_TRIM.offset(0.3, JoinType.Miter, 4.0)
        out.append(SK.stagger_shingles(top, datum=ZW - ZF, seed=13 if gable else 5))
    return union(out) if out else M()


DX, DY, DW, DDEP, DHW, DS = 12.0, 105.0, 20.0, 30.0, 14.0, 1.2     # the west dormer: face line, centre, size


def _dormer():
    """The gabled dormer on the west slope: a flat-bottomed box (it drops into a pocket in the
    roof and stands on a seat) with a shingled pentagon face and an opening for a scroll-headed
    attic window. Local: u across, v up from its foot, w out (the face at w = 0)."""
    apex = DHW + DS * DW / 2
    front = poly([(-DW / 2, 0.0), (DW / 2, 0.0), (DW / 2, DHW), (0.0, apex), (-DW / 2, DHW)])
    body = box([-DW / 2, 0.0, -DDEP], [DW / 2, DHW, 0.0]) - box([-DW / 2 + 1.2, 1.2, -DDEP - 1], [DW / 2 - 1.2, DHW + 1, -1.6])
    body = body + ext(front, -1.6, 0.0)
    win = O.window_insert(7.6, 10.0, rise=None, style="scroll", casing=0.8, ends=0.2, sill_ext=0.3, clip=True)
    wv = 3.4
    body = body - ext(win["cut"].translate((0.0, wv)), -2.0, 1.0)
    reg = (front.offset(-0.5) - win["landing"].translate((0.0, wv))) ^ rect(-DW / 2, 0.6, DW / 2, apex)
    body = body + SK.stagger_shingles(reg, datum=0.6, seed=11)
    return body, win, wv, front, apex


def _ridge_crest(a, b, z0, h=3.0):
    """Iron cresting for the hip ridge as its own strip standing on the ridge cap's flat top:
    a base bar, the pierced fence, and a turned urn finial at each end. Prints upright."""
    f = Facade(a, b, z0)
    L = f.L
    parts = [box([-0.6, -0.6, 0.0], [L + 0.6, 0.6, 1.0])]
    cr = R.crest_fence(L, h=h, pitch=1.6).transform(frame([0, 0, 0.8], [1.0, 0, 0], [0, 0, 1.0], [0, -1.0, 0]))
    parts.append(cr)
    for u in (0.0, L):
        parts.append(TW.finial("urn", 1.2, 7.2).translate([u, 0, 0.8]))
    m = union(parts)
    A = np.eye(3, 4)
    A[:, 0] = [f.u[0], f.u[1], 0.0]
    A[:, 1] = [-f.u[1], f.u[0], 0.0]
    A[:, 2] = [0, 0, 1.0]
    A[:, 3] = [a[0], a[1], z0]
    return m.transform(A)


# ------------------------------------------------------------------ build
def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    r = RAKE - D_EAVE
    pieces = [([(0.0, 0.0), (X1, 0.0), (X1, Y1), (0.0, Y1)], [0, 1, 2, 3], S_MAIN),
              ([(WX0, WY0 - r), (X1, WY0 - r), (X1, 40.0), (WX0, 40.0)], [1, 3], S_WING)]
    specs = [dict(p0=(WX0, WY0), p1=(X1, WY0), slope=S_WING, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture=SLATE, tex_kw=dict(pitch=1.6, wtab=2.2, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA, hollow=2.6)
    wl = rf["walls"][0]
    gables = [(MAIN, 2, wl["cs"].translate((0.0, Z_EAVE - ZF)))]
    eave_cs = cs_union([MAIN.cs, TOWER.cs])
    eave_path = max(eave_cs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(eave_cs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01),
               slab(offset(BAY.cs, 8.0) ^ rect(0.0, -200.0, 400.0, WY0 - 0.6), BAY_LEDGE - LEDGE - 0.6, BAY_TOP + 0.01)]
    clear = [lip_keep(cs_union([b.cs for b in BLOCKS]), 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="board", clear=clear, siding=_siding, gables=gables,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    ledge_b = CO.ledge(BAY.pts, BAY_LEDGE, LEDGE) - MAIN.solid(grow=0.2, dz0=-1, dz1=1)
    kit.add("WALLS-1", "Sage", st["shells"][0] + ledge_b, group="walls")
    kit.add("JOINT", "Sage", st["rings"][0], group="walls")
    # the lip for the roof round the main block; none under the gable or round the tower
    tkeep = TOWER.solid(grow=0.2, dz0=-1, dz1=1)
    no_lip = union([box([WX0 - D_EAVE - 0.6, WY0 - 1, ZW - 1], [X1 + D_EAVE + 0.6, WY0 + 5.0, ZW + 5]),
                    tkeep, slab(offset(TOWER.cs, 1.0), ZW - 1, ZW + 5)])
    lip = (_corbel(MAIN.cs, 3.0, ZW) + lip_ring(MAIN.cs, 3.0, ZW)) - no_lip
    # inside the house the tower's walls rise from the joint so its top storey bears all round
    allcs = cs_union([b.cs for b in BLOCKS])
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(allcs, 3.0, S1 + RJ)
    ledges = CO.ledge(eave_path, ZE, LEDGE) + CO.ledge(TOWER.pts, ZT, LEDGE)
    tlip = _corbel(TOWER.cs, 3.0, ZTW) + lip_ring(TOWER.cs, 3.0, ZTW)
    kit.add("WALLS-2", "Gold", st["shells"][1] + lip + tring + ledges + tlip, group="walls")
    # the cornices: the joint and the eave run round the tower too; the tower's own at its top
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    # the eave's rings wrap the tower: parted where they meet it and halved round it (to fit)
    cut = CO.blades(CO.tower_cuts(eave_path, TC, TA + 8.0, wall=TA, away=(-1.0, -1.0), tower=TOWER.pts, house=MAIN.pts), ZE, ZW)
    rings, _ = CO.level(eave_path, ZE, EAVE, cut=cut)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    # the tower's own cornice stops where the main roof climbs past it behind
    t_env, _ = R.hip_roof(pieces, Z_EAVE + 1.4, S_MAIN, D_EAVE + 1.4, texture=None, zlo=ZW)     # over the hip caps too
    rings, _ = CO.level(TOWER.pts, ZT, TOWER_C, cut=t_env)
    CO.add_level(kit, rings, "CORNICE-T", "tower")
    rings, _ = CO.level(BAY.pts, BAY_LEDGE, BAY_C, cut=MAIN.solid(grow=0.7, dz0=-2, dz1=2))
    CO.add_level(kit, rings, "CORNICE-B", "bay")
    kit.add("FOUNDATION", "Fieldstone", foundation(BLOCKS, 0.0, ZF), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the main roof: a hollow banded-slate hip with the wing's front gable
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    zr = Z_EAVE + S_MAIN * (X1 / 2 + D_EAVE)
    ry0, ry1 = X1 / 2, Y1 - X1 / 2
    walls_env = wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
    caps = [G.ridge_cap((X1 / 2, ry0), (X1 / 2, ry1), zr, S_MAIN, ZW)]
    zcw = Z_EAVE + S_WING * (GL / 2 + D_EAVE)
    xm = (WX0 + X1) / 2
    y_meet = (zcw - Z_EAVE) / S_MAIN - D_EAVE + 1.0
    caps.append(G.ridge_cap((xm, WY0 - RAKE), (xm, y_meet), zcw, S_WING, ZW))
    corners = [(-D_EAVE, -D_EAVE), (X1 + D_EAVE, Y1 + D_EAVE), (-D_EAVE, Y1 + D_EAVE)]
    ends = [(X1 / 2, ry0), (X1 / 2, ry1), (X1 / 2, ry1)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.6, up=0.9, drop=2.2)
                  for c, e in zip(corners, ends)])
    roof = roof + ((union(caps) + hips) - walls_env)
    roof = roof.trim_by_plane([0, 0, 1.0], ZW) - lip_keep(MAIN.cs, 3.0, ZW)
    # chimneys stand in blind pockets over seats; the dormer drops into a pocket on a seat
    CW = 11.6
    chims = [(40.0, 150.0), (120.0, 128.0)]
    pockets = []
    zch = []
    for (cx, cy) in chims:
        zroof = Z_EAVE + S_MAIN * (min(cx + D_EAVE, X1 + D_EAVE - cx, cy + D_EAVE, Y1 + D_EAVE - cy) - CW / 2)
        z0 = round((zroof - 3.0) / 0.2) * 0.2
        zch.append(z0)
        roof = roof + G.chimney_seat(solid_env, cx, cy, CW / 2, zr + 1.0)
        pockets.append(box([cx - CW / 2 - 0.4, cy - CW / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CW / 2 + 0.4, zr + 40]))
    dbody, dwin, dwv, dface, dapex = _dormer()
    zdf = ZW + round((Z_EAVE - ZW + S_MAIN * (DX + D_EAVE) - 1.0) / 0.2) * 0.2
    Ad = np.array([[0.0, 0, -1.0, DX], [-1.0, 0, 0, DY], [0, 1.0, 0, zdf]])
    dkeep = ext(dface.offset(0.3, JoinType.Miter, 4.0), -DDEP - 0.3, 0.9).transform(Ad)
    dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
    dseat = ext(rect(-DW / 2 - 1.3, ZW - zdf, DW / 2 + 1.3, 0.0), -DDEP - 1.3, 1.6).transform(Ad) ^ solid_env
    top_cs = MAIN.cs
    roof = roof - union(pockets) - dpocket - slab(offset(TOWER.cs, 1.4), ZW - 1, ZTW + 90) + \
        (dseat - dpocket - lip_keep(top_cs, 3.0, ZW))
    rz = G.ridge_cap((X1 / 2, ry0), (X1 / 2, ry1), zr, S_MAIN, ZW).bounding_box()[5]
    kit.add("ROOF-main", "Slate", roof, group="roof")
    kit.add("ROOF-crest", "Slate", _ridge_crest((X1 / 2, ry0 - 2.0), (X1 / 2, ry1 + 2.0), rz), group="roof")
    for k, ((cx, cy), z0) in enumerate(zip(chims, zch)):
        ch = TW.chimney("corbel", w=CW, d=CW, h=round((zr - 2.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof")
    kit.add("DORMER", "Gold", dbody.transform(Ad), group="roof")
    Aw = Ad.copy()
    Aw[:, 3] = Ad[:, 3] + Ad[:, 1] * dwv
    wworld, wP, zones = O.place(dwin, Aw, "Windows_Doors", "Sash", "Glass")
    kit.add("WIN-dormer", "Windows_Doors", wworld, P=wP, group="inserts", render=zones)
    # the dormer's own gabled roof: boxed eaves, printed upright on its two soffits
    ez = DHW - 1.2 * DS
    droof_cs = poly([(-DW / 2 - 1.6, ez), (-DW / 2, ez), (-DW / 2, DHW), (0.0, dapex + 0.2), (DW / 2, DHW),
                     (DW / 2, ez), (DW / 2 + 1.6, ez), (DW / 2 + 1.6, ez + 1.6), (0.0, dapex + 2.2),
                     (-DW / 2 - 1.6, ez + 1.6)])
    droof = ext(droof_cs, -DDEP - 8.0, 1.6).transform(Ad) - solid_env - dbody.transform(Ad) - roof
    kit.add("DORMER-roof", "Slate", max(droof.decompose(), key=lambda m_: m_.volume()), group="roof")
    # the gable's sunburst and collar, flat on the shingles
    gf = MAIN.facades()[2]
    kit.add("GABLE-trim", "Cream", gf.place(ext(GABLE_TRIM, 0.0, G.TRIM_D)), P=inv34(gf.A), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the tower's hollow slate spire on its cornice, and a separate finial
    dsp = TOWER_C["layers"][-1]["P"] + 0.6
    sp = G.gabled_roof([(TOWER.pts, list(range(8)), S_SPIRE)], ZTW + 1.4, dsp, [], texture=SPIRE_SLATE,
                       tex_kw=dict(pitch=1.6, wtab=1.9, d=0.4), inner_cs=offset(TOWER.cs, -2.4), fascia=1.4, hollow=2.4)
    tip = ZTW + 1.4 + S_SPIRE * (TA + dsp)
    zseat = round((tip - 3.0) / 0.2) * 0.2
    seat = M.cylinder(1.0, 1.5, 1.5, 32).translate([TC[0], TC[1], zseat - 0.4])
    spire = (sp["body"] + sp["tex"]).trim_by_plane([0, 0, -1.0], -zseat) - seat - lip_keep(TOWER.cs, 3.0, ZTW)
    kit.add("TOWER-SPIRE", "Slate", spire, group="tower")
    kit.add("TOWER-FINIAL", "Slate", TW.finial("urn", 1.4, 11.0).translate([TC[0], TC[1], zseat - 0.4]), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- the bay: its cornice (above) and a banded slate hip under the joint
    bay_keep = union([MAIN.solid(grow=0.45, dz0=-1, dz1=300)])
    deck_z = S1 - 0.4
    broof, btex = R.hip_roof([(BAY.pts, [0, 1, 2])], BAY_TOP, 0.8, BAY_C["layers"][-1]["P"] + 0.2, texture=SLATE,
                             flat_top=deck_z, tex_kw=dict(pitch=1.6, wtab=2.2, d=0.4), zlo=BAY_TOP)
    kit.add("BAY-ROOF", "Slate", (broof + btex) - bay_keep, group="bay")

    # --- wraparound porch: turned posts, railings, sawn-work arcades, planked floor
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor              # the roof tucks under the joint's ledge
    c45 = 0.663
    ppoly = [(-20.0, -40.0), (WX0, -40.0), (WX0, WY0), (WX0, 0.0), (0.0, 0.0), (0.0, 118.0), (-38.0, 118.0),
             (-38.0, -22.0)]
    Lc = math.hypot(18.0, 18.0)
    runs = [dict(a=(0.0, 118.0), b=(-38.0, 118.0), posts=[3.2, 36.4]),
            dict(a=(-38.0, 118.0), b=(-38.0, -22.0), posts=[1.6, 30.0, 58.0, 86.0, 113.0, 140.0 - c45]),
            dict(a=(-38.0, -22.0), b=(-20.0, -40.0), posts=[c45, Lc - c45]),
            dict(a=(-20.0, -40.0), b=(WX0, -40.0), posts=[c45, 26.0, 50.0, 72.0, 102.4]),
            dict(a=(WX0, -40.0), b=(WX0, WY0), posts=[1.6])]
    P = FT.porch_turned(ppoly, runs, H_floor, post_h, steps_at=[(3, DOOR_X + 20.0, 18.0)],
                        planks=dict(pitch=1.8, border=1.6), joined=True, ledger_off=1.5,
                        pier_tex="fieldstone", roof_edge="dentil")
    fkeep = slab(offset(cs_union([b.cs for b in BLOCKS]), 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    deck = P["deck"] - fkeep           # planks and frame in one part: wood planks, one filament change
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    for k, fr in enumerate(sorted(P["frames"], key=lambda m: -m.volume())):
        kit.add(f"PORCH-frame-{k}", "Cream", fr, group="porch")
    for k, (arc, A) in enumerate(P["arcades"]):
        kit.add(f"PORCH-arcade-{k}", "Cream", arc, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=0) for b in BLOCKS]) + TOWER.solid(grow=1.45, dz0=-20, dz1=300)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    proof = P["roof"] - bld_keep - ins_keep - box([WX0 + 2.4, -80, 0], [300, WY0 + 0.5, 300])    # stops at the wing
    ptop = proof.bounding_box()[5]
    below = proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8))
    cap = proof.trim_by_plane([0, 0, 1.0], ptop - 0.8)                # standing-seam tin, square to each wall
    inner = M.extrude(cap.slice(ptop - 0.4).offset(-0.5), 5).translate([0, 0, ptop - 1])
    ribs = union([box([x - 0.25, -80, ptop - 0.01], [x + 0.25, 0.0, ptop + 0.4]) for x in np.arange(-36.4, WX0 + 1, 5.2)])
    ribs = ribs + union([box([-80, y - 0.25, ptop - 0.01], [0.0, y + 0.25, ptop + 0.4]) for y in np.arange(2.6, 120, 5.2)])
    ribs = ribs ^ inner
    kit.add("PORCH-roof", "Cream", below, P=print_flip(), group="porch")
    kit.add("PORCH-roof-cap", "Slate", cap + ribs, group="porch")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "PorchGray", sm.transform(A) - fkeep, group="porch")
    # back stoop under the rear door
    e, u = MAIN.locate(78.0, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "PorchGray", FT.steps(17.0, ZF - 0.6, 5).transform(A), group="porch")
    print("specks dropped:", kit.drop_specks())
    print("porch", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "beaumont")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "beaumont.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Test"))
