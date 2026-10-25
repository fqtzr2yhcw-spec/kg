"""The Lakeshore Freight House: an original HO-scale (1:87.1) railroad freight house, building 65
(the railroad and town batch).

A long one-storey freight shed of about 1890 at car-floor height on a timber crib, in shiplap of
alternating wide and narrow courses painted mineral red, under a low gable of rolled roofing
whose deep eaves reach out over the loading docks on long solid braces. Planked docks run the
length of both sides on cribbed timber faces, with steps at the west end. Three sliding freight
doors on each side (cross-bucked leaves filled with diagonal boards, hung from tracks under
sheet-iron hoods) and one in the east end; the agent's office in the west end with a four-light
door and four-pane windows; LAKESHORE FREIGHT on a long board over the track-side doors; a
stovepipe for the office stove. The eave cornice is riveted plates tied by bars over a course of
bolt heads, on the braces.

usage: python3 -m hoarch.buildings.lakeshore [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, slab, union
from hoarch import cornice as CO, features as FT, gables as G, openings as O, town as TN
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Lakeshore Freight House"
COLORS = {"Oxide": "#8A3A2A", "Cream": "#EDE2C6", "Iron": "#3A3A3A", "Tar": "#474747", "Crib": "#6B5440",
          "PorchDeck": "#7A6650", "Windows_Doors": "#EDE2C6"}
RENDER_MAT = {"Oxide": "siding", "Cream": "trim", "Iron": "iron", "Tar": "roof", "Crib": "crib", "PorchDeck": "deck",
              "Planks": "planks", "Windows_Doors": "trim", "Door": "door", "Glass": "glass", "Letters": "iron"}
PALETTE = {"siding": ("#8A3A2A", 0.85), "trim": ("#EDE2C6", 0.5), "iron": ("#2E2E2E", 0.5), "roof": ("#474747", 0.9),
           "crib": ("#6B5440", 0.9), "deck": ("#6E5B48", 0.85), "planks": ("#8C7456", 0.85), "door": ("#8A3A2A", 0.7)}
VIEWS = {"hero": [-30, 16, 70, 0.95, [0, 0, 0]], "front": [0, 6, 80, 0.92, [0, 0, 0]], "rear": [150, 18, 70, 0.95, [0, 0, 0]],
         "right": [60, 12, 70, 0.95, [0, 0, 0]]}

# ------------------------------------------------------------------ the eave cornice (unique to the Lakeshore)
LEDGE = 1.4
EAVE = dict(pitch=16.0, margin=6.0, layers=[
    dict(kind="frieze", h=5.0, b=1.2, orn="rivetplates", role="Cream"),
    dict(kind="course", h=1.6, b=1.4, orn="boltheads", role="Iron"),
    dict(kind="bed", h=2.6, b=1.4, P=11.2, role="Cream", brackets=dict(style="dockbrace", t=1.6, reach=0.5)),
    dict(kind="crown", h=2.0, b=1.4, P=11.6, orn="bevel", role="Oxide")])
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 14.0                                       # the floor at car-floor height, level with the docks
ZE = ZF + 42.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 12.0, 5.0, 1.8
S_MAIN = 0.4
W, D = 190.0, 70.0
YC = D / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
DK = 18.0                                       # the docks' depth
FW, FH = 20.0, 28.0                             # the freight doors
SIGN_X, SIGN_V, SIGN_L, SIGN_H = 105.0, 33.0, 100.0, 5.0
PIPE = (22.0, YC + 8.0)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    fd = TN.door_freightx(FW, FH)
    win = TN.window_freight(10.0, 14.0)
    for x in (60.0, 105.0, 150.0):
        add(x, 0.0, 0.4, fd, f"freight-S{x:.0f}", "door")
        add(x, D, 0.4, fd, f"freight-N{x:.0f}", "door")
    add(W, 25.0, 0.4, fd, "freight-E", "door")
    add(30.0, 0.0, 0.4, TN.door_office(10.0, 24.0), "office-S", "door")
    add(14.0, 0.0, 10.0, win, "S14")
    for x in (16.0, 34.0):
        add(x, D, 10.0, win, f"N{x:.0f}")
    add(0.0, YC, 0.4, TN.door_office(10.0, 24.0), "office-W", "door")
    for y in (14.0, 56.0):
        add(0.0, y, 10.0, win, f"W{y:.0f}")
    return L


OPENINGS = _openings()


def _fields(f):
    """Plain fields in the shiplap: the sliding doors' hardware and the long sign board."""
    out = []
    for op in OPENINGS:
        if op.name.startswith("freight") and np.allclose(MAIN.facades()[op.edge].n, f.n):
            out.append(TN.rect(op.u - FW / 2 - 2.2, op.v0 - 0.2, op.u + FW / 2 + FW * 0.85 + 0.8, op.v0 + FH + 3.8))
    if np.allclose(MAIN.facades()[0].n, f.n):
        e, u = MAIN.locate(SIGN_X, 0.0)
        out.append(TN.rect(u - SIGN_L / 2 - 0.3, SIGN_V - 0.3, u + SIGN_L / 2 + 0.3, SIGN_V + SIGN_H + 0.3))
    return out


def _skin(f, b, reg):
    reg = reg - TN.rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    for fl in _fields(f):
        reg = reg - fl
    return TN.shiplap_alternating(reg, datum=0.0)


def _dock(pts, runs, steps_run):
    H_floor = ZF - 0.2
    PP = FT.porch_turned(pts, runs, H_floor, 20.0, steps_at=[(steps_run, DK / 2, 12.0)], over=0.0, inset=2.0,
                         rail=None, planks=dict(pitch=1.8, border=1.2), post="depot", skirt="dockcrib",
                         pier_tex="plain", top=False)
    return PP


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    pieces = [(MAIN.pts, [0, 2], S_MAIN)]
    gdefs = [dict(p0=(W, 0.0), p1=(W, D), slope=S_MAIN, e=0.3), dict(p0=(0.0, D), p1=(0.0, 0.0), slope=S_MAIN, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="rolllap", tex_kw=dict(pitch=3.2, wtab=3.2, d=0.35),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    we, ww = rf["walls"]
    gables = [(MAIN, 1, we["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 3, ww["cs"].translate((0.0, Z_EAVE - ZF)))]
    undress = [slab(offset(base, 13.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    walls = wall_shell(BLOCKS, OPENINGS, t=3.0, belt=None, corners="none", water_table=False, siding=_skin,
                       gables=gables, undress=undress, partitions=[((36.0, 3.0), (36.0, D - 3.0), 2.0, ZF, ZW)])
    walls = walls - lip_keep(base, 3.0, ZF, 1.2)
    no_lip = union([box([-1, -20, ZW - 1], [5.0, D + 20, ZW + 5]), box([W - 5.0, -20, ZW - 1], [W + 1, D + 20, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    walls = walls + lip + CO.ledge(MAIN.pts, ZE, LEDGE)
    walls = walls - union([O.place(op.spec, op.local_frame(), "Windows_Doors", "Door", "Glass")[0]
                           for op in OPENINGS if op.name.startswith("freight")])
    kit.add("WALLS", "Oxide", walls, group="walls")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="crib")
    kit.add("FOUNDATION", "Crib", fnd, group="foundation")
    ins_keep = []
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        b = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if op.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P,
                       key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{op.name[:6]}", group="inserts", render=zones)
        ins_keep.append(part.solid)
    f = MAIN.facades()[0]
    e, u = MAIN.locate(SIGN_X, 0.0)
    A = f.A.copy()
    A[:, 3] = f.world(u, SIGN_V, 0.0)
    sb, letters = TN.sign_freight("LAKESHORE FREIGHT", SIGN_L, SIGN_H, cap=3.2)
    kit.add("SIGN", "Cream", sb.transform(A), P=np.column_stack([np.vstack([A[:, 0], A[:, 1], A[:, 2]]), np.zeros(3)]),
            group="signs", render=[("Cream", (sb - letters).transform(A)), ("Letters", letters.transform(A))])
    print("walls + cornice + inserts", round(time.time() - t0, 1))

    # --- the roof: rolled roofing on a low gable, a ridge cap, the office stovepipe
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((-RAKE, YC), (W + RAKE, YC), zr, S_MAIN, ZW) - walls_env)
    px, py = PIPE
    zp = Z_EAVE + S_MAIN * (D - py + D_EAVE) - 4.0
    pipe = (M.cylinder(zr + 14.0 - zp, 1.3, 1.3, 24).translate([px, py, zp]) +
            M.cylinder(1.2, 3.0, 1.4, 24).translate([px, py, zp + 4.4]) +
            M.cylinder(1.0, 2.6, 0.4, 24).translate([px, py, zr + 14.0]) + M.cylinder(0.6, 1.3, 1.3, 24).translate([px, py, zr + 13.99 - 0.6]))
    roof = roof - lip_keep(base, 3.0, ZW) - M.cylinder(80.0, 1.5, 1.5, 24).translate([px, py, ZW]) - pipe
    kit.add("ROOF", "Tar", max(roof.decompose(), key=lambda m_: m_.volume()), group="roof")
    kit.add("STOVEPIPE", "Iron", pipe, group="roof")
    print("roof", round(time.time() - t0, 1))

    # --- the docks: planks on cribbed faces, steps at the west end of each
    fkeep = slab(offset(base, 2.0), -1, ZF + 1.3)                      # clear of the crib's timber ends
    s_pts = [(0.0, 0.0), (0.0, -DK), (W, -DK), (W, 0.0)]
    s_runs = [dict(a=(0.0, 0.0), b=(0.0, -DK), posts=[3.4, DK - 2.0]), dict(a=(0.0, -DK), b=(W, -DK), posts=[2.0, W - 2.0]),
              dict(a=(W, -DK), b=(W, 0.0), posts=[2.0, DK - 3.4])]
    n_pts = [(0.0, D), (W, D), (W, D + DK), (0.0, D + DK)]
    n_runs = [dict(a=(W, D), b=(W, D + DK), posts=[3.4, DK - 2.0]), dict(a=(W, D + DK), b=(0.0, D + DK), posts=[2.0, W - 2.0]),
              dict(a=(0.0, D + DK), b=(0.0, D), posts=[2.0, DK - 3.4])]
    for tag, pts, runs, sr in (("S", s_pts, s_runs, 0), ("N", n_pts, n_runs, 2)):
        PP = _dock(pts, runs, sr)
        deck = PP["deck"] - fkeep
        kit.add(f"DOCK-{tag}", "PorchDeck", deck, P=print_flip(), group="docks",
                render=FT.plank_zones(deck, ZF - 0.2, "Planks", "PorchDeck"))
        for k, (sm, A) in enumerate(PP["steps"]):
            kit.add(f"DOCK-{tag}-steps", "Crib", sm.transform(A) - fkeep - deck, group="docks")
            FT.key_into(kit, f"DOCK-{tag}-steps", [f"DOCK-{tag}"], (1, 0, 0), depth=0.8, conform=True)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "lakeshore")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "lakeshore.npz"))
    import json
    json.dump({"materials": {k: [h, r, 0.0] for k, (h, r) in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
