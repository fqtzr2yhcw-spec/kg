"""The Fairhaven: an original HO-scale (1:87.1) Colonial Revival house with a Victorian flair,
house 40 of the Colonial batch (a Colonial front, two-storey canted bays, a Palladian gable,
a turned-post veranda).

A symmetrical front of two storeys under a side-gabled roof of pinked slates: celadon channel
rustic siding below, moss-green lap of two exposures in turn above, on snecked stone. Two
canted bays rise the full two storeys either side of the entrance, each under its own low
hip, the eave cornice wrapping round them. Over the middle a front cross-gable carries a
Palladian window (a round-headed centre light between two square-headed side lights under a
running entablature, fluted mullions, a keystone). Between the bays a veranda on turned
candlestick posts with cup-and-ring balusters, a terracotta frieze of interlocking rings, a
Vitruvian-scroll fascia and a skirt pierced with cloverleaves. Between the storeys a
terracotta frieze of wheat sheaves, a cream reeded course and a cream ovolo; at the eave a
terracotta frieze of trailing ivy, cream billets, a soffit on palmette consoles and a
terracotta cavetto. First-storey windows (two over two) under ogee hood mouldings with little
finials; second-storey windows under flat caps on scrolled consoles over panelled aprons; a
lunette in each end gable. A pair of glazed doors under a leaded fan-and-drape transom
between reeded casings, a flat hood on tall consoles. Two quoined Flemish-bond chimneys.

usage: python3 -m hoarch.buildings.fairhaven [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import box, compose, cs_union, inv34, offset, poly, rect, slab, union, zq
from hoarch import cornice as CO, features as FT, freeclassic as FC, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Fairhaven"
COLORS = {"Celadon": "#9DB39E", "Moss": "#7C9580", "Cream": "#F1EAD6", "Terracotta": "#B4553C", "Charcoal": "#40464A",
          "Stone": "#8E8A80", "Brick": "#8A3F30", "PorchDeck": "#F1EAD6", "Windows_Doors": "#F1EAD6"}
RENDER_MAT = {"Celadon": "siding", "Moss": "siding2", "Cream": "trim", "Terracotta": "accent", "Charcoal": "roof",
              "Stone": "stone2", "Brick": "brick", "PorchDeck": "trim", "Planks": "planks", "Windows_Doors": "trim",
              "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Fairhaven)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="wheat", role="Terracotta"),
    dict(kind="course", h=1.4, b=1.4, orn="reeds", role="Cream"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="ovolo", role="Cream")])
EAVE = dict(pitch=11.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.2, b=1.2, orn="ivy", role="Terracotta"),
    dict(kind="course", h=1.6, b=1.4, orn="billet", role="Cream"),
    dict(kind="bed", h=2.2, b=1.4, P=6.4, role="Cream", brackets=dict(style="palmette", t=1.2, reach=0.4)),
    dict(kind="crown", h=2.8, b=1.4, P=7.2, orn="cavetto", role="Terracotta")])
RJ = zq(LEDGE + 0.4 + CO.band_height(JOINT))
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 12.0
S1 = ZF + 44.0
ZE = S1 + RJ + 38.0
ZW = zq(ZE + HE)
FASCIA = 1.8
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 7.4, 7.6, 1.8
S_MAIN, S_CROSS, S_BAY = 0.8, 1.0, 0.35
V1 = 6.0
V2 = S1 + RJ + 4.0 - ZF

# ------------------------------------------------------------------ plan
W, D = 204.0, 108.0
XC = W / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BD = 12.0                        # the canted bays' depth
BAYS_X = [(20.0, 60.0), (W - 60.0, W - 20.0)]


def _bay(x0, x1, name):
    return Block(name, [(x0, 3.0), (x0, 0.0), (x0 + BD, -BD), (x1 - BD, -BD), (x1, 0.0), (x1, 3.0)], ZF, ZW)


BAY_L, BAY_R = _bay(*BAYS_X[0], "bayL"), _bay(*BAYS_X[1], "bayR")
BLOCKS = [MAIN, BAY_L, BAY_R]
CG = (XC - 30.0, XC + 30.0)      # the front cross-gable's span
PX0, PX1, PY = 62.0, W - 62.0, -16.0     # the veranda between the bays


def _siding(f, b, reg):
    """Channel rustic below the joint, lap of two exposures above and in the gables; nothing
    behind the eave cornice."""
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    cut = S1 - b.z0
    out = []
    lo = reg ^ rect(-1, -100, f.L + 1, cut)
    hi = reg ^ rect(-1, cut, f.L + 1, 999)
    if not lo.is_empty():
        out.append(FC.siding_channel(lo, datum=0.0))
    if not hi.is_empty():
        out.append(FC.siding_alternating(hi, datum=S1 + RJ - b.z0))
    return union(out) if out else M()


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    lo, up = FC.window_ogee_hood(10.0, 22.0), FC.window_consoled(10.0, 20.0)
    lo8, up8 = FC.window_ogee_hood(8.0, 22.0), FC.window_consoled(8.0, 20.0)
    add(MAIN, XC, 0.0, 0.8, FC.door_consoled(13.0, 24.0, 4.4), "front-door", "door")
    for x in (XC - 22.0, XC + 22.0):
        add(MAIN, x, 0.0, V1, lo, f"F{x:.0f}-1")
    for x in (XC - 22.0, XC, XC + 22.0):
        add(MAIN, x, 0.0, V2, up, f"F{x:.0f}-2")
    for bay, tag in ((BAY_L, "L"), (BAY_R, "R")):
        Q = [np.array(p) for p in bay.pts]
        for k, (w1, t) in ((1, (8.0, "a")), (2, (10.0, "f")), (3, (8.0, "b"))):
            m = (Q[k] + Q[k + 1]) / 2
            add(bay, m[0], m[1], V1, lo8 if w1 < 9 else lo, f"bay{tag}{t}-1")
            add(bay, m[0], m[1], V2, up8 if w1 < 9 else up, f"bay{tag}{t}-2")
    add(MAIN, XC, 0.0, ZW - ZF + 3.0, FC.window_palladian(11.0, 5.6, 19.0), "palladian")
    for x_, tag in ((0.0, "W"), (W, "E")):
        for y in (28.0, 80.0):
            add(MAIN, x_, y, V1, lo, f"{tag}{y:.0f}-1")
            add(MAIN, x_, y, V2, up, f"{tag}{y:.0f}-2")
        add(MAIN, x_, D / 2, ZW - ZF + 5.0, FC.window_lunette(12.0), f"{tag}-lunette")
    add(MAIN, XC, D, 0.8, FC.door_consoled(11.0, 23.0, 4.0), "back-door", "door")
    for x in (36.0, 68.0, W - 68.0, W - 36.0):
        add(MAIN, x, D, V1, lo, f"B{x:.0f}-1")
    for x in (36.0, 68.0, XC, W - 68.0, W - 36.0):
        add(MAIN, x, D, V2, up, f"B{x:.0f}-2")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    r = RAKE - D_EAVE
    gy = (S_CROSS * ((CG[1] - CG[0]) / 2 + D_EAVE)) / S_MAIN + 4.0
    pieces = [(MAIN.pts, [0, 2], S_MAIN), ([(CG[0], -r), (CG[1], -r), (CG[1], gy), (CG[0], gy)], [1, 3], S_CROSS)]
    specs = [dict(p0=(W, 0.0), p1=(W, D), slope=S_MAIN, e=0.3), dict(p0=(0.0, D), p1=(0.0, 0.0), slope=S_MAIN, e=0.3),
             dict(p0=(CG[0], 0.0), p1=(CG[1], 0.0), slope=S_CROSS, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, specs, texture="pinked", tex_kw=dict(pitch=1.6, wtab=2.4, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA, hollow=2.8)
    we, ww, wc = rf["walls"]
    gables = [(MAIN, 1, we["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 3, ww["cs"].translate((0.0, Z_EAVE - ZF))),
              (MAIN, 0, wc["cs"].translate((CG[0], Z_EAVE - ZF)))]
    base = cs_union([b.cs for b in BLOCKS])
    eave_path = max(base.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_siding, gables=gables,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        clear=[lip_keep(base, 3.0, ZF, 1.2)])
    kit.add("WALLS-1", "Celadon", st["shells"][0], group="walls")
    kit.add("JOINT", "Celadon", st["rings"][0], group="walls")
    no_lip = union([box([CG[0] - D_EAVE - 0.6, -1, ZW - 1], [CG[1] + D_EAVE + 0.6, 5.0, ZW + 5]),
                    box([W - 5.0, -1, ZW - 1], [W + 1, D + 1, ZW + 5]), box([-1, -1, ZW - 1], [5.0, D + 1, ZW + 5])])
    lip = (_corbel(MAIN.cs, 3.0, ZW) + lip_ring(MAIN.cs, 3.0, ZW)) - no_lip
    ledges = CO.ledge(eave_path, ZE, LEDGE)
    kit.add("WALLS-2", "Moss", st["shells"][1] + lip + ledges, group="walls")
    for tag, path, z0, spec in (("J", st["outlines"][0], S1 + LEDGE + 0.4, JOINT), ("E", eave_path, ZE, EAVE)):
        rings, _ = CO.level(path, z0, spec)
        CO.add_level(kit, rings, f"CORNICE-{tag}", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="snecked")
    kit.add("FOUNDATION", "Stone", fnd, group="foundation")
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

    # --- the main roof with its cross-gable, two chimneys near the gable ends
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15]))
                       for wl in rf["walls"]])
    zc = Z_EAVE + S_CROSS * ((CG[1] - CG[0]) / 2 + D_EAVE)
    y_meet = (zc - Z_EAVE) / S_MAIN - D_EAVE + 1.0
    caps = [G.ridge_cap((-RAKE, D / 2), (W + RAKE, D / 2), zr, S_MAIN, ZW),
            G.ridge_cap((XC, -RAKE), (XC, y_meet), zc, S_CROSS, ZW)]
    roof = roof + (union(caps) - walls_env)
    roof = roof - lip_keep(MAIN.cs, 3.0, ZW)
    solid_env, _ = R.hip_roof([(MAIN.pts, [0, 2], S_MAIN)], Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 12.0, 10.0
    z0 = zq(zr - S_MAIN * CD / 2 - 3.0)
    chims = []
    for cx in (26.0, W - 26.0):
        roof = roof + (box([cx - CW / 2 - 1.2, D / 2 - CD / 2 - 1.2, ZW + 0.01], [cx + CW / 2 + 1.2, D / 2 + CD / 2 + 1.2, z0 + 0.01])
                       ^ solid_env)
        roof = roof - box([cx - CW / 2 - 0.5, D / 2 - CD / 2 - 0.5, z0], [cx + CW / 2 + 0.5, D / 2 + CD / 2 + 0.5, zr + 40])
        chims.append(FC.chimney_quoined(CW, CD, zq(zr + 14.0 - z0)).translate([cx, D / 2, z0]))
    kit.add("ROOF", "Charcoal", roof, group="roof")
    for k, c in enumerate(chims):
        kit.add(f"CHIMNEY-{k}", "Brick", c, key="CHIMNEY", group="roof")
    # the bays: a low hip of the same slates on each one's cornice, stopped at the wall
    dct = EAVE["layers"][-1]["P"] + 0.4
    for k, bay in enumerate((BAY_L, BAY_R)):
        x0, x1 = BAYS_X[k]
        keep = MAIN.solid(grow=0.45, dz0=-1, dz1=300) + box([-50, -60, 0], [x0, 0, 300]) + box([x1, -60, 0], [300, 0, 300])
        broof, btex = R.hip_roof([(bay.pts, [1, 2, 3])], ZW + 1.0, S_BAY, dct, texture="pinked",
                                 tex_kw=dict(pitch=1.6, wtab=2.4, d=0.4), zlo=ZW)
        kit.add(f"BAY-roof-{k}", "Charcoal", (broof + btex) - keep - roof, key="BAY-roof", group="bay")
    print("roof", round(time.time() - t0, 1))

    # --- the veranda between the bays
    ppts = [(PX0, 0.0), (PX0, PY), (PX1, PY), (PX1, 0.0)]
    Lf = PX1 - PX0
    ud = XC - PX0
    runs = [dict(a=(PX0, 0.0), b=(PX0, PY), posts=[3.0, -PY - 1.6]),
            dict(a=(PX0, PY), b=(PX1, PY), posts=[1.6, ud - 12.0, ud + 12.0, Lf - 1.6]),
            dict(a=(PX1, PY), b=(PX1, 0.0), posts=[1.6, -PY - 3.0])]
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    PP = FT.porch_turned(ppts, runs, H_floor, post_h, steps_at=[(1, ud, 18.0)],
                         planks=dict(pitch=1.8, border=1.2), joined=True, ledger_off=1.5, post="candlestick",
                         rail="cupring", arcade="chainrings", skirt="clover", pier_tex="snecked", roof_edge="vitruvian",
                         top=True, flat_arcades=True)
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    ins_keep = union([box(np.array(p.solid.bounding_box()[:3]) - 0.2, np.array(p.solid.bounding_box()[3:]) + 0.2)
                      for p in inserts if p is not None])
    deck = PP["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch",
            render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([b.solid(grow=1.8, dz0=-20, dz1=0) for b in BLOCKS])
    FT.add_porch_top(kit, "PORCH", PP, bld_keep + ins_keep + fnd,
                     "Cream", "Cream", tin_col="Charcoal", arcade_col="Terracotta")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PORCH-steps-{k}", "Stone", sm.transform(A) - fkeep - deck, group="porch")
    e, u = MAIN.locate(XC, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Stone", FT.steps(16.0, ZF - 0.6, 4).transform(A) - fnd, group="porch")
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "fairhaven")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "fairhaven.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
