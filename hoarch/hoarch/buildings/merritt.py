"""The Merritt -- an original HO-scale (1:87.1) Stick-style house for the lineup. Rev B: the
house-size plan (170 x 140 mm, storeys of 42 and 38 mm) and built-up cornices at every level.

Tall and steep: a front-gabled main block with a cross-gabled wing and an open truss in every
gable (collar tie, king post with a drop, struts and a fan of sticks). The clapboard walls are
framed by applied stickwork: corner and field verticals, bands under the sills and X-braced
dado panels, over a parged foundation, under a roof of staggered shakes with a ribbed chimney.
Windows have crossed-stick casings, pent hoods on knee braces over stick friezes and
four-over-one sash; the entrance has crossbuck doors under a stick transom; a braced porch
(square stick posts, X-braced railings, a slatted skirt on brick piers) runs across the front.

- Between the storeys a three-part cornice: an oxide-red frieze of stick frames with little
  knee braces in their corners, a cream block course and a cream cavetto crown.
- At the eave (along the eave walls and across the gable ends under the trusses): an
  oxide-red frieze of X-braced stick panels, a cream cable course, a cream soffit on diagonal
  knee braces and a cream bevel crown.

usage: python3 -m hoarch.buildings.merritt [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import box, clapboard, compose, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, gables as G, openings as O, roof as R, trimwork as TW
from hoarch.kit import Kit, print_flip
from hoarch.ornament import stroke
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Merritt Stick Style House"
COLORS = {"PorchDeck": "#EDE3C8", "Planks": "#6F5034",       # the planked porch deck: two colours, one change
          "Sage": "#8C9670", "Cream": "#EDE3C8", "Charcoal": "#3D3F42", "Fieldstone": "#8D877C",
          "Brick": "#8A3B2B", "PorchGray": "#6B706F", "Oxide": "#7A3B2A", "Windows_Doors": "#EDE3C8"}
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks",
              "Sage": "siding", "Cream": "trim", "Charcoal": "roof", "Fieldstone": "stone", "Brick": "brick",
              "PorchGray": "porchfloor", "Oxide": "accent", "Windows_Doors": "trim", "Sash": "sash", "Door": "door",
              "Glass": "glass"}
PALETTE = {"siding": ["#8C9670", 0.65, 0.0], "trim": ["#EDE3C8", 0.55, 0.0], "roof": ["#3D3F42", 0.8, 0.0],
           "stone": ["#8D877C", 0.9, 0.0], "brick": ["#8A3B2B", 0.85, 0.0], "porchfloor": ["#6B706F", 0.7, 0.0],
           "sash": ["#5A1A24", 0.45, 0.0], "door": ["#5A1A24", 0.45, 0.0], "accent": ["#7A3B2A", 0.6, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Merritt)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.8, b=1.2, orn="stickwork", role="Oxide"),
    dict(kind="course", h=1.6, b=1.4, orn="blocks", role="Cream"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="cavetto", role="Cream")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.6, b=1.2, orn="xbrace", role="Oxide"),
    dict(kind="course", h=1.6, b=1.4, orn="cable", role="Cream"),
    dict(kind="bed", h=2.0, b=1.4, P=6.4, role="Cream", brackets=dict(style="brace", t=0.9, reach=0.6)),
    dict(kind="crown", h=2.4, b=1.4, P=7.0, orn="bevel", role="Cream")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 14.0
S1 = ZF + 42.0
ZE = S1 + RJ + 38.0
ZW = ZE + HE                    # the wall top behind the eave cornice; the roof sits here
FASCIA = 2.0
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 7.4, 7.8, 1.8
SLOPE = 1.3
V1 = 8.0
V2 = S1 + RJ + 5.0 - ZF

# ------------------------------------------------------------------ plan
MW, MD_ = 100.0, 140.0
WY0, WY1, WX1 = 34.0, 100.0, 170.0
MAIN = Block("main", [(0, 0), (MW, 0), (MW, MD_), (0, MD_)], ZF, ZW)
WING = Block("wing", [(MW - 3.0, WY0), (WX1, WY0), (WX1, WY1), (MW - 3.0, WY1)], ZF, ZW)
BLOCKS = [MAIN, WING]


def _siding(f, b, reg):
    """Clapboard framed by applied stickwork: boards framing every window, bands at the
    floor lines and under the eave cornice, and X braces in the wall panels between windows.
    Nothing in the eave's cornice band; the verticals run on up into the gables."""
    L = f.L
    edge = _edge_of(b, f)
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, L + 1, ZW - b.z0)
    tex = clapboard(reg, pitch=1.2, d=0.3, dmin=0.05, datum=1.8)
    lands = [o.cs_on_facade(o.spec["landing"]).bounds() for o in OPENINGS if o.block is b and o.edge == edge]
    vs = sorted({0.6, L - 0.6} | {round(x, 2) for lb in lands for x in (lb[0] - 0.9, lb[2] + 0.9) if 1.0 < x < L - 1.0})
    storeys = [(2.0, S1 - ZF - 2.2), (S1 + RJ - ZF + 1.2, ZE - LEDGE - 1.6 - ZF)]
    sticks = [rect(u - 0.5, 1.8, u + 0.5, 400) for u in vs]
    for (lo, hi) in storeys:
        sticks.append(rect(-1, hi, L + 1, hi + 1.0))
        sticks.append(rect(-1, lo - 1.0, L + 1, lo))
        for a_, c_ in zip(vs[:-1], vs[1:]):
            if c_ - a_ < 6.0:
                continue
            busy = any(lb[0] < c_ and lb[2] > a_ and lb[1] < hi and lb[3] > lo for lb in lands)
            if busy:
                continue
            sticks += [stroke([(a_ + 0.5, lo), (c_ - 0.5, hi)], 0.8), stroke([(a_ + 0.5, hi), (c_ - 0.5, lo)], 0.8)]
    cs = (cs_union(sticks) ^ reg).offset(-0.3, JoinType.Miter, 4.0).offset(0.3, JoinType.Miter, 4.0)
    return tex + M.extrude(cs, 0.6)


def _edge_of(b, f):
    for i, g in enumerate(b.facades()):
        if np.allclose(g.p0, f.p0) and np.allclose(g.p1, f.p1):
            return i
    return -1


def _specs():
    return [dict(p0=(0.0, 0.0), p1=(MW, 0.0), slope=SLOPE, blk=MAIN, edge=0, u0=0.0),
            dict(p0=(MW, MD_), p1=(0.0, MD_), slope=SLOPE, blk=MAIN, edge=2, u0=0.0),
            dict(p0=(WX1, WY0), p1=(WX1, WY1), slope=SLOPE, blk=WING, edge=1, u0=0.0)]


def _pieces():
    r = RAKE - D_EAVE
    return [([(0.0, -r), (MW, -r), (MW, MD_ + r), (0.0, MD_ + r)], [1, 3], SLOPE),
            ([(MW / 2, WY0), (WX1 + r, WY0), (WX1 + r, WY1), (MW / 2, WY1)], [0, 2], SLOPE)]


def _openings():
    L = []
    front_door = O.door_stick(13.0, 30.0)
    back_door = O.door_stick(11.0, 27.0, leaves=1, transom=3.6)
    s41 = dict(lites=(1, 2), rows=(1, 2), qa=False)            # four-over-one sash
    lo = O.window_stick(9.6, 24.0, **s41)
    lo_wide = O.window_stick(11.4, 24.0, lites=(1, 3), rows=(1, 2), qa=False)     # six-over-one
    up = O.window_stick(9.6, 21.0, **s41)
    attic = O.window_stick(7.2, 14.0, apron=False, **s41)

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    va = ZW - ZF + 3.0
    add(MAIN, 30.0, 0.0, 0.4, front_door, "front-door", "door")
    add(MAIN, 72.0, 0.0, V1, lo_wide, "front-1")
    for x in (25.0, 75.0):
        add(MAIN, x, 0.0, V2, up, f"front-2-{int(x)}")
    for x in (MW / 2 - 11.0, MW / 2 + 11.0):
        add(MAIN, x, 0.0, va, attic, f"front-attic-{int(x)}")
    for y in (24.0, 70.0, 116.0):
        add(MAIN, 0.0, y, V1, lo, f"west-1-{int(y)}")
        add(MAIN, 0.0, y, V2, up, f"west-2-{int(y)}")
    for y in (15.0, 122.0):
        add(MAIN, MW, y, V1, lo, f"east-1-{int(y)}")
        add(MAIN, MW, y, V2, up, f"east-2-{int(y)}")
    add(MAIN, 75.0, MD_, 0.4, back_door, "back-door", "door")
    add(MAIN, 25.0, MD_, V1, lo, "back-1")
    for x in (25.0, 75.0):
        add(MAIN, x, MD_, V2, up, f"back-2-{int(x)}")
    add(MAIN, MW / 2, MD_, va, attic, "back-attic")
    xm = (MW + WX1) / 2 + 1.5
    add(WING, xm, WY0, V1, lo_wide, "wing-front-1")
    add(WING, xm, WY0, V2, up, "wing-front-2")
    add(WING, xm, WY1, V1, lo, "wing-back-1")
    add(WING, xm, WY1, V2, up, "wing-back-2")
    for y in (WY0 + 16.0, WY1 - 16.0):
        add(WING, WX1, y, V1, lo, f"wing-east-1-{int(y)}")
    add(WING, WX1, (WY0 + WY1) / 2, V2, up, "wing-east-2")
    add(WING, WX1, (WY0 + WY1) / 2, va, attic, "wing-attic")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    specs = _specs()
    base = cs_union([MAIN.cs, WING.cs])
    rf = G.gabled_roof(_pieces(), Z_EAVE, D_EAVE, specs, texture="stagger", tex_kw=dict(pitch=1.6, wtab=1.9, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA)
    gables = [(g["blk"], g["edge"], wl["cs"].translate((g["u0"], Z_EAVE - ZF))) for g, wl in zip(specs, rf["walls"])]
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="stepped", siding=_siding, gables=gables,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    kit.add("WALLS-1", "Sage", st["shells"][0], group="walls")
    kit.add("JOINT", "Sage", st["rings"][0], group="walls")
    no_lip = union([box([-1, -1, ZW - 1], [MW + 1, 5.0, ZW + 5]), box([-1, MD_ - 5.0, ZW - 1], [MW + 1, MD_ + 1, ZW + 5]),
                    box([WX1 - 5.0, WY0 - 1, ZW - 1], [WX1 + 1, WY1 + 1, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    eave_path = max(base.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    kit.add("WALLS-2", "Sage", st["shells"][1] + lip + CO.ledge(eave_path, ZE, LEDGE), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    kit.add("FOUNDATION", "Fieldstone", foundation(BLOCKS, 0.0, ZF, style="parged"), group="foundation")
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

    # --- roof: hollow, with rake skins, ridge caps, a chimney; open trusses in the gables
    zr = Z_EAVE + SLOPE * (MW / 2 + D_EAVE)
    zw = Z_EAVE + SLOPE * ((WY1 - WY0) / 2 + D_EAVE)
    x_meet = MW - ((zw - Z_EAVE) / SLOPE - D_EAVE) - 1.0
    caps = union([G.ridge_cap((MW / 2, -RAKE), (MW / 2, MD_ + RAKE), zr, SLOPE, ZW),
                  G.ridge_cap((x_meet, (WY0 + WY1) / 2), (WX1 + RAKE, (WY0 + WY1) / 2), zw, SLOPE, ZW)])
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), 4.0).translate([0, 0, -3.15]))
                       for wl in rf["walls"]])
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"] + (caps - walls_env)
    roof = roof.trim_by_plane([0, 0, 1.0], ZW) - lip_keep(base, 3.0, ZW)
    CH = 10.0
    chims = [(MW / 2, 96.0)]
    z_low = zr - SLOPE * (CH / 2) - 0.2
    z0 = round((z_low - 2.4) / 0.2) * 0.2
    solid_env, _ = R.hip_roof(_pieces(), Z_EAVE, SLOPE, D_EAVE, texture=None, zlo=ZW)
    for (x, y) in chims:
        roof = roof + G.chimney_seat(solid_env, x, y, CH / 2, zr + 1.0)
    g = CH / 2 + 0.8                         # clear of the chimney's pilaster ribs
    pockets = union([box([x - g, y - g, z0], [x + g, y + g, zr + 40]) for x, y in chims])
    kit.add("ROOF", "Charcoal", roof - pockets, group="roof")
    for k, (x, y) in enumerate(chims):
        ch = TW.chimney("ribbed", w=CH, d=CH, h=round((zr + 16.0 - z0) / 0.2) * 0.2).translate([x, y, z0])
        kit.add(f"CHIMNEY-{k}", "Brick", ch, key="CHIMNEY", group="roof")
    for k, (g, wl) in enumerate(zip(specs, rf["walls"])):
        tr = G.gable_truss(wl["L"], wl["slope"], D_EAVE, skin=SKIN, width=2.0)
        f = wl["facade"]
        A = f.A.copy()
        A[:, 3] = f.world(0.0, 0.0, RAKE)
        kit.add(f"TRUSS-{k}", "Cream", tr.transform(A), P=inv34(A), key=f"TRUSS-{wl['L']:.0f}", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- braced porch across the front
    PD = 24.0
    ppoly = [(0.0, -PD), (MW, -PD), (MW, 0.0), (0.0, 0.0)]
    runs = [dict(a=(0.0, 0.0), b=(0.0, -PD), posts=[3.2, PD - 1.6]),
            dict(a=(0.0, -PD), b=(MW, -PD), posts=[1.6, 20.0, 40.0, 60.0, 80.0, MW - 1.6]),
            dict(a=(MW, -PD), b=(MW, 0.0), posts=[1.6, PD - 3.2])]
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor              # the roof tucks under the joint's ledge
    P = FT.porch_turned(ppoly, runs, H_floor, post_h, steps_at=[(1, 30.0, 16.0)],
                        planks=dict(pitch=1.7, border=1.6, diagonal=True),
                        joined=True, ledger_off=1.5, arcade="braced", post="stick", rail="x", skirt="slats",
                        pier_tex="parged", roof_edge="sticks")
    fkeep = slab(offset(MAIN.cs, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    deck = P["deck"] - fkeep           # planks and frame in one part: wood planks, one filament change
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    tabs = union([arc for arc, _ in P["arcades"]])
    fnd = foundation(BLOCKS, 0.0, ZF, style="parged")
    for k, fr in enumerate(sorted(P["frames"], key=lambda m: -m.volume())):
        kit.add(f"PORCH-frame-{k}", "Cream", fr - tabs - fnd, group="porch")
    for k, (arc, A) in enumerate(P["arcades"]):
        kit.add(f"PORCH-arcade-{k}", "Cream", arc, P=compose(FT.ARCADE_PRINT, inv34(A)), group="porch")
    bld_keep = MAIN.solid(grow=1.45, dz0=-20, dz1=0)
    proof = P["roof"] - bld_keep - ins_keep
    ptop = proof.bounding_box()[5]
    kit.add("PORCH-roof", "Cream", proof.trim_by_plane([0, 0, -1.0], -(ptop - 0.8)), P=print_flip(), group="porch")
    kit.add("PORCH-roof-tin", "Charcoal", proof.trim_by_plane([0, 0, 1.0], ptop - 0.8), group="porch")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Fieldstone", sm.transform(A) - fkeep, group="porch")
    e, u = MAIN.locate(75.0, MD_)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Fieldstone", FT.steps(15.0, ZF - 0.6, 5).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "merritt")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "merritt.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
