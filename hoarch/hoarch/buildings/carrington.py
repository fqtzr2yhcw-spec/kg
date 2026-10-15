"""The Carrington -- an original HO-scale (1:87.1) Southern Colonial Revival mansion, 1906: the ninth of
the grand batch (houses 91 to 100, hoarch.grand), on the mansard batch's roof system
(hoarch.secondempire).

A cotton factor's mansion. Two storeys of butter-yellow bevelled clapboard on a red brick base
with arched, iron-grilled vents, panelled corner pilasters, every window a six-over-six sash
between louvered plantation shutters (festooned cornice caps below, splayed flat arches with
keystones above). At the middle of the front the wall bows out in three facets, and round the
bow stands a colossal portico of six Ionic columns on a curved plan, carrying an architrave, a
dentilled cornice and a balustrade; inside it, on the storey cornice, a curved cast-iron balcony
on consoles. The front door has a leaded elliptical fanlight and sidelights between fluted
pilasters under a dentilled entablature; over it a Palladian window. The bow's top is a deck
with its own balustrade at the eave. A hipped slate roof with pedimented dormers rises to a
widow's walk; tall panelled brick chimneys stand at either end.

- Storey joint: a white ribbon-and-reed course, a yellow frieze of swags hung from bow-knots, a
  white cyma.
- Eave: ribbon and reed, a yellow frieze of Prince-of-Wales plumes between festoons, volute
  modillions, a white cyma.
- Crest (the widow's walk): a yellow course of festoons and beads under a white ovolo, a white
  balustrade with ball-topped pedestals.

usage: python3 -m hoarch.buildings.carrington [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import Facade, box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, grand as G, openings as O, roof as R, secondempire as SE
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, foundation, lip_keep, stacked_shells

NAME = "The Carrington"
COLORS = {"Clapboard": "#E6D49A", "Trim": "#F1EEE4", "Brick": "#8E3B2E", "Slate": "#4A5058", "Iron": "#1F2326",
          "Planks": "#7A5C40", "Windows_Doors": "#F1EEE4", "Addins": "#4A5058"}
RENDER_MAT = {"Clapboard": "siding", "Trim": "trim", "Brick": "brick", "Slate": "roof", "Iron": "iron", "Planks": "planks",
              "Windows_Doors": "trim", "Addins": "roof", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"siding": ["#E6D49A", 0.75, 0.0], "trim": ["#F1EEE4", 0.6, 0.0], "brick": ["#8E3B2E", 0.85, 0.0],
           "roof": ["#4A5058", 0.75, 0.0], "iron": ["#1F2326", 0.45, 0.3], "planks": ["#7A5C40", 0.75, 0.0],
           "sash": ["#2A2E2A", 0.45, 0.0], "door": ["#2E4A36", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Carrington)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="ribbonreed", role="Trim"),
    dict(kind="frieze", h=5.4, b=1.2, orn="bowknotswags", role="Clapboard"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="cyma", role="Trim")])
EAVE = dict(pitch=7.0, margin=3.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="ribbonreed", role="Trim"),
    dict(kind="frieze", h=6.4, b=1.2, orn="plumes", role="Clapboard"),
    dict(kind="bed", h=3.2, b=1.4, P=7.6, role="Trim", brackets=dict(style="volutemod", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.6, b=1.4, P=8.4, orn="cyma", role="Trim")])
CREST_COURSE = dict(h=2.6, b=0.6, orn=G.festoonchain, role="Clapboard")
CREST_CROWN = dict(h=2.4, P=3.4, kind="ovolo", role="Trim", blocks=None)
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 7.0
S1 = ZF + 36.0
ZE = S1 + RJ + 36.0
ZW = ZE + HE
DK = EAVE["layers"][-1]["P"] + 0.2
RH = 26.0
ZR1 = ZW + RH
D_TOP = round(DK - 1.0 - (RH - 0.8) / math.tan(math.radians(50.0)), 1)
ROOF = [(DK, ZW), (DK - 1.0, ZW + 0.8), (D_TOP, ZR1)]
SLATE = dict(pitch=1.6, wtab=1.8, d=0.35, shape="square")
Z_ADD = ZW + 2.0
G.CR_LEVELS.update(hi=S1 + RJ - ZF)
V1, V2 = 5.0, S1 + RJ - ZF + 2.8

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 156.0, 92.0
XC = X1 / 2
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
# the bow: three facets on an arc of radius 30 about (XC, 10), bulging 20 out of the front wall
BR, BC = 30.0, (XC, 10.0)
_ba = math.asin(BC[1] / BR)
BOW_ARC = [(BC[0] + BR * math.cos(a), BC[1] + BR * math.sin(a)) for a in np.linspace(math.pi + _ba, 2 * math.pi - _ba, 4)]
BOW = Block("bow", [(BOW_ARC[0][0], 3.0), (BOW_ARC[0][0], 0.0)] + BOW_ARC[1:-1] + [(BOW_ARC[-1][0], 0.0), (BOW_ARC[-1][0], 3.0)],
            ZF, ZW)
BLOCKS = [MAIN, BOW]
RP = BR + 14.0                                   # the portico's circumradius about the bow's centre
INS = 4.2
CHIMS = [(24.0, 46.0), (132.0, 46.0)]


def _walls(f, b, reg):
    """Bevelled clapboard on both storeys; nothing in the cornice bands."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    lo = reg ^ rect(-1, -100, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, S1 + RJ - b.z0, f.L + 1, 999)
    out = []
    if not lo.is_empty():
        out.append(G.lap_carrington(lo, datum=0.0, seed=3 + int(f.L) % 7))
    if not hi.is_empty():
        out.append(G.lap_carrington(hi, datum=S1 + RJ - b.z0 + 0.2, seed=11 + int(f.L) % 7))
    return union(out) if out else M()


def _openings():
    L = []

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    lo, up = G.window_carrington_lower(), G.window_carrington_upper()
    # the bow's three facets (midpoints): the door and the Palladian window on the middle one
    facets = [((BOW_ARC[i][0] + BOW_ARC[i + 1][0]) / 2, (BOW_ARC[i][1] + BOW_ARC[i + 1][1]) / 2) for i in range(3)]
    for k, (x, y) in enumerate(facets):
        if k == 1:
            add(BOW, x, y, 1.2, G.door_carrington(w=8.4, side=2.0), "front-door", "door")
            add(BOW, x, y, V2, G.window_carrington_palladian(), "palladian")
        else:
            add(BOW, x, y, V1, lo, f"B{k}-1")
            add(BOW, x, y, V2, up, f"B{k}-2")
    for x in (14.0, 32.0, 124.0, 142.0):
        add(MAIN, x, 0.0, V1, lo, f"S{x:.0f}-1")
        add(MAIN, x, 0.0, V2, up, f"S{x:.0f}-2")
    for x_, tag in ((0.0, "W"), (X1, "E")):
        for y in (24.0, 46.0, 68.0):
            add(MAIN, x_, y, V1, lo, f"{tag}{y:.0f}-1")
            add(MAIN, x_, y, V2, up, f"{tag}{y:.0f}-2")
    for x in (20.0, 46.0, 110.0, 136.0):
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
    for x in (20.0, 46.0, XC, 110.0, 136.0):
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, XC, Y1, 1.2, G.door_carrington(w=8.4, h=19.0, back=True), "back-door", "door")
    return L


OPENINGS = _openings()
ADDINS = [(36.0, 0.0), (120.0, 0.0), (40.0, Y1), (XC, Y1), (116.0, Y1), (0.0, 46.0), (X1, 46.0)]


def _frame_on(block, x, y, z, w0):
    e, u = block.locate(x, y)
    f = block.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, z - block.z0, w0)
    return A


def _addins(kit, block, places, prof, z_sill, sp, tag):
    pl = [SE.addin_place(sp, prof, z_sill) for _ in places]
    depth = max(d for _, d in pl)
    keeps, flashes = [], []
    for k, ((x, y), (w0, _)) in enumerate(zip(places, pl)):
        A = _frame_on(block, x, y, z_sill, w0)
        a = SE.addin(sp, depth)
        keeps.append(a["keep"].transform(A))
        flashes.append(a["flash"].transform(A))
        zones = [("Glass", a["glass"].transform(A)), ("Slate", (a["plug"] - a["glass"]).transform(A)),
                 ("Trim", a["frame"].transform(A))]
        kit.add(f"{tag}-{k}", "Addins", a["solid"].transform(A), P=inv34(A), change=(round(depth, 1), "Trim"),
                key=tag, group="addins", render=zones)
    print(tag, "plug", depth)
    return union(keeps), union(flashes)


def _deck_plate(C, z):
    dcs = poly(R.offset_path(C["path"], -1.6))
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + 2.6, x1, 5.2)]) ^ dcs
    return C["deck"] + slab(seams, z - 0.01, z + 0.4)


def _strips(kit, tag, chain, z, keep, fence, h, colour, group, end=0.7, t=0.9):
    """Flat-printed strips along an open chain, standing at z, cut by ``keep``; their names."""
    names = []
    for i in range(len(chain) - 1):
        f = Facade(np.array(chain[i]), np.array(chain[i + 1]), 0.0)
        if f.L < 2 * end + 3.0:
            continue
        cs = fence(f.L - 2 * end, h).translate([end, 0.0])
        strip = M.extrude(cs, t).translate([0, 0, -t / 2])
        A = f.A.copy()
        A[:, 3] = f.world(0, 0, 0) + np.array([0, 0, z - 0.01])
        seg = strip.transform(A) - keep
        for j, piece in enumerate(seg.decompose()):
            if piece.volume() > 3.0:
                n = f"{tag}-{i}{chr(97 + j)}"
                kit.add(n, colour, piece, P=inv34(A), group=group)
                names.append(n)
    return names


def _arc(r, y_cut=-1.4, n=5):
    """The portico's half-polygon about the bow's centre: its two ends on y = y_cut."""
    a0 = math.pi + math.asin((BC[1] - y_cut) / r)
    return [(BC[0] + r * math.cos(a), BC[1] + r * math.sin(a)) for a in np.linspace(a0, 3 * math.pi - a0, n + 1)]


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    allcs = cs_union([b.cs for b in BLOCKS])
    eave_path = max(allcs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(allcs, 10.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    st = stacked_shells(BLOCKS, [o for o in OPENINGS], [S1], t=3.0, corners="carrington", clear=[lip_keep(allcs, 3.0, ZF, 1.2)],
                        siding=_walls, prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=undress)
    kit.add("WALLS-1", "Clapboard", st["shells"][0], group="walls")
    kit.add("JOINT", "Clapboard", st["rings"][0], group="walls")
    walls2 = st["shells"][1] + CO.ledge(eave_path, ZE, LEDGE)
    kit.add("WALLS-2", "Clapboard", walls2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    kit.add("FOUNDATION", "Brick", foundation(BLOCKS, 0.0, ZF, style="carrington"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Trim", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the hipped roof (upside down) with its dormers, the widow's walk, the stacks
    mans, mtex, inner = R.mansard(MAIN.pts, ROOF, t=2.6, tex=SLATE)
    mk, mf = _addins(kit, MAIN, ADDINS, ROOF, Z_ADD, G.addin_carrington(), "ADDIN")
    C = SE.crest_ring(MAIN.pts, D_TOP, ZR1, D_TOP - inner(ZR1), CREST_COURSE, CREST_CROWN)
    kit.add("ROOF", "Slate", (mans + (mtex - mf)) - mk - C["groove"] - walls2, P=print_flip(), group="roof")
    kit.add("CREST", "Trim", C["solid"], P=print_flip(), change=C["change"], group="roof", render=C["zones"])
    zdeck = C["z_top"]
    pads = union([box([x - 7.0, y - 4.6, zdeck - 0.6], [x + 7.0, y + 4.6, zdeck + 1]) for x, y in CHIMS])
    kit.add("ROOF-deck", "Slate", _deck_plate(C, zdeck) - pads, group="roof")
    for k, (x, y) in enumerate(CHIMS):
        kit.add(f"CHIMNEY-{k}", "Brick", G.chimney_carrington(12.0, 7.0, 30.0).translate([x, y, zdeck - 0.6]), key="CHIMNEY", group="roof")
    walk = []
    for i, seg, A, L in SE.cresting_strips(C["path"], zdeck, C["rail"], G.fence_carrington_balustrade, 6.0):
        n = f"CREST-walk-{i}"
        kit.add(n, "Trim", seg, P=inv34(A), key=f"CREST-walk-{round(L, 1)}", group="roof")
        walk.append(n)
    print("roof", round(time.time() - t0, 1))

    # --- the bow's deck at the eave, from the cornice's crown back to the roof's foot, a
    # balustrade round it
    Pc = EAVE["layers"][-1]["P"]
    mfoot = M.hull_points([(x, y, z) for x, y in R.offset_path(MAIN.pts, DK + 0.7) for z in (ZW - 1, ZW + 40)])
    bd = slab(offset(BOW.cs, Pc + 0.2), ZW, ZW + 1.2) - mfoot
    bd = max(bd.decompose(), key=lambda m_: m_.volume())
    kit.add("BOW-deck", "Slate", bd, group="bow")
    bow_rails = []
    for i, seg, A, L in SE.cresting_strips(BOW.pts, ZW + 1.2, Pc - 1.2, G.fence_carrington_balustrade, 5.2):
        seg = seg - mfoot
        if not seg.is_empty() and seg.volume() > 3.0:
            for j, piece in enumerate(seg.decompose()):
                if piece.volume() > 3.0:
                    n = f"BOW-rail-{i}{chr(97 + j)}"
                    kit.add(n, "Trim", piece, P=inv34(A), group="bow")
                    bow_rails.append(n)
    print("bow", round(time.time() - t0, 1))

    # --- the colossal portico round the bow: six Ionic columns, an architrave, a dentilled
    # cornice, a planked floor, a balustrade on its roof
    pts = _arc(RP)
    Ls = [float(np.linalg.norm(np.subtract(pts[i + 1], pts[i]))) for i in range(len(pts) - 1)]
    turn = 2 * math.asin(Ls[0] / (2 * RP))              # the polygon turns this much at each corner
    c = INS * math.tan(turn / 2)
    runs = []
    for i in range(len(pts) - 1):
        L = Ls[i]
        posts = [10.0 if i == 0 else c, L - 10.0 if i == len(pts) - 2 else L - c]     # (the end columns clear the storey cornice)
        runs.append(dict(a=pts[i], b=pts[i + 1], posts=posts))
    H_floor = ZF
    post_h = ZE - 2.6 - H_floor - 5.2
    P = FT.porch_turned(pts, runs, H_floor, post_h, steps_at=[(2, Ls[2] / 2, 16.0)], inset=INS, rail=None, beam=3.2,
                        post="carringtonionic", arcade="festoonarchitrave", skirt="carrington", pier_tex="brick",
                        roof_edge="dentilegg", planks=dict(pitch=1.5, border=1.8), drop=3.0, top=True)
    where = []
    for r in runs:
        f = Facade(np.array(r["a"]), np.array(r["b"]), 0.0)
        for u in r["posts"]:
            p = f.p0 + f.u * u - f.n * INS
            if not any(np.allclose(p, q, atol=0.05) for q in where):
                where.append(p)
    z0r = H_floor + post_h
    P["top"] = P["top"] + union([box([p[0] - 0.5, p[1] - 0.5, z0r - 0.6], [p[0] + 0.5, p[1] + 0.5, z0r + 0.6]) for p in where])
    fkeep = slab(offset(allcs, 1.7), -1, ZF + 1.3)
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    deck_ = P["deck"] - fkeep
    kit.add("PORCH-deck", "Brick", deck_, P=print_flip(), group="portico", render=FT.plank_zones(deck_, H_floor, "Planks", "Brick"))
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=300) for b in BLOCKS])
    ptop = FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_keep, "Trim", "Trim", tin_col="Slate", tin="flat",
                            group="portico")["ptop"]
    parts = {p_.name: p_ for p_ in kit.parts}
    parts["PORCH-top"].solid = parts["PORCH-top"].solid - parts["FOUNDATION"].solid
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Brick", sm.transform(A) - fkeep - parts["PORCH-top"].solid, group="portico")
    pkeep = bld_keep + slab(offset(allcs, Pc + 0.4), ZE - 0.4, 999)
    prails = _strips(kit, "PORCH-rail", _arc(RP - 2.2, y_cut=-1.4), ptop, pkeep, G.fence_carrington_balustrade, 6.0,
                     "Trim", "portico", end=1.6)
    print("portico", round(time.time() - t0, 1))

    # --- the curved iron balcony inside the portico, on the storey cornice
    zb = S1 + RJ + 1.22                          # (the deck rests on the storey cornice's crown)
    rb = RP - INS / math.cos(turn / 2) - 2.5 - 1.4
    breg = poly(_arc(rb, y_cut=0.0)) - offset(allcs, 0.6)
    breg = max(breg.decompose(), key=lambda c_: c_.area())
    cons = []
    for i in range(len(_arc(rb)) - 1):
        a_, b_ = np.array(_arc(rb)[i]), np.array(_arc(rb)[i + 1])
        m_ = (a_ + b_) / 2
        d_ = m_ - np.array(BC)
        ang = math.atan2(d_[1], d_[0]) + math.pi
        p_ = m_ - d_ / np.linalg.norm(d_) * 0.2
        if p_[1] < -4.0:
            cons.append((p_[0], p_[1], ang))
    bal = G.balcony_carrington(breg, zb, consoles=cons) - union([p_.solid for p_ in kit.parts if p_.name.startswith("WIN-B") or
                                                                 p_.name.startswith("WIN-palladian") or p_.name.startswith("CORNICE-J")])
    kit.add("BALCONY", "Iron", bal, P=print_flip(), group="portico")
    bkeep = union([b.solid(grow=0.8, dz0=-20, dz1=300) for b in BLOCKS]) + ins_keep
    brails = _strips(kit, "BALCONY-rail", _arc(rb - 0.6, y_cut=0.0), zb, bkeep, SE.printable(G.fence_carrington_iron), 9.0,
                     "Iron", "portico", end=0.8)
    e, u = MAIN.locate(XC, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Brick", FT.steps(14.0, ZF - 0.6, 4).transform(A), group="portico")
    print("balcony", round(time.time() - t0, 1))

    for n in walk:
        FT.key_into(kit, n, ["CREST"], (0, 0, -1), depth=0.6)
    for n in bow_rails:
        FT.key_into(kit, n, ["BOW-deck"], (0, 0, -1), depth=0.6)
    for n in prails:
        FT.key_into(kit, n, ["PORCH-top"], (0, 0, -1), depth=0.6)
    for n in brails:
        FT.key_into(kit, n, ["BALCONY"], (0, 0, -1), depth=0.6)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "carrington")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:60]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "carrington.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Addins"))
