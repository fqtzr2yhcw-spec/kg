"""The Hawthorn -- an original HO-scale (1:87.1) Eastlake house with a square tower, the smaller
tower house of the batch, combining the photos' towers with a compact plan. Rev B: the
house-size plan (190 x 136 mm, storeys of 42 and 38 mm), framed windows spaced along the walls,
and built-up cornices at every level.

Oxblood cove-and-bead siding with incised Eastlake corner boards on a base of stacked ledge
stones; a mustard belt carrying a raised zigzag; a hipped roof of spade-cut slates with a
front gable over the west bay, its gable in the same slates under a star gable ornament (a
collar, a king post through a disc pierced with an eight-pointed star, a drop and a spike).
A square tower stands forward on the east, rising a storey above the eaves with paired
windows, a cornice on comma brackets and a steep pyramid roof with a pineapple finial; an
octagonal chimney with a corbelled crown. A porch across the front on tapered square posts
with paddle balusters, a Tudor-arched frieze, a sawtooth fascia and a skirt of chevron
boards on ledge-stone piers. Windows with a fan of bars in the upper sash under incised
sunflower head boards; doors with a shoulder-headed light over two panels and a bow-tie
transom. Between the storeys a three-part cornice (a mustard zigzag frieze, a forest-green
billet course and a mustard stepped crown); at the eave a four-part one (a mustard frieze
incised with sunflowers, a green reeded course, a mustard soffit on Eastlake ladder brackets
and a green torus crown); round the tower's top a green chevron frieze, a mustard soffit on
ladder brackets and a mustard cyma crown.

usage: python3 -m hoarch.buildings.hawthorn [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import box, compose, cs_union, inv34, offset, poly, rect, scallop_rows, slab, union
from hoarch import cornice as CO, features as FT, gables as G, openings as O, roof as R, skins as SK, storefront as SF, \
    trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Hawthorn"
COLORS = {"Oxblood": "#7E2F2A", "Mustard": "#C9A43E", "Forest": "#2F4A3A", "Slate": "#4A4E55", "Ledge": "#9A8F80",
          "Brick": "#8A3B2B", "PorchDeck": "#9A8F80", "Windows_Doors": "#C9A43E"}
RENDER_MAT = {"Oxblood": "siding", "Mustard": "trim", "Forest": "forest", "Slate": "roof", "Ledge": "stone",
              "Brick": "brick", "PorchDeck": "stone", "Planks": "planks", "Windows_Doors": "trim", "Sash": "sash",
              "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Hawthorn)
LEDGE = 1.4
JOINT = dict(pitch=11.0, margin=3.6, layers=[
    dict(kind="frieze", h=4.2, b=1.2, orn="zigzag", role="Mustard"),
    dict(kind="course", h=1.6, b=1.4, orn="billet", role="Forest"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="stepped", role="Mustard")])
EAVE = dict(pitch=11.0, margin=3.6, layers=[
    dict(kind="frieze", h=5.6, b=1.2, orn="sunflower", role="Mustard"),
    dict(kind="course", h=1.6, b=1.4, orn="reeds", role="Forest"),
    dict(kind="bed", h=2.0, b=1.4, P=6.0, role="Mustard", brackets=dict(style="ladder", t=0.9, reach=0.6)),
    dict(kind="crown", h=2.6, b=1.4, P=6.8, orn="torus", role="Forest")])
TOWER_C = dict(pitch=8.0, margin=3.0, layers=[
    dict(kind="frieze", h=4.0, b=1.2, orn="chevron", role="Forest"),
    dict(kind="bed", h=1.8, b=1.4, P=5.0, role="Mustard", brackets=dict(style="ladder", t=0.8, reach=0.7)),
    dict(kind="crown", h=2.2, b=1.4, P=5.8, orn="cyma", role="Mustard")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 12.0
S1 = ZF + 42.0                  # first-storey shell top = the joint ring's foot
ZE = S1 + RJ + 38.0             # the eave ledge's top
ZW = ZE + HE                    # the wall top behind the eave cornice; the roof sits here
ZT = ZW + 40.0                  # the tower's ledge (its cornice clears the main roof)
ZTW = ZT + CO.band_height(TOWER_C)
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 7.2, 4.0, 1.8
S_MAIN, S_GABLE = 0.9, 1.25
V1 = 8.0
V2 = S1 + RJ + 5.0 - ZF

# ------------------------------------------------------------------ plan
W, D = 190.0, 136.0
FG = (8.0, 80.0)                          # the front gable's span on the front wall
TX0, TX1, TY0, TY1 = 144.0, 190.0, -20.0, 24.0
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
TOWER = Block("tower", [(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)], ZF, ZTW)
BLOCKS = [MAIN, TOWER]
DOOR_X = 118.0


def _siding(f, b, reg):
    """Cove-and-bead siding on the walls, spade-cut slates in the gable field; nothing behind
    the cornices."""
    cut = ZE - b.z0 if b is MAIN else ZT - b.z0
    top = ZW - b.z0 if b is MAIN else 999
    out = []
    lo = reg ^ rect(-1, -100, f.L + 1, cut)
    hi = reg ^ rect(-1, top, f.L + 1, 999)
    if not lo.is_empty():
        out.append(SK.cove_bead_lap(lo, datum=0.0))
    if not hi.is_empty():
        out.append(scallop_rows(hi, 1.6, 2.2, d=0.42, datum=top + 0.4, shape="spade", lap=2.0))
    return union(out) if out else M()


def _openings():
    L = []

    def win(w, h, rise=0, head="incised"):
        return SF.window_commercial(w, h, rise=rise, lites=(1, 1), rows=(1, 1), sill=1.2, head=head, upper="fan",
                                    casing=1.3, band=True)

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    door = lambda w, h: SF.door_commercial(w, h, transom=4.2, leaf="shouldered", tstyle="bowtie", head=None, leaves=1)
    add(MAIN, DOOR_X, 0.0, 0.0, door(12.0, 30.0), "door", "door")
    gm = (FG[0] + FG[1]) / 2
    for x in (gm - 15.0, gm + 15.0):
        add(MAIN, x, 0.0, V1, win(8.4, 24.0), f"F{x:.0f}-1")
        add(MAIN, x, 0.0, V2, win(8.4, 21.0), f"F{x:.0f}-2")
    add(MAIN, gm, 0.0, ZW - ZF + 4.0, win(8.0, 15.0, head=None), "front-gable")
    add(MAIN, DOOR_X, 0.0, V2, win(8.4, 21.0), f"F{DOOR_X:.0f}-2")
    add(MAIN, 92.0, 0.0, V1, win(8.4, 24.0), "F92-1")
    tm = (TX0 + TX1) / 2
    add(TOWER, tm, TY0, V1, win(8.4, 24.0), "T-front-1")
    add(TOWER, tm, TY0, V2, win(8.4, 21.0), "T-front-2")
    add(TOWER, TX1, (TY0 + 2.0) / 2, V1, win(7.2, 22.0), "T-east-1")
    add(TOWER, TX1, (TY0 + 2.0) / 2, V2, win(7.2, 20.0), "T-east-2")
    tw = win(7.2, 16.0, head=None)
    for (x, y) in ((tm, TY0), (TX1, (TY0 + TY1) / 2)):             # the faces clear of the main roof
        add(TOWER, x, y, ZT - ZF - 24.0, tw, f"T{x:.0f}-{y:.0f}-3")
    for y in (52.0, 88.0, 120.0):
        add(MAIN, W, y, V1, win(8.4, 24.0), f"E{y:.0f}-1")
        add(MAIN, W, y, V2, win(8.4, 21.0), f"E{y:.0f}-2")
    for y in (30.0, 68.0, 106.0):
        add(MAIN, 0.0, y, V1, win(8.4, 24.0), f"W{y:.0f}-1")
        add(MAIN, 0.0, y, V2, win(8.4, 21.0), f"W{y:.0f}-2")
    add(MAIN, 150.0, D, 0.0, door(10.0, 28.0), "back-door", "door")
    for x in (26.0, 64.0, 102.0):
        add(MAIN, x, D, V1, win(8.4, 24.0), f"B{x:.0f}-1")
    for x in (26.0, 64.0, 102.0, 150.0):
        add(MAIN, x, D, V2, win(8.4, 21.0), f"B{x:.0f}-2")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    r = RAKE - D_EAVE
    zcf = Z_EAVE + S_GABLE * ((FG[1] - FG[0]) / 2 + D_EAVE)
    gy = (zcf - Z_EAVE) / S_MAIN - D_EAVE + 4.0
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN),
              ([(FG[0], -r), (FG[1], -r), (FG[1], gy), (FG[0], gy)], [1, 3], S_GABLE)]
    specs = [dict(p0=(FG[0], 0.0), p1=(FG[1], 0.0), slope=S_GABLE, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture="spade", tex_kw=dict(pitch=1.5, wtab=2.2, d=0.42),
                       skin=SKIN, rake=RAKE, inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA, hollow=2.6)
    wf = rf["walls"][0]
    gables = [(MAIN, 0, wf["cs"].translate((FG[0], Z_EAVE - ZF)))]
    tower_keep = TOWER.solid(grow=0.2, dz0=-1, dz1=1)
    undress = [slab(offset(MAIN.cs, 8.0) - offset(TOWER.cs, 1.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="incised", siding=_siding, gables=gables,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    kit.add("WALLS-1", "Oxblood", st["shells"][0], group="walls")
    kit.add("JOINT", "Oxblood", st["rings"][0], group="walls")
    no_lip = union([box([FG[0] - D_EAVE - 0.6, -1, ZW - 1], [FG[1] + D_EAVE + 0.6, 5.0, ZW + 5]),
                    tower_keep, slab(offset(TOWER.cs, 1.0), ZW - 1, ZW + 5)])
    lip = (_corbel(MAIN.cs, 3.0, ZW) + lip_ring(MAIN.cs, 3.0, ZW)) - no_lip
    allcs = cs_union([b.cs for b in BLOCKS])
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(allcs, 3.0, S1 + RJ)
    ledges = (CO.ledge(MAIN.pts, ZE, LEDGE) - tower_keep) + CO.ledge(TOWER.pts, ZT, LEDGE)
    kit.add("WALLS-2", "Oxblood", st["shells"][1] + lip + tring + ledges, group="walls")
    for tag, path, z0, spec, cut in (("J", st["outlines"][0], S1 + LEDGE + 0.4, JOINT, None),
                                     ("E", MAIN.pts, ZE, EAVE, TOWER.solid(grow=1.1, dz0=-2, dz1=2)),
                                     ("T", TOWER.pts, ZT, TOWER_C, None)):
        rings, _ = CO.level(path, z0, spec, cut=cut)
        CO.add_level(kit, rings, f"CORNICE-{tag}", "tower" if tag == "T" else "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="ledgestone")
    kit.add("FOUNDATION", "Ledge", fnd, group="foundation")
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

    # --- the main roof: a hollow hip with the front gable, cut round the tower
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (min(W, D) / 2 + D_EAVE)
    ends = [(D / 2, D / 2), (W - D / 2, D / 2)] if W >= D else [(W / 2, W / 2), (W / 2, D - W / 2)]
    caps = [G.ridge_cap(ends[0], ends[1], zr, S_MAIN, ZW)]
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
                       for wl in rf["walls"]])
    fx = (FG[0] + FG[1]) / 2
    caps.append(G.ridge_cap((fx, -RAKE), (fx, (zcf - Z_EAVE) / S_MAIN - D_EAVE + 1.0), zcf, S_GABLE, ZW))
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    cend = [ends[0], ends[1], ends[1], ends[0]]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.6, up=0.9, drop=2.2) for c, e in zip(corners, cend)])
    roof = roof + ((union(caps) + hips) - walls_env)
    roof = roof - lip_keep(MAIN.cs, 3.0, ZW)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW = 11.0
    cx, cy = 52.0, 100.0
    zroof = Z_EAVE + S_MAIN * min(cx - CW / 2 + D_EAVE, D + D_EAVE - cy - CW / 2)
    z0 = round((zroof - 3.0) / 0.2) * 0.2
    roof = roof + G.chimney_seat(solid_env, cx, cy, CW / 2, zr + 1.0)
    pocket = box([cx - CW / 2 - 0.4, cy - CW / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CW / 2 + 0.4, zr + 40])
    roof = roof - pocket - slab(offset(TOWER.cs, 1.4), ZW - 1, ZTW + 80)
    kit.add("ROOF", "Slate", roof, group="roof")
    ch = TW.chimney("octagon", w=CW, d=CW, h=round((zr + 16.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0])
    kit.add("CHIMNEY", "Brick", ch, group="roof")
    orn = G.gable_star(wf["L"], wf["slope"], D_EAVE, skin=SKIN)
    f = wf["facade"]
    A = f.A.copy()
    A[:, 3] = f.world(0.0, 0.0, RAKE)
    ow = orn.transform(A) - (roof + ch)                       # the gable's feet stop on the main roof
    kit.add("GABLE", "Mustard", max(ow.decompose(), key=lambda m_: m_.volume()), P=inv34(A), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the tower: a steep pyramid roof on its cornice, a pineapple finial
    zc0 = ZTW
    d_t = TOWER_C["layers"][-1]["P"] + 0.4
    tsol, ttex = R.hip_roof([(TOWER.pts, [0, 1, 2, 3])], zc0, 2.2, d_t, texture="spade",
                            tex_kw=dict(pitch=1.5, wtab=2.2, d=0.42), zlo=zc0)
    half = (TX1 - TX0) / 2 + d_t
    zs = round((zc0 + 2.2 * (half - 1.6)) / 0.2) * 0.2
    kit.add("TOWER-roof", "Slate", (tsol + ttex).trim_by_plane([0, 0, -1.0], -zs), group="tower")
    kit.add("TOWER-finial", "Mustard", TW.finial("pineapple", 2.0, 15.0).translate([(TX0 + TX1) / 2, (TY0 + TY1) / 2, zs]),
            group="tower")
    print("tower", round(time.time() - t0, 1))

    # --- the porch across the front, from the west corner to the tower
    XW, XE, FY = 0.0, TX0, -28.0
    ppts = [(XW, 0.0), (XW, FY), (XE, FY), (XE, 0.0)]
    Lf = XE - XW
    ud = DOOR_X - XW
    runs = [dict(a=(XW, 0.0), b=(XW, FY), posts=[3.0, -FY - 1.6]),
            dict(a=(XW, FY), b=(XE, FY), posts=[1.6, 32.0, 64.0, 96.0, ud - 12.0, Lf - 2.6])]
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    PP = FT.porch_turned(ppts, runs, H_floor, post_h, steps_at=[(1, ud, 18.0)],
                         planks=dict(pitch=1.7, border=1.8), joined=True, ledger_off=1.5, post="tapered",
                         rail="paddle", arcade="tudor", skirt="chevron", pier_tex="ledgestone", roof_edge="sawtooth",
                         top=True, flat_arcades=True)
    fkeep = slab(offset(allcs, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    deck = PP["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([b.solid(grow=1.8, dz0=-20, dz1=0) for b in BLOCKS])
    FT.add_porch_top(kit, "PORCH", PP, bld_keep + ins_keep + fnd,
                     "Mustard", "Mustard", tin_col="Slate", arcade_col="Forest")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PORCH-steps-{k}", "Ledge", sm.transform(A) - fkeep - deck, group="porch")
    e, u = MAIN.locate(150.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Ledge", FT.steps(14.0, ZF - 0.6, 5).transform(A) - fnd, group="porch")
    # glue joints: nothing small is left butted on a dab of glue (see NOTES.md)
    FT.crown(kit, "TOWER-finial", "TOWER-roof")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "hawthorn")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "hawthorn.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
