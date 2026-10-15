"""Pleasant Valley School: an original HO-scale (1:87.1) one-room country schoolhouse, building 66
(the railroad and town batch).

A tall one-room school of about 1882, painted schoolhouse red with white corner boards, in German
(cove) siding on brick piers with lattice between, under a steep front gable of bevel-butt
shingles. The pair of four-panel doors, under a three-light transom and a gabled hood on scroll
brackets, stands in the middle of the gable front between two tall six-over-six windows, with
PLEASANT VALLEY SCHOOL on a round-ended board above; five tall windows light each side. A
louvred belfry with a flared cornice and a steep pyramid rides the front of the ridge; a brick
stove flue rises at the back. The eave cornice is hanging bellflowers over a counting-frame
course, on scroll brackets.

usage: python3 -m hoarch.buildings.pleasant [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, slab, union
from hoarch import cornice as CO, features as FT, gables as G, openings as O, roof as R, town as TN
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "Pleasant Valley School"
COLORS = {"Red": "#9B2B22", "White": "#F1EEE6", "Black": "#2B2B2B", "Shingle": "#6B5B4B", "Brick": "#8A4A3A",
          "Windows_Doors": "#F1EEE6"}
RENDER_MAT = {"Red": "siding", "White": "trim", "Black": "black", "Shingle": "roof", "Brick": "brick",
              "Windows_Doors": "trim", "Door": "door", "Glass": "glass", "Letters": "black"}
PALETTE = {"siding": ("#9B2B22", 0.85), "trim": ("#F1EEE6", 0.5), "black": ("#2B2B2B", 0.5), "roof": ("#6B5B4B", 0.9),
           "brick": ("#8A4A3A", 0.9), "door": ("#5C3A26", 0.6)}
VIEWS = {"hero": [-34, 14, 70, 0.95, [0, 0, 0]], "front": [0, 6, 80, 0.92, [0, 0, 0]], "rear": [150, 16, 70, 0.95, [0, 0, 0]],
         "right": [60, 12, 70, 0.95, [0, 0, 0]]}

# ------------------------------------------------------------------ the eave cornice (unique to Pleasant Valley)
LEDGE = 1.4
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.2, b=1.2, orn="bellflowers", role="White"),
    dict(kind="course", h=1.6, b=1.4, orn="abacus", role="Black"),
    dict(kind="bed", h=2.2, b=1.4, P=5.8, role="White", brackets=dict(style="schoolscroll", t=1.6, reach=0.5)),
    dict(kind="crown", h=1.8, b=1.4, P=6.2, orn="cyma", role="Red")])
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 10.0
ZE = ZF + 50.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 6.6, 4.0, 1.8
S_MAIN = 0.9
W, D = 100.0, 150.0
XC = W / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
V1 = 10.0
BOARD_V, BOARD_L, BOARD_H = Z_EAVE - ZF + 4.0, 56.0, 5.0
BELFRY = (XC, 16.0, 16.0)                          # x, y, width
CHIM = (XC, D - 12.0)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    win = TN.window_school(11.0, 28.0)
    add(XC, 0.0, 0.4, TN.door_school(16.0, 28.0), "front-door", "door")
    for x in (20.0, 80.0):
        add(x, 0.0, V1, win, f"S{x:.0f}")
    for y in (25.0, 50.0, 75.0, 100.0, 125.0):
        add(0.0, y, V1, win, f"W{y:.0f}")
        add(W, y, V1, win, f"E{y:.0f}")
    for x in (30.0, 70.0):
        add(x, D, V1, win, f"N{x:.0f}")
    return L


OPENINGS = _openings()


def _skin(f, b, reg):
    reg = reg - TN.rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    if np.allclose(MAIN.facades()[0].n, f.n):
        reg = reg - TN.rect(f.L / 2 - BOARD_L / 2 - 0.3, BOARD_V - 0.3, f.L / 2 + BOARD_L / 2 + 0.3, BOARD_V + BOARD_H + 0.3)
    return TN.lap_german(reg, datum=0.0, corners=(0.9, f.L - 0.9))


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    pieces = [(MAIN.pts, [1, 3], S_MAIN)]
    gdefs = [dict(p0=(0.0, 0.0), p1=(W, 0.0), slope=S_MAIN, e=0.3), dict(p0=(W, D), p1=(0.0, D), slope=S_MAIN, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="bevelbutt", tex_kw=dict(pitch=1.8, wtab=2.4, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    ws, wn = rf["walls"]
    gables = [(MAIN, 0, ws["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 2, wn["cs"].translate((0.0, Z_EAVE - ZF)))]
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    walls = wall_shell(BLOCKS, OPENINGS, t=3.0, belt=None, corners="none", water_table=False, siding=_skin,
                       gables=gables, undress=undress)
    walls = walls - lip_keep(base, 3.0, ZF, 1.2)
    no_lip = union([box([-10, -10, ZW - 1], [W + 10, 5.0, ZW + 5]), box([-10, D - 5.0, ZW - 1], [W + 10, D + 10, ZW + 5])])
    walls = walls + ((_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip) + CO.ledge(MAIN.pts, ZE, LEDGE)
    cb = union([box([x - 2.0, y - 2.0, ZF - 1], [x + 2.0, y + 2.0, ZE]) for x in (0.0, W) for y in (0.0, D)])
    kit.add("WALLS", "Red", walls, group="walls", render=[("Red", walls - cb), ("White", walls ^ cb)])
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="pierlattice")
    kit.add("FOUNDATION", "Brick", fnd, group="foundation")
    ins_keep = []
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        b = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if op.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P,
                       key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}", group="inserts", render=zones)
        ins_keep.append(part.solid)
    f = MAIN.facades()[0]
    A = f.A.copy()
    A[:, 3] = f.world(f.L / 2, BOARD_V, 0.0)
    bd, letters = TN.board_school("PLEASANT VALLEY SCHOOL", BOARD_L, BOARD_H)
    kit.add("NAME-BOARD", "White", bd.transform(A), P=np.column_stack([np.vstack([A[:, 0], A[:, 1], A[:, 2]]), np.zeros(3)]),
            group="walls", render=[("White", (bd - letters).transform(A)), ("Letters", letters.transform(A))])
    print("walls + cornice + inserts", round(time.time() - t0, 1))

    # --- the roof: bevel-butt shingles, a ridge cap, a seat for the belfry, the flue through it
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (W / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((XC, -RAKE), (XC, D + RAKE), zr, S_MAIN, ZW) - walls_env)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    bx, by, bw = BELFRY
    z_seat = round((Z_EAVE + S_MAIN * (W / 2 - bw / 2 + D_EAVE) - 0.6) / 0.2) * 0.2
    roof = roof + (box([bx - bw / 2 - 1.5, by - bw / 2 - 1.5, ZW + 0.01], [bx + bw / 2 + 1.5, by + bw / 2 + 1.5, z_seat + 0.01]) ^ solid_env)
    roof = roof - box([bx - bw / 2 - 0.15, by - bw / 2 - 0.15, z_seat], [bx + bw / 2 + 0.15, by + bw / 2 + 0.15, zr + 50])
    cx, cy = CHIM
    zc = round((zr - 5.0) / 0.2) * 0.2
    roof = roof - box([cx - 4.6, cy - 4.6, zc], [cx + 4.6, cy + 4.6, zr + 60])
    roof = roof + (box([cx - 6.0, cy - 6.0, ZW + 0.01], [cx + 6.0, cy + 6.0, zc]) ^ solid_env)
    roof = roof - lip_keep(base, 3.0, ZW)
    kit.add("ROOF", "Shingle", max(roof.decompose(), key=lambda m_: m_.volume()), group="roof")
    kit.add("BELFRY", "White", TN.belfry_school(bw, zr + 3.0 - z_seat, 11.0).translate([bx, by, z_seat]), group="roof")
    kit.add("CHIMNEY", "Brick", TN.chimney_school(8.0, 8.0, zr + 12.0 - zc).translate([cx, cy, zc]), group="roof")
    e, u = MAIN.locate(XC, 0.0)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STEPS", "Brick", FT.steps(22.0, ZF - 0.6, 4).transform(A) - fnd, group="steps")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "pleasant")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "pleasant.npz"))
    import json
    json.dump({"materials": {k: [h, r, 0.0] for k, (h, r) in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
