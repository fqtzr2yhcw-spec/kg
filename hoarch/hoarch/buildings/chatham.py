"""The Chatham: an original HO-scale (1:87.1) Cape Cod, house 36 of the third batch.

A storey and a half under a steep side-gabled roof: weathered silver shingles (every fifth
course cut to diamond points) on a tabby foundation studded with shell. A 'cross and bible'
door under a five-light transom between pilasters sunk with lozenges and a dentilled cap, a
millstone for its doorstep; six-over-six windows under little shed hoods on knee brackets,
navy board shutters cut with pine trees; plain-capped lights in the gables. At the eave a navy
frieze of fouled anchors, a white rope course and a white cyma, running across the gable feet;
three shingle-cheeked dormers with bargeboards and drops, a centre chimney with a band of
soldier bricks and three flues, a roof of shingles in courses square and rounded. To the east
a lower wing under its own gable, its eave hung with a frieze of sailor's knots.

usage: python3 -m hoarch.buildings.chatham [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import JoinType, Manifold as M

from hoarch.core import box, cs_union, inv34, offset, poly, rect, slab, union
from hoarch import colonial as C, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit
from hoarch.ornament import ext
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Chatham"
COLORS = {"Silver": "#A5A29A", "White": "#F3F2EE", "Charcoal": "#3E4146", "Navy": "#26395A", "Brick": "#8C4B3B",
          "Tabby": "#C2B8A0", "Windows_Doors": "#F3F2EE"}
RENDER_MAT = {"Silver": "siding", "White": "trim", "Charcoal": "roof", "Navy": "shutter", "Brick": "brick2",
              "Tabby": "stone2", "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Chatham)
LEDGE = 1.4
EAVE = dict(pitch=11.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="anchors", role="Navy"),
    dict(kind="course", h=1.4, b=1.4, orn="rope", role="White"),
    dict(kind="crown", h=2.6, b=1.4, P=5.8, orn="cyma", role="White")])
WING_C = dict(pitch=10.0, margin=3.4, layers=[
    dict(kind="frieze", h=4.2, b=1.2, orn="knots", role="Navy"),
    dict(kind="crown", h=2.2, b=1.4, P=4.2, orn="ovolo", role="White")])
HE = CO.band_height(EAVE)
ROOF_TEX = ("square", "rounded")

# ------------------------------------------------------------------ levels (on the 0.2 mm grid)
ZF = 10.0
ZE = ZF + 34.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 6.4, 6.6, 1.8
S_MAIN = 1.0
WING_ZE = ZF + 28.0
WING_ZW = round((WING_ZE + CO.band_height(WING_C)) / 0.2) * 0.2
W_EAVE = WING_ZW + 1.4
D_EAVE_W, RAKE_W, S_W = 5.0, 5.2, 1.0

# ------------------------------------------------------------------ plan (x east, y north; the front faces south)
W, D = 150.0, 84.0
XC = W / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
WX1, WY0, WY1 = 194.0, 14.0, 70.0
WING = Block("wing", [(W - 3.0, WY0), (WX1, WY0), (WX1, WY1), (W - 3.0, WY1)], ZF, WING_ZW)
BLOCKS = [MAIN, WING]
WING_RIDGE = W_EAVE + S_W * ((WY1 - WY0) / 2 + D_EAVE_W)
V1 = 8.0
SHUT_CAS, SHUT_GAP = 1.0, 0.8


def _siding(f, b, reg):
    """Diamond-banded shingles; nothing in the cornice bands; the gables shingled again."""
    top = (WING_ZE if b is WING else ZE) - LEDGE - 0.6 - b.z0
    lo = reg ^ rect(-1, -1, f.L + 1, top)
    out = C.shingles_diamond_band(lo, datum=0.0)
    if b is MAIN or b is WING:
        zw = (WING_ZW if b is WING else ZW) - b.z0 + 0.2
        hi = reg ^ rect(-1, zw, f.L + 1, 999)
        if not hi.is_empty():
            out = out + C.shingles_diamond_band(hi, datum=zw)
    return out


def _openings():
    L, SH = [], []

    def add(blk, x, y, v0, sp, name, kind="window", shutters=False):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))
        if shutters:
            SH.append(name)

    lo = C.window_hooded(9.6, 18.0)
    gw = C.window_hooded(7.0, 9.0, lites=(2, 2), rows=(1, 1), hood=False)
    for x in (20.0, 44.0, W - 44.0, W - 20.0):
        add(MAIN, x, 0.0, V1, lo, f"S{x:.0f}", shutters=True)
    add(MAIN, XC, 0.0, 0.4, C.door_crossbible(11.0, 28.0), "front-door", "door")
    for x in (20.0, 50.0, 100.0):
        add(MAIN, x, D, V1, lo, f"N{x:.0f}", shutters=True)
    add(MAIN, 128.0, D, 0.4, C.door_crossbible(10.0, 26.0), "back-door", "door")
    for y in (22.0, D - 22.0):
        add(MAIN, 0.0, y, V1, lo, f"W{y:.0f}", shutters=True)
    for y in (28.0, D - 28.0):
        add(MAIN, 0.0, y, ZW - ZF + 3.0, gw, f"W{y:.0f}-gable")
    add(MAIN, W, D / 2, WING_RIDGE + 4.0 - ZF, gw, "E-gable")
    wx = (W + WX1) / 2
    wlo = C.window_hooded(9.6, 15.0)
    add(WING, wx, WY0, 6.0, wlo, "wingS")
    add(WING, wx, WY1, 6.0, wlo, "wingN")
    for y in (28.0, WY1 - 14.0):
        add(WING, WX1, y, 6.0, wlo, f"wingE{y:.0f}")
    add(WING, WX1, (WY0 + WY1) / 2, WING_ZW - ZF + 2.6, gw, "wingE-gable")
    return L, SH


OPENINGS, SHUTTERED = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    # --- the roofs first: their gable walls go into the shell
    rf = G.gabled_roof([(MAIN.pts, [0, 2], S_MAIN)], Z_EAVE, D_EAVE,
                       [dict(p0=(W, 0.0), p1=(W, D), slope=S_MAIN, e=0.3), dict(p0=(0.0, D), p1=(0.0, 0.0), slope=S_MAIN, e=0.3)],
                       texture=ROOF_TEX, tex_kw=dict(pitch=1.5, wtab=2.2, d=0.42), skin=SKIN, rake=RAKE,
                       inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.6)
    we, ww = rf["walls"]
    wpath = [(W + 0.5, WY0), (WX1, WY0), (WX1, WY1), (W + 0.5, WY1)]
    wrf = G.gabled_roof([(wpath, [0, 2], S_W)], W_EAVE, D_EAVE_W, [dict(p0=(WX1, WY0), p1=(WX1, WY1), slope=S_W, e=0.3)],
                        texture=ROOF_TEX, tex_kw=dict(pitch=1.5, wtab=2.2, d=0.42), skin=SKIN, rake=RAKE_W,
                        inner_cs=offset(WING.cs, -3.0), fascia=1.4, hollow=2.4)
    wg = wrf["walls"][0]
    gables = [(MAIN, 1, we["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 3, ww["cs"].translate((0.0, Z_EAVE - ZF))),
              (WING, 1, wg["cs"].translate((0.0, W_EAVE - ZF)))]
    wenv, _ = R.hip_roof([(wpath, [0, 2], S_W)], W_EAVE + 1.4, S_W, D_EAVE_W + 1.0, texture=None, zlo=WING_ZW - 1.0)
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(WING.cs, 8.0) - offset(base, 0.5), WING_ZE - LEDGE - 0.6, WING_ZW + 0.01),
               wenv ^ box([W - 1.0, -500, -10], [W + 2.0, 500, 500])]
    walls = wall_shell(BLOCKS, OPENINGS, t=3.0, belt=None, corners="none", water_table=False, siding=_siding,
                       gables=gables, undress=undress, partitions=[((XC - 18.0, 3.0), (XC - 18.0, D - 3.0), 2.0, ZF, ZW)])
    walls = walls - lip_keep(cs_union([b_.cs for b_ in BLOCKS]), 3.0, ZF, 1.2)
    no_lip = union([box([W - 5.0, -1, ZW - 1], [W + 1, D + 1, ZW + 5]), box([-1, -1, ZW - 1], [5.0, D + 1, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    path = max(base.to_polygons(), key=lambda L_: abs(poly(L_).area()))
    wing_lip = (_corbel(WING.cs, 3.0, WING_ZW) + lip_ring(WING.cs, 3.0, WING_ZW)) - MAIN.solid(grow=0.3, dz0=-5, dz1=5) - \
        box([WX1 - 5.0, WY0 - 1, WING_ZW - 1], [WX1 + 1, WY1 + 1, WING_ZW + 5])
    wing_ledge = CO.ledge(WING.pts, WING_ZE, LEDGE) - MAIN.solid(grow=0.2, dz0=-1, dz1=1)
    wing_zone = box([W - 1.0, WY0 - D_EAVE_W - 1.0, ZF], [W + 30.0, WY1 + D_EAVE_W + 1.0, 400.0])
    eave_ledge = CO.ledge(path, ZE, LEDGE) - wing_zone
    kit.add("WALLS", "Silver", walls + lip + eave_ledge + wing_lip + wing_ledge, group="walls")
    rings, _ = CO.level(path, ZE, EAVE, cut=wing_zone)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(WING.pts, WING_ZE, WING_C, cut=MAIN.solid(grow=0.7, dz0=-2, dz1=2))
    CO.add_level(kit, rings, "CORNICE-W", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="tabby")
    kit.add("FOUNDATION", "Tabby", fnd, group="foundation")
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}",
                group="inserts", render=zones)
        if o.name in SHUTTERED:
            w_op, h_op = b[2] - b[0], b[3] - b[1]
            left, right = C.shutters_pair(w_op, h_op, casing=SHUT_CAS, gap=SHUT_GAP, make=C.shutter_pine)
            for side, m in (("L", left), ("R", right)):
                kit.add(f"SHUTTER-{o.name}-{side}", "Navy", m.translate([0, 0, 0.44]).transform(A), P=inv34(A),
                        key=f"SHUTTER-{h_op:.1f}", group="shutters")
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the main roof: dormers in pockets, the chimney at the ridge
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((-RAKE, D / 2), (W + RAKE, D / 2), zr, S_MAIN, ZW) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW)
    solid_env, _ = R.hip_roof([(MAIN.pts, [0, 2], S_MAIN)], Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW = 12.0
    z0 = round((zr - S_MAIN * CW / 2 - 3.0) / 0.2) * 0.2
    roof = roof + (box([XC - CW / 2 - 1.2, D / 2 - CW / 2 - 1.2, ZW + 0.01], [XC + CW / 2 + 1.2, D / 2 + CW / 2 + 1.2, z0 + 0.01]) ^ solid_env)
    roof = roof - box([XC - CW / 2 - 0.5, D / 2 - CW / 2 - 0.5, z0], [XC + CW / 2 + 0.5, D / 2 + CW / 2 + 0.5, zr + 40])
    DW, DDEP, DHW = 13.0, 16.0, 11.0
    dyf = 10.0
    zdf = round((Z_EAVE + S_MAIN * (dyf + D_EAVE) - 1.0) / 0.2) * 0.2
    dbody, dcore, dface = C.dormer_cape(DW, DDEP, DHW)
    dAs = []
    for dxc in (36.0, XC, W - 36.0):
        Ad = np.array([[1.0, 0, 0, dxc], [0, 0, -1.0, dyf], [0, 1.0, 0, zdf]])
        dkeep = ext(dface.offset(0.5, JoinType.Miter, 4.0), -DDEP - 0.3, 1.0).transform(Ad)
        dpocket = dkeep ^ box([-500, -500, zdf], [500, 500, 999])
        dseat = box([dxc - DW / 2 - 1.3, dyf - 1.6, ZW], [dxc + DW / 2 + 1.3, dyf + DDEP + 1.3, zdf]) ^ solid_env
        roof = roof - dpocket + (dseat - dpocket - lip_keep(base, 3.0, ZW))
        dAs.append(Ad)
    kit.add("ROOF", "Charcoal", roof, group="roof")
    ez = DHW - 1.6 * 1.0
    rise = DW / 2
    droof_cs = poly([(-DW / 2 - 1.6, ez), (-DW / 2, ez), (-DW / 2, DHW), (0.0, DHW + rise + 0.2), (DW / 2, DHW),
                     (DW / 2, ez), (DW / 2 + 1.6, ez), (DW / 2 + 1.6, ez + 1.6), (0.0, DHW + rise + 2.2), (-DW / 2 - 1.6, ez + 1.6)])
    for k, Ad in enumerate(dAs):
        kit.add(f"DORMER-{k}", "Silver", dbody.transform(Ad), key="DORMER", group="roof")
        kit.add(f"DORMER-core-{k}", "Charcoal", dcore.transform(Ad), key="DORMER-core", group="roof")
        droof = ext(droof_cs, -DDEP - 8.0, 1.2).transform(Ad) - solid_env - dbody.transform(Ad) - roof
        kit.add(f"DORMER-roof-{k}", "Charcoal", max(droof.decompose(), key=lambda m_: m_.volume()), key="DORMER-roof", group="roof")
    kit.add("CHIMNEY", "Brick", C.chimney_soldier(CW, CW, zr + 10.0 - z0).translate([XC, D / 2, z0]), group="roof")
    # --- the wing's roof, against the main house's east gable
    wroof = wrf["body"] + wrf["tex"] + wrf["skins"] + wrf["skin_tex"]
    wx = (W + WX1) / 2
    wzr = W_EAVE + S_W * ((WY1 - WY0) / 2 + D_EAVE_W)
    wenv_g = wg["facade"].place(M.extrude(wg["cs"].offset(0.15), RAKE_W + 4.2).translate([0, 0, -3.15]))
    wroof = wroof + (G.ridge_cap((W + 0.5, (WY0 + WY1) / 2), (WX1 + RAKE_W, (WY0 + WY1) / 2), wzr, S_W, WING_ZW) - wenv_g)
    wroof = (wroof ^ box([W + 0.5, -500, -10], [500, 500, 500])) - lip_keep(WING.cs, 3.0, WING_ZW)
    kit.add("WING-roof", "Charcoal", wroof, group="roof")
    print("roofs", round(time.time() - t0, 1), "wing ridge", round(wx, 1))

    # --- a millstone for the front step, brick steps at the back door
    ms = C.millstone_step(7.0, 1.8)
    blk = box([XC - 6.0, -9.0, 0.0], [XC + 6.0, -0.6, ZF - 2.2])
    kit.add("STOOP-front", "Tabby", (blk + ms.translate([XC, -6.8, ZF - 2.21])) - fnd, group="stoop")
    e, u = MAIN.locate(128.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.8)
    kit.add("STOOP-back", "Brick", FT.steps(14.0, ZF - 0.6, 3).transform(A) - fnd, group="stoop")
    print("specks dropped:", kit.drop_specks())
    print("done", round(time.time() - t0, 1))
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "chatham")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:40]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "chatham.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
