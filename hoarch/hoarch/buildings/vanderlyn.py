"""The Vanderlyn -- an original HO-scale (1:87.1) Beaux-Arts palace, 1902: the fifth of the grand batch
(houses 91 to 100, hoarch.grand), on the mansard batch's roof system (hoarch.secondempire).

A white palace for a Gilded Age fortune. On a panelled podium, a ground storey of deep
V-jointed rustication pierced by round-arched French windows under scrolled keys with
balconettes; an upper storey of buff brick in English cross bond between colossal pilasters, its
windows in eared architraves under segmental pediments on balconies. A cornice of bucrania and
garlands on garland consoles under a verdigris crown carries a balustrade of bottle balusters
between pedestals with balls; behind it a copper mansard with oeils-de-boeuf rises to a crested
deck with bronze anthemion cresting, and at the centre a ribbed dome on a drum of oculi under a
lantern and a gilt ball. A colossal portico of four fluted Composite columns rises through both
storeys to a triglyph entablature and a pediment with a cartouche between garlands, a palmette
and urns at its corners, over a broad flight of steps.

- Storey joint: a marble course of rosettes and beads, an ochre anthemion, a marble crown.
- Eave: rosettes and beads, an ochre frieze of bucrania and garlands, garland consoles, a
  verdigris cyma.
- Crest: a marble course of little palmettes under a verdigris cavetto.

usage: python3 -m hoarch.buildings.vanderlyn [check] [export]
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

NAME = "The Vanderlyn"
COLORS = {"Marble": "#ECE9E1", "Buff": "#D6BC8C", "Ochre": "#C3A266", "Copper": "#6E9C88", "Bronze": "#5E4A2E",
          "Gilt": "#C9A64E", "Windows_Doors": "#ECE9E1", "Addins": "#6E9C88"}
RENDER_MAT = {"Marble": "marble", "Buff": "brick", "Ochre": "accent", "Copper": "copper", "Bronze": "bronze", "Gilt": "gilt",
              "Windows_Doors": "marble", "Addins": "copper", "Sash": "sash", "Door": "door", "Glass": "glass"}
PALETTE = {"marble": ["#ECE9E1", 0.55, 0.0], "brick": ["#D6BC8C", 0.85, 0.0], "accent": ["#C3A266", 0.6, 0.0],
           "copper": ["#6E9C88", 0.55, 0.2], "bronze": ["#5E4A2E", 0.45, 0.4], "gilt": ["#C9A64E", 0.35, 0.6],
           "sash": ["#2E2A24", 0.45, 0.0], "door": ["#3A2A1E", 0.45, 0.0]}

# ------------------------------------------------------------------ cornices (unique to the Vanderlyn)
LEDGE = 1.4
JOINT = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="rosettebeads", role="Marble"),
    dict(kind="frieze", h=5.4, b=1.2, orn="anthemion", role="Ochre"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="ovolo", role="Marble")])
EAVE = dict(pitch=11.0, margin=4.0, layers=[
    dict(kind="course", h=1.8, b=1.0, orn="rosettebeads", role="Marble"),
    dict(kind="frieze", h=7.0, b=1.2, orn="bucrania", role="Ochre"),
    dict(kind="bed", h=3.2, b=1.4, P=8.6, role="Marble", brackets=dict(style="garlandconsole", t=1.6, reach=0.6)),
    dict(kind="crown", h=3.0, b=1.4, P=9.4, orn="cyma", role="Copper")])
CREST_COURSE = dict(h=2.6, b=0.6, orn=G.anthemionlets, role="Marble")
CREST_CROWN = dict(h=2.4, P=3.4, kind="cavetto", role="Copper", blocks=None)
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 10.0
S1 = ZF + 36.0
ZE = S1 + RJ + 36.0
ZW = ZE + HE
RH = 24.0
ZR1 = ZW + RH
D0 = -0.6                                       # the mansard's foot, just inside the wall face: the crown carries the balustrade
D_TOP = round(D0 - 0.6 - (RH - 1.0) / math.tan(math.radians(72.0)), 1)
ROOF = [(D0, ZW), (D0 - 0.6, ZW + 1.0), (D_TOP, ZR1)]
SLATE = dict(pitch=1.6, wtab=1.8, d=0.35, shape=G.slate_copper)
Z_ADD = ZW + 4.0
G.VL_LEVELS.update(hi=S1 + RJ - ZF)
V1, V2 = 4.0, S1 + RJ - ZF + 4.6

# ------------------------------------------------------------------ plan (mm; x east, y north, front = south)
X1, Y1 = 150.0, 92.0
XC, YC = X1 / 2, Y1 / 2
MAIN = Block("main", [(0, 0), (X1, 0), (X1, Y1), (0, Y1)], ZF, ZW)
BLOCKS = [MAIN]
PW_, PD = 52.0, 18.0                            # the portico: width, depth
CHIMS = [(24.0, YC), (X1 - 24.0, YC)]


def _walls(f, b, reg):
    """V-jointed rustication below the joint, English cross bond above; nothing in the eave band."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, 999)
    lo = reg ^ rect(-1, -100, f.L + 1, S1 - b.z0)
    hi = reg ^ rect(-1, S1 + RJ - b.z0, f.L + 1, 999)
    out = []
    if not lo.is_empty():
        out.append(G.rusticated_vjoint(lo, datum=0.0))
    if not hi.is_empty():
        out.append(G.brick_englishcross(hi, datum=S1 + RJ - b.z0 + 0.2))
    return union(out) if out else M()


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    lo, up = G.window_vanderlyn_ground(), G.window_vanderlyn_upper()
    add(XC, 0.0, 0.8, G.door_vanderlyn(h=23.0), "front-door", "door")
    for x in (16.0, 38.0, 57.0, 93.0, 112.0, 134.0):
        add(x, 0.0, V1, lo, f"S{x:.0f}-1")
    for x in (16.0, 38.0, 57.0, XC, 93.0, 112.0, 134.0):
        add(x, 0.0, V2, up, f"S{x:.0f}-2")
    for x_, tag in ((0.0, "W"), (X1, "E")):
        for y in (22.0, YC, 70.0):
            add(x_, y, V1, lo, f"{tag}{y:.0f}-1")
            add(x_, y, V2, up, f"{tag}{y:.0f}-2")
    for x in (16.0, 38.0, 58.0, 92.0, 112.0, 134.0):
        add(x, Y1, V1, lo, f"N{x:.0f}-1")
    for x in (16.0, 38.0, 58.0, XC, 92.0, 112.0, 134.0):
        add(x, Y1, V2, up, f"N{x:.0f}-2")
    add(XC, Y1, 0.8, G.door_vanderlyn_back(), "back-door", "door")
    return L


OPENINGS = _openings()
ADDINS = [(24.0, 0.0), (47.0, 0.0), (103.0, 0.0), (126.0, 0.0), (24.0, Y1), (52.0, Y1), (98.0, Y1), (126.0, Y1),
          (0.0, 28.0), (0.0, 64.0), (X1, 28.0), (X1, 64.0)]


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
        zones = [("Glass", a["glass"].transform(A)), ("Copper", (a["plug"] - a["glass"]).transform(A)),
                 ("Marble", a["frame"].transform(A))]
        kit.add(f"{tag}-{k}", "Addins", a["solid"].transform(A), P=inv34(A), change=(round(depth, 1), "Marble"),
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
    allcs = MAIN.cs
    undress = [slab(offset(allcs, 10.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="vanderlyn", clear=[lip_keep(allcs, 3.0, ZF, 1.2)],
                        siding=_walls, prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False,
                        undress=undress)
    kit.add("WALLS-1", "Marble", st["shells"][0], group="walls")
    kit.add("JOINT", "Buff", st["rings"][0], group="walls")
    walls2 = st["shells"][1] + CO.ledge(MAIN.pts, ZE, LEDGE)
    kit.add("WALLS-2", "Buff", walls2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    kit.add("FOUNDATION", "Marble", foundation(BLOCKS, 0.0, ZF, style="dadopodium"), group="foundation")
    inserts = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        tag = f"{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}"
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Marble", "Door" if o.kind == "door" else "Sash", "Glass")
        inserts.append(kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                               key=f"{key}-{tag}-{o.v0 > 20}", group="inserts", render=zones))
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the balustrade on the cornice's crown, in front of the copper mansard (seated on its profile)
    crown = union([p_.solid for p_ in kit.parts if p_.name.startswith("CORNICE-E")])
    path = R.offset_path(MAIN.pts, 4.4)
    n = len(path)
    for i in range(n):
        a, b = np.array(path[i]), np.array(path[(i + 1) % n])
        f = Facade(a, b, 0.0)
        cs = G.fence_vanderlyn_balustrade(f.L - 2.6, 6.4).translate([1.3, 0.0])
        strip = M.extrude(cs, 1.4).translate([0, 0, -0.7])
        A = f.A.copy()
        A[:, 3] = f.world(0, 0, 0) + np.array([0, 0, ZW - 0.01])
        kit.add(f"ROOF-balustrade-{i}", "Marble", strip.transform(A) - crown, P=inv34(A), group="roof")

    # --- the mansard (upside down), oeils-de-boeuf, crest, deck, stacks, cresting, the dome
    mans, mtex, inner = R.mansard(MAIN.pts, ROOF, t=2.6, tex=SLATE)
    mk, mf = _addins(kit, MAIN, ADDINS, ROOF, Z_ADD, G.addin_vanderlyn(), "ADDIN")
    C = SE.crest_ring(MAIN.pts, D_TOP, ZR1, D_TOP - inner(ZR1), CREST_COURSE, CREST_CROWN)
    kit.add("MANSARD", "Copper", (mans + (mtex - mf)) - mk - C["groove"], P=print_flip(), group="roof")
    kit.add("CREST", "Copper", C["solid"], P=print_flip(), change=C["change"], group="roof", render=C["zones"])
    zdeck = C["z_top"]
    dome, zdt = G.dome_vanderlyn(13.0, 12.0, 11.0)
    dome = dome.translate([XC, YC, zdeck])
    pads = union([box([x - 6.0, y - 5.0, zdeck - 0.6], [x + 6.0, y + 5.0, zdeck + 1]) for x, y in CHIMS] +
                 [M.cylinder(1.0, 13.3, 13.3, 64).translate([XC, YC, zdeck - 0.01])])
    kit.add("ROOF-deck", "Copper", _deck_plate(C, zdeck) - pads, group="roof")
    kit.add("DOME", "Copper", dome, group="dome")
    kit.add("DOME-finial", "Gilt", G._ball(1.4, zdeck + zdt + 1.4, neck=0.7).translate([XC, YC, 0.0]) +
            M.cylinder(1.2, 0.7, 0.7, 16).translate([XC, YC, zdeck + zdt - 0.4]), group="dome")
    FT.crown(kit, "DOME-finial", "DOME")
    for k, (x, y) in enumerate(CHIMS):
        kit.add(f"CHIMNEY-{k}", "Marble", G.chimney_vanderlyn(11.0, 9.0, 24.0).translate([x, y, zdeck - 0.6]), key="CHIMNEY", group="roof")
    for i, seg, A, L in SE.cresting_strips(C["path"], zdeck, C["rail"], SE.printable(G.fence_vanderlyn), 7.2):
        kit.add(f"CREST-iron-{i}", "Bronze", seg, P=inv34(A), key=f"CREST-iron-{round(L, 1)}", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the colossal portico: four Composite columns, a triglyph entablature, the pediment
    x0, x1 = XC - PW_ / 2, XC + PW_ / 2
    FY = -PD
    pts = [(x0, -1.4), (x0, FY), (x1, FY), (x1, -1.4)]
    Ls, Lf = PD - 1.4, PW_
    ins = 4.2
    runs = [dict(a=(x0, -1.4), b=(x0, FY), posts=[4.8, Ls - ins]),
            dict(a=(x0, FY), b=(x1, FY), posts=[ins, 18.0, Lf - 18.0, Lf - ins]),
            dict(a=(x1, FY), b=(x1, -1.4), posts=[ins, Ls - 4.8])]
    H_floor = ZF
    post_h = ZE - 2.6 - H_floor - 5.2
    P = FT.porch_turned(pts, runs, H_floor, post_h, steps_at=[(1, Lf / 2, 24.0)], inset=ins, rail=None, beam=3.2,
                        post="composite", arcade="regulae", skirt="dadopanels", pier_tex="stone", roof_edge="triglyphs",
                        planks=dict(pitch=3.2, crack=0.3, border=2.2), drop=3.0, top=True)
    where = []
    for r in runs:
        f = Facade(r["a"], r["b"], 0.0)
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
    kit.add("PORTICO-deck", "Marble", deck_, P=print_flip(), group="portico")
    bld_keep = union([b.solid(grow=1.45, dz0=-20, dz1=300) for b in BLOCKS])
    ptop = FT.add_porch_top(kit, "PORTICO", P, bld_keep + ins_keep, "Marble", "Marble", tin_col="Copper", tin="flat",
                            group="portico")["ptop"]
    parts = {p_.name: p_ for p_ in kit.parts}
    parts["PORTICO-top"].solid = parts["PORTICO-top"].solid - parts["FOUNDATION"].solid
    for k, (sm, A) in enumerate(P["steps"]):
        kit.add(f"PORTICO-steps-{k}", "Marble", sm.transform(A) - fkeep, group="portico")
    edep = 3.0
    Ag = np.array([[-1.0, 0, 0, XC], [0, -1.0, 0, FY - 1.0 + edep], [0, 0, 1.0, ptop]])
    kit.add("PORTICO-pediment", "Marble", G.pediment_vanderlyn(PW_ + 2.0, edep, 11.0).transform(Ag), P=inv34(Ag), group="portico")
    e, u = MAIN.locate(XC, Y1)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.6)
    kit.add("STOOP-back", "Marble", FT.steps(16.0, ZF - 0.6, 4).transform(A), group="portico")
    print("portico", round(time.time() - t0, 1))

    for p_ in [p_ for p_ in kit.parts if p_.name.startswith("CREST-iron")]:
        FT.key_into(kit, p_.name, ["CREST"], (0, 0, -1), depth=0.6)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "vanderlyn")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:60]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "vanderlyn.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors", "Addins"))
