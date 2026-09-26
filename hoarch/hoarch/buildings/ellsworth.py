"""The Ellsworth: an original HO-scale (1:87.1) Colonial Revival house with a Victorian flair,
house 39 of the Colonial batch (a Colonial front, a Victorian corner tower, a wraparound
porch).

A symmetrical five-bay front, two storeys under a hip roof of ogee-pointed slates: Delft-blue
double-course lap siding below, a paler blue of wave-coursed shingles above, on a foundation
of cobblestones laid in rows. At the front-east corner a hexagonal tower rises a stage above
the eave to a copper ogee roof in flat-seam courses with rolled hips and a flame finial. Its
windows keep to two faces a storey (round-headed lights in keyed archivolts), its top stage's
other front faces carry blind panels with a roundel. A porch runs across the front, round the
foot of the tower and down the east side on panelled pedestals with short Tuscan columns,
bottle balusters, an ochre frieze of festoons with tassels, a fascia of guttae, a louvred
skirt, and a segmental pediment with a cartouche over the steps. Between the storeys an ochre
frieze of lyres, an ivory pellet course and an ivory torus; at the eave an ochre frieze of
torches and bowknots, ivory dentils, a soffit on ogee consoles and an ochre cyma; round the
tower's top an ochre waterleaf frieze on ogee consoles under an ivory crown. First-storey
windows with a divided upper sash under a cushion frieze and a cap; six-over-one windows
above under a carved festoon; a leaded doorway (an oval light, lozenge sidelights, an
elliptical fanlight of rays) between fluted Ionic pilasters under a keyed archivolt. Two
broken-pediment dormers with urns; a herringbone-panelled chimney with two crock pots.

usage: python3 -m hoarch.buildings.ellsworth [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import box, circle, compose, cs_union, inv34, ngon, offset, poly, rect, slab, union, zq
from hoarch import cornice as CO, features as FT, freeclassic as FC, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.ornament import chamfer_box, ext, oval
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Ellsworth"
COLORS = {"Blue": "#6886A4", "Wedgwood": "#93AAC0", "Ivory": "#F2ECDC", "Ochre": "#C99B45", "Slate": "#4F555C",
          "Verdigris": "#5E9C8A", "Cobble": "#8E877C", "Brick": "#8C4533", "PorchDeck": "#F2ECDC",
          "Windows_Doors": "#F2ECDC"}
RENDER_MAT = {"Blue": "siding", "Wedgwood": "shingle", "Ivory": "trim", "Ochre": "accent", "Slate": "roof",
              "Verdigris": "copper", "Cobble": "stone2", "Brick": "brick", "PorchDeck": "trim", "Planks": "planks",
              "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Ellsworth)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="lyres", role="Ochre"),
    dict(kind="course", h=1.4, b=1.4, orn="pellets", role="Ivory"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="torus", role="Ivory")])
EAVE = dict(pitch=11.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.4, b=1.2, orn="torches", role="Ochre"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Ivory", tooth=0.9, gap=0.6),
    dict(kind="bed", h=2.2, b=1.4, P=6.4, role="Ivory", brackets=dict(style="ogee", t=1.2, reach=0.4)),
    dict(kind="crown", h=2.8, b=1.4, P=7.2, orn="cyma", role="Ochre")])
TOWER_C = dict(pitch=7.0, margin=2.6, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="waterleaf", role="Ochre"),
    dict(kind="bed", h=1.8, b=1.4, P=5.2, role="Ivory", brackets=dict(style="ogee", t=0.9, reach=0.6)),
    dict(kind="crown", h=2.2, b=1.4, P=6.0, orn="stepped", role="Ivory")])
RJ = zq(LEDGE + 0.4 + CO.band_height(JOINT))
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 12.0
S1 = ZF + 44.0                  # first-storey shell top = the joint ring's foot
ZE = S1 + RJ + 38.0             # the eave ledge's top
ZW = zq(ZE + HE)                # the wall top behind the eave cornice; the roof sits here
ZT = ZW + 30.0                  # the tower's cornice ledge
ZTW = zq(ZT + CO.band_height(TOWER_C))
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
D_EAVE = 7.4
S_MAIN = 0.9
V1 = 6.0
V2 = S1 + RJ + 4.0 - ZF

# ------------------------------------------------------------------ plan
W, D = 196.0, 112.0
TC, TA = (W - 4.0, -6.0), 21.0  # the hexagonal tower: centre and apothem (edge 0 faces the street)
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
TOWER = Block("tower", ngon(TC, TA, n=6), ZF, ZTW)
BLOCKS = [MAIN, TOWER]
XF = 171.2                      # where the tower meets the front wall; the five bays are centred on 0..XF
DOOR_X = XF / 2
BAYS = [XF * (k + 0.5) / 5 for k in range(5)]
PD, FY, XW, YE = 15.0, -18.0, 10.0, 72.0    # porch: depth round the tower, front line, west end, east run's end
TWIN = {"1": (0, 2), "2": (0, 2), "3": (5, 1)}   # the tower's windows by storey (faces, edge 0 = the street face)
TPANEL = (0, 2)                                    # its top stage's blind panels


def _siding(f, b, reg):
    """Double-course lap below the joint, wave-coursed shingles above it and on the tower's top
    stage; nothing behind the cornices."""
    top = (ZT if b is TOWER else ZE) - b.z0
    reg = reg - rect(-1, top, f.L + 1, (ZTW if b is TOWER else ZW) - b.z0)
    cut = S1 - b.z0
    out = []
    lo = reg ^ rect(-1, -100, f.L + 1, cut)
    hi = reg ^ rect(-1, cut, f.L + 1, 999)
    if not lo.is_empty():
        out.append(FC.siding_double(lo, datum=0.0))
    if not hi.is_empty():
        out.append(FC.shingles_undulating(hi, datum=S1 + RJ - b.z0))
    return union(out) if out else M()


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    lo = FC.window_prairie(10.0, 22.0)
    up = FC.window_festoon(10.0, 20.0)
    add(MAIN, DOOR_X, 0.0, 0.8, FC.door_leaded(12.0, 24.0, 4.0, 6.0), "front-door", "door")
    for k, x in enumerate(BAYS):
        if k != 2:
            add(MAIN, x, 0.0, V1, lo, f"F{x:.0f}-1")
        add(MAIN, x, 0.0, V2, up, f"F{x:.0f}-2")
    for y in (26.0, 58.0, 90.0):
        add(MAIN, 0.0, y, V1, lo, f"W{y:.0f}-1")
        add(MAIN, 0.0, y, V2, up, f"W{y:.0f}-2")
    for y in (48.0, 88.0):
        add(MAIN, W, y, V1, lo, f"E{y:.0f}-1")
        add(MAIN, W, y, V2, up, f"E{y:.0f}-2")
    add(MAIN, 110.0, D, 0.8, FC.door_leaded(9.0, 23.0, 2.6, 4.6), "back-door", "door")
    for x in (26.0, 64.0, 150.0, 180.0):
        add(MAIN, x, D, V1, lo, f"B{x:.0f}-1")
    for x in (26.0, 64.0, 110.0, 150.0, 180.0):
        add(MAIN, x, D, V2, up, f"B{x:.0f}-2")
    # the tower: two faces a storey, alternating with the top stage
    tw = FC.window_keyed_arch(9.0, 20.0)
    tw2 = FC.window_keyed_arch(9.0, 22.0)
    tw3 = FC.window_keyed_arch(8.0, 18.0)
    fs = TOWER.facades()
    for lvl, sp, v0 in (("1", tw, V1), ("2", tw2, V2), ("3", tw3, ZW - ZF + 5.0)):
        for k in TWIN[lvl]:
            m = (fs[k].p0 + fs[k].p1) / 2
            add(TOWER, m[0], m[1], v0, sp, f"tower{k}-{lvl}")
    return L


OPENINGS = _openings()


def tower_panel(w=12.0, h=18.0):
    """A blind panel for the tower's top stage: a moulded frame round a sunk field with an oval
    roundel carrying a boss, a small apron block under it. Local (u across, v up from its foot,
    w out from the wall); prints face-up."""
    fr = rect(-w / 2, 0.0, w / 2, h)
    inner = fr.offset(-1.1, JoinType.Miter, 4.0)
    parts = [ext(fr, 0.0, 0.5), ext(fr - inner, 0.49, 0.95),
             ext((fr - fr.offset(-0.45, JoinType.Miter, 4.0)), 0.94, 1.2)]
    c = (0.0, h * 0.55)
    ring = oval(c, w * 0.26, h * 0.22, 36) - oval(c, w * 0.26 - 0.6, h * 0.22 - 0.6, 36)
    parts.append(ext(ring, 0.49, 1.05))
    parts.append(ext(circle(c, 0.9, 20), 0.49, 1.2))
    parts.append(chamfer_box(-w / 2 + 2.0, -1.2, w / 2 - 2.0, 0.01, 0.0, 0.9, c=0.3, bottom=0.5))
    return union(parts)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = cs_union([b.cs for b in BLOCKS])
    fs = TOWER.facades()
    # the top stage's blind panels: their frames stand where the shingles are left off
    panels = []
    for k in TPANEL:
        f = fs[k]
        A = f.A.copy()
        A[:, 3] = f.world(f.L / 2, ZW - ZF + 5.0, 0.0)
        panels.append((k, A))
    pan_keep = [ext(rect(-6.6, -1.8, 6.6, 18.6), -0.5, 3.0).transform(A) for _, A in panels]
    undress = [slab(offset(MAIN.cs, 8.0) - offset(TOWER.cs, 1.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01)] + pan_keep
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_siding,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        clear=[lip_keep(base, 3.0, ZF, 1.2)])
    kit.add("WALLS-1", "Blue", st["shells"][0], group="walls")
    kit.add("JOINT", "Blue", st["rings"][0], group="walls")
    tkeep = TOWER.solid(grow=0.2, dz0=-1, dz1=1)
    no_lip = union([tkeep, slab(offset(TOWER.cs, 1.0), ZW - 1, ZW + 5)])
    lip = (_corbel(MAIN.cs, 3.0, ZW) + lip_ring(MAIN.cs, 3.0, ZW)) - no_lip
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(base, 3.0, S1 + RJ)
    ledges = (CO.ledge(MAIN.pts, ZE, LEDGE) - tkeep) + CO.ledge(TOWER.pts, ZT, LEDGE)
    kit.add("WALLS-2", "Wedgwood", st["shells"][1] + lip + tring + ledges, group="walls")
    for tag, path, z0, spec, cut in (("J", st["outlines"][0], S1 + LEDGE + 0.4, JOINT, None),
                                     ("E", MAIN.pts, ZE, EAVE, TOWER.solid(grow=1.1, dz0=-2, dz1=2)),
                                     ("T", TOWER.pts, ZT, TOWER_C, None)):
        rings, _ = CO.level(path, z0, spec, cut=cut)
        CO.add_level(kit, rings, f"CORNICE-{tag}", "tower" if tag == "T" else "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="cobble")
    kit.add("FOUNDATION", "Cobble", fnd, group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}", group="inserts", render=zones))
    pnl = tower_panel()
    for k, A in panels:
        kit.add(f"TOWER-panel-{k}", "Ivory", pnl.transform(A), P=inv34(A), key="TOWER-panel", group="tower")
    print("walls + inserts", round(time.time() - t0, 1))

    # --- the main roof: a hollow hip of ogee-pointed slates, two dormers, the chimney behind
    pieces = [(MAIN.pts, [0, 1, 2, 3])]
    roof, rtex = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture="ogee", tex_kw=dict(pitch=1.6, wtab=2.2, d=0.4), zlo=ZW)
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    inner, _ = R.hip_roof(pieces, Z_EAVE - 2.8 * math.sqrt(1 + S_MAIN ** 2), S_MAIN, D_EAVE, texture=None)
    roof = (roof - (inner ^ slab(offset(MAIN.cs, -3.0), ZW - 1, zr + 50))) + rtex
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    roof = roof + union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.3, up=0.7, drop=2.0)
                         for c, e in zip(corners, ends)])
    roof = roof + G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZW, half=1.3, up=0.7)
    roof = roof - lip_keep(MAIN.cs, 3.0, ZW)
    roof = roof.trim_by_plane([0, 0, 1.0], ZW)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 12.0, 9.0
    cx, cy = 62.0, 76.0
    zroof = Z_EAVE + S_MAIN * min(cx - CW / 2 + D_EAVE, cy - CD / 2 + D_EAVE, D + D_EAVE - cy - CD / 2)
    z0 = zq(zroof - 3.0)
    roof = roof + G.chimney_seat(solid_env, cx, cy, CW / 2, zr + 1.0)
    roof = roof - box([cx - CW / 2 - 0.4, cy - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CD / 2 + 0.4, zr + 40])
    roof = roof - slab(offset(TOWER.cs, 1.4), ZW - 1, ZTW + 90)
    DW, DDEP, DHW = 18.0, 20.0, 14.0
    dyf = 16.0
    zdf = zq(Z_EAVE + S_MAIN * (dyf + D_EAVE) - 1.0)
    dbody, dcore, dface, durn = FC.dormer_broken(DW, DDEP, DHW)
    dorms = []
    for dxc in (BAYS[1], BAYS[3]):
        Ad = np.array([[1.0, 0, 0, dxc], [0, 0, -1.0, dyf], [0, 1.0, 0, zdf]])
        dkeep = ext(dface.offset(0.3, JoinType.Miter, 4.0), -DDEP - 0.3, 0.3).transform(Ad)
        dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
        dseat = box([dxc - DW / 2 - 1.3, dyf - 1.6, ZW], [dxc + DW / 2 + 1.3, dyf + DDEP + 1.3, zdf]) ^ solid_env
        dorms.append((Ad, dpocket, dseat))
    for Ad, dp, ds in dorms:
        roof = roof - dp
    for Ad, dp, ds in dorms:
        roof = roof + (ds - dp - lip_keep(MAIN.cs, 3.0, ZW))
    roof = roof - union([dbody.transform(Ad) for Ad, dp, ds in dorms])
    kit.add("ROOF", "Slate", roof, group="roof")
    ch = FC.chimney_herringbone(CW, CD, zq(zr + 16.0 - z0)).translate([cx, cy, z0])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    rise = DW / 2
    ez = DHW - 1.6
    droof_cs = poly([(-DW / 2 - 1.6, ez), (-DW / 2, ez), (-DW / 2, DHW), (0.0, DHW + rise + 0.2), (DW / 2, DHW),
                     (DW / 2, ez), (DW / 2 + 1.6, ez), (DW / 2 + 1.6, ez + 1.6), (0.0, DHW + rise + 2.2),
                     (-DW / 2 - 1.6, ez + 1.6)])
    for k, (Ad, dp, ds) in enumerate(dorms):
        kit.add(f"DORMER-{k}", "Ivory", dbody.transform(Ad), key="DORMER", group="roof")
        kit.add(f"DORMER-core-{k}", "Slate", dcore.transform(Ad), key="DORMER-core", group="roof")
        kit.add(f"DORMER-urn-{k}", "Ochre", durn.transform(Ad), key="DORMER-urn", group="roof")
        droof = ext(droof_cs, -DDEP - 6.0, -1.6).transform(Ad) - solid_env - dbody.transform(Ad) - roof
        kit.add(f"DORMER-roof-{k}", "Slate", max(droof.decompose(), key=lambda m_: m_.volume()), key="DORMER-roof",
                group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the tower's copper ogee roof on its cornice, a flame finial on its neck
    dct = TOWER_C["layers"][-1]["P"] + 0.4
    HO = 38.0
    og = FC.roof_ogee(TA + dct, HO).translate([TC[0], TC[1], ZTW])
    kit.add("TOWER-roof", "Verdigris", og, group="tower")
    kit.add("TOWER-finial", "Ochre", FC.finial_flambeau(1.4, 12.0).translate([TC[0], TC[1], ZTW + HO]), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- the porch: across the front, round the foot of the tower, down the east side
    hexp = ngon(TC, TA + PD, n=6)
    v5, v0, v1, v2, v3 = [np.array(hexp[i]) for i in (5, 0, 1, 2, 3)]
    t1 = (FY - v5[1]) / (v0[1] - v5[1])
    P1 = tuple(v5 + (v0 - v5) * t1)
    XE = W + 18.0
    t2 = (v2[0] - XE) / (v2[0] - v3[0])
    P2 = tuple(v2 + (v3 - v2) * t2)
    ppts = [(XW, 0.0), (XW, FY), P1, tuple(v0), tuple(v1), tuple(v2), P2, (XE, YE), (W, YE), (W, 0.0)]
    inset = 1.6
    ca = inset * math.tan(math.radians(30.0))          # at the hexagon's corners (a 60 degree turn)
    cm = inset * math.tan(math.radians(30.0))          # at the two inside corners (also 60 degrees)

    def L_(a, b):
        return float(np.linalg.norm(np.array(b) - np.array(a)))

    Lf = L_((XW, FY), P1)
    ud = DOOR_X - XW
    Lh = L_(v0, v1)
    runs = [dict(a=(XW, 0.0), b=(XW, FY), posts=[3.0, -FY - 1.6]),
            dict(a=(XW, FY), b=P1, posts=[1.6, 30.0, ud - 12.0, ud + 12.0, 0.5 * (ud + 12.0 + Lf), Lf + cm],
                 piers=[1.6, 30.0, ud - 12.0, ud + 12.0, 0.5 * (ud + 12.0 + Lf), Lf - ca]),
            dict(a=P1, b=tuple(v0), posts=[-cm, L_(P1, v0) - ca], piers=[ca, L_(P1, v0) - ca]),
            dict(a=tuple(v0), b=tuple(v1), posts=[ca, Lh / 2, Lh - ca]),
            dict(a=tuple(v1), b=tuple(v2), posts=[ca, Lh / 2, Lh - ca]),
            dict(a=tuple(v2), b=P2, posts=[ca, L_(v2, P2) + cm], piers=[ca, L_(v2, P2) - ca]),
            dict(a=P2, b=(XE, YE), posts=[-cm, 0.5 * (YE - P2[1]), YE - P2[1] - 1.6],
                 piers=[ca, 0.5 * (YE - P2[1]), YE - P2[1] - 1.6]),
            dict(a=(XE, YE), b=(W, YE), posts=[1.6, XE - W - 3.0])]
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    PP = FT.porch_turned(ppts, runs, H_floor, post_h, steps_at=[(1, ud, 18.0)],
                         planks=dict(pitch=1.8, border=1.2), joined=True, ledger_off=1.5, post="pedestal",
                         rail="pear", arcade="festoons", skirt="louvres", pier_tex="cobble", roof_edge="guttae")
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    deck = PP["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    tabs = union([arc_ for arc_, _ in PP["arcades"]])
    for k, fr in enumerate(sorted(PP["frames"], key=lambda m_: -m_.volume())):
        kit.add(f"PORCH-frame-{k}", "Ivory", fr - tabs - fnd, group="porch")
    for k, (arc_, A) in enumerate(PP["arcades"]):
        kit.add(f"PORCH-frieze-{k}", "Ochre", arc_, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = union([b.solid(grow=1.8, dz0=-20, dz1=0) for b in BLOCKS])
    proof = PP["roof"] - bld_keep - ins_keep
    ptop = proof.bounding_box()[5]
    kit.add("PORCH-roof", "Ivory", proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8)), P=print_flip(), group="porch")
    kit.add("PORCH-roof-top", "Slate", proof.trim_by_plane([0, 0, 1.0], ptop - 0.8), group="porch")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PORCH-steps-{k}", "Cobble", sm.transform(A) - fkeep - deck, group="porch")
    edep = 5.0
    Ag = np.array([[-1.0, 0, 0, DOOR_X], [0, -1.0, 0, FY - 1.0 + edep], [0, 0, 1.0, ptop]])
    kit.add("PORCH-pediment", "Ivory", FC.entry_segmental(22.0, edep, 6.4).transform(Ag), P=inv34(Ag), group="porch")
    e, u = MAIN.locate(110.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Cobble", FT.steps(16.0, ZF - 0.6, 4).transform(A) - fnd, group="porch")
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "ellsworth")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "ellsworth.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
