"""The Sandoval: an original HO-scale (1:87.1) Pueblo Revival house, house 60 of the fifth
batch (the Craftsman era, 1900-1930).

Stepped adobe masses under flat roofs: a broad one-storey house and, set back on its roof, an
upper storey, each walled round its roof by a soft parapet with wooden canales spouting
through it, the round ends of the vigas standing out of the walls in a row below. Mud plaster
over adobe, fallen away here and there to show the big bricks. Across the front a portal on
peeled log posts with carved zapatas and a squared beam, low adobe bancos between the posts,
a flat roof of latillas. The windows are turquoise casements deep in soft reveals under adzed
timber lintels (upstairs on carved zapatas); the door a carved Spanish door of four rosette
panels; a glazed door from the upper storey onto the roof terrace. A round kiva chimney rises
from the roof; an horno, the beehive oven, stands in the yard. Cloud terraces and latillas at
the upper storey's roof.

usage: python3 -m hoarch.buildings.sandoval [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, rect, slab, union
from hoarch import craftsman2 as CR2, cornice as CO, features as FT, openings as O
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, wall_shell

NAME = "The Sandoval"
COLORS = {"Adobe": "#C8A27C", "Viga": "#6B4E34", "Turquoise": "#3F8FA0", "Clay": "#B06A45", "Brick": "#A5805C",
          "Planks": "#8A6A4A", "PorchDeck": "#8A6A4A", "Windows_Doors": "#3F8FA0"}
RENDER_MAT = {"Adobe": "siding", "Viga": "wood", "Turquoise": "accent", "Clay": "trim", "Brick": "brick",
              "Planks": "planks", "PorchDeck": "planks", "Windows_Doors": "accent", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Sandoval)
LEDGE = 1.4
EAVE1 = dict(pitch=14.0, margin=5.0, layers=[
    dict(kind="frieze", h=4.6, b=1.2, orn="vigas", role="Viga"),
    dict(kind="course", h=1.4, b=1.4, orn="latillas", role="Clay"),
    dict(kind="crown", h=2.0, b=1.4, P=3.2, orn="torus", role="Adobe")])
EAVE2 = dict(pitch=15.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="cloudterrace", role="Turquoise"),
    dict(kind="course", h=1.4, b=1.4, orn="latillas", role="Clay"),
    dict(kind="crown", h=2.0, b=1.4, P=3.2, orn="torus", role="Adobe")])
HE1, HE2 = CO.band_height(EAVE1), CO.band_height(EAVE2)

# ------------------------------------------------------------------ levels and plan
ZF = 6.0
ZE1 = ZF + 36.0
ZW1 = round((ZE1 + HE1) / 0.2) * 0.2
ZE2 = ZW1 + 34.0
ZW2 = round((ZE2 + HE2) / 0.2) * 0.2
MX0, MX1, MY0, MY1 = 0.0, 160.0, 20.0, 110.0
UX0, UX1, UY0 = 50.0, 130.0, 55.0
MAIN = Block("main", [(MX0, MY0), (MX1, MY0), (MX1, MY1), (MX0, MY1)], ZF, ZW1)
UPPER = Block("upper", [(UX0, UY0), (UX1, UY0), (UX1, MY1), (UX0, MY1)], ZW1, ZW2)
V1 = 8.0
ZONES = dict(brick=[])


def _skin(f, b, reg):
    top = (ZE1 if b is MAIN else ZE2) - LEDGE - 0.6 - b.z0
    reg = reg - rect(-1, top, f.L + 1, 999)
    sk, br = CR2.adobe_plaster(reg, seed=int(f.p0[0] * 3 + f.p0[1] + b.z0) % 97, parts=True)
    ZONES["brick"].append(f.place(br.translate([0, 0, -0.02])))
    return sk


def _openings():
    m, u = [], []

    def add(L, blk, x, y, v0, sp, name, kind="window"):
        e, uu = blk.locate(x, y)
        L.append(Opening(blk, e, uu, v0, sp, name, kind))

    g = CR2.window_pueblo(14.0, 18.0)
    up = CR2.window_pueblo(14.0, 15.0, upper=True)
    add(m, MAIN, 70.0, MY0, 0.4, CR2.door_pueblo(11.0, 23.0), "front-door", "door")
    for x in (40.0, 100.0, 145.0):
        add(m, MAIN, x, MY0, V1, g, f"S{x:.0f}")
    for y in (45.0, 85.0):
        add(m, MAIN, MX0, y, V1, g, f"W{y:.0f}")
        add(m, MAIN, MX1, y, V1, g, f"E{y:.0f}")
    add(m, MAIN, 24.0, MY1, 0.4, CR2.door_pueblo(10.0, 21.0), "back-door", "door")
    for x in (70.0, 110.0, 145.0):
        add(m, MAIN, x, MY1, V1, g, f"N{x:.0f}")
    add(u, UPPER, 90.0, UY0, 2.0, CR2.door_pueblo(10.0, 21.0, glazed=True), "terrace-door", "door")
    for x in (65.0, 115.0):
        add(u, UPPER, x, UY0, 6.0, up, f"U-S{x:.0f}")
        add(u, UPPER, x, MY1, 6.0, up, f"U-N{x:.0f}")
    add(u, UPPER, UX0, 84.0, 6.0, up, "U-W")
    add(u, UPPER, UX1, 84.0, 6.0, up, "U-E")
    return m, u


OPEN1, OPEN2 = _openings()
OPENINGS = OPEN1 + OPEN2


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    ZONES["brick"].clear()
    t0 = time.time()
    mcs, ucs = MAIN.cs, UPPER.cs
    parts_ = [((UX0, UY0 + 1.5), (UX1, UY0 + 1.5), 3.0, ZF, ZW1), ((UX0 + 1.5, UY0), (UX0 + 1.5, MY1), 3.0, ZF, ZW1),
              ((UX1 - 1.5, UY0), (UX1 - 1.5, MY1), 3.0, ZF, ZW1)]
    w1 = wall_shell([MAIN], OPEN1, t=3.0, belt=None, corners="none", water_table=False, siding=_skin,
                    undress=[slab(offset(mcs, 8.0), ZE1 - LEDGE - 0.6, ZW1 + 0.01)], partitions=parts_)
    w1 = w1 - lip_keep(mcs, 3.0, ZF, 1.2)
    w1 = w1 + _corbel(mcs, 3.0, ZW1) + lip_ring(mcs, 3.0, ZW1) + _corbel(ucs, 3.0, ZW1) + lip_ring(ucs, 3.0, ZW1) + CO.ledge(MAIN.pts, ZE1, LEDGE)
    bz = union(ZONES["brick"])
    kit.add("WALLS-1", "Adobe", w1, group="walls", render=[("Adobe", w1 - bz), ("Brick", w1 ^ bz)])
    ZONES["brick"].clear()
    w2 = wall_shell([UPPER], OPEN2, t=3.0, belt=None, corners="none", water_table=False, siding=_skin,
                    undress=[slab(offset(ucs, 8.0), ZE2 - LEDGE - 0.6, ZW2 + 0.01)])
    w2 = w2 - lip_keep(ucs, 3.0, ZW1, 1.2) - lip_keep(mcs, 3.0, ZW1, 1.2)
    w2 = w2 + _corbel(ucs, 3.0, ZW2) + lip_ring(ucs, 3.0, ZW2) + CO.ledge(UPPER.pts, ZE2, LEDGE)
    bz = union(ZONES["brick"])
    kit.add("WALLS-2", "Adobe", w2, group="walls", render=[("Adobe", w2 - bz), ("Brick", w2 ^ bz)])
    rings, _ = CO.level(MAIN.pts, ZE1, EAVE1)
    CO.add_level(kit, rings, "CORNICE-1", "cornice")
    rings, _ = CO.level(UPPER.pts, ZE2, EAVE2)
    CO.add_level(kit, rings, "CORNICE-2", "cornice")
    fnd = foundation([MAIN], 0.0, ZF, style="adobeplinth")
    kit.add("FOUNDATION", "Adobe", fnd, group="foundation")
    ins_keep = []
    chg = (O.PLUG, "Viga")
    for op in OPENINGS:
        A = op.local_frame()
        sp = op.spec
        b = sp["cut"].bounds()
        key = "DOOR" if op.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Turquoise", "Door" if op.kind == "door" else "Turquoise", "Glass")
        k_ = M.cube([400.0, 400.0, 20.0]).translate([-200.0, -200.0, 0.0]).transform(A)
        zones = [(c_, m_ - k_) for c_, m_ in zones] + [("Viga", world ^ k_)]
        part = kit.add(f"{key}-{op.name}", "Windows_Doors", world, P=P, key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{op.block is UPPER}",
                       group="inserts", render=zones, change=chg)
        ins_keep.append(part.solid)
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the roofs: two trays (deck and parapet in one), canales through the parapets, the
    # kiva chimney on the lower roof
    hole = slab(offset(ucs, 1.0), ZW1 - 1.0, ZW1 + 20.0)
    gap = box([UX0 - 1.0, MY1 - 5.0, ZW1 - 1.0], [UX1 + 1.0, MY1 + 1.0, ZW1 + 20.0])
    t1 = CR2.roof_tray(mcs, ZW1, hole=hole, gap=gap) - lip_keep(mcs, 3.0, ZW1) - lip_keep(ucs, 3.0, ZW1)
    can = []
    for (x, y, rot) in ((30.0, MY0, 0), (140.0, MY0, 0), (MX0, 60.0, 1), (MX1, 60.0, 2)):
        c = CR2.canale(ZW1 + 3.2)
        if rot == 0:
            c = c.rotate([0, 0, 180]).translate([x, y + 2.6 - 2.6, 0])
        elif rot == 1:
            c = c.rotate([0, 0, 90]).translate([x, y, 0])
        else:
            c = c.rotate([0, 0, -90]).translate([x, y, 0])
        can.append(c)
    t1 = t1 + union(can)
    cx, cy = 146.0, 92.0
    c1 = union([p.solid for p in kit.parts if p.name.startswith("CORNICE-1")])
    kit.add("ROOF-1", "Adobe", t1 - c1, group="roof")
    kit.add("CHIMNEY", "Adobe", CR2.chimney_kiva(24.0).translate([cx, cy, ZW1 + 1.6]), group="roof")
    t2 = CR2.roof_tray(ucs, ZW2) - lip_keep(ucs, 3.0, ZW2)
    can2 = [CR2.canale(ZW2 + 3.2).rotate([0, 0, 180]).translate([x, UY0, 0]) for x in (70.0, 110.0)]
    c2 = union([p.solid for p in kit.parts if p.name.startswith("CORNICE-2")])
    kit.add("ROOF-2", "Adobe", (t2 + union(can2)) - c2, group="roof")
    print("roofs", round(time.time() - t0, 1))

    # --- the portal across the front: log posts with zapatas, bancos, a flat latilla roof
    PX0, PX1, PD = 20.0, 120.0, MY0
    ppts = [(PX0, MY0), (PX0, 0.0), (PX1, 0.0), (PX1, MY0)]
    Lp = PX1 - PX0
    H_floor = ZF - 1.4
    runs = [dict(a=(PX0, MY0), b=(PX0, 0.0), posts=[3.0, PD - 2.6]),
            dict(a=(PX0, 0.0), b=(PX1, 0.0), posts=[2.6, 34.0, 66.0, Lp - 2.6]),
            dict(a=(PX1, 0.0), b=(PX1, MY0), posts=[2.6, PD - 3.0])]
    ptop = ZF + 30.0
    o = 2.4
    PP = FT.porch_turned(ppts, runs, H_floor, ptop - 5.2 - H_floor, steps_at=[(1, 70.0 - PX0, 14.0)], over=o, inset=2.6,
                         rail_h=5.2, planks=dict(pitch=1.8, border=1.2), post="sandoval", rail="banco", arcade="zapatabeam",
                         skirt="adobe", pier_tex="adobeplinth", roof_edge="canales", top=True)
    fkeep = slab(offset(mcs, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    deck = PP["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch", render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([p.solid for p in kit.parts if p.name in ("WALLS-1", "WALLS-2") or p.name.startswith("CORNICE")])
    keep = bld_keep + union(ins_keep) + fnd
    res = FT.add_porch_top(kit, "PORCH", PP, keep, "Viga", "Viga", tin="custom", group="porch")
    zs = res["ptop"] - 0.8
    outer_cs = rect(PX0 - o, -o, PX1 + o, MY0 + 0.2)
    pt = CR2.roof_tray(outer_cs, zs, deck=1.4, parapet=3.8, band=1.6, gap=box([PX0 - o - 1, MY0 - 2.0, zs - 1], [PX1 + o + 1, MY0 + 1, zs + 10]))
    pt = pt + union([CR2.canale(zs + 2.2, L=2.0, w=1.4).rotate([0, 0, 180]).translate([x, -o, 0]) for x in (PX0 + 6.0, PX1 - 6.0)])
    pt = pt - bld_keep - union(ins_keep) - res["top"].solid
    kit.add("PORCH-roof", "Adobe", max(pt.decompose(), key=lambda m_: m_.volume()), group="porch")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PORCH-steps-{k}", "Adobe", sm.transform(A) - fkeep - deck, group="porch")
    e, u = MAIN.locate(24.0, MY1)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Adobe", FT.steps(14.0, ZF - 0.6, 2).transform(A) - fnd, group="porch")
    kit.add("HORNO", "Adobe", CR2.horno().translate([-11.0, 70.0, 0.0]), group="yard")      # against the west wall
    FT.key_into(kit, "PORCH-steps-0", ["PORCH-deck"], (0, 1, 0), depth=0.8, conform=True)
    FT.key_into(kit, "STOOP-back", ["FOUNDATION"], (0, -1, 0), depth=0.8, conform=True)
    FT.key_into(kit, "HORNO", ["FOUNDATION"], (1, 0, 0), depth=0.8, conform=True, band=(0.0, 1.2))
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "sandoval")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "sandoval.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
