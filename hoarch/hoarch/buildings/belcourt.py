"""The Belcourt -- an original HO-scale (1:87.1) Italianate house of the mansard batch (houses 81
to 90): the batch's flat-roof variant, with the same idea as the mansard houses (the last
storey is a band of small windows plugged in under a layered eave).

Ochre ashlar laid in tall and short courses with cream trim and oxblood accents, on a raised
basement of frost-work rustication. Two storeys and an attic band: oblong frieze windows with
cast grilles sit between tall paired consoles that hang from the eave's soffit down over the
band. A two-storey canted bay on the east. A flat tin roof behind a cream balustrade, a square
belvedere with a round-headed window in each face under its own bracketed cornice and a low
tin pyramid with a ball-and-spire finial, two stuccoed stacks with blind niches. An entrance
portico of paired half-fluted columns with double-ball balusters.

- Ground-floor windows round-headed under keyed archivolts with rosettes and a cornice; upper
  windows flat-headed with crossettes under segmental caps on little brackets; a double door
  under a radiating fanlight between imposts and rosettes.
- Storey joint: an oxblood frieze of interlaced square links, a cream crown.
- Attic sill: a cream fluted band and an oxblood crown.
- Eave: a cream soffit with a fascia on tall paired long consoles, an oxblood cavetto crown
  with blocks.
- Belvedere: an oxblood frieze of sixfoils, a soffit on short long-consoles, a crown.

usage: python3 -m hoarch.buildings.belcourt [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import Facade, box, ccw, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, openings as O, roof as R, secondempire as SE
from hoarch import shell as SH
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, foundation, lip_keep, stacked_shells

NAME = "Belcourt"
COLORS = {"PorchDeck": "#EFE6CF", "Planks": "#6F5034",
          "Ochre": "#C79A4B", "Cream": "#EFE6CF", "Oxblood": "#6E2A2A", "Tin": "#6D7378", "Stone": "#9C9488",
          "Windows_Doors": "#EFE6CF"}
RENDER_MAT = {"PorchDeck": "trim", "Planks": "planks", "Ochre": "walls", "Cream": "trim", "Oxblood": "accent",
              "Tin": "roof", "Stone": "stone", "Windows_Doors": "trim", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"walls": ["#C79A4B", 0.85, 0.0], "trim": ["#EFE6CF", 0.6, 0.0], "accent": ["#6E2A2A", 0.55, 0.0],
           "roof": ["#6D7378", 0.6, 0.15], "stone": ["#9C9488", 0.9, 0.0], "planks": ["#6F5034", 0.75, 0.0],
           "sash": ["#3A2A22", 0.45, 0.0], "door": ["#4A2216", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Belcourt)
LEDGE = 1.4
PITCH, MARGIN, PAIR = 30.0, 8.0, 3.2       # the eave's bracket stations: the frieze windows go between them
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.0, b=1.2, orn="squarelinks", role="Oxblood"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="ogee_fillet", role="Cream")])
ATTIC = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.2, orn="flutecourse", role="Cream"),
    dict(kind="crown", h=2.0, b=1.4, P=3.2, orn="bevel", role="Oxblood")])
EAVE = dict(pitch=PITCH, margin=MARGIN, pair=PAIR, layers=[
    dict(kind="bed", h=2.4, b=1.4, P=8.4, role="Cream", fascia=dict(h=1.2, d=0.4),
         brackets=dict(style="longconsole", t=1.6, h=12.0)),
    dict(kind="crown", h=3.0, b=1.4, P=9.2, orn="cavetto", role="Oxblood", blocks=dict(w=1.6, h=1.0, d=0.5))])
BELV_C = dict(pitch=10.0, margin=3.0, pair=2.4, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="sixfoils", role="Oxblood"),
    dict(kind="bed", h=1.8, b=1.4, P=5.4, role="Cream", brackets=dict(style="longconsole", t=1.6, reach=0.7)),
    dict(kind="crown", h=2.2, b=1.4, P=6.0, orn="cavetto", role="Oxblood")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2

# ------------------------------------------------------------------ levels (all on the 0.2 mm grid)
ZF = 15.0
S1 = ZF + 42.0
ZA0 = S1 + RJ + 38.0                         # the attic sill cornice's ledge
HAT = CO.band_height(ATTIC)
ZE = ZA0 + HAT + 15.0                        # the eave ledge: the attic band is 15 mm between them
ZW = ZE + CO.band_height(EAVE)
V1, V2 = 7.0, S1 + RJ + 5.0 - ZF
V_ATTIC = ZE - 9.6 - ZF                      # the frieze windows' sills
BELV_H = 30.0

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 196.0, 136.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
BAY = Block("bay", [(X1 - 3.0, 46.0), (X1, 46.0), (X1 + 12.0, 54.0), (X1 + 12.0, 82.0), (X1, 90.0), (X1 - 3.0, 90.0)], ZF, ZW)
BLOCKS = [MAIN, BAY]
BX, BY, BS = 98.0, 70.0, 44.0                # the belvedere's centre and side
CHIMS = [(24.0, 68.0), (172.0, 68.0)]


def _skin(f, b, reg):
    """Pseudo-isodomic ashlar; nothing in the cornice bands."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0) - rect(-1, ZA0 - LEDGE - 0.6 - b.z0, f.L + 1, ZA0 + HAT - b.z0)
    return SE.ashlar_pseudoisodomic(reg, datum=1.8)


def _eave_path():
    allcs = cs_union([b.cs for b in BLOCKS])
    return max(allcs.to_polygons(), key=lambda L_: abs(poly(L_).area()))


def _on_wall(p, q):
    """The (block, facade index, u of p) whose facade carries the eave edge p -> q."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    for b in BLOCKS:
        for e, f in enumerate(b.facades()):
            a, t, n = f.p0, f.u, f.n
            if abs((p - a) @ n) < 0.05 and abs((q - a) @ n) < 0.05 and (q - p) @ t > 0:
                u = (p - a) @ t
                if -0.05 <= u <= f.L + 0.05:
                    return b, e, u
    return None


# ------------------------------------------------------------------ openings
def _openings():
    L = []
    lo = SE.window_belcourt_lower()
    up = SE.window_belcourt_upper()
    att = SE.window_belcourt_attic()
    front = SE.door_belcourt()
    back = SE.door_belcourt_back()

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    for x in (23.0, 53.0, 143.0, 173.0):
        add(MAIN, x, 0, V1, lo, f"S{x:.0f}-1")
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
    for x in (23.0, 53.0, 98.0, 143.0, 173.0):
        add(MAIN, x, 0, V2, up, f"S{x:.0f}-2")
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, 98.0, 0, 0.4, front, "front-door", "door")
    add(MAIN, 98.0, Y1, 0.4, back, "back-door", "door")
    for y in (23.0, 53.0, 83.0, 113.0):
        add(MAIN, 0, y, V1, lo, f"W{y:.0f}-1")
        add(MAIN, 0, y, V2, up, f"W{y:.0f}-2")
    for y in (22.0, 114.0):
        add(MAIN, X1, y, V1, lo, f"E{y:.0f}-1")
        add(MAIN, X1, y, V2, up, f"E{y:.0f}-2")
    add(BAY, X1 + 12.0, 68.0, V1, lo, "bay-1")
    add(BAY, X1 + 12.0, 68.0, V2, up, "bay-2")
    # the frieze windows: one in every bay between the eave's bracket pairs that has room for one
    P_ = ccw(_eave_path())
    k = 0
    for i in range(len(P_)):
        p, q = P_[i], P_[(i + 1) % len(P_)]
        Le = math.dist(p, q)
        hit = _on_wall(p, q)
        if hit is None:
            continue
        b, e, u0 = hit
        for uc, wd in CO._between(Le, PITCH, MARGIN, PAIR, 0.8):
            if wd >= 11.2:
                L.append(Opening(b, e, u0 + uc, V_ATTIC, att, f"A{k}"))
                k += 1
    return L


OPENINGS = _openings()


# ------------------------------------------------------------------ build
def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    allcs = cs_union([b.cs for b in BLOCKS])
    eave_path = _eave_path()
    undress = [slab(offset(allcs, 8.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(allcs, 8.0), ZA0 - LEDGE - 0.6, ZA0 + HAT + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", clear=[lip_keep(allcs, 3.0, ZF, 1.2)],
                        siding=_skin, prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=undress)
    kit.add("WALLS-1", "Ochre", st["shells"][0], group="walls")
    kit.add("JOINT", "Ochre", st["rings"][0], group="walls")
    rings_e, _ = CO.level(eave_path, ZE, EAVE)
    # the eave's consoles hang below its ledge, down over the attic band, their backs on the
    # ashlar: the ledge is notched round each one
    hang = union([r["solid"] for r in rings_e]) ^ box([-1e3, -1e3, ZE - 20.0], [1e3, 1e3, ZE + 0.01])
    notches = union([box(list(np.array(c.bounding_box()[:3]) - 0.15), list(np.array(c.bounding_box()[3:]) + [0.15, 0.15, 0.5]))
                     for c in hang.decompose() if c.volume() > 0.5])
    ledges = (CO.ledge(eave_path, ZE, LEDGE) - notches) + CO.ledge(eave_path, ZA0, LEDGE)
    kit.add("WALLS-2", "Ochre", st["shells"][1] + ledges, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZA0, ATTIC)
    CO.add_level(kit, rings, "CORNICE-A", "cornice")
    CO.add_level(kit, rings_e, "CORNICE-E", "cornice")
    kit.add("FOUNDATION", "Stone", foundation(BLOCKS, 0.0, ZF, style="frostwork"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Cream", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1), "frieze windows", sum(1 for o in OPENINGS if o.name.startswith("A")))

    # --- the flat roof: a tin deck on the eave's crown, the balustrade, chimneys, the belvedere
    Pc = EAVE["layers"][-1]["P"]
    zd = ZW + 1.4
    deck = slab(offset(allcs, Pc + 0.2), ZW, zd)
    dcs = offset(allcs, Pc - 1.4)
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x0, y - 0.25, x1, y + 0.25) for y in np.arange(y0 + 2.6, y1, 5.2)]) ^ dcs
    BELV = Block("belvedere", [(BX - BS / 2, BY - BS / 2), (BX + BS / 2, BY - BS / 2), (BX + BS / 2, BY + BS / 2),
                               (BX - BS / 2, BY + BS / 2)], zd - 0.6, zd + BELV_H)
    pocket = BELV.solid(grow=0.15, dz0=0.0, dz1=5.0)
    pads = union([box([x - 6.2, y - 6.7, zd - 0.6], [x + 6.2, y + 6.7, zd + 1]) for x, y in CHIMS])
    deck = deck + slab(seams - offset(BELV.cs, 1.0), zd - 0.01, zd + 0.4) - pads - pocket
    kit.add("ROOF-deck", "Tin", deck, group="roof")
    for i, seg, A, L in SE.cresting_strips(eave_path, zd, Pc - 1.2, SE.fence_belcourt, 5.0):
        kit.add(f"BALUSTRADE-{i}", "Cream", seg, P=inv34(A), key=f"BALUSTRADE-{round(L, 1)}", group="roof")
    for k, (x, y) in enumerate(CHIMS):
        ch = SE.chimney_belcourt(w=10.0, d=11.0, h=22.0).translate([x, y, zd - 0.6])
        kit.add(f"CHIMNEY-{k}", "Ochre", ch, key="CHIMNEY", group="roof")
    # belvedere: walls with a window each side, its cornice, a low tin pyramid with its finial
    bw = SE.window_belcourt_belvedere()
    bops = []
    for x, y, nm in ((BX, BY - BS / 2, "S"), (BX + BS / 2, BY, "E"), (BX, BY + BS / 2, "N"), (BX - BS / 2, BY, "W")):
        e, u = BELV.locate(x, y)
        bops.append(Opening(BELV, e, u, 4.0, bw, f"BELV-{nm}"))
    zbt = BELV.z1 - CO.band_height(BELV_C)
    bwalls = SH.wall_shell([BELV], bops, t=2.4, corners="none", water_table=False, belt=None,
                           siding=lambda f, b, reg: SE.ashlar_pseudoisodomic(reg - rect(-1, zbt - LEDGE - 0.6 - b.z0, f.L + 1, 99), datum=0.6),
                           undress=[slab(offset(BELV.cs, 8.0), zbt - LEDGE - 0.6, BELV.z1 + 1)])
    kit.add("BELVEDERE", "Ochre", bwalls + CO.ledge(BELV.pts, zbt, LEDGE), group="belvedere")
    for o in bops:
        world, P, zones = O.place(o.spec, o.local_frame(), "Cream", "Sash", "Glass")
        kit.add(f"WIN-{o.name}", "Windows_Doors", world, P=P, key="WIN-belvedere", group="inserts", render=zones)
    rings, zbtop = CO.level(BELV.pts, zbt, BELV_C)
    CO.add_level(kit, rings, "CORNICE-BV", "belvedere")
    Pb = BELV_C["layers"][-1]["P"] + 0.2
    base = offset(BELV.cs, Pb)
    bx0, by0, bx1, by1 = base.bounds()
    roof = M.hull_points([(x, y, zbtop) for x in (bx0, bx1) for y in (by0, by1)] +
                         [(x, y, zbtop + 0.8) for x in (bx0, bx1) for y in (by0, by1)] +
                         [(BX + sx * 3.0, BY + sy * 3.0, zbtop + 7.0) for sx in (-1, 1) for sy in (-1, 1)])
    kit.add("BELVEDERE-roof", "Tin", roof, group="belvedere")
    kit.add("BELVEDERE-finial", "Cream", SE.finial_ballspire(8.0).translate([BX, BY, zbtop + 6.99]), group="belvedere")
    print("roof", round(time.time() - t0, 1))

    # --- entrance portico: paired half-fluted columns
    H_floor = ZF - 1.4
    post_h = S1 - 2.0 - 5.6 - H_floor
    y0, y1 = -1.4, -22.0
    px0, px1 = 98.0 - 22.0, 98.0 + 22.0
    Lp = px1 - px0
    runs = [dict(a=(px0, y0), b=(px0, y1), posts=[1.7, (y0 - y1) - 1.6]),
            dict(a=(px0, y1), b=(px1, y1), posts=[1.6, 4.9, Lp - 4.9, Lp - 1.6]),
            dict(a=(px1, y1), b=(px1, y0), posts=[1.6, (y0 - y1) - 1.7])]
    P = FT.porch_turned([(px0, y0), (px0, y1), (px1, y1), (px1, y0)], runs, H_floor, post_h,
                        steps_at=[(1, Lp / 2, 18.0)], planks=dict(pitch=1.4, border=1.6), joined=True,
                        post="halffluted", rail="doubleball", arcade="paterae", skirt="louvres", pier_tex="limestone",
                        roof_edge="pelletdentil", top=True)
    fkeep = slab(offset(allcs, 1.7), -1, ZF + 1.3)
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    deck_ = P["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck_, P=print_flip(), group="porch",
            render=FT.plank_zones(deck_, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=300) for b in BLOCKS])
    FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_keep, "Cream", "Cream", tin_col="Tin", tin="flat")
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Stone", sm.transform(A) - fkeep, group="porch")
    e, u = MAIN.locate(98.0, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Stone", FT.steps(15.0, ZF - 0.6, 6).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("BALUSTRADE")]:
        FT.key_into(kit, p_.name, ["ROOF-deck"], (0, 0, -1), depth=0.6)
    FT.crown(kit, "BELVEDERE-finial", "BELVEDERE-roof")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "belcourt")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "belcourt.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
