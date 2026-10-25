"""The Pullman: an original HO-scale (1:87.1) Chicago brick bungalow, house 57 of the fifth
batch (the Craftsman era, 1900-1930).

A broad one-and-a-half-storey bungalow of brown wire-cut face brick, scored on every face, on
a raised basement under a bevelled limestone water table. Across the front a three-sided bay
carries a big Chicago window (a fixed pane between narrow sashes under an art-glass transom of
circles in squares) and a double-hung art-glass sash on each canted side, all on long
limestone sills under keystoned lintels. A low hipped roof of T-lock shingles with deep eaves
on slab consoles over a frieze of Sullivanesque terra cotta (seed pods and curling fronds) and
paired dentils; a bellcast dormer in the front slope and another in the back. The door, beside
the bay, is oak with a lozenge-chain art-glass light in a limestone surround whose hood rests
on scrolled consoles, up a brick stoop with limestone copings. A brick chimney with limestone
bands climbs the east wall.

usage: python3 -m hoarch.buildings.pullman [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, poly, rect, slab, union
from hoarch import craftsman2 as CR2, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Pullman"
COLORS = {"Brick": "#8C5A3C", "Limestone": "#D8CFBC", "Green": "#3F4A3A", "Roof": "#4A4F52", "Terracotta": "#B9724A",
          "Windows_Doors": "#3F4A3A"}
RENDER_MAT = {"Brick": "brick", "Limestone": "stone", "Green": "trim", "Roof": "roof", "Terracotta": "accent",
              "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ the cornice (unique to the Pullman)
LEDGE = 1.4
EAVE = dict(pitch=15.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.8, b=1.2, orn="sullivan", role="Terracotta"),
    dict(kind="course", h=1.4, b=1.4, orn="pairdentil", role="Limestone"),
    dict(kind="bed", h=2.6, b=1.4, P=7.2, role="Green", brackets=dict(style="slabconsole", t=1.4, reach=0.4)),
    dict(kind="crown", h=2.2, b=1.4, P=7.6, orn="torus", role="Green")])
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 16.0                                        # a raised basement
ZE = ZF + 38.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE = 9.0
S = 0.45
W, D = 150.0, 120.0
XC, YC = W / 2, D / 2
BX0, BX1, BD = 20.0, 92.0, 14.0                 # the canted bay
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BAY = Block("bay", [(BX0, 3.0), (BX0, 0.0), (BX0 + BD, -BD), (BX1 - BD, -BD), (BX1, 0.0), (BX1, 3.0)], ZF, ZW)
BLOCKS = [MAIN, BAY]
OUT_PTS = [(0.0, 0.0), (BX0, 0.0), (BX0 + BD, -BD), (BX1 - BD, -BD), (BX1, 0.0), (W, 0.0), (W, D), (0.0, D)]
DOOR_X = 121.0
CHY = 72.0                                       # the chimney, on the east wall
V1 = 8.0


def _chim_keep(x1=W - 0.2):
    return union([box([x1, CHY - 10.6, -1.0], [W + 12.0, CHY + 10.6, ZE - 3.0]),
                  box([x1, CHY - 8.2, ZE - 3.1], [W + 12.0, CHY + 8.2, 400.0])])


def _skin(f, b, reg):
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, 999)
    if b is MAIN and f.n[0] > 0.5:
        reg = reg - rect(CHY - 10.8, -ZF - 1, CHY + 10.8, 999)
    return CR2.brick_scratch(reg, seed=int(f.p0[0] + 3 * f.p0[1]) % 91)


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    cw = CR2.window_chicago(30.0, 21.0)
    a12 = CR2.window_artsash(11.0, 21.0)
    a16 = CR2.window_artsash(15.0, 21.0)
    add(BAY, (BX0 + BX1) / 2, -BD, V1, cw, "bay-front")
    add(BAY, BX0 + BD / 2, -BD / 2, V1, a12, "bay-W")
    add(BAY, BX1 - BD / 2, -BD / 2, V1, a12, "bay-E")
    add(MAIN, DOOR_X, 0.0, 0.4, CR2.door_chicago(11.0, 24.0), "front-door", "door")
    add(MAIN, 140.0, 0.0, V1, a12, "S140")
    for y in (26.0, 62.0, 98.0):
        add(MAIN, 0.0, y, V1, a16, f"W{y:.0f}")
    for y in (30.0, 106.0):
        add(MAIN, W, y, V1, a16, f"E{y:.0f}")
    for x in (28.0, 64.0, 128.0):
        add(MAIN, x, D, V1, a16, f"N{x:.0f}")
    add(MAIN, 96.0, D, 0.4, CR2.door_halflight(9.0, 21.0), "back-door", "door")
    return L


OPENINGS = _openings()


def _frame(u, v, w, o):
    return np.column_stack([u, v, w, o]).astype(float)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs + BAY.cs
    undress = [slab(offset(base, 10.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    walls = wall_shell(BLOCKS, OPENINGS, t=3.0, belt=None, corners="none", water_table=False, siding=_skin,
                       undress=undress, partitions=[((XC, 3.0), (XC, D - 3.0), 2.0, ZF, ZW), ((3.0, 64.0), (W - 3.0, 64.0), 2.0, ZF, ZW)])
    walls = walls - lip_keep(base, 3.0, ZF, 1.2)
    lip = _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)
    ck, ck_out = _chim_keep(), _chim_keep(W)
    walls = walls + lip + CO.ledge(OUT_PTS, ZE, LEDGE) - ck_out
    kit.add("WALLS", "Brick", walls, group="walls")
    rings, _ = CO.level(OUT_PTS, ZE, EAVE, cut=ck)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="chicagobase") - ck
    kit.add("FOUNDATION", "Brick", fnd, group="foundation", change=(round((ZF - 1.8) / 0.2) * 0.2, "Limestone"),
            render=[("Brick", fnd ^ box([-50, -50, -1], [W + 50, D + 50, ZF - 1.8])), ("Limestone", fnd - box([-50, -50, -1], [W + 50, D + 50, ZF - 1.8]))])
    ins_keep = []
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        b = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        name = f"{key}-{op.name}"
        world, P, zones = O.place(sp, A, "Green", "Door" if op.kind == "door" else "Green", "Glass")
        k_ = M.cube([400.0, 400.0, 20.0]).translate([-200.0, -200.0, 0.0]).transform(A)
        zones = [(c_, m_ - k_) for c_, m_ in zones] + [("Limestone", world ^ k_)]
        part = kit.add(name, "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                       group="inserts", render=zones, change=(O.PLUG, "Limestone"))
        ins_keep.append(part.solid)
    print("walls + cornice + inserts", round(time.time() - t0, 1))

    # --- the roof: a low hip over the house and the bay, T-lock shingles, two bellcast dormers
    bay_roof = [(BX0, 30.0), (BX0, 0.0), (BX0 + BD, -BD), (BX1 - BD, -BD), (BX1, 0.0), (BX1, 30.0)]
    pieces = [(MAIN.pts, [0, 1, 2, 3], S), (bay_roof, [1, 2, 3], S)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, [], texture="tlock", tex_kw=dict(pitch=1.8, wtab=3.0, d=0.38),
                       inner_cs=offset(MAIN.cs, -3.0), fascia=FASCIA, hollow=2.8)
    roof = rf["body"] + rf["tex"]
    zr = Z_EAVE + S * (D / 2 + D_EAVE)
    ends = [(D / 2, YC), (W - D / 2, YC)] if W >= D else [(W / 2, W / 2), (W / 2, D - W / 2)]
    corners = [(-D_EAVE, -D_EAVE), (W + D_EAVE, -D_EAVE), (W + D_EAVE, D + D_EAVE), (-D_EAVE, D + D_EAVE)]
    cend = [ends[0], ends[1], ends[1], ends[0]]
    roof = roof + G.ridge_cap(ends[0], ends[1], zr, S, ZW, half=1.3, up=0.7)
    roof = roof + union([G.hip_cap((c[0], c[1], Z_EAVE), (e[0], e[1], zr), half=1.3, up=0.7, drop=1.8) for c, e in zip(corners, cend)])
    roof = roof - lip_keep(base, 3.0, ZW)
    roof = roof.trim_by_plane([0, 0, 1.0], Z_EAVE - FASCIA)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S, D_EAVE, texture=None, zlo=ZW)
    DW, DDEP, DHW = 26.0, 14.0, 10.0
    dyf = 14.0
    zdf = round((Z_EAVE + S * (dyf + D_EAVE) - 1.0) / 0.2) * 0.2
    dbody, dcore, dface = CR2.dormer_bellcast(DW, DDEP, DHW)
    droof = CR2.dormer_bellcast_roof(DW, DDEP, DHW)
    up_ = (0.0, 0.0, 1.0)
    dA = [_frame((1, 0, 0), up_, (0, -1, 0), (DOOR_X - 2.0, dyf, zdf)), _frame((-1, 0, 0), up_, (0, 1, 0), (XC, D - dyf, zdf))]
    for Ad in dA:
        dkeep = ext(dface.offset(0.3), -DDEP - 0.3, 0.3).transform(Ad)
        dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
        seat = box([-DW / 2 - 1.3, ZW - zdf, -DDEP - 1.3], [DW / 2 + 1.3, 0.0, 1.6]).transform(Ad) ^ solid_env
        roof = roof - dpocket + (seat - dpocket - lip_keep(base, 3.0, ZW)) - dbody.transform(Ad)
    roof = roof - ck
    kit.add("ROOF", "Roof", roof, group="roof")
    for k, Ad in enumerate(dA):
        kit.add(f"DORMER-{k}", "Brick", dbody.transform(Ad), key="DORMER", group="roof")
        kit.add(f"DORMER-core-{k}", "Roof", dcore.transform(Ad), key="DORMER-core", group="roof")
        dr = droof.transform(Ad) - solid_env - dbody.transform(Ad) - roof
        kit.add(f"DORMER-roof-{k}", "Roof", max(dr.decompose(), key=lambda m_: m_.volume()), key="DORMER-roof", group="roof")
    chim = CR2.chimney_chicago(zr + 8.0, ZE - 3.2).transform(np.array([[0, 1.0, 0, W], [-1.0, 0, 0, CHY], [0, 0, 1.0, 0]]))
    kit.add("CHIMNEY", "Brick", chim, group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the stoop: steps between brick cheek walls with limestone copings, one part
    e, u = MAIN.locate(DOOR_X, 0.0)
    f = MAIN.facades()[e]
    A = f.A.copy()
    A[:, 3] = f.world(u, -ZF, 1.4)
    rise = ZF - 0.6
    st_ = FT.steps(16.0, rise, 6, cheek=2.6)
    stoop = st_.transform(A) - fnd - walls
    brick = (box([-60.0, -1.0, -1.0], [-8.0, rise + 0.4, 60.0]) + box([8.0, -1.0, -1.0], [60.0, rise + 0.4, 60.0])).transform(A)
    kit.add("STOOP", "Limestone", stoop, group="steps", render=[("Limestone", stoop - brick), ("Brick", stoop ^ brick)])
    e, u = MAIN.locate(96.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Limestone", FT.steps(14.0, ZF - 0.6, 5).transform(A) - fnd, group="steps")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "pullman")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "pullman.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
