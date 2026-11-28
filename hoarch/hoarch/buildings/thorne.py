"""The Thorne Livery: an original HO-scale (1:87.1) livery and feed stable, building 67 (the
railroad and town batch).

A tall gable-fronted stable of about 1886 in rough horizontal boards whose courses break at
random butt joints, painted sage with cream trim and bottle-green accents, on a base of river
cobbles, under a steep roof of round-cornered shingles. The big doors (a pair of framed leaves
boarded in chevrons, on long strap hinges) open under THORNE LIVERY & FEED on a swallowtail
board; the hay-loft doors in the gable open under a hay hood with a hoist beam. Stall windows of
four lights run down both sides, with two Dutch doors on the east; a ventilator cupola rides the
ridge with louvred sides and a trotting-horse weathervane over the compass points. The eave
cornice is horseshoes, points up, over a course of snaffle bits, on ogee braces.

usage: python3 -m hoarch.buildings.thorne [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, slab, union
from hoarch import cornice as CO, features as FT, gables as G, openings as O, roof as R, town as TN
from hoarch.kit import Kit
from hoarch.ornament import side_profile
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Thorne Livery"
COLORS = {"Sage": "#8E9585", "Cream": "#ECE3C9", "Green": "#2F4A3A", "Iron": "#3A3A3A", "Shingle": "#5E5A55",
          "Cobble": "#9A958B", "Windows_Doors": "#ECE3C9"}
RENDER_MAT = {"Sage": "siding", "Cream": "trim", "Green": "green", "Iron": "iron", "Shingle": "roof", "Cobble": "stone",
              "Windows_Doors": "trim", "Door": "door", "Glass": "glass", "Letters": "green"}
PALETTE = {"siding": ("#8E9585", 0.85), "trim": ("#ECE3C9", 0.5), "green": ("#2F4A3A", 0.6), "iron": ("#2E2E2E", 0.5),
           "roof": ("#5E5A55", 0.9), "stone": ("#9A958B", 0.9), "door": ("#2F4A3A", 0.65)}
VIEWS = {"hero": [-34, 14, 70, 0.95, [0, 0, 0]], "front": [0, 6, 80, 0.92, [0, 0, 0]], "rear": [150, 16, 70, 0.95, [0, 0, 0]],
         "right": [60, 12, 70, 0.95, [0, 0, 0]]}

# ------------------------------------------------------------------ the eave cornice (unique to the Thorne)
LEDGE = 1.4
EAVE = dict(pitch=12.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.2, b=1.2, orn="horseshoes", role="Green"),
    dict(kind="course", h=1.6, b=1.4, orn="snaffles", role="Iron"),
    dict(kind="bed", h=2.2, b=1.4, P=5.4, role="Cream", brackets=dict(style="ogeebrace", t=1.6, reach=0.5)),
    dict(kind="crown", h=1.8, b=1.4, P=5.8, orn="ovolo", role="Green")])
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 8.0
ZE = ZF + 58.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.4
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 6.2, 4.0, 1.8
S_MAIN = 0.95
W, D = 110.0, 150.0
XC = W / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
HAY_V = Z_EAVE - ZF + 8.0
HOOD_V = HAY_V + 15.2 + 1.2
BOARD_V, BOARD_L, BOARD_H = 40.0, 66.0, 6.0
CUP = (XC, D / 2, 18.0)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    stall = TN.window_stall(7.0, 7.0)
    add(XC, 0.0, 0.4, TN.door_stable(30.0, 34.0), "front-doors", "door")
    add(XC, 0.0, HAY_V, TN.door_hay(14.0, 14.0), "hay-door", "door")
    for x in (15.0, 95.0):
        add(x, 0.0, 20.0, stall, f"S{x:.0f}")
    for y in (18.0, 42.0, 66.0, 90.0, 114.0, 138.0):
        add(0.0, y, 30.0, stall, f"W{y:.0f}")
        add(W, y, 30.0, stall, f"E{y:.0f}")
    for y in (30.0, 102.0):
        add(W, y, 0.4, TN.door_dutch(10.0, 22.0), f"dutch-E{y:.0f}", "door")
    add(XC, D, 0.4, TN.door_stable(24.0, 30.0), "back-doors", "door")
    return L


OPENINGS = _openings()


def _skin(f, b, reg):
    reg = reg - TN.rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    if np.allclose(MAIN.facades()[0].n, f.n):
        reg = reg - TN.rect(f.L / 2 - BOARD_L / 2 - 0.3, BOARD_V - 0.3, f.L / 2 + BOARD_L / 2 + 0.3, BOARD_V + BOARD_H + 0.3)
        reg = reg - TN.poly([(f.L / 2 - 11.3, HOOD_V - 0.3), (f.L / 2 + 11.3, HOOD_V - 0.3), (f.L / 2, HOOD_V + 10.6)])
    return TN.boards_butted(reg, datum=0.0, seed=int(abs(f.n[0]) * 3 + abs(f.n[1]) * 7))


def _ramp(w, depth, rise):
    """A plank ramp up to the big doors (local: u across, v up, w out from the wall)."""
    body = side_profile([(0.0, 0.0), (depth, 0.0), (depth, 0.4), (0.0, rise)], -w / 2, w / 2)
    grooves = union([box([u - 0.12, -1.0, -1.0], [u + 0.12, rise + 2.0, depth + 1.0]) for u in np.arange(-w / 2 + 1.8, w / 2, 1.8)])
    skin = side_profile([(-1.0, rise - 0.3), (depth + 1.0, 0.1), (depth + 1.0, 2.0), (-1.0, rise + 2.0)], -w / 2 - 1, w / 2 + 1)
    return body - (grooves ^ skin)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    pieces = [(MAIN.pts, [1, 3], S_MAIN)]
    gdefs = [dict(p0=(0.0, 0.0), p1=(W, 0.0), slope=S_MAIN, e=0.3), dict(p0=(W, D), p1=(0.0, D), slope=S_MAIN, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="roundcorner", tex_kw=dict(pitch=1.8, wtab=2.2, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    ws, wn = rf["walls"]
    gables = [(MAIN, 0, ws["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 2, wn["cs"].translate((0.0, Z_EAVE - ZF)))]
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    walls = wall_shell(BLOCKS, OPENINGS, t=3.0, belt=None, corners="none", water_table=False, siding=_skin,
                       gables=gables, undress=undress)
    walls = walls - lip_keep(base, 3.0, ZF, 1.2)
    no_lip = union([box([-10, -10, ZW - 1], [W + 10, 5.0, ZW + 5]), box([-10, D - 5.0, ZW - 1], [W + 10, D + 10, ZW + 5])])
    walls = walls + ((_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip) + CO.ledge(MAIN.pts, ZE, LEDGE)
    kit.add("WALLS", "Sage", walls, group="walls")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="cobble")
    kit.add("FOUNDATION", "Cobble", fnd, group="foundation")
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
    flat = lambda A_: np.column_stack([np.vstack([A_[:, 0], A_[:, 1], A_[:, 2]]), np.zeros(3)])
    A = f.A.copy()
    A[:, 3] = f.world(f.L / 2, BOARD_V, 0.0)
    bd, letters = TN.board_livery("THORNE LIVERY & FEED", BOARD_L, BOARD_H)
    kit.add("SIGN", "Cream", bd.transform(A), P=flat(A), group="walls",
            render=[("Cream", (bd - letters).transform(A)), ("Letters", letters.transform(A))])
    A = f.A.copy()
    A[:, 3] = f.world(f.L / 2, HOOD_V, 0.0)
    hood = TN.hay_hood(22.0, 10.0, 10.0)
    kit.add("HAY-HOOD", "Green", hood.transform(A), P=flat(A), group="walls")
    print("walls + cornice + inserts", round(time.time() - t0, 1))

    # --- the roof: round-cornered shingles, a ridge cap, a seat for the cupola
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (W / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((XC, -RAKE), (XC, D + RAKE), zr, S_MAIN, ZW) - walls_env)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    cx, cy, cw = CUP
    z_seat = round((Z_EAVE + S_MAIN * (W / 2 - cw / 2 + D_EAVE) - 0.6) / 0.2) * 0.2
    roof = roof + (box([cx - cw / 2 - 1.5, cy - cw / 2 - 1.5, ZW + 0.01], [cx + cw / 2 + 1.5, cy + cw / 2 + 1.5, z_seat]) ^ solid_env)
    roof = roof - box([cx - cw / 2 - 0.15, cy - cw / 2 - 0.15, z_seat], [cx + cw / 2 + 0.15, cy + cw / 2 + 0.15, zr + 60])
    roof = roof - lip_keep(base, 3.0, ZW)
    kit.add("ROOF", "Shingle", max(roof.decompose(), key=lambda m_: m_.volume()), group="roof")
    kit.add("CUPOLA", "Cream", TN.cupola_livery(cw, zr + 3.0 - z_seat, 10.0).translate([cx, cy, z_seat]), group="roof")
    # --- plank ramps to the big doors
    for x, y, wd, nm in ((XC, 0.0, 34.0, "RAMP-front"), (XC, D, 28.0, "RAMP-back")):
        e, u = MAIN.locate(x, y)
        fb = MAIN.facades()[e]
        A = fb.A.copy()
        A[:, 3] = fb.world(u, -ZF, 1.2)
        kit.add(nm, "Cobble", _ramp(wd, 14.0, ZF - 0.2).transform(A) - fnd - union(ins_keep), group="steps")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "thorne")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "thorne.npz"))
    import json
    json.dump({"materials": {k: [h, r, 0.0] for k, (h, r) in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
