"""Engine Company No. 3: an original HO-scale (1:87.1) village engine house, building 64 (the
railroad and town batch).

A two-storey firehouse of about 1884 in buff brick laid in American common bond, banded with red
soldier courses, on a bevelled granite water table, under a front gable of pressed-tin shingles.
Two tall round-arched apparatus doors (leaves of six lights over cross-braced panels, radiating
fanlights, two rowlock rings and stone keystones on impost blocks) open onto a sloping apron of
granite setts; three tall segmental-headed windows above; ENGINE No. 3 on an arch-topped stone
in the gable. A hose-drying tower rises at the back corner with slit lights and louvred vents
to a pyramid of pressed tin and a ball finial. Cornices of flame tongues over a ladder course
(the storey joint) and of Maltese crosses tied by a hose rope, on pike-hook brackets (the eave
and the tower).

usage: python3 -m hoarch.buildings.engine3 [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, slab, union
from hoarch import cornice as CO, features as FT, gables as G, openings as O, roof as R, town as TN
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "Engine Company No. 3"
COLORS = {"Buff": "#D4B97F", "Red": "#8C2F24", "Stone": "#BDB5A3", "Cream": "#EFE5CC", "Tin": "#6F767B", "Granite": "#8E8C87",
          "Windows_Doors": "#EFE5CC"}
RENDER_MAT = {"Buff": "brick", "Red": "red", "Stone": "stone", "Cream": "trim", "Tin": "roof", "Granite": "granite",
              "Windows_Doors": "trim", "Door": "door", "Glass": "glass", "Letters": "red"}
PALETTE = {"brick": ("#D4B97F", 0.9), "red": ("#8C2F24", 0.7), "stone": ("#BDB5A3", 0.85), "trim": ("#EFE5CC", 0.5),
           "roof": ("#6F767B", 0.55), "granite": ("#8E8C87", 0.9), "door": ("#8C2F24", 0.55)}
VIEWS = {"hero": [-34, 14, 70, 0.95, [0, 0, 0]], "front": [0, 6, 80, 0.92, [0, 0, 0]], "rear": [150, 16, 70, 0.95, [0, 0, 0]],
         "right": [60, 12, 70, 0.95, [0, 0, 0]]}

# ------------------------------------------------------------------ cornices (unique to Engine No. 3)
LEDGE = 1.4
JOINT = dict(pitch=10.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="flames", role="Red"),
    dict(kind="course", h=1.6, b=1.4, orn="rungs", role="Stone"),
    dict(kind="crown", h=2.0, b=1.4, P=3.4, orn="stepped", role="Red")])
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.4, b=1.2, orn="maltese", role="Red"),
    dict(kind="course", h=1.6, b=1.4, orn="rungs", role="Stone"),
    dict(kind="bed", h=2.4, b=1.4, P=7.6, role="Cream", brackets=dict(style="hook", t=1.6, reach=0.5)),
    dict(kind="crown", h=2.0, b=1.4, P=8.0, orn="bevel", role="Red")])
TOWER_C = dict(pitch=7.0, margin=2.6, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="maltese", role="Red"),
    dict(kind="course", h=1.6, b=1.4, orn="rungs", role="Stone"),
    dict(kind="crown", h=2.0, b=1.4, P=3.8, orn="stepped", role="Red")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 6.0
S1 = ZF + 46.0
ZE = S1 + RJ + 34.0
ZW = round((ZE + HE) / 0.2) * 0.2
ZT = ZW + 68.0
ZTW = round((ZT + CO.band_height(TOWER_C)) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 8.4, 5.0, 1.8
S_MAIN = 0.7
W, D = 110.0, 150.0
XC = W / 2
TX0, TX1, TY0, TY1 = -10.0, 12.0, D - 46.0, D - 24.0
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
TOWER = Block("tower", [(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)], ZF, ZTW)
BLOCKS = [MAIN, TOWER]
V1 = 10.0
V2 = S1 + RJ + 5.0 - ZF
SOLDIERS = (V1 - 2.4, V1 + 20.0 + 3.2, V2 - 3.0, V2 + 25.2)
TAB_V, TAB_L, TAB_H = Z_EAVE - ZF + 5.0, 40.0, 6.0      # the name stone in the front gable
CHIM = (XC + 16.0, D - 22.0)


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    lo = TN.window_fire_lower(10.0, 20.0)
    up = TN.window_fire_upper(10.0, 22.0)
    app = TN.door_apparatus(26.0, 36.0)
    for x in (30.0, 80.0):
        add(MAIN, x, 0.0, 0.2, app, f"engine-{x:.0f}", "door")
    for x in (20.0, XC, 90.0):
        add(MAIN, x, 0.0, V2, up, f"S{x:.0f}-2")
    for y in (30.0, 62.0, 94.0, 126.0):
        add(MAIN, W, y, V1, lo, f"E{y:.0f}")
        add(MAIN, W, y, V2, up, f"E{y:.0f}-2")
    for y in (30.0, 62.0):
        add(MAIN, 0.0, y, V1, lo, f"W{y:.0f}")
    for y in (30.0, 62.0, 90.0):
        add(MAIN, 0.0, y, V2, up, f"W{y:.0f}-2")
    add(MAIN, 80.0, D, 0.4, TN.door_fire_rear(11.0, 25.0), "back-door", "door")
    add(MAIN, 30.0, D, V1, lo, "N30")
    for x in (30.0, 80.0):
        add(MAIN, x, D, V2, up, f"N{x:.0f}-2")
    slit = TN.window_hoseslit(4.0, 14.0)
    tyc = (TY0 + TY1) / 2
    for k, v in enumerate((14.0, V2 + 2.0, ZW - ZF + 16.0)):
        add(TOWER, TX0, tyc, v, slit, f"T-slit-{k}")
    lv = TN.window_hoselouvre(8.0, 14.0)
    vl = ZW - ZF + 48.0
    for (x, y, nm) in (((TX0 + TX1) / 2, TY0, "S"), (TX1, tyc, "E"), ((TX0 + TX1) / 2, TY1, "N"), (TX0, tyc, "W")):
        add(TOWER, x, y, vl, lv, f"T-vent-{nm}")
    return L


OPENINGS = _openings()


def _skin(f, b, reg):
    if b is MAIN:
        reg = reg - TN.rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
        if np.allclose(MAIN.facades()[0].n, f.n):
            reg = reg - TN.rect(f.L / 2 - TAB_L / 2 - 1.0, TAB_V - 0.2, f.L / 2 + TAB_L / 2 + 1.0, TAB_V + TAB_H + TAB_L * 0.22 + 0.4)
    else:
        reg = reg - TN.rect(-1, ZT - LEDGE - 0.6 - b.z0, f.L + 1, 999)
    return TN.brick_firehouse(reg, datum=0.0, soldiers=SOLDIERS)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    pieces = [(MAIN.pts, [1, 3], S_MAIN)]
    gdefs = [dict(p0=(0.0, 0.0), p1=(W, 0.0), slope=S_MAIN, e=0.3), dict(p0=(W, D), p1=(0.0, D), slope=S_MAIN, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="embossed", tex_kw=dict(pitch=1.9, wtab=1.9, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    ws, wn = rf["walls"]
    gables = [(MAIN, 0, ws["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 2, wn["cs"].translate((0.0, Z_EAVE - ZF)))]
    tower_keep = TOWER.solid(grow=0.2, dz0=-1, dz1=1)
    tw = TOWER.solid(grow=0.6, dz0=-5, dz1=500)
    undress = [slab(offset(base, 10.0) - offset(TOWER.cs, 1.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(TOWER.cs, 9.0), ZT - LEDGE - 0.6, ZTW + 0.01)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=gables,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress)
    w1 = st["shells"][0] - lip_keep(base, 3.0, ZF, 1.2) - lip_keep(TOWER.cs, 3.0, ZF, 1.2)
    kit.add("WALLS-1", "Buff", w1, group="walls")
    kit.add("JOINT", "Stone", st["rings"][0], group="walls")
    no_lip = union([box([-10, -10, ZW - 1], [W + 10, 5.0, ZW + 5]), box([-10, D - 5.0, ZW - 1], [W + 10, D + 10, ZW + 5]),
                    tower_keep, slab(offset(TOWER.cs, 1.0), ZW - 1, ZW + 5)])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    tring = slab((offset(TOWER.cs, -0.05) - offset(TOWER.cs, -3.0)) ^ offset(base, -3.05), S1 + RJ, ZW + 1.2)
    tring = tring - lip_keep(MAIN.cs + TOWER.cs, 3.0, S1 + RJ)
    ledge_e = CO.ledge(MAIN.pts, ZE, LEDGE) - tower_keep
    tlip = _corbel(TOWER.cs, 3.0, ZTW) + lip_ring(TOWER.cs, 3.0, ZTW)
    w2 = st["shells"][1] + lip + tring + ledge_e + CO.ledge(TOWER.pts, ZT, LEDGE) + tlip
    kit.add("WALLS-2", "Buff", w2, group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE, cut=TOWER.solid(grow=1.1, dz0=-2, dz1=2))
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(TOWER.pts, ZT, TOWER_C)
    CO.add_level(kit, rings, "CORNICE-T", "tower")
    fnd = foundation(BLOCKS, 0.0, ZF, style="bevelgranite")
    kit.add("FOUNDATION", "Granite", fnd, group="foundation")
    ins_keep = []
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        b = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if op.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P,
                       key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{op.name[:5]}", group="inserts", render=zones)
        ins_keep.append(part.solid)
    f = MAIN.facades()[0]
    A = f.A.copy()
    A[:, 3] = f.world(f.L / 2, TAB_V, 0.0)
    tab, letters = TN.tablet_fire("ENGINE No. 3", TAB_L, TAB_H, cap=3.4)
    kit.add("NAME-STONE", "Stone", tab.transform(A), P=np.column_stack([np.vstack([A[:, 0], A[:, 1], A[:, 2]]), np.zeros(3)]),
            group="walls", render=[("Stone", (tab - letters).transform(A)), ("Letters", letters.transform(A))])
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the roof: pressed tin, a ridge cap, cut round the hose tower, the stack through it
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (W / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((XC, -RAKE), (XC, D + RAKE), zr, S_MAIN, ZW) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW) - tw
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    cx, cy = CHIM
    CW = 9.0
    zc = Z_EAVE + S_MAIN * (W - cx - CW / 2 + D_EAVE - 0.4)
    z0 = round((zc - 6.0) / 0.2) * 0.2
    roof = roof + (box([cx - CW / 2 - 1.8, cy - 7.0 / 2 - 1.8, ZW + 0.01], [cx + CW / 2 + 1.8, cy + 7.0 / 2 + 1.8, z0 + 0.01]) ^ solid_env)
    roof = roof - box([cx - CW / 2 - 0.6, cy - 7.0 / 2 - 0.6, z0], [cx + CW / 2 + 0.6, cy + 7.0 / 2 + 0.6, zr + 60])
    kit.add("ROOF", "Tin", max(roof.decompose(), key=lambda m_: m_.volume()), group="roof")
    kit.add("CHIMNEY", "Buff", TN.chimney_firehouse(CW, 7.0, zr + 10.0 - z0).translate([cx, cy, z0]), group="roof")
    # --- the hose tower's pyramid and finial
    d_t = TOWER_C["layers"][-1]["P"] + 0.4
    tpts = [(TX0, TY0), (TX1, TY0), (TX1, TY1), (TX0, TY1)]
    troof, ttex = R.hip_roof([(tpts, [0, 1, 2, 3])], ZTW + 1.2, 1.3, d_t, texture="embossed",
                             tex_kw=dict(pitch=1.6, wtab=1.6, d=0.35), zlo=ZTW)
    kit.add("TOWER-roof", "Tin", (troof + ttex) - lip_keep(TOWER.cs, 3.0, ZTW), group="tower")
    apex = ZTW + 1.2 + 1.3 * ((TX1 - TX0) / 2 + d_t)
    kit.add("FINIAL", "Stone", TN.finial_blockball().translate([(TX0 + TX1) / 2, (TY0 + TY1) / 2, apex - 1.0]), group="tower")
    FT.crown(kit, "FINIAL", "TOWER-roof")
    # --- the sett apron before the engine doors, and the back step
    e, u = MAIN.locate(XC, 0.0)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.0)
    kit.add("APRON", "Granite", TN.apron_setts(84.0, 16.0, ZF - 0.2).transform(A) - fnd - union(ins_keep), group="steps")
    e, u = MAIN.locate(80.0, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STEP-back", "Granite", FT.steps(15.0, ZF - 0.6, 3).transform(A) - fnd, group="steps")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "engine3")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "engine3.npz"))
    import json
    json.dump({"materials": {k: [h, r, 0.0] for k, (h, r) in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
