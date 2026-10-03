"""The Fontaine -- an original HO-scale (1:87.1) Second Empire house of the mansard batch (houses
81 to 90), on the batch's roof system (hoarch.secondempire), and the batch's grandest.

An H in plan, of grey granite: the ground storey in banded rustication, the upper one in fine
ashlar, vermiculated quoins at every corner, marble dressings and verdigris accents, on a battered
granite plinth. A centre range under a straight mansard between two end pavilions that break
forward and back under taller mansards of their own; a square tower in the middle of the front,
flush with the pavilions, carrying the entrance and rising a storey over the eave to a swelling
dome with three wreathed oculi, a crest and a bannerette vane. The slating is square with a band
of diamond-slate pyramids. Verandas fill the two recesses either side of the tower on
bell-capital columns, tulip balusters, a lunette frieze and a fascia of bells; their deck runs on
in front of them as an open terrace that meets before the tower door, railed with tulip balusters
between ball-capped newels, the steps coming down at the door.

- Ground-floor windows round-headed between engaged columns under a short entablature, a shield
  keystone; upper windows in eared architraves under broken pediments with urns; the tower's top
  window under an archivolt over a balustered apron; the entrance a double door under a fanlight of
  three circles between paired columns, an entablature and a balustered blocking course.
- Storey joint: a marble chain of bells, a verdigris frieze of lozenges and rosettes, a marble
  crown.
- Eave (and the tower's top): a marble loop knot, a verdigris frieze of coronets, a chain of
  bells, a soffit on ram's-horn consoles and a verdigris crown.
- Crests: a marble loop knot under a verdigris ovolo crown on block modillions.

usage: python3 -m hoarch.buildings.fontaine [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, openings as O, roof as R, secondempire as SE
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Fontaine"
COLORS = {"PorchDeck": "#E9E5DA", "Planks": "#6F5034",       # the planked porch floor: two colours, one change
          "Granite": "#A29E95", "Marble": "#E9E5DA", "Verdigris": "#4F7F6E", "Slate": "#343B47", "Iron": "#232528",
          "Plinth": "#6F6B66", "Windows_Doors": "#E9E5DA", "Addins": "#343B47"}
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks", "Granite": "walls", "Marble": "trim", "Verdigris": "accent",
              "Slate": "roof", "Iron": "iron", "Plinth": "stone", "Windows_Doors": "trim", "Addins": "roof", "Sash": "sash",
              "Door": "door", "Glass": "glass"}
PALETTE = {"walls": ["#A29E95", 0.85, 0.0], "trim": ["#E9E5DA", 0.6, 0.0], "accent": ["#4F7F6E", 0.5, 0.0],
           "roof": ["#343B47", 0.75, 0.0], "iron": ["#232528", 0.45, 0.3], "stone": ["#6F6B66", 0.9, 0.0],
           "planks": ["#6F5034", 0.75, 0.0], "sash": ["#22262A", 0.45, 0.0], "door": ["#4F7F6E", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Fontaine)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="bellchain", role="Marble"),
    dict(kind="frieze", h=5.4, b=1.2, orn="lozengerosettes", role="Verdigris"),
    dict(kind="crown", h=2.2, b=1.4, P=3.8, orn="bevel", role="Marble")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="loopknot", role="Marble"),
    dict(kind="frieze", h=6.4, b=1.2, orn="coronets", role="Verdigris"),
    dict(kind="course", h=1.6, b=1.4, orn="bellchain", role="Marble"),
    dict(kind="bed", h=2.2, b=1.4, P=7.0, role="Marble", brackets=dict(style="ramshorn", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.8, b=1.4, P=7.8, orn="cyma", role="Verdigris")])
TOWER_C = dict(pitch=11.0, margin=3.5, layers=[
    dict(kind="frieze", h=6.0, b=1.2, orn="coronets", role="Verdigris"),
    dict(kind="bed", h=2.0, b=1.4, P=6.0, role="Marble", brackets=dict(style="ramshorn", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.4, b=1.4, P=6.8, orn="cyma", role="Verdigris")])
CREST_COURSE = dict(h=2.0, b=0.6, orn=SE.loopknot, role="Marble")
CREST_CROWN = dict(h=2.6, P=3.4, kind="ovolo", role="Verdigris", blocks=(0.9, 5.0))
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (all on the 0.2 mm grid)
ZF = 13.0
S1 = ZF + 42.0
ZE = S1 + RJ + 38.0
ZW = ZE + HE
MZ0 = ZW
MH, PMH = 30.0, 42.0       # the centre range's mansard, the pavilions'
MZ1, PZ1 = MZ0 + MH, MZ0 + PMH
DK = EAVE["layers"][-1]["P"] + 0.2
D_TOP, PD_TOP = -2.0, -4.0
MANSARD = [(DK, MZ0), (DK - 1.4, MZ0 + 1.4), (D_TOP, MZ1)]
PAV_MANSARD = [(DK, MZ0), (DK - 1.4, MZ0 + 1.4), (PD_TOP, PZ1)]
SLATE = dict(pitch=1.8, wtab=2.4, d=0.4, shape=SE.slate_pyramids)
ZT = ZW + 40.0            # the tower's ledge: its top storey stands over the eave and the centre crest
ZTW = ZT + CO.band_height(TOWER_C)
DOME_H = 28.0
V1, V2 = 6.4, S1 + RJ + 5.0 - ZF
V3 = ZW + 9.0 - ZF
Z_ADD = MZ0 + 3.2
Z_ADDP = MZ0 + 5.0

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
PW_, PY0, PY1 = 52.0, -20.0, 124.0         # the pavilions: width, front, back
X1 = 224.0
PAVW = Block("pav-west", [(0, PY0), (PW_, PY0), (PW_, PY1), (0, PY1)], ZF, ZW)
PAVE = Block("pav-east", [(X1 - PW_, PY0), (X1, PY0), (X1, PY1), (X1 - PW_, PY1)], ZF, ZW)
MAIN = Block("centre", [(PW_ - 12.0, 0), (X1 - PW_ + 12.0, 0), (X1 - PW_ + 12.0, 104.0), (PW_ - 12.0, 104.0)], ZF, ZW)
TX0, TX1, TY0, TY1 = 94.0, 130.0, -20.0, 16.0
TOWER = Block("tower", [(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)], ZF, ZTW)
TERR = 14.0               # the open terrace's depth before the verandas and the tower
NEWEL_H = 14.3            # (the porch builder's post height that makes its newels 12.5 tall)
BLOCKS = [MAIN, PAVW, PAVE, TOWER]
PAVS = [(PAVW, "PAVW"), (PAVE, "PAVE")]
CX = X1 / 2


def _stone(f, b, reg):
    """Banded rustication below the joint, fine ashlar above; nothing in the cornice bands."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    if b is TOWER:
        reg = reg - rect(-1, ZT - b.z0, f.L + 1, 999)
    lo = reg ^ rect(-1, -100, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, S1 + RJ - b.z0, f.L + 1, 999)
    out = []
    if not lo.is_empty():
        out.append(SE.bandedrustic(lo, datum=1.8))
    if not hi.is_empty():
        out.append(SE.ashlarfine(hi, datum=S1 + RJ - b.z0 + 0.4))
    return union(out) if out else M()


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    lo = SE.window_fontaine_lower()
    up = SE.window_fontaine_upper()
    tw = SE.window_fontaine_tower()
    front = SE.door_fontaine()
    back = SE.door_fontaine_back()

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    add(TOWER, CX, TY0, 0.4, front, "front-door", "door")
    add(TOWER, CX, TY0, V2, up, "T-S2")
    add(TOWER, CX, TY0, V3, tw, "T-S3")                     # the tower's top storey: one light, on the street
    for x in (72.0, X1 - 72.0):                                                    # the centre range
        add(MAIN, x, 0, V1, lo, f"C{x:.0f}-1")
        add(MAIN, x, 0, V2, up, f"C{x:.0f}-2")
        add(MAIN, x, 104.0, V1, lo, f"N{x:.0f}-1")
        add(MAIN, x, 104.0, V2, up, f"N{x:.0f}-2")
    add(MAIN, CX, 104.0, V2, up, "N112-2")
    add(MAIN, CX, 104.0, 0.4, back, "back-door", "door")
    for pav, tag in PAVS:                                                          # the pavilions
        x0 = pav.pts[0][0]
        x = x0 + PW_ / 2                                       # one window a floor in each end: solid masonry round it
        add(pav, x, PY0, V1, lo, f"{tag}S-1")
        add(pav, x, PY0, V2, up, f"{tag}S-2")
        add(pav, x, PY1, V1, lo, f"{tag}N-1")
        add(pav, x, PY1, V2, up, f"{tag}N-2")
        xs = 0.0 if pav is PAVW else X1
        for y in (10.0, 52.0, 94.0):
            add(pav, xs, y, V1, lo, f"{tag}{y:.0f}-1")
            add(pav, xs, y, V2, up, f"{tag}{y:.0f}-2")
    return L


OPENINGS = _openings()
MAIN_ADDINS = [(72.0, 0.0), (X1 - 72.0, 0.0), (72.0, 104.0), (CX, 104.0), (X1 - 72.0, 104.0)]
TOWER_ADDINS = [(CX, TY0), (TX0, 0.0), (TX1, 0.0)]


def _frame_on(block, x, y, z, w0):
    e, u = block.locate(x, y)
    f = block.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, z - ZF, w0)
    return A


def _volume(path, prof, top=0.0):
    """The solid inside a mansard's outer face (to cut the other roof back to it), carried up
    ``top`` past its last point."""
    P, Mi = R._edges(path)

    def ring(d, z):
        return np.c_[P + d * Mi, np.full(len(P), z)]
    segs = list(zip(prof[:-1], prof[1:])) + ([(prof[-1], (prof[-1][0], prof[-1][1] + top))] if top else [])
    return union([M.hull_points(np.vstack([ring(d0, z0), ring(d1, z1)]).tolist()) for (d0, z0), (d1, z1) in segs])


def _addins(kit, places, prof, z_sill, tag):
    """One roof's add-ins, places = [(block, x, y, spec, key)], one plug length each roof (one
    colour change). Returns (pocket cutters, slate clearances) in world."""
    pl = [SE.addin_place(sp, prof, z_sill) for _, _, _, sp, _ in places]
    depth = max(d for _, d in pl)
    keeps, flashes = [], []
    for k, ((block, x, y, sp, key), (w0, _)) in enumerate(zip(places, pl)):
        A = _frame_on(block, x, y, z_sill, w0)
        a = SE.addin(sp, depth)
        keeps.append(a["keep"].transform(A))
        flashes.append(a["flash"].transform(A))
        zones = [("Glass", a["glass"].transform(A)), ("Slate", (a["plug"] - a["glass"]).transform(A)),
                 ("Marble", a["frame"].transform(A))]
        kit.add(f"{tag}-{k}", "Addins", a["solid"].transform(A), P=inv34(A), change=(round(depth, 1), "Marble"),
                key=f"{tag}-{key}", group="addins", render=zones)
    print(tag, "plug", depth)
    return union(keeps), union(flashes)


def _deck(C, z):
    dcs = poly(R.offset_path(C["path"], -1.6))
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + 2.6, x1, 5.2)]) ^ dcs
    return C["deck"] + slab(seams, z - 0.01, z + 0.4)


# ------------------------------------------------------------------ build
def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    allcs = cs_union([b.cs for b in BLOCKS])
    eave_path = max(allcs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(allcs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="vermiquoin", clear=[lip_keep(allcs, 3.0, ZF, 1.2)],
                        siding=_stone, prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=undress)
    kit.add("WALLS-1", "Granite", st["shells"][0], group="walls")
    kit.add("JOINT", "Granite", st["rings"][0], group="walls")
    # inside the house the tower's walls rise from the joint so its top storey bears all round
    rest = cs_union([b.cs for b in (MAIN, PAVW, PAVE)])
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(rest, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(allcs, 3.0, S1 + RJ)
    ledges = CO.ledge(eave_path, ZE, LEDGE) + CO.ledge(TOWER.pts, ZT, LEDGE)
    tlip = _corbel(TOWER.cs, 3.0, ZTW) + lip_ring(TOWER.cs, 3.0, ZTW)
    kit.add("WALLS-2", "Granite", st["shells"][1] + tring + ledges + tlip, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    tcen = ((TX0 + TX1) / 2, (TY0 + TY1) / 2)
    cut = CO.blades(CO.tower_cuts(eave_path, tcen, 34.0, tower=TOWER.pts, house=MAIN.pts), ZE, ZW)
    rings, _ = CO.level(eave_path, ZE, EAVE, cut=cut)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(TOWER.pts, ZT, TOWER_C)
    CO.add_level(kit, rings, "CORNICE-T", "tower")
    kit.add("FOUNDATION", "Plinth", foundation(BLOCKS, 0.0, ZF, style="batteredgranite"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Marble", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    tower_keep = TOWER.solid(grow=2.1, dz0=-1, dz1=400)
    tower_hug = TOWER.solid(grow=0.5, dz0=-1, dz1=400)
    # --- the three mansards (upside down): the pavilions' rise through the centre's; each is cut
    # back to the other's slates
    main_vol = _volume(MAIN.pts, [(d + 0.5, z) for d, z in MANSARD])
    pav_vols = union([_volume(p.pts, [(d + 0.5, z) for d, z in PAV_MANSARD], top=20.0) for p, _ in PAVS])
    mans, mtex, inner = R.mansard(MAIN.pts, MANSARD, t=2.6, tex=SLATE)
    sp, big = SE.addin_fontaine(), SE.addin_fontaine(big=True)
    mk, mf = _addins(kit, [(MAIN, x, y, sp, "one") for x, y in MAIN_ADDINS], MANSARD, Z_ADD, "ADDIN")
    pplaces = []
    for pav, tag in PAVS:
        x0 = pav.pts[0][0]
        pplaces += [(pav, x0 + PW_ / 2, PY0, big, "big"), (pav, x0 + PW_ / 2, PY1, big, "big")]
        xs = 0.0 if pav is PAVW else X1
        pplaces += [(pav, xs, y, sp, "one") for y in (10.0, 52.0, 94.0)]
    pk, pf = _addins(kit, pplaces, PAV_MANSARD, Z_ADDP, "ADDIN-P")
    C = SE.crest_ring(MAIN.pts, D_TOP, MZ1, D_TOP - inner(MZ1), CREST_COURSE, CREST_CROWN)
    kit.add("MANSARD", "Slate", (mans + (mtex - mf)) - mk - pav_vols - tower_hug - C["groove"], P=print_flip(), group="roof")
    kit.add("CREST", "Verdigris", C["solid"] - pav_vols - tower_hug, P=print_flip(), change=C["change"], group="roof",
            render=[(r, z - pav_vols - tower_hug) for r, z in C["zones"]])
    zdeck = C["z_top"]
    chims = [(70.0, 70.0), (X1 - 70.0, 70.0)]
    pads = union([box([x - 6.0, y - 5.0, zdeck - 0.6], [x + 6.0, y + 5.0, zdeck + 1]) for x, y in chims])
    kit.add("ROOF-deck", "Slate", _deck(C, zdeck) - pads - pav_vols - tower_hug, group="roof")
    for i, seg, A, L in SE.cresting_strips(C["path"], zdeck, C["rail"], SE.fence_fontaine, 3.4):
        for j, piece in enumerate((seg - pav_vols - tower_keep).decompose()):
            if piece.volume() > 3.0:
                kit.add(f"CREST-iron-{i}{'abc'[j]}", "Iron", piece, P=inv34(A), group="roof")
    for k, (x, y) in enumerate(chims):
        ch = SE.chimney_fontaine(w=11.0, d=9.0, h=25.0).translate([x, y, zdeck - 0.6])
        kit.add(f"CHIMNEY-{k}", "Granite", ch, key="CHIMNEY", group="roof")
    for pav, tag in PAVS:
        pm, ptex, pin = R.mansard(pav.pts, PAV_MANSARD, t=2.6, tex=SLATE)
        PC = SE.crest_ring(pav.pts, PD_TOP, PZ1, PD_TOP - pin(PZ1), CREST_COURSE, CREST_CROWN)
        kit.add(f"{tag}-MANSARD", "Slate", (pm + (ptex - pf)) - pk - main_vol - PC["groove"], P=print_flip(), group="pavilions")
        kit.add(f"{tag}-CREST", "Verdigris", PC["solid"], P=print_flip(), change=PC["change"], group="pavilions",
                render=PC["zones"])
        pz = PC["z_top"]
        kit.add(f"{tag}-deck", "Slate", _deck(PC, pz), group="pavilions")
        for i, seg, A, L in SE.cresting_strips(PC["path"], pz, PC["rail"], SE.fence_fontaine, 3.8):
            kit.add(f"{tag}-iron-{i}", "Iron", seg, P=inv34(A), key=f"PAV-iron-{round(L, 1)}", group="pavilions")
    print("roofs", round(time.time() - t0, 1))

    # --- the tower: its cornice (above), a swelling dome with three oculi, crest, vane
    dprof = SE.bell_profile(TOWER_C["layers"][-1]["P"] + 0.2, ZTW, -7.0, ZTW + DOME_H, kick=(0.6, 0.6), power=1.7,
                            step=7.2, convex=True)
    dome, dtex, din = R.mansard(TOWER.pts, dprof, t=2.4, tex=dict(pitch=1.6, wtab=2.0, d=0.35, shape="square"))
    oc = SE.addin_fontaine_oculus()
    tk, tf = _addins(kit, [(TOWER, x, y, oc, "oculus") for x, y in TOWER_ADDINS], dprof, ZTW + 4.0, "ADDIN-T")
    TC = SE.crest_ring(TOWER.pts, dprof[-1][0], ZTW + DOME_H, dprof[-1][0] - din(ZTW + DOME_H), CREST_COURSE, CREST_CROWN)
    dm = (dome + (dtex - tf)) - tk - lip_keep(TOWER.cs, 3.0, ZTW) - TC["groove"]
    dm = union([c for c in dm.decompose() if c.volume() > 50.0])       # not the loose middle the groove cuts off
    kit.add("TOWER-DOME", "Slate", dm, P=print_flip(),
            group="tower")
    kit.add("TOWER-CREST", "Verdigris", TC["solid"], P=print_flip(), change=TC["change"], group="tower", render=TC["zones"])
    tz = TC["z_top"]
    kit.add("TOWER-deck", "Slate", TC["deck"], group="tower")
    for i, seg, A, L in SE.cresting_strips(TC["path"], tz, TC["rail"], SE.fence_fontaine, 3.4):
        kit.add(f"TOWER-iron-{i}", "Iron", seg, P=inv34(A), key=f"TOWER-iron-{round(L, 1)}", group="tower")
    kit.add("TOWER-finial", "Iron", SE.finial_bannerette(14.0).translate([tcen[0], tcen[1], tz - 0.01]), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- verandas in the two recesses either side of the tower, on one deck that runs on in
    #     front of them as an open terrace, meeting before the tower door; the steps at the door
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    w_, yf = -1.4, PY0
    fkeep = slab(offset(allcs, 1.7), -1, ZF + 1.3)
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=300) for b in BLOCKS])
    socks, vposts = [], []
    for tag, xa, xb in (("VERANDA-W", PW_ + 1.4, TX0 - 1.4), ("VERANDA-E", TX1 + 1.4, X1 - PW_ - 1.4)):
        Lf = xb - xa
        pts = [(xa, w_), (xa, yf), (xb, yf), (xb, w_)]
        runs = [dict(a=(xa, yf), b=(xb, yf), posts=[1.7, Lf - 1.7])]       # clear of the walls' plinths
        # (the steps' gap in the railing is the way out onto the terrace; the steps themselves go)
        P = FT.porch_turned(pts, runs, H_floor, post_h, steps_at=[(0, Lf / 2, 14.0)], planks=dict(pitch=1.4, border=1.6),
                            joined=True, post="bellcapital", rail="tulipbell", arcade="lunettearcade", skirt="rusticblocks",
                            pier_tex="stone", roof_edge="belldrops", top=True)
        P["top"] = P["top"] + P["roof"].translate([0.0, 0.0, -0.1])      # fuse the roof to the beams it sits on
        FT.add_porch_top(kit, tag, P, bld_keep + ins_keep, "Marble", "Marble", tin_col="Slate", tin="flat")
        socks += [box([x - 1.0, y - 1.0, H_floor - 2.0], [x + 1.0, y + 1.0, H_floor + 1.0]) for x, y in P["sockets"]]
        vposts += [xa + 1.7, xb - 1.7]
    # the deck under both: the verandas' floors, then the terrace strip TERR deep across the front,
    # stepped back past the tower's foundation; newels and tulip-bell railings round its open edges,
    # one at each veranda's front post, and either side of the steps
    XA, XB, YT, yt = PW_ + 1.4, X1 - PW_ - 1.4, PY0 - TERR, TY0 + w_
    pts = [(XA, w_), (XA, yf), (XA, YT), (XB, YT), (XB, yf), (XB, w_), (TX1 + 1.4, w_), (TX1 + 1.4, yt),
           (TX0 - 1.4, yt), (TX0 - 1.4, w_)]
    LT = XB - XA
    truns = [dict(a=(XA, yf), b=(XA, YT), posts=[2.4, TERR - 1.6]),            # clear of the pavilion's foundation
             dict(a=(XA, YT), b=(XB, YT), posts=[1.6, vposts[1] - XA, CX - 12.6 - XA, CX + 12.6 - XA, vposts[2] - XA,
                                                LT - 1.6]),
             dict(a=(XB, YT), b=(XB, yf), posts=[1.6, TERR - 2.4])]
    T = FT.porch_turned(pts, truns, H_floor, NEWEL_H, steps_at=[(1, CX - XA, 22.0)], planks=dict(pitch=1.4, border=1.6),
                        joined=True, post="bellnewel", rail="tulipbell", arcade="lunettearcade", skirt="rusticblocks",
                        pier_tex="stone", roof_edge="belldrops")
    deck_ = T["deck"] - fkeep - union(socks)
    kit.add("PORCH-deck", "PorchDeck", deck_, P=print_flip(), group="porch",
            render=FT.plank_zones(deck_, H_floor, "Planks", "PorchDeck"))
    for i, fr in enumerate(T["frames"]):
        kit.add(f"TERRACE-rail-{i}", "Marble", fr, group="porch")
    for k, (sm, A) in enumerate(T["steps"]):
        kit.add(f"TERRACE-steps-{k}" if len(T["steps"]) > 1 else "TERRACE-steps", "Plinth", sm.transform(A) - fkeep,
                group="porch")
    e, u = MAIN.locate(CX, 104.0)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Plinth", FT.steps(15.0, ZF - 0.6, 5).transform(A), group="porch")
    print("porches", round(time.time() - t0, 1))
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("CREST-iron")]:
        FT.key_into(kit, p_.name, ["CREST"], (0, 0, -1), depth=0.6)
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("PAV") and "-iron-" in p_.name]:
        FT.key_into(kit, p_.name, [p_.name.split("-iron-")[0] + "-CREST"], (0, 0, -1), depth=0.6)
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("TOWER-iron")]:
        FT.key_into(kit, p_.name, ["TOWER-CREST"], (0, 0, -1), depth=0.6)
    FT.crown(kit, "TOWER-finial", "TOWER-deck")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "fontaine")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "fontaine.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Addins"))
