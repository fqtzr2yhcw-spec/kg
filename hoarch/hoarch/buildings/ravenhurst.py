"""The Ravenhurst -- an original HO-scale (1:87.1) castellated Gothic Revival villa, 1868: the tenth and
last of the grand batch (houses 91 to 100, hoarch.grand).

A Hudson River castle in the manner of A. J. Davis. A ground storey of grey squared rubble
brought to course with little snecks, an upper storey of knapped flint chequered with limestone
squares, stepped angle buttresses at every corner. Every roof is flat behind battlements pierced
with cross loops. A square tower on the front-west corner rises two stages over the roof to its
own battlements, with a pepperpot turret under a slate spire at each of its corners and a great
three-light window of panel tracery in its face. A canted bay on the east side carries the
battlements round it. Tudor-arched windows of two cusped lights under square labels below,
single traceried lights above; the oak door with its strap hinges and wicket grille stands in a
four-centred arch of two orders under a label, shields in its spandrels. A porch of clustered
piers and Tudor arches carries a battlemented roof; clustered chimneys of twisted brick rise from
the roof.

- Storey joint: a limestone dogtooth course, a crimson frieze of quatrefoils in square panels,
  a limestone bevel.
- Eave: dogtooth, a crimson corbel table of little arches on grotesque heads, Gothic corbels, a
  limestone torus; the tower the same on its own scale.

usage: python3 -m hoarch.buildings.ravenhurst [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import Facade, box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, grand as G, openings as O
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, foundation, lip_keep, stacked_shells

NAME = "The Ravenhurst"
COLORS = {"Granite": "#8E8C84", "Flint": "#6E7074", "Limestone": "#D9D1BD", "Crimson": "#7B2228", "Lead": "#5C6064",
          "Brick": "#8C4632", "Slate": "#3C4450", "Planks": "#6B4E36", "Windows_Doors": "#D9D1BD"}
RENDER_MAT = {"Granite": "granite", "Flint": "flint", "Limestone": "stone", "Crimson": "accent", "Lead": "roof",
              "Brick": "brick", "Slate": "slate", "Planks": "planks", "Windows_Doors": "stone", "Sash": "sash",
              "Door": "door", "Glass": "glass"}
PALETTE = {"granite": ["#8E8C84", 0.9, 0.0], "flint": ["#6E7074", 0.7, 0.05], "stone": ["#D9D1BD", 0.7, 0.0],
           "accent": ["#7B2228", 0.6, 0.0], "roof": ["#5C6064", 0.6, 0.25], "brick": ["#8C4632", 0.85, 0.0],
           "slate": ["#3C4450", 0.7, 0.0], "planks": ["#6B4E36", 0.75, 0.0], "sash": ["#2A2C2E", 0.45, 0.0],
           "door": ["#4A3020", 0.5, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Ravenhurst)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="dogtoothleaf", role="Limestone"),
    dict(kind="frieze", h=5.2, b=1.2, orn="panelquatrefoils", role="Crimson"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="bevel", role="Limestone")])
EAVE = dict(pitch=6.0, margin=3.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="dogtoothleaf", role="Limestone"),
    dict(kind="frieze", h=6.4, b=1.2, orn="grotesques", role="Crimson"),
    dict(kind="bed", h=3.2, b=1.4, P=7.0, role="Limestone", brackets=dict(style="corbelhead", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.6, b=1.4, P=7.8, orn="torus", role="Limestone")])
TOWER_C = dict(pitch=5.6, margin=1.6, layers=[
    dict(kind="frieze", h=4.8, b=1.2, orn="grotesques", role="Crimson"),
    dict(kind="bed", h=2.6, b=1.4, P=5.8, role="Limestone", brackets=dict(style="corbelhead", t=1.6, reach=0.5)),
    dict(kind="crown", h=2.4, b=1.4, P=6.4, orn="torus", role="Limestone")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 8.0
S1 = ZF + 36.0
ZE = S1 + RJ + 34.0
ZW = ZE + HE
DK = EAVE["layers"][-1]["P"] + 0.2
ZT = ZW + 34.0                                   # the tower's two stages over the roof
ZTW = ZT + CO.band_height(TOWER_C)
DT = TOWER_C["layers"][-1]["P"] + 0.2
G.RV_LEVELS.update(hi=S1 + RJ - ZF)
V1, V2 = 6.0, S1 + RJ - ZF + 3.0
BATT_H = 6.0

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 150.0, 94.0
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
TOWER = Block("tower", [(-10.0, -14.0), (26.0, -14.0), (26.0, 22.0), (-10.0, 22.0)], ZF, ZTW)
BAY = Block("bay", [(X1 - 3.0, 40.0), (X1, 40.0), (X1 + 8.0, 46.0), (X1 + 8.0, 66.0), (X1, 72.0), (X1 - 3.0, 72.0)], ZF, ZW)
BLOCKS = [MAIN, TOWER, BAY]
DOOR_X = 84.0
CHIMS = [(64.0, 74.0), (118.0, 30.0)]
BART_R = 4.2


def _walls(f, b, reg):
    """Squared rubble below the joint, flint chequer above; nothing in the cornice bands."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    if b is TOWER:
        reg = reg - rect(-1, ZT - b.z0 - LEDGE - 0.6, f.L + 1, 999)
    lo = reg ^ rect(-1, -100, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, S1 + RJ - b.z0, f.L + 1, 999)
    out = []
    if not lo.is_empty():
        out.append(G.rubble_coursed(lo, datum=0.0, seed=23 + int(f.L) % 11))
    if not hi.is_empty():
        out.append(G.flint_chequer(hi, datum=S1 + RJ - b.z0 + 0.2, seed=29 + int(f.L) % 11))
    return union(out) if out else M()


def _openings():
    L = []

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    lo, up = G.window_ravenhurst_ground(), G.window_ravenhurst_upper()
    add(MAIN, DOOR_X, 0.0, 1.2, G.door_ravenhurst(), "front-door", "door")
    for x in (40.0, 56.0, 112.0, 130.0):
        add(MAIN, x, 0.0, V1, lo, f"S{x:.0f}-1")
    for x in (40.0, 56.0, DOOR_X, 112.0, 130.0):
        add(MAIN, x, 0.0, V2, up, f"S{x:.0f}-2")
    for y in (38.0, 60.0, 80.0):
        add(MAIN, 0.0, y, V1, lo, f"W{y:.0f}-1")
        add(MAIN, 0.0, y, V2, up, f"W{y:.0f}-2")
    for y in (20.0, 86.0):
        add(MAIN, X1, y, V1, lo, f"E{y:.0f}-1")
        add(MAIN, X1, y, V2, up, f"E{y:.0f}-2")
    add(BAY, X1 + 8.0, 56.0, V1, lo, "BAY-1")
    add(BAY, X1 + 8.0, 56.0, V2, up, "BAY-2")
    for x in (22.0, 48.0, 102.0, 128.0):
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
    for x in (22.0, 48.0, 75.0, 102.0, 128.0):
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, 75.0, Y1, 1.2, G.door_ravenhurst(w=9.0, h=19.0, back=True), "back-door", "door")
    add(TOWER, 8.0, -14.0, V1, lo, "T-S1")
    add(TOWER, 8.0, -14.0, V2, up, "T-S2")
    add(TOWER, 8.0, -14.0, ZW - ZF + 3.0, G.window_ravenhurst_great(), "T-great")
    add(TOWER, -10.0, 4.0, V1, lo, "T-W1")
    add(TOWER, -10.0, 4.0, V2, up, "T-W2")
    add(TOWER, -10.0, 4.0, ZW - ZF + 6.0, up, "T-W3")
    add(TOWER, 8.0, 22.0, ZW - ZF + 6.0, up, "T-N3")
    return L


OPENINGS = _openings()


def _strips(kit, tag, chain, z, keep, fence, h, colour, group, end=0.7, t=1.0):
    """Flat-printed strips (battlements) along a chain, standing at z, cut by ``keep``."""
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


def _ring(cs, d):
    pts = [tuple(p) for p in max(offset(cs, d).to_polygons(), key=lambda L_: abs(poly(L_).area()))]
    return pts + [pts[0]]


def _deck(dcs, z, pitch=5.2):
    """A flat lead roof: a 1.0 mm sheet with standing seams 0.4 mm proud."""
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x0, y - 0.25, x1, y + 0.25) for y in np.arange(y0 + pitch / 2, y1, pitch)]) ^ offset(dcs, -2.6)
    return slab(dcs, z - 1.0, z) + slab(seams, z - 0.01, z + 0.4)


def _bartizans():
    """The four pepperpot turrets on the tower's top corners, standing on its deck, in world
    coords: [(solid, A, spire foot z)], A placing each turret's local frame (it prints upright
    in that frame)."""
    out = []
    xs, ys = (TOWER.pts[0][0], TOWER.pts[1][0]), (TOWER.pts[0][1], TOWER.pts[2][1])
    for (cx, sx) in ((xs[0], -1), (xs[1], 1)):
        for (cy, sy) in ((ys[0], -1), (ys[1], 1)):
            b, zt = G.bartizan_ravenhurst(BART_R, 12.0, 9.0)
            A = np.array([[1.0, 0.0, 0.0, cx + sx * 0.8], [0.0, 1.0, 0.0, cy + sy * 0.8], [0.0, 0.0, 1.0, ZTW + 1.0]])
            out.append((b.transform(A), A, zt + ZTW + 1.0))
    return out


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    allcs = cs_union([b.cs for b in BLOCKS])
    eave_path = max(allcs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(allcs, 10.0), ZE - LEDGE - 0.6, ZW + 0.01), slab(offset(TOWER.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="ravenhurst", clear=[lip_keep(allcs, 3.0, ZF, 1.2)],
                        siding=_walls, prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=undress)
    kit.add("WALLS-1", "Granite", st["shells"][0], group="walls")
    kit.add("JOINT", "Flint", st["rings"][0], group="walls")
    ledges = CO.ledge(eave_path, ZE, LEDGE) + CO.ledge(TOWER.pts, ZT, LEDGE)
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(allcs, 3.0, S1 + RJ)
    walls2 = st["shells"][1] + ledges + tring
    kit.add("WALLS-2", "Flint", walls2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(TOWER.pts, ZT, TOWER_C)
    CO.add_level(kit, rings, "CORNICE-T", "tower")
    kit.add("FOUNDATION", "Granite", foundation(BLOCKS, 0.0, ZF, style="quatrefoilplinth"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Limestone", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the pepperpot turrets on the tower's corners, standing on its deck
    barts = _bartizans()
    bkeep = union([b_ for b_, _, _ in barts])
    for k, (b_, A, ztop) in enumerate(barts):
        solid = b_
        h_change = round((ztop - A[2, 3]) / 0.2) * 0.2
        kit.add(f"BARTIZAN-{k}", "Limestone", solid, P=inv34(A), key="BARTIZAN", change=(h_change, "Slate"), group="tower",
                render=[("Limestone", solid ^ box([-1e3, -1e3, -1e3], [1e3, 1e3, ztop])), ("Slate", solid - box([-1e3, -1e3, -1e3], [1e3, 1e3, ztop]))])
    print("bartizans", round(time.time() - t0, 1))

    # --- the flat roofs: a lead deck over the house inside the battlements, the clustered stacks;
    # the tower's own deck and battlements
    tower_hug = TOWER.solid(grow=0.3, dz0=-1, dz1=400)
    zdeck = ZW + 1.0
    pads = union([box([x - 6.2, y - 3.6, zdeck - 0.5], [x + 6.2, y + 3.6, zdeck + 1]) for x, y in CHIMS])
    kit.add("ROOF-deck", "Lead", _deck(offset(allcs, DK - 1.4), zdeck) - tower_hug - pads - walls2, group="roof")
    for k, (x, y) in enumerate(CHIMS):
        kit.add(f"CHIMNEY-{k}", "Brick", G.chimney_ravenhurst(11.0, 6.0, 30.0).translate([x, y, zdeck - 0.5]), key="CHIMNEY", group="roof")
    tzone = slab(offset(TOWER.cs, DK + 1.2), ZW - 1, 999)
    batt = _strips(kit, "ROOF-batt", _ring(allcs, DK - 2.6), zdeck, tzone, G.fence_ravenhurst_battlements, BATT_H, "Limestone", "roof")
    zt = ZTW + 1.0
    kit.add("TOWER-deck", "Lead", _deck(offset(TOWER.cs, DT - 1.4), zt, pitch=4.4) - bkeep, group="tower")
    tbatt = _strips(kit, "TOWER-batt", _ring(TOWER.cs, DT - 2.6), zt, union([G.bartizan_ravenhurst(BART_R + 0.4, 12.0, 9.0)[0].transform(A) for _, A, _ in barts]),
                    G.fence_ravenhurst_battlements, BATT_H - 0.6, "Limestone", "tower", end=1.0)
    print("roofs", round(time.time() - t0, 1))

    # --- the porch before the door: clustered piers, Tudor arches, a battlemented flat roof
    x0, x1, FY = DOOR_X - 18.0, DOOR_X + 18.0, -15.0
    pts = [(x0, -1.4), (x0, FY), (x1, FY), (x1, -1.4)]
    Ls, Lf = -1.4 - FY, x1 - x0
    ins = 2.2
    runs = [dict(a=(x0, -1.4), b=(x0, FY), posts=[3.0, Ls - ins]),
            dict(a=(x0, FY), b=(x1, FY), posts=[ins, Lf / 2 - 4.6, Lf / 2 + 4.6, Lf - ins]),
            dict(a=(x1, FY), b=(x1, -1.4), posts=[ins, Ls - 3.0])]
    H_floor = ZF - 1.0
    post_h = S1 - 2.4 - H_floor - 5.0
    P = FT.porch_turned(pts, runs, H_floor, post_h, steps_at=[(1, Lf / 2, 8.0)], inset=ins, rail=None, beam=2.6,
                        post="clusterpier", arcade="tudorarch", skirt="ravenhurst", pier_tex="stone", roof_edge="crenelfascia",
                        planks=dict(pitch=1.6, border=1.8), drop=8.0, top=True)
    where = []
    for r in runs:
        f = Facade(np.array(r["a"]), np.array(r["b"]), 0.0)
        for u in r["posts"]:
            p = f.p0 + f.u * u - f.n * ins
            if not any(np.allclose(p, q, atol=0.05) for q in where):
                where.append(p)
    z0r = H_floor + post_h
    P["top"] = P["top"] + union([box([p[0] - 0.5, p[1] - 0.5, z0r - 0.6], [p[0] + 0.5, p[1] + 0.5, z0r + 0.6]) for p in where])
    fkeep = slab(offset(allcs, 1.7), -1, ZF + 1.3)
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    deck_ = P["deck"] - fkeep
    kit.add("PORCH-deck", "Granite", deck_, P=print_flip(), group="porch", render=FT.plank_zones(deck_, H_floor, "Planks", "Granite"))
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=300) for b in BLOCKS])
    ptop = FT.add_porch_top(kit, "PORCH", P, bld_keep + ins_keep, "Limestone", "Limestone", tin_col="Lead", tin="flat")["ptop"]
    parts = {p_.name: p_ for p_ in kit.parts}
    parts["PORCH-top"].solid = parts["PORCH-top"].solid - parts["FOUNDATION"].solid
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORCH-steps-{k}", "Granite", sm.transform(A) - fkeep - parts["PORCH-top"].solid, group="porch")
    pkeep = bld_keep + slab(offset(allcs, 4.8), S1 - 0.2, 999)
    chain = [(x0 + 0.9, -1.4), (x0 + 0.9, FY + 0.9), (x1 - 0.9, FY + 0.9), (x1 - 0.9, -1.4)]
    pbatt = _strips(kit, "PORCH-batt", chain, ptop, pkeep, G.fence_ravenhurst_battlements, 5.0, "Limestone", "porch", end=0.6)
    e, u = MAIN.locate(75.0, Y1)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Granite", FT.steps(13.0, ZF - 0.6, 4).transform(A), group="porch")
    print("porch", round(time.time() - t0, 1))

    for n in batt:
        FT.key_into(kit, n, ["ROOF-deck"], (0, 0, -1), depth=0.6)
    for n in tbatt:
        FT.key_into(kit, n, ["TOWER-deck"], (0, 0, -1), depth=0.6)
    for n in pbatt:
        FT.key_into(kit, n, ["PORCH-top"], (0, 0, -1), depth=0.6)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "ravenhurst")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:60]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "ravenhurst.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
