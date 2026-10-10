"""The Porter: an original HO-scale (1:87.1) Connecticut River Valley Colonial, house 46 of the
fourth batch (all Colonial).

A two-storey house of mustard-yellow clapboards, short riven lengths with their lapped joints
staggered, between beaded corner boards, on random rubble laid up with raised ribbon
pointing, and a one-storey kitchen ell against its east gable with a porch along its front.
The glory is the doorway, as on the Valley's great houses: a pair of leaves of four raised
panels under a transom of five bull's-eye lights, between rusticated pilasters with scrolled
capitals, a pulvinated frieze and a segmental pediment with a sunburst rising in it. The
ground-floor windows (twelve over twelve) stand between slim pilasters under little
pediments; the upper windows (twelve over eight) have caps with three bull's-eyes on the
frieze. Between the storeys a Prussian-blue frieze of scallop shells between C-scrolls over a
coin moulding and a cyma reversa; at the eave pine cones hung between sprays of needles over
dentils, a soffit on double-scrolled modillions and a torus. Shakes with slanted butts on a
side-gabled roof, two ribbed stacks. The ell's porch stands on ringed posts with sunburst
railings and a frieze of pierced squares and drops, under a shed roof.

usage: python3 -m hoarch.buildings.porter [check] [export]
"""
import os
import sys
import time

import numpy as np
from manifold3d import Manifold as M

from hoarch.core import box, cs_union, offset, poly, rect, slab, union
from hoarch import colonial4 as C4, cornice as CO, features as FT, gables as G, openings as O, roof as R
from hoarch.kit import Kit, print_flip
from hoarch.shell import Block, Opening, _corbel, foundation, lip_keep, lip_ring, stacked_shells

NAME = "The Porter"
COLORS = {"Mustard": "#C8A04E", "Linen": "#EDE7D6", "Prussian": "#2F4A6B", "Cedar": "#6B6157", "Rubble": "#8A8378",
          "Brick": "#8A4632", "Planks": "#6E5238", "PorchDeck": "#6E5238", "Windows_Doors": "#EDE7D6"}
RENDER_MAT = {"Mustard": "siding", "Linen": "trim", "Prussian": "accent", "Cedar": "roof", "Rubble": "stone",
              "Brick": "brick", "Planks": "planks", "PorchDeck": "planks", "Windows_Doors": "trim", "Door": "door",
              "Glass": "glass"}

# ------------------------------------------------------------------ cornices (unique to the Porter)
LEDGE = 1.4
JOINT = dict(pitch=15.0, margin=4.0, layers=[
    dict(kind="frieze", h=4.4, b=1.2, orn="shells", role="Prussian"),
    dict(kind="course", h=1.4, b=1.4, orn="coins", role="Linen"),
    dict(kind="crown", h=2.2, b=1.4, P=3.4, orn="reverse", role="Linen")])
EAVE = dict(pitch=14.0, margin=4.0, layers=[
    dict(kind="frieze", h=5.0, b=1.2, orn="pinecones", role="Prussian"),
    dict(kind="course", h=1.6, b=1.4, orn="dentil", role="Linen", tooth=0.8, gap=0.6),
    dict(kind="bed", h=2.2, b=1.4, P=5.6, role="Linen", brackets=dict(style="doublescroll", t=1.4, reach=0.3)),
    dict(kind="crown", h=2.8, b=1.4, P=6.4, orn="torus", role="Linen")])
ELL_C = dict(pitch=13.0, margin=3.6, layers=[
    dict(kind="frieze", h=4.0, b=1.2, orn="shells", role="Prussian"),
    dict(kind="course", h=1.4, b=1.4, orn="coins", role="Linen"),
    dict(kind="crown", h=2.2, b=1.4, P=3.6, orn="cavetto", role="Linen")])
RJ = round((LEDGE + 0.4 + CO.band_height(JOINT)) / 0.2) * 0.2
HE = CO.band_height(EAVE)

# ------------------------------------------------------------------ levels and plan
ZF = 10.0
S1 = ZF + 42.0
ZU = S1 + RJ
ZE = ZU + 38.0
ZW = round((ZE + HE) / 0.2) * 0.2
FASCIA = 1.6
Z_EAVE = ZW + FASCIA
D_EAVE, RAKE, SKIN = 6.4, 6.6, 1.8
S_MAIN = 0.85
W, D = 150.0, 92.0
XC, YC = W / 2, D / 2
EX0, EX1, EY0, EY1 = W - 3.0, W + 56.0, 20.0, 80.0          # the ell (it overlaps the main wall by 3)
ELL_ZE = ZF + 30.0
ELL_ZW = round((ELL_ZE + CO.band_height(ELL_C)) / 0.2) * 0.2
ELL_EAVE = ELL_ZW + 1.4
S_ELL, D_EAVE_E = 0.8, 5.0
MAIN = Block("main", [(0, 0), (W, 0), (W, D), (0, D)], ZF, ZW)
ELL = Block("ell", [(EX0, EY0), (EX1, EY0), (EX1, EY1), (EX0, EY1)], ZF, ELL_ZW)
BLOCKS = [MAIN, ELL]
BAYS = (22.0, 50.0, W - 50.0, W - 22.0)
V1 = 7.0
V2 = ZU - ZF + 5.0


def _skin(f, b, reg):
    """Short clapboards between corner boards; nothing in the eave bands."""
    if b is ELL:
        reg = reg - rect(-1, ELL_ZE - LEDGE - 0.6 - b.z0, f.L + 1, 999)
        return C4.clapboard_short(reg, f.L, datum=0.0, seed=int(f.p0[1]) % 97)
    reg = reg - rect(-1, ZE - LEDGE - 0.6 - b.z0, f.L + 1, ZW - b.z0 + 0.2)
    return C4.clapboard_short(reg, f.L, datum=0.0, seed=int(abs(f.n[0]) * 3 + abs(f.n[1]) * 7 + f.p0[0]) % 97,
                              qtop=ZE - LEDGE - 0.6 - b.z0)


def _openings():
    L = []

    def add(blk, x, y, v0, sp, name, kind="window"):
        e, u = blk.locate(x, y)
        L.append(Opening(blk, e, u, v0, sp, name, kind))

    lo = C4.window_aedicule(10.0, 24.0)
    up = C4.window_bullseyecap(10.0, 20.0)
    att = C4.window_bullseyecap(7.0, 10.0)
    for x in BAYS:
        add(MAIN, x, 0.0, V1, lo, f"S{x:.0f}-1")
        add(MAIN, x, D, V1, lo, f"N{x:.0f}-1")
    for x in BAYS + (XC,):
        add(MAIN, x, 0.0, V2, up, f"S{x:.0f}-2")
        add(MAIN, x, D, V2, up, f"N{x:.0f}-2")
    add(MAIN, XC, 0.0, 0.4, C4.door_crv(12.0, 24.0), "front-door", "door")
    add(MAIN, XC, D, 0.4, C4.door_battenlight(10.0, 21.0), "back-door", "door")
    for y in (26.0, 66.0):
        add(MAIN, 0.0, y, V1, lo, f"W{y:.0f}-1")
        add(MAIN, 0.0, y, V2, up, f"W{y:.0f}-2")
    for y in (22.0, 70.0):                                              # clear of the ell's roof
        add(MAIN, W, y, V2, up, f"E{y:.0f}-2")
    for x_, tag in ((0.0, "W"), (W, "E")):
        add(MAIN, x_, YC, Z_EAVE + 3.0 - ZF, att, f"{tag}-attic")
    ell = C4.window_bullseyecap(9.0, 16.0)                            # the ell's storey is lower
    add(ELL, W + 12.0, EY0, 0.4, C4.door_battenlight(9.0, 18.0), "ell-door", "door")
    add(ELL, W + 42.0, EY0, V1, ell, "ellS42")
    for x in (W + 18.0, W + 40.0):
        add(ELL, x, EY1, V1, ell, f"ellN{x - W:.0f}")
    for y in (36.0, 64.0):
        add(ELL, EX1, y, V1, ell, f"ellE{y:.0f}")
    return L


OPENINGS = _openings()


def build(kit=None):
    kit = kit or Kit(NAME, COLORS, RENDER_MAT)
    kit.parts.clear()
    t0 = time.time()
    base = MAIN.cs
    pieces = [(MAIN.pts, [0, 2], S_MAIN)]
    gdefs = [dict(p0=(W, 0.0), p1=(W, D), slope=S_MAIN, e=0.3), dict(p0=(0.0, D), p1=(0.0, 0.0), slope=S_MAIN, e=0.3)]
    rf = G.gabled_roof(pieces, Z_EAVE, D_EAVE, gdefs, texture="slant", tex_kw=dict(pitch=1.6, wtab=2.4, d=0.4),
                       skin=SKIN, rake=RAKE, inner_cs=offset(base, -3.0), fascia=FASCIA, hollow=2.8)
    we, ww = rf["walls"]
    gables = [(MAIN, 1, we["cs"].translate((0.0, Z_EAVE - ZF))), (MAIN, 3, ww["cs"].translate((0.0, Z_EAVE - ZF)))]
    ell_zone = box([W - 1.0, EY0 - D_EAVE_E - 1.0, ZF], [EX1 + 30.0, EY1 + D_EAVE_E + 1.0, 400.0])
    undress = [slab(offset(base, 8.0), ZE - LEDGE - 0.6, ZW + 0.01),
               slab(offset(ELL.cs, 8.0) - offset(base, 0.5), ELL_ZE - LEDGE - 0.6, ELL_ZW + 0.01)]
    clear = [lip_keep(base, 3.0, ZF, 1.2)]
    st = stacked_shells(BLOCKS, OPENINGS, [S1], t=3.0, corners="none", siding=_skin, gables=gables, clear=clear,
                        prof=CO.joint_profile(RJ, LEDGE), belt_blocks=None, water_table=False, undress=undress,
                        partitions=[((XC - 18.0, 3.0), (XC - 18.0, D - 3.0), 2.0, ZF, ZW)])
    ell_lip = (_corbel(ELL.cs, 3.0, ELL_ZW) + lip_ring(ELL.cs, 3.0, ELL_ZW)) - MAIN.solid(grow=0.3, dz0=-5, dz1=5)
    ell_ledge = CO.ledge(ELL.pts, ELL_ZE, LEDGE) - MAIN.solid(grow=0.2, dz0=-1, dz1=1)
    kit.add("WALLS-1", "Mustard", st["shells"][0] + ell_lip + ell_ledge, group="walls")
    kit.add("JOINT", "Mustard", st["rings"][0], group="walls")
    no_lip = union([box([W - 5.0, -1, ZW - 1], [W + 1, D + 1, ZW + 5]), box([-1, -1, ZW - 1], [5.0, D + 1, ZW + 5])])
    lip = (_corbel(base, 3.0, ZW) + lip_ring(base, 3.0, ZW)) - no_lip
    kit.add("WALLS-2", "Mustard", st["shells"][1] + lip + CO.ledge(MAIN.pts, ZE, LEDGE), group="walls")
    # the ell's roof rises against the east gable through the belt: the belt cornice stops against it
    ell_env, _ = R.hip_roof([(ELL.pts, [0, 1, 2], S_ELL)], ELL_EAVE + 0.6, S_ELL, D_EAVE_E + 0.6, texture=None, zlo=ELL_ZW - 1.0)
    rings, _ = CO.level(st["outlines"][0], S1 + LEDGE + 0.4, JOINT, cut=ell_env)
    CO.add_level(kit, rings, "CORNICE-J", "cornice")
    rings, _ = CO.level(MAIN.pts, ZE, EAVE)
    CO.add_level(kit, rings, "CORNICE-E", "cornice")
    rings, _ = CO.level(ELL.pts, ELL_ZE, ELL_C, cut=MAIN.solid(grow=0.7, dz0=-2, dz1=2))
    CO.add_level(kit, rings, "CORNICE-ELL", "cornice")
    fnd = foundation(BLOCKS, 0.0, ZF, style="ribbon")
    kit.add("FOUNDATION", "Rubble", fnd, group="foundation")
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

    # --- the main roof: slant-butted shakes, a ridge cap, two ribbed stacks
    roof = rf["body"] + rf["tex"] + rf["skins"] + rf["skin_tex"]
    zr = Z_EAVE + S_MAIN * (D / 2 + D_EAVE)
    walls_env = union([wl["facade"].place(M.extrude(wl["cs"].offset(0.15), RAKE + 4.2).translate([0, 0, -3.15])) for wl in rf["walls"]])
    roof = roof + (G.ridge_cap((-RAKE, YC), (W + RAKE, YC), zr, S_MAIN, ZW) - walls_env)
    roof = roof - lip_keep(base, 3.0, ZW)
    solid_env, _ = R.hip_roof(pieces, Z_EAVE, S_MAIN, D_EAVE, texture=None, zlo=ZW)
    CW, CD = 10.0, 8.0
    pockets, stacks = [], []
    for cx in (40.0, W - 40.0):
        z0 = round((zr - 8.0) / 0.2) * 0.2
        roof = roof + (box([cx - CW / 2 - 1.2, YC - CD / 2 - 1.2, ZW + 0.01], [cx + CW / 2 + 1.2, YC + CD / 2 + 1.2, z0 + 0.01]) ^ solid_env)
        pockets.append(box([cx - CW / 2 - 0.4, YC - CD / 2 - 0.4, z0], [cx + CW / 2 + 0.4, YC + CD / 2 + 0.4, zr + 40]))
        stacks.append(C4.chimney_ribbed(CW, CD, zr + 12.0 - z0).translate([cx, YC, z0]))
    roof = roof - union(pockets)
    kit.add("ROOF", "Cedar", roof, group="roof")
    for k, s_ in enumerate(stacks):
        kit.add(f"CHIMNEY-{k}", "Brick", s_, key="CHIMNEY", group="roof")
    # the ell's roof: hipped at its east end, against the main house's east gable
    erf = G.gabled_roof([(ELL.pts, [0, 1, 2], S_ELL)], ELL_EAVE, D_EAVE_E, [], texture="slant",
                        tex_kw=dict(pitch=1.5, wtab=2.2, d=0.38), inner_cs=offset(ELL.cs, -3.0), fascia=1.4, hollow=2.4)
    main_keep = union([p.solid for p in kit.parts if p.name in ("WALLS-1", "JOINT", "WALLS-2") or p.name.startswith("CORNICE")])
    eroof = (erf["body"] + erf["tex"]) - MAIN.solid(grow=0.35, dz0=-5, dz1=300) - main_keep - union(ins_keep) - lip_keep(ELL.cs, 3.0, ELL_ZW)
    eroof = eroof.trim_by_plane([0, 0, 1.0], ELL_ZW)
    kit.add("ELL-roof", "Cedar", max(eroof.decompose(), key=lambda m_: m_.volume()), group="ell")
    print("roofs", round(time.time() - t0, 1))

    # --- the ell's porch, under a shed roof
    INSET = 1.6
    PY0 = EY0 - 14.0
    ppts = [(W, PY0), (EX1, PY0), (EX1, EY0), (W, EY0)]
    L0 = EX1 - W
    runs = [dict(a=(W, PY0), b=(EX1, PY0), posts=[2.6, 21.0, 38.6, L0 - INSET]),
            dict(a=(EX1, PY0), b=(EX1, EY0), posts=[INSET, (EY0 - PY0) - 3.0])]
    H_floor = ZF - 1.4
    S_P, o = 0.22, 2.0
    zs = ELL_ZE - 0.6 - S_P * ((EY0 - PY0) + o)
    PP = FT.porch_turned(ppts, runs, H_floor, zs + 0.8 - 5.2 - H_floor, steps_at=[(0, 12.0, 9.0)], over=o, inset=INSET,
                         planks=dict(pitch=1.8, border=1.2), post="ringed", rail="rays", arcade="blockdrops",
                         skirt="slats", pier_tex="ribbon", roof_edge="beadroll", top=True)
    fkeep = slab(offset(base, 0.8 + 0.55 + 0.15) + offset(ELL.cs, 0.8 + 0.55 + 0.15), -1, ZF + 1.3)
    deck = PP["deck"] - fkeep
    kit.add("PORCH-deck", "PorchDeck", deck, P=print_flip(), group="porch", render=FT.plank_zones(deck, H_floor, "Planks", "PorchDeck"))
    bld_keep = union([p.solid for p in kit.parts if p.name in ("WALLS-1", "JOINT", "WALLS-2") or p.name.startswith("CORNICE")])
    keep = bld_keep + union(ins_keep) + fnd
    res = FT.add_porch_top(kit, "PORCH", PP, keep, "Linen", "Linen", tin="custom", group="porch")
    zs = res["ptop"] - 0.8
    outer = [(W - 1.0, PY0 - o), (EX1 + o, PY0 - o), (EX1 + o, EY0 + 3.0), (W - 1.0, EY0 + 3.0)]
    sk, sk_tex = R.hip_roof([(outer, [0, 1])], zs, S_P, 0.0, texture="slant", tex_kw=dict(pitch=1.5, wtab=2.0, d=0.38), zlo=zs)
    shed = ((sk + sk_tex) ^ slab(poly(outer), zs, zs + 8.0)) - bld_keep - union(ins_keep) - MAIN.solid(grow=0.3, dz0=-5, dz1=300)
    kit.add("PORCH-roof", "Cedar", max(shed.decompose(), key=lambda m_: m_.volume()), group="porch")
    for k, (sm, A) in enumerate(PP["steps"]):
        kit.add(f"PORCH-steps-{k}", "Rubble", sm.transform(A) - fkeep - deck, group="porch")
    # --- steps at the front and back doors
    for (x, y) in ((XC, 0.0), (XC, D)):
        e, u = MAIN.locate(x, y)
        f = MAIN.facades()[e]
        A = f.A.copy()
        A[:, 3] = f.world(u, -ZF, 1.4)
        kit.add(f"STOOP-{e}", "Rubble", FT.steps(20.0 if y == 0.0 else 15.0, ZF - 0.6, 4).transform(A) - fnd, group="steps")
    FT.key_into(kit, "PORCH-steps-0", ["PORCH-deck"], (0, 1, 0), depth=0.8, conform=True)
    print("specks dropped:", kit.drop_specks())
    return kit


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.abspath(__file__))
    OUT = os.path.join(HERE, "..", "..", "out", "porter")
    os.makedirs(OUT, exist_ok=True)
    kit = build()
    print(len(kit.parts), "parts")
    if "check" in sys.argv:
        bad = kit.interference()
        print("interfering pairs:", len(bad))
        for b in bad[:80]:
            print("  ", b)
        print("bed:", kit.bed_check())
    kit.render_npz(os.path.join(OUT, "porter.npz"))
    if "export" in sys.argv:
        from hoarch.kit import slice_check
        kit.export(os.path.join(OUT, "kit"), layer=0.2)
        slice_check(os.path.join(OUT, "kit"), os.path.join(HERE, "..", "..", "slicer", "bambu_like.ini"), layer=0.2,
                    supported=("Windows_Doors",))
