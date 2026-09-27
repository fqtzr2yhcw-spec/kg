"""The Capistrano: an original HO-scale (1:87.1) Mission Revival house, house 55 of the fifth
batch (the Craftsman era, 1900-1930).

Two storeys of hand-troweled plaster under low hipped roofs of pan-and-cover clay tile with
broad eaves on ogee-cut rafter tails. Over the front wall rises the mission parapet: ogee
shoulders, stepped scrolls and a round-arched crest with a quatrefoil, capped in tile. At the
east corner a bell tower climbs past the roof to an open belfry, a round arch in every face and
a bell hung in the front one, under a low tiled pyramid. Across the front, between the corner
and the tower, an arcade of round arches on plain round columns, low pierced walls between
them. The ground-floor windows are round-arched behind wrought-iron rejas; the upper ones
segmental with keystones on corbelled sills. The door is a studded plank leaf under a round
arch in a portal of barley-twist columns with a shell over it. Between the storeys little bell
niches over a corbel table; at the eaves a blind arcade on Solomonic colonnettes over
crosslets.

usage: python3 -m hoarch.buildings.capistrano [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, circle, cs_union, offset, rect, slab, union
from hoarch import craftsman2 as CR2, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Capistrano"
COLORS = {"Adobe": "#E8D8BE", "Terracotta": "#B2552F", "Timber": "#5A3B26", "Clay": "#C9A27A", "Iron": "#2E2B28",
          "Planks": "#8C4A32", "PorchDeck": "#8C4A32", "Windows_Doors": "#5A3B26"}
RENDER_MAT = {"Adobe": "siding", "Terracotta": "roof", "Timber": "wood", "Clay": "trim", "Iron": "accent",
              "Planks": "planks", "PorchDeck": "planks", "Windows_Doors": "wood", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Capistrano)
LEDGE = 1.4
JOINT = dict(pitch=15.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="bellniches", role="Clay"),
    dict(kind="course", h=1.6, b=1.4, orn="corbeltable", role="Adobe"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="stepped", role="Clay")])
EAVE = dict(pitch=14.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.8, b=1.2, orn="solomonic", role="Clay"),
    dict(kind="course", h=1.6, b=1.4, orn="crosslets", role="Adobe"),
    dict(kind="bed", h=2.6, b=1.4, P=7.0, role="Timber", brackets=dict(style="ogeetail", t=1.2, reach=0.35)),
    dict(kind="crown", h=2.2, b=1.4, P=7.4, orn="cavetto", role="Timber")])
TOWER_C = dict(pitch=12.0, margin=3.0, layers=[
    dict(kind="frieze", h=4.2, b=1.2, orn="bellniches", role="Clay"),
    dict(kind="course", h=1.4, b=1.4, orn="crosslets", role="Adobe"),
    dict(kind="crown", h=2.2, b=1.4, P=4.4, orn="cavetto", role="Timber")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 8.0
S1 = ZF + 38.0
ZU = S1 + RJ
ZE = ZU + 32.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
D_EAVE = 8.0
S_MAIN = 0.42
W, D = 150.0, 96.0
XC, YC = W / 2, D / 2
TX0, TX1, TY0, TY1 = 112.0, 150.0, -16.0, 22.0     # the bell tower
TXC, TYC = (TX0 + TX1) / 2, (TY0 + TY1) / 2
ZT = ZW + 34.0
ZTW = round((ZT + CO.band_height(TOWER_C)) / 0.2) * 0.2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
TOWER = Block("tower", [(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)], ZF, ZTW)
BLOCKS = [MAIN, TOWER]
PX0, PL, PH = 22.0, 70.0, 34.0                      # the mission parapet over the front wall
PXC = PX0 + PL / 2
V1 = 6.0
V2 = ZU - ZF + 4.0
BEL_SILL = ZW + 16.0                                # the belfry's arches: sill, springing, half-width
BEL_SPRING = BEL_SILL + 8.0
BEL_R = 5.5
BAR_TOP = BEL_SPRING + 0.8


def _skin(f, b, reg):
    top = (ZE if b is MAIN else ZT) - LEDGE - 0.6 - b.z0
    band_hi = (ZW if b is MAIN else ZTW) - b.z0 + 0.2
    reg = reg - rect(-1, top, f.L + 1, band_hi)
    out = CR2.stucco_mission(reg, seed=int(f.p0[0] * 3 + f.p0[1]) % 89)
    if b is MAIN and f.n[1] < -0.5:                  # the quatrefoil in the parapet's crest
        c = (PXC, ZW - ZF + PH - 12.0)
        r = 2.0
        q = cs_union([circle((c[0] + dx, c[1] + dy), r, 24) for dx, dy in ((r, 0), (-r, 0), (0, r), (0, -r))])
        ring = q.offset(0.7) - q
        out = out + M.extrude(ring, 0.9) - M.extrude(q, 1.0).translate([0, 0, -0.6])
    return out


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    g = CR2.window_reja(14.0, 20.0)
    u = CR2.window_segmental(14.0, 16.0)
    gt = CR2.window_reja(12.0, 20.0)
    ut = CR2.window_segmental(12.0, 16.0)
    add(MAIN, PXC, 0.0, 0.4, CR2.door_mission(12.0, 24.0), "front-door", "door")
    for x in (35.0, 79.0):
        add(MAIN, x, 0.0, V1, g, f"S{x:.0f}-1")
    for x in (22.0, PXC, 92.0):
        add(MAIN, x, 0.0, V2, u, f"S{x:.0f}-2")
    add(TOWER, TXC, TY0, V1, gt, "T-S-1")
    add(TOWER, TXC, TY0, V2, ut, "T-S-2")
    add(TOWER, TX1, 3.0, V1, gt, "T-E-1")
    add(TOWER, TX1, 3.0, V2, ut, "T-E-2")
    add(MAIN, W, 60.0, V1, g, "E60-1")
    for y in (44.0, 78.0):
        add(MAIN, W, y, V2, u, f"E{y:.0f}-2")
    for y in (28.0, 68.0):
        add(MAIN, 0.0, y, V1, g, f"W{y:.0f}-1")
        add(MAIN, 0.0, y, V2, u, f"W{y:.0f}-2")
    for x in (30.0, 64.0):
        add(MAIN, x, D, V1, g, f"N{x:.0f}-1")
    add(MAIN, 104.0, D, 0.4, CR2.door_plankarch(9.0, 21.0), "back-door", "door")
    for x in (30.0, 72.0, 114.0):
        add(MAIN, x, D, V2, u, f"N{x:.0f}-2")
    return L


OPENINGS = _openings()


def _belfry():
    """The belfry arches (cuts through the tower walls) and their trim: an archivolt band,
    impost blocks and a sill on every face, and the slots in the front arch's jambs that take
    the bell's bar."""
    cuts, trim = [], []
    for e, f in enumerate(TOWER.facades()):
        uc = f.L / 2
        vs = BEL_SPRING - TOWER.z0
        v0 = BEL_SILL - TOWER.z0
        arch = cs_union([rect(uc - BEL_R, v0, uc + BEL_R, vs), circle((uc, vs), BEL_R, 40)])
        cuts.append(f.place(M.extrude(arch, 7.0).translate([0, 0, -5.0])))
        band = (circle((uc, vs), BEL_R + 1.3, 40) - circle((uc, vs), BEL_R, 40)) ^ rect(uc - 9, vs, uc + 9, vs + 9)
        imp = rect(uc - BEL_R - 1.6, vs - 1.0, uc - BEL_R, vs + 0.01) + rect(uc + BEL_R, vs - 1.0, uc + BEL_R + 1.6, vs + 0.01)
        sill = rect(uc - BEL_R - 1.8, v0 - 1.0, uc + BEL_R + 1.8, v0 + 0.01)
        trim.append(f.place(M.extrude(band, 0.9) + M.extrude(imp, 1.1) + M.extrude(sill, 1.3)))
    slot = box([TXC - 7.0, TY0 + 0.65, BAR_TOP - 1.7], [TXC + 7.0, TY0 + 3.1, BAR_TOP + 0.1])
    return union(cuts), union(trim), slot


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    allcs = cs_union([b.cs for b in BLOCKS])
    par = CR2.mission_parapet(PL, PH)
    gables = [(MAIN, 0, par.translate((PX0, ZW - ZF)))]
    tower_keep = TOWER.solid(grow=0.2, dz0=-1, dz1=1)
    undress = [slab(offset(base, 10.0) - offset(TOWER.cs, 1.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01)]
    clear = [lip_keep(allcs, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=gables, clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((XC - 14.0, 3.0), (XC - 14.0, D - 3.0), 2.0, ZF, ZW)])
    kit.add("WALLS-1", "Adobe", st["shells"][0], group="walls")
    kit.add("JOINT", "Adobe", st["rings"][0], group="walls")
    no_lip = union([box([PX0 - 1.0, -1, ZW - 1], [PX0 + PL + 1.0, 5.0, ZW + 5]), tower_keep,
                    slab(offset(TOWER.cs, 1.0), ZW - 1, ZW + 5)])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(base, -3.05), ZU, ZW + 1.2)
    tring = tring - lip_keep(allcs, 3.0, ZU)
    ledges = (CO.ledge(MAIN.pts, ZE, LEDGE) - tower_keep) + CO.ledge(TOWER.pts, ZT, LEDGE)
    z_floor = BEL_SILL - 1.2
    shelf = _corbel(TOWER.cs, 3.0, z_floor, reach=2.0)
    bcut, btrim, slot = _belfry()
    w2 = st["shells"][1] + lip + tring + ledges + shelf
    w2 = (w2 - bcut) + btrim - slot
    kit.add("WALLS-2", "Adobe", w2, group="walls")
    kit.add("BELFRY-floor", "Clay", slab(offset(TOWER.cs, -3.15), z_floor, z_floor + 1.2), group="tower")
    for tag, path, z0, spec, cut in (("J", st["outlines"][0], S1 + LEDGE + 0.4, JOINT, None),
                                     ("E", MAIN.pts, ZE, EAVE, TOWER.solid(grow=1.1, dz0=-2, dz1=2)),
                                     ("T", TOWER.pts, ZT, TOWER_C, None)):
        rings, _ = CO.level(path, z0, spec, cut=cut)
        CO.add_level(kit, rings, f"CORNICE-{tag}", "tower" if tag == "T" else "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="missionplinth")
    kit.add("FOUNDATION", "Adobe", fnd, group="foundation")
    ins_keep = []
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        b = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        name = f"{key}-{op.name}"
        reja = sp["top"] > 20.0 and op.kind != "door" and op.v0 < 20
        front = name == "DOOR-front-door"
        world, P, zones = O.place(sp, A, "Timber",
                                  "Door" if op.kind == "door" else "Timber", "Glass")
        chg = (round((O.PLUG + 0.8) / 0.2) * 0.2, "Iron") if reja else ((O.PLUG, "Clay") if front else None)
        if chg is not None:                          # render as it prints: the second colour from the change up
            k_ = M.cube([400.0, 400.0, 20.0]).translate([-200.0, -200.0, chg[0] - O.PLUG]).transform(A)
            zones = [(c_, m_ - k_) for c_, m_ in zones] + [(chg[1], world ^ k_)]
        part = kit.add(name, "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{op.v0 > 20}",
                       group="inserts", render=zones, change=chg)
        ins_keep.append(part.solid)
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the main roof: a low tile hip, notched for the parapet and cut round the tower
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, [], texture="pancover", tex_kw=dict(pitch=3.2, seam_pitch=2.8, d=0.45),
                       inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.4)
    roof = rf["body"] + rf["tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    ends = [(D / 2, YC), (W - D / 2, YC)]
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    cend = [ends[0], ends[1], ends[1], ends[0]]
    roof = roof + G.ridge_cap(ends[0], ends[1], zr, S_MAIN, ZW, half=1.4, up=0.8)
    roof = roof + union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.4, up=0.8, drop=1.8) for c, e in zip(corners, cend)])
    roof = roof.trim_by_plane([0, 0, 1.0], Z_EAVE - FASCIA)
    roof = roof - lip_keep(base, 3.0, ZW) - slab(offset(TOWER.cs, 1.4), ZW - 1, ZTW + 80)
    roof = roof - box([PX0 - 0.2, -D_EAVE - 5.0, ZW - 5.0], [PX0 + PL + 0.2, 3.15, 400.0])
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW = 11.0
    cx, cy = 40.0, 78.0
    zroof = Z_EAVE + S_MAIN * min(cx - CW / 2 + D_EAVE, D + D_EAVE - cy - CW / 2)
    z0 = round((zroof - 3.0) / 0.2) * 0.2
    roof = roof + G.chimney_seat(solid_env, cx, cy, CW / 2, zr + 1.0)
    pocket = box([cx - CW / 2 - 0.4, cy - CW / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CW / 2 + 0.4, zr + 40])
    roof = roof - pocket
    kit.add("ROOF", "Terracotta", max(roof.decompose(), key=lambda m_: m_.volume()), group="roof")
    kit.add("CHIMNEY", "Adobe", CR2.chimney_mission(CW, CW, round((zr + 9.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0]), group="roof")
    # the parapet's tile coping: a band on its shaped top, printed flat
    cap_cs = (par.offset(1.1) - par) ^ rect(-5.0, 1.0, PL + 5.0, PH + 5.0)
    f0 = MAIN.facades()[0]
    A = f0.A.copy()
    A[:, 3] = f0.world(PX0, ZW - ZF, 0.0)
    cap = M.extrude(cap_cs, 4.4).translate([0, 0, -3.7]).transform(A)
    ends_ = cs_union([circle((x, y), 0.55, 12) for (x, y) in np.array(par.offset(1.1).to_polygons()[0])[::3] if y > 2.0])
    cap = cap + M.extrude(ends_ ^ cap_cs.offset(0.3), 0.5).translate([0, 0, 0.7]).transform(A)
    kit.add("PARAPET-cap", "Terracotta", cap - roof,
            P=np.linalg.inv(np.vstack([A, [0, 0, 0, 1]]))[:3], group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the tower: a low tiled pyramid, a ball finial, the bell on its bar in the front arch
    d_t = TOWER_C["layers"][-1]["P"] + 0.4
    tsol, ttex = R.hip_roof([(TOWER.pts, [0, 1, 2, 3])], ZTW, 0.55, d_t, texture="pancover",
                            tex_kw=dict(pitch=3.0, seam_pitch=2.6, d=0.42), zlo=ZTW)
    half = (TX1 - TX0) / 2 + d_t
    zs = round((ZTW + 0.55 * (half - 1.4)) / 0.2) * 0.2
    kit.add("TOWER-roof", "Terracotta", (tsol + ttex).trim_by_plane([0, 0, -1.0], -zs), group="tower")
    fin = CR2.PW._revolve([(0.0, 0.0), (1.6, 0.0), (1.6, 0.8), (0.9, 1.4), (0.8, 2.4), (1.4, 3.4), (1.5, 4.4), (1.1, 5.4),
                           (0.5, 5.8), (0.35, 8.4), (0.0, 9.4)], 32)
    kit.add("TOWER-finial", "Iron", fin.translate([TXC, TYC, zs]), group="tower")
    bell = CR2.bell_hung(13.8).translate([TXC, TY0 + 1.6 + 0.8 - 0.05, BAR_TOP])
    kit.add("BELL", "Iron", bell, P=print_flip(), group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- the arcade porch across the front, from the west corner to the tower
    XW, XE, PD = 0.0, TX0, -TY0
    ppts = [(XW, 0.0), (XW, -PD), (XE, -PD), (XE, 0.0)]
    runs = [dict(a=(XW, 0.0), b=(XW, -PD), posts=[3.0, PD - 1.6]),
            dict(a=(XW, -PD), b=(XE, -PD), posts=[1.6, 23.6, 45.6, 68.4, 90.4, XE - XW - 2.0])]
    H_floor = ZF - 1.4
    S_P, o = 0.3, 2.4
    zs_p = S1 - 0.6 - S_P * (PD + o)
    PP = FT.porch_turned(ppts, runs, H_floor, zs_p + 0.8 - 5.2 - H_floor, steps_at=[(1, PXC - XW, 16.0)], over=o, inset=1.6,
                         rail_h=7.6, planks=dict(pitch=1.8, border=1.2), post="capistrano", rail="quatrefoils",
                         arcade="missionarch", skirt="archvent", pier_tex="missionplinth", roof_edge="tileends", top=True,
                         drop=11.0)
    fkeep = slab(offset(allcs, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    deck = PP["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch", render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([p.solid for p in kit.parts if p.name in ("WALLS-1", "JOINT", "WALLS-2") or p.name.startswith("CORNICE")])
    keep = bld_keep + union(ins_keep) + fnd
    res = FT.add_porch_top(kit, "PORCH", PP, keep, "Adobe", "Adobe", tin="custom", group="porch")
    zs2 = res["ptop"] - 0.8
    outer = [(XW - o, -PD - o), (XE - 0.2, -PD - o), (XE - 0.2, 3.0), (XW - o, 3.0)]
    sk, sk_tex = R.hip_roof([(outer, [0, 3])], zs2, S_P, 0.0, texture="pancover", tex_kw=dict(pitch=3.0, seam_pitch=2.6, d=0.42), zlo=zs2)
    shed = ((sk + sk_tex) ^ slab(cs_union([rect(XW - o, -PD - o, XE - 0.2, 3.0)]), zs2, zs2 + 12.0)) - bld_keep - union(ins_keep)
    kit.add("PORCH-roof", "Terracotta", max(shed.decompose(), key=lambda m_: m_.volume()), group="porch")
    for k, (sm, A_) in enumerate(PP["steps"]):
        kit.add(f"PORCH-steps-{k}", "Clay", sm.transform(A_) - fkeep - deck, group="porch")
    e, u = MAIN.locate(104.0, D)
    fb = MAIN.facades()[e]
    A_ = fb.A.copy()
    A_[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Clay", FT.steps(14.0, ZF - 0.6, 3).transform(A_) - fnd, group="porch")
    FT.crown(kit, "TOWER-finial", "TOWER-roof")
    FT.key_into(kit, "PORCH-steps-0", ["PORCH-deck"], (0, 1, 0), depth=0.8, conform=True)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "capistrano")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "capistrano.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
