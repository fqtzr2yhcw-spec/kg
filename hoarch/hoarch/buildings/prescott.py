"""The Prescott: an original HO-scale (1:87.1) Federal (Adam) house, house 41 and the first of
the fourth batch (all Colonial).

A two-storey house of five bays, sheathed all round in apricot flush boarding (wide boards
laid edge to edge, the joints hairlines) on a brownstone base whose top course has a band of
vermiculated blocks. The ground-floor windows stand in blind arches, a carved fan over each
under an archivolt on moulded imposts; the upper windows wear entablature caps with reeded end
blocks and an oval patera, and over the door a tripartite (Wyatt) window shares a cap with
three paterae. The Adam entrance: a six-panel door between leaded sidelights under a transom
leaded in swags, engaged colonnettes either side, and over it a great carved fan in an
archivolt with a keystone, up brownstone steps. Between the storeys a Wedgwood-blue frieze of
fasces bound with crossed ribbons over a white course of beads and lozenges and a cavetto; at
the eave a Wedgwood frieze of crossed arrows through rings with rows of stars between, white
dentils, a soffit on white guttae mutules and a cyma reversa crown. A low hip of slate in square
and chisel-pointed courses stands behind a white roof balustrade (panelled pedestals with
ball finials, saltire panels crossing through rings), four tall stacks with brick dentil caps.

usage: python3 -m hoarch.buildings.prescott [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, cs_union, offset, poly, rect, slab, union
from hoarch import cornice as CO, features as FT, federal as F, gables as G, openings as O, roof as R
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Prescott"
COLORS = {"Apricot": "#D9A983", "White": "#F1EFE8", "Wedgwood": "#6F8FB3", "Slate": "#4A4F57",
          "Brownstone": "#6B4A3A", "Brick": "#8A4632", "Windows_Doors": "#F1EFE8"}
RENDER_MAT = {"Apricot": "siding", "White": "trim", "Wedgwood": "accent", "Slate": "roof", "Brownstone": "stone",
              "Brick": "brick", "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Prescott)
LEDGE = 1.4
JOINT = dict(pitch=14.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="fasces", role="Wedgwood"),
    dict(kind="course", h=1.4, b=1.4, orn="beadlozenge", role="White"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="cavetto", role="White")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.6, b=1.2, orn="arrows", role="Wedgwood"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="White", tooth=0.8, gap=0.6),
    dict(kind="bed", h=2.0, b=1.4, P=5.8, role="White", brackets=dict(style="guttae", t=1.4, reach=0.3)),
    dict(kind="crown", h=2.8, b=1.4, P=6.6, orn="reverse", role="White")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 12.0
S1 = ZF + 42.0
ZE = S1 + RJ + 38.0
ZW = ZE + HE
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE = 7.2
S_MAIN = 0.62
V1 = 7.6
V2 = S1 + RJ + 5.0 - ZF

# ------------------------------------------------------------------ plan (x east, y north; the front faces south)
W, D = 200.0, 116.0
XC = W / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
BAYS = (24.0, 62.0, 138.0, 176.0)


def _skin(f, b, reg):
    """Flush boarding all round; nothing in the eave's band."""
    reg = reg - rect(-1, ZE - b.z0, f.L + 1, 999)
    return F.flush_boards(reg, datum=1.0, seed=int(abs(f.n[0]) * 3 + abs(f.n[1]) * 7 + f.p0[0]))


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    lo = F.window_blindarch(9.6, 22.0)
    up = F.window_tablet(9.6, 21.0)
    for x in BAYS:
        add(x, 0.0, V1, lo, f"S{x:.0f}-1")
        add(x, 0.0, V2, up, f"S{x:.0f}-2")
    add(XC, 0.0, 0.4, F.door_adam(11.0, 22.0), "front-door", "door")
    add(XC, 0.0, V2, F.window_wyatt(9.6, 21.0), "S-wyatt")
    for x_ in (0.0, W):
        for y in (34.0, 82.0):
            tag = "W" if x_ == 0 else "E"
            add(x_, y, V1, lo, f"{tag}{y:.0f}-1")
            add(x_, y, V2, up, f"{tag}{y:.0f}-2")
    for x in BAYS:
        add(x, D, V1, lo, f"N{x:.0f}-1")
    for x in BAYS + (XC,):
        add(x, D, V2, up, f"N{x:.0f}-2")
    add(XC, D, 0.4, F.door_adam(10.0, 22.0, fan=False), "back-door", "door")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN)]
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    clear = [lip_keep(base, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=[], clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((XC - 22.0, 3.0), (XC - 22.0, D - 3.0), 2.0, ZF, ZW)])
    kit.add("WALLS-1", "Apricot", st["shells"][0], group="walls")
    kit.add("JOINT", "Apricot", st["rings"][0], group="walls")
    eave_path = MAIN.pts
    lip = _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)
    kit.add("WALLS-2", "Apricot", st["shells"][1] + lip + CO.ledge(eave_path, ZE, LEDGE), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(eave_path, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="vermiculated")
    kit.add("FOUNDATION", "Brownstone", fnd, group="foundation")

    # windows and doors
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{o.v0 > 20}", group="inserts", render=zones)
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the roof: a low hip of slate in square and chisel-pointed courses, behind a balustrade
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, [], texture=["square", "chisel"], tex_kw=dict(pitch=1.6, wtab=2.2, d=0.4),
                       inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    roof = rf["body"] + rf["tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    caps = [G.ridge_cap((D / 2, D / 2), (W - D / 2, D / 2), zr, S_MAIN, ZW, half=1.2, up=0.6)]
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    ends = [(D / 2, D / 2), (W - D / 2, D / 2), (W - D / 2, D / 2), (D / 2, D / 2)]
    hips = union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.2, up=0.6, drop=1.8)
                  for c, e in zip(corners, ends)])
    roof = roof + union(caps) + hips
    ZB = round((Z_EAVE + 1.0) / 0.2) * 0.2                  # the balustrade stands on a level curb round the edge
    roof = roof + F.roof_curb(corners, Z_EAVE - 0.6, ZB)
    roof = roof - F.roof_curb(corners, ZB, ZB + 40.0, w=3.0)          # nothing stands up where the balustrade goes
    roof = roof - lip_keep(base, 3.0, ZW)
    roof = roof.trim_by_plane([0, 0, 1.0], Z_EAVE - FASCIA)          # a flat base: nothing (hip-cap ends) hangs below it
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    # four tall stacks, in pairs at the ends
    CW, CD = 8.0, 11.0
    pockets, stacks = [], []
    for cx in (17.0, W - 17.0):
        for cy in (30.0, D - 30.0):
            zroof = Z_EAVE + S_MAIN * (min(cx, W - cx) - CW / 2 + D_EAVE)
            z0 = round((zroof - 3.0) / 0.2) * 0.2
            roof = roof + G.chimney_seat(solid_env, cx, cy, max(CW, CD) / 2, zr + 1.0)
            pockets.append(box([cx - CW / 2 - 0.4, cy - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, cy + CD / 2 + 0.4, zr + 40]))
            stacks.append(F.chimney_dentil(CW, CD, zr + 10.0 - z0).translate([cx, cy, z0]))
    roof = roof - union(pockets)
    kit.add("ROOF", "Slate", roof, group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Brick", s_, key="CHIMNEY", group="roof")
    for side, run in F.balustrade_runs(corners, ZB, h=7.0):
        kit.add(f"BALUSTRADE-{side}", "White", run, key=f"BALUSTRADE-{'fb' if side in ('front', 'back') else 'ends'}", group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the steps up to the doors
    f0 = MAIN.facades()[0]
    A = f0.A.copy()
    A[:, 3] = f0.world(XC, -ZF, 1.4)
    kit.add("STEPS-front", "Brownstone", FT.steps(24.0, ZF - 0.6, 4, cheek=2.0).transform(A) - fnd, group="steps")
    e, u = MAIN.locate(XC, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Brownstone", FT.steps(16.0, ZF - 0.6, 4).transform(A) - fnd, group="steps")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "prescott")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "prescott.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
