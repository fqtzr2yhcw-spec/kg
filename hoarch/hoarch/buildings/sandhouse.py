"""The Blackwater Sand House: an original HO-scale (1:87.1) locomotive sanding plant, building 73
(the engine terminal batch).

A brick sand-drying house of about 1895 in English bond, soldier courses at the sills and under
the eave, on tooled granite; segmental windows of six over six lights under rowlock arches with
keystones, a boarded door with a transom, and at the west end a pair of diagonal-boarded doors
under a heavy lintel where the wet sand is shovelled in from an open plank bin. The drying
stove's brick stack rises through a roof of tar paper held by battens. In front, by the track,
the sand tower: a riveted steel bin with a coned hopper on four splayed, X-braced legs, the air
pipe up one leg, two telescoping spouts raking out over the track. The eave cornice: sand domes
on a pipe over a strap of paired rivets, on cove brackets.

usage: python3 -m hoarch.buildings.sandhouse [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, rect, slab, union
from hoarch import cornice as CO, gables as G, openings as O, roof as R, yard as YD
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Blackwater Sand House"
COLORS = {"Brick": "#8E3F2C", "Bone": "#D8CCAE", "Iron": "#2B2B2B", "Tar": "#3F3C39", "Stone": "#A8A190", "Steel": "#4E5358",
          "Timber": "#5B4734", "Sand": "#C8B07A", "Windows_Doors": "#D8CCAE"}
RENDER_MAT = {"Brick": "brick", "Bone": "trim", "Iron": "iron", "Tar": "roof", "Stone": "stone", "Steel": "steel",
              "Timber": "timber", "Sand": "sand", "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}
PALETTE = {"brick": ("#8E3F2C", 0.9, 0.0), "trim": ("#D8CCAE", 0.55, 0.0), "iron": ("#2B2B2B", 0.45, 0.3),
           "roof": ("#3F3C39", 0.9, 0.0), "stone": ("#A8A190", 0.9, 0.0), "steel": ("#4E5358", 0.5, 0.35),
           "timber": ("#5B4734", 0.9, 0.0), "sand": ("#C8B07A", 0.95, 0.0), "door": ("#5A2A20", 0.7, 0.0)}
VIEWS = {"hero": [-34, 14, 60, 0.95, [0, 0, 0]], "front": [0, 6, 70, 0.92, [0, 0, 0]], "rear": [150, 16, 60, 0.95, [0, 0, 0]]}

# ------------------------------------------------------------------ the eave cornice (unique to the sand house)
LEDGE = 1.4
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="sanddomes", role="Bone"),
    dict(kind="course", h=1.6, b=1.4, orn="rivetpairs", role="Iron"),
    dict(kind="bed", h=2.4, b=1.4, P=6.0, role="Bone", brackets=dict(style="sandcove", t=1.6, reach=0.5)),
    dict(kind="crown", h=2.0, b=1.4, P=6.4, orn="torus", role="Iron")])
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 5.0
ZE = ZF + 26.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 5.0, 3.5, 1.6
S_MAIN = 0.65
W, D = 64.0, 30.0
YC = D / 2
MAIN = Block("house", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
ZR = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
CHIM = (12.0, YC + 4.5)

TX, TY = 44.0, -17.0                     # the sand tower
T_S, T_H, Z_TF = 17.0, 58.0, 4.0         # its legs' spread and height, the footings' tops
BIN_R, BIN_H, HOP = 11.0, 18.0, 9.0
WB = (-19.0, 8.0)                        # the wet-sand bin


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    win = YD.window_sand(8.0, 13.0)
    for x in (8.0, 24.0, 56.0):
        add(x, 0.0, 9.0, win, f"S{x:.0f}")
    add(38.0, 0.0, 0.4, YD.door_sand(10.0, 22.0), "front", "door")
    for x in (16.0, 48.0):
        add(x, D, 9.0, win, f"N{x:.0f}")
    add(W, YC, 9.0, win, "E")
    add(0.0, YC, 0.4, YD.door_sandbin(16.0, 20.0), "wet-sand", "door")
    return L


OPENINGS = _openings()


def _skin(f, b, reg):
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    return YD.brick_english(reg, datum=0.0, soldiers=(6.2, ZE - LEDGE - 0.6 - b.z0 - 2.6))


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    pieces = [(MAIN.pts, [0, 2], S_MAIN)]
    gdefs = [dict(p0=(W, 0.0), p1=(W, D), slope=S_MAIN, e=0.3), dict(p0=(0.0, D), p1=(0.0, 0.0), slope=S_MAIN, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="tarbatten", tex_kw=dict(pitch=4.2, wtab=5.0, d=0.3),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    we, ww = rf["walls"]
    gables = [(MAIN, 1, we["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 3, ww["cs"].translate((0.0, Z_EAVE - ZF)))]
    undress = [slab(offset(base, 10.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    walls = wall_shell(BLOCKS, OPENINGS, t=3.0, belt=None, corners="none", water_table=False, siding=_skin,
                       gables=gables, undress=undress)
    walls = walls - lip_keep(base, 3.0, ZF, 1.2)
    no_lip = union([box([-1, -20, ZW - 1], [5.0, D + 20, ZW + 5]), box([W - 5.0, -20, ZW - 1], [W + 1, D + 20, ZW + 5])])
    walls = walls + ((_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip) + CO.ledge(MAIN.pts, ZE, LEDGE)
    kit.add("WALLS", "Brick", walls, group="walls")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="tooled")
    kit.add("FOUNDATION", "Stone", fnd, group="foundation")
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        bb = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if op.kind == "door" else "Windows_Doors", "Glass")
        kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P, key=f"{key}-{bb[2] - bb[0]:.1f}x{bb[3] - bb[1]:.1f}-{op.name[:5]}",
                group="inserts", render=zones)
    print("walls + cornice + inserts", round(time.time() - t0, 1))

    # --- the roof: tar paper on battens, a ridge roll, the stove's stack on a flat seat
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((-RAKE, YC), (W + RAKE, YC), ZR, S_MAIN, ZW, half=1.2, up=0.7) - walls_env)
    roof = (roof - lip_keep(base, 3.0, ZW)).trim_by_plane([0, 0, 1.0], ZW)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    cx, cy = CHIM
    CW = 7.0
    zc = Z_EAVE + S_MAIN * (D + D_EAVE - cy - CW / 2 - 0.4)
    z0 = round((zc - 5.0) / 0.2) * 0.2
    roof = roof + (box([cx - CW / 2 - 1.8, cy - CW / 2 - 1.8, ZW + 0.01], [cx + CW / 2 + 1.8, cy + CW / 2 + 1.8, ZR + 60]) ^ solid_env)   # up into the shell: joined to it
    roof = roof - box([cx - CW / 2 - 0.6, cy - CW / 2 - 0.6, z0], [cx + CW / 2 + 0.6, cy + CW / 2 + 0.6, ZR + 60])
    kit.add("ROOF", "Tar", roof, group="roof")
    kit.add("CHIMNEY", "Brick", YD.chimney_sand(CW, CW, ZR + 10.0 - z0).translate([cx, cy, z0]), group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the sand tower: footings, legs, bin, cap, spouts
    s2 = T_S / 2
    pad = box([TX - s2 - 4.0, TY - s2 - 4.0, 0.0], [TX + s2 + 4.0, TY + s2 + 4.0, 1.6])
    socks = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = TX + sx * s2, TY + sy * s2
            pad = pad + M.hull_points([(x + a * 2.6, y + c * 2.6, 1.59) for a in (-1, 1) for c in (-1, 1)] +
                                      [(x + a * 1.6, y + c * 1.6, Z_TF) for a in (-1, 1) for c in (-1, 1)])
            socks.append(box([x - 0.75, y - 0.75, Z_TF - 1.8], [x + 0.75, y + 0.75, Z_TF + 0.1]))
    kit.add("TOWER-FOOTINGS", "Stone", pad - union(socks), group="foundation")
    legs = YD.sand_legs(T_H, T_S, open_face=-1).translate([TX, TY, Z_TF])
    kit.add("TOWER-LEGS", "Steel", legs, P=print_flip(), group="tower")
    z_plate = Z_TF + T_H + 1.6
    zo = z_plate - HOP                                     # the outlet
    kit.add("TOWER-BIN", "Steel", YD.sand_bin(BIN_R, BIN_H, HOP).translate([TX, TY, zo]), P=print_flip(), group="tower")
    kit.add("TOWER-CAP", "Steel", YD.sand_cap(BIN_R).translate([TX, TY, zo + HOP + BIN_H]), group="tower-top")
    kit.add("SPOUTS", "Iron", YD.sand_spouts().translate([TX, TY, zo]), group="tower")
    # --- the wet-sand bin at the west end, heaped with sand
    wbin, heap = YD.wetbin(20.0, 16.0, 9.0)
    kit.add("WET-BIN", "Timber", wbin.translate([WB[0], WB[1], 0.0]), group="yard")
    kit.add("SAND-HEAP", "Sand", heap.translate([WB[0], WB[1], 0.0]), group="yard")
    print("tower + bin", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "sandhouse")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "sandhouse.npz"))
    import json
    json.dump({"materials": {k: list(v) for k, v in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
