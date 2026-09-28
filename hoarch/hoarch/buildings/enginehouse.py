"""The Blackwater Engine House: an original HO-scale (1:87.1) two-stall brick engine house, building
74 (the engine terminal batch).

A two-stall engine house of about 1896, 230 mm deep for a small Consolidation and its tender, in
American-bond brick with pilasters between the bays, on stippled concrete. Each stall door is a
round-headed opening under a double rowlock arch with a stone keystone on moulded imposts, the
head filled with a fanlight; the leaves (six lights over boards, braced, strap hinges) are
separate, to glue shut or stand open for the engines. Seven round-headed windows of twelve
lights with fanlights down each side under projecting brick hoods, two at the back, and an
oculus in each gable. A roof of rough random slate with a long clerestory monitor on the ridge
and a smoke jack over each stall. The eave cornice: diamond smokestacks over a course of rails
seen end on, on stepped brick corbels.

The track in the renders is scenery for the pictures, not a part.

usage: python3 -m hoarch.buildings.enginehouse [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, rect, slab, union
from hoarch import cornice as CO, gables as G, openings as O, roof as R, yard as YD
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Blackwater Engine House"
COLORS = {"Brick": "#7E3526", "Bone": "#D8CCAE", "Iron": "#2B2B2B", "Slate": "#4F545A", "Concrete": "#A9A69E",
          "Doors": "#5E2A22", "Windows_Doors": "#D8CCAE"}
RENDER_MAT = {"Brick": "brick", "Bone": "trim", "Iron": "iron", "Slate": "roof", "Concrete": "stone", "Doors": "door",
              "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}
PALETTE = {"brick": ("#7E3526", 0.9, 0.0), "trim": ("#D8CCAE", 0.55, 0.0), "iron": ("#2B2B2B", 0.45, 0.3),
           "roof": ("#4F545A", 0.75, 0.0), "stone": ("#A9A69E", 0.9, 0.0), "door": ("#5E2A22", 0.7, 0.0),
           "ballast": ("#8C877E", 0.97, 0.0), "ties": ("#3F3328", 0.9, 0.0), "rail": ("#77716A", 0.35, 0.8)}
VIEWS = {"hero": [-34, 16, 60, 0.95, [0, 0, 0]], "front": [0, 8, 70, 0.92, [0, 0, 0]], "rear": [150, 18, 60, 0.95, [0, 0, 0]]}

# ------------------------------------------------------------------ the eave cornice (unique to the engine house)
LEDGE = 1.4
EAVE = dict(pitch=15.5, margin=6.0, layers=[
    dict(kind="frieze", h=5.4, b=1.2, orn="diamondstacks", role="Bone"),
    dict(kind="course", h=1.6, b=1.4, orn="railprofiles", role="Iron"),
    dict(kind="bed", h=2.6, b=1.4, P=7.0, role="Bone", brackets=dict(style="enginecorbel", t=1.6, reach=0.5)),
    dict(kind="crown", h=2.2, b=1.4, P=7.6, orn="cyma", role="Brick")])
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 3.0
ZE = ZF + 76.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 6.0, 4.5, 1.8
S_MAIN = 0.6
W, D = 116.0, 230.0
XC = W / 2
MAIN = Block("house", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
ZR = Z_EAVE + S_MAIN * (W / 2 + D_EAVE)
STALLS = (29.0, 87.0)
DW, DH = 42.0, 64.0
WIN_U = [22.0 + 31.0 * k for k in range(7)]
SIDE_PIERS = [3.0] + [37.5 + 31.0 * k for k in range(6)] + [D - 3.0]
MON_Y0, MON_Y1, MON_W = 25.0, 205.0, 24.0
JACKS = [(29.0, 172.0), (87.0, 172.0)]
PIER_TOP = ZE - LEDGE - 0.6 - ZF


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    arch = YD.door_engine_arch(DW, DH)
    for k, x in enumerate(STALLS):
        add(x, 0.0, 0.0, arch, f"stall{k + 1}", "door")
    win = YD.window_engine(13.0, 30.0)
    for u in WIN_U:
        add(W, u, 18.0, win, f"E{u:.0f}")
        add(0.0, D - u, 18.0, win, f"W{u:.0f}")
    for x in STALLS:
        add(x, D, 18.0, win, f"N{x:.0f}")
    oc = YD.oculus_engine(14.0)
    add(XC, 0.0, ZW - ZF + 6.0, oc, "oculus-S")
    add(XC, D, ZW - ZF + 6.0, oc, "oculus-N")
    return L


OPENINGS = _openings()


def _skin(f, b, reg):
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    if abs(f.n[0]) > 0.5:                                  # the long sides
        piers = SIDE_PIERS
    else:                                                  # the ends
        piers = [3.0, XC, W - 3.0]
    return YD.brick_american(reg, datum=0.0, piers=piers, pier_w=6.0 if abs(f.n[0]) > 0.5 else 8.0, pier_top=PIER_TOP)


def _leaf_frame(x_h, side, z0):
    """A leaf standing open at right angles to the front, just inside the doorway's edge at x_h,
    its hinge edge against the jamb band."""
    if side > 0:
        return np.array([[0.0, 0.0, -1.0, x_h + 2.0], [-1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, z0]])
    return np.array([[0.0, 0.0, 1.0, x_h - 2.0], [1.0, 0.0, 0.0, -LEAF_W], [0.0, 1.0, 0.0, z0]])


LEAF_W = DW / 2 - 0.4
LEAF_H = DH - DW / 2 - 1.3 - 0.6


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    pieces = [(MAIN.pts, [1, 3], S_MAIN)]
    gdefs = [dict(p0=(0.0, 0.0), p1=(W, 0.0), slope=S_MAIN, e=0.3), dict(p0=(W, D), p1=(0.0, D), slope=S_MAIN, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="randomslate", tex_kw=dict(pitch=2.2, wtab=3.0, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=3.0)
    ws, wn = rf["walls"]
    gables = [(MAIN, 0, ws["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 2, wn["cs"].translate((0.0, Z_EAVE - ZF)))]
    undress = [slab(offset(base, 12.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    walls = wall_shell(BLOCKS, OPENINGS, t=3.0, belt=None, corners="none", water_table=False, siding=_skin,
                       gables=gables, undress=undress)
    walls = walls - lip_keep(base, 3.0, ZF, 1.2)
    no_lip = union([box([-20, -1, ZW - 1], [W + 20, 5.0, ZW + 5]), box([-20, D - 5.0, ZW - 1], [W + 20, D + 1, ZW + 5])])
    walls = walls + ((_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip) + CO.ledge(MAIN.pts, ZE, LEDGE)
    kit.add("WALLS", "Brick", walls, group="walls")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    f0 = MAIN.facades()[0]
    fnd = foundation(BLOCKS, 0.0, ZF, style="stippled", openings=[(f0, x, -ZF - 1.0, DW, ZF + 3.0) for x in STALLS])
    kit.add("FOUNDATION", "Concrete", fnd, group="foundation")
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        bb = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Windows_Doors", "Glass")
        kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P, key=f"{key}-{bb[2] - bb[0]:.1f}x{bb[3] - bb[1]:.1f}-{op.name[:4]}",
                group="inserts", render=zones)
    # the stall doors' leaves, shown standing open
    for k, x in enumerate(STALLS):
        for side, xh in ((1, x - DW / 2), (-1, x + DW / 2)):
            leaf, gl = YD.door_engine_leaf(LEAF_W, LEAF_H, side=side)
            A = _leaf_frame(xh, side, ZF + 0.3)
            Pl = np.column_stack([np.vstack([A[:, 0], A[:, 1], A[:, 2]]), np.zeros(3)])
            glass = YD.ext(gl, 0.0, 1.21).transform(A)
            kit.add(f"LEAF-{k + 1}{'L' if side > 0 else 'R'}", "Doors", leaf.transform(A), P=Pl, key=f"LEAF-{'L' if side > 0 else 'R'}",
                    group="doors", render=[("Doors", leaf.transform(A) - glass), ("Glass", leaf.transform(A) ^ glass)])
    print("walls + cornice + inserts", round(time.time() - t0, 1))

    # --- the roof: random slate, a ridge roll at each end, flat seats for the monitor and jacks
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((XC, -RAKE), (XC, D + RAKE), ZR, S_MAIN, ZW, half=1.3, up=0.8) - walls_env)
    roof = (roof - lip_keep(base, 3.0, ZW)).trim_by_plane([0, 0, 1.0], ZW)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    z_ms = round((ZR - 8.0) / 0.2) * 0.2
    roof = roof + (box([XC - MON_W / 2 - 1.6, MON_Y0 - 1.6, ZW + 0.01], [XC + MON_W / 2 + 1.6, MON_Y1 + 1.6, z_ms + 0.01]) ^ solid_env)
    roof = roof - box([XC - MON_W / 2 - 0.8, MON_Y0 - 0.9, z_ms], [XC + MON_W / 2 + 0.8, MON_Y1 + 0.9, ZR + 60])
    jacks = []
    JW = 12.0
    for (jx, jy) in JACKS:
        dx = abs(jx - XC) + JW / 2 + 0.4
        zc = Z_EAVE + S_MAIN * (W / 2 + D_EAVE - dx)
        z0 = round((zc - 3.0) / 0.2) * 0.2
        roof = roof + (box([jx - JW / 2 - 1.6, jy - JW / 2 - 1.6, ZW + 0.01], [jx + JW / 2 + 1.6, jy + JW / 2 + 1.6, z0 + 0.01]) ^ solid_env)
        roof = roof - box([jx - JW / 2 - 0.3, jy - JW / 2 - 0.3, z0], [jx + JW / 2 + 0.3, jy + JW / 2 + 0.3, ZR + 60])
        jacks.append(YD.smokejack(JW, h0=ZR + 2.0 - z0, flue_h=22.0).translate([jx, jy, z0]))
    kit.add("ROOF", "Slate", roof, group="roof")
    mon, mglass, mh = YD.monitor_engine(MON_Y1 - MON_Y0, MON_W, 13.0)
    mon = mon.translate([XC, (MON_Y0 + MON_Y1) / 2, z_ms])
    mglass = mglass.translate([XC, (MON_Y0 + MON_Y1) / 2, z_ms])
    ch = round((mh + 0.01) / 0.2) * 0.2
    kit.add("MONITOR", "Bone", mon, group="roof", change=(ch, "Slate"),
            render=[("Bone", mon - mglass - box([-999, -999, z_ms + ch], [999, 999, 999])), ("Slate", mon ^ box([-999, -999, z_ms + ch], [999, 999, 999])),
                    ("Glass", mon ^ mglass)])
    for k, j in enumerate(jacks):
        kit.add(f"SMOKEJACK-{k + 1}", "Iron", j, key="SMOKEJACK", group="roof")
    print("roof", round(time.time() - t0, 1))
    print("specks dropped:", kit.drop_specks())
    return kit


def scenery():
    """Render-only: a track into each stall."""
    out = {}
    bal, ties, rails = [], [], []
    for x in STALLS:
        bal.append(M.hull_points([(x + dx, y, z) for y in (-90.0, D - 8.0) for (dx, z) in ((-18.0, 0.0), (18.0, 0.0), (-14.0, 2.4), (14.0, 2.4))]))
        ties += [box([x - 14.9, y - 1.3, 2.4], [x + 14.9, y + 1.3, 4.2]) for y in np.arange(-88.0, D - 10.0, 6.4)]
        rails += [box([x + s - 0.45, -90.0, 4.2], [x + s + 0.45, D - 8.0, 6.3]) for s in (-8.7, 8.7)]
    return {"ballast": union(bal), "ties": union(ties), "rail": union(rails)}


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "enginehouse")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    npz = os.path.join(OUT, "enginehouse.npz")
    kit.render_npz(npz)
    from hoarch.kit import mesh_arrays
    data = dict(np.load(npz))
    for name, m in scenery().items():
        v, f = mesh_arrays(m)
        data[name + "__v"], data[name + "__f"] = v.astype(np.float32), f.astype(np.int32)
    np.savez_compressed(npz, **data)
    import json
    json.dump({"materials": {k: list(v) for k, v in PALETTE.items()}, "views": VIEWS},
              open(os.path.join(OUT, "palette.json"), "w"), indent=1)
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
