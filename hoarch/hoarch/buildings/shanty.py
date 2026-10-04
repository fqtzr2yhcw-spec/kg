"""The Crossing Shanty and Oil House: an original HO-scale (1:87.1) pair of small railroad
buildings with a crossbuck, building 77 (the engine terminal batch).

The crossing watchman's shanty is an octagon on a crib of old crossties: a wainscot of diagonal
boards to a rail, narrow level boards above, big two-over-two windows under sloped heads on
bracket ends toward the road and both ways down the track, a four-light door, a cornice of the
crossing bell's wire on its pulleys under a crown, a roof of pressed-tin diamonds with a finial
and the stovepipe's bonnet. The oil house is brick with a dogtooth course under the eave, on
granite sills: a riveted iron fire door crossed by straps in a stone frame, barred vents in the
ends, a cornice of oil cans on a shelf rail, and a roof of cleated tin. A crossbuck on its post
stands by the road.

The track and plank crossing in the renders are scenery for the pictures, not parts.

usage: python3 -m hoarch.buildings.shanty [check] [export]
"""
import math
import os
import sys

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, rect, slab, union
from hoarch import cornice as CO, gables as G, openings as O, roof as R, yard as YD
from hoarch.kit import Kit
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Crossing Shanty and Oil House"
COLORS = {"Cream": "#E6DCC0", "Green": "#2F4A36", "Tin": "#7F8487", "Ties": "#4A3B2E", "Brick": "#8C3F2C",
          "Granite": "#A5A29B", "Iron": "#2B2B2B", "Windows_Doors": "#E6DCC0"}
RENDER_MAT = {"Cream": "siding", "Green": "green", "Tin": "roof", "Ties": "timber", "Brick": "brick", "Granite": "stone",
              "Iron": "iron", "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}
PALETTE = {"siding": ("#E6DCC0", 0.6, 0.0), "green": ("#2F4A36", 0.6, 0.0), "roof": ("#7F8487", 0.45, 0.35),
           "timber": ("#4A3B2E", 0.9, 0.0), "brick": ("#8C3F2C", 0.9, 0.0), "stone": ("#A5A29B", 0.9, 0.0),
           "iron": ("#2B2B2B", 0.45, 0.3), "trim": ("#2F4A36", 0.6, 0.0), "door": ("#2F4A36", 0.6, 0.0),
           "ballast": ("#8C877E", 0.97, 0.0), "ties": ("#3F3328", 0.9, 0.0), "rail": ("#77716A", 0.35, 0.8),
           "planks": ("#6B563F", 0.9, 0.0)}
VIEWS = {"hero": [-30, 16, 60, 0.95, [0, 0, 0]], "front": [0, 8, 70, 0.92, [0, 0, 0]], "rear": [150, 18, 60, 0.95, [0, 0, 0]]}

LEDGE = 1.2
SH_C = dict(pitch=6.0, margin=2.0, layers=[
    dict(kind="course", h=1.6, b=1.2, orn="signalwire", role="Green"),
    dict(kind="crown", h=1.8, b=1.4, P=3.2, orn="ovolo", role="Cream")])
OIL_C = dict(pitch=7.0, margin=3.0, layers=[
    dict(kind="frieze", h=4.0, b=1.2, orn="oilcans", role="Cream"),
    dict(kind="crown", h=1.8, b=1.4, P=3.4, orn="cavetto", role="Green")])

# --- the shanty: an octagon, flats square to the axes
APO = 10.0
RC = APO / math.cos(math.pi / 8)
SH_PTS = [(RC * math.cos(math.pi / 8 + k * math.pi / 4), RC * math.sin(math.pi / 8 + k * math.pi / 4)) for k in range(8)]
ZF_S = 5.0
ZE_S = ZF_S + 24.0
ZW_S = round((ZE_S + CO.band_height(SH_C)) / 0.2) * 0.2
SHANTY = Block("shanty", SH_PTS, ZF_S, ZW_S)
S_SH = 1.1
PIPE = (3.5, 3.0)

# --- the oil house
OX0, OX1, OY0, OY1 = 30.0, 54.0, 0.0, 18.0
ZF_O = 3.0
ZE_O = ZF_O + 22.0
ZW_O = round((ZE_O + CO.band_height(OIL_C)) / 0.2) * 0.2
OIL = Block("oil", [(OX0, OY0), (OX1, OY0), (OX1, OY1), (OX0, OY1)], ZF_O, ZW_O)
S_OIL = 0.55
CROSSBUCK = (-22.0, -16.0)


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    win = YD.window_shanty(6.0, 10.0)
    add(SHANTY, 0.0, -APO, 0.4, YD.door_shanty(6.0, 18.0), "shanty-door", "door")
    add(SHANTY, APO, 0.0, 9.0, win, "shanty-E")
    add(SHANTY, -APO, 0.0, 9.0, win, "shanty-W")
    add(SHANTY, 0.0, APO, 9.0, win, "shanty-N")
    add(OIL, (OX0 + OX1) / 2, OY0, 0.4, YD.door_oilhouse(8.0, 16.0), "oil-door", "door")
    vent = YD.vent_oilhouse(6.0, 4.0)
    add(OIL, OX1, (OY0 + OY1) / 2, 11.0, vent, "oil-vent-E")
    add(OIL, OX0, (OY0 + OY1) / 2, 11.0, vent, "oil-vent-W")
    return L


OPENINGS = _openings()


def _skin(f, b, reg):
    if b is SHANTY:
        reg = reg - rect(-1, ZE_S - LEDGE - 0.6 - b.z0, f.L + 1, 999)
        return YD.shanty_diag(reg, datum=0.0, rail=8.0)
    reg = reg - rect(-1, ZE_O - LEDGE - 0.6 - b.z0, f.L + 1, ZW_O - b.z0 + 0.2)
    return YD.brick_dogtooth(reg, datum=0.0, dog=ZE_O - LEDGE - 0.6 - b.z0 - 2.4)


def _inserts(kit, ops):
    for op in ops:
        A = op.local_frame()
        sp = op.spec
        bb = sp["cut"].bounds()
        kk = "DOOR" if op.kind == "door" else "WIN"
        world, Pp, zones = O.place(sp, A, "Windows_Doors", "Door" if op.kind == "door" else "Windows_Doors", "Glass")
        kit.add(f"{kk}-{op.name}", "Windows_Doors", world, P=Pp, key=f"{kk}-{bb[2] - bb[0]:.1f}x{bb[3] - bb[1]:.1f}-{op.block.name}",
                group="inserts", render=zones)


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    # --- the shanty
    base = SHANTY.cs
    ops = [op for op in OPENINGS if op.block is SHANTY]
    walls = wall_shell([SHANTY], ops, t=2.2, belt=None, corners="none", water_table=False, siding=_skin,
                       undress=[slab(offset(base, 6.0), ZE_S - LEDGE - 0.6, ZW_S + 0.01)])
    walls = walls - lip_keep(base, 2.2, ZF_S, 1.2) + _corbel(base, 2.2, ZW_S) + lip_ring(base, 2.2, ZW_S) + CO.ledge(SH_PTS, ZE_S, LEDGE, t=2.2)
    kit.add("SHANTY-WALLS", "Cream", walls, group="walls")
    rings, _ = CO.level(SH_PTS, ZE_S, SH_C, t=2.2)
    CO.add_level(kit, rings, "SHANTY-CORNICE", "cornice")
    kit.add("SHANTY-CRIB", "Ties", foundation([SHANTY], 0.0, ZF_S, t=2.2, style="tiecrib"), group="foundation")
    _inserts(kit, ops)
    z_eave = ZW_S + 1.0
    sol, tex = R.hip_roof([(SH_PTS, list(range(8)))], z_eave, S_SH, 2.8, texture="diamondtin",
                          tex_kw=dict(pitch=1.5, wtab=2.0, d=0.3), zlo=ZW_S)
    zt = z_eave + S_SH * (APO + 2.8)
    fin = M.cylinder(3.0, 0.8, 0.55, 16).translate([0, 0, zt - 1.6]) + M.sphere(1.2, 16).translate([0, 0, zt + 2.3])
    px, py = PIPE
    zp = z_eave + S_SH * (APO + 2.8 - math.hypot(px, py) * 0.95) - 4.0
    pipe = YD.stovepipe_shanty(zt + 5.0 - zp).translate([px, py, zp])
    roof = (sol + tex + fin - lip_keep(base, 2.2, ZW_S)).trim_by_plane([0, 0, 1.0], ZW_S)
    roof = roof - M.cylinder(60.0, 1.0, 1.0, 20).translate([px, py, ZW_S]) - pipe
    kit.add("SHANTY-ROOF", "Tin", roof, group="roof")
    kit.add("STOVEPIPE", "Iron", pipe, group="roof")

    # --- the oil house
    base = OIL.cs
    ops = [op for op in OPENINGS if op.block is OIL]
    pieces = [(OIL.pts, [0, 2], S_OIL)]
    gd = [dict(p0=(OX1, OY0), p1=(OX1, OY1), slope=S_OIL, e=0.3), dict(p0=(OX0, OY1), p1=(OX0, OY0), slope=S_OIL, e=0.3)]
    ze = ZW_O + 1.2
    rf = G.gabled_roof(pieces, ze, 3.2, gd, texture="cleatseam", tex_kw=dict(pitch=6.0, wtab=2.8, d=0.3), skin=1.4, rake=2.4,
                       inner_cs=None, fascia=1.2)      # solid: a pitch this low can't be hollowed and print
    we, ww = rf["walls"]
    gables = [(OIL, 1, we["cs"].translate((0.0, ze - ZF_O))), (OIL, 3, ww["cs"].translate((0.0, ze - ZF_O)))]
    walls = wall_shell([OIL], ops, t=2.4, belt=None, corners="none", water_table=False, siding=_skin, gables=gables,
                       undress=[slab(offset(base, 6.0), ZE_O - LEDGE - 0.6, ZW_O + 0.01)])
    no_lip = union([box([OX0 - 1, OY0 - 20, ZW_O - 1], [OX0 + 4.5, OY1 + 20, ZW_O + 5]), box([OX1 - 4.5, OY0 - 20, ZW_O - 1], [OX1 + 1, OY1 + 20, ZW_O + 5])])
    walls = walls - lip_keep(base, 2.4, ZF_O, 1.2) + ((_corbel(base, 2.4, ZW_O) + lip_ring(base, 2.4, ZW_O)) - no_lip) + CO.ledge(OIL.pts, ZE_O, LEDGE, t=2.4)
    kit.add("OIL-WALLS", "Brick", walls, group="walls")
    rings, _ = CO.level(OIL.pts, ZE_O, OIL_C, t=2.4)
    CO.add_level(kit, rings, "OIL-CORNICE", "cornice")
    kit.add("OIL-FOUNDATION", "Granite", foundation([OIL], 0.0, ZF_O, t=2.4, style="granitesill"), group="foundation")
    _inserts(kit, ops)
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), 2.4 + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    yc = (OY0 + OY1) / 2
    zr = ze + S_OIL * ((OY1 - OY0) / 2 + 3.2)
    roof = roof + (G.ridge_cap((OX0 - 2.4, yc), (OX1 + 2.4, yc), zr, S_OIL, ZW_O, half=0.9, up=0.5) - walls_env)
    roof = (roof - lip_keep(base, 2.4, ZW_O)).trim_by_plane([0, 0, 1.0], ZW_O)
    kit.add("OIL-ROOF", "Tin", roof, group="roof")

    # --- the crossbuck, standing by the road; printed flat on its back
    cb = YD.crossbuck(40.0, 17.0)
    Ac = np.array([[1.0, 0.0, 0.0, CROSSBUCK[0]], [0.0, 0.0, -1.0, CROSSBUCK[1]], [0.0, 1.0, 0.0, 0.0]])
    kit.add("CROSSBUCK", "Cream", cb.transform(Ac), P=np.array([[1.0, 0, 0, 0], [0, 0, 1.0, 0], [0, -1.0, 0, 0]]), group="yard")
    print("specks dropped:", kit.drop_specks())
    return kit


def scenery():
    """Render-only: the track past the shanty and a plank road crossing over it."""
    y0 = -34.0
    bal = M.hull_points([(x, y0 + dy, z) for x in (-80.0, 80.0) for (dy, z) in ((-18.0, 0.0), (18.0, 0.0), (-14.0, 2.4), (14.0, 2.4))])
    ties = union([box([x - 1.3, y0 - 14.9, 2.4], [x + 1.3, y0 + 14.9, 4.2]) for x in np.arange(-78.0, 78.0, 6.4)])
    rails = union([box([-80.0, y0 + s - 0.45, 4.2], [80.0, y0 + s + 0.45, 6.3]) for s in (-8.7, 8.7)])
    xr = -28.0
    road = union([M.hull_points([(xr + dx, y0 + sg * y, z) for dx in (-11.0, 11.0) for (y, z) in ((16.0, 6.0), (45.0, 0.0), (16.0, 0.0))])
                  for sg in (-1, 1)])
    planks = union([box([xr - 11.0, y0 + y - 1.8, 4.2], [xr + 11.0, y0 + y + 1.8, 6.1]) - box([xr - 12, y0 + y - 0.3, 5.9], [xr + 12, y0 + y + 0.3, 7])
                    for y in (-12.5, 0.0, 12.5)])
    return {"ballast": bal + road, "ties": ties, "rail": rails, "planks": planks}


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "shanty")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    npz = os.path.join(OUT, "shanty.npz")
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
