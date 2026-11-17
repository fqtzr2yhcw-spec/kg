"""The Pingree: an original HO-scale (1:87.1) Salem Federal mansion after McIntire, house 47 of
the fourth batch (all Colonial).

A square brick house of three storeys diminishing upward, in stretcher bond laid in fine
struck joints, on bush-hammered granite. Across the front a semicircular portico of four
slender columns (fluted shafts, capitals of two tiers of leaves) carries a curved fluted
entablature and a balustrade of spindle-necked urns; under it the entrance: a six-panel door
between oval-leaded sidelights under one elliptical fanlight, reeded pilasters and a keyed
cornice; over it a pair of glazed doors under an elliptical fan opens onto the portico's
roof. Ground-floor windows under marble lintels with splayed ends and a tablet carved with a
patera; first-floor windows under thin cornices over fluted aprons; short windows on kneeled
sills in the top storey. Buff stone cornices at every level: baskets of fruit between
paterae, dolphins arched over a shell, and at the eave Federal eagles with ribbons and stars
over dentils, ovolo modillions and a cyma. A low hip of slates with a tongue at every butt,
flat on top for a belvedere with a round-headed window on each face, its own cornice and a
gilded eagle on a ball; at each end a pair of stacks joined by a curtain wall.

usage: python3 -m hoarch.buildings.pingree [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, offset, poly, rect, slab, union
from hoarch import colonial4 as C4, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells, wall_shell

NAME = "The Pingree"
COLORS = {"Brick": "#8C3F2C", "Cream": "#EFE8D5", "Buff": "#C9B99A", "Slate": "#4E555E", "Granite": "#9A968C",
          "Gilt": "#C9A546", "Windows_Doors": "#EFE8D5"}
RENDER_MAT = {"Brick": "brick", "Cream": "trim", "Buff": "accent", "Slate": "roof", "Granite": "stone", "Gilt": "gilt",
              "Windows_Doors": "trim", "Door": "door", "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Pingree)
LEDGE = 1.4
JOINT1 = dict(pitch=16.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="baskets", role="Buff"),
    dict(kind="course", h=1.4, b=1.4, orn="reeds", role="Cream"),
    dict(kind="crown", h=2.2, b=1.4, P=3.4, orn="ogee_fillet", role="Cream")])
JOINT2 = dict(pitch=18.0, margin=5.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="dolphins", role="Buff"),
    dict(kind="course", h=1.4, b=1.4, orn="twist", role="Cream"),
    dict(kind="crown", h=2.2, b=1.4, P=3.4, orn="stepped", role="Cream")])
EAVE = dict(pitch=17.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.6, b=1.2, orn="eagles", role="Buff"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Cream", tooth=0.8, gap=0.6),
    dict(kind="bed", h=2.2, b=1.4, P=5.8, role="Cream", brackets=dict(style="ovolomod", t=1.4, reach=0.3)),
    dict(kind="crown", h=2.8, b=1.4, P=6.6, orn="cyma", role="Cream")])
CUPOLA_C = dict(pitch=9.0, margin=3.0, layers=[
    dict(kind="frieze", h=3.8, b=1.2, orn="baskets", role="Buff"),
    dict(kind="course", h=1.2, b=1.2, orn="dentil", role="Cream", tooth=0.7, gap=0.5),
    dict(kind="crown", h=2.0, b=1.2, P=3.8, orn="cavetto", role="Cream")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT1)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 12.0
S1 = ZF + 40.0
ZU1 = S1 + RJ
S2 = ZU1 + 36.0
ZU2 = S2 + RJ
ZE = ZU2 + 30.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE = 7.0
S_MAIN = 0.45
W, D = 156.0, 124.0
XC, YC = W / 2, D / 2
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
BLOCKS = [MAIN]
BAYS = (22.0, 50.0, W - 50.0, W - 22.0)
SIDE = (30.0, 62.0, 94.0)
V1 = 7.0
V2 = ZU1 - ZF + 5.0
V3 = ZU2 - ZF + 4.0
PR = 18.0                                        # the portico's radius
H_POR = ZF - 0.4                                 # its floor
CUP = 26.0                                       # the belvedere's width
CUP_H = 20.0


def _skin(f, b, reg):
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, 999)
    return C4.brick_struck(reg, datum=0.0)


def _openings():
    L = []

    def add(x, y, v0, sp, name, kind="window"):
        e, u = MAIN.locate(x, y)
        L.append(Opening(MAIN, e, u, v0, sp, name, kind))

    lo = C4.window_splaylintel(10.0, 24.0)
    mid = C4.window_fluteapron(10.0, 22.0)
    top = C4.window_kneeled(10.0, 14.0)
    for x in BAYS:
        add(x, 0.0, V1, lo, f"S{x:.0f}-1")
        add(x, D, V1, lo, f"N{x:.0f}-1")
        add(x, 0.0, V2, mid, f"S{x:.0f}-2")
    for x in BAYS + (XC,):
        add(x, D, V2, mid, f"N{x:.0f}-2")
        add(x, 0.0, V3, top, f"S{x:.0f}-3")
        add(x, D, V3, top, f"N{x:.0f}-3")
    add(XC, 0.0, 0.4, C4.door_elliptic(10.0, 22.0), "front-door", "door")
    add(XC, 0.0, ZU1 - ZF + 0.8, C4.door_balcony(11.0, 21.0), "balcony-door", "door")
    add(XC, D, 1.2, C4.door_balcony(10.0, 21.0), "back-door", "door")
    for x_, tag in ((0.0, "W"), (W, "E")):
        for y in SIDE:
            add(x_, y, V1, lo, f"{tag}{y:.0f}-1")
            add(x_, y, V2, mid, f"{tag}{y:.0f}-2")
            add(x_, y, V3, top, f"{tag}{y:.0f}-3")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01)]
    clear = [lip_keep(base, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1, S2], t=3.0, corners="none", siding=_skin, gables=[], clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((XC - 20.0, 3.0), (XC - 20.0, D - 3.0), 2.0, ZF, ZW),
                                    ((XC + 20.0, 3.0), (XC + 20.0, D - 3.0), 2.0, ZF, ZW)])
    kit.add("WALLS-1", "Brick", st["shells"][0], group="walls")
    kit.add("JOINT-1", "Brick", st["rings"][0], group="walls")
    kit.add("WALLS-2", "Brick", st["shells"][1], group="walls")
    kit.add("JOINT-2", "Brick", st["rings"][1], group="walls")
    lip = _corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)
    kit.add("WALLS-3", "Brick", st["shells"][2] + lip + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT1)
    CO.add_level(kit, rings, "CORNICE-J1", "cornice")
    rings, _ = CO.level(st["outlines"][1], S2 + LEDGE + 0.4, JOINT2)
    CO.add_level(kit, rings, "CORNICE-J2", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="bushgranite")
    kit.add("FOUNDATION", "Granite", fnd, group="foundation")
    ins_keep = []
    for o in OPENINGS:
        A = o.local_frame()
        sp = o.spec
        b = sp["cut"].bounds()
        key = "DOOR" if o.kind == "door" else "WIN"
        world, P, zones = O.place(sp, A, "Windows_Doors", "Door" if o.kind == "door" else "Windows_Doors", "Glass")
        part = kit.add(f"{key}-{o.name}", "Windows_Doors", world, P=P,
                       key=f"{key}-{b[2] - b[0]:.1f}x{b[3] - b[1]:.1f}-{o.v0 > 20}", group="inserts", render=zones)
        ins_keep.append(part.solid)
    print("walls + cornices + inserts", round(time.time() - t0, 1))

    # --- the low hip, flat on top for the belvedere; a curtained pair of stacks at each end
    pieces = [(MAIN.pts, [0, 1, 2, 3], S_MAIN)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, [], texture="tab", tex_kw=dict(pitch=1.6, wtab=2.4, d=0.4),
                       inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    run_ = (D / 2 + D_EAVE) - (CUP / 2 + 4.0)
    z_flat = round((Z_EAVE + S_MAIN * run_) / 0.2) * 0.2
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    roof = (rf["body"] + rf["tex"]).trim_by_plane([0, 0, -1.0], -z_flat)
    roof = roof + (slab(offset(base, 20.0), z_flat - 1.6, z_flat) ^ solid_env)          # the deck closes the hollow roof
    roof = roof - lip_keep(base, 3.0, ZW)
    CW, CD, GAP = 7.0, 9.0, 16.0
    pockets, stacks = [], []
    for cx in (11.0, W - 11.0):
        z0 = round((Z_EAVE + 3.0) / 0.2) * 0.2
        half_y = GAP / 2 + CW
        roof = roof + (box([cx - CD / 2 - 1.2, YC - half_y - 1.2, ZW + 0.01], [cx + CD / 2 + 1.2, YC + half_y + 1.2, z0 + 0.01]) ^ solid_env)
        pockets.append(box([cx - CD / 2 - 0.4, YC - half_y - 0.4, z0], [cx + CD / 2 + 0.4, YC + half_y + 0.4, z_flat + 60]))
        ch = C4.chimney_curtain(CW, CD, GAP, z_flat + 10.0 - z0, zc=0.0)
        stacks.append(ch.rotate([0, 0, 90]).translate([cx, YC, z0]))
    roof = roof - union(pockets)
    kit.add("ROOF", "Slate", roof, group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Brick", s_, key="CHIMNEY", group="roof")
    # --- the belvedere
    cze = z_flat + CUP_H
    czw = round((cze + CO.band_height(CUPOLA_C)) / 0.2) * 0.2
    c0 = (XC - CUP / 2, YC - CUP / 2)
    cup = Block("cupola", [c0, (c0[0] + CUP, c0[1]), (c0[0] + CUP, c0[1] + CUP), (c0[0], c0[1] + CUP)], z_flat, czw)
    cwin = C4.window_cupola_arch(9.0, 13.0)
    cup_ops = []
    for k, (x, y) in enumerate(((XC, c0[1]), (c0[0] + CUP, YC), (XC, c0[1] + CUP), (c0[0], YC))):
        e, u = cup.locate(x, y)
        cup_ops.append(Opening(cup, e, u, 3.2, cwin, f"cupola-{k}"))
    cup_und = [slab(offset(cup.cs, 8.0), cze - LEDGE - 0.6, czw + 0.01)]
    cwalls = wall_shell([cup], cup_ops, t=2.4, belt=None, corners="board", water_table=False, undress=cup_und,
                        siding=lambda f, b, reg: C4.ext(reg - rect(-1, cze - LEDGE - 0.6 - b.z0, f.L + 1, 999), 0.0, 0.3))
    clip = _corbel(cup.cs, 2.4, czw) + lip_ring(cup.cs, 2.4, czw)
    kit.add("CUPOLA-walls", "Cream", cwalls + CO.ledge(cup.pts, cze, LEDGE, t=2.4) + clip, group="cupola")
    for o in cup_ops:
        A = o.local_frame()
        world, P, zones = O.place(o.spec, A, "Windows_Doors", "Windows_Doors", "Glass")
        kit.add(f"WIN-{o.name}", "Windows_Doors", world, P=P, key="WIN-cupola", group="cupola", render=zones)
    rings, _ = CO.level(cup.pts, cze, CUPOLA_C, t=2.4)
    CO.add_level(kit, rings, "CORNICE-CUP", "cupola")
    cd = CUPOLA_C["layers"][-1]["P"] + 0.6
    croof, ctex = R.hip_roof([(cup.pts, [0, 1, 2, 3])], czw + 1.4, 0.6, cd, texture="tab",
                             tex_kw=dict(pitch=1.4, wtab=2.0, d=0.36), zlo=czw)
    zseat = round((czw + 1.4 + 0.6 * (CUP / 2 + cd) - 1.0) / 0.2) * 0.2
    seat = M.cylinder(1.0, 1.1, 1.1, 32).translate([XC, YC, zseat - 0.4])
    kit.add("CUPOLA-roof", "Slate", (croof + ctex).trim_by_plane([0, 0, -1.0], -zseat) - seat - lip_keep(cup.cs, 2.4, czw),
            group="cupola")
    kit.add("CUPOLA-finial", "Gilt", C4.finial_eagle(6.0).translate([XC, YC, zseat - 0.4]), group="cupola")
    print("roof + belvedere", round(time.time() - t0, 1))

    # --- the semicircular portico
    col_h = round((ZU1 - H_POR - 4.0 - 1.6 - 1.4 + 0.01) / 0.2) * 0.2
    PP = C4.semicircle_portico((XC, 0.0), PR, H_POR, col_h, n_cols=4, steps=3, rail_h=7.0)
    bld_keep = union([p.solid for p in kit.parts if p.name.startswith(("WALLS", "JOINT", "CORNICE"))])
    keep = bld_keep + union(ins_keep) + fnd
    kit.add("PORTICO-floor", "Granite", PP["floor"] - fnd - keep, group="portico")
    kit.add("PORTICO-top", "Cream", PP["top"] - keep, P=print_flip(), group="portico")
    kit.add("PORTICO-balustrade", "Cream", PP["balustrade"] - keep, group="portico")
    # --- the back stoop
    e, u = MAIN.locate(XC, D)
    fb = MAIN.facades()[e]
    A = fb.A.copy()
    A[:, 3] = fb.world(u, -ZF, 1.4)
    kit.add("STOOP-back", "Granite", FT.steps(18.0, ZF + 0.6, 5).transform(A) - fnd, group="steps")
    FT.crown(kit, "CUPOLA-finial", "CUPOLA-roof")
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "pingree")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "pingree.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
