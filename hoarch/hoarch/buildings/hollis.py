"""The Hollis -- an original HO-scale (1:87.1) Folk Victorian farmhouse for the lineup.

An L-plan gable-front-and-wing farmhouse: Dutch lap siding with chevron boarding in the
gables, and in every gable peak gingerbread (a rafter board edged with sawn drops, a spindle
screen hung from a king post with a turned drop). A spindlework porch (spindle posts and
railings, a spindle frieze with fan brackets, a horizontal-slat skirt) fills the corner of
the L. Pedimented window crowns with fans and dentils over two-over-two sash, board-and-
batten shutters, a half-glass door under a diamond-paned transom, a rock-faced block
foundation, a beaded belt, a roof of small red pressed-metal shingles and two plain brick
chimneys.

usage: python3 -m hoarch.buildings.hollis [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import box, compose, cs_union, inv34, offset, rect, slab, union
from hoarch import features as FT, gables as G, openings as O, roof as R, skins as SK, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Hollis Folk Victorian Farmhouse"
COLORS = {"PorchDeck": "#F2F0EB", "Planks": "#6F5034",       # the planked porch deck: two colours, one change
          "Robin": "#A9BAC2", "White": "#F2F0EB", "TinRed": "#7B3A2C", "Fieldstone": "#8D877C", "Brick": "#8A3B2B",
          "Forest": "#2F4A3A", "PorchGray": "#6B706F", "Windows_Doors": "#F2F0EB"}
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks",
              "Robin": "siding", "White": "trim", "TinRed": "roof", "Fieldstone": "stone", "Brick": "brick",
              "Forest": "accent", "PorchGray": "porchfloor", "Windows_Doors": "trim", "Sash": "sash", "Door": "door",
              "Glass": "glass"}

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 8.0
S1 = ZF + 34.0
RH = 4.4
ZE = S1 + RH + 30.0
FASCIA = 1.6
Z_EAVE = ZE + FASCIA
D_EAVE, RAKE, SKIN = 3.0, 3.2, 1.8
SLOPE = 1.2
V1 = 6.0
V2 = S1 + RH + 3.0 - ZF

# ------------------------------------------------------------------ plan: gable front and wing
MW, MD_ = 40.0, 70.0
WY0, WX1 = 30.0, 90.0
MAIN = Block("main", [(0, 0), (MW, 0), (MW, MD_), (0, MD_)], ZF, ZE)
WING = Block("wing", [(MW - 3.0, WY0), (WX1, WY0), (WX1, MD_), (MW - 3.0, MD_)], ZF, ZE)
BLOCKS = [MAIN, WING]
GABLE_EDGES = {("main", 0), ("main", 2), ("wing", 1)}


def _edge_of(b, f):
    for i, g in enumerate(b.facades()):
        if np.allclose(g.p0, f.p0) and np.allclose(g.p1, f.p1):
            return i
    return -1


def _siding(f, b, reg):
    """Dutch lap siding, and chevron boarding in the gables above a flat band at the eave line."""
    H = b.z1 - b.z0
    lo = reg ^ rect(-1, -1, f.L + 1, H)
    out = SK.dutch_lap(lo, datum=1.8)
    if (b.name, _edge_of(b, f)) in GABLE_EDGES:
        band = reg ^ rect(-1, H, f.L + 1, H + 1.2)
        hi = reg ^ rect(-1, H + 1.2, f.L + 1, H + 200)
        out = out + M.extrude(band, 0.6) + SK.diagonal_boards(hi, centre=f.L / 2)
    return out


def _specs():
    return [dict(p0=(0.0, 0.0), p1=(MW, 0.0), slope=SLOPE, blk=MAIN, edge=0, u0=0.0),
            dict(p0=(MW, MD_), p1=(0.0, MD_), slope=SLOPE, blk=MAIN, edge=2, u0=0.0),
            dict(p0=(WX1, WY0), p1=(WX1, MD_), slope=SLOPE, blk=WING, edge=1, u0=0.0)]


def _pieces():
    r = RAKE - D_EAVE
    return [([(0.0, -r), (MW, -r), (MW, MD_ + r), (0.0, MD_ + r)], [1, 3], SLOPE),
            ([(MW / 2 + D_EAVE, WY0), (WX1 + r, WY0), (WX1 + r, MD_), (MW / 2 + D_EAVE, MD_)], [0, 2], SLOPE)]


def _openings():
    L = []
    door = O.door_folk(10.0, 24.0)
    back_door = O.door_folk(9.0, 23.0, head="cap")
    lo = O.window_folk(8.0, 19.0, lites=(2, 2))                  # two-over-two
    up = O.window_folk(7.6, 18.0, head="cap", lites=(2, 2))

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    for x in (11.0, 29.0):
        add(MAIN, x, 0.0, V1, lo, f"front-1-{int(x)}")
        add(MAIN, x, 0.0, V2, up, f"front-2-{int(x)}")
    for y in (14.0, 38.0, 58.0):
        add(MAIN, 0.0, y, V1, lo, f"west-1-{int(y)}")
        add(MAIN, 0.0, y, V2, up, f"west-2-{int(y)}")
    add(MAIN, MW, 16.0, V2, up, "east-2")
    add(WING, 52.0, WY0, 0.4, door, "front-door", "door")
    add(WING, 74.0, WY0, V1, lo, "wing-front-1")
    for x in (54.0, 76.0):
        add(WING, x, WY0, V2, up, f"wing-front-2-{int(x)}")
    for y in (40.0, 60.0):
        add(WING, WX1, y, V1, lo, f"wing-east-1-{int(y)}")
    add(WING, WX1, (WY0 + MD_) / 2, V2, up, "wing-east-2")
    add(MAIN, 14.0, MD_, V1, lo, "back-1-14")
    add(MAIN, 20.0, MD_, V2, up, "back-2-20")
    add(WING, 64.0, MD_, 0.4, back_door, "back-door", "door")
    add(WING, 80.0, MD_, V1, lo, "back-1-80")
    add(WING, 72.0, MD_, V2, up, "back-2-72")
    return L


OPENINGS = _openings()


def _shuttered():
    """Windows with room for a pair of shutters: clear of the corners, of the other openings'
    trim and of their neighbours' shutters (checked facade by facade)."""
    out = set()
    by = {}
    for o in OPENINGS:
        by.setdefault((o.block.name, o.edge), []).append(o)
    for (bn, e), ops in by.items():
        f = ops[0].block.facades()[e]
        spans = []
        for o in ops:
            lb = o.cs_on_facade(o.spec["landing"]).bounds()
            spans.append((lb[0], lb[2], lb[1], lb[3]))
        taken = []
        for o in sorted(ops, key=lambda o: o.u):
            if o.kind == "door":
                continue
            b = o.spec["cut"].bounds()
            hw = (b[2] - b[0]) / 2
            a, c = o.u - 2 * hw - 2.5, o.u + 2 * hw + 2.5
            v0, v1 = o.v0, o.v0 + (b[3] - b[1])
            if a < 3.2 or c > f.L - 3.2:
                continue
            clash = any(s0 < c and s1 > a and t0 < v1 and t1 > v0 and not (abs((s0 + s1) / 2 - o.u) < 0.5)
                        for s0, s1, t0, t1 in spans + taken)
            if not clash:
                out.add(o.name)
                taken.append((a, c, v0, v1))
    return out


SHUTTERED = _shuttered()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    specs = _specs()
    base = cs_union([MAIN.cs, WING.cs])
    rf = G.gabled_roof(_pieces(), Z_EAVE, D_EAVE, specs, texture="square", tex_kw=dict(pitch=1.2, wtab=1.5, d=0.3),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA)
    gables = [(g["blk"], g["edge"], wl["cs"].translate((g["u0"], Z_EAVE - ZF))) for g, wl in zip(specs, rf["walls"])]
    bprof, bblocks = TW.BELTS["bead"]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="capital", siding=_siding, gables=gables, prof=bprof,
                        belt_blocks=bblocks)
    kit.add("WALLS-1", "Robin", st["shells"][0], group="walls")
    kit.add("BELT", "White", st["rings"][0], group="walls")
    no_lip = union([box([-1, -1, ZE - 1], [MW + 1, 5.0, ZE + 5]), box([-1, MD_ - 5.0, ZE - 1], [MW + 1, MD_ + 1, ZE + 5]),
                    box([WX1 - 5.0, WY0 - 1, ZE - 1], [WX1 + 1, MD_ + 1, ZE + 5])])
    lip = (_corbel(base, 3.0, ZE) + lip_ring(base, 3.0, ZE)) - no_lip
    kit.add("WALLS-2", "Robin", st["shells"][1] + lip, group="walls")
    kit.add("FOUNDATION", "Fieldstone", foundation(BLOCKS, 0.0, ZF, style="block"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "White", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{tag}",
                               group="inserts", render=zones))
        if o.name in SHUTTERED:
            w_op, h_op = b[2] - b[0], b[3] - b[1]
            left, right = FT.shutters_for(w_op, h_op, casing=1.8, gap=0.6, h=h_op, style="board")
            for side, m in (("L", left), ("R", right)):            # standing clear of the Dutch lap butts (0.46)
                kit.add(f"SHUTTER-{o.name}-{side}", "Forest", m.translate([0, 0, 0.48]).transform(A), P=inv34(A),
                        key=f"SHUTTER-{h_op:.1f}", group="shutters")
    print("walls + inserts", round(time.time() - t0, 1))

    # --- roof: hollow, with rake skins, ridge caps, a chimney; open trusses in the gables
    zr = Z_EAVE + SLOPE * (MW / 2 + D_EAVE)
    zw = Z_EAVE + SLOPE * ((MD_ - WY0) / 2 + D_EAVE)
    caps = union([G.ridge_cap((MW / 2, -RAKE), (MW / 2, MD_ + RAKE), zr, SLOPE, ZE),
                  G.ridge_cap((MW / 2, (WY0 + MD_) / 2), (WX1 + RAKE, (WY0 + MD_) / 2), zw, SLOPE, ZE)])
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), 4.0).translate([0, 0, -3.15]))
                       for wl in rf["walls"]])
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"] + (caps - walls_env)
    roof = roof - lip_keep(base, 3.0, ZE)
    CH = 8.0
    chims = [(MW / 2, 12.0), (72.0, (WY0 + MD_) / 2)]
    z_low = zr - SLOPE * (CH / 2) - 0.2
    z0 = round((z_low - 2.4) / 0.2) * 0.2
    solid_env, _ = R.hip_roof(_pieces(), Z_EAVE, SLOPE, D_EAVE, texture=None, zlo=ZE)
    for (x, y) in chims:
        roof = roof + G.chimney_seat(solid_env, x, y, CH / 2, zr + 1.0)
    pockets = union([box([x - CH / 2 - 0.4, y - CH / 2 - 0.4, z0], [x + CH / 2 + 0.4, y + CH / 2 + 0.4, zr + 40])
                     for x, y in chims])
    kit.add("ROOF", "TinRed", roof - pockets, group="roof")
    for k, (x, y) in enumerate(chims):
        ch = TW.chimney("plain", w=CH, d=CH, h=round((zr + 12.0 - z0) / 0.2) * 0.2).translate([x, y, z0])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof")
    for k, (g, wl) in enumerate(zip(specs, rf["walls"])):
        tr = G.gable_gingerbread(wl["L"], wl["slope"], D_EAVE, skin=SKIN)
        f = wl["facade"]
        A = f.A.copy()
        A[:, 3] = f.world(0.0, 0.0, RAKE)
        kit.add(f"GABLE-{k}", "White", tr.transform(A), P=inv34(A), key=f"GABLE-{wl['L']:.0f}", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- spindlework porch in the corner of the L
    PY0 = 14.0
    ppoly = [(MW, PY0), (WX1 - 2.0, PY0), (WX1 - 2.0, WY0), (MW, WY0)]
    Lf = WX1 - 2.0 - MW
    runs = [dict(a=(MW, PY0), b=(WX1 - 2.0, PY0), posts=[3.2, 18.0, 33.0, Lf - 1.6]),
            dict(a=(WX1 - 2.0, PY0), b=(WX1 - 2.0, WY0), posts=[1.6, WY0 - PY0 - 3.2])]
    H_floor = ZF - 1.0
    post_h = 42.0 - H_floor
    P = FT.porch_turned(ppoly, runs, H_floor, post_h, steps_at=[(0, 12.0, 10.0)],
                        planks=dict(pitch=2.4, border=0.0),
                        joined=True, ledger_off=1.5, arcade="spindle", post="spindle", rail="spindle", skirt="hslats",
                        pier_tex="block", roof_edge="button")
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    deck = P["deck"] - fkeep           # planks and frame in one part: wood planks, one filament change
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    tabs = union([arc for arc, _ in P["arcades"]])
    fnd = foundation(BLOCKS, 0.0, ZF, style="block")
    for k, fr in enumerate(sorted(P["frames"], key=lambda m: -m.volume())):
        kit.add(f"PORCH-frame-{k}", "White", fr - tabs - fnd, group="porch")
    for k, (arc, A) in enumerate(P["arcades"]):
        kit.add(f"PORCH-arcade-{k}", "White", arc, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = MAIN.solid(grow=2.0, dz0=-20, dz1=0) + WING.solid(grow=2.0, dz0=-20, dz1=0)
    shut_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                       for p in kit.parts if p.name.startswith("SHUTTER")])
    proof = P["roof"] - bld_keep - ins_keep - shut_keep
    ptop = proof.bounding_box()[5]
    kit.add("PORCH-roof", "White", proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8)), P=print_flip(), group="porch")
    kit.add("PORCH-roof-tin", "TinRed", proof.trim_by_plane([0, 0, 1.0], ptop - 0.8), group="porch")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Fieldstone", sm.transform(A) - fkeep, group="porch")
    e, u = WING.locate(64.0, MD_)
    f = WING.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Fieldstone", FT.steps(13.0, ZF - 0.6, 3).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "hollis")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "hollis.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
