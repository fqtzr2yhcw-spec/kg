"""The Foscari -- an original HO-scale (1:87.1) Venetian Gothic Revival palazzo, 1876: the eighth of the
grand batch (houses 91 to 100, hoarch.grand).

A shipping magnate's palazzo after the Ca' d'Oro and the Fondaco dei Turchi. A ground storey of
white Istrian ashlar in tall and short courses on a plinth with a saw-tooth water table, a piano
nobile of rose stucco patterned in the Doge's Palace lozenge diaper, twisted rope colonnettes up
every corner. Two corner towers (torreselle) frame the front and rise a stage over the roof to
flat tops edged with Venetian merlons and pinnacles. Between them an open loggia of cusped ogee
arches on slender columns with leafy basket capitals carries a balcony, and over it the piano
nobile's polifora: five cusped ogee lights on colonnettes under a band of quatrefoils in rings,
all in a frame of saw-tooth dentils. Every other window is an ogee or a pointed light in a
dentil frame, patere (carved roundels) in its spandrels, the upper ones on balconettes. The flat
roof is edged with merlons; on it stand a timber altana (the Venetian roof terrace) and three
funnel chimneys.

- Ground storey: pointed lights behind iron grilles under saw-tooth hoods, a patera over each.
  Piano nobile: cusped ogee lights in dentil rectangles on balconettes. Towers' top stages:
  biforas (two ogee lights and a quatrefoil oculus).
- Storey joint: an Istrian dentello course, a Verona-red frieze of patere and formelle (panels
  with a cross between leaves), an Istrian ovolo.
- Eave: dentello, a gilt corbel table of hanging cusped arches, stepped mensola corbels, an
  Istrian cyma reversa; the towers the same on a smaller scale.

usage: python3 -m hoarch.buildings.foscari [check] [export]
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

NAME = "The Foscari"
COLORS = {"Istrian": "#E9E3D4", "Rose": "#D49C8B", "Verona": "#A3443A", "Gilt": "#C9A24E", "Lead": "#6B6F72",
          "Brick": "#A65A3E", "Larch": "#7C5B3B", "Planks": "#6E4E33", "Windows_Doors": "#E9E3D4"}
RENDER_MAT = {"Istrian": "stone", "Rose": "stucco", "Verona": "accent", "Gilt": "gilt", "Lead": "roof", "Brick": "brick",
              "Larch": "wood", "Planks": "planks", "Windows_Doors": "stone", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"stone": ["#E9E3D4", 0.65, 0.0], "stucco": ["#D49C8B", 0.85, 0.0], "accent": ["#A3443A", 0.6, 0.0],
           "gilt": ["#C9A24E", 0.35, 0.6], "roof": ["#6B6F72", 0.6, 0.25], "brick": ["#A65A3E", 0.85, 0.0],
           "wood": ["#7C5B3B", 0.7, 0.0], "planks": ["#6E4E33", 0.75, 0.0], "sash": ["#2C3A36", 0.45, 0.0],
           "door": ["#4A2E22", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Foscari)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.6, b=1.0, orn="dentello", role="Istrian"),
    dict(kind="frieze", h=5.6, b=1.2, orn="pateraeformelle", role="Verona"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="ovolo", role="Istrian")])
EAVE = dict(pitch=6.0, margin=3.0, layers=[
    dict(kind="course", h=1.6, b=1.0, orn="dentello", role="Istrian"),
    dict(kind="frieze", h=6.4, b=1.2, orn="archetti", role="Gilt"),
    dict(kind="bed", h=3.2, b=1.4, P=7.0, role="Istrian", brackets=dict(style="mensola", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.6, b=1.4, P=7.8, orn="reverse", role="Istrian")])
TOWER_C = dict(pitch=5.4, margin=1.6, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="archetti", role="Gilt"),
    dict(kind="bed", h=2.6, b=1.4, P=5.8, role="Istrian", brackets=dict(style="mensola", t=1.6, reach=0.5)),
    dict(kind="crown", h=2.4, b=1.4, P=6.4, orn="reverse", role="Istrian")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 6.0
S1 = ZF + 36.0
ZE = S1 + RJ + 40.0
ZW = ZE + HE
DK = EAVE["layers"][-1]["P"] + 0.2
ZT = ZW + 26.0                                   # the towers' top stage over the roof
ZTW = ZT + CO.band_height(TOWER_C)
DT = TOWER_C["layers"][-1]["P"] + 0.2
G.FS_LEVELS.update(hi=S1 + RJ - ZF)
V1, V2 = 5.0, S1 + RJ - ZF + 6.0
MERLON_H = 6.0

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 148.0, 92.0
XC = X1 / 2
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
TW = Block("tower-w", [(0.0, -8.0), (32.0, -8.0), (32.0, 24.0), (0.0, 24.0)], ZF, ZTW)
TE = Block("tower-e", [(116.0, -8.0), (X1, -8.0), (X1, 24.0), (116.0, 24.0)], ZF, ZTW)
TOWERS = [TW, TE]
BLOCKS = [MAIN, TW, TE]
CHIMS = [(14.0, 54.0), (134.0, 54.0), (XC, 84.0)]
ALTANA = (XC, 50.0, 40.0, 26.0, 9.0)             # centre x, y, width, depth, post height


def _walls(f, b, reg):
    """Istrian ashlar below the joint, diapered rose stucco above; nothing in the cornice bands."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    if b in TOWERS:
        reg = reg - rect(-1, ZT - b.z0 - LEDGE - 0.6, f.L + 1, 999)
    lo = reg ^ rect(-1, -100, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, S1 + RJ - b.z0, f.L + 1, 999)
    out = []
    if not lo.is_empty():
        out.append(G.stone_istrian(lo, datum=0.0))
    if not hi.is_empty():
        out.append(G.stucco_diaper(hi, datum=S1 + RJ - b.z0 + 0.2))
    return union(out) if out else M()


def _openings():
    L = []

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    lo, up = G.window_foscari_ground(), G.window_foscari_upper()
    bif = G.window_foscari_bifora()
    add(MAIN, XC, 0.0, 1.2, G.door_foscari(h=22.0), "front-door", "door")
    for x in (50.0, 98.0):
        add(MAIN, x, 0.0, V1, lo, f"S{x:.0f}-1")
    for x in (46.0, 102.0):
        add(MAIN, x, 0.0, V2, up, f"S{x:.0f}-2")
    add(MAIN, XC, 0.0, V2, G.window_foscari_polifora(), "polifora")
    for T, xf, side, tag in ((TW, 16.0, 0.0, "TW"), (TE, 132.0, X1, "TE")):
        add(T, xf, -8.0, V1, lo, f"{tag}-S1")
        add(T, xf, -8.0, V2, up, f"{tag}-S2")
        add(T, xf, -8.0, ZW - ZF + 3.4, bif, f"{tag}-S3")
        add(T, side, 8.0, V1, lo, f"{tag}-X1")
        add(T, side, 8.0, V2, up, f"{tag}-X2")
        add(T, side, 8.0, ZW - ZF + 3.4, bif, f"{tag}-X3")
    for x_, tag in ((0.0, "W"), (X1, "E")):
        for y in (40.0, 62.0, 82.0):
            add(MAIN, x_, y, V1, lo, f"{tag}{y:.0f}-1")
            add(MAIN, x_, y, V2, up, f"{tag}{y:.0f}-2")
    for x in (20.0, 44.0, 104.0, 128.0):
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, XC, Y1, 1.2, G.door_foscari(w=10.0, h=21.0, back=True), "back-door", "door")
    add(MAIN, XC, Y1, V2, G.window_foscari_polifora(n=3), "polifora-back")
    return L


OPENINGS = _openings()


def _strips(kit, tag, ring, z, keep, fence, h, colour, group, end=0.7, t=1.0):
    """Flat-printed strips (merlons, a balcony front) along every edge of a closed or open chain,
    standing at z, cut by ``keep``; returns their names."""
    names = []
    for i in range(len(ring) - 1):
        f = Facade(np.array(ring[i]), np.array(ring[i + 1]), 0.0)
        if f.L < 2 * end + 3.0:
            continue
        cs = fence(f.L - 2 * end, h).translate([end, 0.0])
        strip = M.extrude(cs, t).translate([0, 0, -t / 2])
        A = f.A.copy()
        A[:, 3] = f.world(0, 0, 0) + np.array([0, 0, z - 0.01])
        seg = strip.transform(A) - keep
        for j, piece in enumerate(seg.decompose()):
            if piece.volume() > 2.0:
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
    seams = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + pitch / 2, x1, pitch)]) ^ offset(dcs, -2.6)
    return slab(dcs, z - 1.0, z) + slab(seams, z - 0.01, z + 0.4)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    allcs = cs_union([b.cs for b in BLOCKS])
    eave_path = max(allcs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(allcs, 10.0), ZE - LEDGE - 0.6, ZW + 0.01)] + \
        [slab(offset(T.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01) for T in TOWERS]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="foscari", clear=[lip_keep(allcs, 3.0, ZF, 1.2)],
                        siding=_walls, prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=undress)
    kit.add("WALLS-1", "Istrian", st["shells"][0], group="walls")
    kit.add("JOINT", "Rose", st["rings"][0], group="walls")
    ledges = CO.ledge(eave_path, ZE, LEDGE) + union([CO.ledge(T.pts, ZT, LEDGE) for T in TOWERS])
    # inside the house the towers' walls rise from the joint, so their stages over the roof bear
    # all round
    trings = union([slab((offset(T.cs, -0.05) - offset(T.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RJ, ZW + 1.2) for T in TOWERS])
    trings = trings - lip_keep(allcs, 3.0, S1 + RJ)
    walls2 = st["shells"][1] + ledges + trings
    kit.add("WALLS-2", "Rose", walls2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    for T, tag in ((TW, "W"), (TE, "E")):
        rings, _ = CO.level(T.pts, ZT, TOWER_C)
        CO.add_level(kit, rings, f"CORNICE-T{tag}", "towers")
    kit.add("FOUNDATION", "Istrian", foundation(BLOCKS, 0.0, ZF, style="foscari"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Istrian", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the flat roof: a lead deck over the walls and the crown, merlons round it, the altana,
    # funnel chimneys
    tower_hug = union([T.solid(grow=0.3, dz0=-1, dz1=400) for T in TOWERS])
    zdeck = ZW + 1.0
    ax, ay, aw, ad, ah = ALTANA
    alt = G.altana_foscari(aw, ad, ah).translate([ax, ay, zdeck])
    feet = []
    for x in (ax - aw / 2 + 1.4, ax, ax + aw / 2 - 1.4):
        for y in (ay - ad / 2 + 1.4, ay + ad / 2 - 1.4):
            feet.append(box([x - 0.6, y - 0.6, zdeck - 0.9], [x + 0.6, y + 0.6, zdeck + 1.0]))
            feet.append(box([x - 0.9, y - 0.9, zdeck], [x + 0.9, y + 0.9, zdeck + 1.0]))
    pads = union([box([x - 4.4, y - 4.4, zdeck - 0.5], [x + 4.4, y + 4.4, zdeck + 1]) for x, y in CHIMS])
    deck = _deck(offset(allcs, DK - 1.4), zdeck)
    kit.add("ROOF-deck", "Lead", deck - tower_hug - pads - union(feet) - walls2, group="roof")
    for k, (x, y) in enumerate(CHIMS):
        kit.add(f"CHIMNEY-{k}", "Brick", G.chimney_foscari(6.0, 28.0).translate([x, y, zdeck - 0.5]), key="CHIMNEY", group="roof")
    kit.add("ALTANA", "Larch", alt, P=print_flip(), group="roof")
    zap = zdeck + ah + 1.2
    ring_a = [(ax - aw / 2 + 0.6, ay - ad / 2 + 0.6), (ax + aw / 2 - 0.6, ay - ad / 2 + 0.6), (ax + aw / 2 - 0.6, ay + ad / 2 - 0.6),
              (ax - aw / 2 + 0.6, ay + ad / 2 - 0.6), (ax - aw / 2 + 0.6, ay - ad / 2 + 0.6)]
    arails = _strips(kit, "ALTANA-rail", ring_a, zap, M(), G.fence_foscari_altana, 5.0, "Larch", "roof", end=0.8, t=0.8)
    tzone = union([slab(offset(T.cs, DK + 1.2), ZW - 1, 999) for T in TOWERS])
    merli = _strips(kit, "ROOF-merli", _ring(allcs, DK - 2.6), zdeck, tzone, G.fence_foscari_merli, MERLON_H, "Istrian", "roof")
    print("roof", round(time.time() - t0, 1))

    # --- the towers' flat tops: a lead deck, a pinnacle at every corner, merlons between
    tmerli = []
    for T, tag in ((TW, "W"), (TE, "E")):
        zt = ZTW + 1.0
        tdeck = _deck(offset(T.cs, DT - 1.4), zt, pitch=4.4)
        ring = _ring(T.cs, DT - 2.6)
        pins = union([G.finial_foscari(9.0).translate([x, y, zt - 0.01]) for x, y in ring[:-1]])
        # the pinnacles print with the deck: lead up to the seams' tops, one change to Istrian
        kit.add(f"TOWER-{tag}-deck", "Lead", tdeck + pins, change=(1.4, "Istrian"), group="towers",
                render=[("Lead", tdeck), ("Istrian", pins)])
        tmerli += [(n, f"TOWER-{tag}-deck") for n in
                   _strips(kit, f"TOWER-{tag}-merli", ring, zt, M(), G.fence_foscari_merli, MERLON_H - 1.0, "Istrian", "towers",
                           end=1.7)]
    print("towers", round(time.time() - t0, 1))

    # --- the loggia between the towers: cusped ogee arches on Venetian columns, a planked floor, a
    # balcony front on its flat roof
    FY = -8.0
    xa, xb = TW.pts[1][0] + 1.4, TE.pts[0][0] - 1.4
    pts = [(xa, -1.4), (xa, FY), (xb, FY), (xb, -1.4)]
    Lf = xb - xa
    ud = XC - xa
    nb = 7
    bay = (Lf - 3.4) / nb
    posts = [1.7 + bay * k for k in range(nb + 1)]
    runs = [dict(a=(xa, FY), b=(xb, FY), posts=posts)]
    H_floor = ZF - 1.0
    post_h = S1 - 2.4 - H_floor - 5.0
    P = FT.porch_turned(pts, runs, H_floor, post_h, steps_at=[(0, ud, 8.0)], planks=dict(pitch=1.6, border=1.8),
                        post="foscari", rail="foscaritwist", arcade="venetianogee", skirt="foscari", pier_tex="stone",
                        roof_edge="dentello", drop=9.0, top=True)
    f = Facade(np.array(runs[0]["a"]), np.array(runs[0]["b"]), 0.0)
    where = [f.p0 + f.u * u - f.n * 1.6 for u in posts]
    z0r = H_floor + post_h
    P["top"] = P["top"] + union([box([p[0] - 0.5, p[1] - 0.5, z0r - 0.6], [p[0] + 0.5, p[1] + 0.5, z0r + 0.6]) for p in where])
    fkeep = slab(offset(allcs, 1.7), -1, ZF + 1.3)
    ins_keep = union([box([b[0] - 0.2, b[1] - 0.2, math.floor((b[2] - 0.2) / 0.2) * 0.2],
                          [b[3] + 0.2, b[4] + 0.2, math.ceil((b[5] + 0.2) / 0.2) * 0.2])
                      for b in (p.solid.bounding_box() for p in inserts if p is not None)])
    deck_ = P["deck"] - fkeep
    kit.add("LOGGIA-deck", "Istrian", deck_, P=print_flip(), group="loggia",
            render=FT.plank_zones(deck_, H_floor, "Planks", "Istrian"))
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=300) for b in BLOCKS])
    ptop = FT.add_porch_top(kit, "LOGGIA", P, bld_keep + ins_keep, "Istrian", "Istrian", tin_col="Lead", tin="flat",
                            group="loggia")["ptop"]
    parts = {p_.name: p_ for p_ in kit.parts}
    parts["LOGGIA-top"].solid = parts["LOGGIA-top"].solid - parts["FOUNDATION"].solid
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"LOGGIA-steps-{k}", "Istrian", sm.transform(A) - fkeep - parts["LOGGIA-top"].solid, group="loggia")
    bkeep = bld_keep + slab(offset(allcs, 4.8), S1 - 0.2, 999)
    balc = _strips(kit, "LOGGIA-balcony", [(xa, FY + 1.0), (xb, FY + 1.0)], ptop, bkeep, G.fence_foscari_balcony, 6.0,
                   "Istrian", "loggia")
    e, u = MAIN.locate(XC, Y1)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Istrian", FT.steps(13.0, ZF - 0.6, 3).transform(A), group="loggia")
    print("loggia", round(time.time() - t0, 1))

    for n in merli:
        FT.key_into(kit, n, ["ROOF-deck"], (0, 0, -1), depth=0.6)
    for n, d in tmerli:
        FT.key_into(kit, n, [d], (0, 0, -1), depth=0.6)
    for n in arails:
        FT.key_into(kit, n, ["ALTANA"], (0, 0, -1), depth=0.6)
    for n in balc:
        FT.key_into(kit, n, ["LOGGIA-top"], (0, 0, -1), depth=0.6)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "foscari")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:60]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "foscari.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
