"""The Harcourt -- an original HO-scale (1:87.1) Second Empire house for the lineup. Rev B: the
house-size plan (186 x 150 mm, storeys of 42 and 38 mm) and built-up cornices at every level.

A symmetrical block of Flemish-bond red brick (a diamond diaper of proud headers) with a
centre tower over the entrance and cream stone trim: sculpted window surrounds, a straight
bell-cast mansard of square slate banded with hexagons, round-topped dormers, iron cresting on
its flat top, and a tall concave mansard cap on the tower. Paneled chimneys, an iron finial. A
one-storey canted bay on the east side, an entrance portico on fluted columns with urn
balusters and an entablature, and a rock-faced granite foundation.

- Between the storeys a three-part cornice: a limestone frieze of upright acanthus leaves, a
  verdigris cable course and a limestone cyma crown.
- At the eave, under the mansard and round the tower: a verdigris anthemion frieze (palmettes
  and lotus buds), a limestone dentil course, a limestone soffit on block modillions and a
  verdigris cavetto crown.
- Round the tower's top a limestone frieze of ringed square bosses, a verdigris soffit on block
  brackets and a limestone ovolo crown; round the bay an anthemion frieze, a bracketed soffit
  and a stepped crown under a flat deck with cresting.

usage: python3 -m hoarch.buildings.harcourt [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, compose, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, openings as O, roof as R, skins as SK, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Harcourt Second Empire"
COLORS = {"PorchDeck": "#D9CFB6", "Planks": "#6F5034",       # the planked porch deck: two colours, one change
          "Brick": "#8E3B2C", "Limestone": "#D9CFB6", "Slate": "#4A5159", "Iron": "#27292C",
          "Granite": "#7E7C78", "PorchGray": "#6B706F", "Verdigris": "#4F7F72", "Windows_Doors": "#D9CFB6"}
# windows and doors print in one colour and are painted; Sash/Door/Glass are render-only zones
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks",
              "Brick": "brick", "Limestone": "trim", "Slate": "roof", "Iron": "iron", "Granite": "stone",
              "PorchGray": "porchfloor", "Verdigris": "accent", "Windows_Doors": "trim", "Sash": "sash", "Door": "door",
              "Glass": "glass"}
PALETTE = {"brick": ["#8E3B2C", 0.85, 0.0], "trim": ["#D9CFB6", 0.6, 0.0], "roof": ["#4A5159", 0.75, 0.0],
           "iron": ["#27292C", 0.45, 0.3], "stone": ["#7E7C78", 0.9, 0.0], "porchfloor": ["#6B706F", 0.7, 0.0],
           "sash": ["#2E3B33", 0.45, 0.0], "door": ["#4A2616", 0.45, 0.0], "accent": ["#4F7F72", 0.5, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Harcourt)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="acanthus", role="Limestone"),
    dict(kind="course", h=1.6, b=1.4, orn="cable", role="Verdigris"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="cyma", role="Limestone")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.8, b=1.2, orn="anthemion", role="Verdigris"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Limestone", tooth=0.9, gap=0.6),
    dict(kind="bed", h=2.2, b=1.4, P=6.4, role="Limestone", brackets=dict(style="block", t=1.0, reach=0.6)),
    dict(kind="crown", h=2.8, b=1.4, P=7.2, orn="cavetto", role="Verdigris")])
TOWER_C = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="bosses", role="Limestone"),
    dict(kind="bed", h=1.8, b=1.4, P=5.0, role="Verdigris", brackets=dict(style="block", t=0.9, reach=0.7)),
    dict(kind="crown", h=2.2, b=1.4, P=5.8, orn="ovolo", role="Limestone")])
BAY_C = dict(pitch=8.0, margin=2.6, layers=[
    dict(kind="frieze", h=4.0, b=1.2, orn="anthemion", role="Limestone"),
    dict(kind="bed", h=1.6, b=1.4, P=4.4, role="Verdigris", brackets=dict(style="block", t=0.8, reach=0.7)),
    dict(kind="crown", h=1.8, b=1.4, P=5.0, orn="stepped", role="Limestone")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (all on the 0.2 mm grid)
ZF = 14.0                 # foundation top / first floor
S1 = ZF + 42.0            # first-storey shell top = the joint ring's foot
ZE = S1 + RJ + 38.0       # the eave ledge's top
ZW = ZE + HE              # the wall top: the mansard's foot stands on the eave's crown here
MZ0 = ZW
MH = 36.0                 # mansard height
MZ1 = MZ0 + MH
DK = EAVE["layers"][-1]["P"] + 0.2
MANSARD = [(DK, MZ0), (DK - 1.6, MZ0 + 1.6), (-3.2, MZ1)]      # bell-cast kick, then about 75 degrees
ZT = ZW + 48.0            # the tower's ledge (its top storey stands over the mansard)
ZTW = ZT + CO.band_height(TOWER_C)
TCAP_H = 26.0
V1, V2 = 8.0, S1 + RJ + 5.0 - ZF        # sill heights above ZF
V3 = ZW + 14.0 - ZF                     # tower third storey

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 186.0, 150.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
TX0, TX1, TY0, TY1 = 68.0, 118.0, -16.0, 28.0
TOWER = Block("tower", [(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)], ZF, ZTW)
BAY_LEDGE = ZF + 33.0
BAY_TOP = BAY_LEDGE + CO.band_height(BAY_C)
BAY = Block("bay", [(X1 - 3.0, 58.0), (X1, 58.0), (X1 + 12.0, 66.0), (X1 + 12.0, 88.0), (X1, 96.0),
                    (X1 - 3.0, 96.0)], ZF, BAY_TOP)
BLOCKS = [MAIN, TOWER, BAY]
SLATE = ("square", "square", "square", "hex")    # banded courses
TOWER_SLATE = ("square",)


def _brick(f, b, reg):
    """Flemish bond with a diamond diaper of headers standing 0.15 mm prouder; nothing in the
    cornice bands."""
    if b is BAY:
        reg = reg - rect(-1, BAY_LEDGE - b.z0, f.L + 1, 999)
    else:
        reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
        if b is TOWER:
            reg = reg - rect(-1, ZT - b.z0, f.L + 1, 999)
    return SK.brick_bond(reg, "flemish", datum=1.8, diaper=0.15)


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    lo = O.window_se(10.4, 24.0, rise=0, head="pediment")                     # sculpted surrounds
    up = O.window_se(9.6, 21.0, rise=2.4, head="hood", apron=False)
    bay_f = O.window_se(10.4, 19.0, rise=0, head="cap", arch_w=1.4, apron=False)
    bay_s = O.window_se(7.2, 19.0, rise=0, head="cap", arch_w=1.2, apron=False, sill_consoles=False)
    tw2 = O.window_se(12.0, 25.0, rise=None, head="hood", apron=False)       # round-headed
    tw3 = O.window_se(11.2, 20.0, rise=2.4, head="pediment", apron=False)
    front = O.door_se(17.0, 28.0, leaf="arch_panels", tstyle="plain")
    back = O.door_se(11.6, 27.0, leaves=1, pil=1.6, leaf="arch_panels", tstyle="plain")

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    for x in (18.0, 46.0, 140.0, 168.0):                                  # front, either side of the tower
        add(MAIN, x, 0, V1, lo, f"S{x:.0f}-1")
        add(MAIN, x, 0, V2, up, f"S{x:.0f}-2")
    mx = (TX0 + TX1) / 2
    add(TOWER, mx, TY0, 0.4, front, "front-door", "door")                 # tower front
    add(TOWER, mx, TY0, V2, tw2, "T-2")
    add(TOWER, mx, TY0, V3, tw3, "T-3")
    for y in (28.0, 75.0, 122.0):                                         # west
        add(MAIN, 0, y, V1, lo, f"W{y:.0f}-1")
        add(MAIN, 0, y, V2, up, f"W{y:.0f}-2")
    for y in (28.0, 122.0):                                               # east, with the bay between
        add(MAIN, X1, y, V1, lo, f"E{y:.0f}-1")
        add(MAIN, X1, y, V2, up, f"E{y:.0f}-2")
    add(MAIN, X1, 77.0, V2, up, "E77-2")
    Q = BAY.pts
    for i in range(len(Q)):                                               # the bay's three faces
        a, b = np.array(Q[i]), np.array(Q[(i + 1) % len(Q)])
        if min(a[0], b[0]) < X1 - 0.1 or np.linalg.norm(b - a) < 5:
            continue
        m = (a + b) / 2
        add(BAY, m[0], m[1], V1 - 1.0, bay_f if abs(a[0] - b[0]) < 0.1 else bay_s, f"bay{i}-1")
    for x in (34.0, 152.0):                                               # rear
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, 93.0, Y1, 0.4, back, "back-door", "door")
    add(MAIN, 93.0, Y1, V2, up, "N93-2")
    return L


OPENINGS = _openings()
# dormers: centre points on the wall line
DORMERS = [(34.0, 0), (152.0, 0), (X1, 28.0), (X1, 122.0), (0, 28.0), (0, 122.0), (34.0, Y1), (93.0, Y1), (152.0, Y1)]
D_FACE = DK - 0.4         # dormer face, outward from the wall face (on the mansard's kick)
DORMER_KW = dict(W=18.0, H=15.0, D=13.0, win_w=8.0, win_h=17.0)


def _dormer_frame(x, y):
    """Facade frame of the dormer centred on the wall-line point (x, y), at the mansard foot."""
    e, u = MAIN.locate(x, y)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, MZ0 - ZF, D_FACE)
    return A


# ------------------------------------------------------------------ build
def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    eave_cs = cs_union([MAIN.cs, TOWER.cs])
    eave_path = max(eave_cs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(eave_cs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01),
               slab(offset(BAY.cs, 8.0) - offset(MAIN.cs, 2.0), BAY_LEDGE - LEDGE - 0.6, BAY_TOP + 0.01)]
    clear = [lip_keep(cs_union([b.cs for b in BLOCKS]), 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="quoin_even", clear=clear, siding=_brick,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    main_keep = MAIN.solid(grow=0.45, dz0=-1, dz1=300)
    ledge_b = CO.ledge(BAY.pts, BAY_LEDGE, LEDGE) - MAIN.solid(grow=0.2, dz0=-1, dz1=1)
    kit.add("WALLS-1", "Brick", st["shells"][0] + ledge_b, group="walls")
    kit.add("JOINT", "Brick", st["rings"][0], group="walls")
    # inside the house the tower's walls rise from the joint so its top storey bears all round
    allcs = cs_union([b.cs for b in BLOCKS])
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(allcs, 3.0, S1 + RJ)
    ledges = CO.ledge(eave_path, ZE, LEDGE) + CO.ledge(TOWER.pts, ZT, LEDGE)
    tlip = _corbel(TOWER.cs, 3.0, ZTW) + lip_ring(TOWER.cs, 3.0, ZTW)
    kit.add("WALLS-2", "Brick", st["shells"][1] + tring + ledges + tlip, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    # the eave's rings wrap the tower: parted where they meet it (the tower's piece slides on
    # from the front)
    tcen = ((TX0 + TX1) / 2, (TY0 + TY1) / 2)
    cut = CO.blades(CO.tower_cuts(eave_path, tcen, 32.0, tower=TOWER.pts, house=MAIN.pts), ZE, ZW)
    rings, _ = CO.level(eave_path, ZE, EAVE, cut=cut)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(TOWER.pts, ZT, TOWER_C)
    CO.add_level(kit, rings, "CORNICE-T", "tower")
    rings, _ = CO.level(BAY.pts, BAY_LEDGE, BAY_C, cut=MAIN.solid(grow=0.7, dz0=-2, dz1=2))
    CO.add_level(kit, rings, "CORNICE-B", "bay")
    kit.add("FOUNDATION", "Granite", foundation(BLOCKS, 0.0, ZF, style="granite"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Limestone", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    tower_keep = TOWER.solid(grow=2.1, dz0=-1, dz1=400)
    tower_hug = TOWER.solid(grow=0.5, dz0=-1, dz1=400)          # the mansard notch hugs the tower (brick 0.25 proud)
    # --- mansard band (upside down) on the eave's crown, with dormer notches; it drops round the tower
    mans, mtex, inner = R.mansard(MAIN.pts, MANSARD, t=2.6, tex=dict(pitch=1.6, wtab=1.9, d=0.4, shape=SLATE))
    dorm = []
    for k, (x, y) in enumerate(DORMERS):
        A = _dormer_frame(x, y)
        dm = FT.dormer(**DORMER_KW)
        dorm.append((A, dm))
    notches = union([dm["keep"].transform(A) for A, dm in dorm])
    kit.add("MANSARD", "Slate", (mans + mtex) - tower_hug - notches, P=print_flip(), group="roof")
    for k, (A, dm) in enumerate(dorm):
        kit.add(f"DORMER-{k}", "Limestone", dm["body"].transform(A), key="DORMER", group="dormers")
        kit.add(f"DORMER-hood-{k}", "Slate", dm["hood"].transform(A), P=compose(print_flip(), inv34(A)),
                key="DORMER-hood", group="dormers")
        win = dm["window"]
        wb = win.bounding_box()
        glass = win ^ box([-50, -50, wb[2] - 0.1], [50, 50, wb[2] + O.GLASS])
        zones = [("Glass", glass.transform(A)), ("Sash", (win - glass).transform(A))]
        kit.add(f"WIN-dormer-{k}", "Windows_Doors", win.transform(A), P=inv34(A), key="WIN-dormer",
                group="inserts", render=zones)
    # --- top curb (upside down) and standing-seam deck, iron cresting strips, chimneys on the deck
    t_top = MANSARD[-1][0] - inner(MZ1)
    T = R.mansard_top(MAIN.pts, MANSARD[-1][0], MZ1, t_top)
    zdeck = T["z_top"]
    chims = [(22.0, 75.0), (164.0, 75.0)]
    pads = union([box([x - 6.6, y - 6.6, zdeck - 0.6], [x + 6.6, y + 6.6, zdeck + 1]) for x, y in chims])
    kit.add("ROOF-curb", "Limestone", T["ring"] - tower_hug, P=print_flip(), group="roof")
    kit.add("ROOF-deck", "Slate", T["deck"] - tower_hug - pads, group="roof")
    top_path = T["path"]
    crest = R.cresting(top_path, zdeck, h=2.8, pitch=2.0, d_off=-1.0, style="spear")
    for i, seg, A, L in R.cresting_strips(crest, top_path, zdeck, -1.0):
        for j, piece in enumerate((seg - tower_keep).decompose()):
            if piece.volume() > 1.0:
                kit.add(f"CREST-{i}{'ab'[j] if j < 2 else j}", "Iron", piece, P=inv34(A), group="roof")
    for k, (x, y) in enumerate(chims):
        ch = TW.chimney("paneled", w=11.6, d=11.6, h=19.6).translate([x, y, zdeck - 0.6])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- tower: its cornice, the concave slate cap, curb and deck, cresting and finial
    cz0 = ZTW
    cprof = FT.tower_cap(None, cz0, TCAP_H, d_flare=TOWER_C["layers"][-1]["P"] + 0.2, d_top=-5.4, bands=6)
    cap, ctex, cin = R.mansard(TOWER.pts, cprof, t=2.4, tex=dict(pitch=1.4, wtab=1.6, d=0.35, shape=TOWER_SLATE))
    kit.add("TOWER-CAP", "Slate", (cap + ctex) - lip_keep(TOWER.cs, 3.0, ZTW), group="tower")
    TT_ = R.mansard_top(TOWER.pts, cprof[-1][0], cz0 + TCAP_H, cprof[-1][0] - cin(cz0 + TCAP_H), seams=3.6)
    ttop_path, tdeck = TT_["path"], TT_["z_top"]
    tc = ((TX0 + TX1) / 2, (TY0 + TY1) / 2)
    fpad = box([tc[0] - 1.8, tc[1] - 1.8, tdeck - 0.01], [tc[0] + 1.8, tc[1] + 1.8, tdeck + 1])
    kit.add("TOWER-curb", "Limestone", TT_["ring"], P=print_flip(), group="tower")
    kit.add("TOWER-deck", "Slate", TT_["deck"] - fpad, group="tower")
    tcrest = R.cresting(ttop_path, tdeck, h=3.2, pitch=2.0, d_off=-1.0, style="spear")
    for i, seg, A, L in R.cresting_strips(tcrest, ttop_path, tdeck, -1.0):
        kit.add(f"TOWER-crest-{i}", "Iron", seg, P=inv34(A), key=f"TOWER-crest-{round(L, 1)}", group="tower")
    kit.add("TOWER-finial", "Iron", TW.finial("iron", 1.6, 11.0).translate([tc[0], tc[1], tdeck]), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- east bay: its cornice (above), a flat deck over the crown and cresting on the deck
    bdeck = slab(offset(BAY.cs, BAY_C["layers"][-1]["P"] + 0.2), BAY_TOP, BAY_TOP + 1.2) - main_keep
    bdeck = max(bdeck.decompose(), key=lambda m: m.volume())
    kit.add("BAY-roof", "Slate", bdeck, group="bay")
    bz = BAY_TOP + 1.2
    bcrest = R.cresting(BAY.pts, bz, h=2.8, pitch=2.0, d_off=3.2, style="spear") - MAIN.solid(grow=4.2, dz0=-1, dz1=300)
    for i, seg, A, L in R.cresting_strips(bcrest, BAY.pts, bz, 3.2):
        if not seg.is_empty() and seg.volume() > 1.0:
            kit.add(f"BAY-crest-{i}", "Iron", seg, P=inv34(A), group="bay")

    # --- entrance portico: turned posts and railings in one piece, arcades, tin roof
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor                 # the roof tucks under the joint's ledge
    y0, y1 = TY0 - 1.4, TY0 - 30.0
    px0, px1 = TX0 - 8.0, TX1 + 8.0
    runs = [dict(a=(px0, y0), b=(px0, y1), posts=[1.7, (y0 - y1) - 1.6]),
            dict(a=(px0, y1), b=(px1, y1), posts=[1.6, 16.0, (px1 - px0) - 16.0, (px1 - px0) - 1.6]),
            dict(a=(px1, y1), b=(px1, y0), posts=[1.6, (y0 - y1) - 1.7])]
    P = FT.porch_turned([(px0, y0), (px0, y1), (px1, y1), (px1, y0)], runs, H_floor, post_h,
                        steps_at=[(1, (px1 - px0) / 2, 18.0)], planks=dict(pitch=1.4, border=1.6), joined=True,
                        post="fluted", rail="urn", arcade="entablature", skirt="square", pier_tex="granite",
                        roof_edge="fillet", top=True)
    fkeep = slab(offset(cs_union([b.cs for b in BLOCKS]), 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    # keep-out boxes round the inserts, their tops and bottoms on the layer grid (the porch
    # roof is notched by them and prints upside down)
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    deck = P["deck"] - fkeep           # planks and frame in one part: wood planks, one filament change
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=0) for b in BLOCKS]) + TOWER.solid(grow=1.45, dz0=-20, dz1=300)
    cap_ = FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_keep, "Limestone", "Limestone", tin="custom")["cap"]
    ptop = cap_.bounding_box()[5]
    inner_cs = M.extrude(cap_.slice(ptop - 0.4).offset(-0.5), 5).translate([0, 0, ptop - 1])
    # flat-seam tin: battens both ways, a grid of panels (the Ashby's tin has ribs one way only)
    ribs = union([box([x - 0.25, y1 - 10, ptop - 0.01], [x + 0.25, y0, ptop + 0.4])
                  for x in np.arange(px0 + 1.0, px1, 5.2)] +
                 [box([px0 - 10, y - 0.25, ptop - 0.01], [px1 + 10, y + 0.25, ptop + 0.4])
                  for y in np.arange(y1 + 2.6, y0, 5.2)]) ^ inner_cs
    kit.add("PORCH-roof-tin", "Slate", cap_ + ribs, group="porch")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Granite", sm.transform(A) - fkeep, group="porch")
    # back stoop
    e, u = MAIN.locate(93.0, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.8)                     # clear of the rock-faced granite
    kit.add("STOOP-back", "Granite", FT.steps(17.0, ZF - 0.6, 5).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    # glue joints: nothing small is left butted on a dab of glue (see NOTES.md)
    FT.crown(kit, "TOWER-finial", "TOWER-deck")
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("BAY-crest")]:
        FT.key_into(kit, p_.name, ["BAY-roof"], (0, 0, -1), depth=0.6)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "harcourt")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "harcourt.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
