"""The Alvarado: an original HO-scale (1:87.1) Spanish Colonial house, house 48 of the fourth
batch (all Colonial).

Two storeys of thick adobe under whitewashed lime plaster, trowelled in soft sweeps over a
painted dado, on a plinth of coquina blocks pocked with shells. On the street front the
portal: a pair of plank leaves studded with iron nails under a mixtilinear (scalloped) arch
in a moulded stone surround with a keystone and a cornice. The ground-floor casements stand
deep behind projecting rejas of turned spindles; upstairs the casements are under wooden
lintels cut in scalloped arches, and three glazed plank doors open onto the street balcony,
cantilevered on carved brackets, railed with ringed spindles and roofed on slim posts with
crossed zapatas, under a frieze of little scalloped arches and a fascia of tile ends. Between
the storeys a frieze of azulejos (tiles with stars and quatrefoils) over the Franciscan
cordon; at the eave pomegranates between eight-pointed stars, dentils and viga ends. A low
hip of barrel tiles, two stacks capped with little tiled saddles, and a garden wall with an
arched gate against the east end.

usage: python3 -m hoarch.buildings.alvarado [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, poly, rect, slab, union
from hoarch import colonial4 as C4, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Alvarado"
COLORS = {"Whitewash": "#F1ECE0", "Azul": "#2E5E9E", "Wood": "#5A3B28", "Cantera": "#C9A188", "Tile": "#B45A3C",
          "Coquina": "#CDBF9E", "Planks": "#6E5238", "PorchDeck": "#5A3B28", "Windows_Doors": "#5A3B28"}
RENDER_MAT = {"Whitewash": "siding", "Azul": "accent", "Wood": "wood", "Cantera": "trim", "Tile": "roof",
              "Coquina": "stone", "Planks": "planks", "PorchDeck": "wood", "Windows_Doors": "wood", "Door": "door",
              "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Alvarado)
LEDGE = 1.4
JOINT = dict(pitch=14.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="azulejos", role="Azul"),
    dict(kind="course", h=1.6, b=1.4, orn="cordon", role="Cantera"),
    dict(kind="crown", h=2.2, b=1.4, P=3.4, orn="bevel", role="Cantera")])
EAVE = dict(pitch=14.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.0, b=1.2, orn="pomegranates", role="Cantera"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Wood", tooth=0.8, gap=0.6),
    dict(kind="bed", h=2.2, b=1.4, P=5.8, role="Wood", brackets=dict(style="zapata", t=1.6, reach=0.3)),
    dict(kind="crown", h=2.6, b=1.4, P=6.4, orn="cavetto", role="Wood")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 6.0
S1 = ZF + 40.0
ZU = S1 + RJ
ZE = ZU + 36.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
D_EAVE = 6.4
S_MAIN = 0.42
W, D = 196.0, 104.0
XC, YC = W / 2, D / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
BX0, BX1, BD = 46.0, W - 46.0, 14.0            # the street balcony
V1 = 8.0
V2 = ZU - ZF + 5.0
VB = ZU - ZF + 0.8
TOP_DZ = 5.2


def _skin(f, b, reg):
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, 999)
    return C4.plaster_trowelled(reg, datum=0.0, dado=6.0)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    lo = C4.window_reja(10.0, 20.0)
    up = C4.window_ornatehead(10.0, 20.0)
    bdoor = C4.door_plankglazed(10.0, 21.0)
    for x in (20.0, 60.0, W - 60.0, W - 20.0):
        add(x, 0.0, V1, lo, f"S{x:.0f}-1")
    add(XC, 0.0, 0.4, C4.door_mixtilinear(12.0, 22.0), "portal", "door")
    for x in (XC - 32.0, XC, XC + 32.0):
        add(x, 0.0, VB, bdoor, f"S{x:.0f}-bal", "door")
    for x in (20.0, W - 20.0):
        add(x, 0.0, V2, up, f"S{x:.0f}-2")
    for x in (30.0, 70.0, W - 70.0, W - 30.0):
        add(x, D, V1, lo, f"N{x:.0f}-1")
    add(XC, D, 1.0, C4.door_plankglazed(10.0, 20.0), "back-door", "door")
    for x in (30.0, 70.0, XC, W - 70.0, W - 30.0):
        add(x, D, V2, up, f"N{x:.0f}-2")
    for x_, tag in ((0.0, "W"), (W, "E")):
        for y in (22.0, 76.0):
            add(x_, y, V1, lo, f"{tag}{y:.0f}-1")
            add(x_, y, V2, up, f"{tag}{y:.0f}-2")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    clear = [lip_keep(base, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=[], clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((XC - 22.0, 3.0), (XC - 22.0, D - 3.0), 2.0, ZF, ZW)])
    kit.add("WALLS-1", "Whitewash", st["shells"][0], group="walls")
    kit.add("JOINT", "Whitewash", st["rings"][0], group="walls")
    lip = _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)
    kit.add("WALLS-2", "Whitewash", st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")
    bal_zone = box([BX0 - 0.5, -30.0, 0.0], [BX1 + 0.5, 0.6, 400.0])                # the balcony takes the joint's place there
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=bal_zone)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="coquina")
    kit.add("FOUNDATION", "Coquina", fnd, group="foundation")
    ins_keep = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                       key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{o.v0 > 20}", group="inserts", render=zones)
        ins_keep.append(part.solid)
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the roof: a low hip of barrel tiles, capped, two saddle-capped stacks
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, [], texture="barrel", tex_kw=dict(pitch=2.2, seam_pitch=2.6, d=0.5),
                       inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.6)
    roof = rf["body"] + rf["tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    caps = [G.ridge_cap((D / 2, YC), (W - D / 2, YC), zr, S_MAIN, ZW, half=1.3, up=0.7)]
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, YC), (W - D / 2, YC), (W - D / 2, YC), (D / 2, YC)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.3, up=0.7, drop=1.8) for c, e in zip(corners, ends)])
    roof = roof + union(caps) + hips
    roof = roof - lip_keep(base, 3.0, ZW)
    roof = roof.trim_by_plane([0, 0, 1.0], Z_EAVE - FASCIA)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW = 9.0
    pockets, stacks = [], []
    for cx in (64.0, W - 64.0):
        z0 = round((zr - 6.0) / 0.2) * 0.2
        # a block under the stack from the pocket's floor to the ridge, over a 45-degree
        # pyramid of fill in the hollow: the stack stands on its whole foot
        hs = CW / 2 + 1.2
        roof = roof + ((M.hull_points([(cx + sx * hs, YC + sy * hs, z0) for sx in (-1, 1) for sy in (-1, 1)] + [(cx, YC, z0 - hs - 0.5)])
                        + box([cx - hs, YC - hs, z0], [cx + hs, YC + hs, zr + 1.0])) ^ solid_env)
        pockets.append(box([cx - CW / 2 - 0.4, YC - CW / 2 - 0.4, z0], [cx + CW / 2 + 0.4, YC + CW / 2 + 0.4, zr + 40]))
        stacks.append(C4.chimney_tilesaddle(CW, CW, zr + 16.0 - z0).translate([cx, YC, z0]))
    roof = roof - union(pockets)
    kit.add("ROOF", "Tile", roof, group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Whitewash", s_, key="CHIMNEY", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the street balcony: a deck on carved brackets, its posts, railings and frieze in one
    # piece with its flat top (pegged into the deck), under a shed roof of barrel tiles
    INSET = 1.6
    pts = [(BX0, 0.0), (BX0, -BD), (BX1, -BD), (BX1, 0.0)]
    L0 = BX1 - BX0
    runs = [dict(a=(BX0, 0.0), b=(BX0, -BD), posts=[3.0, BD - INSET]),
            dict(a=(BX0, -BD), b=(BX1, -BD), posts=[INSET + (L0 - 2 * INSET) * k / 4 for k in range(5)]),
            dict(a=(BX1, -BD), b=(BX1, 0.0), posts=[INSET, BD - 3.0])]
    S_B, o = 0.3, 2.0
    zs = ZE - 0.6 - S_B * (BD + o)
    PB = FT.porch_turned(pts, runs, ZU, zs + 0.8 - TOP_DZ - ZU, over=o, inset=INSET, rail_h=8.2, post="zapata",
                         rail="rejaspindle", arcade="mixtilinear", roof_edge="tejas", top=True)
    bld_keep = union([p.solid for p in kit.parts if p.name.startswith(("WALLS", "JOINT", "CORNICE"))])
    keep = bld_keep + union(ins_keep) + fnd
    where = []
    for r in runs:
        f = FT.Facade(r["a"], r["b"], 0.0)
        for u in r["posts"]:
            p = f.p0 + f.u * u - f.n * INSET
            if not any(np.allclose(p, q, atol=0.05) for q in where):
                where.append(p)
    planks = FT.porch_planks(pts, [0, 1, 2], H=ZU, t=1.2, pitch=1.8, crack=0.25, border=1.4, along=(0.0, 1.0))
    gcs = poly(pts)
    frame = slab(gcs - offset(gcs, -2.2), ZU - 3.2, ZU - 1.19) + slab(gcs, ZU - 1.8, ZU - 1.19)
    brk = C4.poly([(0.0, 0.0), (-BD + 0.8, 0.0), (-BD + 0.8, -1.4), (-BD + 2.4, -1.8), (-BD + 3.2, -3.0), (-BD + 5.0, -3.4),
                   (-6.0, -4.2), (-3.4, -5.6), (-1.6, -7.2), (0.0, -7.6)])
    brackets = union([M.extrude(brk, 1.6).translate([0, 0, -0.8]).transform(np.array([[0, 0, 1.0, x], [1.0, 0, 0, 0], [0, 1.0, 0, ZU - 3.2]]))
                      for x in np.arange(BX0 + 5.0, BX1 - 3.0, 13.2)])
    socks = union([box([p[0] - 1.0, p[1] - 1.0, ZU - 2.0], [p[0] + 1.0, p[1] + 1.0, ZU + 1.0]) for p in where])
    deck = ((planks + frame + brackets) - socks) - keep
    kit.add("BALCONY-deck", "PorchDeck", deck, P=print_flip(), group="balcony", render=FT.plank_zones(deck, ZU, "Planks", "Wood"))
    res = FT.add_porch_top(kit, "BALCONY", PB, keep, "Wood", "Wood", tin="custom", group="balcony")
    zs = res["ptop"] - 0.8
    outer = [(BX0 - o, -BD - o), (BX1 + o, -BD - o), (BX1 + o, 3.0), (BX0 - o, 3.0)]
    sk, sk_tex = R.hip_roof([(outer, [0, 1, 3])], zs, S_B, 0.0, texture="barrel", tex_kw=dict(pitch=2.0, seam_pitch=2.4, d=0.45), zlo=zs)
    shed = ((sk + sk_tex) ^ slab(poly(outer), zs, zs + 10.0)) - bld_keep - union(ins_keep)
    kit.add("BALCONY-roof", "Tile", max(shed.decompose(), key=lambda m_: m_.volume()), group="balcony")
    print("balcony", round(time.time() - t0, 1))

    # --- the garden wall and gate against the east end
    wall, cop, arch = C4.garden_wall(34.0, 16.0, 2.4, 10.0, 12.0)
    Ag = np.array([[1.0, 0, 0, W - 1.5], [0, 1.0, 0, 40.0], [0, 0, 1.0, 0.0]])
    kit.add("GARDENWALL", "Whitewash", wall.transform(Ag) - fnd - bld_keep, group="garden")
    kit.add("GARDENWALL-coping", "Tile", cop.transform(Ag) - bld_keep, group="garden")
    leaf = C4.ext(arch.offset(-0.12, C4.JoinType.Round), -0.8, 0.8)                  # a snug fit, glued round its edge
    grooves = C4.ext(C4.cs_union([rect(x - 0.18, -1, x + 0.18, 30) for x in np.arange(17.0 - 5.0 + 1.25, 17.0 + 5.0, 1.25)]), 0.5, 1.0)
    gate = (leaf - grooves).transform(np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, 1.0, 0, 0]])).transform(Ag)
    kit.add("GATE", "Wood", gate, group="garden")
    # --- steps at the portal and the back door
    for (x, y), wd, n in (((XC, 0.0), 22.0, 3), ((XC, D), 15.0, 3)):
        e, u = MAIN.locate(x, y)
        f = MAIN.facades()[e]
        A = f.A.copy()
        A[:, 3] = f.world(u, -ZF, 1.4)
        kit.add(f"STOOP-{e}", "Cantera", FT.steps(wd, ZF - 0.6 + (0.6 if y == D else 0.0), n).transform(A) - fnd, group="steps")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "alvarado")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "alvarado.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
