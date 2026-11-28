"""The Chantilly -- an original HO-scale (1:87.1) Châteauesque country house, 1892: the fourth of the
grand batch (houses 91 to 100, hoarch.grand), on the mansard batch's roof system
(hoarch.secondempire).

A Loire château brought to an American lawn: a ground storey of fine limestone ashlar on a plinth
of diamond-point blocks, an upper storey of red brick in header bond with tabled stone quoins, and
over a cornice of ermine spots on machicolation corbels a steep roof of blue slate banded with
honeycomb slates, set with tall stone lucarnes (a grand one over the door), stopping at a flat
crested top with lead fleuron cresting. Two round towers stand on the front corners under
candle-snuffer cones crowned by lead épis; a balustraded terrace runs across the front between
them. The ornament is François I's and Anne de Bretagne's: salamanders in flames, ermines, the
knotted cord.

- Ground storey: stone cross windows (croisées), the upper lights in diamond leading, under
  dripstones on carved bosses, lozenge aprons. Upper storey: demi-croisées between candelabra
  pilasters under shell pediments. Towers: transomed lights under dripstones.
- Door: two linenfold leaves under a basket-arched fanlight, candelabra pilasters, an entablature
  and a shell pediment between pinnacles.
- Storey joint: a stone knotted cord, an azure frieze of crowned salamanders, a stone cavetto.
- Eave: the cord, an azure frieze of ermines, machicolation corbels, a stone ogee crown. Towers:
  a blind arcade of little arches on the same corbels.
- Crests: a stone lozenge chain under a lead cavetto.

usage: python3 -m hoarch.buildings.chantilly [check] [export]
"""
import math
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import Facade, box, cs_union, inv34, ngon, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, grand as G, openings as O, roof as R, secondempire as SE
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, foundation, lip_keep, lip_ring, _corbel, stacked_shells

NAME = "The Chantilly"
COLORS = {"Stone": "#E4DCC8", "Brick": "#9B3F2E", "Slate": "#3F4752", "Lead": "#5A5F66", "Azure": "#2E4A7D",
          "Gilt": "#C2A05A", "Windows_Doors": "#E4DCC8", "Addins": "#3F4752"}
RENDER_MAT = {"Stone": "stone", "Brick": "brick", "Slate": "roof", "Lead": "lead", "Azure": "accent", "Gilt": "gilt",
              "Windows_Doors": "stone", "Addins": "roof", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"stone": ["#E4DCC8", 0.75, 0.0], "brick": ["#9B3F2E", 0.85, 0.0], "roof": ["#3F4752", 0.75, 0.0],
           "lead": ["#5A5F66", 0.5, 0.3], "accent": ["#2E4A7D", 0.55, 0.0], "gilt": ["#C2A05A", 0.4, 0.5],
           "sash": ["#2A2E33", 0.45, 0.0], "door": ["#4B2E22", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Chantilly)
LEDGE = 1.4
JOINT = dict(pitch=16.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="cordelette", role="Stone"),
    dict(kind="frieze", h=5.8, b=1.2, orn="salamanders", role="Azure"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="cavetto", role="Stone")])
EAVE = dict(pitch=6.0, margin=3.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="cordelette", role="Stone"),
    dict(kind="frieze", h=6.2, b=1.2, orn="ermines", role="Azure"),
    dict(kind="bed", h=3.0, b=1.4, P=6.8, role="Stone", brackets=dict(style="machicolation", t=1.6, reach=0.6)),
    dict(kind="crown", h=2.8, b=1.4, P=7.6, orn="ogee_fillet", role="Stone")])
TOWER_C = dict(pitch=5.2, margin=1.6, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="machiarches", role="Stone"),
    dict(kind="bed", h=2.4, b=1.4, P=5.8, role="Stone", brackets=dict(style="machicolation", t=1.4, reach=0.5)),
    dict(kind="crown", h=2.4, b=1.4, P=6.4, orn="ogee_fillet", role="Stone")])
CREST_COURSE = dict(h=2.6, b=0.6, orn=G.lozengechain, role="Stone")
CREST_CROWN = dict(h=2.4, P=3.4, kind="cavetto", role="Lead", blocks=None)
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 6.0
S1 = ZF + 36.0
ZE = S1 + RJ + 34.0
ZW = ZE + HE
DK = EAVE["layers"][-1]["P"] + 0.2
RH = 34.0
ZR1 = ZW + RH
D_TOP = round(DK - 1.2 - (RH - 1.2) / math.tan(math.radians(68.0)), 1)
ROOF = [(DK, ZW), (DK - 1.2, ZW + 1.2), (D_TOP, ZR1)]
SLATE = dict(pitch=1.7, wtab=2.0, d=0.4, shape=G.slate_hexbands)
Z_ADD = ZW + 1.0
ZT = ZW + 18.0                                   # the towers' top stage over the eave
ZTW = ZT + CO.band_height(TOWER_C)
DT = TOWER_C["layers"][-1]["P"] + 0.2
CONE_H = 40.0
G.CH_LEVELS.update(hi=S1 + RJ - ZF)
V1, V2 = 6.0, S1 + RJ - ZF + 3.0

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 136.0, 84.0
XC = X1 / 2
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
TA = 15.0
TOWER_W = Block("tower-w", ngon((0.0, 0.0), TA, n=10), ZF, ZTW)
TOWER_E = Block("tower-e", ngon((X1, 0.0), TA, n=10), ZF, ZTW)
TOWERS = [TOWER_W, TOWER_E]
BLOCKS = [MAIN, TOWER_W, TOWER_E]
CHIMS = [(34.0, 46.0), (102.0, 46.0)]
TER = (-20.0, -24.0, X1 + 20.0)                  # the terrace: west end, front edge, east end


def _walls(f, b, reg):
    """Fine ashlar below the joint, header-bond brick above; nothing in the cornice bands."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, ZW - b.z0)
    if b in TOWERS:
        reg = reg - rect(-1, ZT - b.z0 - LEDGE - 0.6, f.L + 1, 999)
    lo = reg ^ rect(-1, -100, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, S1 + RJ - b.z0, f.L + 1, 999)
    out = []
    if not lo.is_empty():
        out.append(G.stone_fine(lo, datum=0.0))
    if not hi.is_empty():
        out.append(G.brick_header(hi, datum=S1 + RJ - b.z0 + 0.2))
    return union(out) if out else M()


def _openings():
    L = []

    def add(block, x, y, v0, sp, name, kind="window"):
        e, u = block.locate(x, y)
        L.append(Opening(block, e, u, v0, sp, name, kind))

    def add_face(block, e, v0, sp, name):
        f = block.facades()[e]
        L.append(Opening(block, e, f.L / 2, v0, sp, name, "window"))

    lo, up = G.window_chantilly_croisee(), G.window_chantilly_upper()
    tw = G.window_chantilly_tower(w=6.0, h=14.0)
    add(MAIN, XC, 0.0, 1.0, G.door_chantilly(), "front-door", "door")
    for x in (32.0, 50.0, 86.0, 104.0):
        add(MAIN, x, 0.0, V1, lo, f"S{x:.0f}-1")
    for x in (32.0, 50.0, XC, 86.0, 104.0):
        add(MAIN, x, 0.0, V2, up, f"S{x:.0f}-2")
    for x_, tag in ((0.0, "W"), (X1, "E")):
        for y in (40.0, 66.0):
            add(MAIN, x_, y, V1, lo, f"{tag}{y:.0f}-1")
            add(MAIN, x_, y, V2, up, f"{tag}{y:.0f}-2")
    for x in (22.0, 46.0, 90.0, 114.0):
        add(MAIN, x, Y1, V1, lo, f"N{x:.0f}-1")
    for x in (22.0, 46.0, XC, 90.0, 114.0):
        add(MAIN, x, Y1, V2, up, f"N{x:.0f}-2")
    add(MAIN, XC, Y1, 1.0, G.door_chantilly_back(), "back-door", "door")
    for T, side, tag in ((TOWER_W, 7, "TW"), (TOWER_E, 3, "TE")):
        for e in (0, side):
            add_face(T, e, V1 + 3.0, tw, f"{tag}{e}-1")
            add_face(T, e, V2 + 2.0, tw, f"{tag}{e}-2")
        add_face(T, 0, ZW - ZF + 2.0, G.window_chantilly_tower(w=6.0, h=9.6), f"{tag}0-3")
    return L


OPENINGS = _openings()
ADDINS = [(31.0, 0.0), (49.0, 0.0), (87.0, 0.0), (105.0, 0.0), (28.0, Y1), (XC, Y1), (108.0, Y1), (0.0, Y1 / 2), (X1, Y1 / 2)]


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
                 ("Stone", a["frame"].transform(A))]
        kit.add(f"{tag}-{k}", "Addins", a["solid"].transform(A), P=inv34(A), change=(round(depth, 1), "Stone"),
                key=tag, group="addins", render=zones)
    print(tag, "plug", depth)
    return union(keeps), union(flashes)


def _deck_plate(C, z):
    dcs = poly(R.offset_path(C["path"], -1.6))
    x0, y0, x1, y1 = dcs.bounds()
    seams = cs_union([rect(x - 0.25, y0, x + 0.25, y1) for x in np.arange(x0 + 2.6, x1, 5.2)]) ^ dcs
    return C["deck"] + slab(seams, z - 0.01, z + 0.4)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    allcs = cs_union([b.cs for b in BLOCKS])
    eave_path = max(allcs.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    undress = [slab(offset(allcs, 10.0), ZE - LEDGE - 0.6, ZW + 0.01)] + \
        [slab(offset(T.cs, 8.0), ZT - LEDGE - 0.6, ZTW + 0.01) for T in TOWERS]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="chantilly", clear=[lip_keep(allcs, 3.0, ZF, 1.2)],
                        siding=_walls, prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=undress)
    kit.add("WALLS-1", "Stone", st["shells"][0], group="walls")
    kit.add("JOINT", "Brick", st["rings"][0], group="walls")
    ledges = CO.ledge(eave_path, ZE, LEDGE) + union([CO.ledge(T.pts, ZT, LEDGE) for T in TOWERS])
    trings = union([slab((offset(T.cs, -0.05) - offset(T.cs, -3.0)) ^ offset(MAIN.cs, -3.05), S1 + RJ, ZW + 1.2) for T in TOWERS])
    trings = trings - lip_keep(allcs, 3.0, S1 + RJ)
    tlips = union([_corbel(T.cs, 3.0, ZTW) + lip_ring(T.cs, 3.0, ZTW) for T in TOWERS])
    walls2 = st["shells"][1] + ledges + trings + tlips
    kit.add("WALLS-2", "Brick", walls2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    for T, tag in ((TOWER_W, "W"), (TOWER_E, "E")):
        rings, _ = CO.level(T.pts, ZT, TOWER_C)
        CO.add_level(kit, rings, f"CORNICE-T{tag}", "towers")
    kit.add("FOUNDATION", "Stone", foundation(BLOCKS, 0.0, ZF, style="diamondpoint"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Stone", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the steep roof (upside down) with its lucarnes, the crest, the deck, stacks, cresting
    tower_hug = union([T.solid(grow=0.5, dz0=-1, dz1=400) for T in TOWERS])
    mans, mtex, inner = R.mansard(MAIN.pts, ROOF, t=2.6, tex=SLATE)
    mk, mf = _addins(kit, MAIN, ADDINS, ROOF, Z_ADD, G.addin_chantilly(), "ADDIN")
    gk, gf = _addins(kit, MAIN, [(XC, 0.0)], ROOF, Z_ADD, G.addin_chantilly(grand=True), "ADDIN-G")
    C = SE.crest_ring(MAIN.pts, D_TOP, ZR1, D_TOP - inner(ZR1), CREST_COURSE, CREST_CROWN)
    # the towers rise through the roof's corners: it, its crest, deck and cresting stop clear of
    # their cornices and cones
    tcut = union([slab(offset(T.cs, DT + 0.4), ZT - LEDGE - 0.8, 999) for T in TOWERS])
    roof = (mans + (mtex - mf - gf)) - mk - gk - C["groove"] - tower_hug - walls2 - tcut
    for k, c in enumerate(sorted([c for c in roof.decompose() if c.volume() > 20.0], key=lambda c: -c.volume())):
        kit.add("ROOF" if k == 0 else ("ROOF-front" if k == 1 else f"ROOF-{k}"), "Slate", c, P=print_flip(), group="roof")
    crest = C["solid"] - tcut
    for k, c in enumerate(sorted([c for c in crest.decompose() if c.volume() > 2.0], key=lambda c: -c.volume())):
        kit.add("CREST" if k == 0 else f"CREST-{k}", "Lead", c, P=print_flip(), change=C["change"], group="roof",
                render=[(r, z ^ c) for r, z in C["zones"]])
    zdeck = C["z_top"]
    pads = union([box([x - 7.0, y - 5.5, zdeck - 0.6], [x + 7.0, y + 5.5, zdeck + 1]) for x, y in CHIMS])
    kit.add("ROOF-deck", "Slate", _deck_plate(C, zdeck) - pads - tcut, group="roof")
    for k, (x, y) in enumerate(CHIMS):
        kit.add(f"CHIMNEY-{k}", "Stone", G.chimney_chantilly(11.0, 8.0, 30.0).translate([x, y, zdeck - 0.6]), key="CHIMNEY", group="roof")
    for i, seg, A, L in SE.cresting_strips(C["path"], zdeck, C["rail"], SE.printable(G.fence_chantilly), 7.2):
        for j, piece in enumerate((seg - tcut).decompose()):
            if piece.volume() > 3.0:
                kit.add(f"CREST-iron-{i}{chr(97 + j)}", "Lead", piece, P=inv34(A), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the towers' candle-snuffer cones, épis
    for T, tag in ((TOWER_W, "W"), (TOWER_E, "E")):
        cprof = [(DT, ZTW), (DT - 1.0, ZTW + 0.8), (-TA + 3.0, ZTW + CONE_H)]
        cone, ctex, _ = R.mansard(T.pts, cprof, t=2.4, tex=dict(pitch=1.5, wtab=1.6, d=0.35, shape="square"))
        ztop = ZTW + CONE_H
        top = slab(offset(T.cs, -TA + 3.0), ztop - 0.6, ztop + 0.8)
        kit.add(f"TOWER-{tag}-cone", "Slate", cone + ctex + top - lip_keep(T.cs, 3.0, ZTW), key="TOWER-cone", group="towers")
        c = np.mean(np.asarray(T.pts), axis=0)
        kit.add(f"TOWER-{tag}-finial", "Gilt", G.finial_epi(12.0).translate([c[0], c[1], ztop + 0.79]), group="towers")
        FT.crown(kit, f"TOWER-{tag}-finial", f"TOWER-{tag}-cone")
    print("towers", round(time.time() - t0, 1))

    # --- the terrace across the front: a paved platform round the towers' feet, a pierced
    # parapet, steps at the door
    x0, y0, x1 = TER
    reg = rect(x0, y0, x1, 0.0) - offset(allcs, 1.4)
    reg = max(reg.decompose(), key=lambda c: c.area())
    rb = reg.bounds()
    joints = cs_union([rect(x - 0.15, rb[1], x + 0.15, rb[3]) for x in np.arange(x0 + 4.0, x1, 4.0)] +
                      [rect(rb[0], y - 0.15, rb[2], y + 0.15) for y in np.arange(y0 + 4.0, 0.0, 4.0)])
    ter = slab(reg, 0.0, ZF) - slab(joints ^ reg.offset(-1.2, G.MIT, 4.0), ZF - 0.3, ZF + 1)
    parts = {p_.name: p_ for p_ in kit.parts}
    kit.add("TERRACE", "Stone", ter - parts["FOUNDATION"].solid, group="terrace")
    keep = union([b.solid(grow=0.6, dz0=-5, dz1=300) for b in BLOCKS])
    gap = (XC - 9.0, XC + 9.0)
    chain = [(x0 + 1.4, -0.6), (x0 + 1.4, y0 + 1.4), (gap[0], y0 + 1.4), None, (gap[1], y0 + 1.4), (x1 - 1.4, y0 + 1.4), (x1 - 1.4, -0.6)]
    segs = [(chain[0], chain[1]), (chain[1], chain[2]), (chain[4], chain[5]), (chain[5], chain[6])]
    for i, (a, b) in enumerate(segs):
        f = Facade(np.array(a), np.array(b), 0.0)
        cs = G.fence_chantilly_terrace(f.L - 1.6, 6.0).translate([0.8, 0.0])
        strip = M.extrude(cs, 1.4).translate([0, 0, -0.7])
        A = f.A.copy()
        A[:, 3] = f.world(0, 0, 0) + np.array([0, 0, ZF - 0.01])
        seg = strip.transform(A) - keep
        for j, piece in enumerate(seg.decompose()):
            if piece.volume() > 3.0:
                kit.add(f"TERRACE-rail-{i}{chr(97 + j)}", "Stone", piece, P=inv34(A), group="terrace")
    fs = Facade(np.array((x0, y0)), np.array((x1, y0)), 0.0)
    A = fs.A.copy()
    A[:, 3] = fs.world(XC - x0, 0.0, 0.0)
    kit.add("TERRACE-steps", "Stone", FT.steps(16.0, ZF, 3).transform(A), group="terrace")
    e, u = MAIN.locate(XC, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Stone", FT.steps(14.0, ZF - 0.6, 3).transform(A), group="terrace")
    print("terrace", round(time.time() - t0, 1))

    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("CREST-iron")]:
        FT.key_into(kit, p_.name, [q.name for q in kit.parts if q.name.startswith("CREST") and "iron" not in q.name], (0, 0, -1), depth=0.6)
    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("TERRACE-rail")]:
        FT.key_into(kit, p_.name, ["TERRACE"], (0, 0, -1), depth=0.6)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "chantilly")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:60]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "chantilly.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Addins"))
