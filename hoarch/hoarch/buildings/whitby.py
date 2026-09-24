"""The Whitby -- an original HO-scale (1:87.1) Carpenter Gothic cottage for the lineup.

A storey and a half in board-and-batten on a rubble-stone base with a drip-moulded belt,
under a steep patterned-slate roof with four gables: the side gables and a steeper cross
gable front and back, each hung with a pierced bargeboard with a king post, drop and spike
finial. Pointed windows with bar tracery: twin lancets under crocketed labels on carved
stops, crocketed gablets on the sides, diamond-paned lancets in the side gables. A
traceried Gothic entrance on engaged shafts, a Gothic porch (clustered shafts, pierced
quatrefoil railings, pointed arches with trefoils, a picket skirt on stone piers), and
chimneys of paired diagonal flues on stone bases.

usage: python3 -m hoarch.buildings.whitby [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import battens, box, compose, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import features as FT, gables as G, openings as O, roof as R, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Whitby Carpenter Gothic Cottage"
COLORS = {"Fawn": "#C4AE84", "Cream": "#EFE6D2", "Slate": "#4E585C", "Fieldstone": "#8D877C", "Brick": "#8A3B2B",
          "PorchGray": "#6B706F", "Windows_Doors": "#EFE6D2"}
RENDER_MAT = {"Fawn": "siding", "Cream": "trim", "Slate": "roof", "Fieldstone": "stone", "Brick": "brick",
              "PorchGray": "porchfloor", "Windows_Doors": "trim", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"siding": ["#C4AE84", 0.65, 0.0], "trim": ["#EFE6D2", 0.55, 0.0], "roof": ["#4E585C", 0.8, 0.0],
           "stone": ["#8D877C", 0.9, 0.0], "brick": ["#8A3B2B", 0.85, 0.0], "porchfloor": ["#6B706F", 0.7, 0.0],
           "sash": ["#3B2A20", 0.45, 0.0], "door": ["#5B2E1C", 0.45, 0.0]}

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 10.0
S1 = ZF + 36.0
RH = 4.4
ZE = S1 + RH + 12.0            # knee wall; the walls stop here and the roof sits on them
FASCIA = 1.6
Z_EAVE = ZE + FASCIA            # top edge of the eave
D_EAVE, RAKE, SKIN = 3.0, 3.2, 1.8
S_MAIN, S_CROSS = 1.2, 1.5      # 50 and 56 degree pitches

# ------------------------------------------------------------------ plan
W, D = 100.0, 60.0
GX0, GX1 = 28.0, 72.0           # the cross gables, front and back
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZE)
BLOCKS = [MAIN]
V1 = 6.0
V2 = S1 + RH + 3.0 - ZF         # second floor sills, from the block base


def _siding(f, b, reg):
    return battens(reg, pitch=3.2, bw=0.8, d=0.4, datum=0.0)


def _gable_cs():
    """Gable walls (edge index, cs in that facade's frame, v up from the block base), and the
    gabled_roof gable specs."""
    ext = 0.3                   # a cross gable keeps the main eave running up to its corners
    specs = [dict(p0=(0.0, D), p1=(0.0, 0.0), slope=S_MAIN, edge=3, u0=0.0),
             dict(p0=(W, 0.0), p1=(W, D), slope=S_MAIN, edge=1, u0=0.0),
             dict(p0=(GX0, 0.0), p1=(GX1, 0.0), slope=S_CROSS, edge=0, u0=GX0, e=ext),
             dict(p0=(GX1, D), p1=(GX0, D), slope=S_CROSS, edge=2, u0=W - GX1, e=ext)]
    return specs


def _roof_pieces():
    r = RAKE - D_EAVE
    main = ([(-r, 0.0), (W + r, 0.0), (W + r, D), (-r, D)], [0, 2], S_MAIN)
    front = ([(GX0, -r), (GX1, -r), (GX1, D / 2 - 2.0), (GX0, D / 2 - 2.0)], [1, 3], S_CROSS)
    back = ([(GX0, D / 2 + 2.0), (GX1, D / 2 + 2.0), (GX1, D + r), (GX0, D + r)], [1, 3], S_CROSS)
    return [main, front, back]


def _openings():
    L = []
    gable_win = O.window_gothic(10.0, 26.0, lights="twin", head="label")
    front_win = O.window_gothic(9.0, 23.0, lights="twin", head="label")
    side_win = O.window_gothic(8.4, 20.0, lights="twin", head="gablet")
    pair_win = O.window_gothic(7.0, 19.0, lights="diamond", head="label", crocket=False)
    attic = O.window_gothic(5.0, 11.0, lights="plain", head="label", crocket=False, finial=False, stops=False)
    back_win = O.window_gothic(9.0, 21.0, lights="cross", head="tudor", flat=True)
    front_door = O.door_gothic(11.6, 27.0)
    back_door = O.door_gothic(9.6, 25.0, leaves=1, shaft=1.2)

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    add(W / 2, 0.0, 0.4, front_door, "front-door", "door")
    for x in (20.0, W - 20.0):
        add(x, 0.0, V1, front_win, f"front-{int(x)}")
    add(W / 2, 0.0, V2 + 1.0, gable_win, "front-gable")
    add(W / 2, D, V2 + 1.0, gable_win, "back-gable")
    add(72.0, D, 0.4, back_door, "back-door", "door")
    for x in (20.0, 44.0):
        add(x, D, V1, back_win, f"back-{int(x)}")
    for x in (0.0, W):
        for y in (16.0, D - 16.0):
            add(x, y, V1, side_win, f"side-{int(x)}-{int(y)}")
        for y in (D / 2 - 7.5, D / 2 + 7.5):
            add(x, y, V2 + 1.0, pair_win, f"gable-{int(x)}-{int(y)}")
        add(x, D / 2, V2 + 24.0, attic, f"attic-{int(x)}")
    return L


OPENINGS = _openings()


def _ridge_caps():
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    zc = Z_EAVE + S_CROSS * ((GX1 - GX0) / 2 + D_EAVE)
    y_meet = (zc - Z_EAVE) / S_MAIN - D_EAVE + 1.0         # where a cross ridge dies into the main slope
    xm = (GX0 + GX1) / 2
    return union([G.ridge_cap((-RAKE, D / 2), (W + RAKE, D / 2), zr, S_MAIN, ZE),
                  G.ridge_cap((xm, -RAKE), (xm, y_meet), zc, S_CROSS, ZE),
                  G.ridge_cap((xm, D - y_meet), (xm, D + RAKE), zc, S_CROSS, ZE)])


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    specs = _gable_cs()
    rf = G.gabled_roof(_roof_pieces(), Z_EAVE, D_EAVE, specs, texture=["square", "square", "diamond", "diamond"],
                       skin=SKIN, rake=RAKE, inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA)
    gables = []
    for g, wl in zip(specs, rf["walls"]):
        cs = wl["cs"].translate((g["u0"], Z_EAVE - ZF))
        gables.append((MAIN, g["edge"], cs))
    bprof, bblocks = TW.BELTS["drip"]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="board", siding=_siding, gables=gables, prof=bprof,
                        belt_blocks=bblocks)
    kit.add("WALLS-1", "Fawn", st["shells"][0], group="walls")
    kit.add("BELT", "Cream", st["rings"][0], group="walls")
    # the roof's locating lip runs only along the eave walls (a gable wall carries on upward)
    no_lip = union([box([-1, -1, ZE - 1], [5.0, D + 1, ZE + 5]), box([W - 5.0, -1, ZE - 1], [W + 1, D + 1, ZE + 5]),
                    box([GX0 - 1.5, -1, ZE - 1], [GX1 + 1.5, 5.0, ZE + 5]),
                    box([GX0 - 1.5, D - 5.0, ZE - 1], [GX1 + 1.5, D + 1, ZE + 5])])
    lip = (_corbel(MAIN.cs, 3.0, ZE) + lip_ring(MAIN.cs, 3.0, ZE)) - no_lip
    kit.add("WALLS-2", "Fawn", st["shells"][1] + lip, group="walls")
    kit.add("FOUNDATION", "Fieldstone", foundation(BLOCKS, 0.0, ZF, style="rubble"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Cream", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{tag}",
                               group="inserts", render=zones))
    print("walls + inserts", round(time.time() - t0, 1))

    # --- roof: one hollow body with its rake skins, located by the lip on the walls
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), 3.3).translate([0, 0, -3.15]))
                       for wl in rf["walls"]])
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"] + (_ridge_caps() - walls_env)
    roof = roof - lip_keep(MAIN.cs, 3.0, ZE)
    chims = [(12.0, D / 2), (W - 12.0, D / 2)]
    CH = 8.0
    ridge = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    z_low = ridge - S_MAIN * (CH / 2) - 0.2              # the roof surface at the stack's lower edges
    z0 = round((z_low - 2.4) / 0.2) * 0.2
    solid_env, _ = R.hip_roof(_roof_pieces(), Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZE)
    for (x, y) in chims:
        roof = roof + G.chimney_seat(solid_env, x, y, CH / 2, ridge + 1.0)
    pockets = union([box([x - CH / 2 - 0.4, y - CH / 2 - 0.4, z0], [x + CH / 2 + 0.4, y + CH / 2 + 0.4, ridge + 40])
                     for x, y in chims])
    kit.add("ROOF", "Slate", roof - pockets, group="roof")
    for k, (x, y) in enumerate(chims):
        ch = TW.chimney("diagonal", w=CH, d=CH, h=ridge + 16.0 - z0).translate([x, y, z0])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof")
    # --- pierced bargeboards on every gable, hung on the rake skin's end
    for k, (g, wl) in enumerate(zip(specs, rf["walls"])):
        bb = G.bargeboard(wl["L"], wl["slope"], D_EAVE, skin=SKIN, width=2.6 if g["slope"] < 1.4 else 2.2)
        f = wl["facade"]
        A = f.A.copy()
        A[:, 3] = f.world(0.0, 0.0, RAKE)
        kit.add(f"BARGE-{k}", "Cream", bb.transform(A), P=inv34(A), key=f"BARGE-{wl['L']:.0f}", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- Gothic porch before the front door: pointed arches with trefoils, turned posts
    PX0, PX1, PD = 28.0, 72.0, 16.0
    ppoly = [(PX0, -PD), (PX1, -PD), (PX1, 0.0), (PX0, 0.0)]
    Lf = PX1 - PX0
    runs = [dict(a=(PX0, 0.0), b=(PX0, -PD), posts=[3.2, PD - 1.6]),
            dict(a=(PX0, -PD), b=(PX1, -PD), posts=[1.6, 14.0, Lf - 14.0, Lf - 1.6]),
            dict(a=(PX1, -PD), b=(PX1, 0.0), posts=[1.6, PD - 3.2])]
    H_floor = ZF - 1.0
    post_h = 44.0 - H_floor                    # the porch roof clears the door's finial
    P = FT.porch_turned(ppoly, runs, H_floor, post_h, steps_at=[(1, Lf / 2, 13.0)], boards=dict(pitch=1.8),
                        joined=True, ledger_off=1.5, arcade="gothic", post="clustered", rail="pierced", skirt="pickets",
                        pier_tex="rubble", roof_edge="drop")
    fkeep = slab(offset(MAIN.cs, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    kit.add("PORCH-deck", "Cream", P["deck"] - fkeep, P=print_flip(), group="porch")
    kit.add("PORCH-floor", "PorchGray", P["floor"] - fkeep, P=print_flip(), group="porch")
    tabs = union([arc for arc, _ in P["arcades"]])
    fnd = foundation(BLOCKS, 0.0, ZF, style="rubble")
    for k, fr in enumerate(sorted(P["frames"], key=lambda m: -m.volume())):
        kit.add(f"PORCH-frame-{k}", "Cream", fr - tabs - fnd, group="porch")
    for k, (arc, A) in enumerate(P["arcades"]):
        kit.add(f"PORCH-arcade-{k}", "Cream", arc, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = MAIN.solid(grow=1.45, dz0=-20, dz1=0)
    proof = P["roof"] - bld_keep - ins_keep
    ptop = proof.bounding_box()[5]
    kit.add("PORCH-roof", "Cream", proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8)), P=print_flip(), group="porch")
    kit.add("PORCH-roof-tin", "Slate", proof.trim_by_plane([0, 0, 1.0], ptop - 0.8), group="porch")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Fieldstone", sm.transform(A) - fkeep, group="porch")
    e, u = MAIN.locate(72.0, D)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Fieldstone", FT.steps(13.0, ZF - 0.6, 3).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "whitby")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "whitby.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
