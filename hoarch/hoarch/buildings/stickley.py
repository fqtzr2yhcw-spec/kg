"""The Stickley: an original HO-scale (1:87.1) two-storey Craftsman house with a sleeping
porch, house 59 of the fifth batch (the Craftsman era, 1900-1930).

A broad two-storey house under a low side-gabled roof of hexagonal slates with deep eaves on
twin rafter tails. The ground storey is wide beaded lap siding, the upper storey ragged shakes,
on board-formed concrete. Against the east gable stands a porch of two tiers: below, an entry
porch on round posts with bolster tops, splat railings and stepped beams; above it, carried on
its one-piece top, the sleeping porch, walled to rail height in shakes and open all round
between its posts under a low hip. At the front door a pergola of round posts, beams and cross
rafters, every end cut in a double step, over a stone terrace. The windows are casements with
small panes across their tops: downstairs under thick heads with keyed through-tenons,
upstairs under arch-cut heads on corbelled sills. Glasgow roses and keyed tenons between the
storeys, a trail of heart leaves at the eaves.

usage: python3 -m hoarch.buildings.stickley [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, poly, rect, slab, union
from hoarch import craftsman2 as CR2, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Stickley"
COLORS = {"Bark": "#5E4A36", "Forest": "#3E5240", "Linen": "#D9CBA8", "Copper": "#9C5B2E", "Slate": "#3F4447",
          "Fieldstone": "#8D8779", "Planks": "#6E5A44", "PorchDeck": "#6E5A44", "Windows_Doors": "#D9CBA8"}
RENDER_MAT = {"Bark": "siding", "Forest": "shingle", "Linen": "trim", "Copper": "accent", "Slate": "roof", "Fieldstone": "stone",
              "Planks": "planks", "PorchDeck": "planks", "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Stickley)
LEDGE = 1.4
JOINT = dict(pitch=15.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="glasgowrose", role="Copper"),
    dict(kind="course", h=1.6, b=1.4, orn="keyedtenons", role="Linen"),
    dict(kind="crown", h=2.2, b=1.4, P=3.8, orn="ovolo", role="Linen")])
EAVE = dict(pitch=14.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="heartleaf", role="Copper"),
    dict(kind="course", h=1.6, b=1.4, orn="keyedtenons", role="Linen"),
    dict(kind="bed", h=2.6, b=1.4, P=8.2, role="Linen", brackets=dict(style="twintails", t=1.2, reach=0.35)),
    dict(kind="crown", h=2.0, b=1.4, P=8.6, orn="stepped", role="Linen")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 9.0
S1 = ZF + 36.0
ZU = S1 + RJ
ZE = ZU + 30.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 9.0, 9.4, 1.8
S = 0.5
W, D = 130.0, 96.0
XC, YC = W / 2, D / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
PY0, PY1, PW_ = 18.0, 78.0, 36.0                 # the two-tier porch on the east gable
DOOR_X = 40.0
V1 = 7.0
V2 = ZU - ZF + 4.0


def _skin(f, b, reg):
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    lo = reg ^ rect(-1, -50, f.L + 1, S1 - b.z0)
    hi = reg - rect(-1, -50, f.L + 1, ZU - b.z0)
    out = CR2.lap_beaded(lo) if not lo.is_empty() else M()
    if not hi.is_empty():
        out = out + CR2.shakes_ragged(hi, datum=ZU - b.z0, seed=int(f.p0[0] + f.p0[1]) % 53)
    return out


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    g2 = CR2.window_stickley(20.0, 20.0, n=2)
    g3 = CR2.window_stickley(28.0, 20.0, n=3)
    u2 = CR2.window_stickley(20.0, 17.0, n=2, upper=True)
    u3 = CR2.window_stickley(28.0, 17.0, n=3, upper=True)
    att = CR2.window_stickley(14.0, 10.0, n=2, upper=True)
    add(DOOR_X, 0.0, 0.4, CR2.door_stickley(11.0, 24.0), "front-door", "door")
    add(14.0, 0.0, V1, CR2.window_stickley(12.0, 20.0, n=1), "S14-1")
    add(78.0, 0.0, V1, g3, "S78-1")
    add(112.0, 0.0, V1, g2, "S112-1")
    for x, sp in ((24.0, u2), (70.0, u3), (110.0, u2)):
        add(x, 0.0, V2, sp, f"S{x:.0f}-2")
    add(W, YC, 0.4, CR2.door_stickley(10.0, 22.0, 1.3, True), "porch-door", "door")
    add(W, YC, V2 - 3.6, CR2.door_stickley(10.0, 21.0, 1.3, True), "sleep-door", "door")
    for y in (29.0, 67.0):
        add(W, y, V1, CR2.window_stickley(12.0, 20.0, n=1), f"E{y:.0f}-1")
        add(W, y, V2, CR2.window_stickley(12.0, 17.0, n=1, upper=True), f"E{y:.0f}-2")
    add(W, YC, Z_EAVE + 7.0 - ZF, att, "E-attic")
    for y in (28.0, 68.0):
        add(0.0, y, V1, g2, f"W{y:.0f}-1")
        add(0.0, y, V2, u2, f"W{y:.0f}-2")
    add(0.0, YC, Z_EAVE + 7.0 - ZF, att, "W-attic")
    for x, sp in ((30.0, g2), (64.0, g2)):
        add(x, D, V1, sp, f"N{x:.0f}-1")
    add(100.0, D, 0.4, CR2.door_stickley(10.0, 22.0, 1.3, True), "back-door", "door")
    for x in (30.0, 64.0, 100.0):
        add(x, D, V2, u2, f"N{x:.0f}-2")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    r = RAKE - D_EAVE
    pieces = [([(-r, 0.0), (W + r, 0.0), (W + r, D), (-r, D)], [0, 2], S)]
    gdefs = [dict(p0=(0.0, D), p1=(0.0, 0.0), slope=S), dict(p0=(W, 0.0), p1=(W, D), slope=S)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="hexslate", tex_kw=dict(pitch=2.0, wtab=2.6, d=0.36),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    gables = [(MAIN, 3, rf["walls"][0]["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 1, rf["walls"][1]["cs"].translate((0.0, Z_EAVE - ZF)))]
    undress = [slab(offset(base, 10.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    st = stacked_shells([MAIN], OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=gables,
                        clear=[lip_keep(base, 3.0, ZF, 1.2)], prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None,
                        water_table=False, undress=undress, partitions=[((XC, 3.0), (XC, D - 3.0), 2.0, ZF, ZW)])
    kit.add("WALLS-1", "Bark", st["shells"][0], group="walls")
    kit.add("JOINT", "Linen", st["rings"][0], group="walls")
    no_lip = union([box([-1, -1, ZW - 1], [5.0, D + 1, ZW + 5]), box([W - 5.0, -1, ZW - 1], [W + 1, D + 1, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    kit.add("WALLS-2", "Forest", st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation([MAIN], 0.0, ZF, style="boardformed")
    kit.add("FOUNDATION", "Fieldstone", fnd, group="foundation")
    ins_keep = []
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        b = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if op.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{op.v0 > 20}",
                       group="inserts", render=zones)
        ins_keep.append(part.solid)
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the roof: hexagonal slates, a ridge cap; a stack on the ridge
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S * (D / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((-RAKE, YC), (W + RAKE, YC), zr, S, ZW) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 12.0, 9.0
    cx, cy = 36.0, YC
    z0 = round((zr - 6.0) / 0.2) * 0.2
    roof = roof + (box([cx - CW / 2 - 1.6, cy - CD / 2 - 1.6, ZW + 0.01], [cx + CW / 2 + 1.6, cy + CD / 2 + 1.6, z0 + 0.01]) ^ solid_env)
    roof = roof - box([cx - CW / 2 - 0.9, cy - CD / 2 - 0.9, z0], [cx + CW / 2 + 0.9, cy + CD / 2 + 0.9, zr + 60])
    kit.add("ROOF", "Slate", roof, group="roof")
    kit.add("CHIMNEY", "Fieldstone", _stack(CW, CD, round((zr + 12.0 - z0) / 0.2) * 0.2).translate([cx, cy, z0]), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the two-tier porch on the east gable: the entry porch below, the sleeping porch on
    # its top; each top is one piece with its posts, pegged into the floor under it
    INSET = 2.6
    ppts = [(W, PY0), (W + PW_, PY0), (W + PW_, PY1), (W, PY1)]
    H_floor = ZF - 1.4
    runs = [dict(a=(W, PY0), b=(W + PW_, PY0), posts=[3.4, PW_ - INSET]),
            dict(a=(W + PW_, PY0), b=(W + PW_, PY1), posts=[INSET, 20.0, 40.0, PY1 - PY0 - INSET]),
            dict(a=(W + PW_, PY1), b=(W, PY1), posts=[INSET, PW_ - 3.4])]
    ptop1 = ZU
    PP = FT.porch_turned(ppts, runs, H_floor, ptop1 - 5.2 - H_floor, steps_at=[(1, 30.0, 14.0)], over=2.0, inset=INSET,
                         rail_h=8.4, planks=dict(pitch=1.8, border=1.2), post="stickley", rail="splats", arcade="bolsterbeam",
                         skirt="formboard", pier_tex="boardformed", roof_edge="twinrafters", top=True)
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    deck = PP["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch", render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([p.solid for p in kit.parts if p.name in ("WALLS-1", "JOINT", "WALLS-2") or p.name.startswith("CORNICE")])
    keep = bld_keep + union(ins_keep) + fnd
    res1 = FT.add_porch_top(kit, "PORCH", PP, keep, "Linen", "Linen", group="porch")
    z1 = res1["ptop"]
    zs2 = ZE - 3.0
    runs2 = [dict(a=(W, PY0), b=(W + PW_, PY0), posts=[3.4, PW_ - INSET]),
             dict(a=(W + PW_, PY0), b=(W + PW_, PY1), posts=[INSET, 20.0, 40.0, PY1 - PY0 - INSET]),
             dict(a=(W + PW_, PY1), b=(W, PY1), posts=[INSET, PW_ - 3.4])]
    PP2 = FT.porch_turned(ppts, runs2, z1, zs2 + 0.8 - 5.2 - z1, steps_at=[], over=2.0, inset=INSET, rail_h=9.0,
                          planks=dict(pitch=1.8, border=1.2), post="stickley", rail="shakeparapet", arcade="bolsterbeam",
                          skirt="formboard", pier_tex="boardformed", roof_edge="twinrafters", top=True)
    res2 = FT.add_porch_top(kit, "SLEEP", PP2, keep, "Slate", "Forest", tin="custom", group="sleeping porch")
    parts = {p.name: p for p in kit.parts}
    socks = union([box([x - 1.0, y - 1.0, z1 - 2.2], [x + 1.0, y + 1.0, z1 + 0.1]) for (x, y) in PP2["sockets"]])
    parts["PORCH-top"].solid = parts["PORCH-top"].solid - socks
    zs = res2["ptop"] - 0.8
    outer = [(W - 0.2, PY0 - 2.0), (W + PW_ + 2.0, PY0 - 2.0), (W + PW_ + 2.0, PY1 + 2.0), (W - 0.2, PY1 + 2.0)]
    hr, hr_tex = R.hip_roof([(outer, [0, 1, 2])], zs, 0.34, 0.0, texture="hexslate", tex_kw=dict(pitch=1.8, wtab=2.4, d=0.34), zlo=zs)
    hroof = ((hr + hr_tex) ^ slab(poly(outer), zs, zs + 20.0)) - bld_keep - union(ins_keep) - roof
    kit.add("SLEEP-roof", "Slate", max(hroof.decompose(), key=lambda m_: m_.volume()), group="sleeping porch")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PORCH-steps-{k}", "Fieldstone", sm.transform(A) - fkeep - deck, group="porch")

    # --- the pergola over the front door, on a stone terrace
    TX0, TX1, TD = DOOR_X - 16.0, DOOR_X + 16.0, 16.0
    terr = box([TX0, -TD, 0.0], [TX1, 0.0, ZF - 1.0]) - fnd
    zp = S1 - 6.0
    per = CR2.pergola(TX0 - 2.0, TX1 + 2.0, 0.0, -TD, zp, (TX0 + 2.0, TX1 - 2.0), zp - 2.6 - (ZF - 1.0), ZF - 1.0)
    per = per - bld_keep - union(ins_keep)
    terr = terr - per
    kit.add("TERRACE", "Fieldstone", terr - _grow_pegs(TX0 + 2.0, TX1 - 2.0, -TD + 1.8, ZF - 1.0), group="pergola")
    kit.add("PERGOLA", "Linen", max(per.decompose(), key=lambda m_: m_.volume()), P=print_flip(), group="pergola")
    e, u = MAIN.locate(100.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Fieldstone", FT.steps(14.0, ZF - 0.6, 3).transform(A) - fnd, group="porch")
    fa = MAIN.facades()[0]
    A = fa.A.copy()
    A[:, 3] = fa.world(DOOR_X, -ZF, TD)
    kit.add("TERRACE-steps", "Fieldstone", FT.steps(14.0, ZF - 1.6, 3).transform(A) - terr, group="pergola")
    FT.key_into(kit, "PORCH-steps-0", ["PORCH-deck"], (-1, 0, 0), depth=0.8, conform=True)
    FT.key_into(kit, "TERRACE-steps", ["TERRACE"], (0, 1, 0), depth=0.8, conform=True)
    FT.key_into(kit, "STOOP-back", ["FOUNDATION"], (0, -1, 0), depth=0.8, conform=True)
    print("specks dropped:", kit.drop_specks())
    return kit


def _grow_pegs(xa, xb, y, z, peg=1.6, clr=0.15):
    """Sockets in the terrace for the pergola's two post pegs."""
    h = peg / 2 + clr
    return union([box([x - h, y - h, z - 1.8], [x + h, y + h, z + 0.1]) for x in (xa, xb)])


def _stack(w, d, h):
    """The Stickley's stack: board-formed concrete to a thick cap with a chamfered drip, two
    square flues standing out of it."""
    h = round(h / 0.2) * 0.2
    zt = h - 3.4
    body = box([-w / 2, -d / 2, 0.0], [w / 2, d / 2, zt])
    from hoarch import trimwork as TW
    body = body + TW._skin(w, d, 0.0, zt - 0.2, lambda reg, i: CR2.foundation_boardformed(reg, seed=i))
    body = body + M.hull_points([(x * (w / 2 + 0.2), y * (d / 2 + 0.2), zt - 0.01) for x in (-1, 1) for y in (-1, 1)] +
                                [(x * (w / 2 + 1.0), y * (d / 2 + 1.0), zt + 0.8) for x in (-1, 1) for y in (-1, 1)])
    body = body + box([-w / 2 - 1.0, -d / 2 - 1.0, zt + 0.79], [w / 2 + 1.0, d / 2 + 1.0, zt + 1.6])
    for sg in (-1, 1):
        body = body + box([sg * w / 4 - 1.6, -1.6, zt + 1.59], [sg * w / 4 + 1.6, 1.6, h]) - box([sg * w / 4 - 0.8, -0.8, h - 3.0], [sg * w / 4 + 0.8, 0.8, h + 1])
    return body


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "stickley")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "stickley.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
