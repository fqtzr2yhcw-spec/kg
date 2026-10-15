"""Section House No. 4: an original pair of HO-scale (1:87.1) railroad section buildings, building 76
(the engine terminal batch): the section gang's tool house and its speeder shed.

Both are in reverse board and batten, painted mineral brown with buff trim, on heavy timber sills
over squared stone blocks, under roofs of double-coursed shingles. The tool house has a boarded
door on a Z brace with strap hinges and a hasp, six-light windows with corner blocks, and the
stove's pipe through the back slope; its eave cornice is the gang's tools (lining bar and spike
maul crossed over a tie) over a crown. The speeder shed stands gable-on to its spur, a pair of
braced doors for the motor car in the gable end; its cornice is a row of track spikes on a tie
plate under a crown.

The track and spur in the renders are scenery for the pictures, not parts.

usage: python3 -m hoarch.buildings.section4 [check] [export]
"""
import os
import sys

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, rect, slab, union
from hoarch import cornice as CO, gables as G, openings as O, yard as YD
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "Section House No. 4"
COLORS = {"Brown": "#6A3B2A", "Buff": "#D9C49A", "Iron": "#2B2B2B", "Shingle": "#4E4640", "Stone": "#9E998E",
          "Windows_Doors": "#D9C49A"}
RENDER_MAT = {"Brown": "siding", "Buff": "trim", "Iron": "iron", "Shingle": "roof", "Stone": "stone",
              "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}
PALETTE = {"siding": ("#6A3B2A", 0.85, 0.0), "trim": ("#D9C49A", 0.55, 0.0), "iron": ("#2B2B2B", 0.45, 0.3),
           "roof": ("#4E4640", 0.85, 0.0), "stone": ("#9E998E", 0.9, 0.0), "door": ("#6A3B2A", 0.7, 0.0),
           "ballast": ("#8C877E", 0.97, 0.0), "ties": ("#3F3328", 0.9, 0.0), "rail": ("#77716A", 0.35, 0.8)}
VIEWS = {"hero": [-34, 16, 60, 0.95, [0, 0, 0]], "front": [0, 8, 70, 0.92, [0, 0, 0]], "rear": [150, 18, 60, 0.95, [0, 0, 0]]}

LEDGE = 1.4
EAVE_T = dict(pitch=11.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.0, b=1.2, orn="trackgang", role="Buff"),
    dict(kind="crown", h=1.8, b=1.4, P=3.6, orn="bevel", role="Brown")])
EAVE_S = dict(pitch=10.0, margin=3.0, layers=[
    dict(kind="course", h=1.6, b=1.2, orn="spikes", role="Iron"),
    dict(kind="crown", h=1.8, b=1.4, P=3.4, orn="ovolo", role="Buff")])
ZF = 3.0
FASCIA = 1.2
S_ROOF = 0.75

TOOL = Block("tool", [(0, 0), (34, 0), (34, 22), (0, 22)], ZF, 0.0)
SPEED = Block("speeder", [(52, 0), (74, 0), (74, 32), (52, 32)], ZF, 0.0)
SHEDS = {
    "TOOL": dict(blk=TOOL, ze=ZF + 24.0, spec=EAVE_T, eaves=[0, 2], gables=[1, 3], d_eave=3.6, rake=2.6),
    "SPEEDER": dict(blk=SPEED, ze=ZF + 24.0, spec=EAVE_S, eaves=[1, 3], gables=[0, 2], d_eave=3.4, rake=2.6),
}
for s_ in SHEDS.values():
    s_["zw"] = round((s_["ze"] + CO.band_height(s_["spec"])) / 0.2) * 0.2
    s_["blk"].z1 = s_["zw"]
STOVE = (6.0, 16.0)


def _openings(key):
    sh = SHEDS[key]
    blk = sh["blk"]
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    win = YD.window_section(7.0, 9.0)
    if key == "TOOL":
        add(11.0, 0.0, 0.4, YD.door_toolhouse(9.0, 19.0), "tool-door", "door")
        add(25.0, 0.0, 9.0, win, "tool-S")
        add(34.0, 11.0, 9.0, win, "tool-E")
        add(17.0, 22.0, 9.0, win, "tool-N")
    else:
        add(63.0, 0.0, 0.4, YD.door_speeder(16.0, 18.0), "speeder-doors", "door")
        add(74.0, 20.0, 9.0, win, "speeder-E")
    return L


def _skin_for(key):
    sh = SHEDS[key]

    def skin(f, b, reg):
        reg = reg - rect(-1, sh["ze"] - LEDGE - 0.6 - b.z0, f.L + 1, sh["zw"] - b.z0 + 0.2)
        return YD.reverse_batten(reg, datum=0.0, pitch=3.0)
    return skin


def _gdefs(blk, edges, slope):
    out = []
    P = blk.pts
    for e in edges:
        out.append(dict(p0=tuple(P[e]), p1=tuple(P[(e + 1) % len(P)]), slope=slope, e=0.3))
    return out


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    for key, sh in SHEDS.items():
        blk = sh["blk"]
        base = blk.cs
        ops = _openings(key)
        z_eave = sh["zw"] + FASCIA
        rf = G.gabled_roof([(blk.pts, sh["eaves"], S_ROOF)], z_eave, sh["d_eave"], _gdefs(blk, sh["gables"], S_ROOF),
                           texture="doublecourse", tex_kw=dict(pitch=1.8, wtab=2.4, d=0.35), skin=1.4, rake=sh["rake"],
                           inner_cs=offset(base, -2.4), fascia=FASCIA, hollow=2.2)
        gables = [(blk, e, wl["cs"].translate((0.0, z_eave - ZF))) for e, wl in zip(sh["gables"], rf["walls"])]
        walls = wall_shell([blk], ops, t=2.4, belt=None, corners="none", water_table=False, siding=_skin_for(key),
                           gables=gables, undress=[slab(offset(base, 8.0), sh["ze"] - LEDGE - 0.6, sh["zw"] + 0.01)])
        P = blk.pts
        no_lip = union([M.extrude(offset(rect(min(P[e][0], P[(e + 1) % 4][0]) - 0.5, min(P[e][1], P[(e + 1) % 4][1]) - 0.5,
                                              max(P[e][0], P[(e + 1) % 4][0]) + 0.5, max(P[e][1], P[(e + 1) % 4][1]) + 0.5), 4.0), 6.0)
                        .translate([0, 0, sh["zw"] - 1.0]) for e in sh["gables"]])
        walls = walls - lip_keep(base, 2.4, ZF, 1.2) + ((_corbel(base, 2.4, sh["zw"]) + lip_ring(base, 2.4, sh["zw"])) - no_lip)
        walls = walls + CO.ledge(blk.pts, sh["ze"], LEDGE, t=2.4)
        kit.add(f"{key}-WALLS", "Brown", walls, group="walls")
        rings, _ = CO.level(blk.pts, sh["ze"], sh["spec"], t=2.4)
        CO.add_level(kit, rings, f"{key}-CORNICE", "cornice")
        fnd = foundation([blk], 0.0, ZF, t=2.4, style="sillblocks")
        kit.add(f"{key}-FOUNDATION", "Stone", fnd, group="foundation")
        ins = []
        for op in ops:
            A = op.local_frame()
            sp = op.spec
            bb = sp["cut"].bounds()
            kk = "DOOR" if op.kind == "door" else "WIN"
            world, Pp, zones = O.place(sp, A, "Windows_Doors", "Door" if op.kind == "door" else "Windows_Doors", "Glass")
            p_ = kit.add(f"{kk}-{op.name}", "Windows_Doors", world, P=Pp, key=f"{kk}-{bb[2] - bb[0]:.1f}x{bb[3] - bb[1]:.1f}",
                         group="inserts", render=zones)
            ins.append(p_.solid)
        roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
        walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), sh["rake"] + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
        bx = base.bounds()
        if sh["eaves"] == [0, 2]:
            yc = (bx[1] + bx[3]) / 2
            zr = z_eave + S_ROOF * ((bx[3] - bx[1]) / 2 + sh["d_eave"])
            cap = G.ridge_cap((bx[0] - sh["rake"], yc), (bx[2] + sh["rake"], yc), zr, S_ROOF, sh["zw"], half=1.0, up=0.6)
        else:
            xc = (bx[0] + bx[2]) / 2
            zr = z_eave + S_ROOF * ((bx[2] - bx[0]) / 2 + sh["d_eave"])
            cap = G.ridge_cap((xc, bx[1] - sh["rake"]), (xc, bx[3] + sh["rake"]), zr, S_ROOF, sh["zw"], half=1.0, up=0.6)
        roof = roof + (cap - walls_env)
        roof = (roof - lip_keep(base, 2.4, sh["zw"])).trim_by_plane([0, 0, 1.0], sh["zw"])
        if key == "TOOL":
            px, py = STOVE
            zp = z_eave + S_ROOF * (bx[3] - py + sh["d_eave"]) - 5.0
            pipe = YD.stovepipe_section(zr + 9.0 - zp).translate([px, py, zp])
            roof = roof - M.cylinder(60.0, 1.2, 1.2, 24).translate([px, py, sh["zw"]]) - pipe
            kit.add("STOVEPIPE", "Iron", pipe, group="roof")
        kit.add(f"{key}-ROOF", "Shingle", roof, group="roof")
    print("specks dropped:", kit.drop_specks())
    return kit


def scenery():
    """Render-only: the main track in front, the speeder's spur to its door."""
    out = {}
    bal = [M.hull_points([(x, -36.0 + dy, z) for x in (-30.0, 108.0) for (dy, z) in ((-18.0, 0.0), (18.0, 0.0), (-14.0, 2.4), (14.0, 2.4))]),
           M.hull_points([(63.0 + dx, y, z) for y in (-24.0, 1.0) for (dx, z) in ((-12.0, 0.0), (12.0, 0.0), (-9.0, 1.2), (9.0, 1.2))])]
    ties = [box([x - 1.3, -36.0 - 14.9, 2.4], [x + 1.3, -36.0 + 14.9, 4.2]) for x in np.arange(-28.0, 106.0, 6.4)]
    ties += [box([63.0 - 12.0, y - 1.1, 1.2], [63.0 + 12.0, y + 1.1, 2.6]) for y in np.arange(-23.0, 0.0, 6.4)]
    rails = [box([-30.0, -36.0 + s - 0.45, 4.2], [108.0, -36.0 + s + 0.45, 6.3]) for s in (-8.7, 8.7)]
    rails += [box([63.0 + s - 0.4, -27.0, 2.6], [63.0 + s + 0.4, 1.0, 4.2]) for s in (-8.7, 8.7)]
    return {"ballast": union(bal), "ties": union(ties), "rail": union(rails)}


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "section4")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    npz = os.path.join(OUT, "section4.npz")
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
